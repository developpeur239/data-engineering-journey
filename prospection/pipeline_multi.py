"""Pipeline élargi (6 départements, 78.10Z + 70.22Z filtré) : exclusions -> enrichissement auto -> CSV.

Entrée  : raw_api_multi.json (fetch_api_multi.py)
Sortie  : candidates_multi.csv (même schéma que cabinets_bordeaux.csv + departement, naf)
Les cabinets de Gironde déjà vérifiés à la main reprennent leurs valeurs de cabinets_bordeaux.csv.
"""
import csv, json, re, concurrent.futures as cf
from guess_domains import check as guess_site
from scrape_sites import run as scrape, CORE

TR = {"NN": "non renseigné", "00": "0 salarié", "01": "1-2", "02": "3-5", "03": "6-9", "11": "10-19", "12": "20-49",
      "21": "50-99", "22": "100-199", "31": "200-249", "32": "250-499", "41": "500-999", "42": "1000-1999", "51": "2000-4999"}
BIG = {"21", "22", "31", "32", "41", "42", "51", "52", "53"}
RESEAUX = re.compile(r"MICHAEL PAGE|PAGE PERSONNEL|\bHAYS\b|ADECCO|RANDSTAD|MANPOWER|ROBERT WALTERS|WALTERS PEOPLE|ROBERT HALF|"
                     r"EXPECTRA|\bLHH\b|BADENOCH|MERCURI URVAL|\bAPEC\b|HARRY HOPE|WINSEARCH|SPRING|KELLY|SYNERGIE|\bCRIT\b|"
                     r"PROMAN|SAMSIC|PARTNAIRE|START PEOPLE|SUPPLAY|\bACTUAL\b|GROUPE LIP|STAFFMATCH|MISTERTEMP|TEMPORIS|"
                     r"DOMINO|\bFED\b|MORGAN PHILIPS|HUDSON|GRAFTON|AXEO|ADEQUAT|PLANETT|MACANDERS|MENWAY|^PROFIL\b|JOB LINK", re.I)
INTERIM = re.compile(r"INTERIM|INTÉRIM|TEMPORAIRE|\bETT\b|TRAVAIL TEMP|OPTEAMAN|JOB INTER|ADOMO", re.I)
HORS = re.compile(r"GROUPEMENT|\bGEIQ\b|^GE\b|\bASS(?:OCIATION)?\b|INSERTION|EMPLOI LOCAL|H[OÔ]TESSE|MANNEQUIN|CASTING|"
                  r"MISSION LOCALE|POLE EMPLOI|FRANCE TRAVAIL|CHAMBRE|\bCCI\b|MAIRIE|COMMUNAUT", re.I)
# Exclusions manuelles déjà établies sur la Gironde
MANUEL = {"481861094": "agence d'hôtesses", "752361147": "agence d'hôtesses/mannequins", "819054586": "agence d'hôtesses",
          "383666377": "NAF erroné (distribution)", "478077233": "groupe (Menway)", "921801924": "en liquidation",
          "984848796": "activité hors recrutement (NAF erroné)"}
NAME_HINT = re.compile(r"industri|\bbtp\b|batiment|bâtiment|construct|ingenier|ingénier|manufact|\benr\b|energ|aero|aéro|"
                       r"maintenance|technique|tech\b|travaux", re.I)


def norm_row(r):
    m = [e for e in r.get("matching_etablissements", []) if str(e.get("code_postal", ""))[:2] == r["_dep_requete"]]
    e = m[0] if m else r["siege"]
    dirs = []
    for d in r.get("dirigeants", []):
        if d.get("type_dirigeant") == "personne physique":
            p = " ".join(dict.fromkeys((d.get("prenoms") or "").split()))
            dirs.append(f"{p.title()} {(d.get('nom') or '').upper()} ({d.get('qualite') or 'n.c.'})")
        else:
            dirs.append(f"{d.get('denomination')} ({d.get('qualite') or 'n.c.'})")
    return {"nom": r["nom_complet"], "siren": r["siren"], "naf": r["_naf_requete"], "departement": r["_dep_requete"],
            "date_creation": r.get("date_creation") or "1900-01-01",
            "tranche_effectif": TR.get(r.get("tranche_effectif_salarie"), "non renseigné"),
            "ville": e.get("libelle_commune"), "adresse": e.get("adresse"), "dirigeants": " ; ".join(dirs),
            "_tranche": r.get("tranche_effectif_salarie"), "_nature": str(r.get("nature_juridique") or "")}


def exclusion(x):
    n = x["nom"]
    if x["siren"] in MANUEL:
        return MANUEL[x["siren"]]
    if RESEAUX.search(n):
        return "grand réseau / groupe"
    if INTERIM.search(n):
        return "intérim / services"
    if x["_tranche"] in BIG:
        return "> 50 salariés"
    if HORS.search(n) or x["_nature"].startswith("92"):
        return "hors cible (groupement d'employeurs, association, hôtesses, organisme public)"
    return None


def auto_score(s, nom):
    """Score 0-3 automatique à partir du site (titre, meta, mots-clés) ou à défaut du nom."""
    if s and s.get("site_ok"):
        head = (s.get("title", "") + " " + s.get("meta", "")).lower()
        if re.search(r"btp|industri|construction|b[âa]timent|ing[ée]nierie|a[ée]ronauti|maintenance|travaux", head):
            return 3
        home = [k for k in CORE if s["kw_home"].get(k)]
        full = [k for k in CORE if s["kw_full"].get(k)]
        if len(home) >= 3:
            return 2
        if full:
            return 1
        return 1 if NAME_HINT.search(nom) else 0
    return 1 if NAME_HINT.search(nom) else 0


def specialite(s):
    if not (s and s.get("site_ok")):
        return "Inconnue (aucune présence web trouvée)"
    top = sorted(s["kw_full"].items(), key=lambda kv: -kv[1])[:5]
    t = (s.get("meta") or s.get("title") or "")[:140]
    return (t + " — " if t else "") + "mots-clés : " + ", ".join(k for k, _ in top)


if __name__ == "__main__":
    raw = json.load(open("raw_api_multi.json"))
    rows = [norm_row(r) for r in raw]
    excl = [(x, exclusion(x)) for x in rows]
    keep = [x for x, e in excl if not e]
    json.dump([{**x, "raison_exclusion": e} for x, e in excl if e], open("exclus_multi.json", "w"), ensure_ascii=False, indent=1)
    print(len(rows), "entreprises,", len(keep), "retenues,", len(rows) - len(keep), "exclues")

    manual = {r["siren"]: r for r in csv.DictReader(open("../cabinets_bordeaux.csv", encoding="utf-8-sig"), delimiter=";")}
    todo = [x for x in keep if x["siren"] not in manual]
    import os
    if os.path.exists("sites_scraped_multi.json"):
        scraped = json.load(open("sites_scraped_multi.json"))
    else:
        with cf.ThreadPoolExecutor(16) as ex:
            sites = dict(ex.map(guess_site, todo))
        json.dump(sites, open("sites_guess_multi.json", "w"))
        with cf.ThreadPoolExecutor(12) as ex:
            scraped = dict(ex.map(lambda kv: (kv[0], scrape(kv)[1] if kv[1] else {"site_ok": False}), sites.items()))
        json.dump(scraped, open("sites_scraped_multi.json", "w"), ensure_ascii=False)
    out = []
    for x in keep:
        if x["siren"] in manual:
            m = manual[x["siren"]]
            row = {**x, **{k: m[k] for k in ("site_web", "telephone", "specialite", "score_btp_industrie", "notes")}}
        else:
            s = scraped.get(x["siren"], {})
            row = {**x, "site_web": s.get("url", "") if s.get("site_ok") else "",
                   "telephone": " / ".join(t[:2] + " " + t[2:4] + " " + t[4:6] + " " + t[6:8] + " " + t[8:] for t in s.get("tel", [])[:2]),
                   "specialite": specialite(s), "score_btp_industrie": auto_score(s, x["nom"]),
                   "notes": ("site détecté automatiquement (à vérifier)" if s.get("site_ok") else "") +
                            (" ; NAF 70.22Z (conseil) : vérifier qu'il s'agit bien de recrutement" if x["naf"] == "70.22Z" else "")}
        out.append({k: v for k, v in row.items() if not k.startswith("_")})
    out.sort(key=lambda r: (-int(r["score_btp_industrie"]), -int(r["date_creation"].replace("-", ""))))
    with open("candidates_multi.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter=";"); w.writeheader(); w.writerows(out)
    from collections import Counter
    print("score:", Counter(int(r["score_btp_industrie"]) for r in out), "| sites:", sum(1 for r in out if r["site_web"]),
          "| dept:", Counter(r["departement"] for r in out))
