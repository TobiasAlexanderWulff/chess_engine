from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_tt_policy_and_metrics_present() -> None:
    client = _client()
    r = client.post("/api/games")
    assert r.status_code == 200
    game_id = r.json()["game_id"]

    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 3})
    assert r_search.status_code == 200
    data = r_search.json()

    # Basic TT metrics
    for key in (
        "tt_probes",
        "tt_hits",
        "tt_exact_hits",
        "tt_lower_hits",
        "tt_upper_hits",
        "tt_stores",
        "tt_replacements",
        "tt_size",
    ):
        assert key in data and isinstance(data[key], int) and data[key] >= 0

    # Hit categories add up to hits
    assert data["tt_exact_hits"] + data["tt_lower_hits"] + data["tt_upper_hits"] == data["tt_hits"]
    # Probes at least hits
    assert data["tt_probes"] >= data["tt_hits"]


def test_tt_max_entries_caps_table_size() -> None:
    client = _client()
    r = client.post("/api/games")
    assert r.status_code == 200
    game_id = r.json()["game_id"]

    # Set a very small TT cap; at depth 3 we will exceed this without eviction
    cap = 64
    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 3, "tt_max_entries": cap})
    assert r_search.status_code == 200
    data = r_search.json()
    assert data["tt_size"] <= cap
