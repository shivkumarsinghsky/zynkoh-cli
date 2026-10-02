"""
Jinja2 rendering layer.

Wraps a Jinja2 Environment pointed at the versioned templates/ directory.
Generators call TemplateRenderer.render(template_path, context)
and get back a rendered string — they never touch Jinja2 directly.
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

from zynkoh_cli.models.generation_context import GenerationContext


class TemplateRenderer:
    """
    Renders .j2 template files from templates/<version>/... using a
    GenerationContext as the template variables.

    StrictUndefined is used deliberately: a template referencing a typo'd
    or missing variable should fail loudly at render time, not silently
    render "None" or an empty string into generated source code.
    """

    def __init__(self, templates_root: Path | None = None) -> None:
        if templates_root is None:
            templates_root = self._default_templates_root()

        self._templates_root = templates_root
        self._env = Environment(
            loader=FileSystemLoader(str(templates_root)),
            undefined=StrictUndefined,
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    @staticmethod
    def _default_templates_root() -> Path:
        """Resolve the packaged templates/ directory inside zynkoh_cli."""
        package_files = resources.files("zynkoh_cli")
        return Path(str(package_files / "templates"))

    def render(self, template_relative_path: str, context: GenerationContext) -> str:
        """
        Render one template file.

        template_relative_path is relative to templates/, e.g.
            "v1/module/app/main.py.j2"

        Returns the rendered content as a string.
        """
        template = self._env.get_template(template_relative_path)
        return template.render(context=context)

    def list_templates(self, subdirectory: str) -> list[str]:
        """
        List all .j2 template files under templates/<subdirectory>/,
        relative to the templates root. Used by generators to discover
        every file a template set defines, so adding a new template file
        doesn't require also updating a hardcoded file list in Python.
        """
        target_dir = self._templates_root / subdirectory
        if not target_dir.exists():
            return []

        return sorted(
            str(p.relative_to(self._templates_root))
            for p in target_dir.rglob("*.j2")
        )