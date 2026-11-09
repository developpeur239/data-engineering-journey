"""Bloc 4 : voix du narrateur (4 passages, 951 car.), réplique du garçon (MiniMax), 3 images, 1 bruitage. Cache : rien
n'est regénéré.   KIE_API_KEY=… ELEVENLABS_API_KEY=… MINIMAX_API_KEY=… python3 b04/generer.py [voix] [garcon] [images] [sons]"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LUNE = HERE.parents[1]
sys.path.insert(0, str(LUNE.parent / "panne_internet"))
PLAGE = LUNE / "film2d/images/decor_plage.png"
STYLE = "Flat 2D vector illustration, same drawing style, line quality and palette as the reference image. No text, no letters, no logos."

BARRIERE = ("The same beach as the reference image, same viewpoint, same light, same dunes, rocks and wooden boardwalk, calm sea: "
            "across the sandy path in the middle ground, a row of grey metal crowd-control barriers blocks access to the water, "
            "with a blank white rectangular sign panel fixed on the middle barrier (the panel is completely blank). No people. " + STYLE)
PORT = ("A small Mediterranean harbour in the French Riviera on a calm sunny morning, wide shot from the quay: moored sailing boats "
        "and small fishing boats along the quays on the left and right, a stone breakwater with a small white lighthouse on the "
        "right, an open calm channel of water in the centre leading out to the open sea and the horizon, plenty of empty water "
        "in the centre, pastel houses behind on the left, light haze. No people, no boats in the central channel. " + STYLE)
PERSOS = ("Character sheet on a plain flat light grey background: four separate full-body figures standing side by side with wide "
          "space between them, same minimalist character design, proportions and thin discreet outline as the reference image of "
          "the children: 1) a young mother with long straight hair to the middle of her back, simple long coat, seen in "
          "three-quarter back view, standing, legs slightly apart; 2) the same mother crouching down on her heels, seen from the side "
          "facing right, one hand forward as if speaking gently to a child; 3) her son, about 6 years old, short tousled hair, "
          "seen in three-quarter back view, standing, legs slightly apart, holding a small RED plastic beach bucket by its handle "
          "in his right hand; 4) the same boy seen from the side facing right, standing, looking straight ahead, holding the red "
          "bucket. Matte colors, soft daylight, no shadow on the ground, no text.")


def voix():
    from render import tts_elevenlabs  # noqa: PLC0415
    n = sum(tts_elevenlabs(t, HERE / f"{k}.wav", "aQROLel5sQbj1vuIVi6B", "eleven_v4", 0.7, 0.5)
            for k, t in json.loads((HERE / "voix.json").read_text()).items())
    print("caractères facturés (narrateur) :", n)


def garcon():
    """Voix retenue le 5 novembre 2026 : French_MovieLeadFemale, speech-2.8-hd, hauteur +4, vitesse 0,95."""
    import requests  # noqa: PLC0415
    for k, txt in json.loads((HERE / "garcon.json").read_text()).items():
        out = HERE / f"{k}.wav"
        if out.exists():
            continue
        body = {"model": "speech-2.8-hd", "text": txt, "stream": False, "language_boost": "French",
                "voice_setting": {"voice_id": "French_MovieLeadFemale", "speed": 0.95, "vol": 1.0, "pitch": 4},
                "audio_setting": {"sample_rate": 32000, "format": "wav", "channel": 1}}
        r = requests.post("https://api.minimax.io/v1/t2a_v2", json=body, timeout=120,
                          headers={"Authorization": f"Bearer {os.environ['MINIMAX_API_KEY']}", "Content-Type": "application/json"})
        r.raise_for_status(); data = r.json()
        if data.get("base_resp", {}).get("status_code", 0) != 0:
            sys.exit(f"MiniMax : {data.get('base_resp')}")
        raw = out.with_suffix(".raw"); raw.write_bytes(bytes.fromhex(data["data"]["audio"]))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-ac", "1", "-ar", "44100", "-sample_fmt", "s16", str(out)], check=True)
        raw.unlink()
        print("garçon :", out, len(txt), "car.")


def images():
    import kie  # noqa: PLC0415
    print(kie.image(BARRIERE, HERE / "plage_barriere.png", refs=[PLAGE], aspect="16:9", resolution="2K"))
    print(kie.image(PORT, HERE / "port.png", refs=[PLAGE], aspect="16:9", resolution="2K"))
    print(kie.image(PERSOS, HERE / "mere_garcon.png", refs=[LUNE / "film/b03/enfants.png", LUNE / "film2d/images/ref_mere.png",
                                                             LUNE / "film2d/images/ref_garcon.png"], aspect="16:9", resolution="2K"))


def sons():
    import sfx_real  # noqa: PLC0415
    sfx_real.LIBRARY["amb_port"] = ("Small Mediterranean harbour on a calm morning: gentle water lapping against hulls, soft clinking "
                                    "of sailboat rigging and masts, a few seagulls far away, one distant boat horn, no music, seamless ambience", 10.0, 0.45)
    print(sfx_real.generate(HERE, ["amb_port"]))


if __name__ == "__main__":
    for w in sys.argv[1:] or ["voix", "garcon", "images", "sons"]:
        globals()[w]()
