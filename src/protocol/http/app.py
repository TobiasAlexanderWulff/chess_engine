from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field

from .error import (
    exception_handler,
    http_exception_handler,
    request_validation_exception_handler,
)
from .logging_middleware import RequestIDLoggingMiddleware
from ...engine.game import Game
from ...engine.move import parse_uci
from ...search.service import SearchService
from ...engine.perft import perft as perft_nodes
from .session import InMemorySessionStore


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
    in_check: bool
    checkmate: bool
    stalemate: bool
    draw: bool
    last_move: Optional[str]
    move_history: list[str]


def create_app() -> FastAPI:
    app = FastAPI(title="Chess Engine API", version="0.0.1")

    # Basic logging setup
    logging.basicConfig(level=logging.INFO)

    # Middleware & error handling
    app.add_middleware(RequestIDLoggingMiddleware)
    # Preserve FastAPI 422 validation behavior and structured HTTP errors
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, request_validation_exception_handler)
    app.add_exception_handler(Exception, exception_handler)

    # In-memory session store for games
    store = InMemorySessionStore()

    @app.get("/healthz")
    async def healthz() -> Dict[str, str]:
        return {"status": "ok"}

    @app.post("/api/games", response_model=CreateGameResponse)
    async def create_game() -> CreateGameResponse:
        game_id = store.create(Game.new())
        game = _require_game(store, game_id)
        return CreateGameResponse(game_id=game_id, fen=game.to_fen())

    @app.get("/api/games/{game_id}/state", response_model=GameState)
    async def get_state(game_id: str) -> GameState:
        game = _require_game(store, game_id)
        return GameState(
            game_id=game_id,
            fen=game.to_fen(),
            legal_moves=[m.to_uci() for m in game.legal_moves()],
            in_check=game.in_check(),
            checkmate=game.checkmate(),
            stalemate=game.stalemate(),
            draw=game.is_draw(),
            last_move=game.move_history_uci()[-1] if game.move_history_uci() else None,
            move_history=game.move_history_uci(),
        )

    @app.post("/api/games/{game_id}/position", response_model=GameState)
    async def set_position(game_id: str, req: SetPositionRequest) -> GameState:
        _require_game(store, game_id)
        try:
            store.set(game_id, Game.from_fen(req.fen))
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid FEN")
        game = _require_game(store, game_id)
        return GameState(
            game_id=game_id,
            fen=game.to_fen(),
            legal_moves=[m.to_uci() for m in game.legal_moves()],
            in_check=game.in_check(),
            checkmate=game.checkmate(),
            stalemate=game.stalemate(),
            draw=game.is_draw(),
            last_move=game.move_history_uci()[-1] if game.move_history_uci() else None,
            move_history=game.move_history_uci(),
        )

    @app.post("/api/games/{game_id}/move", response_model=GameState)
    async def make_move(game_id: str, req: MoveRequest) -> GameState:
        game = _require_game(store, game_id)
        try:
            move = parse_uci(req.move)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        try:
            game.apply_move(move)
        except ValueError:
            # Illegal move attempted
            raise HTTPException(status_code=400, detail="illegal move")

        return GameState(
            game_id=game_id,
            fen=game.to_fen(),
            legal_moves=[m.to_uci() for m in game.legal_moves()],
            in_check=game.in_check(),
            checkmate=game.checkmate(),
            stalemate=game.stalemate(),
            draw=game.is_draw(),
            last_move=game.move_history_uci()[-1] if game.move_history_uci() else None,
            move_history=game.move_history_uci(),
        )

    @app.post("/api/games/{game_id}/search")
    async def search(game_id: str, req: SearchRequest) -> Dict[str, Any]:
        game = _require_game(store, game_id)
        service = SearchService()
        res = service.search(game, depth=req.depth or 1, movetime_ms=req.movetime_ms)
        # Score object: either cp or mate (UCI-style)
        score: Dict[str, Any]
        if res.mate_in is not None:
            score = {"mate": res.mate_in}
        else:
            score = {"cp": res.score_cp} if res.score_cp is not None else None  # type: ignore[assignment]

        return {
            "best_move": res.best_move.to_uci() if res.best_move else None,
            "score": score,
            "pv": [m.to_uci() for m in res.pv],
            "nodes": res.nodes,
            "depth": res.depth,
            "time_ms": res.time_ms,
        }

    @app.post("/api/perft")
    async def perft(payload: Dict[str, Any]) -> Dict[str, Any]:
        fen = payload.get("fen")
        depth = int(payload.get("depth", 1))
        if not fen:
            raise HTTPException(status_code=400, detail="fen is required")
        if depth < 0:
            raise HTTPException(status_code=400, detail="depth must be >= 0")
        try:
            game = Game.from_fen(fen)
        except ValueError:
            raise HTTPException(status_code=400, detail="invalid FEN")
        nodes = perft_nodes(game.board, depth)
        return {"nodes": nodes}

    @app.post("/api/games/{game_id}/undo", response_model=GameState)
    async def undo(game_id: str) -> GameState:
        game = _require_game(store, game_id)
        try:
            game.undo_move()
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return GameState(
            game_id=game_id,
            fen=game.to_fen(),
            legal_moves=[m.to_uci() for m in game.legal_moves()],
            in_check=game.in_check(),
            checkmate=game.checkmate(),
            stalemate=game.stalemate(),
            draw=game.is_draw(),
            last_move=game.move_history_uci()[-1] if game.move_history_uci() else None,
            move_history=game.move_history_uci(),
        )

    return app


def _require_game(store: InMemorySessionStore, game_id: str) -> Game:
    game = store.get(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="game not found")
    return game


# Default app for non-factory servers
app = create_app()
