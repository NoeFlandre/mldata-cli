"""Unit tests for CLI."""

import pytest
from typer.testing import CliRunner


class TestCLIVersion:
    """Tests for CLI version command."""

    def test_version(self, runner):
        """Test version command output."""
        from mldata.cli.main import app

        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "mldata-cli" in result.output


class TestCLIAuth:
    """Tests for auth commands."""

    def test_auth_status(self, runner):
        """Test auth status command."""
        from mldata.cli.main import app

        result = runner.invoke(app, ["auth", "status"])

        # Should show status for each source
        assert result.exit_code == 0
        assert "huggingface" in result.output
        assert "kaggle" in result.output
        assert "openml" in result.output


class TestCLIDoctor:
    """Tests for doctor command."""

    def test_doctor(self, runner):
        """Test doctor command output."""
        from mldata.cli.main import app

        result = runner.invoke(app, ["doctor"])

        assert result.exit_code == 0
        assert "mldata-cli" in result.output
        assert "Authentication" in result.output
        assert "Cache" in result.output
