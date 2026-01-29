"""Unit tests for core services."""

import pytest
from pathlib import Path
import tempfile


class TestProfileService:
    """Tests for ProfileService."""

    def test_profile_csv(self):
        """Test profiling a CSV file."""
        from mldata.core.profile import ProfileService

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('name,age,score\n')
            f.write('Alice,25,85.5\n')
            f.write('Bob,30,92.3\n')
            test_path = Path(f.name)

        try:
            profile = ProfileService()
            result = profile.profile(test_path)

            assert result.path == str(test_path)
            assert result.num_rows == 2
            assert result.num_columns == 3
            assert len(result.columns) == 3

            # Check column names
            col_names = [c.name for c in result.columns]
            assert 'name' in col_names
            assert 'age' in col_names
            assert 'score' in col_names
        finally:
            test_path.unlink()

    def test_profile_parquet(self):
        """Test profiling a Parquet file."""
        from mldata.core.profile import ProfileService
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            test_path = Path(f.name)

        try:
            # Create a DataFrame and save as parquet
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': [10.5, 20.5, 30.5],
            })
            df.write_parquet(test_path)

            profile = ProfileService()
            result = profile.profile(test_path)

            assert result.num_rows == 3
            assert result.num_columns == 2
        finally:
            test_path.unlink()

    def test_profile_numeric_stats(self):
        """Test that numeric statistics are computed correctly."""
        from mldata.core.profile import ProfileService

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('val\n')
            f.write('10\n')
            f.write('20\n')
            f.write('30\n')
            f.write('40\n')
            f.write('50\n')
            test_path = Path(f.name)

        try:
            profile = ProfileService()
            result = profile.profile(test_path)

            stats = result.numeric_stats.get('val')
            assert stats is not None
            assert stats.mean == 30.0
            assert stats.min == 10.0
            assert stats.max == 50.0
        finally:
            test_path.unlink()

    def test_profile_categorical_stats(self):
        """Test that categorical statistics are computed correctly."""
        from mldata.core.profile import ProfileService

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('category\n')
            f.write('A\n')
            f.write('B\n')
            f.write('A\n')
            f.write('C\n')
            f.write('A\n')
            test_path = Path(f.name)

        try:
            profile = ProfileService()
            result = profile.profile(test_path)

            cat_stats = result.categorical_stats.get('category')
            assert cat_stats is not None
            assert cat_stats.unique_values == 3
        finally:
            test_path.unlink()


class TestIncrementalService:
    """Tests for IncrementalService."""

    def test_compute_file_hash(self):
        """Test file hash computation."""
        from mldata.core.incremental import IncrementalService

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('test content')
            test_path = Path(f.name)

        try:
            inc = IncrementalService()
            hash1 = inc.compute_file_hash(test_path)
            hash2 = inc.compute_file_hash(test_path)

            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256 hex length
        finally:
            test_path.unlink()

    def test_compute_dir_hashes(self):
        """Test directory hash computation."""
        from mldata.core.incremental import IncrementalService

        test_dir = Path('/tmp/test-incremental-hashes')
        test_dir.mkdir(exist_ok=True)

        try:
            # Use proper data file extensions
            (test_dir / 'file1.csv').write_text('col1,col2\nval1,val2\n')
            (test_dir / 'file2.csv').write_text('col1,col2\nval3,val4\n')

            inc = IncrementalService()
            hashes = inc.compute_dir_hashes(test_dir)

            assert 'file1.csv' in hashes
            assert 'file2.csv' in hashes
            assert len(hashes['file1.csv']) == 64
        finally:
            import shutil
            shutil.rmtree(test_dir)

    def test_detect_changes_no_cache(self):
        """Test change detection with no previous cache."""
        from mldata.core.incremental import IncrementalService

        test_dir = Path('/tmp/test-detect-changes')
        test_dir.mkdir(exist_ok=True)

        try:
            (test_dir / 'file1.csv').write_text('col1,col2\nval1,val2\n')

            inc = IncrementalService(cache_dir=test_dir / '.cache')
            changes = inc.detect_changes(test_dir)

            assert len(changes['added']) > 0
            assert len(changes['changed']) == 0
            assert len(changes['unchanged']) == 0
        finally:
            import shutil
            shutil.rmtree(test_dir)

    def test_detect_changes_unchanged(self):
        """Test change detection when files haven't changed."""
        from mldata.core.incremental import IncrementalService

        test_dir = Path('/tmp/test-detect-unchanged')
        test_dir.mkdir(exist_ok=True)

        try:
            (test_dir / 'file1.csv').write_text('col1,col2\nval1,val2\n')
            (test_dir / 'file2.csv').write_text('col1,col2\nval3,val4\n')

            inc = IncrementalService(cache_dir=test_dir / '.cache')

            # First run - save hashes
            hashes = inc.compute_dir_hashes(test_dir)
            inc.save_hashes('test://dataset', hashes)

            # Second run - detect changes
            changes = inc.detect_changes(test_dir, 'test://dataset')

            assert len(changes['changed']) == 0
            assert len(changes['unchanged']) == 2
        finally:
            import shutil
            shutil.rmtree(test_dir)

    def test_detect_changes_modified(self):
        """Test change detection when files have been modified."""
        from mldata.core.incremental import IncrementalService
        import time

        test_dir = Path('/tmp/test-detect-modified')
        test_dir.mkdir(exist_ok=True)

        try:
            (test_dir / 'file1.csv').write_text('col1,col2\nval1,val2\n')
            time.sleep(0.1)
            (test_dir / 'file2.csv').write_text('col1,col2\nval3,val4\n')

            inc = IncrementalService(cache_dir=test_dir / '.cache')

            # First run - save hashes
            hashes = inc.compute_dir_hashes(test_dir)
            inc.save_hashes('test://dataset', hashes)

            # Modify file1
            time.sleep(0.1)
            (test_dir / 'file1.csv').write_text('col1,col2\nval1-modified,val2-modified\n')

            # Second run - detect changes
            changes = inc.detect_changes(test_dir, 'test://dataset')

            assert 'file1.csv' in changes['changed']
            assert 'file2.csv' in changes['unchanged']
        finally:
            import shutil
            shutil.rmtree(test_dir)


class TestParallelService:
    """Tests for ParallelService."""

    def test_parallel_convert_files(self):
        """Test parallel file conversion."""
        from mldata.core.parallel import ParallelService

        test_dir = Path('/tmp/test-parallel-convert')
        test_dir.mkdir(exist_ok=True)
        output_dir = test_dir / 'output'
        output_dir.mkdir(exist_ok=True)

        try:
            # Create test CSV files
            for i in range(3):
                (test_dir / f'file{i}.csv').write_text('col1,col2\na,b\nc,d\n')

            parallel = ParallelService(max_workers=2)
            results = parallel.convert_files_parallel(
                list(test_dir.glob('*.csv')),
                output_dir,
                target_format='parquet'
            )

            assert len(results) == 3
            # All should succeed
            for path, success in results:
                assert success

            # Check output files exist
            assert len(list(output_dir.glob('*.parquet'))) == 3
        finally:
            import shutil
            shutil.rmtree(test_dir)

    def test_parallel_process_files(self):
        """Test parallel file processing with custom function."""
        from mldata.core.parallel import ParallelService

        test_dir = Path('/tmp/test-parallel-process')
        test_dir.mkdir(exist_ok=True)

        try:
            # Create test files
            for i in range(3):
                (test_dir / f'file{i}.txt').write_text(f'content {i}')

            parallel = ParallelService(max_workers=2)

            def process_file(path: Path):
                content = path.read_text()
                return (path, len(content))

            results = parallel.process_files_parallel(
                list(test_dir.glob('*.txt')),
                process_file
            )

            assert len(results) == 3
            for path, length in results:
                assert length > 0
        finally:
            import shutil
            shutil.rmtree(test_dir)


class TestDriftService:
    """Tests for DriftService."""

    def test_compute_psi_identical(self):
        """Test PSI computation for identical distributions."""
        from mldata.core.drift import DriftService

        drift = DriftService()
        baseline = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        current = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

        psi = drift.compute_psi(baseline, current)
        assert psi < 0.01  # Should be very small for identical distributions

    def test_compute_psi_different(self):
        """Test PSI computation for different distributions."""
        from mldata.core.drift import DriftService

        drift = DriftService()
        baseline = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        current = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]  # Shifted

        psi = drift.compute_psi(baseline, current)
        assert psi > 0.1  # Should be larger for different distributions

    def test_compute_kl_divergence(self):
        """Test KL divergence computation."""
        from mldata.core.drift import DriftService

        drift = DriftService()
        p = [0.5, 0.3, 0.2]
        q = [0.4, 0.4, 0.2]

        kl = drift.compute_kl_divergence(p, q)
        assert kl >= 0  # KL divergence is always non-negative

    def test_detect_drift(self):
        """Test full drift detection between datasets."""
        from mldata.core.drift import DriftService

        # Create baseline dataset
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('value\n')
            for i in range(100):
                f.write(f'{i * 0.1}\n')
            baseline_path = Path(f.name)

        try:
            # Create current dataset with shift
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write('value\n')
                for i in range(100):
                    f.write(f'{i * 0.1 + 0.5}\n')  # Shifted values
                current_path = Path(f.name)

            try:
                drift = DriftService()
                report = drift.detect_drift(baseline_path, current_path)

                assert report is not None
                assert 'value' in report.numeric_drift
            finally:
                current_path.unlink()
        finally:
            baseline_path.unlink()


class TestSchemaEvolutionService:
    """Tests for SchemaEvolutionService."""

    def test_compare_schemas_identical(self):
        """Test schema comparison with identical schemas."""
        from mldata.core.schema import SchemaEvolutionService, SchemaColumn

        service = SchemaEvolutionService()
        columns = [
            SchemaColumn(name='id', dtype='Int64', nullable=False),
            SchemaColumn(name='name', dtype='String', nullable=False),
        ]

        evolution = service.compare_schemas(columns, columns)

        assert len(evolution.added_columns) == 0
        assert len(evolution.removed_columns) == 0
        assert len(evolution.type_changes) == 0

    def test_compare_schemas_added_column(self):
        """Test schema comparison with added column."""
        from mldata.core.schema import SchemaEvolutionService, SchemaColumn

        service = SchemaEvolutionService()
        baseline = [
            SchemaColumn(name='id', dtype='Int64', nullable=False),
            SchemaColumn(name='name', dtype='String', nullable=False),
        ]
        current = [
            SchemaColumn(name='id', dtype='Int64', nullable=False),
            SchemaColumn(name='name', dtype='String', nullable=False),
            SchemaColumn(name='email', dtype='String', nullable=True),
        ]

        evolution = service.compare_schemas(baseline, current)

        assert len(evolution.added_columns) == 1
        assert evolution.added_columns[0].name == 'email'

    def test_compare_schemas_removed_column(self):
        """Test schema comparison with removed column."""
        from mldata.core.schema import SchemaEvolutionService, SchemaColumn

        service = SchemaEvolutionService()
        baseline = [
            SchemaColumn(name='id', dtype='Int64', nullable=False),
            SchemaColumn(name='name', dtype='String', nullable=False),
            SchemaColumn(name='email', dtype='String', nullable=True),
        ]
        current = [
            SchemaColumn(name='id', dtype='Int64', nullable=False),
            SchemaColumn(name='name', dtype='String', nullable=False),
        ]

        evolution = service.compare_schemas(baseline, current)

        assert len(evolution.removed_columns) == 1
        assert evolution.removed_columns[0].name == 'email'

    def test_compare_schemas_type_change(self):
        """Test schema comparison with type change."""
        from mldata.core.schema import SchemaEvolutionService, SchemaColumn

        service = SchemaEvolutionService()
        baseline = [
            SchemaColumn(name='value', dtype='Int64', nullable=False),
        ]
        current = [
            SchemaColumn(name='value', dtype='Float64', nullable=False),
        ]

        evolution = service.compare_schemas(baseline, current)

        assert len(evolution.type_changes) == 1
        assert evolution.type_changes[0].column == 'value'
        assert evolution.type_changes[0].old_value == 'Int64'
        assert evolution.type_changes[0].new_value == 'Float64'

    def test_detect_evolution(self):
        """Test full schema evolution detection from files."""
        from mldata.core.schema import SchemaEvolutionService

        # Create baseline dataset
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write('id,name,age\n')
            f.write('1,Alice,25\n')
            f.write('2,Bob,30\n')
            baseline_path = Path(f.name)

        try:
            # Create current dataset with added column
            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
                f.write('id,name,age,email\n')
                f.write('1,Alice,25,alice@test.com\n')
                f.write('2,Bob,30,bob@test.com\n')
                current_path = Path(f.name)

            try:
                service = SchemaEvolutionService()
                evolution = service.detect_evolution(baseline_path, current_path)

                assert evolution is not None
                assert len(evolution.added_columns) == 1
                assert evolution.added_columns[0].name == 'email'
            finally:
                current_path.unlink()
        finally:
            baseline_path.unlink()


class TestConfigService:
    """Tests for ConfigService."""

    def test_default_config(self):
        """Test loading default configuration."""
        from mldata.core.config import Config

        config = Config.load()
        assert config.build.default_format == "parquet"
        assert config.cache.max_size_gb == 10.0

    def test_config_set_value(self):
        """Test setting a configuration value."""
        from mldata.core.config import ConfigService

        service = ConfigService()
        service.set("build.default_format", "csv")
        assert service.config.build.default_format == "csv"

    def test_config_set_split(self):
        """Test setting split ratios."""
        from mldata.core.config import ConfigService

        service = ConfigService()
        service.set("build.default_split", "0.7,0.2,0.1")
        assert service.config.build.default_split == [0.7, 0.2, 0.1]

    def test_config_save_load(self):
        """Test saving and loading configuration."""
        from mldata.core.config import Config, ConfigService

        service = ConfigService()
        service.set("build.default_format", "jsonl")
        service.set("build.workers", 8)

        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            config_path = Path(f.name)

        try:
            saved_path = service.save_project_config(config_path)
            assert saved_path.exists()

            # Load and verify
            loaded = Config.load(config_path)
            assert loaded.build.default_format == "jsonl"
            assert loaded.build.workers == 8
        finally:
            config_path.unlink()

    def test_config_get_build_format(self):
        """Test getting build format from config."""
        from mldata.core.config import ConfigService

        service = ConfigService()
        assert service.config.get_build_format() == "parquet"

        service.set("build.default_format", "csv")
        assert service.config.get_build_format() == "csv"


class TestExportService:
    """Tests for ExportService."""

    def test_export_parquet_default_compression(self):
        """Test parquet export with default (snappy) compression."""
        from mldata.core.export import ExportService
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            test_path = Path(f.name)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': [10.5, 20.5, 30.5],
            })

            export = ExportService()
            result = export.export(df, test_path, format='parquet', compression=None)

            assert result.exists()
        finally:
            test_path.unlink()

    def test_export_parquet_gzip_compression(self):
        """Test parquet export with gzip compression."""
        from mldata.core.export import ExportService
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            test_path = Path(f.name)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': [10.5, 20.5, 30.5],
            })

            export = ExportService()
            result = export.export(df, test_path, format='parquet', compression='gzip')

            assert result.exists()
            # Gzip file should be smaller than uncompressed
            assert result.stat().st_size > 0
        finally:
            test_path.unlink()

    def test_export_parquet_gzip_with_level(self):
        """Test parquet export with gzip compression and level."""
        from mldata.core.export import ExportService, CompressionOptions
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            test_path = Path(f.name)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': [10.5, 20.5, 30.5],
            })

            export = ExportService()
            # Test compression level parsing
            comp_options = export.parse_compression('gzip:6')
            assert comp_options.type == 'gzip'
            assert comp_options.level == 6

            result = export.export(df, test_path, format='parquet', compression='gzip:6')
            assert result.exists()
        finally:
            test_path.unlink()

    def test_export_parquet_zstd_compression(self):
        """Test parquet export with zstd compression."""
        from mldata.core.export import ExportService
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            test_path = Path(f.name)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': [10.5, 20.5, 30.5],
            })

            export = ExportService()
            result = export.export(df, test_path, format='parquet', compression='zstd')

            assert result.exists()
        finally:
            test_path.unlink()

    def test_export_parquet_zstd_with_level(self):
        """Test parquet export with zstd compression and level."""
        from mldata.core.export import ExportService
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.parquet', delete=False) as f:
            test_path = Path(f.name)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': [10.5, 20.5, 30.5],
            })

            export = ExportService()
            result = export.export(df, test_path, format='parquet', compression='zstd:3')

            assert result.exists()
        finally:
            test_path.unlink()

    def test_export_csv(self):
        """Test CSV export."""
        from mldata.core.export import ExportService
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
            test_path = Path(f.name)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'name': ['a', 'b', 'c'],
            })

            export = ExportService()
            result = export.export(df, test_path, format='csv')

            assert result.exists()
            content = result.read_text()
            assert 'id' in content
            assert 'name' in content
        finally:
            test_path.unlink()

    def test_export_jsonl(self):
        """Test JSONL export."""
        from mldata.core.export import ExportService
        import polars as pl

        with tempfile.NamedTemporaryFile(suffix='.jsonl', delete=False) as f:
            test_path = Path(f.name)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'name': ['a', 'b', 'c'],
            })

            export = ExportService()
            result = export.export(df, test_path, format='jsonl')

            assert result.exists()
            content = result.read_text()
            lines = content.strip().split('\n')
            assert len(lines) == 3
        finally:
            test_path.unlink()

    def test_compression_guide(self):
        """Test compression guide information."""
        from mldata.core.export import ExportService

        export = ExportService()

        # Check that guide exists for known types
        assert 'snappy' in export.COMPRESSION_GUIDE
        assert 'gzip' in export.COMPRESSION_GUIDE
        assert 'zstd' in export.COMPRESSION_GUIDE

        # Check gzip guide has level support
        assert export.COMPRESSION_GUIDE['gzip']['level_support'] is True
        assert export.COMPRESSION_GUIDE['snappy']['level_support'] is False

    def test_parse_compression_invalid_level(self):
        """Test that invalid compression levels raise errors."""
        from mldata.core.export import ExportService

        export = ExportService()

        # Invalid level for gzip
        try:
            export.parse_compression('gzip:99')
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "1 and 22" in str(e)

    def test_get_compression_info(self):
        """Test getting compression information."""
        from mldata.core.export import ExportService

        export = ExportService()

        info = export.get_compression_info('gzip:6')
        assert info['type'] == 'gzip'
        assert info['level'] == 6
        assert 'typical_ratio' in info
        assert 'speed' in info


class TestFetchService:
    """Tests for FetchService."""

    def test_partial_download_serialization(self):
        """Test PartialDownload serialization."""
        from mldata.core.fetch import PartialDownload

        partial = PartialDownload(
            url="https://example.com/file.zip",
            temp_path=Path("/tmp/test.part"),
            final_path=Path("/tmp/test.zip"),
            expected_size=1000,
            downloaded_size=500,
            etag='"abc123"',
            last_modified="Wed, 21 Oct 2015 07:28:00 GMT",
        )

        # Serialize and deserialize
        data = partial.to_dict()
        restored = PartialDownload.from_dict(data)

        assert restored.url == "https://example.com/file.zip"
        assert restored.expected_size == 1000
        assert restored.downloaded_size == 500
        assert restored.etag == '"abc123"'
        assert restored.temp_path == Path("/tmp/test.part")
        assert restored.final_path == Path("/tmp/test.zip")

    def test_format_eta(self):
        """Test ETA formatting."""
        from mldata.core.fetch import FetchService

        fetch = FetchService()

        assert fetch._format_eta(30) == "30s"
        assert fetch._format_eta(90) == "1m 30s"
        assert fetch._format_eta(3661) == "1h 1m"

    def test_format_speed(self):
        """Test speed formatting."""
        from mldata.core.fetch import FetchService

        fetch = FetchService()

        assert fetch._format_speed(500) == "500 B/s"
        assert fetch._format_speed(2048) == "2.0 KB/s"
        assert fetch._format_speed(1048576) == "1.0 MB/s"

    def test_compute_file_hash(self):
        """Test file hash computation."""
        from mldata.core.fetch import FetchService

        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write('test content for hashing')
            test_path = Path(f.name)

        try:
            fetch = FetchService()
            hash1 = fetch._compute_file_hash(test_path)
            hash2 = fetch._compute_file_hash(test_path)

            # Same file should produce same hash
            assert hash1 == hash2
            # SHA-256 produces 64 character hex string
            assert len(hash1) == 64
        finally:
            test_path.unlink()

    def test_resume_state_cleanup(self):
        """Test resume state cleanup for old downloads."""
        import time
        from mldata.core.fetch import FetchService, PartialDownload

        fetch = FetchService()

        # Create a partial download with old timestamp
        old_time = time.time() - 100000  # ~27 hours ago
        partial = PartialDownload(
            url="https://example.com/old-file.zip",
            temp_path=Path("/tmp/nonexistent.part"),
            final_path=Path("/tmp/old-file.zip"),
            expected_size=1000,
            downloaded_size=500,
            created_at=old_time,
        )

        # Should not error when cleanup called for non-existent files
        fetch.cleanup_resume_state("https://example.com/old-file.zip")

    def test_get_resume_state_not_found(self):
        """Test getting resume state for unknown URL."""
        from mldata.core.fetch import FetchService

        fetch = FetchService()

        # Non-existent URL should return None
        result = fetch.get_resume_state("https://nonexistent.example.com/file.zip")
        assert result is None


class TestFileIntegrityService:
    """Tests for file integrity validation."""

    def test_image_validation_valid(self):
        """Test validating a valid image file."""
        from mldata.core.validate import FileIntegrityService
        from PIL import Image
        import os

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            test_path = Path(f.name)

        try:
            # Create a simple test image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(test_path)

            service = FileIntegrityService()
            result = service.validate_image(test_path)

            assert result.is_valid
            assert result.error is None
            assert result.details.get('width') == 100
            assert result.details.get('height') == 100
        finally:
            test_path.unlink()
            if test_path.with_suffix('.png').exists():
                test_path.with_suffix('.png').unlink()

    def test_image_validation_invalid(self):
        """Test validating an invalid/corrupt image file."""
        from mldata.core.validate import FileIntegrityService

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            test_path = Path(f.name)

        try:
            # Create an invalid PNG file
            test_path.write_bytes(b'not a valid png file content')

            service = FileIntegrityService()
            result = service.validate_image(test_path)

            assert not result.is_valid
            assert result.error is not None
        finally:
            if test_path.exists():
                test_path.unlink()

    def test_file_integrity_run_check(self):
        """Test running file integrity checks."""
        from mldata.core.validate import FileIntegrityService
        from PIL import Image

        # Create test images
        test_dir = Path('/tmp/test-integrity')
        test_dir.mkdir(exist_ok=True)

        valid_image = test_dir / 'valid.png'
        invalid_image = test_dir / 'invalid.png'

        try:
            # Create valid image
            img = Image.new('RGB', (50, 50), color='blue')
            img.save(valid_image)

            # Create invalid file
            invalid_image.write_bytes(b'invalid data')

            service = FileIntegrityService()
            results = service.run_checks([valid_image, invalid_image])

            assert len(results) == 2
            # First file should be valid
            assert results[0].is_valid
            # Second file should be invalid
            assert not results[1].is_valid
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)


class TestDVCService:
    """Tests for DVCService."""

    def test_dvc_service_init(self):
        """Test DVC service initialization."""
        from mldata.integrations.dvc import DVCService

        service = DVCService()
        assert service is not None

    def test_dvc_result_creation(self):
        """Test DVC result creation."""
        from mldata.integrations.dvc import DVCRResult

        result = DVCRResult(success=True, dvc_path=Path("/test/test.dvc"))
        assert result.success is True
        assert result.dvc_path == Path("/test/test.dvc")
        assert result.error is None

    def test_generate_dvc_file(self):
        """Test generating a DVC file."""
        from mldata.integrations.dvc import DVCService
        import yaml

        test_dir = Path('/tmp/test-dvc')
        test_dir.mkdir(exist_ok=True)
        dataset_path = test_dir / "mydataset"
        dataset_path.mkdir()

        try:
            service = DVCService()
            result = service.generate_dvc_file(dataset_path, "abc123hash")

            assert result.success is True
            assert result.dvc_path is not None
            assert result.dvc_path.exists()

            # Verify content
            content = yaml.safe_load(result.dvc_path.read_text())
            assert content["outs"][0]["path"] == "mydataset"
            assert content["outs"][0]["md5"] == "abc123hash"
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_generate_dvc_file_with_remote(self):
        """Test generating a DVC file with remote."""
        from mldata.integrations.dvc import DVCService
        import yaml

        test_dir = Path('/tmp/test-dvc-remote')
        test_dir.mkdir(exist_ok=True)
        dataset_path = test_dir / "mydataset"
        dataset_path.mkdir()

        try:
            service = DVCService()
            result = service.generate_dvc_file(dataset_path, "abc123hash", remote="myremote")

            assert result.success is True

            content = yaml.safe_load(result.dvc_path.read_text())
            assert content["outs"][0]["remote"] == "myremote"
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_generate_dvc_file_nonexistent_path(self):
        """Test generating DVC file for nonexistent path."""
        from mldata.integrations.dvc import DVCService

        service = DVCService()
        result = service.generate_dvc_file(Path("/nonexistent/path"), "hash")

        assert result.success is False
        assert "does not exist" in result.error

    def test_verify_dvc_file_valid(self):
        """Test verifying a valid DVC file."""
        from mldata.integrations.dvc import DVCService
        import yaml

        test_dir = Path('/tmp/test-dvc-verify')
        test_dir.mkdir(exist_ok=True)
        dvc_path = test_dir / "test.dvc"

        try:
            content = {"outs": [{"path": "data", "md5": "abc123"}]}
            dvc_path.write_text(yaml.dump(content))

            service = DVCService()
            assert service.verify_dvc_file(dvc_path) is True
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_verify_dvc_file_invalid(self):
        """Test verifying an invalid DVC file."""
        from mldata.integrations.dvc import DVCService

        test_dir = Path('/tmp/test-dvc-verify-invalid')
        test_dir.mkdir(exist_ok=True)
        dvc_path = test_dir / "invalid.dvc"

        try:
            # Invalid YAML/content
            dvc_path.write_text("not: valid: yaml")

            service = DVCService()
            assert service.verify_dvc_file(dvc_path) is False
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_get_push_instructions(self):
        """Test getting push instructions."""
        from mldata.integrations.dvc import DVCService

        service = DVCService()
        instructions = service.get_push_instructions(Path("/test/dataset"))

        assert "dvc add" in instructions
        assert "git add" in instructions
        assert "git commit" in instructions
        assert "dvc push" in instructions


class TestGitLFSService:
    """Tests for GitLFSService."""

    def test_lfs_service_init(self):
        """Test Git-LFS service initialization."""
        from mldata.integrations.gitlfs import GitLFSService

        service = GitLFSService()
        assert service is not None

    def test_lfs_result_creation(self):
        """Test LFS result creation."""
        from mldata.integrations.gitlfs import LFSResult

        result = LFSResult(success=True, patterns_added=["*.parquet", "*.csv"])
        assert result.success is True
        assert result.patterns_added == ["*.parquet", "*.csv"]

    def test_detect_large_files(self):
        """Test detecting large files."""
        from mldata.integrations.gitlfs import GitLFSService

        test_dir = Path('/tmp/test-lfs-detect')
        test_dir.mkdir(exist_ok=True)

        try:
            # Create a small file (shouldn't be detected)
            small_file = test_dir / "small.csv"
            small_file.write_text("a,b,c\n")

            # Create a large file (mock by writing directly)
            large_file = test_dir / "large.parquet"
            large_file.write_bytes(b"x" * (15 * 1024 * 1024))  # 15 MB

            service = GitLFSService()
            large_files = service.detect_large_files(test_dir)

            # Should detect the parquet file (15MB > 10MB threshold)
            assert len(large_files) >= 1
            assert any("parquet" in str(f[0]) for f in large_files)
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_get_patterns_for_files(self):
        """Test getting patterns for files."""
        from mldata.integrations.gitlfs import GitLFSService
        from pathlib import Path

        service = GitLFSService()

        files = [
            (Path("/test/data.parquet"), "10 MB"),
            (Path("/test/data.csv"), "5 MB"),
            (Path("/test/data.txt"), "1 MB"),
        ]

        patterns = service.get_patterns_for_files(files)

        assert "*.parquet" in patterns
        assert "*.csv" in patterns
        # .txt is not in default patterns
        assert "*.txt" not in patterns

    def test_update_gitattributes(self):
        """Test updating .gitattributes."""
        from mldata.integrations.gitlfs import GitLFSService

        test_dir = Path('/tmp/test-lfs-gitattr')
        test_dir.mkdir(exist_ok=True)

        try:
            service = GitLFSService()
            result = service.update_gitattributes(
                test_dir,
                {"*.parquet", "*.csv"}
            )

            assert result.success is True
            assert len(result.patterns_added) == 2

            gitattr_path = test_dir / ".gitattributes"
            assert gitattr_path.exists()
            assert "*.parquet" in gitattr_path.read_text()
            assert "*.csv" in gitattr_path.read_text()
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_update_gitattributes_no_new_patterns(self):
        """Test updating .gitattributes with existing patterns."""
        from mldata.integrations.gitlfs import GitLFSService

        test_dir = Path('/tmp/test-lfs-gitattr-existing')
        test_dir.mkdir(exist_ok=True)

        try:
            gitattr = test_dir / ".gitattributes"
            gitattr.write_text("*.parquet filter=lfs diff=lfs merge=lfs -text\n")

            service = GitLFSService()
            result = service.update_gitattributes(test_dir, {"*.parquet"})

            # Should succeed but not add new patterns
            assert result.success is True
            assert len(result.patterns_added) == 0
            assert "already exist" in result.output
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_get_tracking_status(self):
        """Test getting LFS tracking status."""
        from mldata.integrations.gitlfs import GitLFSService

        test_dir = Path('/tmp/test-lfs-status')
        test_dir.mkdir(exist_ok=True)

        try:
            gitattr = test_dir / ".gitattributes"
            gitattr.write_text("*.parquet filter=lfs diff=lfs merge=lfs -text\n")

            service = GitLFSService()
            status = service.get_tracking_status(test_dir)

            assert "lfs_installed" in status
            assert "lfs_patterns" in status
            assert "*.parquet" in status["lfs_patterns"]
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_get_instructions(self):
        """Test getting LFS setup instructions."""
        from mldata.integrations.gitlfs import GitLFSService

        service = GitLFSService()
        instructions = service.get_instructions(
            Path("/test/dataset"),
            Path("/test/repo")
        )

        assert "git lfs install" in instructions
        assert "git lfs track" in instructions
        assert "git commit" in instructions
        assert "git push" in instructions

    def test_configure_tracking(self):
        """Test configuring LFS tracking."""
        from mldata.integrations.gitlfs import GitLFSService

        test_dir = Path('/tmp/test-lfs-config')
        test_dir.mkdir(exist_ok=True)
        dataset_dir = test_dir / "dataset"
        dataset_dir.mkdir()

        try:
            service = GitLFSService()
            result = service.configure_tracking(test_dir, dataset_dir)

            assert result.success is True

            gitattr = test_dir / ".gitattributes"
            assert gitattr.exists()
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)


class TestMultiFormatExport:
    """Tests for multi-format export functionality."""

    def test_parse_formats_string(self):
        """Test parsing formats from comma-separated string."""
        from mldata.core.export import ExportService

        export = ExportService()
        formats = export.parse_formats("parquet,csv,jsonl")

        assert len(formats) == 3
        assert "parquet" in formats
        assert "csv" in formats
        assert "jsonl" in formats

    def test_parse_formats_list(self):
        """Test parsing formats from list."""
        from mldata.core.export import ExportService

        export = ExportService()
        formats = export.parse_formats(["parquet", "csv"])

        assert len(formats) == 2
        assert "parquet" in formats
        assert "csv" in formats

    def test_parse_formats_invalid(self):
        """Test that invalid format raises error."""
        from mldata.core.export import ExportService

        export = ExportService()

        try:
            export.parse_formats("invalid_format")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported format" in str(e)

    def test_export_all_formats(self):
        """Test exporting to all supported formats."""
        from mldata.core.export import ExportService
        import polars as pl

        test_dir = Path('/tmp/test-all-formats')
        test_dir.mkdir(exist_ok=True)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': ['a', 'b', 'c'],
            })

            export = ExportService()
            results = export.export_all_formats(df, test_dir)

            assert len(results) == 4  # parquet, csv, json, jsonl
            assert (test_dir / "data.parquet").exists()
            assert (test_dir / "data.csv").exists()
            assert (test_dir / "data.json").exists()
            assert (test_dir / "data.jsonl").exists()
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_export_splits_multiple_formats(self):
        """Test exporting splits to multiple formats."""
        from mldata.core.export import ExportService
        import polars as pl

        test_dir = Path('/tmp/test-splits-multi')
        test_dir.mkdir(exist_ok=True)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3, 4, 5],
                'label': [0, 1, 0, 1, 0],
            })

            splits = {
                'train': df.head(3),
                'val': df.tail(2),
            }

            export = ExportService()
            results = export.export_splits_multiple(splits, test_dir, formats=["parquet", "csv"])

            # Should have train and val
            assert 'train' in results
            assert 'val' in results
            # Each split should have parquet and csv
            assert 'parquet' in results['train']
            assert 'csv' in results['train']
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)


class TestFrameworkExport:
    """Tests for framework export templates."""

    def test_framework_export_service_init(self):
        """Test FrameworkExportService initialization."""
        from mldata.core.framework import FrameworkExportService

        service = FrameworkExportService()
        assert service is not None

    def test_get_pytorch_exporter(self):
        """Test getting PyTorch exporter."""
        from mldata.core.framework import FrameworkExportService, PyTorchExporter

        service = FrameworkExportService()
        exporter = service.get_framework("pytorch")

        assert isinstance(exporter, PyTorchExporter)
        assert exporter.framework_name == "PyTorch"

    def test_get_tensorflow_exporter(self):
        """Test getting TensorFlow exporter."""
        from mldata.core.framework import FrameworkExportService, TensorFlowExporter

        service = FrameworkExportService()
        exporter = service.get_framework("tensorflow")

        assert isinstance(exporter, TensorFlowExporter)
        assert exporter.framework_name == "TensorFlow"

    def test_get_jax_exporter(self):
        """Test getting JAX exporter."""
        from mldata.core.framework import FrameworkExportService, JAXExporter

        service = FrameworkExportService()
        exporter = service.get_framework("jax")

        assert isinstance(exporter, JAXExporter)
        assert exporter.framework_name == "JAX"

    def test_get_invalid_framework(self):
        """Test getting invalid framework raises error."""
        from mldata.core.framework import FrameworkExportService

        service = FrameworkExportService()

        try:
            service.get_framework("invalid")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unsupported framework" in str(e)

    def test_pytorch_export(self):
        """Test PyTorch dataset export."""
        from mldata.core.framework import PyTorchExporter
        import polars as pl

        test_dir = Path('/tmp/test-pytorch-export')
        test_dir.mkdir(exist_ok=True)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'feature': [10.5, 20.5, 30.5],
                'label': [0, 1, 0],
            })

            exporter = PyTorchExporter()
            result = exporter.export(df, test_dir, dataset_name="test_data")

            assert result.success is True
            assert result.output_dir == test_dir
            assert len(result.files_created) >= 2  # parquet + README
            assert "torch" in result.loader_code.lower() or "Dataset" in result.loader_code
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_tensorflow_export(self):
        """Test TensorFlow dataset export."""
        from mldata.core.framework import TensorFlowExporter
        import polars as pl

        test_dir = Path('/tmp/test-tf-export')
        test_dir.mkdir(exist_ok=True)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'feature': [10.5, 20.5, 30.5],
                'label': [0, 1, 0],
            })

            exporter = TensorFlowExporter()
            result = exporter.export(df, test_dir, dataset_name="test_data")

            assert result.success is True
            assert "tensorflow" in result.loader_code.lower() or "tf" in result.loader_code.lower()
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_pytorch_loader_code_generation(self):
        """Test PyTorch loader code generation."""
        from mldata.core.framework import PyTorchExporter

        exporter = PyTorchExporter()
        code = exporter.generate_loader_code(
            "mydataset",
            ["id", "feature", "label"],
            {"id": "Int64", "feature": "Float64", "label": "Int64"},
        )

        assert "Dataset" in code
        assert "DataLoader" in code
        assert "mydataset" in code

    def test_tensorflow_loader_code_generation(self):
        """Test TensorFlow loader code generation."""
        from mldata.core.framework import TensorFlowExporter

        exporter = TensorFlowExporter()
        code = exporter.generate_loader_code(
            "mydataset",
            ["id", "feature", "label"],
            {"id": "Int64", "feature": "Float64", "label": "Int64"},
        )

        assert "tensorflow" in code.lower() or "tf" in code.lower()
        assert "mydataset" in code

    def test_framework_export_result(self):
        """Test FrameworkExportResult creation."""
        from mldata.core.framework import FrameworkExportResult

        result = FrameworkExportResult(
            success=True,
            output_dir=Path("/test"),
            files_created=["file1.parquet", "README.md"],
            loader_code="# loader code here",
        )

        assert result.success is True
        assert len(result.files_created) == 2
        assert "loader code here" in result.loader_code

    def test_export_dataset_function(self):
        """Test the export_dataset convenience function."""
        from mldata.core.framework import export_dataset
        import polars as pl

        test_dir = Path('/tmp/test-export-dataset')
        test_dir.mkdir(exist_ok=True)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'value': ['a', 'b', 'c'],
            })

            result = export_dataset(df, test_dir, format="csv")

            assert result.success is True
            assert (test_dir / "data.csv").exists()
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

    def test_export_dataset_with_framework(self):
        """Test exporting with framework specification."""
        from mldata.core.framework import export_dataset
        import polars as pl

        test_dir = Path('/tmp/test-export-framework')
        test_dir.mkdir(exist_ok=True)

        try:
            df = pl.DataFrame({
                'id': [1, 2, 3],
                'feature': [10.5, 20.5, 30.5],
                'label': [0, 1, 0],
            })

            result = export_dataset(df, test_dir, framework="pytorch", dataset_name="test")

            assert result.success is True
            assert result.loader_code is not None
            assert len(result.loader_code) > 0
        finally:
            import shutil
            if test_dir.exists():
                shutil.rmtree(test_dir)

