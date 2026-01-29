"""Progress utilities."""

import time
from typing import Iterator

from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
    SpinnerColumn,
)


def create_progress_bar(description: str, total: int | None = None) -> Progress:
    """Create a progress bar with standard columns.

    Args:
        description: Task description
        total: Total units (bytes or items)

    Returns:
        Rich Progress instance
    """
    return Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None, complete_style="green", finished_style="green"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        expand=True,
    )


def create_download_progress() -> Progress:
    """Create a progress bar for downloads with ETA.

    Returns:
        Rich Progress instance optimized for downloads
    """
    return Progress(
        SpinnerColumn(style="cyan"),
        TextColumn("[bold cyan]Downloading[/]"),
        BarColumn(bar_width=None, complete_style="green", finished_style="green"),
        TaskProgressColumn(),
        DownloadColumn(),
        TransferSpeedColumn(),
        TimeRemainingColumn(),
        expand=True,
    )


def create_processing_progress() -> Progress:
    """Create a progress bar for processing operations.

    Returns:
        Rich Progress instance for processing
    """
    return Progress(
        SpinnerColumn(style="magenta"),
        TextColumn("[bold magenta]Processing[/]"),
        BarColumn(bar_width=None, complete_style="cyan", finished_style="green"),
        TaskProgressColumn(),
        TextColumn("[cyan]{task.completed}/{task.total}[/]"),
        TransferSpeedColumn(),
        expand=True,
    )


class DownloadProgressTracker:
    """Track download progress with ETA calculation."""

    def __init__(self, description: str, total_bytes: int | None = None):
        self.description = description
        self.total_bytes = total_bytes
        self.current_bytes = 0
        self.speed_bytes_per_sec = 0.0
        self.start_bytes = 0
        self.start_time = 0.0
        self.eta_seconds: float | None = None

    def update(self, bytes_delta: int, elapsed: float) -> None:
        """Update progress with new bytes and elapsed time."""
        self.current_bytes += bytes_delta

        if elapsed > 0:
            self.speed_bytes_per_sec = bytes_delta / elapsed

        if self.total_bytes and self.total_bytes > 0:
            remaining = self.total_bytes - self.current_bytes
            if self.speed_bytes_per_sec > 0:
                self.eta_seconds = remaining / self.speed_bytes_per_sec
            else:
                self.eta_seconds = None


class ProcessingTracker:
    """Track processing progress with time estimation."""

    def __init__(self, description: str, total_items: int | None = None):
        self.description = description
        self.total_items = total_items
        self.completed_items = 0
        self.start_time = time.time()
        self.last_update = self.start_time
        self.items_per_sec = 0.0
        self.eta_seconds: float | None = None

    def update(self, items_completed: int = 1) -> None:
        """Update progress with completed items.

        Args:
            items_completed: Number of items completed since last update
        """
        current_time = time.time()
        elapsed = current_time - self.last_update

        self.completed_items += items_completed
        self.last_update = current_time

        if elapsed > 0:
            self.items_per_sec = items_completed / elapsed

        if self.total_items and self.total_items > 0:
            remaining = self.total_items - self.completed_items
            if self.items_per_sec > 0:
                self.eta_seconds = remaining / self.items_per_sec
            else:
                self.eta_seconds = None

    def get_eta_formatted(self) -> str:
        """Get ETA as formatted string.

        Returns:
            Formatted ETA string (e.g., "2m 30s" or "--")
        """
        if self.eta_seconds is None:
            return "--"

        if self.eta_seconds < 60:
            return f"{int(self.eta_seconds)}s"
        elif self.eta_seconds < 3600:
            minutes = int(self.eta_seconds // 60)
            seconds = int(self.eta_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(self.eta_seconds // 3600)
            minutes = int((self.eta_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def get_speed_formatted(self) -> str:
        """Get processing speed as formatted string.

        Returns:
            Formatted speed string (e.g., "150 items/s")
        """
        if self.items_per_sec < 1:
            return f"{self.items_per_sec:.2f} items/s"
        elif self.items_per_sec < 1000:
            return f"{self.items_per_sec:.1f} items/s"
        else:
            return f"{self.items_per_sec / 1000:.1f}k items/s"
