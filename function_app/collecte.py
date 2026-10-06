"""Logique de collecte partagée par les fonctions Azure (reprise de collecte_test.py).

Règles :
- 3 nouvelles tentatives (attente 2, 4, 8 s) sur erreur réseau, 429 et 5xx ; aucune sur les autres 4xx ;
- chaque fichier brut est écrit en gzip dans Bronze, avec un .manifest.json à côté ;
- en cas d'échec définitif, un manifeste "statut": "echec" garde la trace du trou ;
- aucun en-tête HTTP ni aucune variable d'environnement n'est journalisé ou écrit.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import logging
import os
import time
from dataclasses import dataclass, field

import requests
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContentSettings

# Les journaux HTTP du SDK Azure listent les en-têtes : on les coupe.
for _nom in ("azure", "azure.core.pipeline.policies.http_logging_policy", "urllib3"):
    logging.getLogger(_nom).setLevel(logging.WARNING)

log = logging.getLogger("collecte")
USER_AGENT = "datalake-m2-collecte/1.0 (projet pedagogique)"
TAILLE_MAX = 20 * 1024 * 1024
ESSAIS_SUPPLEMENTAIRES = 3

URLS = {
    "velib_status": "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_status.json",
    "velib_info": "https://velib-metropole-opendata.smovengo.cloud/opendata/Velib_Metropole/station_information.json",
    "prim_disruptions": "https://prim.iledefrance-mobilites.fr/marketplace/disruptions_bulk/disruptions/v2",
    "meteo_archive": "https://archive-api.open-meteo.com/v1/archive",
    "compteurs": "https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-donnees-compteurs/exports/parquet",
    "idfm_arrets_lignes": "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets-lignes/exports/csv",
}


class ErreurDefinitive(Exception):
    """Erreur qu'il est inutile de retenter (4xx hors 429, quota journalier, clé absente...)."""


@dataclass
class Reponse:
    contenu: bytes
    http_status: int
    temps_reponse_s: float
    essais: int
    content_type: str | None = None
    entetes_quota: dict = field(default_factory=dict)


def telecharger(url: str, params: dict | None = None, headers: dict | None = None,
                taille_max: int | None = None) -> Reponse:
    """GET avec retries (même logique que collecte_test.telecharger).

    Sans `taille_max`, la réponse est tronquée à TAILLE_MAX (comportement historique).
    Avec `taille_max`, une réponse plus grande est une erreur : on n'écrit jamais un fichier tronqué.
    """
    derniere = None
    for essai in range(1, ESSAIS_SUPPLEMENTAIRES + 2):
        debut = time.monotonic()
        try:
            r = requests.get(url, params=params, timeout=60,
                             headers={"User-Agent": USER_AGENT, **(headers or {})})
            if r.status_code == 429 and "Daily API request limit" in r.text[:500]:
                raise ErreurDefinitive("HTTP 429 : quota journalier épuisé")
            if r.status_code == 429 or r.status_code >= 500:
                raise requests.HTTPError(f"HTTP {r.status_code}")
            if r.status_code >= 400:
                # message limité au code et au début du corps : jamais d'en-têtes
                raise ErreurDefinitive(f"HTTP {r.status_code} : {r.text[:150]}")
            if taille_max is not None and len(r.content) > taille_max:
                raise ErreurDefinitive(f"réponse de {len(r.content)} octets > limite {taille_max}")
            contenu = r.content[:TAILLE_MAX] if taille_max is None else r.content
            return Reponse(contenu, r.status_code, round(time.monotonic() - debut, 3), essai,
                           r.headers.get("Content-Type"),
                           {k: v for k, v in r.headers.items()
                            if any(m in k.lower() for m in ("ratelimit", "quota"))})
        except ErreurDefinitive:
            raise
        except requests.RequestException as e:
            derniere = e
            log.warning("essai %s/%s échoué sur %s : %s", essai, ESSAIS_SUPPLEMENTAIRES + 1,
                        url.split("?")[0], type(e).__name__)
            if essai <= ESSAIS_SUPPLEMENTAIRES:
                time.sleep(2 ** essai)
    raise RuntimeError(f"échec après {ESSAIS_SUPPLEMENTAIRES + 1} essais : {type(derniere).__name__}: {str(derniere)[:150]}")


# --------------------------------------------------------------------------- stockage

_client: BlobServiceClient | None = None


def conteneur():
    """Conteneur Bronze, authentifié par l'identité managée (aucune clé)."""
    global _client
    if _client is None:
        compte = os.environ["BRONZE_ACCOUNT"]
        _client = BlobServiceClient(f"https://{compte}.blob.core.windows.net", credential=DefaultAzureCredential())
    return _client.get_container_client(os.environ.get("BRONZE_CONTAINER", "bronze"))


def ecrire(chemin: str, donnees: bytes, type_contenu: str) -> None:
    conteneur().upload_blob(chemin, donnees, overwrite=True,
                            content_settings=ContentSettings(content_type=type_contenu))


def existe(chemin: str) -> bool:
    return conteneur().get_blob_client(chemin).exists()


def collecter(source: str, prefixe: str, nom: str, url: str, compter, params: dict | None = None,
              headers: dict | None = None, secret: str | None = None, compresser: bool = True,
              extension: str = "json.gz", extra: dict | None = None, taille_max: int | None = None,
              ecraser: bool = True, alias_standard: bool = False) -> dict:
    """Télécharge, écrit `<prefixe>/<nom>.<extension>` + `<prefixe>/<nom>.manifest.json`.

    `compter(contenu)` renvoie (nb_enregistrements, champs complémentaires).
    Ne lève jamais : renvoie le manifeste (statut "ok", "echec" ou "deja_present").
    `ecraser=False` : si le fichier existe déjà, rien n'est écrit (ni fichier ni manifeste) et le
    statut est "deja_present". `alias_standard` ajoute `taille_octets` et `sha256` (fichier stocké).
    """
    maintenant = dt.datetime.now(dt.timezone.utc)
    manifeste = {"source": source, "url": url, "params": params or {}, "heure_collecte_utc": maintenant.isoformat(),
                 **(extra or {})}
    try:
        rep = telecharger(url, params=params, headers=headers, taille_max=taille_max)
        nb, details = compter(rep.contenu)
        stocke = gzip.compress(rep.contenu, compresslevel=6) if compresser else rep.contenu
        chemin = f"{prefixe}/{nom}.{extension}"
        if not ecraser and existe(chemin):
            log.info("%s : deja_present (%s), rien n'est écrit", source, chemin)
            return {"source": source, "statut": "deja_present", "fichier": chemin, "nb_enregistrements": nb,
                    "taille_stockee_octets": len(stocke), "sha256_stocke": hashlib.sha256(stocke).hexdigest()}
        ecrire(chemin, stocke, "application/gzip" if extension.endswith("gz") else "application/octet-stream")
        manifeste.update({
            "statut": "ok", "fichier": chemin, "http_status": rep.http_status, "essais": rep.essais,
            "temps_reponse_s": rep.temps_reponse_s, "content_type": rep.content_type,
            "taille_brute_octets": len(rep.contenu), "taille_stockee_octets": len(stocke),
            "sha256_brut": hashlib.sha256(rep.contenu).hexdigest(),
            "sha256_stocke": hashlib.sha256(stocke).hexdigest(),
            "nb_enregistrements": nb, "entetes_quota": rep.entetes_quota, **details,
        })
        if alias_standard:
            manifeste.update({"taille_octets": len(stocke), "sha256": manifeste["sha256_stocke"]})
    except Exception as e:  # trace du trou : manifeste d'échec
        manifeste.update({"statut": "echec", "erreur": f"{type(e).__name__}: {str(e)[:300]}"})
    texte = json.dumps(manifeste, ensure_ascii=False, indent=2)
    if secret and secret in texte:  # garde-fou : la clé ne doit jamais être écrite
        manifeste = {k: manifeste[k] for k in ("source", "heure_collecte_utc")}
        manifeste.update({"statut": "echec", "erreur": "secret détecté dans le manifeste : contenu retiré"})
        texte = json.dumps(manifeste, ensure_ascii=False, indent=2)
    try:
        ecrire(f"{prefixe}/{nom}.manifest.json", texte.encode(), "application/json")
    except Exception as e:
        log.error("écriture du manifeste impossible pour %s : %s", source, type(e).__name__)
    log.info("%s : statut=%s http=%s enregistrements=%s fichier=%s", source, manifeste.get("statut"),
             manifeste.get("http_status"), manifeste.get("nb_enregistrements"), manifeste.get("fichier"))
    return manifeste


# --------------------------------------------------------------------------- compteurs d'enregistrements

def compter_gbfs(contenu: bytes):
    d = json.loads(contenu)
    return len(d["data"]["stations"]), {"lastUpdatedOther": d.get("lastUpdatedOther")}


def compter_prim(contenu: bytes):
    d = json.loads(contenu)
    return len(d.get("disruptions", [])), {"nb_lignes": len(d.get("lines", [])),
                                          "lastUpdatedDate": d.get("lastUpdatedDate")}


def compter_meteo(contenu: bytes):
    d = json.loads(contenu)
    h = d["hourly"]
    return len(h["time"]), {"temperatures_nulles": sum(1 for x in h["temperature_2m"] if x is None),
                            "point_grille": [d.get("latitude"), d.get("longitude")]}


def compter_csv_arrets(contenu: bytes):
    """Référentiel IDFM arrets-lignes : CSV `;`, UTF-8 avec BOM, une ligne par couple (arrêt, ligne)."""
    import csv
    import io
    lecteur = csv.DictReader(io.StringIO(contenu.decode("utf-8-sig")), delimiter=";")
    lignes = list(lecteur)
    if not lignes or "stop_id" not in lecteur.fieldnames or "id" not in lecteur.fieldnames:
        raise ValueError("CSV arrets-lignes inattendu (colonnes stop_id / id absentes)")
    return len(lignes), {"encodage": "utf-8 avec BOM", "separateur": ";", "colonnes": lecteur.fieldnames,
                         "nb_arrets_distincts": len({r["stop_id"] for r in lignes}),
                         "nb_lignes_transport_distinctes": len({r["id"] for r in lignes})}


def compter_parquet(contenu: bytes):
    if contenu[:4] != b"PAR1":
        raise ValueError("réponse non Parquet")
    return None, {"format": "parquet"}  # comptage des lignes fait en Silver (pas de pyarrow ici)


def prefixe_date(racine: str, quand: dt.datetime, heure: bool = False) -> str:
    p = f"{racine}/date={quand:%Y-%m-%d}"
    return f"{p}/heure={quand:%H}" if heure else p


def horodatage(quand: dt.datetime) -> str:
    return quand.strftime("%Y%m%dT%H%M%SZ")
