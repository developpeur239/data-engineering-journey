# Inventaire de la zone Bronze

Compte `stdlvelibv8gywf` (ADLS Gen2, Switzerland North), conteneur `bronze`.
Inventaire fait le **mardi 6 octobre 2026 entre 10:44 et 11:10 UTC**, avec `az storage … --auth-mode login` (identité Entra, aucune clé de compte).

- **[mesuré]** : calculé sur le contenu réel de Bronze ou sur les fichiers téléchargés.
- **Règles respectées :** aucun fichier supprimé ni écrasé (comparaison avant/après : 0 fichier disparu, 0 taille modifiée), aucune ressource Azure créée, aucun secret écrit.
- **Téléchargé pour cette tâche :** ≈ **87 Mo** (référentiel IDFM 13,9 Mo, RATPstatus juillet-août ≈ 72,6 Mo via git partiel, météo < 0,1 Mo) sur 500 Mo.

**Bronze avant : 1 176 fichiers, 174,3 Mo. Après : 1 328 fichiers, 224,5 Mo** (+132 ajoutés par moi, +20 collectes automatiques survenues pendant le travail).

---

## 1. Tableau récapitulatif

| Source | Dossier Bronze | Données | Manifestes | Taille | Période couverte | Trous | Statut |
|---|---|---|---|---|---|---|---|
| Vélib' `station_status` | `velib/status/` | 264 | 264 `.manifest` | 9,2 Mo | 05/10 13:10 → 06/10 11:05 UTC | **0** (264/264 créneaux de 5 min) | **OK** |
| Vélib' `station_information` | `velib/info/` | 2 | 2 | 0,1 Mo | 05/10 et 06/10 | 0 | **OK** |
| PRIM perturbations | `prim/disruptions/` | 256 | 264 | 59,2 Mo | 05/10 13:10 → 06/10 11:05 UTC | **8 créneaux** (13:10 → 13:45 le 05/10) : manifestes `echec`, irrécupérables | **OK avec trous connus** |
| Météo Open-Meteo | `meteo/` | 7 | 7 | < 0,1 Mo | 29/09 00:00 → 05/10 23:00 UTC (168 h) | **0** après complément (72 h manquaient) | **complété** |
| Compteurs vélo, historique | `compteurs/historique/` | 15 | 15 `.meta` | 18,9 Mo | 03/09/2025 → 03/10/2026 | 0 | **OK** |
| Compteurs vélo, quotidien | `compteurs/date=…/` | 2 | 2 | 0,1 Mo | 03/10 et 04/10/2026 | 0 | **OK** |
| RATPstatus | `ratpstatus/` | 110 jours | 62 `.manifest` + 48 `.meta` | 54,5 Mo | 02→16/12/2025, 01/07→30/09/2026, + 3 jours isolés | 0 sur les périodes demandées | **complété** (juillet-août ajoutés) |
| Kaggle Vélib' | `kaggle/velib-data/v13/` | 3 | 3 `.meta` | 68,6 Mo | 02/12 → 16/12/2025 | 5 créneaux de 5 min (04:00 UTC) | **OK** |
| Référentiel IDFM | `idfm/arrets_lignes/` | 1 | 1 | 13,9 Mo | extraction du 06/10/2026 | – | **ajouté** (il manquait) |

---

## 2. Contrôles détaillés

### 2.1 `velib/status` : un fichier toutes les 5 min depuis le 05/10 13:10 UTC

- **264 créneaux présents sur 264 attendus** (05/10 : 130, 06/10 : 134), jusqu'à 11:05 UTC.
- **Aucun créneau manquant**, y compris pendant les trois redéploiements et les redémarrages de la Function App.
- 264 manifestes, tous `statut = ok`.

### 2.2 `velib/info`

- `date=2026-10-05/station_information_20261005T135414Z.json.gz` (déclenchement manuel du 05/10 à 13:54 UTC) ;
- `date=2026-10-06/station_information_20261006T033000Z.json.gz` (premier déclenchement planifié).
- Une partition par jour depuis le 05/10 : OK.

### 2.3 `prim/disruptions` : toutes les 5 min depuis 13:35

- **256 fichiers de données sur 264 créneaux** depuis 13:10, soit **8 trous**, tous le 05/10.
- 8 manifestes `echec` (aucun fichier de données associé), de 13:10 à 13:45 UTC :
  - **13:10 → 13:30 (5 créneaux)** : « `PRIM_API_KEY` absente des app settings » ;
  - **13:35 → 13:45 (3 créneaux)** : HTTP 401 « Unauthorized » (valeur invalide).
- **Les échecs ne se limitent donc pas à 13:35–13:45** : les 5 premiers créneaux (13:10–13:30) sont aussi manquants, car la clé n'était pas encore configurée.
- Depuis 13:50 : **256 créneaux consécutifs sans trou**, tous `ok`.

### 2.4 `meteo` : contrôle du contenu, pas des noms de dossiers

Les 7 fichiers ont été téléchargés depuis Bronze et lus :

| Partition | Fichier | Nature | Heures | Nulls |
|---|---|---|---|---|
| 2026-09-29 | `meteo_20260929_j-6_consolidee` | J-6 consolidé | 24 | 0 |
| 2026-09-30 | `meteo_20260930_j-6_consolidee` | J-6 consolidé | 24 | 0 |
| 2026-10-01 | `meteo_20261001_rattrapage` | **ajouté** | 24 | 0 |
| 2026-10-02 | `meteo_20261002_rattrapage` | **ajouté** | 24 | 0 |
| 2026-10-03 | `meteo_20261003_rattrapage` | **ajouté** | 24 | 0 |
| 2026-10-04 | `meteo_20261004_j-1` | J-1 provisoire | 24 | 0 |
| 2026-10-05 | `meteo_20261005_j-1` | J-1 provisoire | 24 | 0 |

- **168 heures distinctes, du 29/09 00:00 au 05/10 23:00 UTC, 0 heure manquante, 0 valeur nulle.** L'exigence « du 05/10 00:00 UTC à la veille d'aujourd'hui » est remplie.
- **Avant mon ajout**, 72 heures manquaient : 1er, 2 et 3 octobre. Elles se trouvaient entre les fichiers J-6 (29-30/09), arrivés par le test manuel, et le J-1 du 04/10.
- **Piège pour Silver :** les fichiers J-1 sont **provisoires**. La Function App recharge chaque jour la journée J-6, version consolidée. Pour un même jour, plusieurs fichiers de natures différentes peuvent donc coexister à terme. Conserver la version `j-6_consolidee` si elle existe, sinon `rattrapage`, sinon `j-1`.
- Précipitations : cumul de l'heure précédente (convention Open-Meteo). Heures en UTC.

### 2.5 `compteurs` : le dossier existe, il s'appelle `compteurs/`

Chemin complet : `abfss://bronze@stdlvelibv8gywf.dfs.core.windows.net/compteurs/`. Il contient **deux sous-arborescences différentes** :

| Sous-chemin | Contenu |
|---|---|
| `compteurs/historique/mois=2025-09/` … `mois=2026-10/` | 14 Parquet mensuels (1,3 à 1,5 Mo ; octobre 0,19 Mo, jours 1 à 3 seulement) + `.meta.json` |
| `compteurs/historique/liste/` | `compteurs_liste_20261005.csv.gz` (113 compteurs, coordonnées) |
| `compteurs/date=2026-10-03/`, `date=2026-10-04/` | 1 Parquet par jour + `.manifest.json` (collecte automatique, **jour de Paris J-2**) |

**Hypothèse sur l'absence dans votre listing Databricks :** je n'ai pas accès à Databricks. Le dossier racine mélange deux schémas de partition (`historique/mois=…` et `date=…`), ce qui peut gêner la découverte automatique de partitions. Lisez-les par deux chemins séparés : `compteurs/historique/mois=*/` et `compteurs/date=*/`.

**Chevauchement à dédoublonner dans Silver :** le fichier `mois=2026-10` (jours 1 à 3, bornes en journée UTC) et `date=2026-10-03` (jour de Paris, de 22:00 UTC la veille à 22:00 UTC) se recoupent le 03/10. Dédoublonner sur (`id_compteur`, `date`). Au 06/10, la série est continue du 03/09/2025 au 04/10/2026.

### 2.6 `ratpstatus`

- **110 jours** présents, un fichier `ratpstatus_AAAAMMJJ.tar.xz` de 720 instantanés chacun.

| Période | Jours | Statut |
|---|---|---|
| 02/12/2025 → 16/12/2025 (période Kaggle) | **15 / 15** | déjà présent |
| 01/07/2026 → 31/08/2026 | **62 / 62** | **ajouté** (44 640 instantanés, 3,58 Go de JSON brut) |
| 01/09/2026 → 30/09/2026 | **30 / 30** | déjà présent |
| Isolés | 03/06/2024, 15/01/2025, 01/10/2026 | déjà présents |

- **Contrôle des 62 jours ajoutés :** 720 fichiers dans chaque archive, écart médian de 2 min, aucun trou de plus d'1 h, sha256 de chaque archive vérifié.
- **Non chargés :** du 02/10 au 05/10/2026. La collecte directe PRIM couvre à partir du 05/10 13:35, d'où une **plage 02-04/10 sans données de pannes**, car ce n'était pas demandé. Un chargement sur 3 jours coûterait environ 3 à 4 Mo.

### 2.7 `kaggle/velib-data/v13`

`velib-data_v13.zip` (13,4 Mo), `velib_concat.parquet` (55,1 Mo, 6 353 181 lignes) et `meteo_archive_20251202_20251216.json` (10,5 Ko), avec leurs `.meta.json`.

---

## 3. Ce qui a été ajouté

| Ajout | Fichiers | Taille | Source |
|---|---|---|---|
| `idfm/arrets_lignes/date=2026-10-06/arrets_lignes.csv` + manifeste | 2 | 13,9 Mo | export CSV `data.iledefrance-mobilites.fr` |
| `meteo/date=2026-10-01…03/meteo_…_rattrapage.json.gz` + 3 manifestes | 6 | ≈ 4 Ko | archive Open-Meteo (appel direct, HTTP 200) |
| `ratpstatus/date=2026-07-01…2026-08-31/ratpstatus_….tar.xz` + 62 manifestes | 124 | 34 Mo | `wincelau/ratpstatus`, git partiel |

**Manifestes ajoutés :** même schéma que les manifestes existants de la Function App, produits par le même code (`collecte.py`), plus `taille_octets` et `sha256` (valeurs du fichier stocké). Exemple, référentiel IDFM :

```json
{"source": "idfm_arrets_lignes", "url": "https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets-lignes/exports/csv",
 "statut": "ok", "heure_collecte_utc": "2026-10-06T10:48:13.600023+00:00", "http_status": 200,
 "taille_octets": 13887797, "sha256": "2c780f8513c7090d0fc7abc01e437c3f616fda7d03eb5306faefe982668f96ee",
 "nb_enregistrements": 74547, "nb_arrets_distincts": 35533, "nb_lignes_transport_distinctes": 2025,
 "encodage": "utf-8 avec BOM", "separateur": ";"}
```

Pour RATPstatus, `http_status` vaut `null` (récupération par git, pas par HTTP). Le champ `methode` et le `commit_git` l'indiquent.

**Hash du référentiel vérifié :** après envoi, le fichier relu dans Bronze a le même sha256 et la même taille (13 887 797 octets) que son manifeste.

---

## 4. Référentiel IDFM `arrets_lignes` : ce qu'il faut savoir pour Silver

- **URL d'export (vérifiée, HTTP 200) :** `https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets-lignes/exports/csv?delimiter=%3B`
- **Format :** CSV, séparateur **`;`**, encodage **UTF-8 avec BOM** (`EF BB BF`), fins de ligne **CRLF**, 13 colonnes.
- **Contenu :** **74 547 lignes** (une par couple arrêt × ligne), **35 533 arrêts** distincts, **2 025 lignes**, coordonnées présentes sur 100 % des lignes. La veille : 74 549 / 35 536 / 2 026. Le jeu évolue chaque jour.
- **Modes :** Bus 72 478, Metro 803, Tramway 564, LocalTrain 263, RapidTransit 254, regionalRail 155, RailShuttle 16, CableWay 10, Funicular 4.
- **Colonne vide :** `bookingrules` (71 550 lignes vides sur 74 547).

En-tête et 3 premières lignes, tels que dans le fichier :

```
id;route_long_name;stop_id;stop_name;stop_lon;stop_lat;operatorname;shortname;bookingrules;mode;pointgeo;nom_commune;code_insee
IDFM:C01389;T1;IDFM:22259;Jean Rostand;2.454386644826771;48.90784693451178;RATP;T1;;Tramway;48.90784693451178, 2.454386644826771;Bobigny;93008
IDFM:C01389;T1;IDFM:24425;Hôtel de Ville de Bobigny;2.4438136690531236;48.906566265422576;RATP;T1;;Tramway;48.906566265422576, 2.4438136690531236;Bobigny;93008
IDFM:C01389;T1;IDFM:22629;La Courneuve - 8 Mai 1945;2.4106374774533097;48.920859363612415;RATP;T1;;Tramway;48.920859363612415, 2.4106374774533097;La Courneuve;93027
```

**Points d'attention pour le nettoyage :**
1. **BOM** : la première colonne risque de s'appeler `﻿id`. En pandas, `encoding="utf-8-sig"`. Avec Spark, je n'ai **pas testé** : vérifier le nom de la première colonne après lecture.
2. **`stop_lat` et `stop_lon` sont du texte**, avec point décimal et une quinzaine de décimales : à convertir en `double`.
3. **`pointgeo`** est « `lat, lon` » (virgule + espace, non guillemeté) : redondant avec `stop_lat`/`stop_lon`, à ignorer.
4. **Jointure avec PRIM / RATPstatus** : retirer les préfixes `line:` (PRIM `line:IDFM:C01389` ↔ `id` = `IDFM:C01389`) et `stop_point:` (PRIM `stop_point:IDFM:22259` ↔ `stop_id` = `IDFM:22259`). Mesuré sur échantillons : 100 % de correspondance après retrait.
5. **Un arrêt apparaît une fois par ligne qui le dessert** : pour un rattachement par distance, dédoublonner d'abord les arrêts.
6. **Plusieurs extractions** : prendre la partition la plus récente (`date=…`) ou conserver l'historique pour suivre les évolutions du réseau.

---

## 5. Collecte automatique : référentiel hebdomadaire

La fonction `collecte_quotidienne` télécharge maintenant **le lundi (date UTC)** le référentiel vers `idfm/arrets_lignes/date=<lundi>/arrets_lignes.csv` + `arrets_lignes.manifest.json`, au même format. Les autres collectes ne sont pas modifiées.

| Test | Résultat |
|---|---|
| Local, lundi 12/10 (stockage factice, appels réels pour le référentiel) | 5 sources appelées dans l'ordre habituel + `idfm_arrets_lignes` ; fichier + manifeste écrits ; 74 547 lignes |
| Local, mardi 13/10 | les 4 collectes d'avant, **aucun** référentiel |
| Local, partition déjà présente | statut `deja_present`, **rien n'est écrit**, fichier existant intact |
| Local, limite de taille (1 Mo) | statut `echec`, **aucun fichier tronqué** n'est écrit |
| Déployé, déclenchement manuel (06/10 11:07 UTC) | exécution réussie en 1,5 s ; 74 547 lignes téléchargées ; partition du jour déjà présente : **`deja_present`, rien écrit** |

**Ce que le test cloud n'a pas prouvé :** une première **écriture** du référentiel par la fonction dans Azure. Le référentiel du 06/10 existait déjà (déposé par mes soins) et je n'avais pas le droit de l'écraser. Cette écriture sera vérifiée **lundi 12/10 à 03:30 UTC** :

```bash
az storage fs file list --account-name stdlvelibv8gywf --auth-mode login -f bronze --path idfm/arrets_lignes --recursive true --query "[].name" -o tsv
```

On doit y voir `date=2026-10-12/arrets_lignes.csv` et son manifeste.

Pour le test manuel, un paramètre temporaire `REFERENTIEL_SEUL=1` limitait l'exécution au référentiel (sans réécrire météo ni compteurs). **Il a été retiré** ; la liste des paramètres de l'application a été vérifiée ensuite.

---

## 6. Ce qui n'a pas pu être fait ou reste imparfait

| Point | Raison |
|---|---|
| PRIM du 05/10 13:10 → 13:45 (8 créneaux) | l'API PRIM ne conserve aucun historique et RATPstatus ne commence qu'au ferré, sans ces instants à 5 min |
| Compteurs avant le 03/09/2025 | hors des 13 mois glissants du portail |
| Pannes du 02 au 04/10/2026 | non demandées ; chargeables à la demande |
| Écriture cloud du référentiel | non démontrée (voir §5) |
| Format des manifestes | **hétérogène** : voir ci-dessous |

**Manifestes hétérogènes.** Les chargements historiques faits avec `collecte_test.py` ont un **`.meta.json`** (champs `url`, `http_status`, `taille_octets`, `sha256`, `telecharge_utc`…) : 15 compteurs, 3 Kaggle, 48 RATPstatus. Les collectes de la Function App et les ajouts de ce jour ont un **`.manifest.json`** (schéma plus riche, `statut`, `heure_collecte_utc`…). Je n'ai pas ajouté de `.manifest.json` à côté des anciens fichiers : cela n'était pas demandé et aurait multiplié les écritures. En Silver, lire les deux motifs `*.manifest.json` et `*.meta.json`, ou me demander de générer les manifestes manquants.

---

## 7. Résumé pour Silver

- **Prêt à lire :** `velib/status`, `velib/info`, `prim/disruptions` (ignorer les 8 `echec`), `meteo` (168 h continues), `compteurs` (continu du 03/09/2025 au 04/10/2026), `ratpstatus` (décembre 2025 et juillet à septembre 2026), `kaggle`, `idfm`.
- **À dédoublonner :** compteurs le 03/10 ; météo selon la nature (J-1 provisoire contre J-6 consolidé).
