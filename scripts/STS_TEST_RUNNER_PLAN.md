# Strategic Test Suite (STS) Test Runner Plan

This plan outlines a Python-based CLI script to run STS (Strategic Test Suite) positions against our chess engine via UCI, compute correctness, and report a final success rate.

## Goals
- Parse `.epd` test files containing STS positions and solutions.
- Launch the engine as a UCI process and communicate per position.
- For each position: set up the board, run a search (depth or time-limited), read `bestmove`.
- Compare engine `bestmove` against the STS-provided solution(s) with optional normalization.
- Accumulate and report per-position results and overall success rate.

## Assumptions
- Engine supports UCI on stdin/stdout and responds to: `uci`, `isready`, `ucinewgame`, `position fen ...`, `go ...`, and returns `bestmove`.
- STS `.epd` lines are FEN + EPD ops; solution encoded in `bm` (best move) and/or `am` (avoid move) tags. Primary scoring uses `bm` (one or more moves, possibly in SAN or UCI format).
- We use UCI long algebraic moves (LAN) like `e2e4`, possibly with promotions `e7e8q`.
- Default constraint is time-based: `go movetime 2000` (2s) per position.

## CLI Interface
- Command: `python scripts/run_sts.py --engine ./build/engine --epd assets/sts/sts.epd --movetime 2000`.
- Options:
  - `--engine PATH` (required): engine binary path.
  - `--epd PATH` (required): EPD file path.
  - `--depth N` (optional): search depth (exclusive with movetime/nodes).
  - `--movetime MS` (optional, default 2000): time in ms per position.
  - `--nodes N` (optional): node limit per position.
  - `--limit N` (optional): max positions to run (for quick runs).
  - `--randomize` (optional): shuffle positions before running.
  - `--threads N` (optional): set UCI Threads if engine supports; runner remains single-process per position.
  - `--hash MB` (optional): set UCI Hash size if supported.
  - `--strict` (optional): enforce exact move string match; otherwise normalize.
  - `--report PATH` (optional): write CSV report (primary output).

## EPD Parsing
1. Read file line-by-line; ignore empty lines and comments (starting with `;` or `#`).
2. Split the line into tokens: first four fields are FEN piece placement, active color, castling, en passant, followed by optional halfmove/fullmove (if present) and then EPD operations in `key value;` pairs.
3. Collect EPD ops into a dict. Keys of interest:
   - `bm`: one or more moves separated by spaces (solutions).
   - `am`: one or more moves to avoid (for completeness; not scored as success).
   - Other metadata (`id`, `c0`, etc.) can be captured but are optional.
4. Store each position as a record: `{fen: str, bm: List[str], am: List[str], meta: Dict[str,str], line_no: int}`.
5. Support move string normalization using python-chess:
   - Use `python-chess` to construct a `Board(fen)` and parse each `bm` token via `board.parse_san(san)` when SAN is detected; convert to UCI via `move.uci()`.
   - If the token already looks like UCI (regex `^[a-h][1-8][a-h][1-8][qrbn]?$`), accept as-is.
   - For multiple `bm` moves, parse each independently on a fresh board from the same FEN.
   - Strip trailing semicolons, quotes, and handle tokens separated by spaces or commas.

## UCI Engine Session Management
1. Start engine process with `subprocess.Popen` (pipes for stdin/stdout, text mode, line-buffered).
2. Initialization sequence:
   - Send `uci`, wait for `uciok` (with timeout).
   - Optionally set options: `setoption name Threads value X`, `setoption name Hash value Y`.
   - Send `isready`, wait for `readyok`.
3. For each position:
   - Send `ucinewgame` every position or at least once at start; safer to send per position for isolation.
   - `position fen <FEN>`.
   - `isready` -> wait `readyok`.
   - Issue search command:
     - If `--depth`: `go depth N`.
     - Else if `--nodes`: `go nodes N`.
     - Else if `--movetime`: `go movetime MS`.
   - Read lines until `bestmove <move>` received or timeout.
   - Capture optional `info` lines for logging.
4. On completion or error, ensure process cleanup: send `quit`, terminate on timeout, kill as last resort.

## Move Comparison Logic
1. Normalize engine move to lowercase UCI (e.g., `E2E4` -> `e2e4`).
2. Prepare accepted solutions set:
   - If `bm` available: normalize all to lowercase UCI using python-chess for SAN inputs.
   - If `bm` empty but `am` present: treat any move not in `am` as correct only if STS variant requires; otherwise mark as unscored.
3. Handle promotions: preserve trailing piece letter; accept either lowercase or uppercase.
4. If `--strict`: compare exact string match.
5. Else: allow minimal normalization (trim whitespace, lowercase, treat `e7e8q` and `e7e8Q` as equal).
6. Result for position:
   - `correct = engine_move in solutions_set` (boolean).
   - Record `{id/meta, fen, engine_bestmove, solutions, correct, time_ms, depth/nodes}`.

## Scoring and Reporting
1. Maintain counters: total_run, total_with_solutions, correct_count.
2. After all positions:
   - If `total_with_solutions > 0`: success_rate = `correct_count / total_with_solutions`.
   - Print summary: `Correct X / Y (Z%)`.
3. Detailed output (primary):
   - Per-position CSV: `id,line_no,correct,engine_move,solutions,fen,time_ms,depth,nodes` written to `--report` or stdout if not provided.
   - Optional JSON array behind a flag `--report-json PATH`.
4. Print top-N misses for debugging (e.g., first 10 incorrect with engine move vs expected).

## Error Handling and Timeouts
1. Global engine startup timeout (e.g., 5s for `uciok`).
2. Read timeouts per `isready` and `bestmove` (e.g., 2x movetime or fixed max like 10s).
3. Graceful fallback if a line has no `bm`: skip from denominator unless `--strict` scoring.
4. Robust parsing to skip malformed lines; log warnings with line numbers.

## Implementation Outline (Python)
1. `argparse` for CLI.
2. `EPDParser` class
   - `parse_line(line: str) -> Optional[EPDRecord]`
   - `parse_file(path: str) -> List[EPDRecord]`
3. `UCIEngine` class
   - `start()`, `send(cmd)`, `read_until(predicate, timeout)`, `set_option(name, value)`, `quit()`
   - `go(fen, limits) -> (bestmove, meta)`
4. `compare_moves(engine_move: str, solutions: List[str], strict: bool) -> bool`
5. `run_suite(records, engine_path, limits, opts) -> RunReport`
6. `main()` to wire CLI → parse EPD → run → print/report.
7. Dependencies: add `python-chess` to `requirements.txt` or project dependencies; import `chess` for SAN parsing.

## Performance and Stability Considerations
- Keep a single engine process for all positions to avoid spawn overhead; still send `ucinewgame` each time.
- Line-buffered reads; avoid blocking by using non-blocking streams or dedicated reader thread if necessary.
- Optionally support `ponderhit`/`stop` not needed; rely on `bestmove` event.
- Allow interrupt (Ctrl+C) to stop gracefully and still dump partial results.

## Extensions (Future)
- SAN-to-UCI conversion using a chess library (e.g., `python-chess`) to handle STS files that list SAN in `bm`.
- Multi-process sharding to parallelize across many positions (each with its own engine instance).
- Weighted scoring if STS assigns points per test.
- HTML summary report with breakdown by theme or section.
