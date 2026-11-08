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
    "hair": (0.043, 0.078, 0.125), "coat": (0.15, 0.25, 0.45), "sleeve": (0.19, 0.3, 0.53), "coat_sh": (0.07, 0.11, 0.2),
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
# - côté nez plus bas) ; mouth (forme, courbure, ouverture, largeur) ; eye / pupil (échelles) ; closed (yeux fermés
# en arcs) ; sweat (goutte) ; puff (souffle) ; curl : la mèche « ? » joue aussi (q, tall = dressée, droop = retombée,
# tight = resserrée).
EXPR = {
    "neutre":    dict(brow=(0, 0, 4), look=(0, 0), lid=(0.14, 0), mouth=("line", 0.2, 0, 1.0), curl="q"),
    "inquiet":   dict(brow=(-34, -10, 3), look=(-10, -2), lid=(0.0, 0), mouth=("wave", 0, 0, 0.9), pupil=0.62,
                      sweat=True, curl="tight"),
    "triste":    dict(brow=(-22, 4, 3), look=(0, 9), lid=(0.42, 0.5), mouth=("line", -1.0, 0, 1.05), curl="droop"),
    "surpris":   dict(brow=(0, -26, 12), look=(0, 0), lid=(0.0, 0), mouth=("open", 0, 1.05, 0.95), eye=1.18, pupil=0.6,
                      curl="tall"),
    "soulagé":   dict(brow=(-6, -14, 10), closed=True, mouth=("open", 0, 0.5, 1.0), cheek=0.6, puff=True, curl="q"),
    "déterminé": dict(brow=(26, 10, 2), look=(0, 3), lid=(0.36, -0.35), mouth=("teeth", 0, 0, 1.0), curl="q"),
}
CURL = {
    "q": lambda s: [M(s(-46), s(-200)), Q(s(-52), s(-285), s(66), s(-292), s(64), s(-228)), Q(s(62), s(-192), s(8), s(-190), s(8), s(-150))],
    "tall": lambda s: [M(s(-46), s(-250)), Q(s(-52), s(-345), s(66), s(-352), s(64), s(-282)), Q(s(62), s(-232), s(8), s(-222), s(8), s(-150))],
    "tight": lambda s: [M(s(-30), s(-196)), Q(s(-34), s(-258), s(50), s(-262), s(48), s(-216)), Q(s(46), s(-188), s(8), s(-186), s(8), s(-150))],
    "droop": lambda s: [M(s(8), s(-150)), Q(s(8), s(-222), s(78), s(-240), s(108), s(-200)), Q(s(128), s(-172), s(118), s(-138), s(96), s(-126))],
}


def head(cx, cy, k, e, prefix):
    """Tête d'adulte au point (cx, cy), facteur d'échelle k (1 = tête de 300 px de large)."""
    E = EXPR[e]
    s = lambda v: v * k  # noqa: E731
    shape(f"{prefix} cheveux arrière", cx, cy - s(40), ellipse=(s(300), s(250)), fills=[fill(C["hair"])])
    for sx in (-1, 1):
        shape(f"{prefix} oreille", cx + sx * s(150), cy + s(15), ellipse=(s(52), s(70)), fills=[fill(C["skin_sh"])])
    # visage : crâne rond, mâchoire plus carrée (adulte)
    face = [M(s(-150), s(-40)), Q(s(-150), s(-150), s(150), s(-150), s(150), s(-40)), L(s(148), s(70)),
            Q(s(146), s(130), s(100), s(160), s(40), s(166)), L(s(-40), s(166)), Q(s(-100), s(160), s(-146), s(130), s(-148), s(70)), Z()]
    shape(f"{prefix} visage", cx, cy, path=face, fills=[fill(C["skin"])])
    # barbe de trois jours très légère sur la mâchoire
    beard = [M(s(-140), s(70)), Q(s(-130), s(135), s(-90), s(160), s(-40), s(166)), L(s(40), s(166)),
             Q(s(90), s(160), s(130), s(135), s(140), s(70)), Q(s(90), s(120), s(-90), s(120), s(-140), s(70)), Z()]
    shape(f"{prefix} barbe", cx, cy, path=beard, fills=[fill(C["hair"], 0.065)])
    fr = [M(s(-152), s(-48)), Q(s(-152), s(-200), s(152), s(-205), s(152), s(-52)),
          Q(s(112), s(-104), s(40), s(-118), s(-20), s(-106)), Q(s(-70), s(-96), s(-122), s(-82), s(-152), s(-48)), Z()]
    shape(f"{prefix} frange", cx, cy, path=fr, fills=[fill(C["hair"])])
    shape(f"{prefix} mèche ?", cx + s(6), cy, path=CURL[E["curl"]](s), strokes=[stroke(C["hair"], s(28))])
    es, ps = E.get("eye", 1.0), E.get("pupil", 1.0)
    for sx in (-1, 1):
        ex, ey = cx + sx * s(60), cy + s(16)
        if E.get("closed"):  # yeux fermés, arcs vers le haut (soulagement)
            shape(f"{prefix} œil fermé", ex, ey + s(6), path=[M(s(-28), s(6)), Q(s(-12), s(-14), s(12), s(-14), s(28), s(6))],
                  strokes=[stroke(C["hair"], s(10))])
        else:
            shape(f"{prefix} œil", ex, ey, ellipse=(s(68 * es), s(80 * es)), fills=[fill(C["eye"])])
            dx, dy = E["look"]
            shape(f"{prefix} pupille", ex + s(dx), ey + s(dy + 5), ellipse=(s(32 * ps), s(38 * ps)), fills=[fill(C["pupil"])])
            shape(f"{prefix} reflet", ex + s(dx + 7 * ps), ey + s(dy - 3 * ps), ellipse=(s(10), s(10)), fills=[fill(C["white"])])
            amt, tilt = E["lid"]
            if amt > 0:
                w, top = s(38 * es), -s(48 * es)
                yb = -s(40 * es) + s(80 * es) * amt
                off = s(20) * tilt
                y_out, y_in = yb + off, yb - off
                yR, yL = (y_out, y_in) if sx > 0 else (y_in, y_out)
                lid = [M(-w, top), L(w, top), L(w, yR), Q(w / 3, yR + (yL - yR) / 3 + s(4), -w / 3, yR + 2 * (yL - yR) / 3 + s(4), -w, yL), Z()]
                shape(f"{prefix} paupière", ex, ey, path=lid, fills=[fill(C["skin"])])
        ang, hy, arch = E["brow"]
        b = [M(s(-32), 0), Q(s(-11), s(-arch), s(11), s(-arch), s(32), 0)]
        # angle > 0 : côté nez vers le bas (détermination) ; < 0 : côté nez relevé (inquiétude, tristesse)
        shape(f"{prefix} sourcil", ex, ey - s(62 * es) + s(hy), path=b, strokes=[stroke(C["hair"], s(16))], rot=-sx * ang)
    shape(f"{prefix} nez", cx, cy + s(66), path=[M(s(-12), 0), Q(s(-6), s(12), s(6), s(12), s(12), 0)], strokes=[stroke(C["skin_sh"], s(9))])
    if E.get("cheek"):
        for sx in (-1, 1):
            shape(f"{prefix} joue", cx + sx * s(100), cy + s(78), ellipse=(s(50), s(28)), fills=[fill(C["cheek"], 0.55 * E["cheek"])])
    if E.get("sweat"):
        d = [M(0, s(-26)), Q(s(7), s(-12), s(17), s(0), s(17), s(9)), Q(s(17), s(20), s(9), s(26), 0, s(26)),
             Q(s(-9), s(26), s(-17), s(20), s(-17), s(9)), Q(s(-17), s(0), s(-7), s(-12), 0, s(-26)), Z()]
        shape(f"{prefix} goutte", cx + s(132), cy - s(40), path=d, fills=[fill(C["sweat"])])
    form, cv, op, mw = E["mouth"]
    my = cy + s(112)
    if form == "open":
        shape(f"{prefix} bouche", cx, my, ellipse=(s(52 * mw), s(60) * op), fills=[fill(C["mouth"])])
    elif form == "teeth":  # mâchoire serrée
        shape(f"{prefix} bouche", cx, my, path=rrect(s(78), s(24), s(10)), fills=[fill(C["white"])], strokes=[stroke(C["mouth"], s(7))])
    elif form == "wave":
        m = [M(s(-40), s(4)), Q(s(-28), s(-12), s(-14), s(-12), 0, s(2)), Q(s(14), s(14), s(28), s(14), s(40), s(-2))]
        shape(f"{prefix} bouche", cx, my, path=m, strokes=[stroke(C["mouth"], s(11))])
    else:
        m = [M(s(-42 * mw), 0), Q(s(-16 * mw), s(30) * cv, s(16 * mw), s(30) * cv, s(42 * mw), 0)]
        shape(f"{prefix} bouche", cx, my, path=m, strokes=[stroke(C["mouth"], s(11))])
    if E.get("puff"):  # souffle de soulagement
        for n, (dx, dy, r) in enumerate([(70, 140, 22), (100, 150, 16), (124, 162, 11)]):
            shape(f"{prefix} souffle {n}", cx + s(dx), cy + s(dy), ellipse=(s(r * 2), s(r * 1.6)), fills=[fill(C["white"], 0.9)],
                  strokes=[stroke(C["sweat"], s(4))])


# poses : bras (coude, main) relatifs à l'épaule ; décalage de tête ; affaissement des épaules ; expression
POSES = {
    "neutre":  dict(arms={-1: ((-34, 140), (-44, 270)), 1: ((34, 140), (44, 270))}, head=(0, 0), slump=0, e="neutre"),
    "abattu":  dict(arms={-1: ((-14, 150), (-4, 290)), 1: ((14, 150), (4, 290))}, head=(0, 52), slump=22, e="triste"),
    "sursaut": dict(arms={-1: ((-96, -10), (-70, -150)), 1: ((96, -10), (70, -150))}, head=(0, -14), slump=-8, e="surpris"),
    "résolu":  dict(arms={-1: ((-96, 120), (-40, 200)), 1: ((88, 110), (-4, 60))}, head=(0, 0), slump=0, e="déterminé"),
}


def figure(cx, top, k, pose, prefix, shadow=True):
    """Personnage entier (env. 3 têtes, adulte) : top = haut des épaules au repos."""
    P = POSES[pose]
    s = lambda v: v * k  # noqa: E731
    if shadow:
        shape(f"{prefix} ombre", cx, top + s(580), ellipse=(s(260), s(36)), fills=[fill(C["shadow"], 0.12)])
    for sx in (-1, 1):  # jambes et baskets (sous les jambes)
        shape(f"{prefix} jambe", cx + sx * s(44), top + s(440), path=rrect(s(66), s(260), s(28)), fills=[fill(C["pants"])])
        shape(f"{prefix} basket", cx + sx * s(50), top + s(560), path=rrect(s(96), s(40), s(20)), fills=[fill(C["shoe"])],
              strokes=[stroke(C["sole"], s(5))])
    t = top + s(P["slump"])  # épaules (plus basses si abattu)
    hdx, hdy = P["head"]
    shape(f"{prefix} cou", cx, t - s(30), path=rrect(s(74), s(80), s(20)), fills=[fill(C["skin_sh"])])
    coat = [M(s(-118), s(10)), Q(s(-150), s(90), s(-164), s(240), s(-150), s(340 - P["slump"])), L(s(150), s(340 - P["slump"])),
            Q(s(164), s(240), s(150), s(90), s(118), s(10)), Q(s(60), s(-15), s(-60), s(-15), s(-118), s(10)), Z()]
    shape(f"{prefix} veste", cx, t, path=coat, fills=[fill(C["coat"])])
    shape(f"{prefix} fermeture", cx, t, path=[M(0, s(40)), L(0, s(335 - P["slump"]))], strokes=[stroke(C["coat_sh"], s(8))])
    for sx in (-1, 1):  # poches
        shape(f"{prefix} poche", cx + sx * s(80), t + s(250), path=[M(s(-26), 0), L(s(26), 0)], strokes=[stroke(C["coat_sh"], s(8))])
    scarf = [M(s(-105), s(-6)), Q(s(-40), s(30), s(40), s(30), s(105), s(-6)), L(s(100), s(30)), Q(s(40), s(66), s(-40), s(66), s(-100), s(30)), Z()]
    shape(f"{prefix} écharpe", cx, t, path=scarf, fills=[fill(C["scarf"])])
    shape(f"{prefix} pan d'écharpe", cx + s(52), t + s(84), path=rrect(s(44), s(130), s(16)), fills=[fill(C["scarf_sh"])], rot=-6)
    head(cx + s(hdx), top - s(205) + s(hdy), k, P["e"], prefix)
    for sx in (-1, 1):  # bras : contour sombre puis manche, main en moufle (se détache du buste)
        (ex, ey), (hx, hy) = P["arms"][sx]
        arm = [M(0, 0), L(s(ex), s(ey)), L(s(hx), s(hy))]
        ox, oy = cx + sx * s(118), t + s(36)
        shape(f"{prefix} bras contour", ox, oy, path=arm, strokes=[stroke(C["coat_sh"], s(62))])
        shape(f"{prefix} bras", ox, oy, path=arm, strokes=[stroke(C["sleeve"], s(48))])
        shape(f"{prefix} main", ox + s(hx), oy + s(hy) + s(10), ellipse=(s(54), s(58)), fills=[fill(C["skin"])])


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
    kh, top_h = 0.72, 557
    shape("Disque héros", 310, top_h - 205 * kh - 30, ellipse=(300, 300), fills=[fill(C["orange"])])
    figure(310, top_h, kh, "neutre", "Héros")
    text("Légende héros", 310, 1022, "Face · posture neutre", 26, C["label"], F, "center")

    # six expressions sur une ligne
    shape("Panneau expressions", 1245, 375, path=rrect(1270, 430, 32), fills=[fill(C["panel"])])
    for i, e in enumerate(EXPR):
        cx = 715 + i * 211
        head(cx, 368, 0.52, e, e.capitalize())
        text(f"Légende {e}", cx, 535, e.capitalize(), 28, C["label"], F, "center")

    # poses sur un fond de scène moyen (preuve de lisibilité hors fiche) + test de silhouette
    shape("Panneau poses", 1090, 830, path=rrect(960, 420, 32), fills=[fill(C["scene"])])
    kp, top_p = 0.33, 806
    for i, (p, lab) in enumerate([("abattu", "Abattu"), ("sursaut", "Sursaut"), ("résolu", "Résolu"), ("sursaut", "Silhouette")]):
        cx = 730 + i * 240
        if lab == "Silhouette":
            MONO[0] = C["ink"]
        figure(cx, top_p, kp, p, lab)
        MONO[0] = None
        text(f"Légende {lab}", cx, 1030, lab, 22, C["white"], F, "center")

    # palette avec codes hexadécimaux
    shape("Panneau palette", 1740, 830, path=rrect(280, 420, 32), fills=[fill(C["panel"])])
    pal = [("Visage", C["skin"]), ("Cheveux", C["hair"]), ("Veste", C["coat"]), ("Écharpe", C["scarf"]), ("Pantalon", C["pants"])]
    for i, (n, col) in enumerate(pal):
        y = 662 + i * 64
        shape(f"Couleur {n}", 1648, y, path=rrect(48, 48, 12), fills=[fill(col)], strokes=[stroke(C["line"], 3)])
        text(f"Nom {n}", 1686, y - 2, n, 22, C["ink"], F)
        text(f"Code {n}", 1686, y + 20, hexa(col), 18, C["label"], F)
    text("Secondaires", 1624, 975, "Secondaires", 18, C["label"], F)
    sec = [C["skin_sh"], C["scarf_sh"], C["sleeve"], C["mouth"], C["cheek"], C["sweat"]]
    for i, col in enumerate(sec):
        shape(f"Secondaire {hexa(col)}", 1640 + i * 40, 1005, ellipse=(30, 30), fills=[fill(col)], strokes=[stroke(C["line"], 2)])
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
