from __future__ import annotations

import threading
import uuid
from typing import Dict, Optional

from ...engine.game import Game


class InMemorySessionStore:
    """Thread-safe in-memory game session store.

    Responsibilities:
    - Create new sessions with unique `game_id`s
    - Retrieve existing sessions by `game_id`
    - Update/replace session state
    - Delete sessions
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._games: Dict[str, Game] = {}

    def create(self, game: Optional[Game] = None) -> str:
        """Create a new game session and return its `game_id`."""
        gid = str(uuid.uuid4())
        if game is None:
            game = Game.new()
        with self._lock:
            self._games[gid] = game
        return gid

    def get(self, game_id: str) -> Optional[Game]:
        with self._lock:
            return self._games.get(game_id)

    def set(self, game_id: str, game: Game) -> None:
        with self._lock:
            if game_id not in self._games:
                raise KeyError(game_id)
            self._games[game_id] = game

    def upsert(self, game_id: str, game: Game) -> None:
        with self._lock:
            self._games[game_id] = game

    def delete(self, game_id: str) -> None:
        with self._lock:
            if game_id in self._games:
                del self._games[game_id]
