# Direction artistique : tableau de bord Vélib'

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
| Fond de page | `#0E1420` | arrière-plan du rapport |
| Surface de carte | `#161E2E` | fond de chaque visuel (rayon 12 px) |
| Survol / infobulle | `#1F2A40` | infobulles, bandes des heures de pointe |
| Grille | `#2B3750` | quadrillage, très discret, 1 px |
| Grille claire | `#566892` | repères en pointillés (moyenne de température), contraste 3:1 sur la carte |
| Texte principal | `#EAF0FA` | titres, valeurs, KPI |
| Texte secondaire | `#A9B6CE` | sous-titres, libellés d'axes |
| Texte discret | `#8D9BB6` | notes, repères, titres d'axes |

Couleurs de données, une par *sens* (elles ne changent jamais d'une page à l'autre) :

| Sens | Hex | Remarque |
|---|---|---|
| **Pénurie** (plus de vélo) | `#E26828` orange braise | chaud = manque |
| **Saturation** (plus de place) | `#2A9FD0` cyan | froid = trop-plein ; orange/bleu est l'axe le mieux conservé en daltonisme |
| **Panne ferrée** | `#D8478A` magenta | la perturbation |
| **Pluie** | `#7F6AE6` violet | la météo |
| Neutre (« sans panne », « sans pluie ») | `#9AA9C4` | l'état de référence est toujours gris |

Pénurie et saturation ne sont jamais confondables : teintes opposées (orange / cyan), ΔE ≥ 29 en vision normale et ≥ 22 en protanopie et deutéranopie.

Rampe séquentielle (taux de pénurie, carte et heatmap) : **une seule teinte** (orange, 45°), de sombre (peu de pénurie, la case « s'éteint » dans le fond) à clair (beaucoup) :
`#362B27` → `#693926` → `#9E4A24` → `#CD642C` → `#EF844A` → `#FFA97B` → `#FFD4BC`.
La luminosité est strictement croissante, y compris sous protanopie et deutéranopie.

Pas d'échelle divergente : l'écart « avec panne − sans panne » est porté par le **signe + / −** du texte ; le trait de liaison des haltères est toujours rose (couleur de la panne).

## 4. Contrôles faits par script (`outils/verifier_palette.py`)

Le script calcule : contraste WCAG du texte et des marques, séparation OKLab ΔE×100 de toutes les paires de séries en vision normale / protanopie / deutéranopie / tritanopie (matrices de Machado 2009), monotonie de la rampe. Les couleurs de série ont aussi été validées avec le validateur du skill `dataviz` (`validate_palette.js --mode dark --surface #161E2E --pairs all` : bande de luminosité, chroma, CVD, vision normale, contraste : tous PASS). La seule paire basse est pénurie↔panne en tritanopie (ΔE 4,8, daltonisme très rare), couverte par l'étiquetage direct et parce que ces deux séries ne figurent jamais dans le même graphique.

Règle absolue : **jamais de rouge/vert seuls**, et jamais la couleur seule pour porter une information : chaque série est aussi nommée (étiquette directe, axe) ou codée par la forme (anneau creux = sans panne, disque plein = avec panne, trait pointillé = pluie).

```
## 1. Contraste du texte (WCAG, seuil AA = 4,5:1)
OK   texte principal #EAF0FA sur fond page #0E1420 : 16.10:1
OK   texte principal #EAF0FA sur fond carte #161E2E : 14.57:1
OK   texte principal #EAF0FA sur fond survol #1F2A40 : 12.53:1
OK   texte secondaire #A9B6CE sur fond page #0E1420 : 9.01:1
OK   texte secondaire #A9B6CE sur fond carte #161E2E : 8.16:1
OK   texte secondaire #A9B6CE sur fond survol #1F2A40 : 7.02:1
OK   texte discret #8D9BB6 sur fond page #0E1420 : 6.58:1
OK   texte discret #8D9BB6 sur fond carte #161E2E : 5.95:1
OK   texte discret #8D9BB6 sur fond survol #1F2A40 : 5.12:1

## 2. Contraste des marques sur la carte (seuil 3:1)
OK   penurie #E26828 sur carte : 4.96:1
OK   saturation #2A9FD0 sur carte : 5.53:1
OK   panne #D8478A sur carte : 4.12:1
OK   pluie #7F6AE6 sur carte : 4.06:1
OK   neutre #9AA9C4 sur carte : 7.02:1
OK   grille_claire #566892 sur carte : 3.01:1

## 3. Séparation des séries (OKLab ΔE×100, toutes les paires, vision normale / daltonismes)
OK   penurie↔saturation : normale 29.1 · protan 22.5 · deutan 23.1 · tritan 32.3
OK   penurie↔panne : normale 15.5 · protan 16.6 · deutan 13.3 · tritan 4.8
OK   penurie↔pluie : normale 30.3 · protan 28.5 · deutan 31.2 · tritan 26.4
OK   saturation↔panne : normale 28.1 · protan 16.5 · deutan 10.9 · tritan 32.9
OK   saturation↔pluie : normale 16.1 · protan 13.6 · deutan 9.9 · tritan 11.2
OK   panne↔pluie : normale 20.8 · protan 14.8 · deutan 18.4 · tritan 25.5
(seuils : vision normale ≥ 15 ; protan/deutan ≥ 6 ; chaque série est de plus étiquetée directement ou par la forme : jamais la couleur seule)

## 4. Rampe séquentielle « braise » (taux de pénurie), sombre → clair, une seule teinte
info étape 1 #362B27 L=0.30 contraste/carte 1.22:1
info étape 2 #693926 L=0.40 contraste/carte 1.76:1
info étape 3 #9E4A24 L=0.51 contraste/carte 2.75:1
info étape 4 #CD642C L=0.62 contraste/carte 4.33:1
info étape 5 #EF844A L=0.72 contraste/carte 6.41:1
info étape 6 #FFA97B L=0.81 contraste/carte 8.90:1
info étape 7 #FFD4BC L=0.90 contraste/carte 12.23:1
OK   luminosité strictement croissante (Δ L ≥ 0,06 entre étapes)
OK   première étape discernable du fond de carte (1.22:1 ≥ 1,15)
OK   rampe monotone en luminosité sous protanopie
OK   rampe monotone en luminosité sous deuteranopie
```

## 5. Typographie

Une seule famille : **Segoe UI** (présente sur tout poste Windows qui ouvre Power BI Desktop ; variante grasse « Segoe UI Semibold »). Tailles fixes. Côté Power BI les tailles sont en pt (1 pt = 1,33 px à l'écran), dans les graphiques Deneb en px :

| Élément | Taille | Graisse |
|---|---|---|
| Valeur de KPI | 36 pt | semi-gras |
| Titre de visuel (énonce la conclusion) | 16 pt | semi-gras |
| Sous-titre (ce que mesure le graphique, unité) | 12 pt | normal |
| Libellés / étiquettes directes (Deneb) | 12 px | normal |
| Axes et graduations (Deneb) | 11 px | normal |
| Infobulle | 12 | normal |

Nombres au format français (virgule décimale, espace avant « % ») : les visuels Deneb sont réglés sur la locale `fr-FR`.

## 6. Grille de mise en page (page 1280 × 720 px)

- marge extérieure **24 px**, gouttière entre visuels **16 px**, rayon des coins **12 px** ;
- largeur utile 1232 px : deux colonnes de 608 px, ou quatre KPI de 296 px, ou trois KPI de 400 px ;
- **bandeau d'en-tête** (y 12 → 68) : titre de page à gauche (énonce la conclusion), filtres à droite : tous les filtres sont **sur une seule ligne, au-dessus des graphiques**, avec leur libellé ;
- **rangée de KPI** (y 80, hauteur 104) quand la page en a ; **zone des graphiques** ensuite (y 200, hauteur 496), jusqu'à y 696 (marge basse 24 px).

| Page | Disposition (largeur × hauteur en px) |
|---|---|
| Vue d'ensemble | 4 KPI de 296 × 104 ; heatmap 608 × 496 à gauche, rythme de la journée 608 × 496 à droite |
| Carte des stations | carte stylisée 800 × 616 ; tableau « top 20 » 416 × 616 |
| Effet des pannes | 3 KPI de 400 × 104 ; haltères 800 × 340 puis « Comment lire » 800 × 140 ; « Méthode » 416 × 496 |
| Effet de la météo | barres 400 × 300 puis « Comment lire » 400 × 300 à gauche ; nuage 816 × 300 puis courbes 816 × 300 à droite |
| Secours (cachée) | grille 3 × 2 de visuels natifs de 400 × 300 |

## 7. Règles graphiques

1. Pas de bordure inutile : les cartes ont un fond, pas de contour visible (la bordure a la couleur du fond et ne sert qu'à arrondir les coins) ; les vues Vega n'ont pas de cadre (`view.stroke = null`).
2. Grille très claire (`#2B3750`, 1 px, 0,6 d'opacité), pas de ligne d'axe.
3. **Étiquetage direct** : le nom de la série est écrit sur le graphique (pics de pénurie et de saturation, « sans panne / avec panne ») ; une légende ne subsiste que quand le direct est impossible.
4. **Titres qui énoncent la conclusion**, jamais écrits dans une spec : une mesure DAX par visuel (`Titre heatmap`, `Titre rythme`, `Titre carte`, `Titre pannes`, `Titre pluie`, `Titre nuage`, `Titre courbes`) calcule la phrase à partir de `gold_station_heure`, en respectant filtres et segments, avec un texte neutre si les données sont vides. Nombres au format français explicite (`FORMAT(x, "#,##0", "fr-FR")`). Le titre doit correspondre à une valeur affichée : celui des haltères porte sur la première ligne (« Pénurie · heure de pointe »).
5. **Unités toujours visibles** : « % des relevés », « pts », « °C ».
6. Pas de double axe, pas de 3D, pas de camembert, pas d'arc-en-ciel.
7. Marques fines : lignes 3 px, points ≥ 8 px, barres arrondies de 4 px, 2 px d'écart entre cases (trait de la couleur du fond).
8. Le texte ne prend jamais la couleur d'une série : valeurs et libellés en gris clair ; c'est la pastille ou la forme voisine qui porte la couleur.

## 8. Infobulles et interactions

- Infobulle : fond `#1F2A40`, texte 12, une ligne « libellé : valeur » par information ; jamais d'information qui n'existe que dans l'infobulle (le survol enrichit, il ne conditionne rien).
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

| Couleur | Hex | Sens unique | Où elle apparaît |
|---|---|---|---|
| Orange braise | `#E26828` | Pénurie : plus de vélo dans la station | 02 rythme (courbe et aire). Les cases et cercles de pénurie utilisent la rampe de même teinte (ci-dessous). |
| Rampe « braise » (7 pas) | `#362B27 #693926 #9E4A24 #CD642C #EF844A #FFA97B #FFD4BC` | Intensité de la pénurie, du presque-fond (peu) au pêche clair (beaucoup) | 01 heatmap, 03 carte |
| Cyan | `#2A9FD0` | Saturation : plus de place libre dans la station | 02 rythme |
| Rose / magenta | `#D8478A` | Panne ferrée en cours à proximité (« avec panne ») | 04 haltères (disque et trait de liaison) |
| Violet | `#7F6AE6` | Il pleut | 05 barres, 06 nuage, 07 courbes |
| Gris bleuté | `#9AA9C4` | Situation de référence : « sans panne », « sans pluie » | 04 haltères, 05 barres, 06 nuage, 07 courbes |
| Blanc cassé | `#EAF0FA` | Texte, tendance, anneau de la valeur maximale : jamais une donnée | 01, 02, 03, 06 |

Les neutres de fond (`#0E1420`, `#161E2E`, `#1F2A40`, `#2B3750`, `#566892`) ne portent jamais de donnée. Là où la météo est le sujet (barres, nuage, courbes), la couleur code *pluie / sans pluie* ; la pénurie et la saturation y sont désignées par l'axe ou le libellé, pas par la couleur. Les visuels natifs de la page « Secours » reprennent les mêmes couleurs par série (réglage explicite, car le thème attribue sinon ses couleurs dans l'ordre).
