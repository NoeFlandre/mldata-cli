"""Configuration models."""

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class CacheConfig(BaseModel):
    """Cache configuration."""

    directory: Path = Path.home() / ".mldata" / "cache"
    max_size_gb: float = 50
    ttl_days: int = 7


class DefaultsConfig(BaseModel):
    """Default configuration."""

    format: str = "parquet"
    split_ratios: list[float] = Field(default_factory=lambda: [0.8, 0.1, 0.1])
    checks: list[str] = Field(default_factory=lambda: ["duplicates", "labels", "missing", "schema"])


class ConnectorConfig(BaseModel):
    """Connector configuration."""

    enabled: bool = True


class MldataConfig(BaseModel):
    """Global mldata configuration."""

    version: int = 1
    cache: CacheConfig = Field(default_factory=CacheConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    connectors: dict[str, ConnectorConfig] = Field(default_factory=dict)
    telemetry: dict[str, Any] = Field(default_factory=lambda: {"enabled": False})

    @classmethod
    def load(cls, config_path: Path | None = None) -> "MldataConfig":
        """Load configuration from file."""
        import yaml

        if config_path is None:
            config_path = Path.home() / ".mldata" / "config.yaml"

        if config_path.exists():
            with open(config_path) as f:
                data = yaml.safe_load(f)
            return cls(**data)

        return cls()

    def save(self, config_path: Path | None = None) -> None:
        """Save configuration to file."""
        import yaml

        if config_path is None:
            config_path = Path.home() / ".mldata" / "config.yaml"

        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w") as f:
            yaml.dump(self.model_dump(mode="json"), f, default_flow_style=False)
