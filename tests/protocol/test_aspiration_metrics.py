from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_search_response_includes_aspiration_fail_counts() -> None:
    client = _client()
    r = client.post("/api/games")
    assert r.status_code == 200
    game_id = r.json()["game_id"]

    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 3})
    assert r_search.status_code == 200
    data = r_search.json()
    assert "fail_high" in data and isinstance(data["fail_high"], int) and data["fail_high"] >= 0
    assert "fail_low" in data and isinstance(data["fail_low"], int) and data["fail_low"] >= 0
