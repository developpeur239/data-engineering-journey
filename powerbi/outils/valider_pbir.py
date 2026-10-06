"""Valide TOUS les JSON du projet contre les schémas officiels Microsoft (microsoft/json-schemas) et le schéma de thème.

Usage : python3 valider_pbir.py [dossier_json-schemas] [dossier_reportThemeSchema]
Sans argument, les dépôts sont clonés (peu profond) dans /tmp si besoin.
"""
import json
import pathlib
import subprocess
import sys

import jsonschema
from referencing import Registry, Resource

import commun as c

RACINE_URL = "https://developer.microsoft.com/json-schemas/"


def cloner(url, dest, sparse=None):
    if not dest.exists():
        base = ["git", "clone", "--depth", "1"]
        subprocess.run(base + (["--filter=blob:none", "--sparse"] if sparse else []) + [url, str(dest)], check=True)
        if sparse:
            subprocess.run(["git", "-C", str(dest), "sparse-checkout", "set", sparse], check=True)
    return dest


def main():
    schemas = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else cloner("https://github.com/microsoft/json-schemas.git", pathlib.Path("/tmp/json-schemas"))
    themes = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else cloner(
        "https://github.com/microsoft/powerbi-desktop-samples.git", pathlib.Path("/tmp/powerbi-desktop-samples"), "Report Theme JSON Schema")

    def retrieve(uri):
        if not uri.startswith(RACINE_URL):
            raise LookupError(uri)
        chemin = schemas / uri[len(RACINE_URL):].split("#")[0]
        return Resource.from_contents(json.loads(chemin.read_text(encoding="utf-8")))

    registre = Registry(retrieve=retrieve)
    ok = True
    nb = 0

    def valider(fichier: pathlib.Path, schema_uri=None, schema_obj=None):
        nonlocal ok, nb
        doc = json.loads(fichier.read_text(encoding="utf-8"))
        if schema_obj is None:
            schema_uri = schema_uri or doc["$schema"]
            schema_obj = {"$ref": schema_uri}
        v = jsonschema.Draft7Validator(schema_obj, registry=registre)
        erreurs = sorted(v.iter_errors(doc), key=lambda e: list(map(str, e.path)))
        nb += 1
        if erreurs:
            ok = False
            print("ECHEC", fichier.relative_to(c.RACINE), f"({len(erreurs)})")
            for e in erreurs[:6]:
                print("      ", "/".join(map(str, e.path)), "->", e.message[:200])

    valider(c.RACINE / "velib_dashboard.pbip")
    for dossier in (c.RACINE / "velib_dashboard.Report", c.RACINE / "velib_dashboard.SemanticModel"):
        valider(dossier / ".platform")
    valider(c.RACINE / "velib_dashboard.SemanticModel" / "definition.pbism")
    valider(c.RACINE / "velib_dashboard.Report" / "definition.pbir")
    for f in sorted((c.RACINE / "velib_dashboard.Report" / "definition").rglob("*.json")):
        valider(f)
    theme_schema = json.loads(sorted(themes.glob("Report Theme JSON Schema/reportThemeSchema-*.json"),
                                     key=lambda p: [int(x) for x in p.stem.split("-")[1].split(".")])[-1].read_text(encoding="utf-8"))
    valider(c.RACINE / "velib_theme.json", schema_obj=theme_schema)
    valider(c.RACINE / "velib_dashboard.Report" / "StaticResources" / "RegisteredResources" / "velib_theme.json", schema_obj=theme_schema)
    print(("OK" if ok else "ECHEC"), f"- {nb} fichiers JSON validés")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
