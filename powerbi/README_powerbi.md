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

| Page | Contenu |
|---|---|
| **Vue d'ensemble** | 4 cartes (nombre de stations, taux de pénurie, taux de saturation, dernière heure) ; carte de chaleur heure × jour ; rythme de la journée avec les heures de pointe annotées ; segments Période et Week-end |
| **Carte des stations** | carte stylisée sans fond de plan (taille = capacité, couleur = taux de pénurie, halo au survol) ; tableau des 20 stations les plus souvent vides ; segments Heure du jour et Heure de pointe |
| **Effet des pannes** | haltères « sans panne → avec panne » (pénurie et saturation, pointe / hors pointe ; le titre porte sur la ligne « Pénurie · heure de pointe », le trait est toujours rose et le signe +/− donne le sens) ; 3 cartes (écart pénurie, écart saturation, part d'heures avec panne ferrée) ; encadré « Méthode » ; segment Panne imprévue |
| **Effet de la météo** | barres avec / sans pluie ; nuage température × pénurie avec tendance ; courbes par heure avec / sans pluie ; encadré « Comment lire » |
| **Secours** (cachée) | un équivalent en visuels Power BI natifs de chaque graphique Deneb |

Les **titres** des 7 graphiques Deneb sont **calculés** par une mesure DAX chacun (`Titre heatmap`, `Titre rythme`, `Titre carte`, `Titre pannes`, `Titre pluie`, `Titre nuage`, `Titre courbes`) : aucun chiffre ni constat n'est écrit dans une spec. Chaque mesure est liée au titre du visuel Power BI (*Format → Titre → Texte → fx*), respecte les filtres et segments, et affiche un texte neutre si les données sont vides. Les nombres sont formatés en français quelle que soit la machine : `FORMAT(x, "#,##0", "fr-FR")` donne « 1 450 » et `FORMAT(x, "0.0", "fr-FR")` donne « 3,0 » (le troisième argument impose la locale ; un motif du type `"# ##0"` n'est pas fiable en DAX). Seul le sous-titre est fixe.
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

`Nb stations` · `Taux pénurie` · `Taux saturation` · `Dernière heure` · `Taux pénurie / saturation avec panne` · `Taux pénurie / saturation sans panne` · `Écart pénurie (pts)` · `Écart saturation (pts)` · `Part heures avec panne ferrée`.
Les mesures « avec panne » ne comptent que les stations à moins de 300 m d'un arrêt ferré (`station_proche_ferre_300m`) et les heures où `panne_ferree_300m` est vraie ; « sans panne » compare aux heures où elle est fausse. Le segment *Panne imprévue* ne restreint que le côté « avec panne ».
Des mesures masquées (`n_penurie`, `n_service`, `n_saturation`, `capacite_max`, `lon_moy`, `lat_moy`, `temperature_moy`, `seuil_temperature`, les 7 `Titre …`) servent aux graphiques Deneb, aux titres et à la page Secours.

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
