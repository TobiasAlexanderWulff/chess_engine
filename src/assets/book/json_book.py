from __future__ import annotations

import json
import os
import random
from typing import Any, Dict, List, Optional

from ...engine.game import Game
from ...engine.move import Move, parse_uci


class JSONBook:
    """Simple JSON-based opening book.

    Format examples:
    - Object mapping FEN -> list of {"uci": "e2e4", "weight": 10}
    - Or {"positions": [{"fen": "...", "moves": [{"uci": "...", "weight": 1}]}]}

    Notes:
    - We validate that the selected move is legal in the given position.
    - Deterministic by default: select highest-weight move; if `randomize=True`,
      select weighted-random using a local RNG seeded from the FEN for stability.
    """

    def __init__(self, path: str) -> None:
        self.path = path
        self._index: Dict[str, List[Dict[str, Any]]] = {}
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.path):
            raise FileNotFoundError(self.path)
        with open(self.path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and "positions" in data:
            for ent in data["positions"]:
                fen = str(ent.get("fen", "")).strip()
                moves = ent.get("moves", [])
                if fen and isinstance(moves, list):
                    self._index[fen] = [dict(m) for m in moves]
        elif isinstance(data, dict):
            # Assume direct mapping of FEN -> list[moves]
            for fen, moves in data.items():
                if isinstance(moves, list):
                    self._index[str(fen).strip()] = [dict(m) for m in moves]
        else:
            raise ValueError("invalid book format")

    def find_move(self, game: Game, *, randomize: bool = False) -> Optional[Move]:
        fen = game.to_fen()
        entries = self._index.get(fen)
        if not entries:
            return None
        legal = game.legal_moves()
        if not legal:
            return None

        # Filter entries to legal moves only
        legal_set = {(m.from_sq, m.to_sq, m.promotion) for m in legal}
        candidates: List[Dict[str, Any]] = []
        for e in entries:
            u = e.get("uci")
            if not isinstance(u, str):
                continue
            try:
                mv = parse_uci(u)
            except Exception:
                continue
            key = (mv.from_sq, mv.to_sq, mv.promotion)
            if key in legal_set:
                w = int(e.get("weight", 1))
                candidates.append({"move": mv, "weight": max(1, w)})

        if not candidates:
            return None

        if not randomize:
            # Deterministic: choose highest weight, tie-break by lexical UCI
            candidates.sort(key=lambda x: (x["weight"], x["move"].to_uci()))
            return candidates[-1]["move"]

        # Weighted random, but seed by FEN for stability across runs
        rng = random.Random(hash(fen) & 0xFFFF_FFFF)
        total = sum(c["weight"] for c in candidates)
        r = rng.randint(1, total)
        acc = 0
        for c in candidates:
            acc += c["weight"]
            if r <= acc:
                return c["move"]
        return candidates[-1]["move"]
