"""Son du prototype (20 s), uniquement avec des bruitages déjà générés pour « Le Dernier Écho » (aucun crédit).

  plage    : vagues et foule de amb_plage, puis lointaines et étouffées quand la mer se retire (8 → 16 s)
  port     : ambiance de port, discrète
  retrait  : souffle filtré qui descend (l'eau qui s'en va), 9 → 19 s
  vent     : se lève à partir de 5 s
  grondement : rumble grave, 13 → 20 s
Sortie : son.wav, stéréo 48 kHz, normalisé à −14 LUFS (gain mesuré + limiteur à −1,7 dBFS).
"""
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

ICI = Path(__file__).resolve().parent
LUNE = ICI.parents[1] / "lune"
SR, DUR = 48000, 20.0
N = int(SR * DUR)
t = np.arange(N) / SR
rng = np.random.default_rng(3)


def charge(p):
    sr, a = wavfile.read(p)
    a = a.astype(np.float64)
    a /= np.abs(a).max() + 1e-9
    if a.ndim > 1:
        a = a.mean(1)
    assert sr == SR, (p, sr)
    return a / (np.sqrt((a ** 2).mean()) + 1e-9) * 0.1          # même niveau RMS de départ


def boucle(a, n, xf=SR):
    """Répète a jusqu'à n échantillons avec fondu enchaîné de xf."""
    out = np.zeros(n)
    pos, w = 0, np.linspace(0, 1, xf)
    while pos < n:
        seg = a.copy()
        seg[:xf] *= w
        seg[-xf:] *= w[::-1]
        m = min(len(seg), n - pos)
        out[pos:pos + m] += seg[:m]
        pos += len(a) - xf
    return out


def env(points):
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def filtre(a, kind, f, order=4):
    return sosfilt(butter(order, f, kind, fs=SR, output="sos"), a)


s = lambda u: u * u * (3 - 2 * u)
plage = boucle(charge(LUNE / "prototype/son/sfx_real/amb_plage.wav"), N)
loin = filtre(plage, "lowpass", 700)
u = np.clip((t - 8) / 8, 0, 1)
plage = (plage * (1 - s(u)) + loin * s(u) * 1.3) * env([(0, 1), (8, 1), (16, 0.45), (20, 0.35)])

port = boucle(charge(LUNE / "film/b04/sfx_real/amb_port.wav"), N) * 0.35 * env([(0, 1), (10, 1), (15, 0.3), (20, 0.2)])
vent = filtre(boucle(charge(LUNE / "film/sons/sfx_real/vent_colline.wav"), N), "highpass", 120) * env([(0, 0), (5, 0.05), (14, 0.5), (20, 0.8)])

# retrait de l'eau : bruit rose filtré, fréquence qui descend
bruit = np.cumsum(rng.normal(size=N)); bruit -= filtre(bruit, "lowpass", 20, 2); bruit /= np.abs(bruit).max()
retrait = np.zeros(N)
for k, (f0, f1) in enumerate([(2600, 1400), (1400, 700), (700, 300)]):
    bande = filtre(bruit, "bandpass", [f1 * 0.7, f0])
    retrait += bande * env([(0, 0), (9 + 2.5 * k, 0), (12 + 2.5 * k, 1), (16 + 1.5 * k, 0.6), (20, 0.3)])
retrait *= 0.9 / (np.abs(retrait).max() + 1e-9) * 0.25

rumble = filtre(boucle(charge(LUNE / "prototype/son/sfx_real/space_rumble.wav"), N, SR // 2), "lowpass", 180) * env([(0, 0), (13, 0), (17, 0.9), (20, 1.1)])

mono = plage + port + vent + retrait + rumble
d = int(0.011 * SR)                                                   # légère largeur stéréo
G = mono + 0.15 * np.roll(filtre(mono, "highpass", 300), d)
D = mono + 0.15 * np.roll(filtre(mono, "highpass", 300), -d)
st = np.stack([G, D], 1)
st[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))[:, None]
st[-int(0.6 * SR):] *= np.linspace(1, 0, int(0.6 * SR))[:, None]
st /= np.abs(st).max() * 1.05
brut = ICI / "son_brut.wav"
wavfile.write(brut, SR, (st * 32767).astype(np.int16))
mes = subprocess.run(["ffmpeg", "-nostats", "-i", str(brut), "-af", "ebur128", "-f", "null", "-"],
                     capture_output=True, text=True).stderr
I = float([l for l in mes.splitlines() if l.strip().startswith("I:")][-1].split()[1])
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af",
                f"volume={-14 - I + 2.0:.2f}dB,alimiter=limit=0.82:attack=3:release=60:level=disabled",
                "-ar", "48000", str(ICI / "son.wav")], check=True)
brut.unlink()
print("ok", ICI / "son.wav")
