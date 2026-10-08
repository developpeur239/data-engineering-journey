# Vérification : « 6 months of Vélib' usage » (bfontaine, 2017)

Vérifié le 2026-10-08 (≈ 07:45 UTC). Rien n'a été déposé dans Azure ; aucun fichier de données n'a été téléchargé (les liens sont morts, voir §1).

## Verdict

**NON utilisable en l'état : les deux fichiers de données répondent HTTP 404.** Une activité Copie Data Factory échouerait.

- La page de description existe toujours (HTTP 200), mais les deux liens qu'elle publie sont cassés.
- Je n'ai trouvé aucune copie : ni redirection, ni autre chemin chez l'auteur, ni miroir (recherche web). Les archives (Wayback Machine) étaient inaccessibles au moment du test (HTTP 429 puis « Temporarily Offline »), donc **je ne peux pas dire si une copie archivée existe**.
- Tout ce qui suit sur la structure vient de la **page de l'auteur, non vérifiée sur les vrais fichiers**. Les volumes (322 Mo, 4,4 Go, 43,9 M lignes, 1 229 stations) et les dates ne sont pas confirmés.
- Les deux contrôles « existe-t-il une correspondance avec les stations actuelles ? » et « mêmes indicateurs possibles ? » sont répondus de façon **théorique**, avec une seule preuve réelle (§3.3).

Recommandation : ne pas bâtir le notebook 06 sur ce dataset tant que le fichier n'est pas retrouvé. Écrire à l'auteur (page https://data.bfontaine.net/ → liens GitHub `bfontaine` / Twitter `@bfontn`) pour demander le nouvel emplacement. En attendant, voir §5.

## 1. Liens

Résultats mesurés (`curl -I`, `curl -r 0-99`, redirections suivies).

| URL | Code HTTP | Redirections | Content-Length | Content-Type | Accept-Ranges |
|---|---|---|---|---|---|
| `https://bfontaine.net/dataset/velibs/disponibilities.jsons.gz` | **404** | aucune | absent (page d'erreur HTML d'environ 564 octets) | `text/html; charset=UTF-8` | absent |
| `https://bfontaine.net/dataset/velibs/stations.jsons.gz` | **404** | aucune | absent | `text/html; charset=UTF-8` | absent |
| `https://data.bfontaine.net/datasets/6-months-of-velibs-usage.html` (page) | 200 | aucune | non communiqué (réponse compressée) | `text/html; charset=utf-8` | `bytes` (sans objet pour les données) |

- Variantes essayées, toutes en 404 : `http://` au lieu de `https://`, `data.bfontaine.net/dataset/velibs/…`, `data.bfontaine.net/datasets/velibs/…`, `data.bfontaine.net/velibs/…`. Le dossier `https://bfontaine.net/dataset/` répond aussi 404.
- Serveur : Apache avec PHP 8.3. La page 404 est servie par le site ; le test de requête partielle (`Range: bytes=0-99`) a reçu la page d'erreur complète (564 octets) : **requêtes partielles non évaluables**, faute de fichier.
- La page de l'auteur date du 25/12/2017 ; les liens n'ont pas été mis à jour.

**Utilisable par une activité Copie Data Factory (source HTTP, anonyme, Binaire) ?** Non, aujourd'hui. Si l'auteur remet les fichiers au même endroit, la configuration serait :

| Élément | Valeur |
|---|---|
| Service lié HTTP | URL de base `https://bfontaine.net`, authentification **Anonyme** |
| Jeu de données | format **Binaire**, compression **None** (garder le `.gz` tel quel dans Bronze), type de source HTTP |
| URL relative (disponibilités) | `/dataset/velibs/disponibilities.jsons.gz` |
| URL relative (stations) | `/dataset/velibs/stations.jsons.gz` |

À confirmer lors de la reprise : Content-Length (322 Mo environ annoncés, sans risque pour Data Factory) et Accept-Ranges (utile seulement pour reprendre un transfert interrompu).

## 2. Structure

Non vérifiée sur fichier réel (téléchargement impossible). Schéma **tel que documenté par l'auteur** (format NDJSON compressé en gzip, une ligne = un objet JSON).

### stations.jsons.gz (annoncé : 107 Ko, 536 Ko décompressé, 1 229 stations)

| Champ | Type | Remarque (selon l'auteur) |
|---|---|---|
| `datasetid` | texte | constante `stations-velib-disponibilites-en-temps-reel` |
| `fields.number` | entier | numéro de la station (ex. 21107) : **c'est ce qui correspond à `stationCode`** (voir §3.3) |
| `fields.name` | texte | `"21107 - SINCHOLLE (CLICHY)"` : numéro, tiret, nom en majuscules |
| `fields.address` | texte | adresse en majuscules |
| `fields.bike_stands` | entier | capacité (nombre de bornes) |
| `fields.bonus` | texte | `"True"` / `"False"` (chaîne, pas booléen) |
| `fields.banking` | booléen | toujours `true` |
| `fields.contract_name` | texte | toujours `"Paris"` |
| `fields.position` | tableau de 2 décimaux | **[latitude, longitude]** (WGS84) |
| `geometry` | objet GeoJSON | `coordinates` = **[longitude, latitude]** (ordre inverse de `position`), `type` = `Point` |
| `recordid` | texte | empreinte hexadécimale |
| `_id` | entier | **identifiant interne, clé de jointure avec les disponibilités** |

Exemple documenté (1 seule ligne ; je n'ai pas pu en extraire 3) :
`{"datasetid":"stations-velib-disponibilites-en-temps-reel","fields":{"address":"RUE BERTRAND SINCHOLLE - 92110 CLICHY","bike_stands":23,"bonus":"False","contract_name":"Paris","name":"21107 - SINCHOLLE (CLICHY)","number":21107,"banking":true,"position":[48.899359637,2.3040405607]},"geometry":{"coordinates":[2.3040405607,48.899359637],"type":"Point"},"recordid":"2201fad6a9d960cd567403ce5e9fbfdd3801f2dd","_id":1}`

### disponibilities.jsons.gz (annoncé : 322 Mo, 4,4 Go décompressé, 43,9 M lignes)

| Champ | Type | Remarque (selon l'auteur) |
|---|---|---|
| `station_id` | entier | **= `_id` du fichier des stations, PAS le numéro de station** |
| `last_update` | texte | `"2017-08-07 22:09:36+02:00"` |
| `bike_stands` | entier | **nombre de bornes libres** (le nom prête à confusion) |
| `bikes` | entier | nombre de vélos disponibles |
| `status` | texte | `"OPEN"` ou `"CLOSED"` (seules valeurs annoncées) |

Exemple documenté : `{"station_id":39,"last_update":"2017-08-07 22:09:36+02:00","bike_stands":23,"bikes":10,"status":"OPEN"}`.
L'auteur précise que `bike_stands + bikes` = capacité de la station.

### Horodatages : ce que le format implique

- **Texte ISO 8601 avec décalage**, en secondes (aucune fraction annoncée), **pas** un entier Unix.
- Heure locale de Paris avec décalage explicite : `+02:00` en été, `+01:00` après le 29/10/2017. **Le fichier mélange donc deux décalages** ; il faut les lire comme des instants (conversion en UTC) et jamais comme des heures « naïves ».
- Valeurs de statut : `OPEN`, `CLOSED` (d'après la page ; non recensé sur les données).

### Ce que je n'ai pas pu calculer

Nombre réel de lignes, première et dernière date, nombre de stations distinctes dans les disponibilités, `status` réellement présents, valeurs manquantes, doublons.

Un point à contrôler en priorité : 43,9 M lignes sur environ 1 229 stations et 6 mois font **environ 195 lignes par station et par jour**, soit une ligne toutes les 7 minutes en moyenne, alors que l'auteur dit avoir interrogé la source **chaque minute** (≈ 1 440 lignes par jour). Le fichier contient donc probablement **seulement les changements d'état**, ou comporte des trous. Hypothèse, non vérifiée. Si c'est le cas, il faudra reconstituer l'état de chaque heure en reportant la dernière valeur connue avant de calculer les indicateurs.

## 3. Cohérence avec vos données

### 3.1 Vos données actuelles (relevées en direct aujourd'hui)

- `station_information.json` : 1 519 stations ; champs `station_id` (entier long, ex. 213688169), `stationCode` (texte, ex. `"16107"`), `name`, `lat`, `lon`, `capacity`.
- `station_status.json` : `station_id`, `stationCode`, `num_bikes_available`, `num_bikes_available_types` (`[{"mechanical":10},{"ebike":2}]`), `num_docks_available`, `is_installed`, `is_renting`, `is_returning` (0/1), `last_reported` (**entier Unix en secondes, UTC**).
- Table Silver `silver_velib_status` : `station_id`, `horodatage_releve_utc`, `horodatage_collecte_utc`, `velos_mecaniques`, `velos_electriques`, places libres, booléens installé / location / retour, `fichier_source`, `date_releve`.

### 3.2 Tableau de correspondance 2017 → Silver

| Colonne Silver | Champ 2017 | Conversion / limite |
|---|---|---|
| `station_id` | `station_id` (= `_id` du fichier stations) → `fields.number` | **Pas directement compatible** : le `station_id` actuel est un entier long différent. Il faut passer par le numéro de station (voir §3.3). Recommandation : ajouter une colonne `station_code` à Silver et clé commune = `stationCode`. |
| `horodatage_releve_utc` | `last_update` | Lire le texte avec son décalage, convertir en **UTC**, type timestamp. |
| `horodatage_collecte_utc` | **absent** | NULL (le jeu ne donne pas l'heure de collecte). |
| `velos_mecaniques` | `bikes` | **tous** les vélos sont mécaniques en 2017 (pas de distinction dans le jeu). |
| `velos_electriques` | **absent** | 0 (le réseau d'alors n'en comptait pas, d'après l'auteur : `bikes` est un total) ; à marquer comme valeur déduite. |
| places libres | `bike_stands` | Renommer : c'est un nombre de **bornes libres**, malgré son nom. |
| booléen « installé » | **absent** | Valeur supposée 1 (pas d'information ; `CLOSED` ne dit pas « désinstallé »). |
| booléen « location » | `status` | `OPEN` → 1 ; `CLOSED` → 0 (approximation). |
| booléen « retour » | `status` | `OPEN` → 1 ; `CLOSED` → 0 (approximation). |
| `fichier_source` | nom du fichier chargé | Alimenté par le pipeline (`disponibilities.jsons.gz`). |
| `date_releve` | dérivée de `horodatage_releve_utc` | Date UTC (ou date de Paris selon votre règle actuelle, à garder identique pour les deux sources). |
| (capacité) | `bike_stands + bikes`, ou `fields.bike_stands` du fichier stations | Colonne absente de `silver_velib_status` ; utile en dimension station. |

Autres écarts : fréquence différente (état toutes les minutes ou à chaque changement, contre un instantané toutes les 5 minutes aujourd'hui) ; types (texte ISO contre entier Unix) ; `bonus` est une chaîne `"True"`/`"False"`.

### 3.3 Identifiants de stations : une seule preuve réelle

Je n'ai pas le fichier des stations, donc **aucun taux de correspondance par numéro ni par position GPS ne peut être calculé**. J'ai seulement testé la station donnée en exemple par l'auteur, contre le GBFS actuel (relevé du 2026-10-08) :

| | 2017 (page de l'auteur) | Aujourd'hui (`station_information`) |
|---|---|---|
| Numéro | `number` = 21107 | `stationCode` = `"21107"` |
| Nom | « 21107 - SINCHOLLE (CLICHY) » | « Bertrand Sincholle - Henri Barbusse » |
| Position | 48.899359637, 2.3040405607 | 48.89925982, 2.30422944 |
| Capacité | 23 | 23 |
| Écart de position | | **≈ 18 m** (sous le seuil de 50 m) |

- Le numéro 2017 se retrouve **tel quel** dans `stationCode` pour cette station, avec la même capacité. C'est un indice favorable, pas une preuve générale (un seul cas).
- Les noms diffèrent (casse, préfixe numérique, libellé de la rue) : **ne pas joindre sur le nom**.
- Dans les relevés actuels, les 1 519 `stationCode` sont tous numériques (`10003` … `92008`), donc la jointure par numéro est techniquement possible.
- À calculer dès que le fichier est disponible : taux de numéros 2017 retrouvés dans `stationCode`, puis, pour les non retrouvés, plus proche voisin à moins de 50 m. Le réseau actuel (1 519 stations) est plus grand que celui de 2017 (1 229), donc au mieux 100 % des stations 2017 retrouvées, mais environ 290 stations actuelles n'ont aucun historique 2017. Les stations déplacées, fermées ou rebaptisées dans l'intervalle sont à prévoir.

### 3.4 Mêmes indicateurs possibles ?

| Indicateur | Faisable ? | Condition |
|---|---|---|
| Pénurie (0 vélo) | Oui | `bikes = 0` (et `status = OPEN`, pour ne pas compter une station fermée) |
| Saturation (0 place libre) | Oui | `bike_stands = 0` (champ « bornes libres », voir ci-dessus) et `OPEN` |
| Par station et par heure | Oui, sous réserve | Heure de Paris obtenue après conversion UTC ; si le fichier ne contient que les changements d'état (voir §2), reporter la dernière valeur connue avant d'agréger, sinon les taux seront faux |
| Vélos électriques | Non | absents en 2017 |
| Croisement avec les pannes ferrées | À vérifier | dépend de la période couverte par vos données de perturbations (juin–novembre 2017) : probablement hors de la couverture de votre source PRIM, à contrôler |
| Météo | Oui | l'archive Open-Meteo couvre 2017 |

## 4. Limites

- Données non téléchargeables : aucune statistique réelle (lignes, dates, stations, statuts).
- Schéma issu de la documentation de l'auteur, de 2017 ; non confronté aux fichiers.
- Réseau de 2017 (JCDecaux, environ 1 229 stations) différent du réseau actuel (Vélib' Métropole, 1 519 stations) : les périodes ne se recouvrent pas, ce jeu serait une **période d'étude distincte**, pas un complément de vos données récentes.
- Licence annoncée : Licence Ouverte Etalab 1.0 (donnée d'origine JCDecaux / Ville de Paris) ; la page cite aussi la licence JCDecaux. À reprendre dans le rapport du projet.

## 5. Recommandation pour le futur notebook 06 (Bronze → Silver)

1. **Ne pas intégrer ce jeu tant que les fichiers ne sont pas rouverts.** Écrire à l'auteur ou chercher une copie archivée (Wayback Machine, à retester plus tard).
2. Si les fichiers reviennent : ingérer dans Bronze en **binaire, `.gz` conservé**, avec un fichier `.meta.json` (URL, date, taille, SHA-256), puis lancer un profilage d'abord (lignes, dates, stations, statuts, doublons).
3. Pour Silver : lire le NDJSON compressé, convertir `last_update` en UTC, joindre `station_id` → `_id` → `number`, puis `number` → `stationCode` actuel ; conserver une colonne `station_code` plutôt que le `station_id` long ; ajouter une colonne `source` (`gbfs_2025+` / `jcdecaux_2017`) et traiter `velos_electriques` comme 0 déduit.
4. Si l'objectif est un historique plus long que votre collecte actuelle, deux sources déjà vérifiées dans ce dépôt restent utilisables : l'historique `lovasoa/historique-velib-opendata` et le jeu Kaggle `velib-data` (voir `verification_historiques.md` et `verification_historiques_2.md`).
