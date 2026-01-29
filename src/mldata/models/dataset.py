"""Dataset models."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class DataModality(str, Enum):
    """Data modality types."""

    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    TABULAR = "tabular"
    MULTIMODAL = "multimodal"
    UNKNOWN = "unknown"


class MLTask(str, Enum):
    """ML task types."""

    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    GENERATION = "generation"
    EMBEDDING = "embedding"
    OTHER = "other"


class DataFormat(str, Enum):
    """Data format types."""

    CSV = "csv"
    JSON = "json"
    JSONL = "jsonl"
    PARQUET = "parquet"
    ARROW = "arrow"
    UNKNOWN = "unknown"


class DatasetSource(str, Enum):
    """Dataset source types."""

    HUGGINGFACE = "huggingface"
    KAGGLE = "kaggle"
    OPENML = "openml"
    LOCAL = "local"
    UNKNOWN = "unknown"


class SearchResult(BaseModel):
    """Search result from a dataset source."""

    source: DatasetSource
    dataset_id: str
    name: str
    description: str | None = None
    size_bytes: int | None = None
    num_samples: int | None = None
    modality: DataModality = DataModality.UNKNOWN
    task: MLTask | None = None
    license: str | None = None
    author: str | None = None
    last_updated: datetime | None = None
    url: str | None = None
    tags: list[str] = Field(default_factory=list)
    relevance_score: float | None = None

    @property
    def uri(self) -> str:
        """Get the URI for this dataset."""
        uri_prefixes = {
            DatasetSource.HUGGINGFACE: "hf",
            DatasetSource.KAGGLE: "kaggle",
            DatasetSource.OPENML: "openml",
            DatasetSource.LOCAL: "local",
            DatasetSource.UNKNOWN: "unknown",
        }
        prefix = uri_prefixes.get(self.source, "unknown")
        return f"{prefix}://{self.dataset_id}"


class DownloadProgress(BaseModel):
    """Download progress update."""

    dataset_id: str
    source: DatasetSource
    current_bytes: int = 0
    total_bytes: int | None = None
    speed_bytes_per_sec: float | None = None
    eta_seconds: float | None = None
    status: str = "downloading"
    file_name: str | None = None


class ColumnInfo(BaseModel):
    """Information about a dataset column."""

    name: str
    dtype: str
    nullable: bool = False
    description: str | None = None


class DatasetMetadata(BaseModel):
    """Metadata about a dataset."""

    source: DatasetSource
    dataset_id: str
    name: str
    description: str | None = None
    size_bytes: int | None = None
    num_samples: int | None = None
    num_columns: int | None = None
    columns: list[ColumnInfo] | None = None
    modality: DataModality = DataModality.UNKNOWN
    tasks: list[MLTask] = Field(default_factory=list)
    license: str | None = None
    author: str | None = None
    version: str | None = None
    last_updated: datetime | None = None
    download_count: int | None = None
    citation: str | None = None
    url: str | None = None
    tags: list[str] = Field(default_factory=list)
    raw_files: list[str] = Field(default_factory=list)

    @property
    def uri(self) -> str:
        """Get the URI for this dataset."""
        uri_prefixes = {
            DatasetSource.HUGGINGFACE: "hf",
            DatasetSource.KAGGLE: "kaggle",
            DatasetSource.OPENML: "openml",
            DatasetSource.LOCAL: "local",
            DatasetSource.UNKNOWN: "unknown",
        }
        prefix = uri_prefixes.get(self.source, "unknown")
        return f"{prefix}://{self.dataset_id}"
