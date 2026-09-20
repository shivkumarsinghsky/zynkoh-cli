"""
Tests for the naming conversion engine (Section 5).
"""

from zynkoh_cli.utils import naming


class TestSnakeCase:
    def test_kebab_to_snake(self) -> None:
        assert naming.to_snake_case("work-order") == "work_order"

    def test_pascal_to_snake(self) -> None:
        assert naming.to_snake_case("InfrastructureMonitoring") == "infrastructure_monitoring"

    def test_already_snake(self) -> None:
        assert naming.to_snake_case("employee") == "employee"


class TestPascalCase:
    def test_kebab_to_pascal(self) -> None:
        assert naming.to_pascal_case("work-order") == "WorkOrder"

    def test_snake_to_pascal(self) -> None:
        assert naming.to_pascal_case("field_service_management") == "FieldServiceManagement"


class TestKebabCase:
    def test_snake_to_kebab(self) -> None:
        assert naming.to_kebab_case("work_order") == "work-order"


class TestPluralization:
    def test_regular_pluralization(self) -> None:
        assert naming.to_snake_plural("employee") == "employees"

    def test_compound_word_pluralizes_last_word_only(self) -> None:
        assert naming.to_snake_plural("work-order") == "work_orders"

    def test_irregular_plural_status(self) -> None:
        assert naming.to_snake_plural("status") == "statuses"

    def test_irregular_plural_person(self) -> None:
        assert naming.to_snake_plural("person") == "people"

    def test_pascal_plural(self) -> None:
        assert naming.to_pascal_plural("work-order") == "WorkOrders"

    def test_kebab_plural(self) -> None:
        assert naming.to_kebab_plural("work_order") == "work-orders"


class TestHumanReadable:
    def test_regular_words(self) -> None:
        assert naming.to_human_readable("work-order") == "Work Order"

    def test_known_acronym(self) -> None:
        assert naming.to_human_readable("hrms") == "HRMS"

    def test_mixed_acronym_and_word(self) -> None:
        # Only exact-match acronym words are uppercased; unknown words
        # still get Title Case.
        assert naming.to_human_readable("crm-integration") == "CRM Integration"


class TestEdgeCases:
    def test_empty_string_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            naming.to_snake_case("")

    def test_whitespace_only_raises(self) -> None:
        import pytest

        with pytest.raises(ValueError):
            naming.to_snake_case("   ")