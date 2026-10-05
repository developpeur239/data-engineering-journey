#!/usr/bin/env python3
"""Collecte d'échantillons pour le projet datalake Azure (Bronze/Silver/Gold).

Télécharge un petit échantillon brut de chaque source dans ./echantillons/<source>/
et écrit, à côté de chaque fichier, un fichier <nom>.meta.json (URL, code HTTP,
temps de réponse, taille, sha256, horodatage de collecte). Le fichier brut n'est
jamais transformé : c'est exactement ce qu'on déposera en zone Bronze.

Usage :
    python collecte_test.py all
    python collecte_test.py velib --polls 3 --interval 60
    python collecte_test.py meteo carburants
    python collecte_test.py dvf --departement 75 --annee 2025
    python collecte_test.py dpe --size 100 --code-postal 75011

Dépendance : requests (pip install requests).
Pour l'ingestion Bronze, il suffira de remplacer `sauver()` par un upload vers
ADLS Gen2 (azure-storage-file-datalake) en gardant le même chemin
<source>/<date de collecte>/<fichier>.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import sys
import time
import zipfile
from pathlib import Path

import requests

RACINE = Path(__file__).resolve().parent / "echantillons"
TAILLE_MAX = 20 * 1024 * 1024  # garde-fou : jamais plus de 20 Mo par fichier
USER_AGENT = "datalake-m2-collecte-test/1.0 (projet pedagogique)"

URLS = {
    "velib_status": "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json",
    "velib_info": "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json",
    "meteo_forecast": "https://api.open-meteo.com/v1/forecast",
    "meteo_archive": "https://archive-api.open-meteo.com/v1/archive",
    "carburants": "https://donnees.roulez-eco.fr/opendata/instantane",
    "dvf": "https://files.data.gouv.fr/geo-dvf/latest/csv/{annee}/departements/{dep}.csv.gz",
    "dpe": "https://data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines",
}


def horodatage() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def telecharger(url: str, params: dict | None = None, essais: int = 4) -> tuple[bytes, dict]:
    """GET en streaming, coupé à TAILLE_MAX, avec retry/backoff (2, 4, 8 s).

    Renvoie (contenu, métadonnées). Les erreurs réseau et les 429/5xx sont
    retentés : l'API archive d'Open-Meteo et data.gouv.fr ont été instables
    pendant les tests.
    """
    derniere_erreur = None
    for essai in range(1, essais + 1):
        debut = time.monotonic()
        try:
            with requests.get(url, params=params, stream=True, timeout=60,
                              headers={"User-Agent": USER_AGENT}) as r:
                if r.status_code == 429 and "Daily API request limit" in r.text:
                    # quota journalier Open-Meteo (par IP) : retenter ne sert à rien
                    raise RuntimeError(f"Quota journalier épuisé : {r.text[:200]}")
                if r.status_code == 429 or r.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
                r.raise_for_status()
                buf = io.BytesIO()
                tronque = False
                for bloc in r.iter_content(64 * 1024):
                    buf.write(bloc)
                    if buf.tell() >= TAILLE_MAX:
                        tronque = True
                        break
                contenu = buf.getvalue()[:TAILLE_MAX]
                meta = {
                    "url": r.url,
                    "http_status": r.status_code,
                    "temps_reponse_s": round(time.monotonic() - debut, 3),
                    "content_type": r.headers.get("Content-Type"),
                    "last_modified": r.headers.get("Last-Modified"),
                    "taille_octets": len(contenu),
                    "tronque_a_20Mo": tronque,
                    "essai": essai,
                }
                return contenu, meta
        except requests.RequestException as e:
            derniere_erreur = e
            print(f"  ! essai {essai}/{essais} échoué ({e})", file=sys.stderr)
            if essai < essais:
                time.sleep(2 ** essai)
    raise RuntimeError(f"Échec après {essais} essais : {url} ({derniere_erreur})")


def sauver(source: str, nom: str, contenu: bytes, meta: dict) -> Path:
    dossier = RACINE / source
    dossier.mkdir(parents=True, exist_ok=True)
    chemin = dossier / nom
    chemin.write_bytes(contenu)
    meta = {**meta, "fichier": nom, "collecte_utc": horodatage(),
            "sha256": hashlib.sha256(contenu).hexdigest()}
    chemin.with_name(nom + ".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"  -> {chemin.relative_to(RACINE.parent)} ({len(contenu):,} o, HTTP {meta['http_status']}, "
          f"{meta['temps_reponse_s']} s)")
    return chemin


# --------------------------------------------------------------------------- sources

def collecter_velib(polls: int = 3, interval: int = 60) -> None:
    print("[A] Vélib' GBFS")
    contenu, meta = telecharger(URLS["velib_info"])
    sauver("velib", f"station_information_{horodatage()}.json", contenu, meta)
    for i in range(polls):
        contenu, meta = telecharger(URLS["velib_status"])
        sauver("velib", f"station_status_{horodatage()}.json", contenu, meta)
        if i < polls - 1:
            time.sleep(interval)


def collecter_meteo(lat: float = 48.85, lon: float = 2.35) -> None:
    print("[B] Open-Meteo")
    variables = "temperature_2m,precipitation"
    contenu, meta = telecharger(URLS["meteo_forecast"], {
        "latitude": lat, "longitude": lon, "hourly": variables, "timezone": "Europe/Paris"})
    sauver("meteo", f"forecast_{horodatage()}.json", contenu, meta)

    # Semaine passée complète (lundi -> dimanche) terminée il y a au moins 7 jours :
    # l'archive (ERA5) est publiée avec ~5 jours de retard.
    aujourd_hui = dt.date.today()
    fin = aujourd_hui - dt.timedelta(days=aujourd_hui.weekday() + 8)
    debut = fin - dt.timedelta(days=6)
    contenu, meta = telecharger(URLS["meteo_archive"], {
        "latitude": lat, "longitude": lon, "hourly": variables, "timezone": "Europe/Paris",
        "start_date": debut.isoformat(), "end_date": fin.isoformat()})
    sauver("meteo", f"archive_{debut}_{fin}.json", contenu, meta)


def collecter_carburants() -> None:
    print("[C] Prix des carburants (flux instantané)")
    contenu, meta = telecharger(URLS["carburants"])
    nom_zip = f"instantane_{horodatage()}.zip"
    sauver("carburants", nom_zip, contenu, meta)
    with zipfile.ZipFile(io.BytesIO(contenu)) as z:
        for info in z.infolist():
            if info.file_size > TAILLE_MAX:
                print(f"  ! {info.filename} dépasse 20 Mo décompressé, non extrait")
                continue
            xml = z.read(info)
            sauver("carburants", f"{Path(nom_zip).stem}_{info.filename}", xml,
                   {**meta, "extrait_de": nom_zip, "taille_octets": len(xml)})


def collecter_dvf(departement: str = "75", annee: int = 2025) -> None:
    print(f"[D] DVF géolocalisé — département {departement}, année {annee}")
    url = URLS["dvf"].format(annee=annee, dep=departement)
    contenu, meta = telecharger(url)
    sauver("dvf", f"dvf_{annee}_{departement}.csv.gz", contenu, meta)


def collecter_dpe(size: int = 100, code_postal: str | None = None) -> None:
    print(f"[E] ADEME DPE logements existants — {size} lignes")
    if size > 10000:
        raise ValueError("L'API data-fair limite size à 10000 (paginer ensuite avec le paramètre 'after').")
    params = {"size": size, "format": "csv"}
    suffixe = "france"
    if code_postal:
        params["code_postal_ban_eq"] = code_postal
        suffixe = code_postal
    contenu, meta = telecharger(URLS["dpe"], params)
    sauver("dpe", f"dpe03existant_{suffixe}_{size}_{horodatage()}.csv", contenu, meta)


# --------------------------------------------------------------------------- CLI

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sources", nargs="+", choices=["all", "velib", "meteo", "carburants", "dvf", "dpe"])
    p.add_argument("--polls", type=int, default=3, help="nombre d'appels station_status (défaut 3)")
    p.add_argument("--interval", type=int, default=60, help="secondes entre deux appels Vélib' (défaut 60)")
    p.add_argument("--departement", default="75")
    p.add_argument("--annee", type=int, default=2025)
    p.add_argument("--size", type=int, default=100, help="lignes DPE (max 10000)")
    p.add_argument("--code-postal", default=None, help="filtre DPE optionnel, ex. 75011")
    a = p.parse_args()

    sources = {"velib", "meteo", "carburants", "dvf", "dpe"} if "all" in a.sources else set(a.sources)
    taches = [
        ("meteo", lambda: collecter_meteo()),
        ("carburants", collecter_carburants),
        ("dvf", lambda: collecter_dvf(a.departement, a.annee)),
        ("dpe", lambda: collecter_dpe(a.size, a.code_postal)),
        ("velib", lambda: collecter_velib(a.polls, a.interval)),  # en dernier : la plus longue
    ]
    erreurs = []
    for nom, f in taches:
        if nom in sources:
            try:
                f()
            except Exception as e:  # une source en panne ne bloque pas les autres
                print(f"  !! {nom} : {e}", file=sys.stderr)
                erreurs.append(nom)
    if erreurs:
        sys.exit(f"Sources en échec : {', '.join(erreurs)}")


if __name__ == "__main__":
    main()
