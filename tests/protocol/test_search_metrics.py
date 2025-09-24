from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_search_response_includes_metrics() -> None:
    client = _client()
    r = client.post("/api/games")
    assert r.status_code == 200
    game_id = r.json()["game_id"]

    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 2})
    assert r_search.status_code == 200
    data = r_search.json()
    # Ensure metrics present and are non-negative integers
    assert "nodes" in data and isinstance(data["nodes"], int) and data["nodes"] >= 0
    assert "qnodes" in data and isinstance(data["qnodes"], int) and data["qnodes"] >= 0
    assert "tt_hits" in data and isinstance(data["tt_hits"], int) and data["tt_hits"] >= 0
    assert "tt_probes" in data and isinstance(data["tt_probes"], int) and data["tt_probes"] >= 0
    # probes should be >= hits
    assert data["tt_probes"] >= data["tt_hits"]
    # qnodes should not exceed nodes
    assert data["qnodes"] <= data["nodes"]
