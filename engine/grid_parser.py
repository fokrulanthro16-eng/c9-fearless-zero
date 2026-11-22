from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, Optional, Set

from .data_snapshot import get_default_matchup
from .models import ComfortTier, MatchupProfile, Role


def _open_lines(path: Path) -> Iterable[str]:
    if path.suffix == ".zst":
        try:
            from compression import zstd  # type: ignore
        except Exception as exc:  # pragma: no cover - depends on Python 3.14 availability
            raise RuntimeError("Python 3.14 compression.zstd is required for .jsonl.zst GRID files") from exc
        with zstd.open(path, "rt", encoding="utf-8") as handle:  # type: ignore[attr-defined]
            yield from handle
        return
    with path.open("r", encoding="utf-8") as handle:
        yield from handle


def _event_fields(event: dict) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    team = event.get("team") or event.get("teamName") or event.get("team_name")
    player = event.get("player") or event.get("playerName") or event.get("summonerName")
    champion = event.get("championId") or event.get("champion_id") or event.get("championName")
    role = event.get("role") or event.get("position")
    return team, player, champion, role


def ingest_grid_matchup(path: Optional[str], fallback: Optional[MatchupProfile] = None) -> MatchupProfile:
    matchup = (fallback or get_default_matchup()).model_copy(deep=True)
    if not path:
        return matchup
    grid_path = Path(path)
    if not grid_path.exists() or grid_path.suffix not in {".jsonl", ".zst"}:
        return matchup

    pools: Dict[str, Dict[Role, Set[str]]] = defaultdict(lambda: defaultdict(set))
    try:
        for line in _open_lines(grid_path):
            if not line.strip():
                continue
            event = json.loads(line)
            if str(event.get("type") or event.get("eventType") or "").upper() not in {"PICK", "CHAMPION_PICK", "CHAMP_SELECT_PICK"}:
                continue
            team, _player, champion, role_value = _event_fields(event)
            if not team or not champion or not role_value:
                continue
            try:
                role = Role(str(role_value).upper())
            except ValueError:
                continue
            pools[str(team)][role].add(str(champion))
    except Exception:
        return matchup

    for team in [matchup.blue_team, matchup.red_team]:
        for role, player in team.players.items():
            observed = pools.get(team.name, {}).get(role, set())
            if observed:
                existing_s = set(player.comfort[ComfortTier.S])
                promoted = sorted(observed - existing_s)
                player.comfort[ComfortTier.A] = sorted(set(player.comfort[ComfortTier.A]).union(promoted))
    return matchup
