"""Pièces articulées des personnages, tirées des images générées (aucune nouvelle génération).

Collègue : haut du corps (tête, torse, bras au café) + bras arrière (pivote à l'épaule) ; les jambes et les
chaussures sont reconstruites en formes noires et articulées (hanche, genou, cheville) pour une vraie marche.
Léa : sa chaise générée est retirée (elle s'assoit sur la chaise du décor), le contour blanc est refait.
Chaque pièce = masque de remplissage + couleurs ; le contour blanc est recalculé au rendu, comme sur les images.
"""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
IMG = HERE.parent / "images"
OUTLINE = 15                              # épaisseur du contour blanc, en pixels natifs (mesurée sur les images)
K = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * OUTLINE + 1, 2 * OUTLINE + 1))


def fill_holes(m):
    m = m.astype(np.uint8)
    h, w = m.shape
    ff = np.pad(m, 1).copy()
    cv2.floodFill(ff, np.zeros((h + 4, w + 4), np.uint8), (0, 0), 1)
    holes = ff[1:-1, 1:-1] == 0
    return (m > 0) | holes


def close(m, r):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE, k) > 0


class Canvas:
    """Toile RGBA de travail (résolution native) où l'on peint les pièces de l'arrière vers l'avant."""

    def __init__(self, w, h):
        self.rgb = np.zeros((h, w, 3), np.uint8); self.a = np.zeros((h, w), np.uint8)

    def paint(self, fill, rgb=None, no_outline=None):
        o = cv2.dilate(fill.astype(np.uint8), K) > 0
        if no_outline is not None:
            o &= ~no_outline
        self.rgb[o] = 255; self.a[o] = 255
        self.rgb[fill] = 0 if rgb is None else rgb[fill]; self.a[fill] = 255

    def rgba(self, scale):
        """Réduction antialiasée (alpha prémultiplié)."""
        h, w = self.a.shape
        size = (max(1, int(w * scale)), max(1, int(h * scale)))
        a = self.a.astype(np.float32) / 255
        pm = cv2.resize(self.rgb.astype(np.float32) * a[..., None], size, interpolation=cv2.INTER_AREA)
        aa = cv2.resize(a, size, interpolation=cv2.INTER_AREA)
        rgb = pm / np.maximum(aa[..., None], 1e-4)
        return np.dstack([np.clip(rgb, 0, 255), aa * 255]).astype(np.uint8)


# ---------------------------------------------------------------------------------------------- collègue
class Collegue:
    HIP_Y = 1300            # hauteur des hanches dans l'image native
    GROUND = 1885           # semelle
    L1, L2 = 272, 258       # cuisse, tibia
    W_HIP, W_KNEE, W_ANK = 172, 142, 112
    ANKLE_H = 78
    SHOULDER = (722, 832)   # pivot du bras arrière

    def __init__(self):
        a = np.array(Image.open(IMG / "collegue_marche_cut.png").convert("RGBA"))
        self.src = a[..., :3]
        lum = self.src.mean(2); blk = ((lum < 90) & (a[..., 3] > 128)).astype(np.uint8)
        n, lab, st, _ = cv2.connectedComponentsWithStats(blk, 8)
        back_leg = [i for i in range(1, n) if st[i, 1] > 1280 and st[i, 4] > 20000]
        back_arm = [i for i in range(1, n) if st[i, 0] > 630 and 700 < st[i, 1] < 1250 and st[i, 4] > 5000]
        arm = np.isin(lab, back_arm)
        body = (blk > 0) & ~arm & ~np.isin(lab, back_leg)
        yy = np.arange(a.shape[0])[:, None]
        body &= yy < self.HIP_Y
        self.upper = fill_holes(close(body, 17))
        cv2.ellipse(u := self.upper.astype(np.uint8), (448, self.HIP_Y - 8), (172, 62), 0, 0, 360, 1, -1)
        self.upper = u > 0
        self.arm = fill_holes(close(arm, 17))
        self.H, self.W = a.shape[:2]

    # --- marche
    @staticmethod
    def _ease(u):
        return u * u * (3 - 2 * u)

    def foot(self, t, P, S, off, hip_x0, v):
        """Position de la cheville (monde, x vers la gauche = avant) et angle du pied, pour une jambe."""
        STANCE = 0.62
        c = t / P + off
        k = np.floor(c); p = c - k
        t_strike = (k - off) * P                                  # instant du dernier appui talon
        x_plant = hip_x0 - v * t_strike - 0.32 * S                # pied posé devant la hanche
        g = self.GROUND - self.ANKLE_H
        toe = 150.0
        if p < STANCE:
            ang = 0.0
            if p < 0.07:                                          # attaque du talon, la pointe se pose
                ang = -12 * (1 - p / 0.07)
            ax, ay = x_plant, g - (abs(np.sin(np.radians(ang))) * 40)
            if p > 0.42:                                          # déroulé : le talon se lève, pivot sur la pointe
                q = (p - 0.42) / (STANCE - 0.42); ang = 28 * q
                tx = x_plant - toe
                ax = tx + toe * np.cos(np.radians(ang)); ay = g - toe * np.sin(np.radians(ang))
            return ax, ay, ang
        u = (p - STANCE) / (1 - STANCE); e = self._ease(u)
        x0 = x_plant - toe + toe * np.cos(np.radians(28)); y0 = g - toe * np.sin(np.radians(28))
        x1 = x_plant - S
        ax = x0 + (x1 - x0) * e
        ay = y0 + (g - y0) * e - 62 * np.sin(np.pi * u)
        ang = 28 * (1 - e) - 12 * e
        return ax, ay, ang

    def leg_mask(self, shape, hip, ank, ang):
        m = np.zeros(shape, np.uint8)
        hx, hy = hip; ax, ay = ank
        d = np.hypot(ax - hx, ay - hy); d = min(d, self.L1 + self.L2 - 1)
        base = np.arctan2(ay - hy, ax - hx)
        cosk = (self.L1 ** 2 + d ** 2 - self.L2 ** 2) / (2 * self.L1 * d)
        k = np.arccos(np.clip(cosk, -1, 1))
        th = base + k                                           # le genou part vers l'avant (x négatif)
        kx, ky = hx + self.L1 * np.cos(th), hy + self.L1 * np.sin(th)
        if kx > (hx + ax) / 2:
            th = base - k; kx, ky = hx + self.L1 * np.cos(th), hy + self.L1 * np.sin(th)

        def seg(p0, p1, w0, w1):
            v = np.array(p1) - np.array(p0); n = np.array([-v[1], v[0]]) / (np.linalg.norm(v) + 1e-9)
            poly = np.array([p0 + n * w0 / 2, p1 + n * w1 / 2, p1 - n * w1 / 2, p0 - n * w0 / 2])
            cv2.fillPoly(m, [np.round(poly * 4).astype(np.int32)], 1, cv2.LINE_AA, 2)
            cv2.circle(m, (int(p1[0] * 4), int(p1[1] * 4)), int(w1 * 2), 1, -1, cv2.LINE_AA, 2)

        H, K_, A_ = np.array([hx, hy]), np.array([kx, ky]), np.array([ax, ay])
        cv2.circle(m, (int(hx * 4), int(hy * 4)), int(self.W_HIP * 2), 1, -1, cv2.LINE_AA, 2)
        seg(H, K_, self.W_HIP, self.W_KNEE); seg(K_, A_, self.W_KNEE, self.W_ANK)
        # chaussure arrondie (comme sur l'image) : talon rond + avant-pied ovale, tournée de l'angle du pied
        r = np.radians(ang)
        R = np.array([[np.cos(r), np.sin(r)], [-np.sin(r), np.cos(r)]])   # rotation : angle > 0 = talon levé

        def P_(x, y):
            return A_ + R @ np.array([x, y])
        heel = P_(18, 38)
        cv2.circle(m, (int(heel[0] * 4), int(heel[1] * 4)), 4 * 44, 1, -1, cv2.LINE_AA, 2)
        toe = P_(-98, 34)
        cv2.ellipse(m, ((float(toe[0]), float(toe[1])), (2 * 96, 2 * 46), -np.degrees(r)), 1, -1, cv2.LINE_AA)
        mid = [P_(18, -6), P_(-60, -8), P_(-110, 80), P_(18, 82)]
        cv2.fillPoly(m, [np.round(np.array(mid) * 4).astype(np.int32)], 1, cv2.LINE_AA, 2)
        return m > 0, (toe, r)

    def frame(self, t, P, S, v, hip_x0, x_world):
        """Rend le collègue à l'instant t. Renvoie (rgba natif, position monde de la hanche)."""
        CW, CH = 1500, 2000
        dx, dy = 750 - 448, 40
        cv = Canvas(CW, CH)
        bob = 11 * np.cos(4 * np.pi * (t / P - 0.31))
        hipw = x_world                                               # hanche (monde, px natifs)
        # bras arrière : balancier opposé à la jambe arrière
        ang_arm = -13 * np.sin(2 * np.pi * (t / P) + np.pi / 2)
        lean = 2.0 + 0.8 * np.sin(4 * np.pi * t / P)

        def place(mask_or_img, rot, pivot, interp):
            M = cv2.getRotationMatrix2D(pivot, rot, 1.0); M[0, 2] += dx; M[1, 2] += dy - bob
            return cv2.warpAffine(mask_or_img, M, (CW, CH), flags=interp)

        piv_body = (448.0, float(self.HIP_Y))
        Mb = cv2.getRotationMatrix2D(piv_body, lean, 1.0)
        sh = Mb @ np.array([*self.SHOULDER, 1.0])
        Ma = cv2.getRotationMatrix2D(tuple(map(float, self.SHOULDER)), ang_arm + lean, 1.0)
        Ma[:, 2] += sh - np.array(self.SHOULDER)
        Ma[0, 2] += dx; Ma[1, 2] += dy - bob
        arm = cv2.warpAffine(self.arm.astype(np.uint8), Ma, (CW, CH), flags=cv2.INTER_NEAREST) > 0
        arm_rgb = cv2.warpAffine(self.src, Ma, (CW, CH), flags=cv2.INTER_LINEAR)
        up = place(self.upper.astype(np.uint8), lean, piv_body, cv2.INTER_NEAREST) > 0
        up_rgb = place(self.src, lean, piv_body, cv2.INTER_LINEAR)
        local = lambda X: X - hipw + 750                              # noqa: E731  (monde → toile)
        legs = []
        for name, off, hx in (("arriere", 0.5, 800), ("avant", 0.0, 700)):
            ax, ay, ang = self.foot(t, P, S, off, 0.0, v)
            ax = ax - (-v * t)                                        # relatif à la hanche
            hip = (hx, self.HIP_Y - 8 + dy - bob)
            ank = (ax + hx, ay + dy)
            legs.append(self.leg_mask((CH, CW), hip, ank, ang)[0])
        cv.paint(arm, arm_rgb)                                        # bras arrière
        cv.paint(legs[0])                                             # jambe arrière
        cv.paint(up, up_rgb)                                          # torse, tête, bras au café
        cv.paint(legs[1], no_outline=up)                              # jambe avant, fondue dans le bassin
        return cv


# ---------------------------------------------------------------------------------------------- Léa
class Lea:
    EYE = (644, 368, 684, 452)

    def __init__(self):
        a = np.array(Image.open(IMG / "lea_profil_cut.png").convert("RGBA"))
        h, w = a.shape[:2]
        yy, xx = np.mgrid[0:h, 0:w]
        rgb = a[..., :3].astype(np.int16)
        white = (rgb.min(2) > 200)
        solid = (a[..., 3] > 128) & ~white
        chair = ((xx < 152) & (yy > 760)) | ((yy > 1418) & (xx < 690))
        body = solid & ~chair
        n, lab, st, _ = cv2.connectedComponentsWithStats(body.astype(np.uint8), 8)
        keep = np.isin(lab, [i for i in range(1, n) if st[i, 4] > 3000])
        self.fill = fill_holes(close(keep, 13))
        self.src = a[..., :3].copy()
        self.H, self.W = h, w

    def frame(self, t):
        """Respiration, tête qui bouge à peine, mains qui tapent, clignement."""
        h, w = self.H, self.W
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        breath = 0.006 * np.sin(2 * np.pi * t / 3.6)
        my = 1415 + (yy - 1415) / (1 + breath * (yy < 1415))           # le haut du corps se soulève un peu
        head = np.clip((760 - yy) / 120, 0, 1)
        my -= head * 3 * np.sin(2 * np.pi * t / 2.9 + 0.7)
        mx = xx - head * 4 * np.sin(2 * np.pi * t / 4.1)
        hand = np.clip((xx - 760) / 110, 0, 1) * ((yy > 860) & (yy < 1090))
        tap = sum(np.exp(-((t - k) / 0.05) ** 2) for k in np.arange(0.15, 4.2, 0.23) if int(k * 13) % 5 != 0)
        my -= hand * 9 * tap
        mx_, my_ = mx.astype(np.float32), my.astype(np.float32)
        fill = cv2.remap(self.fill.astype(np.uint8), mx_, my_, cv2.INTER_NEAREST) > 0
        src = cv2.remap(self.src, mx_, my_, cv2.INTER_LINEAR)
        blink = any(abs(t - b) < 0.07 for b in (1.25, 3.3))
        if blink:
            x0, y0, x1, y1 = self.EYE; reg = src[y0:y1, x0:x1]; reg[reg.min(2) > 150] = (24, 24, 24)
        cv = Canvas(w, h)
        cv.paint(fill, src)
        return cv
