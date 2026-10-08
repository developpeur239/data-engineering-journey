"""Écrit velib_dashboard.Report/ (format PBIR) : 4 pages + page cachée « Secours », visuels Deneb et natifs.

Aucun secret : la connexion à Databricks est dans le modèle sémantique (paramètres), le jeton est saisi dans Power BI.
"""
import json
import shutil

import commun as c
import generer_specs as gs
import specs as sp

NOM = "velib_dashboard"
DOSSIER = c.RACINE / f"{NOM}.Report"
DEF = DOSSIER / "definition"
T = "gold_station_heure"
T2 = "gold_velo_meteo_heure"
ENT = {"courante": T}  # table utilisée par les fabriques de champs (changée le temps de construire la page « Météo · 3 ans »)
DENEB = "deneb7E15AEF80B9E4D4F8E12924291ECE89A"
SCH = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"
V_VISUEL, V_PAGE, V_RAPPORT = "2.7.0", "2.0.0", "3.2.0"
F, TX, S, TY, G = c.F, c.T, c.S, c.TY, c.G
M = G["marge"]
GOUT = G["gouttiere"]

# ------------------------------------------------------------------ expressions Power BI


def lit(v):
    return {"expr": {"Literal": {"Value": v}}}


def chaine(t):
    return lit("'" + t.replace("'", "''") + "'")


def num(n):
    return lit(f"{n}D")


def booleen(b):
    return lit("true" if b else "false")


def couleur(h):
    return {"solid": {"color": lit(f"'{h}'")}}


def champ(nom, mesure=False):
    return {("Measure" if mesure else "Column"): {"Expression": {"SourceRef": {"Entity": ENT["courante"]}}, "Property": nom}}


def projection(nom, mesure=False, actif=False):
    p = {"field": champ(nom, mesure), "queryRef": f"{ENT['courante']}.{nom}", "nativeQueryRef": nom}
    if actif:
        p["active"] = True
    return p


def mesure_expr(nom):
    return {"expr": {"Measure": {"Expression": {"SourceRef": {"Entity": ENT["courante"]}}, "Property": nom}}}


# ------------------------------------------------------------------ éléments communs


def position(x, y, w, h, z=0, ordre=0):
    return {"x": x, "y": y, "z": z, "height": h, "width": w, "tabOrder": ordre}


def conteneur(titre=None, sous_titre=None, titre_mesure=None, alt=None, affiche_titre=True):
    """visualContainerObjects : titre (texte fixe ou mesure), sous-titre, texte alternatif."""
    o = {}
    if titre_mesure or titre:
        o["title"] = [{"properties": {"show": booleen(affiche_titre),
                                      "text": mesure_expr(titre_mesure) if titre_mesure else chaine(titre)}}]
    else:
        o["title"] = [{"properties": {"show": booleen(False)}}]
    if sous_titre:
        o["subTitle"] = [{"properties": {"show": booleen(True), "text": chaine(sous_titre)}}]
    if alt:
        o["general"] = [{"properties": {"altText": chaine(alt)}}]
    return o


def visuel(nom, pos, visual, filtres=None):
    d = {"$schema": f"{SCH}/visualContainer/{V_VISUEL}/schema.json", "name": nom, "position": pos, "visual": visual}
    if filtres:
        d["filterConfig"] = {"filters": filtres}
    return d


# ------------------------------------------------------------------ visuels


def zone_texte(nom, pos, paragraphes):
    """Boîte de texte (titre de page, « Méthode », « Lecture »). paragraphes = [(texte, pt, gras, couleur)]."""
    paras = [{"textRuns": [{"value": t, "textStyle": {"fontFamily": TY["famille_gras"] if g else TY["famille"],
                                                      "fontSize": f"{pt}pt", **({"fontWeight": "600"} if g else {}),
                                                      "color": col}}]} for t, pt, g, col in paragraphes]
    return visuel(nom, pos, {"visualType": "textbox", "objects": {"general": [{"properties": {"paragraphs": paras}}]},
                              "visualContainerObjects": {"title": [{"properties": {"show": booleen(False)}}],
                                                         "background": [{"properties": {"show": booleen(False)}}],
                                                         "border": [{"properties": {"show": booleen(False)}}]},
                              "drillFilterOtherVisuals": True})


def entete(nom, titre, sous):
    return zone_texte(f"{nom}_titre", position(M, 12, 700, 56, 10, 0),
                      [(titre, 22, True, TX["principal"]), (sous, 12, False, TX["secondaire"])])


def carte_kpi(nom, mesure, pos, alt, ordre):
    return visuel(nom, pos, {"visualType": "card",
                             "query": {"queryState": {"Values": {"projections": [projection(mesure, True)]}}},
                             "visualContainerObjects": conteneur(alt=alt, affiche_titre=False),
                             "drillFilterOtherVisuals": True})


def segmentation(nom, colonne, pos, titre, mode, ordre):
    return visuel(nom, pos, {
        "visualType": "slicer",
        "query": {"queryState": {"Values": {"projections": [projection(colonne, False, True)]}}},
        "objects": {"data": [{"properties": {"mode": chaine(mode)}}],
                    "header": [{"properties": {"show": booleen(False)}}]},
        "visualContainerObjects": {
            "title": [{"properties": {"show": booleen(True), "text": chaine(titre), "fontSize": num(11),
                                      "fontColor": couleur(TX["secondaire"])}}],
            "padding": [{"properties": {"top": num(6), "bottom": num(6), "left": num(10), "right": num(10)}}]},
        "drillFilterOtherVisuals": True})


def deneb(nom, cle_spec, pos, titre_mesure, sous_titre, alt):
    fabrique, _ = sp.SPECS[cle_spec]
    spec = json.dumps(fabrique(), ensure_ascii=False, separators=(",", ":"))
    config = json.dumps(c.config_commune(), ensure_ascii=False, separators=(",", ":"))
    projections = [projection(n, t == "mesure") for t, n in gs.CHAMPS[cle_spec]]
    return visuel(nom, pos, {
        "visualType": DENEB,
        "query": {"queryState": {"dataset": {"projections": projections}}},
        "objects": {
            "vega": [{"properties": {"provider": chaine("vegaLite"), "jsonSpec": chaine(spec), "jsonConfig": chaine(config),
                                     "renderMode": chaine("svg"), "enableTooltips": booleen(True),
                                     "enableContextMenu": booleen(True), "enableHighlight": booleen(False),
                                     "enableSelection": booleen(False)}}],
            "developer": [{"properties": {"locale": chaine("fr-FR")}}],
            # lève la limite de lignes par défaut de Deneb (voir README, « Limite de lignes »)
            "dataLimit": [{"properties": {"override": booleen(True)}}],
            "stateManagement": [{"properties": {"denebMetaVersion": chaine("2"), "supportFieldConfiguration": chaine("{}")}}],
        },
        "visualContainerObjects": conteneur(titre_mesure=titre_mesure, sous_titre=sous_titre, alt=alt),
        "drillFilterOtherVisuals": True})


def filtre_top_n(colonne, mesure, n):
    """Filtre « N premiers » au niveau du visuel (même JSON que celui écrit par Power BI Desktop)."""
    col = {"Column": {"Expression": {"SourceRef": {"Source": "g"}}, "Property": colonne}}
    return {"name": "top20_stations", "field": champ(colonne), "type": "TopN",
            "filter": {"Version": 2,
                       "From": [{"Name": "subquery", "Expression": {"Subquery": {"Query": {
                           "Version": 2, "From": [{"Name": "g", "Entity": T, "Type": 0}],
                           "Select": [{**col, "Name": "field"}],
                           "OrderBy": [{"Direction": 2, "Expression": {"Measure": {"Expression": {"SourceRef": {"Source": "g"}}, "Property": mesure}}}],
                           "Top": n}}}, "Type": 2},
                                {"Name": "g", "Entity": T, "Type": 0}],
                       "Where": [{"Condition": {"In": {"Expressions": [col], "Table": {"SourceRef": {"Source": "subquery"}}}}}]}}


def tableau_top(nom, pos, alt):
    cols = [("station_nom", False), ("capacite", False), ("Taux pénurie", True), ("Taux saturation", True)]
    return visuel(nom, pos, {
        "visualType": "tableEx",
        "query": {"queryState": {"Values": {"projections": [projection(n, m) for n, m in cols]}},
                  "sortDefinition": {"sort": [{"field": champ("Taux pénurie", True), "direction": "Descending"}], "isDefaultSort": False}},
        "visualContainerObjects": conteneur(titre="Les 20 stations les plus souvent vides",
                                            sous_titre="Classement sur la sélection en cours (heures, jours, période)", alt=alt),
        "drillFilterOtherVisuals": True}, filtres=[filtre_top_n("station_nom", "Taux pénurie", 20)])


# --- visuels natifs de la page « Secours »

def natif(nom, type_visuel, pos, roles, titre, sous_titre, alt, objets=None):
    qs = {role: {"projections": [projection(n, m, a) for n, m, a in projs]} for role, projs in roles.items()}
    v = {"visualType": type_visuel, "query": {"queryState": qs},
         "visualContainerObjects": conteneur(titre=titre, sous_titre=sous_titre, alt=alt), "drillFilterOtherVisuals": True}
    if objets:
        v["objects"] = objets
    return visuel(nom, pos, v)


def fond_degrade(mesure):
    """Mise en forme conditionnelle : dégradé de la rampe « braise » (min → max) sur la couleur de fond."""
    return {"properties": {"backColor": {"solid": {"color": {"expr": {"FillRule": {
        "Input": champ(mesure, True),
        "FillRule": {"linearGradient2": {
            "min": {"color": {"Literal": {"Value": f"'{c.RAMPE[0]}'"}}},
            "max": {"color": {"Literal": {"Value": f"'{c.RAMPE[6]}'"}}},
            "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'noColor'"}}}}}}}}}}},
        "selector": {"data": [{"dataViewWildcard": {"matchingOption": 1}}], "metadata": f"{T}.{mesure}"}}


def remplissage(hexa, selecteur=None):
    """Couleur d'une série d'un visuel natif (un sens par couleur : voir DESIGN.md §11)."""
    e = {"properties": {"fill": couleur(hexa)}}
    if selecteur:
        e["selector"] = selecteur
    return e


def par_mesure(nom):
    return {"metadata": f"{ENT['courante']}.{nom}"}


def par_valeur(colonne, valeur):
    return {"data": [{"scopeId": {"Comparison": {"ComparisonKind": 0, "Left": champ(colonne), "Right": {"Literal": {"Value": f"'{valeur}'"}}}}}]}


# ------------------------------------------------------------------ pages


def page(nom, titre, visuels, cachee=False, interactions=None):
    p = {"$schema": f"{SCH}/page/{V_PAGE}/schema.json", "name": nom, "displayName": titre, "displayOption": "FitToPage",
         "height": G["hauteur"], "width": G["largeur"],
         "objects": {"background": [{"properties": {"color": couleur(F["page"]), "transparency": num(0)}}],
                     "outspace": [{"properties": {"color": couleur(F["page"]), "transparency": num(0)}}]}}
    if cachee:
        p["visibility"] = "HiddenInViewMode"
    if interactions:
        p["visualInteractions"] = interactions
    return nom, titre, p, visuels


def pages():
    LARG = G["largeur"] - 2 * M            # 1232
    haut_kpi = 104
    y_kpi, y_graph = 80, 200
    h_graph = G["hauteur"] - M - y_graph   # 496
    col2 = (LARG - GOUT) // 2              # 608
    res = []

    # 1. Vue d'ensemble
    nom = "p1_vue_ensemble"
    w_kpi = (LARG - 3 * GOUT) // 4         # 296
    v = [entete(nom, "Vue d'ensemble", "Pénuries et saturations des stations Vélib', heure de Paris"),
         segmentation(f"{nom}_seg_date", "date_paris", position(744, 8, 328, 64, 20, 1), "Période", "Between", 1),
         segmentation(f"{nom}_seg_weekend", "est_weekend", position(1088, 8, 168, 64, 21, 2), "Week-end", "Dropdown", 2)]
    for i, (m, alt) in enumerate([("Nb stations", "Nombre de stations Vélib' observées"),
                                  ("Taux pénurie", "Part des relevés où la station n'a plus de vélo"),
                                  ("Taux saturation", "Part des relevés où la station n'a plus de place libre"),
                                  ("Dernière heure", "Dernière heure de relevé disponible, heure de Paris")]):
        v.append(carte_kpi(f"{nom}_kpi{i + 1}", m, position(M + i * (w_kpi + GOUT), y_kpi, w_kpi, haut_kpi, 5, 3 + i), alt, 3 + i))
    v.append(deneb(f"{nom}_heatmap", "01_heatmap_heure_jour", position(M, y_graph, col2, h_graph, 5, 7), "Titre heatmap",
                   "Part des relevés où la station est vide, par heure et jour de la semaine",
                   "Carte de chaleur : taux de pénurie par heure du jour et jour de la semaine"))
    v.append(deneb(f"{nom}_rythme", "02_rythme_journee", position(M + col2 + GOUT, y_graph, col2, h_graph, 5, 8), "Titre rythme",
                   "Part des relevés en pénurie et en saturation, par heure de la journée",
                   "Courbes du taux de pénurie et du taux de saturation par heure, avec les heures de pointe en repère"))
    res.append(page(nom, "Vue d'ensemble", v))

    # 2. Carte des stations
    nom = "p2_carte"
    larg_carte, larg_tab = 800, LARG - 800 - GOUT
    h2 = G["hauteur"] - M - y_kpi
    carte_id, tab_id = f"{nom}_carte", f"{nom}_top20"
    v = [entete(nom, "Carte des stations", "Où manque-t-on de vélos, à quelle heure ?"),
         segmentation(f"{nom}_seg_heure", "heure_du_jour", position(744, 8, 328, 64, 20, 1), "Heure du jour (Paris)", "Between", 1),
         segmentation(f"{nom}_seg_pointe", "heure_de_pointe", position(1088, 8, 168, 64, 21, 2), "Heure de pointe", "Dropdown", 2),
         deneb(carte_id, "03_carte_stations", position(M, y_kpi, larg_carte, h2, 5, 3), "Titre carte",
               "Un cercle = une station : taille = capacité, couleur = part des relevés en pénurie",
               "Carte stylisée des stations : taille selon la capacité, couleur selon le taux de pénurie"),
         tableau_top(tab_id, position(M + larg_carte + GOUT, y_kpi, larg_tab, h2, 5, 4),
                     "Tableau des 20 stations avec le plus fort taux de pénurie")]
    inter = [{"source": tab_id, "target": carte_id, "type": "NoFilter"}, {"source": carte_id, "target": tab_id, "type": "NoFilter"}]
    res.append(page(nom, "Carte des stations", v, interactions=inter))

    # 3. Effet des pannes
    nom = "p3_pannes"
    w3 = (LARG - 2 * GOUT) // 3            # 400
    v = [entete(nom, "Effet des pannes", "Stations à moins de 300 m d'un arrêt de métro, RER ou tramway"),
         segmentation(f"{nom}_seg_imprevue", "panne_ferree_imprevue_300m", position(1056, 8, 200, 64, 20, 1), "Panne imprévue", "Dropdown", 1)]
    for i, (m, alt) in enumerate([("Écart pénurie (pts)", "Écart de pénurie en points de pourcentage, avec panne moins sans panne"),
                                  ("Écart saturation (pts)", "Écart de saturation en points de pourcentage, avec panne moins sans panne"),
                                  ("Part heures avec panne ferrée", "Part des heures-stations avec une panne ferrée à moins de 300 m")]):
        v.append(carte_kpi(f"{nom}_kpi{i + 1}", m, position(M + i * (w3 + GOUT), y_kpi, w3, haut_kpi, 5, 2 + i), alt, 2 + i))
    larg_h = 800
    h_halt = 340
    v.append(deneb(f"{nom}_haltere", "04_haltere_pannes", position(M, y_graph, larg_h, h_halt, 5, 5), "Titre pannes",
                   "Part des relevés en pénurie et en saturation, sans puis avec panne en cours",
                   "Haltères : taux de pénurie et de saturation sans panne puis avec panne, en heure de pointe et hors pointe"))
    methode = [("Méthode", 16, True, TX["principal"]),
               ("Stations concernées : celles situées à moins de 300 m d'un arrêt de métro, de RER ou de tramway.", 12, False, TX["secondaire"]),
               ("Comparaison : on met côte à côte les heures où une perturbation ferrée est en cours à proximité (« avec panne ») "
                "et celles où le réseau fonctionne normalement (« sans panne »).", 12, False, TX["secondaire"]),
               ("Écart : différence, en points de pourcentage, entre la part de relevés en pénurie (ou en saturation) avec et sans panne.", 12, False, TX["secondaire"]),
               ("Filtre « Panne imprévue » : ne garde, pour « avec panne », que les perturbations non planifiées.", 12, False, TX["secondaire"]),
               ("À retenir : une association n'est pas une preuve de causalité (l'heure, le jour et la météo jouent aussi). "
                "Les données ne couvrent encore que quelques jours : les écarts peuvent changer.", 12, False, TX["principal"])]
    lect = [("Comment lire le graphique", 14, True, TX["principal"]),
            ("Anneau gris : part des relevés sans panne à proximité. Disque rose : part avec panne. Plus le disque est à droite de l'anneau, "
             "plus la panne s'accompagne de pénurie (ou de saturation). Le signe + ou − dit le sens de l'écart.", 12, False, TX["secondaire"])]
    zl = zone_texte(f"{nom}_lecture", position(M, y_graph + h_halt + GOUT, larg_h, h_graph - h_halt - GOUT, 5, 7), lect)
    zl["visual"]["visualContainerObjects"]["background"] = [{"properties": {"show": booleen(True), "color": couleur(F["carte"]), "transparency": num(0)}}]
    zl["visual"]["visualContainerObjects"]["padding"] = [{"properties": {"top": num(14), "bottom": num(14), "left": num(18), "right": num(18)}}]
    v.append(zl)
    zt = zone_texte(f"{nom}_methode", position(M + larg_h + GOUT, y_graph, LARG - larg_h - GOUT, h_graph, 5, 6), methode)
    # carte de fond sous le texte (la boîte de texte est transparente)
    zt["visual"]["visualContainerObjects"]["background"] = [{"properties": {"show": booleen(True), "color": couleur(F["carte"]),
                                                                           "transparency": num(0)}}]
    zt["visual"]["visualContainerObjects"]["padding"] = [{"properties": {"top": num(16), "bottom": num(16), "left": num(18), "right": num(18)}}]
    v.append(zt)
    res.append(page(nom, "Effet des pannes", v))

    # 4. Effet de la météo
    nom = "p4_meteo"
    w_gauche = 400
    w_droite = LARG - w_gauche - GOUT
    h4 = (G["hauteur"] - M - y_kpi - GOUT) // 2    # 300
    v = [entete(nom, "Effet de la météo", "La pluie et la température changent-elles la pénurie ou la saturation ?"),
         deneb(f"{nom}_barres", "05_meteo_barres", position(M, y_kpi, w_gauche, h4, 5, 1), "Titre pluie",
               "Part des relevés, selon qu'il pleut ou non",
               "Barres : taux de pénurie et de saturation avec et sans pluie"),
         deneb(f"{nom}_nuage", "06_meteo_nuage", position(M + w_gauche + GOUT, y_kpi, w_droite, h4, 5, 2), "Titre nuage",
               "Un point = une heure ; association observée, pas preuve de causalité",
               "Nuage de points : température et taux de pénurie, avec tendance lissée"),
         deneb(f"{nom}_courbes", "07_meteo_courbes", position(M + w_gauche + GOUT, y_kpi + h4 + GOUT, w_droite, h4, 5, 3), "Titre courbes",
               "Part des relevés en pénurie par heure de la journée, avec et sans pluie",
               "Courbes du taux de pénurie par heure, avec et sans pluie")]
    lecture = [("Comment lire cette page", 16, True, TX["principal"]),
               ("Barres : pénurie et saturation selon qu'il pleut ou non (météo Open-Meteo, Paris).", 12, False, TX["secondaire"]),
               ("Nuage : un point est une heure ; la ligne blanche est une tendance lissée (loess), à lire comme une indication.", 12, False, TX["secondaire"]),
               ("Courbes : même profil horaire avec et sans pluie ; les bandes grisées sont les heures de pointe (7–10 h et 17–20 h).", 12, False, TX["secondaire"]),
               ("Peu de jours de données : les différences observées sont indicatives, pas démontrées.", 12, False, TX["principal"])]
    zt = zone_texte(f"{nom}_lecture", position(M, y_kpi + h4 + GOUT, w_gauche, h4, 5, 4), lecture)
    zt["visual"]["visualContainerObjects"]["background"] = [{"properties": {"show": booleen(True), "color": couleur(F["carte"]),
                                                                           "transparency": num(0)}}]
    zt["visual"]["visualContainerObjects"]["padding"] = [{"properties": {"top": num(16), "bottom": num(16), "left": num(18), "right": num(18)}}]
    v.append(zt)
    res.append(page(nom, "Effet de la météo", v))

    # 4 bis. Météo · 3 ans de compteurs (table gold_velo_meteo_heure, indépendante de gold_station_heure)
    ENT["courante"] = T2
    nom = "p4b_meteo3"
    h_kpi, y_g2 = 96, 192
    h_row = (G["hauteur"] - M - y_g2 - GOUT) // 2          # 244
    w_c = (LARG - 320 - 2 * GOUT) // 2                      # 448 ; colonne « méthode » de 320 px
    x2 = M + w_c + GOUT
    src = "Source : compteurs de Paris, Open-Meteo, 2023-2025"
    v = [entete(nom, "Météo · 3 ans de compteurs", src),
         segmentation(f"{nom}_seg_jour", "type_jour", position(640, 8, 200, 64, 20, 1), "Type de jour", "Dropdown", 1),
         segmentation(f"{nom}_seg_saison", "saison_libelle", position(856, 8, 200, 64, 21, 2), "Saison", "Dropdown", 2),
         segmentation(f"{nom}_seg_annee", "annee", position(1072, 8, 184, 64, 22, 3), "Année", "Dropdown", 3)]
    w4 = (LARG - 3 * GOUT) // 4                             # 296
    for i, (m, alt) in enumerate([("Effet pluie semaine (%)", "Effet de la pluie sur les passages en semaine, à conditions égales"),
                                  ("Effet pluie week-end (%)", "Effet de la pluie sur les passages le week-end, à conditions égales"),
                                  ("Heures étudiées", "Nombre d'heures de comptage étudiées"),
                                  ("Part des heures de pluie (%)", "Part des heures où il pleut")]):
        v.append(carte_kpi(f"{nom}_kpi{i + 1}", m, position(M + i * (w4 + GOUT), y_kpi, w4, h_kpi, 5, 4 + i), alt, 4 + i))
    v += [deneb(f"{nom}_halteres", "08_meteo3_halteres_periode", position(M, y_g2, w_c, h_row, 5, 8), "Titre météo haltères",
                src, "Haltères : passages par compteur sans pluie puis avec pluie, par période"),
          deneb(f"{nom}_effet", "09_meteo3_effet_conditions_egales", position(x2, y_g2, w_c, h_row, 5, 9), "Titre météo effet",
                src, "Barres : effet de la pluie à conditions égales, en semaine et le week-end"),
          deneb(f"{nom}_classes", "10_meteo3_classes_temperature", position(M, y_g2 + h_row + GOUT, w_c, h_row, 5, 10), "Titre météo température",
                src, "Barres : passages par compteur selon la classe de température, en heure de pointe et sans pluie"),
          deneb(f"{nom}_profil", "11_meteo3_profil_horaire_semaine", position(x2, y_g2 + h_row + GOUT, w_c, h_row, 5, 11), "Titre météo profil",
                src, "Courbes : profil horaire en semaine, avec et sans pluie")]
    methode3 = [("Méthode et limites", 16, True, TX["principal"]),
                ("Passages par compteur : moyenne des comptages par compteur actif, car le nombre de compteurs varie d'une année à l'autre.", 12, False, TX["secondaire"]),
                ("À conditions égales : on compare pluie et temps sec à la même heure, pour le même type de jour et la même saison, "
                 "puis on pondère par le nombre d'heures de pluie (au moins 5 par groupe).", 12, False, TX["secondaire"]),
                ("Jours fériés et vacances scolaires ne sont pas exclus. Un seul point météo pour tout Paris.", 12, False, TX["secondaire"]),
                ("Association, pas causalité : la météo n'explique pas à elle seule les écarts.", 12, False, TX["principal"])]
    zm = zone_texte(f"{nom}_methode", position(M + 2 * w_c + 2 * GOUT, y_g2, 320, 2 * h_row + GOUT, 5, 12), methode3)
    zm["visual"]["visualContainerObjects"]["background"] = [{"properties": {"show": booleen(True), "color": couleur(F["carte"]), "transparency": num(0)}}]
    zm["visual"]["visualContainerObjects"]["padding"] = [{"properties": {"top": num(16), "bottom": num(16), "left": num(18), "right": num(18)}}]
    v.append(zm)
    res.append(page(nom, "Météo · 3 ans de compteurs", v))

    # 4 ter. Secours de la page météo 3 ans (cachée) : équivalents natifs
    nom = "p5b_secours_meteo3"
    cw2, ch2 = (LARG - GOUT) // 2, 300
    pm = lambda m: (m, True, False)  # noqa: E731
    pc = lambda n, a=False: (n, False, a)  # noqa: E731
    v = [entete(nom, "Secours · météo 3 ans (page cachée)", "Mêmes indicateurs avec des visuels Power BI natifs, à utiliser si Deneb n'est pas disponible"),
         natif(f"{nom}_halteres", "clusteredBarChart", position(M, y_kpi, cw2, ch2, 5, 1),
               {"Category": [pc("periode", True)], "Y": [pm("Passages sans pluie"), pm("Passages avec pluie")]},
               "Passages sans / avec pluie", "Équivalent natif des haltères", "Barres groupées des passages par compteur sans et avec pluie",
               {"dataPoint": [remplissage(S["neutre"], par_mesure("Passages sans pluie")), remplissage(S["pluie"], par_mesure("Passages avec pluie"))]}),
         natif(f"{nom}_effet", "clusteredColumnChart", position(M + cw2 + GOUT, y_kpi, cw2, ch2, 5, 2),
               {"Category": [pc("type_jour", True)], "Y": [pm("Effet pluie à conditions égales (%)")]},
               "Effet de la pluie à conditions égales", "Équivalent natif des barres", "Colonnes de l'effet de la pluie par type de jour",
               {"dataPoint": [{"properties": {"defaultColor": couleur(S["pluie"])}}]}),
         natif(f"{nom}_classes", "clusteredColumnChart", position(M, y_kpi + ch2 + GOUT, cw2, ch2, 5, 3),
               {"Category": [pc("classe_temperature", True)], "Y": [pm("Passages pointe temps sec")]},
               "Passages en pointe, temps sec, par température", "Équivalent natif des barres par classe", "Colonnes par classe de température",
               {"dataPoint": [{"properties": {"defaultColor": couleur(S["neutre"])}}]}),
         natif(f"{nom}_profil", "lineChart", position(M + cw2 + GOUT, y_kpi + ch2 + GOUT, cw2, ch2, 5, 4),
               {"Category": [pc("heure_du_jour", True)], "Y": [pm("Passages semaine sans pluie"), pm("Passages semaine avec pluie")]},
               "Profil horaire en semaine", "Équivalent natif des courbes", "Courbes de passages par heure, avec et sans pluie",
               {"dataPoint": [remplissage(S["neutre"], par_mesure("Passages semaine sans pluie")), remplissage(S["pluie"], par_mesure("Passages semaine avec pluie"))]})]
    res.append(page(nom, "Secours · météo 3 ans", v, cachee=True))
    ENT["courante"] = T

    # 5. Secours (cachée) : un équivalent natif de chaque visuel Deneb
    nom = "p5_secours"
    cw, chh = (LARG - 2 * GOUT) // 3, 300
    xs = [M + i * (cw + GOUT) for i in range(3)]
    ys = [y_kpi, y_kpi + chh + GOUT]
    pm = lambda m: (m, True, False)  # noqa: E731
    pc = lambda n, a=False: (n, False, a)  # noqa: E731
    cat = {"background": [{"properties": {}}]}
    v = [entete(nom, "Secours (page cachée)", "Mêmes indicateurs avec des visuels Power BI natifs, à utiliser si Deneb n'est pas disponible"),
         natif(f"{nom}_heatmap", "pivotTable", position(xs[0], ys[0], cw, chh, 5, 1),
               {"Rows": [pc("jour_nom", True)], "Columns": [pc("heure_du_jour", True)], "Values": [pm("Taux pénurie")]},
               "Taux de pénurie par jour et heure", "Équivalent natif de la carte de chaleur", "Matrice jour × heure du taux de pénurie",
               {"values": [fond_degrade("Taux pénurie")]}),
         natif(f"{nom}_rythme", "lineChart", position(xs[1], ys[0], cw, chh, 5, 2),
               {"Category": [pc("heure_du_jour", True)], "Y": [pm("Taux pénurie"), pm("Taux saturation")]},
               "Rythme de la journée", "Équivalent natif du graphique à aires", "Courbes de pénurie et de saturation par heure"),
         natif(f"{nom}_carte", "scatterChart", position(xs[2], ys[0], cw, chh, 5, 3),
               {"Category": [pc("station_nom", True)], "X": [pm("lon_moy")], "Y": [pm("lat_moy")], "Size": [pm("capacite_max")]},
               "Stations", "Équivalent natif de la carte (longitude × latitude, taille = capacité)", "Nuage de points des stations",
               {"dataPoint": [{"properties": {"defaultColor": couleur(S["neutre"])}}]}),
         natif(f"{nom}_haltere", "clusteredBarChart", position(xs[0], ys[1], cw, chh, 5, 4),
               {"Category": [pc("periode", True)], "Y": [pm("Taux pénurie sans panne"), pm("Taux pénurie avec panne")],
                "Tooltips": [pm("Taux saturation sans panne"), pm("Taux saturation avec panne")]},
               "Pénurie sans / avec panne", "Équivalent natif des haltères (la saturation est dans l'infobulle)",
               "Barres groupées de pénurie sans panne et avec panne",
               {"dataPoint": [remplissage(S["neutre"], par_mesure("Taux pénurie sans panne")),
                              remplissage(S["panne"], par_mesure("Taux pénurie avec panne"))]}),
         natif(f"{nom}_barres", "clusteredColumnChart", position(xs[1], ys[1], cw // 2 - 8, chh, 5, 5),
               {"Category": [pc("pluie_libelle", True)], "Y": [pm("Taux pénurie"), pm("Taux saturation")]},
               "Pluie / sans pluie", "Équivalent natif des barres (orange = pénurie, bleu = saturation)", "Colonnes groupées avec et sans pluie"),
         natif(f"{nom}_courbes", "lineChart", position(xs[1] + cw // 2 + 8, ys[1], cw // 2 - 8, chh, 5, 6),
               {"Category": [pc("heure_du_jour", True)], "Series": [pc("pluie_libelle")], "Y": [pm("Taux pénurie")]},
               "Pénurie par heure", "Équivalent natif des courbes avec et sans pluie", "Courbes du taux de pénurie par heure et météo",
               {"dataPoint": [remplissage(S["neutre"], par_valeur("pluie_libelle", "Sans pluie")),
                              remplissage(S["pluie"], par_valeur("pluie_libelle", "Pluie"))]}),
         natif(f"{nom}_nuage", "scatterChart", position(xs[2], ys[1], cw, chh, 5, 7),
               {"Category": [pc("heure_paris", True)], "X": [pm("temperature_moy")], "Y": [pm("Taux pénurie")], "Series": [pc("pluie_libelle")]},
               "Température et pénurie", "Équivalent natif du nuage de points", "Nuage de points température et pénurie",
               {"dataPoint": [remplissage(S["neutre"], par_valeur("pluie_libelle", "Sans pluie")),
                              remplissage(S["pluie"], par_valeur("pluie_libelle", "Pluie"))]})]
    res.append(page(nom, "Secours", v, cachee=True))
    return res


# ------------------------------------------------------------------ écriture


def ecrire():
    if DOSSIER.exists():
        shutil.rmtree(DOSSIER)
    (DOSSIER / "StaticResources" / "RegisteredResources").mkdir(parents=True)
    DEF.mkdir(parents=True)
    c.ecrire_json(DOSSIER / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "Report", "displayName": NOM},
        "config": {"version": "2.0", "logicalId": "8d3b0b38-4f0a-5f0e-8e0f-6f1f0b2f1a02"}})
    c.ecrire_json(DOSSIER / "definition.pbir", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0", "datasetReference": {"byPath": {"path": f"../{NOM}.SemanticModel"}}})
    shutil.copy(c.RACINE / "velib_theme.json", DOSSIER / "StaticResources" / "RegisteredResources" / "velib_theme.json")
    c.ecrire_json(DEF / "version.json", {"$schema": f"{SCH}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"})
    c.ecrire_json(DEF / "report.json", {
        "$schema": f"{SCH}/report/{V_RAPPORT}/schema.json",
        "themeCollection": {"customTheme": {"name": "velib_theme.json", "reportVersionAtImport": {
            "visual": V_VISUEL, "report": V_RAPPORT, "page": V_PAGE}, "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources", "items": [
            {"name": "velib_theme.json", "path": "velib_theme.json", "type": "CustomTheme"}]}],
        "publicCustomVisuals": [DENEB],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True, "useEnhancedTooltips": True,
                     "useDefaultAggregateDisplayName": True}})
    liste = pages()
    (DEF / "pages").mkdir(parents=True, exist_ok=True)
    c.ecrire_json(DEF / "pages" / "pages.json", {"$schema": f"{SCH}/pagesMetadata/1.0.0/schema.json",
                                                  "pageOrder": [p[0] for p in liste if p[2].get("visibility") != "HiddenInViewMode"]
                                                  + [p[0] for p in liste if p[2].get("visibility") == "HiddenInViewMode"],
                                                  "activePageName": liste[0][0]})
    for nom, _, pj, visuels in liste:
        dossier = DEF / "pages" / nom
        dossier.mkdir(parents=True, exist_ok=True)
        c.ecrire_json(dossier / "page.json", pj)
        for vj in visuels:
            d = dossier / "visuals" / vj["name"]
            d.mkdir(parents=True, exist_ok=True)
            c.ecrire_json(d / "visual.json", vj)
    c.ecrire_json(c.RACINE / "velib_dashboard.pbip", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0", "artifacts": [{"report": {"path": f"{NOM}.Report"}}], "settings": {"enableAutoRecovery": True}})
    print("ok", DOSSIER.name, "-", sum(len(p[3]) for p in liste), "visuels,", len(liste), "pages")


if __name__ == "__main__":
    ecrire()
