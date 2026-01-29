"""Fetch service for downloading datasets."""

import asyncio
import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from mldata.connectors.registry import get_connector
from mldata.core.cache import CacheService


@dataclass
class PartialDownload:
    """State for interrupted downloads."""
    url: str
    temp_path: Path
    final_path: Path
    expected_size: int = 0
    downloaded_size: int = 0
    etag: str | None = None
    last_modified: str | None = None
    content_hash: str | None = None
    created_at: float = field(default_factory=time.time)
    resumed_at: float | None = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "url": self.url,
            "temp_path": str(self.temp_path),
            "final_path": str(self.final_path),
            "expected_size": self.expected_size,
            "downloaded_size": self.downloaded_size,
            "etag": self.etag,
            "last_modified": self.last_modified,
            "content_hash": self.content_hash,
            "created_at": self.created_at,
            "resumed_at": self.resumed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PartialDownload":
        """Deserialize from dictionary."""
        return cls(
            url=data["url"],
            temp_path=Path(data["temp_path"]),
            final_path=Path(data["final_path"]),
            expected_size=data.get("expected_size", 0),
            downloaded_size=data.get("downloaded_size", 0),
            etag=data.get("etag"),
            last_modified=data.get("last_modified"),
            content_hash=data.get("content_hash"),
            created_at=data.get("created_at", 0),
            resumed_at=data.get("resumed_at"),
        )


class FetchService:
    """Service for fetching datasets from various sources."""

    # Resume state directory
    RESUME_DIR = Path("~/.mldata/resume").expanduser()

    def __init__(self, cache: CacheService | None = None):
        """Initialize fetch service.

        Args:
            cache: Cache service instance
        """
        self.cache = cache or CacheService()
        self.RESUME_DIR.mkdir(parents=True, exist_ok=True)

    async def fetch(
        self,
        uri: str,
        output_dir: Path,
        *,
        revision: str | None = None,
        subset: str | None = None,
        no_cache: bool = False,
        progress: bool = True,
    ) -> Path:
        """Fetch a dataset from a URI.

        Args:
            uri: Dataset URI (hf://, kaggle://, openml://)
            output_dir: Output directory
            revision: Specific version/revision
            subset: Specific subset/config
            no_cache: Skip cache and download fresh
            progress: Show progress bar

        Returns:
            Path to downloaded dataset directory

        Raises:
            ValueError: If URI is invalid
            Exception: If download fails
        """
        # Get connector
        connector = get_connector(uri)

        # Parse URI to get dataset ID
        dataset_id, params = connector.parse_uri(uri)

        # Check cache
        cache_key = self.cache.get_cache_key(uri, params.get("revision") or revision, params)
        if not no_cache and self.cache.exists(cache_key):
            cached_path = self.cache.get(cache_key)
            if cached_path and Path(cached_path).exists():
                # Copy from cache to output
                return await self._copy_from_cache(cached_path, output_dir, uri)

        # Download with simple progress
        print(f"Downloading {uri}...")

        try:
            async for progress_update in connector.download(
                dataset_id,
                output_dir,
                revision=revision or params.get("revision"),
                subset=subset or params.get("subset"),
            ):
                pass  # Progress updates are yielded by connector

            # Cache the result
            self.cache.set(cache_key, str(output_dir))

            print(f"[green]Downloaded to {output_dir}[/]")

            return output_dir

        except Exception as e:
            print(f"[red]Download failed: {e}[/]")
            raise

    async def fetch_with_resume(
        self,
        url: str,
        output_path: Path,
        *,
        expected_hash: str | None = None,
        progress: bool = True,
    ) -> Path:
        """Fetch a file with resume support.

        Args:
            url: URL to download
            output_path: Final output path
            expected_hash: Expected SHA-256 hash for verification
            progress: Show progress bar

        Returns:
            Path to downloaded file
        """
        import httpx
        import time

        resume_state_path = self.RESUME_DIR / hashlib.md5(url.encode()).hexdigest()
        partial = None

        # Check for existing partial download
        if resume_state_path.exists():
            try:
                partial_data = json.loads(resume_state_path.read_text())
                partial = PartialDownload.from_dict(partial_data)
                # Check if the partial is for the same URL and file exists
                if partial.temp_path.exists() and partial.url == url:
                    print(f"[cyan]Resuming download from {partial.downloaded_size} bytes...[/]")
            except (json.JSONDecodeError, KeyError):
                partial = None

        async with httpx.AsyncClient(timeout=300.0) as client:
            headers = {}

            # Resume from partial file
            if partial and partial.temp_path.exists():
                headers["Range"] = f"bytes={partial.downloaded_size}-"
                partial.resumed_at = time.time()

            response = await client.head(url, follow_redirects=True)
            total_size = int(response.headers.get("content-length", 0))
            etag = response.headers.get("etag")
            last_modified = response.headers.get("last-modified")

            # Update partial info
            if partial:
                partial.expected_size = total_size
                partial.etag = etag
                partial.last_modified = last_modified
            else:
                partial = PartialDownload(
                    url=url,
                    temp_path=output_path.with_suffix(".part"),
                    final_path=output_path,
                    expected_size=total_size,
                    etag=etag,
                    last_modified=last_modified,
                )

            # Start or resume download
            mode = "ab" if partial.downloaded_size > 0 else "wb"
            headers["Range"] = f"bytes={partial.downloaded_size}-" if partial.downloaded_size > 0 else {}

            downloaded_size = partial.downloaded_size
            start_time = time.time()
            last_update = start_time
            speed = 0.0

            async with client.stream("GET", url, headers=headers) as response:
                # Handle partial content or full response
                status = response.status_code
                is_partial = status == 206

                if is_partial:
                    # Resume mode
                    downloaded_size = partial.downloaded_size
                elif partial.downloaded_size > 0 and status == 200:
                    # Server doesn't support resume, start over
                    downloaded_size = 0
                    partial.downloaded_size = 0
                    mode = "wb"

                with open(partial.temp_path, mode) as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Update progress periodically
                        current_time = time.time()
                        elapsed = current_time - last_update
                        if elapsed >= 0.5:
                            # Calculate speed
                            chunk_size = downloaded_size - partial.downloaded_size
                            if elapsed > 0:
                                speed = chunk_size / elapsed

                            # Calculate ETA
                            if total_size > 0 and speed > 0:
                                remaining = total_size - downloaded_size
                                eta = remaining / speed
                                eta_str = self._format_eta(eta)
                                speed_str = self._format_speed(speed)
                                percent = (downloaded_size / total_size * 100) if total_size > 0 else 0
                                print(f"\r  Progress: {percent:.1f}% | {speed_str} | ETA: {eta_str}", end="", flush=True)
                            last_update = current_time

            # Download complete
            print()  # New line after progress

            # Verify hash if provided
            if expected_hash:
                actual_hash = self._compute_file_hash(partial.temp_path)
                if actual_hash != expected_hash:
                    partial.temp_path.unlink()
                    raise ValueError(f"Hash mismatch: expected {expected_hash}, got {actual_hash}")

            # Rename to final path
            if partial.temp_path.exists():
                partial.temp_path.rename(partial.final_path)

            # Update and save final state
            partial.downloaded_size = downloaded_size
            self._save_resume_state(partial)

            # Clean up resume state on success
            resume_state_path.unlink(missing_ok=True)

            print(f"[green]Downloaded to {partial.final_path}[/]")
            return partial.final_path

    def _format_eta(self, seconds: float) -> str:
        """Format ETA as human-readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

    def _format_speed(self, bytes_per_sec: float) -> str:
        """Format speed as human-readable string."""
        if bytes_per_sec < 1024:
            return f"{bytes_per_sec:.0f} B/s"
        elif bytes_per_sec < 1024 * 1024:
            return f"{bytes_per_sec / 1024:.1f} KB/s"
        else:
            return f"{bytes_per_sec / (1024 * 1024):.1f} MB/s"

    def _compute_file_hash(self, path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _save_resume_state(self, partial: PartialDownload) -> None:
        """Save resume state to disk."""
        resume_state_path = self.RESUME_DIR / hashlib.md5(partial.url.encode()).hexdigest()
        resume_state_path.write_text(json.dumps(partial.to_dict()))

    def get_resume_state(self, url: str) -> PartialDownload | None:
        """Get resume state for a URL.

        Args:
            url: Download URL

        Returns:
            PartialDownload state or None
        """
        resume_state_path = self.RESUME_DIR / hashlib.md5(url.encode()).hexdigest()
        if resume_state_path.exists():
            try:
                return PartialDownload.from_dict(json.loads(resume_state_path.read_text()))
            except (json.JSONDecodeError, KeyError):
                return None
        return None

    def cleanup_resume_state(self, url: str) -> None:
        """Clean up resume state for a URL.

        Args:
            url: Download URL
        """
        import time

        resume_state_path = self.RESUME_DIR / hashlib.md5(url.encode()).hexdigest()
        if resume_state_path.exists():
            # Check if file is old (24+ hours) and clean up
            state = self.get_resume_state(url)
            if state:
                age = time.time() - max(state.created_at, state.resumed_at or 0)
                if age > 86400:  # 24 hours
                    if state.temp_path.exists():
                        state.temp_path.unlink()
                    resume_state_path.unlink()

    async def _copy_from_cache(self, cached_path: str, output_dir: Path, uri: str) -> Path:
        """Copy dataset from cache to output directory.

        Args:
            cached_path: Path to cached dataset
            output_dir: Output directory
            uri: Dataset URI (for display)

        Returns:
            Path to output directory
        """
        import shutil

        output_dir.mkdir(parents=True, exist_ok=True)

        cached = Path(cached_path)
        if cached.is_file():
            shutil.copy(cached, output_dir / cached.name)
        else:
            for item in cached.rglob("*"):
                if item.is_file():
                    dest = output_dir / item.relative_to(cached)
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy(item, dest)

        return output_dir

    async def authenticate(self, uri: str) -> bool:
        """Authenticate with the source for a URI.

        Args:
            uri: Dataset URI

        Returns:
            True if authenticated
        """
        connector = get_connector(uri)
        return await connector.authenticate()
