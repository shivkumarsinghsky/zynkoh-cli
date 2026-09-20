"""
Tests for --fields parsing and validation (Section 7, Section 21).
"""

import pytest

from zynkoh_cli.validators.field_validator import FieldValidationError, parse_fields


class TestParseFields:
    def test_empty_input_returns_empty_list(self) -> None:
        assert parse_fields(None) == []
        assert parse_fields("") == []

    def test_single_field(self) -> None:
        fields = parse_fields("code:str")
        assert len(fields) == 1
        assert fields[0].name == "code"
        assert fields[0].type == "str"
        assert fields[0].nullable is False

    def test_multiple_fields(self) -> None:
        fields = parse_fields("code:str,name:str,department_id:uuid")
        assert [f.name for f in fields] == ["code", "name", "department_id"]

    def test_nullable_field_marker(self) -> None:
        fields = parse_fields("department_id:uuid?")
        assert fields[0].type == "uuid"
        assert fields[0].nullable is True

    def test_whitespace_is_trimmed(self) -> None:
        fields = parse_fields(" code : str , name : str ")
        assert fields[0].name == "code"
        assert fields[1].name == "name"


class TestFieldValidationErrors:
    def test_missing_colon_raises(self) -> None:
        with pytest.raises(FieldValidationError):
            parse_fields("code")

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(FieldValidationError):
            parse_fields("code:banana")

    def test_reserved_field_name_raises(self) -> None:
        with pytest.raises(FieldValidationError):
            parse_fields("tenant_id:str")

    def test_reserved_audit_field_raises(self) -> None:
        with pytest.raises(FieldValidationError):
            parse_fields("created_by:uuid")

    def test_duplicate_field_name_raises(self) -> None:
        with pytest.raises(FieldValidationError):
            parse_fields("code:str,code:int")

    def test_invalid_field_name_raises(self) -> None:
        with pytest.raises(FieldValidationError):
            parse_fields("123abc:str")