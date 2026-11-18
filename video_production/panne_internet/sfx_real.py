"""Bruitages réalistes générés par ElevenLabs (Sound Effects), mis en cache dans <work>/sfx_real/.

La clé est lue dans ELEVENLABS_API_KEY (jamais dans le code). Chaque son n'est généré qu'une fois.
Les sons de « signature » (impacts, souffles, montée) restent synthétisés dans fx.py : seuls les objets du
monde réel (terminaux, distributeurs, téléphones, lieux) passent ici.

    python sfx_real.py <work> [nom ...]      # génère les sons manquants (tous, ou ceux nommés)
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

MODEL = "eleven_text_to_sound_v2"

# nom : (description envoyée à ElevenLabs, durée en secondes, influence du texte 0-1)
LIBRARY = {
    # objets : le son exact que fait l'appareil quand il refuse
    "metro_refuse": ("Close-up of a Paris metro ticket vending machine rejecting a contactless bank card: "
                     "two short low electronic error beeps, then a plastic card tapped again on the reader, "
                     "quiet station hall in the background", 3.0, 0.6),
    "card_declined": ("Retail card payment terminal declining a payment: card inserted, short pause, "
                      "then a long harsh error beep from the small speaker, realistic shop", 2.5, 0.65),
    "atm_error": ("Bank ATM on a city street: fingers pressing metal keypad buttons with beeps, "
                  "then a repeated error tone and the card slot motor returning the card", 4.0, 0.6),
    "phone_busy": ("Mobile phone call that cannot connect, heard through the phone earpiece: "
                   "a few seconds of silence then a fast European busy tone, beep beep beep", 4.0, 0.7),
    "phone_error": ("Smartphone notification error buzz, short vibration on a wooden table and a soft "
                    "failed-notification chime", 1.5, 0.6),
    "computer_error": ("Office computer: mouse clicks, a keyboard typing quickly, then a generic system "
                       "error alert sound, not a known brand sound", 3.0, 0.5),
    "pen_paper": ("Ballpoint pen writing numbers quickly on a paper notebook on a shop counter, page turned",
                  4.0, 0.6),
    "cash_coins": ("Small grocery store counter: cash register drawer opening, coins dropped in a tray, "
                   "a banknote unfolded", 3.0, 0.6),
    "terminal_ok": ("Card payment terminal booting up and accepting a payment: soft confirmation beep, "
                    "receipt printer printing a short ticket", 3.5, 0.6),
    "radio_tune": ("Old FM radio being tuned in a quiet apartment: static hiss, tuning sweep, then a clear "
                   "broadcast signal with faint indistinct speech", 4.0, 0.5),
    # lieux (ambiances bouclables)
    "amb_station": ("Paris metro station hall in the morning, footsteps, distant train arriving, "
                    "murmur of commuters, no music", 10.0, 0.4),
    "amb_street": ("Paris street in winter morning, light traffic, footsteps on wet pavement, "
                   "distant scooter, no music", 10.0, 0.4),
    "amb_servers": ("Data center server room, constant fan hum and air conditioning, faint hard drive "
                    "clicks", 10.0, 0.5),
    "amb_hospital": ("Hospital corridor, distant monitor beeps, footsteps, a trolley rolling, quiet voices "
                     "far away, no music", 10.0, 0.4),
    "amb_store": ("Small neighborhood grocery store, fridge hum, people moving, plastic bags, "
                  "muffled tension, no music", 10.0, 0.4),
    "amb_apartment": ("Quiet Paris apartment in the morning, kettle starting, distant city through the "
                      "window, a toddler babbling softly far away", 10.0, 0.4),
    "departures_board": ("Airport terminal departures board: split-flap display flipping rapidly, then a soft "
                         "announcement chime, crowd murmur of stranded travellers, no speech", 6.0, 0.55),
    "amb_queue": ("Tense crowd of people queueing outside on a city sidewalk, murmurs, sighs, shuffling feet, "
                  "distant traffic, no clear words", 10.0, 0.45),
    "child_crying": ("A two-year-old toddler crying and sobbing softly in a metro station, echo of the tiled hall, "
                     "a father hushing gently", 6.0, 0.55),
    "trucks_idle": ("Logistics warehouse yard at dawn: several heavy trucks idling, diesel engines rumbling, "
                    "air brakes hiss, no reversing alarm", 10.0, 0.5),
    "amb_supermarket": ("Supermarket aisle, fridge compressors humming, nervous shoppers, trolley wheels, "
                        "empty shelves, muffled murmurs, no music", 10.0, 0.45),
    "shop_bell": ("Small pharmacy shop door opening with a little bell, footsteps on tiles, quiet interior", 3.0, 0.6),
    "door_knock": ("Knocking on an apartment door in a quiet stairwell, then the door opening with a creak",
                   3.5, 0.6),
    "servers_up": ("Data center: rows of servers powering up, fans spinning up one after another, short positive "
                   "status beeps", 5.0, 0.55),
    "typing_fast": ("Several people typing quickly on keyboards in a technical operations room, mouse clicks, "
                    "quiet concentration", 6.0, 0.55),
    "radio_fm": ("Small FM radio on a kitchen table: light static then a calm broadcast voice, indistinct words, "
                 "warm and close", 8.0, 0.5),
    "monitors_off": ("Rows of office computers crashing: monitors clicking off one after another, fans winding "
                     "down, electrical hum fading", 4.0, 0.55),
    "phone_ring_fail": ("Smartphone calling: two ringback tones then the call drops with a short error beep",
                        4.0, 0.65),
    "notification": ("Short soft smartphone notification chime, clean, modern, not a known brand sound", 1.0, 0.7),
    "digital_clock": ("Digital alarm clock display ticking every second in a silent room, faint electronic beep",
                      4.0, 0.6),
    "terminals_on": ("Several card payment terminals switching on one after another across a city: short "
                     "rising startup beeps, gentle and hopeful", 5.0, 0.6),
}


def eleven_key() -> str:
    """Clé ElevenLabs nettoyée (une virgule ou un espace collé par erreur dans les paramètres la rend invalide)."""
    return os.environ["ELEVENLABS_API_KEY"].strip().strip(",;").strip()


def generate(work: Path, names=None) -> dict[str, Path]:
    """Génère (une seule fois) les sons demandés et renvoie {nom: chemin du .wav 48 kHz mono}."""
    out_dir = work / "sfx_real"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    client = None
    for name in names or LIBRARY:
        text, dur, infl = LIBRARY[name]
        wav = out_dir / f"{name}.wav"
        if not wav.exists():
            if client is None:
                from elevenlabs import ElevenLabs  # noqa: PLC0415
                client = ElevenLabs(api_key=eleven_key())
            mp3 = wav.with_suffix(".mp3")
            with open(mp3, "wb") as f:
                for chunk in client.text_to_sound_effects.convert(
                        text=text, duration_seconds=dur, prompt_influence=infl, model_id=MODEL,
                        output_format="mp3_44100_128"):
                    f.write(chunk)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp3), "-ac", "1", "-ar", "48000",
                            "-sample_fmt", "s16", str(wav)], check=True)
            mp3.unlink()
            print(f"  son généré : {name} ({dur:.1f} s)", flush=True)
        paths[name] = wav
    return paths


if __name__ == "__main__":
    generate(Path(sys.argv[1]), sys.argv[2:] or None)
