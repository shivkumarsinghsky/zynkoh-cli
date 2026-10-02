"""
Tests for module/entity name validation and existence checks.
"""

from pathlib import Path

import pytest

from zynkoh_cli.validators.module_validator import (
    ModuleValidationError,
    validate_entity_does_not_exist,
    validate_module_does_not_exist,
    validate_module_exists,
    validate_name,
)


class TestValidateName:
    def test_valid_name_passes(self) -> None:
        validate_name("hrms", kind="module name")  # should not raise

    def test_valid_hyphenated_name_passes(self) -> None:
        validate_name("work-order", kind="entity name")

    def test_empty_name_raises(self) -> None:
        with pytest.raises(ModuleValidationError):
            validate_name("", kind="module name")

    def test_reserved_name_raises(self) -> None:
        with pytest.raises(ModuleValidationError):
            validate_name("test", kind="module name")

    def test_python_keyword_raises(self) -> None:
        with pytest.raises(ModuleValidationError):
            validate_name("class", kind="module name")

    def test_invalid_characters_raise(self) -> None:
        with pytest.raises(ModuleValidationError):
            validate_name("hr ms", kind="module name")


class TestModuleExistence:
    def test_validate_module_does_not_exist_passes_when_absent(
        self, tmp_modules_root: Path
    ) -> None:
        validate_module_does_not_exist("hrms", tmp_modules_root)  # should not raise

    def test_validate_module_does_not_exist_raises_when_present(
        self, tmp_modules_root: Path
    ) -> None:
        (tmp_modules_root / "hrms").mkdir()
        with pytest.raises(ModuleValidationError):
            validate_module_does_not_exist("hrms", tmp_modules_root)

    def test_validate_module_exists_raises_when_absent(
        self, tmp_modules_root: Path
    ) -> None:
        with pytest.raises(ModuleValidationError):
            validate_module_exists("hrms", tmp_modules_root)

    def test_validate_module_exists_returns_path_when_present(
        self, tmp_modules_root: Path
    ) -> None:
        expected = tmp_modules_root / "hrms"
        expected.mkdir()
        assert validate_module_exists("hrms", tmp_modules_root) == expected


class TestEntityExistence:
    def test_passes_when_entity_file_absent(self, tmp_modules_root: Path) -> None:
        module_path = tmp_modules_root / "hrms"
        module_path.mkdir()
        validate_entity_does_not_exist("employee", module_path)  # should not raise

    def test_raises_when_entity_file_present(self, tmp_modules_root: Path) -> None:
        module_path = tmp_modules_root / "hrms"
        entities_dir = module_path / "app" / "domain" / "entities"
        entities_dir.mkdir(parents=True)
        (entities_dir / "employee.py").write_text("# exists")

        with pytest.raises(ModuleValidationError):
            validate_entity_does_not_exist("employee", module_path)