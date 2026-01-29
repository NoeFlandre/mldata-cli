"""Unit tests for models."""


class TestDatasetModels:
    """Tests for dataset models."""

    def test_search_result_uri(self):
        """Test SearchResult URI property."""
        from mldata.models.dataset import DatasetSource, SearchResult

        result = SearchResult(
            source=DatasetSource.HUGGINGFACE,
            dataset_id="stanfordnlp/imdb",
            name="imdb",
        )

        assert result.uri == "hf://stanfordnlp/imdb"

    def test_dataset_metadata_uri(self):
        """Test DatasetMetadata URI property."""
        from mldata.models.dataset import DatasetMetadata, DatasetSource

        metadata = DatasetMetadata(
            source=DatasetSource.HUGGINGFACE,
            dataset_id="stanfordnlp/imdb",
            name="imdb",
        )

        assert metadata.uri == "hf://stanfordnlp/imdb"


class TestManifestModels:
    """Tests for manifest models."""

    def test_manifest_create(self):
        """Test creating a manifest."""
        from mldata.models.manifest import Manifest

        manifest = Manifest.create(
            source_uri="hf://owner/dataset",
            source_params={"revision": "main"},
            build_params={"seed": 42},
            dataset_info={"name": "dataset", "num_samples": 1000},
            artifact_hashes={"train": "sha256:abc123"},
            tool_version="0.1.0",
            python_version="3.10.0",
        )

        assert manifest.mldata_version == "0.1.0"
        assert manifest.source["uri"] == "hf://owner/dataset"
        assert manifest.build["seed"] == 42
        assert manifest.provenance["artifact_hashes"]["train"] == "sha256:abc123"

    def test_manifest_to_yaml(self, tmp_path):
        """Test saving manifest to YAML."""
        from mldata.models.manifest import Manifest

        manifest = Manifest.create(
            source_uri="hf://owner/dataset",
            source_params={},
            build_params={},
            dataset_info={},
            artifact_hashes={},
            tool_version="0.1.0",
            python_version="3.10.0",
        )

        manifest_path = tmp_path / "manifest.yaml"
        manifest.to_yaml(manifest_path)

        assert manifest_path.exists()


class TestReportModels:
    """Tests for quality report models."""

    def test_quality_report_create(self):
        """Test creating a quality report."""
        from mldata.models.report import QualityReport

        report = QualityReport.create(
            dataset_path="/path/to/dataset",
            dataset_uri="hf://owner/dataset",
        )

        assert report.dataset_path == "/path/to/dataset"
        assert report.dataset_uri == "hf://owner/dataset"
        assert report.generated_at is not None


class TestConfigModels:
    """Tests for configuration models."""

    def test_default_config(self):
        """Test default configuration values."""
        from mldata.models.config import MldataConfig

        config = MldataConfig()

        assert config.version == 1
        assert config.defaults.format == "parquet"
        assert config.defaults.split_ratios == [0.8, 0.1, 0.1]
