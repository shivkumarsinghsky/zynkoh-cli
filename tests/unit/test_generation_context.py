"""
Tests for GenerationContext computed properties.
"""

from zynkoh_cli.models.generation_context import GenerationContext, NamingVariants


class TestPermissionPrefix:
    def test_with_entity(self) -> None:
        ctx = GenerationContext(
            module=NamingVariants.from_raw("hrms"),
            entity=NamingVariants.from_raw("employee"),
        )
        assert ctx.permission_prefix == "hrms.employee"

    def test_without_entity(self) -> None:
        ctx = GenerationContext(module=NamingVariants.from_raw("hrms"))
        assert ctx.permission_prefix == "hrms"


class TestApiPath:
    def test_simple_entity(self) -> None:
        ctx = GenerationContext(
            module=NamingVariants.from_raw("hrms"),
            entity=NamingVariants.from_raw("employee"),
        )
        assert ctx.api_path == "/api/v1/hrms/employees"

    def test_hyphenated_entity_uses_kebab_case(self) -> None:
        ctx = GenerationContext(
            module=NamingVariants.from_raw("eam"),
            entity=NamingVariants.from_raw("work-order"),
        )
        assert ctx.api_path == "/api/v1/eam/work-orders"

    def test_hyphenated_module_uses_kebab_case(self) -> None:
        ctx = GenerationContext(
            module=NamingVariants.from_raw("field-service-management"),
            entity=NamingVariants.from_raw("dispatch"),
        )
        assert ctx.api_path == "/api/v1/field-service-management/dispatches"