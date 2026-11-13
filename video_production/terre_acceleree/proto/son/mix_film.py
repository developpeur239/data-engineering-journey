"""Mixage des séquences du film (règle validée : on n'entend que ce qu'on voit), à partir des relevés de scène.

    python3 son/mix_film.py ouverture|espace|kourou|paris|equateur|apesanteur|nicepente|anneau|fin
        → son_<séquence>.wav (stéréo 48 kHz, −14 LUFS, crête −1,5 dBTP)

Continu : ce que l'image montre en permanence (l'eau, la ville, le vent sur le pont…) + le tic-tac du compteur.
Tic-tac du film : son tempo suit la durée du jour elle-même (64 bpm à 24 h → 86 à 12 h → 121 à 4 h → 166 à 59 min) ;
il accélère avec la Terre du début à la fin, sans à-coups d'une séquence à l'autre.
Ponctuel : seulement au moment où on le voit (séismes, vitres, bille, fusée, rires, foule qui fuit, chaises qui glissent…).
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, fftconvolve, sosfilt

ICI = Path(__file__).resolve().parent
BIB = ICI / "bruitages"
SR = 48000
rng = np.random.default_rng(5)
_cache = {}


def lufs(path):
    err = subprocess.run(["ffmpeg", "-nostats", "-i", str(path), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    return float([l for l in err.splitlines() if l.strip().startswith("I:")][-1].split()[1])


def charge(nom):
    if nom not in _cache:
        p = BIB / f"{nom}.wav"
        sr, a = wavfile.read(p)
        a = a.astype(np.float64) / 32768.0
        if a.ndim == 1:
            a = np.stack([a, a], 1)
        _cache[nom] = a * 10 ** ((-23 - lufs(p)) / 20)                # tous à −23 LUFS
    return _cache[nom]


def env(points, t):
    xs, ys = zip(*points)
    return np.interp(t, xs, ys)


def passe_bas(a, f):
    return sosfilt(butter(4, min(f, SR / 2 - 100), "lowpass", fs=SR, output="sos"), a, axis=0)


_L = int(1.4 * SR)
_IR = rng.normal(size=(_L, 2)) * np.exp(-np.arange(_L) / SR * 4.8)[:, None]
_IR[: int(0.012 * SR)] = 0
_IR /= np.sqrt((_IR ** 2).sum(0))


class Bus:
    def __init__(self, duree):
        self.D, self.N = duree, int(SR * duree)
        self.T = np.arange(self.N) / SR
        self.a = np.zeros((self.N, 2))

    def place(self, nom, debut, gain=0.0, auto=None, fin=None, fi=0.05, fo=0.3, pan=0.0, lp=None, rev=0.0, decalage=0.0, boucle=False):
        a = charge(nom)[int(decalage * SR):]
        fin = self.D if fin is None else min(fin, self.D)
        n = int((fin - debut) * SR)
        if n <= 0:
            return
        if boucle and len(a) < n:
            xf = SR
            w = np.linspace(0, 1, xf)[:, None]
            out = a.copy()
            while len(out) < n:
                out = np.concatenate([out[:-xf], out[-xf:] * (1 - w) + a[:xf] * w, a[xf:]])
            a = out
        a = a[:n].copy(); n = len(a)
        t = debut + np.arange(n) / SR
        if lp:
            a = passe_bas(a, lp)
        g = 10 ** ((gain + (env(auto, t) if auto else 0)) / 20)
        g = g * np.clip(np.arange(n) / (fi * SR + 1), 0, 1) * np.clip((n - np.arange(n)) / (fo * SR + 1), 0, 1)
        a = a * g[:, None]
        if pan:
            th = (pan + 1) * np.pi / 4
            m = a.mean(1)
            a = np.stack([m * np.cos(th), m * np.sin(th)], 1) * np.sqrt(2) * 0.5 + a * 0.5
        if rev:
            a = a * (1 - rev * 0.5) + fftconvolve(a, _IR, axes=0)[:n] * rev
        i = int(debut * SR)
        self.a[i:i + n] += a[: self.N - i]

    def tictac(self, jour, debut=0.3, fin=None, gain=-10):
        """jour : fonction t → durée du jour (h). Tempo = 64 + 22·log2(24 / jour)."""
        fin = self.D - 0.2 if fin is None else fin
        tic = charge("tic")[int(0.77 * SR): int(0.77 * SR) + int(0.11 * SR)].mean(1)
        tic = sosfilt(butter(2, 350, "highpass", fs=SR, output="sos"), tic)
        tic *= np.r_[np.linspace(0, 1, 48), np.ones(len(tic) - 48 - 960), np.linspace(1, 0, 960)]
        tic /= np.abs(tic).max()
        temps, phase, t = [debut], 0.0, debut
        while t < fin:
            phase += (64 + 22 * np.log2(24 / jour(t))) / 60 * 0.002
            if phase >= 1:
                phase -= 1
                temps.append(t)
            t += 0.002
        piste = np.zeros(self.N)
        for k, t0 in enumerate(temps):
            hauteur, g = (1.0, 1.0) if k % 2 == 0 else (0.84, 0.85)
            x = np.interp(np.arange(0, len(tic) - 1, hauteur), np.arange(len(tic)), tic)
            j = int(t0 * SR); x = x[: self.N - j]
            piste[j:j + len(x)] += x * g
        th = (-0.45 + 1) * np.pi / 4
        self.a += np.stack([piste * np.cos(th), piste * np.sin(th)], 1) * np.sqrt(2) * 10 ** (gain / 20)
        return len(temps), 64 + 22 * np.log2(24 / jour(debut)), 64 + 22 * np.log2(24 / jour(fin))

    def ecrire(self, nom, fondu_fin=0.4, silence=False):
        mix = self.a
        mix[-int(fondu_fin * SR):] *= np.linspace(1, 0, int(fondu_fin * SR))[:, None]
        mix[:int(0.03 * SR)] *= np.linspace(0, 1, int(0.03 * SR))[:, None]
        sortie = ICI.parent / f"son_{nom}.wav"
        if silence or np.abs(mix).max() < 1e-6:
            wavfile.write(sortie, SR, np.zeros((self.N, 2), np.int16)); print("ok (silence)", sortie); return
        brut, comp = ICI / f"_brut_{nom}.wav", ICI / f"_comp_{nom}.wav"
        wavfile.write(brut, SR, (mix / (np.abs(mix).max() * 1.05) * 32767).astype(np.int16))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(brut), "-af", "acompressor=threshold=-26dB:ratio=2.2:attack=25:release=400:makeup=1", str(comp)], check=True)
        I = lufs(comp)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(comp), "-af",
                        f"highpass=f=30,volume={-14 - I + 2.6:.2f}dB,alimiter=limit=0.70:attack=2:release=80:level=disabled", "-ar", "48000", str(sortie)], check=True)
        brut.unlink(); comp.unlink()
        print("ok", sortie)


def relevé(nom):
    p = ICI.parent / f"etat_{nom}.json"
    return json.load(open(p)) if p.exists() else None


def jour_de(E):
    TT = np.array([e["t"] for e in E]); J = np.array([e["jour"] for e in E])
    return lambda t: float(np.interp(t, TT, J))


def premier(E, cond, defaut=None):
    return next((e["t"] for e in E if cond(e)), defaut)


# ===================== les séquences =====================
def ouverture(E):
    b = Bus(7); b.place("grave_ouverture", 0, -3, fi=0.6, fo=1.5, lp=400)
    print("tic-tac", b.tictac(jour_de(E), debut=1.0, gain=-11)); b.ecrire("ouverture", fondu_fin=0.8)


def espace(E):
    b = Bus(50)
    b.place("ocean_planetaire", 0, -6, boucle=True, lp=700, fi=1.5, fo=1.0, rev=0.3)    # les océans qui se déplacent
    print("tic-tac", b.tictac(jour_de(E))); b.ecrire("espace", fondu_fin=0.6)


def kourou(E):
    b = Bus(55)
    TT = [e["t"] for e in E]
    niveau = [-4 + 0.05 - e["visuel"] for e in E]                          # niveau de la mer dans la scène (m)
    b.place("vagues_sable", 0, 0, boucle=True, auto=list(zip(TT, [-2 * max(0, n + 1) for n in niveau])), rev=0.2)
    t_rue = premier(E, lambda e: -4 + 0.05 - e["visuel"] > -0.6, 22)       # l'eau atteint la Promenade puis les rues
    b.place("eau_envahit", t_rue, -3, boucle=True, fi=2.5, auto=[(t_rue, -6), (t_rue + 15, 0), (55, 2)], rev=0.2)
    t_fuite = premier(E, lambda e: e["reagi"] > 0, 21)
    b.place("foule_fuit", t_fuite, -5, fi=0.6, fo=1.5, rev=0.2)
    print("eau dans les rues à", t_rue, "s ; fuite à", t_fuite, "s ; tic-tac", b.tictac(jour_de(E))); b.ecrire("kourou", fondu_fin=0.6)


def paris(E):
    b = Bus(90)
    TT = [e["t"] for e in E]
    nuit = [(-8 if e["jourNuit"] < -0.1 else 0) for e in E]
    b.place("ville_paris", 0, -2, boucle=True, auto=list(zip(TT, nuit)), rev=0.15)
    q = [e["seisme"] for e in E]
    b.place("seisme", 14, 0, boucle=True, auto=list(zip(TT, [20 * np.log10(max(v, 0.02)) for v in q])), lp=4000, fi=1.0, rev=0.2)
    for t0, p in [(18.5, -0.4), (27, 0.5), (36, -0.2)]:
        b.place("vitres", t0, -6, pan=p, rev=0.3, fo=0.8)
    b.place("alarmes_voitures", 20, -10, fi=1.0, fo=3.0, rev=0.4, fin=40)
    b.place("bille_roule", 79.2, -2, fi=0.2, fo=0.8, pan=0.1)              # la bille, en gros plan
    print("tic-tac", b.tictac(jour_de(E))); b.ecrire("paris", fondu_fin=0.6)


def equateur(E):
    b = Bus(70)
    TT = [e["t"] for e in E]
    g = [e["g"] for e in E]
    b.place("vagues_plateforme", 0, -1, boucle=True, rev=0.2, auto=list(zip(TT, [6 * np.log10(max(x, 0.05)) for x in g])),
            lp=None)                                                       # les vagues ralentissent et s'adoucissent
    b.place("vent_pont", 0, -9, boucle=True)
    for t0 in (24.5, 31.0):
        b.place("equipe_rires", t0, -5, fi=0.3, fo=1.2, rev=0.25, pan=0.2)
    b.place("fusee_decollage", 44, 1, fi=0.05, fo=4.0, rev=0.3)            # allumage à 44 s
    b.place("metal_grince", 46, -10, fo=2.0, rev=0.3, pan=-0.4)
    print("tic-tac", b.tictac(jour_de(E))); b.ecrire("equateur", fondu_fin=0.6)


def apesanteur(E):
    b = Bus(30)
    b.place("vagues_plateforme", 0, -3, auto=[(0, 0), (8, -4), (14, -40)], rev=0.2, fo=0.5)    # tout se tait…
    b.place("souffle_doux", 3, -8, boucle=True, fi=3.0)
    b.place("gouttes_montent", 10, -10, boucle=True, fi=3.0, rev=0.4)
    print("tic-tac", b.tictac(jour_de(E), gain=-9)); b.ecrire("apesanteur", fondu_fin=0.6)   # … sauf la pulsation


def nicepente(E):
    b = Bus(50)
    b.place("raclement_chaises", 0, -4, boucle=True, fi=1.5, auto=[(0, -6), (20, 0), (50, 2)], rev=0.2)
    for t0, p in [(3, -0.3), (19, 0.3), (34, 0)]:
        b.place("glisse_gens", t0, -6, pan=p, fo=1.5, rev=0.25)
    for t0, p in [(8, 0.4), (28, -0.4)]:
        b.place("voiture_glisse", t0, -5, pan=p, rev=0.25)
    print("tic-tac", b.tictac(jour_de(E))); b.ecrire("nicepente", fondu_fin=0.6)


def anneau(E):
    b = Bus(50)
    b.place("grondement_geant", 0, -3, boucle=True, lp=2500, fi=2.0, auto=[(0, -10), (30, 0), (46, 2), (48.4, -30)], rev=0.3)
    print("tic-tac", b.tictac(jour_de(E), fin=48.3)); b.ecrire("anneau", fondu_fin=1.6)


def fin(E):
    Bus(20).ecrire("fin", silence=True)                                      # silence total sous les cartons


if __name__ == "__main__":
    nom = sys.argv[1]
    E = relevé({"ouverture": "espace_ouverture", "espace": "espace_espace", "anneau": "espace_anneau", "fin": "espace_fin",
                "paris": "paris_paris", "equateur": "navire_equateur", "apesanteur": "navire_apesanteur"}.get(nom, nom))
    globals()[nom](E)
