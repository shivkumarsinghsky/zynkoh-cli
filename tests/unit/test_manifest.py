"""
Tests for ModuleManifest (module.yaml) round-tripping and idempotent
appenders.
"""

from zynkoh_cli.models.manifest import ModuleManifest


def _make_manifest() -> ModuleManifest:
    return ModuleManifest(
        name="HRMS", code="hrms", description="Test", database_schema="hrms"
    )


class TestIdempotentAppenders:
    def test_add_permission_does_not_duplicate(self) -> None:
        manifest = _make_manifest()
        manifest.add_permission("hrms.employee.read")
        manifest.add_permission("hrms.employee.read")
        assert manifest.permissions == ["hrms.employee.read"]

    def test_add_event_does_not_duplicate(self) -> None:
        manifest = _make_manifest()
        manifest.add_event("EmployeeCreated")
        manifest.add_event("EmployeeCreated")
        assert len(manifest.events) == 1

    def test_add_route_appends(self) -> None:
        manifest = _make_manifest()
        manifest.add_route("/api/v1/hrms/employees", ["GET", "POST"])
        assert len(manifest.routes) == 1
        assert manifest.routes[0].path == "/api/v1/hrms/employees"


class TestYamlRoundTrip:
    def test_round_trip_preserves_data(self) -> None:
        manifest = _make_manifest()
        manifest.add_permission("hrms.employee.read")
        manifest.add_event("EmployeeCreated")

        yaml_str = manifest.to_yaml()
        restored = ModuleManifest.from_yaml(yaml_str)

        assert restored.code == "hrms"
        assert restored.permissions == ["hrms.employee.read"]
        assert restored.events[0].name == "EmployeeCreated"