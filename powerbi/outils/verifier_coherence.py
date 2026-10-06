"""Contrôles de cohérence maison (en plus des schémas) :
1. TMDL : indentation à tabulations, noms de colonnes/mesures uniques ;
2. tout champ cité dans un visuel existe dans le modèle (colonne ou mesure) ;
3. tout champ lu par une spec Deneb est bien lié au visuel (ou calculé dans la spec) ;
4. aucun secret : pas de jeton, pas de clé, pas de ligne « dapi… » dans le projet.
"""
import json
import re
import sys

import commun as c
import generer_modele as gm

PROJ = c.RACINE
erreurs = []


def err(m):
    erreurs.append(m)
    print("ECHEC", m)


# 1. TMDL
modele_cols = {n for n, *_ in gm.COLONNES + gm.CALCULEES}
modele_mes = {m[0] for m in gm.MESURES}
assert len(modele_cols) == len(gm.COLONNES + gm.CALCULEES), "colonnes en double"
assert not modele_cols & modele_mes, "nom commun à une colonne et une mesure"
for f in (PROJ / "velib_dashboard.SemanticModel").rglob("*.tmdl"):
    for i, l in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
        if l.startswith(" ") and not re.match(r"^\t+ ", l) and "\t" not in l[:1]:
            # une ligne qui commence par des espaces n'est tolérée que dans un bloc M/DAX (déjà précédé de tabulations)
            err(f"{f.name}:{i} ligne indentée par des espaces")
txt = (PROJ / "velib_dashboard.SemanticModel/definition/tables/gold_station_heure.tmdl").read_text(encoding="utf-8")
for n in modele_cols:
    if f"column {n}\n" not in txt:
        err(f"colonne absente du TMDL : {n}")
for n in modele_mes:
    if f"measure {gm.tmdl_nom(n)} =" not in txt:
        err(f"mesure absente du TMDL : {n}")

# 2 et 3
BIBLIO = {"datum", "d"}
for f in (PROJ / "velib_dashboard.Report/definition").rglob("visual.json"):
    d = json.loads(f.read_text(encoding="utf-8"))
    v = d.get("visual", {})
    refs = set()

    def parcourir(n):
        if isinstance(n, dict):
            for k in ("Column", "Measure"):
                if k in n and isinstance(n[k], dict) and "Property" in n[k]:
                    ent = n[k]["Expression"]["SourceRef"].get("Entity")
                    if ent == gm.TABLE:
                        refs.add((k, n[k]["Property"]))
            for x in n.values():
                parcourir(x)
        elif isinstance(n, list):
            for x in n:
                parcourir(x)
    parcourir(d)
    for k, nom in refs:
        existe = nom in (modele_cols if k == "Column" else modele_mes)
        if not existe:
            err(f"{f.parent.name} : {k} inconnu {nom}")
    if v.get("visualType", "").startswith("deneb"):
        spec = json.loads(v["objects"]["vega"][0]["properties"]["jsonSpec"]["expr"]["Literal"]["Value"][1:-1].replace("''", "'"))
        liees = {p["nativeQueryRef"] for p in v["query"]["queryState"]["dataset"]["projections"]}
        texte = json.dumps(spec, ensure_ascii=False)
        calcules = set(re.findall(r'"as": "([^"]+)"', texte)) | set(re.findall(r'"as": \["([^"]+)", "([^"]+)"\]', texte) and
                                                                    [x for t in re.findall(r'"as": \["([^"]+)", "([^"]+)"\]', texte) for x in t])
        # pivot : les noms de colonnes viennent des valeurs du champ pivoté (série ou météo) ; fold : champs de « fold »
        def cles_inline(n):
            if isinstance(n, dict):
                if isinstance(n.get("values"), list) and n["values"] and isinstance(n["values"][0], dict):
                    yield from n["values"][0].keys()
                for x in n.values():
                    yield from cles_inline(x)
            elif isinstance(n, list):
                for x in n:
                    yield from cles_inline(x)
        calcules |= set(cles_inline(spec))  # annotations en données inline (bandes de pointe, repères de la carte)
        calcules |= {"penurie", "saturation", "Sans pluie", "Pluie", "sans", "avec"}
        utilises = set(re.findall(r'"field": "([^"]+)"', texte)) | set(re.findall(r"datum\.([A-Za-z_][A-Za-z0-9_]*)", texte)) | \
            set(re.findall(r"datum\[''?([^'\]]+)''?\]", texte))
        # champs lus directement dans le jeu de données = utilisés mais non calculés
        manquants = {u for u in utilises if u not in liees and u not in calcules}
        # `datum.value`, `datum.label` : propriétés d'axe Vega, pas des champs
        manquants -= {"value", "label"}
        if manquants:
            err(f"{f.parent.name} : champs lus par la spec mais ni liés ni calculés : {sorted(manquants)}")

# 5. titres : jamais dans les specs, toujours une mesure DAX liée au titre du visuel Deneb
import specs as sp
import couleurs as co


def titres_dans_spec(n, chemin="spec"):
    if isinstance(n, dict):
        if "title" in n and ("mark" in n or "layer" in n or "$schema" in n):
            yield chemin
        for k, x in n.items():
            if k in ("layer", "spec"):
                yield from titres_dans_spec(x, f"{chemin}/{k}")
    elif isinstance(n, list):
        for i, x in enumerate(n):
            yield from titres_dans_spec(x, f"{chemin}[{i}]")


toutes = {nom: f() for nom, (f, _) in sp.SPECS.items()}
for nom, spec in toutes.items():
    for ch in titres_dans_spec(spec):
        err(f"{nom} : titre écrit dans la spec ({ch}) ; il doit venir d'une mesure DAX")
for f in (PROJ / "velib_dashboard.Report/definition").rglob("visual.json"):
    d = json.loads(f.read_text(encoding="utf-8"))
    if d.get("visual", {}).get("visualType", "").startswith("deneb"):
        t = d["visual"]["visualContainerObjects"]["title"][0]["properties"]["text"]["expr"]
        if "Measure" not in t or t["Measure"]["Property"] not in modele_mes:
            err(f"{f.parent.name} : le titre n'est pas lié à une mesure du modèle")
# 6. un sens par couleur
for m in co.verifier(toutes):
    err(m)

# 4. secrets
motifs = [re.compile(r"dapi[0-9a-f]{20,}", re.I), re.compile(r"(?i)(password|passwd|secret|token|apikey|api_key)\s*[:=]\s*[\"'][^\"']{8,}")]
for f in PROJ.rglob("*"):
    if f.is_file() and f.suffix in {".json", ".tmdl", ".md", ".pbir", ".pbip", ".py", ".txt", ".pbism"}:
        t = f.read_text(encoding="utf-8", errors="ignore")
        for m in motifs:
            if m.search(t):
                err(f"secret possible dans {f.relative_to(PROJ)}")
print("OK cohérence" if not erreurs else f"{len(erreurs)} problème(s)")
sys.exit(1 if erreurs else 0)
