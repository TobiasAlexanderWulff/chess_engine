from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_undo_without_moves_returns_400() -> None:
    client = _client()
    r = client.post("/api/games")
    game_id = r.json()["game_id"]

    r_undo = client.post(f"/api/games/{game_id}/undo")
    assert r_undo.status_code == 400
    body = r_undo.json()
    assert body["error"]["code"] == "bad_request"
    assert "no moves" in body["error"]["message"].lower()


def test_undo_restores_prior_state() -> None:
    client = _client()
    r = client.post("/api/games")
    game_id = r.json()["game_id"]
    start_fen = r.json()["fen"]

    # Make a legal move e2e4
    r_move = client.post(f"/api/games/{game_id}/move", json={"move": "e2e4"})
    assert r_move.status_code == 200
    fen_after = r_move.json()["fen"]
    assert " b " in fen_after

    # Undo
    r_undo = client.post(f"/api/games/{game_id}/undo")
    assert r_undo.status_code == 200
    state = r_undo.json()
    assert state["fen"] == start_fen
    assert isinstance(state["legal_moves"], list) and state["legal_moves"]
    assert state["last_move"] is None
    assert state["move_history"] == []
