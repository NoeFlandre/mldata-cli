"""Incremental build service for change detection and selective processing."""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class BuildCache(BaseModel):
    """Cache of file hashes from previous builds."""

    version: str = "1.0"
    source_uri: str = ""
    file_hashes: dict[str, str] = {}

    def save(self, path: Path) -> None:
        """Save cache to file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load(cls, path: Path) -> "BuildCache | None":
        """Load cache from file."""
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text())
            return cls.model_validate(data)
        except Exception:
            return None


class IncrementalService:
    """Service for incremental builds with change detection."""

    def __init__(self, cache_dir: Path | None = None):
        """Initialize incremental service.

        Args:
            cache_dir: Directory for cache files. Defaults to ~/.mldata/cache.
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".mldata" / "incremental"
        self.cache_dir = cache_dir
        self.cache_file = self.cache_dir / "build_cache.json"

    def compute_file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of a file.

        Args:
            path: Path to file

        Returns:
            Hex string of file hash
        """
        import hashlib

        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def compute_dir_hashes(self, dir_path: Path) -> dict[str, str]:
        """Compute hashes for all data files in a directory.

        Args:
            dir_path: Path to directory

        Returns:
            Dict mapping relative file paths to hashes
        """
        hashes = {}
        extensions = {".csv", ".parquet", ".jsonl", ".json", ".arrow"}

        for ext in extensions:
            for file_path in dir_path.rglob(f"*{ext}"):
                # Skip hidden directories and cache directories
                if any(part.startswith(".") for part in file_path.relative_to(dir_path).parts):
                    continue
                relative_path = str(file_path.relative_to(dir_path))
                hashes[relative_path] = self.compute_file_hash(file_path)

        return hashes

    def get_cached_hashes(self) -> BuildCache | None:
        """Get cached hashes from previous build.

        Returns:
            BuildCache or None if not found
        """
        return BuildCache.load(self.cache_file)

    def save_hashes(self, source_uri: str, hashes: dict[str, str]) -> None:
        """Save current hashes for future comparison.

        Args:
            source_uri: Source URI of the dataset
            hashes: Dict of file paths to hashes
        """
        cache = BuildCache(source_uri=source_uri, file_hashes=hashes)
        cache.save(self.cache_file)

    def detect_changes(
        self,
        current_dir: Path,
        source_uri: str | None = None,
    ) -> dict[str, Any]:
        """Detect changes between current and cached build.

        Args:
            current_dir: Directory to check
            source_uri: Source URI for cache lookup

        Returns:
            Dict with changed, added, removed, unchanged lists
        """
        current_hashes = self.compute_dir_hashes(current_dir)
        cached = self.get_cached_hashes()

        result = {
            "changed": [],
            "added": [],
            "removed": [],
            "unchanged": [],
            "total_current": len(current_hashes),
            "total_cached": len(cached.file_hashes) if cached else 0,
        }

        # Check for changed and unchanged files
        if cached:
            for file_path, current_hash in current_hashes.items():
                if file_path in cached.file_hashes:
                    if cached.file_hashes[file_path] != current_hash:
                        result["changed"].append(file_path)
                    else:
                        result["unchanged"].append(file_path)
                else:
                    result["added"].append(file_path)

            # Find removed files
            for file_path in cached.file_hashes:
                if file_path not in current_hashes:
                    result["removed"].append(file_path)
        else:
            result["added"] = list(current_hashes.keys())

        # Check source URI match
        if cached and source_uri and cached.source_uri != source_uri:
            result["source_changed"] = True
            result["message"] = f"Source URI changed from {cached.source_uri} to {source_uri}"

        return result

    def should_process(self, changes: dict[str, Any]) -> bool:
        """Determine if processing is needed based on changes.

        Args:
            changes: Dict from detect_changes

        Returns:
            True if processing should occur
        """
        # Always process if source changed
        if changes.get("source_changed"):
            return True

        # Process if there are changed or added files
        if changes["changed"] or changes["added"]:
            return True

        # Don't process if all files unchanged or only removed
        return False

    def get_files_to_process(
        self,
        current_dir: Path,
        changes: dict[str, Any],
    ) -> list[Path]:
        """Get list of files that need processing.

        Args:
            current_dir: Directory containing files
            changes: Dict from detect_changes

        Returns:
            List of file paths to process
        """
        files_to_process = []

        # Process changed and added files
        for relative_path in changes["changed"] + changes["added"]:
            file_path = current_dir / relative_path
            if file_path.exists():
                files_to_process.append(file_path)

        return files_to_process

    def get_files_to_skip(
        self,
        current_dir: Path,
        changes: dict[str, Any],
    ) -> list[Path]:
        """Get list of files that can be skipped.

        Args:
            current_dir: Directory containing files
            changes: Dict from detect_changes

        Returns:
            List of file paths to skip
        """
        files_to_skip = []

        for relative_path in changes["unchanged"]:
            file_path = current_dir / relative_path
            if file_path.exists():
                files_to_skip.append(file_path)

        return files_to_skip

    def update_cache_after_build(
        self,
        current_dir: Path,
        source_uri: str,
    ) -> None:
        """Update cache after a successful build.

        Args:
            current_dir: Directory containing built files
            source_uri: Source URI of the dataset
        """
        hashes = self.compute_dir_hashes(current_dir)
        self.save_hashes(source_uri, hashes)

    def clear_cache(self) -> None:
        """Clear the build cache."""
        if self.cache_file.exists():
            self.cache_file.unlink()
