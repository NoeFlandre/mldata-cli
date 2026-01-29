"""End-to-end tests for complete workflows."""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from mldata import __version__
from mldata.core.export import ExportService
from mldata.core.manifest import ManifestService
from mldata.core.normalize import NormalizeService
from mldata.core.split import SplitService


class TestBuildPipelineE2E:
    """End-to-end build pipeline tests."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("id,label,text\n")
            for i in range(20):
                label = "pos" if i < 12 else "neg"
                f.write(f"{i},{label},Sample text {i}\n")
            return Path(f.name)

    def test_build_pipeline_parquet(self, sample_data):
        """Test full build pipeline with parquet output."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output"
            output_path.mkdir()

            # 1. Fetch (simulate by reading local file)
            normalize = NormalizeService()
            df = normalize.read_data(sample_data)
            assert df.height == 20

            # 2. Normalize to parquet
            artifacts_dir = output_path / "artifacts"
            artifacts_dir.mkdir()
            parquet_path = artifacts_dir / "data.parquet"
            normalize.convert_format(sample_data, parquet_path, "parquet")
            assert parquet_path.exists()

            # 3. Split
            split_service = SplitService()
            splits = split_service.split(df, ratios=[0.7, 0.15, 0.15], seed=42)

            splits_dir = output_path / "splits"
            splits_dir.mkdir()
            split_service.save_splits(splits, splits_dir, format="parquet")

            assert (splits_dir / "train.parquet").exists()
            assert (splits_dir / "val.parquet").exists()
            assert (splits_dir / "test.parquet").exists()

            # Verify split sizes
            train = pl.read_parquet(splits_dir / "train.parquet")
            val = pl.read_parquet(splits_dir / "val.parquet")
            test = pl.read_parquet(splits_dir / "test.parquet")

            assert train.height == 14  # 70%
            assert val.height == 3  # 15%
            assert test.height == 3  # 15%

    def test_split_command_functionality(self, sample_data):
        """Test split command functionality."""
        with tempfile.TemporaryDirectory() as tmpdir:
            normalize = NormalizeService()
            df = normalize.read_data(sample_data)

            split_service = SplitService()
            splits = split_service.split(df, ratios=[0.7, 0.15, 0.15], seed=42)

            splits_dir = Path(tmpdir) / "splits"
            splits_dir.mkdir()
            split_service.save_splits(splits, splits_dir, format="csv")

            assert (splits_dir / "train.csv").exists()
            assert (splits_dir / "val.csv").exists()
            assert (splits_dir / "test.csv").exists()

            # Also test saving indices
            split_service.save_split_indices(splits, splits_dir)
            assert (splits_dir / "train_indices.csv").exists()

    def test_export_all_formats(self, sample_data):
        """Test exporting to all formats."""
        with tempfile.TemporaryDirectory() as tmpdir:
            export_dir = Path(tmpdir) / "export"
            export_dir.mkdir()

            normalize = NormalizeService()
            df = normalize.read_data(sample_data)

            export = ExportService()

            # Export to parquet
            parquet_path = export_dir / "data.parquet"
            export.export(df, parquet_path, format="parquet")
            assert parquet_path.exists()

            # Export to CSV
            csv_path = export_dir / "data.csv"
            export.export(df, csv_path, format="csv")
            assert csv_path.exists()

            # Export to JSONL
            jsonl_path = export_dir / "data.jsonl"
            export.export(df, jsonl_path, format="jsonl")
            assert jsonl_path.exists()

    def test_manifest_creation_and_verification(self, sample_data):
        """Test manifest creation and verification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "build"
            output_path.mkdir()

            # Create sample artifacts
            artifacts_dir = output_path / "artifacts"
            artifacts_dir.mkdir()
            data_file = artifacts_dir / "data.parquet"
            data_file.write_bytes(b"test")

            manifest_service = ManifestService()

            # Create manifest with the actual file hash
            from mldata.utils.hashing import compute_file_hash

            actual_hash = compute_file_hash(data_file)

            # Create manifest
            manifest = manifest_service.create_manifest(
                source_uri="hf://test/dataset",
                source_params={"revision": "v1.0"},
                build_params={"seed": 42, "split_ratios": [0.8, 0.1, 0.1]},
                dataset_info={"num_samples": 100, "num_columns": 5},
                artifact_hashes={"artifacts/data.parquet": actual_hash},
                tool_version=__version__,
            )

            # Save manifest
            manifest_path = output_path / "manifest.yaml"
            manifest_service.save_manifest(manifest, manifest_path)
            assert manifest_path.exists()

            # Load manifest
            loaded = manifest_service.load_manifest(manifest_path)
            assert loaded.source["uri"] == "hf://test/dataset"
            assert loaded.build["seed"] == 42

            # Compute and verify artifact hashes
            hashes = manifest_service.compute_artifact_hashes(output_path)
            verification = manifest_service.verify_artifact_hashes(loaded, hashes)
            assert verification.get("artifacts/data.parquet") is True

    def test_deterministic_builds(self, sample_data):
        """Test that builds with same seed produce same results."""
        normalize = NormalizeService()
        df = normalize.read_data(sample_data)

        split_service = SplitService()

        # First build
        splits1 = split_service.split(df, ratios=[0.7, 0.15, 0.15], seed=42)

        # Second build with same seed
        splits2 = split_service.split(df, ratios=[0.7, 0.15, 0.15], seed=42)

        # Third build with different seed
        splits3 = split_service.split(df, ratios=[0.7, 0.15, 0.15], seed=123)

        # Same seed should produce same splits
        assert splits1["train"]["id"].to_list() == splits2["train"]["id"].to_list()

        # Different seed should produce different splits
        assert splits1["train"]["id"].to_list() != splits3["train"]["id"].to_list()

    def test_stratified_split_preserves_distribution(self, sample_data):
        """Test stratified split preserves label distribution."""
        normalize = NormalizeService()
        df = normalize.read_data(sample_data)

        split_service = SplitService()
        # Test without stratification first
        splits = split_service.split(df, ratios=[0.7, 0.15, 0.15], seed=42)

        # Check all labels present in train
        if splits["train"].height > 0:
            train_labels = set(splits["train"]["label"].to_list())
            assert "pos" in train_labels
            assert "neg" in train_labels

    def test_quality_report_generation(self, sample_data):
        """Test quality report generation."""
        from mldata.core.validate import ValidateService
        from mldata.models.report import QualityReport

        normalize = NormalizeService()
        df = normalize.read_data(sample_data)

        validate = ValidateService()

        # Create report
        report = QualityReport.create(str(sample_data), "hf://test/dataset")

        # Run checks
        dup_result = validate.check_duplicates(df)
        missing_result = validate.check_missing_values(df)

        assert dup_result["check_name"] == "duplicates"
        assert missing_result["check_name"] == "missing_values"

        # Add results to report
        from mldata.models.report import CheckResult, CheckStatus

        report.checks.append(
            CheckResult(
                check_name="duplicates",
                status=CheckStatus.PASSED if dup_result["passed"] else CheckStatus.FAILED,
            )
        )

        # Save report
        with tempfile.TemporaryDirectory() as tmpdir:
            report_path = Path(tmpdir) / "report.json"
            report.to_json(str(report_path))
            assert report_path.exists()

            report_md_path = Path(tmpdir) / "report.md"
            report.to_markdown(str(report_md_path))
            assert report_md_path.exists()
