"""OpenML connector."""

import os
from pathlib import Path
from typing import Any, AsyncIterator

import openml
from openml.datasets import OpenMLDataset

from mldata.models.dataset import (
    DatasetMetadata,
    DatasetSource,
    DataModality,
    MLTask,
    DownloadProgress,
    SearchResult,
)
from mldata.utils.auth import get_credentials
from mldata.connectors.base import BaseConnector


class OpenMLConnector(BaseConnector):
    """Connector for OpenML datasets."""

    name = "openml"
    uri_schemes = ["openml://"]

    def __init__(self, api_key: str | None = None):
        """Initialize OpenML connector.

        Args:
            api_key: OpenML API key
        """
        self.api_key = api_key or self._get_api_key()

    def _get_api_key(self) -> str | None:
        """Get OpenML API key from credentials."""
        creds = get_credentials("openml")
        if creds:
            return creds.get("token")
        return os.environ.get("OPENML_API_KEY")

    async def authenticate(self) -> bool:
        """Check if authenticated with OpenML."""
        if self.api_key:
            openml.config.apikey = self.api_key
        # OpenML allows some operations without auth
        return True

    def parse_uri(self, uri: str) -> tuple[str, dict[str, str]]:
        """Parse OpenML URI.

        Format: openml://dataset_id

        Args:
            uri: Dataset URI

        Returns:
            Tuple of (dataset_id, params_dict)
        """
        if not uri.startswith("openml://"):
            raise ValueError(f"Invalid OpenML URI: {uri}")

        dataset_id = uri[8:].lstrip("/")  # Remove 'openml://' and any leading slashes

        return dataset_id, {}

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        modality: str | None = None,
        task: str | None = None,
    ) -> list[SearchResult]:
        """Search OpenML for datasets.

        Args:
            query: Search query
            limit: Maximum results
            modality: Filter by modality
            task: Filter by task

        Returns:
            List of search results
        """
        if self.api_key:
            openml.config.apikey = self.api_key

        # Search datasets - use dataframe format to avoid FutureWarning
        try:
            datasets_result = openml.datasets.list_datasets(
                offset=0,
                size=limit * 2,  # Get more to filter
                output_format="dataframe",
            )
        except Exception:
            # Fallback to dict format if dataframe fails
            datasets_result = openml.datasets.list_datasets(
                offset=0,
                size=limit * 2,
                output_format="dict",
            )

        search_results = []

        # Handle both dataframe and dict formats
        if hasattr(datasets_result, "iterrows"):  # DataFrame
            for _, d in datasets_result.head(limit).iterrows():
                d = d.to_dict()
                self._add_search_result(search_results, d, query)
        else:  # Dict
            for did, d in datasets_result.items():
                if len(search_results) >= limit:
                    break
                self._add_search_result(search_results, d, query)

        return search_results

    def _add_search_result(
        self,
        search_results: list[SearchResult],
        d: dict[str, Any],
        query: str,
    ) -> None:
        """Add a single search result from OpenML data."""
        # Filter by query if provided
        if query and query.lower() not in d.get("name", "").lower():
            return

        # Extract data - handle both dict and dataframe column names
        did = d.get("did") or d.get("id")
        name = d.get("name")
        description = d.get("description", "")[:500] if d.get("description") else ""
        num_instances = d.get("NumberOfInstances")
        num_classes = d.get("NumberOfClasses")
        license_val = d.get("license")
        creator = d.get("creator")
        upload_date = d.get("upload_date")

        search_results.append(
            SearchResult(
                source=DatasetSource.OPENML,
                dataset_id=str(did),
                name=name,
                description=description,
                size_bytes=0,  # Not available in list response
                num_samples=num_instances,
                modality=DataModality.TABULAR,  # Default for OpenML
                task=MLTask.CLASSIFICATION if num_classes and num_classes > 0 else MLTask.REGRESSION,
                license=license_val,
                author=creator,
                last_updated=upload_date,
                url=f"https://www.openml.org/d/{did}",
                tags=[],
                relevance_score=None,
            )
        )

    async def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get OpenML dataset metadata.

        Args:
            dataset_id: Dataset ID (numeric string)

        Returns:
            Dataset metadata
        """
        if self.api_key:
            openml.config.apikey = self.api_key

        dataset = openml.datasets.get_dataset(int(dataset_id))

        modality_type = self._infer_modality(dataset.default_target_attribute or "")

        return DatasetMetadata(
            source=DatasetSource.OPENML,
            dataset_id=str(dataset.id),
            name=dataset.name,
            description=dataset.description[:1000] if dataset.description else None,
            size_bytes=dataset.qualities.get("NumberOfFeatures", 0) * 1000,
            num_samples=dataset.qualities.get("NumberOfInstances"),
            num_columns=dataset.qualities.get("NumberOfFeatures"),
            modality=modality_type,
            tasks=[MLTask.CLASSIFICATION if dataset.qualities.get("NumberOfClasses") else MLTask.REGRESSION],
            license=dataset.license,
            author=dataset.creator,
            version=str(dataset.version),
            last_updated=dataset.upload_date,
            url=f"https://www.openml.org/d/{dataset.id}",
            tags=dataset.tags or [],
        )

    async def download(
        self,
        dataset_id: str,
        output_dir: Path,
        *,
        revision: str | None = None,
        subset: str | None = None,
    ) -> AsyncIterator[DownloadProgress]:
        """Download OpenML dataset.

        Args:
            dataset_id: Dataset ID (numeric string)
            output_dir: Output directory
            revision: Not applicable for OpenML
            subset: Not applicable for OpenML

        Yields:
            Download progress updates
        """
        import time

        if self.api_key:
            openml.config.apikey = self.api_key

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        dataset = openml.datasets.get_dataset(int(dataset_id))

        # Get the data file
        data_path = dataset.get_data_path()

        # Copy to output directory
        import shutil

        shutil.copy(data_path, output_dir / "data.arff")

        yield DownloadProgress(
            dataset_id=dataset_id,
            source=DatasetSource.OPENML,
            current_bytes=1,
            total_bytes=1,
            status="completed",
        )

    def _infer_modality(self, target_attribute: str) -> DataModality:
        """Infer data modality from target attribute name."""
        text = target_attribute.lower()

        if any(t in text for t in ["image", "img", "picture", "photo"]):
            return DataModality.IMAGE
        if any(t in text for t in ["audio", "sound", "speech", "voice"]):
            return DataModality.AUDIO
        if any(t in text for t in ["text", "document", "article"]):
            return DataModality.TEXT
        if any(t in text for t in ["class", "label", "target"]):
            return DataModality.TABULAR

        return DataModality.TABULAR
