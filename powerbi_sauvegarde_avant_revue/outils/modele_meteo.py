"""Table gold_velo_meteo_heure (comptages vélo × météo, une ligne par heure 2023-2025) : colonnes, mesures DAX, requête M.

Table indépendante : aucune relation avec gold_station_heure (grain et période différents).
"""
import generer_modele as gm

TABLE2 = "gold_velo_meteo_heure"
T2 = TABLE2


def col2(nom):
    return f"{T2}[{nom}]"


# nom, type TMDL, type M, format d'affichage
COLONNES2 = [
    ("heure_utc", "dateTime", "type datetime", "dd/MM/yyyy HH:mm"), ("heure_paris", "dateTime", "type datetime", "dd/MM/yyyy HH:mm"),
    ("date_paris", "dateTime", "type date", "dd/MM/yyyy"), ("heure_du_jour", "int64", "Int64.Type", "0"),
    ("mois", "int64", "Int64.Type", "0"), ("saison", "string", "type text", None), ("type_jour", "string", "type text", None),
    ("periode", "string", "type text", None), ("passages_total", "int64", "Int64.Type", "#,0"),
    ("compteurs_actifs", "int64", "Int64.Type", "#,0"), ("passages_par_compteur", "double", "type number", "0.0"),
    ("temperature_c", "double", "type number", "0.0"), ("precipitation_mm", "double", "type number", "0.0"),
    ("pluie_mm", "double", "type number", "0.0"), ("vent_kmh", "double", "type number", "0.0"),
    ("il_pleut", "boolean", "type logical", None), ("classe_temperature", "string", "type text", None),
]
# colonnes calculées en DAX dans le modèle : année pour le segment, ordres de tri pour saison et période
CALCULEES2 = [
    ("annee", "int64", "0", f"IF(ISBLANK({col2('date_paris')}), BLANK(), YEAR({col2('date_paris')}))", None),
    ("saison_ordre", "int64", "0",
     f'SWITCH({col2("saison")}, "hiver", 1, "printemps", 2, "été", 3, "automne", 4)', None),
    # copie de `saison` triée par saison_ordre : trier `saison` elle-même par une colonne qui en dépend = dépendance circulaire
    ("saison_libelle", "string", None, col2("saison"), None),
]
TRI = {"saison_libelle": "saison_ordre"}
DOSSIER_MES = "Météo 3 ans"

FPCT = '"+0.0%;-0.0%;0.0%"'
MESURES2 = [
    ("Passages par compteur", f"AVERAGE({col2('passages_par_compteur')})", "0.0", DOSSIER_MES, False),
    ("Passages sans pluie", f"CALCULATE([Passages par compteur], {col2('il_pleut')} = FALSE())", "0.0", DOSSIER_MES, False),
    ("Passages avec pluie", f"CALCULATE([Passages par compteur], {col2('il_pleut')} = TRUE())", "0.0", DOSSIER_MES, False),
    ("Écart pluie brut (%)", "DIVIDE([Passages avec pluie], [Passages sans pluie]) - 1", FPCT, DOSSIER_MES, False),
    ("Heures étudiées", f"COUNTROWS({T2})", "#,0", DOSSIER_MES, False),
    ("Heures de pluie", f"CALCULATE(COUNTROWS({T2}), {col2('il_pleut')} = TRUE())", "#,0", DOSSIER_MES, False),
    ("Part des heures de pluie (%)", "DIVIDE([Heures de pluie], [Heures étudiées])", "0.0%", DOSSIER_MES, False),
    # Effet de la pluie à conditions égales : pour chaque strate type_jour × saison × heure_du_jour ayant au moins 5 heures de
    # pluie, rapport (moyenne avec pluie / moyenne sans pluie) - 1 ; moyenne des strates pondérée par leur nombre d'heures de pluie.
    # SUMMARIZE part du contexte de filtre courant : segments et type_jour sont respectés.
    ("Effet pluie à conditions égales (%)", f"""VAR strates = SUMMARIZE({T2}, {col2('type_jour')}, {col2('saison')}, {col2('heure_du_jour')})
VAR t = ADDCOLUMNS(strates,
    "@np", CALCULATE(COUNTROWS({T2}), {col2('il_pleut')} = TRUE()),
    "@mp", CALCULATE([Passages par compteur], {col2('il_pleut')} = TRUE()),
    "@ms", CALCULATE([Passages par compteur], {col2('il_pleut')} = FALSE()))
VAR ok = FILTER(t, [@np] >= 5 && NOT ISBLANK([@mp]) && NOT ISBLANK([@ms]) && [@ms] <> 0)
RETURN DIVIDE(SUMX(ok, [@np] * ([@mp] / [@ms] - 1)), SUMX(ok, [@np]))""", FPCT, DOSSIER_MES, False),
    ("Effet pluie semaine (%)", f'CALCULATE([Effet pluie à conditions égales (%)], {col2("type_jour")} = "semaine")', FPCT, DOSSIER_MES, False),
    ("Effet pluie week-end (%)", f'CALCULATE([Effet pluie à conditions égales (%)], {col2("type_jour")} = "week-end")', FPCT, DOSSIER_MES, False),
    # mesures d'appui aux visuels Deneb
    ("Passages pointe temps sec", f'CALCULATE([Passages par compteur], {col2("periode")} = "pointe", {col2("il_pleut")} = FALSE())', "0.0", DOSSIER_MES, True),
    ("Heures pointe temps sec", f'CALCULATE(COUNTROWS({T2}), {col2("periode")} = "pointe", {col2("il_pleut")} = FALSE())', "#,0", DOSSIER_MES, True),
    ("Passages semaine sans pluie", f'CALCULATE([Passages sans pluie], {col2("type_jour")} = "semaine")', "0.0", DOSSIER_MES, True),
    ("Passages semaine avec pluie", f'CALCULATE([Passages avec pluie], {col2("type_jour")} = "semaine")', "0.0", DOSSIER_MES, True),
    ("Heures de pluie par strate", f"""COUNTROWS(FILTER({T2}, {col2('il_pleut')} = TRUE()))""", "#,0", DOSSIER_MES, True),
]
TITRES2 = [
    ("Titre météo haltères", f"""VAR e = CALCULATE([Écart pluie brut (%)], {col2('periode')} = "pointe")
RETURN IF(ISBLANK(e), "La pluie change-t-elle la fréquentation à vélo ?",
    "Aux heures de pointe, la pluie " & IF(e < 0, "fait baisser", "fait monter") & " les passages de " & FORMAT(ABS(e), "0.0%", "fr-FR"))"""),
    ("Titre météo effet", f"""VAR s = [Effet pluie semaine (%)]
VAR w = [Effet pluie week-end (%)]
RETURN IF(ISBLANK(s) || ISBLANK(w), "Quel effet de la pluie, à conditions égales ?",
    "Sous la pluie, à conditions égales : " & FORMAT(s, "+0.0%;-0.0%;0.0%", "fr-FR") & " en semaine, "
    & FORMAT(w, "+0.0%;-0.0%;0.0%", "fr-FR") & " le week-end")"""),
    ("Titre météo température", f"""VAR t = ADDCOLUMNS(VALUES({col2('classe_temperature')}), "@v", [Passages pointe temps sec])
VAR m = TOPN(1, t, [@v], DESC)
VAR c = MAXX(m, {col2('classe_temperature')})
VAR v = MAXX(m, [@v])
RETURN IF(ISBLANK(v), "Les passages en pointe selon la température",
    "Par temps sec, les passages en pointe culminent à " & MID(c, 4, LEN(c)) & " (" & FORMAT(v, "0.0", "fr-FR") & " par compteur)")"""),
    ("Titre météo profil", f"""VAR t = ADDCOLUMNS(VALUES({col2('heure_du_jour')}), "@s", [Passages semaine sans pluie], "@a", [Passages semaine avec pluie])
VAR c = FILTER(t, NOT ISBLANK([@s]) && NOT ISBLANK([@a]))
VAR n = COUNTROWS(c)
VAR b = COUNTROWS(FILTER(c, [@a] < [@s]))
RETURN IF(n = 0, "Le profil horaire en semaine, avec et sans pluie",
    "En semaine, la pluie fait baisser les passages à " & FORMAT(b, "#,##0", "fr-FR") & " heures sur " & FORMAT(n, "#,##0", "fr-FR"))"""),
]
MESURES2 += [(n, d, None, DOSSIER_MES, True) for n, d in TITRES2]
MESURES2 = [m for m in MESURES2 if m[0] != "Heures de pluie par strate"]


def requete_m2() -> str:
    types = ",\n".join(f'            {{"{n}", {tm}}}' for n, _, tm, _ in COLONNES2)
    zones = ",\n".join(f'            {{"{n}", each if _ is datetimezone then DateTimeZone.RemoveZone(_) else _, type datetime}}'
                       for n in ("heure_utc", "heure_paris"))
    return f"""let
    Source = Databricks.Catalogs(Hote, CheminHTTP, [Catalog = null, Database = null, EnableAutomaticProxyDiscovery = null]),
    Catalogue_ = Source{{[Name = Catalogue, Kind = "Database"]}}[Data],
    Schema_ = Catalogue_{{[Name = "velib", Kind = "Schema"]}}[Data],
    Table_ = Schema_{{[Name = "{TABLE2}", Kind = "Table"]}}[Data],
    SansFuseau = Table.TransformColumns(Table_, {{
{zones}
        }}),
    Types = Table.TransformColumnTypes(SansFuseau, {{
{types}
        }}, "en-US")
in
    Types"""


def colonne2(nom, tmdl_type, fmt) -> str:
    s = f"\tcolumn {nom}\n\t\tdataType: {tmdl_type}\n"
    if fmt:
        s += f"\t\tformatString: {fmt}\n"
    s += f"\t\tlineageTag: {gm.guid(TABLE2, 'colonne', nom)}\n\t\tsummarizeBy: none\n\t\tsourceColumn: {nom}\n"
    if nom in TRI:
        s += f"\t\tsortByColumn: {TRI[nom]}\n"
    if nom == "date_paris":
        s += "\n\t\tannotation UnderlyingDateTimeDataType = Date\n"
    return s + "\n\t\tannotation SummarizationSetBy = User\n\n"


def calculee2(nom, tmdl_type, fmt, dax, _) -> str:
    s = f"\tcolumn {nom} = {dax}\n\t\tdataType: {tmdl_type}\n\t\tisDataTypeInferred\n"
    if fmt:
        s += f"\t\tformatString: {fmt}\n"
    s += f"\t\tlineageTag: {gm.guid(TABLE2, 'colonne', nom)}\n\t\tsummarizeBy: none\n"
    if nom in TRI:
        s += f"\t\tsortByColumn: {TRI[nom]}\n"
    return s + "\n\t\tannotation SummarizationSetBy = User\n\n"


def table_tmdl2() -> str:
    s = f"table {TABLE2}\n\tlineageTag: {gm.guid('table', TABLE2)}\n\n"
    for m in MESURES2:
        s += gm.bloc_mesure(*m)
    for n, t, _, f in COLONNES2:
        s += colonne2(n, t, f)
    for c in CALCULEES2:
        s += calculee2(*c)
    m = "\n".join("\t\t\t\t" + l if l else "" for l in requete_m2().splitlines())
    s += f"\tpartition {TABLE2} = m\n\t\tmode: import\n\t\tsource =\n{m}\n\n\tannotation PBI_ResultType = Table\n"
    return s
