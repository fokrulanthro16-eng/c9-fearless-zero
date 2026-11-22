from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from engine.data_snapshot import CHAMPIONS, MATCHUPS
from engine.draft_state import DRAFT_SEQUENCE, DraftState
from engine.evaluator import comp_radar, pool_health
from engine.grid_parser import ingest_grid_matchup
from engine.models import ActionRequest, ActionType, ComfortTier, DraftAction, LoadMatchupRequest, Role, Side
from engine.pinch_solver import PinchSolver


app = FastAPI(title="C9 FearlessZero")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATE = DraftState()
SOLVER = PinchSolver()
GRID_SOURCE = "BUILT-IN SNAPSHOT"

frontend_dir = Path(__file__).resolve().parents[1] / "frontend"
if frontend_dir.exists():
    app.mount("/frontend", StaticFiles(directory=str(frontend_dir)), name="frontend")


def _team_payload():
    return {
        "blue_team": STATE.matchup.blue_team.model_dump(mode="json"),
        "red_team": STATE.matchup.red_team.model_dump(mode="json"),
        "grid_feed": GRID_SOURCE,
    }


def _append_unique(champions: list[str], champion_id: str) -> None:
    if champion_id in CHAMPIONS and champion_id not in champions:
        champions.append(champion_id)


def _demo_lock_order() -> list[str]:
    locked: list[str] = []
    pressure_plan = {
        Role.TOP: 3,
        Role.JGL: 3,
        Role.MID: 3,
        Role.BOT: 3,
        Role.SUP: 2,
    }

    for role, count in pressure_plan.items():
        player = STATE.matchup.red_team.players[role]
        added = 0
        for tier in [ComfortTier.S, ComfortTier.A]:
            for champion_id in player.comfort[tier]:
                if added >= count:
                    break
                before = len(locked)
                _append_unique(locked, champion_id)
                if len(locked) > before:
                    added += 1
            if added >= count:
                break

    for team in [STATE.matchup.blue_team, STATE.matchup.red_team]:
        for role in [Role.TOP, Role.JGL, Role.MID, Role.BOT, Role.SUP]:
            player = team.players[role]
            for tier in [ComfortTier.S, ComfortTier.A, ComfortTier.B]:
                for champion_id in player.comfort[tier]:
                    _append_unique(locked, champion_id)
                    if len(locked) == 20:
                        return locked

    for champion in sorted(CHAMPIONS.values(), key=lambda item: (-item.base_score, item.id)):
        _append_unique(locked, champion.id)
        if len(locked) == 20:
            return locked
    return locked[:20]


def _demo_role_for(champion_id: str, side: Side) -> Role | None:
    champion = CHAMPIONS[champion_id]
    team = STATE.matchup.blue_team if side == Side.BLUE else STATE.matchup.red_team
    for role in [Role.TOP, Role.JGL, Role.MID, Role.BOT, Role.SUP]:
        player = team.players[role]
        if role in champion.roles and champion_id in set(player.comfort[ComfortTier.S] + player.comfort[ComfortTier.A] + player.comfort[ComfortTier.B]):
            return role
    return champion.roles[0] if champion.roles else None


def _load_demo_g3_pinch_state() -> dict:
    locked = _demo_lock_order()
    if len(locked) != 20:
        raise HTTPException(status_code=500, detail="Demo state could not find 20 legal champion locks")

    STATE.game = 3
    STATE.step = 0
    STATE.actions.clear()
    STATE.history.clear()
    STATE.fearless_locks.clear()

    pick_steps = [index for index, (_side, action_type) in enumerate(DRAFT_SEQUENCE) if action_type == ActionType.PICK]
    for index, champion_id in enumerate(locked):
        game = 1 if index < 10 else 2
        step = pick_steps[index % 10]
        side, _action_type = DRAFT_SEQUENCE[step]
        role = _demo_role_for(champion_id, side)
        STATE.actions.append(
            DraftAction(
                game=game,
                step=step,
                side=side,
                action_type=ActionType.PICK,
                champion_id=champion_id,
                role=role,
            )
        )
        STATE.fearless_locks[champion_id] = f"G{game}"

    payload = STATE.snapshot()
    payload.update(_team_payload())
    return payload


@app.get("/", include_in_schema=False)
def index():
    index_path = frontend_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not built")
    return FileResponse(index_path)


@app.get("/api/matchups")
def matchups():
    return [{"id": matchup.id, "name": matchup.name, "blue_team": matchup.blue_team.name, "red_team": matchup.red_team.name} for matchup in MATCHUPS.values()]


@app.get("/api/champions")
def champions():
    return [
        champion.model_dump(mode="json")
        for champion in sorted(CHAMPIONS.values(), key=lambda item: (-item.base_score, item.id))
    ]


@app.get("/api/state")
def state():
    payload = STATE.snapshot()
    payload.update(_team_payload())
    return payload


@app.post("/api/action")
def action(request: ActionRequest):
    try:
        return STATE.apply_action(request.champion_id, request.role).model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/undo")
def undo():
    action = STATE.undo()
    return {"undone": action.model_dump(mode="json") if action else None, "state": STATE.snapshot()}


@app.post("/api/next-game")
def next_game():
    try:
        STATE.advance_to_next_game()
        return STATE.snapshot()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reset")
def reset():
    global GRID_SOURCE
    GRID_SOURCE = "BUILT-IN SNAPSHOT"
    STATE.reset()
    return STATE.snapshot()


@app.post("/api/load-matchup")
def load_matchup(request: LoadMatchupRequest):
    global GRID_SOURCE
    if request.matchup_id not in MATCHUPS:
        raise HTTPException(status_code=404, detail="Unknown matchup")
    matchup = ingest_grid_matchup(request.grid_path, MATCHUPS[request.matchup_id])
    GRID_SOURCE = "LOCAL GRID FEED" if request.grid_path else "BUILT-IN SNAPSHOT"
    STATE.reset(matchup)
    return STATE.snapshot()


@app.post("/api/demo-g3-pinch")
def demo_g3_pinch():
    return _load_demo_g3_pinch_state()


@app.get("/api/solve")
def solve():
    try:
        return SOLVER.solve(STATE).model_dump(mode="json")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/dossier")
def dossier():
    red_health = pool_health(STATE, Side.RED)
    radar = comp_radar(STATE)
    lines = [
        f"# Pre-Match Coach Brief: {STATE.matchup.name}",
        "",
        f"## Series State",
        f"- Current game: G{STATE.game}",
        f"- Draft step: {STATE.step}/20",
        f"- Fearless locks: {', '.join(f'{champion} ({game})' for champion, game in sorted(STATE.fearless_locks.items())) or 'None'}",
        "",
        "## Opponent Pool Health",
    ]
    for role, data in red_health.items():
        lines.append(f"- {role.value}: {data['remaining_comfort']} S/A comfort picks remaining - {data['collapse_risk']}")
    lines.extend(["", "## Current Comp Radar"])
    for side, metrics in radar.items():
        lines.append(
            f"- {side.value}: Engage {metrics.Engage:.1f}, Frontline {metrics.Frontline:.1f}, "
            f"AP/AD {metrics.AP_AD_Balance:.1f}, Scaling {metrics.Scaling:.1f}, Pick {metrics.Pick:.1f}"
        )
    lines.extend(["", "## Meta Pool", f"- Champions tracked: {len(CHAMPIONS)}"])
    return {"markdown": "\n".join(lines)}
