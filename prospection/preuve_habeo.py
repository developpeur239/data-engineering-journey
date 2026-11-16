"""Preuve gratuite pour Habeo Recrutement : PME (10-250 salariés) de 33/64/40 qui recrutent en CDI
des profils BTP / industrie, offres publiées directement par l'employeur.

Étapes :
  1. Balayage France Travail (métiers × départements, CDI) : sur 14 jours, puis sans filtre de date
  2. Exclusions par nom (intérim, cabinets, grands groupes, employeur masqué)
  3. Rapprochement API recherche-entreprises : SIREN, effectif, NAF, dirigeants ; exclusion NAF 78.xx / 70.22Z,
     effectif hors 10-250, filiales de grands groupes (dirigeant personne morale)
  4. Agrégation par employeur et score de priorité
Sorties : preuve_candidats.json (tous les employeurs retenus, triés)
"""
import json, re, time, urllib.parse, urllib.request, concurrent.futures as cf
from datetime import date, timedelta
import signals_lib as S

TODAY = date(2026, 11, 16)
DEPTS = ["33", "64", "40"]
METIERS = ["conducteur de travaux", "chef de chantier", "chargé d'affaires", "ingénieur structure", "ingénieur génie civil",
           "projeteur", "technicien bureau d'études", "technicien aéronautique", "technicien de maintenance industrielle",
           "technicien de maintenance", "ingénieur méthodes", "ingénieur production"]
# Intitulés réellement dans le périmètre d'Habeo (le moteur FT ratisse large)
POSTE = re.compile(r"conduct\w* de travaux|chef de chantier|charg[ée]e? d.affaires|ing[ée]nieur(?:e)? (?:structure|g[ée]nie civil|"
                   r"m[ée]thodes?|production|calcul|b[ée]ton|travaux)|projeteu?r|dessinat\w*.projet|technicien\w* (?:de )?bureau d.[ée]tudes|"
                   r"technicien\w* (?:a[ée]ronauti|de maintenance|maintenance)|technicien\w* m[ée]thodes|responsable (?:de )?(?:maintenance|production|m[ée]thodes)",
                   re.I)
INTERMEDIAIRE = re.compile(r"int[ée]rim|recrut|\bRH\b|ressources humaines|talent|search|consult|emploi|job|staff|travail temp|"
                           r"adecco|randstad|manpower|\bcrit\b|michael page|page personnel|hays|expectra|synergie|proman|samsic|"
                           r"partnaire|gojob|leader|abalone|domino|triangle|supplay|actual|interaction|ergalis|start people|temporis|"
                           r"\bfed\b|robert half|spring|lynx|hudson|work ?& ?you|harry hope|walters|lhh|kelly|derichebourg|"
                           r"axe emploi|fab group|nextgen|onepoint|alten|akkodis|assystem|altran|segula|expleo|astek|apave|bureau veritas|socotec",
                           re.I)
GRANDS_GROUPES = re.compile(r"safran|dassault|thales|airbus|vinci|eiffage|bouygues|\bspie\b|engie|ariane|\bnge\b|colas|eurovia|"
                            r"cegelec|ineo|equans|dalkia|veolia|suez|saur|sncf|edf|enedis|orange|total|sogea|razel|fayat|demathieu|"
                            r"leroy merlin|stelia|liebherr|daher|latecoere|ratier|figeac|michelin|ceva|sanofi|turboméca|"
                            r"axians|omexom|actemis|santerne|citeos|getelec|entreprise petit|campenon|gtm|dodin|"
                            r"vallourec|arkema|lafarge|holcim|saint.gobain|schneider|legrand|siemens|alstom|naval group|mbda|"
                            r"cofely|idex|engie|imerys|smurfit|ds smith|lisi|aubert|groupe etchart|etchart|ortec|endel|ponticelli", re.I)
TR = {"11": "10-19", "12": "20-49", "21": "50-99", "22": "100-199", "31": "200-249"}


def ft_search(q, dept, recent):
    out = {}
    for start in range(0, 600, 150):
        p = {"motsCles": q, "lieux": f"{dept}D", "typeContrat": "CDI", "offresPartenaires": "true",
             "range": f"{start}-{start+149}", "tri": "1"}
        if recent:
            p["publieeDepuis"] = "14"
        h = S.get("https://candidat.francetravail.fr/offres/recherche?" + urllib.parse.urlencode(p))
        blocks = re.split(r'(?=<li data-id-offre=)', h)[1:]
        for b in blocks:
            mid = re.search(r'data-id-offre="(\w+)"', b)
            tt = re.search(r'media-heading-title">(.*?)</span>', b, re.S)
            sub = re.search(r'<p translate="no" class="subtext">(.*?)</p>', b, re.S)
            dt = re.search(r'<p class="date">(.*?)</p>', b, re.S)
            ct = re.search(r'<p class="contrat[^"]*">(.*?)</p>', b, re.S)
            desc = re.search(r'<p class="description">(.*?)</p>', b, re.S)
            if not (mid and tt):
                continue
            parts = [x.strip() for x in S.text(sub.group(1)).split(" - ")] if sub else []
            emp = parts[0] if len(parts) >= 3 else ""
            dtxt = S.text(dt.group(1)) if dt else ""
            out[mid.group(1)] = {"id": mid.group(1), "titre": S.text(tt.group(1)), "employeur": emp, "dept": dept,
                                 "ville": parts[-1] if parts else "", "contrat": S.text(ct.group(1)) if ct else "",
                                 "date_txt": dtxt, "date": S.ft_date(dtxt), "description": S.text(desc.group(1)) if desc else "",
                                 "url": f"https://candidat.francetravail.fr/offres/recherche/detail/{mid.group(1)}"}
        if len(blocks) < 150:
            break
        time.sleep(0.3)
    return list(out.values())


def sweep(recent):
    jobs = [(q, d) for q in METIERS for d in DEPTS]
    allo = {}
    with cf.ThreadPoolExecutor(4) as ex:
        for res in ex.map(lambda a: ft_search(a[0], a[1], recent), jobs):
            for o in res:
                allo[o["id"]] = o
    return list(allo.values())


def age_days(o):
    if o["date"] == "30j+":
        return 31
    try:
        return (TODAY - date.fromisoformat(o["date"])).days
    except ValueError:
        return None


# ---------------------------------------------------------------- API recherche-entreprises
def api(params):
    url = "https://recherche-entreprises.api.gouv.fr/search?" + urllib.parse.urlencode(params)
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(url, timeout=30))
        except Exception:
            time.sleep(1.5 * (i + 1))
    return {"results": []}


def lookup(emp, dept):
    """Meilleure correspondance API pour un nom d'employeur, en privilégiant un établissement dans le département."""
    q = re.sub(r"\b(sas|sarl|sa|sasu|eurl|groupe|group)\b", " ", emp, flags=re.I).strip()
    words = [w for w in re.split(r"[^a-z0-9]+", S.norm(q)) if len(w) > 1]
    for params in ({"q": q, "departement": dept, "per_page": 10}, {"q": q, "per_page": 10}):
        time.sleep(0.2)
        for r in api(params).get("results", []):
            names = S.norm(" ".join([r.get("nom_complet") or "", r.get("nom_raison_sociale") or "", r.get("sigle") or ""] +
                                    (r["siege"].get("liste_enseignes") or [])))
            if words and all(w in names for w in words):
                return r
    return None


def describe(r, dept):
    m = [e for e in r.get("matching_etablissements", []) if str(e.get("code_postal", ""))[:2] == dept]
    e = m[0] if m else r["siege"]
    dirs = []
    for d in r.get("dirigeants", []):
        if d.get("type_dirigeant") == "personne physique":
            p = " ".join(dict.fromkeys((d.get("prenoms") or "").split()))
            dirs.append(f"{p.title()} {(d.get('nom') or '').upper()} ({d.get('qualite') or 'n.c.'})")
        else:
            dirs.append(f"{d.get('denomination')} ({d.get('qualite') or 'n.c.'})")
    return {"siren": r["siren"], "raison_sociale": r["nom_complet"], "naf": r.get("activite_principale"),
            "tranche": r.get("tranche_effectif_salarie"), "effectif": TR.get(r.get("tranche_effectif_salarie"), "hors cible"),
            "categorie": r.get("categorie_entreprise"), "ville_etab": e.get("libelle_commune"), "siege": r["siege"].get("libelle_commune"),
            "dirigeants": dirs, "dirigeants_pm": [d.get("denomination") or "" for d in r.get("dirigeants", [])
                                                   if d.get("type_dirigeant") != "personne physique"]}


if __name__ == "__main__":
    recent = sweep(True)
    print("offres CDI < 14 j :", len(recent))
    alls = sweep(False)
    print("offres CDI toutes dates :", len(alls))
    json.dump({"recent": recent, "all": alls}, open("preuve_ft_raw.json", "w"), ensure_ascii=False)

    keep = [o for o in recent if POSTE.search(o["titre"]) and "CDI" in o["contrat"]]
    excl = {"poste hors périmètre": len(recent) - len(keep)}
    by = {}
    for o in keep:
        e = o["employeur"]
        if not e:
            excl["employeur masqué"] = excl.get("employeur masqué", 0) + 1; continue
        if INTERMEDIAIRE.search(e):
            excl["intérim / cabinet"] = excl.get("intérim / cabinet", 0) + 1; continue
        if GRANDS_GROUPES.search(e):
            excl["grand groupe"] = excl.get("grand groupe", 0) + 1; continue
        by.setdefault(S.norm(e), {"employeur": e, "dept": o["dept"], "offres_recentes": []})["offres_recentes"].append(o)
    print("exclusions (offres) :", excl, "| employeurs restants :", len(by))

    # toutes les offres CDI encore en ligne de ces employeurs (tous métiers du périmètre, toutes dates)
    for k, v in by.items():
        v["offres_toutes"] = [o for o in alls if S.norm(o["employeur"]) == k and POSTE.search(o["titre"])]
        ids = {o["id"] for o in v["offres_toutes"]}
        v["offres_toutes"] += [o for o in v["offres_recentes"] if o["id"] not in ids]

    def enrich(item):
        k, v = item
        r = lookup(v["employeur"], v["dept"])
        return k, (describe(r, v["dept"]) if r else None)
    with cf.ThreadPoolExecutor(4) as ex:
        info = dict(ex.map(enrich, by.items()))

    out, rej = [], {}
    for k, v in by.items():
        i = info[k]
        why = None
        if not i:
            why = "introuvable dans l'API"
        elif re.match(r"78\.|70\.22", i["naf"] or ""):
            why = f"NAF {i['naf']} (intermédiaire)"
        elif i["tranche"] not in TR:
            why = f"effectif hors 10-250 ({i['tranche']})"
        elif any(GRANDS_GROUPES.search(pm) for pm in i["dirigeants_pm"]) or i["categorie"] == "GE":
            why = "filiale de grand groupe"
        if why:
            rej[why.split(" (")[0]] = rej.get(why.split(" (")[0], 0) + 1
            continue
        ages = [a for a in (age_days(o) for o in v["offres_toutes"]) if a is not None]
        v.update(info=i, nb_offres=len({S.norm(o["titre"]) + o["ville"] for o in v["offres_toutes"]}),
                 plus_ancienne_jours=max(ages) if ages else None)
        v["priorite"] = (min(v["nb_offres"], 5) * 2) + (3 if (v["plus_ancienne_jours"] or 0) >= 21 else 0)
        out.append(v)
    print("rejets API :", rej, "| PME retenues :", len(out))
    out.sort(key=lambda v: (-v["priorite"], -v["nb_offres"]))
    json.dump(out, open("preuve_candidats.json", "w"), ensure_ascii=False, indent=1)
    for v in out[:30]:
        i = v["info"]
        print(f"{v['priorite']:>2} | {v['employeur'][:32]:32} | {i['effectif']:7} | {i['naf']} | {v['nb_offres']} off. | "
              f"max {v['plus_ancienne_jours']} j | {v['offres_recentes'][0]['titre'][:45]} | {v['offres_recentes'][0]['ville']}")
