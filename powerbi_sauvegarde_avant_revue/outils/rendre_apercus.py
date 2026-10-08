"""Rend chaque spec Vega-Lite en PNG (vl-convert) avec des données fictives, dans une « carte » façon Power BI.

Usage : python3 rendre_apercus.py [nom ...]   (sans argument : tous les visuels, puis planche.png)
Les aperçus ne remplacent pas un test dans Power BI Desktop : police de remplacement (Segoe UI absente sous Linux).
"""
import copy
import io
import json
import sys

import vl_convert as vlc
from PIL import Image, ImageDraw, ImageFont

import commun as c
import donnees_apercu as d
import specs as sp

TAILLES = {"01_heatmap_heure_jour": (608, 496), "02_rythme_journee": (608, 496), "03_carte_stations": (800, 616),
           "04_haltere_pannes": (800, 340), "05_meteo_barres": (400, 300), "06_meteo_nuage": (816, 300),
           "07_meteo_courbes": (816, 300), "08_meteo3_halteres_periode": (440, 244),
           "09_meteo3_effet_conditions_egales": (440, 244), "10_meteo3_classes_temperature": (440, 244),
           "11_meteo3_profil_horaire_semaine": (440, 244)}  # tailles des visuels dans la mise en page 1280 x 720 (voir DESIGN.md)


def _pc(x, n=1):
    """Pourcentage à la française : « 8,7 % » (espace insécable), comme FORMAT(x, "0.0%", "fr-FR")."""
    return f"{x * 100:.{n}f}".replace(".", ",") + "\u00a0%"


def _nb(n):
    """Entier à la française : « 1 450 » (espace fine insécable), comme FORMAT(n, "#,##0", "fr-FR")."""
    return f"{n:,}".replace(",", "\u202f")


def titre_sous_titre(nom, rows):
    """Reproduit ce que les mesures DAX « Titre … » afficheront, avec les données fictives (jamais écrit dans une spec)."""
    if nom == "01_heatmap_heure_jour":
        m = max(rows, key=lambda r: r["n_penurie"] / r["n_service"])
        return (f"Les pénuries culminent le {c.JOURS[m['jour_semaine_ordre'] - 1]} à {m['heure_du_jour']} h",
                "Part des relevés où la station est vide, par heure et jour de la semaine")
    if nom == "02_rythme_journee":
        m = max(rows, key=lambda r: r["n_penurie"] / r["n_service"])
        return (f"Les pénuries explosent à {m['heure_du_jour']} h",
                "Part des relevés en pénurie et en saturation, par heure de la journée")
    if nom == "03_carte_stations":
        n = sum(1 for r in rows if r["n_penurie"] / r["n_service"] > 0.2)
        return (f"{_nb(n)} stations sur {_nb(len(rows))} sont vides plus d'un relevé sur cinq",
                "Un cercle = une station : taille = capacité, couleur = part des relevés en pénurie")
    if nom == "04_haltere_pannes":
        p = next(r for r in rows if r["periode"] == "Heure de pointe")
        e = (p["Taux pénurie avec panne"] - p["Taux pénurie sans panne"]) * 100
        return (f"En heure de pointe, une panne ferrée à moins de 300 m {'augmente' if e >= 0 else 'réduit'} la pénurie de {abs(e):.1f} pts".replace(".", ","),
                "Part des relevés en pénurie et en saturation, sans puis avec panne en cours")
    if nom == "05_meteo_barres":
        sec = next(r for r in rows if r["pluie_libelle"] == "Sans pluie")
        plu = next(r for r in rows if r["pluie_libelle"] == "Pluie")
        return (f"Sous la pluie, la pénurie passe de {_pc(sec['Taux pénurie'])} à {_pc(plu['Taux pénurie'])}",
                "Part des relevés, selon qu'il pleut ou non")
    if nom == "06_meteo_nuage":
        seuil = rows[0]["seuil_temperature"]  # la même valeur que celle tracée sur le graphique
        chaud = [r["Taux pénurie"] for r in rows if r["temperature_c"] >= seuil]
        froid = [r["Taux pénurie"] for r in rows if r["temperature_c"] < seuil]
        return (f"Au-dessus de {seuil:.1f} °C, la pénurie est de {_pc(sum(chaud) / len(chaud))} contre {_pc(sum(froid) / len(froid))} en dessous".replace(".", ","),
                "Un point = une heure ; association observée, pas preuve de causalité")
    if nom == "08_meteo3_halteres_periode":
        p = next(x for x in rows if x["periode"] == "pointe")
        e = p["Passages avec pluie"] / p["Passages sans pluie"] - 1
        return (f"Aux heures de pointe, la pluie {'fait baisser' if e < 0 else 'fait monter'} les passages de {_pc(abs(e))}",
                "Source : compteurs de Paris, Open-Meteo, 2023-2025")
    if nom == "09_meteo3_effet_conditions_egales":
        s = next(x for x in rows if x["type_jour"] == "semaine")["Effet pluie à conditions égales (%)"]
        w = next(x for x in rows if x["type_jour"] == "week-end")["Effet pluie à conditions égales (%)"]
        f = lambda x: ("+" if x > 0 else "-" if x < 0 else "") + _pc(abs(x))  # noqa: E731
        return (f"Sous la pluie, à conditions égales : {f(s)} en semaine, {f(w)} le week-end",
                "Source : compteurs de Paris, Open-Meteo, 2023-2025")
    if nom == "10_meteo3_classes_temperature":
        m = max(rows, key=lambda x: x["Passages pointe temps sec"])
        return (f"Par temps sec, les passages en pointe culminent à {m['classe_temperature'][3:]} ({m['Passages pointe temps sec']:.1f} par compteur)".replace(".", ","),
                "Pointe, hors pluie. Source : compteurs de Paris, Open-Meteo, 2023-2025")
    if nom == "11_meteo3_profil_horaire_semaine":
        b = sum(1 for x in rows if x["Passages semaine avec pluie"] < x["Passages semaine sans pluie"])
        return (f"En semaine, la pluie fait baisser les passages à {b} heures sur {len(rows)}",
                "Source : compteurs de Paris, Open-Meteo, 2023-2025")
    par_heure = {}
    for r in rows:
        par_heure.setdefault(r["heure_du_jour"], {})[r["pluie_libelle"]] = r["Taux pénurie"]
    plus = sum(1 for v in par_heure.values() if v["Pluie"] > v["Sans pluie"])
    return (f"Sous la pluie, la pénurie est plus haute à {plus} heures sur {len(par_heure)}",
            "Part des relevés en pénurie par heure de la journée, avec et sans pluie")


DONNEES = {s: getattr(d, f) for s, (_, f) in sp.SPECS.items()}


def police(taille, gras=False):
    chemin = "/usr/share/fonts/truetype/liberation/LiberationSans-%s.ttf" % ("Bold" if gras else "Regular")
    return ImageFont.truetype(chemin, taille)


def rendre(nom, echelle=2):
    fabrique, _ = sp.SPECS[nom]
    spec = fabrique()
    w, h = TAILLES[nom]
    spec = copy.deepcopy(spec)
    rows = DONNEES[nom]()
    spec["data"] = {"values": rows}
    titre, sous = titre_sous_titre(nom, rows)
    f_titre, f_sous = police(c.TY["taille_titre"] * echelle, True), police(c.TY["taille_sous_titre"] * echelle)
    ligne_t, ligne_s = [], []

    def envelopper(texte, f, largeur):
        mots, lignes, cour = texte.split(" "), [], ""
        for m in mots:
            if f.getlength((cour + " " + m).strip()) <= largeur: cour = (cour + " " + m).strip()
            else: lignes.append(cour); cour = m
        return lignes + [cour]
    ligne_t = envelopper(titre, f_titre, (w - 32) * echelle)
    ligne_s = envelopper(sous, f_sous, (w - 32) * echelle)
    haut = 14 + 22 * len(ligne_t) + 17 * len(ligne_s) + 8  # hauteur de l'en-tête (px), comme un titre Power BI qui passe à la ligne
    spec["width"], spec["height"] = w - 24 - 6, h - haut - 6
    spec["autosize"] = {"type": "fit", "contains": "padding"}
    png = vlc.vegalite_to_png(spec, vl_version="v6.4", scale=echelle, config=c.config_commune(),
                              format_locale="fr-FR", time_format_locale="fr-FR", show_warnings=True)
    graphique = Image.open(io.BytesIO(png)).convert("RGBA")
    carte = Image.new("RGBA", (w * echelle, h * echelle), c.F["page"])
    dessin = ImageDraw.Draw(carte)
    dessin.rounded_rectangle((0, 0, w * echelle - 1, h * echelle - 1), radius=c.G["rayon"] * echelle, fill=c.F["carte"])
    y = 14 * echelle
    for l in ligne_t:
        dessin.text((16 * echelle, y), l, font=f_titre, fill=c.T["principal"]); y += 22 * echelle
    for l in ligne_s:
        dessin.text((16 * echelle, y), l, font=f_sous, fill=c.T["secondaire"]); y += 17 * echelle
    carte.alpha_composite(graphique, (12 * echelle, haut * echelle))
    return carte.convert("RGB"), spec


def planche():
    """Vue d'ensemble : les visuels côte à côte, pour juger l'harmonie (couleurs, typo, marges)."""
    out = c.RACINE / "apercus"
    noms = list(sp.SPECS)
    anciens, nouveaux = noms[:7], noms[7:]
    k = 0.5

    def charger(n, f=k):
        i = Image.open(out / f"{n}.png").convert("RGB")
        return i.resize((int(i.width * f), int(i.height * f)), Image.LANCZOS)
    imgs = {n: charger(n) for n in anciens}
    nov = {n: charger(n) for n in nouveaux}
    marge, entete = 24, 70
    colonnes = [[0, 2, 4], [1, 3, 5, 6]]
    lmax = max(i.width for i in imgs.values())
    largeur = max(marge * 3 + lmax * 2, marge * 3 + max(i.width for i in nov.values()) * 2)
    hauteurs = [sum(imgs[anciens[i]].height + marge for i in col) for col in colonnes]
    bloc2 = 60 + 2 * (max(i.height for i in nov.values()) + marge)
    toile = Image.new("RGB", (largeur, entete + max(hauteurs) + marge + bloc2), c.F["page"])
    d = ImageDraw.Draw(toile)
    d.text((marge, 18), "Aperçu : les visuels Deneb avec des données FICTIVES ou de référence (mise en page et couleurs, pas des résultats)",
           font=police(22, True), fill=c.T["principal"])
    d.text((marge, 46), "Rendu Vega-Lite 6.4 sous Linux, police de remplacement ; le rendu réel se fait dans Power BI Desktop.",
           font=police(14), fill=c.T["secondaire"])
    for j, col in enumerate(colonnes):
        y = entete
        for i in col:
            toile.paste(imgs[anciens[i]], (marge + j * (lmax + marge), y))
            y += imgs[anciens[i]].height + marge
    y0 = entete + max(hauteurs) + marge
    d.text((marge, y0 + 10), "Page « Météo · 3 ans de compteurs » : chiffres de référence de la table Databricks, profil horaire inventé",
           font=police(20, True), fill=c.T["principal"])
    lw = max(i.width for i in nov.values()); lh = max(i.height for i in nov.values())
    for idx, n in enumerate(nouveaux):
        toile.paste(nov[n], (marge + (idx % 2) * (lw + marge), y0 + 60 + (idx // 2) * (lh + marge)))
    toile.save(out / "planche.png")
    print("ok planche", toile.size)


def main(noms):
    out = c.RACINE / "apercus"
    out.mkdir(exist_ok=True)
    for nom in noms:
        img, _ = rendre(nom)
        img.save(out / f"{nom}.png")
        print("ok", nom, img.size)


if __name__ == "__main__":
    main(sys.argv[1:] or list(sp.SPECS))
    if not sys.argv[1:]:
        planche()
