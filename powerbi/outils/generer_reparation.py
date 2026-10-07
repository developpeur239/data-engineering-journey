"""Écrit REPARER_TABLE.md : les colonnes (Power Query) et mesures (DAX) à recréer si la table a été réimportée."""
import commun as c
import generer_modele as gm

mesures = []
for nom, dax, fmt, dossier, masquee in gm.MESURES:
    mesures.append(f"### `{nom}`" + ("  (masquée)" if masquee else "") + f"\n\nFormat : `{fmt or 'Général'}`\n\n```dax\n{nom} =\n{dax}\n```\n")

md = f"""# Réparer la table après un nouvel import

Si, après avoir réimporté ou remplacé la table, des champs ont disparu (`pluie_libelle`, `jour_nom`, `periode`, `jour_semaine_ordre`, `seuil_temperature`, etc.),
c'est normal : **ces champs ne viennent pas de Databricks**.

| Ce qui a disparu | Où c'est stocké | Pourquoi c'est parti |
|---|---|---|
| Colonnes `jour_semaine_ordre`, `jour_nom`, `periode`, `pluie_libelle` | **dans la table du modèle Power BI** (colonnes calculées en DAX) ; elles ne viennent pas de Databricks | si la table est supprimée puis recréée, tout ce qui a été ajouté dessus disparaît |
| Mesures (`seuil_temperature`, `Taux pénurie`, `Titre …`, etc.) | **dans la table du modèle** | idem |

Tout ce qui a été ajouté par-dessus les données Databricks (colonnes calculées et mesures) se fait **dans Power BI** (DAX), pas dans Power Query. Power Query ne sert plus qu'à charger la table et à typer ses colonnes.

Pour éviter ça la prochaine fois : **ne supprimez pas la table**. Pour changer de source, utilisez *Transformer les données → Modifier les paramètres* (`Hote`, `CheminHTTP`, `Catalogue`), ou ouvrez la requête et modifiez l'étape *Source*.

> Hypothèse : la table s'appelle `{gm.TABLE}`. Si votre nouvelle table a un autre nom, remplacez ce nom dans le DAX ci-dessous.

## Étape 1. Recréer les 4 colonnes (dans Power BI, en DAX)

Ordre important : la 2e colonne utilise la 1re.

Pour chacune : dans la vue **Tableau** ou **Rapport**, clic droit sur la table dans le volet *Données* → **Nouvelle colonne**, collez la formule, **Entrée**.

```dax
{chr(10).join(f"{n} = {d}" + chr(10) for n, _, _, d in gm.CALCULEES).rstrip()}
```

Ensuite :
- **Tri des jours** : cliquez sur la colonne `jour_nom` (puis aussi `jour_semaine` si elle existe) → *Outils de colonne → Trier par colonne → `jour_semaine_ordre`*.
- **Résumé** : pour chaque colonne, *Outils de colonne → Résumé → Ne pas résumer*.

Conditions : `date_paris` doit être de type Date, `heure_de_pointe` et `il_pleut` de type Vrai/Faux. Si une formule signale « colonne introuvable », le nom de cette colonne a changé dans votre nouvelle table.

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
