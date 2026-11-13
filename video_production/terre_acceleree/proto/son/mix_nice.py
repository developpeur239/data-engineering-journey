"""Mixage de la séquence 1 « Nice » (58 s), même règle que le prototype validé : on n'entend que ce qu'on voit.

    node etat.cjs nice && python3 son/mix_nice.py     → son_nice.wav (−14 LUFS, crête −1,5 dBTP)

Un seul plan continu : la distance caméra ↔ eau évolue en douceur, le son la suit.
Continu : l'eau (sa distance réelle à la caméra) et le tic-tac (tempo = vitesse du compteur).
Ponctuel : voitures à l'écran, réaction des promeneurs, pas sur les galets, chaque bateau qui touche le fond À L'IMAGE.
"""
import subprocess
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

ICI = Path(__file__).resolve().parent
BIB = ICI / "bruitages"
SR, DUREE = 48000, 58.0
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
E = json.load(open(ICI.parent / "etat_nice.json"))
TT = np.array([e["t"] for e in E])
courbe = lambda f: list(zip(TT, [f(e) for e in E]))
continu, ponctuel = np.zeros((N, 2)), np.zeros((N, 2))

# ===================== CONTINU =====================
# L'eau : volume et clarté selon la distance réelle caméra ↔ bord de l'eau (change à chaque plan).
dist = np.array([max(e["drive"], 20.0) for e in E])
g_eau = -13 * np.log10(dist / 75)                                   # loi adoucie : la mer reste présente de loin
lp_eau = np.clip(16000 * (75 / dist) ** 1.6, 900, 16000)
vis = np.array([e["visuel"] for e in E])
recul = np.clip(np.gradient(vis, TT) / 0.5, 0, 1)                    # vitesse à laquelle la mer se retire (0–1)
ressac_g = g_eau - 7 * recul
retrait_g = g_eau + 20 * np.log10(np.clip(recul, 0.03, 1))
place(continu, "ressac_galets", 0, 0, boucle=True, auto=list(zip(TT, ressac_g)), glisse=list(zip(TT, lp_eau)), rev=0.25)
place(continu, "retrait_eau", 0, -1, boucle=True, auto=list(zip(TT, retrait_g)), glisse=list(zip(TT, lp_eau)), rev=0.3)
# l'eau qui s'égoutte du fond découvert : seulement quand on le voit (au-dessus et sur le fond)
gout = [(e["t"], float(np.clip(-3 - (e["hauteur"] - 10) * 0.5, -16, -3)) if e["surFond"] else -60.0) for e in E]   # plus la caméra est basse au-dessus du fond, plus on l'entend
place(continu, "ecoulement", 0, -6, boucle=True, auto=gout, pan=-0.1)
sous = [(0.5, 7.5), (8.5, 15.5), (18, 25), (28, 35), (38.5, 46), (49, 57)]
resp = [(0, 0)]
for a, _ in sous:
    resp += [(a - 0.25, 0), (a - 0.05, -3), (a + 0.35, -3), (a + 0.7, 0)]                 # petite respiration à chaque phrase
continu *= 10 ** (env(sorted(resp), T) / 20)[:, None]

# Tic-tac : tempo = vitesse du compteur (minutes affichées par seconde)
jour = np.array([e["jour"] for e in E])
vit = np.clip(-np.gradient(jour, TT) * 60, 0, None)
bpm = lambda t: 60 + 25 * np.log2(1 + np.interp(t, TT, vit))
tic = charge("tic")[int(0.77 * SR): int(0.77 * SR) + int(0.11 * SR)].mean(1)
tic = sosfilt(butter(2, 350, "highpass", fs=SR, output="sos"), tic)
tic *= np.r_[np.linspace(0, 1, 48), np.ones(len(tic) - 48 - 960), np.linspace(1, 0, 960)]
tic /= np.abs(tic).max()
temps, phase, t = [0.3], 0.0, 0.3
while t < DUREE - 0.2:
    phase += bpm(t) / 60 * 0.002
    if phase >= 1:
        phase -= 1
        temps.append(t)
    t += 0.002
tictac = np.zeros(N)
for k, t0 in enumerate(temps):
    hauteur, g = (1.0, 1.0) if k % 2 == 0 else (0.84, 0.85)
    x = np.interp(np.arange(0, len(tic) - 1, hauteur), np.arange(len(tic)), tic)
    j = int(t0 * SR); x = x[: N - j]
    tictac[j:j + len(x)] += x * g
th = (-0.45 + 1) * np.pi / 4
continu += np.stack([tictac * np.cos(th), tictac * np.sin(th)], 1) * np.sqrt(2) * 10 ** (-10 / 20)
print(f"tic-tac : {len(temps)} coups, {bpm(1):.0f} → {bpm(57):.0f} bpm")

# ===================== PONCTUEL : seulement à l'image =====================
for c in range(len(E[0]["autos"])):                                  # voitures : chaque passage à l'écran
    vus = [(e["t"], e["autos"][c]) for e in E if e["autos"][c]["vis"]]
    segs, cur = [], []
    for v in vus:
        if cur and v[0] - cur[-1][0] > 0.25:
            segs.append(cur); cur = []
        cur.append(v)
    if cur: segs.append(cur)
    for sg in segs:
        tp = (sg[0][0] + sg[-1][0]) / 2; a = min(sg, key=lambda v: v[1]["d"])[1]
        place(ponctuel, "voiture_passe", max(0, tp - 1.56), -2 - 20 * np.log10(max(a["d"], 20) / 20),
              pan=float(np.clip(a["x"], -0.9, 0.9)), lp=6000, rev=0.15, fi=0.4, fo=0.8)
        print(f"voiture {c} : à l'écran {sg[0][0]}–{sg[-1][0]} s, {a['d']} m")

t_reac = next(e["t"] for e in E if e["reagi"] > 0)                   # les promeneurs s'arrêtent et s'étonnent
place(ponctuel, "foule_etonnee", t_reac - 0.3, -7, fi=0.8, fo=0.6, rev=0.2)
t_desc = next(e["t"] for e in E if e["descendent"] > 0)              # des baigneurs descendent sur les galets
place(ponctuel, "pas_galets", t_desc, -10, lp=6000, pan=-0.3, fo=1.2, rev=0.15)
print(f"réaction de la foule à {t_reac} s, pas sur les galets à {t_desc} s")

sons = ["coque_plastique", "coque_bois", "amarres", "coque_plastique", "coque_bois"]
k = 0
for a, b in zip(E, E[1:]):                                           # bateaux : seulement ceux qu'on voit toucher le fond
    for i, (c0, c1) in enumerate(zip(a["coques"], b["coques"])):
        if c1["echoue"] and not c0["echoue"] and c1["vis"]:
            d = c1["d"]
            place(ponctuel, sons[k % len(sons)], b["t"], -1 - 20 * np.log10(max(d, 60) / 100), decalage=[0, 0, 0, 1.0, 0.6][k % 5],
                  pan=float(np.clip(c1["ex"], -0.9, 0.9)), lp=float(np.clip(9000 * (100 / d) ** 1.3, 1500, 9000)), rev=0.4, fi=0.02, fo=0.6)
            print(f"bateau {i} touche le fond à {b['t']} s ({d} m)")
            k += 1

mix = continu * 10 ** (2 / 20) + ponctuel * 10 ** (-3 / 20)        # équilibre : l'eau et le tic-tac portent, les événements ponctuent
mix[-int(0.3 * SR):] *= np.linspace(1, 0, int(0.3 * SR))[:, None]
mix[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))[:, None]

brut = ICI / "_brut_nice.wav"
wavfile.write(brut, SR, (mix / (np.abs(mix).max() * 1.05) * 32767).astype(np.int16))
comp = ICI / "_comp_nice.wav"                                         # compression douce (mastering) avant la normalisation
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af",
                "acompressor=threshold=-26dB:ratio=2.2:attack=25:release=400:makeup=1", str(comp)], check=True)
brut.unlink(); brut = comp
I = lufs(brut)
sortie = ICI.parent / "son_nice.wav"
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af",
                f"highpass=f=30,volume={-14 - I + 3.0:.2f}dB,alimiter=limit=0.70:attack=2:release=80:level=disabled",
                "-ar", "48000", str(sortie)], check=True)
brut.unlink()
print("ok", sortie)
