"""Vérifie la palette de palette.json : contrastes WCAG, séparation daltonisme (Machado 2009), rampes.

Écrit palette_calculee.json (rampe séquentielle en hex) et affiche un rapport texte
(recopié dans DESIGN.md). Code de sortie 1 si un contrôle obligatoire échoue.
"""
import json, math, pathlib, sys
import numpy as np

ICI = pathlib.Path(__file__).parent
P = json.loads((ICI / "palette.json").read_text(encoding="utf-8"))


def hex2rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)])


def rgb2hex(c):
    c = np.clip(c, 0, 1)
    return "#" + "".join(f"{int(round(v * 255)):02X}" for v in c)


def lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def delin(c):
    return np.where(c <= 0.0031308, 12.92 * c, 1.055 * np.abs(c) ** (1 / 2.4) - 0.055)


M1 = np.array([[0.4122214708, 0.5363325363, 0.0514459929],
               [0.2119034982, 0.6806995451, 0.1073969566],
               [0.0883024619, 0.2817188376, 0.6299787005]])
M2 = np.array([[0.2104542553, 0.7936177850, -0.0040720468],
               [1.9779984951, -2.4285922050, 0.4505937099],
               [0.0259040371, 0.7827717662, -0.8086757660]])


def rgblin2oklab(c):
    return M2 @ np.cbrt(M1 @ c)


def oklab2rgblin(lab):
    l_ = np.linalg.inv(M2) @ lab
    return np.linalg.inv(M1) @ (l_ ** 3)


def oklch2hex(L, C, h):
    for c in np.linspace(C, 0, 200):  # réduit le chroma jusqu'à entrer dans le gamut sRVB
        lab = np.array([L, c * math.cos(math.radians(h)), c * math.sin(math.radians(h))])
        rgb = oklab2rgblin(lab)
        if np.all(rgb >= -1e-4) and np.all(rgb <= 1 + 1e-4):
            return rgb2hex(delin(np.clip(rgb, 0, 1)))
    return rgb2hex(np.array([L, L, L]))


def luminance(h):
    r, g, b = lin(hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


MACHADO = {
    "protanopie": np.array([[0.152286, 1.052583, -0.204868], [0.114503, 0.786281, 0.099216], [-0.003882, -0.048116, 1.051998]]),
    "deuteranopie": np.array([[0.367322, 0.860646, -0.227968], [0.280085, 0.672501, 0.047413], [-0.011820, 0.042940, 0.968881]]),
    "tritanopie": np.array([[1.255528, -0.076749, -0.178779], [-0.078411, 0.930809, 0.147602], [0.004733, 0.691367, 0.303900]]),
}


def lab(h, vision=None):
    c = lin(hex2rgb(h))
    if vision:
        c = np.clip(MACHADO[vision] @ c, 0, 1)
    return rgblin2oklab(c)


def de(a, b, vision=None):
    return 100 * float(np.linalg.norm(lab(a, vision) - lab(b, vision)))


def L_ok(h):
    return float(rgblin2oklab(lin(hex2rgb(h)))[0])


def main():
    echec = False
    rapport = []

    def ligne(ok, texte):
        nonlocal echec
        if ok is False:
            echec = True
        rapport.append(f"{'OK  ' if ok else 'ECHEC' if ok is False else 'info'} {texte}")

    f, t, s = P["fond"], P["texte"], P["serie"]
    rapport.append("## 1. Contraste du texte (WCAG, seuil AA = 4,5:1)")
    for nom, c in t.items():
        for sur in ("page", "carte", "survol"):
            r = contraste(c, f[sur])
            ligne(r >= 4.5, f"texte {nom} {c} sur fond {sur} {f[sur]} : {r:.2f}:1")
    rapport.append("\n## 2. Contraste des marques sur la carte (seuil 3:1)")
    for nom, c in s.items():
        r = contraste(c, f["carte"])
        ligne(r >= 3.0, f"{nom} {c} sur carte : {r:.2f}:1")
    rapport.append("\n## 3. Séparation des séries (OKLab ΔE×100, toutes les paires, vision normale / daltonismes)")
    cats = {k: s[k] for k in ("penurie", "saturation", "panne", "pluie")}
    noms = list(cats)
    pire = {}
    for i in range(len(noms)):
        for j in range(i + 1, len(noms)):
            a, b = cats[noms[i]], cats[noms[j]]
            v = {"normale": de(a, b), "protanopie": de(a, b, "protanopie"), "deuteranopie": de(a, b, "deuteranopie"), "tritanopie": de(a, b, "tritanopie")}
            ligne(v["normale"] >= 15 and min(v["protanopie"], v["deuteranopie"]) >= 6,
                  f"{noms[i]}↔{noms[j]} : normale {v['normale']:.1f} · protan {v['protanopie']:.1f} · deutan {v['deuteranopie']:.1f} · tritan {v['tritanopie']:.1f}")
    rapport.append("(seuils : vision normale ≥ 15 ; protan/deutan ≥ 6 ; chaque série est de plus étiquetée directement ou par la forme : jamais la couleur seule)")
    sq = P["sequentiel_penurie"]
    rampe = [oklch2hex(L, sq["C_max"] * k, sq["teinte_deg"] + (L - 0.6) * 20) for L, k in zip(sq["L"], sq["C_facteurs"])]
    rapport.append("\n## 4. Rampe séquentielle « braise » (taux de pénurie), sombre → clair, une seule teinte")
    for i, h in enumerate(rampe):
        rapport.append(f"info étape {i + 1} {h} L={L_ok(h):.2f} contraste/carte {contraste(h, f['carte']):.2f}:1")
    ls = [L_ok(h) for h in rampe]
    ligne(all(b - a >= 0.06 for a, b in zip(ls, ls[1:])), "luminosité strictement croissante (Δ L ≥ 0,06 entre étapes)")
    ligne(contraste(rampe[0], f["carte"]) >= 1.15, f"première étape discernable du fond de carte ({contraste(rampe[0], f['carte']):.2f}:1 ≥ 1,15)")
    # deutan/protan : la rampe reste ordonnée en luminosité
    for v in ("protanopie", "deuteranopie"):
        lv = [float(lab(h, v)[0]) for h in rampe]
        ligne(all(b > a for a, b in zip(lv, lv[1:])), f"rampe monotone en luminosité sous {v}")
    (ICI / "palette_calculee.json").write_text(json.dumps({"sequentiel_penurie": rampe}, indent=2), encoding="utf-8")
    texte = "\n".join(rapport)
    (ICI / "rapport_palette.txt").write_text(texte + "\n", encoding="utf-8")
    print(texte)
    sys.exit(1 if echec else 0)


main()
