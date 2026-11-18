"""Décors des blocs 5 à 13 (tout en code sur des images déjà générées ; personnages au style de Léa).

  Voiture   : l'embouteillage du soir vu de la voiture (vitre latérale + garçon de profil / pare-brise + mère).
  Porte     : Calern la nuit, le collègue à la porte éclairée ; alarme (lumière rouge), lumières qui vacillent, départ.
  Seisme    : la rue sous la Lune géante (bloc 1) : la chaussée se soulève, une fissure court jusqu'à l'immeuble,
              un pan de façade tombe, poussière.
  Ecran2    : écrans de texte (rapport des gouvernements, ordre d'évacuation, message vocal, « Écouté »).
  Energie, Roche, Comete, Croute, Force, Carte, Recul : schémas.
"""
from pathlib import Path

import cv2
import numpy as np

from decors.astres import Lune, glow, paste_rgba, sphere
from decors.commun import dust, load_rgb, load_rgba, warp_local
from decors.compte import arrow, dashed, fade
from decors.schemas import DIM, GOLD, GREEN, INK, MONO, RED, SANS, canvas, earth, glow_dot, moon, texts
from moteur.core import H, W, ease

FILM = Path(__file__).resolve().parents[1]
LUNE = FILM.parent


def put(f, img, x, feet, s, t=0.0, k=0, shadow=True, opacity=1.0):
    """Un personnage (calque RGBA) posé par les pieds, qui respire."""
    h, w = img.shape[:2]
    br = 0.006 * np.sin(2 * np.pi * t / (3.3 + 0.5 * k) + k)
    if shadow:
        sh = np.zeros(f.shape[:2], np.float32)
        cv2.ellipse(sh, (int(x), int(feet - 3)), (int(w * s * 0.4), int(6 + 8 * s)), 0, 0, 360, 1, -1, cv2.LINE_AA)
        f *= 1 - cv2.GaussianBlur(sh, (0, 0), 4)[..., None] * 0.3 * opacity
    A = np.array([[s, 0, x - w * s / 2], [0, s, feet - h * s], [0, 0, 1]]) @ np.array([[1, 0, 0], [0, 1 + br, -h * br], [0, 0, 1]])
    out, ox, oy = warp_local(img, A[:2].astype(np.float32), f.shape)
    if out is not None:
        a = out[..., 3:4] / 255 * opacity
        reg = f[oy:oy + out.shape[0], ox:ox + out.shape[1]]; reg[:] = reg * (1 - a) + out[..., :3] * a
    return f


# ------------------------------------------------------------------ la voiture dans l'embouteillage
class Voiture:
    def __init__(self, bloc):
        self.img = load_rgb(FILM / "b05/embouteillage.png")
        self.garcon = load_rgba(FILM / "b04/garcon_profil.png")
        m = load_rgba(FILM / "b04/mere_accroupie.png")
        self.mere = m[: int(m.shape[0] * 0.52)].copy()                                # tête et épaules
        self.mere[-40:, :, 3] *= np.linspace(1, 0, 40)[:, None]

    def render(self, t, shot, bloc):
        R = shot["reglages"]; vue = R["vue"]
        f = self.img.copy()
        lr = R.get("lune_r", 40) * (1 + 0.01 * (t - shot["_t0"]))
        lx, ly = R.get("lune_xy", (1900, 330))
        a = fade(t, bloc.t(R["lune"]), 1.5) if "lune" in R else 1.0
        sky = np.zeros(f.shape[:2], np.float32); sky[:700] = 1
        f = glow(f, lx, ly, lr * 2, (120, 120, 150), 0.4 * a)
        paste_rgba(f, Lune.render(int(lr)), lx, ly, sky, opacity=a)
        for k in range(14):                                                            # feux arrière qui clignotent un peu
            rng = np.random.default_rng(k)
            x, y = rng.uniform(150, 2500), rng.uniform(820, 1050)
            if np.sin(t * rng.uniform(0.5, 1.5) + k) > 0.6:
                f = glow(f, x, y, 6, (255, 40, 30), 0.25)
        if vue == "garcon":                                                            # la vitre : cadre sombre arrondi
            fr = np.zeros(f.shape[:2], np.float32)
            cv2.rectangle(fr, (0, 0), (f.shape[1], f.shape[0]), 1, -1)
            win = np.zeros_like(fr)
            cv2.rectangle(win, (380, 180), (2380, 1290), 1, -1)
            win = cv2.GaussianBlur(win, (0, 0), 25)
            win = np.clip(win * 1.6 - 0.3, 0, 1)
            f = f * (0.92 + 0.08 * np.sin(t * 0.3))
            put(f, self.garcon, 560, 1700, 1.15, t, 1, shadow=False)                    # lui, au premier plan, regarde la Lune
            frame = (1 - win)[..., None]
            f = f * (1 - frame * 0.93) + np.array([14, 14, 20], np.float32) * frame * 0.93
            f[:, :] += np.array([20, 8, 30], np.float32) * 0.15
        else:                                                                          # la mère, de profil, au volant
            dash = np.zeros(f.shape[:2], np.float32); dash[1180:] = 1
            put(f, self.mere, 820, 1420, 1.5, t, 0, shadow=False)
            f = f * (1 - dash[..., None] * 0.9) + np.array([16, 16, 22], np.float32) * dash[..., None] * 0.9
        return f


# ------------------------------------------------------------------ Calern, la porte, le collègue
class Porte:
    IMG = "film2d/images/decor_calern_nuit.png"

    def __init__(self, bloc):
        self.img = load_rgb(LUNE / self.IMG)
        self.col = load_rgba(FILM / "b06/collegue.png")
        self.lea = load_rgba(FILM / "b06/lea_face.png")

    def render(self, t, shot, bloc):
        R = shot.get("reglages", {})
        if "image" in R:                                                                  # Calern de jour (retour à la réalité)
            if not hasattr(self, "_jour"):
                self._jour = load_rgb(LUNE / R["image"])
            f = self._jour.copy()
        else:
            f = self.img.copy()
        if "alarme" in R and t >= bloc.t(R["alarme"]):                                   # lumière rouge tournante
            ph = (t - bloc.t(R["alarme"])) * 1.6
            f = f * (0.78 + 0.08 * np.sin(ph * 2 * np.pi)) + np.array([90, 8, 4], np.float32) * (0.5 + 0.5 * np.sin(ph * 2 * np.pi))
        if "vacille" in R and t >= bloc.t(R["vacille"]):                                 # les lumières vacillent
            rng = np.random.default_rng(int(t * 12))
            f = f * (0.45 if rng.random() < 0.25 else 1.0)
        if R.get("collegue"):
            op = 1.0
            x = 360
            if "part" in R and t >= bloc.t(R["part"]):                                   # il s'en va : passe la porte
                u = (t - bloc.t(R["part"])) / 1.6
                x = 360 - 160 * u; op = float(np.clip(1 - u, 0, 1))
            cx, cy, cs = R.get("collegue_xy", (x, 1365, 0.30))
            put(f, self.col, cx if "collegue_xy" in R else x, cy, cs, t, 0, opacity=op)
        if R.get("lea"):                                                                   # Léa, de face, devant les écrans
            lx, ly, ls = R.get("lea_xy", (2330, 1450, 0.44))
            put(f, self.lea, lx, ly, ls, t, 1)
        dust(f, t, (100, 200, f.shape[1] - 100, f.shape[0] - 100), n=60, alpha=0.16)
        return f


# ------------------------------------------------------------------ la rue : la terre se déforme
class Seisme:
    CRACK = [(1480, 1530), (1330, 1440), (1180, 1420), (1010, 1330), (860, 1310), (700, 1260), (585, 1235)]
    CHUNK = [(600, 450), (700, 470), (735, 440), (860, 525), (840, 600), (885, 700), (790, 770), (720, 735), (610, 745)]

    def __init__(self, bloc):
        self.img = load_rgb(FILM / "b01/rue_lune.png")
        m = np.zeros(self.img.shape[:2], np.uint8)
        cv2.fillPoly(m, [np.int32(self.CHUNK)], 1)
        self.cm = m
        self.chunk = np.dstack([self.img, m.astype(np.float32) * 255])

    def render(self, t, shot, bloc):
        R = shot.get("reglages", {})
        f = self.img.copy()
        if "souleve" in R:                                                               # la chaussée se soulève (bosse)
            u = fade(t, bloc.t(R["souleve"]), 1.2)
            if u > 0:
                h, w = f.shape[:2]
                yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
                bump = 26 * u * np.exp(-(((xx - 1300) / 380) ** 2 + ((yy - 1420) / 90) ** 2))
                f = cv2.remap(f, xx, yy + bump, cv2.INTER_LINEAR)
        if "fissure" in R:
            p = float(np.clip((t - bloc.t(R["fissure"])) / R.get("duree_fissure", 3.0), 0, 1))
            pts = np.array(self.CRACK, float)
            seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))]; L = seg[-1] * p
            keep = [pts[0]]
            for i in range(1, len(pts)):
                if seg[i] <= L:
                    keep.append(pts[i])
                else:
                    u = (L - seg[i - 1]) / (seg[i] - seg[i - 1]); keep.append(pts[i - 1] + (pts[i] - pts[i - 1]) * u); break
            if len(keep) > 1:
                cv2.polylines(f, [np.int32(keep)], False, (12, 12, 16), 9, cv2.LINE_AA)
                cv2.polylines(f, [np.int32(keep) + [0, -4]], False, (120, 125, 140), 2, cv2.LINE_AA)
                for q in keep[1:-1:2]:                                                     # petites branches
                    cv2.line(f, tuple(np.int32(q)), tuple(np.int32(q + [40, 30])), (14, 14, 18), 4, cv2.LINE_AA)
        if "effondre" in R and t >= bloc.t(R["effondre"]):                              # un pan de façade tombe
            u = t - bloc.t(R["effondre"])
            hole = cv2.GaussianBlur(self.cm.astype(np.float32), (0, 0), 2)[..., None]   # le trou : intérieur sombre, gravats
            inner = f * 0.28 + np.array([10, 10, 14], np.float32)
            rng = np.random.default_rng(3)
            for _ in range(40):
                x, y = rng.integers(610, 870), rng.integers(450, 750)
                cv2.circle(inner, (int(x), int(y)), int(rng.integers(4, 16)), (55, 55, 62), -1)
            f = f * (1 - hole) + inner * hole
            dy = 0.5 * 2200 * u * u; rot = 25 * u
            if dy < 900:
                M = cv2.getRotationMatrix2D((740, 600), rot, 1.0); M[1, 2] += dy; M[0, 2] += 60 * u
                out, ox, oy = warp_local(self.chunk, M, f.shape)
                if out is not None:
                    a = out[..., 3:4] / 255
                    reg = f[oy:oy + out.shape[0], ox:ox + out.shape[1]]; reg[:] = reg * (1 - a) + out[..., :3] * a
            dcl = np.zeros(f.shape[:2], np.float32)                                         # nuage de poussière
            if u > 0.35:
                cv2.ellipse(dcl, (760, 1260), (int(250 + 300 * u), int(120 + 160 * u)), 0, 0, 360, 1, -1)
                dcl = cv2.GaussianBlur(dcl, (0, 0), 60)[..., None] * min(0.8, (u - 0.35) * 1.2) * max(0.0, 1 - (u - 3) / 3)
                f = f * (1 - dcl) + np.array([150, 150, 160], np.float32) * dcl
        dust(f, t, (40, 40, f.shape[1] - 40, f.shape[0] - 40), n=70, alpha=0.2)
        return f


# ------------------------------------------------------------------ écrans de texte
class Ecran2:
    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items() if k not in ("mode",)}
        f = canvas(grid=False); items = []; mode = R["mode"]
        t0 = shot["_t0"]
        if mode == "rapport":
            lignes = [("RAPPORT CONJOINT DES AGENCES SPATIALES", SANS, 40, DIM),
                      ("Trajectoire de la Lune : confirmée", SANS, 52, INK),
                      ("Contact avec la Terre : dans 2 j 19 h", SANS, 52, INK),
                      ("Moyen connu de l'empêcher : aucun", SANS, 60, RED)]
            for k, (txt, fn, sz, col) in enumerate(lignes):
                a = fade(t, T.get(f"l{k}", t0 + 0.4 * k), 0.4)
                items.append((txt, (160, 240 + 150 * k), fn, sz, col, a, False))
        elif mode == "evacuation":
            blink = 0.55 + 0.45 * np.sin(t * 6)
            over = f.copy(); cv2.rectangle(over, (90, 300), (W - 90, 780), (90, 20, 20), -1)
            f = f * (1 - 0.6) + over * 0.6
            items += [("PRÉFECTURE DES ALPES-MARITIMES", (W / 2, 350), SANS, 36, INK, 1, True),
                      ("ORDRE D'ÉVACUATION", (W / 2, 450), SANS, 110, (255, 120, 110), blink, True),
                      ("Observatoire de Calern · tout le personnel", (W / 2, 640), SANS, 44, INK, 1, True)]
        elif mode == "vocal":                                                         # message vocal (téléphone)
            cv2.rectangle(f, (700, 80), (1220, 1000), (18, 18, 22), -1)
            cv2.rectangle(f, (715, 120), (1205, 960), (10, 14, 24), -1)
            items += [("Camille", (960, 160), SANS, 40, INK, 1, True)]
            rec = T["rec"]; send = T.get("envoi", 1e9); lu = T.get("ecoute", 1e9)
            if t >= rec:
                k = min(t, send) - rec
                for i in range(int(min(30, k * 14))):                                   # forme d'onde qui avance
                    hh = 10 + 60 * abs(np.sin(i * 1.7) * np.sin(i * 0.43))
                    cv2.line(f, (760 + i * 14, int(560 - hh)), (760 + i * 14, int(560 + hh)), (230, 230, 240), 6, cv2.LINE_AA)
                if t < send:
                    f = glow_dot(f, (960, 820), 46, (230, 60, 50), 0.9 + 0.1 * np.sin(t * 8))
                    items.append((f"0:{int(k):02d}", (960, 680), MONO, 40, INK, 1, True))
            if t >= send:
                items += [("Message vocal envoyé", (960, 680), SANS, 36, DIM, 1, True)]
            if t >= lu:
                items += [("Écouté", (1180, 730), SANS, 36, (120, 200, 255), fade(t, lu, 0.3), False)]
        return texts(f, items)


# ------------------------------------------------------------------ schémas
class Energie:
    """Barres en échelle logarithmique : nos moyens face à l'énergie de mouvement de la Lune."""
    BARS = [("arsenal nucléaire mondial", 19.4, GOLD), ("tous les lanceurs spatiaux", 15.0, DIM),
            ("énergie de mouvement de la Lune", 28.9, RED)]

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas(); items = [("ÉNERGIE (joules, échelle logarithmique)", (110, 150), SANS, 30, DIM, 1, False)]
        x0, x1 = 160, 1760
        X = lambda e: x0 + (x1 - x0) * (e - 12) / 18  # noqa: E731
        for e in range(12, 31, 3):
            cv2.line(f, (int(X(e)), 820), (int(X(e)), 840), (90, 110, 140), 2)
            items.append((f"10^{e}", (X(e), 850), MONO, 24, DIM, 1, True))
        for k, (lab, e, col) in enumerate(self.BARS):
            key = ("nucleaire", "lanceurs", "lune")[k]
            a = fade(t, T[key], 0.4); g = float(ease((t - T[key]) / 1.2))
            y = 300 + 150 * k
            if a > 0:
                cv2.rectangle(f, (x0, y), (int(x0 + (X(e) - x0) * g), y + 70), col, -1)
                items.append((lab, (x0, y - 46), SANS, 36, col, a, False))
        items.append(("un milliard de fois plus", (W / 2, 940), SANS, 52, RED, fade(t, T["derisoire"]), True))
        return texts(f, items)


class Roche:
    """La Terre attire plus fort la face proche : près de la Terre, la Lune risque d'être disloquée (limite de Roche)."""
    E, ER = np.array([520.0, 560.0]), 230

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        lim = fade(t, T["limite"], 0.6)
        pts = [self.E + np.array([np.cos(a), np.sin(a)]) * 640 for a in np.linspace(-0.9, 0.9, 80)]
        dashed(f, pts, (170, 80, 70), lim)
        f = earth(f, tuple(self.E.astype(int)), self.ER, t)
        mx = 1500 - 260 * float(ease((t - shot["_t0"]) / 8))
        mc = np.array([mx, 560.0]); mr = 120
        paste_rgba(f, Lune.render(mr, fract=fade(t, T.get("fractures", 1e9), 2.0)), *mc)
        a = fade(t, T["fleches"], 0.4)
        f = arrow(f, mc - [mr, 0], mc - [mr + 170, 0], GOLD, a, 6)
        f = arrow(f, mc + [mr, 0], mc + [mr - 70, 0], GOLD, a, 6)
        items = [("face proche : tirée plus fort", (mc[0] - mr - 180, 400), SANS, 34, GOLD, a, True),
                 ("face éloignée : moins", (mc[0] + mr, 720), SANS, 34, GOLD, a, True),
                 ("limite de Roche", (self.E[0] + 640, 200), SANS, 40, (220, 120, 110), lim, True)]
        return texts(f, items)


class Comete:
    """Histoire réelle : la comète Shoemaker-Levy 9, fragmentée par Jupiter en 1992, ses fragments frappent Jupiter en 1994."""

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        f = canvas(grid=False)
        J, JR = (1300, 560), 300
        cv2.circle(f, J, JR, (190, 160, 120), -1, cv2.LINE_AA)
        for k, (dy, col) in enumerate(((-150, (160, 120, 90)), (-60, (210, 180, 140)), (20, (170, 130, 95)), (110, (200, 170, 130)), (190, (150, 115, 85)))):
            m = np.zeros(f.shape[:2], np.float32); cv2.circle(m, J, JR, 1, -1, cv2.LINE_AA)
            band = np.zeros_like(m); band[J[1] + dy - 25:J[1] + dy + 25] = 1
            band = cv2.GaussianBlur(band * m, (0, 0), 6)[..., None] * 0.6
            f = f * (1 - band) + np.array(col, np.float32) * band
        u = (t - shot["_t0"]) * 0.08
        for k in range(21):                                                                 # le « collier de perles »
            p = np.array([200 + k * 34 + u * 400, 300 + k * 6 + u * 120])
            f = glow_dot(f, p, 7, (230, 235, 245), 0.9)
            cv2.line(f, tuple(np.int32(p)), tuple(np.int32(p - [40, 12])), (120, 130, 150), 2, cv2.LINE_AA)
        items = [("Histoire réelle", (110, 140), SANS, 40, GOLD, 1, False),
                 ("Comète Shoemaker-Levy 9, déchirée par Jupiter en 1992 ; ses fragments frappent Jupiter en 1994", (110, 960), SANS, 32, INK, 1, False)]
        return texts(f, items)


class Croute:
    """Le sol aussi monte et descend avec la Lune (marées terrestres, quelques dizaines de centimètres)."""

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        b = fade(t, T["sol"], 1.0)
        over = f.copy()
        k = 0.08 * b * (1 + 0.3 * np.sin(t * 1.5))
        cv2.ellipse(over, (760, 560), (int(260 * (1 + k)), int(260 * (1 - k * 0.3))), 0, 0, 360, (150, 110, 80), -1, cv2.LINE_AA)
        f = f * 0.4 + over * 0.6
        f = earth(f, (760, 560), 260, t)
        paste_rgba(f, Lune.render(80), 1650, 560)
        items = [("la Terre n'est pas parfaitement rigide", (W / 2, 110), SANS, 48, INK, fade(t, T["rigide"]), True),
                 ("chaque jour, le sol monte et descend d'environ 30 cm", (W / 2, 930), SANS, 40, GOLD, b, True)]
        return texts(f, items)


class Force:
    """Force de marée : × 1 au début, × 75 à 6 h, × 940 à 1 h 30. Une force, jamais une hauteur."""

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas(); x0, y1 = 300, 860
        items = [("FORCE DE MARÉE (comparée au début de la chute)", (110, 150), SANS, 30, DIM, 1, False)]
        for k, (lab, val, key) in enumerate((("début de la chute", 1, "v1"), ("6 h avant", 75, "v75"), ("1 h 30 avant", 940, "v940"))):
            if key not in T:
                continue
            a = fade(t, T[key], 0.4); g = float(ease((t - T[key]) / 1.0))
            hgt = 560 * np.log10(val * 9 + 1) / np.log10(940 * 9 + 1) * g + 6
            x = x0 + k * 480
            cv2.rectangle(f, (x, int(y1 - hgt)), (x + 220, y1), RED if val > 1 else (90, 120, 160), -1)
            items += [(f"× {val}", (x + 110, y1 - hgt - 80), MONO, 56, INK, a, True), (lab, (x + 110, y1 + 20), SANS, 32, DIM, a, True)]
        if "hauteur" in T:
            items.append(("une force, pas une hauteur : le sol ne monte pas mille fois plus haut", (W / 2, 960), SANS, 36, GOLD, fade(t, T["hauteur"]), True))
        return texts(f, items)


class Carte:
    """Zones côtières évacuées (schéma, pas une carte réelle) : la côte, des zones rouges qui s'étendent."""

    def __init__(self, bloc):
        xs = np.linspace(0, W, 200)
        self.coast = np.stack([xs, 620 + 60 * np.sin(xs / 210) + 25 * np.sin(xs / 57)], 1)

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = np.zeros((H, W, 3), np.float32) + np.array([30, 60, 100], np.float32)
        land = np.int32(np.vstack([[[0, 0]], self.coast, [[W, 0]]]))
        cv2.fillPoly(f, [land], (52, 62, 58), cv2.LINE_AA)
        cv2.polylines(f, [np.int32(self.coast)], False, (140, 170, 200), 2, cv2.LINE_AA)
        u = float(ease((t - T["zones"]) / 4.0))
        band = np.zeros(f.shape[:2], np.float32)
        cv2.polylines(band, [np.int32(self.coast - [0, 40 * u])], False, 1, int(10 + 150 * u))
        band = cv2.GaussianBlur(band, (0, 0), 8)[..., None] * 0.55
        mask = np.zeros(f.shape[:2], np.float32); cv2.fillPoly(mask, [land], 1)
        band *= mask[..., None]
        f = f * (1 - band) + np.array([200, 50, 45], np.float32) * band
        for k, (x, nm) in enumerate(((330, "Marseille"), (980, "Toulon"), (1500, "Nice"))):
            y = int(np.interp(x, self.coast[:, 0], self.coast[:, 1]) - 30)
            cv2.circle(f, (x, y), 8, (230, 230, 235), -1, cv2.LINE_AA)
        items = [("Zones côtières évacuées", (110, 150), SANS, 40, INK, 1, False), ("schéma", (110, 205), SANS, 28, DIM, 1, False)]
        for x, nm in ((330, "Marseille"), (980, "Toulon"), (1500, "Nice")):
            items.append((nm, (x + 16, np.interp(x, self.coast[:, 0], self.coast[:, 1]) - 90), SANS, 30, INK, 1, False))
        return texts(f, items)


class Recul:
    """La Lune s'éloigne d'environ 3,8 cm par an (mesuré au laser depuis Calern et ailleurs)."""

    def __init__(self, bloc):
        pass

    def render(self, t, shot, bloc):
        R = shot["reglages"]; T = {k: bloc.t(v) for k, v in R.items()}
        f = canvas()
        f = earth(f, (420, 560), 200, t)
        u = float(ease((t - T["eloigne"]) / 3.0))
        mx = 1480 + 120 * u
        paste_rgba(f, Lune.render(80), mx, 560)
        f = arrow(f, (mx + 100, 560), (mx + 230, 560), GREEN, fade(t, T["eloigne"]), 5)
        items = [("+ 3,8 cm par an", (mx, 700), MONO, 56, GREEN, fade(t, T["eloigne"]), True),
                 ("elle s'éloigne", (W / 2, 900), SANS, 54, INK, fade(t, T.get("fin", 1e9)), True)]
        return texts(f, items)
