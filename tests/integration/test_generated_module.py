"""
End-to-end tests: run the real CLI, then import and exercise the generated FastAPI module.

The unit tests assert on planned file lists; these tests prove the rendered code
actually imports, lints and behaves correctly against a database (SQLite in memory,
standing in for the platform's PostgreSQL session factory).
"""

from __future__ import annotations

import subprocess
import sys
import uuid
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import Any

import pytest
from typer.testing import CliRunner

from zynkoh_cli.main import app as cli

runner = CliRunner()

ASSET_FIELDS = (
    "code:str,name:str,category:str,serial_number:str?,"
    "purchase_cost:decimal?,installed_on:date?,active:bool,meta:json?"
)
WORK_ORDER_FIELDS = "asset_id:uuid,description:text,status:str,due:datetime?,priority:int,score:float?"


def zynkoh(*args: str) -> Any:
    return runner.invoke(cli, list(args))


@pytest.fixture(scope="module")
def module_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("backend") / "apps" / "modules"
    common = ["--modules-root", str(root)]
    assert zynkoh("create", "module", "eam", *common).exit_code == 0
    assert zynkoh("create", "crud", "asset", "--module", "eam", "--fields", ASSET_FIELDS, *common).exit_code == 0
    result = zynkoh(
        "create", "feature", "work-order", "--module", "eam", "--fields", WORK_ORDER_FIELDS, *common
    )
    assert result.exit_code == 0, result.output
    assert zynkoh(
        "create", "crud", "lead", "--module", "eam", "--no-soft-delete", "--fields", "name:str,score:int?", *common
    ).exit_code == 0
    assert zynkoh("create", "entity", "location", "--module", "eam", *common).exit_code == 0
    return root / "eam"


def _purge_app_modules() -> None:
    for name in list(sys.modules):
        if name == "app" or name.startswith("app."):
            del sys.modules[name]


@pytest.fixture(scope="module")
def client(module_dir: Path) -> Iterator[Any]:
    from fastapi.testclient import TestClient
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    _purge_app_modules()
    sys.path.insert(0, str(module_dir))
    try:
        from app.api.dependencies import get_db
        from app.infrastructure.persistence.base import Base
        from app.main import app as api

        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        session_factory = async_sessionmaker(engine, expire_on_commit=False)

        async def create_schema() -> None:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

        async def db() -> AsyncIterator[AsyncSession]:
            # The unit-of-work contract documented in the generated get_db().
            async with session_factory() as session:
                try:
                    yield session
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise

        api.dependency_overrides[get_db] = db
        with TestClient(api) as test_client:
            test_client.portal.call(create_schema)
            yield test_client
    finally:
        sys.path.remove(str(module_dir))
        _purge_app_modules()


@pytest.fixture
def tenant() -> dict[str, str]:
    return {"X-Tenant-Id": str(uuid.uuid4())}


def new_asset(client: Any, tenant: dict[str, str], **overrides: Any) -> dict[str, Any]:
    body = {"code": "P-1", "name": "Pump", "category": "pump", "active": True}
    body.update(overrides)
    response = client.post("/api/v1/eam/assets", headers=tenant, json=body)
    assert response.status_code == 201, response.text
    return dict(response.json())


def test_generated_code_passes_its_own_lint_rules(module_dir: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(module_dir)],
        capture_output=True, text=True, check=False, cwd=module_dir,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_openapi_lists_generated_routes(client: Any) -> None:
    paths = set(client.get("/openapi.json").json()["paths"])
    assert {"/api/v1/eam/assets", "/api/v1/eam/assets/{entity_id}",
            "/api/v1/eam/work-orders", "/api/v1/eam/leads"} <= paths


def test_create_and_read_back_preserves_types(client: Any, tenant: dict[str, str]) -> None:
    created = new_asset(client, tenant, purchase_cost="1234.5678",
                        installed_on="2024-05-01", meta={"site": "north"})
    fetched = client.get(f"/api/v1/eam/assets/{created['id']}", headers=tenant).json()
    assert fetched["purchase_cost"] == "1234.5678"  # Decimal, not float
    assert fetched["installed_on"] == "2024-05-01"  # date, not datetime
    assert fetched["meta"] == {"site": "north"}


def test_list_filters_by_typed_values_and_sorts(client: Any, tenant: dict[str, str]) -> None:
    new_asset(client, tenant, code="A", name="Alpha", installed_on="2024-01-01", purchase_cost="10.5")
    new_asset(client, tenant, code="B", name="Bravo", installed_on="2024-02-01")
    by_date = client.get("/api/v1/eam/assets", headers=tenant, params={"installed_on": "2024-01-01"})
    assert [a["code"] for a in by_date.json()] == ["A"]
    by_cost = client.get("/api/v1/eam/assets", headers=tenant, params={"purchase_cost": "10.5"})
    assert [a["code"] for a in by_cost.json()] == ["A"]
    sorted_desc = client.get("/api/v1/eam/assets", headers=tenant, params={"sort_by": "name", "sort_desc": True})
    assert [a["name"] for a in sorted_desc.json()] == ["Bravo", "Alpha"]


@pytest.mark.parametrize("sort_by", ["name; drop table assets", "meta", "tenant_id"])
def test_sort_field_must_be_on_the_allowlist(client: Any, tenant: dict[str, str], sort_by: str) -> None:
    response = client.get("/api/v1/eam/assets", headers=tenant, params={"sort_by": sort_by})
    assert response.status_code == 400


def test_tenants_are_isolated(client: Any, tenant: dict[str, str]) -> None:
    asset = new_asset(client, tenant)
    other = {"X-Tenant-Id": str(uuid.uuid4())}
    assert client.get(f"/api/v1/eam/assets/{asset['id']}", headers=other).status_code == 404
    assert client.get("/api/v1/eam/assets", headers=other).json() == []
    assert client.delete(f"/api/v1/eam/assets/{asset['id']}", headers=other).status_code == 404
    assert client.get(f"/api/v1/eam/assets/{asset['id']}", headers=tenant).status_code == 200


def test_missing_tenant_header_is_rejected(client: Any) -> None:
    assert client.get("/api/v1/eam/assets").status_code == 400


def test_update_and_missing_entities_return_404(client: Any, tenant: dict[str, str]) -> None:
    asset = new_asset(client, tenant)
    body = {"code": "P-1", "name": "Pump v2", "category": "pump", "active": False}
    updated = client.put(f"/api/v1/eam/assets/{asset['id']}", headers=tenant, json=body)
    assert updated.status_code == 200 and updated.json()["name"] == "Pump v2"
    missing = client.put(f"/api/v1/eam/assets/{uuid.uuid4()}", headers=tenant, json=body)
    assert missing.status_code == 404


def test_soft_delete_hides_entity_from_reads(client: Any, tenant: dict[str, str]) -> None:
    asset = new_asset(client, tenant)
    assert client.delete(f"/api/v1/eam/assets/{asset['id']}", headers=tenant).status_code == 204
    assert client.get(f"/api/v1/eam/assets/{asset['id']}", headers=tenant).status_code == 404
    assert client.get("/api/v1/eam/assets", headers=tenant).json() == []
    assert client.delete(f"/api/v1/eam/assets/{asset['id']}", headers=tenant).status_code == 404


def test_hard_delete_resource(client: Any, tenant: dict[str, str]) -> None:
    lead = client.post("/api/v1/eam/leads", headers=tenant, json={"name": "Acme"}).json()
    assert client.delete(f"/api/v1/eam/leads/{lead['id']}", headers=tenant).status_code == 204
    assert client.get(f"/api/v1/eam/leads/{lead['id']}", headers=tenant).status_code == 404


def test_feature_resource_round_trip(client: Any, tenant: dict[str, str]) -> None:
    body = {"asset_id": str(uuid.uuid4()), "description": "Replace seal", "status": "open",
            "priority": 2, "due": "2024-06-01T09:00:00Z"}
    created = client.post("/api/v1/eam/work-orders", headers=tenant, json=body)
    assert created.status_code == 201, created.text
    listed = client.get("/api/v1/eam/work-orders", headers=tenant).json()
    assert [w["description"] for w in listed] == ["Replace seal"]


def test_generated_module_tests_pass(module_dir: Path) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(module_dir / "tests")],
        capture_output=True, text=True, check=False, cwd=module_dir,
    )
    assert completed.returncode == 0, completed.stdout[-2000:]


@pytest.mark.parametrize("command", ["crud", "feature"])
def test_no_tenant_aware_is_rejected_for_tenant_scoped_generators(tmp_path: Path, command: str) -> None:
    root = tmp_path / "apps" / "modules"
    assert zynkoh("create", "module", "crm", "--modules-root", str(root)).exit_code == 0
    result = zynkoh("create", command, "lead", "--module", "crm", "--fields", "name:str",
                    "--no-tenant-aware", "--modules-root", str(root))
    assert result.exit_code == 1
    assert "not supported" in result.output
    assert not (root / "crm" / "app" / "domain" / "entities" / "lead.py").exists()
