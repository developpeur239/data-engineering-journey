"""Moteur commun du film : un bloc = bXX/shots.json (données) + décors réutilisables (film/decors/*.py).

    python3 -m moteur.core b01                    → rendu complet + son + bXX/blocXX.mp4
    python3 -m moteur.core b01 --images 120,400   → seulement ces images (contrôle), dans bXX/.frames/
    python3 -m moteur.core b01 --planche          → une image par plan, sur une planche-contact (bXX/planche.png)
    python3 -m moteur.core b01 --son              → seulement le son (et le contrôle de niveaux)

Temps : partout où un temps est attendu, on peut écrire un nombre (secondes du bloc) ou une ANCRE sur un mot de la voix,
p. ex. "v1:Lune" (début du mot « Lune » de la voix v1), "v1:Lune.end", "v1.end" (fin de la voix), "v2:rues+0.3",
"#plan_C" (début du plan C), "#plan_C.end". Les mots viennent de bXX/mots.json (moteur/mots.py, Whisper contrôlé).
Textes : {"texte", "de", "a", "pos", …} ; avec "reste" (secondes avant le contact à l'instant « de »), le texte devient un
compte à rebours qui défile ("texte": "impact dans {}").
Les voix sont placées dans "voix" : [{"id": "v1", "at": 1.8}, {"id": "v2", "at": "v1.end+1.7"}, …].

Architecture hybride : chaque plan a un décor (« set ») qui rend l'image source, codé dans film/decors/ ; il peut
s'appuyer sur des images générées (dessins fixes), du code (animation, effets) ou une séquence d'images rendue ailleurs
(3D Blender/Tesseract) via un calque {"type": "sequence"}. L'étalonnage commun (film/style.json) s'applique à tout.
"""
from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FILM = Path(__file__).resolve().parents[1]
LUNE = FILM.parent
FONTS = LUNE / "prototype/fonts"
FPS, W, H = 30, 1920, 1080
SR = 48000


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def restant(sec):
    """Temps restant avant le contact, tel que l'affichent tous les compteurs du film."""
    sec = max(0, int(sec))
    j, r = divmod(sec, 86400); h, r = divmod(r, 3600); m, s = divmod(r, 60)
    return f"{j} j {h:02d} h {m:02d} min {s:02d} s"


def taps(windows, step=0.19):
    """Instants des frappes au clavier dans des périodes [(de, a)] : rythme irrégulier, identique image et son."""
    out = []
    for a, b in windows:
        k = 0
        while True:
            x = a + 0.25 + k * step + 0.05 * np.sin(k * 2.3) + (0.12 if k % 7 == 6 else 0.0)
            if x > b - 0.1:
                break
            out.append(x); k += 1
    return out


def synth(kind, rng):
    """Petits sons synthétisés : clic de clavier, vibreur, impulsion laser, bip d'interface."""
    if kind == "clic":
        m = int(0.03 * SR); x = rng.normal(0, 1, m) * np.exp(-np.arange(m) / (0.004 * SR))
        return np.convolve(x, [1, -0.85], "same") * 0.5
    if kind == "vibreur":
        tt = np.arange(int(0.45 * SR)) / SR
        return np.sin(2 * np.pi * 160 * tt) * (np.sin(2 * np.pi * 9 * tt) > 0) * 0.6
    if kind == "laser":
        tt = np.arange(int(0.18 * SR)) / SR
        return np.sin(2 * np.pi * (2400 - 6000 * tt) * tt) * np.exp(-tt / 0.05) * 0.5
    if kind == "bip":
        tt = np.arange(int(0.12 * SR)) / SR
        return np.sin(2 * np.pi * 1320 * tt) * np.exp(-tt / 0.04) * 0.5
    if kind == "rideau":                                       # rideau de fer qui remonte : cliquetis de lames + roulement
        n = int(1.6 * SR); tt = np.arange(n) / SR
        roll = np.convolve(rng.normal(0, 1, n), np.ones(40) / 40, "same") * 0.25
        clk = np.zeros(n)
        for x in np.arange(0.05, 1.5, 0.075 + 0.01 * np.sin(np.arange(0.05, 1.5, 0.075) * 9)):
            m = int(0.02 * SR); i = int(x * SR)
            clk[i:i + m] += rng.normal(0, 1, m) * np.exp(-np.arange(m) / (0.003 * SR)) * 0.7
        return (roll + clk) * np.minimum(1, tt / 0.1) * np.minimum(1, (1.6 - tt) / 0.2)
    raise KeyError(kind)


def dur_of(p: Path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


# ------------------------------------------------------------------ bloc : données + ancres
class Bloc:
    def __init__(self, name: str):
        self.name, self.dir = name, FILM / name
        self.data = json.loads((self.dir / "shots.json").read_text())
        self.words = json.loads((self.dir / "mots.json").read_text())
        self.vdur = {v["id"]: dur_of(self.dir / f"{v['id']}.wav") for v in self.data["voix"]}
        self.vat = {}
        for v in self.data["voix"]:                          # dans l'ordre : une voix peut s'ancrer sur la précédente
            self.vat[v["id"]] = self.t(v["at"])
        self.shots = self.data["plans"]
        self._resolving = set()
        for s in self.shots:
            s["_t0"] = self.t(s["debut"])
        for a, b in zip(self.shots, self.shots[1:]):
            a["_t1"] = b["_t0"]
        self.shots[-1]["_t1"] = self.t(self.data["fin"])
        self.end = self.shots[-1]["_t1"]

    def word(self, vid: str, w: str, which: str) -> float:
        key = w.lower()
        n = 1
        m = re.match(r"(.+)#(\d+)$", key)                      # "la#2" = 2e occurrence de « la »
        if m:
            key, n = m.group(1), int(m.group(2))
        k = 0
        for x in self.words[vid]:
            if re.sub(r"[^\w’']", "", x["w"].lower()) == key:
                k += 1
                if k == n:
                    return self.vat[vid] + (x["end"] if which == "end" else x["start"])
        raise KeyError(f"mot introuvable : {vid}:{w}")

    def t(self, x) -> float:
        if isinstance(x, (int, float)):
            return float(x)
        m = re.match(r"^\s*([^+\-]+?)\s*([+\-]\s*[\d.]+)?\s*$", x)
        ref, off = m.group(1), float(m.group(2).replace(" ", "")) if m.group(2) else 0.0
        if ref.startswith("#"):                                   # début / fin d'un plan
            sid, _, which = ref[1:].partition(".")
            s = next(s for s in self.shots if s["id"] == sid)
            return (s["_t1"] if which == "end" else s["_t0"]) + off
        vid, _, rest = ref.partition(":")
        if not rest:                                              # "v1" ou "v1.end"
            v, _, which = vid.partition(".")
            return self.vat[v] + (self.vdur[v] if which == "end" else 0.0) + off
        w, _, which = rest.rpartition(".") if rest.endswith((".end", ".start")) else (rest, "", "start")
        return self.word(vid, w, which) + off

    def keys(self, t, ks):
        """Images clés [[temps|ancre, v1, v2…], …] interpolées en douceur."""
        pts = [(self.t(k[0]), k[1:]) for k in ks]
        if t <= pts[0][0]:
            return np.array(pts[0][1], float)
        for (ta, va), (tb, vb) in zip(pts, pts[1:]):
            if t <= tb:
                u = ease((t - ta) / max(1e-6, tb - ta))
                return np.array(va, float) * (1 - u) + np.array(vb, float) * u
        return np.array(pts[-1][1], float)

    def shot_at(self, t):
        for s in self.shots:
            if s["_t0"] <= t < s["_t1"]:
                return s
        return self.shots[-1]


# ------------------------------------------------------------------ caméra et étalonnage
def cam(img, cx, cy, zoom, rot=0.0, shake=(0.0, 0.0)):
    """Fenêtre de caméra dans l'image source : centre, zoom (1 = toute la largeur), roulis (degrés), secousse (px)."""
    sh, sw = img.shape[:2]
    zoom = max(zoom, sh / sw * W / H if sw / sh > W / H else 1.0) * (1 + abs(rot) * 0.012)
    wv = sw / zoom; s = W / wv
    cx = np.clip(cx, wv / 2, sw - wv / 2); hv = H / s; cy = np.clip(cy, hv / 2, sh - hv / 2)
    M = np.float32([[s, 0, -(cx - wv / 2) * s + shake[0]], [0, s, -(cy - hv / 2) * s + shake[1]]])
    if rot:
        R = cv2.getRotationMatrix2D((W / 2, H / 2), rot, 1.0)
        M = (np.vstack([R, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]]))[:2].astype(np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)


STYLE = json.loads((FILM / "style.json").read_text())
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_VIG = (((_xx - W / 2) / (W / 2)) ** 2 + ((_yy - H / 2) / (H / 2)) ** 2)


def grade(f, frame_no, look="defaut"):
    """Étalonnage commun du film (film/style.json) : relève/gamma/gain par canal, contraste, saturation, vignette, grain."""
    g = {**STYLE["defaut"], **STYLE.get(look, {})}
    x = np.clip(f / 255.0, 0, 1)
    lift, gam, gain = np.array(g["releve"]), np.array(g["gamma"]), np.array(g["gain"])
    x = gain * (x + lift * (1 - x))
    x = np.clip(x, 0, 1) ** (1 / gam)
    x = (x - 0.5) * g["contraste"] + 0.5
    lum = x @ np.array([0.2126, 0.7152, 0.0722])
    x = lum[..., None] + (x - lum[..., None]) * g["saturation"]
    x *= (1 - g["vignette"] * np.clip(_VIG - 0.15, 0, None) ** 1.3)[..., None]
    if g["grain"]:
        r = np.random.default_rng(frame_no)
        n = cv2.resize(r.normal(0, 1, (H // 2, W // 2)).astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
        x += n[..., None] * g["grain"]
    return np.clip(x * 255, 0, 255)


# ------------------------------------------------------------------ textes
@lru_cache(None)
def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def draw_text(img, txt, xy, fname, size, fill, center=False):
    im = Image.fromarray(img); d = ImageDraw.Draw(im); f = font(fname, size)
    x, y = xy
    if center:
        bb = d.textbbox((0, 0), txt, font=f); x -= (bb[2] - bb[0]) / 2; y -= (bb[3] - bb[1]) / 2
    d.text((x, y), txt, font=f, fill=fill)
    return np.asarray(im)


# ------------------------------------------------------------------ filtres de plan (données) et calques séquence
def apply_filters(f, t, shot, bloc):
    for flt in shot.get("filtres", []):
        k = flt["type"]
        if k == "paupieres":                                  # ouverture des yeux : flou puis net, bord courbe
            o = float(bloc.keys(t, flt["cles"])[0])
            if o < 1:
                f = cv2.GaussianBlur(f, (0, 0), 1 + (1 - o) * 14)
                xs = np.arange(W) / W * 2 - 1
                half = o * H / 2 * (0.62 + 0.38 * np.sqrt(np.clip(1 - xs ** 2, 0, 1)))
                m = np.clip((half[None, :] - np.abs(np.arange(H)[:, None] - H / 2)) / 40 + 0.5, 0, 1)
                f = f * m[..., None]
        elif k == "eclat":                                    # éblouissement bref au raccord
            a = bloc.t(flt["a"]); d = flt.get("duree", 0.5)
            if a <= t < a + d:
                f = f + flt.get("force", 90) * (1 - ease((t - a) / d))
        elif k == "extinction":                                # désature puis s'éteint (retour en arrière)
            a, b = bloc.t(flt["de"]), bloc.t(flt["a"])
            r = float(ease((t - a) / (b - a))) if t > a else 0.0
            if r > 0:
                g = f.mean(2, keepdims=True)
                f = (f * (1 - 0.7 * r) + g * 0.7 * r) * (1 - r) ** 1.2
        elif k == "fondu_noir":
            a, b = bloc.t(flt["de"]), bloc.t(flt["a"])
            f = f * (1 - float(ease((t - a) / (b - a)))) if t > a else f
    for lay in shot.get("calques", []):                        # séquence d'images rendue ailleurs (3D, Tesseract…)
        if lay["type"] == "sequence":
            i = int((t - bloc.t(lay.get("a", shot["_t0"]))) * FPS)
            p = bloc.dir / lay["chemin"].replace("%05d", f"{max(0, i):05d}")
            if p.exists():
                im = np.asarray(Image.open(p).convert("RGBA")).astype(np.float32)
                a = im[..., 3:4] / 255 * lay.get("opacite", 1.0)
                f = f * (1 - a) + im[..., :3] * a
    return f


# ------------------------------------------------------------------ rendu d'une image
_SETS = {}


def get_set(name, bloc):
    if name not in _SETS:
        mod, _, cls = name.partition(".")
        _SETS[name] = getattr(importlib.import_module(f"decors.{mod}"), cls)(bloc)
    return _SETS[name]


def frame(bloc: Bloc, i: int):
    t = i / FPS
    shot = bloc.shot_at(t)
    over = bloc.data.get("textes", [])
    if shot.get("set") == "noir":
        f = np.zeros((H, W, 3), np.float32)
    else:
        st = get_set(shot["set"], bloc)
        src = st.render(t, shot, bloc)
        c = bloc.keys(t, shot["camera"]) if "camera" in shot else np.array([src.shape[1] / 2, src.shape[0] / 2, 1.0, 0.0])
        cx, cy, z = c[:3]; rot = c[3] if len(c) > 3 else 0.0
        cy += st.bob(t, shot, bloc) if hasattr(st, "bob") else 0.0
        shk = (0.0, 0.0)
        for sk in shot.get("secousses", []):
            a = bloc.t(sk["a"])
            if t > a:
                amp = sk.get("force", 9) * np.exp(-(t - a) / sk.get("duree", 0.45))
                shk = (shk[0] + amp * np.sin(t * 71), shk[1] + amp * np.sin(t * 53 + 1))
        rot += shot.get("respiration_camera", 0.0) * np.sin(2 * np.pi * t / 3.7)
        f = cam(src, cx, cy, z, rot, shk)
        f = apply_filters(f, t, shot, bloc)
        f = grade(f, i, shot.get("look", bloc.data.get("look", "defaut")))
    out = np.clip(f, 0, 255).astype(np.uint8)
    for tx in over:                                             # étiquette, cartons : données du bloc
        a, b = bloc.t(tx["de"]), bloc.t(tx["a"])
        if not (a <= t <= b):
            continue
        fade = tx.get("fondu", 0.0)
        al = min(ease((t - a) / fade), ease((b - t) / fade)) if fade else 1.0
        if "reste" in tx:                                       # compte à rebours : secondes restantes à « de », qui défilent
            tx = {**tx, "texte": tx.get("texte", "{}").format(restant(tx["reste"] - (t - a)))}
        if tx.get("plein_ecran"):
            layer = draw_text(np.zeros_like(out), tx["texte"], (W / 2, H / 2 - 20), tx["police"], tx["taille"], tuple(tx["couleur"]), center=True)
            out = (layer.astype(np.float32) * al).astype(np.uint8)
        else:
            layer = draw_text(out.copy(), tx["texte"], tuple(tx["pos"]), tx["police"], tx["taille"], tuple(tx["couleur"]))
            out = (out * (1 - al) + layer * al).astype(np.uint8)
    return out


# ------------------------------------------------------------------ son : voix, bruitages, ambiances, niveaux contrôlés
def load_audio(p: Path) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).astype(np.float64)


def _fade(x, a=0.0, b=0.0):
    x = x.copy()
    if a:
        k = min(len(x), int(a * SR)); x[:k] *= np.linspace(0, 1, k)
    if b:
        k = min(len(x), int(b * SR)); x[-k:] *= np.linspace(1, 0, k)
    return x


def _loop(x, d, xf=1.0):
    n, f = int(d * SR), int(xf * SR)
    out = x[: min(len(x), n)].copy()
    while len(out) < n:
        k = min(f, len(out), len(x)); r = np.linspace(0, 1, k)
        out[-k:] = out[-k:] * (1 - r) + x[:k] * r
        out = np.concatenate([out, x[k:]])
    return out[:n]


def _put(buf, sig, at, gain=1.0):
    i = max(0, int(at * SR)); j = min(len(buf), i + len(sig))
    if j > i:
        buf[i:j] += sig[: j - i] * gain


def soundtrack(bloc: Bloc, out: Path):
    sys.path.insert(0, str(LUNE.parent / "panne_internet"))
    import fx  # noqa: PLC0415
    N = int(bloc.end * SR)
    voice, bed = np.zeros(N), np.zeros(N)
    for v in bloc.data["voix"]:
        x = load_audio(bloc.dir / f"{v['id']}.wav"); x = x / (np.abs(x).max() + 1e-9) * 0.6
        _put(voice, x, bloc.vat[v["id"]])
    db = lambda g: 10 ** (g / 20)  # noqa: E731
    rng = np.random.default_rng(5)
    if "lea" in bloc.data and bloc.data["lea"].get("frappe"):                   # un clic par frappe de Léa (mêmes instants)
        for x in taps([(bloc.t(a), bloc.t(b)) for a, b in bloc.data["lea"]["frappe"]]):
            _put(bed, synth("clic", rng), x, db(-17) * rng.uniform(0.7, 1.1))
    if "lea" in bloc.data and (bloc.data["lea"].get("telephone") or {}).get("vibre"):
        _put(bed, synth("vibreur", rng), bloc.t(bloc.data["lea"]["telephone"]["vibre"]), db(-14))
    for s in bloc.data.get("son", []):
        at = bloc.t(s["a"])
        if "petit" in s:                                                          # petits sons synthétisés (moteur)
            for k in range(s.get("repete", 1)):
                _put(bed, synth(s["petit"], rng), at + k * s.get("intervalle", 0.5), db(s.get("gain", -12)))
            continue
        if "fichier" in s:
            x = load_audio(bloc.dir / s["fichier"] if not s["fichier"].startswith("/") else Path(s["fichier"]))
        else:                                                    # sons de signature synthétisés (fx.py)
            fn = getattr(fx, s["synth"])
            x = fn(s["args"][0], bloc.t(s["jusqua"]) - at) if s["synth"] == "drone" else fn(*s.get("args", []))
        if s.get("boucle"):
            x = _loop(x, bloc.t(s["jusqua"]) - at)
        if s.get("rms") is not None:
            x = x / (np.sqrt((x ** 2).mean()) + 1e-12) * db(s["rms"])
        elif s.get("normalise", True):
            x = x / (np.abs(x).max() + 1e-9)
        if s.get("assourdi_jusqua"):                              # entendu à travers un mur / une vitre
            cut = int((bloc.t(s["assourdi_jusqua"]) - at) * SR)
            k = np.ones(64) / 64; m = np.convolve(x, k, "same") * 0.6
            x = np.concatenate([m[:max(0, cut)], x[max(0, cut):]])
        x = _fade(x, s.get("fondu_entree", 0.0), s.get("fondu_sortie", 0.0))
        _put(bed, x, at, db(s.get("gain", 0.0)))
    for z in bloc.data.get("silences", []):                        # silences absolus (rien sous la voix)
        bed[int(bloc.t(z["de"]) * SR): int(bloc.t(z["a"]) * SR)] = 0
    duck = fx.duck_under_voice(bed, voice * 32768.0, SR, 1.0, margin=8.0)
    mix = voice + duck
    tmp = out.with_suffix(".brut.wav")
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(tmp)],
                   input=pcm.tobytes(), check=True)
    # niveaux : référence de travail −14 LUFS intégré, crête ≤ −1,5 dBTP : gain mesuré puis limiteur de crête (sur-échantillonné)
    L = STYLE["son"]
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(tmp), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    I0 = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
    lim = 10 ** (L["crete_dbtp"] / 20)
    for _ in range(5):                                         # le limiteur retire un peu de niveau : on recale
        g = L["lufs"] - I0
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-af",
                        f"volume={g:.2f}dB,aresample=192000,alimiter=limit={lim:.4f}:attack=2:release=60:level=false,aresample={SR}",
                        str(out)], check=True)
        r = subprocess.run(["ffmpeg", "-nostats", "-i", str(out), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
        I1 = float(re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1])
        if abs(I1 - L["lufs"]) < 0.3:
            break
        I0 += I1 - L["lufs"]                                  # trop bas → plus de gain au tour suivant
    tmp.unlink()
    report(out, voice, duck)


def report(wav, voice, bed):
    r = subprocess.run(["ffmpeg", "-nostats", "-i", str(wav), "-af", "ebur128=peak=true", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    I = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)[-1]; TP = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", r)[-1]
    on = np.abs(voice) > 0.01
    vr = 20 * np.log10(np.sqrt((voice[on] ** 2).mean()) + 1e-12); br = 20 * np.log10(np.sqrt((bed[on] ** 2).mean()) + 1e-12)
    print(f"son : {I} LUFS intégré · crête réelle {TP} dBTP · voix au-dessus du fond de {vr - br:.1f} dB pendant la parole")


# ------------------------------------------------------------------ rendu complet
_B = None


def _init(name):
    global _B
    cv2.setNumThreads(1)
    _B = Bloc(name)


def _save(i):
    Image.fromarray(frame(_B, i)).save(_B.dir / ".frames" / f"{i:05d}.png", compress_level=1)


def main(argv):
    name = argv[0]
    bloc = Bloc(name)
    tmp = bloc.dir / ".frames"; tmp.mkdir(exist_ok=True)
    n = int(bloc.end * FPS)
    print(f"{name} : {len(bloc.shots)} plans, {bloc.end:.1f} s, {n} images")
    if "--images" in argv:
        for i in map(int, argv[argv.index("--images") + 1].split(",")):
            Image.fromarray(frame(bloc, i)).save(tmp / f"{i:05d}.png", compress_level=1)
        return
    if "--planche" in argv:
        tiles = []
        for s in bloc.shots:
            i = int((s["_t0"] + (s["_t1"] - s["_t0"]) * 0.45) * FPS)
            im = Image.fromarray(frame(bloc, i)).resize((480, 270)); d = ImageDraw.Draw(im)
            d.rectangle((0, 0, 200, 26), fill=(0, 0, 0)); d.text((6, 4), f"{s['id']}  {s['_t0']:.1f}–{s['_t1']:.1f} s", fill=(255, 255, 0), font=font("InstrumentSans-Bold.ttf", 16))
            tiles.append(im)
        cols = 4; rows = (len(tiles) + cols - 1) // cols
        sheet = Image.new("RGB", (480 * cols, 270 * rows))
        for k, im in enumerate(tiles):
            sheet.paste(im, ((k % cols) * 480, (k // cols) * 270))
        sheet.save(bloc.dir / "planche.png"); print("planche :", bloc.dir / "planche.png")
        return
    wav = bloc.dir / f"son_{name}.wav"
    soundtrack(bloc, wav)
    if "--son" in argv:
        return
    todo = [i for i in range(n) if not (tmp / f"{i:05d}.png").exists()]
    from multiprocessing import Pool  # noqa: PLC0415
    with Pool(4, initializer=_init, initargs=(name,)) as pool:
        for k, _ in enumerate(pool.imap_unordered(_save, todo, chunksize=8)):
            if k % 300 == 0:
                print(f"image {k}/{len(todo)}", flush=True)
    out = bloc.dir / f"bloc{name[1:]}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(tmp / "%05d.png"), "-i", str(wav),
                    "-c:v", "libx264", "-preset", "slow", "-b:v", "14M", "-maxrate", "18M", "-bufsize", "28M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                    "-shortest", "-movflags", "+faststart", str(out)], check=True)
    print("ok", out)


if __name__ == "__main__":
    sys.path.insert(0, str(FILM))
    main(sys.argv[1:])
