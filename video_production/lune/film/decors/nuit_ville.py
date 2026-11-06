"""Décors « nuit, petite ville, Lune géante » (bloc 1, réutilisables) : Chambre, Fenetre, Rue.

Chaque décor rend l'image SOURCE (2752×1536) à l'instant t ; la caméra, l'étalonnage et les filtres sont appliqués
ensuite par le moteur, d'après shots.json. Les réglages d'un plan sont dans shot["reglages"] (temps = ancres).
Dessins fixes générés (film/b01/*.png) + tout le mouvement en code.
"""
from pathlib import Path

import cv2
import numpy as np

from decors.commun import CLOUD, FOG, clouds, dust, load_rgb, load_rgba, sky_mask, warp_local  # noqa: F401
from moteur.core import ease

ASSETS = Path(__file__).resolve().parents[1] / "b01"


# ------------------------------------------------------------------ gens aux fenêtres (bustes à contre-jour)
def _busts(sprites):
    out = []
    for a in sprites:
        al = a[..., 3]
        ys = np.nonzero(al.max(1) > 128)[0]; top = ys.min(); cut = int(top + (ys.max() - top) * 0.36)
        out.append(al[top:cut])
    return out


def light_windows(img, wins, busts, relight=True, size=0.62):
    out = img.copy()
    for k, (x0, y0, x1, y1, who) in enumerate(wins):
        w, h = x1 - x0, y1 - y0
        if relight:
            warm = np.array([255, 196, 128], np.float32) * np.linspace(1.0, 0.75, h)[:, None, None]
            out[y0:y1, x0:x1] = out[y0:y1, x0:x1] * 0.15 + warm * 0.85
        if who is not None:                                          # buste en bas de la fenêtre, à contre-jour
            b = busts[who % len(busts)]; bw = int(w * size); bh = int(b.shape[0] * bw / b.shape[1])
            bh = min(bh, int(h * (0.75 if relight else 0.55)))
            bb = cv2.resize(b, (bw, bh), interpolation=cv2.INTER_AREA)[..., None] / 255
            yb = y1 - bh; xb = x0 + (w - bw) // 2 + int(w * 0.05 * ((k % 3) - 1))
            reg = out[yb:y1, xb:xb + bw]; reg[:] = reg * (1 - bb) + np.array([22, 20, 24], np.float32) * bb
        if relight:
            glow = np.zeros(img.shape[:2], np.float32); cv2.rectangle(glow, (x0, y0), (x1, y1), 1, -1)
            glow = cv2.GaussianBlur(glow, (0, 0), max(4, w * 0.25))[..., None] * 0.22
            out = out * (1 - glow) + np.array([255, 190, 120], np.float32) * glow
    return out


def _retour(t, shot, bloc):
    """Avancement du retour en arrière (0 → 1) et son instant de départ."""
    r = shot.get("reglages", {}).get("retour")
    if not r:
        return 0.0, None
    a, b = bloc.t(r["de"]), bloc.t(r["a"])
    return (float(ease((t - a) / (b - a))) if t > a else 0.0), a


# ------------------------------------------------------------------ la chambre
class Chambre:
    """Chambre éclairée par la Lune : rideaux qui ondulent, poussière, lumière qui monte (réglage « lumiere »)."""

    def __init__(self, bloc):
        self.img = load_rgb(ASSETS / "chambre_nuit.png")
        h, w = self.img.shape[:2]
        self.yy, self.xx = np.mgrid[0:h, 0:w].astype(np.float32)
        cur = np.zeros((h, w), np.float32)
        cv2.rectangle(cur, (1390, 150), (1730, 905), 1, -1); cv2.rectangle(cur, (2010, 100), (2480, 1000), 1, -1)
        self.cur_w = cv2.GaussianBlur(cur, (0, 0), 25) * np.clip((self.yy - 150) / 700, 0, 1) ** 1.3  # fixé à la tringle
        self.bright = np.clip((self.img.mean(2) - 150) / 70, 0, 1)                                 # zones éclairées

    def render(self, t, shot, bloc):
        sway = 7 * np.sin(2 * np.pi * t / 5.3 + self.yy * 0.004) + 3 * np.sin(2 * np.pi * t / 2.9 + 1.3)
        f = cv2.remap(self.img, (self.xx - self.cur_w * sway).astype(np.float32), self.yy, cv2.INTER_LINEAR)
        lum = shot.get("reglages", {}).get("lumiere")
        lk = float(ease((t - bloc.t(lum)) / 1.3)) if lum else 1.0
        f *= ((1 - self.bright * (1 - lk) * 0.38) * (0.66 + 0.34 * lk))[..., None]
        dust(f, t, (1450, 300, 2350, 1300), alpha=0.06 + 0.18 * lk)
        return f


# ------------------------------------------------------------------ la vue depuis la fenêtre
class Fenetre:
    """Vue sur la ville et la Lune géante : nuages, gens aux fenêtres, une fenêtre s'éteint, pas vers la fenêtre."""

    def __init__(self, bloc):
        img = load_rgb(ASSETS / "fenetre_rue.png")
        self.sky = sky_mask(img, 800, (780, 2230))
        win = (img[..., 0] > 160) & (img[..., 0] - img[..., 2] > 55)              # fenêtres éclairées (chaudes)
        win = cv2.morphologyEx(win.astype(np.uint8), cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        n, lab = cv2.connectedComponents(cv2.dilate(win, np.ones((9, 9), np.uint8)))   # carreaux d'une fenêtre = 1 fenêtre
        lab = lab * (cv2.dilate(win, np.ones((3, 3), np.uint8)) > 0)
        sizes = np.bincount(lab.ravel())
        cands = [i for i in range(1, n) if 250 < sizes[i] < 30000]
        target = max(cands, key=lambda i: np.mean(np.nonzero(lab == i)[1])) if cands else None
        self.off = (cv2.GaussianBlur(cv2.dilate((lab == target).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32),
                                     (0, 0), 2) if target else None)
        self.dark = cv2.GaussianBlur(img, (0, 0), 1) * np.array([0.30, 0.33, 0.42], np.float32)
        wins = []
        for i in sorted(cands, key=lambda i: -sizes[i]):
            if i == target:
                continue
            ys, xs = np.nonzero(lab == i)
            if ys.max() - ys.min() > 30 and xs.max() - xs.min() > 14:
                wins.append((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1, len(wins)))
        busts = _busts([load_rgba(ASSETS / f"{n}.png") for n in ("fig_1", "fig_0", "fig_3", "foule_1", "foule_5", "foule_4")])
        self.img = light_windows(img, wins[:4], busts, relight=False, size=0.95)

    def render(self, t, shot, bloc):
        f = self.img.copy()
        clouds(f, self.sky[:800], 1800 - 22 * t, 0.85)
        off = shot.get("reglages", {}).get("fenetre_eteinte")
        if self.off is not None and off:
            k = float(ease((t - bloc.t(off)) / 0.25))
            a = (self.off * k)[..., None]
            f = f * (1 - a) + self.dark * a
        return f

    def bob(self, t, shot, bloc):
        """Trois pas jusqu'à la fenêtre (réglage « pas » : début, durée) : la vue monte et descend un peu."""
        p = shot.get("reglages", {}).get("pas")
        if not p:
            return 0.0
        a, d = bloc.t(p["de"]), p.get("duree", 1.6)
        u = (t - a) / d
        return 7 * np.sin(2 * np.pi * 1.9 * (t - a)) * np.sin(np.pi * u) if 0 < u < 1 else 0.0


# ------------------------------------------------------------------ la rue
# la foule : 13 personnes sur trois rangs, du fond vers l'avant : (image, centre x, pieds y, échelle)
_G = 0.33
_GX = 1376 - (2549 - 204) * _G / 2 - 204 * _G
_CROWD = [("foule_0", 1010, 1232, 0.165), ("foule_3", 1555, 1236, 0.16), ("foule_5", 1745, 1230, 0.165),
          ("foule_1", 870, 1300, 0.225), ("foule_2", 1200, 1296, 0.215), ("foule_4", 1880, 1302, 0.22)] + \
    [(f"fig_{k}", _GX + (x0 + x1) / 2 * _G, 1405, _G) for k, (x0, x1) in enumerate([(204, 755), (821, 1320), (1365, 2142), (2176, 2549)])]


class Rue:
    """Rue sous la Lune géante : 13 personnes immobiles qui respirent, ombres, brume, gens aux fenêtres ; le réglage
    « retour » fait repartir nuages et brume à l'envers (de plus en plus vite) et efface les gens."""

    CROWD = _CROWD
    WIN = [(178, 165, 268, 395, 0), (806, 702, 831, 848, 1), (872, 742, 889, 888, None), (1772, 672, 1789, 778, 2),
           (1842, 607, 1859, 718, 3), (1921, 742, 1939, 858, None), (2226, 332, 2254, 418, 4)]

    def __init__(self, bloc):
        self.spr = {n: load_rgba(ASSETS / f"{n}.png") for n, *_ in self.CROWD}
        busts = _busts([self.spr[n] for n in ("fig_1", "fig_0", "fig_3", "foule_1", "foule_5", "foule_4")])
        img = load_rgb(ASSETS / "rue_lune.png")
        self.sky = sky_mask(img, 820)
        self.img = light_windows(img, self.WIN, busts)
        self.fog = cv2.resize(FOG, (FOG.shape[1], 360))
        self.fogy = np.exp(-((np.arange(360)[:, None] - 170) / 110) ** 2)

    def person(self, f, k, t, rew):
        name, cx, feet, s = self.CROWD[k]
        img = self.spr[name]; h, w = img.shape[:2]
        br = 0.006 * np.sin(2 * np.pi * t / (3.4 + 0.37 * k) + k * 1.7)              # respiration, propre à chacun
        sway = 0.35 * np.sin(2 * np.pi * t / (5.0 + 0.6 * k) + k)                    # balancement à peine visible
        R = np.vstack([cv2.getRotationMatrix2D((w / 2, h), sway, 1.0), [0, 0, 1]])
        Sb = np.array([[1, 0, 0], [0, 1 + br, -h * br], [0, 0, 1]])                  # le corps s'étire depuis les pieds
        x = cx - w * s / 2; y = feet - h * s
        As = np.float32([[s, 0.35 * s, x - 0.35 * s * h], [0, -0.42 * s, feet + 0.42 * s * h]])   # ombre vers nous
        sh, sx, sy = warp_local(img[..., 3], As, f.shape)
        if sh is not None:
            sh = cv2.GaussianBlur(sh, (0, 0), 3)[..., None] / 255 * 0.42 * (1 - rew)
            reg = f[sy:sy + sh.shape[0], sx:sx + sh.shape[1]]; reg[:] = reg * (1 - sh * 0.75)
        A = (np.array([[s, 0, x], [0, s, y], [0, 0, 1]]) @ Sb @ R)[:2].astype(np.float32)
        out, ox, oy = warp_local(img, A, f.shape)
        if out is not None:
            a = out[..., 3:4] / 255 * (1 - rew)
            reg = f[oy:oy + out.shape[0], ox:ox + out.shape[1]]; reg[:] = reg * (1 - a) + out[..., :3] * a

    def render(self, t, shot, bloc):
        f = self.img.copy()
        rew, ta = _retour(t, shot, bloc)
        back = (t - ta) if ta is not None and t > ta else 0.0                        # temps écoulé depuis le retour
        tt = t - back
        clouds(f, self.sky[:820], 2400 - 18 * tt + 160 * back ** 1.6, 0.7)
        fx_ = int(300 + 30 * tt - 140 * back ** 1.5) % (FOG.shape[1] - f.shape[1])
        fa = (self.fog[:, fx_:fx_ + f.shape[1]] * self.fogy * 0.28)[..., None]
        f[930:1290] = f[930:1290] * (1 - fa) + np.array([175, 185, 200], np.float32) * fa
        for k in range(len(self.CROWD)):
            self.person(f, k, t, rew)
        return f
