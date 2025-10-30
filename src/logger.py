"""
Logging configuration for Dokploy deployment action.
Provides structured logging with GitHub Actions integration.
"""

import os
import sys
from typing import Optional


class DeployLogger:
    """Logger with GitHub Actions annotations support."""

    def __init__(self, debug: bool = False):
        self.debug_mode = debug

    def debug(self, message: str) -> None:
        """Log debug message (only if debug mode enabled)."""
        if self.debug_mode:
            print(f"[DEBUG] {message}", file=sys.stderr)

    def info(self, message: str) -> None:
        """Log info message."""
        print(f"[INFO] {message}")

    def warning(self, message: str) -> None:
        """Log warning message with GitHub Actions annotation."""
        print(f"::warning::{message}")
        print(f"[WARNING] {message}", file=sys.stderr)

    def error(self, message: str) -> None:
        """Log error message with GitHub Actions annotation."""
        print(f"::error::{message}")
        print(f"[ERROR] {message}", file=sys.stderr)

    def group(self, title: str) -> 'LogGroup':
        """Create a collapsible group in GitHub Actions logs."""
        return LogGroup(title)

    def success(self, message: str) -> None:
        """Log success message."""
        print(f"[SUCCESS] ✓ {message}")


class LogGroup:
    """Context manager for GitHub Actions log groups."""

    def __init__(self, title: str):
        self.title = title

    def __enter__(self):
        print(f"::group::{self.title}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("::endgroup::")
        return False


def create_logger() -> DeployLogger:
    """Create logger instance from environment."""
    debug = os.getenv('INPUT_DEBUG', 'false').lower() == 'true'
    return DeployLogger(debug=debug)
