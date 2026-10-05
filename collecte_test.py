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
    PRIM_API_KEY=... python collecte_test.py prim --polls 3 --interval 120
    python collecte_test.py idfm
    python collecte_test.py hist-velib --debut 2021-03-01 --fin 2021-03-31
    python collecte_test.py hist-ratpstatus --debut 2026-09-01 --fin 2026-09-03

Dépendance : requests (pip install requests).
Pour l'ingestion Bronze, il suffira de remplacer `sauver()` par un upload vers
ADLS Gen2 (azure-storage-file-datalake) en gardant le même chemin
<source>/<date de collecte>/<fichier>.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import statistics
import subprocess
import sys
import tarfile
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
    # PRIM (Île-de-France Mobilités) — Messages Info Trafic, requête globale. Clé obligatoire.
    "prim_disruptions": "https://prim.iledefrance-mobilites.fr/marketplace/disruptions_bulk/disruptions/v2",
    # IDFM open data — « Arrêts et lignes associées » (un arrêt x une ligne, avec coordonnées)
    "idfm_arrets_lignes": "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets-lignes/exports/csv",
    # Historiques communautaires (non officiels)
    # NB : le README annonce le tag « latest », qui n'existe pas (404) ; l'asset est sous le tag « new ».
    "hist_velib_zip": "https://github.com/lovasoa/historique-velib-opendata/releases/download/new/stations.zip",
    "hist_ratpstatus_git": "https://github.com/wincelau/ratpstatus",
    "hist_ratpstatus_raw": "https://raw.githubusercontent.com/wincelau/ratpstatus/main/datas/json/{jour}/{fichier}",
}


def horodatage() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def telecharger(url: str, params: dict | None = None, essais: int = 4,
                headers: dict | None = None, taille_max: int = TAILLE_MAX) -> tuple[bytes, dict]:
    """GET en streaming, coupé à `taille_max`, avec retry/backoff (2, 4, 8 s).

    Renvoie (contenu, métadonnées). Les erreurs réseau et les 429/5xx sont
    retentés : l'API archive d'Open-Meteo et data.gouv.fr ont été instables
    pendant les tests. Les autres 4xx (401 clé invalide...) ne le sont pas.
    Les en-têtes de requête (`headers`, ex. une clé d'API) ne sont JAMAIS
    recopiés dans les métadonnées.
    """
    derniere_erreur = None
    for essai in range(1, essais + 1):
        debut = time.monotonic()
        try:
            with requests.get(url, params=params, stream=True, timeout=60,
                              headers={"User-Agent": USER_AGENT, **(headers or {})}) as r:
                if r.status_code == 429 and "Daily API request limit" in r.text:
                    # quota journalier Open-Meteo (par IP) : retenter ne sert à rien
                    raise RuntimeError(f"Quota journalier épuisé : {r.text[:200]}")
                if r.status_code == 429 or r.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
                if r.status_code >= 400:  # 401/403/404 : retenter ne sert à rien
                    raise RuntimeError(f"HTTP {r.status_code} sur {url} : {r.text[:200]}")
                buf = io.BytesIO()
                tronque = False
                for bloc in r.iter_content(64 * 1024):
                    buf.write(bloc)
                    if buf.tell() >= taille_max:
                        tronque = True
                        break
                contenu = buf.getvalue()[:taille_max]
                meta = {
                    "url": r.url,
                    "http_status": r.status_code,
                    "temps_reponse_s": round(time.monotonic() - debut, 3),
                    "content_type": r.headers.get("Content-Type"),
                    "last_modified": r.headers.get("Last-Modified"),
                    "taille_octets": len(contenu),
                    "tronque": tronque,
                    "essai": essai,
                    # en-têtes de RÉPONSE liés aux quotas (jamais ceux de la requête)
                    "entetes_quota": {k: v for k, v in r.headers.items()
                                      if any(m in k.lower() for m in ("limit", "quota", "retry"))},
                    "entetes_reponse": sorted(r.headers.keys()),
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


def cle_prim() -> str:
    """Lit la clé PRIM dans l'environnement. Elle n'est jamais affichée ni écrite."""
    cle = os.environ.get("PRIM_API_KEY", "").strip()
    if not cle:
        raise RuntimeError("PRIM_API_KEY est vide : définir la variable d'environnement (jamais dans le code).")
    return cle


def collecter_prim(polls: int = 1, interval: int = 120) -> None:
    """Messages Info Trafic PRIM, requête globale (toutes les perturbations en cours et à venir).

    Authentification par l'en-tête HTTP `apiKey`. L'API ne fournit pas d'historique :
    chaque appel est un instantané à archiver en Bronze.
    """
    print("[F] PRIM — Messages Info Trafic (requête globale)")
    cle = cle_prim()
    for i in range(polls):
        contenu, meta = telecharger(URLS["prim_disruptions"], headers={"apiKey": cle})
        try:
            d = json.loads(contenu)
            meta["nb_disruptions"] = len(d.get("disruptions", []))
            meta["nb_lignes"] = len(d.get("lines", []))
            meta["last_updated_date"] = d.get("lastUpdatedDate")
        except ValueError:
            meta["json_invalide"] = True
        meta["authentification"] = "en-tête HTTP apiKey (valeur non enregistrée)"
        if cle in json.dumps(meta):  # garde-fou : la clé ne doit jamais finir sur disque
            raise RuntimeError("La clé PRIM apparaît dans les métadonnées : écriture annulée.")
        sauver("prim", f"disruptions_v2_{horodatage()}.json", contenu, meta)
        if i < polls - 1:
            time.sleep(interval)


def collecter_idfm() -> None:
    """Référentiel IDFM « Arrêts et lignes associées » (CSV `;`, UTF-8, licence ODbL), plafonné à 50 Mo."""
    print("[G] IDFM — Arrêts et lignes associées")
    contenu, meta = telecharger(URLS["idfm_arrets_lignes"], params={"delimiter": ";"},
                                taille_max=50 * 1024 * 1024)
    meta["nb_lignes_csv"] = contenu.count(b"\n") - 1
    sauver("idfm", f"arrets_lignes_{horodatage()}.csv", contenu, meta)


# --------------------------------------------------------------------------- historiques

def _ecrire_meta(chemin: Path, meta: dict) -> None:
    contenu = chemin.read_bytes()
    meta = {**meta, "fichier": chemin.name, "taille_octets": len(contenu),
            "sha256": hashlib.sha256(contenu).hexdigest(), "telecharge_utc": horodatage()}
    chemin.with_name(chemin.name + ".meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"  -> {chemin} ({len(contenu):,} o)")


def charger_historique_velib(date_debut: dt.date, date_fin: dt.date, dossier: Path,
                             taille_max: int = 300 * 1024 * 1024, zip_existant: Path | None = None) -> Path:
    """Historique Vélib' communautaire (lovasoa/historique-velib-opendata).

    Le dépôt ne publie qu'un seul zip (un CSV sans en-tête ni identifiant de station :
    date UTC, capacity, available_mechanical, available_electrical, station_name,
    station_geo, operative). Mesuré le 05/10/2026 : 236 Mo, données du 26/11/2020 au
    09/04/2021 seulement. La fonction télécharge le zip une fois (après un HEAD qui
    vérifie la taille), puis extrait en streaming les lignes de [date_debut, date_fin]
    vers un CSV gzip avec en-tête. Passer `zip_existant` pour ne pas re-télécharger
    les 236 Mo quand le zip est déjà présent ailleurs.
    """
    print(f"[H1] Historique Vélib' {date_debut} -> {date_fin}")
    dossier.mkdir(parents=True, exist_ok=True)
    url = URLS["hist_velib_zip"]
    zip_local = zip_existant or dossier / "stations.zip"
    if zip_existant and not zip_existant.exists():
        raise FileNotFoundError(zip_existant)
    taille = int(requests.head(url, allow_redirects=True, timeout=60).headers.get("Content-Length", 0))
    if taille > taille_max:
        raise RuntimeError(f"stations.zip fait {taille:,} o > limite {taille_max:,} o")
    if not zip_local.exists() or zip_local.stat().st_size != taille:
        with requests.get(url, stream=True, timeout=600, headers={"User-Agent": USER_AGENT}) as r:
            r.raise_for_status()
            with open(zip_local, "wb") as out:
                for bloc in r.iter_content(1024 * 1024):
                    out.write(bloc)
        _ecrire_meta(zip_local, {"url": url, "http_status": 200, "taille_annoncee_head": taille})
    sortie = dossier / f"velib_historique_{date_debut:%Y%m%d}_{date_fin:%Y%m%d}.csv.gz"
    deb, fin = date_debut.isoformat(), (date_fin + dt.timedelta(days=1)).isoformat()
    n, premiere, derniere = 0, None, None
    with zipfile.ZipFile(zip_local) as z, z.open(z.infolist()[0]) as brut, \
            gzip.open(sortie, "wt", encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        w.writerow(["date_utc", "capacity", "available_mechanical", "available_electrical",
                    "station_name", "station_geo", "operative"])
        for ligne in csv.reader(io.TextIOWrapper(brut, encoding="utf-8", newline="")):
            if deb <= ligne[0] < fin:  # dates ISO « AAAA-MM-JJTHH:MMZ » : comparaison lexicale correcte
                w.writerow(ligne); n += 1
                premiere = premiere or ligne[0]; derniere = ligne[0]
    if n == 0:
        print("  ! aucune ligne : l'historique ne couvre que 2020-11-26 -> 2021-04-09")
    _ecrire_meta(sortie, {"url": url, "extrait_de": zip_local.name, "periode_demandee": [str(date_debut), str(date_fin)],
                          "nb_lignes": n, "premiere_date": premiere, "derniere_date": derniere})
    return sortie


def _git(depot: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(depot), *args], check=True, capture_output=True, text=True).stdout


def charger_historique_ratpstatus(date_debut: dt.date, date_fin: dt.date, dossier: Path,
                                  cache_git: Path | None = None) -> list[Path]:
    """Historique RATPstatus (wincelau/ratpstatus) : un instantané PRIM toutes les 2 min.

    Pas de clone complet (le dépôt a des centaines de milliers de fichiers) : clone
    superficiel sans arbres ni blobs (--depth 1 --filter=tree:0), puis checkout
    partiel d'un dossier jour à la fois. Mesuré : ~0,6 Mo transférés par jour grâce
    aux deltas git, pour ~37 Mo de JSON. Un « jour » va de 03:00 à 02:58 le lendemain
    (720 fichiers attendus). Chaque jour est archivé en AAAAMMJJ.tar.xz + .meta.json.
    """
    print(f"[H2] Historique RATPstatus {date_debut} -> {date_fin}")
    dossier.mkdir(parents=True, exist_ok=True)
    depot = cache_git or Path.home() / ".cache" / "ratpstatus_git"
    if not (depot / ".git").exists():
        depot.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "clone", "-q", "--depth", "1", "--filter=tree:0", "--no-checkout",
                        URLS["hist_ratpstatus_git"], str(depot)], check=True)
        _git(depot, "sparse-checkout", "init", "--no-cone")
    commit = _git(depot, "rev-parse", "HEAD").strip()
    sorties, jour = [], date_debut
    while jour <= date_fin:
        j = f"{jour:%Y%m%d}"
        try:
            noms = _git(depot, "ls-tree", "--name-only", f"HEAD:datas/json/{j}").split()
        except subprocess.CalledProcessError:
            noms = []
        if not noms:
            print(f"  ! {j} absent du dépôt")
        else:
            _git(depot, "sparse-checkout", "set", "--no-cone", f"/datas/json/{j}/")
            _git(depot, "checkout", "-q", "HEAD")
            src = depot / "datas" / "json" / j
            archive = dossier / f"ratpstatus_{j}.tar.xz"
            with tarfile.open(archive, "w:xz") as tar:
                for nom in sorted(noms):
                    tar.add(src / nom, arcname=f"{j}/{nom}")
            heures = sorted(dt.datetime.strptime(n[:14], "%Y%m%d%H%M%S") for n in noms)
            ecarts = [(b - a).total_seconds() / 60 for a, b in zip(heures, heures[1:])]
            _ecrire_meta(archive, {
                "url": URLS["hist_ratpstatus_raw"].format(jour=j, fichier="<AAAAMMJJHHMMSS>_disruptions.optimized.json"),
                "depot_git": URLS["hist_ratpstatus_git"], "commit": commit,
                "nb_fichiers": len(noms), "nb_attendus_2min": 720,
                "premier": heures[0].isoformat(), "dernier": heures[-1].isoformat(),
                "ecart_median_min": statistics.median(ecarts) if ecarts else None,
                "trous_sup_1h": sum(1 for e in ecarts if e > 60),
                "taille_json_brute_octets": sum((src / n).stat().st_size for n in noms),
            })
            sorties.append(archive)
        jour += dt.timedelta(days=1)
    return sorties


# --------------------------------------------------------------------------- CLI

def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("sources", nargs="+", choices=["all", "velib", "meteo", "carburants", "dvf", "dpe", "prim", "idfm",
                            "hist-velib", "hist-ratpstatus"])
    p.add_argument("--polls", type=int, default=3, help="nombre d'appels Vélib' / PRIM (défaut 3)")
    p.add_argument("--interval", type=int, default=None,
                   help="secondes entre deux appels (défaut : 60 pour Vélib', 120 pour PRIM)")
    p.add_argument("--departement", default="75")
    p.add_argument("--annee", type=int, default=2025)
    p.add_argument("--size", type=int, default=100, help="lignes DPE (max 10000)")
    p.add_argument("--code-postal", default=None, help="filtre DPE optionnel, ex. 75011")
    p.add_argument("--debut", type=dt.date.fromisoformat, help="historiques : date de début (AAAA-MM-JJ)")
    p.add_argument("--fin", type=dt.date.fromisoformat, help="historiques : date de fin incluse (AAAA-MM-JJ)")
    a = p.parse_args()

    sources = {"velib", "meteo", "carburants", "dvf", "dpe", "idfm"} if "all" in a.sources else set(a.sources)
    taches = [
        ("meteo", lambda: collecter_meteo()),
        ("carburants", collecter_carburants),
        ("dvf", lambda: collecter_dvf(a.departement, a.annee)),
        ("dpe", lambda: collecter_dpe(a.size, a.code_postal)),
        ("idfm", collecter_idfm),
        ("velib", lambda: collecter_velib(a.polls, a.interval or 60)),  # longue : en fin de liste
        ("prim", lambda: collecter_prim(a.polls, a.interval or 120)),  # clé requise : hors "all"
        # chargements historiques : jamais dans "all", période obligatoire
        ("hist-velib", lambda: charger_historique_velib(a.debut, a.fin, RACINE / "historiques" / "velib")),
        ("hist-ratpstatus", lambda: charger_historique_ratpstatus(a.debut, a.fin, RACINE / "historiques" / "ratpstatus")),
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
