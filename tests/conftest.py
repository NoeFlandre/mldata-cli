"""Pytest configuration."""

import pytest
from typer.testing import CliRunner

from mldata.cli.main import app


@pytest.fixture
def runner():
    """CLI runner fixture."""
    return CliRunner()


@pytest.fixture
def cli_app():
    """CLI app fixture."""
    return app
