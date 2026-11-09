"""Voix des blocs 5 à 13, extraites telles quelles du texte V13 validé (texte_voix_V13.md). Cache : rien n'est regénéré.
Une entrée par prise : vN narrateur, gN garçon (MiniMax), cN collègue, lN Léa, mN mère (ElevenLabs).
    ELEVENLABS_API_KEY=… MINIMAX_API_KEY=… python3 generer_voix.py [extraire] [generer]"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

FILM = Path(__file__).resolve().parent
sys.path.insert(0, str(FILM.parents[1] / "panne_internet"))
BLOCS = {"b05": "04:00", "b06": "05:00", "b07": "06:00", "b08": "07:00", "b09": "08:00", "b10": "09:00",
         "b11": "10:00", "b12": "11:00", "b13": "11:50"}
ROLES = {"NARR": "v", "GARÇON": "g", "COLLÈGUE": "c", "LÉA": "l", "MÈRE": "m"}
EL = {"v": ("aQROLel5sQbj1vuIVi6B", 0.7, 0.5), "l": ("txtf1EDouKke753vN8SL", 0.5, 0.75),
      "c": ("AfbuxQ9DVtS4azaxN1W7", 0.5, 0.75), "m": ("kwhMCf63M8O3rCfnQ3oQ", 0.5, 0.75)}


def extraire():
    txt = (FILM.parent / "texte_voix_V13.md").read_text()
    for b, hh in BLOCS.items():
        sec = re.split(r"\n## ", txt.split(f"## {hh}–", 1)[1])[0]
        clips, n = {}, {}
        for par in re.split(r"\n\s*\n", sec)[1:]:
            par = par.strip().replace("**", "")
            if not par or par.startswith(("0", "1")) and "·" in par[:20] or par.startswith("[SILENCE"):
                continue
            m = re.match(r"^(NARR|GARÇON|COLLÈGUE|LÉA|MÈRE) : (.*)$", par, re.S)
            role, t = (m.group(1), m.group(2)) if m else ("NARR", par)
            t = t.strip().strip("«»").strip()
            k = ROLES[role]; n[k] = n.get(k, 0) + 1
            clips[f"{k}{n[k]}"] = t
        (FILM / b).mkdir(exist_ok=True)
        (FILM / b / "voix.json").write_text(json.dumps(clips, ensure_ascii=False, indent=1))
        print(b, {k: len(v) for k, v in clips.items()})


def minimax(txt, out):
    import requests  # noqa: PLC0415
    body = {"model": "speech-2.8-hd", "text": txt, "stream": False, "language_boost": "French",
            "voice_setting": {"voice_id": "French_MovieLeadFemale", "speed": 0.95, "vol": 1.0, "pitch": 4},
            "audio_setting": {"sample_rate": 32000, "format": "wav", "channel": 1}}
    r = requests.post("https://api.minimax.io/v1/t2a_v2", json=body, timeout=120,
                      headers={"Authorization": f"Bearer {os.environ['MINIMAX_API_KEY']}", "Content-Type": "application/json"})
    r.raise_for_status(); data = r.json()
    raw = out.with_suffix(".raw"); raw.write_bytes(bytes.fromhex(data["data"]["audio"]))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-ac", "1", "-ar", "44100", "-sample_fmt", "s16", str(out)], check=True)
    raw.unlink()


def generer():
    from render import tts_elevenlabs  # noqa: PLC0415
    tot = {}
    for b in BLOCS:
        for k, t in json.loads((FILM / b / "voix.json").read_text()).items():
            out = FILM / b / f"{k}.wav"
            if out.exists():
                continue
            if k[0] == "g":
                minimax(t, out); tot["minimax"] = tot.get("minimax", 0) + len(t)
            else:
                v, st, si = EL[k[0]]
                tot["elevenlabs"] = tot.get("elevenlabs", 0) + tts_elevenlabs(t, out, v, "eleven_v4", st, si)
    print("caractères facturés :", tot)


if __name__ == "__main__":
    for w in sys.argv[1:] or ["extraire", "generer"]:
        globals()[w]()
