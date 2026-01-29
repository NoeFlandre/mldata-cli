"""Kaggle connector."""

import os
from collections.abc import AsyncIterator
from pathlib import Path

from mldata.connectors.base import BaseConnector
from mldata.models.dataset import (
    DataModality,
    DatasetMetadata,
    DatasetSource,
    DownloadProgress,
    MLTask,
    SearchResult,
)
from mldata.utils.auth import get_credentials


class KaggleConnector(BaseConnector):
    """Connector for Kaggle datasets."""

    name = "kaggle"
    uri_schemes = ["kaggle://"]

    def __init__(self, username: str | None = None, key: str | None = None):
        """Initialize Kaggle connector.

        Args:
            username: Kaggle username
            key: Kaggle API key
        """
        self._username = username
        self._key = key
        self._api = None  # Lazy initialization

    @property
    def username(self) -> str | None:
        """Get username lazily."""
        if self._username is None:
            self._username = self._get_username()
        return self._username

    @property
    def key(self) -> str | None:
        """Get key lazily."""
        if self._key is None:
            self._key = self._get_key()
        return self._key

    def _get_username(self) -> str | None:
        """Get Kaggle username from credentials."""
        creds = get_credentials("kaggle")
        if creds:
            return creds.get("username")
        return os.environ.get("KAGGLE_USERNAME")

    def _get_key(self) -> str | None:
        """Get Kaggle API key from credentials."""
        creds = get_credentials("kaggle")
        if creds:
            return creds.get("key")
        return os.environ.get("KAGGLE_KEY")

    def _ensure_authenticated(self) -> None:
        """Ensure Kaggle credentials are configured."""
        if not self.username or not self.key:
            raise ValueError(
                "Kaggle credentials not configured. "
                "Run 'mldata auth login kaggle' or set KAGGLE_USERNAME and KAGGLE_KEY environment variables."
            )

    async def authenticate(self) -> bool:
        """Check if authenticated with Kaggle."""
        self._ensure_authenticated()
        return True

    def parse_uri(self, uri: str) -> tuple[str, dict[str, str]]:
        """Parse Kaggle URI.

        Format: kaggle://owner/dataset

        Args:
            uri: Dataset URI

        Returns:
            Tuple of (dataset_id, params_dict)
        """
        if not uri.startswith("kaggle://"):
            raise ValueError(f"Invalid Kaggle URI: {uri}")

        dataset_id = uri[9:]  # Remove 'kaggle://'

        return dataset_id, {}

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        modality: str | None = None,
        task: str | None = None,
    ) -> list[SearchResult]:
        """Search Kaggle for datasets.

        Args:
            query: Search query
            limit: Maximum results
            modality: Filter by modality
            task: Filter by task

        Returns:
            List of search results
        """
        from kaggle.api.kaggle_api_extended import KaggleApi

        self._ensure_authenticated()

        api = KaggleApi()
        api.authenticate()

        # Search datasets
        results = api.dataset_list(search=query, page=1, page_size=limit)

        search_results = []
        for r in results:
            # Kaggle doesn't provide modality/task directly
            modality_type = self._infer_modality(r.subtitle or "", r.tags or "")
            task_type = self._infer_task(r.tags or "")

            search_results.append(
                SearchResult(
                    source=DatasetSource.KAGGLE,
                    dataset_id=r.ref,
                    name=r.name,
                    description=r.subtitle,
                    size_bytes=r.size,
                    num_samples=r.totalVotes,
                    modality=modality_type,
                    task=task_type,
                    license=r.licenses[0].name if r.licenses else None,
                    author=r.ownerName,
                    url=f"https://www.kaggle.com/datasets/{r.ref}",
                    tags=r.tags or [],
                    relevance_score=None,
                )
            )

        return search_results

    async def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get Kaggle dataset metadata.

        Args:
            dataset_id: Dataset ID (owner/name)

        Returns:
            Dataset metadata
        """
        from kaggle.api.kaggle_api_extended import KaggleApi

        self._ensure_authenticated()
        self.validate_dataset_id(dataset_id)

        api = KaggleApi()
        api.authenticate()

        # Get dataset metadata
        metadata = api.dataset_metadata(dataset_id, ".")

        # Parse owner/name
        parts = dataset_id.split("/")

        return DatasetMetadata(
            source=DatasetSource.KAGGLE,
            dataset_id=dataset_id,
            name=parts[-1],
            description="",
            size_bytes=metadata.get("totalSize"),
            modality=DataModality.UNKNOWN,
            tasks=[],
            license=metadata.get("license"),
            author=parts[0],
            version=metadata.get("versionNumber"),
            url=f"https://www.kaggle.com/datasets/{dataset_id}",
        )

    async def download(
        self,
        dataset_id: str,
        output_dir: Path,
        *,
        revision: str | None = None,
        subset: str | None = None,
    ) -> AsyncIterator[DownloadProgress]:
        """Download Kaggle dataset.

        Args:
            dataset_id: Dataset ID (owner/name)
            output_dir: Output directory
            revision: Not applicable for Kaggle
            subset: Not applicable for Kaggle

        Yields:
            Download progress updates
        """
        from kaggle.api.kaggle_api_extended import KaggleApi

        self._ensure_authenticated()
        self.validate_dataset_id(dataset_id)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        api = KaggleApi()
        api.authenticate()

        # Download dataset
        api.dataset_download_files(
            dataset_id,
            path=str(output_dir),
            unzip=True,
        )

        yield DownloadProgress(
            dataset_id=dataset_id,
            source=DatasetSource.KAGGLE,
            current_bytes=1,
            total_bytes=1,
            status="completed",
        )

    def _infer_modality(self, description: str, tags: str) -> DataModality:
        """Infer data modality from description and tags."""
        text = (description + " " + tags).lower()

        if any(t in text for t in ["image", "photo", "picture", "vision"]):
            return DataModality.IMAGE
        if any(t in text for t in ["audio", "sound", "speech", "voice"]):
            return DataModality.AUDIO
        if any(t in text for t in ["text", "nlp", "language", "document"]):
            return DataModality.TEXT
        if any(t in text for t in ["tabular", "csv", "excel", "spreadsheet"]):
            return DataModality.TABULAR

        return DataModality.UNKNOWN

    def _infer_task(self, tags: str) -> MLTask | None:
        """Infer ML task from tags."""
        text = tags.lower()

        if any(t in text for t in ["classification", "classify"]):
            return MLTask.CLASSIFICATION
        if any(t in text for t in ["regression"]):
            return MLTask.REGRESSION
        if any(t in text for t in ["generation", "text generation"]):
            return MLTask.GENERATION

        return MLTask.OTHER
