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
    "ciel": ([1000, 430, 2.0], [1080, 380, 2.1]),
    "ecole": ([330, 1150, 2.65], [360, 1160, 2.8]),
    "restaurant": ([2470, 1080, 2.55], [2500, 1070, 2.7]),
    "lune": ([1760, 720, 1.5], [1900, 330, 2.6]),
}


class Rue:
    # nom, x du centre, y des pieds, échelle (de l'arrière vers l'avant)
    # nom, x du centre À L'ARRIVÉE, y des pieds, échelle, vitesse (px source/s), durée d'un pas (s),
    # jambes : [(y de la hanche, x de séparation, x min, x max), …] dans le dessin d'origine (une paire par personne)
    GENS = [("enf_gris", 262, 1302, 0.25, 95, 0.42, [(830, 197, 50, 320)]),
            ("enf_rayures", 66, 1328, 0.28, 95, 0.40, [(735, 166, 40, 305)]),
            ("enf_vert", 168, 1338, 0.28, 90, 0.38, [(722, 170, 65, 325)]),
            ("parent_fille", 372, 1350, 0.28, 85, 0.52, [(870, 222, 75, 420), (1060, 868, 730, 1017)])]
    MARCHE = 1.9                                               # durée de la marche vers le portail (s), finie à la fin du plan I
    CAR = (500, 1040, 860, 1470)                                # zone de la 2 CV garée devant l'école
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
        self.spr, self.legs = {}, {}
        for n, *_, jambes in self.GENS:                                                  # miroir : ils regardent le portail
            img = load_rgba(B03 / f"{n}.png")[:, ::-1].copy(); w = img.shape[1]
            body = img.copy(); legs = []
            for hip, sx, xa, xb in jambes:
                sx, xa, xb = w - sx, w - xb, w - xa
                for l0, l1 in ((xa, sx), (sx, xb)):
                    piece = np.zeros_like(img); piece[hip:, l0:l1] = img[hip:, l0:l1]
                    body[hip:, l0:l1, 3] = 0
                    legs.append((piece, hip, (l0 + l1) / 2, len(legs) % 2))
            self.spr[n], self.legs[n] = body, legs
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
        cx0, cy0, cx1, cy1 = self.CAR                                                      # la 2 CV devant le trottoir
        r = self.img[cy0:cy1, cx0:cx1]; lum = r.mean(2); sat = r.max(2) - r.min(2)
        m = cv2.morphologyEx(((lum < 150) & (sat < 40)).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
        poly = np.zeros_like(m); cv2.fillPoly(poly, [np.int32([(140, 30), (360, 30), (360, 312), (28, 302), (22, 170), (80, 138), (130, 58)])], 1)
        m &= poly
        n, lab, st, _ = cv2.connectedComponentsWithStats(m); m = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
        ff = m.copy(); hh_, ww_ = m.shape; cv2.floodFill(ff, np.zeros((hh_ + 2, ww_ + 2), np.uint8), (0, 0), 1); m |= 1 - ff
        self.carm = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)[..., None]

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

    def person(self, f, k, t, walk0):
        """Marche découpée : le corps avance et rebondit ; chaque jambe pivote à la hanche. Pendant l'appui, le pied
        reste fixe au sol (la jambe s'incline à mesure que la hanche avance) : aucun glissement. Pendant le pas,
        le pied repart vers l'avant en se levant."""
        name, cx, feet, s, v, T, _ = self.GENS[k]
        body = self.spr[name]; h, w = body.shape[:2]
        tw = np.clip(t - walk0, 0, self.MARCHE)                                         # temps de marche écoulé
        walking = 0 < t - walk0 < self.MARCHE
        x_now = cx + v * (self.MARCHE - tw)                                              # avance vers la gauche, arrive à cx
        S = v * T                                                                         # longueur d'un pas (px source)
        ph = (tw / T + 0.37 * k) if walking or tw > 0 else 0.37 * k                      # phase (en pas)
        br = 0.007 * np.sin(2 * np.pi * t / (3.2 + 0.41 * k) + k * 1.3)
        bob = 5 * s / 0.28 * abs(np.sin(np.pi * ph)) if walking else 0.0                 # le corps monte à chaque pas
        x = x_now - w * s / 2; y = feet - h * s - bob
        sh = np.zeros(f.shape[:2], np.float32)                                            # ombre de contact
        cv2.ellipse(sh, (int(x_now), int(feet - 5)), (int(w * s * 0.36), int(6 + 6 * s)), 0, 0, 360, 1, -1, cv2.LINE_AA)
        f *= 1 - cv2.GaussianBlur(sh, (0, 0), 4)[..., None] * 0.3
        Sb = np.array([[1, 0, 0], [0, 1 + br, -h * br], [0, 0, 1]])
        M = np.array([[s, 0, x], [0, s, y], [0, 0, 1]])
        for piece, hip, lx, side in self.legs[name]:                                     # jambes d'abord (derrière le corps)
            if walking:
                u = (ph / 2 + 0.5 * side) % 1.0                                           # cycle de 2 pas : 0–0,5 appui, 0,5–1 pas
                if u < 0.5:
                    o, lift = -S / 2 + S * (u / 0.5), 0.0                                 # pied fixe : décalage pied − hanche
                else:
                    q = (u - 0.5) / 0.5
                    o, lift = S / 2 - S * float(ease(q)), 10 * s / 0.28 * np.sin(np.pi * q)
            else:
                o, lift = 0.0, 0.0
            L = (h - hip) * s                                                             # longueur de la jambe (px source)
            sh_x = o / max(L, 1)                                                          # décalage du pied, en proportion
            sy = 1 - (lift + bob) / max(L, 1)                                             # le pied reste au sol / se lève
            A = M @ np.array([[1, sh_x, -sh_x * hip], [0, sy, hip * (1 - sy)], [0, 0, 1]])
            out, ox, oy = warp_local(piece, A[:2].astype(np.float32), f.shape)
            if out is not None:
                a = out[..., 3:4] / 255
                reg = f[oy:oy + out.shape[0], ox:ox + out.shape[1]]; reg[:] = reg * (1 - a) + out[..., :3] * a
        out, ox, oy = warp_local(body, (M @ Sb)[:2].astype(np.float32), f.shape)
        if out is not None:
            a = out[..., 3:4] / 255
            reg = f[oy:oy + out.shape[0], ox:ox + out.shape[1]]; reg[:] = reg * (1 - a) + out[..., :3] * a

    def plane(self, f, t, t0):
        """Avion de ligne qui monte, vu de côté (≈ 300 px à l'écran dans la vue « ciel ») ; traînées des deux réacteurs."""
        u = (t - t0) / 3.2
        if not -0.05 <= u <= 1.25:
            return
        p0, p1 = np.array([700.0, 440.0]), np.array([1650.0, 130.0])
        p = p0 + (p1 - p0) * u
        d = (p1 - p0) / np.linalg.norm(p1 - p0); n = np.array([d[1], -d[0]])            # n : « au-dessus » de l'avion
        L = 78                                                                            # demi-longueur du fuselage (px source)
        before = f.copy()                                                                  # l'avion reste derrière les toits
        trail = np.zeros(f.shape[:2], np.float32)                                          # deux traînées, qui s'élargissent et pâlissent
        for e in (-n * 9 - d * 12, -n * 4 - d * 30):
            for k in range(60):
                q = p + e - d * (L * 0.2 + k * 10)
                if np.dot(q - p0, d) < -40:
                    break
                cv2.circle(trail, (int(q[0]), int(q[1])), int(2 + k * 0.15), 1.0 - k / 60, -1, cv2.LINE_AA)
        trail = cv2.GaussianBlur(trail, (0, 0), 2.5)[..., None] * 0.5
        f[:] = f * (1 - trail) + 252 * trail
        P = lambda a, b: p + d * a + n * b  # noqa: E731
        WHITE, SHADE, LINE, WIN = (244, 246, 250), (196, 204, 216), (110, 120, 136), (70, 86, 110)
        far_wing = [P(10, 2), P(-16, 26), P(-28, 26), P(-14, 2)]                          # aile du côté opposé (derrière)
        tail_h = [P(-L + 8, 2), P(-L - 6, 14), P(-L - 14, 14), P(-L - 4, 2)]
        cv2.fillPoly(f, [np.int32(far_wing), np.int32(tail_h)], SHADE, cv2.LINE_AA)
        body = [P(L, -1), P(L - 6, 6), P(L - 18, 9), P(-L + 14, 9), P(-L, 4), P(-L - 4, -2), P(-L + 10, -9), P(L - 20, -9), P(L - 6, -7)]
        cv2.fillPoly(f, [np.int32(body)], WHITE, cv2.LINE_AA)
        belly = [P(L - 18, -9), P(-L + 10, -9), P(-L + 12, -5), P(L - 22, -5)]
        cv2.fillPoly(f, [np.int32(belly)], SHADE, cv2.LINE_AA)
        fin = [P(-L + 16, 8), P(-L - 2, 40), P(-L - 14, 40), P(-L - 2, 6)]                 # dérive
        cv2.fillPoly(f, [np.int32(fin)], WHITE, cv2.LINE_AA)
        cv2.polylines(f, [np.int32(fin)], True, LINE, 1, cv2.LINE_AA)
        wing = [P(14, -3), P(-22, -38), P(-36, -38), P(-12, -3)]                           # aile proche, vers le bas
        cv2.fillPoly(f, [np.int32(wing)], WHITE, cv2.LINE_AA)
        cv2.polylines(f, [np.int32(wing)], True, LINE, 1, cv2.LINE_AA)
        eng = P(-2, -20)                                                                    # réacteur sous l'aile
        cv2.ellipse(f, (int(eng[0]), int(eng[1])), (13, 6), float(np.degrees(np.arctan2(d[1], d[0]))), 0, 360, SHADE, -1, cv2.LINE_AA)
        cv2.polylines(f, [np.int32(body)], True, LINE, 1, cv2.LINE_AA)
        for k in range(14):                                                                 # hublots
            q = P(L - 26 - k * 9, 2)
            cv2.circle(f, (int(q[0]), int(q[1])), 2, WIN, -1, cv2.LINE_AA)
        cv2.fillPoly(f, [np.int32([P(L - 6, 1), P(L - 14, 6), P(L - 20, 4), P(L - 14, 0)])], WIN, cv2.LINE_AA)   # cockpit
        m = np.zeros(f.shape[:2], np.float32); m[:900] = self.sky[:900]
        f[:] = before + (f - before) * m[..., None]

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
            w0 = bloc.t(R["marche"]) if "marche" in R else -1e9
            for k in sorted(range(len(self.GENS)), key=lambda k: self.GENS[k][2]):     # du plus loin au plus proche
                self.person(f, k, t, w0)
            cx0, cy0, cx1, cy1 = self.CAR                                                 # la voiture passe devant eux
            reg = f[cy0:cy1, cx0:cx1]; reg[:] = reg * (1 - self.carm) + self.img[cy0:cy1, cx0:cx1] * self.carm
        return f

    def camera(self, t, shot):
        a, b = VUES[shot["reglages"]["vue"]]
        u = float(ease((t - shot["_t0"]) / max(0.1, shot["_t1"] - shot["_t0"])))
        return np.array(a, float) * (1 - u) + np.array(b, float) * u
