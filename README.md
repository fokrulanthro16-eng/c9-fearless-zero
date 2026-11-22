# C9 FearlessZero

C9 FearlessZero is a deterministic League of Legends Best-of-5 Fearless Draft and champion-pool pinch solver for Cloud9 coaches. It combines a FastAPI backend, a strict Bo5 draft state machine, a bounded alpha-beta tactical solver, and a flat war-room frontend served from `/`.

## Architecture

- `engine/data_snapshot.py`: 60 champion pro-meta snapshot using Riot Data Dragon champion IDs, role tags, damage profile, comp tags, and matchup-specific player pools.
- `engine/draft_state.py`: official 20-step pro draft sequence with Fearless locks that persist across Games 1-5.
- `engine/evaluator.py`: deterministic evaluation combining comp balance, player proficiency, role scarcity, flex value, synergy disruption, and Comfort Collapse Index.
- `engine/pinch_solver.py`: bounded alpha-beta move search returning the top 3 tactical bans or picks from the active side's perspective.
- `engine/grid_parser.py`: optional local GRID `.jsonl` or `.jsonl.zst` ingestion that promotes observed champion pools into the matchup model.
- `api/main.py`: FastAPI app, API routes, demo-state route, and static frontend serving.
- `frontend/`: pro-grade split-panel coaching terminal.
- `tests/`: pytest coverage for draft order, Fearless locks, undo, CCI behavior, demo state, and solver latency.

## Fearless Pool-Pinch Math

The evaluator treats Bo5 Fearless pressure as more than a current-game draft score. Each pick permanently locks the champion for both teams in future games, so a good move can be a short-term comp fit, a future denial, or both.

Core scoring inputs:

- Current-game comp balance: AP/AD balance, engage, frontline, scaling, pick threat, and role coverage.
- Player proficiency: S/A/B comfort tiers per player and role.
- Comfort Collapse Index: remaining unlocked S/A champions per player. Counts at `2` become `STRESSED`, `1` becomes `PINCHED`, and `0` becomes `COLLAPSED`.
- Tactical tie-breakers: exact player proficiency weight, scarcity multiplier, opponent comp-synergy disruption, and flex-role value.

The solver reports `eval_delta` as active-side tactical gain, displayed in the UI as `+X.XX ADV`.

## Game 3 Pinch Demo

Use the `G3 Pinch Demo` button in the top command bar or call:

```bash
curl -X POST http://127.0.0.1:8000/api/demo-g3-pinch
```

The endpoint keeps the active matchup, locks exactly 20 champions across `G1` and `G2`, and opens `G3` at Blue Ban 1. It is designed to show mid-series pool warfare immediately for judges and coaches.

## GRID Ingestion

`engine/grid_parser.py` supports local GRID League of Legends series files:

- Plain `.jsonl`
- Zero-decompression `.jsonl.zst` through Python 3.14 `compression.zstd`

Load a matchup with an optional local GRID path:

```bash
curl -X POST http://127.0.0.1:8000/api/load-matchup ^
  -H "Content-Type: application/json" ^
  -d "{\"matchup_id\":\"c9-tl\",\"grid_path\":\"grid_data/series.jsonl.zst\"}"
```

If the file is absent, malformed, or unavailable, the app gracefully falls back to the built-in pro snapshot.

## Install

```bash
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run

```bash
.\.venv\Scripts\python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/
```

## Verify

```bash
.\.venv\Scripts\python.exe -m pytest -v
```

Expected result: all tests pass, including solver latency and Game 3 demo-state checks.

## JetBrains PyCharm + Codex Workflow

This project was built in JetBrains PyCharm 2025.3 Pro with Codex Agent operating directly in the workspace. PyCharm provided project structure, virtualenv visibility, and local verification, while Codex handled iterative implementation across backend engine files, API endpoints, static frontend assets, tests, and documentation.

The workflow kept changes grounded in the local repository: inspect contracts first, patch scoped files, run pytest, smoke-test FastAPI routes, and restart the local server only after the build passed.
