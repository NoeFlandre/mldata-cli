"""Git-LFS integration service."""

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class LFSResult:
    """Result of Git-LFS operation."""
    success: bool
    patterns_added: list[str] | None = None
    error: str | None = None
    output: str = ""

    def __post_init__(self):
        if self.patterns_added is None:
            self.patterns_added = []


class GitLFSService:
    """Service for Git-LFS integration."""

    # Default patterns for large files
    DEFAULT_PATTERNS = {
        "*.parquet": "Parquet dataset files",
        "*.csv": "CSV data files",
        "*.jsonl": "JSON Lines data files",
        "*.arrow": "Arrow data files",
        "*.feather": "Feather data files",
    }

    # Size thresholds for LFS tracking (in bytes)
    SIZE_THRESHOLDS = {
        ".csv": 10 * 1024 * 1024,  # 10 MB
        ".parquet": 10 * 1024 * 1024,  # 10 MB
        ".jsonl": 10 * 1024 * 1024,  # 10 MB
        ".arrow": 10 * 1024 * 1024,  # 10 MB
        ".feather": 10 * 1024 * 1024,  # 10 MB
    }

    def __init__(self):
        """Initialize Git-LFS service."""
        pass

    def is_installed(self) -> bool:
        """Check if Git-LFS is installed.

        Returns:
            True if git-lfs command is available
        """
        try:
            subprocess.run(
                ["git", "lfs", "version"],
                capture_output=True,
                timeout=5.0,
            )
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def is_in_repo(self, path: Path) -> bool:
        """Check if path is in a git repository.

        Args:
            path: Path to check

        Returns:
            True if in a git repo
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                cwd=path,
                capture_output=True,
                timeout=5.0,
                text=True,
            )
            return result.returncode == 0 and "true" in result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def get_git_root(self, path: Path) -> Optional[Path]:
        """Get the git repository root for a path.

        Args:
            path: Path within git repo

        Returns:
            Git root path or None
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=path,
                capture_output=True,
                timeout=5.0,
                text=True,
            )
            if result.returncode == 0:
                return Path(result.stdout.strip())
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def detect_large_files(self, dataset_path: Path) -> list[tuple[Path, str]]:
        """Detect files that should be tracked with LFS.

        Args:
            dataset_path: Path to dataset

        Returns:
            List of (file_path, reason) tuples
        """
        large_files = []

        if not dataset_path.exists():
            return large_files

        for ext, threshold in self.SIZE_THRESHOLDS.items():
            for file_path in dataset_path.rglob(f"*{ext}"):
                try:
                    size = file_path.stat().st_size
                    if size >= threshold:
                        large_files.append((file_path, f"{size / 1024 / 1024:.1f} MB"))
                except OSError:
                    continue

        return large_files

    def get_patterns_for_files(self, files: list[tuple[Path, str]]) -> set[str]:
        """Get Git-LFS patterns for given files.

        Args:
            files: List of (file_path, size_str) tuples

        Returns:
            Set of patterns to add
        """
        patterns = set()

        for file_path, _ in files:
            suffix = file_path.suffix.lower()
            pattern = f"*{suffix}"

            if pattern in self.DEFAULT_PATTERNS:
                patterns.add(pattern)

        return patterns

    def update_gitattributes(
        self,
        git_root: Path,
        patterns: set[str],
        auto_init: bool = True,
    ) -> LFSResult:
        """Update .gitattributes with LFS patterns.

        Args:
            git_root: Git repository root
            patterns: Patterns to add
            auto_init: Whether to initialize LFS if needed

        Returns:
            LFSResult with operation status
        """
        if not patterns:
            return LFSResult(
                success=True,
                patterns_added=[],
                output="No patterns to add",
            )

        gitattributes_path = git_root / ".gitattributes"

        # Read existing patterns
        existing_patterns = set()
        if gitattributes_path.exists():
            for line in gitattributes_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    # Extract pattern (first word before any space)
                    pattern = line.split()[0] if line.split() else ""
                    existing_patterns.add(pattern)

        # Find new patterns to add
        new_patterns = patterns - existing_patterns

        if not new_patterns:
            return LFSResult(
                success=True,
                patterns_added=[],
                output="All patterns already exist in .gitattributes",
            )

        # Add new patterns
        lines = []
        if gitattributes_path.exists():
            lines = gitattributes_path.read_text().splitlines()

        # Add header if file is new or empty
        if not lines:
            lines.append("# Git-LFS patterns for mldata-cli")
            lines.append("")

        for pattern in sorted(new_patterns):
            desc = self.DEFAULT_PATTERNS.get(pattern, "Large file")
            lines.append(f"{pattern} filter=lfs diff=lfs merge=lfs -text")
            lines.append(f"#   {desc}")

        # Write updated file
        try:
            gitattributes_path.write_text("\n".join(lines) + "\n")

            return LFSResult(
                success=True,
                patterns_added=sorted(new_patterns),
                output=f"Added {len(new_patterns)} patterns to {gitattributes_path}",
            )
        except Exception as e:
            return LFSResult(
                success=False,
                error=f"Failed to write .gitattributes: {e}",
            )

    def install_hooks(self, git_root: Path) -> LFSResult:
        """Install Git-LFS hooks.

        Args:
            git_root: Git repository root

        Returns:
            LFSResult with operation status
        """
        if not self.is_installed():
            return LFSResult(
                success=False,
                error="Git-LFS is not installed",
            )

        try:
            result = subprocess.run(
                ["git", "lfs", "install"],
                cwd=git_root,
                capture_output=True,
                timeout=30.0,
                text=True,
            )

            if result.returncode == 0:
                return LFSResult(
                    success=True,
                    output="Git-LFS hooks installed",
                )
            else:
                return LFSResult(
                    success=False,
                    error=result.stderr,
                )

        except subprocess.TimeoutExpired:
            return LFSResult(
                success=False,
                error="Git-LFS install timed out",
            )
        except FileNotFoundError:
            return LFSResult(
                success=False,
                error="Git-LFS command not found",
            )

    def configure_tracking(self, git_root: Path, dataset_path: Path) -> LFSResult:
        """Configure LFS tracking for a dataset.

        Args:
            git_root: Git repository root
            dataset_path: Path to dataset

        Returns:
            LFSResult with operation status
        """
        # Detect large files
        large_files = self.detect_large_files(dataset_path)
        patterns = self.get_patterns_for_files(large_files)

        if not patterns:
            # Use default patterns if no large files found
            patterns = set(self.DEFAULT_PATTERNS.keys())

        # Update .gitattributes
        result = self.update_gitattributes(git_root, patterns)

        if result.success and patterns:
            # Install hooks if not already installed
            hooks_result = self.install_hooks(git_root)
            if not hooks_result.success:
                result.output += f"\nWarning: {hooks_result.error}"

        return result

    def get_tracking_status(self, git_root: Path) -> dict:
        """Get current LFS tracking status.

        Args:
            git_root: Git repository root

        Returns:
            Dict with status information
        """
        status = {
            "lfs_installed": self.is_installed(),
            "in_repo": self.is_in_repo(git_root),
            "gitattributes_exists": (git_root / ".gitattributes").exists(),
            "lfs_patterns": [],
        }

        gitattributes_path = git_root / ".gitattributes"
        if gitattributes_path.exists():
            for line in gitattributes_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "filter=lfs" in line:
                    pattern = line.split()[0] if line.split() else ""
                    if pattern:
                        status["lfs_patterns"].append(pattern)

        return status

    def get_instructions(self, dataset_path: Path, git_root: Path) -> str:
        """Get instructions for setting up Git-LFS.

        Args:
            dataset_path: Path to dataset
            git_root: Git repository root

        Returns:
            String with instructions
        """
        large_files = self.detect_large_files(dataset_path)
        patterns = self.get_patterns_for_files(large_files)

        instructions = [
            "# Git-LFS Setup Instructions",
            "",
            "# 1. Install Git-LFS (if not already installed):",
            "git lfs install",
            "",
            "# 2. Configure patterns for large files:",
        ]

        if patterns:
            for pattern in sorted(patterns):
                instructions.append(f'git lfs track "*{pattern}"')
        else:
            instructions.append("# No large files detected, using default patterns:")
            for pattern in sorted(self.DEFAULT_PATTERNS.keys()):
                instructions.append(f'git lfs track "*{pattern}"')

        instructions.extend([
            "",
            "# 3. Update .gitattributes:",
            "git add .gitattributes",
            "",
            "# 4. Commit changes:",
            f"git commit -m 'Add Git-LFS tracking for {dataset_path.name}'",
            "",
            "# 5. Commit dataset files:",
            f"git add {dataset_path.name}/",
            f"git commit -m 'Add {dataset_path.name} dataset'",
            "",
            "# 6. Push to remote (files tracked by LFS will be pushed to LFS server):",
            "git push",
        ])

        return "\n".join(instructions)
