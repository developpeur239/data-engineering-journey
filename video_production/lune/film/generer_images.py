"""Images des blocs 5 à 13 (dessins fixes, aucun personnage, aucun astre : la Lune est rendue en code). Cache.
    KIE_API_KEY=… python3 generer_images.py"""
import sys
from pathlib import Path

FILM = Path(__file__).resolve().parent
sys.path.insert(0, str(FILM.parents[1] / "panne_internet"))
import kie  # noqa: E402

STYLE = ("Flat 2D vector illustration, same drawing style, line quality and palette as the reference image. "
         "No people, no Moon, no text, no letters, no logos.")
JOUR, NUIT = FILM / "b04/plage_barriere.png", FILM / "b01/rue_lune.png"
IMAGES = [
    ("b05/embouteillage.png", [JOUR], "A motorway in the south of France at dusk, a long traffic jam: rows of still cars bumper to bumper "
     "on three lanes stretching to the horizon, red tail lights, the nearest car large in the lower right foreground seen from "
     "behind and slightly from the side, fields and low hills on both sides, a clear deep blue-violet evening sky with the last "
     "orange glow on the horizon, the whole upper half of the image is empty sky. "),
    ("b07/cote_inondee.png", [JOUR], "A small coastal town in the south of France where the sea has advanced far inland: a coastal road "
     "disappearing under calm grey water, houses and a small building standing isolated in the water, street lamps and road signs "
     "half submerged, a stranded car with water up to its windows, debris floating, evening light under a heavy grey-violet sky, "
     "the upper third is empty sky. "),
    ("b07/port_vase.png", [FILM / "b04/port.png"], "The same harbour as the reference image, same viewpoint, but the sea has withdrawn "
     "completely: the harbour basin is an expanse of wet grey-brown mud with puddles, the colourful wooden boats lie tilted on their "
     "sides on the mud, mooring ropes hang slack, the breakwater and the white lighthouse are the same, the open sea is a distant "
     "thin line far away, eerie evening light, no people. "),
    ("b07/autoroute_eau.png", [FILM / "b05/embouteillage.png"], "The same motorway traffic jam as the reference image, later in the "
     "evening: beyond the fields on the left, an immense flat sheet of water now covers the land up to the horizon and reflects the "
     "violet sky, a few isolated trees and electricity pylons stand in the water, the cars are still stuck, the whole upper half "
     "of the image is empty sky. "),
    ("b11/colline.png", [NUIT], "A grassy hilltop at night above the countryside of the south of France, a single isolated tree on "
     "the left of the hilltop, a footpath, a parked family car near the top, below a vast dark plain with a few scattered lights and "
     "the coast far away, an immense night sky filling the upper two thirds of the image, empty of any Moon, cold blue moonlight "
     "coming from the upper right. "),
]

if __name__ == "__main__":
    for out, refs, prompt in IMAGES:
        print(kie.image(prompt + STYLE, FILM / out, refs=refs, aspect="16:9", resolution="2K"))
