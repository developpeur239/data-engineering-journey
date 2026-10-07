"""Écrit REPARER_TABLE.md : les colonnes (Power Query) et mesures (DAX) à recréer si la table a été réimportée."""
import commun as c
import generer_modele as gm

mesures = []
for nom, dax, fmt, dossier, masquee in gm.MESURES:
    mesures.append(f"### `{nom}`" + ("  (masquée)" if masquee else "") + f"\n\nFormat : `{fmt or 'Général'}`\n\n```dax\n{nom} =\n{dax}\n```\n")

md = f"""# Réparer la table après un nouvel import

Si, après avoir réimporté ou remplacé la table, des champs ont disparu (`pluie_libelle`, `jour_nom`, `periode`, `jour_semaine_ordre`, `seuil_temperature`, etc.),
c'est normal : **ces champs ne viennent pas de Databricks**.

| Ce qui a disparu | D'où ça venait | Pourquoi c'est parti |
|---|---|---|
| Colonnes `jour_semaine_ordre`, `jour_nom`, `periode`, `pluie_libelle` | étapes ajoutées **dans la requête Power Query** (pas dans la table Gold) | la nouvelle requête ne contient plus ces étapes |
| Mesures (`seuil_temperature`, `Taux pénurie`, `Titre …`, etc.) | **stockées dans la table** du modèle | si la table est supprimée puis recréée, ses mesures disparaissent avec elle |

Pour éviter ça la prochaine fois : **ne supprimez pas la table**. Pour changer de source, utilisez *Transformer les données → Modifier les paramètres* (`Hote`, `CheminHTTP`, `Catalogue`), ou ouvrez la requête et modifiez l'étape *Source*.

> Hypothèse : la table s'appelle `{gm.TABLE}`. Si votre nouvelle table a un autre nom, remplacez ce nom dans le DAX ci-dessous.

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
        each if [date_paris] = null then null else {{"lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"}}{{Date.DayOfWeek([date_paris], Day.Monday)}}, type text),
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

{chr(10).join(mesures)}
## Étape 3. Relier à nouveau les visuels

Un visuel dont un champ a disparu affiche « Corrigez ce visuel » ou reste vide. Pour chaque graphique Deneb, glissez à nouveau dans le puits **Valeurs** les champs listés dans `deneb_specs/_champs_par_visuel.json` (même ordre, sans renommer). Les visuels natifs se corrigent en re-glissant le champ manquant.

## Plus simple : repartir du projet

Si trop de choses manquent, rouvrez `velib_dashboard.pbip` depuis le zip : le modèle contient déjà tout (colonnes, mesures, tri). Il suffit alors de ressaisir le jeton Databricks.
"""
(c.RACINE / "REPARER_TABLE.md").write_text(md, encoding="utf-8")
print("ok REPARER_TABLE.md", len(md))
