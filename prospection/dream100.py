"""Liste "Dream 100" d'artisans à démarcher (relance de devis), à partir de
l'API publique Recherche d'entreprises (recherche-entreprises.api.gouv.fr,
données INSEE / RNE / INPI, sans clé).

Usage :
    python prospection/dream100.py --naf 43.22B,43.22A --dep 33 --nom chauffagistes_33

Critères : entreprise active, siège dans le département (on écarte les
groupes nationaux qui n'ont qu'une agence locale), CA ≤ 20 M€, puis 3 paliers :
  A : CA publié récent (≥ 2022) ≥ 800 k€
  B : 10 salariés ou plus (CA non publié)
  C : CA 500-800 k€ ou 6-9 salariés
Tri : palier, puis CA décroissant, puis effectif. Plusieurs codes NAF possibles
(--naf 43.22B,43.22A).
"""

import argparse
import csv
import json
import re
import time
from pathlib import Path
from urllib.parse import quote_plus

import requests

API = "https://recherche-entreprises.api.gouv.fr/search"
HERE = Path(__file__).parent
CA_MIN, CA_MAX = 800_000, 20_000_000
TARGET = 100

EFFECTIFS = {  # codes INSEE des tranches d'effectif salarié
    "NN": "non renseigné", "00": "0", "01": "1-2", "02": "3-5", "03": "6-9",
    "11": "10-19", "12": "20-49", "21": "50-99", "22": "100-199", "31": "200-249",
    "32": "250-499", "41": "500-999", "42": "1000-1999", "51": "2000-4999",
}
TEN_PLUS = {"11", "12", "21", "22", "31", "32", "41", "42", "51"}
NOT_PEOPLE = ("commissaire", "auditeur")
GROUPS = ("EIFFAGE", "ENGIE", "VINCI", "SPIE", "BOUYGUES", "DALKIA", "IDEX", "EQUANS",
          "AXIMA", "COFELY", "PROXISERVE", "ISERBA", "SAVELYS", "ELYO", "CRAM ")


def fetch_page(naf, dep, page):
    cache = HERE / ".cache" / f"{naf}_{dep}_{page}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    for attempt in range(6):
        try:
            r = requests.get(API, params={
                "activite_principale": naf, "departement": dep, "etat_administratif": "A",
                "per_page": 25, "page": page}, timeout=30)
        except requests.ConnectionError:   # coupure réseau passagère
            time.sleep(2 + 2 * attempt)
            continue
        if r.status_code == 429:  # limite de débit de l'API (7 req/s)
            time.sleep(2 + attempt)
            continue
        r.raise_for_status()
        cache.parent.mkdir(exist_ok=True)
        cache.write_text(r.text)
        return r.json()
    raise RuntimeError(f"échec page {page} après plusieurs tentatives")


def fetch_all(naf, dep):
    page, out = 1, []
    while True:
        data = fetch_page(naf, dep, page)
        out += data["results"]
        if page >= data.get("total_pages", 1):
            return out, data.get("total_results")
        page += 1
        time.sleep(0.2)


def latest_finances(f):
    if not f:
        return None, None, None
    year = max(f)
    return int(year), f[year].get("ca"), f[year].get("resultat_net")


def to_row(e, dep):
    siege = e.get("siege", {})
    year, ca, net = latest_finances(e.get("finances"))
    if not ca:          # 0 € = comptes non publiés (confidentialité), pas un vrai CA
        ca = None
    people = [d for d in e.get("dirigeants", [])
              if d.get("type_dirigeant") == "personne physique"
              and not any(w in (d.get("qualite") or "").lower() for w in NOT_PEOPLE)]
    dirigeant = ", ".join(
        f"{(d.get('prenoms') or '').split(' ')[0].title()} "
        f"{re.sub(r'\s*\(.*?\)', '', d.get('nom') or '').title()} "
        f"({d.get('qualite') or '?'})".strip() for d in people[:2])
    nom = e.get("nom_complet", "")
    ville = siege.get("libelle_commune", "")
    return {
        "nom": nom,
        "enseigne": ", ".join(siege.get("liste_enseignes") or []),
        "ville": ville, "code_postal": siege.get("code_postal", ""),
        "adresse": siege.get("adresse", ""),
        "ca": ca if ca is not None else "", "annee_ca": year or "",
        "resultat_net": net if net is not None else "",
        "effectif": EFFECTIFS.get(e.get("tranche_effectif_salarie") or "NN", "?"),
        "_eff": e.get("tranche_effectif_salarie") or "NN",
        "creation": e.get("date_creation", ""),
        "dirigeants": dirigeant,
        "siren": e.get("siren", ""),
        "lien_pappers": f"https://www.pappers.fr/entreprise/{e.get('siren', '')}",
        "recherche_google_maps": "https://www.google.com/maps/search/?api=1&query="
                                 + quote_plus(f"{nom} {ville}"),
        "_siege_dep": siege.get("departement", ""),
        "_dep": dep,
    }


def tier(r):
    ca = r["ca"] if r["ca"] != "" and r["annee_ca"] >= 2022 else None
    if ca is not None and ca > CA_MAX:
        return None                       # trop gros (groupes)
    if ca is not None and ca >= CA_MIN:
        return "A"
    if r["_eff"] in TEN_PLUS:
        return "B"
    if (ca is not None and ca >= 500_000) or r["_eff"] == "03":
        return "C"
    return None


TIER_LABEL = {"A": "A : CA publié ≥ 800 k€", "B": "B : 10 salariés ou +",
              "C": "C : CA 500-800 k€ ou 6-9 salariés"}
EFF_RANK = ["03", "11", "12", "21", "22", "31", "32", "41", "42", "51"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--naf", required=True, help="un ou plusieurs codes, séparés par des virgules")
    ap.add_argument("--dep", required=True)
    ap.add_argument("--nom", required=True)
    a = ap.parse_args()

    rows, seen = [], set()
    for naf in a.naf.split(","):
        raw, total = fetch_all(naf, a.dep)
        print(f"{total} entreprises actives NAF {naf} dans le {a.dep}")
        for e in raw:
            r = to_row(e, a.dep)
            if any(g in r["nom"].upper() for g in GROUPS):
                continue  # filiales de grands groupes : pas de devis aux particuliers
            if r["_siege_dep"] != a.dep or r["siren"] in seen:
                continue  # on écarte les groupes nationaux (siège ailleurs)
            seen.add(r["siren"])
            r["naf"] = naf
            r["_tier"] = tier(r)
            if r["_tier"]:
                r["palier"] = TIER_LABEL[r["_tier"]]
                rows.append(r)
    rows.sort(key=lambda r: (r["_tier"], -(r["ca"] if r["ca"] != "" and r["annee_ca"] >= 2022 else 0),
                             -(EFF_RANK.index(r["_eff"]) if r["_eff"] in EFF_RANK else -1),
                             r["naf"] != "43.22B"))
    picked = rows[:TARGET]
    for t in "ABC":
        print(f"  palier {t} : {sum(r['_tier'] == t for r in rows)} disponibles, "
              f"{sum(r['_tier'] == t for r in picked)} retenues")

    out = HERE / f"dream100_{a.nom}.csv"
    fields = ["nom", "enseigne", "ville", "code_postal", "ca", "annee_ca", "resultat_net",
              "effectif", "palier", "naf", "creation", "dirigeants", "adresse", "siren",
              "lien_pappers", "recherche_google_maps"]
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(picked)
    print(f"{len(picked)} entreprises -> {out}")


if __name__ == "__main__":
    main()
