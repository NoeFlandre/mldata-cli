"""Configuration management for mldata-cli."""

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Cache configuration."""

    max_size_gb: float = 10.0
    ttl_hours: int = 168  # 1 week


class BuildConfig(BaseModel):
    """Build configuration."""

    default_format: str = "parquet"
    default_split: list[float] = Field(default_factory=lambda: [0.8, 0.1, 0.1])
    default_seed: int | None = None
    compression: str | None = None
    workers: int | None = None


class AuthConfig(BaseModel):
    """Authentication configuration defaults."""

    hf_token: str | None = None
    kaggle_username: str | None = None
    kaggle_key: str | None = None
    openml_apikey: str | None = None


class Config(BaseModel):
    """Main configuration for mldata-cli."""

    version: str = "1.0"
    cache: CacheConfig = Field(default_factory=CacheConfig)
    build: BuildConfig = Field(default_factory=BuildConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Config":
        """Load configuration from file or use defaults.

        Args:
            config_path: Path to config file. If None, checks default locations.

        Returns:
            Config instance
        """
        if config_path is None:
            config_path = cls._find_config()

        if config_path and config_path.exists():
            try:
                data = yaml.safe_load(config_path.read_text())
                return cls.model_validate(data)
            except Exception:
                return cls()

        return cls()

    @staticmethod
    def _find_config() -> Path | None:
        """Find config file in standard locations.

        Priority:
        1. ./mldata.yaml (project root)
        2. ~/.config/mldata.yaml (user config)
        3. ~/.mldata.yaml (legacy user config)
        """
        project_config = Path.cwd() / "mldata.yaml"
        if project_config.exists():
            return project_config

        user_config = Path.home() / ".config" / "mldata.yaml"
        if user_config.exists():
            return user_config

        legacy_config = Path.home() / ".mldata.yaml"
        if legacy_config.exists():
            return legacy_config

        return None

    def save(self, config_path: Path) -> None:
        """Save configuration to file.

        Args:
            config_path: Path to save config
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(self.model_dump_yaml())

    def model_dump_yaml(self) -> str:
        """Export config as YAML string."""
        return yaml.dump(self.model_dump(mode="yaml"), default_flow_style=False)

    def get_build_format(self) -> str:
        """Get default build format."""
        return self.build.default_format

    def get_split_ratios(self) -> list[float]:
        """Get default split ratios."""
        return self.build.default_split

    def get_workers(self) -> int | None:
        """Get default worker count."""
        return self.build.workers


class ConfigService:
    """Service for managing mldata configuration."""

    def __init__(self):
        """Initialize config service."""
        self.config = Config.load()

    def get(self) -> Config:
        """Get current configuration."""
        return self.config

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Dot-separated key path (e.g., "build.default_format")
            value: Value to set
        """
        keys = key.split(".")

        # Navigate to the right level
        obj = self.config
        for k in keys[:-1]:
            if hasattr(obj, k):
                obj = getattr(obj, k)

        # Set the value
        if hasattr(obj, keys[-1]):
            current_type = type(getattr(obj, keys[-1]))
            if current_type is bool and isinstance(value, str):
                value = value.lower() in ("true", "1", "yes")
            elif current_type is list and isinstance(value, str):
                value = [float(x) for x in value.split(",")]
            elif isinstance(value, str) and current_type in (int, float):
                value = current_type(value)
            setattr(obj, keys[-1], value)

    def save_project_config(self, path: Path | None = None) -> Path:
        """Save configuration as project config.

        Args:
            path: Path to save (default: ./mldata.yaml)

        Returns:
            Path to saved config
        """
        config_path = path or Path.cwd() / "mldata.yaml"
        self.config.save(config_path)
        return config_path

    def show(self) -> str:
        """Show current configuration as YAML."""
        return self.config.model_dump_yaml()
