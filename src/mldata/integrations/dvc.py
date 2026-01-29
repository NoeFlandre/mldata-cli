"""DVC integration service."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DVCRResult:
    """Result of DVC operation."""
    success: bool
    dvc_path: Path | None = None
    error: str | None = None
    output: str = ""


class DVCService:
    """Service for DVC (Data Version Control) integration."""

    def __init__(self):
        """Initialize DVC service."""
        pass

    def is_installed(self) -> bool:
        """Check if DVC is installed.

        Returns:
            True if dvc command is available
        """
        try:
            subprocess.run(
                ["dvc", "--version"],
                capture_output=True,
                timeout=5.0,
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_version(self) -> Optional[str]:
        """Get DVC version.

        Returns:
            Version string or None if not installed
        """
        try:
            result = subprocess.run(
                ["dvc", "--version"],
                capture_output=True,
                timeout=5.0,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def generate_dvc_file(
        self,
        dataset_path: Path,
        manifest_hash: str,
        remote: Optional[str] = None,
    ) -> DVCRResult:
        """Generate a .dvc file for a dataset.

        Args:
            dataset_path: Path to the dataset directory
            manifest_hash: Hash from manifest.yaml
            remote: Optional DVC remote name

        Returns:
            DVCRResult with operation status
        """
        if not dataset_path.exists():
            return DVCRResult(
                success=False,
                error=f"Dataset path does not exist: {dataset_path}",
            )

        dvc_path = dataset_path.parent / f"{dataset_path.name}.dvc"

        # Build DVC file content
        dvc_content = {
            "outs": [
                {
                    "path": dataset_path.name,
                    "cache": True,
                    "md5": manifest_hash,
                }
            ]
        }

        # Add remote if specified
        if remote:
            dvc_content["outs"][0]["remote"] = remote

        # Write DVC file
        import yaml

        try:
            dvc_path.write_text(yaml.dump(dvc_content))
            return DVCRResult(
                success=True,
                dvc_path=dvc_path,
                output=f"Generated {dvc_path}",
            )
        except Exception as e:
            return DVCRResult(
                success=False,
                error=f"Failed to write DVC file: {e}",
            )

    def status(self, dataset_path: Path) -> DVCRResult:
        """Check DVC status for a path.

        Args:
            dataset_path: Path to dataset

        Returns:
            DVCRResult with status information
        """
        if not self.is_installed():
            return DVCRResult(
                success=False,
                error="DVC is not installed",
            )

        try:
            result = subprocess.run(
                ["dvc", "status", str(dataset_path)],
                capture_output=True,
                timeout=30.0,
                text=True,
            )

            return DVCRResult(
                success=result.returncode == 0,
                output=result.stdout + result.stderr,
            )
        except subprocess.TimeoutExpired:
            return DVCRResult(
                success=False,
                error="DVC status timed out",
            )
        except FileNotFoundError:
            return DVCRResult(
                success=False,
                error="DVC command not found",
            )

    def add_to_dvc(self, dataset_path: Path) -> DVCRResult:
        """Add a dataset to DVC tracking.

        Args:
            dataset_path: Path to dataset

        Returns:
            DVCRResult with operation status
        """
        if not self.is_installed():
            return DVCRResult(
                success=False,
                error="DVC is not installed. Install with: pip install dvc",
            )

        try:
            result = subprocess.run(
                ["dvc", "add", str(dataset_path)],
                capture_output=True,
                timeout=120.0,
                text=True,
            )

            dvc_path = dataset_path.parent / f"{dataset_path.name}.dvc"

            if result.returncode == 0:
                return DVCRResult(
                    success=True,
                    dvc_path=dvc_path,
                    output=result.stdout,
                )
            else:
                return DVCRResult(
                    success=False,
                    error=result.stderr,
                    output=result.stdout,
                )

        except subprocess.TimeoutExpired:
            return DVCRResult(
                success=False,
                error="DVC add timed out",
            )
        except FileNotFoundError:
            return DVCRResult(
                success=False,
                error="DVC command not found",
            )

    def get_push_instructions(self, dataset_path: Path) -> str:
        """Get instructions for pushing to DVC remote.

        Args:
            dataset_path: Path to dataset

        Returns:
            String with git/dvc commands to run
        """
        dvc_path = dataset_path.parent / f"{dataset_path.name}.dvc"

        instructions = [
            f"# Commands to version and push dataset with DVC:",
            "",
            f"# 1. Add to DVC tracking:",
            f"dvc add {dataset_path.name}",
            "",
            f"# 2. Commit DVC file:",
            f"git add {dvc_path.name} .gitignore",
            f"git commit -m 'Add {dataset_path.name} dataset'",
            "",
            f"# 3. Push to remote:",
            f"git push",
            f"dvc push",
            "",
            "# Note: Ensure DVC remote is configured:",
            "# dvc remote add -d myremote s3://bucket/path",
        ]

        return "\n".join(instructions)

    def verify_dvc_file(self, dvc_path: Path) -> bool:
        """Verify a .dvc file is valid.

        Args:
            dvc_path: Path to .dvc file

        Returns:
            True if file is valid YAML with expected structure
        """
        if not dvc_path.exists():
            return False

        import yaml

        try:
            content = yaml.safe_load(dvc_path.read_text())

            if not isinstance(content, dict):
                return False

            if "outs" not in content:
                return False

            outs = content["outs"]
            if not isinstance(outs, list) or len(outs) == 0:
                return False

            out = outs[0]
            if "path" not in out:
                return False

            return True

        except (yaml.YAMLError, KeyError, TypeError):
            return False
