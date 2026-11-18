"""Enrichit une liste Dream 100 avec Google Places (API "Places API (New)") :
site web, téléphone, note et nombre d'avis Google, fiche Google Maps.

Usage :
    export GOOGLE_PLACES_API_KEY="..."
    python prospection/enrichir_places.py prospection/dream100_chauffagistes_33.csv

Sortie : <fichier>_enrichi.csv à côté du fichier d'entrée.
Coût : 1 appel "Text Search" par entreprise (2 si la première recherche ne
correspond pas). Réponses mises en cache dans prospection/.cache/places/.
"""

import csv
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
from pathlib import Path

import requests

KEY = os.environ.get("GOOGLE_PLACES_API_KEY")
URL = "https://places.googleapis.com/v1/places:searchText"
CACHE = Path(__file__).parent / ".cache" / "places"
FIELDS = ",".join("places." + f for f in [
    "displayName", "formattedAddress", "websiteUri", "nationalPhoneNumber",
    "rating", "userRatingCount", "googleMapsUri", "businessStatus", "primaryTypeDisplayName"])
LEGAL = re.compile(r"\b(sarl|sas|sasu|eurl|sa|snc|ets|entreprise|societe|ste)\b")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    s = LEGAL.sub(" ", re.sub(r"\(.*?\)", " ", s))
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def search(query):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha1(query.encode()).hexdigest() + ".json")
    if path.exists():
        return json.loads(path.read_text())
    for attempt in range(4):
        try:
            r = requests.post(URL, timeout=30, headers={
                "X-Goog-Api-Key": KEY, "X-Goog-FieldMask": FIELDS},
                json={"textQuery": query, "languageCode": "fr", "regionCode": "FR",
                      "pageSize": 1})
        except requests.ConnectionError:
            time.sleep(2 + 2 * attempt)
            continue
        if r.status_code == 429:
            time.sleep(5)
            continue
        if r.status_code != 200:
            raise RuntimeError(f"Places -> {r.status_code}: {r.text[:300]}")
        data = r.json()
        path.write_text(json.dumps(data))
        return data
    raise RuntimeError("Places : échec après plusieurs tentatives")


def match(row, place):
    """ok si même code postal ET un mot du nom en commun ; sinon à vérifier."""
    addr = place.get("formattedAddress", "")
    same_cp = row["code_postal"] and row["code_postal"] in addr
    names = norm(row["nom"]).split() + norm(row["enseigne"]).split()
    found = norm(place.get("displayName", {}).get("text", "")).split()
    common = {w for w in names if len(w) > 2} & set(found)
    if same_cp and common:
        return "ok"
    if common or same_cp:
        return "à vérifier"
    return "douteux"


def main():
    if not KEY or len(sys.argv) < 2:
        sys.exit("Usage : GOOGLE_PLACES_API_KEY=... python enrichir_places.py <liste.csv>")
    src = Path(sys.argv[1])
    rows = list(csv.DictReader(src.open(encoding="utf-8")))
    calls = 0
    for row in rows:
        base = re.sub(r"\s*\(.*?\)", "", row["nom"]).strip()
        queries = []
        if row["enseigne"]:
            queries.append(f"{row['enseigne'].split(',')[0]} {row['ville']}")
        queries.append(f"{base} {row['ville']}")
        best, quality = None, "introuvable"
        for q in dict.fromkeys(queries):
            data = search(q)
            calls += 1
            places = data.get("places", [])
            if not places:
                continue
            m = match(row, places[0])
            if best is None or ["douteux", "à vérifier", "ok"].index(m) > \
                    ["douteux", "à vérifier", "ok"].index(quality if quality != "introuvable" else "douteux"):
                best, quality = places[0], m
            if m == "ok":
                break
        p = best or {}
        row.update({
            "site_web": p.get("websiteUri", ""),
            "telephone": p.get("nationalPhoneNumber", ""),
            "note_google": p.get("rating", ""),
            "nb_avis_google": p.get("userRatingCount", ""),
            "categorie_google": p.get("primaryTypeDisplayName", {}).get("text", ""),
            "nom_google": p.get("displayName", {}).get("text", ""),
            "adresse_google": p.get("formattedAddress", ""),
            "fiche_google_maps": p.get("googleMapsUri", ""),
            "statut_google": p.get("businessStatus", ""),
            "correspondance": quality,
        })
    # Signal "clientèle de particuliers" : les artisans qui travaillent chez des
    # particuliers accumulent des avis Google ; le tertiaire très peu.
    for row in rows:
        n = row["nb_avis_google"]
        row["signal_particuliers"] = ("" if n == "" else "fort (50+ avis)" if n >= 50
                                      else "moyen (15-49 avis)" if n >= 15
                                      else "faible (tertiaire ?)")
    # Plusieurs sociétés du registre peuvent pointer vers la même fiche Google
    # (même groupe familial, filiales) : on le signale.
    first = {}
    for row in rows:
        uri = row["fiche_google_maps"]
        if uri and uri in first:
            row["meme_fiche_que"] = first[uri]
        else:
            row["meme_fiche_que"] = ""
            if uri:
                first[uri] = row["nom"]
    out = src.with_name(src.stem + "_enrichi.csv")
    fields = list(rows[0].keys())
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} entreprises, {calls} recherches (cache compris) -> {out}")


if __name__ == "__main__":
    main()
