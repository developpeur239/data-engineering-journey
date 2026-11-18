"""Bannière (2560x1440) et photo de profil (800x800) de la chaîne, en pleine résolution.

Globe calculé à partir des textures Terre de three.js (jour, lumières de nuit, nuages), lignes de réseau et texte
vectoriels, rendus avec suréchantillonnage. Aucun service d'images.

    python channel_art.py --textures <dossier> --fonts <dossier> --out <dossier>
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

NAVY = (11, 18, 32)
CYAN = (63, 208, 255)
AMBER = (255, 176, 32)

CITIES = {  # lat, lon
    "Paris": (48.86, 2.35), "Londres": (51.5, -0.12), "Madrid": (40.4, -3.7), "Rome": (41.9, 12.5),
    "Berlin": (52.5, 13.4), "Casablanca": (33.6, -7.6), "Alger": (36.75, 3.06), "Dakar": (14.7, -17.45),
    "Abidjan": (5.36, -4.0), "Lagos": (6.5, 3.4), "Douala": (4.05, 9.7), "Kinshasa": (-4.3, 15.3),
    "Le Caire": (30.0, 31.2), "Istanbul": (41.0, 29.0), "Nairobi": (-1.3, 36.8), "Moscou": (55.75, 37.6),
    "New York": (40.7, -74.0), "Montréal": (45.5, -73.6),
}
LINKS = [
    ("Paris", "Londres"), ("Paris", "Madrid"), ("Paris", "Berlin"), ("Paris", "Alger"), ("Paris", "Dakar"),
    ("Paris", "Abidjan"), ("Paris", "Douala"), ("Paris", "Montréal"), ("Londres", "New York"),
    ("Madrid", "Casablanca"), ("Rome", "Le Caire"), ("Berlin", "Moscou"), ("Istanbul", "Moscou"),
    ("Abidjan", "Lagos"), ("Lagos", "Douala"), ("Douala", "Kinshasa"), ("Le Caire", "Nairobi"),
    ("Dakar", "Abidjan"), ("Rome", "Istanbul"), ("Alger", "Lagos"),
]
BROKEN = {("Paris", "Dakar"), ("Le Caire", "Nairobi"), ("Madrid", "Casablanca"), ("Lagos", "Douala")}


def bilinear(tex: np.ndarray, u: np.ndarray, v: np.ndarray) -> np.ndarray:
    h, w = tex.shape[:2]
    x, y = u * (w - 1), np.clip(v * (h - 1), 0, h - 1.001)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    x0 %= w
    x1 = (x0 + 1) % w
    t = tex if tex.ndim == 3 else tex[..., None]
    a = t[y0, x0] * (1 - fx) + t[y0, x1] * fx
    b = t[y0 + 1, x0] * (1 - fx) + t[y0 + 1, x1] * fx
    out = a * (1 - fy) + b * fy
    return out if tex.ndim == 3 else out[..., 0]


class Globe:
    def __init__(self, tex: Path):
        self.day = np.asarray(Image.open(tex / "earth_atmos_2048.jpg").convert("RGB"), np.float32) / 255
        self.night = np.asarray(Image.open(tex / "earth_lights_2048.png").convert("RGB"), np.float32) / 255
        cl = Image.open(tex / "earth_clouds_1024.png").convert("RGBA").resize((2048, 1024), Image.BICUBIC)
        self.clouds = np.asarray(cl, np.float32)[..., 3] / 255

    def basis(self, lon0: float, lat0: float):
        p0, l0 = math.radians(lat0), math.radians(lon0)
        return p0, l0

    def project(self, lat: float, lon: float, lon0: float, lat0: float):
        """Coordonnées (x, y, z) sur le disque unité (z > 0 = face visible)."""
        p, l = math.radians(lat), math.radians(lon)
        p0, l0 = math.radians(lat0), math.radians(lon0)
        x = math.cos(p) * math.sin(l - l0)
        y = math.cos(p0) * math.sin(p) - math.sin(p0) * math.cos(p) * math.cos(l - l0)
        z = math.sin(p0) * math.sin(p) + math.cos(p0) * math.cos(p) * math.cos(l - l0)
        return x, y, z

    def render(self, R: int, lon0: float, lat0: float, light, night_gain=3.0) -> Image.Image:
        yy, xx = np.mgrid[-R:R, -R:R].astype(np.float32) + 0.5
        x, y = xx / R, -yy / R
        r2 = x * x + y * y
        mask = r2 <= 1
        x, y = x[mask], y[mask]
        z = np.sqrt(np.clip(1 - x * x - y * y, 0, 1))
        p0, l0 = math.radians(lat0), math.radians(lon0)
        lat = np.arcsin(np.clip(z * math.sin(p0) + y * math.cos(p0), -1, 1))
        lon = l0 + np.arctan2(x, z * math.cos(p0) - y * math.sin(p0))
        u = (lon / (2 * math.pi) + 0.5) % 1
        v = 0.5 - lat / math.pi
        day = bilinear(self.day, u, v)
        nig = bilinear(self.night, u, v)
        cl = bilinear(self.clouds, u, v)[:, None]
        L = np.array(light, np.float32)
        L /= np.linalg.norm(L)
        sun = x * L[0] + y * L[1] + z * L[2]
        lit = np.clip(sun * 1.1 + 0.08, 0, 1)[:, None]
        dark = np.clip(1 - (sun + 0.12) / 0.3, 0, 1)[:, None]  # terminateur doux
        limb = (z ** 0.4)[:, None]
        dayc = day * (1 - cl * 0.55) + cl * 0.55
        dayc = dayc * lit
        lights = np.clip(nig.mean(axis=1, keepdims=True) - 0.06, 0, 1) * np.array([1.0, 0.74, 0.40], np.float32)
        nightc = day.mean(axis=1, keepdims=True) * np.array([0.035, 0.06, 0.11], np.float32)
        nightc = nightc + np.clip(lights * night_gain, 0, 1.2) * (1 - cl * 0.5) + cl * 0.03
        col = dayc * (1 - dark) + nightc * dark
        col = col * (0.45 + 0.55 * limb)
        # liseré d'atmosphère sur le bord
        rim = np.clip((np.sqrt(x * x + y * y) - 0.9) / 0.1, 0, 1)[:, None] ** 2
        col = col + rim * np.array([0.25, 0.55, 1.0], np.float32) * (0.35 + 0.65 * np.clip(sun + 0.4, 0, 1)[:, None])
        out = np.zeros((2 * R, 2 * R, 4), np.uint8)
        out[mask, :3] = (np.clip(col, 0, 1) * 255).astype(np.uint8)
        out[mask, 3] = 255
        img = Image.fromarray(out, "RGBA")
        # bord antialiasé
        m = Image.new("L", (8 * R, 8 * R), 0)
        ImageDraw.Draw(m).ellipse((0, 0, 8 * R - 1, 8 * R - 1), fill=255)
        img.putalpha(m.resize((2 * R, 2 * R), Image.LANCZOS))
        return img


def halo(R: int, color=(90, 170, 255), width=0.25, alpha=200) -> Image.Image:
    size = int(R * (2 + 2 * width + 0.1))
    gy, gx = np.mgrid[0:size, 0:size].astype(np.float32) - size / 2
    rr = np.sqrt(gx * gx + gy * gy) / R
    g = np.clip(1 - (rr - 1) / width, 0, 1) * (rr > 0.985)
    a = np.zeros((size, size, 4), np.uint8)
    a[..., 0], a[..., 1], a[..., 2] = color
    a[..., 3] = (g ** 2.2 * alpha).astype(np.uint8)
    return Image.fromarray(a, "RGBA")


def stars(w: int, h: int, n: int, seed=3) -> Image.Image:
    rng = np.random.default_rng(seed)
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rng.random() * w, rng.random() * h
        b = rng.random() ** 3
        r = 0.6 + 1.4 * b
        c = int(120 + 135 * b)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c, min(255, c + 20), int(90 + 165 * b)))
    return img


def glow_layer(size, draw_fn, blur: float, ss: int = 2) -> Image.Image:
    """Trait net + halo lumineux, dessinés en suréchantillonnage."""
    W, H = size
    big = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    draw_fn(ImageDraw.Draw(big), ss)
    sharp = big.resize((W, H), Image.LANCZOS)
    soft = sharp.filter(ImageFilter.GaussianBlur(blur))
    soft2 = sharp.filter(ImageFilter.GaussianBlur(blur * 3))
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for layer in (soft2, soft, soft, sharp):
        out = Image.alpha_composite(out, layer)
    return out


def arc_points(g: Globe, a, b, lon0, lat0, n=80, lift=0.10):
    """Grand cercle entre deux villes, légèrement soulevé au-dessus de la surface."""
    (la1, lo1), (la2, lo2) = a, b
    def vec(la, lo):
        p, l = math.radians(la), math.radians(lo)
        return np.array([math.cos(p) * math.cos(l), math.cos(p) * math.sin(l), math.sin(p)])
    v1, v2 = vec(la1, lo1), vec(la2, lo2)
    om = math.acos(np.clip(v1 @ v2, -1, 1))
    pts = []
    for i in range(n + 1):
        t = i / n
        v = (math.sin((1 - t) * om) * v1 + math.sin(t * om) * v2) / math.sin(om)
        h = 1 + lift * om / math.pi * 2 * math.sin(math.pi * t)
        lat = math.degrees(math.asin(v[2]))
        lon = math.degrees(math.atan2(v[1], v[0]))
        x, y, z = g.project(lat, lon, lon0, lat0)
        pts.append((x * h, y * h, z))
    return pts


def draw_network(d: ImageDraw.ImageDraw, g: Globe, cx, cy, R, lon0, lat0, ss, width=2.2):
    for a, b in LINKS:
        pts = arc_points(g, CITIES[a], CITIES[b], lon0, lat0)
        broken = (a, b) in BROKEN
        col = AMBER if broken else CYAN
        seg = []
        for k, (x, y, z) in enumerate(pts):
            visible = z > -0.02 or (x * x + y * y) > 1.0
            if broken and 0.42 < k / len(pts) < 0.58:
                visible = False  # liaison coupée
            if visible:
                seg.append(((cx + x * R) * ss, (cy - y * R) * ss))
            elif seg:
                if len(seg) > 1:
                    d.line(seg, fill=col + (235,), width=int(width * ss), joint="curve")
                seg = []
        if len(seg) > 1:
            d.line(seg, fill=col + (235,), width=int(width * ss), joint="curve")
    for name, (la, lo) in CITIES.items():
        x, y, z = g.project(la, lo, lon0, lat0)
        if z > 0.05:
            px, py, r = (cx + x * R) * ss, (cy - y * R) * ss, 3.2 * ss
            d.ellipse((px - r, py - r, px + r, py + r), fill=(255, 236, 200, 255))


def banner(g: Globe, fonts: Path, out: Path):
    W, H = 2560, 1440
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    # dégradé de fond (plus clair vers le globe)
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.exp(-(((gx - 2150) / 1300) ** 2 + ((gy - 720) / 900) ** 2))
    bg = np.zeros((H, W, 4), np.uint8)
    bg[..., 0] = np.clip(NAVY[0] + 14 * rad, 0, 255)
    bg[..., 1] = np.clip(NAVY[1] + 30 * rad, 0, 255)
    bg[..., 2] = np.clip(NAVY[2] + 52 * rad, 0, 255)
    bg[..., 3] = 255
    img = Image.fromarray(bg, "RGBA")
    img = Image.alpha_composite(img, stars(W, H, 900))
    # grille HUD discrète
    hud = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hud)
    for x in range(0, W, 80):
        hd.line([(x, 0), (x, H)], fill=CYAN + (10,), width=1)
    for y in range(0, H, 80):
        hd.line([(0, y), (W, y)], fill=CYAN + (10,), width=1)
    img = Image.alpha_composite(img, hud)

    cx, cy, R = 2140, 720, 540
    lon0, lat0 = 8, 26
    h = halo(R, width=0.22, alpha=210)
    img.alpha_composite(h, (cx - h.width // 2, cy - h.height // 2))
    globe = g.render(R, lon0, lat0, light=(0.95, 0.25, -0.15), night_gain=3.4)
    img.alpha_composite(globe, (cx - R, cy - R))
    img = Image.alpha_composite(img, glow_layer((W, H), lambda d, ss: draw_network(d, g, cx, cy, R, lon0, lat0, ss), 3))

    # anneau de compte à rebours autour du globe
    def ring(d, ss):
        r = R * 1.13
        box = ((cx - r) * ss, (cy - r) * ss, (cx + r) * ss, (cy + r) * ss)
        d.arc(box, 120, 330, fill=CYAN + (150,), width=int(2 * ss))
        d.arc(box, 330, 345, fill=AMBER + (220,), width=int(4 * ss))
        for k in range(0, 72):
            ang = math.radians(120 + k * 210 / 72)
            r1, r2 = r * 1.015, r * (1.04 if k % 6 == 0 else 1.025)
            d.line([((cx + r1 * math.cos(ang)) * ss, (cy + r1 * math.sin(ang)) * ss),
                    ((cx + r2 * math.cos(ang)) * ss, (cy + r2 * math.sin(ang)) * ss)],
                   fill=CYAN + (110,), width=int(1.5 * ss))
    img = Image.alpha_composite(img, glow_layer((W, H), ring, 2))

    # textes : tout dans la zone visible sur téléphone (1546 x 423 au centre)
    safe = ((W - 1546) // 2, (H - 423) // 2, (W + 1546) // 2, (H + 423) // 2)
    title_font = ImageFont.truetype(str(fonts / "Anton-Regular.ttf"), 190)
    sub_font = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 46)
    tag_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 26)
    x0 = safe[0] + 70
    def texts(d, ss):
        f = ImageFont.truetype(str(fonts / "Anton-Regular.ttf"), 190 * ss)
        y = 548
        d.text((x0 * ss, y * ss), "WhatIfcast", font=f, fill=(255, 255, 255, 255))
        wpx = d.textlength("WhatIfcast", font=f)
        d.text((x0 * ss + wpx + 4 * ss, y * ss), "FR", font=f, fill=CYAN + (255,))
    tl = glow_layer((W, H), texts, 6)
    img = Image.alpha_composite(img, tl)
    d = ImageDraw.Draw(img)
    d.text((x0 + 4, 520), "S I M U L A T I O N S   ·   S C É N A R I O S   ·   D O N N É E S   R É E L L E S",
           font=tag_font, fill=CYAN + (210,))
    d.text((x0 + 4, 790), "Et si… ? Les scénarios qui changent le monde", font=sub_font, fill=(205, 214, 228, 255))
    d.line([(x0 + 4, 868), (x0 + 124, 868)], fill=AMBER + (255,), width=4)
    # coordonnées HUD (visibles seulement sur grand écran)
    d.text((120, 140), "48.86°N  2.35°E   ·   T+00:00:00", font=tag_font, fill=CYAN + (110,))
    d.text((120, 1270), "RÉSEAU MONDIAL  ·  LIAISONS 20  ·  COUPÉES 4", font=tag_font, fill=AMBER + (130,))
    img.convert("RGB").save(out / "banniere_whatifcastfr_2560x1440.png", optimize=True)
    # aperçu des zones de recadrage
    prev = img.convert("RGB").copy()
    pd = ImageDraw.Draw(prev)
    pd.rectangle(safe, outline=(255, 60, 60), width=4)
    pd.rectangle((0, safe[1], W - 1, safe[3]), outline=(255, 255, 0), width=3)
    prev.resize((1280, 720), Image.LANCZOS).save(out / "apercu_zones_banniere.png")


_last_avatar = [None]


def avatar_img(g: Globe, out: Path):
    avatar(g, out)
    return _last_avatar[0]


def avatar(g: Globe, out: Path):
    S = 800
    img = Image.new("RGBA", (S, S), NAVY + (255,))
    gy, gx = np.mgrid[0:S, 0:S].astype(np.float32)
    rad = np.exp(-(((gx - 400) / 380) ** 2 + ((gy - 380) / 380) ** 2))
    bg = np.zeros((S, S, 4), np.uint8)
    bg[..., 0] = np.clip(NAVY[0] + 12 * rad, 0, 255)
    bg[..., 1] = np.clip(NAVY[1] + 26 * rad, 0, 255)
    bg[..., 2] = np.clip(NAVY[2] + 46 * rad, 0, 255)
    bg[..., 3] = 255
    img = Image.fromarray(bg, "RGBA")
    img = Image.alpha_composite(img, stars(S, S, 120, seed=9))
    cx, cy, R = 400, 372, 205
    lon0, lat0 = -18, 22
    h = halo(R, width=0.18, alpha=220)
    img.alpha_composite(h, (cx - h.width // 2, cy - h.height // 2))
    img.alpha_composite(g.render(R, lon0, lat0, light=(-0.75, 0.35, 0.55), night_gain=3.6), (cx - R, cy - R))

    # point d'interrogation : un arc d'orbite autour du globe qui descend en crochet, point ambre dessous
    rq = R * 1.24
    def qmark(d, ss):
        pts = []
        for k in range(0, 121):
            a = math.radians(200 - k * 245 / 120)  # de la gauche, par le haut, jusqu'en bas à droite
            pts.append((cx + rq * math.cos(a), cy - rq * math.sin(a)))
        ex, ey = pts[-1]
        # crochet : courbe de Bézier qui prolonge l'arc sans cassure puis tige verticale sous le globe
        a = math.radians(200 - 245)
        tan = (math.sin(a), math.cos(a))  # direction de l'arc à son extrémité (sens horaire)
        tx, ty = cx, cy + R * 1.42
        c1 = (ex + tan[0] * 95, ey + tan[1] * 95)
        c2 = (tx, ty - 75)
        for k in range(1, 61):
            t = k / 60
            qx = (1 - t) ** 3 * ex + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * tx
            qy = (1 - t) ** 3 * ey + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * ty
            pts.append((qx, qy))
        d.line([(x * ss, y * ss) for x, y in pts], fill=CYAN + (255,), width=int(15 * ss), joint="curve")
        sx, sy = pts[0]
        d.ellipse(((sx - 7.5) * ss, (sy - 7.5) * ss, (sx + 7.5) * ss, (sy + 7.5) * ss), fill=CYAN + (255,))
        d.ellipse(((tx - 7.5) * ss, (ty - 7.5) * ss, (tx + 7.5) * ss, (ty + 7.5) * ss), fill=CYAN + (255,))
        r, dy = 24, cy + R * 1.42 + 62
        d.ellipse(((cx - r) * ss, (dy - r) * ss, (cx + r) * ss, (dy + r) * ss), fill=AMBER + (255,))
    img = Image.alpha_composite(img, glow_layer((S, S), qmark, 7, ss=3))
    img.convert("RGB").save(out / "profil_whatifcastfr_800x800.png", optimize=True)
    _last_avatar[0] = img
    # aperçus : recadrage rond et taille réelle sur YouTube
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse((0, 0, S - 1, S - 1), fill=255)
    circ = Image.new("RGB", (S, S), (255, 255, 255))
    circ.paste(img.convert("RGB"), (0, 0), m)
    small = [circ.resize((s, s), Image.LANCZOS) for s in (176, 98, 48)]
    sheet = Image.new("RGB", (S + 40 + 176 + 40, S), (255, 255, 255))
    sheet.paste(circ, (0, 0))
    y = 40
    for s in small:
        sheet.paste(s, (S + 40, y))
        y += s.height + 40
    sheet.save(out / "apercu_profil_rond.png")


AVATAR_STYLES = {  # fond, point d'interrogation
    "nuit": (NAVY, CYAN),
    "cyan": (CYAN, NAVY),
    "ambre": (AMBER, NAVY),
}


def avatar_bold(g: Globe, out: Path, style: str):
    """Logo simple, reconnaissable en tout petit : un grand point d'interrogation dont le point est la Terre."""
    S, ss = 800, 3
    bg, fg = AVATAR_STYLES[style]
    img = Image.new("RGBA", (S, S), bg + (255,))
    cx, cy, rq, wq = 400, 300, 150, 88
    pts = []
    for k in range(0, 121):
        a = math.radians(165 - k * 215 / 120)
        pts.append((cx + rq * math.cos(a), cy - rq * math.sin(a)))
    ex, ey = pts[-1]
    a = math.radians(165 - 215)
    tan = (math.sin(a), math.cos(a))
    tx, ty = cx, 520
    c1, c2 = (ex + tan[0] * 80, ey + tan[1] * 80), (tx, ty - 70)
    for k in range(1, 61):
        t = k / 60
        pts.append(((1 - t) ** 3 * ex + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t * t * c2[0] + t ** 3 * tx,
                    (1 - t) ** 3 * ey + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t * t * c2[1] + t ** 3 * ty))
    def q(d, s):
        # trait épais = disques posés le long du tracé (bords nets, pas de pointes aux jointures)
        r = wq / 2
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0)))
            for k in range(n):
                x, y = x0 + (x1 - x0) * k / n, y0 + (y1 - y0) * k / n
                d.ellipse(((x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s), fill=fg + (255,))
        x, y = pts[-1]
        d.ellipse(((x - r) * s, (y - r) * s, (x + r) * s, (y + r) * s), fill=fg + (255,))
    big = Image.new("RGBA", (S * ss, S * ss), (0, 0, 0, 0))
    q(ImageDraw.Draw(big), ss)
    mark = big.resize((S, S), Image.LANCZOS)
    if style == "nuit":
        img = Image.alpha_composite(img, mark.filter(ImageFilter.GaussianBlur(14)))
    img = Image.alpha_composite(img, mark)
    # le point : la Terre de nuit, Europe et Afrique allumées, avec un liseré
    R, gy = 84, 668
    ring = Image.new("RGBA", (S * ss, S * ss), (0, 0, 0, 0))
    rr = R + 10
    ImageDraw.Draw(ring).ellipse(((cx - rr) * ss, (gy - rr) * ss, (cx + rr) * ss, (gy + rr) * ss),
                                 fill=(AMBER if style == "nuit" else NAVY) + (255,))
    img = Image.alpha_composite(img, ring.resize((S, S), Image.LANCZOS))
    img.alpha_composite(g.render(R, 12, 22, light=(-0.9, 0.3, 0.3), night_gain=4.0), (cx - R, gy - R))
    img.convert("RGB").save(out / f"profil_{style}_800x800.png", optimize=True)
    return img


def avatar_sheet(imgs: dict, out: Path):
    """Planche de comparaison : chaque logo en rond, en grand puis aux tailles réelles de YouTube."""
    S = 800
    m = Image.new("L", (S, S), 0)
    ImageDraw.Draw(m).ellipse((0, 0, S - 1, S - 1), fill=255)
    cols = len(imgs)
    sheet = Image.new("RGB", (cols * 340 + 40, 600), (255, 255, 255))
    d = ImageDraw.Draw(sheet)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 22)
    for i, (name, im) in enumerate(imgs.items()):
        c = Image.new("RGB", (S, S), (255, 255, 255))
        c.paste(im.convert("RGB"), (0, 0), m)
        x = 40 + i * 340
        d.text((x, 12), name, font=f, fill=(30, 30, 30))
        sheet.paste(c.resize((300, 300), Image.LANCZOS), (x, 50))
        y = 380
        for s in (98, 48, 32):
            sheet.paste(c.resize((s, s), Image.LANCZOS), (x, y))
            y += s + 12
    sheet.save(out / "comparaison_profils.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--textures", type=Path, required=True)
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    g = Globe(a.textures)
    banner(g, a.fonts, a.out)
    imgs = {"actuel": avatar_img(g, a.out)}
    for st in AVATAR_STYLES:
        imgs[st] = avatar_bold(g, a.out, st)
    avatar_sheet(imgs, a.out)


if __name__ == "__main__":
    main()
