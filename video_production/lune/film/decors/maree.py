"""Schémas du bloc 4 « Le premier jour », en code (aucune image générée), palette de decors/schemas.py.

  Maregraphe   : marée observée et marée prévue au marégraphe de Nice ; d'abord superposées (« rythme familier »),
                 puis un faible écart apparaît (réglage "ecart"), signalé en rouge.
  Differentiel : l'attraction de la Lune n'est pas la même partout : forte du côté de la Lune, moyenne au centre,
                 faible du côté opposé ; la différence étire les océans (deux bourrelets).
  Rapproche    : la Lune se rapproche, les bourrelets grandissent (aucun chiffre : une force n'est pas une hauteur d'eau).

Ordre de grandeur honnête : 24 h après le début de la chute, la Lune est à 374 000 km ; la force de marée n'a augmenté
que d'environ 8 % (384 400 / 374 100)³. Sur la marée de Nice (quelques dizaines de cm), l'écart est de l'ordre de 2 cm.
"""
import cv2
import numpy as np

from decors.compte import arrow, dashed, fade
from decors.schemas import DIM, GOLD, INK, MONO, RED, SANS, canvas, earth, glow_dot, moon, texts
from moteur.core import W, ease

OCEAN = (60, 120, 190)


def bulge(f, c, r, k, ang=0.0, a=1.0):
    """Les océans étirés vers la Lune et à l'opposé (k : étirement relatif)."""
    if a <= 0:
        return f
    over = f.copy()
    ax = (int(r * (1 + k)), int(r * (1 - 0.08 * k)))
    cv2.ellipse(over, tuple(int(v) for v in c), ax, np.degrees(ang), 0, 360, OCEAN, -1, cv2.LINE_AA)
    cv2.ellipse(over, tuple(int(v) for v in c), ax, np.degrees(ang), 0, 360, (130, 190, 250), 2, cv2.LINE_AA)
    return f * (1 - 0.55 * a) + over * 0.55 * a


class Maregraphe:
    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        x0, x1, ym, A = 200, 1720, 600, 150
        items = [("MARÉGRAPHE · PORT DE NICE", (110, 150), SANS, 30, DIM, 1, False),
                 ("hauteur d'eau", (x0, 330), SANS, 30, DIM, 1, False),
                 ("dernières 48 h", (x1 - 210, 880), SANS, 28, DIM, 1, False)]
        cv2.line(f, (x0, ym), (x1, ym), (60, 78, 104), 1, cv2.LINE_AA)
        xs = np.linspace(0, 1, 600)
        draw = float(np.clip((t - shot["_t0"]) / 2.0, 0.05, 1))                          # le tracé avance
        n = max(2, int(600 * draw))
        prev = np.stack([x0 + (x1 - x0) * xs, ym - A * np.sin(xs * 4 * 2 * np.pi)], 1)
        dashed(f, list(prev), (120, 150, 190), 1.0, on=3)
        e = fade(t, T.get("ecart", 1e9), 1.2)
        drift = e * 0.10 * np.clip((xs - 0.55) / 0.45, 0, 1) ** 1.5                       # l'écart grandit à la fin
        obs = np.stack([x0 + (x1 - x0) * xs, ym - A * (1 + drift) * np.sin(xs * 4 * 2 * np.pi + drift * 0.6)], 1)[:n]
        cv2.polylines(f, [np.int32(obs)], False, (230, 236, 244), 3, cv2.LINE_AA)
        f = glow_dot(f, obs[-1], 8, (230, 236, 244))
        cv2.line(f, (x1 - 420, 250), (x1 - 360, 250), (120, 150, 190), 2, cv2.LINE_AA)
        cv2.line(f, (x1 - 420, 292), (x1 - 360, 292), (230, 236, 244), 3, cv2.LINE_AA)
        items += [("prévision", (x1 - 340, 232), SANS, 30, (140, 165, 200), 1, False),
                  ("mesure", (x1 - 340, 274), SANS, 30, INK, 1, False)]
        if e > 0:
            bx = int(x0 + (x1 - x0) * 0.78)
            over = f.copy(); cv2.rectangle(over, (bx, 400), (x1, 800), (90, 34, 34), -1)
            f = f * (1 - 0.25 * e) + over * 0.25 * e
            items += [("écart : + 2 cm", (bx - 30 - 330, 760), MONO, 40, RED, e, False),
                      ("hors des prévisions", (bx - 30 - 330, 812), SANS, 30, RED, e, False)]
        return texts(f, items)


class Differentiel:
    C, R, M = np.array([700.0, 560.0]), 220, np.array([1650.0, 560.0])

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        b = fade(t, T["oceans"], 1.0)
        f = bulge(f, self.C, self.R, 0.28 * b * (1 + 0.04 * np.sin(t * 1.4)), 0, b)
        f = earth(f, tuple(self.C.astype(int)), self.R, t)
        f = moon(f, tuple(self.M.astype(int)), 70)
        items = [("Lune", (self.M[0], self.M[1] + 95), SANS, 40, DIM, 1, True)]
        pts = [("plus forte", self.C + [self.R, 0], 210, 0.0),                           # trois flèches vers la Lune
               ("moyenne", self.C, 140, 0.35), ("plus faible", self.C - [self.R, 0], 85, 0.7)]
        for k, (lab, p, L, dl) in enumerate(pts):
            a = fade(t, T["fleches"] + dl, 0.4)
            f = arrow(f, p, p + [L, 0], GOLD, a, 6)
            f = glow_dot(f, p, 7, GOLD, a)
            y = p[1] - 64 if k != 1 else p[1] + 30
            items.append((lab, (p[0] + L / 2, y), SANS, 34, GOLD, a, True))
        items.append(("cette différence étire les océans", (W / 2, 900), SANS, 50, (140, 190, 240), b, True))
        return texts(f, items)


class Rapproche:
    C, R = np.array([620.0, 560.0]), 200

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        u = float(ease((t - T["rapproche"]) / 3.0))
        mx = 1720 - 620 * u                                                              # la Lune avance vers la Terre
        k = 0.12 + 0.42 * u ** 2                                                         # l'effet croît très vite
        f = bulge(f, self.C, self.R, k * (1 + 0.03 * np.sin(t * 1.6)), 0, 1.0)
        f = earth(f, tuple(self.C.astype(int)), self.R, t)
        f = moon(f, (int(mx), 560), int(60 + 22 * u))
        for j in range(1, 6):                                                            # trajet déjà parcouru
            q = (int(mx + j * 40), 560)
            cv2.circle(f, q, 3, tuple(int(v * (1 - j / 6)) for v in (150, 160, 180)), -1, cv2.LINE_AA)
        items = [("plus elle se rapproche…", (W / 2, 120), SANS, 50, INK, fade(t, T["rapproche"]), True),
                 ("…plus l'effet est puissant", (W / 2, 190), SANS, 50, RED, fade(t, T["puissant"]), True)]
        return texts(f, items)
