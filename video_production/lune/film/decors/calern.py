"""Décors de Calern : Exterieur (nuit, laser vers la Lune) et Poste (Léa à son bureau, vue de profil).

Poste reprend tel quel le système validé au test (test_lea/build.py) : corps de l'image validée avec SA chaise,
avant-bras articulé au coude, mains par remplacement (5 dessins), un seul contour fin. Ses actions sont décrites dans
shots.json → "lea" (temps = ancres) et restent continues d'un plan à l'autre :
  "frappe": [[de, a], …]        périodes où elle tape
  "telephone": {"vibre": t, "prise": t}   le téléphone vibre, elle le prend, le lève et le garde en main
  "regard_ecran": [[de, a], …]  elle lève les yeux vers son écran
"""
from pathlib import Path

import cv2
import numpy as np

from decors.commun import load_rgb
from moteur.core import ease, taps
from test_lea import build as TL

ASSETS = Path(__file__).resolve().parents[1]


class Exterieur:
    """L'observatoire la nuit ; réglage « laser » (début) : faisceau vert de la coupole à la Lune, impulsions qui montent."""
    SLIT, MOON = np.array([985.0, 470.0]), np.array([2296.0, 326.0])

    def __init__(self, bloc):
        self.img = load_rgb(ASSETS / "b02/calern_exterieur.png")
        rng = np.random.default_rng(2)
        self.stars = rng.random((160, 3)) * [2752, 900, 1]

    def render(self, t, shot, bloc):
        f = self.img.copy()
        for x, y, p in self.stars:                                       # quelques étoiles scintillent
            k = 0.5 + 0.5 * np.sin(t * (1.5 + 2 * p) + p * 30)
            if k > 0.85:
                cv2.circle(f, (int(x), int(y)), 2, (230, 238, 255), -1, cv2.LINE_AA)
        las = shot.get("reglages", {}).get("laser")
        if las:
            a = bloc.t(las)
            on = float(ease((t - a) / 0.25))
            if on > 0:
                beam = np.zeros(f.shape[:2], np.float32)
                cv2.line(beam, tuple(self.SLIT.astype(int)), tuple(self.MOON.astype(int)), 1.0, 3, cv2.LINE_AA)
                glow = cv2.GaussianBlur(beam, (0, 0), 9) * 2.2
                core = beam * 0.9
                pul = np.zeros_like(beam)
                L = self.MOON - self.SLIT
                for k in range(6):                                       # impulsions qui partent vers la Lune
                    u = ((t - a) * 0.55 - k / 6) % 1.0
                    p0 = self.SLIT + L * u; p1 = self.SLIT + L * max(0.0, u - 0.035)
                    cv2.line(pul, tuple(p1.astype(int)), tuple(p0.astype(int)), 1.0, 7, cv2.LINE_AA)
                pul = cv2.GaussianBlur(pul, (0, 0), 4) * 1.6
                al = np.clip((glow * 0.45 + core + pul) * on, 0, 1)[..., None]
                f = f * (1 - al) + np.array([110, 255, 150], np.float32) * al
                halo = np.zeros(f.shape[:2], np.float32)
                cv2.circle(halo, tuple(self.SLIT.astype(int)), 40, 1, -1)
                halo = cv2.GaussianBlur(halo, (0, 0), 30)[..., None] * 0.5 * on
                f = f * (1 - halo) + np.array([120, 255, 160], np.float32) * halo
        return f


class Poste:
    """Léa à son poste (profil) ; actions continues sur tout le bloc, lues dans shots.json → "lea"."""

    def __init__(self, bloc):
        L = bloc.data.get("lea", {})
        self.frappe = [(bloc.t(a), bloc.t(b)) for a, b in L.get("frappe", [])]
        self.taps = taps(self.frappe)
        tel = L.get("telephone")
        self.vibre = bloc.t(tel["vibre"]) if tel and tel.get("vibre") else 1e9
        g = bloc.t(tel["prise"]) if tel else 1e9
        self.T_STOP, self.T_GRAB, self.T_LIFT, self.T_HOLD = g - 0.6, g, g + 0.3, g + 1.1
        self.regard = [(bloc.t(a), bloc.t(b)) for a, b in L.get("regard_ecran", [])]
        self.blinks = [bloc.t(x) for x in L.get("clignements", [])]

    def typing(self, t):
        return any(a <= t < b for a, b in self.frappe)

    def arm(self, t):
        G, D = TL.GRAB_ANG, TL.GRAB_DX
        if t < self.T_STOP:
            if self.typing(t):
                k = sum(1 for a in self.taps if a <= t)
                near = min((abs(t - a) for a in self.taps), default=1)
                press = np.exp(-(near / 0.045) ** 2)
                return -1.5 + 1.6 * press + 0.8 * np.sin(t * 1.7), ("frappe_index" if k % 2 == 0 else "frappe_majeur"), 40 + 10 * np.sin(t * 0.9)
            return -2.0 + 0.4 * np.sin(t * 1.1), "frappe_index", 40 + 10 * np.sin(t * 0.9)            # mains posées, immobiles
        if t < self.T_GRAB:
            u = ease((t - self.T_STOP) / (self.T_GRAB - self.T_STOP))
            arc = -6.0 * np.sin(np.pi * u)                                       # la main se soulève pendant le trajet
            return -1.5 + (G + 1.5) * u + arc, "main_ouverte", (40 + 10 * np.sin(self.T_STOP * 0.9)) * (1 - u) + D * u
        if t < self.T_LIFT:
            return G, "prise_tel", D
        if t < self.T_HOLD:
            u = ease((t - self.T_LIFT) / (self.T_HOLD - self.T_LIFT))
            return G + (-30.0 - G) * u, ("prise_tel" if u < 0.5 else "tel_tenu"), D * (1 - u) + 10 * u
        return -30.0 + 1.0 * np.sin(t * 2.1), "tel_tenu", 10

    def cels(self, t, half=0.06):
        """Dessin(s) de main à l'instant t : fondu de 0,12 s centré sur chaque changement de pose."""
        c0, c1 = self.arm(t - half)[1], self.arm(t + half)[1]
        if c0 == c1 or {c0, c1} == {"prise_tel", "tel_tenu"}:                 # le téléphone ne se dédouble jamais : remplacement net
            return [(self.arm(t)[1], 1.0)]
        lo, hi = t - half, t + half                                           # instant exact du changement (dichotomie)
        for _ in range(12):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if self.arm(mid)[1] == c0 else (lo, mid)
        w = float(np.clip((t - hi) / (2 * half) + 0.5, 0, 1))
        return [(c0, 1 - w), (c1, w)]

    def lean(self, t):
        """Le buste se penche vers l'avant quand elle tend le bras vers le téléphone (degrés)."""
        u = ease((t - self.T_STOP) / (self.T_GRAB - self.T_STOP)) * (1 - ease((t - self.T_LIFT) / (self.T_HOLD - self.T_LIFT)))
        return 3.0 * u + 0.3 * np.sin(t * 0.8)

    def look(self, t):
        """Regard (décalage de l'œil, px natifs) et inclinaison de la tête : clavier → téléphone → écran."""
        base = (2, 10), 1.5                                                    # vers le clavier
        tp = min(self.vibre + 0.15, self.T_STOP - 0.3)                         # elle regarde le téléphone
        if t >= tp:
            u = ease((t - tp) / 0.3)
            base = (2 + 4 * u, 10 + 4 * u), 1.5 + 0.5 * u                      # vers le téléphone
        for a, b in self.regard:                                              # elle lève les yeux vers l'écran
            if a <= t:
                u = ease((t - a) / 0.45) * (1 - ease((t - b) / 0.45))
                (ex, ey), tl = base
                return (ex * (1 - u) + 9 * u, ey * (1 - u) - 7 * u), tl * (1 - u) - 2.5 * u
        return base

    def render(self, t, shot, bloc):
        T = TL
        f = T.deco.copy()
        if t < self.T_GRAB + 0.07:                                             # téléphone sur le bureau (sous la main pendant le fondu)
            ph = T.CELS["tel_seul"]; s = T.PHONE_S
            buzz = 2.5 * np.sin(t * 90) if self.vibre < t < self.vibre + 0.5 else 0.0
            sc = np.array([(T._sb[0] + T._sb[2]) / 2, (T._sb[1] + T._sb[3]) / 2])
            p = T.place(ph, s, T.PHONE_DESK[0] - sc[0] * s + buzz, T.PHONE_DESK[1] - sc[1] * s)
            a = p[..., 3:4] / 255; f = f * (1 - a) + p[..., :3] * a
            if t > self.vibre:
                glow = np.zeros(f.shape[:2], np.float32)
                cv2.ellipse(glow, (int(T.PHONE_DESK[0]), int(T.PHONE_DESK[1])), (int(T._pw * 0.5), 9), 0, 0, 360, 1, -1)
                glow = cv2.GaussianBlur(glow, (0, 0), 14)[..., None] * 0.9 * ease((t - self.vibre) / 0.2)
                f = f * (1 - glow) + np.array([190, 235, 255], np.float32) * glow
        br = 0.006 * np.sin(2 * np.pi * t / 3.6)
        (ex, ey), tilt = self.look(t)
        yyl = T.ly.astype(np.float32); xxl = T.lx.astype(np.float32)
        head = np.clip((760 - yyl) / 120, 0, 1)
        c, s_ = np.cos(np.radians(tilt * head)), np.sin(np.radians(tilt * head))
        px, py = 520.0, 760.0
        mx = px + (xxl - px) * c - (yyl - py) * s_
        my = py + (xxl - px) * s_ + (yyl - py) * c
        my = 1415 + (my - 1415) / (1 + br * (my < 1415))
        ln = np.radians(self.lean(t)); qx, qy = 500.0, 1415.0                  # pivot de l'inclinaison : l'assise
        up = (my < qy)
        rx = qx + (mx - qx) * np.cos(ln) - (my - qy) * np.sin(ln)
        ry = qy + (mx - qx) * np.sin(ln) + (my - qy) * np.cos(ln)
        mx, my = np.where(up, rx, mx).astype(np.float32), np.where(up, ry, my).astype(np.float32)
        body_img = cv2.remap(T.lea, mx, my, cv2.INTER_LINEAR)
        bmask = cv2.remap(T.body.astype(np.uint8), mx, my, cv2.INTER_NEAREST) > 0
        emask = cv2.remap(T.eye_m.astype(np.uint8), mx, my, cv2.INTER_NEAREST) > 0
        body_img[emask, :3] = 22
        moved = cv2.warpAffine(emask.astype(np.uint8), np.float32([[1, 0, ex], [0, 1, ey]]), (T.lw, T.lh), flags=cv2.INTER_NEAREST) > 0
        if not any(abs(t - b) < 0.06 for b in self.blinks):
            body_img[moved & bmask, :3] = 238
        B = T.place(np.dstack([body_img[..., :3], np.where(bmask, 255, 0).astype(np.float32)]), T.S, T.X0, T.Y0)
        CH = T.place(np.dstack([T.lea[..., :3], np.where(T.chair_m, 255, 0).astype(np.float32)]), T.S, T.X0, T.Y0)
        ang, _, dx = self.arm(t)
        a = np.radians(ang); d = np.array([np.cos(a), np.sin(a)])
        pv = np.array([T.X0 + 500 * T.S, T.Y0 + 1415 * T.S]); lr = np.radians(self.lean(t))
        e0 = T.ELBOW + np.array([0, -br * 300]) - pv
        el = pv + np.array([e0[0] * np.cos(lr) + e0[1] * np.sin(lr), -e0[0] * np.sin(lr) + e0[1] * np.cos(lr)])
        wrist = el + d * (T.FOREARM + dx)
        arm = np.zeros(f.shape[:2], np.uint8)
        cv2.line(arm, tuple((el * 4).astype(int)), tuple((wrist * 4).astype(int)), 1, 64, cv2.LINE_AA, 2)
        cv2.circle(arm, tuple((el * 4).astype(int)), 4 * 32, 1, -1, cv2.LINE_AA, 2)
        hand = np.zeros((f.shape[0], f.shape[1], 4), np.float32)
        for cel, w in self.cels(t):                                           # fondu entre deux dessins de main
            cimg, at = T.CELS[cel], T.ATT[cel]
            Mh = cv2.getRotationMatrix2D((float(at[0]), float(at[1])), -ang, T.CS); Mh[:, 2] += wrist - at
            hw = cv2.warpAffine(cimg, Mh, (f.shape[1], f.shape[0]), flags=cv2.INTER_LINEAR)
            hand[..., :3] += hw[..., :3] * (hw[..., 3:4] / 255) * w; hand[..., 3] += hw[..., 3] * w
        hand[..., :3] /= np.maximum(hand[..., 3:4] / 255, 1e-3); hand[..., 3] = np.clip(hand[..., 3], 0, 255)
        sil = (B[..., 3] > 128) | (arm > 0) | (hand[..., 3] > 128)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        ring = (cv2.dilate(sil.astype(np.uint8), k) > 0) & ~sil                 # contour discret : 2 px
        rim = sil & ~np.roll(sil, -6, axis=1)                                   # bord tourné vers l'écran (à droite)
        rim = cv2.GaussianBlur(rim.astype(np.float32), (0, 0), 1.2)
        ca = CH[..., 3:4] / 255; f = f * (1 - ca) + CH[..., :3] * ca
        sh = np.zeros(f.shape[:2], np.float32)
        cv2.ellipse(sh, (int(T.X0 + 420 * T.S), T.FLOOR + 4), (int(330 * T.S), 14), 0, 0, 360, 1, -1)
        f = f * (1 - cv2.GaussianBlur(sh, (0, 0), 10)[..., None] * 0.55)
        f[ring] = f[ring] * 0.62 + np.array([200, 210, 225], np.float32) * 0.38
        ba = B[..., 3:4] / 255; f = f * (1 - ba) + B[..., :3] * ba
        f[arm > 0] = (24, 24, 26)
        ha = hand[..., 3:4] / 255
        f = f * (1 - ha) + hand[..., :3] * ha
        r = (rim * 0.55)[..., None]                                            # liseré froid : la lumière de l'écran
        return f * (1 - r) + np.array([120, 185, 235], np.float32) * r
