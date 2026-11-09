"""Littoral (blocs 3 et 4, puis 7, 11, 12) : la mer animée en code sur des images fixes.

  Plage     film2d/images/decor_plage.png : reflets qui scintillent, écume qui avance et recule.
  Port      b04/port.png : le même traitement de l'eau + des bateaux (en code) qui sortent par le chenal, avec leur sillage.
  Barriere  b04/plage_barriere.png : la même plage barrée ; panneau « Plage fermée » écrit en code ; la mère et le
            garçon (silhouettes b04/*.png) : "scene" = "arrivee" (ils marchent jusqu'à la barrière et s'arrêtent sur
            "arret"), "accroupie" (la mère s'accroupit près de lui), "garcon" (lui seul, de dos, face à la mer).
"""
from pathlib import Path

import cv2
import numpy as np

from decors.commun import load_rgb, load_rgba, noise_tex, warp_local
from moteur.core import ease, font

LUNE = Path(__file__).resolve().parents[2]
B04 = LUNE / "film/b04"


class Eau:
    IMAGE = "film2d/images/decor_plage.png"
    EXCLU = []                                                                      # rectangles où rien ne bouge (panneau…)
    GLINT = 0.35                                                                    # force des reflets

    def __init__(self, bloc):
        self.img = load_rgb(LUNE / self.IMAGE)
        h, w = self.img.shape[:2]
        r, g, b = (self.img[..., k] for k in range(3))
        yy = np.mgrid[0:h, 0:w][0]
        water = ((b - r) > 14) & (yy > h * 0.22) & (yy < h * 0.92)                  # la mer : bleutée, sous l'horizon
        water = cv2.morphologyEx(water.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
        foam = ((r > 228) & (g > 228) & (b > 228) & (yy > h * 0.36) & (yy < h * 0.75)).astype(np.uint8)
        for x0, y0, x1, y1 in self.EXCLU:
            water[y0:y1, x0:x1] = 0; foam[y0:y1, x0:x1] = 0
        self.water = cv2.GaussianBlur(water.astype(np.float32), (0, 0), 4)
        self.foam = cv2.GaussianBlur(foam.astype(np.float32), (0, 0), 3)
        self.glint = noise_tex(h // 4, w // 4, 3, 21)

    def sea(self, f, t):
        h, w = f.shape[:2]
        sh = int(6 * np.sin(t * 0.9)), int(4 * np.sin(t * 0.7 + 1))               # reflets qui bougent
        g = np.roll(np.roll(self.glint, sh[0] + int(t * 9), 1), sh[1], 0)
        g = cv2.resize(np.clip((g - 0.72) / 0.12, 0, 1) ** 2, (w, h))
        a = (g * self.water * self.GLINT * (1 + 0.3 * np.sin(t * 2.3)))[..., None]
        f = f * (1 - a) + np.array([245, 250, 255], np.float32) * a
        dy = 6 * np.sin(2 * np.pi * t / 4.2)                                        # l'écume avance et recule
        M = np.float32([[1, 0, -dy * 0.6], [0, 1, dy]])
        fo = cv2.warpAffine(self.foam, M, (w, h))[..., None] * 0.5
        return f * (1 - fo) + 250 * fo

    def render(self, t, shot, bloc):
        return self.sea(self.img.copy(), t)


class Plage(Eau):
    pass


class Port(Eau):
    """Les bateaux sortent du port par le chenal, vus de l'arrière, et rapetissent vers l'horizon."""
    IMAGE = "film/b04/port.png"
    GLINT = 0.12
    BATEAUX = [  # départ (x, y, échelle) → arrivée, décalage dans le temps (s), coque, bande
        ((1560, 1330, 1.25), (1600, 915, 0.16), 0.0, (238, 240, 244), (40, 90, 160)),
        ((1330, 1180, 0.85), (1545, 905, 0.13), 2.6, (236, 222, 190), (170, 60, 50)),
    ]

    def boat(self, f, x, y, s, hull, band, t):
        r = 1.5 * np.sin(t * 2.2) * s                                                # léger roulis
        wake = np.zeros(f.shape[:2], np.float32)                                     # sillage en V, vers nous
        for side in (-1, 1):
            p0 = (int(x + side * 50 * s), int(y + 6 * s))
            p1 = (int(x + side * 150 * s), int(y + 170 * s))
            cv2.line(wake, p0, p1, 1.0, max(1, int(6 * s)), cv2.LINE_AA)
        cv2.ellipse(wake, (int(x), int(y + 60 * s)), (int(30 * s) + 1, int(70 * s) + 1), 0, 0, 360, 0.5, -1, cv2.LINE_AA)
        wake = cv2.GaussianBlur(wake, (0, 0), max(1.0, 7 * s))[..., None] * 0.4
        f[:] = f * (1 - wake) + 248 * wake
        P = lambda dx, dy: (int(x + (dx * np.cos(np.radians(r)) - dy * np.sin(np.radians(r))) * s),  # noqa: E731
                            int(y + (dx * np.sin(np.radians(r)) + dy * np.cos(np.radians(r))) * s))
        hullp = np.int32([P(-80, -40), P(80, -40), P(66, 10), P(30, 26), P(-30, 26), P(-66, 10)])
        cv2.fillPoly(f, [hullp], hull, cv2.LINE_AA)
        cv2.fillPoly(f, [np.int32([P(-80, -40), P(80, -40), P(78, -28), P(-78, -28)])], band, cv2.LINE_AA)
        cv2.polylines(f, [hullp], True, (90, 96, 108), max(1, int(2 * s)), cv2.LINE_AA)
        cv2.rectangle(f, P(-36, -96), P(36, -40), (226, 230, 236), -1)               # cabine
        cv2.rectangle(f, P(-26, -84), P(26, -62), (90, 110, 130), -1)                # vitre arrière
        cv2.line(f, P(0, -96), P(0, -170), (110, 114, 120), max(1, int(3 * s)), cv2.LINE_AA)   # antenne / mât court

    def render(self, t, shot, bloc):
        f = self.sea(self.img.copy(), t)
        t0 = shot["_t0"]
        for a, b, dt, hull, band in self.BATEAUX:
            u = (t - t0 + 1.2 - dt) / 7.5                                           # ils sont déjà en route à la coupe
            if 0 <= u <= 1:
                k = float(u) ** 0.7                                                  # perspective : vite près de nous, lent au loin
                x, y, s = (np.array(a) * (1 - k) + np.array(b) * k)
                self.boat(f, x, y, s, hull, band, t)
        return f


def legs_of(spr):
    """Hanche et séparation des jambes, trouvées dans la silhouette (de dos) : la première ligne, en remontant depuis
    les pieds, où les deux jambes se rejoignent."""
    a = spr[..., 3] > 128
    h = a.shape[0]
    hip, split = None, None
    for y in range(h - 20, h // 2, -2):
        d = np.diff(np.r_[0, a[y].astype(int), 0]); s = np.where(d == 1)[0]; e = np.where(d == -1)[0]
        segs = [(x0, x1) for x0, x1 in zip(s, e) if x1 - x0 > 8]
        if len(segs) >= 2:
            split = (segs[0][1] + segs[1][0]) / 2
        elif split is not None:
            hip = y + 6
            break
    return hip, split


class Barriere(Eau):
    IMAGE = "film/b04/plage_barriere.png"
    GLINT = 0.25
    PANNEAU = (1297, 711, 1681, 959)
    EXCLU = [PANNEAU]
    # (x, y des pieds, échelle) : départ et arrivée de la marche ; positions de la scène accroupie
    MERE = ((520, 1530, 0.46), (770, 1150, 0.36))
    GARCON = ((760, 1500, 0.37), (950, 1138, 0.29))
    ACCROUPIE = (800, 1152, 0.36)

    def __init__(self, bloc):
        super().__init__(bloc)
        x0, y0, x1, y1 = self.PANNEAU                                                # « Plage fermée », écrit en code
        from PIL import Image, ImageDraw
        im = Image.fromarray(self.img.astype(np.uint8)); d = ImageDraw.Draw(im)
        for txt, fn, size, col, yy in (("PLAGE FERMÉE", "InstrumentSans-Bold.ttf", 44, (178, 40, 36), y0 + 66),
                                       ("Accès et baignade", "InstrumentSans-Bold.ttf", 30, (40, 44, 52), y0 + 140),
                                       ("interdits", "InstrumentSans-Bold.ttf", 30, (40, 44, 52), y0 + 178)):
            fo = font(fn, size); bb = d.textbbox((0, 0), txt, font=fo)
            d.text(((x0 + x1) / 2 - (bb[2] - bb[0]) / 2, yy), txt, font=fo, fill=col)
        self.img = np.asarray(im).astype(np.float32)
        self.spr = {n: load_rgba(B04 / f"{n}.png") for n in ("mere_dos", "mere_accroupie", "garcon_dos")}
        self.legs = {n: legs_of(self.spr[n]) for n in ("mere_dos", "garcon_dos")}

    def paste(self, f, img, A):
        out, ox, oy = warp_local(img, np.asarray(A)[:2].astype(np.float32), f.shape)
        if out is not None:
            a = out[..., 3:4] / 255
            reg = f[oy:oy + out.shape[0], ox:ox + out.shape[1]]; reg[:] = reg * (1 - a) + out[..., :3] * a

    def figure(self, f, name, x, feet, s, t, k, step=None):
        """Une silhouette debout ou accroupie ; step = (phase, amplitude) pendant la marche (de dos : le pied qui
        avance se lève et monte à l'écran, l'autre reste au sol)."""
        img = self.spr[name]; h, w = img.shape[:2]
        br = 0.006 * np.sin(2 * np.pi * t / (3.3 + 0.5 * k) + k)
        sh = np.zeros(f.shape[:2], np.float32)                                       # ombre de contact
        cv2.ellipse(sh, (int(x), int(feet - 4)), (int(w * s * 0.42), int(8 + 10 * s)), 0, 0, 360, 1, -1, cv2.LINE_AA)
        f *= 1 - cv2.GaussianBlur(sh, (0, 0), 5)[..., None] * 0.28
        bob = 0.0
        M = lambda yb: np.array([[s, 0, x - w * s / 2], [0, s, feet - h * s - yb], [0, 0, 1]])  # noqa: E731
        if step is not None and name in self.legs and self.legs[name][0]:
            ph, amp = step
            hip, split = self.legs[name]
            bob = amp * 0.25 * abs(np.sin(np.pi * ph))
            body = img.copy(); body[hip:, :, 3] = 0
            for side, (l0, l1) in enumerate(((0, int(split)), (int(split), w))):
                piece = np.zeros_like(img); piece[hip:, l0:l1] = img[hip:, l0:l1]
                u = (ph / 2 + 0.5 * side) % 1.0
                lift = amp * np.sin(np.pi * (u - 0.5) / 0.5) if u >= 0.5 else 0.0      # le pied en l'air remonte (il s'éloigne)
                L = (h - hip) * s
                sy = 1 - lift / max(L, 1)
                self.paste(f, piece, M(0) @ np.array([[1, 0, 0], [0, sy, hip * (1 - sy)], [0, 0, 1]]))
            img = body
        S = np.array([[1, 0, 0], [0, 1 + br, -h * br], [0, 0, 1]])
        self.paste(f, img, M(bob) @ S)

    def render(self, t, shot, bloc):
        f = self.sea(self.img.copy(), t)
        R = shot.get("reglages", {})
        sc = R.get("scene")
        if sc == "arrivee":
            stop = bloc.t(R["arret"]); dur = R.get("duree", 3.2)
            u = float(np.clip((t - (stop - dur)) / dur, 0, 1))
            e = 1 - (1 - u) ** 1.6                                                      # ils ralentissent en arrivant
            walking = u < 1
            people = []
            for k, (name, (a, b), T) in enumerate((("mere_dos", self.MERE, 0.55), ("garcon_dos", self.GARCON, 0.42))):
                x, y, s = np.array(a) * (1 - e) + np.array(b) * e
                step = ((t - (stop - dur)) / T + 0.4 * k, 26 * s / 0.3 * (1 - e * 0.5)) if walking else None
                people.append((y, name, x, s, k, step))
            for y, name, x, s, k, step in sorted(people):
                self.figure(f, name, x, y, s, t, k, step)
        elif sc in ("accroupie", "garcon"):
            if sc == "accroupie":
                self.figure(f, "mere_accroupie", *self.ACCROUPIE, t, 0)
            self.figure(f, "garcon_dos", *self.GARCON[1], t, 1)
        elif sc == "fin":
            self.figure(f, "mere_accroupie", *self.ACCROUPIE, t, 0)
            self.figure(f, "garcon_dos", *self.GARCON[1], t, 1)
        return f
