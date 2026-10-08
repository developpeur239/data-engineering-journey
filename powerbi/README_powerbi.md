# Tableau de bord Power BI : pénuries et saturations Vélib'

Projet Power BI (format **.pbip**) qui lit la table Gold `velib.gold_station_heure` servie par le SQL Warehouse Databricks,
et l'affiche en 4 pages (+ 1 page de secours cachée). **Aucun secret n'est stocké dans ces fichiers** : le jeton Databricks se saisit dans Power BI au premier rafraîchissement.

> **Important :** je n'ai pas pu ouvrir ce projet dans Power BI Desktop (je travaille sous Linux). Tous les fichiers ont été validés contre les schémas officiels de Microsoft
> et les graphiques ont été rendus en image, mais le premier vrai test, c'est vous. La section « Si quelque chose ne marche pas » est faite pour ça.

## Ce que contient le dossier

```
powerbi/
├── velib_dashboard.pbip              ← le fichier à ouvrir (double-clic)
├── velib_dashboard.SemanticModel/    ← modèle de données (TMDL) : connexion, colonnes typées, mesures DAX
├── velib_dashboard.Report/           ← rapport (PBIR) : pages, visuels, thème intégré
├── velib_theme.json                  ← thème (couleurs, polices), aussi copié dans le rapport
├── deneb_specs/                      ← les 7 graphiques Deneb en texte (Vega-Lite) + config commune + champs à lier + paris_fond.json (fond de carte)
├── apercus/                          ← aperçus PNG des graphiques (données fictives) + planche.png
├── REPARER_TABLE.md                  ← colonnes et mesures à recréer si vous réimportez la table
├── DESIGN.md                         ← direction artistique (palette, typo, grille, contrôles faits)
└── outils/                           ← scripts Python qui génèrent et valident tout (facultatif)
```

## 1. Avant d'ouvrir : activer 3 fonctionnalités en préversion

Il faut **Power BI Desktop pour Windows, version récente** (celle du Microsoft Store convient).

1. Ouvrez Power BI Desktop (sans rapport).
2. **Fichier → Options et paramètres → Options → Fonctionnalités en préversion.**
3. Cochez :
   - **Enregistrer au format de projet Power BI (.pbip)** (« Power BI Project (.pbip) save option ») ;
   - **Stocker les rapports Power BI au format PBIR** (« Store reports using enhanced metadata format (PBIR) ») ;
   - **Stocker le modèle sémantique au format TMDL** (« Store semantic model using TMDL format »).
4. Validez et **redémarrez** Power BI Desktop. Si l'une de ces options n'existe plus dans votre version, c'est qu'elle est devenue standard : passez à l'étape suivante.

## 2. Ouvrir le projet

1. Décompressez le zip du dépôt, **gardez la structure des dossiers telle quelle**.
2. Double-cliquez sur **`powerbi/velib_dashboard.pbip`** (ou *Fichier → Ouvrir un rapport → Parcourir*, puis choisissez ce fichier).
3. Si Power BI affiche un avertissement sur un visuel personnalisé, voir la section Deneb plus bas.

## 3. Saisir le jeton Databricks (première actualisation)

Les trois paramètres de connexion sont déjà remplis, **sans jeton** :

| Paramètre | Valeur |
|---|---|
| `Hote` | `adb-7405605942490257.17.azuredatabricks.net` |
| `CheminHTTP` | `/sql/1.0/warehouses/4dd75efb6ecd07bd` |
| `Catalogue` | `dbw_datalake_velib_7405605942490257` |

La table lue est `Catalogue` → schéma `velib` → table `gold_station_heure`, en mode **Importation**.

**Créer un jeton** (si vous n'en avez pas) : dans Databricks, cliquez sur votre avatar → *Paramètres* → *Développeur* → *Jetons d'accès* → *Générer un nouveau jeton*. Copiez-le tout de suite, il ne sera plus affiché.

**Le saisir dans Power BI :**
- Cliquez sur **Actualiser** (onglet *Accueil*). Power BI demande les identifiants : choisissez **Jeton d'accès personnel**, collez le jeton, *Se connecter* ; ou
- **Fichier → Options et paramètres → Paramètres de la source de données →** sélectionnez la source Databricks **→ Modifier les autorisations → Jeton d'accès personnel**.

Le SQL Warehouse doit être **démarré** (il s'allume tout seul à la première requête, comptez 1 à 2 minutes).
Ne mettez jamais le jeton dans un fichier du dépôt. Si vous avez déjà publié un jeton par erreur, révoquez-le dans Databricks.

## 4. Rafraîchir les données ou changer de source

- **Rafraîchir :** *Accueil → Actualiser*.
- **Changer d'adresse, de warehouse ou de catalogue :** *Accueil → Transformer les données → Modifier les paramètres*, puis changez `Hote`, `CheminHTTP` ou `Catalogue`, *OK*, *Fermer et appliquer*. Il faudra ressaisir le jeton si l'hôte change.
- Les colonnes attendues sont celles de `gold_station_heure` (33 colonnes) ; Power Query ne fait que les charger et les typer. Les 4 colonnes `jour_semaine_ordre`, `jour_nom`, `periode` et `pluie_libelle` sont des **colonnes calculées en DAX dans le modèle** (voir `REPARER_TABLE.md` pour les recréer). Si Databricks renomme ou supprime une colonne, l'actualisation affiche « La colonne … de la table est introuvable » : remettez le nom d'origine ou modifiez l'étape *Types* dans *Transformer les données*.

## 5. Les pages

Question de recherche : **« Quand et où les stations Vélib' sont-elles vides ou pleines, et la météo et les pannes de transport l'expliquent-elles ? »** Chaque page répond à une sous-question (affichée en sous-titre de la page), chaque indicateur se lit en une phrase et est accompagné du nombre d'observations (dans le sous-titre du visuel ou de la page).

| Page | Question | Indicateurs (et nombre d'observations) | Lecture en une phrase |
|---|---|---|---|
| **Vue d'ensemble** | Quand les stations sont-elles vides ou pleines ? | cartes « Temps passé vide (%) », « Temps passé plein (%) » et « Données à jour au JJ/MM HH:MM » ; courbe horaire vide / plein (visuel principal, N relevés) ; carte de chaleur heure × jour (période couverte et N relevés) ; sous-titre de page : N stations suivies et N relevés | « Les stations se vident aux heures de pointe, surtout le matin en semaine » (le titre de chaque graphique énonce le constat calculé) |
| **Carte des stations** | Où manque-t-on de vélos ? | carte stylisée (taille = capacité, couleur = temps passé vide, N stations) ; tableau des 20 stations les plus souvent vides (Station, Capacité, Temps passé vide en %) | « N stations sur M sont vides plus d'un relevé sur cinq » |
| **Effet des pannes** | Les pannes de transport l'expliquent-elles ? | haltères « sans panne → avec panne » (vide et plein, pointe / hors pointe ; « sur N heures avec panne ») ; carte « Heures avec panne observées » ; segment Panne imprévue (Oui par défaut) | « En heure de pointe, une panne ferrée à moins de 300 m augmente (ou réduit) la pénurie de X pts » |
| **Effet de la météo** | La pluie change-t-elle les pénuries ? | barres avec / sans pluie (« N heures de pluie observées du JJ/MM au JJ/MM ») ; courbe horaire pluie / sec (heures de pluie et heures sèches) ; encadré « Comment lire » | « Sous la pluie, la pénurie passe de X % à Y % » ; « …est plus haute (ou plus basse) à X heures sur Y » |
| **Météo · 3 ans de compteurs** | Le confirme-t-on sur 3 ans de trafic vélo ? | cartes « Effet pluie semaine / week-end (%) » ; barres de l'effet à conditions égales (visuel principal) ; passages par classe de température (pointe, sans pluie) ; profil horaire en semaine ; sous-titre de page : N heures dont X % de pluie | « Sous la pluie, à conditions égales : −15,9 % en semaine, −20,6 % le week-end » |
| **Secours** et **Secours · météo 3 ans** (cachées, inchangées) | | un équivalent en visuels Power BI natifs de chaque graphique Deneb | |

Retirés à la revue finale (parce qu'ils ne répondent pas directement à la question) : la carte « Nb stations » (le nombre figure dans le sous-titre de la page), les cartes « Écart pénurie / saturation (pts) » et « Part heures avec panne ferrée » (remplacée par « Heures avec panne observées »), le nuage de température (confondu avec l'heure de la journée), les haltères par période (écart brut) et les cartes « Heures étudiées » et « Part des heures de pluie » de la page 3 ans. Les mesures correspondantes sont **masquées, pas supprimées** : elles servent aux titres et sous-titres dynamiques. La sauvegarde d'avant la revue est dans `powerbi_sauvegarde_avant_revue/`.

**Sous-titres dynamiques.** Les sous-titres des graphiques (période couverte, nombre de relevés, d'heures ou de stations) sont des mesures `Sous-titre …` liées au sous-titre du visuel. Le sous-titre de page (nombre de stations, nombre d'heures et part de pluie) est le titre d'une zone de texte vide, liée à une mesure (les zones de texte ne peuvent pas afficher une mesure autrement).

Les **titres** des graphiques Deneb sont **calculés** par une mesure DAX chacun (`Titre heatmap`, `Titre rythme`, `Titre carte`, `Titre pannes`, `Titre pluie`, `Titre courbes`, et ceux de la page 3 ans ; `Titre nuage` est conservée, masquée, mais plus affichée) : aucun chiffre ni constat n'est écrit dans une spec. Chaque mesure est liée au titre du visuel Power BI (*Format → Titre → Texte → fx*), respecte les filtres et segments, et affiche un texte neutre si les données sont vides. Les nombres sont formatés en français quelle que soit la machine : `FORMAT(x, "#,##0", "fr-FR")` donne « 1 450 » et `FORMAT(x, "0.0", "fr-FR")` donne « 3,0 » (le troisième argument impose la locale ; un motif du type `"# ##0"` n'est pas fiable en DAX). Seul le sous-titre est fixe.
La page **Secours** est cachée pour les lecteurs mais visible dans Power BI Desktop (onglet grisé en bas).

## 6. Deneb : le visuel qui dessine les graphiques

Les graphiques principaux utilisent **Deneb**, un visuel certifié de la boutique Microsoft (code Vega-Lite en JSON).

**S'il n'est pas installé :** à droite, dans *Visualisations*, cliquez sur **… → Obtenir d'autres visuels**, cherchez **Deneb**, *Ajouter*. Rouvrez ensuite le rapport.
Le rapport déclare Deneb (identifiant `deneb7E15AEF80B9E4D4F8E12924291ECE89A`) dans `report.json` : Power BI le télécharge normalement tout seul à l'ouverture.

**Coller une spec à la main** (si un graphique reste vide ou en erreur) :
1. Ajoutez un visuel **Deneb** sur la page.
2. Glissez dans le puits **Valeurs** les champs listés pour ce graphique dans `deneb_specs/_champs_par_visuel.json` (même ordre, ne les renommez pas).
3. Cliquez sur **… → Modifier** sur le visuel, choisissez **Vega-Lite** comme *Provider*.
4. Onglet **Spec** : collez le contenu du fichier `deneb_specs/0X_….json` ; onglet **Config** : collez `deneb_specs/_config_commun.json`.
5. *Appliquer*. Dans *Mise en forme → Développeur*, réglez **Locale = fr-FR** pour les nombres à la française.

## 6 bis. Fond de carte, formats et limite de lignes

**Fond de la carte (`deneb_specs/paris_fond.json`).** Deux formes très discrètes sous les stations : la limite de Paris et la Seine avec les canaux. Le GeoJSON simplifié (≈ 5 Ko) est **embarqué dans la spec** (Deneb ne charge pas de fichier externe) ; le fichier `paris_fond.json` en est la copie lisible.
- **Source :** Open Data Paris, jeux [« arrondissements »](https://opendata.paris.fr/explore/dataset/arrondissements/) (union des 20 arrondissements) et [« plan-de-voirie-voies-deau »](https://opendata.paris.fr/explore/dataset/plan-de-voirie-voies-deau/) (emprises de la Seine et des canaux, fragments minuscules écartés).
- **Licence :** Open Database License (ODbL) : mention « Données © Ville de Paris ». Traitement : union, simplification (≈ 30 m pour la limite, ≈ 15 m pour l'eau), coordonnées arrondies à 4 décimales. Le tracé de la Seine ne couvre que la traversée de Paris intra-muros. Reproduire : `python3 outils/preparer_fond.py` (réseau et `pip install shapely`).
- La projection est `{"type": "mercator"}` avec `longitude` / `latitude`.

**Formats français des nombres.** `formatLocale` n'est pas une propriété d'une spec Vega-Lite : la locale se règle dans Deneb (*Mise en forme → Développeur → Locale*). Le rapport est déjà réglé sur **fr-FR**, donc les infobulles et étiquettes affichent « 1 450 » (format `,d`) et « 8,7 % ». Les titres, eux, sont formatés par le DAX (§ ci-dessus).

**Limite de lignes de Deneb.** Deneb ne reçoit que les lignes que Power BI lui envoie, déjà regroupées par les champs du visuel (une ligne par combinaison des colonnes liées). Avec les liaisons choisies, on est loin des seuils, même avec plusieurs mois de données :

| Visuel | Lignes envoyées à Deneb (ordre de grandeur) |
|---|---|
| Heatmap | 168 (24 heures × 7 jours), quel que soit le nombre de jours |
| Rythme, courbes pluie | 24 à 48 |
| Haltères, barres | 2 à 4 |
| Carte | ≈ 1 450 (une ligne par station ; peut doubler si une capacité ou des coordonnées changent dans le temps) |
| Nuage | 24 × nombre de jours (168 pour une semaine ; 8 760 pour un an) |

Le seul visuel qui grossit avec le temps est le nuage ; il est donc **déjà pré-agrégé** (une ligne par heure, jamais par station). Par sécurité, chaque visuel Deneb a aussi *Limite de données → Remplacer la limite* activé (`dataLimit.override`). Si vous voyez un bandeau « données tronquées », vérifiez dans *Mise en forme → Limite de données* que ce réglage est actif, ou filtrez la période avec le segment.

## 6 ter. Page « Météo · 3 ans de compteurs » (table `gold_velo_meteo_heure`)

**Sauvegarde.** Avant toute modification, le dossier `powerbi/` a été copié dans `powerbi_sauvegarde_avant_meteo/` (2,5 Mo, commitée). La page « Effet de la météo » d'origine est inchangée.

**Table.** `dbw_datalake_velib_7405605942490257.velib.gold_velo_meteo_heure` (≈ 26 304 lignes, une par heure, 2023-2025), en mode Importation, avec les **mêmes paramètres** `Hote`, `CheminHTTP`, `Catalogue` (aucun secret). Elle est **indépendante** : aucune relation avec `gold_station_heure` (grain et période différents ; le contrôle automatique refuse toute relation). Les segments des pages existantes portent sur `gold_station_heure` : ils **ne filtrent pas** la table météo, et les segments de la nouvelle page (`type_jour`, `saison`, `annee`) ne filtrent pas les autres pages ; aucun segment n'est synchronisé entre pages.
Colonnes ajoutées dans le modèle (DAX) : `annee` (pour le segment), `saison_ordre` et `saison_libelle` (copie de `saison` triée hiver → automne, utilisée par le segment ; trier `saison` directement par une colonne qui en dépend provoquait une dépendance circulaire).

**Mesures** (dossier d'affichage « Météo 3 ans ») : `Passages par compteur`, `Passages sans pluie`, `Passages avec pluie`, `Écart pluie brut (%)`, `Effet pluie à conditions égales (%)`, `Effet pluie semaine (%)`, `Effet pluie week-end (%)`, `Heures de pluie`, `Heures étudiées`, `Part des heures de pluie (%)`, plus des mesures masquées d'appui (`Passages pointe temps sec`, `Heures pointe temps sec`, `Passages semaine sans pluie`, `Passages semaine avec pluie`) et 4 titres dynamiques (`Titre météo haltères`, `Titre météo effet`, `Titre météo température`, `Titre météo profil`), au format français (`FORMAT(…, "fr-FR")`), avec un texte neutre quand il n'y a pas de données.
**`Effet pluie à conditions égales (%)`** : pour chaque groupe `type_jour × saison × heure_du_jour` ayant au moins 5 heures de pluie, rapport (moyenne avec pluie ÷ moyenne sans pluie − 1) ; moyenne de ces rapports pondérée par le nombre d'heures de pluie du groupe. Elle part du contexte de filtre courant (`SUMMARIZE`), donc elle respecte `type_jour` et les autres segments.

**Page.** 3 segments (type de jour, saison, année), 2 chiffres clés (effet pluie semaine et week-end) et 3 graphiques Deneb (`deneb_specs/09` à `11` ; les haltères par période ont été retirés à la revue finale) :
1. (visuel principal) barres de l'effet à conditions égales, semaine et week-end ;
2. passages par compteur selon la classe de température (pointe, temps sec), maximum annoté ; la note sur les vacances d'été n'apparaît que si la dernière classe est en dessous du maximum ;
3. profil horaire en semaine, avec et sans pluie (24 points).
Un encadré « Méthode et limites » rappelle : les compteurs mesurent le trafic vélo (la demande), pas l'état des stations Vélib' ; passages **par compteur** (le nombre de compteurs varie), comparaison **à conditions égales**, jours fériés et vacances non exclus, un seul point météo pour Paris, association et non causalité. Couleurs : violet = pluie, gris = référence.
Chaque graphique a un équivalent natif sur la page cachée « Secours · météo 3 ans ».

### Validation des mesures (à lire)

**Je n'ai pas accès à votre table Databricks ni à un moteur DAX**, donc je n'ai pas pu exécuter les mesures sur vos données. J'ai fait deux choses à la place.

1. **Reconstitution de la table** à partir des mêmes sources publiques (`outils/validation_meteo3/`) : compteurs de la Ville de Paris 2023, 2024, 2025 (fichiers « compteurs », agrégés par heure UTC : somme des passages ÷ nombre de compteurs présents) et Open-Meteo archive (Paris, UTC, `precipitation ≥ 0,1 mm` = pluie). La grille fait bien **26 304 heures**. J'ai ensuite recalculé en Python la logique exacte de la mesure (strates `type_jour × saison × heure_du_jour`, au moins 5 heures de pluie, moyenne pondérée) :

| Contrôle | Votre valeur Databricks | Ma reconstitution | Écart |
|---|---|---|---|
| Heures de pluie retenues par la mesure | 4 618 | **4 618** | aucun |
| Heures de pluie totales (`il_pleut`) | n/d | 4 620 | n/d |
| Effet à conditions égales, semaine | −15,9 % | −14,3 % | **+1,6 point** |
| Effet à conditions égales, week-end | −20,6 % | −19,7 % | **+0,9 point** |
| Écart brut, pointe / journée / nuit | −13,3 % / −11,5 % / −20,6 % (163,6 → 141,8, etc.) | −11,7 % à −14,7 % selon la définition de « pointe » testée (voir le script) | non comparable : définition de la période inconnue |
| Passages en pointe temps sec par classe | 139,8 / 152,0 / 172,5 / 193,9 / 184,1 | non reproduit | seuils de classes inconnus |

**Lecture :** le nombre d'heures de pluie retenues (4 618) est retrouvé **exactement**, ce qui confirme la mécanique des strates et le seuil de 5 heures. L'écart de quelques points sur l'effet vient de ma reconstitution de la colonne `passages_par_compteur` (je ne connais pas votre définition de `compteurs_actifs`, ni vos découpages `periode` et `classe_temperature`). Quatre définitions testées donnent −13,6 % à −14,5 % en semaine, sans atteindre −15,9 %. **Ce n'est donc pas une preuve que la mesure DAX donnera vos chiffres à l'identique.**

2. **Requêtes SQL équivalentes à lancer dans Databricks**, puis à comparer aux cartes Power BI (sans segment actif) :

```sql
-- effet à conditions égales (doit égaler la mesure « Effet pluie à conditions égales (%) »)
WITH strates AS (
  SELECT type_jour, saison, heure_du_jour,
         SUM(CASE WHEN il_pleut THEN 1 ELSE 0 END)                    AS n_pluie,
         AVG(CASE WHEN il_pleut THEN passages_par_compteur END)       AS moy_pluie,
         AVG(CASE WHEN NOT il_pleut THEN passages_par_compteur END)   AS moy_sec
  FROM dbw_datalake_velib_7405605942490257.velib.gold_velo_meteo_heure
  GROUP BY type_jour, saison, heure_du_jour)
SELECT type_jour,
       SUM(n_pluie)                                         AS heures_de_pluie_retenues,
       SUM(n_pluie * (moy_pluie / moy_sec - 1)) / SUM(n_pluie) AS effet_conditions_egales
FROM strates
WHERE n_pluie >= 5 AND moy_sec > 0 AND moy_pluie IS NOT NULL
GROUP BY type_jour;                    -- attendu : semaine -0,159 ; week-end -0,206 ; 4 618 heures au total

-- écart brut par période (mesures « Passages sans pluie », « Passages avec pluie », « Écart pluie brut (%) »)
SELECT periode,
       AVG(CASE WHEN NOT il_pleut THEN passages_par_compteur END) AS sans_pluie,
       AVG(CASE WHEN il_pleut THEN passages_par_compteur END)     AS avec_pluie,
       AVG(CASE WHEN il_pleut THEN passages_par_compteur END)
         / AVG(CASE WHEN NOT il_pleut THEN passages_par_compteur END) - 1 AS ecart
FROM dbw_datalake_velib_7405605942490257.velib.gold_velo_meteo_heure GROUP BY periode;

-- température, pointe, temps sec (mesure masquée « Passages pointe temps sec »)
SELECT classe_temperature, AVG(passages_par_compteur) AS passages_par_compteur
FROM dbw_datalake_velib_7405605942490257.velib.gold_velo_meteo_heure
WHERE periode = 'pointe' AND NOT il_pleut
GROUP BY classe_temperature ORDER BY classe_temperature;
```

Point de vigilance : la mesure calcule la **moyenne simple des `passages_par_compteur`** par heure (comme `AVG` en SQL), pas un ratio de sommes. Si vos chiffres Databricks sont des ratios de sommes, des écarts apparaîtront.
Les valeurs de la colonne `periode` (`pointe`, `journée`, `nuit`), `type_jour` (`semaine`, `week-end`) et `saison` (`hiver`, `printemps`, `été`, `automne`) sont écrites **en minuscules avec accents** dans les mesures : s'ils diffèrent dans votre table, les mesures ressortiront vides.

## 7. Si quelque chose ne marche pas

| Symptôme | À essayer |
|---|---|
| Le .pbip ne s'ouvre pas, ou Power BI dit que le format n'est pas pris en charge | Vérifiez les 3 options en préversion (§1) et redémarrez. Ouvrez bien le fichier `.pbip`, pas un dossier. Mettez Power BI Desktop à jour. |
| Une page « ne s'ouvre pas » ou des visuels sont remplacés par une croix | Ouvrez la page **Secours** : si elle s'affiche, les données arrivent ; le souci vient de Deneb (§6). Sinon, le souci vient de la connexion (§3). |
| Un visuel Deneb reste vide | 1. Vérifiez qu'il y a des données (page Secours). 2. Dans *Mise en forme → Développeur*, vérifiez les champs liés. 3. Ouvrez *Modifier* : Deneb affiche l'erreur de la spec en bas. 4. Recollez la spec (§6). |
| Un titre de graphique est vide | Les titres calculés dépendent des mesures « Titre … » : vérifiez qu'elles existent (volet *Données*, dossier *Titres*, masquées). À défaut, tapez un titre fixe (*Mise en forme → Général → Titre → Texte*). |
| « Impossible de se connecter » / erreur 401 | Jeton expiré ou mal collé : régénérez-le (§3). Vérifiez que le warehouse est démarré. |
| Les heures semblent décalées de 1 à 2 h | `heure_paris` est lu tel quel (le fuseau est retiré, pas converti). Les graphiques utilisent surtout `heure_du_jour` : comparez les deux colonnes dans la table. |
| Les valeurs vrai/faux sont affichées en texte | Dans *Transformer les données*, vérifiez l'étape *Types* (`type logical`). |
| Les jours ne sont pas dans l'ordre | `jour_semaine` est trié par `jour_semaine_ordre` (lundi = 1) : vérifiez ce tri dans *Outils de colonne*. |

## 8. Les mesures du modèle

Visibles : `Taux pénurie` (affiché « Temps passé vide (%) ») · `Taux saturation` (« Temps passé plein (%) ») · `Taux pénurie / saturation avec panne` · `Taux pénurie / saturation sans panne` · `Heures avec panne observées`. Masquées (conservées) : `Nb stations` · `Dernière heure` · `Écart pénurie (pts)` · `Écart saturation (pts)` · `Part heures avec panne ferrée` · les `Sous-titre …` et `Mise à jour des données`. Colonne ajoutée : `panne_imprevue_libelle` (Oui / Non, pour le segment « Panne imprévue » ; les mesures « sans panne » retirent aussi le filtre sur cette colonne).
Les mesures « avec panne » ne comptent que les stations à moins de 300 m d'un arrêt ferré (`station_proche_ferre_300m`) et les heures où `panne_ferree_300m` est vraie ; « sans panne » compare aux heures où elle est fausse. Le segment *Panne imprévue* ne restreint que le côté « avec panne ».
Des mesures masquées (`n_penurie`, `n_service`, `n_saturation`, `capacite_max`, `lon_moy`, `lat_moy`, `temperature_moy`, `seuil_temperature`, les 7 `Titre …`, et pour la table météo 3 ans les mesures d'appui décrites au §6 ter) servent aux graphiques Deneb, aux titres et à la page Secours.

## 9. Choix de design

Détail complet, avec les contrôles chiffrés et les itérations de rendu : voir [`DESIGN.md`](DESIGN.md).

**Compétences utilisées.** `dataviz` (méthode : forme d'abord, couleur selon le rôle, validateur de palette, marques fines, anti-patterns) et `artifact-design` (direction artistique liée au sujet, neutres choisis, jetons de couleur). Il n'existe pas de compétence propre à Power BI ou Vega-Lite ; j'ai appliqué à la place les pratiques de Tufte, Few, Datawrapper et Observable Plot.

**Concept.** « Paris la nuit vue depuis le trottoir » : un fond bleu-nuit sur lequel chaque station s'allume en braise quand elle n'a plus de vélo.
- *Mode sombre* : les marques lumineuses (pénurie forte = case la plus claire) ressortent sans effort, c'est plus confortable en salle projetée, et tous les textes restent à plus de 4,5:1 de contraste.

**Palette.** Neutres bleu-nuit `#0E1420` / `#161E2E` ; pénurie orange `#E26828` ; saturation cyan `#2A9FD0` ; panne magenta `#D8478A` ; pluie violet `#7F6AE6` ; « sans » toujours en gris `#9AA9C4`.
- *Orange contre cyan* : c'est l'axe de couleur le mieux conservé en daltonisme et le plus opposé en sens (manque / trop-plein) : les deux ne peuvent pas se confondre (ΔE ≥ 22 même en protanopie).
- *Une couleur = un sens sur tout le rapport* : le lecteur n'a jamais à réapprendre la légende d'une page à l'autre.
- *Rampe « braise »* (une seule teinte, du presque-fond au pêche clair) : plus c'est clair, plus il manque de vélos ; la luminosité reste ordonnée même sans voir les couleurs.

**Typographie.** Segoe UI partout (sa variante semi-gras pour les titres et les chiffres) : lisible en projection, déjà présente sur Windows, donc rendu identique dans Power BI et dans Deneb.

**Mise en page.** Grille de 1280 × 720 : marges de 24 px, gouttières de 16 px, coins arrondis de 12 px, filtres sur une seule ligne en haut, chiffres clés avant les détails.
- *Titres qui énoncent la conclusion* (« Les pénuries explosent à 8 h ») : on lit le message avant d'étudier le graphique.
- *Étiquetage direct, grilles quasi invisibles, pas de bordures* : l'encre sert aux données, pas au décor.

## 10. Régénérer ou contrôler le projet (facultatif)

Les scripts de `outils/` fabriquent tous les fichiers à partir d'un seul fichier de couleurs (`outils/palette.json`) :

```bash
pip install vl-convert-python pillow jsonschema numpy   # + shapely pour preparer_fond.py
python3 outils/construire.py            # génère le thème, les specs, le modèle, le rapport, DESIGN.md puis valide tout
python3 outils/construire.py --apercus  # + recalcule les PNG de apercus/
```

La validation vérifie : couleurs (contrastes, daltonisme) ; chaque spec Deneb contre le schéma Vega-Lite 6 ; chaque JSON du projet contre les schémas officiels Microsoft ; cohérence modèle / visuels / specs ; absence de secret.

## 11. Ce qui n'a pas pu être vérifié (honnêtement)

- L'ouverture réelle dans Power BI Desktop, le rendu final des visuels et le chargement Databricks.
- La syntaxe TMDL a été écrite d'après la documentation Microsoft mais pas compilée par Power BI.
- Dans le JSON des visuels, les propriétés propres à chaque type (`objects` : segments, cartes, Deneb) ne sont pas décrites par les schémas Microsoft : elles suivent des exemples publics. Le filtre « 20 premiers » du tableau et les titres calculés par mesure en font partie.
- Le comportement exact de Deneb pour les champs renommés, les booléens, la locale `fr-FR`, le réglage `dataLimit.override` et le fond `geoshape` (rendu validé seulement avec vl-convert).
- Les couleurs par série des visuels natifs de la page Secours (sélecteurs `scopeId` / `metadata`).
- Le décalage horaire éventuel de `heure_paris` selon la façon dont Databricks stocke l'horodatage.
