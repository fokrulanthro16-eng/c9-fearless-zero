from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient

from api.main import app
from engine.draft_state import DRAFT_SEQUENCE, DraftState
from engine.evaluator import pool_health
from engine.models import ActionType, Role, Side
from engine.pinch_solver import PinchSolver


def test_full_20_step_turn_order():
    state = DraftState()
    picks = [
        "Aatrox", "Ahri", "Akali", "Alistar", "Aphelios", "Ashe",
        "Azir", "Braum", "Caitlyn", "Camille", "Corki", "Draven",
        "Ezreal", "Gnar", "Gragas", "Gwen", "Hwei", "Ivern", "JarvanIV", "Jax",
    ]
    seen = []
    for champion in picks:
        seen.append(state.current_turn)
        state.apply_action(champion)
    assert seen == DRAFT_SEQUENCE
    assert state.step == 20
    assert len(state.actions) == 20


def test_fearless_locks_persist_from_game_1_to_game_3():
    state = DraftState()
    picks = [
        "Aatrox", "Ahri", "Akali", "Alistar", "Aphelios", "Ashe",
        "Azir", "Braum", "Caitlyn", "Camille", "Corki", "Draven",
        "Ezreal", "Gnar", "Gragas", "Gwen", "Hwei", "Ivern", "JarvanIV", "Jax",
    ]
    for champion in picks:
        state.apply_action(champion)
    assert state.fearless_locks["Azir"] == "G1"
    state.advance_to_next_game()
    assert state.game == 2
    with pytest.raises(ValueError, match="Fearless locked"):
        state.apply_action("Azir")
    for champion in [
        "Jinx", "Kaisa", "Kalista", "Karma", "Khazix", "Kindred",
        "KSante", "LeeSin", "Leona", "Poppy", "Lulu", "Maokai",
        "Milio", "Rakan", "Nautilus", "Neeko", "Nocturne", "Olaf", "Orianna", "Ornn",
    ]:
        state.apply_action(champion)
    state.advance_to_next_game()
    assert state.game == 3
    assert state.fearless_locks["KSante"] == "G2"
    assert state.fearless_locks["Azir"] == "G1"


def test_illegal_locked_pick_rejection_and_same_game_duplicate():
    state = DraftState()
    state.apply_action("Vi")
    with pytest.raises(ValueError, match="already used"):
        state.apply_action("Vi")
    for champion in [
        "Sejuani", "Maokai", "Azir", "Orianna", "Ahri", "Corki",
        "Yone", "Kaisa", "Xayah", "Varus", "Jinx", "Rell",
        "Nautilus", "Rakan", "Alistar", "Renekton", "KSante", "Gnar", "Ornn",
    ]:
        state.apply_action(champion)
    state.advance_to_next_game()
    with pytest.raises(ValueError, match="Fearless locked"):
        state.apply_action("Yone")


def test_undo_restores_step_and_locks():
    state = DraftState()
    for champion in ["Renekton", "Sejuani", "Azir", "Orianna", "Ahri", "Corki", "Yone"]:
        state.apply_action(champion)
    assert state.step == 7
    assert state.fearless_locks["Yone"] == "G1"
    undone = state.undo()
    assert undone.champion_id == "Yone"
    assert state.step == 6
    assert "Yone" not in state.fearless_locks
    assert state.current_turn == (Side.BLUE, ActionType.PICK)


def test_cci_triggers_when_shallow_role_pool_is_targeted():
    state = DraftState()
    for champion in ["KSante", "Renekton", "Gnar", "Ornn"]:
        state.apply_action(champion)
    health = pool_health(state, Side.RED)
    assert health[Role.TOP]["remaining_comfort"] == 1
    assert health[Role.TOP]["collapse_risk"] == "PINCHED"
    solver = PinchSolver()
    result = solver.solve(state)
    assert any(move.pinch_tag in {"POOL PINCH", "DENY COMFORT"} for move in result.top_moves)


def test_solver_latency_under_200ms():
    state = DraftState()
    for champion in ["KSante", "Vi", "Azir", "Kaisa", "Rell", "Renekton", "Sejuani", "Orianna"]:
        state.apply_action(champion)
    solver = PinchSolver()
    start = time.perf_counter()
    result = solver.solve(state)
    elapsed_ms = (time.perf_counter() - start) * 1000
    assert elapsed_ms < 200
    assert len(result.top_moves) == 3
    assert -10.0 <= result.eval_score <= 10.0


def test_demo_g3_pinch_endpoint_locks_20_champions_and_stresses_roles():
    client = TestClient(app)
    client.post("/api/load-matchup", json={"matchup_id": "c9-tl"})

    response = client.post("/api/demo-g3-pinch")
    assert response.status_code == 200
    state = response.json()

    assert state["game"] == 3
    assert state["step"] == 0
    assert state["turn"] == {"side": "BLUE", "action_type": "BAN"}
    assert len(state["fearless_locks"]) == 20
    assert list(state["fearless_locks"].values()).count("G1") == 10
    assert list(state["fearless_locks"].values()).count("G2") == 10

    solve = client.get("/api/solve").json()
    risks = [row["collapse_risk"] for row in solve["red_pool_health"].values()]
    assert sum(risk in {"STRESSED", "PINCHED", "COLLAPSED"} for risk in risks) >= 2
    client.post("/api/reset")


def test_demo_solver_top_moves_have_distinct_player_specific_deltas():
    client = TestClient(app)
    client.post("/api/load-matchup", json={"matchup_id": "c9-tl"})
    client.post("/api/demo-g3-pinch")

    solve = client.get("/api/solve").json()
    moves = solve["top_moves"]
    player_names = {
        player["name"]
        for player in client.get("/api/state").json()["red_team"]["players"].values()
    }

    assert len(moves) == 3
    assert len({move["eval_delta"] for move in moves}) == 3
    assert all(any(player in move["reason"] for player in player_names) for move in moves)
    assert all(move["eval_delta"] > 0 for move in moves)
    client.post("/api/reset")
