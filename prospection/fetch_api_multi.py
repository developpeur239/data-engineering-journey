"""Collecte API recherche-entreprises : 78.10Z (tout) + 70.22Z (noms recrutement/search/talent/RH/chasse)
sur les départements 33, 40, 64, 17, 86, 31. Écrit raw_api_multi.json (dédoublonné par SIREN)."""
import json, re, time, urllib.parse, urllib.request
BASE = "https://recherche-entreprises.api.gouv.fr/search"
DEPTS = ["33", "40", "64", "17", "86", "31"]
NAME_7022 = re.compile(r"recrut|search|talent|\bRH\b|chasse", re.I)
Q_7022 = ["recrutement", "recruitment", "search", "talent", "talents", "rh", "chasse", "chasseur"]


def call(params):
    url = BASE + "?" + urllib.parse.urlencode(params)
    for i in range(6):
        try:
            return json.load(urllib.request.urlopen(url, timeout=30))
        except Exception as e:
            time.sleep(2 ** i)  # l'API limite à ~7 req/s
    raise RuntimeError(url)


def all_pages(params):
    out, page = [], 1
    while True:
        d = call({**params, "per_page": 25, "page": page})
        out += d["results"]
        if page >= d["total_pages"]:
            return out, d["total_results"]
        page += 1
        time.sleep(0.25)


res = {}
for dep in DEPTS:
    r, n = all_pages({"activite_principale": "78.10Z", "departement": dep, "etat_administratif": "A"})
    for x in r:
        x["_naf_requete"] = "78.10Z"; x["_dep_requete"] = dep; res.setdefault(x["siren"], x)
    print(dep, "78.10Z", n)
    for q in Q_7022:
        r, n = all_pages({"q": q, "activite_principale": "70.22Z", "departement": dep, "etat_administratif": "A"})
        keep = [x for x in r if NAME_7022.search(x["nom_complet"] + " " + " ".join(x["siege"].get("liste_enseignes") or []))]
        for x in keep:
            x["_naf_requete"] = "70.22Z"; x["_dep_requete"] = dep; res.setdefault(x["siren"], x)
        print(dep, "70.22Z", q, n, "->", len(keep))
json.dump(list(res.values()), open("raw_api_multi.json", "w"), ensure_ascii=False)
print("TOTAL", len(res))
