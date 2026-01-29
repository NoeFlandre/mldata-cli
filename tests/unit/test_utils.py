"""Unit tests for utils."""

import pytest
from pathlib import Path


class TestAuthUtils:
    """Tests for auth utilities."""

    def test_get_credentials_no_creds(self):
        """Test getting credentials when none configured."""
        from mldata.utils.auth import get_credentials, clear_credentials

        # Clear any existing credentials
        clear_credentials("huggingface")

        creds = get_credentials("huggingface")
        # Should return None or empty dict
        assert creds is None or len(creds) == 0


class TestHashingUtils:
    """Tests for hashing utilities."""

    def test_compute_hash(self):
        """Test computing hash of data."""
        from mldata.utils.hashing import compute_hash

        hash1 = compute_hash("hello")
        hash2 = compute_hash("hello")
        hash3 = compute_hash("world")

        assert hash1 == hash2
        assert hash1 != hash3
        assert hash1.startswith("sha256:")

    def test_compute_file_hash(self, tmp_path):
        """Test computing hash of a file."""
        from mldata.utils.hashing import compute_file_hash

        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world")

        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)

        assert hash1 == hash2
        assert hash1.startswith("sha256:")


class TestConfigUtils:
    """Tests for config utilities."""

    def test_default_cache_config(self):
        """Test default cache configuration."""
        from mldata.models.config import CacheConfig

        config = CacheConfig()

        assert config.max_size_gb == 50
        assert config.ttl_days == 7
        assert "cache" in str(config.directory)
