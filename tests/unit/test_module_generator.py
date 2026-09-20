"""
Tests for ModuleGenerator's plan (Section 4) — asserts on the generator's
*intent* (which files, where) without touching the filesystem or Jinja2.
"""

from pathlib import Path

from zynkoh_cli.generators.module_generator import ModuleGenerator
from zynkoh_cli.models.generation_context import GenerationContext, NamingVariants


def _make_generator(tmp_modules_root: Path) -> ModuleGenerator:
    ctx = GenerationContext(module=NamingVariants.from_raw("hrms"))
    return ModuleGenerator(
        ctx, dry_run=True, force=False, modules_root=tmp_modules_root
    )


class TestPlanFiles:
    def test_plans_main_py(self, tmp_modules_root: Path) -> None:
        gen = _make_generator(tmp_modules_root)
        planned = gen.plan_files()
        output_paths = [p.output_path for p in planned]
        assert tmp_modules_root / "hrms" / "app" / "main.py" in output_paths

    def test_plans_into_correct_module_directory(self, tmp_modules_root: Path) -> None:
        gen = _make_generator(tmp_modules_root)
        planned = gen.plan_files()
        for p in planned:
            assert str(p.output_path).startswith(str(tmp_modules_root / "hrms"))

    def test_plan_files_has_no_side_effects(self, tmp_modules_root: Path) -> None:
        gen = _make_generator(tmp_modules_root)
        gen.plan_files()
        # Nothing should exist on disk yet — plan_files() must be pure.
        assert not (tmp_modules_root / "hrms").exists()


class TestManifestBuilding:
    def test_manifest_has_correct_code_and_schema(self, tmp_modules_root: Path) -> None:
        gen = _make_generator(tmp_modules_root)
        manifest = gen._build_manifest()
        assert manifest.code == "hrms"
        assert manifest.database_schema == "hrms"
        assert manifest.name == "HRMS"

    def test_manifest_tenant_strategy_reflects_context(
        self, tmp_modules_root: Path
    ) -> None:
        ctx = GenerationContext(
            module=NamingVariants.from_raw("hrms"), tenant_aware=False
        )
        gen = ModuleGenerator(
            ctx, dry_run=True, force=False, modules_root=tmp_modules_root
        )
        manifest = gen._build_manifest()
        assert manifest.tenant_strategy == "none"


class TestDryRunDoesNotWrite:
    def test_generate_with_dry_run_writes_nothing(self, tmp_modules_root: Path) -> None:
        gen = _make_generator(tmp_modules_root)
        gen.generate()
        assert not (tmp_modules_root / "hrms").exists()


class TestRealGenerationWritesFiles:
    def test_generate_without_dry_run_creates_module_yaml(
        self, tmp_modules_root: Path
    ) -> None:
        ctx = GenerationContext(module=NamingVariants.from_raw("crm"))
        gen = ModuleGenerator(
            ctx, dry_run=False, force=False, modules_root=tmp_modules_root
        )
        gen.generate()
        manifest_path = tmp_modules_root / "crm" / "module.yaml"
        assert manifest_path.exists()
        assert "code: crm" in manifest_path.read_text()