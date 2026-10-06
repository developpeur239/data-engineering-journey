"""Prépare deneb_specs/paris_fond.json : limite de Paris + Seine et canaux (GeoJSON simplifié, ~20 Ko).

Sources (Open Data Paris, licence ODbL) :
  - arrondissements          -> limite de Paris (union des 20 arrondissements)
  - plan-de-voirie-voies-deau -> Seine et canaux (emprises des voies d'eau, petits fragments écartés)
Nécessite un accès réseau et `pip install shapely`. Le fichier produit est versionné : ce script n'a besoin
d'être relancé que pour le refaire.
"""
import gzip
import json
import urllib.request

from shapely.geometry import mapping, shape
from shapely.ops import unary_union

import commun as c

BASE = "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/{}/exports/geojson"


def charger(nom):
    b = urllib.request.urlopen(BASE.format(nom), timeout=120).read()
    return json.loads(gzip.decompress(b) if b[:2] == b"\x1f\x8b" else b)


def arrondir(geom, n=4):
    def r(x):
        if isinstance(x, (list, tuple)) and x and isinstance(x[0], (int, float)):
            return [round(v, n) for v in x]
        return [r(i) for i in x]
    g = mapping(geom)
    return {"type": g["type"], "coordinates": r(g["coordinates"])}


def main():
    paris = unary_union([shape(f["geometry"]).buffer(0) for f in charger("arrondissements")["features"]]).simplify(0.0003)
    eau = [shape(f["geometry"]).buffer(0) for f in charger("plan-de-voirie-voies-deau")["features"]]
    eau = unary_union([g for g in eau if g.area * 1e6 >= 2]).simplify(0.00015)
    fond = {"type": "FeatureCollection",
            "source": "Open Data Paris : jeux « arrondissements » et « plan-de-voirie-voies-deau » (https://opendata.paris.fr)",
            "licence": "Open Database License (ODbL) 1.0 : mention « Données © Ville de Paris »",
            "traitement": "union des arrondissements, simplification (≈ 30 m pour la limite, ≈ 15 m pour l'eau), coordonnées arrondies à 4 décimales",
            "features": [
                {"type": "Feature", "properties": {"nom": "Limite de Paris"}, "geometry": arrondir(paris)},
                {"type": "Feature", "properties": {"nom": "Seine et canaux"}, "geometry": arrondir(eau)}]}
    sortie = c.RACINE / "deneb_specs" / "paris_fond.json"
    sortie.write_text(json.dumps(fond, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print("ok", sortie.name, sortie.stat().st_size, "octets")


if __name__ == "__main__":
    main()
