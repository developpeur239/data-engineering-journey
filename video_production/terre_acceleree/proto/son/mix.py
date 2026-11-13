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


import json
ETAT = json.load(open(ICI.parent / "etat.json"))          # événements de la scène (node etat.cjs)

continu, ponctuel = np.zeros((N, 2)), np.zeros((N, 2))

# ===================== CONTINU : ce que l'image montre en permanence =====================
# 1. L'eau. Ressac sur les galets, puis la mer qui aspire en reculant, puis l'eau qui s'égoutte du fond découvert.
#    Plus elle s'éloigne, plus elle est faible, sourde (passe-bas) et réverbérée.
place(continu, "ressac_galets", 0, 0, boucle=True, auto=[(0, 0), (6, 0), (9, -5), (12, -13), (15, -24), (20, -30)],
      glisse=[(0, 16000), (6, 16000), (13, 900), (20, 700)], rev=0.25)
place(continu, "retrait_eau", 6.4, -2, fi=2.2, auto=[(6.4, -6), (9, 0), (12, 0), (15, -6), (20, -13)],
      glisse=[(6.4, 16000), (11, 9000), (16, 2600), (20, 1500)], rev=0.3)
place(continu, "ecoulement", 12.0, -10, boucle=True, fi=2.0, pan=-0.15)
continu *= 10 ** (env([(0, 0), (14.55, 0), (14.75, -4), (15.15, -4), (15.5, 0), (20, 0)], T) / 20)[:, None]   # respiration sous-titre


# 2. Le tic-tac du compteur : son tempo suit la vitesse à laquelle le compteur défile (même calcul que scene.js).
def jour_h(t):
    return 24 - 2.5 * np.clip(t / DUREE, 0, 1) ** 3


def bpm(t):
    vitesse = (jour_h(t) - jour_h(t + 0.05)) * 60 / 0.05          # minutes affichées par seconde
    return 60 + 25 * np.log2(1 + vitesse)                         # 60 bpm au repos, ≈ 175 quand il s'emballe


tic = charge("tic")[int(0.77 * SR): int(0.77 * SR) + int(0.11 * SR)].mean(1)
tic = sosfilt(butter(2, 350, "highpass", fs=SR, output="sos"), tic)
tic *= np.r_[np.linspace(0, 1, 48), np.ones(len(tic) - 48 - 960), np.linspace(1, 0, 960)]
tic /= np.abs(tic).max()
temps, phase, t = [], 0.0, 0.3
while t < DUREE - 0.2:
    phase += bpm(t) / 60 * 0.002
    if phase >= 1:
        phase -= 1
        temps.append(t)
    t += 0.002
temps = [0.3] + temps
tictac = np.zeros(N)
for k, t0 in enumerate(temps):
    hauteur, g = (1.0, 1.0) if k % 2 == 0 else (0.84, 0.85)      # tic … tac
    x = np.interp(np.arange(0, len(tic) - 1, hauteur), np.arange(len(tic)), tic)
    j = int(t0 * SR); x = x[: N - j]
    tictac[j:j + len(x)] += x * g
th = (-0.45 + 1) * np.pi / 4                                        # côté du compteur (gauche)
continu += np.stack([tictac * np.cos(th), tictac * np.sin(th)], 1) * np.sqrt(2) * 10 ** (-17 / 20)
print(f"tic-tac : {len(temps)} coups, {bpm(1):.0f} bpm au début → {bpm(19.5):.0f} bpm à la fin")

# ===================== PONCTUEL : seulement quand on le voit =====================
# Voitures : uniquement pendant qu'elles sont à l'écran, au plus près, du côté où on les voit.
for c in range(len(ETAT[0]["autos"])):
    vus = [(e["t"], e["autos"][c]) for e in ETAT if e["autos"][c]["vis"]]
    if not vus:
        continue
    tp = round((vus[0][0] + vus[-1][0]) / 2, 2); a = min(vus, key=lambda v: v[1]["d"])[1]   # milieu du passage à l'écran
    place(ponctuel, "voiture_passe", max(0, tp - 1.56), -2 - 20 * np.log10(a["d"] / 20), pan=float(np.clip(a["x"], -0.9, 0.9)),
          lp=6000, rev=0.15, fi=0.4, fo=0.8)
    print(f"voiture {c} : à l'écran de {vus[0][0]} à {vus[-1][0]} s, au plus près à {tp} s ({a['d']} m)")

# Les gens réagissent (10,9 → 15,8 s), puis certains descendent sur les galets (12,6 s).
place(ponctuel, "foule_etonnee", 11.0, -5, fi=0.8, fo=0.3)
place(ponctuel, "pas_galets", 12.7, -9, lp=6000, pan=-0.3, fo=1.2, rev=0.15)

# Chaque bateau qui touche le fond (instants tirés de la scène), de plus en plus loin.
echoues = []
for a, b in zip(ETAT, ETAT[1:]):
    echoues += [b["t"]] * (b["echoues"] - a["echoues"])
sons = ["coque_plastique", "coque_bois", "amarres", "coque_plastique", "coque_bois", "coque_plastique", "coque_bois", "coque_plastique"]
for k, t0 in enumerate(echoues):
    place(ponctuel, sons[k % len(sons)], t0, -8 - 1.2 * k, decalage=[0, 0, 0, 1.0, 0.6, 0.3, 1.2, 1.5][k % 8],
          pan=[0.45, -0.25, 0.5, -0.5, 0.6, 0.1, -0.6, 0.3][k % 8], lp=4500 - 350 * k, rev=0.4, fi=0.02, fo=0.6)
print("bateaux échoués à", echoues)

mix = continu + ponctuel
mix[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))[:, None]
mix[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))[:, None]

brut = ICI / "_brut.wav"
wavfile.write(brut, SR, (mix / (np.abs(mix).max() * 1.05) * 32767).astype(np.int16))
I = lufs(brut)
sortie = ICI.parent / "son.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af",
                f"highpass=f=30,volume={-14 - I + 1.2:.2f}dB,alimiter=limit=0.75:attack=2:release=80:level=disabled",
                "-ar", "48000", str(sortie)], check=True)
brut.unlink()
print("ok", sortie)
