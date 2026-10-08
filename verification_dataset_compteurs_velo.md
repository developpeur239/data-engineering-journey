# Vérification : « Historique des comptages horaires de vélos et localisation des sites de comptage » (Ville de Paris)

Vérifié le 2026-10-08. Les 20 fichiers ont été téléchargés en local pour l'analyse (338 Mo) puis supprimés. Rien n'a été déposé dans Azure.

## Verdict

**Utilisable avec Data Factory, et la contrainte de 2 à 5 Go est atteignable, mais pas avec « 2 fichiers » : le jeu est publié en 20 zips (un par année et par type).**

| Question | Réponse |
|---|---|
| Liens directs, anonymes, sans redirection | **Oui**, 20 pièces jointes en HTTP 200 |
| Copie Data Factory (HTTP anonyme, Binaire) | **Oui** |
| Tout le jeu entre 2 et 5 Go ? | **Non : 19,17 Go** décompressés (compteurs 6,14 Go + sites 13,03 Go) |
| Un seul fichier suffit-il ? | **Seulement pour les sites** : `sites` 2023 (2,65 Go), 2024 (2,88 Go), 2025 (3,20 Go). Aucun fichier `compteurs` seul n'atteint 2 Go (maximum : 1,93 Go en 2025). |
| Meilleure sélection (grain horaire) | **Compteurs 2023 + 2024 + 2025 = 4,83 Go** (4 833 344 267 octets), 3 zips, 3 années complètes. Compteurs 2024 + 2025 = 3,65 Go (2 zips). |

Réserves importantes : trois formats de fichier différents selon les années (séparateur, encodage, dates), des dates sans fuseau avant 2024 (voir §3), et un volume de lignes très inégal. Détails ci-dessous.

## Identifiants à utiliser dans Data Factory (sélection recommandée : compteurs 2023, 2024, 2025)

| Année | `<id>` de la pièce jointe | URL relative (base `https://opendata.paris.fr`) | Décompressé |
|---|---|---|---|
| 2023 | `2023_comptage_velo_donnees_compteurs_zip` | `/api/explore/v2.1/catalog/datasets/comptage-velo-historique-donnees-compteurs/attachments/2023_comptage_velo_donnees_compteurs_zip` | 1 179 295 725 o |
| 2024 | `2024_comptage_velo_donnees_compteurs_zip` | `/api/explore/v2.1/catalog/datasets/comptage-velo-historique-donnees-compteurs/attachments/2024_comptage_velo_donnees_compteurs_zip` | 1 724 653 331 o |
| 2025 | `2025_comptage_velo_donnees_compteurs_zip` | `/api/explore/v2.1/catalog/datasets/comptage-velo-historique-donnees-compteurs/attachments/2025_comptage_velo_donnees_compteurs_zip` | 1 929 395 211 o |
| **Total** | | | **4 833 344 267 o (4,83 Go)** |

## 1. Liens

Ce que l'API Opendatasoft expose : `GET https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-historique-donnees-compteurs/attachments` liste **20 pièces jointes** (ODbL ; jeu modifié le 20/02/2026).

URL directe de chaque pièce jointe : `https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/comptage-velo-historique-donnees-compteurs/attachments/<id>`

Tous les `HEAD` répondent **HTTP 200, sans redirection** (`content-type: application/zip`, `content-disposition: attachment`, `accept-ranges: bytes`).
**Réserve :** une requête `Range: bytes=0-99` a reçu le fichier complet (HTTP 200, pas 206) : l'en-tête `Accept-Ranges` est annoncé mais pas honoré. Aucune reprise de transfert partielle ; sans conséquence pour une copie Data Factory, mais un téléchargement interrompu repart de zéro.

| `<id>` | Taille compressée (octets) | Décompressée (octets) |
|---|---|---|
| `2016_comptage_velo_donnees_compteurs_zip` | 1 415 753 | 104 306 070 |
| `2016_comptage_velo_donnees_sites_comptage_zip` | 5 374 282 | 343 808 511 |
| `2017_comptage_velo_donnees_compteurs_zip` | 1 983 385 | 145 434 423 |
| `2017_comptage_velo_donnees_sites_comptage_zip` | 7 435 530 | 470 994 582 |
| `2018_comptage_velo_donnees_compteurs_csv_zip` | 1 115 714 | 32 183 460 |
| `2018_comptage_velo_donnees_sites_comptage_csv_zip` | 11 340 079 | 348 356 923 |
| `2019_comptage_velo_donnees_compteurs_csv_zip` | 3 036 681 | 89 806 348 |
| `2019_comptage_velo_donnees_sites_comptage_csv_zip` | 13 416 987 | 349 635 965 |
| `2020_comptage_velo_donnees_compteurs_csv_zip` | 4 348 771 | 161 440 954 |
| `2020_comptage_velo_donnees_sites_comptage_csv_zip` | 16 097 257 | 360 791 545 |
| `2021_comptage_velo_donnees_compteurs_csv_zip` | 6 466 938 | 385 282 001 |
| `2021_comptage_velo_donnees_sites_comptage_csv_zip` | 23 707 487 | 1 217 953 559 |
| `2022_comptage_velo_donnees_compteurs_zip` | 6 924 008 | 389 834 292 |
| `2022_comptage_velo_donnees_sites_comptage_zip` | 23 220 019 | 1 211 657 378 |
| `2023_comptage_velo_donnees_compteurs_zip` | 19 555 342 | 1 179 295 725 |
| `2023_comptage_velo_donnees_sites_comptage_zip` | 37 544 767 | 2 651 379 889 |
| `2024_comptage_velo_donnees_compteurs_zip` | 47 879 302 | 1 724 653 331 |
| `2024_comptage_velo_donnees_sites_comptage_zip` | 33 105 302 | 2 880 508 027 |
| `2025_comptage_velo_donnees_compteurs_zip` | 21 200 803 | 1 929 395 211 |
| `2025_comptage_velo_donnees_sites_comptage_zip` | 52 834 424 | 3 197 852 545 |
| **Total** | **338 002 831** (338 Mo) | **19 174 576 507** (19,17 Go ; 17,86 Gio) |

(Les tailles décompressées viennent de l'index des zips : exactes. Les zips 2018 à 2021 contiennent aussi un dossier `__MACOSX` de quelques centaines d'octets, à ignorer.)

**Copie Data Factory : oui.**

| Élément | Valeur |
|---|---|
| Service lié HTTP : URL de base | `https://opendata.paris.fr` |
| Authentification | Anonyme |
| Jeu de données source | type HTTP, format **Binaire**, compression `None` (garder le `.zip`) |
| URL relative (exemple recommandé) | `/api/explore/v2.1/catalog/datasets/comptage-velo-historique-donnees-compteurs/attachments/2024_comptage_velo_donnees_compteurs_zip` |
| Nom du fichier de sortie | à fixer explicitement (ex. `2024-comptage-velo-donnees-compteurs.zip`) ; le nom vient de `content-disposition`, que Data Factory n'utilise pas |

Une activité Copie par fichier (paramétrer l'URL relative avec l'`<id>`). Je n'ai pas lancé Data Factory : la compatibilité repose sur le comportement standard du connecteur HTTP (200 direct, pas de redirection ni d'authentification).

## 2. Taille et verdict 2–5 Go

| Sélection | Octets décompressés | Go | Dans 2–5 Go ? |
|---|---|---|---|
| Tout `compteurs` (2016–2025) | 6 141 635 054 | 6,14 | non (trop gros) |
| Tout `sites` (2016–2025) | 13 032 941 453 | 13,03 | non |
| Tout le jeu | 19 174 576 507 | 19,17 | non |
| `sites` 2023 seul / 2024 seul / 2025 seul | 2 651 379 889 / 2 880 508 027 / 3 197 852 545 | 2,65 / 2,88 / 3,20 | **oui, un seul fichier** |
| `compteurs` 2025 seul (le plus gros) | 1 929 395 211 | 1,93 | non (< 2 Go) |
| `compteurs` 2024 + 2025 | 3 654 048 542 | 3,65 | oui |
| **`compteurs` 2023 + 2024 + 2025** | **4 833 344 267** | **4,83** | **oui** (limite haute) |
| `compteurs` 2022 à 2025 | 5 223 178 559 | 5,22 | non (dépasse 5 Go) |

**Recommandation :** `compteurs` 2023 + 2024 + 2025 (4,83 Go, grain horaire, 3 années complètes). Si le professeur compte en Gio (2^30), cela fait 4,50 Gio : toujours dans la fourchette.

## 3. Structure

Deux familles de fichiers : **« compteurs »** (un enregistrement par **compteur** et par **heure**, un site pouvant avoir plusieurs compteurs, ex. un par sens) et **« sites »** (un enregistrement par **site** et par **quart d'heure** ; le nom « comptage horaire » de la colonne est trompeur).

### Colonnes

**compteurs** (9 colonnes) : `Identifiant du compteur` (texte, ex. `100003096-101003096`), `Nom du compteur`, `Identifiant du site de comptage`, `Nom du site de comptage`, `Comptage horaire` (nombre de passages de vélos), `Date et heure de comptage`, `Date d'installation du site de comptage`, `Lien vers photo du site de comptage`, `Coordonnées géographiques` (texte `"lat,lon"`, 5 à 6 décimales).

**sites** (6 colonnes, 7 en 2018–2020) : `Identifiant du point de comptage`, `Nom du point de comptage`, `Comptage horaire`, `Date et heure de comptage`, (`Date d'installation du point de comptage` en 2018–2020 seulement), `Lien vers photo du point de comptage`, `Coordonnées géographiques`.

### Trois formats selon les années

| Années | Séparateur | Encodage | Guillemets | Format de date |
|---|---|---|---|---|
| 2016–2017, 2021–2022 (compteurs et sites) | `;` | UTF-8 | non | `2021-01-01T00:00:00` **sans fuseau** |
| 2018–2020 | `;` | UTF-8 | non | `2018-11-29T01:00:00+01:00` (avec décalage) |
| 2023 : compteurs `;`, sites `,` | `;` / `,` | UTF-8 (BOM sur les compteurs) | oui | `2023-06-09 04:30:00.000` **sans fuseau** |
| 2024 | `;` | UTF-8 | oui | `2024-01-02 19:00:00.000 +0100` (avec décalage) |
| 2025 | `,` | **Windows-1252 (pas UTF-8)** | oui | `2025-05-06 14:00:00.000 +0200` |

Autres écarts : le décompte est entier (`3`) ou décimal (`155.0`) selon l'année ; la colonne photo est une liste entre accolades ou crochets (jusqu'à plusieurs liens) dans les fichiers récents, longue et inutile ; 2025 contient des accents encodés en cp1252 (`é` = octet `E9`) : un lecteur UTF-8 échoue dès l'en-tête. **Un notebook ou un flux de données doit donc lire chaque année avec ses propres options** (séparateur, encodage, format de date).

### Exemples (3 lignes réelles, colonnes réduites)

```
# compteurs 2016 (; , sans fuseau)
100003097-SC;105 rue La Fayette E-O;100003097;105 rue La Fayette E-O;3;2016-01-01T00:00:00;;<photo>;48.87773,2.3506
100003097-SC;105 rue La Fayette E-O;100003097;105 rue La Fayette E-O;6;2016-01-01T01:00:00;;<photo>;48.87773,2.3506
100003097-SC;105 rue La Fayette E-O;100003097;105 rue La Fayette E-O;14;2016-01-01T02:00:00;;<photo>;48.87773,2.3506
# compteurs 2024 (; guillemets, avec décalage)
"100044493-101044493";"67 boulevard Voltaire SE-NO";"100044493";"67 boulevard Voltaire";155.0;2024-01-02 19:00:00.000 +0100;2018-06-27 00:00:00.000;{'https://filer.eco-counter-tools.com/...'};"..."
# sites 2022 (quart d'heure)
100003096;97 avenue Denfert Rochereau;0;2022-01-01T00:00:00;<photo>;48.83504,2.33314
100003096;97 avenue Denfert Rochereau;0;2022-01-01T00:15:00;<photo>;48.83504,2.33314
100003096;97 avenue Denfert Rochereau;13;2022-01-01T01:00:00;<photo>;48.83504,2.33314
```

### Dates et fuseau

- **2018–2020 et 2024–2025 : heure locale de Paris avec décalage** (`+01:00` / `+0200`) : conversion en UTC sans ambiguïté.
- **2016–2017 et 2021–2023 : heure locale sans décalage**. Contrôles : le pic du matin tombe à 8 h en janvier et 9 h en juillet, comme dans les fichiers à décalage de 2024 : cela correspond bien à l'heure locale de Paris. **Anomalie :** le 27/03/2022 contient des relevés à `02:00`, heure qui n'existe pas en France (passage à l'heure d'été). Hypothèse : heure locale de Paris, avec des horodatages mal gérés autour des changements d'heure. À traiter en conversion avec le fuseau `Europe/Paris` et à contrôler.
- Dans le fichier 2024, le 27/10/2024 il manque l'heure `02:00 +0100` (la seconde « 2 h » du retour à l'heure d'hiver).
- Le décompte `Comptage horaire` est un **nombre de passages sur l'heure (ou le quart d'heure)** qui commence à l'horodatage (non vérifié dans la documentation).

### Période, compteurs, complétude (lecture intégrale des 20 fichiers)

| Année | Compteurs (fichier compteurs) : lignes / compteurs | Sites : lignes / sites | Remarques |
|---|---|---|---|
| 2016 | 404 064 / 46 | 1 616 256 / 45 | complet |
| 2017 | 560 640 / 64 | 2 242 560 / 48 | complet |
| 2018 | 157 825 / 45 (**40 %** de l'attendu) | 2 271 177 / 65 | **1 789 073 comptes vides** (79 %) dans les sites |
| 2019 | 436 729 / 81 (62 %) | 2 271 305 / 65 | **945 695 comptes vides** (42 %) dans les sites |
| 2020 | 784 339 / 96 (93 %) | 2 314 738 / 72 | |
| 2021 | 1 462 920 / 167 | 5 851 680 / 75 | un site (« Voie Georges Pompidou ») est répété **10 fois** par quart d'heure |
| 2022 | 1 471 680 / 168 | 5 886 720 / 75 | idem |
| 2023 | 860 190 / 101 (97 %) | 3 128 640 / 98 | dernier relevé 30/12 |
| 2024 | 1 505 640 / 179 (96 %) | 2 964 967 / 91 (93 %) | |
| 2025 | 1 502 954 / 172 (99,8 %) | 2 955 727 / 88 (96 %) | arrête au 31/12/2025 : **aucune donnée 2026** |

- **Période totale : 01/01/2016 → 31/12/2025** (heure locale), soit 10 ans.
- **416 compteurs** distincts (tous fichiers compteurs confondus) et **109 sites** distincts dans les fichiers sites ; les compteurs se rattachent à 278 sites.
- Complétude = lignes ÷ (identifiants × durée), approximative : un compteur installé en cours d'année fait baisser le taux sans « trou » réel.
- Valeurs : aucune valeur négative ni non numérique hors comptes vides de 2018–2019 ; maxima suspects en 2022–2024 (6 390 ; 8 190 ; 11 577 passages en une heure) à filtrer. Le maximum 2025 est 999 : à vérifier (plafonnement ?).
- La complétude trouée de 2018–2019 vient des pannes de compteurs ; les compteurs apparaissent et disparaissent d'une année à l'autre : il faut raisonner par compteur actif.

## 4. Cohérence avec vos données

### 4.1 Avec vos stations Vélib'

Je n'ai pas accès à votre table `silver_velib_stations` ; la comparaison utilise `station_information.json` actuel (1 519 stations, même source que votre Bronze) relevé aujourd'hui. Distance à vol d'oiseau, positions des compteurs de 2025.

| | Compteurs (fichier 2025) | Sites (fichier 2025) |
|---|---|---|
| Éléments | 172 (1 position invalide : non évaluable) | 88 |
| **Avec au moins une station Vélib' à moins de 300 m** | **171 sur 172 (99,4 %)**, soit **100 %** des positions valides | **88 sur 88 (100 %)** |
| À moins de 100 m | 84 | 40 |
| Distance médiane à la station la plus proche | 103 m | 107 m |
| Stations à moins de 300 m (médiane / maximum) | 3 / 10 | 3 / 10 |

Conclusion : la jointure **par distance est possible pour tous les compteurs actifs** ; attention aux stations multiples (3 en médiane, jusqu'à 10) : choisir la plus proche, ou agréger les stations dans un rayon. Les compteurs d'anciennes années sont à rejouer avec leurs propres coordonnées.

### 4.2 Avec votre météo horaire

- **Grain :** le fichier `compteurs` est **horaire**, comme votre météo (Open-Meteo, relevés horaires en UTC). Les fichiers `sites` sont au quart d'heure : somme sur l'heure.
- **Conversion en UTC :**
  - années avec décalage (2018–2020, 2024–2025) : conversion directe ;
  - années sans décalage (2016–2017, 2021–2023) : traiter comme heure de Paris avec `Europe/Paris`, puis convertir en UTC ; gérer l'heure fantôme (27/03) et l'heure doublée du retour à l'heure d'hiver (le 30/10/2022 apparaît une seule fois par compteur : 168 lignes à 02h pour 168 compteurs).
- **Recouvrement avec ce que vous avez déjà :** votre Bronze actuel contient les compteurs sur 13 mois glissants (jeu `comptage-velo-donnees-compteurs`, depuis le 03/09/2025). Le jeu historique couvre jusqu'au 31/12/2025 : le recouvrement existe de septembre à décembre 2025 ; à dédoublonner par (compteur, heure).
- Le chevauchement avec vos données Vélib' (collecte depuis octobre 2026) est **nul** pour l'historique : ce jeu sert d'étude vélo/météo longue durée, pas de complément à la collecte Vélib'.

## 5. Limites

- 20 fichiers, trois formats, deux encodages, fuseau absent sur la moitié des années : le pipeline demande du travail de normalisation.
- Aucune donnée en 2026 ; le jeu n'est plus mis à jour (millésimes annuels figés) ; les données récentes passent par votre Bronze (13 mois glissants).
- Les « sites » ont des lignes répétées pour les sites à plusieurs compteurs (2021, 2022) : dédoublonner ou préférer les fichiers `compteurs`.
- Pas de mesure de qualité officielle ; compteurs en panne ou aberrants à filtrer.
- Licence : ODbL (Ville de Paris), à citer.

## 6. Recommandation pour la suite

1. **Pour le professeur :** présenter `compteurs` 2023 + 2024 + 2025 (3 copies Data Factory, 4,83 Go décompressés). Alternative à un seul fichier : `sites` 2024 (2,88 Go) ou `sites` 2025 (3,20 Go).
2. **Bronze :** copie binaire des `.zip` tels quels, un dossier par année, avec un `.meta.json` (URL, date, taille, SHA-256).
3. **Silver :** un lecteur par format d'année (séparateur, encodage cp1252 pour 2025, dates avec ou sans décalage), colonnes utiles seulement (identifiant compteur, site, heure, comptage, latitude, longitude), conversion en UTC, dédoublonnage, indicateur de qualité par compteur actif.
4. **Jointure Vélib' :** station la plus proche à moins de 300 m (ou moyenne des stations du rayon) ; jointure météo à l'heure UTC.
