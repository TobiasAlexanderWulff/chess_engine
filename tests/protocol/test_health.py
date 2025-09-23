from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def test_healthz_ok() -> None:
    client = TestClient(create_app())
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
    assert "x-request-id" in r.headers
