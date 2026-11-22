from __future__ import annotations

from typing import Dict, List

from .models import Champion, ComfortTier, DamageProfile, MatchupProfile, PlayerProfile, Role, TeamProfile


CHAMPIONS: Dict[str, Champion] = {
    "Aatrox": Champion(id="Aatrox", name="Aatrox", roles=[Role.TOP], damage=DamageProfile.AD, tags=["frontline", "engage"], base_score=8.1),
    "Ahri": Champion(id="Ahri", name="Ahri", roles=[Role.MID], damage=DamageProfile.AP, tags=["pick", "engage"], base_score=8.4),
    "Akali": Champion(id="Akali", name="Akali", roles=[Role.MID, Role.TOP], damage=DamageProfile.AP, tags=["pick"], base_score=7.8),
    "Alistar": Champion(id="Alistar", name="Alistar", roles=[Role.SUP], damage=DamageProfile.AP, tags=["engage", "frontline", "disengage"], base_score=8.2),
    "Aphelios": Champion(id="Aphelios", name="Aphelios", roles=[Role.BOT], damage=DamageProfile.AD, tags=["scaling"], base_score=8.0),
    "Ashe": Champion(id="Ashe", name="Ashe", roles=[Role.BOT, Role.SUP], damage=DamageProfile.AD, tags=["engage", "poke", "pick"], base_score=7.7),
    "Azir": Champion(id="Azir", name="Azir", roles=[Role.MID], damage=DamageProfile.AP, tags=["scaling", "disengage"], base_score=8.8),
    "Braum": Champion(id="Braum", name="Braum", roles=[Role.SUP], damage=DamageProfile.MIXED, tags=["frontline", "disengage"], base_score=7.6),
    "Caitlyn": Champion(id="Caitlyn", name="Caitlyn", roles=[Role.BOT], damage=DamageProfile.AD, tags=["poke"], base_score=7.9),
    "Camille": Champion(id="Camille", name="Camille", roles=[Role.TOP], damage=DamageProfile.AD, tags=["pick", "scaling"], base_score=7.7),
    "Corki": Champion(id="Corki", name="Corki", roles=[Role.MID], damage=DamageProfile.MIXED, tags=["poke", "scaling"], base_score=8.5),
    "Draven": Champion(id="Draven", name="Draven", roles=[Role.BOT], damage=DamageProfile.AD, tags=["pick"], base_score=7.6),
    "Ezreal": Champion(id="Ezreal", name="Ezreal", roles=[Role.BOT], damage=DamageProfile.AD, tags=["poke"], base_score=7.8),
    "Gnar": Champion(id="Gnar", name="Gnar", roles=[Role.TOP], damage=DamageProfile.AD, tags=["frontline", "engage"], base_score=7.9),
    "Gragas": Champion(id="Gragas", name="Gragas", roles=[Role.TOP, Role.JGL], damage=DamageProfile.AP, tags=["engage", "disengage", "frontline"], base_score=8.0),
    "Gwen": Champion(id="Gwen", name="Gwen", roles=[Role.TOP], damage=DamageProfile.AP, tags=["scaling"], base_score=7.8),
    "Hwei": Champion(id="Hwei", name="Hwei", roles=[Role.MID], damage=DamageProfile.AP, tags=["poke", "disengage"], base_score=8.0),
    "Ivern": Champion(id="Ivern", name="Ivern", roles=[Role.JGL], damage=DamageProfile.AP, tags=["disengage", "scaling"], base_score=7.5),
    "JarvanIV": Champion(id="JarvanIV", name="Jarvan IV", roles=[Role.JGL], damage=DamageProfile.AD, tags=["engage", "frontline"], base_score=8.0),
    "Jax": Champion(id="Jax", name="Jax", roles=[Role.TOP], damage=DamageProfile.MIXED, tags=["scaling"], base_score=7.9),
    "Jayce": Champion(id="Jayce", name="Jayce", roles=[Role.TOP, Role.MID], damage=DamageProfile.AD, tags=["poke"], base_score=8.1),
    "Jinx": Champion(id="Jinx", name="Jinx", roles=[Role.BOT], damage=DamageProfile.AD, tags=["scaling"], base_score=8.5),
    "Kaisa": Champion(id="Kaisa", name="Kai'Sa", roles=[Role.BOT], damage=DamageProfile.MIXED, tags=["scaling", "pick"], base_score=8.4),
    "Kalista": Champion(id="Kalista", name="Kalista", roles=[Role.BOT], damage=DamageProfile.AD, tags=["engage"], base_score=8.1),
    "Karma": Champion(id="Karma", name="Karma", roles=[Role.MID, Role.SUP], damage=DamageProfile.AP, tags=["poke", "disengage"], base_score=8.0),
    "Khazix": Champion(id="Khazix", name="Kha'Zix", roles=[Role.JGL], damage=DamageProfile.AD, tags=["pick"], base_score=7.2),
    "Kindred": Champion(id="Kindred", name="Kindred", roles=[Role.JGL], damage=DamageProfile.AD, tags=["scaling"], base_score=7.8),
    "KSante": Champion(id="KSante", name="K'Sante", roles=[Role.TOP], damage=DamageProfile.AD, tags=["frontline", "disengage"], base_score=8.7),
    "Leblanc": Champion(id="Leblanc", name="LeBlanc", roles=[Role.MID], damage=DamageProfile.AP, tags=["pick", "poke"], base_score=7.9),
    "LeeSin": Champion(id="LeeSin", name="Lee Sin", roles=[Role.JGL], damage=DamageProfile.AD, tags=["engage", "pick"], base_score=8.2),
    "Leona": Champion(id="Leona", name="Leona", roles=[Role.SUP], damage=DamageProfile.AP, tags=["engage", "frontline"], base_score=7.8),
    "Lulu": Champion(id="Lulu", name="Lulu", roles=[Role.SUP], damage=DamageProfile.AP, tags=["disengage", "scaling"], base_score=7.5),
    "Maokai": Champion(id="Maokai", name="Maokai", roles=[Role.JGL, Role.SUP], damage=DamageProfile.AP, tags=["engage", "frontline", "pick"], base_score=8.6),
    "Milio": Champion(id="Milio", name="Milio", roles=[Role.SUP], damage=DamageProfile.AP, tags=["disengage", "scaling"], base_score=7.6),
    "Nautilus": Champion(id="Nautilus", name="Nautilus", roles=[Role.SUP], damage=DamageProfile.AP, tags=["engage", "frontline", "pick"], base_score=8.4),
    "Neeko": Champion(id="Neeko", name="Neeko", roles=[Role.MID, Role.SUP], damage=DamageProfile.AP, tags=["engage", "pick"], base_score=7.8),
    "Nocturne": Champion(id="Nocturne", name="Nocturne", roles=[Role.JGL], damage=DamageProfile.AD, tags=["engage", "pick"], base_score=7.7),
    "Olaf": Champion(id="Olaf", name="Olaf", roles=[Role.TOP, Role.JGL], damage=DamageProfile.AD, tags=["frontline"], base_score=7.3),
    "Orianna": Champion(id="Orianna", name="Orianna", roles=[Role.MID], damage=DamageProfile.AP, tags=["engage", "scaling"], base_score=8.6),
    "Ornn": Champion(id="Ornn", name="Ornn", roles=[Role.TOP], damage=DamageProfile.AP, tags=["frontline", "engage", "scaling"], base_score=8.4),
    "Poppy": Champion(id="Poppy", name="Poppy", roles=[Role.TOP, Role.JGL, Role.SUP], damage=DamageProfile.AD, tags=["frontline", "disengage"], base_score=8.1),
    "Rakan": Champion(id="Rakan", name="Rakan", roles=[Role.SUP], damage=DamageProfile.AP, tags=["engage", "disengage"], base_score=8.5),
    "Rell": Champion(id="Rell", name="Rell", roles=[Role.SUP, Role.JGL], damage=DamageProfile.AP, tags=["engage", "frontline"], base_score=8.5),
    "Renata": Champion(id="Renata", name="Renata Glasc", roles=[Role.SUP], damage=DamageProfile.AP, tags=["disengage", "scaling"], base_score=7.7),
    "Renekton": Champion(id="Renekton", name="Renekton", roles=[Role.TOP], damage=DamageProfile.AD, tags=["frontline", "engage"], base_score=8.3),
    "Rumble": Champion(id="Rumble", name="Rumble", roles=[Role.TOP, Role.JGL], damage=DamageProfile.AP, tags=["engage", "poke"], base_score=8.3),
    "Sejuani": Champion(id="Sejuani", name="Sejuani", roles=[Role.JGL], damage=DamageProfile.AP, tags=["engage", "frontline"], base_score=8.4),
    "Senna": Champion(id="Senna", name="Senna", roles=[Role.BOT, Role.SUP], damage=DamageProfile.AD, tags=["scaling", "poke"], base_score=7.9),
    "Sivir": Champion(id="Sivir", name="Sivir", roles=[Role.BOT], damage=DamageProfile.AD, tags=["scaling", "disengage"], base_score=7.4),
    "Skarner": Champion(id="Skarner", name="Skarner", roles=[Role.JGL, Role.TOP], damage=DamageProfile.AD, tags=["engage", "frontline", "pick"], base_score=8.2),
    "Sylas": Champion(id="Sylas", name="Sylas", roles=[Role.MID], damage=DamageProfile.AP, tags=["engage", "scaling"], base_score=8.0),
    "Taliyah": Champion(id="Taliyah", name="Taliyah", roles=[Role.MID, Role.JGL], damage=DamageProfile.AP, tags=["pick", "poke"], base_score=8.1),
    "Tristana": Champion(id="Tristana", name="Tristana", roles=[Role.MID, Role.BOT], damage=DamageProfile.AD, tags=["scaling"], base_score=8.0),
    "TwistedFate": Champion(id="TwistedFate", name="Twisted Fate", roles=[Role.MID, Role.TOP], damage=DamageProfile.AP, tags=["pick"], base_score=7.7),
    "Varus": Champion(id="Varus", name="Varus", roles=[Role.BOT], damage=DamageProfile.AD, tags=["poke", "pick"], base_score=8.3),
    "Vi": Champion(id="Vi", name="Vi", roles=[Role.JGL], damage=DamageProfile.AD, tags=["engage", "pick"], base_score=8.4),
    "Viego": Champion(id="Viego", name="Viego", roles=[Role.JGL], damage=DamageProfile.AD, tags=["scaling", "pick"], base_score=7.9),
    "Xayah": Champion(id="Xayah", name="Xayah", roles=[Role.BOT], damage=DamageProfile.AD, tags=["scaling", "disengage"], base_score=8.4),
    "Yone": Champion(id="Yone", name="Yone", roles=[Role.MID, Role.TOP], damage=DamageProfile.AD, tags=["engage", "scaling"], base_score=8.2),
    "Zeri": Champion(id="Zeri", name="Zeri", roles=[Role.BOT], damage=DamageProfile.AD, tags=["scaling"], base_score=8.1),
}


def _player(name: str, role: Role, s: List[str], a: List[str], b: List[str]) -> PlayerProfile:
    return PlayerProfile(name=name, role=role, comfort={ComfortTier.S: s, ComfortTier.A: a, ComfortTier.B: b})


def _team(name: str, players: List[PlayerProfile]) -> TeamProfile:
    return TeamProfile(name=name, players={player.role: player for player in players})


CLOUD9 = _team(
    "Cloud9",
    [
        _player("Thanatos", Role.TOP, ["KSante", "Renekton", "Rumble"], ["Gnar", "Aatrox", "Jax", "Ornn"], ["Camille", "Gwen", "Yone"]),
        _player("Blaber", Role.JGL, ["Vi", "Sejuani", "LeeSin"], ["Maokai", "Viego", "JarvanIV", "Nocturne"], ["Kindred", "Poppy", "Skarner"]),
        _player("Jojopyun", Role.MID, ["Ahri", "Azir", "Yone"], ["Orianna", "Corki", "Taliyah", "Sylas"], ["Leblanc", "Tristana", "Hwei"]),
        _player("Berserker", Role.BOT, ["Kaisa", "Varus", "Xayah"], ["Jinx", "Kalista", "Ezreal", "Zeri"], ["Aphelios", "Caitlyn", "Draven"]),
        _player("Vulcan", Role.SUP, ["Rakan", "Rell", "Nautilus"], ["Alistar", "Braum", "Renata", "Milio"], ["Leona", "Karma", "Ashe"]),
    ],
)


MATCHUPS: Dict[str, MatchupProfile] = {
    "c9-tl": MatchupProfile(
        id="c9-tl",
        name="Cloud9 vs Team Liquid",
        blue_team=CLOUD9,
        red_team=_team(
            "Team Liquid",
            [
                _player("Impact", Role.TOP, ["KSante", "Renekton"], ["Gnar", "Ornn", "Aatrox"], ["Gwen", "Jax"]),
                _player("UmTi", Role.JGL, ["Sejuani", "Maokai"], ["Vi", "Poppy", "Skarner"], ["JarvanIV", "Ivern"]),
                _player("APA", Role.MID, ["Azir", "Neeko"], ["Taliyah", "Orianna", "Ahri"], ["Hwei", "Corki"]),
                _player("Yeon", Role.BOT, ["Varus", "Kaisa"], ["Xayah", "Jinx", "Ezreal"], ["Aphelios", "Caitlyn"]),
                _player("CoreJJ", Role.SUP, ["Rakan", "Nautilus"], ["Rell", "Alistar", "Renata"], ["Braum", "Leona"]),
            ],
        ),
    ),
    "c9-fly": MatchupProfile(
        id="c9-fly",
        name="Cloud9 vs FlyQuest",
        blue_team=CLOUD9,
        red_team=_team(
            "FlyQuest",
            [
                _player("Bwipo", Role.TOP, ["Olaf", "Renekton", "KSante"], ["Ornn", "Gnar", "Rumble"], ["Camille", "Gragas"]),
                _player("Inspired", Role.JGL, ["Ivern", "Viego", "Nocturne"], ["Sejuani", "Vi", "Kindred"], ["Maokai", "Skarner"]),
                _player("Quad", Role.MID, ["Azir", "Corki", "Tristana"], ["Orianna", "Ahri", "Hwei"], ["Yone", "Taliyah"]),
                _player("Massu", Role.BOT, ["Kaisa", "Zeri", "Varus"], ["Xayah", "Jinx", "Ezreal"], ["Caitlyn", "Aphelios"]),
                _player("Busio", Role.SUP, ["Rakan", "Rell", "Alistar"], ["Nautilus", "Milio", "Renata"], ["Leona", "Braum"]),
            ],
        ),
    ),
    "c9-geng": MatchupProfile(
        id="c9-geng",
        name="Cloud9 vs Gen.G",
        blue_team=CLOUD9,
        red_team=_team(
            "Gen.G",
            [
                _player("Kiin", Role.TOP, ["KSante", "Rumble", "Jax"], ["Renekton", "Gnar", "TwistedFate"], ["Camille", "Gwen"]),
                _player("Canyon", Role.JGL, ["LeeSin", "Nocturne", "Sejuani"], ["Vi", "Maokai", "Viego"], ["Khazix", "Kindred"]),
                _player("Chovy", Role.MID, ["Azir", "Corki", "Yone"], ["Orianna", "Ahri", "Tristana"], ["Hwei", "Taliyah"]),
                _player("Peyz", Role.BOT, ["Kaisa", "Varus", "Zeri"], ["Xayah", "Jinx", "Kalista"], ["Aphelios", "Ezreal"]),
                _player("Lehends", Role.SUP, ["Rakan", "Alistar", "Maokai"], ["Rell", "Nautilus", "Leona"], ["Braum", "Renata"]),
            ],
        ),
    ),
}


def get_default_matchup() -> MatchupProfile:
    return MATCHUPS["c9-tl"].model_copy(deep=True)
