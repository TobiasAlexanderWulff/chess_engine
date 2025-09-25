from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_search_includes_iteration_stats() -> None:
    client = _client()
    r = client.post("/api/games")
    assert r.status_code == 200
    game_id = r.json()["game_id"]

    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 3, "movetime_ms": 10})
    assert r_search.status_code == 200
    data = r_search.json()

    assert "iters" in data and isinstance(data["iters"], list)
    iters = data["iters"]
    assert len(iters) >= 1
    # Entries contain required numeric fields
    for it in iters:
        assert isinstance(it.get("depth"), int)
        assert isinstance(it.get("time_ms"), int)
        assert isinstance(it.get("nodes"), int)
        assert isinstance(it.get("qnodes"), int)
        assert isinstance(it.get("fail_high"), int)
        assert isinstance(it.get("fail_low"), int)

    # The last iteration depth should equal overall reported depth
    assert iters[-1]["depth"] == data["depth"]
