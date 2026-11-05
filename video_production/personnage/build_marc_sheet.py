"""Planche du personnage iconique WhatIfCastFR, construite en formes vectorielles modifiables (Tesseract).

    python build_marc_sheet.py <dossier_projet> <police Bricolage .ttf> [logo .png] [chemin tsrct]

Le dossier projet doit être nouveau (créé par ce script). Sortie : Personnage.tsrct (modifiable) et Personnage.png.

Identité : grosse tête ronde, mèche en point d'interrogation (rappel du logo « ? »), grands yeux et sourcils épais
(l'émotion passe par eux), veste bleu nuit et écharpe orange WhatIfCastFR. Pas de silhouette noire (style Last Soul).
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT, FONT = Path(sys.argv[1]), Path(sys.argv[2])
LOGO = Path(sys.argv[3]).resolve() if len(sys.argv) > 3 else None
TSRCT = sys.argv[4] if len(sys.argv) > 4 else str(Path.home() / ".local/share/Tesseract/bin/tsrct")

C = {  # palette (sRGB 0..1) ; orange = orange exact du logo (#FFB020)
    "bg": (0.965, 0.945, 0.91), "panel": (0.995, 0.99, 0.98), "hero": (1.0, 0.9, 0.72), "scene": (0.42, 0.5, 0.6),
    "line": (0.82, 0.79, 0.74), "ink": (0.11, 0.14, 0.2), "label": (0.3, 0.34, 0.42),
    "skin": (0.93, 0.72, 0.58), "skin_sh": (0.84, 0.6, 0.47), "cheek": (0.95, 0.56, 0.5),
    "hair": (0.11, 0.14, 0.2), "coat": (0.12, 0.18, 0.3), "sleeve": (0.16, 0.24, 0.38), "coat_sh": (0.08, 0.12, 0.21),
    "scarf": (1.0, 0.69, 0.125), "scarf_sh": (0.88, 0.53, 0.07), "pants": (0.33, 0.36, 0.42),
    "shoe": (0.98, 0.98, 0.97), "sole": (0.11, 0.14, 0.2), "eye": (0.99, 0.99, 0.98), "pupil": (0.07, 0.08, 0.1),
    "white": (0.99, 0.99, 0.99), "mouth": (0.45, 0.17, 0.16), "sweat": (0.55, 0.8, 0.96), "shadow": (0.0, 0.0, 0.0),
    "orange": (1.0, 0.69, 0.125),
}
MONO = [None]  # couleur unique (test de silhouette)
actions, _id = [], [0]


def nid():
    _id[0] += 1
    return _id[0]


def T(x=0.0, y=0.0, rot=0.0, s=100.0):
    return {"anchorPoint": [0, 0], "position": [x, y], "scale": [s, s], "rotation": rot, "opacity": 100}


def fill(c, a=1.0):
    c = MONO[0] or c
    return {"paint": {"type": "solid", "color": [*c, a]}, "fillRule": "nonZeroWinding", "blendMode": "normal", "opacity": 1}


def stroke(c, w, cap="round"):
    c = MONO[0] or c
    return {"paint": {"type": "solid", "color": [*c, 1]}, "width": w, "cap": cap, "join": "round", "miterLimit": 4,
            "blendMode": "normal", "opacity": 1}


def shape(name, x, y, path=None, ellipse=None, fills=(), strokes=(), rot=0.0, parent=None):
    lid = nid()
    a = {"type": "createFxShapeLayer", "compositionId": "main", "layerId": lid, "name": name, "insertIndex": 0,
         "activeRange": {"start": 0, "duration": 3000}, "transform": T(x, y, rot),
         "shape": {"path": {"commands": path or []}, "fills": list(fills), "strokes": list(strokes)}}
    if ellipse:
        a["shape"]["ellipse"] = {"position": [0, 0], "size": list(ellipse)}
    actions.append(a)
    return lid


def M(x, y): return {"type": "moveTo", "x": x, "y": y}
def L(x, y): return {"type": "lineTo", "x": x, "y": y}
def Q(c1x, c1y, c2x, c2y, x, y): return {"type": "cubicTo", "c1x": c1x, "c1y": c1y, "c2x": c2x, "c2y": c2y, "x": x, "y": y}
def Z(): return {"type": "close"}


def rrect(w, h, r):  # rectangle aux coins arrondis, centré
    k = 0.5523 * r; x0, y0, x1, y1 = -w / 2, -h / 2, w / 2, h / 2
    return [M(x0 + r, y0), L(x1 - r, y0), Q(x1 - r + k, y0, x1, y0 + r - k, x1, y0 + r), L(x1, y1 - r),
            Q(x1, y1 - r + k, x1 - r + k, y1, x1 - r, y1), L(x0 + r, y1), Q(x0 + r - k, y1, x0, y1 - r + k, x0, y1 - r),
            L(x0, y0 + r), Q(x0, y0 + r - k, x0 + r - k, y0, x0 + r, y0), Z()]


def text(name, x, y, s, size, col, font, just="left"):
    lid = nid()
    actions.append({"type": "createFxTextLayer", "compositionId": "main", "insertIndex": 0, "layerId": lid, "name": name,
                    "activeRange": {"start": 0, "duration": 3000}, "transform": T(x, y),
                    "sourceText": {"text": s, "fontFamily": font[0], "fontStyle": font[1], "fontSize": size,
                                   "fillColor": [*col, 1], "justification": just}})
    return lid


# ---------- tête : la même construction pour toutes les expressions ----------
# brow (angle intérieur, hauteur, cambrure) ; look (dx, dy) ; lid (fermeture 0..1, inclinaison : + extérieur plus bas,
# - côté nez plus bas) ; mouth (courbure, ouverture, largeur) ; eye / pupil (échelles) ; sweat (goutte) ;
# curl : la mèche « ? » joue aussi (q = normale, tall = dressée, droop = retombée)
EXPR = {
    "neutre":    dict(brow=(0, 0, 5), look=(0, 0), lid=(0.12, 0), mouth=(0.25, 0, 1.0), eye=1.0, pupil=1.0, curl="q"),
    "inquiet":   dict(brow=(-26, -12, 4), look=(-9, -1), lid=(0.0, 0), mouth=(-0.3, 0, 0.75), eye=1.0, pupil=0.72,
                      sweat=True, curl="q"),
    "triste":    dict(brow=(-20, 4, 4), look=(0, 9), lid=(0.42, 0.45), mouth=(-0.75, 0, 0.9), eye=1.0, pupil=1.0, curl="droop"),
    "surpris":   dict(brow=(0, -30, 12), look=(0, 0), lid=(0.0, 0), mouth=(0, 1.05, 0.85), eye=1.15, pupil=0.62, curl="tall"),
    "soulagé":   dict(brow=(-8, -2, 8), look=(0, 3), lid=(0.62, 0), mouth=(0.8, 0, 1.0), eye=1.0, pupil=1.0, cheek=0.55, curl="q"),
    "déterminé": dict(brow=(24, 10, 2), look=(0, 3), lid=(0.36, -0.35), mouth=(-0.08, 0, 1.15), eye=1.0, pupil=1.0, curl="q"),
}
CURL = {
    "q": lambda s: [M(s(-46), s(-200)), Q(s(-52), s(-285), s(66), s(-292), s(64), s(-228)), Q(s(62), s(-192), s(8), s(-190), s(8), s(-150))],
    "tall": lambda s: [M(s(-46), s(-250)), Q(s(-52), s(-345), s(66), s(-352), s(64), s(-282)), Q(s(62), s(-232), s(8), s(-222), s(8), s(-150))],
    "droop": lambda s: [M(s(8), s(-150)), Q(s(8), s(-222), s(78), s(-240), s(108), s(-200)), Q(s(128), s(-172), s(118), s(-138), s(96), s(-126))],
}


def head(cx, cy, k, e, prefix):
    """Tête au point (cx, cy), facteur d'échelle k (1 = tête de 300 px de large)."""
    E = EXPR[e]
    s = lambda v: v * k  # noqa: E731
    shape(f"{prefix} cheveux arrière", cx, cy - s(40), ellipse=(s(300), s(250)), fills=[fill(C["hair"])])
    for sx in (-1, 1):
        shape(f"{prefix} oreille", cx + sx * s(150), cy + s(15), ellipse=(s(56), s(74)), fills=[fill(C["skin_sh"])])
    shape(f"{prefix} visage", cx, cy + s(10), path=rrect(s(300), s(290), s(140)), fills=[fill(C["skin"])])
    fr = [M(s(-150), s(-20)), Q(s(-150), s(-170), s(150), s(-175), s(150), s(-25)),
          Q(s(110), s(-80), s(40), s(-95), s(-20), s(-80)), Q(s(-70), s(-70), s(-120), s(-55), s(-150), s(-20)), Z()]
    shape(f"{prefix} frange", cx, cy, path=fr, fills=[fill(C["hair"])])
    shape(f"{prefix} mèche ?", cx + s(6), cy, path=CURL[E["curl"]](s), strokes=[stroke(C["hair"], s(28))])
    es, ps = E["eye"], E["pupil"]
    for sx in (-1, 1):
        ex, ey = cx + sx * s(62), cy + s(18)
        shape(f"{prefix} œil", ex, ey, ellipse=(s(78 * es), s(92 * es)), fills=[fill(C["eye"])])
        dx, dy = E["look"]
        shape(f"{prefix} pupille", ex + s(dx), ey + s(dy + 6), ellipse=(s(36 * ps), s(42 * ps)), fills=[fill(C["pupil"])])
        shape(f"{prefix} reflet", ex + s(dx + 8 * ps), ey + s(dy - 4 * ps), ellipse=(s(11), s(11)), fills=[fill(C["white"])])
        amt, tilt = E["lid"]
        if amt > 0:
            w, top = s(44 * es), -s(56 * es)
            yb = -s(46 * es) + s(92 * es) * amt
            off = s(22) * tilt
            y_out, y_in = yb + off, yb - off
            yR, yL = (y_out, y_in) if sx > 0 else (y_in, y_out)
            lid = [M(-w, top), L(w, top), L(w, yR), Q(w / 3, yR + (yL - yR) / 3 + s(5), -w / 3, yR + 2 * (yL - yR) / 3 + s(5), -w, yL), Z()]
            shape(f"{prefix} paupière", ex, ey, path=lid, fills=[fill(C["skin"])])
        ang, hy, arch = E["brow"]
        b = [M(s(-36), 0), Q(s(-12), s(-arch), s(12), s(-arch), s(36), 0)]
        # angle > 0 : côté nez vers le bas (détermination) ; < 0 : côté nez relevé (inquiétude, tristesse)
        shape(f"{prefix} sourcil", ex, ey - s(72 * es) + s(hy), path=b, strokes=[stroke(C["hair"], s(17))], rot=-sx * ang)
    if E.get("cheek"):
        for sx in (-1, 1):
            shape(f"{prefix} joue", cx + sx * s(98), cy + s(82), ellipse=(s(52), s(30)), fills=[fill(C["cheek"], 0.55 * E["cheek"])])
    if E.get("sweat"):
        d = [M(0, s(-26)), Q(s(7), s(-12), s(17), s(0), s(17), s(9)), Q(s(17), s(20), s(9), s(26), 0, s(26)),
             Q(s(-9), s(26), s(-17), s(20), s(-17), s(9)), Q(s(-17), s(0), s(-7), s(-12), 0, s(-26)), Z()]
        shape(f"{prefix} goutte", cx + s(136), cy - s(64), path=d, fills=[fill(C["sweat"])])
    cv, op, mw = E["mouth"]
    if op > 0:
        shape(f"{prefix} bouche", cx, cy + s(102), ellipse=(s(40 * mw), s(56) * op), fills=[fill(C["mouth"])])
    else:
        m = [M(s(-30 * mw), 0), Q(s(-12 * mw), s(26) * cv, s(12 * mw), s(26) * cv, s(30 * mw), 0)]
        shape(f"{prefix} bouche", cx, cy + s(100), path=m, strokes=[stroke(C["mouth"], s(9))])


# poses : bras (coude, main) relatifs à l'épaule, pour le bras gauche (-1) et droit (+1) ; décalage de tête ; expression
POSES = {
    "neutre":    dict(arms={-1: ((-30, 105), (-40, 205)), 1: ((30, 105), (40, 205))}, head=(0, 0), e="neutre"),
    "abattu":    dict(arms={-1: ((-6, 112), (6, 222)), 1: ((6, 112), (-6, 222))}, head=(0, 26), e="triste"),
    "sursaut":   dict(arms={-1: ((-78, -18), (-58, -128)), 1: ((78, -18), (58, -128))}, head=(0, -12), e="surpris"),
    "résolu":    dict(arms={-1: ((-82, 92), (-26, 152)), 1: ((62, 88), (-18, 40))}, head=(0, 0), e="déterminé"),
}


def figure(cx, top, k, pose, prefix, shadow=True):
    """Personnage entier : top = haut des épaules."""
    P = POSES[pose]
    s = lambda v: v * k  # noqa: E731
    if shadow:
        shape(f"{prefix} ombre", cx, top + s(386), ellipse=(s(250), s(34)), fills=[fill(C["shadow"], 0.12)])
    for sx in (-1, 1):  # jambes et baskets (sous les jambes)
        shape(f"{prefix} jambe", cx + sx * s(42), top + s(296), path=rrect(s(62), s(124), s(26)), fills=[fill(C["pants"])])
        shape(f"{prefix} basket", cx + sx * s(48), top + s(362), path=rrect(s(92), s(40), s(20)), fills=[fill(C["shoe"])],
              strokes=[stroke(C["sole"], s(5))])
    coat = [M(s(-118), s(10)), Q(s(-150), s(80), s(-160), s(190), s(-148), s(266)), L(s(148), s(266)),
            Q(s(160), s(190), s(150), s(80), s(118), s(10)), Q(s(60), s(-15), s(-60), s(-15), s(-118), s(10)), Z()]
    shape(f"{prefix} veste", cx, top, path=coat, fills=[fill(C["coat"])])
    shape(f"{prefix} fermeture", cx, top + s(150), path=[M(0, s(-110)), L(0, s(112))], strokes=[stroke(C["coat_sh"], s(8))])
    scarf = [M(s(-105), s(-6)), Q(s(-40), s(30), s(40), s(30), s(105), s(-6)), L(s(100), s(30)), Q(s(40), s(66), s(-40), s(66), s(-100), s(30)), Z()]
    shape(f"{prefix} écharpe", cx, top, path=scarf, fills=[fill(C["scarf"])])
    shape(f"{prefix} pan d'écharpe", cx + s(52), top + s(78), path=rrect(s(44), s(120), s(16)), fills=[fill(C["scarf_sh"])], rot=-6)
    hdx, hdy = P["head"]
    head(cx + s(hdx), top - s(174) + s(hdy), k, P["e"], prefix)
    for sx in (-1, 1):  # bras (manche un peu plus claire que la veste), puis main en moufle
        (ex, ey), (hx, hy) = P["arms"][sx]
        sh = (sx * s(118), s(34))
        arm = [M(0, 0), L(s(ex) - s(sx * 0), s(ey)), L(s(hx), s(hy))]
        shape(f"{prefix} bras", cx + sh[0], top + sh[1], path=arm, strokes=[stroke(C["sleeve"], s(50))])
        shape(f"{prefix} main", cx + sh[0] + s(hx), top + sh[1] + s(hy) + s(8), ellipse=(s(52), s(56)), fills=[fill(C["skin"])])


def hexa(c):
    return "#" + "".join(f"{round(v * 255):02X}" for v in c)


def main():
    ROOT.mkdir()                       # projet neuf : échoue s'il existe déjà
    (ROOT / ".tesseract-work").mkdir()
    proj = str(ROOT / "Personnage.tsrct")
    run = lambda *a: subprocess.run([TSRCT, *a], check=True, capture_output=True, text=True).stdout  # noqa: E731
    run("project", "create", "--project", proj)
    font = json.loads(run("project", "import-font", "--project", proj, "--file", str(FONT)))
    F = (font["fontFamily"], "ExtraBold")
    if LOGO:
        run("project", "import-asset", "--project", proj, "--file", str(LOGO), "--asset-id", "logo", "--kind", "image")
    doc = json.loads(run("project", "inspect", "--project", proj))
    doc["dimensions"] = {"width": 1920, "height": 1080}
    (ROOT / ".tesseract-work/doc.json").write_text(json.dumps(doc))
    run("project", "commit", "--project", proj, "--file", str(ROOT / ".tesseract-work/doc.json"))

    actions.append({"type": "createFxRectLayer", "compositionId": "main", "layerId": nid(), "name": "Fond", "insertIndex": 0,
                    "activeRange": {"start": 0, "duration": 3000}, "transform": T(0, 0), "rect": {"size": [1920, 1080], "fillColor": [*C["bg"], 1]}})
    # bandeau aux couleurs du logo
    actions.append({"type": "createFxRectLayer", "compositionId": "main", "layerId": nid(), "name": "Bandeau", "insertIndex": 0,
                    "activeRange": {"start": 0, "duration": 3000}, "transform": T(0, 0), "rect": {"size": [1920, 130], "fillColor": [*C["orange"], 1]}})
    text("Titre", 170, 92, "Marc", 76, C["ink"], F)
    text("Sous-titre", 370, 88, "Personnage iconique WhatIfCastFR", 32, C["ink"], F)
    text("Règle", 1880, 86, "La mèche « ? » et la tête-point : la signature", 24, C["ink"], F, "right")

    # héros : face, posture neutre, sur un disque orange (rappel du logo)
    shape("Panneau héros", 310, 600, path=rrect(540, 880, 32), fills=[fill(C["hero"])])
    kh, top_h = 0.9, 628
    shape("Disque héros", 310, top_h - 174 * kh - 40, ellipse=(390, 390), fills=[fill(C["orange"])])
    figure(310, top_h, kh, "neutre", "Héros")
    text("Légende héros", 310, 1015, "Face · posture neutre", 26, C["label"], F, "center")

    # six expressions sur une ligne
    shape("Panneau expressions", 1245, 375, path=rrect(1270, 430, 32), fills=[fill(C["panel"])])
    for i, e in enumerate(EXPR):
        cx = 715 + i * 211
        head(cx, 368, 0.52, e, e.capitalize())
        text(f"Légende {e}", cx, 535, e.capitalize(), 28, C["label"], F, "center")

    # poses sur un fond de scène moyen (preuve de lisibilité hors fiche) + test de silhouette
    shape("Panneau poses", 1090, 830, path=rrect(960, 420, 32), fills=[fill(C["scene"])])
    kp, top_p = 0.37, 832
    for i, (p, lab) in enumerate([("abattu", "Abattu"), ("sursaut", "Sursaut"), ("résolu", "Résolu"), ("neutre", "Silhouette")]):
        cx = 730 + i * 240
        if lab == "Silhouette":
            MONO[0] = C["ink"]
        figure(cx, top_p, kp, p, lab)
        MONO[0] = None
        text(f"Légende {lab}", cx, 1024, lab, 24, C["white"], F, "center")

    # palette avec codes hexadécimaux
    shape("Panneau palette", 1740, 830, path=rrect(280, 420, 32), fills=[fill(C["panel"])])
    pal = [("Visage", C["skin"]), ("Cheveux", C["hair"]), ("Veste", C["coat"]), ("Écharpe", C["scarf"]), ("Pantalon", C["pants"])]
    for i, (n, col) in enumerate(pal):
        y = 675 + i * 78
        shape(f"Couleur {n}", 1652, y, path=rrect(56, 56, 14), fills=[fill(col)], strokes=[stroke(C["line"], 3)])
        text(f"Nom {n}", 1694, y - 2, n, 24, C["ink"], F)
        text(f"Code {n}", 1694, y + 24, hexa(col), 20, C["label"], F)

    acts = ROOT / ".tesseract-work/actions.json"
    acts.write_text(json.dumps(actions, ensure_ascii=False))
    out = json.loads(run("project", "apply", "--project", proj, "--actions", str(acts)))
    print("actions appliquées :", out.get("appliedActions"), "avertissements :", out.get("warnings"))
    if LOGO:  # calque image du logo (schéma document) au-dessus de tout
        doc = json.loads(run("project", "inspect", "--project", proj))
        lid = max(l["id"] for l in doc["composition"]["layers"]) + 1
        doc["composition"]["layers"].insert(0, {
            "type": "Image", "id": lid, "name": "Logo", "blendMode": "normal", "activeRange": {"start": 0, "duration": 3000},
            "transform": {"anchorPoint": [0, 0], "position": [30, 10], "scale": [13.75, 13.75], "rotation": 0, "opacity": 100},
            "source": {"assetId": "logo", "fit": "contain"}})
        (ROOT / ".tesseract-work/doc.json").write_text(json.dumps(doc, ensure_ascii=False))
        run("project", "commit", "--project", proj, "--file", str(ROOT / ".tesseract-work/doc.json"))
    run("preview", "--project", proj, "--time", "1", "--output", str(ROOT / "Personnage.png"))
    print("ok", ROOT / "Personnage.png")


if __name__ == "__main__":
    main()
