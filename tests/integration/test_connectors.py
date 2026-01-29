"""Integration tests for dataset connectors."""

from mldata.connectors import HuggingFaceConnector, KaggleConnector, LocalConnector, OpenMLConnector, get_connector


class TestConnectorInitialization:
    """Tests for connector initialization."""

    def test_huggingface_connector_init(self):
        """Test HuggingFace connector initialization."""
        connector = HuggingFaceConnector(token="fake_token")
        assert connector.token == "fake_token"

    def test_kaggle_connector_init(self):
        """Test Kaggle connector initialization."""
        connector = KaggleConnector(username="test", key="fake_key")
        assert connector.username == "test"

    def test_openml_connector_init(self):
        """Test OpenML connector initialization."""
        connector = OpenMLConnector(api_key="fake_key")
        assert connector.api_key == "fake_key"

    def test_local_connector_init(self):
        """Test Local connector initialization."""
        connector = LocalConnector()
        assert connector.name == "local"


class TestConnectorURIParsing:
    """Tests for URI parsing across connectors."""

    def test_huggingface_uri_basic(self):
        """Parse basic HuggingFace URI."""
        connector = HuggingFaceConnector()
        dataset_id, params = connector.parse_uri("hf://stanfordnlp/imdb")
        assert dataset_id == "stanfordnlp/imdb"
        assert params == {}

    def test_huggingface_uri_with_revision(self):
        """Parse HuggingFace URI with revision."""
        connector = HuggingFaceConnector()
        dataset_id, params = connector.parse_uri("hf://owner/dataset@v1.0.0")
        assert dataset_id == "owner/dataset"
        assert params["revision"] == "v1.0.0"

    def test_huggingface_uri_with_huggingface_scheme(self):
        """Parse HuggingFace URI with huggingface:// scheme."""
        connector = HuggingFaceConnector()
        dataset_id, params = connector.parse_uri("huggingface://owner/dataset")
        assert dataset_id == "owner/dataset"

    def test_kaggle_uri(self):
        """Parse Kaggle URI."""
        connector = KaggleConnector()
        dataset_id, params = connector.parse_uri("kaggle://username/dataset")
        assert dataset_id == "username/dataset"

    def test_openml_uri(self):
        """Parse OpenML URI."""
        connector = OpenMLConnector()
        dataset_id, params = connector.parse_uri("openml://123")
        assert dataset_id == "123"

    def test_openml_uri_with_slash(self):
        """Parse OpenML URI with leading slash."""
        connector = OpenMLConnector()
        dataset_id, params = connector.parse_uri("openml:///456")
        assert dataset_id == "456"

    def test_openml_uri_with_path(self):
        """Parse OpenML URI with path."""
        connector = OpenMLConnector()
        dataset_id, params = connector.parse_uri("openml://789")
        assert dataset_id == "789"


class TestConnectorFactory:
    """Tests for connector factory function."""

    def test_get_connector_huggingface(self):
        """Test connector factory for HuggingFace."""
        connector = get_connector("hf://test/dataset")
        assert isinstance(connector, HuggingFaceConnector)

    def test_get_connector_huggingface_long_scheme(self):
        """Test connector factory for HuggingFace with huggingface://."""
        connector = get_connector("huggingface://owner/dataset")
        assert isinstance(connector, HuggingFaceConnector)

    def test_get_connector_kaggle(self):
        """Test connector factory for Kaggle."""
        connector = get_connector("kaggle://test/dataset")
        assert isinstance(connector, KaggleConnector)

    def test_get_connector_openml(self):
        """Test connector factory for OpenML."""
        connector = get_connector("openml://123")
        assert isinstance(connector, OpenMLConnector)

    def test_get_connector_invalid(self):
        """Test connector factory with invalid URI."""
        try:
            get_connector("invalid://test")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


class TestLocalConnector:
    """Tests for LocalConnector."""

    def test_parse_uri_file_scheme(self):
        """Parse file:// URI."""
        connector = LocalConnector()
        path, params = connector.parse_uri("file:///tmp/data.csv")
        assert path == "/tmp/data.csv"
        assert params == {}

    def test_parse_uri_absolute_path(self):
        """Parse absolute path."""
        connector = LocalConnector()
        path, params = connector.parse_uri("/absolute/path/to/data.csv")
        assert path == "/absolute/path/to/data.csv"

    def test_parse_uri_relative_path(self):
        """Parse relative path."""
        connector = LocalConnector()
        path, params = connector.parse_uri("./data/data.csv")
        assert path == "./data/data.csv"

    def test_parse_uri_glob_pattern(self):
        """Parse glob pattern."""
        connector = LocalConnector()
        path, params = connector.parse_uri("data/*.csv")
        assert path == "data/*.csv"

    def test_authenticate(self):
        """Local connector always returns True for authentication."""
        connector = LocalConnector()
        import asyncio

        result = asyncio.run(connector.authenticate())
        assert result is True

    def test_search_returns_empty(self):
        """Local search always returns empty list."""
        connector = LocalConnector()
        import asyncio

        result = asyncio.run(connector.search("test", limit=10))
        assert result == []


class TestLocalConnectorFactory:
    """Tests for local path handling in connector factory."""

    def test_get_connector_local_file_scheme(self):
        """Test connector factory for local file:// paths."""
        connector = get_connector("file:///tmp/data.csv")
        assert isinstance(connector, LocalConnector)

    def test_get_connector_local_absolute_path(self):
        """Test connector factory for absolute paths."""
        connector = get_connector("/tmp/data.csv")
        assert isinstance(connector, LocalConnector)

    def test_get_connector_local_relative_path(self):
        """Test connector factory for relative paths starting with ./"""
        connector = get_connector("./data/data.csv")
        assert isinstance(connector, LocalConnector)
