"""Rendu de la vidéo « La panne mondiale d'Internet » entièrement en code.

    python render.py --work /chemin/de/travail --geo countries.geojson --voice fr_FR-siwis-medium.onnx
    python render.py ... --only 1-5 --preview      # quelques scènes, en 960x540, pour tester

Étapes :
  1. Voix : une piste par scène avec Piper (synthèse vocale locale), mise en cache.
  2. Images : chaque scène est dessinée image par image avec Pillow (motion design sombre :
     étiquette SIMULATION / HISTOIRE RÉELLE, gros chiffres, globe, cartes, interfaces),
     encodée en H.264 par ffmpeg, scènes rendues en parallèle.
  3. Son : voix + nappe d'ambiance générée (aucune musique sous droits), volume normalisé (−15 LUFS).
  4. Sorties : video.mp4, sous-titres .srt, chapitres pour la description YouTube.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import sys
import wave
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from scenes import BEATS, SCENES  # noqa: E402

FPS = 24
PAD_S = 0.45          # silence après chaque phrase
LENGTH_SCALE = 1.08   # voix un peu plus lente (~150 mots/min)

# Palette (identité propre, différente de Hindcast)
BG1, BG2 = (8, 22, 21), (17, 44, 40)
RED, MINT, PAPER = (255, 90, 54), (94, 230, 176), (232, 221, 196)
TXT, GREY, DIM = (242, 242, 238), (138, 145, 143), (60, 78, 74)
AMBER = (255, 184, 77)

# Orthographe phonétique pour la voix de synthèse française, appliquée UNIQUEMENT au texte lu.
# Le script, les sous-titres et le texte à l'écran restent inchangés. Vérifié par re-transcription (Whisper).
PRONUNCIATION = {
    "Domain Name System": "Daumeïne Neïme Sistème",
    "Cloudflare": "Claoude-flère",
    "l'application X, ChatGPT ou Spotify": "l'application Ixe, Tchatte G P T ou Spotifaille",
    "Parametrix": "Paramétrix",
    "Rogers": "Rodjeurse",
}


def spoken(text: str) -> str:
    for a, b in PRONUNCIATION.items():
        text = text.replace(a, b)
    return text


FONT_DIR = Path("/usr/share/fonts/opentype/inter")
MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
_fonts: dict = {}


def font(size: int, weight: str = "Bold", mono: bool = False) -> ImageFont.FreeTypeFont:
    key = (size, weight, mono)
    if key not in _fonts:
        path = MONO if mono else str(FONT_DIR / f"Inter-{weight}.otf")
        _fonts[key] = ImageFont.truetype(path, size)
    return _fonts[key]


def ease(x: float) -> float:
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def mix(c1, c2, a):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * a) for i in range(3))


# --------------------------------------------------------------------------- #
# Géographie
# --------------------------------------------------------------------------- #
class Geo:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        self.polys: list[tuple[str, np.ndarray]] = []
        for f in data["features"]:
            code = f["properties"]["ADM0_A3"]
            g = f["geometry"]
            rings = g["coordinates"] if g["type"] == "Polygon" else [p[0] for p in g["coordinates"]]
            if g["type"] == "Polygon":
                rings = [g["coordinates"][0]]
            for ring in rings:
                self.polys.append((code, np.array(ring, dtype=float)))
        rng = random.Random(7)
        # points de « lumières » : sommets des côtes, sous-échantillonnés
        pts = np.concatenate([r for _, r in self.polys])
        idx = rng.sample(range(len(pts)), min(1400, len(pts)))
        self.lights = pts[idx]


CABLES = [  # paires de points côtiers (lon, lat), tracées en grands cercles
    ((-74, 40.5), (-5, 43.3)), ((-74, 40.5), (-4, 50.3)), ((-80, 26), (-38, -12)), ((-38, -12), (13, -9)),
    ((-5, 36), (32, 31)), ((32, 31), (43, 12)), ((43, 12), (72, 19)), ((72, 19), (80, 6)),
    ((80, 6), (103.8, 1.3)), ((103.8, 1.3), (121, 14)), ((121, 14), (139.7, 35)), ((139.7, 35), (-122.4, 37.7)),
    ((103.8, 1.3), (115.8, -32)), ((151.2, -33.8), (174.8, -36.8)), ((151.2, -33.8), (-157.8, 21.3)),
    ((-157.8, 21.3), (-122.4, 37.7)), ((-5, 43.3), (-9, 38.7)), ((18.4, -33.9), (-9, 38.7)), ((39.7, -4), (43, 12)),
]


def great_circle(a, b, n=60):
    lon1, lat1, lon2, lat2 = map(math.radians, (*a, *b))
    p1 = np.array([math.cos(lat1) * math.cos(lon1), math.cos(lat1) * math.sin(lon1), math.sin(lat1)])
    p2 = np.array([math.cos(lat2) * math.cos(lon2), math.cos(lat2) * math.sin(lon2), math.sin(lat2)])
    om = math.acos(max(-1, min(1, float(p1 @ p2)))) or 1e-6
    out = []
    for t in np.linspace(0, 1, n):
        p = (math.sin((1 - t) * om) * p1 + math.sin(t * om) * p2) / math.sin(om)
        out.append((math.degrees(math.atan2(p[1], p[0])), math.degrees(math.asin(p[2]))))
    return np.array(out)


def ortho(lonlat: np.ndarray, lon0: float, lat0: float):
    lon, lat = np.radians(lonlat[:, 0]), np.radians(lonlat[:, 1])
    l0, p0 = math.radians(lon0), math.radians(lat0)
    cosc = math.sin(p0) * np.sin(lat) + math.cos(p0) * np.cos(lat) * np.cos(lon - l0)
    x = np.cos(lat) * np.sin(lon - l0)
    y = math.cos(p0) * np.sin(lat) - math.sin(p0) * np.cos(lat) * np.cos(lon - l0)
    vis = cosc > 0
    # points cachés : ramenés sur l'horizon pour garder des polygones fermés
    norm = np.sqrt(x * x + y * y) + 1e-9
    x = np.where(vis, x, x / norm)
    y = np.where(vis, y, y / norm)
    return x, y, vis


def inside(ring: np.ndarray, x: float, y: float) -> bool:
    """Point dans un polygone (lancer de rayon)."""
    xs, ys = ring[:, 0], ring[:, 1]
    xj, yj = np.roll(xs, 1), np.roll(ys, 1)
    cross = ((ys > y) != (yj > y)) & (x < (xj - xs) * (y - ys) / (yj - ys + 1e-12) + xs)
    return bool(cross.sum() % 2)


REGIONS = {  # lon_min, lat_min, lon_max, lat_max
    "world": (-170, -58, 190, 80), "usa": (-128, 22, -64, 52), "canada": (-145, 40, -48, 74),
    "france": (-5.5, 41.2, 9.8, 51.3), "pacific": (155, -38, 205, -5),
}


# --------------------------------------------------------------------------- #
# Éléments communs
# --------------------------------------------------------------------------- #
class Canvas:
    def __init__(self, w: int, h: int):
        self.w, self.h = w, h
        self.s = w / 1920
        y = np.linspace(0, 1, h)[:, None]
        x = np.linspace(0, 1, w)[None, :]
        r = np.sqrt((x - 0.5) ** 2 + (y - 0.45) ** 2)
        a = np.clip(1 - r * 1.3, 0, 1)[..., None]
        bg = np.array(BG1) * (1 - a) + np.array(BG2) * a
        vign = np.clip(1.15 - r * 0.9, 0.55, 1)[..., None]
        self.bg = Image.fromarray((bg * vign).astype(np.uint8), "RGB")

    def S(self, v):  # mise à l'échelle
        return int(v * self.s)


def text_c(d: ImageDraw.ImageDraw, xy, text, f, fill, anchor="mm"):
    d.text(xy, text, font=f, fill=fill, anchor=anchor)


def overlay(img: Image.Image, cv: Canvas, label: str, onscreen: str, t: float, dur: float, beat: int):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    real = label != "SIMULATION"
    col = MINT if real else RED
    # étiquette
    x, y = S(56), S(52)
    d.rounded_rectangle((x, y, x + S(30 + 13 * len(label)), y + S(40)), radius=S(6), outline=col + (230,), width=max(1, S(2)), fill=(0, 0, 0, 90))
    d.ellipse((x + S(12), y + S(14), x + S(24), y + S(26)), fill=col)
    d.text((x + S(34), y + S(20)), label, font=font(S(18), "SemiBold"), fill=TXT, anchor="lm")
    # marque de la chaîne (provisoire)
    d.text((cv.w - S(56), y + S(20)), "◆ 72 H", font=font(S(20), "Bold"), fill=GREY, anchor="rm")
    # bandeau bas : texte à l'écran
    a = ease((t - 0.25) / 0.5) * (1 - ease((t - (dur - 0.35)) / 0.35))
    if onscreen and a > 0:
        f = font(S(30), "Bold")
        tw = d.textlength(onscreen, font=f)
        bx, by = cv.w / 2, cv.h - S(92) + (1 - a) * S(14)
        d.rounded_rectangle((bx - tw / 2 - S(26), by - S(30), bx + tw / 2 + S(26), by + S(30)), radius=S(8), fill=(0, 0, 0, int(150 * a)))
        d.rectangle((bx - tw / 2 - S(26), by - S(30), bx - tw / 2 - S(20), by + S(30)), fill=col + (int(255 * a),))
        d.text((bx, by), onscreen, font=f, fill=TXT + (int(255 * a),), anchor="mm")
    return img


def hud(img: Image.Image, cv: Canvas, t: float, p: dict, kind: str):
    """Panneau de données, coordonnées et mention ILLUSTRATION, façon documentaire."""
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    rows = p.get("hud", [])
    if rows:
        a = ease((t - 0.4) / 0.5)
        x0, y0 = cv.w - S(470), cv.h - S(150) - len(rows) * S(36)
        d.rectangle((x0 - S(20), y0 - S(20), cv.w - S(40), y0 + len(rows) * S(36)), fill=(0, 0, 0, int(140 * a)))
        d.rectangle((x0 - S(20), y0 - S(20), x0 - S(16), y0 + len(rows) * S(36)), fill=MINT + (int(255 * a),))
        for i, (k, v) in enumerate(rows):
            y = y0 + i * S(36) + S(4)
            d.text((x0, y), k.upper(), font=font(S(18), "SemiBold"), fill=GREY + (int(255 * a),), anchor="lt")
            d.text((cv.w - S(60), y), v, font=font(S(20), mono=True), fill=TXT + (int(255 * a),), anchor="rt")
    if p.get("coords"):
        d.text((cv.w - S(56), cv.h - S(34)), p["coords"], font=font(S(18), mono=True), fill=GREY, anchor="rb")
    if kind in ("device", "person") or p.get("illustration"):
        d.text((S(56), cv.h - S(34)), "ILLUSTRATION", font=font(S(16), "SemiBold"), fill=GREY, anchor="lb")


def fade(img: Image.Image, t: float, dur: float) -> Image.Image:
    k = min(ease(t / 0.3), 1 - ease((t - (dur - 0.2)) / 0.2) * 0.6)
    if k >= 0.999:
        return img
    return Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, max(0.0, k))


# --------------------------------------------------------------------------- #
# Types de scènes
# --------------------------------------------------------------------------- #
def draw_title(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.8)
    big = p["big"]
    size = 150 if len(big) < 12 else 110
    text_c(d, (cv.w / 2, cv.h / 2 - cv.S(30) + (1 - a) * cv.S(30)), big, font(cv.S(size), "Black"), TXT + (int(255 * a),))
    b = ease((t - 0.6) / 0.8)
    if p.get("sub"):
        text_c(d, (cv.w / 2, cv.h / 2 + cv.S(90)), p["sub"], font(cv.S(34), "Medium"), GREY + (int(255 * b),))
    w = cv.S(420) * b
    d.rectangle((cv.w / 2 - w / 2, cv.h / 2 + cv.S(50), cv.w / 2 + w / 2, cv.h / 2 + cv.S(54)), fill=RED + (200,))


def fmt_num(v: float, decimals: int = 0) -> str:
    s = f"{v:,.{decimals}f}".replace(",", " ").replace(".", ",")
    return s


def draw_number(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    k = ease(t / 1.6)
    val = p["value"] * k
    s = fmt_num(val, p.get("decimals", 0))
    col = RED if p.get("accent") else TXT
    text_c(d, (cv.w / 2, cv.h / 2 - cv.S(40)), s, font(cv.S(190), "Black"), col)
    text_c(d, (cv.w / 2, cv.h / 2 + cv.S(90)), p["unit"], font(cv.S(44), "Bold"), TXT)
    b = ease((t - 0.9) / 0.8)
    if p.get("sub"):
        text_c(d, (cv.w / 2, cv.h / 2 + cv.S(150)), p["sub"], font(cv.S(28), "Medium"), GREY + (int(255 * b),))


def draw_chrono(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    h, m, s = map(int, p["start"].split(":"))
    total = h * 3600 + m * 60 + s + int(t * 2.2)
    txt = f"{total // 3600:02d}:{total // 60 % 60:02d}:{total % 60:02d}"
    text_c(d, (cv.w / 2, cv.h / 2 - cv.S(20)), txt, font(cv.S(200), mono=True), RED)
    text_c(d, (cv.w / 2, cv.h / 2 + cv.S(120)), p["date"], font(cv.S(38), "Bold"), TXT)


class MapLayer:
    def __init__(self, geo: Geo, cv: Canvas, p: dict):
        self.geo, self.cv, self.p = geo, cv, p
        self.region = REGIONS[p["region"]]
        lo0, la0, lo1, la1 = self.region
        margin = cv.S(120)
        sx = (cv.w - 2 * margin) / (lo1 - lo0)
        sy = (cv.h - 2 * margin - cv.S(60)) / (la1 - la0)
        self.k = min(sx, sy)
        self.ox = cv.w / 2 - (lo0 + lo1) / 2 * self.k
        self.oy = cv.h / 2 - cv.S(20) + (la0 + la1) / 2 * self.k
        self.shift = p["region"] == "pacific"
        base = Image.new("RGBA", (cv.w, cv.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(base, "RGBA")
        hl = set(p.get("highlight", []))
        for code, ring in geo.polys:
            pts = ring.copy()
            if self.shift:
                pts[:, 0] = np.where(pts[:, 0] < 0, pts[:, 0] + 360, pts[:, 0])
            xy = [self.xy(lo, la) for lo, la in pts]
            fill = (RED + (140,)) if code in hl else (34, 64, 58, 255)
            d.polygon(xy, fill=fill, outline=(70, 110, 100, 255))
        self.base = base
        rng = random.Random(3)
        self.dots = []
        if p.get("dots"):
            lands = [r for c, r in geo.polys if c == "FRA" and r[:, 0].mean() > -6]
            ring = max(lands, key=len)
            while len(self.dots) < p["dots"]:
                lo, la = rng.uniform(lo0, lo1), rng.uniform(la0, la1)
                if inside(ring, lo, la):
                    self.dots.append((lo, la, rng.random()))

    def xy(self, lo, la):
        return (self.ox + lo * self.k, self.oy - la * self.k)

    def draw(self, img, t, dur):
        cv, p = self.cv, self.p
        img.paste(self.base, (0, 0), self.base)
        d = ImageDraw.Draw(img, "RGBA")
        S = cv.S
        if p.get("lights_off"):
            k = ease(t / max(dur - 1, 1))
            for i, (lo, la) in enumerate(self.geo.lights):
                if (i / len(self.geo.lights)) < k:
                    continue
                x, y = self.xy(lo, la)
                d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=AMBER + (200,))
        if p.get("cables"):
            k = ease(t / 2.0)
            for a, b in CABLES:
                arc = great_circle(a, b)
                n = max(2, int(len(arc) * k))
                pts = [self.xy(lo, la) for lo, la in arc[:n]]
                for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
                    if abs(x2 - x1) < cv.w / 3:
                        d.line((x1, y1, x2, y2), fill=MINT + (220,), width=max(1, S(3)))
        for i, (lo, la, ph) in enumerate(self.dots):
            x, y = self.xy(lo, la)
            on = (t / max(dur - 1, 1)) > ph if p.get("relight") else (t * 1.4) > ph * 2
            col = (MINT if p.get("relight") else RED) if on else DIM
            r = S(6)
            d.ellipse((x - r, y - r, x + r, y + r), fill=col + (230,))
        for lo, la, name in p.get("points", []):
            x, y = self.xy(lo, la)
            pulse = (t * 0.8) % 1
            r = S(10 + 40 * pulse)
            d.ellipse((x - r, y - r, x + r, y + r), outline=RED + (int(255 * (1 - pulse)),), width=S(3))
            d.ellipse((x - S(9), y - S(9), x + S(9), y + S(9)), fill=RED)
            d.text((x + S(22), y - S(4)), name, font=font(S(30), "Bold"), fill=TXT, anchor="lm")
        if p.get("cable_cut") and len(p.get("points", [])) >= 2:
            (x1, y1), (x2, y2) = self.xy(*p["points"][0][:2]), self.xy(*p["points"][1][:2])
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            d.line((x1, y1, mx - S(14), my), fill=MINT + (230,), width=S(4))
            d.line((mx + S(14), my, x2, y2), fill=MINT + (230,), width=S(4))
            if t > 1.0:
                c = S(18)
                d.line((mx - c, my - c, mx + c, my + c), fill=RED, width=S(6))
                d.line((mx - c, my + c, mx + c, my - c), fill=RED, width=S(6))


class TexGlobe:
    """Globe texturé (textures Terre jour / lumières de nuit / nuages, issues des images NASA)."""

    def __init__(self, tex_dir: Path, radius: int):
        self.day = np.asarray(Image.open(tex_dir / "earth_atmos_2048.jpg").convert("RGB"), dtype=np.float32) / 255
        self.night = np.asarray(Image.open(tex_dir / "earth_lights_2048.png").convert("RGB"), dtype=np.float32) / 255
        cl = Image.open(tex_dir / "earth_clouds_1024.png").convert("RGBA").resize((2048, 1024), Image.BILINEAR)
        self.clouds = np.asarray(cl, dtype=np.float32)[..., 3] / 255  # densité des nuages = transparence
        self.R = radius
        yy, xx = np.mgrid[-radius:radius, -radius:radius].astype(np.float32) + 0.5
        x, y = xx / radius, -yy / radius
        r2 = x * x + y * y
        self.mask = r2 <= 1
        self.x, self.y = x[self.mask], y[self.mask]
        self.z = np.sqrt(np.clip(1 - self.x ** 2 - self.y ** 2, 0, 1))
        light = np.array([-0.55, 0.45, 0.70])
        light /= np.linalg.norm(light)
        self.shade = np.clip(self.x * light[0] + self.y * light[1] + self.z * light[2], 0, 1)
        self.limb = self.z ** 0.35
        rng = np.random.default_rng(5)
        self.off_rank = rng.random(self.day.shape[:2]).astype(np.float32)  # ordre d'extinction des lumières
        # halo d'atmosphère
        size = int(radius * 2.5)
        gy, gx = np.mgrid[0:size, 0:size].astype(np.float32) - size / 2
        rr = np.sqrt(gx * gx + gy * gy) / radius
        glow = np.clip(1 - (rr - 1) / 0.22, 0, 1) * (rr > 0.98)
        halo = np.zeros((size, size, 4), dtype=np.uint8)
        halo[..., 0], halo[..., 1], halo[..., 2] = 90, 170, 255
        halo[..., 3] = (glow ** 2 * 170).astype(np.uint8)
        self.halo = Image.fromarray(halo, "RGBA")

    def render(self, lon0: float, lat0: float, mode: str, off: float = 0.0, cloud_shift: float = 0.0) -> Image.Image:
        p0, l0 = math.radians(lat0), math.radians(lon0)
        x, y, z = self.x, self.y, self.z
        lat = np.arcsin(np.clip(z * math.sin(p0) + y * math.cos(p0), -1, 1))
        lon = l0 + np.arctan2(x, z * math.cos(p0) - y * math.sin(p0))
        h, w = self.day.shape[:2]
        u = ((lon / (2 * math.pi) + 0.5) % 1 * (w - 1)).astype(np.int32)
        v = ((0.5 - lat / math.pi) * (h - 1)).astype(np.int32)
        uc = ((lon / (2 * math.pi) + 0.5 + cloud_shift) % 1 * (w - 1)).astype(np.int32)
        cl = self.clouds[v, uc][:, None]
        if mode == "night":
            lum = np.clip(self.night[v, u].mean(axis=1, keepdims=True) - 0.08, 0, 1)
            lights = lum * np.array([1.0, 0.72, 0.38], dtype=np.float32)
            base = self.day[v, u].mean(axis=1, keepdims=True) * np.array([0.03, 0.05, 0.09], dtype=np.float32)
            base = base + np.clip(lights * 3.2, 0, 1) * (self.off_rank[v, u] >= off)[:, None]
            base = base * (0.35 + 0.65 * self.limb[:, None]) + cl * 0.035
        else:
            base = self.day[v, u] * (0.18 + 0.95 * self.shade[:, None])
            base = base * (1 - cl * 0.6) + cl * 0.6 * (0.2 + 0.85 * self.shade[:, None])
            base *= (0.55 + 0.45 * self.limb[:, None])
        out = np.zeros((2 * self.R, 2 * self.R, 4), dtype=np.uint8)
        rgb = (np.clip(base, 0, 1) * 255).astype(np.uint8)
        out[self.mask, :3] = rgb
        out[self.mask, 3] = 255
        return Image.fromarray(out, "RGBA")


_globes: dict = {}


def draw_texglobe(img, cv, t, dur, p, tex_dir: Path):
    S = cv.S
    R_ = S(400)
    key = (R_, str(tex_dir))
    if key not in _globes:
        _globes[key] = TexGlobe(tex_dir, R_)
    g = _globes[key]
    cx, cy = int(cv.w / 2), int(cv.h / 2 - S(10))
    lon0 = p.get("lon0", 0) + t * 4
    lat0 = p.get("lat0", 20)
    off = ease(t / max(dur - 1, 1)) if p.get("lights_off") or p.get("nodes_off") else 0.0
    sphere = g.render(lon0, lat0, p.get("mode", "day"), off, cloud_shift=t * 0.002)
    img.paste(g.halo, (cx - g.halo.width // 2, cy - g.halo.height // 2), g.halo)
    img.paste(sphere, (cx - R_, cy - R_), sphere)
    d = ImageDraw.Draw(img, "RGBA")
    if p.get("cables"):
        k = ease(t / 2.0)
        for a, b in CABLES:
            arc = great_circle(a, b, 50)
            x, y, vis = ortho(arc, lon0, lat0)
            n = max(2, int(len(arc) * k))
            for i in range(n - 1):
                if vis[i] and vis[i + 1]:
                    d.line((cx + x[i] * R_, cy - y[i] * R_, cx + x[i + 1] * R_, cy - y[i + 1] * R_),
                           fill=(RED if p.get("nodes_off") else MINT) + (230,), width=S(3))
    for lo, la, name in p.get("points", []):
        x, y, vis = ortho(np.array([[lo, la]]), lon0, lat0)
        if vis[0]:
            px, py = cx + x[0] * R_, cy - y[0] * R_
            d.ellipse((px - S(8), py - S(8), px + S(8), py + S(8)), fill=RED)
            d.text((px + S(18), py), name, font=font(S(28), "Bold"), fill=TXT, anchor="lm")


def draw_globe(img, cv, t, dur, p, geo: Geo):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    R_ = S(380)
    cx, cy = cv.w / 2, cv.h / 2 - S(20)
    lon0 = p.get("lon0", 0) + t * 6
    # halo
    for i in range(6):
        r = R_ + S(6 + i * 6)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=MINT + (40 - i * 6,), width=S(4))
    d.ellipse((cx - R_, cy - R_, cx + R_, cy + R_), fill=(10, 30, 40, 255))
    for _, ring in geo.polys:
        x, y, vis = ortho(ring, lon0, 15)
        if not vis.any():
            continue
        pts = list(zip(cx + x * R_, cy - y * R_))
        d.polygon(pts, fill=(34, 64, 58, 255), outline=(70, 110, 100, 255))
    if p.get("cables"):
        k = ease(t / 2.0)
        for a, b in CABLES:
            arc = great_circle(a, b, 50)
            x, y, vis = ortho(arc, lon0, 15)
            n = max(2, int(len(arc) * k))
            for i in range(n - 1):
                if vis[i] and vis[i + 1]:
                    d.line((cx + x[i] * R_, cy - y[i] * R_, cx + x[i + 1] * R_, cy - y[i + 1] * R_), fill=MINT + (230,), width=S(3))
    x, y, vis = ortho(geo.lights[::3], lon0, 15)
    off = p.get("nodes_off")
    k = ease(t / max(dur - 1, 1))
    for i in np.where(vis)[0]:
        if off and (i / len(vis)) < k:
            col = RED + (160,)
        else:
            col = AMBER + (210,)
        px, py = cx + x[i] * R_, cy - y[i] * R_
        d.ellipse((px - 2, py - 2, px + 2, py + 2), fill=col)


def draw_circles(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    cx, cy = cv.w / 2, cv.h / 2 - S(20)
    names = ["MAISON", "RUE", "COMMERCES", "MARC"]
    for i in range(4, 0, -1):
        k = ease((t - (4 - i) * 0.25) / 0.6)
        r = S(90 + i * 85) * k
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=RED + (int(90 + 30 * i),), width=S(3))
        if k > 0.9:
            d.text((cx + r * 0.72, cy - r * 0.72), f"{i} · {names[i - 1]}", font=font(S(24), "SemiBold"), fill=GREY, anchor="lm")
    d.ellipse((cx - S(14), cy - S(14), cx + S(14), cy + S(14)), fill=RED)
    text_c(d, (cx, cy + S(40)), "VOUS", font(S(30), "Black"), TXT)


def draw_choice(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    opts = [("01", "ATTENDRE", "Radio FM"), ("02", "PARTIR", "Pompes bloquées"), ("03", "STOCKER", "Espèces en caisse")]
    w, h, gap = S(440), S(440), S(50)
    x0 = cv.w / 2 - (3 * w + 2 * gap) / 2
    for i, (n, title, sub) in enumerate(opts):
        k = ease((t - i * 0.15) / 0.6)
        x, y = x0 + i * (w + gap), cv.h / 2 - h / 2 - S(30) + (1 - k) * S(40)
        act = p["active"] == i
        col = RED if act else (DIM if p["active"] >= 0 else GREY)
        d.rounded_rectangle((x, y, x + w, y + h), radius=S(18), fill=(0, 0, 0, 120 if act else 70), outline=col + (int(255 * k),), width=S(4 if act else 2))
        d.text((x + S(36), y + S(40)), n, font=font(S(96), "Black"), fill=col + (int(255 * k),))
        d.text((x + S(36), y + S(250)), title, font=font(S(48), "Black"), fill=(TXT if act or p["active"] < 0 else GREY) + (int(255 * k),))
        d.text((x + S(36), y + S(320)), sub, font=font(S(30), "Medium"), fill=GREY + (int(255 * k),))


def draw_bars(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    text_c(d, (cv.w / 2, S(220)), p["title"], font(S(46), "Black"), TXT)
    items = p["items"]
    bw, maxh, base = S(220), S(480), cv.h - S(230)
    gap = S(160)
    x0 = cv.w / 2 - (len(items) * bw + (len(items) - 1) * gap) / 2
    for i, (name, v, unit) in enumerate(items):
        k = ease((t - 0.3 - i * 0.35) / 1.2)
        hgt = max(S(6), maxh * (v / p["max"]) * k)
        x = x0 + i * (bw + gap)
        col = RED if i == 0 else MINT
        d.rectangle((x, base - hgt, x + bw, base), fill=col + (230,))
        lab = p["labels"][i] if p.get("labels") else f"{fmt_num(v * k)}{unit}"
        text_c(d, (x + bw / 2, base - hgt - S(40)), lab, font(S(52), "Black"), TXT)
        text_c(d, (x + bw / 2, base + S(36)), name, font(S(28), "SemiBold"), GREY)


def draw_list(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    items = p["items"]
    lh = S(78) if len(items) > 3 else S(120)
    y0 = cv.h / 2 - S(30) - (len(items) - 1) * lh / 2
    for i, it in enumerate(items):
        k = ease((t - i * 0.35) / 0.5)
        y = y0 + i * lh
        x = S(420) + (1 - k) * S(40)
        d.rectangle((x - S(30), y - S(18), x - S(22), y + S(18)), fill=MINT + (int(255 * k),))
        d.text((x, y), it, font=font(S(46 if len(items) > 3 else 52), "Bold"), fill=TXT + (int(255 * k),), anchor="lm")


# ---- interfaces et objets -------------------------------------------------- #
def screen(d, box, lines, col, S, title=None):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=S(12), fill=(4, 14, 14, 255), outline=(60, 90, 84, 255), width=S(3))
    y = y0 + S(40)
    if title:
        d.text(((x0 + x1) / 2, y), title, font=font(S(28), "Bold"), fill=GREY, anchor="mm")
        y += S(56)
    for ln in lines:
        size = 34
        while size > 14 and d.textlength(ln, font=font(S(size), "Bold")) > (x1 - x0) - S(30):
            size -= 2
        d.text(((x0 + x1) / 2, y), ln, font=font(S(size), "Bold"), fill=col, anchor="mm")
        y += S(54)


def draw_device(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    cx, cy = cv.w / 2, cv.h / 2 - S(30)
    what = p["what"]
    bad = p.get("bad")
    blink = (int(t * 2) % 2 == 0)
    stc = RED if bad else (MINT if p.get("good") else AMBER)
    k = ease(t / 0.6)
    oy = (1 - k) * S(30)
    if what in ("terminal", "ticket", "atm"):
        w, h = (S(360), S(560)) if what == "terminal" else (S(520), S(640))
        x0, y0 = cx - w / 2, cy - h / 2 + oy
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=S(36), fill=(30, 40, 40, 255), outline=(80, 100, 96, 255), width=S(4))
        title = {"terminal": "TERMINAL", "ticket": "AUTOMATE", "atm": "DISTRIBUTEUR"}[what]
        screen(d, (x0 + S(40), y0 + S(50), x0 + w - S(40), y0 + S(300)), [p.get("status", "")] if blink or not bad else [""], stc, S, title)
        if what == "terminal":
            for r in range(4):
                for c in range(3):
                    bx, by = x0 + S(60) + c * S(85), y0 + S(330) + r * S(52)
                    d.rounded_rectangle((bx, by, bx + S(70), by + S(40)), radius=S(8), fill=(50, 64, 62, 255))
        else:
            d.rectangle((x0 + S(90), y0 + S(360), x0 + w - S(90), y0 + S(380)), fill=(10, 16, 16, 255))
            d.rectangle((x0 + S(140), y0 + S(470), x0 + w - S(140), y0 + S(490)), fill=(10, 16, 16, 255))
            d.text((cx, y0 + S(430)), "CARTE", font=font(S(22), "SemiBold"), fill=GREY, anchor="mm")
        if p.get("queue"):
            for i in range(9):
                px = x0 - S(120) - i * S(95)
                if px < S(20):
                    break
                d.ellipse((px - S(26), cy + S(90), px + S(26), cy + S(142)), fill=(70, 96, 90, 255))
                d.rounded_rectangle((px - S(40), cy + S(150), px + S(40), cy + S(330)), radius=S(30), fill=(70, 96, 90, 255))
    elif what == "phone":
        w, h = S(380), S(720)
        x0, y0 = cx - w / 2, cy - h / 2 + oy
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=S(50), fill=(20, 26, 26, 255), outline=(90, 110, 106, 255), width=S(5))
        bars = p.get("bars", 0)
        for i in range(4):
            col = TXT if i < bars else DIM
            d.rectangle((x0 + S(40) + i * S(16), y0 + S(70) - i * S(8), x0 + S(50) + i * S(16), y0 + S(78)), fill=col)
        d.text((x0 + w - S(40), y0 + S(70)), "08:31", font=font(S(24), "SemiBold"), fill=TXT, anchor="rm")
        y = y0 + S(170)
        for ln in p.get("lines", []):
            d.rounded_rectangle((x0 + S(30), y, x0 + w - S(30), y + S(90)), radius=S(16), fill=(40, 52, 52, 255))
            d.text((x0 + S(56), y + S(45)), ln, font=font(S(28), "SemiBold"), fill=TXT, anchor="lm")
            y += S(110)
        d.text((cx, y0 + h - S(110)), p.get("status", ""), font=font(S(30), "Black"), fill=RED if blink else (RED[0], RED[1], RED[2], 120), anchor="mm")
        # roue de chargement
        a0 = (t * 360) % 360
        d.arc((cx - S(40), y + S(20), cx + S(40), y + S(100)), a0, a0 + 270, fill=GREY, width=S(6))
    elif what == "computer":
        w, h = S(900), S(520)
        x0, y0 = cx - w / 2, cy - h / 2 + oy
        d.rounded_rectangle((x0, y0, x0 + w, y0 + h), radius=S(18), fill=(20, 26, 26, 255), outline=(90, 110, 106, 255), width=S(5))
        d.rectangle((cx - S(30), y0 + h, cx + S(30), y0 + h + S(80)), fill=(60, 74, 72, 255))
        d.rectangle((cx - S(180), y0 + h + S(80), cx + S(180), y0 + h + S(96)), fill=(60, 74, 72, 255))
        hdr = "DOSSIER PATIENT" if p.get("hospital") else "NAVIGATEUR"
        d.rectangle((x0 + S(20), y0 + S(20), x0 + w - S(20), y0 + S(70)), fill=(40, 52, 52, 255))
        d.text((x0 + S(44), y0 + S(45)), hdr, font=font(S(24), "SemiBold"), fill=GREY, anchor="lm")
        text_c(d, (cx, cy + oy - S(20)), "⚠", font(S(110), "Black"), RED)
        text_c(d, (cx, cy + oy + S(90)), p.get("status", ""), font(S(38), "Black"), TXT)
    elif what == "board":
        rows = [("DL 1203", "ATLANTA", "ANNULÉ"), ("DL 0457", "NEW YORK", "ANNULÉ"), ("DL 2210", "LOS ANGELES", "ANNULÉ"),
                ("DL 0981", "BOSTON", "ANNULÉ"), ("DL 1777", "SEATTLE", "ANNULÉ"), ("DL 0308", "MIAMI", "ANNULÉ")]
        x0, y0 = cx - S(620), cy - S(260) + oy
        d.rectangle((x0, y0, x0 + S(1240), y0 + S(520)), fill=(10, 12, 12, 255), outline=(60, 74, 72, 255), width=S(4))
        d.text((x0 + S(40), y0 + S(40)), "DÉPARTS", font=font(S(34), "Black"), fill=AMBER, anchor="lm")
        for i, (f, c, s) in enumerate(rows):
            k2 = ease((t - i * 0.25) / 0.4)
            y = y0 + S(110) + i * S(66)
            d.text((x0 + S(40), y), f, font=font(S(34), mono=True), fill=AMBER, anchor="lm")
            d.text((x0 + S(300), y), c, font=font(S(34), mono=True), fill=AMBER, anchor="lm")
            d.text((x0 + S(980), y), s if k2 > 0.5 else "À L'HEURE", font=font(S(34), mono=True), fill=RED if k2 > 0.5 else MINT, anchor="lm")
    elif what == "servers":
        mode = p.get("mode", "fail")
        for r in range(5):
            x0 = cx - S(560) + r * S(240)
            y0 = cy - S(300) + oy
            d.rectangle((x0, y0, x0 + S(180), y0 + S(600)), fill=(24, 32, 32, 255), outline=(70, 90, 86, 255), width=S(3))
            for u in range(12):
                y = y0 + S(24) + u * S(48)
                d.rectangle((x0 + S(14), y, x0 + S(166), y + S(36)), fill=(14, 20, 20, 255))
                prog = (t / max(dur - 0.5, 1))
                seed = (r * 12 + u) / 60
                if mode == "fail":
                    col = RED if seed < prog * 1.5 else MINT
                elif mode == "ok":
                    col = MINT if seed < prog * 1.5 else RED
                else:
                    col = AMBER if (int(t * 3) + r + u) % 3 else MINT
                d.ellipse((x0 + S(140), y + S(12), x0 + S(152), y + S(24)), fill=col)
        if p.get("clock"):
            text_c(d, (cx, cy + S(350) + oy), p["clock"], font(S(64), mono=True), RED)
        if p.get("label"):
            text_c(d, (cx, cy - S(350) + oy), p["label"], font(S(36), "Black"), GREY)
    elif what == "notebook":
        x0, y0 = cx - S(380), cy - S(300) + oy
        d.rounded_rectangle((x0, y0, x0 + S(760), y0 + S(600)), radius=S(10), fill=PAPER + (255,))
        for i in range(10):
            y = y0 + S(110) + i * S(48)
            d.line((x0 + S(30), y, x0 + S(730), y), fill=(180, 170, 150, 255), width=S(2))
        d.text((x0 + S(40), y0 + S(56)), p.get("title", ""), font=font(S(38), "Black"), fill=(140, 40, 30, 255), anchor="lm")
        for i, ln in enumerate(p.get("lines", [])):
            k2 = ease((t - 0.4 - i * 0.5) / 0.4)
            if k2 > 0:
                d.text((x0 + S(50), y0 + S(150) + i * S(96)), ln, font=font(S(40), "Medium"), fill=(30, 40, 70, int(255 * k2)), anchor="lm")
    elif what == "cash":
        notes = p.get("notes", [])
        for i, n in enumerate(notes):
            k2 = ease((t - i * 0.3) / 0.6)
            x0 = cx - S(300) + i * S(90) - (len(notes) - 1) * S(45)
            y0 = cy - S(160) + i * S(50) + (1 - k2) * S(60)
            d.rounded_rectangle((x0, y0, x0 + S(600), y0 + S(300)), radius=S(16), fill=(180, 200, 170, int(255 * k2)), outline=(90, 110, 90, int(255 * k2)), width=S(4))
            d.text((x0 + S(300), y0 + S(150)), n, font=font(S(110), "Black"), fill=(40, 70, 50, int(255 * k2)), anchor="mm")
        if p.get("notebook"):
            x0, y0 = cx + S(320), cy - S(100)
            d.rounded_rectangle((x0, y0, x0 + S(300), y0 + S(380)), radius=S(10), fill=PAPER + (255,))
            for i, ln in enumerate(["Maman", "Crèche", "Médecin", "Voisin", "Mairie"]):
                d.text((x0 + S(30), y0 + S(50) + i * S(64)), ln + " ……", font=font(S(32), "Medium"), fill=(30, 40, 70, 255), anchor="lm")
    elif what == "warehouse":
        d.rectangle((cx - S(700), cy - S(260) + oy, cx + S(700), cy + S(200) + oy), outline=(70, 90, 86, 255), width=S(4), fill=(16, 26, 26, 255))
        for i in range(4):
            x0 = cx - S(620) + i * S(330)
            y0 = cy + S(40) + oy
            d.rectangle((x0, y0, x0 + S(220), y0 + S(140)), fill=(60, 80, 76, 255))
            d.rectangle((x0 + S(220), y0 + S(50), x0 + S(290), y0 + S(140)), fill=(80, 100, 96, 255))
            for wx in (x0 + S(40), x0 + S(240)):
                d.ellipse((wx - S(22), y0 + S(130), wx + S(22), y0 + S(174)), fill=(20, 24, 24, 255))
            d.text((x0 + S(110), y0 - S(30)), "EN ATTENTE", font=font(S(22), "Bold"), fill=RED if blink else GREY, anchor="mm")
        for r in range(3):
            for c in range(10):
                x0, y0 = cx - S(640) + c * S(128), cy - S(230) + r * S(80) + oy
                d.rectangle((x0, y0, x0 + S(100), y0 + S(60)), fill=(120, 96, 64, 255))
    elif what == "shelves":
        for r in range(4):
            y = cy - S(280) + r * S(160) + oy
            d.rectangle((cx - S(640), y + S(120), cx + S(640), y + S(134)), fill=(90, 110, 106, 255))
            for c in range(16):
                gone = (c * 7 + r * 3) % 16 / 16 < ease(t / max(dur - 0.5, 1)) * 1.1
                if not gone:
                    x = cx - S(620) + c * S(78)
                    d.rectangle((x, y + S(40), x + S(60), y + S(120)), fill=(MINT if (c + r) % 3 else AMBER) + (180,))
    elif what == "radio":
        x0, y0 = cx - S(460), cy - S(220) + oy
        d.rounded_rectangle((x0, y0, x0 + S(920), y0 + S(440)), radius=S(40), fill=(60, 50, 40, 255), outline=(110, 96, 80, 255), width=S(5))
        d.rounded_rectangle((x0 + S(60), y0 + S(60), x0 + S(860), y0 + S(170)), radius=S(10), fill=PAPER + (255,))
        for i, fq in enumerate(range(88, 109, 4)):
            xx = x0 + S(100) + i * S(140)
            d.text((xx, y0 + S(140)), str(fq), font=font(S(26), "SemiBold"), fill=(60, 50, 40, 255), anchor="mm")
            d.line((xx, y0 + S(80), xx, y0 + S(110)), fill=(60, 50, 40, 255), width=S(3))
        nx = x0 + S(100) + (0.5 + 0.05 * math.sin(t)) * S(700)
        d.line((nx, y0 + S(70), nx, y0 + S(165)), fill=RED, width=S(5))
        for i in range(7):
            for j in range(4):
                d.ellipse((x0 + S(80) + i * S(50), y0 + S(220) + j * S(50), x0 + S(110) + i * S(50), y0 + S(250) + j * S(50)), fill=(40, 32, 26, 255))
        for k2, xx in enumerate((x0 + S(640), x0 + S(800))):
            d.ellipse((xx - S(60), y0 + S(250), xx + S(60), y0 + S(370)), fill=(40, 32, 26, 255), outline=(110, 96, 80, 255), width=S(4))
        # ondes
        for i in range(3):
            r = S(60 + ((t * 80 + i * 60) % 180))
            d.arc((cx - r, y0 - S(40) - r, cx + r, y0 - S(40) + r), 200, 340, fill=MINT + (int(200 * (1 - (r - S(60)) / S(180))),), width=S(4))


def draw_person(img, cv, t, dur, p):
    d = ImageDraw.Draw(img, "RGBA")
    S = cv.S
    k = ease(t / 0.6)
    cx, cy = cv.w / 2 - S(120), cv.h / 2 + S(10) + (1 - k) * S(30)
    body = (120, 150, 142, 255)
    d.ellipse((cx - S(60), cy - S(330), cx + S(60), cy - S(210)), fill=body)
    d.rounded_rectangle((cx - S(110), cy - S(190), cx + S(110), cy + S(200)), radius=S(80), fill=body)
    if p.get("child"):
        d.ellipse((cx + S(60), cy - S(150), cx + S(130), cy - S(80)), fill=(170, 196, 188, 255))
        d.rounded_rectangle((cx + S(50), cy - S(80), cx + S(150), cy + S(40)), radius=S(40), fill=(170, 196, 188, 255))
    if p.get("neighbor"):
        nx = cx - S(330)
        d.ellipse((nx - S(55), cy - S(310), nx + S(55), cy - S(200)), fill=(96, 116, 110, 255))
        d.rounded_rectangle((nx - S(100), cy - S(180), nx + S(100), cy + S(200)), radius=S(70), fill=(96, 116, 110, 255))
        d.text((nx, cy + S(250)), "VOISIN", font=font(S(26), "Bold"), fill=GREY, anchor="mm")
    d.text((cx, cy + S(250)), "MARC", font=font(S(26), "Bold"), fill=GREY, anchor="mm")
    if p.get("radio"):
        rx, ry = cx + S(330), cy + S(60)
        d.rounded_rectangle((rx - S(110), ry - S(70), rx + S(110), ry + S(70)), radius=S(20), fill=(60, 50, 40, 255))
        d.ellipse((rx + S(20), ry - S(40), rx + S(90), ry + S(30)), fill=(40, 32, 26, 255))
        d.text((rx, ry - S(110)), "FM", font=font(S(30), "Black"), fill=MINT, anchor="mm")
    # panneau d'état
    px = cv.w / 2 + S(330)
    col = RED if p.get("bad") else (MINT if p.get("good") else AMBER)
    if p.get("clock"):
        text_c(d, (px + S(160), cv.h / 2 - S(120)), p["clock"], font(S(120), mono=True), TXT)
    if p.get("status"):
        f = font(S(40), "Black")
        tw = d.textlength(p["status"], font=f)
        y = cv.h / 2 + (S(30) if p.get("clock") else -S(40))
        d.rounded_rectangle((px, y - S(36), px + tw + S(60), y + S(36)), radius=S(10), outline=col, width=S(4), fill=(0, 0, 0, 100))
        d.text((px + S(30), y), p["status"], font=f, fill=col, anchor="lm")


# --------------------------------------------------------------------------- #
# Rendu
# --------------------------------------------------------------------------- #
def tts(text: str, out: Path, voice: Path):
    """Piper : synthèse locale gratuite."""
    if out.exists():
        return
    subprocess.run([sys.executable, "-m", "piper", "-m", str(voice), "--length-scale", str(LENGTH_SCALE), "-f", str(out)],
                   input=spoken(text).encode("utf-8"), check=True, capture_output=True)


MINIMAX_URL = "https://api.minimax.io/v1/t2a_v2"


def tts_minimax(text: str, out: Path, voice_id: str, model: str, speed: float, emotion: str | None):
    """MiniMax (API payante, clé dans la variable d'environnement MINIMAX_API_KEY).

    Pas de réécriture phonétique : le modèle est multilingue et lit les noms anglais.
    """
    if out.exists():
        return
    import os  # noqa: PLC0415
    import requests  # noqa: PLC0415
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        sys.exit("Erreur : définis la variable d'environnement MINIMAX_API_KEY.")
    voice = {"voice_id": voice_id, "speed": speed, "vol": 1.0, "pitch": 0}
    if emotion:
        voice["emotion"] = emotion
    body = {
        "model": model, "text": text, "stream": False, "language_boost": "French",
        "voice_setting": voice,
        "audio_setting": {"sample_rate": 32000, "format": "wav", "channel": 1},
    }
    r = requests.post(MINIMAX_URL, json=body, timeout=120,
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    r.raise_for_status()
    data = r.json()
    status = data.get("base_resp", {})
    if status.get("status_code", 0) != 0 or not data.get("data", {}).get("audio"):
        sys.exit(f"Erreur MiniMax : {status.get('status_code')} {status.get('status_msg')}")
    raw = bytes.fromhex(data["data"]["audio"])
    # normalise en WAV mono 16 bits via ffmpeg (quel que soit le conteneur renvoyé)
    tmp = out.with_suffix(".raw")
    tmp.write_bytes(raw)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-ac", "1", "-ar", "32000", "-sample_fmt", "s16", str(out)], check=True)
    tmp.unlink()


def scene_key(scene) -> str:
    import hashlib  # noqa: PLC0415
    code = Path(__file__).read_bytes()  # le cache se périme dès que le code de rendu change
    return hashlib.sha1(repr(scene).encode() + code).hexdigest()[:8]


def wav_duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def render_scene(args):
    i, scene, frames, w, h, geo_path, out, tex_dir = args
    beat, label, voice, onscreen, kind, p = scene
    cv = Canvas(w, h)
    geo = Geo(Path(geo_path)) if kind in ("map", "globe") else None
    layer = MapLayer(geo, cv, p) if kind == "map" else None
    dur = frames / FPS
    proc = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}", "-r", str(FPS), "-i", "-",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
        stdin=subprocess.PIPE)
    for f in range(frames):
        t = f / FPS
        img = cv.bg.copy()
        if kind == "title":
            draw_title(img, cv, t, dur, p)
        elif kind == "number":
            draw_number(img, cv, t, dur, p)
        elif kind == "chrono":
            draw_chrono(img, cv, t, dur, p)
        elif kind == "map":
            layer.draw(img, t, dur)
        elif kind == "globe":
            if tex_dir and Path(tex_dir).exists():
                draw_texglobe(img, cv, t, dur, p, Path(tex_dir))
            else:
                draw_globe(img, cv, t, dur, p, geo)
        elif kind == "circles":
            draw_circles(img, cv, t, dur, p)
        elif kind == "choice":
            draw_choice(img, cv, t, dur, p)
        elif kind == "bars":
            draw_bars(img, cv, t, dur, p)
        elif kind == "list":
            draw_list(img, cv, t, dur, p)
        elif kind == "device":
            draw_device(img, cv, t, dur, p)
        elif kind == "person":
            draw_person(img, cv, t, dur, p)
        # léger mouvement de caméra (zoom lent)
        z = 1 + 0.035 * (t / max(dur, 1))
        if z > 1.001:
            W2, H2 = int(w / z), int(h / z)
            img = img.crop(((w - W2) // 2, (h - H2) // 2, (w - W2) // 2 + W2, (h - H2) // 2 + H2)).resize((w, h), Image.BILINEAR)
        hud(img, cv, t, p, kind)
        overlay(img, cv, label, onscreen, t, dur, beat)
        img = fade(img, t, dur)
        proc.stdin.write(img.tobytes())
    proc.stdin.close()
    proc.wait()
    return i


def ambient(path: Path, seconds: float):
    """Nappe d'ambiance générée : accords graves + souffle filtré (aucun droit d'auteur)."""
    sr = 44100
    n = int(seconds * sr)
    t = np.arange(n) / sr
    sig = np.zeros(n)
    for f, a in ((55, 0.5), (82.4, 0.35), (110, 0.25), (164.8, 0.12)):
        sig += a * np.sin(2 * np.pi * f * t + 0.3 * np.sin(2 * np.pi * 0.05 * t))
    sig *= 0.6 + 0.4 * np.sin(2 * np.pi * t / 23) ** 2
    rng = np.random.default_rng(1)
    noise = np.cumsum(rng.normal(0, 1, n))
    noise -= np.convolve(noise, np.ones(4410) / 4410, mode="same")
    sig += 0.02 * noise / (np.abs(noise).max() + 1e-9)
    sig /= np.abs(sig).max()
    fade_n = sr * 3
    sig[:fade_n] *= np.linspace(0, 1, fade_n)
    sig[-fade_n:] *= np.linspace(1, 0, fade_n)
    data = (sig * 0.5 * 32767).astype(np.int16)
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(data.tobytes())


def fmt_ts(s: float, srt=False) -> str:
    h, m = int(s // 3600), int(s // 60 % 60)
    sec = s % 60
    if srt:
        return f"{h:02d}:{m:02d}:{int(sec):02d},{int((sec % 1) * 1000):03d}"
    return f"{m:02d}:{int(sec):02d}"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    ap.add_argument("--geo", type=Path, required=True)
    ap.add_argument("--voice", type=Path, help="modèle Piper .onnx (si --tts piper)")
    ap.add_argument("--tts", choices=["piper", "minimax"], default="piper")
    ap.add_argument("--minimax-voice", default="French_MaleNarrator",
                    help="ex. French_MaleNarrator, French_Male_Speech_New, French_FemaleAnchor, French_MovieLeadFemale")
    ap.add_argument("--minimax-model", default="speech-2.8-hd")
    ap.add_argument("--minimax-speed", type=float, default=1.0)
    ap.add_argument("--minimax-emotion", help="ex. calm, fearful (facultatif)")
    ap.add_argument("--only", help="ex. 1-5")
    ap.add_argument("--textures", type=Path, help="dossier des textures Terre (globe réaliste)")
    ap.add_argument("--preview", action="store_true", help="960x540 pour tester vite")
    ap.add_argument("--jobs", type=int, default=4)
    a = ap.parse_args(argv)

    w, h = (960, 540) if a.preview else (1920, 1080)
    work = a.work
    tts_dir = work / ("tts" if a.tts == "piper" else f"tts_minimax_{a.minimax_voice}_{a.minimax_speed}")
    tts_dir.mkdir(parents=True, exist_ok=True)
    (work / "seg").mkdir(exist_ok=True)
    idx = list(range(len(SCENES)))
    if a.only:
        lo, hi = map(int, a.only.split("-"))
        idx = [i for i in idx if lo - 1 <= i <= hi - 1]

    # 1. Voix
    frames = {}
    for i in idx:
        wav = tts_dir / f"{i:02d}.wav"
        if a.tts == "minimax":
            tts_minimax(SCENES[i][2], wav, a.minimax_voice, a.minimax_model, a.minimax_speed, a.minimax_emotion)
        else:
            tts(SCENES[i][2], wav, a.voice)
        frames[i] = int(math.ceil((wav_duration(wav) + PAD_S) * FPS))
    print(f"Voix prêtes : {len(idx)} scènes, {sum(frames.values()) / FPS / 60:.2f} min")

    # 2. Images
    suffix = "_p" if a.preview else ""
    seg = {i: work / "seg" / f"{i:02d}_{frames[i]}_{scene_key(SCENES[i])}{suffix}.mp4" for i in idx}
    jobs = [(i, SCENES[i], frames[i], w, h, str(a.geo), seg[i], str(a.textures) if a.textures else None)
            for i in idx if not seg[i].exists()]
    print(f"  {len(idx) - len(jobs)} scène(s) déjà rendue(s), {len(jobs)} à rendre")
    with ProcessPoolExecutor(a.jobs) as ex:
        for done in ex.map(render_scene, jobs):
            print(f"  scène {done + 1}/{len(SCENES)} rendue", flush=True)

    # 3. Son : voix calée sur les images + ambiance
    voice_track = work / f"voice{suffix}.wav"
    sr = 22050
    chunks = []
    for i in idx:
        with wave.open(str(tts_dir / f"{i:02d}.wav")) as wv:
            sr = wv.getframerate()
            data = np.frombuffer(wv.readframes(wv.getnframes()), dtype=np.int16)
        target = int(frames[i] / FPS * sr)
        lead = int(0.15 * sr)
        buf = np.zeros(target, dtype=np.int16)
        buf[lead:lead + min(len(data), target - lead)] = data[: target - lead]
        chunks.append(buf)
    allv = np.concatenate(chunks)
    with wave.open(str(voice_track), "w") as wv:
        wv.setnchannels(1)
        wv.setsampwidth(2)
        wv.setframerate(sr)
        wv.writeframes(allv.tobytes())
    total_s = len(allv) / sr
    amb = work / "ambient.wav"
    ambient(amb, total_s)

    concat = work / f"concat{suffix}.txt"
    concat.write_text("".join(f"file '{seg[i]}'\n" for i in idx))
    out = work / f"video{suffix}.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-i", str(voice_track), "-i", str(amb),
        "-filter_complex",
        "[1:a]aresample=48000,highpass=f=70,acompressor=threshold=-18dB:ratio=3:attack=5:release=120[v];"
        "[2:a]aresample=48000,volume=0.10[m];"
        "[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-15:TP=-1.5:LRA=11[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)], check=True)

    # 4. Sous-titres et chapitres
    srt, chapters, t0, seen = [], [], 0.0, set()
    for n, i in enumerate(idx, 1):
        dur = frames[i] / FPS
        srt.append(f"{n}\n{fmt_ts(t0 + 0.15, True)} --> {fmt_ts(t0 + dur - 0.2, True)}\n{SCENES[i][2]}\n")
        if SCENES[i][0] not in seen:
            seen.add(SCENES[i][0])
            chapters.append(f"{fmt_ts(t0)} - {BEATS[SCENES[i][0]]}")
        t0 += dur
    (work / f"sous-titres{suffix}.srt").write_text("\n".join(srt), encoding="utf-8")
    (work / f"chapitres{suffix}.txt").write_text("\n".join(chapters) + "\n", encoding="utf-8")
    print(f"Terminé : {out} ({t0 / 60:.2f} min)")


if __name__ == "__main__":
    main()
