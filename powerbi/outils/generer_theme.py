"""Génère velib_theme.json à partir de palette.json (thème Power BI, mode sombre, Segoe UI)."""
import commun as c

F, T, S, TY, G = c.F, c.T, c.S, c.TY, c.G
R = c.RAMPE
GRAS = TY["famille_gras"]
NORMAL = TY["famille"]


def solide(hexa):
    return {"solid": {"color": hexa}}


def texte(taille, couleur, famille=NORMAL):
    return {"fontFamily": famille, "fontSize": taille, "fontColor": solide(couleur)}


def theme():
    axe = {"show": True, "fontFamily": NORMAL, "fontSize": TY["taille_axe"], "labelColor": solide(T["secondaire"]),
           "showAxisTitle": False, "titleColor": solide(T["discret"]), "titleFontSize": TY["taille_axe"],
           "titleFontFamily": NORMAL, "gridlineShow": True, "gridlineColor": solide(F["grille"]), "gridlineThickness": 1,
           "gridlineStyle": "solid"}
    axe_cat = {**axe, "gridlineShow": False}
    legende = {"show": True, "fontFamily": NORMAL, "fontSize": TY["taille_label"], "labelColor": solide(T["secondaire"]),
               "position": "Top", "showTitle": False}
    etiquettes = {"fontFamily": NORMAL, "fontSize": TY["taille_label"], "color": solide(T["principal"])}
    return {
        "name": "Vélib Nuit",
        "dataColors": [S["penurie"], S["saturation"], S["panne"], S["pluie"], S["neutre"], R[3], R[5], R[1]],
        "good": S["neutre"], "neutral": S["neutre"], "bad": S["penurie"],
        "maximum": R[6], "center": R[3], "minimum": R[0], "null": F["grille"],
        "foreground": T["principal"], "foregroundNeutralSecondary": T["secondaire"],
        "foregroundNeutralTertiary": T["discret"], "foregroundLight": T["principal"], "foregroundDark": F["page"],
        "background": F["carte"], "backgroundLight": F["survol"], "backgroundNeutral": F["grille"], "backgroundDark": F["page"],
        "secondaryBackground": F["survol"], "tableAccent": S["penurie"], "accent": S["penurie"],
        "hyperlink": S["saturation"], "visitedHyperlink": S["pluie"], "disabledText": T["discret"],
        "textClasses": {
            "callout": {"fontSize": TY["taille_kpi"], "fontFace": GRAS, "color": T["principal"]},
            "title": {"fontSize": TY["taille_titre"], "fontFace": GRAS, "color": T["principal"]},
            "header": {"fontSize": TY["taille_titre"], "fontFace": GRAS, "color": T["principal"]},
            "label": {"fontSize": TY["taille_label"], "fontFace": NORMAL, "color": T["secondaire"]},
            "largeTitle": {"fontSize": TY["taille_titre"], "fontFace": GRAS, "color": T["principal"]},
            "boldLabel": {"fontSize": TY["taille_label"], "fontFace": GRAS, "color": T["principal"]},
            "dataTitle": {"fontSize": TY["taille_label"], "fontFace": NORMAL, "color": T["secondaire"]},
            "smallLabel": {"fontSize": TY["taille_axe"], "fontFace": NORMAL, "color": T["secondaire"]},
        },
        "visualStyles": {
            "*": {"*": {
                "background": [{"show": True, "color": solide(F["carte"]), "transparency": 0}],
                "border": [{"show": True, "color": solide(F["carte"]), "radius": G["rayon"], "width": 1}],
                "dropShadow": [{"show": False}],
                "title": [{"show": True, "alignment": "left", "titleWrap": True, "fontFamily": GRAS,
                           "fontSize": TY["taille_titre"], "fontColor": solide(T["principal"])}],
                "subTitle": [{"show": True, "alignment": "left", "titleWrap": True, "fontFamily": NORMAL,
                              "fontSize": TY["taille_sous_titre"], "fontColor": solide(T["secondaire"])}],
                "padding": [{"top": 12, "bottom": 12, "left": 16, "right": 16}],
                "visualHeader": [{"show": False}],
                "visualTooltip": [{"type": "Default", "titleFontColor": solide(T["principal"]),
                                   "valueFontColor": solide(T["secondaire"]), "fontSize": TY["taille_infobulle"],
                                   "fontFamily": NORMAL, "background": solide(F["survol"]), "transparency": 0}],
                "lockAspect": [{"show": False}],
            }},
            "page": {"*": {
                "background": [{"color": solide(F["page"]), "transparency": 0}],
                "outspace": [{"color": solide(F["page"]), "transparency": 0}],
            }},
            "card": {"*": {
                "labels": [{"color": solide(T["principal"]), "fontSize": TY["taille_kpi"], "fontFamily": GRAS}],
                "categoryLabels": [{"show": True, "color": solide(T["secondaire"]), "fontSize": TY["taille_label"],
                                    "fontFamily": NORMAL}],
            }},
            "slicer": {"*": {
                "header": [{"show": False}],
                "items": [{"fontColor": solide(T["principal"]), "fontFamily": NORMAL, "textSize": TY["taille_label"],
                           "background": solide(F["survol"])}],
            }},
            "tableEx": {"*": {
                "columnHeaders": [{"fontColor": solide(T["secondaire"]), "backColor": solide(F["carte"]),
                                   "fontFamily": GRAS, "fontSize": TY["taille_label"], "outline": "None"}],
                "values": [{"fontColor": solide(T["principal"]), "backColorPrimary": solide(F["carte"]),
                            "backColorSecondary": solide(F["carte"]), "fontFamily": NORMAL, "fontSize": TY["taille_label"]}],
                "grid": [{"gridHorizontal": True, "gridHorizontalColor": solide(F["grille"]), "gridVertical": False,
                          "outlineColor": solide(F["carte"]), "rowPadding": 4}],
                "total": [{"show": False}],
            }},
            "pivotTable": {"*": {
                "columnHeaders": [{"fontColor": solide(T["secondaire"]), "backColor": solide(F["carte"]),
                                   "fontFamily": NORMAL, "fontSize": TY["taille_label"]}],
                "rowHeaders": [{"fontColor": solide(T["principal"]), "backColor": solide(F["carte"]),
                                "fontFamily": NORMAL, "fontSize": TY["taille_label"]}],
                "values": [{"fontColor": solide(T["principal"]), "backColorPrimary": solide(F["carte"]),
                            "backColorSecondary": solide(F["carte"]), "fontFamily": NORMAL, "fontSize": TY["taille_label"]}],
            }},
            "lineChart": {"*": {"categoryAxis": [axe_cat], "valueAxis": [axe], "legend": [legende], "labels": [etiquettes],
                                "lineStyles": [{"strokeWidth": 3, "showMarker": False, "lineChartType": "smooth"}]}},
            "clusteredColumnChart": {"*": {"categoryAxis": [axe_cat], "valueAxis": [axe], "legend": [legende], "labels": [etiquettes]}},
            "scatterChart": {"*": {"categoryAxis": [axe_cat], "valueAxis": [axe], "legend": [legende]}},
            "textbox": {"*": {
                "background": [{"show": False}], "border": [{"show": False}], "title": [{"show": False}],
                "subTitle": [{"show": False}], "padding": [{"top": 0, "bottom": 0, "left": 0, "right": 0}],
            }},
        },
    }


if __name__ == "__main__":
    c.ecrire_json(c.RACINE / "velib_theme.json", theme())
    print("ok velib_theme.json")
