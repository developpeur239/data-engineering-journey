"""Insert 2D (Tesseract) : le téléphone de Léa à 05:25, vu de dessus. Le message de la sœur arrive, Léa tape
« J'arrive », hésite, puis efface. 5 s, 1920×1080, projet modifiable + MP4.

    python3 build_insert.py <dossier_neuf>

Style : aplats vectoriels, main en silhouette noire pure sans contour (elle se lit sur l'écran clair), interface en très
grand (3 ou 4 éléments), cône de lumière et vignettage pour l'ambiance. Polices : Instrument Sans (texte de l'interface).
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

TSRCT = str(Path.home() / ".local/share/Tesseract/bin/tsrct")
FONTS = Path(__file__).resolve().parents[1] / "prototype/fonts"
ROOT = Path(sys.argv[1])
DUR = 5000

A, _id = [], [0]


def nid():
    _id[0] += 1
    return _id[0]


def T(x=0.0, y=0.0, rot=0.0, s=100.0, op=100.0):
    return {"anchorPoint": [0, 0], "position": [x, y], "scale": [s, s], "rotation": rot, "opacity": op}


def rgb(h, a=1.0):
    h = h.lstrip("#"); return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [a]


def fill(h, a=1.0):
    return {"paint": {"type": "solid", "color": rgb(h, a)}, "fillRule": "nonZeroWinding", "blendMode": "normal", "opacity": 1}


def M(x, y): return {"type": "moveTo", "x": x, "y": y}
def L(x, y): return {"type": "lineTo", "x": x, "y": y}
def C(a, b, c, d, x, y): return {"type": "cubicTo", "c1x": a, "c1y": b, "c2x": c, "c2y": d, "x": x, "y": y}
def Z(): return {"type": "close"}


def rrect(x, y, w, h, r):
    k = 0.5523 * r; x1, y1 = x + w, y + h
    return [M(x + r, y), L(x1 - r, y), C(x1 - r + k, y, x1, y + r - k, x1, y + r), L(x1, y1 - r), C(x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1),
            L(x + r, y1), C(x + r - k, y1, x, y1 - r + k, x, y1 - r), L(x, y + r), C(x, y + r - k, x + r - k, y, x + r, y), Z()]


def ellipse(cx, cy, rx, ry):
    k = 0.5523
    return [M(cx + rx, cy), C(cx + rx, cy + k * ry, cx + k * rx, cy + ry, cx, cy + ry), C(cx - k * rx, cy + ry, cx - rx, cy + k * ry, cx - rx, cy),
            C(cx - rx, cy - k * ry, cx - k * rx, cy - ry, cx, cy - ry), C(cx + k * rx, cy - ry, cx + rx, cy - k * ry, cx + rx, cy), Z()]


PENSEE = False   # pensée de Léa pendant l'hésitation : ajout au texte V13, à valider avant de l'activer
_eid = [1000]


def grad(kind, start, end, stops):
    """Remplissage en dégradé ; stops : [(position 0..1, couleur hex, opacité)]."""
    return {"paint": {"type": "gradient", "gradientType": kind, "start": list(start), "end": list(end),
                      "stops": [{"offset": o, "color": rgb(c, a)} for o, c, a in stops]},
            "fillRule": "nonZeroWinding", "blendMode": "normal", "opacity": 1}


def blur(lid, px):
    _eid[0] += 1
    A.append({"type": "addFxLayerEffect", "compositionId": "main", "layerId": lid, "effectId": _eid[0], "effect": {"type": "gaussianBlur", "blurriness": px}})


def gshape(name, path, fill_, parent=None, start=0, dur=DUR):
    lid = nid()
    act = {"type": "createFxShapeLayer", "compositionId": "main", "layerId": lid, "name": name, "insertIndex": 0,
           "activeRange": {"start": start, "duration": dur}, "transform": T(), "shape": {"path": {"commands": path}, "fills": [fill_], "strokes": []}}
    if parent:
        act["parentLayerId"] = parent
    A.append(act); return lid


def shape(name, path, color, a=1.0, parent=None, start=0, dur=DUR, tr=None):
    lid = nid()
    act = {"type": "createFxShapeLayer", "compositionId": "main", "layerId": lid, "name": name, "insertIndex": 0,
           "activeRange": {"start": start, "duration": dur}, "transform": tr or T(),
           "shape": {"path": {"commands": path}, "fills": [fill(color, a)], "strokes": []}}
    if parent:
        act["parentLayerId"] = parent
    A.append(act); return lid


def group(name, tr, parent=None):
    lid = nid()
    act = {"type": "createFxGroupLayer", "compositionId": "main", "layerId": lid, "name": name, "insertIndex": 0,
           "activeRange": {"start": 0, "duration": DUR}, "transform": tr}
    if parent:
        act["parentLayerId"] = parent
    A.append(act); return lid


def text(name, x, y, s, size, color, font, parent=None, start=0, dur=DUR, just="left", a=1.0):
    lid = nid()
    act = {"type": "createFxTextLayer", "compositionId": "main", "insertIndex": 0, "layerId": lid, "name": name,
           "activeRange": {"start": start, "duration": dur}, "transform": T(x, y),
           "sourceText": {"text": s, "fontFamily": font[0], "fontStyle": font[1], "fontSize": size, "fillColor": rgb(color, a), "justification": just}}
    if parent:
        act["parentLayerId"] = parent
    A.append(act); return lid


def key(i, t, v, ease="smooth"):
    e = {"type": "cubicBezier", "x1": 0.3, "y1": 0, "x2": 0.2, "y2": 1} if ease == "smooth" else {"type": ease}
    return {"id": f"k{i}_{t}", "layerTime": int(t), "value": {"type": "float", "value": float(v)}, "easing": e}


def build(fr, fb):
    # ---------- décor : table en lames de bois, faisceau de la lampe, objets flous, vignettage ----------
    import random
    rnd = random.Random(7)
    shape("Bureau", rrect(0, 0, 1920, 1080, 0), "#26292e")
    y = -20
    while y < 1080:   # lames de largeurs et de tons variés
        h = rnd.choice([72, 84, 96, 110]); tone = rnd.choice(["#2a2d32", "#2e3136", "#33363b", "#2c2f34", "#30333a"])
        gshape(f"Lame {int(y)}", rrect(0, y, 1920, h - 4, 0), grad("linear", (0, y), (1920, y), [(0, tone, 1), (0.5, tone, 0.92), (1, "#24272c", 1)]))
        shape(f"Joint {int(y)}", rrect(0, y + h - 4, 1920, 4, 0), "#1c1e22", 0.9)
        for k in range(rnd.randint(3, 6)):   # veinage : quelques traits allongés, très discrets
            x0 = rnd.uniform(-200, 1700); w = rnd.uniform(200, 700); yy = y + rnd.uniform(10, h - 16)
            lid = shape(f"Veine {int(y)}_{k}", rrect(x0, yy, w, 2.5, 1.2), rnd.choice(["#3d4046", "#202226"]), 0.32)
        y += h
    # faisceau diagonal doux de la lampe (haut gauche)
    lid = gshape("Faisceau", [M(-300, -200), L(900, -200), L(1700, 1300), L(300, 1300), Z()],
                 grad("linear", (200, 0), (1300, 900), [(0, "#f3efe4", 0.24), (0.55, "#f3efe4", 0.1), (1, "#f3efe4", 0.0)]))
    blur(lid, 70)
    # objets du bureau, hors foyer : le pied de l'écran (gauche) et une tasse (haut droite)
    lid = shape("Pied d'écran flou", rrect(250, -40, 230, 520, 40), "#15171a", 0.85); blur(lid, 55)
    lid = shape("Socle flou", rrect(150, 430, 430, 70, 30), "#15171a", 0.8); blur(lid, 50)
    lid = shape("Tasse floue", ellipse(1660, 140, 150, 150), "#3c4046", 0.9); blur(lid, 45)
    lid = shape("Tasse intérieur", ellipse(1660, 140, 118, 118), "#1b1d21", 0.9); blur(lid, 45)
    # vignettage radial progressif
    gshape("Vignettage", rrect(0, 0, 1920, 1080, 0), grad("radial", (900, 470), (900 + 1250, 470),
           [(0, "#000000", 0.0), (0.45, "#000000", 0.08), (0.8, "#000000", 0.42), (1, "#000000", 0.62)]))

    # ---------- téléphone (repère local : centre du téléphone) ----------
    P = group("Téléphone", T(985, 470, -8, 92))
    W, H = 500, 1000
    lid = shape("Ombre du téléphone", rrect(-W / 2 + 10, -H / 2 + 16, W, H, 70), "#000000", 0.55, P); blur(lid, 26)
    shape("Coque", rrect(-W / 2, -H / 2, W, H, 70), "#0f1114", 1, P)
    shape("Écran", rrect(-W / 2 + 18, -H / 2 + 18, W - 36, H - 36, 56), "#16253f", 1, P)
    X0, Y0 = -W / 2 + 18, -H / 2 + 18
    text("Heure", X0 + 40, Y0 + 62, "23:41", 28, "#c9d6ea", fb, P)
    shape("En-tête", rrect(X0, Y0 + 90, W - 36, 118, 0), "#1d2f4e", 1, P)
    shape("Avatar", ellipse(X0 + 74, Y0 + 149, 36, 36), "#d4913c", 1, P)
    text("Initiale", X0 + 74, Y0 + 163, "C", 38, "#1a1d22", fb, P, just="center")
    text("Nom", X0 + 128, Y0 + 145, "Camille", 40, "#f2f5f9", fb, P)
    text("Lien", X0 + 128, Y0 + 182, "Sœur", 26, "#9fb0c8", fr, P)
    # le message arrive à 0,25 s
    shape("Bulle", rrect(X0 + 28, Y0 + 250, 390, 150, 40), "#2d3e5c", 1, P, start=250, dur=DUR - 250)
    text("Message 1", X0 + 58, Y0 + 312, "On est sur la route.", 36, "#f4f6f9", fb, P, start=250, dur=DUR - 250)
    text("Message 2", X0 + 58, Y0 + 362, "Tu nous rejoins ?", 36, "#f4f6f9", fb, P, start=250, dur=DUR - 250)
    text("Heure du message", X0 + 32, Y0 + 434, "23:39", 22, "#8496b2", fr, P, start=250, dur=DUR - 250)

    # champ de saisie et clavier virtuel AZERTY
    FY = Y0 + 540
    shape("Champ", rrect(X0 + 24, FY, W - 36 - 150, 78, 39), "#24365a", 1, P)
    shape("Envoyer", ellipse(X0 + W - 36 - 70, FY + 39, 36, 36), "#3c6fd6", 1, P)
    shape("Flèche", [M(X0 + W - 36 - 82, FY + 24), L(X0 + W - 36 - 54, FY + 39), L(X0 + W - 36 - 82, FY + 54), Z()], "#ffffff", 1, P)
    KY, KW, KH, GAP = Y0 + 650, 40, 64, 6
    rows = ["AZERTYUIOP", "QSDFGHJKLM", "WXCVBN'⌫"]
    keys = {}
    shape("Fond du clavier", rrect(X0, KY - 14, W - 36, 3 * (KH + 12) + 40, 0), "#0f1a2e", 1, P)
    for r, row in enumerate(rows):
        n = len(row); wide = r == 2
        kw = KW if not wide else KW
        total = n * kw + (n - 1) * GAP + (30 if wide else 0)
        x = X0 + (W - 36 - total) / 2
        for ch in row:
            w = kw + (30 if ch == "⌫" else 0)
            y = KY + r * (KH + 12)
            shape(f"Touche {ch}", rrect(x, y, w, KH, 9), "#c7d0de" if ch != "⌫" else "#8e9bb0", 1, P)
            if ch == "⌫":   # symbole d'effacement dessiné (la police n'a pas ce glyphe)
                cx0, cy0 = x + w / 2, y + KH / 2
                shape("Symbole effacer", [M(cx0 - 22, cy0), L(cx0 - 10, cy0 - 13), L(cx0 + 20, cy0 - 13), L(cx0 + 20, cy0 + 13), L(cx0 - 10, cy0 + 13), Z()], "#1a2233", 1, P)
                shape("Croix effacer", [M(cx0 - 3, cy0 - 6), L(cx0 + 10, cy0 + 6), L(cx0 + 12, cy0 + 4), L(cx0 - 1, cy0 - 8), Z(),
                                        M(cx0 - 3, cy0 + 6), L(cx0 + 10, cy0 - 6), L(cx0 + 12, cy0 - 4), L(cx0 - 1, cy0 + 8), Z()], "#c7d0de", 1, P)
            else:
                text(f"Lettre {ch}", x + w / 2, y + 44, ch, 30, "#1a2233", fb, P, just="center")
            keys[ch] = (x + w / 2, y + KH / 2, w)
            x += w + GAP

    # ---------- frappe : J ' A R R I V E, hésitation, puis effacement ----------
    word = "J'arrive"; seq = ["J", "'", "A", "R", "R", "I", "V", "E"]
    t_type = [700 + i * 240 for i in range(len(seq))]
    t_erase = [3050 + i * 160 for i in range(len(seq))]
    states = []   # (début, fin, texte)
    prev = 0
    for i, t in enumerate(t_type):
        states.append((prev, t + 60, word[:i])); prev = t + 60
    states.append((prev, t_erase[0] + 60, word))
    prev = t_erase[0] + 60
    for i, t in enumerate(t_erase[1:], 1):
        states.append((prev, t + 60, word[:len(word) - i])); prev = t + 60
    states.append((prev, DUR, ""))
    for a, b, s in states:
        if b <= a:
            continue
        if s:
            text(f"Saisie « {s} »", X0 + 56, FY + 52, s, 38, "#f4f6f9", fb, P, start=a, dur=b - a)
        else:
            text("Invite", X0 + 56, FY + 52, "Message", 34, "#7f92b0", fr, P, start=a, dur=b - a)
    # curseur qui clignote pendant l'hésitation (2,7 s → 3,05 s) et après l'effacement
    for k, (a, b) in enumerate([(2660, 2860), (2960, 3050), (4500, 4700), (4850, 5000)]):
        n_chars = len(word) if a < 3050 else 0
        cx = X0 + 60 + (n_chars * 16.3 if n_chars else 0)
        shape(f"Curseur {k}", rrect(cx, FY + 18, 4, 44, 2), "#8fd0ff", 1, P, start=a, dur=b - a)
    # touches qui s'éclairent quand le doigt les frappe
    taps = list(zip(t_type, seq)) + [(t, "⌫") for t in t_erase]
    for i, (t, ch) in enumerate(taps):
        kx, ky, w = keys[ch]
        shape(f"Appui {i}", rrect(kx - w / 2, ky - KH / 2, w, KH, 9), "#ffffff", 0.75, P, start=t - 20, dur=120)

    # ---------- main : silhouette noire, index tendu ; le bout du doigt est l'origine du groupe ----------
    Hd = group("Main", T(keys["J"][0] + 420, keys["J"][1] + 520, 0), P)
    BLK, RIM = "#0a0b0d", "#2f333a"   # silhouette noire ; liseré fin qui sépare les doigts (comme une lumière de bord)

    def finger(name, base, tip, w):
        """Doigt en gélule (bouts ronds), orienté de la base vers le bout ; liseré fin pour le séparer du voisin."""
        bx, by = base; dx, dy = tip[0] - bx, tip[1] - by; L_ = math.hypot(dx, dy) + w * 0.5
        rot = math.degrees(math.atan2(dx, -dy))
        lid = nid()
        A.append({"type": "createFxShapeLayer", "compositionId": "main", "layerId": lid, "name": name, "insertIndex": 0, "parentLayerId": Hd,
                  "activeRange": {"start": 0, "duration": DUR}, "transform": T(bx, by, rot),
                  "shape": {"path": {"commands": rrect(-w / 2, -L_ + w / 2, w, L_ + 30, w / 2)}, "fills": [fill(BLK)],
                            "strokes": [{"paint": {"type": "solid", "color": rgb(RIM)}, "width": 3, "cap": "round", "join": "round", "miterLimit": 4, "blendMode": "normal", "opacity": 1}]}})
        return lid

    shape("Avant-bras", [M(55, 285), C(95, 270, 150, 280, 190, 300), L(540, 1150), L(330, 1185), Z()], BLK, 1, Hd)
    # doigts repliés derrière l'index, en léger éventail, de plus en plus courts ; l'index tendu devant
    finger("Auriculaire", (172, 228), (150, 152), 34)
    finger("Annulaire", (142, 212), (108, 112), 40)
    finger("Majeur", (106, 200), (62, 74), 42)
    finger("Index", (68, 196), (0, 2), 42)
    finger("Pouce", (78, 268), (2, 226), 40)
    # la paume par-dessus, sans liseré : elle cache la base des doigts
    shape("Paume", [M(28, 190), C(80, 160, 165, 170, 200, 210), C(222, 245, 212, 300, 182, 324), C(140, 344, 72, 338, 46, 310),
                    C(22, 282, 12, 222, 28, 190), Z()], BLK, 1, Hd)
    # trajectoire du doigt : entrée par le bas, chaque touche, hésitation, effacement, retrait
    kx = [(0, keys["J"][0] + 420, keys["J"][1] + 520)]
    kx.append((560, keys["J"][0] + 4, keys["J"][1] + 40))
    for t, ch in taps:
        x, y, _ = keys[ch]
        kx.append((t - 110, x + 6, y + 30)); kx.append((t, x, y)); kx.append((t + 70, x + 4, y + 22))
    kx.append((2700, keys["E"][0] + 30, keys["E"][1] + 80))   # le doigt se suspend : elle hésite
    kx.append((4700, keys["⌫"][0] + 60, keys["⌫"][1] + 150)); kx.append((4999, keys["⌫"][0] + 90, keys["⌫"][1] + 210))
    kx.sort(key=lambda r: r[0]); dedup = []
    for r in kx:
        if dedup and r[0] <= dedup[-1][0]:
            continue
        dedup.append(r)
    A.append({"type": "setFxPositionKeyframes", "compositionId": "main", "layerId": Hd,
              "positionX": {"keyframes": [key("x", t, x) for t, x, _ in dedup]},
              "positionY": {"keyframes": [key("y", t, y) for t, _, y in dedup]}})

    if PENSEE:   # pensée de Léa, à gauche du téléphone, pendant l'hésitation (style du guide : Comic Neue, halo sombre)
        lid = gshape("Halo pensée", rrect(140, 380, 520, 90, 45), grad("radial", (400, 425), (700, 425), [(0, "#000000", 0.55), (1, "#000000", 0.0)]), start=2550, dur=1000); blur(lid, 24)
        text("Pensée", 400, 440, "Je ne peux pas partir.", 46, "#f0b04a", fb, start=2550, dur=1000, just="center")

    # étiquette de fiction (petite, lisible)
    text("Étiquette", 58, 74, "SIMULATION HYPOTHÉTIQUE", 24, "#d9dde3", fb, a=0.8)


def main():
    ROOT.mkdir(); (ROOT / ".work").mkdir()
    proj = str(ROOT / "insert_telephone.tsrct")
    run = lambda *a: subprocess.run([TSRCT, *a], check=True, capture_output=True, text=True).stdout  # noqa: E731
    run("project", "create", "--project", proj)
    fr_ = json.loads(run("project", "import-font", "--project", proj, "--file", str(FONTS / "InstrumentSans-Regular.ttf")))
    fb_ = json.loads(run("project", "import-font", "--project", proj, "--file", str(FONTS / "InstrumentSans-Bold.ttf")))
    doc = json.loads(run("project", "inspect", "--project", proj))
    doc["dimensions"] = {"width": 1920, "height": 1080}; doc["duration"] = DUR / 1000
    (ROOT / ".work/doc.json").write_text(json.dumps(doc)); run("project", "commit", "--project", proj, "--file", str(ROOT / ".work/doc.json"))
    build((fr_["fontFamily"], fr_.get("fontStyle", "Regular")), (fb_["fontFamily"], fb_.get("fontStyle", "Bold")))
    (ROOT / ".work/actions.json").write_text(json.dumps(A, ensure_ascii=False))
    out = json.loads(run("project", "apply", "--project", proj, "--actions", str(ROOT / ".work/actions.json")))
    print("actions :", out.get("appliedActions"), "avertissements :", out.get("warnings"))
    print(proj)


if __name__ == "__main__":
    main()
