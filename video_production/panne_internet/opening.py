"""Prototype de l'ouverture (scènes 1 à 3) dans le style de référence : 3D en code + couche graphique + bruitages réels.

    python opening.py <work> [--frames 2,8,15]   # --frames : images de contrôle seulement

Réutilise les voix déjà en cache (aucun crédit), la chronologie de render.py (marge 0,15 s, fins de scène de edit_plan)
et les bruitages ElevenLabs de sfx_real (s'ils sont en cache).
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

import edit_plan as plan
import fx
from render import FPS, PAD_S
from scenes import SCENES

HERE = Path(__file__).parent
LEAD = 0.15
VOICE = "tts_eleven_aQROLel5sQbj1vuIVi6B_eleven_v4"


def timeline(work: Path, idx=(0, 1, 2)) -> dict:
    tts, t, scenes = work / VOICE, 0.0, []
    for i in idx:
        ed = tts / f"{i:02d}_ed.wav"
        with wave.open(str(ed)) as w:
            vd = w.getnframes() / w.getframerate()
        spans = json.loads(ed.with_suffix(".json").read_text())["spans"]
        dur = math.ceil((vd + plan.PAD.get(i + 1, PAD_S)) * FPS) / FPS
        scenes.append({"n": i + 1, "start": t, "dur": dur, "voice": str(ed),
                       "spans": [[t + LEAD + a, t + LEAD + b] for a, b in spans]})
        t += dur
    s2 = scenes[1]["spans"]
    events = {"tap1": s2[1][0] - 0.45, "tap2": s2[1][1] + 0.35}
    return {"fps": FPS, "total": t, "scenes": scenes, "events": events}


def _read(path: Path, sr_out: int = fx.SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr_out), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16) / 32768.0


def _onset(x: np.ndarray) -> float:
    """Premier transitoire net du fichier (pour caler le bip sur l'image)."""
    env = np.abs(x)
    k = int(0.01 * fx.SR)
    env = np.convolve(env, np.ones(k) / k, mode="same")
    i = np.argmax(env > env.max() * 0.35)
    return i / fx.SR


def soundtrack(work: Path, tl: dict) -> tuple[Path, Path, Path, Path]:
    n = int((tl["total"] + 1) * fx.SR)
    voice, sfx, amb, music_env, gate = (np.zeros(n) for _ in range(5))
    gate += 1
    s1, s2, s3 = tl["scenes"]
    for s in tl["scenes"]:
        fx._add(voice, _read(Path(s["voice"])), s["start"] + LEAD)
    real = work / "sfx_real"
    # cuisine : pièce calme (synthèse) ; station : ambiance réelle, qui démarre 1 s avant la coupe (pont sonore)
    room = fx.ambience("room", s1["dur"] + 0.5, 1) * fx._fade_env(int((s1["dur"] + 0.5) * fx.SR), 0, int((s1["dur"] + 0.5) * fx.SR), int(0.8 * fx.SR))
    fx._add(amb, room, 0.0, 0.35)
    if (real / "amb_station.wav").exists():
        st = _read(real / "amb_station.wav")
        a0, a1 = s2["start"] - 1.0, tl["total"]
        L = int((a1 - a0) * fx.SR)
        loop = np.concatenate([st] * (L // len(st) + 1))[:L]
        loop *= fx._fade_env(L, 0, L, int(1.0 * fx.SR))
        loop[int((s3["start"] - a0) * fx.SR):] *= 0.55          # le carton « simulation » : la station s'éloigne
        fx._add(amb, loop, a0, 0.9)
    if (real / "metro_refuse.wav").exists():
        mr = _read(real / "metro_refuse.wav")
        fx._add(sfx, mr, tl["events"]["tap1"] + 0.15 - _onset(mr), 0.8)
    for s in (s2, s3):
        fx._add(sfx, fx.whoosh(), s["start"] - 0.35, 0.4)
    # coupure de musique sur « La lumière brille, mais les données ne passent plus », impact dans le blanc qui suit
    a, b = s2["spans"][2]
    gate[int((a - 0.3) * fx.SR):int((b + 0.05) * fx.SR)] = 0
    hit = fx.impact()[: int(0.9 * fx.SR)]
    fx._add(sfx, hit * np.linspace(1, 0, len(hit)) ** 0.5, b + 0.06, fx.TIERS["medium"][3])
    music_env += fx._fade_env(n, 0, n, int(3 * fx.SR))
    k = int(0.15 * fx.SR)
    gate = np.convolve(gate, np.ones(k) / k, mode="same")
    music = fx.drone("neutral", n / fx.SR) * music_env * gate
    music = music / (np.abs(music).max() + 1e-9) * 0.6
    v16 = (np.clip(voice, -1, 1) * 32767).astype(np.int16)
    sfx = fx.duck_under_voice(sfx, v16, fx.SR, 0.45)
    print(f"Contrôle du mixage : {len(fx.mix_check(v16, fx.SR, sfx, 0.45))} conflit(s)")
    out = work / "opening"
    out.mkdir(exist_ok=True)
    paths = []
    for name, sig in (("voice", voice), ("music", music), ("sfx", sfx), ("amb", amb / (np.abs(amb).max() + 1e-9) * 0.5)):
        fx._write(out / f"{name}.wav", sig)
        paths.append(out / f"{name}.wav")
    return tuple(paths)


def main():
    work = Path(sys.argv[1])
    tl = timeline(work)
    out = work / "opening"
    out.mkdir(parents=True, exist_ok=True)
    (out / "timeline.json").write_text(json.dumps(tl, indent=1))
    print(f"Durée : {tl['total']:.2f} s")
    html = HERE / "3d" / "ouverture.html"
    if "--frames" in sys.argv:
        frames = sys.argv[sys.argv.index("--frames") + 1]
        subprocess.run(["node", str(HERE / "3d" / "render_seq.js"), str(html), str(out / "timeline.json"),
                        str(out / "check"), "1280", str(FPS), frames], check=True)
        return
    video = out / "images.mp4"
    subprocess.run(["node", str(HERE / "3d" / "render_seq.js"), str(html), str(out / "timeline.json"), str(video), "1920", str(FPS)], check=True)
    voice, music, sfx, amb = soundtrack(work, tl)
    mixed = out / "mix.wav"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", str(voice), "-i", str(music), "-i", str(sfx), "-i", str(amb), "-filter_complex",
        "[0:a]highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120,asplit=2[v][key];"
        "[1:a]volume=0.22[mraw];[mraw][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[m];"
        "[2:a]volume=0.45[s];[3:a]volume=0.16[am];"
        "[v][m][s][am]amix=inputs=4:duration=first:normalize=0,loudnorm=I=-14:TP=-2:LRA=11,"
        "aresample=48000,alimiter=limit=0.708:attack=1:release=60:level=false[a]",
        "-map", "[a]", "-c:a", "pcm_s24le", str(mixed)], check=True)
    meas = subprocess.run(["ffmpeg", "-nostats", "-i", str(mixed), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    gain = min(-14.0 - float(meas.rsplit("I:", 1)[1].split("LUFS")[0]), 1.5)
    final = out / "ouverture.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(mixed), "-af", f"volume={gain:.2f}dB",
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(final)], check=True)
    print("Terminé :", final)


if __name__ == "__main__":
    main()
