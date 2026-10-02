"""
BaseGenerator: shared orchestration for all concrete generators.

A concrete generator's job is narrow: given a GenerationContext, decide
*which* template files to render and *where* they go. Everything else —
dry-run handling, overwrite protection, rendering, writing, reporting,
and manifest updates — lives here, once.

This is what makes generators testable in isolation: a test
can subclass BaseGenerator with a fake plan_files() and assert on the
FileWriter's planned output, without touching the real filesystem.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from zynkoh_cli.models.generation_context import GenerationContext
from zynkoh_cli.models.manifest import ModuleManifest
from zynkoh_cli.utils.file_writer import FileWriter, WriteResult, WriteStatus
from zynkoh_cli.utils.formatter import format_python_files
from zynkoh_cli.utils.renderer import TemplateRenderer


@dataclass
class PlannedFile:
    """One (template, output-path) pair a generator wants rendered."""

    template_relative_path: str
    output_path: Path


class BaseGenerator(ABC):
    """
    Subclass and implement plan_files() to describe what gets generated.

    Concrete generators should NOT call FileWriter or TemplateRenderer
    directly — call self.generate() and let the base class orchestrate.
    """

    def __init__(
        self,
        context: GenerationContext,
        *,
        dry_run: bool = False,
        force: bool = False,
        renderer: TemplateRenderer | None = None,
    ) -> None:
        self.context = context
        self.dry_run = dry_run
        self.force = force
        self.renderer = renderer or TemplateRenderer()
        self.writer = FileWriter(dry_run=dry_run, force=force)

    @abstractmethod
    def plan_files(self) -> list[PlannedFile]:
        """
        Return every (template, output_path) pair this generator produces.

        Must not have side effects — no filesystem writes here. This is
        purely a description of intent, which is what makes dry-run and
        testing possible: the same plan can be inspected without executing
        it.
        """
        raise NotImplementedError

    def update_manifest(self, manifest: ModuleManifest) -> None:
        """
        Optionally mutate the module's manifest (add permissions, events,
        routes). Default no-op — module_generator overrides this to build
        a fresh manifest; feature/crud generators override it to append
        to an existing one.
        """
        return

    def plan_extra_files(self) -> list[tuple[Path, str]]:
        """
        Optional: return (output_path, content) pairs whose content is
        built directly in Python rather than rendered from a .j2 template.

        Used for things like module.yaml, where a typed model + to_yaml()
        is safer than hand-templating YAML. Default: none.
        """
        return []
    
    def plan_appends(self) -> list[tuple[Path, str, str]]:
        """
        Optional: return (file_path, marker_line, content_to_append) triples.

        If marker_line is not already present in file_path's content, appends
        content_to_append to the end of the file. Idempotent: re-running the
        same generator against the same feature won't duplicate the append.
        Default: none.
        """
        return []

    def generate(self) -> list[WriteResult]:
        """
        The full orchestration: plan -> render -> queue -> write -> report.

        Returns the list of WriteResults so commands/*.py can decide
        whether to treat conflicts as a hard failure (e.g. exit code 1
        for CI/CD use).
        """
        planned_files = self.plan_files()

        for planned in planned_files:
            content = self.renderer.render(
                planned.template_relative_path, self.context
            )
            self.writer.plan(planned.output_path, content)

        for output_path, content in self.plan_extra_files():
            self.writer.plan(output_path, content, always_overwrite=True)

        appended = self._apply_appends()

        results = self.writer.execute()
        if not self.dry_run:
            written = [
                r.path
                for r in results
                if r.status in (WriteStatus.CREATED, WriteStatus.OVERWRITTEN)
            ]
            format_python_files([*written, *appended])
        self.writer.report(results)
        return results

    def _apply_appends(self) -> list[Path]:
        """
        Appends are applied directly (not dry-run-safe individually) but
        skipped entirely in dry-run mode, matching FileWriter's contract.
        """
        appended: list[Path] = []
        if self.dry_run:
            return appended

        for file_path, marker_line, content_to_append in self.plan_appends():
            if not file_path.exists():
                continue

            existing = file_path.read_text(encoding="utf-8")
            if marker_line in existing:
                continue  # already appended — idempotent re-run

            file_path.write_text(existing.rstrip("\n") + "\n" + content_to_append + "\n", encoding="utf-8")
            appended.append(file_path)
        return appended

    def has_conflicts(self, results: list[WriteResult]) -> bool:
        return self.writer.has_conflicts(results)