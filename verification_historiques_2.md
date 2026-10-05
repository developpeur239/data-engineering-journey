# Vérification des historiques, 2ᵉ partie : Kaggle Vélib' (déc. 2025) et compteurs vélo de Paris

Tests faits le **lundi 5 octobre 2026, entre 12:15 et 12:50 UTC**, avec `curl`, Python 3.11, DuckDB 1.5 et `git`.

Chaque information est marquée :
- **[mesuré]** : obtenu par une requête ou un calcul sur les fichiers téléchargés ;
- **[lu]** : tiré d'une fiche, d'une description ou d'une documentation ;
- **[estimé]** : extrapolé à partir d'une mesure partielle.

> **Identifiants Kaggle.** Les variables `KAGGLE_USERNAME` et `KAGGLE_KEY` étaient **vides**. Vous avez joint
> `kaggle.json` : il a été lu directement par les commandes, et son contenu injecté en variable d'environnement le
> temps d'un processus. Il n'a jamais été recopié, affiché ni écrit dans un fichier ; un `grep` de la clé sur le dépôt
> donne **0** occurrence. Le fichier joint étant passé par la conversation, **régénérez la clé sur Kaggle**.
> `charger_historique_kaggle()` lit les deux variables d'environnement.

---

## 1. Tableau récapitulatif

| | **A. Kaggle « velib-data »** | **B. Compteurs vélo Paris** |
|---|---|---|
| URL | `kaggle.com/datasets/adrienmorel97/velib-data` (API `api/v1/datasets/download/…`) | `opendata.paris.fr`, jeux `comptage-velo-donnees-compteurs` + `comptage-velo-compteurs` (API v2.1) |
| Période mesurée | **02/12/2025 00:00 → 16/12/2025 16:35 UTC** (14,7 jours) | **03/09/2025 01:00 → 03/10/2026 21:00 UTC** (9 501 h, ≈ 13 mois) |
| Fréquence réelle | **5,0 min** (écart médian par station ; 90e centile 5,3 min ; maximum 10,5 min) | **horaire** (toutes les dates à hh:00:00 ; écart médian 1 h) |
| Format | 1 Parquet (Snappy), 14 colonnes, 6 353 181 lignes | Parquet par export (ou CSV `;` avec BOM), 17 colonnes, 1 043 193 lignes |
| Volume | Zip **13,4 Mo** → Parquet **55,1 Mo** (non commité) | **18,8 Mo** de Parquet pour 13 mois ; CSV toutes colonnes ≈ 2 Go brut / 361 Mo gzip [estimé] |
| Complétude | **99,88 %** de la grille 5 min ; toujours 1 503 stations par créneau | **97,2 %** des heures × compteurs ; 104/113 compteurs ≥ 95 % ; 25 compteurs en panne à un moment |
| Mise à jour [lu] | Version 13 du 16/12/2025 : **figé** | Quotidienne (J-1), 13 mois glissants ; dernière le 04/10/2026 |
| Licence [lu] | **CC BY-SA 4.0** | **ODbL** (Ville de Paris, DVD) |
| Lien avec mes données | `station_id` **= `station_id` de l'API Vélib'** (1 498/1 503, 99,7 %). Pénurie calculable ; **saturation non fiable** (pas de colonne bornes libres) | Coordonnées : 100 % des compteurs à ≤ 500 m d'un arrêt ferré ; aucun lien direct avec Vélib' |
| **Verdict** | **OK avec réserves** : excellent mais court (15 jours), et saturation approximative | **OK avec réserves** : officiel, 13 mois de recouvrement avec RATPstatus, pannes de compteurs à filtrer ; **à archiver dès maintenant** |

---

## 2. Source A : Kaggle « velib-data »

### A1. Métadonnées [mesuré via l'API, contenu lu]

| Élément | Valeur |
|---|---|
| Accès à `GET /api/v1/datasets/view/adrienmorel97/velib-data` | HTTP 200, **avec et sans authentification** |
| Auteur | « Adrien » |
| Version | **13**, du **16/12/2025 à 16:47 UTC** (« Update 2025-12-16 ») |
| Licence | **CC BY-SA 4.0** |
| Statistiques | 160 téléchargements ; *usability* 1.0 |
| Fichiers | **un seul** : `velib_concat.parquet`, de 55 133 541 octets |
| Zip complet (requête Range de 1 octet) | **13 406 856 octets** |

Le HEAD sur l'URL de téléchargement renvoie **404**, alors qu'un GET avec `Range: bytes=0-0` renvoie 206 avec `Content-Range` : c'est cette requête Range qui sert à lire la taille.

La description **[lu]** annonce plusieurs colonnes qui **n'existent pas** dans le fichier **[mesuré]** : nombre de bornes libres, `occ_ratio`, `stations_meta.csv`, `calendar_features.csv`.

### A2. Contenu [mesuré]

- **Colonnes :** `ts_utc`, `tbin_utc` (TIMESTAMP_NS, UTC), `station_id` (BIGINT), `bikes`, `capacity`, `mechanical`, `ebike`, `status` (`OK` / `CLOSED`), `lat`, `lon`, `name`, `temp_C`, `precip_mm`, `wind_mps`.
- **Encodage :** UTF-8 (accents corrects, ex. « Ventadour - Opéra »).
- **Fuseau :** UTC. `ts_utc` est l'instant de collecte, en moyenne 41 s après le créneau `tbin_utc`.
- **Taille :** 1 503 stations, 4 227 créneaux de 5 min, **6 353 181 lignes** (le chiffre du projet tiers est confirmé).
- **Qualité :** **0 doublon** (station, créneau), **0 valeur NULL**.
- **Statut :** `OK` dans 6 198 895 lignes, `CLOSED` dans 154 286.
- **Anomalies :**
  - `bikes ≠ mechanical + ebike` : 35 836 lignes ;
  - `bikes > capacity` : 11 411 lignes ;
  - `capacity = 0` : 28 605 lignes.
- **Météo :** jointe par heure (353 heures distinctes).

### A3. Trous [mesuré]

- **Aucun créneau de plus de 15 min sans relevé.**
- **5 créneaux manquants** sur 4 232 attendus, tous à **04:00 UTC** : les 2, 8, 11, 12 et 13 décembre, sans doute une maintenance quotidienne.
- **Complétude de la grille 5 min : 99,88 %.**
- Le dernier jour (16/12) est partiel : 200 créneaux sur 288.

### A4. Compatibilité avec ma collecte en direct [mesuré]

**Identifiants.** Le `station_id` Kaggle est **le même `station_id` que l'API Vélib'** (1 498 sur 1 503, soit 99,7 %), et non le `stationCode` (0 %). Exemple : 6294 = « Marché aux fleurs » dans les deux sources, à 0 m. Par le nom, 99,5 % des stations correspondent ; par la distance (≤ 20 m), 99,5 % aussi.

**Pénurie.** `bikes = 0` permet le même calcul que ma collecte.

**Saturation : pas de colonne « bornes libres ».** J'ai testé l'approximation `capacity − bikes = 0` sur mes 3 relevés en direct :

| Mesure | Résultat |
|---|---|
| Stations où `capacity − vélos` = bornes libres | **44,6 % seulement** (bornes hors service) |
| Saturations réelles (`num_docks_available = 0`) | 84 |
| Saturations détectées par l'approximation | 47, dont **42 correctes** |

L'approximation ne retrouve donc **qu'environ la moitié des saturations**. → Avec Kaggle, la pénurie est fiable, la saturation ne l'est pas.

### A5. RATPstatus du 2 au 16 décembre 2025 [mesuré]

Chargé par `charger_historique_ratpstatus` (clone partiel) dans `echantillons/historiques/ratpstatus/`, soit 15 fichiers tar.xz pour 5,5 Mo.

- **Complétude : 15 jours sur 15 à 720/720 fichiers (100 %)**, écart médian de 2 min, aucun trou de plus d'1 h. Seuls 2 fichiers JSON sont invalides (vides).
- **Épisodes ferrés** : cause PERTURBATION, regroupement par titre, jour et présences contiguës (≤ 10 min), comme dans `verification_historiques.md`. On en compte **1 824** (à partir de 3 028 identifiants bruts), d'une durée médiane de 66 min (p75 : 86 min).

| | BLOQUANTE | PERTURBEE | INFORMATION |
|---|---|---|---|
| Métro | 105 | 895 | 0 |
| RER / train | 186 | 487 | 24 |
| Tram | 39 | 88 | 0 |
| **Total** | **330** | **1 470** | 24 |

À part, les travaux comptent 10 épisodes bloquants et 123 perturbés.

### A6. Météo Open-Meteo, archive [mesuré]

Un seul appel, du 02/12 au 16/12/2025, point (48,85 ; 2,35), en UTC :

- **HTTP 200 en 0,78 s**, 10 510 octets, 360 lignes horaires, 0 valeur NULL ;
- point de grille renvoyé : 48,82 ; 2,29 ;
- température de −0,3 à 15,8 °C, précipitations cumulées de 17,6 mm.

**Aucune erreur 429 ni de quota.** Fichier : `echantillons/historiques/kaggle/meteo_archive_20251202_20251216.json`.

### A7. Faisabilité « jour ouvré à 8 h » [mesuré]

**Paramètres :**
- 11 jours ouvrés, du 2 au 16/12/2025 ;
- 8 h à Paris = 07:00 UTC en décembre ;
- 1 503 stations, soit 16 533 couples (station, jour) ;
- incidents ferrés actifs dans l'instantané de 08:00, gravités BLOQUANTE + PERTURBEE, rayon de 300 m.

| Arrêts pris en compte | Couples « avec » | Stations ≥ 3 « avec » | Stations ≥ 3 « sans » | **Stations ≥ 3 des deux** | Pénurie à 8 h avec / sans (descriptif) |
|---|---|---|---|---|---|
| Arrêts ciblés (`stop_point`) | 288 (1,7 %) | 13 | 1 497 | **7** | 3,5 % / 4,1 % |
| Arrêts + lignes entières | 1 535 (9,3 %) | 135 | 1 429 | **61** | 6,1 % / 3,9 % |

**Conclusion A7 : non.** Ces 15 jours, même ajoutés à la semaine en direct, ne suffisent pas pour comparer **une même station** « même heure, même type de jour, avec / sans panne ».

- **En arrêts ciblés**, seules 7 stations ont 3 cas de chaque. La semaine en direct en apporterait environ 5 jours de plus, soit au mieux une vingtaine de stations [estimé].
- **En lignes entières**, 61 stations ont 3 cas de chaque, mais cette définition est trop large : une ligne perturbée à 15 km rend « avec » une station.
- **Ce qui est faisable :** une comparaison **par groupes** (stations proches d'une panne contre les autres, au même créneau et avec la même météo), sur les 15 jours plus la semaine. Les taux ci-dessus restent descriptifs, et l'écart change de signe selon la définition retenue.

---

## 3. Source B : compteurs vélo de Paris

### B1. Métadonnées (API Opendatasoft v2.1)

**[lu] Fiche `comptage-velo-donnees-compteurs`**

| Élément | Valeur |
|---|---|
| Producteur | Direction de la Voirie et des Déplacements, Ville de Paris |
| Licence | **ODbL** |
| Mise à jour | `daily` ; modifié le 04/10/2026 à 11:00 UTC |
| Couverture annoncée | « comptages horaires… sur 13 mois glissants (J-13 mois), mis à jour à J-1 » |
| Source | Partenaire Eco Compteur |
| Champs | `id_compteur`, `nom_compteur`, `id` (site), `name`, `sum_counts`, `date`, `installation_date`, `coordinates`, et plusieurs champs de photos et d'URLs |

**[lu] Alerte qualité affichée en tête de description :** « ATTENTION : Au 08/09/2023, le jeu de données Comptage vélo – Données compteurs subit des dysfonctionnements qui peut altérer la véracité des informations transmises. » Elle est toujours présente en 2026. Autre avertissement **[lu]** : « Les sites bidirectionnels tels que celui de Rivoli cumulent les comptages dans les 2 sens. »

**[mesuré]**
- **1 043 193 enregistrements**, 113 compteurs, 82 sites.
- Période **du 03/09/2025 01:00 au 03/10/2026 21:00 UTC** : les 13 mois glissants sont bien mesurés.
- Liste `comptage-velo-compteurs` : 113 compteurs, tous géolocalisés.

### B2. Taille de l'export

Pas de `Content-Length` : l'export est envoyé en flux. Tailles mesurées pour une journée, puis extrapolées à 396 jours :

| Export d'une journée | Taille / jour [mesuré] | 13 mois [estimé] |
|---|---|---|
| CSV, toutes colonnes | 5 021 607 o | **≈ 1 989 Mo** |
| CSV, toutes colonnes, gzip | 912 647 o | ≈ 361 Mo |
| CSV, 5 colonnes utiles, gzip | 41 344 o | ≈ 16 Mo |
| **Parquet, toutes colonnes** | 130 900 o | ≈ 52 Mo |

Le CSV complet dépassait le budget, mais pas le Parquet. J'ai donc téléchargé **les 13 mois complets en Parquet, un fichier par mois** : **18,8 Mo mesurés** au total, soit 1,3 à 1,5 Mo par mois. L'estimation à partir d'un seul jour était pessimiste.

Une première tentative d'export global en un seul fichier s'est **coupée en cours de flux** (`IncompleteRead`, 3,6 Mo perdus). D'où le découpage par mois, l'écriture dans un fichier `.part` et les nouvelles tentatives de `charger_compteurs_velo()`.

### B3. Inspection [mesuré]

- **Granularité : horaire.** Toutes les dates tombent à hh:00:00. Il y a 2 592 lignes par jour pour 108 compteurs (2 664 et 2 599 lignes les jours de changement d'heure).
- **Fuseau : UTC** (`TIMESTAMP WITH TIME ZONE`, `+00:00`). Les pics tombent à 16–17 h UTC (18–19 h à Paris) et à 7 h UTC.
- **Hypothèse non vérifiée :** `date` désignerait le **début** de l'heure comptée.
- **Compteurs actifs** (au moins un comptage > 0 sur les 7 derniers jours) : **108 sur 113**.
- **Qualité :** 0 doublon, 1 401 valeurs NULL, 39 619 zéros. Médiane de 46 vélos/h, 99e centile à 555, maximum à 1 961.

**Complétude des compteurs :**
- 97,2 % au global, 104 compteurs à ≥ 95 %, 4 compteurs sous 80 % ;
- les moins complets sont « Face 104 rue d'Aubervilliers » (42 %, plus de données après le 19/02/2026) et « 39 quai François Mauriac » (76 %).

**Pannes (zéros ou NULL pendant 24 h ou plus) :** 27 séquences sur 25 compteurs, pour 17 501 h au total.

| Compteur | Période à zéro |
|---|---|
| **106 av. Denfert-Rochereau NE-SO** | à zéro **pendant 8 191 h**, du 05/09/2025 au 12/08/2026 |
| 24 bd Jourdan E-O | 4 837 h |
| 51 bd Masséna SO-NE | 1 813 h |
| 27 bd Diderot E-O | 562 h |
| Porte de Bagnolet, deux sens | 357 h |

**Trous (heures absentes pendant plus de 24 h) :** 240, dont 28 bd Diderot (610 h en juillet-août 2026), 147 av. d'Italie (333 h) et quai de la Tournelle (179 h).

**Valeurs aberrantes :** 10 comptages dépassent 3 fois le 99e centile de leur compteur. Exemples : Grande Armée, 714 vélos/h le 08/09/2026 contre un p99 de 171 ; porte de Charenton, 170 contre 8 ; Cours la Reine, **1 961 vélos/h à 21 h UTC** (nocturne, suspect).

### B4. Recouvrement avec RATPstatus [mesuré]

RATPstatus couvre du 22/04/2024 au 05/10/2026 à 02:58 (heure de Paris). La **période commune exacte** est donc celle des compteurs : **du 03/09/2025 01:00 au 03/10/2026 21:00 UTC**, soit 13 mois.

### B5. Jointure géographique [mesuré]

113 compteurs, comparés aux **1 960 arrêts ferrés** d'`arrets-lignes` (métro, RER, Transilien, tram, etc.), en distance haversine :

| Rayon | Compteurs avec au moins un arrêt ferré |
|---|---|
| 300 m | **93 / 113 (82 %)** |
| 500 m | **113 / 113 (100 %)** |
| 1 km | 113 / 113 (100 %) |

### B6. Faisabilité et première comparaison (septembre 2026) [mesuré]

**Paramètres :**
- RATPstatus de septembre 2026 chargé par `charger_historique_ratpstatus`, **sans transfert** puisque les données étaient déjà dans le cache git ;
- 22 jours ouvrés ;
- 8 h à Paris = comptage de 06:00 UTC ;
- gravités BLOQUANTE + PERTURBEE, ferré, rayon de 500 m ;
- exclusion des couples où le compteur est absent ou à 0 (pannes) : 266 exclus.

| Arrêts pris en compte | Couples « avec » / « sans » | Compteurs ≥ 5 « avec » | **≥ 5 de chaque** | Moyenne brute à 8 h, avec / sans | **Ratio apparié (même compteur) avec / sans** |
|---|---|---|---|---|---|
| Arrêts ciblés | 164 / 2 056 | 11 | **11** | 334 / 316 vélos/h | médiane **0,98** (0,88 à 1,63) ; > 1 pour 4 compteurs sur 11 |
| Arrêts + lignes entières | 552 / 1 668 | 40 | **35** | 351 / 306 vélos/h | médiane **0,99** (0,88 à 1,50) ; > 1 pour 11 sur 35 |

**Lecture descriptive, sans causalité :** l'écart brut (+6 % à +15 %) **disparaît à compteur égal** (médiane ≈ 1). Il venait surtout de l'emplacement des compteurs, ceux proches des lignes souvent perturbées étant des axes plus chargés. Sur un mois, aucun effet visible d'une panne ferrée sur le comptage vélo à 8 h. Avec 13 mois, on aurait environ 13 fois plus de cas [estimé] : il y a donc assez de matière pour une vraie analyse, avec contrôle de la météo et du jour.

### B7. Archivage dans Bronze

Les données de plus de 13 mois disparaissent du portail **[lu]**. Le jour le plus ancien, actuellement le 03/09/2025, sort de la fenêtre **chaque jour**.

1. **Maintenant :** sauvegarde initiale des 13 mois, déjà faite ici (18,8 Mo) : `charger_compteurs_velo(2025-09-03, 2026-10-03)` vers `bronze/compteurs/mois=AAAA-MM/comptages_AAAAMM.parquet`.
2. **Chaque jour**, par Azure Function Timer vers 08:00 UTC, après la mise à jour J-1 : `charger_compteurs_velo(J-1, J-1)` vers `bronze/compteurs/date=AAAA-MM-JJ/`, avec `.meta.json` (URL, sha256, nombre de lignes). On ajoute un instantané de la **liste des compteurs** (`compteurs_liste_AAAAMMJJ.csv.gz`), qui change au fil des aménagements.
3. **Chaque mois :** consolidation du mois précédent en un seul Parquet, pour éviter les petits fichiers. Les données de J-1 pouvant être corrigées, on retélécharge le mois complet une fois et on le compare par sha256.
4. Volume : environ 1,5 Mo par mois en Parquet. Négligeable.

---

## 4. Total téléchargé [mesuré]

| Poste | Octets |
|---|---|
| Kaggle (zip complet) | 13 406 856 |
| RATPstatus, 2–16 décembre 2025 (croissance du cache git) | 67 195 904 |
| RATPstatus, septembre 2026 | **0** (déjà dans le cache git local) |
| Compteurs : 13 Parquet mensuels + liste | 18 861 321 |
| Sondes de taille, export interrompu, nouvelle tentative, Open-Meteo | 9 985 673 |
| Métadonnées (Kaggle, Opendatasoft) | < 0,1 Mo |
| **Total données** | **≈ 109,4 Mo** sur 400 Mo |

Les paquets installés avec pip (`kaggle`, `duckdb`) ne sont **pas comptés** (non mesurés).

Le transfert git de décembre 2025 a coûté environ **4,5 Mo par jour**, contre 0,6 à 0,8 Mo par jour mesurés pour septembre 2026. L'efficacité des deltas varie selon les périodes.

---

## 5. Problèmes rencontrés

1. **Identifiants Kaggle absents de l'environnement ;** le fichier joint a été utilisé sans être recopié (voir encadré). La clé est à régénérer.
2. **Kaggle :**
   - le HEAD de l'URL de téléchargement renvoie 404, d'où l'usage d'une requête Range ;
   - la **description promet des colonnes absentes**, en particulier les bornes libres ;
   - la saturation n'est qu'approximable (≈ 50 % de rappel mesuré).
3. **pandas et pyarrow absents ;** DuckDB installé à la place. DuckDB exige `pytz` pour les `TIMESTAMPTZ` : contourné avec `AT TIME ZONE 'UTC'`.
4. **Opendatasoft :**
   - pas de `Content-Length` sur les exports ;
   - export global coupé en cours de flux (3,6 Mo perdus), corrigé par un découpage mensuel, des fichiers `.part` et de nouvelles tentatives ;
   - coordonnées en type `GEOMETRY` dans le Parquet, lues depuis la liste CSV des compteurs à la place ;
   - CSV avec BOM.
5. **Compteurs :** alerte qualité officielle toujours affichée, 25 compteurs en panne (zéros prolongés), valeurs nocturnes aberrantes, sites bidirectionnels cumulés.
6. **RATPstatus :** 2 fichiers vides en décembre 2025 ; identifiants d'incidents fragmentés (3 028 identifiants pour 1 824 épisodes).

---

## 6. Recommandation

**Sources à garder :**

| Source | Rôle | Période |
|---|---|---|
| **Collecte en direct** (Vélib' + PRIM + météo) | Cœur du projet | La semaine du projet |
| **Kaggle Vélib'** | **Historique Vélib' à 5 min**, mêmes `station_id` que l'API | **02/12 → 16/12/2025** |
| **RATPstatus** | Pannes ferrées en face de Kaggle et des compteurs | 02/12 → 16/12/2025 (fait) et septembre 2026 (fait) ; étendre si besoin à septembre 2025 → octobre 2026 |
| **Compteurs vélo Paris** | « Trafic vélo × pannes » sur 13 mois | **03/09/2025 → 03/10/2026**, **à archiver dès maintenant** |
| Open-Meteo archive | Météo horaire de toutes les périodes historiques | Un appel par période |

**Organisation de l'analyse :**

1. **Vélib' × pannes**, sur 15 jours Kaggle + 7 jours en direct, soit environ 16 jours ouvrés :
   - indicateur principal : **pénurie** (`bikes = 0`) ; la saturation n'est fiable que sur la semaine en direct ;
   - comparaison **par groupes** de stations (proches ou non d'un arrêt ferré touché, BLOQ. + PERT., à 300 m), **au même créneau, sur le même type de jour et avec la même météo** ;
   - **pas de comparaison station par station**, faute de cas (7 stations à 3 cas de chaque en décembre).
2. **Trafic vélo × pannes**, sur 13 mois de compteurs + RATPstatus :
   - comparaison **appariée par compteur**, possible sur 11 à 35 compteurs **par mois** ;
   - premier résultat descriptif : pas d'effet visible (ratio ≈ 0,98–0,99) ;
   - à affiner : heures de pointe, gravité bloquante seule, contrôle de la pluie.
3. **Architecture :**
   - dans Bronze, des chargements uniques (Kaggle, RATPstatus par période, compteurs sur 13 mois) **à côté** de la collecte toutes les 5 min, plus un archivage quotidien des compteurs ;
   - dans Silver, une grille commune ; le **quart d'heure** reste valable, et l'agrégation à l'heure s'impose pour les compteurs ;
   - une colonne `source` pour distinguer l'origine de chaque ligne.

**Faisabilité en une semaine :**
- **Source A + RATPstatus : oui.** Les données sont déjà téléchargées, propres et jointes à 99,7 %. C'est à intégrer au cœur du projet.
- **Source B : à garder en bonus.** Les données sont prêtes (18,8 Mo), mais le nettoyage des compteurs en panne, la gestion des sites bidirectionnels et l'analyse appariée sur 13 mois représentent un second projet. Il faut en revanche **lancer son archivage quotidien dès maintenant**, faute de quoi les mois les plus anciens seront perdus.

Fonctions ajoutées à `collecte_test.py` :

- `charger_historique_kaggle(dossier)` : identifiants lus dans l'environnement, Range pour la taille, pas de nouveau téléchargement si le fichier est présent, `.meta.json` sans secret ;
- `charger_compteurs_velo(date_debut, date_fin)` : un Parquet par mois, fichiers `.part` et nouvelles tentatives, `.meta.json` par fichier.

En ligne de commande : `python collecte_test.py hist-kaggle` et `python collecte_test.py compteurs --debut … --fin …`.
