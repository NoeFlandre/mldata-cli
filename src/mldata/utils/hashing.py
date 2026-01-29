"""Hashing utilities."""

import hashlib
from pathlib import Path


def compute_hash(data: bytes | str) -> str:
    """Compute SHA-256 hash of data."""
    if isinstance(data, str):
        data = data.encode()
    return f"sha256:{hashlib.sha256(data).hexdigest()}"


def compute_file_hash(file_path: Path, chunk_size: int = 8192) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return f"sha256:{sha256.hexdigest()}"


def compute_dir_hash(dir_path: Path) -> str:
    """Compute hash of all files in a directory."""
    import os

    hashes = []
    for root, _, files in os.walk(dir_path):
        for file in sorted(files):
            file_path = Path(root) / file
            rel_path = file_path.relative_to(dir_path)
            file_hash = compute_file_hash(file_path)
            hashes.append(f"{rel_path}:{file_hash}")

    combined = "|".join(hashes)
    return compute_hash(combined)
