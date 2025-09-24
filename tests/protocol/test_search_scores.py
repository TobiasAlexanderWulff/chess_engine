from __future__ import annotations

from fastapi.testclient import TestClient

from src.protocol.http.app import create_app


def _client() -> TestClient:
    return TestClient(create_app())


def test_search_returns_cp_score_for_normal_position() -> None:
    client = _client()
    # Create game in start position
    r = client.post("/api/games")
    assert r.status_code == 200
    game_id = r.json()["game_id"]

    # Depth 1 search should return a cp score (likely 0 in startpos)
    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 1})
    assert r_search.status_code == 200
    body = r_search.json()
    assert "score" in body and isinstance(body["score"], dict)
    # Must contain cp and not mate
    assert "cp" in body["score"]
    assert "mate" not in body["score"]


def test_search_returns_mate_score_when_mate() -> None:
    client = _client()
    # Create game, set a checkmate position (black to move checkmated)
    r = client.post("/api/games")
    game_id = r.json()["game_id"]
    mate_fen = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
    r_pos = client.post(f"/api/games/{game_id}/position", json={"fen": mate_fen})
    assert r_pos.status_code == 200

    r_search = client.post(f"/api/games/{game_id}/search", json={"depth": 2})
    assert r_search.status_code == 200
    body = r_search.json()
    assert "score" in body and isinstance(body["score"], dict)
    # Must contain mate and not cp
    assert "mate" in body["score"]
    assert "cp" not in body["score"]
    # Side to move is mated, so mate should be <= 0
    assert isinstance(body["score"]["mate"], int)
    assert body["score"]["mate"] <= 0
