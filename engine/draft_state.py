from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .data_snapshot import CHAMPIONS, get_default_matchup
from .models import ActionType, DraftAction, MatchupProfile, Role, Side


DRAFT_SEQUENCE: List[tuple[Side, ActionType]] = [
    (Side.BLUE, ActionType.BAN), (Side.RED, ActionType.BAN), (Side.BLUE, ActionType.BAN),
    (Side.RED, ActionType.BAN), (Side.BLUE, ActionType.BAN), (Side.RED, ActionType.BAN),
    (Side.BLUE, ActionType.PICK), (Side.RED, ActionType.PICK), (Side.RED, ActionType.PICK),
    (Side.BLUE, ActionType.PICK), (Side.BLUE, ActionType.PICK), (Side.RED, ActionType.PICK),
    (Side.RED, ActionType.BAN), (Side.BLUE, ActionType.BAN), (Side.RED, ActionType.BAN), (Side.BLUE, ActionType.BAN),
    (Side.RED, ActionType.PICK), (Side.BLUE, ActionType.PICK), (Side.BLUE, ActionType.PICK), (Side.RED, ActionType.PICK),
]


@dataclass
class DraftState:
    matchup: MatchupProfile = field(default_factory=get_default_matchup)
    game: int = 1
    step: int = 0
    actions: List[DraftAction] = field(default_factory=list)
    fearless_locks: Dict[str, str] = field(default_factory=dict)
    history: List[tuple[DraftAction, Dict[str, str]]] = field(default_factory=list)

    @property
    def current_turn(self) -> tuple[Side, ActionType]:
        if self.step >= len(DRAFT_SEQUENCE):
            raise ValueError("Current game draft is complete")
        return DRAFT_SEQUENCE[self.step]

    def current_game_actions(self) -> List[DraftAction]:
        return [action for action in self.actions if action.game == self.game]

    def current_game_champions(self) -> set[str]:
        return {action.champion_id for action in self.current_game_actions()}

    def picked_by_side(self, side: Side) -> List[DraftAction]:
        return [
            action for action in self.current_game_actions()
            if action.side == side and action.action_type == ActionType.PICK
        ]

    def is_available(self, champion_id: str) -> bool:
        return champion_id in CHAMPIONS and champion_id not in self.fearless_locks and champion_id not in self.current_game_champions()

    def legal_candidates(self, limit_role: Optional[Role] = None) -> List[str]:
        candidates = [
            champion.id
            for champion in CHAMPIONS.values()
            if self.is_available(champion.id) and (limit_role is None or limit_role in champion.roles)
        ]
        return sorted(candidates, key=lambda champion_id: (-CHAMPIONS[champion_id].base_score, champion_id))

    def apply_action(self, champion_id: str, role: Optional[Role] = None) -> DraftAction:
        side, action_type = self.current_turn
        if champion_id not in CHAMPIONS:
            raise ValueError(f"Unknown champion: {champion_id}")
        if champion_id in self.fearless_locks:
            raise ValueError(f"{champion_id} is Fearless locked from {self.fearless_locks[champion_id]}")
        if champion_id in self.current_game_champions():
            raise ValueError(f"{champion_id} is already used in Game {self.game}")
        if role and role not in CHAMPIONS[champion_id].roles:
            raise ValueError(f"{champion_id} cannot be assigned to {role}")

        action = DraftAction(game=self.game, step=self.step, side=side, action_type=action_type, champion_id=champion_id, role=role)
        self.history.append((action, dict(self.fearless_locks)))
        self.actions.append(action)
        if action_type == ActionType.PICK:
            self.fearless_locks[champion_id] = f"G{self.game}"
        self.step += 1
        return action

    def undo(self) -> Optional[DraftAction]:
        if not self.history:
            return None
        action, previous_locks = self.history.pop()
        self.actions.pop()
        self.fearless_locks = previous_locks
        self.game = action.game
        self.step = action.step
        return action

    def advance_to_next_game(self) -> None:
        if self.step != len(DRAFT_SEQUENCE):
            raise ValueError("Cannot advance before completing all 20 draft steps")
        if self.game >= 5:
            raise ValueError("Best-of-5 already reached Game 5")
        self.game += 1
        self.step = 0

    def reset(self, matchup: Optional[MatchupProfile] = None) -> None:
        if matchup is not None:
            self.matchup = matchup
        self.game = 1
        self.step = 0
        self.actions.clear()
        self.fearless_locks.clear()
        self.history.clear()

    def snapshot(self) -> dict:
        side, action_type = self.current_turn if self.step < len(DRAFT_SEQUENCE) else (None, None)
        return {
            "matchup": self.matchup.name,
            "game": self.game,
            "step": self.step,
            "turn": {"side": side, "action_type": action_type} if side else None,
            "actions": [action.model_dump(mode="json") for action in self.actions],
            "fearless_locks": self.fearless_locks,
        }
