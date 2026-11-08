"""Schémas du bloc 3 « Le compte à rebours », tout en code (aucune image générée), même palette que decors/schemas.py.

  Chute      : l'orbite expliquée. mode "arret" (la vitesse latérale disparaît), "normal" (elle tombe autour de la
               Terre sans la toucher), "directe" (sans mouvement latéral, elle tombe droit sur nous).
  Calcul     : l'écran de calcul → « 4 j 20 h », barre « Durée de la chute », repère « déjà écoulé : 17 h », puis le
               temps restant avant le contact qui défile (4 j 2 h 46 à la détection, 22 h 14).
  Globe      : la Terre, ses lumières, « 8 milliards d'habitants ».
  Acceleration : la vitesse de chute mesurée heure après heure (elle augmente).
  Marees     : prévision de marée habituelle, puis recalculée (l'amplitude grandit, sans chiffres de hauteur).
  Influence  : la Lune soulève les océans (bourrelets de marée qui suivent la Lune).

Valeurs physiques (chute libre radiale depuis 384 400 km, GM Terre + Lune, contact à 4 j 19 h 36) :
  écoulé 16 h 50 → vitesse de chute 167 m/s, 5 000 km parcourus ; 20 h → 199 m/s ; 24 h → 240 m/s ; 27 h → 272 m/s.
Le compteur affiche toujours le temps RESTANT avant le contact (règle de montage, plan_rendu_v2 § 7.1 bis).
"""
import cv2
import numpy as np

from decors.schemas import DIM, GOLD, GREEN, INK, MONO, RED, SANS, canvas, earth, glow_dot, moon, texts
from moteur.core import H, W, ease, restant

DETECTION_RESTE = 4 * 86400 + 2 * 3600 + 46 * 60          # J0 22:14 → contact J5 01:00


def fade(t, a, d=0.35):
    return float(ease((t - a) / d))


def arrow(f, p, q, col, a=1.0, w=4):
    if a <= 0:
        return f
    over = f.copy()
    cv2.arrowedLine(over, tuple(np.int32(p)), tuple(np.int32(q)), col, w, cv2.LINE_AA, tipLength=0.2)
    return f * (1 - a) + over * a


def dashed(f, pts, col, a=1.0, on=2):
    """Pointillés fondus (a = opacité ; rien n'est tracé à 0, jamais de trait noir)."""
    if a <= 0.01:
        return f
    over = f.copy()
    for k in range(0, len(pts) - 1, on):
        cv2.line(over, tuple(np.int32(pts[k])), tuple(np.int32(pts[k + 1])), col, 2, cv2.LINE_AA)
    f[:] = f * (1 - a) + over * a
    return f


def panel(f, x0, y0, x1, y1, a=1.0):
    over = f.copy(); cv2.rectangle(over, (x0, y0), (x1, y1), (22, 32, 50), -1)
    cv2.rectangle(over, (x0, y0), (x1, y1), (58, 84, 118), 2, cv2.LINE_AA)
    return f * (1 - a) + over * a


# ------------------------------------------------------------------ l'orbite expliquée
class Chute:
    C, RO, E = np.array([960.0, 560.0]), 380, 0.62

    def __init__(self, bloc):
        pass

    def P(self, ang, r=1.0):
        return self.C + np.array([np.cos(ang), np.sin(ang) * self.E]) * self.RO * r

    def orbit(self, f, a=1.0):
        pts = [self.P(k / 160 * 2 * np.pi) for k in range(161)]
        dashed(f, pts, (70, 90, 120), a)

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items() if k != "mode"}
        mode = R["mode"]; f = canvas(); items = []
        if mode == "arret":                      # la Lune avance… sa flèche verte devient rouge, se brise, s'efface
            self.orbit(f)
            f = earth(f, tuple(self.C.astype(int)), 95, t)
            stop = T["arret"]
            ang = -0.6 + 0.16 * (min(t, stop) - shot["_t0"])
            pm = self.P(ang)
            tang = np.array([-np.sin(ang), np.cos(ang) * self.E]); tang /= np.linalg.norm(tang)
            hit = fade(t, stop, 0.15); gone = fade(t, stop + 0.5, 0.5)
            col = tuple(int(g * (1 - hit) + r * hit) for g, r in zip(GREEN, RED))
            f = arrow(f, pm, pm + tang * 170 * (1 - 0.6 * gone), col, 1 - gone)
            if t > stop:                         # éclat bref à l'arrêt
                f = glow_dot(f, pm, 40, (255, 230, 200), 0.6 * (1 - fade(t, stop, 0.5)))
            f = moon(f, tuple(pm.astype(int)), 34)
            items += [("vitesse orbitale", (pm[0] + 40, pm[1] - 110), SANS, 40, col, 1 - gone, False),
                      ("environ 1 km/s", (pm[0] + 40, pm[1] - 62), SANS, 34, col, (1 - gone) * fade(t, T["valeur"]), False),
                      ("0 km/s", (pm[0] + 40, pm[1] - 62), MONO, 40, RED, gone, False)]
        elif mode == "normal":                   # elle tombe en permanence… mais avance assez vite pour rater la Terre
            self.orbit(f, 0.7)
            f = earth(f, tuple(self.C.astype(int)), 95, t)
            ang = -1.9 + 0.33 * (t - shot["_t0"])
            pm = self.P(ang)
            for k in range(1, 40):               # sa trace : un arc qui fait le tour
                q = self.P(ang - k * 0.035); a = 0.8 * (1 - k / 40)
                cv2.circle(f, tuple(q.astype(int)), 3, tuple(int(v * a) for v in (160, 170, 190)), -1, cv2.LINE_AA)
            tang = np.array([-np.sin(ang), np.cos(ang) * self.E]); tang /= np.linalg.norm(tang)
            down = self.C - pm; down /= np.linalg.norm(down)
            f = arrow(f, pm, pm + tang * 150, GREEN, fade(t, T["vitesse"]))
            f = arrow(f, pm, pm + down * 110, RED, fade(t, T["tomber"]))
            f = moon(f, tuple(pm.astype(int)), 34)
            items += [("elle tombe…", (W / 2, 120), SANS, 50, RED, fade(t, T["tomber"]), True),
                      ("…mais avance assez vite pour toujours manquer la Terre", (W / 2, 190), SANS, 42, GREEN, fade(t, T["autour"]), True)]
        else:                                    # "directe" : plus de mouvement latéral, la Lune tombe droit
            self.orbit(f, 0.45)
            f = earth(f, tuple(self.C.astype(int)), 95, t)
            ang = -0.6 + 0.16 * 2.0
            p0 = self.P(ang)
            tang = np.array([-np.sin(ang), np.cos(ang) * self.E]); tang /= np.linalg.norm(tang)
            ghost = fade(t, shot["_t0"], 0.3) * (1 - fade(t, T["lateral"] + 0.6, 0.5))
            f = arrow(f, p0, p0 + tang * 150, (70, 140, 95), ghost)
            if ghost > 0.05:                     # la flèche latérale barrée
                c = p0 + tang * 75; nrm = np.array([-tang[1], tang[0]])
                x = fade(t, T["lateral"], 0.25) * ghost
                over = f.copy(); cv2.line(over, tuple(np.int32(c - nrm * 40 - tang * 30)), tuple(np.int32(c + nrm * 40 + tang * 30)), RED, 6, cv2.LINE_AA)
                f = f * (1 - x) + over * x
            fall = T["directement"]
            u = min(0.62, max(0.0, t - fall) ** 2 * 0.06)
            pm = p0 + (self.C - p0) * u
            line = fade(t, T["rien"], 0.5)
            dashed(f, [p0 + (self.C - p0) * (k / 40) * 0.78 for k in range(41)], (150, 70, 66), line)
            down = self.C - pm; down /= np.linalg.norm(down)
            f = arrow(f, pm, pm + down * 130, RED, fade(t, T["rien"]))
            f = moon(f, tuple(pm.astype(int)), 34)
            items += [("mouvement latéral", (p0[0] + 40, p0[1] - 110), SANS, 40, (110, 190, 140), ghost, False),
                      ("plus rien ne la retient", (W / 2, 120), SANS, 50, RED, fade(t, T["rien"]), True)]
        return texts(f, items)


# ------------------------------------------------------------------ l'écran de calcul : 4 j 20 h
class Calcul:
    LIGNES = ["distance Terre–Lune      384 399 km", "vitesse latérale         0,000 km/s",
              "attraction terrestre     0,0027 m/s²", "intégration de la chute  pas de 10 s",
              "…", "contact : surface terrestre atteinte"]

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas(grid=False)
        items = [("CALCUL DE TRAJECTOIRE · CALERN", (110, 150), SANS, 30, DIM, 1, False)]
        res = fade(t, T["resultat"], 0.3)
        f = panel(f, 90, 215, W - 90, 960)
        step = min(0.32, (T["resultat"] - T["calcul"]) / (len(self.LIGNES) + 0.5))
        n = int(np.clip((t - T["calcul"]) / step, 0, len(self.LIGNES)))         # les lignes défilent, finies avant « quatre »
        for k, ln in enumerate(self.LIGNES[:n]):
            items.append((ln, (160, 250 + 54 * k), MONO, 36, INK if k < 5 else GOLD, 1 - res, False))
        if n and n < len(self.LIGNES) and t < T["resultat"]:
            bw = int(1400 * min(1, (t - T["calcul"]) / (T["resultat"] - T["calcul"])))
            cv2.rectangle(f, (160, 600), (160 + bw, 616), (70, 110, 160), -1)
        if res > 0:                                                               # « Quatre jours et vingt heures »
            items.append(("4 j 20 h", (W / 2, 290 - 40 * (1 - res)), MONO, 170, RED, res, True))
        bar = fade(t, T["duree"], 0.5)
        if bar > 0:                                                               # la barre de la durée totale
            x0, x1, y = 200, W - 200, 660
            cv2.rectangle(f, (x0, y), (x1, y + 34), tuple(int(v * bar) for v in (40, 52, 72)), -1)
            done = x0 + (x1 - x0) * 16.83 / 115.6
            el = fade(t, T["ecoule"], 0.5)
            cv2.rectangle(f, (x0, y), (int(x0 + (done - x0) * el), y + 34), tuple(int(v * bar) for v in RED), -1)
            items += [("Durée totale de la chute : 4 j 20 h", (W / 2, y - 130), SANS, 46, INK, bar, True),
                      ("début de la chute", (x0, y + 50), SANS, 28, DIM, bar, False),
                      ("impact", (x1, y + 50), SANS, 28, RED, bar, True)]
            if el > 0:
                cv2.line(f, (int(done), y - 14), (int(done), y + 48), tuple(int(v * el) for v in GOLD), 3, cv2.LINE_AA)
                items.append(("déjà écoulé : 17 h", (done - 10, y - 50), SANS, 30, GOLD, el, False))
        rest = fade(t, T["reste"], 0.4)
        if rest > 0:                                                              # le compte à rebours démarre
            items += [("temps restant avant l'impact", (W / 2, 780), SANS, 34, DIM, rest, True),
                      (restant(DETECTION_RESTE - (t - T["reste"])), (W / 2, 830), MONO, 64, GOLD, rest, True)]
        return texts(f, items)


# ------------------------------------------------------------------ la Terre et ses huit milliards d'habitants
class Globe:
    C, R = (960, 600), 330

    def __init__(self, bloc):
        r = np.random.default_rng(11)
        pts = []                                                                  # lumières des villes (côté nuit)
        while len(pts) < 900:
            x, y = r.uniform(-1, 1, 2)
            if x * x + y * y < 0.96 and True:
                pts.append((x, y, r.uniform(0.3, 1), r.uniform(0, 6.28)))
        self.lights = np.array(pts)
        land = np.zeros((H, W, 3), np.float32); land = earth(land, self.C, self.R, 0.0)
        g = land[..., 1] - land[..., 2]                                            # vert des continents
        self.on = np.array([g[int(self.C[1] + y * self.R), int(self.C[0] + x * self.R)] > 10 for x, y, *_ in self.lights])

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas(grid=False)
        rng = np.random.default_rng(4)
        for x, y, b in rng.random((220, 3)):                                      # étoiles
            cv2.circle(f, (int(x * W), int(y * H)), 1, tuple(int(60 + 120 * b) for _ in range(3)), -1)
        f = earth(f, self.C, self.R, 0.0)                                         # immobile : les lumières restent sur les terres
        yy, xx = np.mgrid[0:H, 0:W]                                               # terminateur : la moitié droite dans la nuit
        d = ((xx - self.C[0]) ** 2 + (yy - self.C[1]) ** 2) <= self.R ** 2
        night = np.clip((xx - self.C[0] + 230) / 200, 0, 1) * d * 0.66
        f = f * (1 - night[..., None])
        li = fade(t, T["habitants"], 0.8)
        for x, y, b, ph in self.lights[self.on]:
            if x > -0.45:
                a = li * b * (0.75 + 0.25 * np.sin(t * 2 + ph)) * np.clip((x + 0.45) / 0.3, 0, 1)
                p = (int(self.C[0] + x * self.R), int(self.C[1] + y * self.R))
                if a > 0.02:
                    cv2.circle(f, p, 2, tuple(float(v * a + f[p[1], p[0], k] * (1 - a)) for k, v in enumerate(GOLD)), -1, cv2.LINE_AA)
        f = moon(f, (1700, 220), 26)
        n = int(8_000_000_000 * min(1, max(0, t - T["habitants"]) / 1.4))
        items = [("moins de 5 jours", (W / 2, 70), SANS, 56, RED, fade(t, T["jours"]), True),
                 (f"{n:,}".replace(",", " "), (W / 2, 935), MONO, 76, INK, li, True),
                 ("habitants", (W / 2, 1022), SANS, 34, DIM, li, True)]
        return texts(f, items)


# ------------------------------------------------------------------ la chute s'accélère
class Acceleration:
    MES = [(16.83, 167), (18.5, 182), (20.0, 199), (22.0, 220), (24.0, 240), (26.0, 261), (27.0, 272)]

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        x0, y0, x1, y1 = 260, 260, 1700, 860
        X = lambda h: x0 + (x1 - x0) * h / 30  # noqa: E731
        Y = lambda v: y1 - (y1 - y0) * v / 320  # noqa: E731
        cv2.line(f, (x0, y1), (x1, y1), (90, 110, 140), 2, cv2.LINE_AA); cv2.line(f, (x0, y0), (x0, y1), (90, 110, 140), 2, cv2.LINE_AA)
        items = [("VITESSE DE CHUTE DE LA LUNE · MESURES", (110, 150), SANS, 30, DIM, 1, False),
                 ("vitesse (m/s)", (x0 + 24, y0 - 20), SANS, 30, DIM, 1, False),
                 ("heures depuis le début de la chute", (W / 2, y1 + 64), SANS, 30, DIM, 1, True)]
        for h in (0, 10, 20, 30):
            items.append((f"{h} h", (X(h), y1 + 16), MONO, 26, DIM, 1, True))
        hs = np.linspace(0, 16.83, 60)                                            # avant la détection : calculé, en pointillés
        dashed(f, [(X(h), Y(9.92 * h)) for h in hs], (110, 80, 80))
        items.append(("avant la détection (calculé)", (X(1), Y(150) - 20), SANS, 26, (130, 110, 110), 1, False))
        a, b = T["mesures"], T["accelere"]
        k = int(np.clip((t - a) / max(0.3, (b - a)) * len(self.MES), 0, len(self.MES)))
        pts = self.MES[:max(k, 0)]
        if len(pts) > 1:
            cv2.polylines(f, [np.int32([(X(h), Y(v)) for h, v in pts])], False, (150, 70, 66), 3, cv2.LINE_AA)
        for h, v in pts:
            f = glow_dot(f, (X(h), Y(v)), 10, RED)
        if pts:
            h, v = pts[-1]
            items.append((f"{v} m/s", (X(h) + 24, Y(v) - 60), MONO, 46, RED, 1, False))
        items.append(("elle accélère", (W / 2, 990), SANS, 52, RED, fade(t, b), True))
        return texts(f, items)


# ------------------------------------------------------------------ les prévisions de marée recalculées
class Marees:
    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        x0, x1, ym = 200, 1720, 600
        items = [("PRÉVISIONS DE MARÉE · CÔTE MÉDITERRANÉENNE", (110, 150), SANS, 30, DIM, 1, False),
                 ("niveau de la mer", (x0, 290), SANS, 30, DIM, 1, False)]
        cv2.line(f, (x0, ym), (x1, ym), (60, 78, 104), 1, cv2.LINE_AA)
        for k, lab in enumerate(("J1", "J2", "J3", "J4")):
            items.append((lab, (x0 + (x1 - x0) * (k + 0.5) / 4, 900), MONO, 30, DIM, 1, True))
        xs = np.linspace(0, 1, 500); per = 4 * 1.93                               # deux marées par jour, sur quatre jours
        base = np.sin(xs * per * 2 * np.pi)
        P = lambda amp: np.stack([x0 + (x1 - x0) * xs, ym - amp * base], 1)  # noqa: E731
        cv2.polylines(f, [np.int32(P(np.full_like(xs, 70)))], False, (90, 120, 160), 3, cv2.LINE_AA)
        cv2.line(f, (x1 - 420, 250), (x1 - 360, 250), (90, 120, 160), 3, cv2.LINE_AA)
        items.append(("prévision habituelle", (x1 - 340, 232), SANS, 30, (120, 150, 190), 1, False))
        g = ease((t - T["recalcul"]) / 2.2)
        if g > 0:                                                                 # la nouvelle prévision se dessine
            n = max(2, int(500 * g))
            amp = 70 * (1 + 2.6 * xs[:n] ** 2.2)
            pts = P(np.pad(amp, (0, 500 - n), mode="edge"))[:n]
            cv2.polylines(f, [np.int32(pts)], False, RED, 3, cv2.LINE_AA)
            f = glow_dot(f, pts[-1], 8, RED)
            nv = fade(t, T["recalcul"] + 0.6)
            over = f.copy(); cv2.line(over, (x1 - 420, 300), (x1 - 360, 300), RED, 3, cv2.LINE_AA); f = f * (1 - nv) + over * nv
            items.append(("nouvelle prévision", (x1 - 340, 282), SANS, 30, RED, nv, False))
        if int(t * 2.5) % 2 and t < T["recalcul"] + 2.2:
            items.append(("recalcul en cours…", (W - 470, 150), SANS, 30, GOLD, 1, False))
        return texts(f, items)


# ------------------------------------------------------------------ l'influence de la Lune sur les océans
class Influence:
    C, R = np.array([760.0, 560.0]), 230

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        mang = 0.12 * np.sin(t * 0.25)                                             # la Lune glisse un peu ; les bourrelets la suivent
        mp = self.C + np.array([np.cos(mang), np.sin(mang)]) * 820
        b = fade(t, T["oceans"], 1.2) * (1 + 0.05 * np.sin(t * 1.3))
        if b > 0:                                                                  # l'océan soulevé, des deux côtés
            over = f.copy()
            cv2.ellipse(over, tuple(self.C.astype(int)), (int(self.R * (1 + 0.3 * b)), int(self.R * (1 - 0.02 * b))),
                        np.degrees(mang), 0, 360, (60, 120, 190), -1, cv2.LINE_AA)
            cv2.ellipse(over, tuple(self.C.astype(int)), (int(self.R * (1 + 0.3 * b)), int(self.R * (1 - 0.02 * b))),
                        np.degrees(mang), 0, 360, (130, 190, 250), 2, cv2.LINE_AA)
            f = f * 0.5 + over * 0.5
        f = earth(f, tuple(self.C.astype(int)), self.R, t)
        f = moon(f, tuple(mp.astype(int)), 60)
        lines = fade(t, T["influence"], 0.6)
        for k in range(-3, 4):                                                     # lignes d'attraction vers la Lune
            y = k * 46
            p = (int(mp[0] - 80), int(mp[1] + y * 0.5)); q = (int(self.C[0] + self.R + 90), int(self.C[1] + y))
            dashed(f, [np.array(p) + (np.array(q) - np.array(p)) * (j / 30) for j in range(31)], (140, 150, 170), lines * 0.8)
        items = [("depuis des milliards d'années, la Lune soulève les océans", (W / 2, 900), SANS, 44, INK, fade(t, T["milliards"], 0.5), True),
                 ("marée", (self.C[0] + self.R + 30, self.C[1] - 190), SANS, 38, (140, 190, 240), b, False)]
        return texts(f, items)
