"""Manifest models."""

from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class Manifest(BaseModel):
    """Dataset build manifest capturing full provenance."""

    mldata_version: str
    created_at: datetime
    python_version: str

    source: dict[str, Any] = Field(default_factory=dict)
    build: dict[str, Any] = Field(default_factory=dict)
    provenance: dict[str, Any] = Field(default_factory=dict)
    dataset: dict[str, Any] = Field(default_factory=dict)
    quality: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def create(
        cls,
        source_uri: str,
        source_params: dict[str, Any],
        build_params: dict[str, Any],
        dataset_info: dict[str, Any],
        artifact_hashes: dict[str, str],
        tool_version: str,
        python_version: str,
    ) -> "Manifest":
        """Create a new manifest."""
        import hashlib
        import platform
        from datetime import timezone

        now = datetime.now(timezone.utc)

        # Compute source hash
        source_content = f"{source_uri}{source_params}".encode()
        source_hash = f"sha256:{hashlib.sha256(source_content).hexdigest()}"

        manifest = cls(
            mldata_version=tool_version,
            created_at=now,
            python_version=python_version,
            source={
                "uri": source_uri,
                **source_params,
                "fetched_at": now.isoformat(),
            },
            build=build_params,
            provenance={
                "source_hash": source_hash,
                "artifact_hashes": artifact_hashes,
            },
            dataset=dataset_info,
            quality={"checks_passed": True, "issues_found": 0},
            environment={
                "os": platform.system(),
                "architecture": platform.machine(),
                "python_version": python_version,
            },
        )

        return manifest

    def to_yaml(self, path: Path) -> None:
        """Write manifest to YAML file."""
        import yaml

        with open(path, "w") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False, sort_keys=False)

    @classmethod
    def from_yaml(cls, path: Path) -> "Manifest":
        """Load manifest from YAML file."""
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(**data)


class BuildConfig(BaseModel):
    """Configuration for a dataset build."""

    source_uri: str
    output_dir: Path | None = None
    format: str = "parquet"
    split_ratios: list[float] = Field(default_factory=lambda: [0.8, 0.1, 0.1])
    seed: int | None = None
    stratify_column: str | None = None
    checks: list[str] = Field(default_factory=lambda: ["duplicates", "labels", "missing", "schema"])
    no_cache: bool = False
