"""Schémas et écrans en code (1920×1080, aucune image générée) : Laser (aller-retour Terre–Lune), Ecran (télémétrie
de Calern : mesures, confirmation, graphique de l'écart), Orbite (la Lune quitte son orbite et tombe).

Palette du film (nuit bleue), chiffres en Fragment Mono, textes en Instrument Sans. Chaque apparition est ancrée sur un
mot de la voix (shot["reglages"]). Valeurs physiques cohérentes : 384 000 km, ≈ 2,5 s aller-retour ; chute libre de la
Lune vers la Terre (a ≈ 0,0027 m/s²) → 5 m après 1 min, 122 m après 5 min, 486 m après 10 min ; écart en temps = 2·d/c.
"""
import cv2
import numpy as np
from PIL import Image, ImageDraw

from moteur.core import H, W, ease, font

BG = np.array([13, 19, 30], np.float32)
INK = (214, 222, 232); DIM = (120, 136, 156); GREEN = (110, 255, 150); RED = (255, 110, 96); GOLD = (244, 200, 110)
MONO, SANS = "FragmentMono-Regular.ttf", "InstrumentSans-Bold.ttf"


def canvas(grid=True):
    f = np.zeros((H, W, 3), np.float32); f[:] = BG
    if grid:
        for x in range(0, W, 80):
            cv2.line(f, (x, 0), (x, H), (19, 27, 41), 1)
        for y in range(0, H, 80):
            cv2.line(f, (0, y), (W, y), (19, 27, 41), 1)
    yy, xx = np.mgrid[0:H, 0:W]
    v = 1 - 0.35 * np.clip(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2 - 0.2, 0, 1)
    return f * v[..., None]


def texts(f, items):
    """items : (texte, (x, y), police, taille, couleur, opacité, centré)"""
    im = Image.fromarray(np.clip(f, 0, 255).astype(np.uint8)); layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for txt, (x, y), fn, size, col, al, center in items:
        if al <= 0:
            continue
        fo = font(fn, size)
        if center:
            bb = d.textbbox((0, 0), txt, font=fo); x -= (bb[2] - bb[0]) / 2
        d.text((x, y), txt, font=fo, fill=(*col, int(255 * min(1, al))))
    im = Image.alpha_composite(im.convert("RGBA"), layer).convert("RGB")
    return np.asarray(im).astype(np.float32)


def glow_dot(f, p, r, col, a=1.0):
    m = np.zeros((H, W), np.float32)
    cv2.circle(m, (int(p[0]), int(p[1])), int(r), 1, -1, cv2.LINE_AA)
    g = cv2.GaussianBlur(m, (0, 0), r * 1.6) * 1.4
    al = np.clip(m + g, 0, 1)[..., None] * a
    return f * (1 - al) + np.array(col, np.float32) * al


def earth(f, c, r, t):
    cv2.circle(f, c, r, (38, 84, 150), -1, cv2.LINE_AA)
    rng = np.random.default_rng(1)
    for k in range(7):                                              # continents stylisés qui tournent lentement
        ang = rng.uniform(0, 2 * np.pi) + t * 0.05; rr = rng.uniform(0.2, 0.75) * r
        p = (int(c[0] + rr * np.cos(ang)), int(c[1] + rr * np.sin(ang) * 0.8))
        cv2.ellipse(f, p, (int(r * rng.uniform(0.15, 0.3)), int(r * rng.uniform(0.1, 0.2))), rng.uniform(0, 180), 0, 360, (70, 128, 96), -1, cv2.LINE_AA)
    m = np.zeros((H, W), np.float32); cv2.circle(m, c, r, 1, -1, cv2.LINE_AA)
    f *= (1 - (1 - m) * 0)[..., None]
    out = np.zeros((H, W), np.float32); cv2.circle(out, c, r + 3, 1, 3, cv2.LINE_AA)
    out = cv2.GaussianBlur(out, (0, 0), 6)[..., None] * 0.9
    return f * (1 - out) + np.array([120, 180, 255], np.float32) * out


def moon(f, c, r):
    cv2.circle(f, c, r, (168, 170, 176), -1, cv2.LINE_AA)
    for dx, dy, rr in ((-0.3, -0.2, 0.18), (0.25, 0.1, 0.22), (-0.05, 0.4, 0.12), (0.35, -0.35, 0.1)):
        cv2.circle(f, (int(c[0] + dx * r), int(c[1] + dy * r)), int(rr * r), (138, 140, 148), -1, cv2.LINE_AA)
    return f


# ------------------------------------------------------------------ l'aller-retour du laser
class Laser:
    E, M = (330, 560), (1580, 540)

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        f = earth(f, self.E, 175, t); f = moon(f, self.M, 100)
        e0 = np.array([self.E[0] + 177, self.E[1] - 10.0]); m0 = np.array([self.M[0] - 100, self.M[1] - 4.0])
        items = [("Terre", (self.E[0], self.E[1] + 200), SANS, 46, DIM, 1, True), ("Lune", (self.M[0], self.M[1] + 125), SANS, 46, DIM, 1, True),
                 ("Calern", (e0[0] - 20, e0[1] - 80), SANS, 40, INK, ease((t - T["depart"] + 1.2) / 0.4), True)]
        glow = ease((t - T["distance"]) / 0.5)                                    # la distance
        if glow > 0:
            for x in range(int(e0[0]) + 20, int(m0[0]) - 20, 26):
                cv2.line(f, (x, 720), (x + 12, 720), tuple(int(v * glow) for v in (70, 90, 120)), 2, cv2.LINE_AA)
            items.append(("384 000 km", ((e0[0] + m0[0]) / 2, 740), MONO, 52, INK, glow, True))
        rf = ease((t - T["reflecteur"]) / 0.4)                                    # le réflecteur sur la Lune
        if rf > 0:
            cv2.rectangle(f, (int(m0[0]) + 4, int(m0[1]) - 13), (int(m0[0]) + 28, int(m0[1]) + 13), tuple(int(v * rf) for v in GOLD), -1)
            items.append(("réflecteur", (m0[0] + 12, m0[1] - 150), SANS, 40, GOLD, rf, True))
        a, mid, b = T["depart"], T["arrivee"], T["retour"]                       # l'impulsion : aller puis retour
        if t >= a:
            if t < mid:
                u = (t - a) / (mid - a); p = e0 + (m0 - e0) * u; trail = [e0 + (m0 - e0) * max(0, u - k * 0.012) for k in range(12)]
            elif t < b:
                u = (t - mid) / (b - mid); p = m0 + (e0 - m0) * u; trail = [m0 + (e0 - m0) * max(0, u - k * 0.012) for k in range(12)]
            else:
                p, trail = None, []
            if t < mid:
                cv2.line(f, tuple(e0.astype(int)), tuple(p.astype(int)), (40, 110, 70), 2, cv2.LINE_AA)
            elif t < b:
                cv2.line(f, tuple(e0.astype(int)), tuple(m0.astype(int)), (30, 80, 52), 2, cv2.LINE_AA)
            for k, q in enumerate(trail):
                f = glow_dot(f, q, 9 - k * 0.55, GREEN, 0.5 * (1 - k / 12))
            if p is not None:
                f = glow_dot(f, p, 12, GREEN)
            items.append(("aller  →", ((e0[0] + m0[0]) / 2, 450), SANS, 44, GREEN, ease((t - a) / 0.3) * (1 - ease((t - mid) / 0.3)), True))
            items.append(("←  retour", ((e0[0] + m0[0]) / 2, 450), SANS, 44, GREEN, ease((t - mid) / 0.3) * (1 - ease((t - b - 1.5) / 0.4)), True))
            u = np.clip((t - a) / (b - a), 0, 1) * 2.5                           # le chronomètre : 0 → 2,50 s pile sur « demie »
            items.append((f"{u:.2f} s".replace(".", ","), (W / 2, 150), MONO, 92, GOLD if t >= b else INK, 1, True))
        ar = ease((t - T["aller_retour"]) / 0.4)
        if ar > 0:
            items.append(("aller-retour : environ 2,5 secondes", (W / 2, 890), SANS, 54, GOLD, ar, True))
        return texts(f, items)


# ------------------------------------------------------------------ l'écran de télémétrie
class Ecran:
    def __init__(self, bloc):
        pass

    def panel(self, f, x0, y0, x1, y1, a=1.0):
        over = f.copy(); cv2.rectangle(over, (x0, y0), (x1, y1), (22, 32, 50), -1)
        cv2.rectangle(over, (x0, y0), (x1, y1), (58, 84, 118), 2, cv2.LINE_AA)
        return f * (1 - a) + over * a

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items() if k != "vue"}
        f = canvas(grid=False)
        items = [("TÉLÉMÉTRIE LASER-LUNE · CALERN", (90, 118), SANS, 30, DIM, 1, False),
                 ("EN DIRECT", (W - 290, 118), SANS, 28, RED, 1, False)]
        if int(t * 2) % 2:                                                          # voyant qui clignote
            cv2.circle(f, (W - 316, 136), 9, RED, -1, cv2.LINE_AA)
        vue = R["vue"]
        if vue in ("mesure", "mesure2"):
            f = self.panel(f, 90, 190, W - 90, 950)
            items += [("Temps aller-retour attendu", (160, 230), SANS, 38, DIM, 1, False),
                      ("2,509 431 20 s", (160, 290), MONO, 96, INK, 1, False)]
            m = T["mesure"]
            if t >= m:                                                             # la mesure s'affiche chiffre par chiffre
                full = "2,509 431 17 s"; n = int(np.clip((t - m) / 0.6, 0, 1) * len(full))
                items += [("Temps mesuré", (160, 470), SANS, 38, DIM, 1, False), (full[:n], (160, 530), MONO, 96, INK, 1, False)]
            e = T.get("ecart", 1e9)
            ea = ease((t - e) / 0.3)
            if ea > 0:
                over = f.copy(); cv2.rectangle(over, (150, 525), (1100, 650), (90, 34, 34), -1); f = f * (1 - 0.35 * ea) + over * 0.35 * ea
                items += [("écart : − 0,033 µs   (5 m plus près)", (160, 700), MONO, 48, RED, ea, False)]
            if vue == "mesure2":
                r2 = ease((t - T["mesure2"]) / 0.3)
                items += [("mesure n° 2 :  2,509 431 16 s   écart − 0,040 µs", (160, 800), MONO, 40, RED, r2, False)]
        elif vue == "confirmation":
            f = self.panel(f, 90, 190, W - 90, 950)
            items += [("Mesure n° 1   écart − 0,033 µs", (160, 230), MONO, 44, RED, 1, False),
                      ("Mesure n° 2   écart − 0,040 µs", (160, 300), MONO, 44, RED, 1, False)]
            c = ease((t - T["message"]) / 0.35)
            if c > 0:
                y = 450 + 40 * (1 - c)
                f = self.panel(f, 260, int(y), W - 260, int(y) + 300, c)
                items += [("Station laser partenaire", (330, y + 40), SANS, 40, DIM, c, False),
                          ("Même écart mesuré.", (330, y + 105), SANS, 64, INK, c, False),
                          ("CONFIRMÉ", (330, y + 195), MONO, 60, GOLD, ease((t - T["confirme"]) / 0.3), False)]
            p = ease((t - T["panne"]) / 0.3)
            items += [("Instruments : OK   ·   Horloge : OK   ·   Réflecteur : OK", (W / 2, 860), SANS, 36, GREEN, p, True)]
        elif vue == "graphe":
            x0, y0, x1, y1 = 260, 220, 1700, 900                                    # écart (m) en fonction du temps (min)
            cv2.line(f, (x0, y1), (x1, y1), (90, 110, 140), 2, cv2.LINE_AA); cv2.line(f, (x0, y0), (x0, y1), (90, 110, 140), 2, cv2.LINE_AA)
            items += [("temps depuis la première mesure", (x1 - 560, y1 + 30), SANS, 30, DIM, 1, False),
                      ("écart (m)", (x0 - 10, y0 - 60), SANS, 30, DIM, 1, False)]
            X = lambda m: x0 + (x1 - x0) * m / 11  # noqa: E731
            Y = lambda d: y1 - (y1 - y0) * d / 520  # noqa: E731
            for mm in (0, 1, 5, 10):
                items.append((f"{mm} min", (X(mm), y1 + 70), MONO, 26, DIM, 1, True))
            g = ease((t - T["courbe"]) / 2.5)                                      # la courbe de chute se dessine
            if g > 0:
                ts = np.linspace(0, 11 * g, 120)
                pts = np.stack([X(ts), Y(0.5 * 0.0027 * (ts * 60) ** 2)], 1).astype(np.int32)
                cv2.polylines(f, [pts], False, (120, 70, 66), 3, cv2.LINE_AA)
            for k, (mm, d, key) in enumerate(((1, 4.9, "p1"), (5, 122, "p2"), (10, 486, "p3"))):
                a = ease((t - T[key]) / 0.3)
                if a > 0:
                    f = glow_dot(f, (X(mm), Y(d)), 11, RED, a)
                    items.append((f"{d:g} m".replace(".", ","), (X(mm) + 26, Y(d) - 58), MONO, 44, RED, a, False))
        return texts(f, items)


# ------------------------------------------------------------------ l'orbite
class Orbite:
    C, RO = (960, 560), 360

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        for k in range(120):                                                       # l'orbite habituelle, en pointillés
            a0 = k / 120 * 2 * np.pi
            if k % 2 == 0:
                p0 = (int(self.C[0] + self.RO * np.cos(a0)), int(self.C[1] + self.RO * np.sin(a0) * 0.62))
                p1 = (int(self.C[0] + self.RO * np.cos(a0 + 0.04)), int(self.C[1] + self.RO * np.sin(a0 + 0.04) * 0.62))
                cv2.line(f, p0, p1, (70, 90, 120), 2, cv2.LINE_AA)
        f = earth(f, self.C, 95, t)
        stop, fall = T["arret"], T["chute"]
        ang = -0.5 + 0.22 * (min(t, stop) - (stop - 6))                            # la Lune avance sur son orbite…
        pm = np.array([self.C[0] + self.RO * np.cos(ang), self.C[1] + self.RO * np.sin(ang) * 0.62])
        if t > fall:                                                               # … puis tombe droit vers la Terre
            u = (t - fall) ** 2 * 0.045
            pm = pm + (np.array(self.C, float) - pm) * min(u, 0.55)
            for k in range(1, 16):
                q = pm + (pm - np.array(self.C, float)) * k * 0.02
                cv2.circle(f, (int(q[0]), int(q[1])), 2, (120, 130, 150), -1, cv2.LINE_AA)
        va = 1 - ease((t - stop) / 0.5)                                            # la vitesse orbitale disparaît
        if va > 0:
            tang = np.array([-np.sin(ang), np.cos(ang) * 0.62]); tang /= np.linalg.norm(tang)
            q = pm + tang * 150
            cv2.arrowedLine(f, tuple(pm.astype(int)), tuple(q.astype(int)), tuple(int(v * va) for v in GREEN), 4, cv2.LINE_AA, tipLength=0.2)
        if t > fall:
            dirv = np.array(self.C, float) - pm; dirv /= np.linalg.norm(dirv)
            q = pm + dirv * 130
            cv2.arrowedLine(f, tuple(pm.astype(int)), tuple(q.astype(int)), RED, 4, cv2.LINE_AA, tipLength=0.22)
        f = moon(f, (int(pm[0]), int(pm[1])), 34)
        items = [("orbite habituelle", (self.C[0] + self.RO - 40, self.C[1] - 290), SANS, 42, DIM, 1 - ease((t - fall) / 0.6) * 0.6, True),
                 ("vitesse orbitale", (pm[0] + 40, pm[1] - 100), SANS, 38, GREEN, va * ease((t - T["orbite"]) / 0.3), False),
                 ("chute", (pm[0] - 190, pm[1] + 40), SANS, 46, RED, ease((t - fall) / 0.4), False)]
        return texts(f, items)
