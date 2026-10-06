"""Écrit velib_dashboard.SemanticModel/ (format TMDL) : paramètres, requête Databricks, colonnes typées, mesures."""
import json
import uuid

import commun as c

NOM = "velib_dashboard"
DOSSIER = c.RACINE / f"{NOM}.SemanticModel"
TABLE = "gold_station_heure"
NS = uuid.UUID("5a1c2b7e-0d0e-4f1a-9a55-2f4f0c0b7a01")


def guid(*parts) -> str:
    return str(uuid.uuid5(NS, "/".join(parts)))


# nom, type TMDL, type M, format d'affichage (None = défaut)
COLONNES = [
    ("station_id", "string", "type text", None), ("station_nom", "string", "type text", None),
    ("station_code", "string", "type text", None), ("latitude", "double", "type number", "0.00000"),
    ("longitude", "double", "type number", "0.00000"), ("capacite", "int64", "Int64.Type", "0"),
    ("heure_utc", "dateTime", "type datetime", "dd/MM/yyyy HH:mm"), ("heure_paris", "dateTime", "type datetime", "dd/MM/yyyy HH:mm"),
    ("date_paris", "dateTime", "type date", "dd/MM/yyyy"), ("heure_du_jour", "int64", "Int64.Type", "0"),
    ("jour_semaine", "string", "type text", None), ("est_weekend", "boolean", "type logical", None),
    ("heure_de_pointe", "boolean", "type logical", None), ("nb_releves", "int64", "Int64.Type", "#,0"),
    ("nb_releves_en_service", "int64", "Int64.Type", "#,0"), ("nb_releves_penurie", "int64", "Int64.Type", "#,0"),
    ("nb_releves_saturation", "int64", "Int64.Type", "#,0"), ("taux_penurie", "double", "type number", "0.0%"),
    ("taux_saturation", "double", "type number", "0.0%"), ("velos_moyens", "double", "type number", "0.0"),
    ("velos_electriques_moyens", "double", "type number", "0.0"), ("places_libres_moyennes", "double", "type number", "0.0"),
    ("temperature_c", "double", "type number", "0.0"), ("precipitation_mm", "double", "type number", "0.0"),
    ("il_pleut", "boolean", "type logical", None), ("station_proche_ferre_300m", "boolean", "type logical", None),
    ("panne_ferree_300m", "boolean", "type logical", None), ("panne_ferree_500m", "boolean", "type logical", None),
    ("panne_ferree_bloquante_300m", "boolean", "type logical", None), ("panne_ferree_imprevue_300m", "boolean", "type logical", None),
    ("panne_bus_300m", "boolean", "type logical", None), ("nb_pannes_ferrees_300m", "int64", "Int64.Type", "0"),
    ("distance_min_panne_ferree_m", "double", "type number", "0"),
]
# colonnes ajoutées dans Power Query (pas dans Databricks)
CALCULEES = [
    ("jour_semaine_ordre", "int64", "Int64.Type", "0"), ("jour_nom", "string", "type text", None),
    ("periode", "string", "type text", None), ("pluie_libelle", "string", "type text", None),
]

PARAMETRES = [
    ("Hote", "adb-7405605942490257.17.azuredatabricks.net", "Adresse du workspace Databricks (sans https://)"),
    ("CheminHTTP", "/sql/1.0/warehouses/4dd75efb6ecd07bd", "Chemin HTTP du SQL Warehouse"),
    ("Catalogue", "dbw_datalake_velib_7405605942490257", "Catalogue Unity Catalog"),
]

T = TABLE
# format personnalisé « +1,2 pts » ; en TMDL la valeur est entre guillemets, les guillemets internes sont doublés
FORMAT_PTS = '"+0.0"" pts"";-0.0"" pts"";0.0"" pts"""'


def col(nom):
    return f"{T}[{nom}]"


MESURES = [
    # (nom, DAX, format, dossier, masquée)
    ("Nb stations", f"DISTINCTCOUNT({col('station_id')})", "#,0", "Indicateurs", False),
    ("Taux pénurie", f"DIVIDE(SUM({col('nb_releves_penurie')}), SUM({col('nb_releves_en_service')}))", "0.0%", "Indicateurs", False),
    ("Taux saturation", f"DIVIDE(SUM({col('nb_releves_saturation')}), SUM({col('nb_releves_en_service')}))", "0.0%", "Indicateurs", False),
    ("Dernière heure", f"MAX({col('heure_paris')})", "dd/MM HH:mm", "Indicateurs", False),
]
for ind in ("pénurie", "saturation"):
    base = f"[Taux {ind}]"
    MESURES.append((f"Taux {ind} avec panne",
                    f"CALCULATE({base}, {col('station_proche_ferre_300m')} = TRUE(), {col('panne_ferree_300m')} = TRUE())",
                    "0.0%", "Pannes", False))
    MESURES.append((f"Taux {ind} sans panne",
                    f"CALCULATE({base}, REMOVEFILTERS({col('panne_ferree_imprevue_300m')}), "
                    f"{col('station_proche_ferre_300m')} = TRUE(), {col('panne_ferree_300m')} = FALSE())",
                    "0.0%", "Pannes", False))
for ind in ("pénurie", "saturation"):
    MESURES.append((f"Écart {ind} (pts)", f"([Taux {ind} avec panne] - [Taux {ind} sans panne]) * 100", FORMAT_PTS, "Pannes", False))
MESURES.append(("Part heures avec panne ferrée",
                f"DIVIDE(CALCULATE(COUNTROWS({T}), {col('station_proche_ferre_300m')} = TRUE(), {col('panne_ferree_300m')} = TRUE()), "
                f"CALCULATE(COUNTROWS({T}), REMOVEFILTERS({col('panne_ferree_imprevue_300m')}), {col('station_proche_ferre_300m')} = TRUE()))",
                "0.0%", "Pannes", False))
# mesures d'appui pour les visuels Deneb (Deneb calcule les taux lui-même à partir de ces sommes)
MESURES += [
    ("n_service", f"SUM({col('nb_releves_en_service')})", "#,0", "Appui Deneb", True),
    ("n_penurie", f"SUM({col('nb_releves_penurie')})", "#,0", "Appui Deneb", True),
    ("n_saturation", f"SUM({col('nb_releves_saturation')})", "#,0", "Appui Deneb", True),
    ("capacite_max", f"MAX({col('capacite')})", "0", "Appui Deneb", True),
    # appui de la page « Secours » (visuels natifs : les axes X / Y d'un nuage de points attendent des mesures)
    ("lon_moy", f"AVERAGE({col('longitude')})", "0.00000", "Appui natif", True),
    ("lat_moy", f"AVERAGE({col('latitude')})", "0.00000", "Appui natif", True),
    ("temperature_moy", f"AVERAGE({col('temperature_c')})", "0.0", "Appui natif", True),
]
# titres dynamiques (une conclusion calculée sur les données filtrées, avec repli prudent si aucune donnée)
TITRES = [
    ("Titre heatmap", f"""VAR t = ADDCOLUMNS(
    SUMMARIZE({T}, {col('heure_du_jour')}, {col('jour_semaine_ordre')}, {col('jour_nom')}),
    "@r", [Taux pénurie])
VAR m = TOPN(1, t, [@r], DESC)
VAR h = MAXX(m, {col('heure_du_jour')})
VAR j = MAXX(m, {col('jour_nom')})
RETURN IF(ISBLANK(h), "Où et quand manque-t-on de vélos ?", "Les pénuries culminent le " & j & " à " & h & " h")"""),
    ("Titre rythme", f"""VAR t = ADDCOLUMNS(VALUES({col('heure_du_jour')}), "@r", [Taux pénurie])
VAR m = TOPN(1, t, [@r], DESC)
VAR h = MAXX(m, {col('heure_du_jour')})
RETURN IF(ISBLANK(h), "Les pénuries au fil de la journée", "Les pénuries explosent à " & h & " h")"""),
    ("Titre carte", f"""VAR t = ADDCOLUMNS(VALUES({col('station_id')}), "@r", [Taux pénurie])
VAR n = COUNTROWS(FILTER(t, [@r] > 0.2))
VAR total = COUNTROWS(t)
RETURN IF(total = 0, "Quelles stations manquent de vélos ?", n & " stations sur " & FORMAT(total, "#,0") & " sont vides plus d'un relevé sur cinq")"""),
    ("Titre pannes", """VAR e = [Écart pénurie (pts)]
RETURN IF(ISBLANK(e), "Une panne ferrée à proximité change-t-elle la pénurie ?",
    "Une panne ferrée à moins de 300 m " & IF(e >= 0, "augmente", "réduit") & " la pénurie de " & FORMAT(ABS(e), "0.0") & " pts")"""),
    ("Titre pluie", f"""VAR a = CALCULATE([Taux pénurie], {col('il_pleut')} = FALSE())
VAR b = CALCULATE([Taux pénurie], {col('il_pleut')} = TRUE())
RETURN IF(ISBLANK(a) || ISBLANK(b), "Pénurie et saturation, avec et sans pluie",
    "Sous la pluie, la pénurie passe de " & FORMAT(a, "0.0%") & " à " & FORMAT(b, "0.0%"))"""),
]
for nom, dax in TITRES:
    MESURES.append((nom, dax, None, "Titres", True))


def tmdl_nom(n: str) -> str:
    return f"'{n}'" if any(ch in n for ch in " .=:'") else n


def bloc_mesure(nom, dax, fmt, dossier, masquee) -> str:
    lignes = dax.splitlines()
    if len(lignes) == 1:
        s = f"\tmeasure {tmdl_nom(nom)} = {dax}\n"
    else:
        s = f"\tmeasure {tmdl_nom(nom)} =\n" + "".join(f"\t\t\t{l}\n" for l in lignes)
    if fmt:
        s += f"\t\tformatString: {fmt}\n"
    if masquee:
        s += "\t\tisHidden\n"
    s += f"\t\tdisplayFolder: {dossier}\n\t\tlineageTag: {guid('mesure', nom)}\n\n"
    return s


def bloc_colonne(nom, tmdl_type, fmt, calculee=False) -> str:
    s = f"\tcolumn {tmdl_nom(nom)}\n\t\tdataType: {tmdl_type}\n"
    if fmt:
        s += f"\t\tformatString: {fmt}\n"
    s += f"\t\tlineageTag: {guid('colonne', nom)}\n\t\tsummarizeBy: none\n\t\tsourceColumn: {nom}\n"
    if nom == "jour_semaine":
        s += "\t\tsortByColumn: jour_semaine_ordre\n"
    if nom == "jour_nom":
        s += "\t\tsortByColumn: jour_semaine_ordre\n"
    if nom == "latitude":
        s += "\t\tdataCategory: Latitude\n"
    if nom == "longitude":
        s += "\t\tdataCategory: Longitude\n"
    if nom == "date_paris":
        s += "\n\t\tannotation UnderlyingDateTimeDataType = Date\n"
    s += "\n\t\tannotation SummarizationSetBy = User\n\n"
    return s


def requete_m() -> str:
    types = ",\n".join(f'            {{"{n}", {tm}}}' for n, _, tm, _ in COLONNES)
    zones = ",\n".join(
        f'            {{"{n}", each if _ is datetimezone then DateTimeZone.RemoveZone(_) else _, type datetime}}'
        for n in ("heure_utc", "heure_paris"))
    return f"""let
    Source = Databricks.Catalogs(Hote, CheminHTTP, [Catalog = null, Database = null, EnableAutomaticProxyDiscovery = null]),
    Catalogue_ = Source{{[Name = Catalogue, Kind = "Database"]}}[Data],
    Schema_ = Catalogue_{{[Name = "velib", Kind = "Schema"]}}[Data],
    Table_ = Schema_{{[Name = "{TABLE}", Kind = "Table"]}}[Data],
    SansFuseau = Table.TransformColumns(Table_, {{
{zones}
        }}),
    Types = Table.TransformColumnTypes(SansFuseau, {{
{types}
        }}, "en-US"),
    JourOrdre = Table.AddColumn(Types, "jour_semaine_ordre",
        each if [date_paris] = null then null else Date.DayOfWeek([date_paris], Day.Monday) + 1, Int64.Type),
    JourNom = Table.AddColumn(JourOrdre, "jour_nom",
        each if [date_paris] = null then null else {{"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}}{{Date.DayOfWeek([date_paris], Day.Monday)}}, type text),
    Periode = Table.AddColumn(JourNom, "periode",
        each if [heure_de_pointe] = true then "Heure de pointe" else "Hors pointe", type text),
    Pluie = Table.AddColumn(Periode, "pluie_libelle",
        each if [il_pleut] = true then "Pluie" else "Sans pluie", type text)
in
    Pluie"""


def table_tmdl() -> str:
    s = f"table {TABLE}\n\tlineageTag: {guid('table', TABLE)}\n\n"
    for m in MESURES:
        s += bloc_mesure(*m)
    for n, t, _, f in COLONNES + CALCULEES:
        s += bloc_colonne(n, t, f)
    m = "\n".join("\t\t\t\t" + l if l else "" for l in requete_m().splitlines())
    s += f"\tpartition {TABLE} = m\n\t\tmode: import\n\t\tsource =\n{m}\n\n\tannotation PBI_ResultType = Table\n"
    return s


def expressions_tmdl() -> str:
    s = ""
    for nom, valeur, descr in PARAMETRES:
        s += (f"/// {descr}\nexpression {nom} = \"{valeur}\" meta [IsParameterQuery=true, Type=\"Text\", IsParameterQueryRequired=true]\n"
              f"\tlineageTag: {guid('parametre', nom)}\n\n\tannotation PBI_ResultType = Text\n\n")
    return s


MODEL = f"""model Model
	culture: fr-FR
	defaultPowerBIDataSourceVersion: powerBI_V3
	discourageImplicitMeasures
	sourceQueryCulture: fr-FR
	dataAccessOptions
		legacyRedirects
		returnErrorValuesAsNull

ref table {TABLE}

ref culture fr-FR

annotation PBI_QueryOrder = ["Hote","CheminHTTP","Catalogue","{TABLE}"]

annotation __PBI_TimeIntelligenceEnabled = 0

annotation PBI_ProTooling = ["DevMode"]
"""


def main():
    (DOSSIER / "definition" / "tables").mkdir(parents=True, exist_ok=True)
    (DOSSIER / "definition" / "cultures").mkdir(parents=True, exist_ok=True)
    c.ecrire_json(DOSSIER / ".platform", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {"type": "SemanticModel", "displayName": NOM},
        "config": {"version": "2.0", "logicalId": guid("platform", "SemanticModel")}})
    c.ecrire_json(DOSSIER / "definition.pbism", {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.0", "settings": {}})
    (DOSSIER / "definition" / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1601\n", encoding="utf-8")
    (DOSSIER / "definition" / "model.tmdl").write_text(MODEL, encoding="utf-8")
    (DOSSIER / "definition" / "expressions.tmdl").write_text(expressions_tmdl(), encoding="utf-8")
    (DOSSIER / "definition" / "cultures" / "fr-FR.tmdl").write_text("culture fr-FR\n", encoding="utf-8")
    (DOSSIER / "definition" / "tables" / f"{TABLE}.tmdl").write_text(table_tmdl(), encoding="utf-8")
    print("ok", DOSSIER.name)


if __name__ == "__main__":
    main()
