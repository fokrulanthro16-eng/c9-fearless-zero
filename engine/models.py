from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    TOP = "TOP"
    JGL = "JGL"
    MID = "MID"
    BOT = "BOT"
    SUP = "SUP"


class DamageProfile(str, Enum):
    AD = "AD"
    AP = "AP"
    MIXED = "MIXED"


class ActionType(str, Enum):
    BAN = "BAN"
    PICK = "PICK"


class Side(str, Enum):
    BLUE = "BLUE"
    RED = "RED"


class ComfortTier(str, Enum):
    S = "S"
    A = "A"
    B = "B"


class Champion(BaseModel):
    id: str
    name: str
    roles: List[Role]
    damage: DamageProfile
    tags: List[str]
    base_score: float = Field(ge=0, le=10)


class PlayerProfile(BaseModel):
    name: str
    role: Role
    comfort: Dict[ComfortTier, List[str]]


class TeamProfile(BaseModel):
    name: str
    players: Dict[Role, PlayerProfile]


class MatchupProfile(BaseModel):
    id: str
    name: str
    blue_team: TeamProfile
    red_team: TeamProfile


class DraftAction(BaseModel):
    game: int
    step: int
    side: Side
    action_type: ActionType
    champion_id: str
    role: Optional[Role] = None


class MoveRecommendation(BaseModel):
    champion_id: str
    action_type: ActionType
    eval_delta: float
    target_role: Optional[Role]
    pinch_tag: str
    reason: str


class PoolHealth(BaseModel):
    role: Role
    remaining_comfort: int
    collapse_risk: str


class RadarMetrics(BaseModel):
    Engage: float
    Frontline: float
    AP_AD_Balance: float
    Scaling: float
    Pick: float


class SolverResult(BaseModel):
    eval_score: float
    top_moves: List[MoveRecommendation]
    opponent_pool_health: Dict[Role, PoolHealth]
    blue_pool_health: Dict[Role, PoolHealth]
    red_pool_health: Dict[Role, PoolHealth]
    comp_radar: Dict[Side, RadarMetrics]


class ActionRequest(BaseModel):
    champion_id: str
    role: Optional[Role] = None


class LoadMatchupRequest(BaseModel):
    matchup_id: str
    grid_path: Optional[str] = None
