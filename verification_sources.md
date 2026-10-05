# Vérification des sources : projet datalake Azure (Bronze / Silver / Gold)

Tests faits le **lundi 5 octobre 2026, entre 08:37 et 08:49 UTC** (10:37–10:49, heure de Paris), avec `curl` et Python 3.11 / `requests`.
Tous les chiffres ci-dessous ont été **mesurés** sur les fichiers de `./echantillons/`. Quand une information vient
seulement de métadonnées (data.gouv.fr, ADEME), c'est indiqué.

> **Contexte réseau.** Les tests ont été lancés depuis un conteneur cloud dont la sortie internet passe par un proxy
> partagé. Deux problèmes (quota Open-Meteo, coupures data.gouv.fr) sont probablement liés à cette IP partagée.
> Ils sont décrits en détail plus bas, mais il faut **les re-tester depuis votre machine ou depuis Azure**.

Pour reproduire les échantillons : `python collecte_test.py all` (environ 3 min, à cause des 3 appels Vélib' espacés d'1 min).

---

## 1. Tableau récapitulatif

| Source | URL testée | Format réel | Volume mesuré | Fréquence de mise à jour | Clé API | Licence | Verdict |
|---|---|---|---|---|---|---|---|
| **A. Vélib' GBFS** | `.../Velib_Metropole/station_status.json` + `station_information.json` | JSON UTF-8 (GBFS 1.x, champs en double camelCase / snake_case) | status : 464 Ko par appel (31 Ko gzippé), 1 519 stations. info : 284 Ko | `lastUpdatedOther` avance **toutes les ~61 s** (mesuré sur 4 appels). `last_reported` est en retard d'environ 20 min | Non | ODbL d'après les jeux Ville de Paris / Région IDF sur data.gouv.fr (un 3ᵉ jeu indique Licence Ouverte : **à confirmer**) | **OK avec réserves** |
| **B. Open-Meteo** | `api.open-meteo.com/v1/forecast` et `archive-api.open-meteo.com/v1/archive` | JSON UTF-8, tableaux colonnaires (`hourly.time[]`, `hourly.temperature_2m[]`…) | ~5 Ko par semaine et par point (168 lignes horaires) | Prévision : pas horaire, `current` tous les 15 min (`interval: 900`). Archive : semaine du 21 au 27/09 disponible | Non (gratuit, **10 000 appels/jour**, usage non commercial) | Données sous CC BY 4.0 (page /en/licence vérifiée) | **OK avec réserves** |
| **C. Prix carburants** | `donnees.roulez-eco.fr/opendata/instantane` | ZIP → 1 XML **ISO-8859-1**, imbriqué (`pdv` > `prix`/`services`/`horaires`) | 941 Ko zippé → 12,1 Mo XML. **9 834 stations**, 30 201 prix | Fichier régénéré au moins une fois entre 06:50 et 08:40 UTC (`Last-Modified`). « Continue » selon data.gouv.fr. Historiques `/jour` (1,1 Mo) et `/annee/2025` (31,7 Mo) existent | Non | Licence Ouverte v2.0 (data.gouv.fr) | **OK** |
| **D. DVF géolocalisé** | `files.data.gouv.fr/geo-dvf/latest/csv/2025/departements/75.csv.gz` | CSV UTF-8 (sans BOM), virgule, gzip | Paris 2025 : 2,06 Mo gz → 16 Mo, **84 440 lignes × 40 colonnes**. National : 523 Mo gz | Semestrielle (métadonnées). Fichier du 18/05/2026, couvre 2021 → 2025 | Non | Licence Ouverte v2.0 | **OK** (en tant que source seule) |
| **E. ADEME DPE** | `data.ademe.fr/data-fair/api/v1/datasets/dpe03existant/lines?size=100` | API JSON ou CSV (`format=csv`) **UTF-8 avec BOM** | **15 705 770 lignes**, 226 colonnes en CSV. 100 lignes = 205 Ko. Paris : 849 678 DPE | `dataUpdatedAt` = 01/10/2026. DPE le plus récent : 28/09/2026 | Non (lecture publique) | Licence Ouverte v2.0 | **OK avec réserves** |
| **A+B croisement** | voir §3 | – | – | – | – | – | **OK** (jointure testée : 1 519/1 519) |
| **D+E croisement** | voir §4 | – | – | – | – | – | **Risqué** (31 % d'adresses retrouvées) |

---

## 2. Détail par source

### A. Vélib' Métropole (GBFS)

**Accès**

| Appel | HTTP | Temps de réponse |
|---|---|---|
| station_information | 200 | 0,87 s |
| station_status #1 (08:40:43Z) | 200 | 0,98 s |
| station_status #2 (08:41:44Z) | 200 | 0,81 s |
| station_status #3 (08:42:45Z) | 200 | 1,00 s |

Pas de clé API. Le service est derrière Cloudflare (`cf-cache-status: DYNAMIC`).

**Structure.** Les deux fichiers ont la forme `{lastUpdatedOther, ttl: 3600, data: {stations: [...]}}`.

- `station_information` : 1 519 stations et 8 champs : `station_id`, `stationCode`, `name`, `lat`, `lon`, `capacity`, `station_opening_hours`, `rental_methods`.
- `station_status` : 1 519 stations et 12 champs : `station_id`, `num_bikes_available`, `numBikesAvailable`, `num_bikes_available_types` (liste `[{mechanical}, {ebike}]`), `num_docks_available`, `numDocksAvailable`, `is_installed`, `is_returning`, `is_renting`, `last_reported`, `stationCode`, `station_opening_hours`.
- Encodage : UTF-8 sans BOM. Les accents sont présents dans `name`.

**Exemples (station_status #1)**

| station_id | stationCode | num_bikes_available | num_docks_available | last_reported (UTC) | is_renting |
|---|---|---|---|---|---|
| 213688169 | 16107 | 8 (4 méca + 4 élec) | 27 | 2026-10-05 08:21:11 | 1 |
| 19179944124 | 40001 | 18 | 9 | 1791188510 (epoch) | 1 |
| 18795078746 | 32304 | 4 | 24 | 1791188427 | 1 |
| 36255 | 9020 | 4 | 17 | 1791188507 | 1 |
| 251039991 | 14111 | 21 | 4 | 1791188628 | 1 |

Correspondance avec `station_information` : `213688169` = « Benjamin Godard - Victor Hugo », lat 48.865983, lon 2.275725, capacité 35.

**Valeurs manquantes**

- `station_opening_hours` est `null` pour 1 519/1 519 stations.
- `rental_methods` est absent pour 625/1 519 stations.
- Aucun champ manquant dans `station_status`.
- 0 doublon sur `station_id`. Les 1 519 stations sont identiques dans les deux fichiers.
- 2 stations ont `is_installed = 0` et 15 ont `is_renting = 0`.
- 13 stations ont un `last_reported` de plus de 24 h (le plus ancien date du 21/02/2021).

**Test des 3 appels à 1 minute d'intervalle**

| Comparaison | `lastUpdatedOther` | `last_reported` modifié | `num_bikes_available` modifié | Total vélos dispo |
|---|---|---|---|---|
| appel 1 | 08:39:53Z | – | – | 19 117 |
| appel 1 → 2 | 08:40:54Z | **0 station** | **136 stations** | 19 119 |
| appel 2 → 3 | 08:41:55Z | **0 station** | **154 stations** | 19 116 |
| 4ᵉ appel (08:43:26) vs appel 1 | 08:43:00Z | 91 stations | – | – |

Exemple pour la station 213688169 : 8 → 9 → 9 vélos, alors que `last_reported` reste à 08:21:11 sur les 3 appels.

**Conclusion.** Les compteurs changent bien chaque minute. En revanche, `last_reported` est mis à jour **par lots, avec
environ 20 min de retard** : au 4ᵉ appel (08:43Z), le maximum était encore à 08:23:48. Il ne faut **pas** s'en servir
comme horodatage d'observation. Utiliser `lastUpdatedOther` (au niveau du fichier) ou l'heure de collecte.

**Verdict : OK avec réserves.**

- Il n'y a **pas d'historique** côté source : tout l'historique doit être construit par vos propres collectes. C'est justement l'intérêt du Bronze, mais il faut lancer la collecte dès le 1er jour.
- `last_reported` n'est pas fiable (voir ci-dessus).
- `station_id` dépasse 2³¹ (ex. 19179944124) : le typer en `bigint`. `stationCode` est une chaîne, sans zéro devant (« 9020 »).
- `ttl` vaut 3600 alors que les données changent toutes les minutes : ne pas se fier au `ttl` pour la fréquence de collecte.
- Volume en collecte chaque minute : 464 Ko × 1 440 = **~670 Mo/jour en JSON brut** (~44 Mo/jour en gzip, ratio ×15). Toutes les 5 min : ~134 Mo/jour brut.

### B. Open-Meteo

**Accès** (sans clé)

| Appel | Résultat |
|---|---|
| forecast, 1er test curl | 200 en 0,49 s |
| forecast, script | essai 1 : erreur SSL (EOF), essai 2 : **200 en 0,65 s** |
| forecast multi-points (4 coordonnées en 1 appel) | 200 en 0,74 s |
| forecast `past_days=2&current=…` | 1er essai : timeout 30 s, 2ᵉ essai : 200 |
| archive, 1er test curl | erreur SSL au bout de 30 s, puis **HTTP 429**, puis 200 |
| archive, script | 429, 429, 429, puis **200 en 0,78 s** (4ᵉ essai) |
| archive, test suivant | `{"error":true,"reason":"Daily API request limit exceeded. Please try again tomorrow."}` |

**Structure.** Les métadonnées sont `latitude`, `longitude`, `elevation`, `timezone`, `utc_offset_seconds`, `hourly_units`.
Les valeurs sont stockées **en colonnes** : `hourly.time[]`, `hourly.temperature_2m[]`, `hourly.precipitation[]`.
Il y a donc 3 champs × 168 lignes par semaine, en UTF-8. On n'observe aucun `null` (0/168 pour chaque variable, dans les
deux fichiers).

| Fichier | Point renvoyé (demandé : 48.85 / 2.35) | Période | Température min / max | Précipitations cumulées |
|---|---|---|---|---|
| forecast | **48.84 / 2.36** | 05/10 → 11/10 (7 j) | 7,9 / 23,9 °C | 15,1 mm |
| archive | **48.8225 / 2.2881** | 21/09 → 27/09 | 11,3 / 27,6 °C | 0,0 mm |

**5 lignes (archive, heure de Paris)**

| time | temperature_2m | precipitation |
|---|---|---|
| 2026-09-21T00:00 | 16.5 | 0.0 |
| 2026-09-21T01:00 | 15.6 | 0.0 |
| 2026-09-21T02:00 | 14.5 | 0.0 |
| 2026-09-21T03:00 | 14.0 | 0.0 |
| 2026-09-21T04:00 | 13.4 | 0.0 |

**Verdict : OK avec réserves.**

- **Quota de 10 000 appels/jour par IP** (offre gratuite, usage non commercial). Il a été épuisé depuis l'IP partagée du conteneur, pas par nos ~10 appels. Depuis votre IP ou Azure, ce ne devrait pas être un problème, mais **gardez des appels peu nombreux** : un appel multi-points par heure suffit.
- La connexion a été instable pendant les tests (2 erreurs SSL, 3 timeouts). `collecte_test.py` fait donc des retries (2, 4, 8 s).
- Le point renvoyé est **recalé sur la grille du modèle**, et la grille n'est pas la même pour la prévision et pour l'archive (écart d'environ 5 km). Il faut stocker les `latitude`/`longitude` renvoyées dans le Bronze.
- Le fuseau horaire est à fixer explicitement (`timezone=Europe/Paris`). Sinon les heures sont en GMT : le même instant apparaissait à 14,5 °C « 00:00 GMT » contre 16,5 °C « 00:00 Paris ».
- `precipitation` horaire = cumul de **l'heure précédente** (convention Open-Meteo). C'est à prendre en compte pour l'arrondi de l'heure dans la jointure.
- Alternative à l'archive pour les derniers jours : `forecast?past_days=N` a renvoyé 72 lignes à partir du 03/10. Le délai de publication exact de l'archive n'a pas pu être mesuré (quota).

### C. Prix des carburants (flux instantané)

**Accès.** HTTP 200 en 0,76–0,86 s, 941 Ko, `application/zip`, pas de clé API.

**Contenu.** Le zip contient 1 fichier, `PrixCarburants_instantane.xml` (12 127 351 octets).

**Encodage.** Le prologue est `<?xml version="1.0" encoding="ISO-8859-1"?>`. Un décodage en UTF-8 **échoue** (octet 0xE9 à la
position 660). Il faut donc lire le fichier avec un parseur XML qui respecte le prologue, ou en `latin-1`.

**Structure**

```
pdv_liste
└── pdv  @id @latitude @longitude @cp @pop(R|A)     ← 9 834 stations
    ├── adresse, ville                                  (9 834 / 9 834)
    ├── horaires @automate-24-24 > jour @id @nom @ferme (8 519 / 9 834)
    ├── services > service*                             (9 834 / 9 834)
    └── prix @nom @id @maj @valeur                      ← 30 201 lignes de prix
```

- Répartition des carburants : Gazole 8 784, SP98 6 826, E10 6 720, E85 3 638, SP95 2 728, GPLc 1 505.
- `pop` : R (route) 9 398, A (autoroute) 436.
- Prix en €/L décimaux, de 0,777 à 2,900.
- Aucun élément `rupture` n'a été trouvé dans ce fichier.

**5 lignes (aplaties station × carburant)**

| id | cp | ville | adresse | latitude | longitude | carburant | valeur | maj |
|---|---|---|---|---|---|---|---|---|
| 89100001 | 89100 | SENS | 84 ROUTE DE MAILLOT | 4818300 | 330900 | Gazole | 2.429 | 2026-09-28 11:45:27 |
| 89100001 | 89100 | SENS | 84 ROUTE DE MAILLOT | 4818300 | 330900 | E85 | 0.859 | 2026-08-25 10:02:31 |
| 89100001 | 89100 | SENS | 84 ROUTE DE MAILLOT | 4818300 | 330900 | E10 | 2.209 | 2026-09-28 11:45:27 |
| 89100001 | 89100 | SENS | 84 ROUTE DE MAILLOT | 4818300 | 330900 | SP98 | 2.289 | 2026-09-28 11:42:00 |
| 40500002 | 40500 | Saint-Sever | Route de Mont de Marsan | 4377300 | -56700 | Gazole | 2.379 | 2026-09-30 15:04:41 |

**Valeurs manquantes et qualité**

- 702 stations n'ont **aucun prix**.
- 1 315 stations n'ont pas de bloc `horaires`.
- Chaque station n'a que les carburants qu'elle vend : il n'y a pas de colonne vide, mais l'ensemble des carburants varie d'une station à l'autre.
- Les dates `maj` vont du 28/07/2025 au 05/10/2026. 895 prix ont plus de 30 jours et 6 042 datent d'aujourd'hui.
- La casse des villes est hétérogène (`SENS` / `Saint-Sever`).
- Seulement 47 stations à Paris (75).

**Fraîcheur.** Le `Last-Modified` valait 06:50:16 UTC au téléchargement de 08:40, puis 08:40:16 UTC à 08:45, 08:46, 08:47
et 08:48. Le `maj` le plus récent du fichier (08:49:56) correspond à 06:49:56 UTC : **les `maj` sont en heure de Paris
sans fuseau.**

**Verdict : OK.** Source fiable et rapide, sans clé. Réserves :

- **Encodage latin-1.**
- **Coordonnées en entiers × 100 000** (`4818300` → 48.18300). Format « PTV_GEODECIMAL » : il faut diviser par 100 000.
- XML imbriqué à aplatir en Silver.
- Dates sans fuseau.
- La fréquence exacte de régénération reste à mesurer (polling toutes les 10 min pendant une journée).
- Atout : des historiques officiels existent (`/opendata/jour` = 1,1 Mo, `/opendata/annee/2025` = 31,7 Mo).

### D. DVF géolocalisé

**Repérage.** Via l'API `https://www.data.gouv.fr/api/1/datasets/demandes-de-valeurs-foncieres-geolocalisees/` :

- licence `lov2`, fréquence `semiannual` ;
- 3 ressources : le fichier national `dvf.csv.gz` (**523 Mo**, à ne pas télécharger), la documentation, et le dossier `https://files.data.gouv.fr/geo-dvf/latest/csv/` ;
- arborescence : `csv/<année>/departements/<dep>.csv.gz`, et aussi `communes/` et `full.csv.gz` (98 Mo pour 2025).

**Fichier retenu :** `https://files.data.gouv.fr/geo-dvf/latest/csv/2025/departements/75.csv.gz`

- 302 vers OVH S3, puis 200 en 2,1 s.
- `Content-Length` 2 056 139, `Last-Modified` 18/05/2026, `Accept-Ranges: bytes`.
- Autres années pour Paris : 2021 = 2,1 Mo, 2022 = 2,4 Mo, 2023 = 2,0 Mo, 2024 = 1,8 Mo.

**Format.** CSV UTF-8 sans BOM, séparateur virgule, 84 440 lignes, 40 colonnes. Les dates vont du 02/01/2025 au 31/12/2025.
Les colonnes sont :

`id_mutation, date_mutation, numero_disposition, nature_mutation, valeur_fonciere, adresse_numero, adresse_suffixe, adresse_nom_voie, adresse_code_voie, code_postal, code_commune, nom_commune, code_departement, ancien_code_commune, ancien_nom_commune, id_parcelle, ancien_id_parcelle, numero_volume, lot1_numero … lot5_surface_carrez, nombre_lots, code_type_local, type_local, surface_reelle_bati, nombre_pieces_principales, code_nature_culture, nature_culture, code_nature_culture_speciale, nature_culture_speciale, surface_terrain, longitude, latitude`

**5 lignes**

| id_mutation | date | nature | valeur_fonciere | adresse | cp | type_local | surface_bati | pièces | lon | lat |
|---|---|---|---|---|---|---|---|---|---|---|
| 2025-1273241 | 2025-01-03 | Vente | 1500000 | 27 RUE DES ROSIERS | 75004 | Local industriel… | 160 | 0 | 2.358325 | 48.857555 |
| 2025-1273242 | 2025-01-03 | Vente | 430500 | 88 RUE MARCADET | 75018 | Dépendance | | 0 | 2.346344 | 48.890689 |
| 2025-1273242 | 2025-01-03 | Vente | 430500 | 88 RUE MARCADET | 75018 | Appartement | 48 | 3 | 2.346344 | 48.890689 |
| 2025-1273243 | 2025-01-03 | Vente | 527700 | 161 RUE MARCADET | 75018 | Appartement | 40 | 1 | 2.337299 | 48.891073 |
| 2025-1273243 | 2025-01-03 | Vente | 527700 | 161 RUE MARCADET | 75018 | Dépendance | | 0 | 2.337299 | 48.891073 |

**Valeurs manquantes**

| Colonne | % vide |
|---|---|
| `valeur_fonciere` | 1,2 % |
| `code_postal` | 0,2 % |
| `type_local` | 0,7 % |
| `surface_reelle_bati` | 48,9 % (les dépendances n'ont pas de surface) |
| `lot1_surface_carrez` | 62,9 % |
| `adresse_suffixe` | 96 % |
| `ancien_*` | 100 % |
| `latitude` / `longitude` | 17 lignes sans coordonnées |

Répartition : `type_local` = Dépendance 40 655, Appartement 37 796, Local commercial 5 186, Maison 190.
`nature_mutation` = Vente 83 447, Échange 483, VEFA 352, Adjudication 156.

**Verdict : OK.** Accès simple, fichier par département et par année, coordonnées WGS84 déjà présentes. Réserves :

- **Une mutation = plusieurs lignes.** 40 811 mutations pour 84 440 lignes, et 22 809 mutations sont sur plusieurs lignes. `valeur_fonciere` est **répétée sur chaque ligne** : la sommer naïvement surestime fortement les montants.
- Le prix au m² n'a de sens que pour les mutations contenant un seul local.
- Mise à jour seulement **semestrielle** : pas de flux, donc peu d'intérêt pour un pipeline incrémental.

### E. ADEME DPE logements existants (`dpe03existant`)

**Accès** (sans clé)

| Appel | HTTP | Temps | Taille |
|---|---|---|---|
| `GET .../lines?size=100` (JSON) | 200 | 1,41 s | 604 Ko |
| `GET .../lines?size=100&format=csv` | 200 | 1,34 s | 210 Ko |
| `GET .../lines?size=10001` | – | – | erreur `"size + skip" cannot be more than 10000` |

Au-delà de 10 000 lignes, il faut paginer avec le curseur `after` (fourni dans le champ `next`). Les filtres fonctionnent,
par exemple `code_postal_ban_eq=75011` (56 909 DPE) ou `code_departement_ban_eq=75` (849 678 DPE).

**Format**

- Schéma de 230 champs dans les métadonnées. Le CSV en contient 226 : les 4 champs internes `_geopoint`, `_id`, `_i`, `_rand` n'y sont pas.
- **Le CSV commence par un BOM UTF-8.** La 1ʳᵉ colonne lue sans précaution s'appelle donc `﻿numero_dpe` (`KeyError` constaté). Il faut lire avec `encoding="utf-8-sig"`.
- **Certains noms de colonnes contiennent des espaces** : `conso_5 usages_ef`, `conso_5 usages_par_m2_ef`, `emission_ges_5_usages par_m2`. Ces noms sont refusés par Parquet/Delta : il faut les renommer en Silver.

**Colonnes utiles** (taux de vide sur l'échantillon France de 100 lignes / échantillon 75011 de 100 lignes)

| Rôle | Colonnes | % vide France / 75011 |
|---|---|---|
| Identifiant | `numero_dpe` | 0 / 0 |
| Date | `date_etablissement_dpe` (aussi `date_reception_dpe`, `date_fin_validite_dpe`) | 0 / 0 |
| **Étiquette** | `etiquette_dpe` (A–G), `etiquette_ges` | 0 / 0 |
| Consommation | `conso_5_usages_par_m2_ep`, `emission_ges_5_usages par_m2` | 0 / 0 |
| **Surface** | `surface_habitable_logement` (aussi `surface_habitable_immeuble`) | 4 / 2 |
| **Code postal** | `code_postal_ban`, `code_insee_ban`, `code_departement_ban` | 14 / 0 |
| Adresse | `adresse_ban`, `numero_voie_ban`, `nom_rue_ban`, `identifiant_ban`, `score_ban` | 14 / 0 |
| Coordonnées | `coordonnee_cartographique_x_ban` / `_y_ban` (**Lambert 93, EPSG:2154**) | 14 / 0 |
| Bâtiment | `type_batiment`, `periode_construction`, `annee_construction`, `id_rnb` | annee : 47 / 76 ; id_rnb : 62 / 83 |
| Chauffage | `type_energie_principale_chauffage` | 0 / 0 |

Autres constats :

- Sur 100 lignes, 22 à 36 colonnes sont entièrement vides et 79 à 90 sont vides à plus de 50 %.
- Étiquettes (75011) : B 1, C 32, D 20, E 27, F 8, G 12.

**5 lignes (filtre 75011)**

| numero_dpe | date | DPE | GES | type | surface | cp | adresse_ban | x (L93) | y (L93) |
|---|---|---|---|---|---|---|---|---|---|
| 2675E0079556Y | 2026-01-12 | D | D | appartement | 38.2 | 75011 | 82 Rue de la Roquette 75011 Paris | 654220.84 | 6861956.66 |
| 2175E0788073K | 2021-11-27 | D | B | appartement | 66.4 | 75011 | 54 Rue de Malte 75011 Paris | 653512.46 | 6863246.09 |
| 2675E0022855D | 2026-01-06 | C | B | appartement | 18.6 | 75011 | 48 Passage du Bureau 75011 Paris | 655533.8 | 6861674.22 |
| 2675E0066025N | 2026-01-10 | C | A | appartement | 33.8 | 75011 | 6 Rue Popincourt 75011 Paris | 654340.8 | 6862076.14 |
| 2675E0008072O | 2026-01-05 | E | C | appartement | 40.6 | 75011 | 51 Rue Alexandre Dumas 75011 Paris | 655587.45 | 6861732.3 |

**Fréquence.** `dataUpdatedAt` = 2026-10-01. Le DPE le plus récent (`sort=-date_etablissement_dpe`) date du 28/09/2026.
Le tri par défaut de l'API **n'est pas chronologique** : les 100 premières lignes vont de 2021 à janvier 2026.

**Verdict : OK avec réserves.**

- API rapide et sans clé.
- Le volume complet (15,7 M lignes × 226 colonnes, soit environ 2 Ko par ligne en CSV, **~30 Go estimés**) impose une extraction filtrée et paginée.
- Pièges : BOM, colonnes avec espaces, Lambert 93, beaucoup de colonnes vides.
- La `bbox` du jeu de données va de −5,98° à 64,05° de latitude : il y a des géocodages aberrants ou hors métropole à filtrer.

---

## 3. Croisement A + B (Vélib' × météo) : testé

**Clé de jointure : `heure` (heure de Paris, tronquée à l'heure) + `point_meteo`.**

- **Côté Vélib'**, l'heure se calcule à partir de `lastUpdatedOther`, converti d'epoch UTC vers `Europe/Paris` puis tronqué. Ne pas utiliser `last_reported` (voir A).
- **Côté météo**, on prend `hourly.time` obtenu avec `timezone=Europe/Paris`. Il est déjà au format `YYYY-MM-DDTHH:00`.
- **Côté spatial**, deux options mesurées :
  1. **Un seul point pour Paris.** Toutes les stations reçoivent la même météo. C'est le plus simple, et suffisant pour 1 semaine.
  2. **Une tuile par station** : arrondir `lat`/`lon` de la station au pas *p* et appeler Open-Meteo une fois en multi-points (testé : 4 points en un appel, HTTP 200, 0,74 s). Les 1 519 stations donnent **11 tuiles à 0,1°, 34 tuiles à 0,05° et 144 tuiles à 0,02°**. On stocke la table `station_id → tuile`. Comme la grille du modèle est d'environ 0,02° (48.84/2.36 renvoyé pour 48.85/2.35), un pas de 0,05° est un bon compromis.

**Résultat sur les échantillons** (prévision du 05/10, point unique) :

| Snapshot | Observation (Paris) | Clé heure | Météo jointe | Stations jointes |
|---|---|---|---|---|
| #1 | 10:39:53 CEST | 2026-10-05T10:00 | 14,7 °C, 0,0 mm | **1 519 / 1 519** |
| #2 | 10:40:54 CEST | 2026-10-05T10:00 | 14,7 °C, 0,0 mm | 1 519 / 1 519 |
| #3 | 10:41:55 CEST | 2026-10-05T10:00 | 14,7 °C, 0,0 mm | 1 519 / 1 519 |

**Attention à l'arrondi.** Les précipitations de « 11:00 » couvrent la plage 10:00–11:00. Pour expliquer l'état d'une
station observée à 10:40, on peut préférer l'heure **supérieure** pour la pluie. Il faut choisir une convention
(troncature ou heure supérieure) et la documenter en Silver.

## 4. Croisement D + E (DVF × DPE) : testé, difficile

Il n'existe **aucun identifiant commun**. DVF a `id_parcelle` ; le DPE n'a ni parcelle ni lot, et `id_rnb` est vide à
62–83 %. Test de jointure par adresse (numéro + voie normalisés, majuscules, sans accents) entre les 100 DPE du 75011 et
DVF 2025 du 75011 : **31/100 retrouvés**.

DVF abrège les types de voie (`BD`, `PAS`, `AV`…) alors que le DPE les écrit en toutes lettres, et la correspondance se
fait au niveau de **l'immeuble**, pas du logement (plusieurs appartements à la même adresse). Il faudrait en plus convertir
Lambert 93 → WGS84 pour une jointure spatiale. C'est faisable, mais c'est un projet de *data quality* à part entière.

---

## 5. Problèmes rencontrés

1. **Open-Meteo, quota.** `HTTP 429` puis `Daily API request limit exceeded`, venant de l'IP de sortie partagée du conteneur cloud. Les échantillons ont été obtenus au 4ᵉ essai. → Re-tester depuis votre IP ; limiter à 1 appel multi-points par heure.
2. **Open-Meteo, connexion instable.** 2 erreurs SSL (`UNEXPECTED_EOF`, `SSL_ERROR_SYSCALL`) et 3 timeouts de 30 s sur une quinzaine d'appels. → Retries avec backoff dans `collecte_test.py`.
3. **data.gouv.fr, coupures.** 6 `Connection reset by peer` sur la page HTML et sur l'API de recherche ; chaque fois, un nouvel essai a fonctionné. `files.data.gouv.fr` (DVF) n'a posé aucun problème.
4. **Vélib' : `last_reported` en retard d'environ 20 min**, mis à jour par lots, plus 13 stations figées depuis plus de 24 h. → Horodater avec `lastUpdatedOther`.
5. **Carburants, encodage ISO-8859-1.** La lecture en UTF-8 échoue.
6. **Carburants, coordonnées ×100 000 et dates `maj` sans fuseau** (heure de Paris).
7. **DPE, BOM UTF-8** (1ʳᵉ colonne `﻿numero_dpe`) et **noms de colonnes avec espaces**, incompatibles avec Parquet/Delta.
8. **DPE, `size` ≤ 10 000.** Il faut paginer avec `after` ; le volume complet est d'environ 30 Go.
9. **DVF, lignes multiples par mutation** avec `valeur_fonciere` dupliquée.
10. **Systèmes de coordonnées hétérogènes** : WGS84 (Vélib', Open-Meteo, DVF), Lambert 93 (DPE), entiers ×10⁵ (carburants).
11. **Licence Vélib' ambiguë** sur data.gouv.fr (ODbL pour les jeux Ville de Paris et Région IDF, Licence Ouverte pour un autre jeu Ville de Paris). → Vérifier sur le portail opendata.paris.fr et citer la source (ODbL : attribution + partage à l'identique des bases dérivées).

## 6. Échantillons produits (`./echantillons/`)

Chaque fichier est accompagné d'un `.meta.json` : URL, code HTTP, temps de réponse, taille, sha256, horodatage de collecte.

| Dossier | Fichiers | Taille |
|---|---|---|
| `velib/` | `station_information_*.json` + 3 × `station_status_*.json` (08:40, 08:41, 08:42 UTC) | 1,7 Mo |
| `meteo/` | `forecast_*.json`, `archive_2026-09-21_2026-09-27.json` | 28 Ko |
| `carburants/` | `instantane_*.zip` + XML extrait | 13 Mo |
| `dvf/` | `dvf_2025_75.csv.gz` (laissé compressé, comme en Bronze) | 2,0 Mo |
| `dpe/` | `dpe03existant_france_100_*.csv`, `dpe03existant_75011_100_*.csv` | 420 Ko |

---

## 7. Recommandation

### Sujet recommandé : **(1) Vélib' + météo**

**Pourquoi c'est le plus faisable en 1 semaine**

- Les deux sources ont été validées techniquement : sans clé, réponses en moins d'1 s, JSON UTF-8 propre, 0 valeur manquante sur les champs utiles.
- La jointure a été **testée de bout en bout** : 1 519/1 519 stations jointes. Elle repose sur une clé simple (heure + point météo) et ne demande ni normalisation d'adresse ni changement de projection.
- Le modèle Gold est naturel :
  - faits `fact_disponibilite(station, heure, vélos méca/élec, bornes libres)` ;
  - dimensions `dim_station`, `dim_meteo_heure`, `dim_temps` ;
  - KPI : taux de remplissage, stations vides ou pleines, effet de la pluie et de la température.
- Peu de pièges, tous identifiés : `last_reported`, `bigint`, fuseau horaire, quota Open-Meteo.

**Pourquoi un datalake est réellement utile ici**

- **Historisation.** Le GBFS ne donne **que l'état présent** : sans collecte régulière, l'historique n'existe nulle part. Le Bronze append-only (un fichier horodaté par appel, partitionné `source/date/heure`) *est* la donnée. Le Silver dédoublonne et met à plat, le Gold agrège à l'heure.
- **Volume.** Environ 670 Mo/jour de JSON brut à 1 appel/min (~4,7 Go/semaine, ~20 Go/mois). C'est trop pour un simple tableur, mais idéal pour montrer l'intérêt de Parquet/Delta : le JSON se compresse ×15 en gzip, et le passage en colonnes réduit encore la taille.
- **Formats et rythmes variés.** On a du JSON imbriqué (`num_bikes_available_types`), une dimension lente (`station_information`, à historiser en SCD2 : capacité, stations ouvertes ou fermées), et une API météo colonnaire avec un rythme différent (horaire contre minute). Des données de référence pourraient être ajoutées facilement (IRIS, arrondissements).

**Point de vigilance.** Il faut **démarrer la collecte dès le jour 1** (Azure Function timer ou pipeline Data Factory toutes les
1 à 5 min, et la météo une fois par heure), puisque l'historique s'accumule au fil de la semaine. Pour le reste, utiliser les
snapshots déjà collectés et l'archive Open-Meteo.

### Les deux autres sujets

- **(2) Carburants : bon plan B, surtout si la collecte continue n'est pas possible.** Une seule source, mais un vrai format différent (XML latin-1 imbriqué dans un zip). Surtout, **des historiques officiels sont téléchargeables** (`/opendata/annee/2025`, 31,7 Mo), ce qui permet un backfill immédiat. Le défaut : moins de variété de sources et pas de croisement naturel, à moins d'ajouter une source externe.
- **(3) DVF + DPE : déconseillé en 1 semaine.**
  - Le DPE fait environ 30 Go au complet, avec 226 colonnes, un BOM, des noms de colonnes avec espaces et du Lambert 93.
  - DVF est semestriel : pas d'ingestion incrémentale à montrer.
  - Surtout, la jointure, cœur du sujet, ne retrouve que **31 % des adresses** au niveau de l'immeuble. Il faudrait plusieurs jours de normalisation ou de géocodage avant d'avoir un Gold exploitable.
  - C'est un excellent sujet de volume et de qualité de données, mais sur 3 à 4 semaines.
