"""Prototype 2D du Dernier Écho (43 s) : même déroulé que prototype/proto.html, refait en 2D (images générées + Tesseract).

    python3 build_film.py <dossier_neuf>    → projet .tsrct modifiable + film_muet.mp4 (l'insert du téléphone et le son
                                              sont ajoutés ensuite par assemble.py)

Plans (s) : 0–4 large Calern nuit · 4–6,5 collègue à la porte · 6,5–8 Léa en gros plan · 8–16 INSERT téléphone (8 s)
· 16–18,5 collègue · 18,5–22 Léa se tourne · 22–26 collision · 26–30 noir absolu · 30–34 Calern de jour · 34–43 plage.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"
TSRCT = str(Path.home() / ".local/share/Tesseract/bin/tsrct")
FONT = HERE.parent / "prototype/fonts/InstrumentSans-Bold.ttf"
ROOT = Path(sys.argv[1])
DUR = 43000
ASSETS = ["decor_calern_nuit", "decor_calern_jour", "decor_espace", "decor_plage",
          "lea_profil_cut", "lea_face_cut", "collegue_porte_cut", "collegue_marche_cut", "garcon_court_cut", "mere_marche_cut"]
SIZE = {a: Image.open(IMG / f"{a}.png").size for a in ASSETS}

A, LAYERS, _id = [], [], [100]


def nid():
    _id[0] += 1
    return _id[0]


def T(x=0.0, y=0.0, s=100.0, ax=0.0, ay=0.0, op=100.0):
    return {"anchorPoint": [ax, ay], "position": [x, y], "scale": [s, s], "rotation": 0, "opacity": op}


def key(i, t, v):
    return {"id": f"{i}_{int(t)}", "layerTime": int(t), "value": {"type": "float", "value": float(v)},
            "easing": {"type": "cubicBezier", "x1": 0.35, "y1": 0, "x2": 0.25, "y2": 1}}


def image(asset, x, y, height=None, width=None, start=0, dur=None):
    """Calque image (ajouté au document après coup) : (x, y) = coin haut gauche, taille par hauteur ou largeur."""
    w, h = SIZE[asset]; s = 100.0 * (height / h if height else width / w)
    lid = nid()
    return {"type": "Image", "id": lid, "name": asset, "blendMode": "normal", "activeRange": {"start": start, "duration": dur},
            "transform": {"anchorPoint": [0, 0], "position": [x, y], "scale": [s, s], "rotation": 0, "opacity": 100},
            "source": {"assetId": asset, "fit": "contain"}}


def cover(asset):
    """Décor qui couvre tout le cadre (centré), quelle que soit la proportion de l'image."""
    w, h = SIZE[asset]; s = max(1920 / w, 1080 / h) * 1.02
    return image(asset, (1920 - w * s) / 2, (1080 - h * s) / 2, width=w * s)


def shot(name, start, end, children, cam=None):
    """Plan : groupe calé dans le temps ; cam = (ancre x, ancre y, échelle début, échelle fin) en coordonnées du décor."""
    ax, ay, s0, s1 = cam or (960, 540, 100, 104)
    # le cadre ne sort jamais du décor : l'ancre est bornée selon l'échelle la plus faible du plan
    m = min(s0, s1) / 100
    ax = min(max(ax, 960 / m), 1920 - 960 / m); ay = min(max(ay, 540 / m), 1080 - 540 / m)
    gid = nid(); d = end - start
    for c in children:
        c["activeRange"] = {"start": start, "duration": d}; c["parent"] = gid   # les enfants comptent en temps du film
    win = {"start": start, "duration": d}
    LAYERS.append({"type": "Group", "id": gid, "name": name, "blendMode": "normal",
                   "playback": {"type": "windowed", "inputOffsetMs": 0, "inputRange": win,
                                "mapping": {"type": "linear", "input": win, "output": win}},
                   "transform": {"anchorPoint": [ax, ay], "position": [960, 540], "scale": [s0, s0], "rotation": 0, "opacity": 100},
                   "layers": list(reversed(children))})
    for prop in ("scaleX", "scaleY"):
        A.append({"type": "setFxPropertyKeyframes", "compositionId": "main", "property": {"layerId": gid, "propertyType": prop},
                  "keyframes": [key(f"cam{gid}{prop}", 0, s0), key(f"cam{gid}{prop}", d - 1, s1)]})
    return gid


def move(lid, pts):
    """Trajectoire d'un calque : [(temps local ms, x, y)]."""
    A.append({"type": "setFxPositionKeyframes", "compositionId": "main", "layerId": lid,
              "positionX": {"keyframes": [key(f"mx{lid}", t, x) for t, x, _ in pts]},
              "positionY": {"keyframes": [key(f"my{lid}", t, y) for t, _, y in pts]}})


def fade(lid, pts):
    A.append({"type": "setFxPropertyKeyframes", "compositionId": "main", "property": {"layerId": lid, "propertyType": "opacity"},
              "keyframes": [key(f"op{lid}", t, v) for t, v in pts]})


def build():
    nuit = lambda: cover("decor_calern_nuit")  # noqa: E731
    # Léa assise de profil à son poste (ses mains à la hauteur du bureau), le collègue dans la porte, à contre-jour
    lea_p = lambda: image("lea_profil_cut", 1215, 590, height=470)  # noqa: E731
    col = lambda: image("collegue_porte_cut", 152, 655, height=340)  # noqa: E731
    # 1. large (0–4 s) : le collègue apparaît dans la porte à 2,6 s
    c1 = col(); shot("1 Calern nuit, large", 0, 4000, [nuit(), lea_p(), c1], cam=(960, 560, 100, 105)); fade(c1["id"], [(2500, 0), (2900, 100)])
    # 2. la porte (4–6,5 s) : « On doit partir. »
    shot("2 Collègue à la porte", 4000, 6500, [nuit(), lea_p(), col()], cam=(400, 790, 250, 262))
    # 3. Léa (6,5–8 s) : la notification, elle baisse les yeux vers le téléphone
    shot("3 Léa, gros plan", 6500, 8000, [nuit(), lea_p(), col()], cam=(1330, 700, 230, 240))
    # 4. 8–16 s : insert du téléphone (incrusté par assemble.py)
    # 5. le collègue (16–18,5 s) : « Tu ne peux plus rien changer. »
    shot("5 Collègue", 16000, 18500, [nuit(), lea_p(), col()], cam=(410, 790, 255, 268))
    # 6. Léa s'est tournée vers lui (18,5–22 s) : « Je sais. Mais on peut encore comprendre ce qui nous arrive. »
    shot("6 Léa se tourne", 18500, 22000, [nuit(), image("lea_face_cut", 1225, 585, height=480), col()], cam=(1340, 720, 215, 232))
    # 7. collision (22–26 s) : la lumière monte jusqu'au blanc
    flash = {"type": "Shape", "id": nid(), "name": "Éclair blanc", "blendMode": "normal", "activeRange": {"start": 0, "duration": None},
             "transform": {"anchorPoint": [0, 0], "position": [0, 0], "scale": [100, 100], "rotation": 0, "opacity": 0}, "shape": None}
    A.append({"type": "createFxRectLayer", "compositionId": "main", "layerId": flash["id"], "name": "Éclair blanc", "insertIndex": 0,
              "activeRange": {"start": 22000, "duration": 4000}, "transform": T(0, 0, op=0), "rect": {"size": [1920, 1080], "fillColor": [1, 0.97, 0.92, 1]}})
    fade(flash["id"], [(0, 0), (1600, 0), (3700, 100), (3999, 100)])
    shot("7 Collision", 22000, 26000, [cover("decor_espace")], cam=(1150, 520, 100, 118))
    # 8. 26–30 s : noir absolu (rien)
    # 9. Calern de jour (30–34 s) : Léa au travail, le collègue passe avec son café, souriant
    cm = image("collegue_marche_cut", 1650, 560, height=420)
    shot("9 Calern jour", 30000, 34000, [cover("decor_calern_jour"), image("lea_profil_cut", 1290, 600, height=460), cm],
         cam=(1100, 600, 102, 106))
    move(cm["id"], [(0, 1700, 560), (3999, 820, 565)])
    # 10. plage (34–43 s) : le garçon court vers l'eau avec son seau, sa mère le rejoint ; « Heureusement… »
    g = image("garcon_court_cut", 1450, 650, height=360); m = image("mere_marche_cut", 2000, 450, height=560)
    shot("10 Plage", 34000, 43000, [cover("decor_plage"), g, m], cam=(900, 600, 100, 106))
    move(g["id"], [(0, 1450, 650), (4500, 820, 640), (8999, 700, 640)])
    move(m["id"], [(0, 2000, 450), (2200, 2000, 450), (7500, 1060, 455), (8999, 1000, 455)])


def main():
    ROOT.mkdir(); (ROOT / ".work").mkdir()
    proj = str(ROOT / "film_2d.tsrct")
    run = lambda *a: subprocess.run([TSRCT, *a], check=True, capture_output=True, text=True).stdout  # noqa: E731
    run("project", "create", "--project", proj)
    font = json.loads(run("project", "import-font", "--project", proj, "--file", str(FONT)))
    for a in ASSETS:
        run("project", "import-asset", "--project", proj, "--file", str(IMG / f"{a}.png"), "--asset-id", a, "--kind", "image")
    build()
    doc = json.loads(run("project", "inspect", "--project", proj))
    doc["dimensions"] = {"width": 1920, "height": 1080}; doc["duration"] = DUR / 1000
    black = {"type": "Shape", "id": 99, "name": "Fond noir", "blendMode": "normal", "activeRange": {"start": 0, "duration": DUR},
             "transform": {"anchorPoint": [0, 0], "position": [0, 0], "scale": [100, 100], "rotation": 0, "opacity": 100},
             "shape": {"path": {"commands": [{"type": "moveTo", "x": 0, "y": 0}, {"type": "lineTo", "x": 1920, "y": 0}, {"type": "lineTo", "x": 1920, "y": 1080},
                                             {"type": "lineTo", "x": 0, "y": 1080}, {"type": "close"}]},
                       "fills": [{"paint": {"type": "solid", "color": [0, 0, 0, 1]}, "fillRule": "nonZeroWinding", "blendMode": "normal", "opacity": 1}], "strokes": []}}
    doc["composition"]["layers"] = list(reversed(LAYERS)) + [black]
    (ROOT / ".work/doc.json").write_text(json.dumps(doc, ensure_ascii=False))
    run("project", "commit", "--project", proj, "--file", str(ROOT / ".work/doc.json"))
    # étiquette de fiction : visible jusqu'au noir de la collision (26 s), jamais au retour à la réalité
    A.append({"type": "createFxTextLayer", "compositionId": "main", "insertIndex": 0, "layerId": nid(), "name": "Étiquette",
              "activeRange": {"start": 0, "duration": 26000}, "transform": T(58, 74, op=80),
              "sourceText": {"text": "SIMULATION HYPOTHÉTIQUE", "fontFamily": font["fontFamily"], "fontStyle": font.get("fontStyle", "Bold"),
                             "fontSize": 24, "fillColor": [0.85, 0.87, 0.89, 1], "justification": "left"}})
    (ROOT / ".work/actions.json").write_text(json.dumps(A, ensure_ascii=False))
    out = json.loads(run("project", "apply", "--project", proj, "--actions", str(ROOT / ".work/actions.json")))
    print("actions :", out.get("appliedActions"), "avertissements :", out.get("warnings"))
    print(proj)


if __name__ == "__main__":
    main()
