"""
Shared pytest fixtures for the zynkoh-cli test suite.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_modules_root(tmp_path: Path) -> Path:
    """A throwaway apps/modules/ directory for generator tests."""
    root = tmp_path / "apps" / "modules"
    root.mkdir(parents=True)
    return root