"""Connector registry."""

from typing import Type

from mldata.connectors.base import BaseConnector
from mldata.connectors.huggingface import HuggingFaceConnector
from mldata.connectors.kaggle import KaggleConnector
from mldata.connectors.openml import OpenMLConnector
from mldata.connectors.local import LocalConnector


CONNECTORS: dict[str, Type[BaseConnector]] = {
    "huggingface": HuggingFaceConnector,
    "hf": HuggingFaceConnector,
    "kaggle": KaggleConnector,
    "openml": OpenMLConnector,
    "local": LocalConnector,
}

URI_SCHEME_MAP: dict[str, Type[BaseConnector]] = {}


def _build_uri_scheme_map() -> None:
    """Build a mapping from URI schemes to connectors."""
    for name, connector in CONNECTORS.items():
        for scheme in connector.uri_schemes:
            URI_SCHEME_MAP[scheme] = connector


_build_uri_scheme_map()


def get_connector(uri: str) -> BaseConnector:
    """Get the appropriate connector for a URI.

    Args:
        uri: Dataset URI (e.g., 'hf://owner/dataset') or local path

    Returns:
        Connector instance for the URI

    Raises:
        ValueError: If no connector found for URI scheme
    """
    # Check for local paths (no scheme, or file:// scheme)
    if "://" not in uri:
        # Check if it's a valid local path
        from pathlib import Path
        path = Path(uri)
        if uri.startswith("/") or uri.startswith("./") or uri.startswith("../"):
            return LocalConnector()
        if path.exists():
            return LocalConnector()
        if path.absolute().exists():
            return LocalConnector()
        raise ValueError(f"Invalid URI format: {uri}")

    scheme = uri.split("://")[0]

    # Add scheme if not present
    if scheme not in URI_SCHEME_MAP:
        # Try common mappings
        scheme_map = {
            "hf": HuggingFaceConnector,
            "huggingface": HuggingFaceConnector,
            "kaggle": KaggleConnector,
            "openml": OpenMLConnector,
            "local": LocalConnector,
            "file": LocalConnector,
        }
        if scheme in scheme_map:
            return scheme_map[scheme]()
        raise ValueError(f"Unknown source: {uri}")

    return URI_SCHEME_MAP[scheme]()


def parse_dataset_id(uri: str) -> tuple[str, dict[str, str]]:
    """Parse a URI to extract dataset ID and parameters.

    Args:
        uri: Dataset URI (e.g., 'hf://owner/dataset@v1.0')

    Returns:
        Tuple of (dataset_id, params_dict)
    """
    connector = get_connector(uri)
    return connector.parse_uri(uri)
