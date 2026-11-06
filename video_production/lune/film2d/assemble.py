"""Assemblage du prototype 2D (43 s) : film muet + insert du téléphone (8–16 s) + bande-son.

    python3 assemble.py            → film2d/prototype_2d_dernier_echo.mp4

Même règles de son que prototype/mix.py (plan v2), recalées sur le nouveau découpage :
voix castées (ElevenLabs), frappe synchronisée lettre par lettre sur l'insert, silence pendant l'hésitation,
coupure totale au noir (26–30 s), aucune musique au retour, musique douce seulement après « … simulation. ».
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
LUNE = HERE.parent
sys.path.insert(0, str(LUNE / "prototype"))
sys.path.insert(0, str(LUNE.parent / "panne_internet"))
import fx  # noqa: E402

SR, T = 48000, 43.0
N = int(SR * T)
VO, SFX = LUNE / "voix_prototype", LUNE / "prototype" / "son" / "sfx_real"
INSERT_AT = 8.0
# temps de l'insert (insert_2d/build_insert.py, INSERT_LONG=1), en secondes locales
T_MSG, T_TYPE0, T_STEP, T_ERASE0, T_ESTEP, N_KEYS = 0.3, 3.0, 0.3, 6.6, 0.16, 8


def load(p: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def loop(x, d, xf=1.0):
    n, f = int(d * SR), int(xf * SR)
    out = x[: min(len(x), n)].copy()
    while len(out) < n:
        k = min(f, len(out), len(x)); r = np.linspace(0, 1, k)
        out[-k:] = out[-k:] * (1 - r) + x[:k] * r
        out = np.concatenate([out, x[k:]])
    return out[:n]


def fade(x, a=0.0, b=0.0):
    x = x.copy()
    if a:
        k = int(a * SR); x[:k] *= np.linspace(0, 1, k)
    if b:
        k = int(b * SR); x[-k:] *= np.linspace(1, 0, k)
    return x


def put(buf, sig, at, gain=1.0):
    i = int(at * SR); j = min(len(buf), i + len(sig)); buf[i:j] += sig[: j - i] * gain


norm = lambda x, p=1.0: x / (np.abs(x).max() + 1e-9) * p  # noqa: E731
rms = lambda x, db: x / (np.sqrt((x ** 2).mean()) + 1e-12) * 10 ** (db / 20)  # noqa: E731


def taps(x, n_max=12):
    """Découpe les impacts de doigt de l'enregistrement de frappe (grains de 110 ms)."""
    env = np.convolve(np.abs(x), np.ones(240) / 240, "same")
    thr, gap, g = env.max() * 0.35, int(0.09 * SR), int(0.11 * SR)
    out, i = [], 0
    while i < len(env) - g and len(out) < n_max:
        if env[i] > thr:
            s = max(0, i - int(0.005 * SR)); out.append(fade(x[s:s + g], 0.002, 0.04)); i += gap
        else:
            i += 1
    return out


def soundtrack() -> Path:
    voice, sfx, amb, mus = (np.zeros(N) for _ in range(4))
    # --- Calern, nuit (0–22 s) : ambiance plus basse pendant l'insert (on est dans la tête de Léa)
    a = fade(loop(rms(load(SFX / "amb_calern_nuit.wav"), -32), 22.0), 1.0, 0.05)
    a[int(8 * SR):int(16 * SR)] *= 10 ** (-6 / 20)
    put(amb, a, 0.0)
    put(mus, fade(fx.drone("dark", 22.0), 2.0, 0.05), 0.0, 0.07)
    for name, at in [("A1_narr", 0.3), ("A2_collegue", 4.3), ("A3_collegue", 16.4), ("A4_lea", 18.55)]:
        put(voice, norm(load(VO / f"{name}.wav"), 0.6), at)
    put(sfx, norm(load(SFX / "notification.wav")), INSERT_AT + T_MSG, 0.32)
    grains = taps(load(SFX / "phone_typing.wav"))
    rng = np.random.default_rng(7)
    for i in range(N_KEYS):                                   # « J'arrive », lettre par lettre
        put(sfx, norm(grains[i % len(grains)]), INSERT_AT + T_TYPE0 + i * T_STEP, 0.20 * rng.uniform(0.85, 1.1))
    for i in range(N_KEYS):                                   # effacement, plus rapide et plus léger
        put(sfx, norm(grains[(i + 3) % len(grains)]), INSERT_AT + T_ERASE0 + i * T_ESTEP, 0.13 * rng.uniform(0.85, 1.1))
    # --- collision (22–26 s)
    put(mus, fade(fx.drone("dark", 4.0), 0.3, 0.0), 22.0, 0.22)
    put(sfx, fx.riser(4.0), 22.0, 0.35)
    put(sfx, norm(load(SFX / "space_rumble.wav")), 22.0, 0.55)
    put(voice, norm(load(VO / "B1_narr.wav"), 0.6), 22.4)
    # --- noir absolu 26–30 s, Calern de jour 30–34 s, plage 34–43 s ; pas de musique avant la révélation
    put(amb, fade(loop(rms(load(SFX / "amb_calern_jour.wav"), -30), 4.0), 0.02, 0.05), 30.0)
    put(amb, fade(loop(rms(load(SFX / "amb_plage.wav"), -29), 9.0), 0.02, 0.6), 34.0)
    put(voice, norm(load(VO / "B2_narr.wav"), 0.6), 37.6)
    put(mus, fade(fx.drone("bright", 2.2), 1.4, 0.6), 40.8, 0.09)

    under = fx.duck_under_voice(sfx + amb + mus, voice * 32768.0, SR, 1.0, margin=8.0)
    mix = voice + under
    mix[int(26.0 * SR): int(30.0 * SR)] = 0.0
    mix *= 1.45
    mix = np.where(np.abs(mix) > 0.85, np.sign(mix) * (0.85 + 0.1 * np.tanh((np.abs(mix) - 0.85) / 0.1)), mix)
    wav = HERE / "mix_2d.wav"
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(wav)],
                   input=pcm.tobytes(), check=True)
    return wav


def main():
    wav = soundtrack()
    out = HERE / "prototype_2d_dernier_echo.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(HERE / "film_muet.mp4"),
                    "-itsoffset", str(INSERT_AT), "-i", str(HERE / "insert_8s.mp4"), "-i", str(wav),
                    "-filter_complex", f"[0:v][1:v]overlay=0:0:eof_action=pass:enable='between(t,{INSERT_AT},{INSERT_AT + 8})'[v]",
                    "-map", "[v]", "-map", "2:a", "-c:v", "libx264", "-crf", "18", "-preset", "medium", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-t", str(T), "-movflags", "+faststart", str(out)], check=True)
    print("ok", out)


if __name__ == "__main__":
    main()
