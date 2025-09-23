from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .error import exception_handler
from .logging_middleware import RequestIDLoggingMiddleware
from ...engine.game import Game
from ...engine.move import parse_uci
from ...search.service import SearchService


logger = logging.getLogger(__name__)


class CreateGameResponse(BaseModel):
    game_id: str
    fen: str


class SetPositionRequest(BaseModel):
    fen: str = Field(..., description="FEN string")


class MoveRequest(BaseModel):
    move: str = Field(..., description="UCI move string, e.g., e2e4")


class SearchRequest(BaseModel):
    depth: Optional[int] = Field(default=None, ge=1, le=64)
    movetime_ms: Optional[int] = Field(default=None, ge=1)


class GameState(BaseModel):
    game_id: str
    fen: str
    legal_moves: list[str]


def create_app() -> FastAPI:
    app = FastAPI(title="Chess Engine API", version="0.0.1")

    # Basic logging setup
    logging.basicConfig(level=logging.INFO)

    # Middleware & error handling
    app.add_middleware(RequestIDLoggingMiddleware)
    app.add_exception_handler(Exception, exception_handler)

    # In-memory single-session placeholder (Plan 5 will add sessions)
    state: Dict[str, Game] = {}

    @app.get("/healthz")
    async def healthz() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/games", response_model=CreateGameResponse)
    async def create_game() -> CreateGameResponse:
        # Placeholder: single game with fixed ID until sessions are added (Plan 5)
        game_id = "default"
        game = Game.new()
        state[game_id] = game
        return CreateGameResponse(game_id=game_id, fen=game.to_fen())

    @app.get("/api/games/{game_id}/state", response_model=GameState)
    async def get_state(game_id: str) -> GameState:
        game = _require_game(state, game_id)
        return GameState(
            game_id=game_id,
            fen=game.to_fen(),
            legal_moves=[m.to_uci() for m in game.legal_moves()],
        )

    @app.post("/api/games/{game_id}/position", response_model=GameState)
    async def set_position(game_id: str, req: SetPositionRequest) -> GameState:
        game = _require_game(state, game_id)
        state[game_id] = Game.from_fen(req.fen)
        game = state[game_id]
        return GameState(
            game_id=game_id,
            fen=game.to_fen(),
            legal_moves=[m.to_uci() for m in game.legal_moves()],
        )

    @app.post("/api/games/{game_id}/move", response_model=GameState)
    async def make_move(game_id: str, req: MoveRequest) -> GameState:
        game = _require_game(state, game_id)
        try:
            move = parse_uci(req.move)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        try:
            game.apply_move(move)
        except NotImplementedError:
            # Until move application exists (Plan 3), signal unimplemented
            raise HTTPException(status_code=501, detail="move application not implemented")

        return GameState(
            game_id=game_id,
            fen=game.to_fen(),
            legal_moves=[m.to_uci() for m in game.legal_moves()],
        )

    @app.post("/api/games/{game_id}/search")
    async def search(game_id: str, req: SearchRequest) -> Dict[str, Any]:
        game = _require_game(state, game_id)
        service = SearchService()
        res = service.search(game, depth=req.depth or 1, movetime_ms=req.movetime_ms)
        return {
            "best_move": res.best_move.to_uci() if res.best_move else None,
            "score": {"cp": res.score_cp} if res.score_cp is not None else None,
            "pv": [m.to_uci() for m in res.pv],
            "nodes": res.nodes,
            "depth": res.depth,
            "time_ms": res.time_ms,
        }

    @app.post("/api/perft")
    async def perft(payload: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder response until move generation (Plan 3)
        fen = payload.get("fen")
        depth = int(payload.get("depth", 1))
        if not fen:
            raise HTTPException(status_code=400, detail="fen is required")
        if depth < 0:
            raise HTTPException(status_code=400, detail="depth must be >= 0")
        return {"nodes": 0}

    return app


def _require_game(state: Dict[str, Game], game_id: str) -> Game:
    if game_id not in state:
        raise HTTPException(status_code=404, detail="game not found")
    return state[game_id]


# Default app for non-factory servers
app = create_app()
