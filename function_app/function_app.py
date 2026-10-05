"""Function App de collecte Bronze — projet datalake Vélib' × météo × pannes (M2 Data).

- collecte_5min        : Vélib' station_status + PRIM perturbations, toutes les 5 min (UTC).
- collecte_quotidienne : station_information, météo (archive Open-Meteo) et compteurs vélo, à 03:30 UTC.

Aucun secret dans ce code : la clé PRIM est lue dans l'app setting PRIM_API_KEY,
le stockage est accédé par identité managée (rôle Storage Blob Data Contributor).
"""

import datetime as dt
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from zoneinfo import ZoneInfo

import azure.functions as func

import collecte as c

app = func.FunctionApp()
PARIS = ZoneInfo("Europe/Paris")


@app.timer_trigger(schedule="0 */5 * * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def collecte_5min(timer: func.TimerRequest) -> None:
    maintenant = dt.datetime.now(dt.timezone.utc)
    ts = c.horodatage(maintenant)
    cle = os.environ.get("PRIM_API_KEY", "").strip()

    def velib():
        return c.collecter("velib_station_status", c.prefixe_date("velib/status", maintenant, heure=True),
                           f"status_{ts}", c.URLS["velib_status"], c.compter_gbfs)

    def prim():
        prefixe = c.prefixe_date("prim/disruptions", maintenant, heure=True)
        if not cle:  # trou tracé sans appel : la clé n'est pas encore configurée
            return _echec_sans_cle(prefixe, ts)
        return c.collecter("prim_disruptions", prefixe, f"disruptions_{ts}", c.URLS["prim_disruptions"],
                           c.compter_prim, headers={"apiKey": cle}, secret=cle)

    # Appels indépendants : l'échec de l'un n'empêche pas l'écriture de l'autre.
    with ThreadPoolExecutor(max_workers=2) as pool:
        resultats = [f.result() for f in (pool.submit(velib), pool.submit(prim))]
    if timer.past_due:
        logging.warning("collecte_5min en retard sur son horaire")
    # Journalisé ici (thread principal) : les logs écrits depuis les threads du pool
    # perdent le contexte d'invocation et ne remontent pas dans Application Insights.
    for r in resultats:
        logging.info("%s : statut=%s http=%s enregistrements=%s erreur=%s", r.get("source"), r.get("statut"),
                     r.get("http_status"), r.get("nb_enregistrements"), r.get("erreur"))


def _echec_sans_cle(prefixe: str, ts: str) -> dict:
    import json
    manifeste = {"source": "prim_disruptions", "url": c.URLS["prim_disruptions"],
                 "heure_collecte_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                 "statut": "echec", "erreur": "PRIM_API_KEY absente des app settings"}
    try:
        c.ecrire(f"{prefixe}/disruptions_{ts}.manifest.json",
                 json.dumps(manifeste, ensure_ascii=False, indent=2).encode(), "application/json")
    except Exception as e:
        logging.error("manifeste PRIM impossible : %s", type(e).__name__)
    logging.warning("prim_disruptions : statut=echec (PRIM_API_KEY absente)")
    return manifeste


@app.timer_trigger(schedule="0 30 3 * * *", arg_name="timer", run_on_startup=False, use_monitor=True)
def collecte_quotidienne(timer: func.TimerRequest) -> None:
    executer_quotidienne(dt.datetime.now(dt.timezone.utc))


def executer_quotidienne(maintenant: dt.datetime) -> list[dict]:
    ts = c.horodatage(maintenant)
    aujourd_hui = maintenant.date()
    veille = aujourd_hui - dt.timedelta(days=1)
    resultats = []

    # 1. Vélib' station_information (référentiel du jour)
    resultats.append(c.collecter("velib_station_information", c.prefixe_date("velib/info", maintenant),
                                 f"station_information_{ts}", c.URLS["velib_info"], c.compter_gbfs))

    # 2. Météo : veille (J-1) + rattrapage J-6, l'archive ERA5 étant consolidée avec ~5 jours de retard
    for jour, nature in ((veille, "j-1"), (aujourd_hui - dt.timedelta(days=6), "j-6_consolidee")):
        quand = dt.datetime(jour.year, jour.month, jour.day, tzinfo=dt.timezone.utc)
        resultats.append(c.collecter(
            "meteo_archive", c.prefixe_date("meteo", quand), f"meteo_{jour:%Y%m%d}_{nature}",
            c.URLS["meteo_archive"], c.compter_meteo,
            params={"latitude": 48.85, "longitude": 2.35, "start_date": jour.isoformat(), "end_date": jour.isoformat(),
                    "hourly": "temperature_2m,precipitation", "timezone": "UTC"},
            extra={"jour_meteo": jour.isoformat(), "nature": nature}))

    # 3. Compteurs vélo : journée de Paris J-2 (mesuré : le portail publie J-1 vers 11:00 UTC,
    #    donc à 03:30 UTC la dernière journée complète est J-2). Bornes converties en UTC.
    jour_cpt = aujourd_hui - dt.timedelta(days=2)
    debut = dt.datetime(jour_cpt.year, jour_cpt.month, jour_cpt.day, tzinfo=PARIS).astimezone(dt.timezone.utc)
    fin = (dt.datetime(jour_cpt.year, jour_cpt.month, jour_cpt.day, tzinfo=PARIS) + dt.timedelta(days=1)).astimezone(dt.timezone.utc)
    quand = dt.datetime(jour_cpt.year, jour_cpt.month, jour_cpt.day, tzinfo=dt.timezone.utc)
    resultats.append(c.collecter(
        "compteurs_velo_paris", c.prefixe_date("compteurs", quand), f"comptages_{jour_cpt:%Y%m%d}",
        c.URLS["compteurs"], c.compter_parquet, extension="parquet",
        params={"where": f'date >= "{debut:%Y-%m-%dT%H:%M:%S}Z" and date < "{fin:%Y-%m-%dT%H:%M:%S}Z"'},
        compresser=False, extra={"jour_paris": jour_cpt.isoformat(), "licence": "ODbL (Ville de Paris)"}))

    for r in resultats:
        logging.info("%s : statut=%s http=%s enregistrements=%s fichier=%s erreur=%s", r.get("source"), r.get("statut"),
                     r.get("http_status"), r.get("nb_enregistrements"), r.get("fichier"), r.get("erreur"))
    return resultats
