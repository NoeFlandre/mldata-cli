"""Main CLI application using Typer."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from mldata import __version__
from mldata.utils.auth import check_credentials, get_credentials, save_credentials, clear_credentials

app = typer.Typer(
    name="mldata",
    help="Unified CLI for ML dataset acquisition and preparation",
    add_completion=False,
    no_args_is_help=True,
    pretty_exceptions_short=True,
    pretty_exceptions_show_locals=False,
)
auth_app = typer.Typer(help="Manage authentication credentials")
console = Console()


# =============================================================================
# VERSION
# =============================================================================

@app.command("version")
def version_cmd() -> None:
    """Show version information."""
    console.print(f"[bold]mldata-cli[/] version [green]{__version__}[/]")


# =============================================================================
# SEARCH
# =============================================================================

@app.command("search")
def search_cmd(
    query: str = typer.Argument(..., help="Search query"),
    source: Optional[str] = typer.Option(None, "-s", "--source", help="Filter by source (hf, kaggle, openml)"),
    modality: Optional[str] = typer.Option(None, "-m", "--modality", help="Filter by modality (text, image, audio, tabular)"),
    task: Optional[str] = typer.Option(None, "-t", "--task", help="Filter by task (classification, regression, generation)"),
    license: Optional[str] = typer.Option(None, "-l", "--license", help="Filter by license"),
    min_size: Optional[str] = typer.Option(None, "--min-size", help="Minimum size (e.g., 10MB)"),
    max_size: Optional[str] = typer.Option(None, "--max-size", help="Maximum size (e.g., 1GB)"),
    limit: int = typer.Option(20, "-n", "--limit", help="Maximum results"),
) -> None:
    """Search for datasets across sources."""
    import asyncio

    from mldata.connectors import HuggingFaceConnector, KaggleConnector, OpenMLConnector

    async def _search():
        results = []

        # Search all sources or specific one
        if source is None or source in ("hf", "huggingface"):
            hf_connector = HuggingFaceConnector()
            try:
                hf_results = await hf_connector.search(query, limit=limit, modality=modality, task=task)
                results.extend(hf_results)
            except Exception as e:
                console.print(f"[yellow]HF search failed: {e}[/]")

        if source is None or source == "kaggle":
            try:
                kg_connector = KaggleConnector()
                # Check if credentials are available before trying to search
                if kg_connector.username and kg_connector.key:
                    kg_results = await kg_connector.search(query, limit=limit, modality=modality, task=task)
                    results.extend(kg_results)
                # Skip silently if not configured
            except ImportError:
                # Kaggle package not installed
                pass
            except ValueError as e:
                # Kaggle not configured - skip silently
                pass
            except Exception as e:
                console.print(f"[yellow]Kaggle search failed: {e}[/]")

        if source is None or source == "openml":
            om_connector = OpenMLConnector()
            try:
                om_results = await om_connector.search(query, limit=limit, modality=modality, task=task)
                results.extend(om_results)
            except Exception as e:
                console.print(f"[yellow]OpenML search failed: {e}[/]")

        # Filter by license if specified
        if license and results:
            results = [r for r in results if r.license and license.lower() in r.license.lower()]

        return results

    results = asyncio.run(_search())

    if not results:
        console.print("[yellow]No results found[/]")
        return

    # Display results
    table = Table(title=f"Search Results ({len(results)} datasets)")
    table.add_column("Source", style="cyan", width=10)
    table.add_column("Name", style="green")
    table.add_column("Size", justify="right", width=10)
    table.add_column("Modality", width=10)
    table.add_column("License", width=12)

    for r in results[:limit]:
        size_str = f"{r.size_bytes / 1024 / 1024:.1f} MB" if r.size_bytes else "Unknown"
        table.add_row(
            r.source.value,
            r.name,
            size_str,
            r.modality.value,
            r.license or "-",
        )

    console.print(table)


# =============================================================================
# INFO
# =============================================================================

@app.command("info")
def info_cmd(
    uri: str = typer.Argument(..., help="Dataset URI (hf://owner/dataset, kaggle://owner/dataset, openml://id, /local/path.csv)"),
    sample: int = typer.Option(5, "-s", "--sample", help="Show sample rows"),
    schema: bool = typer.Option(True, "--schema/--no-schema", help="Show schema"),
) -> None:
    """Show detailed information about a dataset."""
    import asyncio

    from mldata.connectors import get_connector

    async def _info():
        connector = get_connector(uri)
        dataset_id, _ = connector.parse_uri(uri)
        return await connector.get_metadata(dataset_id)

    try:
        metadata = asyncio.run(_info())

        # Main info panel
        info_text = Text()
        info_text.append(f"Name: {metadata.name}\n", style="bold")
        info_text.append(f"Source: {metadata.source.value}\n")
        if metadata.description:
            desc_preview = metadata.description[:200] + "..." if len(metadata.description) > 200 else metadata.description
            info_text.append(f"Description: {desc_preview}\n")
        if metadata.size_bytes:
            info_text.append(f"Size: {metadata.size_bytes / 1024 / 1024:.1f} MB\n")
        if metadata.num_samples:
            info_text.append(f"Samples: {metadata.num_samples:,}\n")
        if metadata.num_columns:
            info_text.append(f"Columns: {metadata.num_columns}\n")
        info_text.append(f"Modality: {metadata.modality.value}\n")
        if metadata.tasks:
            info_text.append(f"Tasks: {', '.join(t.value for t in metadata.tasks)}\n")
        if metadata.license:
            info_text.append(f"License: {metadata.license}\n")
        if metadata.author:
            info_text.append(f"Author: {metadata.author}\n")
        if metadata.download_count:
            info_text.append(f"Downloads: {metadata.download_count:,}\n")
        if metadata.citation:
            cit_preview = metadata.citation[:100] + "..." if len(metadata.citation) > 100 else metadata.citation
            info_text.append(f"Citation: {cit_preview}\n")
        if metadata.version:
            info_text.append(f"Version: {metadata.version[:12]}\n")
        if metadata.url:
            info_text.append(f"URL: {metadata.url}\n")

        console.print(Panel(info_text, title=f"Dataset: {metadata.name}", expand=False))

        # Schema table
        if schema and metadata.columns:
            from rich.table import Table
            schema_table = Table(title="Schema", show_header=True, header_style="bold")
            schema_table.add_column("#", width=4, justify="right")
            schema_table.add_column("Name", style="cyan")
            schema_table.add_column("Type", style="green")
            schema_table.add_column("Nullable", width=9)

            for i, col in enumerate(metadata.columns[:20], 1):  # Limit to 20 columns
                nullable = "Yes" if col.nullable else "No"
                schema_table.add_row(str(i), col.name, col.dtype, nullable)

            if len(metadata.columns) > 20:
                schema_table.add_row(f"...", f"({len(metadata.columns) - 20} more)", "...", "...")

            console.print(schema_table)

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


# =============================================================================
# PULL
# =============================================================================

@app.command("pull")
def pull_cmd(
    uri: str = typer.Argument(..., help="Dataset URI"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output directory"),
    revision: Optional[str] = typer.Option(None, "-r", "--revision", help="Specific version/revision"),
    subset: Optional[str] = typer.Option(None, "--subset", help="Specific subset/config"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Force fresh download"),
) -> None:
    """Download a dataset."""
    import asyncio
    from pathlib import Path
    from mldata.core.fetch import FetchService

    async def _pull():
        fetch = FetchService()
        output_dir = Path(output) if output else Path(f"mldata/{uri.split('/')[-1]}")
        await fetch.fetch(uri, output_dir, revision=revision, subset=subset, no_cache=no_cache)
        return output_dir

    try:
        output_dir = asyncio.run(_pull())
        console.print(f"[green]Dataset downloaded to: {output_dir}[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


# =============================================================================
# BUILD
# =============================================================================

@app.command("build")
def build_cmd(
    uri: str = typer.Argument(..., help="Dataset URI"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output directory"),
    format: str = typer.Option("parquet", "-f", "--format", help="Output format (parquet, csv, jsonl)"),
    split: str = typer.Option("0.8,0.1,0.1", "-s", "--split", help="Train/val/test split ratios"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed for reproducibility"),
    stratify: Optional[str] = typer.Option(None, "--stratify", help="Column to stratify on"),
    validate: bool = typer.Option(True, "--validate/--no-validate", help="Run quality validation"),
    no_cache: bool = typer.Option(False, "--no-cache", help="Skip cache"),
    incremental: bool = typer.Option(False, "--incremental", help="Enable incremental builds (skip unchanged files)"),
) -> None:
    """Full pipeline: fetch, normalize, validate, split, and export a dataset."""
    import asyncio
    from pathlib import Path
    from mldata.core.fetch import FetchService
    from mldata.core.normalize import NormalizeService
    from mldata.core.split import SplitService
    from mldata.core.export import ExportService
    from mldata.core.manifest import ManifestService
    from mldata.core.validate import ValidateService
    from mldata.core.incremental import IncrementalService

    async def _build():
        dataset_name = uri.split("/")[-1]
        output_dir = Path(output) if output else Path(f"mldata/{dataset_name}")
        output_dir.mkdir(parents=True, exist_ok=True)

        console.print(f"[bold]Building dataset from {uri}[/]")

        # Initialize incremental service
        processed_count = 0
        skipped_count = 0

        if incremental:
            console.print("[cyan]Running incremental build...[/]")
            incremental_service = IncrementalService()

        # 1. Fetch
        console.print("[cyan]Fetching dataset...[/]")
        fetch = FetchService()
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True, exist_ok=True)

        # Check if we should skip due to incremental build
        should_fetch = True
        if incremental:
            # Check cache for existing raw data
            existing_files = list(raw_dir.rglob("*"))
            if existing_files:
                console.print(f"[yellow]Found {len(existing_files)} existing files, checking for changes...[/]")
                should_fetch = False
                skipped_count += 1

        if should_fetch:
            await fetch.fetch(uri, raw_dir, no_cache=no_cache)
            processed_count += 1

        # 2. Find and detect format
        console.print("[cyan]Detecting format...[/]")
        normalize = NormalizeService()
        # Look for data files recursively (handle split subdirs)
        data_files = list(raw_dir.rglob("*.parquet")) + list(raw_dir.rglob("*.csv")) + list(raw_dir.rglob("*.jsonl"))
        if not data_files:
            raise ValueError("No data files found")

        # Use the first file found (e.g., train split)
        data_file = data_files[0]
        console.print(f"[cyan]Using: {data_file}[/]")

        # Normalize to target format
        artifacts_dir = output_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        output_file = artifacts_dir / f"data.{format}"

        # Check for incremental skip on artifacts
        should_process = True
        if incremental and output_file.exists():
            existing_hash = incremental_service.compute_file_hash(output_file)
            new_hash = incremental_service.compute_file_hash(data_file)
            if existing_hash == new_hash:
                console.print(f"[yellow]Skipping {output_file.name} (unchanged)[/]")
                should_process = False
                skipped_count += 1

        if should_process:
            df = normalize.read_data(data_file)
            normalize.convert_format(data_file, output_file, format)
            console.print(f"[green]Normalized to {format}[/]")
            processed_count += 1

        # 3. Split
        ratios = [float(x) for x in split.split(",")]
        if len(ratios) != 3:
            raise ValueError("Must provide 3 ratios (e.g., 0.8,0.1,0.1)")

        console.print("[cyan]Creating splits...[/]")
        split_service = SplitService()
        df = normalize.read_data(output_file)
        splits = split_service.split(df, ratios=ratios, seed=seed, stratify_column=stratify)

        splits_dir = output_dir / "splits"
        split_paths = split_service.save_splits(splits, splits_dir, format=format)
        for name, path in split_paths.items():
            console.print(f"  [green]{name}: {path}[/]")

        # 4. Validate
        if validate:
            console.print("[cyan]Running quality checks...[/]")
            validate_service = ValidateService()
            # Run basic checks
            dup_result = validate_service.check_duplicates(df)
            missing_result = validate_service.check_missing_values(df)

            console.print(f"  Duplicates: {dup_result['exact_duplicates']} found")
            console.print(f"  Missing values: {missing_result['total_missing']} found")

        # 5. Generate manifest
        console.print("[cyan]Generating manifest...[/]")
        manifest_service = ManifestService()
        artifact_hashes = manifest_service.compute_artifact_hashes(output_dir)

        manifest = manifest_service.create_manifest(
            source_uri=uri,
            source_params={},
            build_params={
                "format": format,
                "split_ratios": ratios,
                "seed": seed,
                "stratify": stratify,
            },
            dataset_info={
                "name": dataset_name,
                "num_samples": len(df),
                "num_columns": len(df.columns),
            },
            artifact_hashes=artifact_hashes,
            tool_version=__version__,
        )

        manifest_path = output_dir / "manifest.yaml"
        manifest_service.save_manifest(manifest, manifest_path)
        console.print(f"[green]Manifest: {manifest_path}[/]")

        # Report incremental stats
        if incremental:
            console.print(f"[cyan]Incremental build: Processed: {processed_count}, Skipped: {skipped_count}[/]")

        return output_dir

    try:
        output_dir = asyncio.run(_build())
        console.print(f"\n[bold green]Build complete: {output_dir}[/]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


# =============================================================================
# VALIDATE
# =============================================================================

@app.command("validate")
def validate_cmd(
    path: Path = typer.Argument(..., help="Path to dataset directory or file"),
    checks: Optional[str] = typer.Option(None, "-c", "--checks", help="Comma-separated checks to run (duplicates, labels, missing, schema, files)"),
    report: Optional[str] = typer.Option(None, "-r", "--report", help="Output report path (auto-detect .md/.json)"),
    json_output: bool = typer.Option(False, "--json", help="Output JSON format"),
    sample: Optional[float] = typer.Option(None, "-s", "--sample", help="Sample percentage for file checks (10-100)"),
) -> None:
    """Run quality validation checks on a dataset."""
    from mldata.core.validate import ValidateService, FileIntegrityService
    from mldata.core.normalize import NormalizeService
    from mldata.models.report import QualityReport, CheckResult, CheckStatus

    console.print(f"[bold]Validating: {path}[/]")

    # Handle file path directly
    data_files = []
    if path.is_file():
        if path.suffix.lower() in (".csv", ".parquet", ".jsonl", ".json"):
            data_files = [path]
    else:
        # Find data files (look recursively in splits, artifacts, etc.)
        data_files = list(path.rglob("*.csv")) + list(path.rglob("*.parquet")) + list(path.rglob("*.jsonl"))

    # Check if this is a file integrity check (media files)
    file_integrity_files = []
    if path.is_file():
        file_integrity_files = [path]
    elif path.is_dir():
        # Find media files for integrity check
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff"}
        audio_exts = {".wav", ".mp3", ".flac", ".ogg", ".m4a", ".aac"}
        media_exts = image_exts | audio_exts
        file_integrity_files = list(path.rglob("*"))
        file_integrity_files = [f for f in file_integrity_files if f.is_file() and f.suffix.lower() in media_exts]

    # Run file integrity check if requested
    check_list = []
    raw_checks = checks

    if checks == "all":
        check_list = ["duplicates", "labels", "missing", "schema", "files"] if file_integrity_files else ["duplicates", "labels", "missing", "schema"]
    elif checks:
        check_list = [c.strip() for c in checks.split(",")]
    else:
        # Default: run all checks if files present, otherwise data checks
        check_list = ["duplicates", "labels", "missing", "schema", "files"] if file_integrity_files else ["duplicates", "labels", "missing", "schema"]

    all_passed = True
    passed_count = 0
    failed_count = 0

    # Run file integrity check first if requested
    if "files" in check_list and file_integrity_files:
        console.print(f"  [cyan]Running files...[/]")

        integrity = FileIntegrityService()
        sample_percent = sample if sample else 100.0

        try:
            results = integrity.run_checks(file_integrity_files, sample_percent=sample_percent)

            valid_count = sum(1 for r in results if r.is_valid)
            invalid_count = len(results) - valid_count

            if invalid_count == 0:
                console.print(f"    [green]✓[green] files: PASS (all {valid_count} files valid)")
                passed_count += 1
                file_passed = True
            else:
                console.print(f"    [red]✗[red] files: FAIL ({invalid_count}/{len(results)} files invalid)")
                all_passed = False
                failed_count += 1
                file_passed = False

                # Show invalid files
                invalid_files = [r for r in results if not r.is_valid]
                console.print(f"      [yellow]Invalid files:[/]")
                for result in invalid_files[:10]:
                    console.print(f"        - {result.path.name}: {result.error}")

                if len(invalid_files) > 10:
                    console.print(f"        ... and {len(invalid_files) - 10} more")

        except Exception as e:
            console.print(f"    [yellow]! files: ERROR - {e}[/]")
            all_passed = False
            failed_count += 1
            file_passed = False

        # Remove files from check_list since we handle it separately
        check_list = [c for c in check_list if c != "files"]

    # Skip data checks if no data files
    if not data_files and check_list:
        console.print("[yellow]No data files found, skipping data checks[/]")
        check_list = []

    if not data_files and not file_integrity_files:
        console.print("[red]No valid files found in path[/]")
        console.print("[cyan]Tip: Ensure the path contains data files (.csv, .parquet, .jsonl) or media files (.jpg, .png, .wav, etc.)[/]")
        raise typer.Exit(2)

    # Skip if only file check was requested and no data checks needed
    if not check_list:
        if not all_passed:
            raise typer.Exit(2)
        raise typer.Exit(0)

    normalize = NormalizeService()
    validate = ValidateService()

    # Read data
    try:
        df = normalize.read_data(data_files[0])
    except Exception as e:
        console.print(f"[red]Failed to read data file: {e}[/]")
        console.print("[cyan]Tip: Check that the file is a valid CSV, Parquet, or JSONL file[/]")
        raise typer.Exit(2)

    report_obj = QualityReport.create(str(path))
    report_obj.num_samples = len(df)
    report_obj.num_columns = len(df.columns)

    # Run checks
    if checks == "all":
        check_list = ["duplicates", "labels", "missing", "schema"]
    else:
        check_list = checks.split(",") if checks else ["duplicates", "labels", "missing", "schema"]

    all_passed = True
    passed_count = 0
    failed_count = 0

    for check_name in check_list:
        console.print(f"  [cyan]Running {check_name}...[/]")

        try:
            if check_name == "duplicates":
                result = validate.check_duplicates(df)
            elif check_name == "labels":
                result = validate.check_label_distribution(df, "label")
            elif check_name == "missing":
                result = validate.check_missing_values(df)
            elif check_name == "schema":
                result = validate.check_schema_consistency(df)
            else:
                continue

            status = "✓" if result["passed"] else "✗"
            style = "green" if result["passed"] else "red"
            console.print(f"    [{style}]{status}[/{style}] {check_name}: {'PASS' if result['passed'] else 'FAIL'}")

            # Add to report
            check_result = CheckResult(
                check_name=check_name,
                status=CheckStatus.PASSED if result["passed"] else CheckStatus.FAILED,
                message=f"{check_name}: {'PASS' if result['passed'] else 'FAIL'}",
                details=result,
            )
            report_obj.checks.append(check_result)

            # Show detailed failure information
            if not result["passed"]:
                all_passed = False
                failed_count += 1
                _show_validation_details(check_name, result)
            else:
                passed_count += 1

        except Exception as e:
            console.print(f"    [yellow]! {check_name}: ERROR - {e}[/]")
            all_passed = False
            failed_count += 1

            check_result = CheckResult(
                check_name=check_name,
                status=CheckStatus.ERROR,
                message=str(e),
            )
            report_obj.checks.append(check_result)

    # Update summary
    report_obj.summary = {
        "total_checks": len(check_list),
        "passed": passed_count,
        "failed": failed_count,
        "num_samples": len(df),
        "num_columns": len(df.columns),
    }

    # Save report
    if report:
        # Auto-detect format from extension
        if report.endswith(".md") or report.endswith(".markdown"):
            report_obj.to_markdown(report)
            console.print(f"[green]Report saved: {report}[/]")
        elif report.endswith(".json") or not report.endswith("."):
            report_obj.to_json(f"{report}.json" if not report.endswith(".json") else report)
            console.print(f"[green]Report saved: {report}[/]")
        else:
            # Default to JSON
            report_obj.to_json(f"{report}.json")
            console.print(f"[green]Report saved: {report}.json[/]")
    elif json_output:
        import json
        console.print(json.dumps(report_obj.model_dump(), indent=2))

    if not all_passed:
        raise typer.Exit(2)


def _show_validation_details(check_name: str, result: dict) -> None:
    """Show detailed validation failure information."""
    from rich.table import Table

    if check_name == "duplicates":
        count = result.get("exact_duplicates", 0)
        ratio = result.get("duplicate_ratio", 0)
        console.print(f"      [yellow]Found {count} duplicate rows ({ratio*100:.1f}%)[/]")
        console.print(f"      [cyan]Suggestion: Remove duplicates or investigate data source[/]")

    elif check_name == "labels":
        imbalance = result.get("imbalance_ratio", 0)
        num_classes = result.get("num_classes", 0)
        console.print(f"      [yellow]Imbalance ratio: {imbalance*100:.1f}% ({num_classes} classes)[/]")
        console.print(f"      [cyan]Suggestion: Consider data augmentation or class weights[/]")

    elif check_name == "missing":
        issues = result.get("issues", [])
        total = result.get("total_missing", 0)
        console.print(f"      [yellow]{total} missing values across {len(issues)} columns[/]")

        if issues:
            table = Table(show_header=True, header_style="bold")
            table.add_column("Column", style="cyan")
            table.add_column("Missing", justify="right", width=10)
            table.add_column("Percent", justify="right", width=10)
            table.add_column("Severity", width=10)
            table.add_column("Suggestion", style="dim")

            for issue in issues[:10]:  # Limit to 10 issues
                col = issue.get("column", "?")
                count = issue.get("missing_count", 0)
                ratio = issue.get("missing_ratio", 0) * 100

                # Determine severity
                if ratio > 50:
                    severity = "[red]ERROR[/]"
                    suggestion = "Remove column"
                elif ratio > 20:
                    severity = "[yellow]WARNING[/]"
                    suggestion = "Consider removal"
                else:
                    severity = "[blue]INFO[/]"
                    suggestion = "Impute"

                table.add_row(col, str(count), f"{ratio:.1f}%", severity, suggestion)

            console.print(table)

            if len(issues) > 10:
                console.print(f"      ... and {len(issues) - 10} more columns")

    elif check_name == "schema":
        issues = result.get("issues", [])
        console.print(f"      [yellow]{len(issues)} schema issues found[/]")

        for issue in issues[:5]:
            col = issue.get("column", "?")
            issue_desc = issue.get("issue", "?")
            console.print(f"      - [cyan]{col}[/]: {issue_desc}")

        if len(issues) > 5:
            console.print(f"      ... and {len(issues) - 5} more issues")


# =============================================================================
# DRIFT
# =============================================================================

@app.command("drift")
def drift_cmd(
    baseline: Path = typer.Argument(..., help="Baseline dataset (older build)"),
    current: Path = typer.Argument(..., help="Current dataset (newer build)"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output report path (.json or .md)"),
    detailed: bool = typer.Option(False, "-d", "--detailed", help="Show detailed statistics"),
) -> None:
    """Detect data drift between two datasets using PSI and KL divergence."""
    from mldata.core.drift import DriftService

    console.print(f"[bold]Drift Detection[/]")
    console.print(f"  Baseline: {baseline}")
    console.print(f"  Current:  {current}")

    # Find data files - handle both files and directories
    def find_data_file(path: Path) -> Path | None:
        if path.is_file():
            if path.suffix.lower() in (".csv", ".parquet", ".jsonl", ".json"):
                return path
            return None
        # Look in directory
        files = list(path.rglob("*.parquet")) + list(path.rglob("*.csv")) + list(path.rglob("*.jsonl"))
        return files[0] if files else None

    baseline_file = find_data_file(baseline)
    current_file = find_data_file(current)

    if not baseline_file or not current_file:
        console.print("[red]Could not find data files in one or both paths[/]")
        raise typer.Exit(1)

    try:
        drift_service = DriftService()
        report = drift_service.detect_drift(baseline_file, current_file)

        # Display report
        if report.overall_drift_detected:
            console.print("\n[yellow][bold]Drift Detected![/][/]")
        else:
            console.print("\n[green][bold]No Significant Drift[/][/]")

        summary = report.severity_summary
        console.print(f"  Severity: {summary.get('high', 0)} high, {summary.get('medium', 0)} medium, {summary.get('low', 0)} low")

        # Show numeric drift
        if report.numeric_drift:
            console.print("\n[bold]Numeric Columns[/]")
            for col, drift in report.numeric_drift.items():
                psi = drift.get("psi", 0)
                severity = drift.get("severity", "unknown")
                detected = drift.get("drift_detected", False)

                status = "DRIFT" if detected else "OK"
                style = "red" if detected else "green"
                console.print(f"  [{style}]{status}[/{style}] {col}: PSI={psi:.4f} ({severity})")

                if detailed and detected:
                    b_stats = drift.get("baseline_stats", {})
                    c_stats = drift.get("current_stats", {})
                    console.print(f"       Mean: {b_stats.get('mean', 0):.2f} -> {c_stats.get('mean', 0):.2f}")

        # Show categorical drift
        if report.categorical_drift:
            console.print("\n[bold]Categorical Columns[/]")
            for col, drift in report.categorical_drift.items():
                psi = drift.get("psi", 0)
                severity = drift.get("severity", "unknown")
                detected = drift.get("drift_detected", False)

                status = "DRIFT" if detected else "OK"
                style = "red" if detected else "green"
                console.print(f"  [{style}]{status}[/{style}] {col}: PSI={psi:.4f} ({severity})")

        # Save report
        if output:
            if output.endswith(".md"):
                report.to_markdown(output)
                console.print(f"\n[green]Report saved: {output}[/]")
            elif output.endswith(".json"):
                report.to_json(output)
                console.print(f"\n[green]Report saved: {output}[/]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


# =============================================================================
# PROFILE
# =============================================================================

@app.command("profile")
def profile_cmd(
    path: Path = typer.Argument(..., help="Path to dataset file or directory"),
    output: Optional[str] = typer.Option(None, "-o", "--output", help="Output report path (.json or .md)"),
    stats: bool = typer.Option(True, "--stats/--no-stats", help="Show statistics"),
    schema: bool = typer.Option(True, "--schema/--no-schema", help="Show schema"),
    sample: int = typer.Option(5, "-s", "--sample", help="Show sample rows"),
) -> None:
    """Generate a profile of a dataset with statistics."""
    from mldata.core.profile import ProfileService
    from rich.table import Table

    console.print(f"[bold]Profiling: {path}[/]")

    try:
        profile_service = ProfileService()
        profile = profile_service.profile(path)

        # Overview panel
        from rich.text import Text
        from rich.panel import Panel

        overview = Text()
        overview.append(f"Path: {profile.path}\n")
        overview.append(f"Rows: {profile.num_rows:,}\n" if profile.num_rows else "Rows: Unknown\n")
        overview.append(f"Columns: {profile.num_columns}\n" if profile.num_columns else "")
        if profile.file_size_bytes:
            overview.append(f"Size: {profile.file_size_bytes / 1024 / 1024:.2f} MB\n")

        console.print(Panel(overview, title="Overview", expand=False))

        # Schema table
        if schema and profile.columns:
            console.print("\n[bold]Schema[/]")
            schema_table = Table(show_header=True, header_style="bold")
            schema_table.add_column("#", width=4, justify="right")
            schema_table.add_column("Name", style="cyan")
            schema_table.add_column("Type", style="green")
            schema_table.add_column("Nullable", width=9)
            schema_table.add_column("Unique", justify="right", width=8)

            for i, col in enumerate(profile.columns, 1):
                nullable = "Yes" if col.nullable else "No"
                unique = str(col.unique_count) if col.unique_count else "-"
                schema_table.add_row(str(i), col.name, col.dtype, nullable, unique)

            console.print(schema_table)

        # Numeric statistics
        if stats and profile.numeric_stats:
            console.print("\n[bold]Numeric Statistics[/]")
            for col_name, stats_data in profile.numeric_stats.items():
                console.print(f"\n[cyan]{col_name}[/]")
                stat_lines = [
                    f"  Mean: {stats_data.mean:.4f}" if stats_data.mean is not None else "  Mean: N/A",
                    f"  Std:  {stats_data.std:.4f}" if stats_data.std is not None else "  Std:  N/A",
                    f"  Min:  {stats_data.min}" if stats_data.min is not None else "  Min:  N/A",
                    f"  Max:  {stats_data.max}" if stats_data.max is not None else "  Max:  N/A",
                    f"  Median: {stats_data.median}" if stats_data.median is not None else "",
                ]
                for line in stat_lines:
                    if line:
                        console.print(line)

                if stats_data.percentiles:
                    console.print("  Percentiles:")
                    for p, v in sorted(stats_data.percentiles.items()):
                        console.print(f"    {p}%: {v:.4f}")

        # Categorical statistics
        if stats and profile.categorical_stats:
            console.print("\n[bold]Categorical Statistics[/]")
            for col_name, cat_data in profile.categorical_stats.items():
                console.print(f"\n[cyan]{col_name}[/]")
                console.print(f"  Unique values: {cat_data.unique_values}")
                if cat_data.top_values:
                    console.print("  Top values:")
                    for v in cat_data.top_values[:5]:
                        console.print(f"    {v['value']}: {v['count']:,}")

        # Save report
        if output:
            if output.endswith(".md"):
                profile.to_markdown(output)
                console.print(f"\n[green]Report saved: {output}[/]")
            elif output.endswith(".json"):
                profile.to_json(output)
                console.print(f"\n[green]Report saved: {output}[/]")
            else:
                # Default to JSON
                profile.to_json(f"{output}.json")
                console.print(f"\n[green]Report saved: {output}.json[/]")

    except Exception as e:
        console.print(f"[red]Error: {e}[/]")
        raise typer.Exit(1)


# =============================================================================
# SPLIT
# =============================================================================

@app.command("split")
def split_cmd(
    path: Path = typer.Argument(..., help="Path to dataset file or directory"),
    ratios: str = typer.Argument(..., help="Split ratios (e.g., 0.8,0.1,0.1)"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output directory"),
    seed: Optional[int] = typer.Option(None, "--seed", help="Random seed"),
    stratify: Optional[str] = typer.Option(None, "--stratify", help="Column to stratify on"),
    format: str = typer.Option("csv", "-f", "--format", help="Output format"),
    indices: bool = typer.Option(False, "-i", "--indices", help="Save split indices"),
) -> None:
    """Split a dataset into train/val/test sets."""
    from mldata.core.normalize import NormalizeService
    from mldata.core.split import SplitService

    ratio_list = [float(x) for x in ratios.split(",")]
    if len(ratio_list) != 3:
        console.print("[red]Must provide 3 ratios[/]")
        raise typer.Exit(1)

    output_dir = output or (path.parent / f"splits_{path.stem}")
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[bold]Splitting {path}[/]")
    console.print(f"Ratios: {ratio_list}")
    if seed:
        console.print(f"Seed: {seed}")
    if stratify:
        console.print(f"Stratify: {stratify}")

    # Read data
    normalize = NormalizeService()
    if path.is_dir():
        data_files = list(path.glob("*.csv")) + list(path.glob("*.parquet"))
        df = normalize.read_data(data_files[0])
    else:
        df = normalize.read_data(path)

    # Split
    split_service = SplitService()
    splits = split_service.split(df, ratios=ratio_list, seed=seed, stratify_column=stratify)

    # Save
    split_paths = split_service.save_splits(splits, output_dir, format=format)
    console.print("\n[green]Splits created:[/]")
    for name, p in split_paths.items():
        console.print(f"  {name}: {p}")

    # Save indices if requested
    if indices:
        index_paths = split_service.save_split_indices(splits, output_dir)
        console.print("\n[green]Index files:[/]")
        for name, p in index_paths.items():
            console.print(f"  {name}: {p}")


# =============================================================================
# EXPORT
# =============================================================================

@app.command("export")
def export_cmd(
    path: Path = typer.Argument(..., help="Path to dataset"),
    format: Optional[str] = typer.Option(None, "-f", "--format", help="Export format (parquet, csv, jsonl)"),
    formats: Optional[str] = typer.Option(None, "--formats", help="Export to multiple formats (comma-separated: parquet,csv,jsonl)"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output directory"),
    compression: Optional[str] = typer.Option(None, "--compression", help="Compression (snappy, gzip, zstd)"),
    all_formats: bool = typer.Option(False, "-a", "--all", help="Export to all formats"),
    framework: Optional[str] = typer.Option(None, "--framework", help="Export with framework loader (pytorch, tensorflow, jax)"),
    dvc: bool = typer.Option(False, "--dvc", help="Generate DVC file for dataset versioning"),
    git_lfs: bool = typer.Option(False, "--git-lfs", help="Configure Git-LFS tracking for large files"),
) -> None:
    """Export a dataset to a specific format or multiple formats."""
    from mldata.core.normalize import NormalizeService
    from mldata.core.export import ExportService
    from mldata.core.framework import FrameworkExportService
    from mldata.integrations.dvc import DVCService
    from mldata.integrations.gitlfs import GitLFSService

    export = ExportService()
    normalize = NormalizeService()

    output_dir = output or (path / "artifacts")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find data file
    if path.is_file():
        data_file = path
    else:
        data_files = list(path.rglob("*.csv")) + list(path.rglob("*.parquet")) + list(path.rglob("*.jsonl"))
        if not data_files:
            console.print(f"[red]No data files found in {path}[/]")
            raise typer.Exit(1)
        data_file = data_files[0]

    console.print(f"[bold]Exporting {data_file}[/]")

    # Determine formats to export
    if formats:
        format_list = export.parse_formats(formats)
    elif all_formats:
        format_list = ["parquet", "csv", "json", "jsonl"]
    elif format:
        format_list = [format]
    else:
        format_list = ["parquet"]  # Default

    # Export to multiple formats
    output_paths = export.export_multiple(
        normalize.read_data(data_file),
        output_dir,
        formats=format_list,
        compression=compression
    )

    for fmt, output_path in output_paths.items():
        console.print(f"  [green]{fmt}: {output_path}[/]")

    # Framework export
    if framework:
        console.print(f"[bold]Generating {framework} framework loader...[/]")
        from mldata.core.framework import export_dataset
        dataset_name = path.name
        framework_output = export_dataset(
            normalize.read_data(data_file),
            output_dir,
            format="parquet",
            framework=framework,
            dataset_name=dataset_name
        )
        if framework_output.success:
            for file in framework_output.files_created:
                console.print(f"  [green]Created: {file}[/]")
        else:
            console.print(f"  [red]Framework export failed: {framework_output.error}[/]")

    # DVC integration
    if dvc:
        console.print(f"[bold]Generating DVC file...[/]")
        dvc_service = DVCService()
        # Compute hash of the data file
        from mldata.core.fetch import FetchService
        fetch = FetchService()
        file_hash = fetch._compute_file_hash(data_file)
        dvc_result = dvc_service.generate_dvc_file(
            path,
            file_hash,
            remote=None
        )
        dvc_path = path.parent / f"{path.name}.dvc"
        if dvc_result.success:
            console.print(f"  [green]dvc: {dvc_path}[/]")
            console.print(f"  [cyan]→ Run 'dvc push' to upload to remote storage[/]")
        else:
            console.print(f"  [red]DVC failed: {dvc_result.error}[/]")

    # Git-LFS integration
    if git_lfs:
        console.print(f"[bold]Configuring Git-LFS...[/]")
        lfs_service = GitLFSService()
        import os
        git_root = os.getcwd()
        lfs_result = lfs_service.configure_tracking(Path(git_root), path)
        if lfs_result.success:
            console.print(f"  [green]Git-LFS configured[/]")
            console.print(f"  [cyan]→ Run 'git add .gitattributes' and 'git add -A && git commit'[/]")
        else:
            console.print(f"  [red]Git-LFS failed: {lfs_result.error}[/]")


# =============================================================================
# REBUILD
# =============================================================================

@app.command("rebuild")
def rebuild_cmd(
    manifest: Path = typer.Argument(..., help="Path to manifest.yaml"),
    output: Optional[Path] = typer.Option(None, "-o", "--output", help="Output directory (default: same as manifest)"),
    verify: bool = typer.Option(True, "-v", "--verify/--no-verify", help="Verify output against manifest"),
    dry_run: bool = typer.Option(False, "-n", "--dry-run", help="Show what would happen without executing"),
) -> None:
    """Rebuild a dataset from its manifest."""
    import asyncio
    from pathlib import Path as PathType
    from mldata.core.manifest import ManifestService
    from mldata.core.fetch import FetchService
    from mldata.core.normalize import NormalizeService
    from mldata.core.split import SplitService
    from mldata.core.export import ExportService
    from mldata.core.validate import ValidateService
    from mldata import __version__

    manifest_service = ManifestService()

    # Load manifest
    try:
        manifest_data = manifest_service.load_manifest(manifest)
    except Exception as e:
        console.print(f"[red]Failed to load manifest: {e}[/]")
        raise typer.Exit(1)

    source_uri = manifest_data.source.get("uri") if manifest_data.source else None
    if not source_uri:
        console.print("[red]No source URI in manifest[/]")
        raise typer.Exit(1)

    # Use original output or new location
    if not output:
        output = manifest.parent

    # Extract build parameters
    build_params = manifest_data.build or {}
    split_ratios = build_params.get("split_ratios", [0.8, 0.1, 0.1])
    seed = build_params.get("seed")
    stratify = build_params.get("stratify")
    output_format = build_params.get("format", "parquet")

    console.print(f"[bold]Rebuilding from manifest[/]")
    console.print(f"Source: {source_uri}")
    console.print(f"Output: {output}")
    console.print(f"Format: {output_format}")
    console.print(f"Split:  {split_ratios}")
    if seed:
        console.print(f"Seed:   {seed}")

    if dry_run:
        console.print("\n[yellow]Dry run - would execute:[/]")
        console.print(f"  mldata build {source_uri} --output {output}")
        console.print(f"  --format {output_format}")
        console.print(f"  --split {','.join(str(x) for x in split_ratios)}")
        if seed:
            console.print(f"  --seed {seed}")
        if stratify:
            console.print(f"  --stratify {stratify}")
        return

    async def _rebuild():
        output_dir = PathType(output)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Fetch
        console.print("\n[cyan]Fetching dataset...[/]")
        fetch = FetchService()
        raw_dir = output_dir / "raw"
        await fetch.fetch(source_uri, raw_dir, no_cache=False)

        # 2. Normalize
        console.print("[cyan]Normalizing...[/]")
        normalize = NormalizeService()
        data_files = list(raw_dir.rglob("*.parquet")) + list(raw_dir.rglob("*.csv")) + list(raw_dir.rglob("*.jsonl"))
        if not data_files:
            raise ValueError("No data files found after fetch")

        data_file = data_files[0]
        artifacts_dir = output_dir / "artifacts"
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        output_file = artifacts_dir / f"data.{output_format}"
        normalize.convert_format(data_file, output_file, output_format)

        # 3. Split
        console.print("[cyan]Creating splits...[/]")
        split_service = SplitService()
        df = normalize.read_data(output_file)
        splits = split_service.split(df, ratios=split_ratios, seed=seed, stratify_column=stratify)
        splits_dir = output_dir / "splits"
        split_service.save_splits(splits, splits_dir, format=output_format)

        # 4. Validate
        console.print("[cyan]Validating...[/]")
        validate = ValidateService()
        dup_result = validate.check_duplicates(df)
        missing_result = validate.check_missing_values(df)
        console.print(f"  Duplicates: {dup_result['exact_duplicates']}")
        console.print(f"  Missing: {missing_result['total_missing']}")

        # 5. Generate manifest
        console.print("[cyan]Generating manifest...[/]")
        artifact_hashes = manifest_service.compute_artifact_hashes(output_dir)

        new_manifest = manifest_service.create_manifest(
            source_uri=source_uri,
            source_params=manifest_data.source.get("params", {}) if manifest_data.source else {},
            build_params={
                "format": output_format,
                "split_ratios": split_ratios,
                "seed": seed,
                "stratify": stratify,
            },
            dataset_info={
                "name": manifest_data.dataset.get("name", "dataset") if manifest_data.dataset else "dataset",
                "num_samples": len(df),
                "num_columns": len(df.columns),
            },
            artifact_hashes=artifact_hashes,
            tool_version=__version__,
        )

        manifest_path = output_dir / "manifest.yaml"
        manifest_service.save_manifest(new_manifest, manifest_path)

        # 6. Verify
        if verify:
            console.print("\n[cyan]Verifying rebuild...[/]")
            verification = _verify_rebuild(manifest_data, new_manifest, output_dir)
            _display_verification(verification)

        return output_dir

    try:
        result = asyncio.run(_rebuild())
        console.print(f"\n[bold green]Rebuild complete: {result}[/]")
    except Exception as e:
        console.print(f"[red]Rebuild failed: {e}[/]")
        raise typer.Exit(1)


def _verify_rebuild(original_manifest, new_manifest, output_dir: Path) -> dict:
    """Verify rebuild against original manifest."""
    verification = {
        "source_match": original_manifest.source.get("uri") == new_manifest.source.get("uri") if original_manifest.source and new_manifest.source else False,
        "format_match": original_manifest.build.get("format") == new_manifest.build.get("format") if original_manifest.build and new_manifest.build else False,
        "split_ratios_match": original_manifest.build.get("split_ratios") == new_manifest.build.get("split_ratios") if original_manifest.build and new_manifest.build else False,
        "seed_match": original_manifest.build.get("seed") == new_manifest.build.get("seed") if original_manifest.build and new_manifest.build else False,
        "samples_match": original_manifest.dataset.get("num_samples") == new_manifest.dataset.get("num_samples") if original_manifest.dataset and new_manifest.dataset else False,
        "columns_match": original_manifest.dataset.get("num_columns") == new_manifest.dataset.get("num_columns") if original_manifest.dataset and new_manifest.dataset else False,
        "files_exist": list(output_dir.glob("*.yaml")) and list(output_dir.glob("splits/*")),
    }

    verification["all_match"] = all(verification.values())
    return verification


def _display_verification(verification: dict) -> None:
    """Display verification results."""
    from rich.table import Table

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Result", width=12)

    checks = [
        ("Source URI", verification.get("source_match")),
        ("Format", verification.get("format_match")),
        ("Split ratios", verification.get("split_ratios_match")),
        ("Seed", verification.get("seed_match")),
        ("Sample count", verification.get("samples_match")),
        ("Column count", verification.get("columns_match")),
        ("Files exist", verification.get("files_exist")),
    ]

    for name, result in checks:
        status = "✓ PASS" if result else "✗ FAIL"
        style = "green" if result else "red"
        table.add_row(name, f"[{style}]{status}[/{style}]")

    console.print(table)

    if verification.get("all_match"):
        console.print("[green]Rebuild verification: ALL CHECKS PASSED[/]")
    else:
        console.print("[yellow]Rebuild verification: Some checks failed[/]")


# =============================================================================
# DIFF
# =============================================================================

@app.command("diff")
def diff_cmd(
    path1: Path = typer.Argument(..., help="First build directory or manifest"),
    path2: Path = typer.Argument(..., help="Second build directory or manifest"),
    data: bool = typer.Option(True, "-d", "--data/--no-data", help="Compare actual data"),
    manifest: bool = typer.Option(True, "-m", "--manifest/--no-manifest", help="Compare manifest parameters"),
    drift: bool = typer.Option(False, "--drift", help="Detect data drift (PSI, KL divergence)"),
    schema: bool = typer.Option(False, "--schema", help="Show schema evolution"),
    detailed: bool = typer.Option(False, "-D", "--detailed", help="Show detailed differences"),
) -> None:
    """Compare two dataset builds with optional drift and schema analysis."""
    from mldata.core.manifest import ManifestService
    from mldata.core.diff import DiffService
    from mldata.core.drift import DriftService
    from mldata.core.schema import SchemaEvolutionService

    manifest_service = ManifestService()
    diff_service = DiffService()
    drift_service = DriftService()

    # Load manifests if paths exist
    m1 = None
    m2 = None
    manifest1_uri = "unknown"
    manifest2_uri = "unknown"

    try:
        manifest1_path = path1 if path1.is_file() and path1.name == "manifest.yaml" else path1 / "manifest.yaml"
        if manifest1_path.exists():
            m1 = manifest_service.load_manifest(manifest1_path)
            manifest1_uri = m1.source.get("uri") if m1.source else "unknown"

        manifest2_path = path2 if path2.is_file() and path2.name == "manifest.yaml" else path2 / "manifest.yaml"
        if manifest2_path.exists():
            m2 = manifest_service.load_manifest(manifest2_path)
            manifest2_uri = m2.source.get("uri") if m2.source else "unknown"
    except Exception as e:
        console.print(f"[yellow]Warning: Could not load one or both manifests: {e}[/]")

    console.print(f"[bold]Comparing builds[/]")
    console.print(f"  Build 1: {manifest1_uri}")
    console.print(f"  Build 2: {manifest2_uri}")

    # Compare manifest parameters
    if manifest and m1 and m2:
        _compare_manifests(m1, m2, detailed)

    # Detect data drift
    if drift:
        console.print("\n[bold]Data Drift Detection[/]")
        try:
            # Find data files
            data1 = list(path1.rglob("*.parquet")) + list(path1.rglob("*.csv")) + list(path1.rglob("*.jsonl"))
            data2 = list(path2.rglob("*.parquet")) + list(path2.rglob("*.csv")) + list(path2.rglob("*.jsonl"))

            if data1 and data2:
                drift_report = drift_service.detect_drift(data1[0], data2[0])
                _display_drift_report(drift_report, detailed)
            else:
                console.print("[yellow]Could not find data files for drift detection[/]")
        except Exception as e:
            console.print(f"[yellow]Drift detection failed: {e}[/]")

    # Detect schema evolution
    if schema:
        console.print("\n[bold]Schema Evolution[/]")
        try:
            # Find data files
            data1 = list(path1.rglob("*.parquet")) + list(path1.rglob("*.csv")) + list(path1.rglob("*.jsonl"))
            data2 = list(path2.rglob("*.parquet")) + list(path2.rglob("*.csv")) + list(path2.rglob("*.jsonl"))

            if data1 and data2:
                schema_service = SchemaEvolutionService()
                evolution = schema_service.detect_evolution(data1[0], data2[0])
                _display_schema_evolution(evolution)
            else:
                console.print("[yellow]Could not find data files for schema analysis[/]")
        except Exception as e:
            console.print(f"[yellow]Schema analysis failed: {e}[/]")

    # Compare actual data
    if data:
        console.print("\n[bold]Data Comparison[/]")
        comparison = diff_service.compare_data(path1, path2)

        if "error" in comparison:
            console.print(f"[yellow]{comparison['error']}[/]")
        else:
            _display_data_comparison(comparison, detailed)


# =============================================================================
# AUTH
# =============================================================================

# =============================================================================
# DIFF HELPER FUNCTIONS
# =============================================================================

def _compare_manifests(m1, m2, detailed: bool) -> None:
    """Compare two manifests and display differences."""
    differences = []

    # Check seed
    seed1 = m1.build.get("seed")
    seed2 = m2.build.get("seed")
    if seed1 != seed2:
        differences.append(("Seed", str(seed1) if seed1 else "None", str(seed2) if seed2 else "None"))

    # Check split ratios
    r1 = m1.build.get("split_ratios", [])
    r2 = m2.build.get("split_ratios", [])
    if r1 != r2:
        differences.append(("Split ratios", str(r1), str(r2)))

    # Check format
    f1 = m1.build.get("format", "parquet")
    f2 = m2.build.get("format", "parquet")
    if f1 != f2:
        differences.append(("Format", f1, f2))

    # Check dataset size
    d1_samples = m1.dataset.get("num_samples") if m1.dataset else 0
    d2_samples = m2.dataset.get("num_samples") if m2.dataset else 0
    if d1_samples != d2_samples:
        differences.append(("Samples", str(d1_samples), str(d2_samples)))

    if differences:
        console.print("\n[yellow]Manifest Differences:[/]")
        console.print(f"  {'Parameter':<15} {'Build 1':<20} {'Build 2':<20}")
        console.print(f"  {'-'*15} {'-'*20} {'-'*20}")
        for param, v1, v2 in differences:
            console.print(f"  {param:<15} {v1:<20} {v2:<20}")
    else:
        console.print("\n[green]Manifest parameters match[/]")

    if detailed:
        console.print("\n[cyan]Manifest 1 provenance:[/]")
        console.print(f"  Source hash: {m1.provenance.get('source_hash', 'N/A')[:16]}...")
        console.print(f"  Created: {m1.created_at}")
        console.print("\n[cyan]Manifest 2 provenance:[/]")
        console.print(f"  Source hash: {m2.provenance.get('source_hash', 'N/A')[:16]}...")
        console.print(f"  Created: {m2.created_at}")


def _display_data_comparison(comparison: dict, detailed: bool) -> None:
    """Display data comparison results."""
    from rich.table import Table

    # Shape comparison
    shape = comparison.get("shape", {})
    rows_match = shape.get("rows_match", False)
    cols_match = shape.get("columns_match", False)

    console.print("\n[bold]Shape Comparison[/]")
    console.print(f"  Rows:    {shape.get('path1', {}).get('rows', '?')} vs {shape.get('path2', {}).get('rows', '?')} {'✓ MATCH' if rows_match else '✗ DIFFERENT'}")
    console.print(f"  Columns: {shape.get('path1', {}).get('columns', '?')} vs {shape.get('path2', {}).get('columns', '?')} {'✓ MATCH' if cols_match else '✗ DIFFERENT'}")

    # Schema comparison
    schema = comparison.get("schema", {})
    all_types_match = schema.get("all_types_match", True)

    console.print("\n[bold]Schema Comparison[/]")
    console.print(f"  Columns: {'✓ All types match' if all_types_match else '✗ Type differences found'}")

    if detailed:
        type_mismatches = schema.get("type_mismatches", [])
        if type_mismatches:
            console.print("\n  Type mismatches:")
            for tm in type_mismatches[:5]:
                console.print(f"    - {tm['column']}: {tm['type1']} vs {tm['type2']}")

        only_in_1 = schema.get("only_in_1", [])
        only_in_2 = schema.get("only_in_2", [])
        if only_in_1:
            console.print(f"  Only in Build 1: {', '.join(only_in_1)}")
        if only_in_2:
            console.print(f"  Only in Build 2: {', '.join(only_in_2)}")

    # Checksum comparison
    checksums = comparison.get("checksums", {})
    checksum_match = checksums.get("match", False)

    console.print("\n[bold]Checksums[/]")
    console.print(f"  Build 1: {checksums.get('path1', 'N/A')}")
    console.print(f"  Build 2: {checksums.get('path2', 'N/A')}")
    console.print(f"  Match:   {'✓ IDENTICAL' if checksum_match else '✗ DIFFERENT'}")

    if not checksum_match:
        console.print("  [yellow]Note: Different checksums are expected if using different seeds[/]")

    # Sample value comparison
    if detailed:
        samples = comparison.get("sample_values", {})
        cols = samples.get("columns", [])
        all_match = samples.get("all_match", True)

        console.print("\n[bold]Sample Values (first 5 rows)[/]")
        for col_data in cols[:5]:
            col = col_data["column"]
            match = col_data["match"]
            status = "✓" if match else "✗"
            vals1 = str(col_data["path1_values"][:3])
            vals2 = str(col_data["path2_values"][:3])
            console.print(f"  {status} {col}: {vals1} vs {vals2}")

        if len(cols) > 5:
            console.print(f"  ... and {len(cols) - 5} more columns")

    # Summary
    console.print("\n" + "="*60)
    shape_ok = rows_match and cols_match
    schema_ok = all_types_match
    console.print(f"Summary: Shapes {'✓' if shape_ok else '✗'} | Schema {'✓' if schema_ok else '✗'} | Data {'✓' if checksum_match else '✗'}")


def _display_drift_report(report, detailed: bool) -> None:
    """Display drift detection report."""
    from rich.table import Table

    # Overall status
    if report.overall_drift_detected:
        console.print("[yellow]Drift detected![/]")
    else:
        console.print("[green]No significant drift detected[/]")

    # Severity summary
    summary = report.severity_summary
    console.print(f"  Severity: {summary.get('high', 0)} high, {summary.get('medium', 0)} medium, {summary.get('low', 0)} low")

    # Numeric drift
    if report.numeric_drift:
        console.print("\n[bold]Numeric Drift[/]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Column", style="cyan")
        table.add_column("PSI", justify="right", width=10)
        table.add_column("Severity", width=10)
        table.add_column("Status", width=8)

        for col, drift in report.numeric_drift.items():
            psi = drift.get("psi", 0)
            severity = drift.get("severity", "low")
            detected = drift.get("drift_detected", False)

            status = "DRIFT" if detected else "OK"
            style = "red" if detected else "green"

            table.add_row(col, f"{psi:.4f}", severity, f"[{style}]{status}[/{style}]")

        console.print(table)

        if detailed:
            for col, drift in report.numeric_drift.items():
                if drift.get("drift_detected"):
                    b_stats = drift.get("baseline_stats", {})
                    c_stats = drift.get("current_stats", {})
                    console.print(f"\n[cyan]{col}[/] baseline vs current:")
                    console.print(f"  Mean: {b_stats.get('mean', 'N/A'):.4f} -> {c_stats.get('mean', 'N/A'):.4f}")
                    console.print(f"  Std:  {b_stats.get('std', 'N/A'):.4f} -> {c_stats.get('std', 'N/A'):.4f}")

    # Categorical drift
    if report.categorical_drift:
        console.print("\n[bold]Categorical Drift[/]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Column", style="cyan")
        table.add_column("PSI", justify="right", width=10)
        table.add_column("Chi²", justify="right", width=10)
        table.add_column("Severity", width=10)
        table.add_column("Status", width=8)

        for col, drift in report.categorical_drift.items():
            psi = drift.get("psi", 0)
            chi_sq = drift.get("chi_squared", 0)
            severity = drift.get("severity", "low")
            detected = drift.get("drift_detected", False)

            status = "DRIFT" if detected else "OK"
            style = "red" if detected else "green"

            table.add_row(col, f"{psi:.4f}", f"{chi_sq:.4f}", severity, f"[{style}]{status}[/{style}]")

        console.print(table)


def _display_schema_evolution(evolution) -> None:
    """Display schema evolution report."""
    from rich.table import Table

    # Summary
    summary = evolution.summary
    console.print(f"Schema changes: +{summary.get('added', 0)} -{summary.get('removed', 0)} ~{summary.get('type_changed', 0)}")

    # Breaking changes
    if evolution.breaking_changes:
        console.print("\n[red][bold]Breaking Changes:[/][/]")
        for change in evolution.breaking_changes:
            console.print(f"  - {change.column}: {change.change_type.value} ({change.old_value} -> {change.new_value})")

    # Added columns
    if evolution.added_columns:
        console.print("\n[bold]Added Columns[/]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Nullable", width=9)

        for col in evolution.added_columns:
            table.add_row(col.name, col.dtype, "Yes" if col.nullable else "No")

        console.print(table)

    # Removed columns
    if evolution.removed_columns:
        console.print("\n[bold]Removed Columns[/]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="green")
        table.add_column("Nullable", width=9)

        for col in evolution.removed_columns:
            table.add_row(col.name, col.dtype, "Yes" if col.nullable else "No")

        console.print(table)

    # Type changes
    if evolution.type_changes:
        console.print("\n[bold]Type Changes[/]")
        table = Table(show_header=True, header_style="bold")
        table.add_column("Column", style="cyan")
        table.add_column("Old Type", style="red")
        table.add_column("New Type", style="green")

        for change in evolution.type_changes:
            table.add_row(change.column, change.old_value or "", change.new_value or "")

        console.print(table)


# =============================================================================
# AUTH
# =============================================================================

@auth_app.command("status")
def auth_status() -> None:
    """Show authentication status for all sources."""
    sources = ["huggingface", "kaggle", "openml"]
    for s in sources:
        status = "✓" if check_credentials(s) else "✗"
        console.print(f"{status} {s}")


@auth_app.command("login")
def auth_login(
    source: str = typer.Argument(..., help="Source to configure"),
) -> None:
    """Configure credentials for a source."""
    if source == "huggingface":
        token = typer.prompt("Enter your HuggingFace token", hide_input=True)
        save_credentials("huggingface", token=token)
        console.print("[green]HuggingFace token saved[/]")
    elif source == "kaggle":
        username = typer.prompt("Enter your Kaggle username")
        key = typer.prompt("Enter your Kaggle API key", hide_input=True)
        save_credentials("kaggle", username=username, key=key)
        console.print("[green]Kaggle credentials saved[/]")
    elif source == "openml":
        api_key = typer.prompt("Enter your OpenML API key", hide_input=True)
        save_credentials("openml", token=api_key)
        console.print("[green]OpenML API key saved[/]")
    else:
        console.print(f"[red]Unknown source: {source}[/]")
        raise typer.Exit(1)


@auth_app.command("logout")
def auth_logout(
    source: str = typer.Argument(..., help="Source to remove credentials for"),
) -> None:
    """Remove credentials for a source."""
    clear_credentials(source)
    console.print(f"[green]Credentials cleared for {source}[/]")


@app.command("auth")
def auth_cmd(
    source: Optional[str] = typer.Argument(None, help="Source (huggingface, kaggle, openml)"),
) -> None:
    """Manage authentication credentials.

    Use subcommands: status, login, logout
    """
    if source:
        console.print(f"Use 'mldata auth login {source}' or 'mldata auth status'")
    else:
        from mldata.utils.auth import check_credentials

        table = Table(title="Authentication Status")
        table.add_column("Source", style="cyan")
        table.add_column("Status", style="green")

        sources = ["huggingface", "kaggle", "openml"]
        for s in sources:
            status = "✓ Configured" if check_credentials(s) else "✗ Not configured"
            table.add_row(s, status)

        console.print(table)


# =============================================================================
# DOCTOR
# =============================================================================

@app.command("doctor")
def doctor_cmd() -> None:
    """Diagnose configuration and connectivity issues."""
    from mldata.core.cache import CacheService

    console.print("[bold]mldata-cli Doctor[/]")
    console.print("-" * 40)

    # Check auth
    console.print("\n[bold]Authentication:[/]")
    for source in ["huggingface", "kaggle", "openml"]:
        status = "✓" if check_credentials(source) else "✗"
        console.print(f"  {status} {source}")

    # Check cache
    console.print("\n[bold]Cache:[/]")
    cache = CacheService()
    stats = cache.stats
    console.print(f"  Directory: {cache.cache_dir}")
    console.print(f"  Size: {stats['size_bytes'] / 1024 / 1024:.1f} MB / {stats['max_size_gb']} GB")
    console.print(f"  Entries: {stats['entries']}")


# =============================================================================
# CONFIG
# =============================================================================

@app.command("config")
def config_cmd(
    get: Optional[str] = typer.Option(None, "-g", "--get", help="Get a config value (e.g., 'build.default_format')"),
    set: Optional[str] = typer.Option(None, "-s", "--set", help="Set a config value (e.g., 'build.default_format parquet')"),
    path: bool = typer.Option(False, "-p", "--path", help="Show config file path"),
    show: bool = typer.Option(False, "-S", "--show", help="Show all configuration"),
) -> None:
    """Show or modify mldata-cli configuration.

    Use --get to view a value, --set to modify, or --show to see all.
    Create a project config with: mldata config --set build.default_format csv > mldata.yaml
    """
    from mldata.core.config import ConfigService

    service = ConfigService()
    config = service.get()

    if path:
        from mldata.core.config import Config
        config_path = Config._find_config()
        if config_path:
            console.print(str(config_path))
        else:
            console.print("No config file found")
        return

    if show:
        console.print("[bold]mldata-cli Configuration[/]")
        console.print("-" * 40)
        console.print(service.show())
        return

    if get:
        # Navigate to the value
        keys = get.split(".")
        obj = config
        for key in keys:
            if hasattr(obj, key):
                obj = getattr(obj, key)
            else:
                console.print(f"[red]Unknown config key: {get}[/]")
                return
        console.print(str(obj))
        return

    if set:
        parts = set.split(" ", 1)
        if len(parts) != 2:
            console.print("[red]Invalid format. Use: --set key value[/]")
            return
        key, value = parts
        try:
            service.set(key, value)
            console.print(f"[green]Set {key} = {value}[/]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/]")
        return

    # Default: show help
    console.print("[bold]mldata-cli Configuration[/]")
    console.print("-" * 40)
    console.print("Options:")
    console.print("  -g, --get <key>   Get a config value")
    console.print("  -s, --set <key> <value>  Set a config value")
    console.print("  -p, --path       Show config file path")
    console.print("  -S, --show       Show all configuration")
    console.print("")
    console.print("Common keys:")
    console.print("  build.default_format    Default export format (parquet, csv, jsonl)")
    console.print("  build.default_split     Default split ratios (e.g., 0.8,0.1,0.1)")
    console.print("  build.workers           Parallel workers (default: CPU count)")
    console.print("  build.compression       Default compression (snappy, gzip, zstd)")
    console.print("  cache.max_size_gb       Cache size limit in GB")
    console.print("")
    console.print("Config file locations (in priority order):")
    console.print("  1. ./mldata.yaml (project)")
    console.print("  2. ~/.config/mldata.yaml (user)")
    console.print("  3. ~/.mldata.yaml (legacy)")


# Add auth as a subcommand of main app
app.add_typer(auth_app, name="auth")


# =============================================================================
# COMMAND SUGGESTIONS & ERROR HANDLING
# =============================================================================

# Known commands for suggestion
KNOWN_COMMANDS = [
    "search", "info", "pull", "build", "validate", "drift", "profile", "split",
    "export", "rebuild", "diff", "auth", "config", "doctor", "version",
]

# Common typos/variations
COMMAND_ALIASES = {
    "get": "info",
    "download": "pull",
    "dl": "pull",
    "install": "pull",
    "check": "validate",
    "test": "validate",
    "verify": "validate",
    "run": "build",
    "make": "build",
    "compile": "build",
    "compare": "diff",
    "cmp": "diff",
    "status": "auth status",
    "login": "auth login",
    "logout": "auth logout",
    "help": None,  # Special case - --help is built-in
    "version": "version",
    "--version": "version",
    "-v": "version",
}


def _suggest_command(invalid_cmd: str) -> str | None:
    """Suggest a similar command for a typo."""
    # Check aliases first
    if invalid_cmd.lower() in COMMAND_ALIASES:
        suggestion = COMMAND_ALIASES[invalid_cmd.lower()]
        if suggestion:
            return suggestion
        return None

    # Calculate Levenshtein distance for fuzzy matching
    from difflib import SequenceMatcher

    best_match = None
    best_ratio = 0

    for cmd in KNOWN_COMMANDS:
        ratio = SequenceMatcher(None, invalid_cmd.lower(), cmd.lower()).ratio()
        if ratio > best_ratio and ratio > 0.5:  # Threshold for suggestion
            best_ratio = ratio
            best_match = cmd

    return best_match


def main() -> None:
    """Main entry point with error handling."""
    import sys
    import re
    import signal

    # Set up signal handler for graceful cancellation
    cancelled = False

    def signal_handler(signum, frame):
        nonlocal cancelled
        cancelled = True
        console.print("\n[yellow]Operation cancelled by user (Ctrl+C)[/]")
        console.print("[cyan]Cleaning up...[/]")

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        app()
    except SystemExit as e:
        # Handle cancellation exit code
        if e.code == 130:
            console.print("\n[yellow]Build cancelled[/]")
            console.print("Tip: Use --dry-run to preview builds without executing")
        raise
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Operation cancelled[/]")
        console.print("[cyan]Partial files may have been created.[/]")
        console.print("Tip: Use --dry-run to preview builds without executing")
        raise SystemExit(130)
    except Exception as e:
        error_msg = str(e)
        error_lower = error_msg.lower()

        # Provide helpful error messages for common issues
        if "no such command" in error_lower:
            # Extract the invalid command
            match = re.search(r"no such command: '(.+?)'", error_msg)
            if match:
                invalid_cmd = match.group(1)
                suggestion = _suggest_command(invalid_cmd)

                console.print(f"[red]Unknown command: {invalid_cmd}[/]")

                if suggestion:
                    console.print(f"[cyan]Did you mean: 'mldata {suggestion}'?[/]")
                else:
                    console.print("\n[bold]Available commands:[/]")
                    for cmd in sorted(KNOWN_COMMANDS):
                        console.print(f"  - {cmd}")

        elif "could not resolve path" in error_lower or "no such file or directory" in error_lower:
            console.print(f"[red]Error: Path not found[/]")
            console.print("[cyan]Tip: Check that the file or directory exists[/]")

        elif "connection" in error_lower or "network" in error_lower or "timeout" in error_lower:
            console.print(f"[red]Error: Network connection failed[/]")
            console.print("[cyan]Tip: Check your internet connection and try again[/]")

        elif "authentication" in error_lower or "credential" in error_lower or "api key" in error_lower:
            console.print(f"[red]Error: Authentication failed[/]")
            console.print("[cyan]Tip: Run 'mldata auth login <source>' to configure credentials[/]")

        else:
            console.print(f"[red]Error: {error_msg}[/]")

            # Suggest debugging steps for unexpected errors
            console.print("\n[cyan]For debugging:[/]")
            console.print("  1. Check that the path exists and is accessible")
            console.print("  2. Verify the file format is supported (CSV, Parquet, JSONL)")
            console.print("  3. Run 'mldata doctor' to check your configuration")

        raise SystemExit(1)


if __name__ == "__main__":
    main()
