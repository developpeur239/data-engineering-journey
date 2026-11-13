"""Bibliothèque de bruitages du prototype de Nice, générés par ElevenLabs (Sound Effects, stéréo).

Chaque son n'est généré qu'une fois (cache dans son/bruitages/). Clé fournie par le proxy de l'environnement.
    python3 son/bibliotheque.py            # génère les sons manquants
    python3 son/bibliotheque.py nom ...    # (re)génère seulement ceux-là (supprimer le .wav pour régénérer)
"""
import subprocess
import sys
from pathlib import Path

import requests

ICI = Path(__file__).resolve().parent
DOSSIER = ICI / "bruitages"
URL = "https://api.elevenlabs.io/v1/sound-generation"
MODELE = "eleven_text_to_sound_v2"

# nom : (description, durée en s, influence du texte 0–1)
SONS = {
    # --- lits d'ambiance : la Promenade un après-midi normal ---
    "ressac_galets": ("Gentle Mediterranean waves breaking on a pebble beach in Nice, the distinctive rolling clatter of "
                      "pebbles dragged back by each wave, calm sunny afternoon, close and detailed, no people, no music", 10, 0.5),
    "foule_promenade": ("Relaxed crowd on a seaside promenade in the south of France, people chatting in French at a distance, "
                        "footsteps, children laughing far away, summer afternoon, no music", 20, 0.45),
    "trafic_promenade": ("Light traffic on a sunny seaside boulevard heard from the promenade behind you, occasional cars and a "
                         "scooter passing by, distant, no horns, no music", 20, 0.4),
    "vent_palmiers": ("Light warm sea breeze rustling dry palm fronds, gentle, summer afternoon, no music", 15, 0.5),
    "mouettes": ("A few seagulls calling over the Mediterranean sea, distant, occasional calls, no music", 12, 0.5),
    # --- le basculement ---
    "frisson": ("A very low, barely perceptible rumble from deep underground, like the whole planet shifting, slowly swelling, "
                "ominous, realistic, no music", 6, 0.55),
    "retrait_eau": ("The sea pulling away from a pebble beach: a long continuous backwash sucking and hissing through millions "
                    "of pebbles, the sound slowly moving away, eerie, the waves do not come back, no music", 15, 0.6),
    "ecoulement": ("Seawater draining off exposed rocks and seaweed, trickling, gurgling, dripping, close and wet, no music", 10, 0.55),
    "foule_etonnee": ("A crowd on a beach promenade becoming puzzled then worried, murmurs rising, a few people exclaiming in "
                      "French, someone shouts 'Regardez la mer !', confused voices, no screaming, no music", 12, 0.5),
    "mouettes_envol": ("A flock of seagulls suddenly taking off together, many wings flapping loudly, alarmed calls, no music", 5, 0.6),
    # --- le fond découvert ---
    "coque_plastique": ("A small fiberglass motorboat hull settling and scraping onto rocks as the water drains away, hollow "
                        "creak and grind, no music", 4, 0.6),
    "coque_bois": ("A wooden fishing boat slowly tipping over onto wet sand and pebbles, deep wood creaking, a mast rope "
                   "slapping, no music", 4, 0.6),
    "amarres": ("Mooring ropes straining and creaking, a heavy metal anchor chain dragging over rocks, no music", 6, 0.55),
    "poissons": ("Stranded fish flopping on wet pebbles, small wet slaps, close, no music", 5, 0.6),
    "pas_galets": ("Several people walking quickly down a pebble beach toward the water, crunching footsteps on pebbles, "
                   "no voices, no music", 8, 0.55),
    # --- la tension monte ---
    "chien": ("A small dog barking nervously in the distance near a seaside, no music", 4, 0.55),
    "alarme_voiture": ("A car alarm going off in the distance on a city boulevard, no music", 6, 0.55),
    "grondement": ("Deep rumble of the earth slowly growing stronger, distant thunder-like groan of the ground, cinematic "
                   "but realistic, building, no music", 10, 0.55),
    "vent_monte": ("Wind rising over the sea, gusts becoming stronger and colder, whistling slightly, no music", 12, 0.5),
    # --- le temps qui s'écoule (calé sur le compteur) ---
    "tic": ("A single crisp mechanical clock tick, close, dry, one tick only, no reverb, no music", 1, 0.7),
    "coup_final": ("Sudden deep sub-bass boom with a short dark reverberant tail, cinematic hit, no music", 3, 0.6),
}


def genere(noms=None):
    DOSSIER.mkdir(parents=True, exist_ok=True)
    for nom in noms or SONS:
        wav = DOSSIER / f"{nom}.wav"
        if wav.exists():
            continue
        texte, duree, infl = SONS[nom]
        r = requests.post(URL, headers={"xi-api-key": "proxy-injected"}, timeout=180,
                          json={"text": texte, "duration_seconds": duree, "prompt_influence": infl, "model_id": MODELE})
        r.raise_for_status()
        mp3 = wav.with_suffix(".mp3")
        mp3.write_bytes(r.content)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mp3), "-ar", "48000", "-ac", "2", str(wav)], check=True)
        mp3.unlink()
        print(f"généré : {nom} ({duree} s)", flush=True)


if __name__ == "__main__":
    genere(sys.argv[1:] or None)
