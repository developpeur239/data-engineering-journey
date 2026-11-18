"""Bande-son du prototype (43 s) puis assemblage avec la vidéo.

    python3 mix.py <video_muette.mp4> <sortie.mp4>

Voix : ../voix_prototype/*.wav (ElevenLabs). Bruitages : son/sfx_real/*.wav (ElevenLabs Sound Effects).
Musique : nappes de ../../panne_internet/fx.py. Règles du plan v2 : coupure totale au noir (26 s), 4 s de silence
absolu, aucune musique au retour à Calern ni sur la plage, musique douce seulement après « … simulation. ».
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "panne_internet"))
import fx  # noqa: E402

SR, T = 48000, 43.0
N = int(SR * T)


def load(p: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def loop(x: np.ndarray, d: float, xf: float = 1.0) -> np.ndarray:
    """Boucle une ambiance sur d secondes avec un fondu enchaîné à chaque raccord."""
    n, f = int(d * SR), int(xf * SR)
    out = x[: min(len(x), n)].copy()
    while len(out) < n:
        k = min(f, len(out), len(x))
        ramp = np.linspace(0, 1, k)
        out[-k:] = out[-k:] * (1 - ramp) + x[:k] * ramp
        out = np.concatenate([out, x[k:]])
    return out[:n]


def fade(x: np.ndarray, a: float = 0.0, b: float = 0.0) -> np.ndarray:
    x = x.copy()
    if a:
        k = int(a * SR); x[:k] *= np.linspace(0, 1, k)
    if b:
        k = int(b * SR); x[-k:] *= np.linspace(1, 0, k)
    return x


def put(buf, sig, at, gain=1.0):
    i = int(at * SR); j = min(len(buf), i + len(sig)); buf[i:j] += sig[: j - i] * gain


norm = lambda x, p=1.0: x / (np.abs(x).max() + 1e-9) * p  # noqa: E731
rms = lambda x, db: x / (np.sqrt((x ** 2).mean()) + 1e-12) * 10 ** (db / 20)  # noqa: E731  (niveau moyen visé, en dBFS)
VO, SFX = HERE.parent / "voix_prototype", HERE / "son" / "sfx_real"
voice, sfx, amb, mus = (np.zeros(N) for _ in range(4))

# --- A. Calern, nuit (0–22 s) ---
put(amb, fade(loop(rms(load(SFX / "amb_calern_nuit.wav"), -32), 22.0), 1.0, 0.05), 0.0)
put(mus, fade(fx.drone("dark", 22.0), 2.0, 0.05), 0.0, 0.07)
for name, at in [("A1_narr", 0.3), ("A2_collegue", 4.2), ("A3_collegue", 14.8), ("A4_lea", 17.4)]:
    put(voice, norm(load(VO / f"{name}.wav"), 0.6), at)
put(sfx, norm(load(SFX / "notification.wav")), 7.9, 0.32)
put(sfx, norm(load(SFX / "phone_typing.wav")), 10.6, 0.22)

# --- B. Collision (22–26 s) : apogée puis coupure totale ---
put(mus, fade(fx.drone("dark", 4.0), 0.3, 0.0), 22.0, 0.22)
put(sfx, fx.riser(4.0), 22.0, 0.35)
put(sfx, norm(load(SFX / "space_rumble.wav")), 22.0, 0.55)
put(voice, norm(load(VO / "B1_narr.wav"), 0.6), 22.4)

# --- noir absolu 26–30 s, puis Calern de jour (30–34 s) et plage (34–43 s), sans musique ---
put(amb, fade(loop(rms(load(SFX / "amb_calern_jour.wav"), -30), 4.0), 0.02, 0.05), 30.0)
put(amb, fade(loop(rms(load(SFX / "amb_plage.wav"), -29), 9.0), 0.02, 0.6), 34.0)
put(voice, norm(load(VO / "B2_narr.wav"), 0.6), 37.6)
put(mus, fade(fx.drone("bright", 2.2), 1.4, 0.6), 40.8, 0.09)

# les effets et l'ambiance s'effacent sous la voix (fenêtres de 50 ms), puis coupure nette au noir
under = fx.duck_under_voice(sfx + amb + mus, voice * 32768.0, SR, 1.0, margin=8.0)
mix = voice + under
mix[int(26.0 * SR): int(30.0 * SR)] = 0.0
mix = mix * 1.45                                   # crêtes de voix vers −1,2 dBFS
mix = np.where(np.abs(mix) > 0.85, np.sign(mix) * (0.85 + 0.1 * np.tanh((np.abs(mix) - 0.85) / 0.1)), mix)   # limiteur doux

wav = HERE / "son" / "proto_mix.wav"
pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(wav)],
               input=pcm.tobytes(), check=True)
subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", sys.argv[1], "-i", str(wav), "-map", "0:v", "-map", "1:a",
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest", sys.argv[2]], check=True)
print("ok", sys.argv[2])
