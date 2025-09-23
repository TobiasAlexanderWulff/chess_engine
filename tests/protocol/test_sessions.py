from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_create_game_and_get_state() -> None:
    client = _client()
    r = client.post("/api/games")
    assert r.status_code == 200
    body = r.json()
    assert "game_id" in body and isinstance(body["game_id"], str) and body["game_id"]
    game_id = body["game_id"]
    assert body["fen"]

    # Fetch state
    r2 = client.get(f"/api/games/{game_id}/state")
    assert r2.status_code == 200
    state = r2.json()
    assert state["game_id"] == game_id
    assert state["fen"]
    assert isinstance(state["legal_moves"], list)


def test_get_state_unknown_id_404() -> None:
    client = _client()
    r = client.get("/api/games/does-not-exist/state")
    assert r.status_code == 404
    body = r.json()
    assert "error" in body
    assert body["error"]["code"] == "not_found"


def test_set_position_validation_and_success() -> None:
    client = _client()
    # Create
    r = client.post("/api/games")
    game_id = r.json()["game_id"]

    # Invalid FEN
    r_bad = client.post(f"/api/games/{game_id}/position", json={"fen": ""})
    assert r_bad.status_code == 400
    assert r_bad.json()["error"]["code"] == "bad_request"

    # Valid FEN (start position)
    start_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    r_ok = client.post(f"/api/games/{game_id}/position", json={"fen": start_fen})
    assert r_ok.status_code == 200
    state = r_ok.json()
    assert state["fen"] == start_fen


def test_move_endpoint_unimplemented_returns_501() -> None:
    client = _client()
    r = client.post("/api/games")
    game_id = r.json()["game_id"]

    r_move = client.post(f"/api/games/{game_id}/move", json={"move": "e2e4"})
    assert r_move.status_code == 501
    err = r_move.json()["error"]
    # 5xx maps to "internal_error" code in our envelope helper
    assert err["code"] == "internal_error"


def test_search_endpoint_shape() -> None:
    client = _client()
    r = client.post("/api/games")
    game_id = r.json()["game_id"]

    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 2})
    assert r_search.status_code == 200
    data = r_search.json()
    assert set(["best_move", "score", "pv", "nodes", "depth", "time_ms"]).issubset(data.keys())
    assert data["depth"] == 2
    assert isinstance(data["pv"], list)
