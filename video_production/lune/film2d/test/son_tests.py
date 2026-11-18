"""Son des deux plans tests, puis assemblage avec les vidéos muettes.

    python3 son_tests.py   → test/plan_calern.mp4, test/plan_espace.mp4, test/tests_2_plans.mp4

Calern : ambiance de jour + clics de clavier calés sur les frappes de Léa + pas calés sur chaque pose du talon.
Espace : grondement + montée + nappe sombre (bruitages déjà générés, aucun nouveau crédit).
"""
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parents[2] / "panne_internet"))
from assemble import SFX, SR, fade, load, loop, norm, put, rms, taps  # noqa: E402
import fx  # noqa: E402

T = 4.0
N = int(SR * T)


def footstep(rng):
    n = int(0.09 * SR); t = np.arange(n) / SR
    x = rng.normal(0, 1, n) * np.exp(-t / 0.018)
    k = np.exp(-np.arange(-20, 21) ** 2 / 60.0); x = np.convolve(x, k / k.sum(), "same")   # sourd : semelle sur béton
    thump = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.03)
    return norm(x * 0.7 + thump * 0.6)


def write(sig, path):
    sig = np.where(np.abs(sig) > 0.85, np.sign(sig) * (0.85 + 0.1 * np.tanh((np.abs(sig) - 0.85) / 0.1)), sig)
    pcm = (np.clip(sig, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(path)],
                   input=pcm.tobytes(), check=True)


def mux(video, wav, out):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(video), "-i", str(wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest", "-movflags", "+faststart", str(out)], check=True)


def main():
    rng = np.random.default_rng(2)
    # --- Calern
    a = np.zeros(N)
    put(a, fade(loop(rms(load(SFX / "amb_calern_jour.wav"), -28), T), 0.3, 0.3), 0)
    grains = taps(load(SFX / "phone_typing.wav"))
    for k in np.arange(0.15, 4.2, 0.23):                       # mêmes instants que les mains de Léa (pieces.Lea)
        if int(k * 13) % 5 != 0 and k < T - 0.12:
            put(a, norm(grains[rng.integers(len(grains))]), k, 0.07 * rng.uniform(0.8, 1.1))
    for st in [k * 1.0 for k in range(0, 5)] + [(k + 0.5) * 1.0 for k in range(0, 4)]:   # appuis du talon (P = 1 s)
        put(a, footstep(rng), st, 0.16 * rng.uniform(0.85, 1.05))
    write(a * 1.3, HERE / "son_calern.wav")
    mux(HERE / "plan_calern_muet.mp4", HERE / "son_calern.wav", HERE / "plan_calern.mp4")
    # --- espace
    b = np.zeros(N)
    put(b, fade(fx.drone("dark", T), 0.5, 0.2), 0, 0.25)
    r = norm(load(SFX / "space_rumble.wav"))[:N]
    put(b, r * np.linspace(0.3, 1.0, len(r)), 0, 0.6)
    put(b, fx.riser(T), 0, 0.35)
    write(b * 1.2, HERE / "son_espace.wav")
    mux(HERE / "plan_espace_muet.mp4", HERE / "son_espace.wav", HERE / "plan_espace.mp4")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(HERE / "plan_calern.mp4"), "-i", str(HERE / "plan_espace.mp4"),
                    "-filter_complex", "[0:v][0:a][1:v][1:a]concat=n=2:v=1:a=1[v][a]", "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-movflags", "+faststart", str(HERE / "tests_2_plans.mp4")], check=True)
    print("ok")


if __name__ == "__main__":
    main()
