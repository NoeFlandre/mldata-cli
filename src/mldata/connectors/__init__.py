"""Connectors module."""

from mldata.connectors.base import BaseConnector
from mldata.connectors.huggingface import HuggingFaceConnector
from mldata.connectors.kaggle import KaggleConnector
from mldata.connectors.local import LocalConnector
from mldata.connectors.openml import OpenMLConnector
from mldata.connectors.registry import CONNECTORS, get_connector

__all__ = [
    "BaseConnector",
    "HuggingFaceConnector",
    "KaggleConnector",
    "OpenMLConnector",
    "LocalConnector",
    "get_connector",
    "CONNECTORS",
]
