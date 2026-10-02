"""
Post-generation formatting.

Templates render import blocks whose order depends on which field types an
entity uses, so sorting them inside Jinja would be fragile. Instead, every
generator runs Ruff's import sorter and pyupgrade fixes over the Python files
it just wrote. Ruff picks up the generated module's own pyproject.toml, so the
output matches the lint rules the module ships with.

Formatting is best-effort: generation never fails because the formatter is
unavailable or exits non-zero; the files are already valid Python.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

RUFF_FIX_RULES = "I,UP,F401"


def format_python_files(paths: Iterable[Path]) -> bool:
    """Sort imports and apply safe pyupgrade fixes. Returns True if Ruff ran cleanly."""
    targets = sorted({str(p) for p in paths if p.suffix == ".py" and p.exists()})
    if not targets:
        return True
    try:
        completed = subprocess.run(
            [sys.executable, "-m", "ruff", "check", "--fix", "--quiet",
             "--select", RUFF_FIX_RULES, "--exit-zero", *targets],
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0
