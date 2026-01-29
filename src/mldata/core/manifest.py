"""Manifest service for build provenance tracking."""

import hashlib
import json
import platform
from datetime import datetime
from pathlib import Path
from typing import Any

from mldata.models.manifest import Manifest
from mldata.models.dataset import DatasetMetadata


class ManifestService:
    """Service for creating and managing build manifests."""

    def __init__(self):
        """Initialize manifest service."""
        pass

    def create_manifest(
        self,
        source_uri: str,
        source_params: dict[str, Any],
        build_params: dict[str, Any],
        dataset_info: dict[str, Any],
        artifact_hashes: dict[str, str],
        tool_version: str,
    ) -> Manifest:
        """Create a new manifest for a build.

        Args:
            source_uri: Source URI of the dataset
            source_params: Parameters from source (version, subset, etc.)
            build_params: Build parameters (seed, ratios, format, etc.)
            dataset_info: Dataset information (size, samples, schema)
            artifact_hashes: SHA-256 hashes of output artifacts
            tool_version: mldata-cli version

        Returns:
            Manifest instance
        """
        from datetime import timezone

        now = datetime.now(timezone.utc)

        # Compute source hash
        source_content = f"{source_uri}{json.dumps(source_params, sort_keys=True)}".encode()
        source_hash = f"sha256:{hashlib.sha256(source_content).hexdigest()}"

        manifest = Manifest(
            mldata_version=tool_version,
            created_at=now,
            python_version=platform.python_version(),
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
                "python_version": platform.python_version(),
            },
        )

        return manifest

    def save_manifest(self, manifest: Manifest, path: Path) -> None:
        """Save manifest to YAML file.

        Args:
            manifest: Manifest instance
            path: Output file path
        """
        import yaml

        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w") as f:
            yaml.dump(manifest.model_dump(mode="json"), f, default_flow_style=False, sort_keys=False)

    def load_manifest(self, path: Path) -> Manifest:
        """Load manifest from YAML file.

        Args:
            path: Path to manifest file

        Returns:
            Manifest instance
        """
        import yaml

        with open(path) as f:
            data = yaml.safe_load(f)

        return Manifest(**data)

    def verify_artifact_hashes(
        self,
        manifest: Manifest,
        actual_hashes: dict[str, str],
    ) -> dict[str, bool]:
        """Verify artifact hashes against manifest.

        Args:
            manifest: Manifest instance
            actual_hashes: Dict of artifact name to actual hash

        Returns:
            Dict mapping artifact name to match status
        """
        expected_hashes = manifest.provenance.get("artifact_hashes", {})

        results = {}
        for artifact_name, expected in expected_hashes.items():
            actual = actual_hashes.get(artifact_name)
            results[artifact_name] = expected == actual

        return results

    def compute_artifact_hashes(
        self,
        output_dir: Path,
    ) -> dict[str, str]:
        """Compute hashes for all artifacts in output directory.

        Args:
            output_dir: Output directory path

        Returns:
            Dict mapping artifact name to hash
        """
        hashes = {}

        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(output_dir)
                artifact_name = str(rel_path)
                file_hash = self._compute_file_hash(file_path)
                hashes[artifact_name] = file_hash

        return hashes

    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of a file.

        Args:
            file_path: Path to file

        Returns:
            SHA-256 hash as hex string
        """
        import hashlib

        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"
