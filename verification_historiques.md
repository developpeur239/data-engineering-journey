# Vérification des historiques communautaires : Vélib' et RATPstatus

Tests faits le **lundi 5 octobre 2026, entre 11:35 et 12:10 UTC**, avec `curl`, `git` et Python 3.11.

Chaque information est marquée :
- **[mesuré]** : obtenu par une requête ou un calcul sur les fichiers téléchargés ;
- **[lu]** : tiré d'un README, d'un script ou d'un fichier LICENSE.

---

## 0. Accès, méthode et budget de téléchargement

**API GitHub inaccessible** **[mesuré]**. `api.github.com/repos/…` renvoie **HTTP 403**, avec le message « GitHub access to this repository is not enabled for this session ». Les flux `github.com/…/releases.atom` et `…/commits/main.atom` renvoient aussi 403. Ce n'est pas un *rate limit* GitHub, c'est le proxy de la session. L'outil d'accès confirme que seules les **lectures git anonymes** et les fichiers bruts sont servis.

Méthode utilisée, sans jamais cloner un dépôt en entier :

| Besoin | Méthode |
|---|---|
| Dernier commit | `git clone --depth 1 --filter=blob:none` (Vélib') et `--filter=tree:0` (RATPstatus), sans checkout |
| Listing des dossiers | `git ls-tree` (arbres récupérés à la demande) |
| Contenu RATPstatus | `git sparse-checkout` **d'un dossier jour à la fois** (environ 0,6 Mo transférés par jour grâce aux deltas git) |
| README, LICENSE, scripts, tailles | `raw.githubusercontent.com` (GET et HEAD) |
| Zip Vélib' | HEAD, puis lecture du répertoire central du zip par **requête Range** (64 Ko), puis téléchargement complet |

**Budget : dépassé par erreur.** Le total transféré est d'environ **519 Mo**, pour une limite de 300 Mo. Un test de période vide de `charger_historique_velib()`, lancé avec un autre dossier, a **re-téléchargé le zip de 236 Mo** inutilement. La copie a été supprimée et la fonction accepte désormais `zip_existant=` pour l'éviter.

| Poste | Transféré |
|---|---|
| `stations.zip` (Vélib'), téléchargement utile | 236,0 Mo |
| `stations.zip`, **doublon accidentel** | 236,0 Mo |
| git RATPstatus (arbres de 896 jours + 33 jours de contenu) | 45,7 Mo |
| git Vélib', README, LICENSE, HEAD, Range, 16 fichiers bruts | < 2 Mo |
| **Total** | **≈ 519 Mo** (≈ 283 Mo sans le doublon) |

---

## 1. Tableau récapitulatif

| | **A. Historique Vélib'** (lovasoa) | **B. RATPstatus** (wincelau) |
|---|---|---|
| URL | `github.com/lovasoa/historique-velib-opendata`. Fichier : `…/releases/download/**new**/stations.zip` (l'URL `…/latest/…` du README renvoie **404**) | `github.com/wincelau/ratpstatus`, dossier `datas/json/AAAAMMJJ/` |
| Période **[mesuré]** | **26/11/2020 12:59 → 09/04/2021 14:37 UTC** (135 jours) | **22/04/2024 → 04/10/2026** (896 jours) |
| Encore à jour ? | **Non.** Données arrêtées au **09/04/2021**. Asset modifié pour la dernière fois le 07/12/2021, dernier commit le 04/04/2023 (README) | **Oui.** Dernier commit le **05/10/2026 à 03:01** (« Données de la journée 20261004 ») |
| Fréquence annoncée **[lu]** | 15 min (cron `*/15`) | « toutes les 2 minutes environ » |
| Fréquence réelle **[mesuré]** | **21 min** (médiane par station), écarts de 13 à 21 min | **2 min** (720 fichiers par jour) ; 1 min du 10 au 22/05/2024 |
| Format **[mesuré]** | ZIP → **un seul CSV de 818 Mo**, UTF-8 sans BOM, **sans en-tête**, 7 colonnes, **sans identifiant de station** | Un JSON par instantané, **même structure que l'API PRIM** (`disruptions[]`, `lines[]`, `lastUpdatedDate`) + `disruption_id` |
| Volume **[mesuré]** | 236 Mo zippé, 818 Mo décompressé, 10 986 730 lignes | **1,235 Go de JSON brut/mois** (sept. 2026) ; 23 Mo de transfert git/mois ; 0,2–0,5 Mo/jour en tar.xz |
| Complétude **[mesuré]** | **61,1 %** des relevés attendus à 15 min. 175 trous > 1 h. Seulement 7 jours sur 135 complets à 90 % | **≥ 99,9 %** : 890/896 jours ≥ 90 %, 0 jour absent. 3 fichiers vides (0 octet) en septembre 2026 |
| Lien avec mes données | Par nom ou coordonnées uniquement : 92,7 % (nom) / 93,0 % (≤ 20 m) | **Lignes : 100 %** ; **arrêts (`stop_point`) : 99,3–100 %** dans `arrets-lignes` |
| Licence **[lu]** | Code : **GPL-3.0** (LICENSE). Données : non précisée dans le README (source Vélib' Métropole open data) | Code : **AGPL-3.0** (README + LICENSE). Données : issues de PRIM (licence PRIM non vérifiée, pages bloquées) |
| **Verdict** | **KO pour le projet** : arrêté en 2021, incomplet, sans recouvrement avec RATPstatus | **OK** (ferré uniquement, pas de bus) |

---

## 2. Source A : historique Vélib'

### 2.1 Activité

- **[lu]** Le workflow GitHub Actions est programmé toutes les 15 min (`cron: '*/15 * * * *'`). Il télécharge le zip de la release, ajoute une ligne par station et ré-uploade le zip.
- **[lu]** `fetch_data.py` appelle encore l'ancien hôte `velib-metropole-opendata.**smoove.pro**`, alors que l'hôte actuel est `smovengo.cloud`. C'est une **hypothèse non vérifiée** pour expliquer l'arrêt (l'historique des runs Actions est inaccessible, API bloquée).
- **[mesuré]**
  - `git ls-remote` : pas de tag `latest`, un seul tag `new`. **D'où le 404 de l'URL du README.**
  - Derniers commits : 04/04/2023 (README), 27/07/2020 (« Fix data loss on failed upload »). 46 commits au total.
  - HEAD de l'asset : `Content-Length: 236010999`, `Last-Modified: Tue, 07 Dec 2021 09:05:44 GMT`.
  - Répertoire central du zip, lu par Range : un seul membre, `historique_stations.csv`, 817 854 669 octets décompressés, **daté du 2021-04-09 14:37**.

### 2.2 Contenu

Mesures faites en streaming sur les 10 986 730 lignes, en 132 s.

- **Format.** 7 colonnes, sans en-tête : `date` (`AAAA-MM-JJTHH:MMZ`, UTC), `capacity`, `available_mechanical`, `available_electrical`, `station_name`, `station_geo` (`"lat,lon"` entre guillemets, 5 décimales), `operative` (`True`/`False`).
- **Qualité.** 0 ligne mal formée, 0 valeur vide.
- **Stations.** 1 399 noms distincts, 1 406 couples (nom, coordonnées), entre 1 396 et 1 399 stations par relevé.
- **Fréquence.** 7 866 horodatages distincts. Écart médian entre deux relevés d'une même station : **21 min**. Écarts successifs les plus fréquents : 20, 19, 15, 14, 17 et 21 min (délais de démarrage de GitHub Actions).

5 premières lignes :

```
2020-11-26T12:59Z,35,4,5,Benjamin Godard - Victor Hugo,"48.86598,2.27572",True
2020-11-26T12:59Z,55,23,4,André Mazet - Saint-André des Arts,"48.85376,2.33910",True
2020-11-26T12:59Z,20,0,0,Charonne - Robert et Sonia Delauney,"48.85591,2.39257",True
2020-11-26T12:59Z,21,0,1,Toudouze - Clauzel,"48.87930,2.33736",True
2020-11-26T12:59Z,30,3,1,Mairie du 12ème,"48.84086,2.38755",True
```

### 2.3 Trous et complétude

- **Relevés :** 12 871 attendus à 15 min, **7 866 présents, soit 61,1 %**.
- **Par mois** (rapporté à la période réellement couverte) :

| Mois | Complétude |
|---|---|
| 2020-11 | 91,8 % |
| 2020-12 | 67,6 % |
| 2021-01 | **36,5 %** |
| 2021-02 | 59,4 % |
| 2021-03 | 68,9 % |
| 2021-04 | 88,3 % |

- **175 trous de plus d'1 h**, pour 315 h cumulées :
  - **04/02/2021 18:54 → 08/02/2021 14:40 (91,8 h)**
  - 01/12/2020 (3,7 h)
  - 28/01/2021 (3,4 h)
  - 15 et 22/03/2021 (≈ 2 h)
  - **chaque nuit du 9 au 25/01/2021**, entre 00:00 et 02:00 UTC (≈ 1,8 h)
  - plusieurs fins d'après-midi de janvier (≈ 1,7 h)
- 132 jours sur 135 ont au moins un relevé, mais **seulement 7 jours atteignent 90 %** de la grille à 15 min.

### 2.4 Compatibilité avec mes données en direct

Le CSV ne contient **ni `station_id` ni `stationCode`** : `fetch_data.py` les retire. Taux de correspondance mesuré avec `station_information` de 2026 (1 519 stations) :

| Critère | Taux |
|---|---|
| Même nom (normalisé) | 1 304 / 1 406 = **92,7 %** |
| Station actuelle à ≤ 20 m | 1 307 / 1 406 = **93,0 %** (≤ 50 m : 95,3 %) |
| Même nom **et** ≤ 50 m | 1 292 / 1 406 = **91,9 %** |

On peut donc retrouver le `stationCode` ou le `station_id` actuel pour environ 92 % des stations, par un appariement sur le nom et la distance.

---

## 3. Source B : RATPstatus

### 3.1 Activité et structure

- **[mesuré]** HEAD `main` = `4d69a1d`, commité le **05/10/2026 à 03:01:21 +02:00** par « Bot winy » (« Données de la journée 20261004 »). Il y a un commit de données par jour.
- **[lu]** Le README annonce « toutes les 2 minutes environ à partir du 23 avril 2024 ». **[mesuré]** Le premier dossier est le `20240422`, partiel (91 fichiers).
- **[mesuré]** Contenu de `datas/` :

| Dossier | Contenu | Rôle supposé |
|---|---|---|
| `json/` | 896 dossiers `AAAAMMJJ` | Instantanés |
| `jsonlines/` | 883 fichiers `AAAAMMJJ025901_lines.json` | Référentiel des lignes du jour |
| `disruptions_ids/` | 868 fichiers `AAAAMMJJ_disruptions_ids.csv` | Paires d'identifiants |
| `json_userinfos/` | – | – |

- **Nommage [mesuré].** `datas/json/AAAAMMJJ/AAAAMMJJHHMMSS_disruptions.optimized.json`. Les 651 906 noms suivent tous ce motif.
  - Les secondes valent `01` dans 98 % des cas.
  - L'horodatage du nom est en **heure de Paris** : le fichier `…085801` contient `lastUpdatedDate 06:57:15Z`.
- **Journée d'exploitation [mesuré].** Un dossier va de **03:00 à 02:58 le lendemain**, soit **720 fichiers**.
  - Les journées de passage à l'heure d'hiver comptent 25 h, donc 750 fichiers.
  - Du 10 au 22/05/2024, l'intervalle était d'une minute (jusqu'à 1 440 fichiers par jour).

### 3.2 Taille

| Mesure | Valeur | Statut |
|---|---|---|
| Fichier (HEAD sur 15 fichiers) | 20 à 71 Ko | mesuré |
| Journée (5 fichiers × 720) | 26 à 38 Mo | **estimation** |
| **Septembre 2026, JSON brut** | **1 235 218 345 octets ≈ 41 Mo/jour** | mesuré |
| Transfert git | 23 Mo pour 30 jours | mesuré |
| tar.xz | 0,24 Mo (03/06/2024), 0,22 Mo (15/01/2025), 0,50 Mo (01/10/2026) | mesuré |
| Transfert gzip HTTP | facteur ×5,7 (47 114 → 8 258 octets) | mesuré |

**Estimation du volume à partir du mois mesuré :**

| Période | JSON brut | tar.xz | Transfert git | JSON gzip (Bronze fichier par fichier) |
|---|---|---|---|---|
| 1 mois | ≈ 1,2 Go | ≈ 12 Mo | ≈ 23 Mo | ≈ 215 Mo |
| 3 mois | ≈ 3,7 Go | ≈ 36 Mo | ≈ 70 Mo | ≈ 650 Mo |

### 3.3 Trois journées téléchargées

Les journées 03/06/2024, 15/01/2025 et 01/10/2026 sont toutes complètes (720/720 fichiers, 0 erreur JSON). Elles sont stockées en `echantillons/historiques/ratpstatus/ratpstatus_AAAAMMJJ.tar.xz`, chacune avec son `.meta.json`.

| | 03/06/2024 | 15/01/2025 | 01/10/2026 |
|---|---|---|---|
| Perturbations distinctes (`id`) | 329 | 324 | 361 |
| Gravité | BLOQ 34 / PERT 295 | BLOQ 42 / PERT 276 / INFO 6 | BLOQ 34 / PERT 326 / INFO 1 |
| Lignes touchées | 37 | 32 | 41 |
| Modes | Metro, Tramway, RapidTransit, LocalTrain | idem | idem + RailShuttle |
| **Lignes retrouvées dans `arrets-lignes`** | **37/37 (100 %)** | **32/32 (100 %)** | **41/41 (100 %)** |
| **`stop_point` retrouvés** | 176/176 (100 %) | 138/139 (99,3 %) | 237/237 (100 %) |
| Lignes ayant des arrêts ciblés (`stop_point`) | 12/37 | 13/32 | 15/41 |

**Comparaison avec mon échantillon PRIM direct [mesuré] :**

- **Même structure,** même format d'identifiants (`line:IDFM:C01372`, `stop_point:IDFM:…`), mêmes gravités (`BLOQUANTE` / `PERTURBEE` / `INFORMATION`) et mêmes dates `AAAAMMJJTHHMMSS` en heure de Paris.
- **Champs en plus :** `disruption_id` (absent en 2024, présent en 2025-2026).
- **Champs en moins selon les années :**
  - `shortMessage` et `impactedSections` sont absents en 2024 ;
  - `tags` n'est présent que dans 38 % des messages en 2026.
- **Différence majeure : RATPstatus ne garde que le ferré** (métro, RER, Transilien, tram, CDGVAL, funiculaire). **Aucun bus**, alors que le flux PRIM direct est à plus de 90 % du bus.
- **Arrêts touchés : présents**, ce qui rend possible la jointure à 300 m. Mais la majorité des lignes est touchée « en entier » (objet `line`) plutôt qu'à des arrêts précis.

### 3.4 Trous sur un mois complet (septembre 2026)

**[mesuré]** Listing des 30 dossiers via `git ls-tree` : **30/30 jours présents, 720 fichiers chacun**, aucun jour manquant ni incomplet. En revanche, **3 fichiers sont vides** (0 octet, JSON invalide) : `20260904072801`, `20260908151601` et `20260922163001`.

Sur les 896 jours, 6 jours sont sous 90 % :

| Jour | Complétude |
|---|---|
| 22/04/2024 | 13 % (démarrage) |
| 19/08/2024 | 79 % |
| 20/08/2024 | 84 % |
| 21/08/2024 | 87 % |
| 22/08/2024 | 88 % |
| 23/08/2024 | 59 % |

Les trous d'exactement 1 h des 29-30/03/2025 et 28-29/03/2026 correspondent au **passage à l'heure d'été** : ce ne sont pas de vrais trous.

---

## 4. Étape C : période commune et faisabilité

### C1. Période commune complète à ≥ 90 %

**Il n'y en a aucune.** Vélib' s'arrête le **09/04/2021**, RATPstatus commence le **22/04/2024** : il y a **3 ans d'écart, sans aucun recouvrement**. De plus, l'historique Vélib' n'atteint 90 % de complétude que 7 jours sur 135.

### C2. Fenêtre de 2 à 3 mois

**Impossible à définir** avec ces deux sources. La seule fenêtre utilisable pour croiser Vélib' et les pannes est **la semaine de collecte en direct**. Côté pannes seul, la fenêtre la plus récente et complète serait **juillet → septembre 2026** (100 % de complétude, mais sans Vélib' en face).

### C3. Combien de cas sur un mois ? (septembre 2026, RATPstatus)

Le comptage est fait **comme si** l'on disposait de l'historique Vélib' pour cette période, avec les coordonnées des 1 519 stations de 2026. Il répond à la question : le volet pannes produit-il assez de cas ?

**Incidents ferrés** (cause `PERTURBATION`), gravité maximale atteinte **[mesuré]** :

| | BLOQUANTE | PERTURBEE | INFORMATION |
|---|---|---|---|
| Métro | 263 | 2 080 | 17 |
| RER / train | 639 | 2 134 | 0 |
| Tram | 131 | 263 | 2 |
| **Total (`disruption_id` distincts)** | **1 040** | **4 498** | 19 |

**Attention :** le même incident change souvent d'identifiant. 2 198 identifiants n'apparaissent que dans **un seul** instantané. En regroupant par même titre, même jour et présences contiguës (≤ 10 min), on obtient **3 542 épisodes, dont 690 bloquants et 2 842 perturbés**, d'une durée médiane de **66 min** (p75 : 88 min). Les travaux, à part, représentent 48 cas bloquants et 240 perturbés.

**Créneaux « jour ouvré à 8 h »** : 22 jours ouvrés, instantané de 08:00, × 1 519 stations = 33 418 couples (station, jour).

| Incidents actifs à 8 h | Arrêts pris en compte | Créneaux réseau avec au moins 1 station à < 300 m | Couples (station, jour) **avec** / **sans** | Stations avec ≥ 3 créneaux « avec » |
|---|---|---|---|---|
| BLOQUANTE (0,4 par jour) | arrêts ciblés | 3/22 | **57 (0,17 %)** / 33 361 | **0** |
| BLOQUANTE | + lignes entières | 4/22 | 215 (0,64 %) / 33 203 | 3 |
| BLOQ. + PERT. (8,3 par jour) | arrêts ciblés | 21/22 | **821 (2,5 %)** / 32 597 | **109** (47 avec ≥ 5) |
| BLOQ. + PERT. | + lignes entières | 22/22 | 3 274 (9,8 %) / 30 144 | 426 (216 avec ≥ 5) |

**Conclusion C3.** En ne gardant que les incidents **bloquants**, il n'y a **pas assez de cas** pour comparer « même station, même heure, même type de jour, avec ou sans panne » : 57 cas sur un mois, et aucune station avec 3 cas. En incluant **PERTURBEE**, il y a sur 1 mois **109 stations avec au moins 3 cas**, et sur 3 mois environ 3 fois plus. **Ce serait suffisant si l'historique Vélib' existait sur la même période, ce qui n'est pas le cas.**

Sur la seule semaine en direct (5 jours ouvrés), on peut attendre environ 190 couples « avec » (BLOQ. + PERT., arrêts ciblés), mais au plus 1 ou 2 par station. La comparaison devra donc **agréger les stations** (stations proches d'un incident contre les autres, à même heure et même météo) au lieu de comparer une station à elle-même.

### C4. Harmonisation 15 min / 5 min dans Silver

Règle proposée : **tout ramener au quart d'heure UTC, en prenant un seul relevé par quart d'heure pour toutes les sources.**

1. `quart = floor(horodatage_utc, 15 min)`. Pour Vélib' en direct, on part de `lastUpdatedOther` ; pour l'historique, de la colonne `date`, déjà en UTC.
2. **Vélib' :** on garde le **dernier relevé du quart d'heure**. On ne fait ni moyenne ni « au moins un zéro sur 3 relevés ». Sinon, la collecte à 5 min produirait mécaniquement plus de pénuries que l'historique à environ 20 min.
3. **Quarts sans relevé :** valeur `NULL` et indicateur `observe = false`. On ne fait **aucune interpolation**, sauf éventuellement un report du relevé précédent sur un seul quart, signalé `impute = true`.
4. **Pannes (2 min) :** une perturbation est « active pendant le quart » si elle apparaît dans au moins un instantané du quart **et** si l'heure tombe dans une de ses `applicationPeriods`, dates converties de l'heure de Paris vers l'UTC.
5. Une colonne `source` (`direct` / `historique_lovasoa` / `ratpstatus`) dans chaque table Silver permet de filtrer ou de comparer.

---

## 5. Problèmes rencontrés

1. **API GitHub bloquée par le proxy** (403, ce n'est pas un rate limit), ainsi que les flux `.atom`. Les dates de release et de commit ont été obtenues **par git** et par les en-têtes HTTP.
2. **URL documentée cassée.** `releases/download/latest/stations.zip`, donnée dans le README, renvoie 404 ; le bon tag est `new`.
3. **Budget de 300 Mo dépassé** (environ 519 Mo) à cause d'un re-téléchargement accidentel du zip, voir §0.
4. **Le zip Vélib' (236 Mo) n'est pas commité :** il dépasse la limite GitHub de 100 Mo par fichier. Il reste en local dans `echantillons/historiques/velib/`, avec son `.meta.json`. Je ne pouvais pas modifier `.gitignore` (hors périmètre autorisé) : pensez à l'y ajouter ou à le supprimer.
5. **Historique Vélib' :** pas d'en-tête, pas d'identifiant de station, horodatage de collecte et non de relevé (`TODO: use last_reported ?` dans le code). Il faut apparier les stations par nom et distance.
6. **RATPstatus :** 3 fichiers vides par mois, identifiants de perturbation instables (un incident = plusieurs `disruption_id`), pas de bus, journée de 03:00 à 03:00 en heure de Paris.

---

## 6. Recommandation

**RATPstatus : oui.** Il faut l'utiliser comme **historique des pannes ferrées**, de préférence sur **juillet → septembre 2026** (3 mois récents, 100 % complets, format identique à PRIM). Il sert à :

- caractériser les pannes (fréquence par ligne et par heure, durée réelle, part de bloquantes) ;
- choisir les seuils (gravité, 200/300/500 m) avant même la semaine de collecte ;
- prolonger la série de pannes au-delà de la semaine en direct, sans changer de parseur.

**Historique Vélib' (lovasoa) : non.** Il est arrêté depuis avril 2021, complet à 61 %, sans identifiant de station, et **sans aucun recouvrement** avec RATPstatus. Il ne permet donc pas l'analyse « lundi 8 h avec / sans panne ». Il peut tout au plus servir de **profil de référence 2020-2021** (heure × jour, par station appariée), avec la mise en garde Covid / couvre-feu de l'hiver 2020-2021. Une autre source d'historique Vélib' 2024-2026 serait nécessaire ; je n'en ai **pas vérifié**.

**Changements d'architecture :**

1. **Bronze : deux modes d'ingestion vers le même conteneur.**
   - `bronze/ratpstatus/date=AAAA-MM-JJ/ratpstatus_AAAAMMJJ.tar.xz`, avec un `.meta.json` par jour. C'est un **chargement unique** par `charger_historique_ratpstatus()`, qui ne transfère qu'environ 70 Mo pour 3 mois via git partiel.
   - Collecte directe à 5 min, inchangée : `bronze/prim/…`, `bronze/velib/…`.
   - Optionnel : `bronze/velib_historique/stations.zip`, chargé une fois.
2. **Silver :**
   - un parseur commun PRIM / RATPstatus (même JSON) ;
   - dédoublonnage des perturbations par (titre, ligne, présences contiguës) ;
   - grille commune au quart d'heure (§C4) ;
   - colonne `source`.
3. **Gold :**
   - indicateurs de pannes sur 3 mois (ferré) ;
   - indicateurs Vélib' × pannes **uniquement sur la semaine en direct**, en comparant des groupes de stations plutôt qu'une station à elle-même ;
   - le cas échéant, profil de référence Vélib' 2020-2021 présenté séparément.

Fonctions ajoutées à `collecte_test.py` :

- `charger_historique_velib(date_debut, date_fin, dossier, zip_existant=None)` ;
- `charger_historique_ratpstatus(date_debut, date_fin, dossier, cache_git=None)`.

En ligne de commande : `python collecte_test.py hist-ratpstatus --debut 2026-07-01 --fin 2026-09-30`.
