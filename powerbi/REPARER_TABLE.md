# Réparer la table après un nouvel import

Si, après avoir réimporté ou remplacé la table, des champs ont disparu (`pluie_libelle`, `jour_nom`, `periode`, `jour_semaine_ordre`, `seuil_temperature`, etc.),
c'est normal : **ces champs ne viennent pas de Databricks**.

| Ce qui a disparu | D'où ça venait | Pourquoi c'est parti |
|---|---|---|
| Colonnes `jour_semaine_ordre`, `jour_nom`, `periode`, `pluie_libelle` | étapes ajoutées **dans la requête Power Query** (pas dans la table Gold) | la nouvelle requête ne contient plus ces étapes |
| Mesures (`seuil_temperature`, `Taux pénurie`, `Titre …`, etc.) | **stockées dans la table** du modèle | si la table est supprimée puis recréée, ses mesures disparaissent avec elle |

Pour éviter ça la prochaine fois : **ne supprimez pas la table**. Pour changer de source, utilisez *Transformer les données → Modifier les paramètres* (`Hote`, `CheminHTTP`, `Catalogue`), ou ouvrez la requête et modifiez l'étape *Source*.

> Hypothèse : la table s'appelle `gold_station_heure`. Si votre nouvelle table a un autre nom, remplacez ce nom dans le DAX ci-dessous.

## Étape 1. Recréer les 4 colonnes (Power Query)

1. *Accueil → Transformer les données.*
2. Cliquez sur votre requête (la table), puis *Accueil → Éditeur avancé*.
3. Repérez la dernière ligne avant le mot `in`, et le nom de la dernière étape (par exemple `#"Type modifié"`). Ajoutez une virgule à la fin de cette ligne, puis collez les 4 étapes ci-dessous, en remplaçant `DERNIERE_ETAPE` par ce nom.
4. Remplacez la dernière ligne (celle après `in`) par `Pluie`.
5. *Terminé*, puis *Fermer et appliquer*.

```m
    JourOrdre = Table.AddColumn(DERNIERE_ETAPE, "jour_semaine_ordre",
        each if [date_paris] = null then null else Date.DayOfWeek([date_paris], Day.Monday) + 1, Int64.Type),
    JourNom = Table.AddColumn(JourOrdre, "jour_nom",
        each if [date_paris] = null then null else {"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}{Date.DayOfWeek([date_paris], Day.Monday)}, type text),
    Periode = Table.AddColumn(JourNom, "periode",
        each if [heure_de_pointe] = true then "Heure de pointe" else "Hors pointe", type text),
    Pluie = Table.AddColumn(Periode, "pluie_libelle",
        each if [il_pleut] = true then "Pluie" else "Sans pluie", type text)
```

Conditions : `date_paris` doit être de type **Date**, `heure_de_pointe` et `il_pleut` de type **Vrai/Faux**. Si l'éditeur signale une erreur « la colonne est introuvable », le nom de la colonne a changé dans votre nouvelle table.

Ensuite, remettez le tri des jours : cliquez sur la colonne `jour_semaine` (puis aussi sur `jour_nom`) → *Outils de colonne → Trier par colonne → `jour_semaine_ordre`*.

## Étape 2. Recréer les mesures (DAX)

Pour chaque mesure : clic droit sur la table dans le volet *Données* → **Nouvelle mesure**, collez le texte, validez. Pour les mesures masquées, clic droit → *Masquer dans la vue Rapport*. Pour le format, sélectionnez la mesure puis *Outils de mesure → Format*.

Si **seule** `seuil_temperature` manque, ne recréez que celle-là. Sinon, créez les mesures dans cet ordre (les dernières utilisent les premières).

### `Nb stations`

Format : `#,0`

```dax
Nb stations =
DISTINCTCOUNT(gold_station_heure[station_id])
```

### `Taux pénurie`

Format : `0.0%`

```dax
Taux pénurie =
DIVIDE(SUM(gold_station_heure[nb_releves_penurie]), SUM(gold_station_heure[nb_releves_en_service]))
```

### `Taux saturation`

Format : `0.0%`

```dax
Taux saturation =
DIVIDE(SUM(gold_station_heure[nb_releves_saturation]), SUM(gold_station_heure[nb_releves_en_service]))
```

### `Dernière heure`

Format : `dd/MM HH:mm`

```dax
Dernière heure =
MAX(gold_station_heure[heure_paris])
```

### `Taux pénurie avec panne`

Format : `0.0%`

```dax
Taux pénurie avec panne =
CALCULATE([Taux pénurie], gold_station_heure[station_proche_ferre_300m] = TRUE(), gold_station_heure[panne_ferree_300m] = TRUE())
```

### `Taux pénurie sans panne`

Format : `0.0%`

```dax
Taux pénurie sans panne =
CALCULATE([Taux pénurie], REMOVEFILTERS(gold_station_heure[panne_ferree_imprevue_300m]), gold_station_heure[station_proche_ferre_300m] = TRUE(), gold_station_heure[panne_ferree_300m] = FALSE())
```

### `Taux saturation avec panne`

Format : `0.0%`

```dax
Taux saturation avec panne =
CALCULATE([Taux saturation], gold_station_heure[station_proche_ferre_300m] = TRUE(), gold_station_heure[panne_ferree_300m] = TRUE())
```

### `Taux saturation sans panne`

Format : `0.0%`

```dax
Taux saturation sans panne =
CALCULATE([Taux saturation], REMOVEFILTERS(gold_station_heure[panne_ferree_imprevue_300m]), gold_station_heure[station_proche_ferre_300m] = TRUE(), gold_station_heure[panne_ferree_300m] = FALSE())
```

### `Écart pénurie (pts)`

Format : `"+0.0"" pts"";-0.0"" pts"";0.0"" pts"""`

```dax
Écart pénurie (pts) =
([Taux pénurie avec panne] - [Taux pénurie sans panne]) * 100
```

### `Écart saturation (pts)`

Format : `"+0.0"" pts"";-0.0"" pts"";0.0"" pts"""`

```dax
Écart saturation (pts) =
([Taux saturation avec panne] - [Taux saturation sans panne]) * 100
```

### `Part heures avec panne ferrée`

Format : `0.0%`

```dax
Part heures avec panne ferrée =
DIVIDE(CALCULATE(COUNTROWS(gold_station_heure), gold_station_heure[station_proche_ferre_300m] = TRUE(), gold_station_heure[panne_ferree_300m] = TRUE()), CALCULATE(COUNTROWS(gold_station_heure), REMOVEFILTERS(gold_station_heure[panne_ferree_imprevue_300m]), gold_station_heure[station_proche_ferre_300m] = TRUE()))
```

### `n_service`  (masquée)

Format : `#,0`

```dax
n_service =
SUM(gold_station_heure[nb_releves_en_service])
```

### `n_penurie`  (masquée)

Format : `#,0`

```dax
n_penurie =
SUM(gold_station_heure[nb_releves_penurie])
```

### `n_saturation`  (masquée)

Format : `#,0`

```dax
n_saturation =
SUM(gold_station_heure[nb_releves_saturation])
```

### `capacite_max`  (masquée)

Format : `0`

```dax
capacite_max =
MAX(gold_station_heure[capacite])
```

### `seuil_temperature`  (masquée)

Format : `0.0`

```dax
seuil_temperature =
CALCULATE(AVERAGE(gold_station_heure[temperature_c]), ALLSELECTED(gold_station_heure[heure_paris]), ALLSELECTED(gold_station_heure[temperature_c]), ALLSELECTED(gold_station_heure[pluie_libelle]))
```

### `lon_moy`  (masquée)

Format : `0.00000`

```dax
lon_moy =
AVERAGE(gold_station_heure[longitude])
```

### `lat_moy`  (masquée)

Format : `0.00000`

```dax
lat_moy =
AVERAGE(gold_station_heure[latitude])
```

### `temperature_moy`  (masquée)

Format : `0.0`

```dax
temperature_moy =
AVERAGE(gold_station_heure[temperature_c])
```

### `Titre heatmap`  (masquée)

Format : `Général`

```dax
Titre heatmap =
VAR t = ADDCOLUMNS(
    SUMMARIZE(gold_station_heure, gold_station_heure[heure_du_jour], gold_station_heure[jour_semaine_ordre], gold_station_heure[jour_nom]),
    "@r", [Taux pénurie])
VAR m = TOPN(1, t, [@r], DESC)
VAR h = MAXX(m, gold_station_heure[heure_du_jour])
VAR j = MAXX(m, gold_station_heure[jour_nom])
RETURN IF(ISBLANK(h), "Où et quand manque-t-on de vélos ?", "Les pénuries culminent le " & j & " à " & h & " h")
```

### `Titre rythme`  (masquée)

Format : `Général`

```dax
Titre rythme =
VAR t = ADDCOLUMNS(VALUES(gold_station_heure[heure_du_jour]), "@r", [Taux pénurie])
VAR m = TOPN(1, t, [@r], DESC)
VAR h = MAXX(m, gold_station_heure[heure_du_jour])
RETURN IF(ISBLANK(h), "Les pénuries au fil de la journée", "Les pénuries explosent à " & h & " h")
```

### `Titre carte`  (masquée)

Format : `Général`

```dax
Titre carte =
VAR t = ADDCOLUMNS(VALUES(gold_station_heure[station_id]), "@r", [Taux pénurie])
VAR n = COUNTROWS(FILTER(t, [@r] > 0.2))
VAR total = COUNTROWS(t)
RETURN IF(total = 0, "Quelles stations manquent de vélos ?",
    FORMAT(n, "#,##0", "fr-FR") & " stations sur " & FORMAT(total, "#,##0", "fr-FR") & " sont vides plus d'un relevé sur cinq")
```

### `Titre pannes`  (masquée)

Format : `Général`

```dax
Titre pannes =
VAR e = CALCULATE([Écart pénurie (pts)], gold_station_heure[heure_de_pointe] = TRUE())
RETURN IF(ISBLANK(e), "Une panne ferrée à proximité change-t-elle la pénurie ?",
    "En heure de pointe, une panne ferrée à moins de 300 m " & IF(e >= 0, "augmente", "réduit")
    & " la pénurie de " & FORMAT(ABS(e), "0.0", "fr-FR") & " pts")
```

### `Titre pluie`  (masquée)

Format : `Général`

```dax
Titre pluie =
VAR a = CALCULATE([Taux pénurie], gold_station_heure[il_pleut] = FALSE())
VAR b = CALCULATE([Taux pénurie], gold_station_heure[il_pleut] = TRUE())
RETURN IF(ISBLANK(a) || ISBLANK(b), "Pénurie et saturation, avec et sans pluie",
    "Sous la pluie, la pénurie passe de " & FORMAT(a, "0.0%", "fr-FR") & " à " & FORMAT(b, "0.0%", "fr-FR"))
```

### `Titre nuage`  (masquée)

Format : `Général`

```dax
Titre nuage =
VAR seuil = [seuil_temperature]
VAR chaud = CALCULATE([Taux pénurie], gold_station_heure[temperature_c] >= seuil)
VAR froid = CALCULATE([Taux pénurie], gold_station_heure[temperature_c] < seuil)
RETURN IF(ISBLANK(seuil) || ISBLANK(chaud) || ISBLANK(froid), "La pénurie varie-t-elle avec la température ?",
    "Au-dessus de " & FORMAT(seuil, "0.0", "fr-FR") & " °C, la pénurie est de " & FORMAT(chaud, "0.0%", "fr-FR")
    & " contre " & FORMAT(froid, "0.0%", "fr-FR") & " en dessous")
```

### `Titre courbes`  (masquée)

Format : `Général`

```dax
Titre courbes =
VAR t = ADDCOLUMNS(VALUES(gold_station_heure[heure_du_jour]),
    "@p", CALCULATE([Taux pénurie], gold_station_heure[il_pleut] = TRUE()),
    "@s", CALCULATE([Taux pénurie], gold_station_heure[il_pleut] = FALSE()))
VAR comparables = FILTER(t, NOT ISBLANK([@p]) && NOT ISBLANK([@s]))
VAR total = COUNTROWS(comparables)
VAR plus = COUNTROWS(FILTER(comparables, [@p] > [@s]))
RETURN IF(total = 0, "À chaque heure, la pluie change-t-elle la pénurie ?",
    "Sous la pluie, la pénurie est plus haute à " & FORMAT(plus, "#,##0", "fr-FR") & " heures sur " & FORMAT(total, "#,##0", "fr-FR"))
```

## Étape 3. Relier à nouveau les visuels

Un visuel dont un champ a disparu affiche « Corrigez ce visuel » ou reste vide. Pour chaque graphique Deneb, glissez à nouveau dans le puits **Valeurs** les champs listés dans `deneb_specs/_champs_par_visuel.json` (même ordre, sans renommer). Les visuels natifs se corrigent en re-glissant le champ manquant.

## Plus simple : repartir du projet

Si trop de choses manquent, rouvrez `velib_dashboard.pbip` depuis le zip : le modèle contient déjà tout (colonnes, mesures, tri). Il suffit alors de ressaisir le jeton Databricks.
