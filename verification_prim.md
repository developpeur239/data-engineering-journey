# Vérification de la source « pannes » : PRIM Messages Info Trafic + référentiel IDFM

Tests faits le **lundi 5 octobre 2026, entre 10:10 et 10:25 UTC** (12:10–12:25, heure de Paris), avec `curl` et
Python 3.11. Tous les chiffres viennent des fichiers enregistrés dans `echantillons/prim/` et `echantillons/idfm/`.

> **Sécurité.** La clé PRIM n'est écrite dans aucun fichier : ni code, ni `.meta.json`, ni log, ni rapport, ni
> historique git. Un `grep` de la valeur sur tout le dépôt, l'historique git et le scratchpad donne 0 occurrence.
> Le code la lit uniquement dans la variable d'environnement `PRIM_API_KEY`. Comme elle a été **collée dans la
> conversation**, il faut la **régénérer sur PRIM** et la stocker désormais comme variable d'environnement.
> `.gitignore` couvre maintenant `.env`, `.env.*`, `*.secret(s)`, `secrets/`, `*.key`, `*.pem` et `prim_api_key*`.

---

## 1. Tableau récapitulatif

| Élément | Résultat mesuré | Verdict |
|---|---|---|
| **Endpoint** | `GET https://prim.iledefrance-mobilites.fr/marketplace/disruptions_bulk/disruptions/v2` (requête globale, sans paramètre) | OK |
| **Authentification** | En-tête HTTP **`apiKey`**. Sans clé : `401 {"message":"No API key found in request"}`. Fausse clé : `401 {"message":"Unauthorized"}`. Vraie clé : `200` | OK |
| **Format** | JSON UTF-8 sans BOM, compressé au transport. Racine : `{disruptions[], lines[], lastUpdatedDate}`. **1,41–1,44 Mo**, réponse en **~1,06 s** | OK |
| **Fréquence réelle** | `lastUpdatedDate` avance à **chaque** appel (3 appels espacés de 2 min) : le contenu change (937 → 936 → 910 perturbations). Le flux n'est pas figé | OK |
| **Quotas** | En-têtes `x-ratelimit-limit-day: 1000` et `ratelimit-limit: 1000`, remise à zéro vers 00:00 UTC. **288 appels/jour = 28,8 % du quota** | OK |
| **Historique** | **Non.** Les paramètres de date sont ignorés (sha256 identique). Navitia ne renvoie aucune perturbation terminée. Les perturbations disparaissent du flux après leur fin. **Pas d'historique, il faut archiver soi-même** | Réserve |
| **Licence** | **Non vérifiée** : les pages PRIM sont bloquées (voir §6). transport.data.gouv.fr indique « mobility-licence » pour le jeu IDFM (GTFS/NeTEx/SIRI) | À confirmer |
| **Référentiel arrêts-lignes** | IDFM `arrets-lignes` : CSV `;` UTF-8 **avec BOM**, 74 549 lignes, 35 536 arrêts, 2 026 lignes, ODbL, mis à jour quotidiennement (dernière fois le 04/10/2026 à 15:06 UTC) | OK |
| **Jointure des identifiants** | **100 %** (722/722 lignes, 1 716/1 716 arrêts), à condition de retirer les préfixes `line:` et `stop_point:` (0 % sans normalisation) | OK |
| **Jointure spatiale Vélib'** | 99,1 % des stations ont au moins une ligne à 300 m. 41 s en force brute contre **0,12 s** avec une grille | OK |
| **Verdict global** | Source fiable, riche et joignable. À archiver dès le jour 1 et à exploiter **au niveau des arrêts**, pas des lignes | **OK avec réserves** |

---

## 2. Étape 1 : trouver le bon endpoint

**Problème.** Les trois pages de documentation demandées renvoient **HTTP 403 Cloudflare** (« Sorry, you have been blocked ») :

- depuis le conteneur avec `curl`, y compris avec un user-agent de navigateur ;
- via l'outil WebFetch ;
- avec Chromium headless, qui échoue en plus sur le certificat du proxy ; je n'ai pas désactivé la vérification TLS ;
- via les copies web.archive.org (snapshots du 16/05, 10/06 et 11/04/2026 repérés), qui coupent la connexion.

Je n'ai donc **pas pu lire la page officielle elle-même**. L'URL retenue repose sur des sources concordantes, puis a été
validée par les appels réels :

| Information | Source | Confirmée par le test |
|---|---|---|
| URL `…/marketplace/disruptions_bulk/disruptions/v2` | Résultat de recherche indexant la page PRIM « Traffic Info Messages – Global Query » (`/en/apis/idfm-disruptions_bulk`) + ticket GitHub [Anthodev/lapin-fute#9](https://github.com/Anthodev/lapin-fute/issues/9) | Oui, HTTP 200 avec la clé |
| En-tête `apiKey` | Message PRIM de génération du jeton (« Son utilisation se fait au travers de l'entête HTTP « apiKey » ») | Oui : 401 sans en-tête, 200 avec |
| Quotas « 5 req/s ; 18 000/jour pour les jetons d'avant le 13/03/2024, 1 000/jour après » | Extrait de recherche de la page [Traffic Info Messages – Global Query](https://prim.iledefrance-mobilites.fr/en/apis/idfm-disruptions_bulk) | Oui : `x-ratelimit-limit-day: 1000` |
| Correspondance avec l'ancienne API Navitia `line_reports` v2 | Extrait de recherche (page « Ile-de-France Mobilités Calculator – Traffic Info Messages (v2) ») | `…/marketplace/v2/navitia/line_reports/line_reports` répond (quota séparé de 4 000/jour) |
| Fréquence de mise à jour **annoncée** | **Non trouvée** (page bloquée) | Fréquence **mesurée**, voir §3.4 |

---

## 3. Étape 2 : l'API de perturbations

### 3.1 Appels

| Appel (UTC) | HTTP | Temps | Taille | Perturbations | `lastUpdatedDate` | Quota restant |
|---|---|---|---|---|---|---|
| sans clé | 401 | – | – | `No API key found in request` | – | – |
| fausse clé | 401 | – | – | `Unauthorized` | – | – |
| #1 10:17:44 | 200 | 1,069 s | 1 441 609 o | 937 | 10:17:14.901Z | 999 |
| #2 10:19:45 | 200 | 1,063 s | 1 440 931 o | 936 | 10:19:15.096Z | 998 |
| #3 10:21:46 | 200 | 1,057 s | 1 414 072 o | 910 | 10:21:16.147Z | 997 |

### 3.2 Structure

- **`disruptions[]`** (937), avec les champs `id` (UUID), `applicationPeriods[]` (`begin`/`end`), `lastUpdate`,
  `cause`, `severity`, `title`, `message` (**HTML**), `shortMessage` (601/937), `impactedSections` (339/937) et
  `tags` (170/937, toujours `"Actualité"`).
- **`lines[]`** (722 lignes touchées), avec les champs `id`, `name`, `shortName`, `mode`, `networkId` et
  `impactedObjects[]`. Chaque objet impacté contient `type`, `id`, `name` et **`disruptionIds[]`**.
  - Le lien perturbation → ligne passe **par cette liste**, pas par la perturbation.
  - Types d'objets impactés : 2 504 `stop_point`, 561 `line` (ligne entière) et 8 `stop_area`.
  - 935/937 perturbations sont rattachées à au moins une ligne.
- **Identifiants**
  - lignes : `line:IDFM:C02139` ;
  - arrêts : `stop_point:IDFM:16874`, `stop_area:IDFM:71675` ;
  - réseau : `network:IDFM:1087`.
- **Dates**
  - `begin`, `end` et `lastUpdate` sont au format `YYYYMMDDTHHMMSS`, **en heure de Paris, sans fuseau**. La dernière `lastUpdate` vaut 12:16 alors que l'appel a eu lieu à 10:17 UTC.
  - `lastUpdatedDate`, à la racine, est en UTC ISO 8601.
  - Les `lastUpdate` vont du 11/10/2024 au 05/10/2026.

### 3.3 Gravité, cause, périodes

Les **valeurs réelles sont en français**, pas `BLOCKING` / `DISTURBED` / `INFORMATION` :

| | BLOQUANTE | PERTURBEE | INFORMATION | Total |
|---|---|---|---|---|
| Toutes (appel #1) | 486 | 378 | 73 | 937 |
| **Actives à 12:17 (Paris)** | **251** | **221** | **68** | **540** |

- Causes, sur toutes les perturbations : TRAVAUX 473, PERTURBATION 416, INFORMATION 48.
- Causes, sur les perturbations actives : PERTURBATION 261, TRAVAUX 237, INFORMATION 42.
- Statut :
  - 540 actives ;
  - 296 uniquement à venir ;
  - 69 dont toutes les périodes sont terminées mais encore présentes dans le flux.
- Nombre de périodes par perturbation : 1 dans 768 cas sur 937, jusqu'à 132.
- **Messages sans date de fin : 0 %** (0 période sur 2 926 sans `end`, aucune fin « infinie » en 2099).
  - Attention, une fin est souvent **une estimation** (ex. « RER E : perturbations », de 11:52 à 14:00).
  - Les messages INFORMATION ont des périodes de plusieurs années (médiane 25 082 h, soit environ 2,9 ans).

### 3.4 Répartition par mode et par gravité

Une perturbation qui touche plusieurs modes est comptée dans chacun.

| Mode | Toutes : BLOQ. / PERT. / INFO. | **Actives : BLOQ. / PERT. / INFO.** |
|---|---|---|
| Métro | 25 / 3 / 1 | **2 / 0 / 0** |
| RER / train (RapidTransit, LocalTrain, regionalRail, RailShuttle) | 1 / 134 / 0 | **0 / 8 / 0** |
| Tram | 6 / 1 / 2 | **1 / 1 / 2** |
| Bus | 454 / 238 / 70 | **248 / 210 / 66** |
| Sans ligne | 0 / 2 / 0 | 0 / 2 / 0 |

**Le flux est à plus de 90 % du bus.** Les perturbations ferrées actives à 12:17 :

| Ligne | Gravité | Cause | Message |
|---|---|---|---|
| Métro 4 | BLOQUANTE | TRAVAUX | « Travaux de rénovation – Arrêt non desservi » |
| Métro 8 | BLOQUANTE | TRAVAUX | « Travaux de rénovation – Arrêt non desservi » |
| Tram T3a | BLOQUANTE | PERTURBATION | « Mesures de sécurité – Trafic interrompu » |
| Tram T4 | PERTURBEE | PERTURBATION | Mouvement social du 5 au 9/10 |
| RER C | PERTURBEE | TRAVAUX | Gares non desservies |
| RER D | PERTURBEE | PERTURBATION | Allègement de l'offre |
| RER E | PERTURBEE | PERTURBATION | Perturbations |
| Ligne P | PERTURBEE | PERTURBATION | Trafic perturbé |
| Ligne R | PERTURBEE | PERTURBATION | Ralentissement |

### 3.5 Fréquence de mise à jour réelle

| Comparaison | Nouvelles | Retirées | Modifiées | sha256 |
|---|---|---|---|---|
| appel 1 → 2 | +1 (Métro 7 : « Gêne à la fermeture des portes ») | −2 (Bus 306, manifestation terminée à 11:02) | 0 | différent |
| appel 2 → 3 | +1 (Tram T1 : manifestation) | −27 (26 BLOQUANTE / 1 PERTURBEE, manifestations terminées) | 0 | différent |

**Les données changent. `lastUpdatedDate` est toujours environ 30 s antérieur à l'appel**, ce qui suggère une
régénération continue avec un cache côté serveur (en-têtes `Age`, `x-cache-status`, `cf-cache-status` présents).
Les perturbations terminées sont **retirées du flux** avec un délai d'environ 1 h observé (fin à 11:02, retrait vers 12:19).

### 3.6 Historique

| Test | Résultat |
|---|---|
| `disruptions/v2?since=20260921T000000&until=20260927T235959` | HTTP 200, **sha256 identique** à l'appel #3 : paramètres ignorés |
| `disruptions/v2?date=2026-09-21` | HTTP 200, **sha256 identique** : paramètre ignoré |
| Navitia `line_reports` v2, sans filtre | 466 perturbations (status : 411 active, 49 future, 6 past), 1 280 `line_reports` paginés par 100 |
| Navitia `line_reports` v2 `since/until` = semaine du 21/09 | 363 perturbations, **toutes `active`**, **0 terminée avant le 05/10** : simple filtre sur ce qui est encore stocké |
| Jeux open data IDFM | Aucun jeu « historique des perturbations » dans le catalogue `data.iledefrance-mobilites.fr`. Seul `grands-travaux-ete-2026` (54 lignes) concerne des travaux passés |

**Conclusion : pas d'historique, il faut archiver soi-même.** Chaque appel est un instantané à déposer en Bronze. La
durée réelle d'un incident se reconstitue en Silver à partir de la première et de la dernière apparition de son `id`.

### 3.7 Quotas

- En-têtes relevés :
  - `ratelimit-limit: 1000`
  - `ratelimit-remaining`
  - `x-ratelimit-limit-day: 1000`
  - `x-ratelimit-remaining-day`
  - `ratelimit-reset: 49337` (s), soit une remise à zéro vers 00:00 UTC (02:00 à Paris)
- **1 appel toutes les 5 min = 288 appels/jour = 28,8 % du quota.** Il reste 712 appels pour les retries et les tests. Le système est compatible ; toutes les 2 min (720/jour) passerait encore.
- L'API Navitia `line_reports` a son **propre quota de 4 000/jour** (`ratelimit-remaining` 3 999).
- Consommation de ces tests : 5 appels sur le quota `disruptions_bulk` et 2 sur Navitia.

---

## 4. Étape 3 : référentiel des arrêts et lignes

| Candidat | Coordonnées | Identifiant de ligne | Taille | Retenu |
|---|---|---|---|---|
| **IDFM `arrets-lignes`** (« Arrêts et lignes associées ») | oui (`stop_lat`, `stop_lon`, WGS84) | oui (`id` = `IDFM:C01371`) | **13,9 Mo** | **Oui** |
| IDFM `referentiel-des-lignes` (2 128 lignes) | non | oui | – | Non : pas de coordonnées |
| IDFM `arrets` (37 956 arrêts) | oui | non | – | Non : pas de lignes |
| GTFS IDFM (transport.data.gouv.fr, `eu.ftp.opendatasoft.com/stif/GTFS/IDFM-gtfs.zip`) | oui | oui (via `trips`/`stop_times`) | **136,4 Mo** | Non : plus de 50 Mo et 4 fichiers à joindre ; `arrets-lignes` en est la version aplatie |

**Fiche du jeu retenu**

- **URL :** `https://data.iledefrance-mobilites.fr/api/explore/v2.1/catalog/datasets/arrets-lignes/exports/csv?delimiter=;`
- **Téléchargement :** HTTP 200 en 7,2 s, sans clé.
- **Format :** CSV séparé par `;`, **UTF-8 avec BOM**, fins de ligne CRLF.
- **Volume :** **74 549 lignes** (une par couple arrêt × ligne, 0 doublon), 13 colonnes. Taille totale de 13,9 Mo, téléchargée en entier.
- **Colonnes :** `id`, `route_long_name`, `stop_id`, `stop_name`, `stop_lon`, `stop_lat`, `operatorname`, `shortname`, `bookingrules`, `mode`, `pointgeo`, `nom_commune`, `code_insee`.
- **Valeurs vides :** 0 % partout, sauf `bookingrules` (96 %).
- **Contenu :** **35 536 arrêts** distincts et **2 026 lignes**.
  - Lignes par mode : Bus 1 966, Metro 16, Tramway 15, regionalRail 11, LocalTrain 9, RapidTransit 5, RailShuttle 2, CableWay 1, Funicular 1.
  - Couvre toute l'Île-de-France (latitude 47,96–49,46).
- **Licence :** ODbL (version française).
- **Mise à jour :** quotidienne, la dernière le **04/10/2026 à 15:06 UTC**.
- **Format des identifiants :** `IDFM:C01371` pour les lignes et `IDFM:463130` pour les arrêts. Ce sont **les mêmes que l'API, sans les préfixes** `line:` et `stop_point:`.

---

## 5. Étape 4 : jointure de bout en bout

Script de test sans clé, qui lit les fichiers enregistrés. Instantané PRIM #1 (12:17 à Paris, 540 perturbations
actives), `station_information` Vélib' (1 519 stations) et `arrets-lignes`.

### 5.1 Correspondance des identifiants

| | Brut | Après suppression du préfixe | Sans correspondance |
|---|---|---|---|
| Lignes (`line:IDFM:Cxxxxx` → `IDFM:Cxxxxx`) | 0/722 (0 %) | **722/722 (100 %)** | aucune |
| Arrêts impactés (`stop_point:IDFM:n` → `IDFM:n`) | – | **1 716/1 716 (100 %)** | aucun |

### 5.2 Rattachement des stations Vélib' aux lignes

Distance **haversine** (rayon terrestre de 6 371 km).

| Rayon | Stations avec ≥ 1 ligne | Lignes par station (moy. / méd.) | Stations avec ≥ 1 ligne ferrée |
|---|---|---|---|
| 200 m | 1 454 / 1 519 (95,7 %) | 4,9 / 4 | 689 |
| **300 m** | **1 506 / 1 519 (99,1 %)** | **7,0 / 6** | **971** |
| 500 m | 1 519 / 1 519 (100 %) | 12,0 / 10 | 1 302 |

### 5.3 Stations proches d'une perturbation active

**Au niveau de la ligne (méthode demandée), le résultat n'est pas exploitable.** Une ligne de bus fermée à un seul
arrêt, à 15 km de là, rend « perturbées » toutes les stations situées le long de son tracé :

| Rayon | Ligne BLOQUANTE | Ligne BLOQ. + PERT. | Ligne ferrée BLOQUANTE | Ligne ferrée BLOQ. + PERT. |
|---|---|---|---|---|
| 200 m | 1 243 (81,8 %) | 1 265 (83,3 %) | 144 (9,5 %) | 197 (13,0 %) |
| 300 m | 1 398 (92,0 %) | 1 414 (93,1 %) | 243 (16,0 %) | 328 (21,6 %) |
| 500 m | 1 485 (97,8 %) | 1 495 (98,4 %) | 424 (27,9 %) | 571 (37,6 %) |

**Au niveau des arrêts réellement impactés (méthode recommandée)**, avec les `stop_point` de `impactedObjects` :

| Périmètre | Gravité | Arrêts impactés | 200 m | **300 m** | 500 m |
|---|---|---|---|---|---|
| Tous modes, arrêts ciblés | BLOQUANTE | 793 | 306 (20,1 %) | **438 (28,8 %)** | 746 (49,1 %) |
| Tous modes, arrêts ciblés | BLOQ. + PERT. | 887 | 331 (21,8 %) | **472 (31,1 %)** | 800 (52,7 %) |
| Tous modes, arrêts + lignes entières | BLOQUANTE | 4 635 | 1 029 (67,7 %) | 1 205 (79,3 %) | 1 361 (89,6 %) |
| **Ferré seul, arrêts ciblés** | BLOQUANTE | 14 | 12 (0,8 %) | **19 (1,3 %)** | 52 (3,4 %) |
| **Ferré seul, arrêts ciblés** | BLOQ. + PERT. | 102 | 44 (2,9 %) | **74 (4,9 %)** | 165 (10,9 %) |
| Ferré seul, arrêts + lignes entières | BLOQ. + PERT. | 304 | 93 (6,1 %) | 164 (10,8 %) | 328 (21,6 %) |

Remarque : 61 des 540 perturbations actives sont des **manifestations**, et le tram T4 est en mouvement social.
Aujourd'hui n'est donc pas un jour « moyen ».

### 5.4 Temps de calcul

| Méthode | Temps (Python pur) | Remarque |
|---|---|---|
| Force brute : 1 519 × 35 536 = 54 M distances haversine | **41 s** | Acceptable une fois, trop lent toutes les 5 min |
| **Grille** (cellules de la taille du rayon, 9 voisines) | **105 / 124 / 146 ms** (200 / 300 / 500 m) | **Résultat identique** à la force brute (vérifié par assertion), environ 300 fois plus rapide |

Optimisation proposée :

- **Précalculer une fois par jour en Silver** une table `station_arret(station_id, stop_id, distance_m)`, au moment où le référentiel est rafraîchi.
- Chaque instantané PRIM ne demande ensuite qu'une **jointure par identifiant** (`stop_id`), sans aucun calcul de distance.
- Pour aller plus loin : index spatial (`geopandas.sjoin_nearest`, extension spatiale de DuckDB) ou cellules H3.

---

## 6. Problèmes rencontrés

1. **Documentation PRIM inaccessible.** HTTP 403 Cloudflare depuis le conteneur, depuis WebFetch et sur le PDF officiel ; web.archive.org coupe la connexion ; Chromium headless échoue sur le certificat du proxy, et la vérification TLS n'a pas été désactivée. L'endpoint, l'en-tête et le quota ont été établis par recoupement, puis **confirmés par les appels**. La fréquence annoncée et la licence ne sont pas confirmées. → À relire depuis un navigateur personnel.
2. **Clé collée dans le chat** (la variable d'environnement était vide au départ). Elle n'a été utilisée que dans une commande, le temps d'un processus, et n'est écrite nulle part. → **La régénérer.**
3. **Gravités en français** (`BLOQUANTE` / `PERTURBEE` / `INFORMATION`), différentes de la nomenclature attendue.
4. **Dates sans fuseau** (heure de Paris) dans `applicationPeriods` et `lastUpdate`, alors que `lastUpdatedDate` est en UTC.
5. **Préfixes d'identifiants** (`line:`, `stop_point:`) absents du référentiel : 0 % de correspondance sans normalisation.
6. **BOM UTF-8** dans le CSV `arrets-lignes`, à lire en `utf-8-sig`.
7. **`message` en HTML** (balises et styles en ligne), à nettoyer en Silver.
8. **Biais bus.** Plus de 90 % des perturbations concernent le bus, et la jointure au niveau de la ligne surestime fortement l'impact (92 % des stations).
9. **Pas d'historique.** Les perturbations terminées disparaissent du flux en environ 1 h.

---

## 7. Assez de pannes sur une semaine ?

**Ce qu'on observe aujourd'hui** (un seul instantané, pas une moyenne) :

- **540 perturbations actives**, dont **261 incidents** (cause PERTURBATION).
- **215 incidents mis à jour aujourd'hui.**
- Côté ferré : 2 métro, 8 RER/train et 4 tram actifs, dont 5 incidents du jour (RER E ×2, ligne P, ligne R, T3a).

**Durées annoncées** (plus longue période d'application) :

| Type | Médiane | Quartiles (p25 – p75) | Nombre |
|---|---|---|---|
| Incidents (PERTURBATION) | 10 h | 4,5 h – 1 018 h | – |
| Incidents ferrés | **4,5 h** | 2 h – 94 h | 16 |
| Travaux | 24 h | 4,5 h – 2 036 h | – |

Ces durées sont **annoncées**, pas observées : la durée réelle se mesurera avec l'archivage (première et dernière apparition).

**Estimation, à confirmer par la collecte.** Il y a plusieurs incidents ferrés par jour et des centaines d'incidents de
bus. Sur 7 jours d'archivage toutes les 5 min, on peut donc attendre **plusieurs dizaines d'incidents ferrés** et
**plus d'un millier d'incidents de bus**. C'est suffisant pour une analyse descriptive, mais **juste pour une analyse
statistique ferrée seule**.

**Plan B si la semaine est calme côté ferré :**

1. Inclure la gravité **PERTURBEE**. Au niveau des arrêts ferrés, la population passe de 19 à 74 stations proches à 300 m.
2. Inclure les **TRAVAUX planifiés** (237 actifs, 296 à venir), connus à l'avance : comparaison avant / pendant les travaux pour les stations voisines.
3. Inclure les **arrêts de bus non desservis** au niveau des arrêts (793 arrêts BLOQUANTE, soit 28,8 % des stations à 300 m).
4. Garder le volet comme **variable explicative secondaire** (indicateur « perturbation à moins de 300 m », oui ou non) plutôt que comme sujet principal.

---

## 8. Recommandation

**Oui, on garde le volet « pannes », comme dimension secondaire du sujet Vélib' × météo.** Raisons :

- **Faisabilité prouvée :**
  - l'API répond en environ 1 s ;
  - le quota couvre largement 288 appels/jour (28,8 %) ;
  - le flux change réellement d'un appel à l'autre ;
  - la jointure des identifiants est à **100 %** ;
  - la jointure spatiale prend **0,12 s**.
- **Intérêt datalake renforcé.** Comme Vélib', PRIM **ne garde aucun historique** : l'archivage Bronze toutes les 5 min crée une donnée qui n'existe nulle part ailleurs. Le référentiel ODbL quotidien illustre en plus une dimension qui évolue lentement.
- **Conditions :**
  1. archiver dès le jour 1 (`python collecte_test.py prim --polls 1` toutes les 5 min, même déclencheur que Vélib') ;
  2. joindre au niveau des **arrêts impactés**, pas des lignes ;
  3. séparer ferré et bus dans les analyses ;
  4. traiter les dates comme heure de Paris ;
  5. annoncer que la semaine observée peut être atypique (manifestations, grèves).
