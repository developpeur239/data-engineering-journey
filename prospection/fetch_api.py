"""Étape 1-2 : récupère les entreprises NAF 78.10Z actives en Gironde (33)."""
import json, time, urllib.request, urllib.parse

BASE = "https://recherche-entreprises.api.gouv.fr/search"
params = dict(activite_principale="78.10Z", departement="33", etat_administratif="A", per_page=25)
out, page, pages = [], 1, 1
while page <= pages:
    url = BASE + "?" + urllib.parse.urlencode({**params, "page": page})
    for attempt in range(5):
        try:
            d = json.load(urllib.request.urlopen(url, timeout=30)); break
        except Exception as e:
            time.sleep(2 ** attempt)
    pages = d["total_pages"]; out += d["results"]; page += 1
    time.sleep(0.3)
json.dump(out, open("raw_api.json", "w"), ensure_ascii=False, indent=1)
print(len(out), "entreprises")
