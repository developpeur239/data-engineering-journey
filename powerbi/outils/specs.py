"""Specs Vega-Lite (Deneb) des 7 visuels. Toutes les couleurs et tailles viennent de commun.py / palette.json.

Convention : `data: {"name": "dataset"}` ; pas de width/height (Deneb applique 'container') ;
les noms de champs sont ceux des champs liés dans Power BI (voir NOMS_CHAMPS dans generer_rapport.py).
"""
import json

import commun as c

FOND_PARIS = json.loads((c.RACINE / "deneb_specs" / "paris_fond.json").read_text(encoding="utf-8"))
VL = "https://vega.github.io/schema/vega-lite/v6.json"
F, T, S, TY = c.F, c.T, c.S, c.TY
JOURS_JS = "[" + ",".join(f"'{j}'" for j in c.JOURS) + "]"
HEURE_AXE = {"values": [0, 3, 6, 9, 12, 15, 18, 21], "labelExpr": "datum.value + ' h'", "title": None}
TAILLE_LABEL = TY["taille_label"]
TAILLE_AXE = TY["taille_axe"]


def rgba(hexa: str, a: float) -> str:
    h = hexa.lstrip("#")
    return f"rgba({int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)},{a})"


def survol(champs, quand="mouseover"):
    return {"name": "survol", "select": {"type": "point", "on": quand, "clear": "mouseout", "fields": champs}}


def bandes_pointe(hauteur_texte=True):
    """Bandes 7-10 h et 17-20 h, annotées."""
    couche = [{
        "data": {"values": [{"a": 7, "b": 10, "t": "pointe du matin"}, {"a": 17, "b": 20, "t": "pointe du soir"}]},
        "mark": {"type": "rect", "color": F["survol"], "opacity": 0.75, "cornerRadius": 4},
        "encoding": {"x": {"field": "a", "type": "quantitative"}, "x2": {"field": "b"},
                     "y": {"value": 0}, "y2": {"value": {"expr": "height"}}},
    }]
    if hauteur_texte:
        couche.append({
            "data": {"values": [{"m": 8.5, "t": "pointe du matin"}, {"m": 18.5, "t": "pointe du soir"}]},
            "mark": {"type": "text", "baseline": "bottom", "dy": -8, "fontSize": TAILLE_AXE, "color": T["discret"]},
            "encoding": {"x": {"field": "m", "type": "quantitative"}, "y": {"value": {"expr": "height"}}, "text": {"field": "t"}},
        })
    return couche


# --------------------------------------------------------------------------- 1. heatmap
def heatmap():
    x = {"field": "heure_du_jour", "type": "quantitative", "scale": {"domain": [0, 24], "nice": False},
         "axis": {**HEURE_AXE, "grid": False}}
    y = {"field": "jour_semaine_ordre", "type": "ordinal", "sort": "ascending",
         "axis": {"labelExpr": f"{JOURS_JS}[datum.value-1]", "title": None, "grid": False, "labelFontSize": TAILLE_LABEL,
                  "labelColor": T["secondaire"]}}
    return {
        "$schema": VL,
        "data": {"name": "dataset"},
        "padding": {"top": 26, "left": 6, "right": 14, "bottom": 6},
        "transform": [
            {"calculate": "datum.n_service > 0 ? datum.n_penurie / datum.n_service : null", "as": "taux_penurie"},
            {"calculate": "datum.n_service > 0 ? datum.n_saturation / datum.n_service : null", "as": "taux_saturation"},
            {"calculate": "datum.heure_du_jour + 1", "as": "heure_fin"},
            {"calculate": f"{JOURS_JS}[datum.jour_semaine_ordre - 1]", "as": "jour"},
            {"calculate": "(datum.heure_du_jour < 10 ? '0' : '') + datum.heure_du_jour + ' h – ' + (datum.heure_fin < 10 ? '0' : '') + datum.heure_fin + ' h'", "as": "plage"},
            {"joinaggregate": [{"op": "max", "field": "taux_penurie", "as": "taux_max"}]},
        ],
        "layer": [
            {   # repères des heures de pointe, au-dessus de la grille
                "data": {"values": [{"a": 7, "b": 10}, {"a": 17, "b": 20}]},
                "mark": {"type": "rule", "strokeWidth": 2, "color": T["discret"], "strokeCap": "round"},
                "encoding": {"x": {"field": "a", "type": "quantitative", "scale": {"domain": [0, 24], "nice": False}},
                             "x2": {"field": "b"}, "y": {"value": -8}},
            },
            {
                "data": {"values": [{"m": 8.5, "t": "pointe du matin"}, {"m": 18.5, "t": "pointe du soir"}]},
                "mark": {"type": "text", "baseline": "bottom", "dy": -14, "fontSize": TAILLE_AXE, "color": T["discret"]},
                "encoding": {"x": {"field": "m", "type": "quantitative", "scale": {"domain": [0, 24], "nice": False}},
                             "y": {"value": 0}, "text": {"field": "t"}},
            },
            {
                "params": [survol(["heure_du_jour", "jour_semaine_ordre"])],
                "mark": {"type": "rect", "cornerRadius": 4, "stroke": F["carte"], "strokeWidth": 2},
                "encoding": {
                    "x": x, "x2": {"field": "heure_fin"}, "y": y,
                    "color": {"field": "taux_penurie", "type": "quantitative",
                              "scale": {"range": c.RAMPE, "domainMin": 0},
                              "legend": {"title": "Pénurie (% des relevés)", "orient": "bottom", "direction": "horizontal",
                                         "gradientLength": 260, "gradientThickness": 8, "format": ".0%", "titleOrient": "left",
                                         "titleLimit": 220, "titlePadding": 14, "offset": 14}},
                    "opacity": {"condition": {"param": "survol", "value": 1}, "value": 0.4},
                    "tooltip": [
                        {"field": "jour", "type": "nominal", "title": "Jour"},
                        {"field": "plage", "type": "nominal", "title": "Heure (Paris)"},
                        {"field": "taux_penurie", "type": "quantitative", "title": "Pénurie", "format": ".1%"},
                        {"field": "taux_saturation", "type": "quantitative", "title": "Saturation", "format": ".1%"},
                        {"field": "n_service", "type": "quantitative", "title": "Relevés en service", "format": ",d"},
                    ],
                },
            },
            {   # anneau sur la case la plus tendue
                "transform": [{"filter": "datum.taux_penurie === datum.taux_max"}],
                "mark": {"type": "rect", "cornerRadius": 4, "fill": None, "stroke": T["principal"], "strokeWidth": 2, "tooltip": None},
                "encoding": {"x": x, "x2": {"field": "heure_fin"}, "y": y},
            },
        ],
    }


# --------------------------------------------------------------------------- 2. rythme de la journée
def rythme():
    ech = {"domain": [0, 23], "nice": False}
    x = {"field": "heure_du_jour", "type": "quantitative", "scale": ech, "axis": {**HEURE_AXE, "grid": False}}
    y = {"field": "taux", "type": "quantitative", "scale": {"domainMin": 0},
         "axis": {"format": ".0%", "title": None, "tickCount": 4}}

    def serie(cle, libelle, couleur):
        filtre = {"filter": f"datum.serie === '{cle}'"}
        degrade = {"gradient": "linear", "x1": 1, "y1": 1, "x2": 1, "y2": 0,
                   "stops": [{"offset": 0, "color": rgba(couleur, 0)}, {"offset": 1, "color": rgba(couleur, 0.38)}]}
        return [
            {"transform": [filtre], "mark": {"type": "area", "interpolate": "monotone", "line": False, "color": degrade,
                                             "tooltip": None},
             "encoding": {"x": x, "y": {**y, "stack": None}}},
            {"transform": [filtre], "mark": {"type": "line", "interpolate": "monotone", "strokeWidth": 3, "color": couleur,
                                             "strokeCap": "round", "tooltip": None},
             "encoding": {"x": x, "y": {**y, "stack": None}}},
            {   # pic de la série : point + étiquette directe
                "transform": [filtre, {"joinaggregate": [{"op": "max", "field": "taux", "as": "pic"}], "groupby": ["serie"]},
                              {"filter": "datum.taux === datum.pic"},
                              {"calculate": f"'{libelle} · pic à ' + datum.heure_du_jour + ' h'", "as": "etiquette"}],
                "layer": [
                    {"mark": {"type": "point", "filled": True, "opacity": 1, "size": 110, "color": couleur, "stroke": F["carte"], "strokeWidth": 2, "tooltip": None},
                     "encoding": {"x": x, "y": y}},
                    {"mark": {"type": "text", "align": "left", "dx": 12, "dy": -4, "fontSize": TAILLE_LABEL, "color": T["principal"],
                              "fontWeight": 600},
                     "encoding": {"x": x, "y": y, "text": {"field": "etiquette"}}},
                ],
            },
        ]

    return {
        "$schema": VL,
        "data": {"name": "dataset"},
        "padding": {"top": 10, "left": 6, "right": 14, "bottom": 6},
        "transform": [
            {"calculate": "datum.n_service > 0 ? datum.n_penurie / datum.n_service : null", "as": "penurie"},
            {"calculate": "datum.n_service > 0 ? datum.n_saturation / datum.n_service : null", "as": "saturation"},
            {"fold": ["penurie", "saturation"], "as": ["serie", "taux"]},
        ],
        "layer": [
            *bandes_pointe(),
            *serie("penurie", "Pénurie", S["penurie"]),
            *serie("saturation", "Saturation", S["saturation"]),
            {   # survol : règle verticale + infobulle commune aux deux séries
                "transform": [{"pivot": "serie", "value": "taux", "groupby": ["heure_du_jour"]},
                              {"calculate": "(datum.heure_du_jour < 10 ? '0' : '') + datum.heure_du_jour + ' h – ' + (datum.heure_du_jour + 1 < 10 ? '0' : '') + (datum.heure_du_jour + 1) + ' h'", "as": "plage"}],
                "params": [{"name": "survol", "select": {"type": "point", "fields": ["heure_du_jour"], "nearest": True,
                                                         "on": "mouseover", "clear": "mouseout"}}],
                "mark": {"type": "rule", "strokeWidth": 1, "color": T["discret"]},
                "encoding": {"x": x,
                             "opacity": {"condition": {"param": "survol", "empty": False, "value": 1}, "value": 0},
                             "tooltip": [{"field": "plage", "type": "nominal", "title": "Heure (Paris)"},
                                         {"field": "penurie", "type": "quantitative", "title": "Pénurie", "format": ".1%"},
                                         {"field": "saturation", "type": "quantitative", "title": "Saturation", "format": ".1%"}]},
            },
        ],
    }


# --------------------------------------------------------------------------- 3. carte stylisée
REPERES = [("Gare du Nord", 48.8809, 2.3553), ("Gare de Lyon", 48.8443, 2.3744), ("Montparnasse", 48.8421, 2.3219),
           ("Châtelet", 48.8584, 2.3470), ("République", 48.8675, 2.3636), ("Trocadéro", 48.8629, 2.2877)]


def carte():
    lon0, lat0 = 2.3488, 48.8566
    geo = {"longitude": {"field": "longitude", "type": "quantitative"}, "latitude": {"field": "latitude", "type": "quantitative"}}
    classes = ["moins de 2 %", "2 à 5 %", "5 à 10 %", "10 à 15 %", "15 à 20 %", "20 à 30 %", "plus de 30 %"]
    fond_legende = {"fillColor": F["carte"], "padding": 10, "cornerRadius": 8, "offset": 6}
    taux = {"field": "classe", "type": "ordinal", "sort": classes,
            "scale": {"domain": classes, "range": c.RAMPE},
            "legend": {"title": "Relevés en pénurie", "orient": "bottom-left", "symbolType": "square", "symbolSize": 170,
                       "rowPadding": 4, "symbolStrokeWidth": 0, "symbolOpacity": 1, **fond_legende}}
    taille = {"field": "capacite_max", "type": "quantitative", "scale": {"range": [10, 130], "zero": False},
              "legend": {"title": "Capacité (places)", "orient": "bottom-right", "values": [20, 40, 60], "rowPadding": 6,
                         "symbolFillColor": T["secondaire"], "symbolStrokeColor": T["secondaire"], "symbolOpacity": 1,
                         "symbolStrokeWidth": 0, **fond_legende}}

    def repere(**extra):
        return {"data": {"values": [{"nom": n, "latitude": la, "longitude": lo} for n, la, lo in REPERES]},
                "mark": {"type": "text", "fontSize": TAILLE_AXE, "dy": -11, "fontWeight": 600, "tooltip": None, **extra},
                "encoding": {**geo, "text": {"field": "nom"}}}

    return {
        "$schema": VL,
        "data": {"name": "dataset"},
        "padding": {"top": 6, "left": 6, "right": 6, "bottom": 6},
        "projection": {"type": "mercator", "center": [lon0, lat0], "scale": {"expr": "min(width / 0.0072, height / 0.0050)"}},
        "transform": [
            {"calculate": "datum.n_service > 0 ? datum.n_penurie / datum.n_service : null", "as": "taux"},
            {"filter": "isValid(datum.taux) && isValid(datum.latitude) && isValid(datum.longitude)"},
            {"calculate": "datum.taux < 0.02 ? 'moins de 2 %' : datum.taux < 0.05 ? '2 à 5 %' : datum.taux < 0.10 ? '5 à 10 %' : datum.taux < 0.15 ? '10 à 15 %' : datum.taux < 0.20 ? '15 à 20 %' : datum.taux < 0.30 ? '20 à 30 %' : 'plus de 30 %'", "as": "classe"},
        ],
        "layer": [
            # fond très discret : limite de Paris puis Seine et canaux (Open Data Paris, ODbL ; voir paris_fond.json)
            {"data": {"values": [FOND_PARIS["features"][0]]},
             "mark": {"type": "geoshape", "fill": F["survol"], "fillOpacity": 0.55, "stroke": F["grille"], "strokeWidth": 1, "tooltip": None}},
            {"data": {"values": [FOND_PARIS["features"][1]]},
             "mark": {"type": "geoshape", "fill": F["grille"], "fillOpacity": 0.8, "stroke": None, "tooltip": None}},
            {
                "params": [survol(["station_id"])],
                "mark": {"type": "circle", "strokeWidth": 0.8, "opacity": 1},
                "encoding": {**geo, "size": taille, "color": taux, "stroke": {"value": F["carte"]},
                             "order": {"field": "taux", "type": "quantitative"},
                             "fillOpacity": {"condition": {"param": "survol", "value": 0.95}, "value": 0.35},
                             "tooltip": [{"field": "station_nom", "type": "nominal", "title": "Station"},
                                         {"field": "capacite_max", "type": "quantitative", "title": "Capacité (places)", "format": ",d"},
                                         {"field": "taux", "type": "quantitative", "title": "Relevés en pénurie", "format": ".1%"},
                                         {"field": "n_service", "type": "quantitative", "title": "Relevés en service", "format": ",d"}]},
            },
            {   # halo : anneau clair autour de la station survolée, invisible sinon
                "mark": {"type": "circle", "fill": None, "stroke": T["principal"], "strokeWidth": 2, "tooltip": None},
                "encoding": {**geo, "size": {"value": 420},
                             "strokeOpacity": {"condition": {"param": "survol", "empty": False, "value": 0.9}, "value": 0}},
            },
            # repères d'orientation, par-dessus les stations (halo de la couleur de fond pour rester lisibles)
            repere(color=F["carte"], stroke=F["carte"], strokeWidth=5),
            repere(color=T["secondaire"]),
        ],
    }


# --------------------------------------------------------------------------- 4. haltères « sans panne → avec panne »
def haltere():
    cles = ["Taux pénurie sans panne", "Taux pénurie avec panne", "Taux saturation sans panne", "Taux saturation avec panne"]
    ligne = {"field": "ligne", "type": "nominal", "sort": {"field": "ordre"},
             "axis": {"title": None, "grid": True, "gridDash": [2, 5], "gridOpacity": 0.9, "labelFontSize": TAILLE_LABEL, "labelColor": T["principal"],
                      "labelExpr": "split(datum.label, ' · ')", "labelLineHeight": 16, "labelLimit": 160}}
    xs = {"type": "quantitative", "scale": {"domainMin": 0, "nice": True, "zero": True},
          "axis": {"format": ".0%", "title": None, "tickCount": 5, "grid": True}}
    return {
        "$schema": VL,
        "data": {"name": "dataset"},
        "padding": {"top": 30, "left": 6, "right": 90, "bottom": 6},
        "transform": [
            {"fold": cles, "as": ["cle", "valeur"]},
            {"calculate": "indexof(datum.cle, 'pénurie') >= 0 ? 'Pénurie' : 'Saturation'", "as": "indicateur"},
            {"calculate": "indexof(datum.cle, 'sans') >= 0 ? 'sans' : 'avec'", "as": "etat"},
            {"pivot": "etat", "value": "valeur", "groupby": ["periode", "indicateur"]},
            {"calculate": "(datum.avec - datum.sans) * 100", "as": "ecart"},
            {"calculate": "datum.indicateur + ' · ' + datum.periode", "as": "ligne"},
            {"calculate": "(datum.periode === 'Heure de pointe' ? 0 : 2) + (datum.indicateur === 'Pénurie' ? 0 : 1)", "as": "ordre"},
            {"calculate": "max(datum.avec, datum.sans)", "as": "borne"},
            {"calculate": "(datum.ecart >= 0 ? '+' : '−') + replace(format(abs(datum.ecart), '.1f'), '.', ',') + ' pts'", "as": "texte_ecart"},
        ],
        "layer": [
            {   # trait de liaison : toujours la couleur « panne » ; le signe +/− du texte dit le sens de l'écart
                "mark": {"type": "rule", "strokeWidth": 4, "strokeCap": "round", "color": S["panne"], "tooltip": None},
                "encoding": {"y": ligne, "x": {**xs, "field": "sans"}, "x2": {"field": "avec"},
                             "opacity": {"condition": {"param": "survol", "value": 1}, "value": 0.35}},
            },
            {   # « sans panne » : anneau neutre
                "mark": {"type": "point", "filled": True, "opacity": 1, "size": 190, "fill": F["carte"], "stroke": S["neutre"], "strokeWidth": 3, "tooltip": None},
                "encoding": {"y": ligne, "x": {**xs, "field": "sans"},
                             "opacity": {"condition": {"param": "survol", "value": 1}, "value": 0.35}},
            },
            {   # « avec panne » : disque plein, couleur de la panne
                "params": [survol(["ligne"])],
                "mark": {"type": "point", "filled": True, "opacity": 1, "size": 190, "color": S["panne"], "stroke": F["carte"], "strokeWidth": 2},
                "encoding": {"y": ligne, "x": {**xs, "field": "avec"},
                             "opacity": {"condition": {"param": "survol", "value": 1}, "value": 0.35},
                             "tooltip": [{"field": "ligne", "type": "nominal", "title": "Situation"},
                                         {"field": "sans", "type": "quantitative", "title": "Sans panne", "format": ".1%"},
                                         {"field": "avec", "type": "quantitative", "title": "Avec panne", "format": ".1%"},
                                         {"field": "texte_ecart", "type": "nominal", "title": "Écart"}]},
            },
            {   # écart en points, à droite de l'haltère
                "mark": {"type": "text", "align": "left", "dx": 16, "fontSize": TAILLE_LABEL + 2, "fontWeight": 600, "color": T["principal"], "tooltip": None},
                "encoding": {"y": ligne, "x": {**xs, "field": "borne"}, "text": {"field": "texte_ecart"}},
            },
            {   # légende directe, une seule fois (première ligne)
                "transform": [{"filter": "datum.ordre === 0"}],
                "layer": [
                    {"mark": {"type": "text", "align": "center", "dy": -26, "fontSize": TAILLE_AXE, "color": T["secondaire"]},
                     "encoding": {"y": ligne, "x": {**xs, "field": "sans"}, "text": {"value": "sans panne"}}},
                    {"mark": {"type": "text", "align": "center", "dy": -26, "fontSize": TAILLE_AXE, "color": T["secondaire"]},
                     "encoding": {"y": ligne, "x": {**xs, "field": "avec"}, "text": {"value": "avec panne"}}},
                ],
            },
        ],
    }


# --------------------------------------------------------------------------- 5. météo : barres
def meteo_barres():
    ordre = ["Sans pluie", "Pluie"]
    echelle = {"domain": ordre, "range": [S["neutre"], S["pluie"]]}
    return {
        "$schema": VL,
        "data": {"name": "dataset"},
        "padding": {"top": 26, "left": 6, "right": 14, "bottom": 6},
        "transform": [{"fold": ["Taux pénurie", "Taux saturation"], "as": ["cle", "taux"]},
                      {"calculate": "indexof(datum.cle, 'pénurie') >= 0 ? 'Pénurie' : 'Saturation'", "as": "indicateur"}],
        "encoding": {
            "x": {"field": "indicateur", "type": "nominal", "sort": ["Pénurie", "Saturation"],
                  "axis": {"title": None, "grid": False, "labelFontSize": TAILLE_LABEL + 1, "labelColor": T["principal"], "labelAngle": 0}},
            "xOffset": {"field": "pluie_libelle", "type": "nominal", "sort": ordre},
            "y": {"field": "taux", "type": "quantitative", "scale": {"domainMin": 0}, "axis": {"format": ".0%", "title": None, "tickCount": 4}},
        },
        "layer": [
            {"params": [survol(["pluie_libelle", "indicateur"])],
             "mark": {"type": "bar", "cornerRadiusTopLeft": 4, "cornerRadiusTopRight": 4, "stroke": F["carte"], "strokeWidth": 2},
             "encoding": {"color": {"field": "pluie_libelle", "type": "nominal", "scale": echelle,
                                    "legend": {"title": None, "orient": "bottom", "direction": "horizontal", "symbolType": "square", "offset": 14}},
                          "opacity": {"condition": {"param": "survol", "value": 1}, "value": 0.45},
                          "tooltip": [{"field": "indicateur", "type": "nominal", "title": "Indicateur"},
                                      {"field": "pluie_libelle", "type": "nominal", "title": "Météo"},
                                      {"field": "taux", "type": "quantitative", "title": "Taux", "format": ".1%"}]}},
            {"mark": {"type": "text", "dy": -8, "baseline": "bottom", "fontSize": TAILLE_LABEL, "fontWeight": 600, "color": T["principal"]},
             "encoding": {"text": {"field": "taux", "type": "quantitative", "format": ".1%"}}},
            {   # marge en haut de l'axe : point invisible à 125 % du maximum, pour que l'étiquette de la plus haute barre ne touche rien
                "transform": [{"joinaggregate": [{"op": "max", "field": "taux", "as": "maxi"}]},
                              {"calculate": "datum.maxi * 1.25", "as": "plafond"}],
                "mark": {"type": "point", "opacity": 0, "tooltip": None},
                "encoding": {"y": {"field": "plafond", "type": "quantitative"}}},
        ],
    }


# --------------------------------------------------------------------------- 6. météo : nuage température × pénurie
def meteo_nuage():
    echelle = {"domain": ["Sans pluie", "Pluie"], "range": [S["neutre"], S["pluie"]]}
    x = {"field": "temperature_c", "type": "quantitative", "scale": {"zero": False},
         "axis": {"title": None, "grid": False, "labelExpr": "datum.value + ' °C'"}}
    y = {"field": "Taux pénurie", "type": "quantitative", "scale": {"domainMin": 0},
         "axis": {"format": ".0%", "title": None, "tickCount": 4}}
    return {
        "$schema": VL,
        "data": {"name": "dataset"},
        "padding": {"top": 10, "left": 6, "right": 14, "bottom": 6},
        "transform": [{"calculate": "timeFormat(toDate(datum.heure_paris), '%d/%m %Hh')", "as": "quand"}],
        "layer": [
            {"params": [survol(["heure_paris"])],
             "mark": {"type": "circle", "size": 70, "stroke": F["carte"], "strokeWidth": 1},
             "encoding": {"x": x, "y": y,
                          "color": {"field": "pluie_libelle", "type": "nominal", "scale": echelle,
                                    "legend": {"title": None, "orient": "top-right", "direction": "horizontal", "offset": 4, "fillColor": F["carte"], "padding": 6, "cornerRadius": 6}},
                          "opacity": {"condition": {"param": "survol", "value": 0.95}, "value": 0.55},
                          "tooltip": [{"field": "quand", "type": "nominal", "title": "Heure"},
                                      {"field": "temperature_c", "type": "quantitative", "title": "Température (°C)", "format": ".1f"},
                                      {"field": "Taux pénurie", "type": "quantitative", "title": "Pénurie", "format": ".1%"},
                                      {"field": "pluie_libelle", "type": "nominal", "title": "Météo"}]}},
            {   # tendance lissée (loess), toutes heures confondues
                "transform": [{"loess": "Taux pénurie", "on": "temperature_c", "bandwidth": 0.6}],
                "layer": [
                    {"mark": {"type": "line", "color": T["principal"], "strokeWidth": 3, "strokeCap": "round", "tooltip": None},
                     "encoding": {"x": x, "y": y}},
                    {"transform": [{"window": [{"op": "last_value", "field": "temperature_c", "as": "tmax"}],
                                    "frame": [None, None], "sort": [{"field": "temperature_c"}]},
                                   {"filter": "datum.temperature_c === datum.tmax"}],
                     "layer": [
                         {"mark": {"type": "text", "align": "right", "dx": -6, "dy": -14, "fontSize": TAILLE_LABEL, "fontWeight": 600,
                                   "color": F["carte"], "stroke": F["carte"], "strokeWidth": 5, "text": "tendance lissée", "tooltip": None},
                          "encoding": {"x": x, "y": y}},
                         {"mark": {"type": "text", "align": "right", "dx": -6, "dy": -14, "fontSize": TAILLE_LABEL, "fontWeight": 600,
                                   "color": T["principal"], "text": "tendance lissée", "tooltip": None},
                          "encoding": {"x": x, "y": y}},
                     ]},
                ],
            },
        ],
    }


# --------------------------------------------------------------------------- 7. météo : courbes par heure
def meteo_courbes():
    echelle = {"domain": ["Sans pluie", "Pluie"], "range": [S["neutre"], S["pluie"]]}
    ech = {"domain": [0, 23], "nice": False}
    x = {"field": "heure_du_jour", "type": "quantitative", "scale": ech, "axis": {**HEURE_AXE, "grid": False}}
    y = {"field": "Taux pénurie", "type": "quantitative", "scale": {"domainMin": 0}, "axis": {"format": ".0%", "title": None, "tickCount": 4}}
    return {
        "$schema": VL,
        "data": {"name": "dataset"},
        "padding": {"top": 10, "left": 6, "right": 14, "bottom": 6},
        "layer": [
            *bandes_pointe(),
            {"mark": {"type": "line", "interpolate": "monotone", "strokeWidth": 3, "strokeCap": "round", "tooltip": None},
             "encoding": {"x": x, "y": y,
                          "color": {"field": "pluie_libelle", "type": "nominal", "scale": echelle,
                                    "legend": {"title": None, "orient": "top-right", "direction": "horizontal", "offset": 4, "fillColor": F["carte"], "padding": 6, "cornerRadius": 6}},
                          "strokeDash": {"field": "pluie_libelle", "type": "nominal", "scale": {"domain": ["Sans pluie", "Pluie"], "range": [[1, 0], [6, 4]]}}}},
            {   # survol : règle verticale, infobulle commune
                "transform": [{"pivot": "pluie_libelle", "value": "Taux pénurie", "groupby": ["heure_du_jour"]},
                              {"calculate": "(datum.heure_du_jour < 10 ? '0' : '') + datum.heure_du_jour + ' h – ' + (datum.heure_du_jour + 1 < 10 ? '0' : '') + (datum.heure_du_jour + 1) + ' h'", "as": "plage"}],
                "params": [{"name": "survol", "select": {"type": "point", "fields": ["heure_du_jour"], "nearest": True, "on": "mouseover", "clear": "mouseout"}}],
                "mark": {"type": "rule", "strokeWidth": 1, "color": T["discret"]},
                "encoding": {"x": x,
                             "opacity": {"condition": {"param": "survol", "empty": False, "value": 1}, "value": 0},
                             "tooltip": [{"field": "plage", "type": "nominal", "title": "Heure (Paris)"},
                                         {"field": "Sans pluie", "type": "quantitative", "title": "Sans pluie", "format": ".1%"},
                                         {"field": "Pluie", "type": "quantitative", "title": "Pluie", "format": ".1%"}]},
            },
        ],
    }


SPECS = {
    "01_heatmap_heure_jour": (heatmap, "heatmap"),
    "02_rythme_journee": (rythme, "rythme"),
    "03_carte_stations": (carte, "stations"),
    "04_haltere_pannes": (haltere, "pannes"),
    "05_meteo_barres": (meteo_barres, "meteo_barres"),
    "06_meteo_nuage": (meteo_nuage, "meteo_nuage"),
    "07_meteo_courbes": (meteo_courbes, "meteo_courbes"),
}
