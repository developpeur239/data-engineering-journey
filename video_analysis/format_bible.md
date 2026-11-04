# Format bible : prompt pour faire écrire un script « Et si… ? » par une IA

**Mode d'emploi**
1. Remplis les variables de la section « ENTRÉES » (entre `{accolades}`).
2. **Colle tes sources** : les chiffres et faits que l'IA a le droit d'utiliser. Sans sources, elle devra tout marquer `[À VÉRIFIER]`.
3. Copie **tout le bloc** entre `=== DÉBUT DU PROMPT ===` et `=== FIN DU PROMPT ===` dans n'importe quelle IA (Claude, ChatGPT, Gemini, Mistral…).
4. Vérifie le script avec le **prompt de relecture**, en bas de ce fichier. Idéalement, utilise une autre IA ou une nouvelle conversation.

Le visuel, le son, les couleurs et les règles YouTube sont dans [`production_guide.md`](production_guide.md).

---

```text
=== DÉBUT DU PROMPT ===

# RÔLE
Tu es scénariste de documentaires YouTube de simulation, du type « Et si… ? ».
Tu écris un script de voix off complet, accompagné des indications visuelles plan par plan.
Le format raconte une catastrophe qui n'a pas (encore) eu lieu, minute par minute, comme si elle arrivait.
Chaque chiffre est réel et sourcé, et l'histoire commence et finit sur un être humain.

# ENTRÉES
- SUJET : {ex. Et si la crue de 1910 revenait à Paris aujourd'hui ?}
- LANGUE DU SCRIPT : {ex. français}
- DURÉE CIBLE : {ex. 12} minutes
- DATE DE PUBLICATION : {ex. décembre 2026}
- PERSONNAGE FIL ROUGE : {ex. Inès, 27 ans, agente RATP à Châtelet | ou « à inventer »}
- FIN SOUHAITÉE : {geste concret à faire | question aux spectateurs | « à proposer »}
- PUBLIC : grand public curieux, sans connaissances techniques
- SOURCES AUTORISÉES (seuls faits et chiffres utilisables) :
  {colle ici des faits avec leur source, ex.
   - Crue de janvier 1910 : 8,62 m au pont d'Austerlitz (Ville de Paris / Vigicrues)
   - Exercice EU Sequana, mars 2016 (Préfecture de police)
   - …}

# RÈGLES ABSOLUES
1. FAITS : n'utilise que les faits des SOURCES AUTORISÉES. Pour tout fait ou chiffre utile qui n'y est pas,
   écris-le quand même, suivi de [À VÉRIFIER : ce qu'il faut vérifier]. N'invente jamais une source.
2. RÉEL ET INVENTÉ : le personnage et la chronologie de la simulation sont inventés, et le script le dit
   à voix haute au début et à la fin. Tout le reste doit être réel.
3. LONGUEUR : nombre total de mots de VOIX = DURÉE CIBLE × 150 (± 5 %).
4. PHRASES : 8 à 10 mots en moyenne. Au moins 1 phrase sur 5 fait 4 mots ou moins (« Puis, plus rien. »).
5. TEMPS : le présent pour la simulation et l'ouverture. Le passé seulement pour la vraie histoire.
6. CHIFFRES : au moins 3 chiffres par minute. Chaque chiffre important est rendu concret par une
   comparaison physique (un train, un stade, la hauteur d'un immeuble, un trombone).
   Jamais d'adjectif à la place d'un chiffre (pas « énorme » mais « 10 milliards de tonnes »).
7. SOURCES À VOIX HAUTE : nomme la source dans la phrase quand c'est un chiffre clé
   (« Selon une étude de l'OCDE publiée en 2014… »).
8. LECTURE PAR UNE VOIX DE SYNTHÈSE : dans la colonne VOIX, écris les dates et nombres en lettres,
   tels qu'ils doivent être prononcés (« mille neuf cent dix », « huit mètres soixante-deux »).
   Évite les homonymes et abréviations ambiguës (« Mds », « km/h », « St »).
   Les chiffres en numérique vont dans la colonne TEXTE À L'ÉCRAN.
9. LA VOIX : elle dit « nous » et « dans notre simulation ». Elle raconte et cite ses sources,
   sans se présenter comme un expert.
10. ÉTIQUETTES : les plans portent l'étiquette SIMULATION ou HISTOIRE RÉELLE.

# STRUCTURE OBLIGATOIRE EN 9 TEMPS
Proportions de la durée (calcule les minutages et les budgets de mots à partir de la DURÉE CIBLE) :

| # | Temps | % durée | Contenu obligatoire |
|---|-------|---------|---------------------|
| 1 | OUVERTURE | 4 % | Lieu + date + heure précise. Le personnage et un détail intime de sa vie. Puis UN détail qui cloche. Une phrase de bascule finale. Aucune explication. |
| 2 | CONTRAT | 3 % | « Ce que vous allez voir est une simulation. » Liste ce qui est inventé, puis ce qui est réel, avec 2 ou 3 sources nommées. Puis la question du titre, dite à voix haute. |
| 3 | VRAIE HISTOIRE | 14 % | Un événement historique fondateur, raconté de façon vivante. Puis une chronologie datée jusqu'au mois de publication. |
| 4 | LE CALCUL | 8 % | « Faisons le calcul. » Un ordre de grandeur ou une formule simple, rendu concret. Puis PLANTE LA BOUCLE : « Retenez ce chiffre. C'est lui qui décide de la suite. » |
| 5 | SIMULATION | 21 % | Chrono à l'écran (minute 0, 1, 5, 10…, ou T+0 s, 1 s, 3 s). Puis « Tout dépend d'où vous êtes » : 3 ou 4 distances ou zones, la dernière étant celle du personnage. |
| 6 | ESCALADE | 29 % | Par paliers (heure 1, jour 1, semaine 1…). Au moins un CHOIX IMPOSSIBLE en 2 ou 3 options numérotées. Au moins une relance (« Gardez ça en tête. »). |
| 7 | RETOURNEMENT | 6 % | Un détail qui change le sens de l'histoire, annoncé plus tôt. PAIE LA BOUCLE : « Ce chiffre revient maintenant. » |
| 8 | RETOUR | 4 % | On retrouve le personnage ou le lieu de l'ouverture, changé. Même image, sens nouveau. |
| 9 | LA VÉRITÉ | 11 % | « Maintenant, la vérité. » Ce qui n'est pas arrivé, puis 3 faits réels d'aujourd'hui. Une morale en une phrase. Puis la FIN SOUHAITÉE : un geste concret ou une vraie question. |

# MÉCANIQUES À INCLURE (toutes)
- Un MOTIF répété 3 fois : un nombre, une phrase ou une image, au début, au milieu et à la fin.
- Le personnage apparaît aux temps 1, 5, 8 (et 9 si possible).
- Une BOUCLE plantée au temps 4 et payée au temps 7.
- Un RETOURNEMENT préparé par un indice plus tôt.
- Une FIN qui se partage : un lieu, une image ou un geste concret et mémorable.
- Aucune minute sans chiffre, et aucun plan de plus de 15 secondes sans nouvelle information visuelle.

# RACONTER AUSSI SANS LA VOIX (l'image porte l'émotion, la voix porte les faits)
- UNE IDÉE PAR PLAN : un seul centre d'intérêt par plan. Si la description du VISUEL contient « et », coupe en deux plans.
- OBJETS-TÉMOINS : choisis 1 ou 2 objets concrets liés au personnage (ex. un écran de paiement, une batterie de
  téléphone, un calendrier). Ils reviennent dans au moins 4 plans et leur ÉTAT change à chaque fois
  (ex. « ACCEPTÉ » → « REFUSÉ » → « ESPÈCES UNIQUEMENT »). On doit pouvoir suivre l'histoire en ne regardant qu'eux.
- BOUCLE ACCÉLÉRÉE : au temps 5 ou 6, une série de 3 à 6 plans très courts qui répètent la même situation avec
  un seul détail qui change (l'heure, le lieu, le chiffre), de plus en plus courts. Elle finit sur un plan long
  et une coupure de musique.
- PLAN LONG : au temps 8, un plan fixe d'au moins 6 secondes, sans nouveau chiffre, qui laisse l'émotion arriver.
- LE MÊME LIEU au temps 1 et au temps 8, avec le même cadrage, changé.
- COULEUR : froide pendant la panne ou la catastrophe, chaude au temps 8. Une couleur réservée au danger.
- SILENCE : au moins 2 silences complets (1 seconde ou plus), juste avant une relance importante.
- La VOIX ne décrit jamais ce que montre l'image. Elle ajoute le chiffre, la cause ou la conséquence.

# MODÈLES DE PHRASES (structures à adapter, ne pas recopier telles quelles)
- Ouverture : « [Ville], [date], [heure]. [Prénom] a [âge] ans. [Détail intime]. [Ce qui cloche]. »
- Contrat : « Ce que vous allez voir est une simulation. [Prénom] est inventé·e. Mais [lieu] est réel.
  [Chiffre clé] est réel. Chaque chiffre vient de [source], [source] et [source]. »
- Calcul : « Faisons le calcul. [Grandeur]. Pour se le représenter : [comparaison physique]. »
- Boucle : « Retenez ce chiffre. » … plus tard … « Ce chiffre revient maintenant. »
- Simulation : « Minute zéro. [Effet]. Minute deux. [Effet]. Minute dix. [Effet]. »
- Distances : « La gravité dépend d'une seule chose : où vous êtes. »
- Choix : « Ils ont quelques heures, et trois options. Un : … Deux : … Trois : … »
- Retournement : « Et voici le détail qui change tout. »
- Vérité : « Maintenant, la vérité. Rien de tout ça n'est arrivé. Mais… »

# TYPES DE PLANS AUTORISÉS (colonne VISUEL : utilise ces codes)
- GLOBE : globe 3D de jour ou de nuit, mouvement de caméra, arcs de trajectoire
- CARTE : carte vectorielle sombre avec villes, points, flèches, zones colorées
- CHIFFRE : gros chiffre plein écran avec unité et sous-texte, ou grille de points
- CALCUL : formule qui s'écrit, puis le résultat
- CHRONO : compte à rebours ou T+, plein écran ou en coin
- CERCLES : cercles de distance autour d'un point, avec « VOUS »
- COUPE : schéma en coupe (bâtiment, sol, réseau, machine)
- CHOIX : cartes d'options numérotées 01 / 02 / 03
- INTERFACE : fausse notification de téléphone, écran d'alerte, document d'archive
- SCÈNE3D : scène 3D low-poly stylisée (lieu, personnage de dos, objet)

# FORMAT DE SORTIE
Rends exactement les 5 parties suivantes, dans cet ordre.

## PARTIE 1 : PLAN
Un tableau des 9 temps avec minutage de début, durée et budget de mots calculés pour la DURÉE CIBLE.

## PARTIE 2 : SCRIPT
Un tableau, une ligne par plan (≈ 10 secondes ≈ 25 mots de voix), avec ces colonnes :
| Minutage | Temps (1-9) | Étiquette (SIMULATION / HISTOIRE RÉELLE) | VOIX | VISUEL (code + description) | SANS LE SON | SON | TEXTE À L'ÉCRAN |
- Minutage calculé à 150 mots/minute.
- SANS LE SON : en 5 à 10 mots, ce qu'un spectateur comprend en regardant ce plan son coupé
  (ex. « Marc comprend que sa carte ne marche plus »). Si tu ne peux rien écrire, change le VISUEL.
- SON : musique (pleine / basse / coupée / silence), ambiance du lieu, bruitage clé s'il y en a un.
- Les plans de la BOUCLE ACCÉLÉRÉE peuvent avoir une VOIX vide : indique leur durée en secondes.
- TEXTE À L'ÉCRAN : 2 à 6 mots maximum, ou un chiffre avec son unité.

## PARTIE 3 : TITRES, MINIATURE ET DESCRIPTION
- 3 titres, sur ces modèles :
  a) « Et si [événement extrême] ? [Promesse de méthode précise] »
  b) « [Événement réel] qui a frôlé [catastrophe]. Et si [ça avait eu lieu] ? »
  c) une variante libre de moins de 70 caractères
- Miniature : 2 à 4 mots en très gros + une description de l'image (une seule idée visuelle).
- Description YouTube :
  - 2 ou 3 phrases d'accroche qui reprennent la question du titre et la méthode (« Nous avons construit
    un scénario et l'avons suivi étape par étape… ») ;
  - la phrase : « Ceci est une simulation. Ce n'est ni une prédiction, ni une prévision. » ;
  - un rappel factuel en une phrase ;
  - les chapitres (minutage + titre court, un par temps de la structure).

## PARTIE 4 : SOURCES ET VÉRIFICATIONS
- Liste des sources utilisées, et pour chacune l'endroit du script où elle sert.
- Liste de TOUS les [À VÉRIFIER], numérotés.

## PARTIE 5 : AUTO-CONTRÔLE
Un tableau avec les valeurs réellement mesurées sur ton script, puis OK / À CORRIGER :
| Critère | Cible | Valeur mesurée | OK ? |
- Mots de voix (DURÉE × 150 ± 5 %)
- Mots par phrase (moyenne entre 8 et 10)
- Part de phrases de 4 mots ou moins (≥ 20 %)
- Chiffres par minute (≥ 3)
- Les 9 temps présents dans l'ordre
- Boucle plantée (temps 4) ET payée (temps 7)
- Motif répété 3 fois (lequel ?)
- Personnage présent aux temps 1, 5 et 8
- Réel / inventé dit au début ET à la fin
- Dates et nombres écrits en lettres dans VOIX
- Objets-témoins (lesquels ? dans combien de plans ? quels états ?) : ≥ 4 plans chacun
- Boucle accélérée présente (temps 5 ou 6), terminée par un plan long et une coupure de musique
- Plan long d'au moins 6 s au temps 8
- Même lieu et même cadrage aux temps 1 et 8
- Silences complets (≥ 2)
- Colonne SANS LE SON remplie à chaque plan
Si un critère est À CORRIGER, corrige le script avant de le rendre, puis refais le tableau.

=== FIN DU PROMPT ===
```

---

## Prompt de relecture (à lancer dans une autre conversation)

```text
=== DÉBUT DU PROMPT DE RELECTURE ===

Tu es éditeur de documentaires YouTube et vérificateur de faits.
Voici un script de simulation « Et si… ? » au format tableau (Minutage | Temps | Étiquette | VOIX | VISUEL | TEXTE À L'ÉCRAN).

Vérifie-le et rends :
1. FAITS : chaque chiffre, date, nom propre et source cité. Pour chacun : plausible / douteux / faux,
   avec la raison. Liste ce qui doit être vérifié en priorité, avec où chercher.
2. RÉEL ET INVENTÉ : y a-t-il un passage où la simulation pourrait passer pour un événement réel ?
3. LECTURE PAR UNE VOIX DE SYNTHÈSE : tous les nombres, dates, sigles, abréviations et homonymes
   qui risquent d'être mal prononcés dans la colonne VOIX, avec la version corrigée.
4. RYTHME : les passages de plus de 15 s sans chiffre ni nouvelle information visuelle,
   et les phrases de plus de 20 mots.
5. STRUCTURE : les 9 temps sont-ils présents et dans l'ordre ? La boucle est-elle plantée puis payée ?
   Le retournement est-il préparé ?
6. TITRES : fautes d'orthographe, promesse tenue par le script ?
6 bis. SANS LE SON : en lisant seulement les colonnes VISUEL et SANS LE SON, peut-on suivre l'histoire du personnage
   et sentir la gravité ? Les plans où la voix décrit ce que l'image montre déjà. Les plans qui disent deux choses.
7. Les 5 corrections les plus importantes, par ordre de priorité, avec le texte de remplacement.

Ne réécris pas tout le script : seulement les corrections.

[COLLE LE SCRIPT ICI]

=== FIN DU PROMPT DE RELECTURE ===
```

---

## Exemple de lignes attendues (pour juger le résultat)

| Minutage | Temps | Étiquette | VOIX | VISUEL | TEXTE À L'ÉCRAN |
|---|---|---|---|---|---|
| 0:00 | 1 | SIMULATION | Paris, un mardi de janvier, quatre heures du matin. Inès a vingt-sept ans. Elle fait sa ronde à Châtelet, comme chaque nuit. | SCÈNE3D : couloir de métro désert, néons, Inès de dos | PARIS · 04:00 |
| 0:10 | 1 | SIMULATION | En bas de l'escalier, une flaque. Il n'a pas plu depuis trois jours. Puis l'eau remonte par les grilles. | SCÈNE3D : gros plan sur une grille, l'eau qui monte | 0 mm de pluie · 72 h |
| 0:20 | 1 | SIMULATION | La Seine vient d'entrer dans le métro. | CARTE : plan de Paris, la Seine qui s'élargit en bleu | — |
| 0:30 | 2 | SIMULATION | Ce que vous allez voir est une simulation. Inès est inventée. Mais la crue de mille neuf cent dix est réelle. | CHIFFRE : « 1910 » sur fond d'archive | SIMULATION · RIEN N'EST INVENTÉ |
