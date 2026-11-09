"""Bruitages des blocs 5 à 13 (ElevenLabs, une génération chacun, cache film/sons/)."""
import sys
from pathlib import Path

FILM = Path(__file__).resolve().parent
sys.path.insert(0, str(FILM.parents[1] / "panne_internet"))
import sfx_real  # noqa: E402

L = sfx_real.LIBRARY
L["amb_embouteillage"] = ("Motorway traffic jam at dusk heard from outside a car: idling engines, a distant horn, a car door, "
                          "murmur of people, crickets in the fields, no music, seamless ambience", 10.0, 0.45)
L["craquement"] = ("Deep ground crack and rumble: asphalt splitting, a heavy cracking sound, then part of a building facade "
                   "collapsing with falling stones and dust, no music", 6.0, 0.5)
L["alarme"] = ("Building evacuation alarm heard inside an observatory: a repeating electronic two-tone siren, slightly "
               "reverberant, seamless loop, no voices", 8.0, 0.5)
L["impacts"] = ("Distant massive meteor impacts: deep booming explosions far away, rolling thunder-like shock waves, low "
                "rumble, no music", 10.0, 0.5)
L["vent_colline"] = ("Night wind on an open grassy hilltop, rustling grass and a lone tree, very quiet, no insects, no music, "
                     "seamless ambience", 10.0, 0.45)
if __name__ == "__main__":
    print(sfx_real.generate(FILM / "sons", ["amb_embouteillage", "craquement", "alarme", "impacts", "vent_colline"]))
