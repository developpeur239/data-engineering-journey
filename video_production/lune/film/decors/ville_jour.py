"""La ville le lendemain matin (bloc 3) : b03/rue_jour.png (même rue que le bloc 1, de jour, petite Lune pâle).

Réglage "vue" : large | ciel | ecole | restaurant | lune (cadrage par défaut si le plan n'a pas de "camera").
Tout ce qui bouge est en code : nuages clairs qui défilent, un avion qui monte (réglage "avion"), les enfants et le parent
devant le portail de l'école (calques détourés de b03/enfants.png, qui respirent), le rideau de fer du restaurant qui
remonte (réglage "rideau") et découvre une salle éclairée.
"""
from pathlib import Path

import cv2
import numpy as np

from decors.commun import CLOUD, load_rgb, load_rgba, warp_local
from moteur.core import ease

B03 = Path(__file__).resolve().parents[1] / "b03"

VUES = {                                                       # [x, y, zoom] au début → à la fin du plan
    "large": ([1376, 768, 1.0], [1376, 744, 1.06]),
    "ciel": ([1080, 380, 2.0], [1160, 340, 2.1]),
    "ecole": ([330, 1150, 2.65], [360, 1160, 2.8]),
    "restaurant": ([2470, 1080, 2.55], [2500, 1070, 2.7]),
    "lune": ([1760, 720, 1.5], [1900, 330, 2.6]),
}


class Rue:
    # nom, x du centre, y des pieds, échelle (de l'arrière vers l'avant)
    GENS = [("enf_gris", 262, 1302, 0.25), ("enf_rayures", 92, 1326, 0.28), ("parent_fille", 300, 1348, 0.28),
            ("enf_vert", 478, 1338, 0.28)]
    SH = (2478, 884, 2752, 1302)                               # rideau de fer du restaurant (x0, y0, x1, y1)

    def __init__(self, bloc):
        self.img = load_rgb(B03 / "rue_jour.png")
        h, w = self.img.shape[:2]
        r, g, b = (self.img[..., k] for k in range(3))
        yy = np.mgrid[0:h, 0:w][0]
        sky = (b > r + 25) & (b > 190) & (yy < 900)
        sky = cv2.morphologyEx(sky.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        self.sky = cv2.GaussianBlur(sky.astype(np.float32), (0, 0), 2)
        self.cloud = cv2.resize(CLOUD, (CLOUD.shape[1], 900))
        self.spr = {n: load_rgba(B03 / f"{n}.png")[:, ::-1].copy() for n, *_ in self.GENS}   # miroir : ils regardent le portail
        x0, y0, x1, y1 = self.SH
        reg = self.img[y0:y1, x0:x1]
        rr, gg, bb = reg[..., 0], reg[..., 1], reg[..., 2]
        lum = reg.mean(2)
        m = (lum > 92) & (lum < 240) & (bb - rr > -6) & (bb - rr < 40)            # lames du rideau (pas le lampadaire ni les chaises)
        m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
        self.shm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.2)[..., None]
        col = self.img[y0:y1, 2700:2716].mean(1, keepdims=True)                     # une colonne propre du rideau, répétée
        self.lames = np.repeat(col, x1 - x0, 1)
        self.salle = self._salle(x1 - x0, y1 - y0)

    @staticmethod
    def _salle(w, h):
        """L'intérieur du restaurant : salle chaude éclairée, suspensions, tables et chaises en silhouettes."""
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        f = np.zeros((h, w, 3), np.float32) + np.array([120, 84, 58], np.float32)
        f *= (0.75 + 0.35 * (1 - yy / h))[..., None]
        cv2.rectangle(f, (0, int(h * 0.62)), (w, h), (92, 62, 44), -1)                   # sol
        for k, x in enumerate((60, 170, 250)):
            cv2.line(f, (x, 0), (x, 70 + 10 * k), (60, 40, 30), 2, cv2.LINE_AA)            # suspensions
            g = np.exp(-((xx - x) ** 2 + (yy - 80 - 10 * k) ** 2) / 900.0)[..., None]
            f = f * (1 - g * 0.8) + np.array([255, 214, 150], np.float32) * g * 0.8
        for x in (40, 150, 240):                                                           # tables et chaises
            cv2.rectangle(f, (x, int(h * 0.58)), (x + 70, int(h * 0.6)), (70, 46, 34), -1)
            cv2.line(f, (x + 35, int(h * 0.6)), (x + 35, int(h * 0.78)), (70, 46, 34), 4)
            cv2.rectangle(f, (x - 18, int(h * 0.55)), (x - 12, int(h * 0.8)), (78, 52, 38), -1)
        return f

    def person(self, f, k, t):
        name, cx, feet, s = self.GENS[k]
        img = self.spr[name]; h, w = img.shape[:2]
        br = 0.007 * np.sin(2 * np.pi * t / (3.2 + 0.41 * k) + k * 1.3)                 # respiration
        sway = 0.4 * np.sin(2 * np.pi * t / (4.6 + 0.7 * k) + k)                          # léger balancement
        R = np.vstack([cv2.getRotationMatrix2D((w / 2, h), sway, 1.0), [0, 0, 1]])
        Sb = np.array([[1, 0, 0], [0, 1 + br, -h * br], [0, 0, 1]])
        x = cx - w * s / 2; y = feet - h * s
        sh = np.zeros(f.shape[:2], np.float32)                                            # ombre de contact
        cv2.ellipse(sh, (int(cx), int(feet)), (int(w * s * 0.42), int(12 + 8 * s)), 0, 0, 360, 1, -1, cv2.LINE_AA)
        sh = cv2.GaussianBlur(sh, (0, 0), 6)[..., None] * 0.35
        f *= 1 - sh
        A = (np.array([[s, 0, x], [0, s, y], [0, 0, 1]]) @ Sb @ R)[:2].astype(np.float32)
        out, ox, oy = warp_local(img, A, f.shape)
        if out is not None:
            a = out[..., 3:4] / 255
            reg = f[oy:oy + out.shape[0], ox:ox + out.shape[1]]; reg[:] = reg * (1 - a) + out[..., :3] * a

    def plane(self, f, t, t0):
        u = (t - t0) / 3.0
        if not 0 <= u <= 1.2:
            return
        p0, p1 = np.array([480.0, 640.0]), np.array([1700.0, 200.0])
        p = p0 + (p1 - p0) * u
        d = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([-d[1], d[0]])
        trail = np.zeros(f.shape[:2], np.float32)                                          # traînée qui s'élargit et pâlit
        for k in range(40):
            q = p - d * k * 9
            if np.dot(q - p0, d) < 0:
                break
            cv2.circle(trail, (int(q[0]), int(q[1])), int(2 + k * 0.12), 1.0 - k / 40, -1, cv2.LINE_AA)
        trail = cv2.GaussianBlur(trail, (0, 0), 2)[..., None] * 0.55
        f[:] = f * (1 - trail) + 252 * trail
        L = 34                                                                            # silhouette : fuselage, ailes, dérive
        body = [p + d * L, p + d * L * 0.7 + n * 3, p - d * L + n * 3, p - d * L - n * 3, p + d * L * 0.7 - n * 3]
        wing = [p + d * 6, p - d * 10 + n * 28, p - d * 16 + n * 28, p - d * 4, p - d * 16 - n * 26, p - d * 10 - n * 26]
        tail = [p - d * L * 0.8, p - d * L * 1.02 + n * 12, p - d * L * 1.08 + n * 12, p - d * L]
        for poly in (wing, body, tail):
            cv2.fillPoly(f, [np.int32(poly)], (236, 240, 246), cv2.LINE_AA)
        cv2.polylines(f, [np.int32(body)], True, (150, 160, 175), 1, cv2.LINE_AA)

    def shutter(self, f, t, t0):
        x0, y0, x1, y1 = self.SH; hh = y1 - y0
        u = float(ease((t - t0) / 1.5)) if t0 is not None else 0.0
        if u <= 0:
            return
        light = 0.55 + 0.45 * float(ease((t - t0 - 0.9) / 0.6))                        # la salle s'allume
        inside = self.salle * light
        off = int(u * hh * 0.97)
        lames = np.zeros_like(inside); lames[:hh - off] = self.lames[off:]                   # le rideau remonte et s'enroule
        cover = np.zeros((hh, x1 - x0, 1), np.float32); cover[:hh - off] = 1
        new = inside * (1 - cover) + lames * cover
        cv2.line(new, (0, hh - off), (x1 - x0, hh - off), (70, 76, 84), 3)                   # barre basse du rideau
        reg = f[y0:y1, x0:x1]; reg[:] = reg * (1 - self.shm) + new * self.shm

    def render(self, t, shot, bloc):
        R = shot.get("reglages", {})
        f = self.img.copy()
        xo = int(600 + 14 * t) % (self.cloud.shape[1] - f.shape[1])                         # voiles de nuages clairs
        c = self.cloud[:, xo:xo + f.shape[1]] * self.sky[:900] * 0.35
        f[:900] = f[:900] * (1 - c[..., None]) + 252 * c[..., None]
        if "avion" in R:
            self.plane(f, t, bloc.t(R["avion"]))
        self.shutter(f, t, bloc.t(R["rideau"]) if "rideau" in R else None)
        if R.get("vue") in ("ecole", "large"):
            for k in range(len(self.GENS)):
                self.person(f, k, t)
        return f

    def camera(self, t, shot):
        a, b = VUES[shot["reglages"]["vue"]]
        u = float(ease((t - shot["_t0"]) / max(0.1, shot["_t1"] - shot["_t0"])))
        return np.array(a, float) * (1 - u) + np.array(b, float) * u
