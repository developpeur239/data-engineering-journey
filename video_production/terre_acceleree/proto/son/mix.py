"""Mixage du prototype de Nice (20 s) à partir de la bibliothèque ElevenLabs (voir conception.md).

    python3 son/mix.py      → son.wav (stéréo 48 kHz, −14 LUFS, crête −1,5 dBTP)

Chaque son est d'abord ramené à −23 LUFS, puis placé avec : gain (dB, automatisable), fondus, panoramique,
filtre passe-bas (fixe ou glissant : la distance), réverbération (l'espace) et boucle si besoin.
"""
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

ICI = Path(__file__).resolve().parent
BIB = ICI / "bruitages"
SR, DUREE = 48000, 20.0
N = int(SR * DUREE)
T = np.arange(N) / SR
rng = np.random.default_rng(11)


def lufs(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    return float([l for l in err.splitlines() if l.strip().startswith("I:")][-1].split()[1])


_cache = {}
def charge(nom):
    if nom not in _cache:
        p = BIB / f"{nom}.wav"
        sr, a = wavfile.read(p)
        assert sr == SR
        a = a.astype(np.float64) / 32768.0
        if a.ndim == 1:
            a = np.stack([a, a], 1)
        _cache[nom] = a * 10 ** ((-23 - lufs(p)) / 20)              # tous à −23 LUFS
    return _cache[nom]


def env(points, t):
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def passe_bas(a, f):
    return sosfilt(butter(4, min(f, SR / 2 - 100), "lowpass", fs=SR, output="sos"), a, axis=0)


# réponse impulsionnelle : espace ouvert de bord de mer (réflexions diffuses, 1,4 s)
_L = int(1.4 * SR)
_IR = rng.normal(size=(_L, 2)) * np.exp(-np.arange(_L) / SR * 4.8)[:, None]
_IR[: int(0.012 * SR)] = 0
_IR /= np.sqrt((_IR ** 2).sum(0))


def place(bus, nom, debut, gain=0.0, auto=None, fin=None, fi=0.05, fo=0.3, pan=0.0, lp=None, glisse=None,
          rev=0.0, decalage=0.0, boucle=False):
    """Pose `nom` à `debut` s. auto = [(t, dB)] (temps absolu) ; glisse = [(t, Hz)] : passe-bas qui varie."""
    a = charge(nom)[int(decalage * SR):]
    fin = DUREE if fin is None else min(fin, DUREE)
    n = int((fin - debut) * SR)
    if boucle and len(a) < n:                                       # boucle avec fondu enchaîné de 1 s
        xf = SR
        w = np.linspace(0, 1, xf)[:, None]
        out = a.copy()
        while len(out) < n:
            out = np.concatenate([out[:-xf], out[-xf:] * (1 - w) + a[:xf] * w, a[xf:]])
        a = out
    a = a[:n].copy()
    n = len(a)
    t = debut + np.arange(n) / SR
    if lp:
        a = passe_bas(a, lp)
    if glisse:                                                      # distance : mélange entre clair et sourd
        f_min = min(f for _, f in glisse)
        sourd = passe_bas(a, f_min)
        k = np.clip((env(glisse, t) - f_min) / (max(f for _, f in glisse) - f_min + 1e-9), 0, 1) ** 0.6
        a = a * k[:, None] + sourd * (1 - k[:, None])
    g = 10 ** ((gain + (env(auto, t) if auto else 0)) / 20)
    g = g * np.clip(np.arange(n) / (fi * SR + 1), 0, 1) * np.clip((n - np.arange(n)) / (fo * SR + 1), 0, 1)
    a = a * g[:, None]
    if pan:                                                         # panoramique à puissance constante
        th = (pan + 1) * np.pi / 4
        m = a.mean(1)
        a = np.stack([m * np.cos(th), m * np.sin(th)], 1) * np.sqrt(2) * 0.5 + a * 0.5
    if rev:
        w = fftconvolve(a, _IR, axes=0)[:n] * rev
        a = a * (1 - rev * 0.5) + w
    i = int(debut * SR)
    bus[i:i + n] += a[: N - i]


amb, evt = np.zeros((N, 2)), np.zeros((N, 2))
souffle = [(0, 0), (14.55, 0), (14.75, -6), (15.15, -6), (15.5, 0), (20, 0)]   # respiration sous le sous-titre

# --- 1. la vie normale ---
place(amb, "ressac_galets", 0, 0, boucle=True, auto=[(0, 0), (6, 0), (9, -5), (12, -13), (15, -24), (20, -30)],
      glisse=[(0, 16000), (6, 16000), (13, 900), (20, 700)], rev=0.25)
place(amb, "foule_promenade", 0, -3, auto=[(0, 0), (10.4, 0), (11.2, -11), (13, -18), (20, -24)], fo=0.5)
place(amb, "trafic_promenade", 0, -11, lp=3200, auto=[(0, 0), (12, 0), (16, -7), (20, -9)], rev=0.15)
place(amb, "vent_palmiers", 0, -7, boucle=True, auto=[(0, 0), (13, 0), (16, -12), (20, -20)])
place(amb, "mouettes", 0, -6, fin=10.6, fo=1.4, pan=0.2, rev=0.2)

# --- 2. le basculement ---
place(evt, "frisson", 5.0, -9, lp=320, fi=2.0, fo=1.5)
place(evt, "retrait_eau", 6.4, -2, fi=2.2, auto=[(6.4, -6), (9, 0), (12, 0), (15, -6), (20, -13)],
      glisse=[(6.4, 16000), (11, 9000), (16, 2600), (20, 1500)], rev=0.3)
place(evt, "mouettes_envol", 10.0, -1, pan=0.6, fi=0.1, fo=1.0, rev=0.15)          # les oiseaux partent les premiers
place(evt, "foule_etonnee", 11.2, -4, fi=0.8, fo=0.2)
place(evt, "pas_galets", 12.8, -9, lp=6000, pan=-0.3, fo=1.2, rev=0.15)
place(evt, "ecoulement", 12.0, -9, boucle=True, fi=2.0, pan=-0.15)

# bateaux qui s'échouent (instants tirés de la scène), de plus en plus loin
coques = [(12.6, "coque_plastique", 0.0, -9, 0.45, 3800), (13.0, "coque_bois", 0.0, -8, -0.25, 5000),
          (13.8, "amarres", 0.0, -10, 0.5, 4500), (14.2, "coque_plastique", 1.0, -12, -0.5, 3000),
          (15.9, "coque_bois", 0.6, -12, 0.6, 2400), (17.1, "coque_plastique", 0.3, -14, 0.1, 2000),
          (17.6, "coque_bois", 1.2, -15, -0.6, 1800), (19.4, "coque_plastique", 1.5, -16, 0.3, 1600)]
for t0, nom, dec, g, p, f in coques:
    place(evt, nom, t0, g, decalage=dec, pan=p, lp=f, rev=0.4, fi=0.02, fo=0.6)
place(evt, "poissons", 14.5, -13, pan=0.2, lp=7000, fo=0.8)

# --- 3. la menace ---
place(evt, "vent_monte", 13.8, -4, fi=3.0, auto=[(13.8, -8), (20, 0)])
place(evt, "grondement", 15.0, -3, fi=1.6, lp=900, auto=[(15, -8), (19.5, 0)])
place(evt, "chien", 15.6, -15, pan=-0.7, lp=3500, rev=0.45)
place(evt, "alarme_voiture", 16.8, -17, pan=0.8, lp=3000, rev=0.5, fo=0.4)

# nettoyage du grave : l'ambiance ne descend pas sous 90 Hz (le grave est réservé au grondement et au coup final)
amb = sosfilt(butter(2, 90, "highpass", fs=SR, output="sos"), amb, axis=0)
mix = (amb * 10 ** ((env(souffle, T) - 6) / 20)[:, None]) + evt * 10 ** (env([(0, -1), (12, 0), (20, 3)], T) / 20)[:, None]
coupe = int(19.6 * SR)                                              # coupure nette : tout s'arrête…
mix[coupe:] *= np.clip(1 - np.arange(N - coupe) / (0.04 * SR), 0, 1)[:, None]
fin = np.zeros((N, 2))
place(fin, "coup_final", 19.55, -1, fi=0.005, fo=0.15)              # … sur un coup grave
mix += fin
mix[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))[:, None]

brut = ICI / "_brut.wav"
wavfile.write(brut, SR, (mix / (np.abs(mix).max() * 1.05) * 32767).astype(np.int16))
I = lufs(brut)
sortie = ICI.parent / "son.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af",
                f"highpass=f=25,volume={-14 - I + 1.2:.2f}dB,alimiter=limit=0.79:attack=2:release=80:level=disabled",
                "-ar", "48000", str(sortie)], check=True)
brut.unlink()
print("ok", sortie)
