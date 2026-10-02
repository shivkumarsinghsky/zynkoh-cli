"""
Safe file-writing layer for all generators.

Centralizes dry-run handling, overwrite protection, and reporting so that
no generator ever writes to disk directly with open()/Path.write_text().

Every generator collects a list of (path, content) pairs, then hands them
to a FileWriter instance, which decides what actually happens.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from rich.console import Console
from rich.table import Table


class WriteStatus(StrEnum):
    CREATED = "created"
    SKIPPED = "skipped"
    CONFLICT = "conflict"
    OVERWRITTEN = "overwritten"
    DRY_RUN = "dry_run"


@dataclass
class WriteResult:
    path: Path
    status: WriteStatus


@dataclass
class FileWriter:
    """
    Collects planned writes and executes them according to dry_run/force
    settings, then reports results via Rich.

    Usage:
        writer = FileWriter(dry_run=False, force=False)
        writer.plan(Path("apps/modules/hrms/app/main.py"), content)
        writer.plan(Path("apps/modules/hrms/module.yaml"), content)
        results = writer.execute()
        writer.report(results)
    """

    dry_run: bool = False
    force: bool = False
    console: Console = field(default_factory=Console)

    _planned: list[tuple[Path, str, bool]] = field(default_factory=list, init=False)

    def plan(self, path: Path, content: str, *, always_overwrite: bool = False) -> None:
        """
        Queue a file to be written. Does not touch the filesystem yet.

        always_overwrite=True bypasses the conflict check regardless of
        --force. Use only for generator-internal, mechanically-merged
        files (manifests, package __init__.py stubs) — never for
        rendered business logic a developer might have hand-edited.
        """
        self._planned.append((path, content, always_overwrite))

    def execute(self) -> list[WriteResult]:
        """
        Write all planned files (unless dry_run), respecting overwrite
        protection. Returns a result per file for reporting.
        """
        results: list[WriteResult] = []

        for path, content, always_overwrite in self._planned:
            results.append(self._write_one(path, content, always_overwrite))

        return results

    def _write_one(self, path: Path, content: str, always_overwrite: bool) -> WriteResult:
        exists = path.exists()

        if self.dry_run:
            return WriteResult(path=path, status=WriteStatus.DRY_RUN)

        if exists and not self.force and not always_overwrite:
            return WriteResult(path=path, status=WriteStatus.CONFLICT)

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

        status = WriteStatus.OVERWRITTEN if exists else WriteStatus.CREATED
        return WriteResult(path=path, status=status)
   
    def report(self, results: list[WriteResult]) -> None:
        """Print a Rich table summarizing what happened."""
        table = Table(title="Generation Result")
        table.add_column("Status", style="bold")
        table.add_column("Path")

        status_styles = {
            WriteStatus.CREATED: "green",
            WriteStatus.OVERWRITTEN: "yellow",
            WriteStatus.SKIPPED: "dim",
            WriteStatus.CONFLICT: "red",
            WriteStatus.DRY_RUN: "cyan",
        }

        for result in results:
            style = status_styles.get(result.status, "white")
            table.add_row(
                f"[{style}]{result.status.value.upper()}[/{style}]",
                str(result.path),
            )

        self.console.print(table)

        conflicts = [r for r in results if r.status == WriteStatus.CONFLICT]
        if conflicts:
            self.console.print(
                f"\n[bold red]{len(conflicts)} file(s) already exist.[/bold red] "
                "Re-run with [bold]--force[/bold] to overwrite them.",
            )

    def has_conflicts(self, results: list[WriteResult]) -> bool:
        return any(r.status == WriteStatus.CONFLICT for r in results)