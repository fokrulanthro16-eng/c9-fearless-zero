from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .data_snapshot import CHAMPIONS
from .draft_state import DraftState
from .models import ActionType, ComfortTier, MatchupProfile, PlayerProfile, RadarMetrics, Role, Side


TAG_TO_METRIC = {
    "engage": "Engage",
    "frontline": "Frontline",
    "scaling": "Scaling",
    "pick": "Pick",
}

TIER_WEIGHTS = {
    ComfortTier.S: 1.85,
    ComfortTier.A: 1.15,
    ComfortTier.B: 0.45,
}

TAG_DISRUPTION_WEIGHTS = {
    "engage": 0.42,
    "frontline": 0.38,
    "pick": 0.32,
    "scaling": 0.26,
    "poke": 0.22,
    "disengage": 0.18,
}


@dataclass(frozen=True)
class PlayerChampionFit:
    role: Role
    player: PlayerProfile
    tier: Optional[ComfortTier]
    proficiency_weight: float
    remaining_before: int
    remaining_after: int


@dataclass(frozen=True)
class TacticalMoveProfile:
    champion_id: str
    action_type: ActionType
    acting_side: Side
    target_side: Side
    target_role: Optional[Role]
    target_player: Optional[str]
    target_tier: Optional[ComfortTier]
    proficiency_weight: float
    remaining_before: int
    remaining_after: int
    scarcity_multiplier: float
    synergy_disruption: float
    flex_value: float
    comp_value: float
    tactical_score: float
    pinch_tag: str


def comfort_score(player: PlayerProfile, champion_id: str) -> float:
    if champion_id in player.comfort[ComfortTier.S]:
        return 1.4
    if champion_id in player.comfort[ComfortTier.A]:
        return 0.8
    if champion_id in player.comfort[ComfortTier.B]:
        return 0.3
    return -0.5


def team_for_side(matchup: MatchupProfile, side: Side):
    return matchup.blue_team if side == Side.BLUE else matchup.red_team


def opponent(side: Side) -> Side:
    return Side.RED if side == Side.BLUE else Side.BLUE


def remaining_comfort_for_player(state: DraftState, player: PlayerProfile, include_b: bool = False) -> int:
    tiers = [ComfortTier.S, ComfortTier.A] + ([ComfortTier.B] if include_b else [])
    pool = {champion for tier in tiers for champion in player.comfort[tier]}
    unavailable = set(state.fearless_locks) | state.current_game_champions()
    return len([champion for champion in pool if champion in CHAMPIONS and champion not in unavailable])


def proficiency_tier(player: PlayerProfile, champion_id: str) -> Optional[ComfortTier]:
    for tier in [ComfortTier.S, ComfortTier.A, ComfortTier.B]:
        if champion_id in player.comfort[tier]:
            return tier
    return None


def proficiency_weight(tier: Optional[ComfortTier]) -> float:
    return TIER_WEIGHTS.get(tier, 0.12)


def scarcity_multiplier(remaining_count: int) -> float:
    if remaining_count <= 0:
        return 2.35
    if remaining_count == 1:
        return 2.1
    if remaining_count == 2:
        return 1.78
    if remaining_count == 3:
        return 1.46
    if remaining_count == 4:
        return 1.18
    return 1.0


def pool_health(state: DraftState, side: Side) -> Dict[Role, dict]:
    team = team_for_side(state.matchup, side)
    health = {}
    for role, player in team.players.items():
        count = remaining_comfort_for_player(state, player)
        if count <= 0:
            risk = "COLLAPSED"
        elif count == 1:
            risk = "PINCHED"
        elif count == 2:
            risk = "STRESSED"
        else:
            risk = "SAFE"
        health[role] = {"remaining_comfort": count, "collapse_risk": risk}
    return health


def player_champion_fit(state: DraftState, champion_id: str, side: Side) -> Optional[PlayerChampionFit]:
    champion = CHAMPIONS[champion_id]
    team = team_for_side(state.matchup, side)
    best: Optional[tuple[int, int, Role, PlayerProfile, Optional[ComfortTier]]] = None
    role_order = {role: index for index, role in enumerate([Role.TOP, Role.JGL, Role.MID, Role.BOT, Role.SUP])}
    tier_order = {ComfortTier.S: 0, ComfortTier.A: 1, ComfortTier.B: 2}

    for role, player in team.players.items():
        tier = proficiency_tier(player, champion_id)
        if tier is None and role not in champion.roles:
            continue
        rank = tier_order.get(tier, 5)
        role_rank = role_order[role]
        candidate = (rank, role_rank, role, player, tier)
        if best is None or candidate[:2] < best[:2]:
            best = candidate

    if best is None:
        return None

    _rank, _role_rank, role, player, tier = best
    before = remaining_comfort_for_player(state, player)
    removes_comfort = 1 if tier in {ComfortTier.S, ComfortTier.A} and champion_id not in state.current_game_champions() else 0
    after = max(0, before - removes_comfort)
    return PlayerChampionFit(
        role=role,
        player=player,
        tier=tier,
        proficiency_weight=proficiency_weight(tier),
        remaining_before=before,
        remaining_after=after,
    )


def comp_radar(state: DraftState) -> Dict[Side, RadarMetrics]:
    radar: Dict[Side, RadarMetrics] = {}
    for side in [Side.BLUE, Side.RED]:
        actions = state.picked_by_side(side)
        metrics = {"Engage": 0.0, "Frontline": 0.0, "Scaling": 0.0, "Pick": 0.0}
        ad = ap = 0
        for action in actions:
            champion = CHAMPIONS[action.champion_id]
            for tag in champion.tags:
                metric = TAG_TO_METRIC.get(tag)
                if metric:
                    metrics[metric] += 2.0
            if champion.damage.value in {"AD", "MIXED"}:
                ad += 1
            if champion.damage.value in {"AP", "MIXED"}:
                ap += 1
        balance = 10.0 - min(10.0, abs(ad - ap) * 2.5) if actions else 0.0
        radar[side] = RadarMetrics(
            Engage=min(10.0, metrics["Engage"]),
            Frontline=min(10.0, metrics["Frontline"]),
            AP_AD_Balance=balance,
            Scaling=min(10.0, metrics["Scaling"]),
            Pick=min(10.0, metrics["Pick"]),
        )
    return radar


def tag_synergy_disruption(state: DraftState, champion_id: str, target_side: Side) -> float:
    champion = CHAMPIONS[champion_id]
    current_tags = {
        tag
        for action in state.picked_by_side(target_side)
        for tag in CHAMPIONS[action.champion_id].tags
    }
    value = sum(TAG_DISRUPTION_WEIGHTS.get(tag, 0.1) for tag in champion.tags)
    value += sum(0.16 for tag in champion.tags if tag in current_tags)
    return round(value, 3)


def flex_role_value(state: DraftState, champion_id: str, target_side: Side) -> float:
    champion = CHAMPIONS[champion_id]
    team = team_for_side(state.matchup, target_side)
    comfort_roles = 0
    for player in team.players.values():
        tier = proficiency_tier(player, champion_id)
        if tier in {ComfortTier.S, ComfortTier.A}:
            comfort_roles += 1
    role_flex = max(0, len(champion.roles) - 1) * 0.28
    roster_flex = max(0, comfort_roles - 1) * 0.18
    return round(role_flex + roster_flex, 3)


def own_comp_value(state: DraftState, champion_id: str, acting_side: Side) -> float:
    champion = CHAMPIONS[champion_id]
    own_picks = state.picked_by_side(acting_side)
    existing_tags = {
        tag
        for action in own_picks
        for tag in CHAMPIONS[action.champion_id].tags
    }
    value = 0.0
    if "frontline" in champion.tags and "frontline" not in existing_tags:
        value += 0.38
    if "engage" in champion.tags and "engage" not in existing_tags:
        value += 0.34
    if "pick" in champion.tags and "pick" not in existing_tags:
        value += 0.22
    if "scaling" in champion.tags and len(own_picks) >= 2:
        value += 0.16
    return round(value, 3)


def _pinch_tag(action_type: ActionType, champion_id: str, fit: Optional[PlayerChampionFit], flex_value_: float, comp_value_: float) -> str:
    if fit and fit.remaining_after <= 1 and fit.remaining_before > fit.remaining_after:
        return "POOL PINCH"
    if action_type == ActionType.PICK and flex_value_ >= 0.28:
        return "FLEX STEAL"
    if fit and fit.tier in {ComfortTier.S, ComfortTier.A}:
        return "DENY COMFORT"
    champion = CHAMPIONS[champion_id]
    if comp_value_ >= 0.34 or {"engage", "frontline"}.intersection(champion.tags):
        return "COMP BALANCE"
    return "DENY COMFORT" if action_type == ActionType.BAN else "COMP BALANCE"


def tactical_move_profile(state: DraftState, champion_id: str, acting_side: Side, action_type: ActionType) -> TacticalMoveProfile:
    champion = CHAMPIONS[champion_id]
    enemy_side = opponent(acting_side)
    target_side = enemy_side if action_type == ActionType.BAN else acting_side
    primary_fit = player_champion_fit(state, champion_id, target_side)
    deny_fit = player_champion_fit(state, champion_id, enemy_side)
    fit = primary_fit if action_type == ActionType.BAN else (deny_fit or primary_fit)

    before = fit.remaining_before if fit else 0
    after = fit.remaining_after if fit else 0
    scarcity = scarcity_multiplier(after if action_type == ActionType.PICK else before)
    prof = fit.proficiency_weight if fit else 0.12
    synergy = tag_synergy_disruption(state, champion_id, enemy_side)
    flex = flex_role_value(state, champion_id, enemy_side)
    comp = own_comp_value(state, champion_id, acting_side) if action_type == ActionType.PICK else 0.0
    threshold_bonus = 0.0
    if fit and before > after:
        if after <= 0:
            threshold_bonus = 1.25
        elif after == 1:
            threshold_bonus = 0.9
        elif after == 2:
            threshold_bonus = 0.55
        elif after == 3:
            threshold_bonus = 0.28

    if action_type == ActionType.BAN:
        tactical = prof * scarcity + synergy * 0.72 + flex * 0.55 + threshold_bonus + champion.base_score * 0.035
    else:
        own_prof = primary_fit.proficiency_weight if primary_fit else 0.12
        steal_prof = deny_fit.proficiency_weight if deny_fit else 0.0
        tactical = own_prof * 0.72 + steal_prof * scarcity * 0.62 + synergy * 0.42 + flex * 0.7 + comp + threshold_bonus + champion.base_score * 0.03

    # Stable low-amplitude tie-breaker keeps tactical rows deterministic without hiding material score.
    stable = (sum((index + 1) * ord(char) for index, char in enumerate(champion_id)) % 23) * 0.003
    tactical += stable
    tag = _pinch_tag(action_type, champion_id, fit, flex, comp)
    return TacticalMoveProfile(
        champion_id=champion_id,
        action_type=action_type,
        acting_side=acting_side,
        target_side=target_side,
        target_role=fit.role if fit else (champion.roles[0] if champion.roles else None),
        target_player=fit.player.name if fit else None,
        target_tier=fit.tier if fit else None,
        proficiency_weight=round(prof, 3),
        remaining_before=before,
        remaining_after=after,
        scarcity_multiplier=round(scarcity, 3),
        synergy_disruption=round(synergy, 3),
        flex_value=round(flex, 3),
        comp_value=round(comp, 3),
        tactical_score=round(tactical, 4),
        pinch_tag=tag,
    )


def _team_comp_score(state: DraftState, side: Side) -> float:
    radar = comp_radar(state)[side]
    role_count = len({action.role for action in state.picked_by_side(side) if action.role})
    return (
        radar.Engage * 0.18
        + radar.Frontline * 0.16
        + radar.AP_AD_Balance * 0.16
        + radar.Scaling * 0.12
        + radar.Pick * 0.12
        + role_count * 0.25
    )


def _proficiency_score(state: DraftState, side: Side) -> float:
    team = team_for_side(state.matchup, side)
    total = 0.0
    for action in state.picked_by_side(side):
        if action.role and action.role in team.players:
            total += comfort_score(team.players[action.role], action.champion_id)
        else:
            total += 0.1
    return total


def comfort_collapse_index(state: DraftState, side: Side) -> float:
    score = 0.0
    for data in pool_health(state, side).values():
        count = data["remaining_comfort"]
        if count <= 0:
            score += 4.0
        elif count == 1:
            score += 2.5
        elif count == 2:
            score += 1.0
    return score


def evaluate_state(state: DraftState) -> float:
    blue = _team_comp_score(state, Side.BLUE) + _proficiency_score(state, Side.BLUE)
    red = _team_comp_score(state, Side.RED) + _proficiency_score(state, Side.RED)
    cci = comfort_collapse_index(state, Side.RED) - comfort_collapse_index(state, Side.BLUE)
    score = (blue - red) + cci * 0.7
    return max(-10.0, min(10.0, round(score, 3)))


def infer_target_role(state: DraftState, champion_id: str, target_side: Side) -> Optional[Role]:
    fit = player_champion_fit(state, champion_id, target_side)
    if fit:
        return fit.role
    champion = CHAMPIONS[champion_id]
    return champion.roles[0] if champion.roles else None


def action_pinch_value(state: DraftState, champion_id: str, acting_side: Side, action_type: ActionType) -> tuple[float, Optional[Role], str]:
    profile = tactical_move_profile(state, champion_id, acting_side, action_type)
    return profile.tactical_score, profile.target_role, profile.pinch_tag
