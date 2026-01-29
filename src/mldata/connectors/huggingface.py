"""HuggingFace connector."""

import os
from pathlib import Path
from typing import AsyncIterator

from huggingface_hub import HfApi

from mldata.models.dataset import (
    DatasetMetadata,
    DatasetSource,
    DataModality,
    MLTask,
    DownloadProgress,
    SearchResult,
)
from mldata.connectors.base import BaseConnector


class HuggingFaceConnector(BaseConnector):
    """Connector for HuggingFace Hub datasets."""

    name = "huggingface"
    uri_schemes = ["hf://", "huggingface://"]

    def __init__(self, token: str | None = None):
        """Initialize HuggingFace connector.

        Args:
            token: HuggingFace API token
        """
        self.token = token or os.environ.get("HUGGINGFACE_TOKEN")
        self.api = HfApi(token=self.token)

    async def authenticate(self) -> bool:
        """Check if authenticated with HuggingFace."""
        if self.token:
            return True
        # Try to use token-less access for public datasets
        return True

    def parse_uri(self, uri: str) -> tuple[str, dict[str, str]]:
        """Parse HuggingFace URI.

        Format: hf://owner/dataset[@revision]

        Args:
            uri: Dataset URI

        Returns:
            Tuple of (dataset_id, params_dict)
        """
        if not uri.startswith(("hf://", "huggingface://")):
            raise ValueError(f"Invalid HuggingFace URI: {uri}")

        uri = uri.replace("huggingface://", "hf://")
        parts = uri[5:].split("@")

        dataset_id = parts[0]
        params = {}

        if len(parts) > 1:
            params["revision"] = parts[1]

        return dataset_id, params

    async def search(
        self,
        query: str,
        *,
        limit: int = 20,
        modality: str | None = None,
        task: str | None = None,
    ) -> list[SearchResult]:
        """Search HuggingFace Hub for datasets.

        Args:
            query: Search query
            limit: Maximum results
            modality: Filter by modality
            task: Filter by task

        Returns:
            List of search results
        """
        # Search for datasets
        results = list(self.api.list_datasets(
            search=query,
            limit=limit,
        ))

        search_results = []
        for r in results:
            # Fetch full metadata for size, license, etc.
            try:
                full_info = self.api.dataset_info(r.id)
                size_bytes = getattr(full_info, "usedStorage", None)
                # License can be a list or string
                license_data = full_info.card_data.get("license") if full_info.card_data else None
                if isinstance(license_data, list):
                    license = license_data[0] if license_data else None
                elif isinstance(license_data, str):
                    license = license_data
                else:
                    license = None
                tags = full_info.tags or []
            except Exception:
                size_bytes = None
                license = None
                tags = r.tags or []

            # Determine modality from tags
            modality_type = self._infer_modality(tags)
            task_type = self._infer_task(tags)

            # Filter by modality if specified
            if modality and modality_type.value != modality:
                continue

            search_results.append(
                SearchResult(
                    source=DatasetSource.HUGGINGFACE,
                    dataset_id=r.id,
                    name=r.id.split("/")[-1],
                    description=getattr(r, "description", "") or "",
                    size_bytes=size_bytes,
                    modality=modality_type,
                    task=task_type,
                    license=license,
                    author=r.id.split("/")[0],
                    url=f"https://huggingface.co/datasets/{r.id}",
                    tags=tags,
                    relevance_score=None,
                )
            )

        return search_results

    async def get_metadata(self, dataset_id: str) -> DatasetMetadata:
        """Get HuggingFace dataset metadata.

        Args:
            dataset_id: Dataset ID (owner/name)

        Returns:
            Dataset metadata
        """
        from datasets import load_dataset

        self.validate_dataset_id(dataset_id)

        info = self.api.dataset_info(dataset_id)

        # Infer modality and task from tags
        modality = self._infer_modality(info.tags or [])
        tasks = [self._infer_task(info.tags or [])] if info.tags else []

        # Handle license which can be a list or string
        license_data = info.card_data.get("license") if info.card_data else None
        if isinstance(license_data, list):
            license = license_data[0] if license_data else None
        elif isinstance(license_data, str):
            license = license_data
        else:
            license = None

        # Extract description from card_data
        description = ""
        if info.card_data:
            # Try different paths for description
            description = info.card_data.get("annotations", {}).get("description", "")
            if not description:
                description = info.card_data.get("description", "")

        # Get citation from card_data
        citation = None
        if info.card_data:
            citation = info.card_data.get("citation")

        # Load dataset to get schema and sample
        columns = None
        num_samples = None
        try:
            # Disable progress bars
            import os
            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

            dataset = load_dataset(dataset_id, split="train", trust_remote_code=True)
            if hasattr(dataset, "info") and dataset.info.features:
                from mldata.models.dataset import ColumnInfo
                columns = []
                for name, dtype in dataset.info.features.items():
                    col_info = ColumnInfo(
                        name=name,
                        dtype=str(dtype),
                        nullable=False,
                    )
                    columns.append(col_info)
            num_samples = len(dataset) if hasattr(dataset, "__len__") else None
        except Exception:
            pass  # Keep None values on failure

        return DatasetMetadata(
            source=DatasetSource.HUGGINGFACE,
            dataset_id=dataset_id,
            name=dataset_id.split("/")[-1],
            description=description,
            size_bytes=getattr(info, "usedStorage", None),
            num_samples=num_samples,
            num_columns=len(columns) if columns else None,
            columns=columns,
            modality=modality,
            tasks=tasks,
            license=license,
            author=dataset_id.split("/")[0],
            version=info.sha,
            last_updated=info.last_modified,
            url=f"https://huggingface.co/datasets/{dataset_id}",
            tags=info.tags or [],
            citation=citation,
        )

    async def download(
        self,
        dataset_id: str,
        output_dir: Path,
        *,
        revision: str | None = None,
        subset: str | None = None,
    ) -> AsyncIterator[DownloadProgress]:
        """Download HuggingFace dataset.

        Args:
            dataset_id: Dataset ID (owner/name)
            output_dir: Output directory
            revision: Git revision (branch, tag, commit)
            subset: Dataset configuration/subset

        Yields:
            Download progress updates
        """
        from datasets import load_dataset

        self.validate_dataset_id(dataset_id)

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Prepare download config
        download_config = {
            "token": self.token,
            "revision": revision or "main",
            "download_mode": "reuse_cache_if_exists",
        }

        # Disable progress bars
        import os
        os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"

        if subset:
            download_config["name"] = subset

        # Load dataset
        try:
            dataset = load_dataset(dataset_id, **download_config)

            # Save dataset files
            for split_name, ds in dataset.items():
                split_dir = output_dir / split_name
                split_dir.mkdir(parents=True, exist_ok=True)

                # Determine format and save
                if hasattr(ds, "to_pandas"):
                    # Save as parquet if possible
                    ds.to_parquet(str(split_dir / "data.parquet"))
                else:
                    ds.save_to_disk(str(split_dir))

                yield DownloadProgress(
                    dataset_id=dataset_id,
                    source=DatasetSource.HUGGINGFACE,
                    current_bytes=1,
                    total_bytes=1,
                    status="completed",
                    file_name=split_name,
                )

        except Exception as e:
            yield DownloadProgress(
                dataset_id=dataset_id,
                source=DatasetSource.HUGGINGFACE,
                status="error",
            )
            raise

    def _infer_modality(self, tags: list[str]) -> DataModality:
        """Infer data modality from tags."""
        # Extract tag values (handle prefixes like "modality:text")
        tag_values = []
        for t in tags:
            if ":" in t:
                tag_values.append(t.split(":", 1)[1].lower())
            else:
                tag_values.append(t.lower())

        if any(t in tag_values for t in ["image", "vision", "imageclassification", "objectdetection"]):
            return DataModality.IMAGE
        if any(t in tag_values for t in ["audio", "speech", "asr", "texttospeech"]):
            return DataModality.AUDIO
        if any(t in tag_values for t in ["text", "nlp", "language", "tokenclassification", "questionanswering"]):
            return DataModality.TEXT
        if any(t in tag_values for t in ["tabular", "csv", "json", "database"]):
            return DataModality.TABULAR

        return DataModality.UNKNOWN

    def _infer_task(self, tags: list[str]) -> MLTask | None:
        """Infer ML task from tags."""
        # Extract tag values (handle prefixes like "task_categories:text-classification")
        tag_values = []
        for t in tags:
            if ":" in t:
                tag_values.append(t.split(":", 1)[1].lower())
            else:
                tag_values.append(t.lower())

        if any(t in tag_values for t in ["classification", "imageclassification", "textclassification"]):
            return MLTask.CLASSIFICATION
        if any(t in tag_values for t in ["regression"]):
            return MLTask.REGRESSION
        if any(t in tag_values for t in ["generation", "textgeneration", "translation"]):
            return MLTask.GENERATION

        return MLTask.OTHER
