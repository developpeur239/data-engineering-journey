"""Astres rendus en code à partir des textures NASA (film2d/test/textures) : une seule Lune pour tout le film.

  sphere(tex, r, lon0, lumiere)  → RGBA (2r × 2r) : sphère orthographique éclairée (texture équirectangulaire).
  Lune.draw(f, (x, y), r, …)     → la Lune : fractures qui s'étendent, bord déformé, fragmentation en blocs.
  Ciel   (décor) : une image fixe + la Lune dans le ciel (derrière l'horizon), météores, lueur.
  Espace (décor) : la Terre et la Lune dans l'espace, approche, contact, incandescence, panaches (11:00).
  Photos (décor) : écran de Calern, deux photographies de la Lune comparées (08:00).

Tailles apparentes (fiche Lune, plan_rendu_v2 § 7.1) : × 1 au début, × 1,1 à 48 h, × 2 au soir du 2e jour (voiture),
× 4,5 à 6 h, × 12 à 1 h 30, × 35 au dernier écho.
"""
from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np

from decors.commun import dust, load_rgb
from moteur.core import H, W, ease

TEX = Path(__file__).resolve().parents[2] / "film2d/test/textures"
LUNE_IMG = Path(__file__).resolve().parents[2]


@lru_cache(None)
def texture(name):
    return cv2.imread(str(TEX / name))[..., ::-1].astype(np.float32)


@lru_cache(64)
def _grid(r):
    yy, xx = np.mgrid[-r:r, -r:r].astype(np.float32) + 0.5
    x, y = xx / r, yy / r
    d2 = x * x + y * y
    inside = d2 <= 1.0
    z = np.sqrt(np.clip(1 - d2, 0, 1))
    alpha = np.clip((1 - np.sqrt(d2)) * r + 0.5, 0, 1)                  # bord antialiasé
    return x, y, z, inside, alpha


def sphere(tex_name, r, lon0=0.0, light=(-0.55, -0.35, 0.76), ambient=0.08, gain=1.0):
    r = max(2, int(r))
    tex = texture(tex_name); th, tw = tex.shape[:2]
    x, y, z, inside, alpha = _grid(r)
    lat = np.arcsin(np.clip(-y, -1, 1))
    lon = np.arctan2(x, z) + lon0
    u = ((lon / (2 * np.pi) + 0.5) % 1.0) * (tw - 1)
    v = (0.5 - lat / np.pi) * (th - 1)
    col = cv2.remap(tex, u.astype(np.float32), v.astype(np.float32), cv2.INTER_LINEAR)
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    lam = np.clip(x * L[0] + y * L[1] + z * L[2], 0, 1)
    shade = ambient + (1 - ambient) * lam ** 0.8
    col = col * shade[..., None] * gain
    return np.dstack([np.clip(col, 0, 255), alpha * 255]).astype(np.float32)


def paste_rgba(f, img, cx, cy, mask=None, opacity=1.0):
    h, w = img.shape[:2]
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(f.shape[1], x0 + w), min(f.shape[0], y0 + h)
    if X0 >= X1 or Y0 >= Y1:
        return f
    sub = img[Y0 - y0:Y1 - y0, X0 - x0:X1 - x0]
    a = sub[..., 3:4] / 255 * opacity
    if mask is not None:
        a = a * mask[Y0:Y1, X0:X1, None]
    reg = f[Y0:Y1, X0:X1]; reg[:] = reg * (1 - a) + sub[..., :3] * a
    return f


def glow(f, cx, cy, r, col, a):
    if a <= 0:
        return f
    m = np.zeros(f.shape[:2], np.float32)
    cv2.circle(m, (int(cx), int(cy)), int(r), 1, -1, cv2.LINE_AA)
    g = cv2.GaussianBlur(m, (0, 0), max(2, r * 0.6))[..., None] * a
    return f + np.array(col, np.float32) * g


# ------------------------------------------------------------------ la Lune
FRACTURES = [  # polylignes en (longitude, latitude) sur la face visible, en radians ; la 1re est « la ligne sombre »
    [(-0.55, 0.42), (-0.32, 0.30), (-0.12, 0.26), (0.05, 0.12), (0.22, 0.05), (0.40, -0.08), (0.62, -0.12)],
    [(0.05, 0.12), (0.10, -0.15), (0.02, -0.38), (0.12, -0.62)],
    [(-0.32, 0.30), (-0.45, 0.05), (-0.70, -0.10)],
    [(0.40, -0.08), (0.55, 0.20), (0.75, 0.38)],
    [(-0.12, 0.26), (-0.05, 0.55), (0.10, 0.75)],
]


def _proj(lon, lat, r):
    return np.array([np.sin(lon) * np.cos(lat), -np.sin(lat)]) * r


def fractures(img, r, prog, n=5, width=1.0):
    """Trace les fractures (prog 0 → 1 : elles s'étendent) sur le rendu RGBA de la Lune, centrée dans img."""
    c = np.array([img.shape[1] / 2, img.shape[0] / 2])
    out = img.copy()
    for k, poly in enumerate(FRACTURES[:n]):
        p = float(np.clip(prog * 1.6 - k * 0.15, 0, 1))
        if p <= 0:
            continue
        pts = np.array([c + _proj(lo, la, r) for lo, la in poly])
        seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]
        L = seg[-1] * p
        keep = [pts[0]]
        for i in range(1, len(pts)):
            if seg[i] <= L:
                keep.append(pts[i])
            else:
                u = (L - seg[i - 1]) / (seg[i] - seg[i - 1]); keep.append(pts[i - 1] + (pts[i] - pts[i - 1]) * u); break
        t = max(1, int(r * 0.012 * width * (1.4 if k == 0 else 1.0)))
        cv2.polylines(out, [np.int32(keep)], False, (40, 36, 34, 255), t, cv2.LINE_AA)
        cv2.polylines(out, [np.int32(keep)], False, (90, 70, 60, 255), max(1, t // 3), cv2.LINE_AA)
    out[..., 3] = img[..., 3]
    return out


class Lune:
    @staticmethod
    def render(r, fract=0.0, deform=0.0, eclat=0.0, lon0=0.0):
        img = sphere("lune_lroc_nasa.png", r, lon0, light=(-0.25, -0.2, 0.95), ambient=0.12, gain=1.1)
        if fract > 0:
            img = fractures(img, r, fract)
        if deform > 0:                                                           # le bord tourné vers la Terre s'étire
            h, w = img.shape[:2]
            M = np.float32([[1 + 0.10 * deform, 0, -0.10 * deform * w * 0.0], [0, 1 - 0.03 * deform, 0.015 * deform * h]])
            pad = int(w * 0.12 * deform) + 2
            img = cv2.copyMakeBorder(img, 0, 0, 0, pad, cv2.BORDER_CONSTANT, value=0)
            img = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
        if eclat > 0:                                                            # lueur rouge sous les fractures (fin)
            a = img[..., 3:4] / 255
            img[..., :3] = img[..., :3] + np.array([30, 8, 0], np.float32) * eclat * a
        return img

    @staticmethod
    @lru_cache(8)
    def _pieces(r, n=14, seed=5):
        rng = np.random.default_rng(seed)
        pts = []
        while len(pts) < n:
            p = rng.uniform(-1, 1, 2)
            if p @ p < 0.85:
                pts.append(p)
        pts = np.array(pts) * r + r
        yy, xx = np.mgrid[0:2 * r, 0:2 * r]
        d = np.stack([(xx - px) ** 2 + (yy - py) ** 2 for px, py in pts])
        return np.argmin(d, 0), pts

    @staticmethod
    def fragments(f, cx, cy, r, u, toward=(0.0, 1.0), fract=1.0, mask=None):
        """Fragmentation : la Lune se découpe en blocs qui s'écartent (u : 0 → 1) ; les blocs du côté de la Terre
        (direction « toward ») partent plus vite."""
        img = Lune.render(int(r), fract=fract, eclat=min(1.0, u * 1.5))
        lab, pts = Lune._pieces(int(r))
        c = np.array([r, r], float); tw = np.array(toward, float); tw /= np.linalg.norm(tw)
        order = np.argsort([np.dot(p - c, tw) for p in pts])                     # du fond vers l'avant
        for k in order:
            m = (lab == k).astype(np.float32)
            piece = img.copy(); piece[..., 3] *= m
            d = pts[k] - c; nd = np.linalg.norm(d) + 1e-6
            front = max(0.0, np.dot(d / nd, tw))
            off = d / nd * r * 0.45 * u ** 1.4 + tw * r * 0.9 * u * u * front              # écartement + avance vers la Terre
            ang = (k % 5 - 2) * 4 * u
            R = cv2.getRotationMatrix2D((float(pts[k][0]), float(pts[k][1])), ang, 1.0)
            piece = cv2.warpAffine(piece, R, (piece.shape[1], piece.shape[0]))
            if u > 0.05:                                                         # bord incandescent des cassures
                edge = cv2.morphologyEx((piece[..., 3] > 128).astype(np.uint8), cv2.MORPH_GRADIENT, np.ones((3, 3), np.uint8))
                piece[..., :3] += edge[..., None] * np.array([255, 120, 40], np.float32) * min(1.0, u * 2)
            paste_rgba(f, piece, cx + off[0], cy + off[1], mask)
        for k in range(int(40 * u)):                                             # poussière et petits débris
            rng = np.random.default_rng(k)
            a = rng.uniform(0, 2 * np.pi); dd = r * (0.9 + rng.uniform(0, 1.2) * u)
            p = (int(cx + np.cos(a) * dd + tw[0] * r * u * rng.uniform(0, 1.5)), int(cy + np.sin(a) * dd + tw[1] * r * u * rng.uniform(0, 1.5)))
            cv2.circle(f, p, max(1, int(r * 0.012 * rng.uniform(0.5, 2))), (150, 140, 130), -1, cv2.LINE_AA)
        return f


# ------------------------------------------------------------------ décor : une image + la Lune dans le ciel
class Ciel:
    """reglages : image (chemin depuis lune/), horizon (y source ; la Lune passe derrière tout ce qui est plus bas, et
    derrière tout ce qui n'est pas du ciel), lune [x, y, rayon] (source), fract, deform, morceaux (ancre de début de la
    fragmentation), meteores (ancre), lueur (0–1, la nuit s'éclaire), nuit (assombrit l'image, 0–1)."""

    def __init__(self, bloc):
        self.cache = {}

    def base(self, p, horizon):
        key = (p, horizon)
        if key not in self.cache:
            img = load_rgb(LUNE_IMG / p)
            r, g, b = img[..., 0], img[..., 1], img[..., 2]
            lum = img.mean(2)
            yy = np.mgrid[0:img.shape[0], 0:img.shape[1]][0]
            sky = ((b >= r - 4) & (np.abs(cv2.Laplacian(lum, cv2.CV_32F)) < 6) & (yy < horizon)).astype(np.uint8)
            sky = cv2.morphologyEx(sky, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
            n, lab, st, _ = cv2.connectedComponentsWithStats(sky)                # le ciel : la grande zone reliée au haut
            top = set(np.unique(lab[:6])) - {0}
            sky = np.isin(lab, list(top)).astype(np.float32)
            self.cache[key] = (img, cv2.GaussianBlur(sky, (0, 0), 1.5))
        return self.cache[key]

    def render(self, t, shot, bloc):
        R = shot["reglages"]
        img, sky = self.base(R["image"], R.get("horizon", 99999))
        f = img.copy()
        nuit = R.get("nuit", 0.0)
        if nuit:
            f *= 1 - nuit
        lx, ly, lr = (bloc.keys(t, R["lune"]) if isinstance(R["lune"][0], list) else np.array(R["lune"], float))
        lr *= 1 + R.get("croissance", 0.0) * (t - shot["_t0"])                   # elle grossit pendant le plan
        fract = float(bloc.keys(t, R["fract"])[0]) if isinstance(R.get("fract"), list) else R.get("fract", 0.0)
        lum = R.get("lueur", 0.35)
        f = glow(f, lx, ly, lr * 1.6, (150, 160, 180), lum * 0.5)                 # halo
        if "morceaux" in R and t >= bloc.t(R["morceaux"]):
            u = (t - bloc.t(R["morceaux"])) / R.get("duree_morceaux", 12.0)
            Lune.fragments(f, lx, ly, lr, float(np.clip(u, 0, 1.2)), toward=R.get("vers", (0.15, 1.0)), mask=sky)
        else:
            moon = Lune.render(int(lr), fract=fract, deform=R.get("deform", 0.0))
            paste_rgba(f, moon, lx, ly, sky)
        if "meteores" in R and t >= bloc.t(R["meteores"]):
            f = meteors(f, t - bloc.t(R["meteores"]), lx, ly, lr, sky)
        if R.get("poussiere"):
            dust(f, t, (40, 40, f.shape[1] - 40, f.shape[0] - 40), n=50, alpha=0.15)
        return f


def meteors(f, dt, lx, ly, lr, sky):
    """Fragments qui entrent dans l'atmosphère : traînées incandescentes, certaines énormes."""
    over = np.zeros_like(f); a = np.zeros(f.shape[:2], np.float32)
    for k in range(18):
        rng = np.random.default_rng(100 + k)
        t0 = rng.uniform(0, 6); age = dt - t0
        if age < 0:
            continue
        big = k % 6 == 0
        start = np.array([lx + rng.uniform(-1, 1) * lr, ly + rng.uniform(-0.5, 1) * lr])
        dirv = np.array([rng.uniform(-0.6, 0.6), 1.0]); dirv /= np.linalg.norm(dirv)
        speed = rng.uniform(260, 420) * (0.7 if big else 1.0)
        p = start + dirv * speed * age
        if p[1] > f.shape[0] + 200:
            continue
        tail = p - dirv * speed * min(age, 0.9)
        w = int(rng.uniform(3, 6) * (3 if big else 1))
        cv2.line(over, tuple(np.int32(tail)), tuple(np.int32(p)), (255, 170, 90), w, cv2.LINE_AA)
        cv2.line(a, tuple(np.int32(tail)), tuple(np.int32(p)), 0.9, w, cv2.LINE_AA)
        cv2.circle(over, tuple(np.int32(p)), w + 2, (255, 240, 210), -1, cv2.LINE_AA)
        cv2.circle(a, tuple(np.int32(p)), w + 2, 1.0, -1, cv2.LINE_AA)
    a = cv2.GaussianBlur(a, (0, 0), 3)[..., None] * sky[..., None]
    over = cv2.GaussianBlur(over, (0, 0), 3)
    g = cv2.GaussianBlur(a, (0, 0), 18)[..., None] if a.ndim == 2 else cv2.GaussianBlur(a[..., 0], (0, 0), 18)[..., None]
    return f * (1 - a) + over * a + np.array([255, 150, 80], np.float32) * g * 0.6


# ------------------------------------------------------------------ décor : l'espace (collision)
class Espace:
    """reglages : terre [x, y, r], lune (images clés [[t, x, y, r], …]), contact (ancre), fract, morceaux…"""

    def __init__(self, bloc):
        rng = np.random.default_rng(9)
        self.stars = rng.random((500, 3))

    def render(self, t, shot, bloc):
        R = shot["reglages"]
        f = np.zeros((H, W, 3), np.float32) + np.array([4, 6, 12], np.float32)
        for x, y, b in self.stars:
            cv2.circle(f, (int(x * W), int(y * H)), 1, tuple(float(40 + 160 * b) for _ in range(3)), -1)
        ex, ey, er = R["terre"]
        rot = 0.02 * t
        earth = sphere("terre_bluemarble_nasa.png", er, 1.2 + rot, light=(0.5, -0.3, 0.8), ambient=0.05, gain=1.05)
        mx, my, mr = bloc.keys(t, R["lune"])
        tc = bloc.t(R["contact"]) if "contact" in R else 1e9
        if t < tc:
            f = glow(f, ex, ey, er * 1.05, (60, 120, 220), 0.35)
            paste_rgba(f, earth, ex, ey)
            if "morceaux" in R and t >= bloc.t(R["morceaux"]):
                Lune.fragments(f, mx, my, mr, float(np.clip((t - bloc.t(R["morceaux"])) / 10, 0, 0.6)), toward=(ex - mx, ey - my))
            else:
                paste_rgba(f, Lune.render(int(mr), fract=R.get("fract", 0.0)), mx, my)
        else:                                                                    # après le contact
            u = t - tc
            paste_rgba(f, earth, ex, ey)
            dirv = np.array([mx - ex, my - ey]); dirv /= np.linalg.norm(dirv)
            cp = np.array([ex, ey]) + dirv * er * 0.95                            # point de contact
            m = np.zeros(f.shape[:2], np.float32)                                 # région incandescente qui s'étend
            cv2.circle(m, tuple(np.int32(cp)), int(er * min(0.9, 0.12 + 0.18 * u)), 1, -1, cv2.LINE_AA)
            e = np.zeros(f.shape[:2], np.float32); cv2.circle(e, (int(ex), int(ey)), int(er), 1, -1, cv2.LINE_AA)
            m = cv2.GaussianBlur(m, (0, 0), er * 0.08) * e
            f = f * (1 - m[..., None]) + np.array([255, 140, 50], np.float32) * m[..., None]
            rest = max(0.0, 1 - u / 2.5)                                           # ce qui reste de la Lune s'enfonce
            if rest > 0:
                paste_rgba(f, Lune.render(int(mr * (0.5 + 0.5 * rest)), fract=1.0, eclat=1.0), *(cp + dirv * mr * 0.6 * rest), opacity=rest)
            pl = np.zeros_like(f); pa = np.zeros(f.shape[:2], np.float32)          # panaches de roche fondue
            for k in range(420):
                rng = np.random.default_rng(k)
                ang = np.arctan2(dirv[1], dirv[0]) + rng.normal(0, 0.6)
                sp = rng.uniform(0.1, 0.75) * er
                d = np.array([np.cos(ang), np.sin(ang)])
                q1 = cp + d * sp * u ** 0.7; q0 = cp + d * sp * u ** 0.7 * 0.55
                w = max(1, int(er * 0.012 * rng.uniform(0.6, 2.0)))
                col = (255, int(110 + 110 * rng.random()), 50) if rng.random() < 0.7 else (140, 120, 110)
                cv2.line(pl, tuple(np.int32(q0)), tuple(np.int32(q1)), col, w, cv2.LINE_AA)
                cv2.line(pa, tuple(np.int32(q0)), tuple(np.int32(q1)), 0.85, w, cv2.LINE_AA)
            pa = cv2.GaussianBlur(pa, (0, 0), 2.5)[..., None]; pl = cv2.GaussianBlur(pl, (0, 0), 2.5)
            f = f * (1 - pa) + pl + np.array([255, 130, 50], np.float32) * cv2.GaussianBlur(pa[..., 0], (0, 0), 25)[..., None] * 0.8
            flash = max(0.0, 1 - u / 0.8)
            f = glow(f, *cp, er * 0.9, (255, 240, 220), 2.2 * flash)
            f = f + 255 * max(0.0, 1 - u / 0.35) * 0.9                              # éclair blanc au contact
        return f


# ------------------------------------------------------------------ décor : deux photographies comparées
class Photos:
    """reglages : mode "telephones" (48 h : les gens comparent leurs photos, Lune × 1 et × 1,1) ou "calern" (08:00 :
    la région intacte, puis la ligne sombre), avec les ancres "seconde", "zoom", "transmise"."""

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        from decors.schemas import DIM, INK, MONO, RED, SANS, canvas, texts  # noqa: PLC0415
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items() if k != "mode"}
        f = canvas(grid=False)
        items = []
        if R["mode"] == "telephones":
            for k, (x, rr, lab) in enumerate(((620, 150, "il y a deux jours"), (1300, 165, "ce soir"))):
                a = float(ease((t - shot["_t0"] - 0.6 * k) / 0.5))
                ph = np.zeros_like(f); cv2.rectangle(ph, (x - 230, 150), (x + 230, 930), (18, 18, 22), -1)
                cv2.rectangle(ph, (x - 215, 200), (x + 215, 880), (8, 10, 20), -1)
                f = f * (1 - a) + ph * a if a > 0 else f
                if a > 0:
                    paste_rgba(f, sphere("lune_lroc_nasa.png", rr, gain=1.1), x, 520, opacity=a)
                    items.append((lab, (x, 950), SANS, 34, DIM, a, True))
            items.append(("+ 10 %", (960, 500), MONO, 64, RED, float(ease((t - T["comparer"]) / 0.4)), True))
        else:
            sec, z = T["seconde"], float(ease((t - T.get("zoom", 1e9)) / 1.2))
            items.append(("CALERN · IMAGERIE LUNAIRE", (110, 150), SANS, 30, DIM, 1, False))
            for k, (x, lab, fr) in enumerate(((560, "22 h 41", 0.0), (1360, "22 h 47", 1.0))):
                if k == 1 and t < sec:
                    continue
                r0 = 300
                big = Lune.render(int(r0 * (1 + 1.4 * z)), fract=0.35 if k == 1 else 0.0)
                h, w = big.shape[:2]                                                     # recadrée sur la région
                cx, cy = w // 2 + int(-0.15 * r0 * (1 + 1.4 * z)), h // 2 + int(-0.22 * r0 * (1 + 1.4 * z))
                crop = big[max(0, cy - 300):cy + 300, max(0, cx - 330):cx + 330]
                paste_rgba(f, crop, x, 540)
                cv2.rectangle(f, (x - 330, 240), (x + 330, 840), (70, 90, 120), 2, cv2.LINE_AA)
                items.append((lab, (x - 320, 856), MONO, 34, INK, 1, False))
            if t >= T.get("transmise", 1e9):
                items.append(("Observatoire partenaire : même anomalie", (W / 2, 950), SANS, 40, RED, float(ease((t - T["transmise"]) / 0.4)), True))
        return texts(f, items)
