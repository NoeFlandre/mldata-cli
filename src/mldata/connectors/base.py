"""Base connector interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import AsyncIterator

from mldata.models.dataset import DatasetMetadata, DownloadProgress, SearchResult


class BaseConnector(ABC):
    """Abstract base class for dataset source connectors."""

    name: str = "base"
    uri_schemes: list[str] = []

    @abstractmethod
    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        modality: str | None = None,
        task: str | None = None,
    ) -> list[SearchResult]:
        """Search for datasets matching query.

        Args:
            query: Search query string
            limit: Maximum results to return
            modality: Filter by data modality
            task: Filter by ML task

        Returns:
            List of search results
        """
        ...

    @abstractmethod
    async def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get detailed metadata for a dataset.

        Args:
            dataset_id: Dataset identifier

        Returns:
            Dataset metadata
        """
        ...

    @abstractmethod
    async def download(
        self,
        dataset_id: str,
        output_dir: Path,
        *,
        revision: str | None = None,
        subset: str | None = None,
    ) -> AsyncIterator[DownloadProgress]:
        """Download dataset files, yielding progress updates.

        Args:
            dataset_id: Dataset identifier
            output_dir: Directory to download files to
            revision: Specific version/revision to download
            subset: Specific subset/config to download

        Yields:
            Download progress updates
        """
        ...

    @abstractmethod
    async def authenticate(self) -> bool:
        """Verify authentication is configured and valid.

        Returns:
            True if authenticated, raises AuthError otherwise
        """
        ...

    @abstractmethod
    def parse_uri(self, uri: str) -> tuple[str, dict[str, str]]:
        """Parse a URI into dataset_id and parameters.

        Args:
            uri: Dataset URI (e.g., 'hf://owner/dataset@v1.0')

        Returns:
            Tuple of (dataset_id, params_dict)
        """
        ...

    def validate_dataset_id(self, dataset_id: str) -> None:
        """Validate dataset ID format.

        Args:
            dataset_id: Dataset identifier to validate

        Raises:
            ValueError: If dataset ID is invalid
        """
        if not dataset_id or "/" not in dataset_id:
            raise ValueError(f"Invalid dataset ID format: {dataset_id}")
