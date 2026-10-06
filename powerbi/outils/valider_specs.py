"""Valide chaque spec Vega-Lite et la config commune contre le schéma officiel Vega-Lite v6 (celui de Deneb 2.x)."""
import json
import pathlib
import sys
import urllib.request

import jsonschema

import commun as c

URL = "https://vega.github.io/schema/vega-lite/v6.json"
CACHE = pathlib.Path("/tmp/vega-lite-v6.json")


def schema():
    if not CACHE.exists():
        CACHE.write_bytes(urllib.request.urlopen(URL, timeout=60).read())
    return json.loads(CACHE.read_text(encoding="utf-8"))


def main():
    s = schema()
    ok = True
    v = jsonschema.Draft7Validator(s)
    for f in sorted((c.RACINE / "deneb_specs").glob("0*.json")):
        spec = json.loads(f.read_text(encoding="utf-8"))
        erreurs = sorted(v.iter_errors(spec), key=lambda e: list(e.path))
        print(("OK   " if not erreurs else "ECHEC"), f.name, f"({len(erreurs)} erreur(s))")
        for e in erreurs[:8]:
            ok = False
            print("     ", "/".join(map(str, e.path)), "->", e.message[:160])
    cfg = json.loads((c.RACINE / "deneb_specs" / "_config_commun.json").read_text(encoding="utf-8"))
    cv = jsonschema.Draft7Validator({"$ref": "#/definitions/Config", "definitions": s["definitions"]})
    erreurs = list(cv.iter_errors(cfg))
    print(("OK   " if not erreurs else "ECHEC"), "_config_commun.json", f"({len(erreurs)} erreur(s))")
    for e in erreurs[:8]:
        ok = False
        print("     ", "/".join(map(str, e.path)), "->", e.message[:160])
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
