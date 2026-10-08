# Vérification : `lovasoa/historique-velib-opendata`, release « new » (`stations.zip`)

Vérifié le 2026-10-08 (≈ 08:00 UTC). Fichier téléchargé en local pour l'analyse, puis supprimé. Rien n'a été déposé dans Azure.

## Verdict

**Lien et données : utilisables. Contraintes du cours : deux écarts importants.**

| Critère | Résultat |
|---|---|
| Copie Data Factory (HTTP anonyme, Binaire) | **Oui** |
| Taille décompressée entre 2 et 5 Go (consigne du professeur) | **Non : 817 854 669 octets (0,82 Go).** Le zip fait 236 010 999 octets (225 Mo). Hors fourchette. |
| Période annoncée : déc. 2019 → avril 2021 | **Faux : 2020-11-26 12:59 UTC → 2021-04-09 14:37 UTC** (environ 4,5 mois, pas 16). |
| Relevés ~15 min | **Médiane 21 min, moyenne 24,5 min**, avec un trou de 3,8 jours (5 → 7 fév. 2021). |
| Identifiant de station | **Aucun** (nom + coordonnées seulement). |

Si votre professeur exige 2 à 5 Go, ce fichier seul ne suffit pas. Il faudrait le compléter, par exemple avec la release `latest` (non analysée ici) ou une autre source. Techniquement, il est propre : 10 986 730 lignes, aucune valeur manquante.

## 1. Lien

URL testée : `https://github.com/lovasoa/historique-velib-opendata/releases/download/new/stations.zip`

| Étape | Code | Détail |
|---|---|---|
| Requête initiale | **302 Found** | redirige vers `https://release-assets.githubusercontent.com/github-production-release-asset/229592966/…` |
| URL finale | **200 OK** | `Content-Length: 236010999` ; `Content-Type: application/octet-stream` ; `Content-Disposition: attachment; filename=stations.zip` ; **`Accept-Ranges: bytes`** |
| Requête partielle `Range: bytes=0-99` | **206 Partial Content** | `Content-Range: bytes 0-99/236010999` |

- Taille réelle téléchargée : **236 010 999 octets** (identique à l'annonce de 225 Mo ; SHA-256 `ccdb67732d0cd69f5611d9c070c03d7f5fb3b0e272fc9f31632cdaaab1e7a01c`). Téléchargement en 3 secondes.
- La redirection mène à un **autre domaine** (`release-assets.githubusercontent.com`) avec une adresse **signée et valable environ une heure** : ne copiez jamais l'adresse finale, utilisez toujours l'adresse GitHub d'origine, qui est stable.

**Activité Copie Data Factory : oui**, le connecteur HTTP suit les redirections.

| Élément | Valeur |
|---|---|
| Service lié HTTP : URL de base | `https://github.com` |
| Authentification | Anonyme |
| URL relative (jeu de données source, type HTTP, format **Binaire**) | `/lovasoa/historique-velib-opendata/releases/download/new/stations.zip` |
| Compression | `None` pour garder le `.zip` tel quel dans Bronze (recommandé) ; `ZipDeflate` pour obtenir directement le CSV (817 Mo) |

À noter : je n'ai pas lancé Data Factory moi-même ; la compatibilité repose sur le comportement standard du connecteur HTTP (redirection suivie, `Accept-Ranges` présent). Un essai à vide avec « Aperçu des données » ou une exécution réelle le confirmera. Autre point : GitHub peut limiter les téléchargements anonymes très fréquents ; un chargement unique est sans risque.

## 2. Taille et contenu du zip

| Élément | Valeur |
|---|---|
| Fichiers dans le zip | **1** : `historique_stations.csv` (daté du 2021-04-09 14:37) |
| Taille décompressée | **817 854 669 octets** (780 Mio, 0,82 Go) |
| Nombre de lignes | **10 986 730** (aucun en-tête : toutes les lignes sont des données) |

## 3. Structure

CSV UTF-8, séparateur virgule, guillemets doubles autour des champs contenant une virgule, **sans ligne d'en-tête**. Colonnes (d'après le README du dépôt, vérifiées sur les valeurs) :

| # | Colonne | Type | Exemple | Remarque |
|---|---|---|---|---|
| 1 | `date` | texte ISO `AAAA-MM-JJTHH:MMZ` | `2020-11-26T12:59Z` | **UTC** (suffixe `Z`), précision à la **minute** |
| 2 | `capacity` | entier | `35` | capacité de la station |
| 3 | `available_mechanical` | entier | `4` | vélos mécaniques |
| 4 | `available_electrical` | entier | `5` | vélos électriques |
| 5 | `station_name` | texte | `Benjamin Godard - Victor Hugo` | même libellé que `name` du GBFS actuel |
| 6 | `station_geo` | texte `"lat,lon"` | `"48.86598,2.27572"` | **une seule colonne** contenant les deux coordonnées, 5 décimales |
| 7 | `operative` | texte `True` / `False` | `True` | 10 769 264 `True` ; 217 466 `False` |

Exemples réels (3 lignes, début du fichier) :

```
2020-11-26T12:59Z,35,4,5,Benjamin Godard - Victor Hugo,"48.86598,2.27572",True
2020-11-26T12:59Z,55,23,4,André Mazet - Saint-André des Arts,"48.85376,2.33910",True
2020-11-26T12:59Z,20,0,0,Charonne - Robert et Sonia Delauney,"48.85591,2.39257",True
```

Profil complet (lecture en flux de l'intégralité des 10,99 M de lignes) :

| Mesure | Résultat |
|---|---|
| Première / dernière date | 2020-11-26T12:59Z / 2021-04-09T14:37Z |
| Horodatages distincts | 7 866 (1 396 à 1 399 stations par horodatage) |
| Stations distinctes | **1 406** couples (nom, position) ; 1 399 noms ; 1 404 positions |
| Valeurs manquantes / non numériques / négatives | 0 / 0 / 0 |
| Jours couverts | 132 sur 135 : **aucun relevé les 5, 6 et 7 février 2021** |
| Intervalle entre relevés (min) | 5 % : 10 ; 25 % : 15 ; **médiane : 21** ; 75 % : 28 ; 95 % : 51 ; 99 % : 70 |
| Intervalles > 30 min / > 60 min / > 6 h | 1 547 / 175 / **1** (5 506 min, du 04/02 au 08/02 14:40 UTC) |
| Relevés par jour | médiane 60 ; maximum 92 ; la cadence de 15 min (96 par jour) n'est jamais atteinte |

Anomalies repérées :
- **64 762 lignes avec `capacity = 0`** (stations hors service) ; 2 036 lignes avec **vélos > capacité** (ex. capacité 34, 28 mécaniques + 7 électriques).
- Au moins une position invalide : `48.88500,48.88500` pour « Arago - Paul Lafargue ».
- 7 noms ont deux positions différentes (stations déplacées ou doublons de nom : « Université », « Place de l'Europe », etc.).
- La date est-elle l'heure de collecte ou celle du dernier relevé de la station ? Non indiqué : à traiter comme heure de relevé approximative.

## 4. Cohérence avec votre Silver

### 4.1 Tableau de correspondance → `silver_velib_status`

| Colonne Silver | Source (ce fichier) | Conversion / limite |
|---|---|---|
| `station_id` | **absent** | Pas d'identifiant. Il faut le déduire par nom ou position (§4.2) vers `stationCode` ou `station_id` actuel. |
| `horodatage_releve_utc` | `date` | Texte ISO UTC à la minute : lecture directe en timestamp UTC (retirer le `Z`, ou le garder avec le format `yyyy-MM-dd'T'HH:mm'Z'`). Aucune conversion de fuseau. |
| `horodatage_collecte_utc` | **absent** | NULL, ou égal à `date` si vous considérez que c'est la collecte. |
| `velos_mecaniques` | `available_mechanical` | Direct (entier). |
| `velos_electriques` | `available_electrical` | Direct (entier). |
| places libres | `capacity − (mécaniques + électriques)` | Calculable, voir §4.3. |
| booléen « installé » | **absent** | Non fourni ; `operative` n'est pas la même notion. |
| booléen « location » | `operative` | Approximation (`True` → 1). |
| booléen « retour » | `operative` | Approximation (`True` → 1). |
| `fichier_source` | nom du CSV | Fourni par votre pipeline (`historique_stations.csv`, ajouter le zip d'origine). |
| `date_releve` | dérivée de `date` | Garder la même règle que pour vos relevés actuels (date UTC ou date de Paris). |
| (position) | `station_geo` | À scinder en `lat` et `lon` (décimaux) avant la jointure. |
| (capacité) | `capacity` | Colonne utile, absente de `silver_velib_status`. |

Autres écarts : pas de ligne d'en-tête (à déclarer dans le jeu de données ou le notebook) ; fréquence irrégulière (médiane 21 min, contre 5 min dans votre collecte actuelle) ; `operative` est une chaîne `True`/`False`.

### 4.2 Correspondance des stations avec vos stations actuelles

Aucun identifiant dans le fichier : correspondance mesurée **par nom puis par position**, contre `station_information.json` relevé aujourd'hui (1 519 stations).

| Critère (sur les 1 406 stations du fichier) | Stations retrouvées | Taux |
|---|---|---|
| Nom identique (casse, accents et tirets normalisés) | 1 304 | **92,7 %** |
| Position à moins de 50 m d'une station actuelle | 1 340 | **95,3 %** |
| Nom **et** position | 1 292 | 91,9 % |
| **Nom ou position** | **1 352** | **96,2 %** |
| Aucun des deux | 54 | 3,8 % |

- Sens inverse : **1 336 stations actuelles sur 1 519 (88 %)** ont une station historique à moins de 50 m ; **environ 180 stations actuelles n'ont aucun historique** (ouvertures postérieures à avril 2021).
- Les 54 stations sans correspondance sont surtout des **déplacements ou renommages** (ex. « Alésia - Suisses » : la plus proche aujourd'hui est à 98 m sous un autre nom) ; une position invalide en fait partie.
- **Recommandation :** jointure par **plus proche voisin à moins de 50 m**, avec le nom en contrôle ; rejeter ou examiner à la main les doublons de nom à deux positions.

### 4.3 Places libres calculables ?

**Oui**, par `capacity − available_mechanical − available_electrical`. Précautions :
- 64 762 lignes ont `capacity = 0` (station hors service) : mettre `places_libres` à NULL plutôt que 0.
- 2 036 lignes ont plus de vélos que de capacité : le résultat serait négatif ; le ramener à 0 (`max(0, …)`) ou à NULL, et les compter dans un contrôle qualité.
- Pénurie (0 vélo) : 475 817 lignes (4,3 %) ; saturation (0 place libre) : 137 443 lignes dont 64 762 sont des `capacity = 0` à exclure. Calcul à faire sur les lignes `operative = True` seulement.

## 5. Limites

- Période et volume très inférieurs à l'annonce ; la période se recoupe avec la fenêtre de votre collecte actuelle (2026) ? **Non** : ce sont deux périodes distinctes, sans recouvrement.
- Cadence irrégulière (≈ 21 min) : pour des indicateurs par heure, prévoir 2 à 4 relevés par heure et station, parfois zéro. Le trou du 5 au 7 février 2021 est à signaler.
- Licence GPL-3.0 annoncée pour le dépôt, **non vérifiée ici** ; les données d'origine viennent de l'open data Vélib' Métropole (le README renvoie à velib-metropole.fr). À citer dans le rapport du projet.
- Je n'ai pas analysé la release `latest` : elle contient sans doute une période plus récente, donc potentiellement plus volumineuse.

## 6. Recommandation pour le notebook 06 (Bronze → Silver)

1. **Bronze :** copie binaire du `.zip` (Data Factory, voir §1), avec un fichier `.meta.json` (URL d'origine, date, taille, SHA-256).
2. **Lecture :** CSV sans en-tête, schéma explicite (7 colonnes), `date` en timestamp UTC, `station_geo` scindé en latitude et longitude.
3. **Silver :** jointure des stations par plus proche voisin < 50 m vers vos stations actuelles ; ajouter une colonne `source` (`lovasoa_2020_2021`) ; `places_libres` calculé et borné ; marquer `operative` comme proxy de « location / retour ».
4. **Indicateurs horaires :** reporter le dernier relevé connu sur l'heure, sans combler le trou du 5 au 7 février 2021 (le marquer en « donnée absente »).
5. **Si l'exigence de 2 à 5 Go est ferme :** ce jeu seul (0,82 Go) ne la remplit pas ; l'associer à une autre source ou à la release `latest`, après vérification de sa taille.
