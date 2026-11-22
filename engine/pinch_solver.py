from __future__ import annotations

import time
from typing import List, Tuple

from .data_snapshot import CHAMPIONS
from .draft_state import DraftState
from .evaluator import (
    action_pinch_value,
    comp_radar,
    evaluate_state,
    infer_target_role,
    opponent,
    player_champion_fit,
    pool_health,
    tactical_move_profile,
    team_for_side,
)
from .models import ActionType, ComfortTier, MoveRecommendation, PoolHealth, Side, SolverResult


class PinchSolver:
    def __init__(self, max_candidates: int = 18, time_budget_ms: int = 140):
        self.max_candidates = max_candidates
        self.time_budget_ms = time_budget_ms

    def solve(self, state: DraftState) -> SolverResult:
        start = time.perf_counter()
        base = evaluate_state(state)
        if state.step >= 20:
            blue_health = {
                role: PoolHealth(role=role, remaining_comfort=data["remaining_comfort"], collapse_risk=data["collapse_risk"])
                for role, data in pool_health(state, Side.BLUE).items()
            }
            red_health = {
                role: PoolHealth(role=role, remaining_comfort=data["remaining_comfort"], collapse_risk=data["collapse_risk"])
                for role, data in pool_health(state, Side.RED).items()
            }
            return SolverResult(
                eval_score=base,
                top_moves=[],
                opponent_pool_health=red_health,
                blue_pool_health=blue_health,
                red_pool_health=red_health,
                comp_radar=comp_radar(state),
            )
        side, action_type = state.current_turn
        candidates = self._candidate_pool(state)[: self.max_candidates]
        scored: List[Tuple[float, MoveRecommendation]] = []

        for champion_id in candidates:
            if (time.perf_counter() - start) * 1000 > self.time_budget_ms:
                break
            profile = tactical_move_profile(state, champion_id, side, action_type)
            role = infer_target_role(state, champion_id, side if action_type == ActionType.PICK else opponent(side))
            state.apply_action(champion_id, role if action_type == ActionType.PICK else None)
            score = self._bounded_reply_score(state, start)
            state.undo()
            blue_delta = score - base
            active_delta = blue_delta if side == Side.BLUE else -blue_delta
            active_gain = round(active_delta + profile.tactical_score * 0.58, 2)
            reason = self._reason(state, profile)
            scored.append(
                (
                    active_gain,
                    MoveRecommendation(
                        champion_id=champion_id,
                        action_type=action_type,
                        eval_delta=active_gain,
                        target_role=profile.target_role,
                        pinch_tag=profile.pinch_tag,
                        reason=reason,
                    ),
                )
            )

        scored.sort(key=lambda item: (-item[0], item[1].champion_id))
        opponent_health = {
            role: PoolHealth(role=role, remaining_comfort=data["remaining_comfort"], collapse_risk=data["collapse_risk"])
            for role, data in pool_health(state, opponent(side)).items()
        }
        blue_health = {
            role: PoolHealth(role=role, remaining_comfort=data["remaining_comfort"], collapse_risk=data["collapse_risk"])
            for role, data in pool_health(state, Side.BLUE).items()
        }
        red_health = {
            role: PoolHealth(role=role, remaining_comfort=data["remaining_comfort"], collapse_risk=data["collapse_risk"])
            for role, data in pool_health(state, Side.RED).items()
        }
        return SolverResult(
            eval_score=base,
            top_moves=[move for _score, move in scored[:3]],
            opponent_pool_health=opponent_health,
            blue_pool_health=blue_health,
            red_pool_health=red_health,
            comp_radar=comp_radar(state),
        )

    def _candidate_pool(self, state: DraftState) -> List[str]:
        side, action_type = state.current_turn
        target_team = team_for_side(state.matchup, opponent(side) if action_type == ActionType.BAN else side)
        comfort = []
        for player in target_team.players.values():
            comfort.extend(player.comfort["S"])
            comfort.extend(player.comfort["A"])
        available_comfort = [champion for champion in comfort if state.is_available(champion)]
        meta = state.legal_candidates()
        ordered = []
        for champion_id in available_comfort + meta:
            if champion_id not in ordered and champion_id in CHAMPIONS and state.is_available(champion_id):
                ordered.append(champion_id)
        return sorted(ordered, key=lambda champion_id: (-self._static_candidate_score(state, champion_id), champion_id))

    def _static_candidate_score(self, state: DraftState, champion_id: str) -> float:
        side, action_type = state.current_turn
        pinch, _role, _tag = action_pinch_value(state, champion_id, side, action_type)
        return CHAMPIONS[champion_id].base_score + pinch

    def _bounded_reply_score(self, state: DraftState, start: float) -> float:
        if state.step >= 20 or (time.perf_counter() - start) * 1000 > self.time_budget_ms:
            return evaluate_state(state)
        side, action_type = state.current_turn
        best = -999.0 if side.value == "BLUE" else 999.0
        for champion_id in self._candidate_pool(state)[:6]:
            role = infer_target_role(state, champion_id, side)
            try:
                state.apply_action(champion_id, role if action_type == ActionType.PICK else None)
            except ValueError:
                continue
            score = evaluate_state(state)
            state.undo()
            if side.value == "BLUE":
                best = max(best, score)
            else:
                best = min(best, score)
        return evaluate_state(state) if abs(best) == 999.0 else best

    def _reason(self, state: DraftState, profile) -> str:
        champion = CHAMPIONS[profile.champion_id]
        tier = self._tier_label(profile.target_tier)
        team = team_for_side(state.matchup, opponent(profile.acting_side))
        role = profile.target_role.value if profile.target_role else "FLEX"
        player = profile.target_player or f"{team.name} {role}"
        game_note = f"for G{state.game}" if state.game >= 3 else f"before G{state.game + 1}"

        if profile.action_type == ActionType.BAN:
            if profile.pinch_tag == "POOL PINCH":
                return (
                    f"Denies {player} ({role}) {tier} {champion.name}; "
                    f"drops {team.name} {role} comfort pool to {profile.remaining_after} {game_note}."
                )
            if profile.target_tier in {ComfortTier.S, ComfortTier.A}:
                return (
                    f"Denies {player} ({role}) {tier} {champion.name}; "
                    f"scarcity x{profile.scarcity_multiplier:.2f} leaves {profile.remaining_after} trusted picks."
                )
            return (
                f"Removes {champion.name} from {team.name} {role} plans; "
                f"breaks {self._tag_phrase(champion.tags)} synergy."
            )

        own_fit = player_champion_fit(state, profile.champion_id, profile.acting_side)
        own_player = own_fit.player.name if own_fit else team_for_side(state.matchup, profile.acting_side).name
        own_role = own_fit.role.value if own_fit else (champion.roles[0].value if champion.roles else "FLEX")
        if profile.target_player and profile.target_tier in {ComfortTier.S, ComfortTier.A}:
            return (
                f"Secures {self._tag_phrase(champion.tags)} on {champion.name} for {own_player} ({own_role}) "
                f"and flexes it away from {player} ({role}); pool falls to {profile.remaining_after}."
            )
        return (
            f"Secures {self._tag_phrase(champion.tags)} on {champion.name} for {own_player} ({own_role}); "
            f"adds comp value {profile.comp_value:.2f}."
        )

    def _tier_label(self, tier) -> str:
        if tier == ComfortTier.S:
            return "S-tier"
        if tier == ComfortTier.A:
            return "A-tier"
        if tier == ComfortTier.B:
            return "B-tier pocket"
        return "off-pool"

    def _tag_phrase(self, tags: list[str]) -> str:
        if "frontline" in tags and "engage" in tags:
            return "frontline engage"
        if "engage" in tags and "pick" in tags:
            return "engage pick"
        return " + ".join(tags[:2]) if tags else "comp balance"
