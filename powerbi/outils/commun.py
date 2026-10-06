"""Éléments partagés par tous les visuels : palette, typographie, bloc `config` Vega-Lite commun.

Toutes les couleurs et tailles viennent de palette.json (source unique) : rien n'est codé en dur ailleurs.
"""
import json
import pathlib

ICI = pathlib.Path(__file__).parent
RACINE = ICI.parent
P = json.loads((ICI / "palette.json").read_text(encoding="utf-8"))
RAMPE = json.loads((ICI / "palette_calculee.json").read_text(encoding="utf-8"))["sequentiel_penurie"]

F, T, S, D, TY, G = P["fond"], P["texte"], P["serie"], P["divergent"], P["typo"], P["grille_page"]
# Police : Segoe UI d'abord ; les suivantes ne servent que si elle est absente (aperçus Linux).
POLICE = f"{TY['famille']}, Arial, Helvetica, sans-serif"

JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def config_commune() -> dict:
    """Bloc `config` identique pour tous les visuels Deneb (copié tel quel dans jsonConfig)."""
    texte = {"font": POLICE, "color": T["secondaire"]}
    return {
        "background": "transparent",
        "font": POLICE,
        "padding": {"left": 6, "right": 14, "top": 6, "bottom": 6},
        "view": {"stroke": None},
        "axis": {
            "domain": False, "ticks": False, "grid": True,
            "gridColor": F["grille"], "gridWidth": 1, "gridOpacity": 0.6,
            "labelFont": POLICE, "labelFontSize": TY["taille_axe"], "labelColor": T["secondaire"],
            "labelPadding": 8, "labelFontWeight": "normal",
            "titleFont": POLICE, "titleFontSize": TY["taille_axe"], "titleFontWeight": "normal",
            "titleColor": T["discret"], "titlePadding": 10,
        },
        "axisX": {"grid": False},
        "legend": {
            "labelFont": POLICE, "labelFontSize": TY["taille_label"], "labelColor": T["secondaire"],
            "titleFont": POLICE, "titleFontSize": TY["taille_axe"], "titleFontWeight": "normal",
            "titleColor": T["discret"], "symbolType": "circle", "symbolSize": 90,
            "padding": 0, "offset": 8, "orient": "top-left",
        },
        "text": texte,
        "mark": {"font": POLICE},
        "title": {"font": POLICE, "color": T["principal"], "fontSize": TY["taille_titre"],
                  "fontWeight": 600, "anchor": "start", "subtitleFont": POLICE,
                  "subtitleColor": T["secondaire"], "subtitleFontSize": TY["taille_sous_titre"]},
        "range": {"category": [S["penurie"], S["saturation"], S["panne"], S["pluie"], S["neutre"]],
                  "ramp": RAMPE, "heatmap": RAMPE},
        "customFormatTypes": True,
    }


def ecrire_json(chemin: pathlib.Path, obj) -> None:
    chemin.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
