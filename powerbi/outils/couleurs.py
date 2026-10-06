"""Un sens par couleur : relève les couleurs réellement utilisées par chaque spec Deneb et vérifie qu'elles respectent les rôles."""
import json
import re

import commun as c

S, F, T, R = c.S, c.F, c.T, c.RAMPE
NEUTRES_DECOR = {F["carte"], F["survol"], F["grille"], F["page"]}
TEXTES = set(T.values())
# rôles autorisés par spec (couleurs de données uniquement ; fonds et textes sont toujours permis)
AUTORISE = {
    "01_heatmap_heure_jour": set(R),
    "02_rythme_journee": {S["penurie"], S["saturation"]},
    "03_carte_stations": set(R),
    "04_haltere_pannes": {S["panne"], S["neutre"]},
    "05_meteo_barres": {S["pluie"], S["neutre"]},
    "06_meteo_nuage": {S["pluie"], S["neutre"]},
    "07_meteo_courbes": {S["pluie"], S["neutre"]},
}
SENS = [
    ("Orange braise", S["penurie"], "Pénurie : plus de vélo dans la station", "02 rythme (courbe et aire). Les cases et cercles de pénurie utilisent la rampe de même teinte (ci-dessous)."),
    ("Rampe « braise » (7 pas)", None, "Intensité de la pénurie, du presque-fond (peu) au pêche clair (beaucoup)", "01 heatmap, 03 carte"),
    ("Cyan", S["saturation"], "Saturation : plus de place libre dans la station", "02 rythme"),
    ("Rose / magenta", S["panne"], "Panne ferrée en cours à proximité (« avec panne »)", "04 haltères (disque et trait de liaison)"),
    ("Violet", S["pluie"], "Il pleut", "05 barres, 06 nuage, 07 courbes"),
    ("Gris bleuté", S["neutre"], "Situation de référence : « sans panne », « sans pluie »", "04 haltères, 05 barres, 06 nuage, 07 courbes"),
    ("Blanc cassé", T["principal"], "Texte, tendance, anneau de la valeur maximale : jamais une donnée", "01, 02, 03, 06"),
]


def _hex(v):
    v = v.lstrip("#").upper()
    return "#" + v[:6]


def couleurs_spec(spec) -> set:
    texte = json.dumps(spec, ensure_ascii=False)
    out = {_hex(h) for h in re.findall(r"#[0-9A-Fa-f]{6}(?![0-9A-Fa-f])", texte)}
    for r, g, b in re.findall(r"rgba\((\d+),(\d+),(\d+),", texte):
        out.add("#%02X%02X%02X" % (int(r), int(g), int(b)))
    return out


def verifier(specs: dict) -> list:
    """specs : nom -> dict de spec. Retourne la liste des violations."""
    erreurs = []
    donnees = {S["penurie"], S["saturation"], S["panne"], S["pluie"], S["neutre"], *R}
    connues = donnees | NEUTRES_DECOR | TEXTES
    for nom, spec in specs.items():
        utilisees = couleurs_spec(spec)
        hors_palette = utilisees - connues
        if hors_palette:
            erreurs.append(f"{nom} : couleur hors palette {sorted(hors_palette)}")
        interdites = (utilisees & donnees) - AUTORISE[nom]
        if interdites:
            erreurs.append(f"{nom} : couleur de données utilisée hors de son sens {sorted(interdites)}")
    return erreurs


def utilisations(specs: dict) -> dict:
    return {nom: couleurs_spec(s) for nom, s in specs.items()}
