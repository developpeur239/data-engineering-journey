"""Régénère DESIGN.md à partir de palette.json et du rapport de verifier_palette.py (le document reste synchronisé)."""
import commun as c

P, R = c.P, c.RAMPE
rap = (c.ICI / "rapport_palette.txt").read_text(encoding="utf-8").strip()
S, F, T, TY, G = P["serie"], P["fond"], P["texte"], P["typo"], P["grille_page"]
import couleurs as co
import specs as sp

_util = co.utilisations({n: f() for n, (f, _) in sp.SPECS.items()})


def _tableau_sens():
    lignes = ["| Couleur | Hex | Sens unique | Où elle apparaît |", "|---|---|---|---|"]
    for nom, hexa, sens, ou in co.SENS:
        h = f"`{hexa}`" if hexa else "`" + " ".join(R) + "`"
        lignes.append(f"| {nom} | {h} | {sens} | {ou} |")
    return "\n".join(lignes)


md = f"""# Direction artistique : tableau de bord Vélib'

> Ce document a été écrit **avant** tout JSON du rapport (thème, specs Deneb, pages), puis mis à jour après les itérations de rendu (§10).
> Les couleurs et tailles vivent dans un seul fichier, `outils/palette.json` ; le thème Power BI, les specs Deneb et ce document en dérivent.

## 0. Compétences consultées

| Compétence | Utilisée pour |
|---|---|
| `dataviz` (lue en entier : méthode, choix de la forme, formule de couleur, marques, interaction, anti-patterns, palette de référence, validateur `validate_palette.js`) | choix de la forme, rôle de chaque couleur, contrôles de contraste et de daltonisme, règles de marques fines, infobulles |
| `artifact-design` (lue) | discipline de direction artistique : concept lié au sujet, neutres choisis (pas de gris pur), couleurs en jetons, cohérence des éléments répétés |

**Il n'existe pas de compétence dédiée à Power BI ni à Vega-Lite** dans cet environnement. À défaut, j'applique les pratiques publiées de Tufte (rapport données/encre, pas de décor inutile), Stephen Few (tableaux de bord lisibles d'un coup d'œil, un message par visuel), Datawrapper (titres qui énoncent la conclusion, étiquetage direct, annotations) et Observable Plot (marques simples, échelles explicites).

Quand la règle de l'utilisateur et celle du skill divergent, celle de l'utilisateur gagne : par exemple, il demande de l'étiquetage direct plutôt que des légendes ; les légendes ne subsistent que là où le direct est impossible (échelle de couleur de la carte et de la heatmap, pluie/sans pluie).

## 1. Concept visuel (une phrase)

**« Paris la nuit vue depuis le trottoir : un fond d'encre bleu-nuit sur lequel chaque station s'allume en braise quand elle n'a plus de vélo. »**

## 2. Mode : sombre

- le sujet (des stations qui « s'allument ») et la carte stylisée, sans fond de plan, gagnent en lisibilité quand les marques *brillent* sur un fond sombre : une forte pénurie est la valeur la plus claire de l'écran, donc la première chose vue ;
- le rapport sera projeté en soutenance : un fond sombre limite l'éblouissement dans une salle tamisée ;
- les contrastes restent ≥ 4,5:1 pour tout le texte (§4) : le mode sombre ne coûte rien en accessibilité.

## 3. Palette

Neutres teintés bleu-nuit (aucun gris pur, ni noir pur, ni blanc pur) :

| Rôle | Hex | Usage |
|---|---|---|
| Fond de page | `{F['page']}` | arrière-plan du rapport |
| Surface de carte | `{F['carte']}` | fond de chaque visuel (rayon {G['rayon']} px) |
| Survol / infobulle | `{F['survol']}` | infobulles, bandes des heures de pointe |
| Grille | `{F['grille']}` | quadrillage, très discret, 1 px |
| Grille claire | `{F['grille_claire']}` | repères en pointillés (moyenne de température), contraste 3:1 sur la carte |
| Texte principal | `{T['principal']}` | titres, valeurs, KPI |
| Texte secondaire | `{T['secondaire']}` | sous-titres, libellés d'axes |
| Texte discret | `{T['discret']}` | notes, repères, titres d'axes |

Couleurs de données, une par *sens* (elles ne changent jamais d'une page à l'autre) :

| Sens | Hex | Remarque |
|---|---|---|
| **Pénurie** (plus de vélo) | `{S['penurie']}` orange braise | chaud = manque |
| **Saturation** (plus de place) | `{S['saturation']}` cyan | froid = trop-plein ; orange/bleu est l'axe le mieux conservé en daltonisme |
| **Panne ferrée** | `{S['panne']}` magenta | la perturbation |
| **Pluie** | `{S['pluie']}` violet | la météo |
| Neutre (« sans panne », « sans pluie ») | `{S['neutre']}` | l'état de référence est toujours gris |

Pénurie et saturation ne sont jamais confondables : teintes opposées (orange / cyan), ΔE ≥ 29 en vision normale et ≥ 22 en protanopie et deutéranopie.

Rampe séquentielle (taux de pénurie, carte et heatmap) : **une seule teinte** (orange, {P['sequentiel_penurie']['teinte_deg']}°), de sombre (peu de pénurie, la case « s'éteint » dans le fond) à clair (beaucoup) :
`{'` → `'.join(R)}`.
La luminosité est strictement croissante, y compris sous protanopie et deutéranopie.

Pas d'échelle divergente : l'écart « avec panne − sans panne » est porté par le **signe + / −** du texte ; le trait de liaison des haltères est toujours rose (couleur de la panne).

## 4. Contrôles faits par script (`outils/verifier_palette.py`)

Le script calcule : contraste WCAG du texte et des marques, séparation OKLab ΔE×100 de toutes les paires de séries en vision normale / protanopie / deutéranopie / tritanopie (matrices de Machado 2009), monotonie de la rampe. Les couleurs de série ont aussi été validées avec le validateur du skill `dataviz` (`validate_palette.js --mode dark --surface {F['carte']} --pairs all` : bande de luminosité, chroma, CVD, vision normale, contraste : tous PASS). La seule paire basse est pénurie↔panne en tritanopie (ΔE 4,8, daltonisme très rare), couverte par l'étiquetage direct et parce que ces deux séries ne figurent jamais dans le même graphique.

Règle absolue : **jamais de rouge/vert seuls**, et jamais la couleur seule pour porter une information : chaque série est aussi nommée (étiquette directe, axe) ou codée par la forme (anneau creux = sans panne, disque plein = avec panne, trait pointillé = pluie).

```
{rap}
```

## 5. Typographie

Une seule famille : **{TY['famille']}** (présente sur tout poste Windows qui ouvre Power BI Desktop ; variante grasse « {TY['famille_gras']} »). Tailles fixes. Côté Power BI les tailles sont en pt (1 pt = 1,33 px à l'écran), dans les graphiques Deneb en px :

| Élément | Taille | Graisse |
|---|---|---|
| Valeur de KPI | {TY['taille_kpi']} pt | semi-gras |
| Titre de visuel (énonce la conclusion) | {TY['taille_titre']} pt | semi-gras |
| Sous-titre (ce que mesure le graphique, unité) | {TY['taille_sous_titre']} pt | normal |
| Libellés / étiquettes directes (Deneb) | {TY['taille_label']} px | normal |
| Axes et graduations (Deneb) | {TY['taille_axe']} px | normal |
| Infobulle | {TY['taille_infobulle']} | normal |

Nombres au format français (virgule décimale, espace avant « % ») : les visuels Deneb sont réglés sur la locale `fr-FR`.

## 6. Grille de mise en page (page {G['largeur']} × {G['hauteur']} px)

- marge extérieure **{G['marge']} px**, gouttière entre visuels **{G['gouttiere']} px**, rayon des coins **{G['rayon']} px** ;
- largeur utile 1232 px : deux colonnes de 608 px, ou quatre KPI de 296 px, ou trois KPI de 400 px ;
- **bandeau d'en-tête** (y 12 → 68) : titre de page à gauche (énonce la conclusion), filtres à droite : tous les filtres sont **sur une seule ligne, au-dessus des graphiques**, avec leur libellé ;
- **rangée de KPI** (y 80, hauteur 104) quand la page en a ; **zone des graphiques** ensuite (y 200, hauteur 496), jusqu'à y 696 (marge basse {G['marge']} px).

| Page | Disposition (largeur × hauteur en px) |
|---|---|
| Vue d'ensemble | 4 KPI de 296 × 104 ; heatmap 608 × 496 à gauche, rythme de la journée 608 × 496 à droite |
| Carte des stations | carte stylisée 800 × 616 ; tableau « top 20 » 416 × 616 |
| Effet des pannes | 3 KPI de 400 × 104 ; haltères 800 × 340 puis « Comment lire » 800 × 140 ; « Méthode » 416 × 496 |
| Effet de la météo | barres 400 × 300 puis « Comment lire » 400 × 300 à gauche ; nuage 816 × 300 puis courbes 816 × 300 à droite |
| Météo · 3 ans de compteurs | 4 KPI de 296 × 96 ; grille 2 × 2 de graphiques de 448 × 244 ; « Méthode et limites » 320 × 504 à droite |
| Secours (cachées) | grille 3 × 2 de visuels natifs de 400 × 300 ; grille 2 × 2 pour la météo 3 ans |

## 7. Règles graphiques

1. Pas de bordure inutile : les cartes ont un fond, pas de contour visible (la bordure a la couleur du fond et ne sert qu'à arrondir les coins) ; les vues Vega n'ont pas de cadre (`view.stroke = null`).
2. Grille très claire (`{F['grille']}`, 1 px, 0,6 d'opacité), pas de ligne d'axe.
3. **Étiquetage direct** : le nom de la série est écrit sur le graphique (pics de pénurie et de saturation, « sans panne / avec panne ») ; une légende ne subsiste que quand le direct est impossible.
4. **Titres qui énoncent la conclusion**, jamais écrits dans une spec : une mesure DAX par visuel (`Titre heatmap`, `Titre rythme`, `Titre carte`, `Titre pannes`, `Titre pluie`, `Titre nuage`, `Titre courbes`) calcule la phrase à partir de `gold_station_heure`, en respectant filtres et segments, avec un texte neutre si les données sont vides. Nombres au format français explicite (`FORMAT(x, "#,##0", "fr-FR")`). Le titre doit correspondre à une valeur affichée : celui des haltères porte sur la première ligne (« Pénurie · heure de pointe »).
5. **Unités toujours visibles** : « % des relevés », « pts », « °C ».
6. Pas de double axe, pas de 3D, pas de camembert, pas d'arc-en-ciel.
7. Marques fines : lignes 3 px, points ≥ 8 px, barres arrondies de 4 px, 2 px d'écart entre cases (trait de la couleur du fond).
8. Le texte ne prend jamais la couleur d'une série : valeurs et libellés en gris clair ; c'est la pastille ou la forme voisine qui porte la couleur.

## 8. Infobulles et interactions

- Infobulle : fond `{F['survol']}`, texte {TY['taille_infobulle']}, une ligne « libellé : valeur » par information ; jamais d'information qui n'existe que dans l'infobulle (le survol enrichit, il ne conditionne rien).
- Survol : la marque survolée garde son opacité (1), les autres passent à **0,35–0,45** ; sur la carte, un **halo** (anneau clair) entoure la station survolée.
- Sélection croisée désactivée dans les visuels Deneb (pas de filtrage accidentel) ; les filtres passent par les segments en haut de page.

## 9. Limites assumées

- Segoe UI n'est pas disponible dans mon environnement Linux : les aperçus PNG de `apercus/` sont rendus avec une police de remplacement (Arial/Liberation Sans, un peu plus large). Ils servent à juger la composition, les couleurs et les collisions, pas le rendu pixel par pixel.
- Les aperçus utilisent des **données fictives** (`outils/donnees_apercu.py`) : les titres et valeurs qu'on y lit ne sont pas des résultats.
- Les titres calculés (mesures DAX) ne sont pas visibles dans les aperçus du graphique seul ; l'aperçu les reconstitue avec les données fictives.

## 10. Revue visuelle : ce que j'ai vu et corrigé (≥ 2 itérations par visuel)

Chaque PNG a été regardé puis critiqué avec la méthode `dataviz` (forme, couleur par rôle, marques fines, étiquetage, collisions) avant correction.

| Visuel | Itération 1 : défauts relevés | Corrections |
|---|---|---|
| Heatmap | axe des heures absent ; rampe qui tire sur le brun terne ; titre non cohérent avec la case entourée ; trou entre sous-titre et grille | axes fusionnés correctement ; rampe retravaillée (début quasi neutre, la case « s'éteint ») ; titre calculé depuis les données ; marges resserrées ; légende raccourcie |
| Rythme | libellé « pointe du matin » écrasé par le pic de pénurie | libellés des bandes placés au pied de la bande |
| Carte | cercles translucides par défaut (opacité 0,7 des marques Vega-Lite) → teintes olive fausses ; carte trop petite ; repères illisibles ; légende de classes à échelle trompeuse | opacité 1 forcée ; échelle de projection recalée sur Paris et la proche banlieue ; repères avec halo de la couleur du fond ; 7 classes lisibles ; légende en carte arrondie |
| Haltères | lignes sans repère horizontal | repères pointillés par ligne ; étiquettes « sans panne / avec panne » sur la première ligne seulement |
| Barres pluie | légende posée sur l'étiquette de la plus haute barre ; carte trop haute pour 4 barres | légende placée sous l'axe ; visuel ramené à 400 × 300 et accompagné du bloc « Comment lire » |
| Nuage | étiquette « tendance lissée » recouverte par les points ; titre d'axe redondant avec « °C » | halo de la couleur du fond derrière l'étiquette, placée à gauche ; titre d'axe supprimé ; légende dans le coin libre |
| Courbes | place réservée à la légende qui écrase le tracé ; pluie indiscernable sans couleur | légende dans le coin libre ; pluie = pointillé **et** violet |

Page « Météo · 3 ans de compteurs » (4 visuels) :

| Visuel | Défaut relevé | Correction |
|---|---|---|
| Haltères période | libellés « avec pluie » et « sans pluie » superposés (valeurs proches) ; titre tronqué | libellés placés de part et d'autre des disques ; l'aperçu fait passer les titres à la ligne comme Power BI |
| Effet à conditions égales | note recouverte par l'étiquette d'une barre ; titre sur 3 lignes | marge sous les barres (axe prolongé de 80 %) ; titre raccourci (« −15,9 % en semaine, −20,6 % le week-end ») |
| Classes de température | note et maximum annoté superposés | marge en haut de l'axe, note alignée à gauche, maximum annoté au-dessus de la barre |
| Profil horaire | légende posée sur le pic du soir | légende en haut à gauche, zone libre de la nuit |

Troisième tour (page météo 3 ans) :

| Visuel | Défaut relevé | Correction |
|---|---|---|
| Haltères période | sur l'échelle commune 0–170, la ligne « Nuit » (13,9 → 11,0) est réduite à un point : l'écart ne se voit pas | **échelle commune conservée** (une échelle par ligne ferait paraître la nuit aussi fréquentée que la pointe et casserait la comparaison entre périodes) ; colonne de valeurs à droite de chaque ligne : « sans → avec » (ex. « 13,9 → 11,0 ») puis l'écart en gras (« −20,6 % ») ; le nombre dit ce que le dessin ne peut pas montrer pour la nuit |
| Classes de température | libellés et découpage non conformes à la colonne source | valeurs de `classe_temperature` reprises telles quelles (« 1. moins de 5 °C », « 2. 5 à 12 °C », « 3. 12 à 20 °C », « 4. 20 à 27 °C », « 5. 27 °C et plus ») ; le préfixe numérique ne sert qu'au tri et est retiré à l'affichage (axe, infobulle, titre dynamique) ; le titre reprend la classe réelle du maximum (« 20 à 27 °C (193,9 par compteur) ») |

Deuxième tour (retours de relecture) :

| Visuel | Défaut relevé | Correction |
|---|---|---|
| Barres | la valeur 10,1 % frôlait la légende ; pas de marge en haut de l'axe | légende sous l'axe ; point invisible à 125 % du maximum pour garder de l'air au-dessus de la plus haute barre |
| Carte | pas de repère géographique ; « 1450 » sans espace | fond très discret (limite de Paris, Seine et canaux, `deneb_specs/paris_fond.json`) ; nombres formatés en `fr-FR` |
| Haltères | titre sans valeur correspondante ; lignes trop espacées ; trait vert-bleu en plus du rose | titre calculé sur la ligne « Pénurie · heure de pointe » ; carte ramenée à 800 × 340 ; trait toujours rose, le signe +/− dit le sens |
| Nuage | « tendance lissée » au milieu des points | étiquette au bout droit de la courbe, avec halo de la couleur du fond |
| Courbes | pas de repère des heures de pointe | libellés « pointe du matin / pointe du soir » comme dans le rythme |

`apercus/planche.png` rassemble les 7 visuels pour juger l'harmonie d'ensemble.

## 11. Un sens par couleur dans tout le rapport

Vérifié automatiquement (`outils/couleurs.py`, lancé par `verifier_coherence.py`) : chaque spec n'utilise que ses couleurs de données autorisées, et aucune couleur hors palette.

{_tableau_sens()}

Les neutres de fond (`{F['page']}`, `{F['carte']}`, `{F['survol']}`, `{F['grille']}`, `{F['grille_claire']}`) ne portent jamais de donnée. Là où la météo est le sujet (barres, nuage, courbes), la couleur code *pluie / sans pluie* ; la pénurie et la saturation y sont désignées par l'axe ou le libellé, pas par la couleur. Les visuels natifs de la page « Secours » reprennent les mêmes couleurs par série (réglage explicite, car le thème attribue sinon ses couleurs dans l'ordre).
"""
(c.RACINE / "DESIGN.md").write_text(md, encoding="utf-8")
print("ok DESIGN.md", len(md))
