# Guide de production : la simulation « Et si… ? » documentaire

Format tiré de l'analyse de 3 vidéos de Hindcast (voir `hindcast_recette.md`).
**Pour faire écrire un script par une IA, utilise [`format_bible.md`](format_bible.md)** : c'est la version « prompt » de ce guide.
Les chiffres viennent des mesures (transcriptions, changements de plan, images), pas d'impressions.
**À reprendre : la mécanique. À changer : le sujet, la langue, la charte et le nom.**

---

## 0. Le format en une phrase

> **Une catastrophe qui n'a pas (encore) eu lieu, racontée minute par minute comme si elle arrivait, où chaque chiffre est réel et sourcé, et qui commence et finit sur un être humain.**

---

## 1. Les chiffres cibles

| Paramètre | Cible | Mesuré chez Hindcast |
|---|---|---|
| Durée | **12 à 15 min** | 11,3 / 11,4 / 16,9 min |
| Longueur du script | **durée (min) × 150 mots** : 1 800 mots pour 12 min | 1 769 à 2 484 mots |
| Débit de la voix | **150 mots/min** | 147 à 159 |
| Longueur des phrases | **8 à 10 mots en moyenne** | 8,1 à 9,9 (médiane 7 à 9) |
| Phrases-chocs (≤ 4 mots) | **15 à 25 %** des phrases | 13 à 26 % |
| Chiffres à l'écran et dans la voix | **au moins 3 par minute** | 3,0 à 3,7/min |
| Changements de scène | **environ 5 par minute** (un plan dure ≈ 10 s) | 4,9 à 5,0/min (la vidéo la moins vue : 1,4) |
| Nouvelle information visuelle | **toutes les 3 à 5 s** : texte, chiffre, mouvement, même sans changer de plan | observé sur les planches |
| Part de parole | **≈ 97 %** : pas de silence | 96 à 99 % |
| Musique | nappe **continue** sous la voix | aucune pause > 0,6 s |
| Volume final | **−14 à −16 LUFS** | −15,2 à −17,1 |

---

## 2. Le squelette minuté (modèle de 12 min, 1 800 mots)

| # | Temps | Durée | Mots | Ce qui s'y passe | Rôle |
|---|---|---|---|---|---|
| 1 | **0:00 – 0:30** | 30 s | 75 | **Ouverture sensorielle** : un lieu, une date, une heure. Un humain ordinaire et un détail intime (un examen, un champ de blé, un toit). Puis **un détail qui cloche**. On finit sur une phrase de bascule. | Accroche : le spectateur est *dedans* avant de savoir de quoi on parle |
| 2 | 0:30 – 0:50 | 20 s | 50 | **Contrat d'honnêteté** : « simulation », mais ce qui est réel est listé, avec des sources nommées. Puis le titre, dit à voix haute. | Crédibilité : désamorce le « fake » |
| 3 | 0:50 – 2:30 | 1 min 40 | 250 | **La vraie histoire, datée** : un événement historique fondateur, puis une chronologie récente **jusqu'au mois de publication**. | Ancre dans le réel, fait monter la tension |
| 4 | 2:30 – 3:30 | 1 min | 150 | **« Faisons le calcul »** : une formule ou un ordre de grandeur, **rendu concret** (« le poids d'un trombone »). **On plante la boucle** : « Retenez ce chiffre. » | Comprendre, et une dette envers le spectateur |
| 5 | 3:30 – 6:00 | 2 min 30 | 375 | **Simulation minutée** : chrono (T+0, 1 s, 3 s, 10 min…), puis **« tout dépend d'où vous êtes »** avec des cercles de distance ou une carte des risques. On repasse par l'humain de l'ouverture. | Cœur spectaculaire |
| 6 | 6:00 – 9:30 | 3 min 30 | 525 | **Escalade par étapes** (heure 1, jour 1, semaine 1, an 1), avec **au moins un choix impossible** (options 01 / 02 / 03) et des relances (« Gardez ça en tête »). | Tient la rétention au milieu |
| 7 | 9:30 – 10:15 | 45 s | 110 | **Retournement**, et **la boucle plantée revient** : « Ce chiffre revient maintenant. » | Récompense |
| 8 | 10:15 – 10:45 | 30 s | 75 | **Retour à l'ouverture** : le même lieu ou la même personne, changés. | Boucle fermée et émotion |
| 9 | 10:45 – 12:00 | 1 min 15 | 190 | **« Maintenant, la vérité »** : ce qui est réel ou inventé, l'état du monde aujourd'hui, une morale en une phrase. Puis **une fin concrète** : un geste à faire, ou une vraie question pour les commentaires. | Partage et commentaires |

**Pour une autre durée**, garde les proportions :
- ouverture et contrat : 7 % ;
- histoire : 14 % ;
- calcul : 8 % ;
- simulation : 21 % ;
- escalade : 29 % ;
- retournement : 6 % ;
- retour : 4 % ;
- vérité : 11 %.

---

## 3. Les mécaniques de rétention, à cocher dans chaque script

- [ ] **Un humain fil rouge** (inventé, mais présenté comme tel), vu au début, au milieu et à la fin
- [ ] **Un détail qui cloche** dans les 20 premières secondes
- [ ] **Une boucle plantée tôt et payée tard** : « Retenez ce chiffre / cette incertitude », puis 5 à 7 minutes plus tard, « Ce chiffre revient »
- [ ] **Un motif répété 3 fois** : un nombre (« 81 ans »), une phrase, une image
- [ ] **Un chrono à l'écran** pendant la simulation
- [ ] **« Tout dépend d'où vous êtes »** : cercles de distance ou carte rouge / orange / jaune
- [ ] **Un choix impossible** présenté en 2 ou 3 options numérotées
- [ ] **Un retournement** que le spectateur n'a pas vu venir, mais qui était annoncé
- [ ] **Une fin qui se partage** : un lieu ou un geste concret. C'est la fin sur la Nouvelle-Zélande qui a fait le plus de réponses
- [ ] **Aucun silence**, et une information visuelle nouvelle toutes les 3 à 5 s

---

## 4. Le style d'écriture

**Les règles**
1. **Le présent, toujours** : « Le missile décolle. » Pas « décollerait ».
2. **Des phrases courtes**, avec **une phrase-choc sur 5** : « Puis, plus rien. » « Pas de marchés. Pas d'échanges. »
3. **Chaque chiffre est rendu concret** : une comparaison physique (un train, un trombone, la hauteur des avions de ligne).
4. **Les sources sont nommées dans la phrase** : « Une étude publiée dans *Nature Food* en 2022… »
5. **Jamais d'adjectif à la place d'un chiffre** : pas « énorme », mais « 10 milliards de tonnes ».
6. **Réel et inventé sont séparés à voix haute**, au début et à la fin.

**Des phrases modèles en français, à adapter**

| Moment | Modèle |
|---|---|
| Ouverture | « [Ville], [date], [heure]. [Prénom] a [âge] ans. [Détail intime]. [Phrase de bascule : quelque chose ne va pas]. » |
| Contrat | « Ce que vous allez voir est une simulation. [Prénom] est inventé·e. Mais [lieu] est réel. [Chiffre clé] est réel. Chaque chiffre vient de [source 1], [source 2] et [source 3]. » |
| Calcul | « Faisons le calcul. [Formule ou ordre de grandeur]. Pour se représenter ça : [comparaison physique]. » |
| Boucle | « Retenez ce chiffre. C'est lui qui décide de tout ce qui suit. » … puis « Ce chiffre revient maintenant. » |
| Simulation | « Zéro seconde. [Effet]. Une seconde. [Effet]. Trois secondes. [Effet]. » |
| Distance | « La gravité dépend d'une seule chose : où vous êtes. À 1 kilomètre… À 5 kilomètres… À 40 kilomètres, [Prénom]… » |
| Choix | « Les dirigeants ont quelques heures, et trois options. Un : … Deux : … Trois : … » |
| Retournement | « Et voici le détail qui change tout. » |
| Vérité | « Maintenant, la vérité. Rien de tout ça n'est arrivé. Mais [3 faits réels]. La question n'est pas *si*, mais *quand*. » |
| Fin | « Alors, si un jour vous voyez [signe], [geste concret]. » ou « Et vous, [vraie question] ? Dites-le en commentaire. » |

---

## 5. La charte visuelle

**La mise en page, identique sur chaque plan**

```
┌──────────────────────────────────────────────────────────┐
│ ● SIMULATION / ● HISTOIRE RÉELLE           [logo]  T+00:03 │  ← étiquette + chrono
│ TITRE DE SCÈNE                                           │
│ sous-titre de contexte (petit, gris)                     │
│                                                          │
│                [ visuel principal ]          GROS CHIFFRE │
│                                                          │
│              LÉGENDE QUI RÉSUME LA PHRASE                │  ← bas de l'écran
└──────────────────────────────────────────────────────────┘
```

**Les couleurs**

| Rôle | Hindcast (mesuré) | Pour ta chaîne : prends une identité différente |
|---|---|---|
| Fond principal | noir `#000000`, bleu nuit `#061826`, gris anthracite `#2E2C32` | ex. bleu-vert profond `#0B1F1E` |
| Fond secondaire | `#143045`, brun nuit `#1A1316` | ex. `#13302C` |
| Danger / inventé | rouge vif *(à l'œil)* | ex. orange sang `#FF5A36` |
| Réel / sûr | cyan *(à l'œil)* | ex. vert menthe `#5EE6B0` |
| Archive / papier | crème `#DBD0AA` | ex. `#E8DDC4` |
| Texte | blanc, gris `#7F8283` | blanc cassé `#F2F2EE`, gris `#8A918F` |

**La typographie :** une sans-serif grasse en capitales pour les titres et les chiffres (ex. Inter Tight, Archivo Black), une monospace pour les chronos et les coordonnées (ex. JetBrains Mono). Ce sont des polices libres.

**Les 10 types de plans, et comment les faire en code**

| Type de plan | Quand | Outil |
|---|---|---|
| **Globe 3D** jour ou nuit, caméra qui se déplace, arcs de trajectoire | Ouverture, changements d'échelle | Three.js / react-three-fiber (textures NASA Blue/Black Marble) |
| **Carte vectorielle sombre** : villes, points, flèches, zones colorées | Histoire, escalade, carte des risques | D3 + GeoJSON (Natural Earth), rendu dans Remotion |
| **Gros chiffre** avec unité et sous-texte, ou grille de points | Toutes les minutes | Remotion |
| **« FAISONS LE CALCUL »** : formule qui s'écrit, puis le résultat | Calcul | Remotion + KaTeX |
| **Chrono** (T+, compte à rebours) | Simulation | Remotion (police monospace) |
| **Cercles de distance** « 1 km · VOUS » | Simulation | SVG animé |
| **Schéma en coupe** : montagne, ligne électrique, transformateur | Calcul, explication | SVG / D3 |
| **Cartes de choix** 01 / 02 / 03 | Escalade | Remotion |
| **Fausse interface** : notification de téléphone, écran d'alerte, archive papier | Ouverture, simulation | Remotion (HTML/CSS) |
| **Scène 3D low-poly** : champ, ville la nuit, chambre | Ouverture, retour | Three.js ou Blender en Python (le plus long à produire) |

---

## 6. Le son

- **La voix :** idéalement **ta propre voix**. Si tu utilises une synthèse vocale :
  - écris les dates et les nombres comme ils doivent être lus (« mille neuf cent quarante-cinq ») ;
  - réécoute tout avant l'export ;
  - sur la vidéo à 1,6M, le commentaire le plus aimé se moque d'une erreur de lecture.
- **La musique :** une nappe ambient ou cinématique continue, environ 18 à 20 dB sous la voix, qui monte pendant les silences de transition. Choisis une musique libre de droits.
- **Les effets :** un grondement grave aux impacts, un « tic » discret quand un chiffre apparaît, un souffle sur les mouvements de caméra.
- **Le mixage :** voix vers −16 LUFS, export final entre −14 et −16 LUFS.

---

## 7. Le titre et la miniature

**Les modèles de titre** (tirés de leurs vidéos) :
- « Et si [événement extrême] ? [Promesse précise de méthode] » → *« …? Nous avons simulé chaque minute qui suit »*
- « [L'événement réel] qui a frôlé [la catastrophe]. Et si [ça avait eu lieu] ? » → *« La tempête solaire qui a raté la Terre de 9 jours. Et si… ? »*
- **Relis le titre** : leur vidéo à 1,6M a une faute (« Agains ») relevée en commentaire.

**La miniature :** une image unique et spectaculaire, avec 2 à 4 mots en très gros (*« 12 MINUTES TO EXTINCTION »*, *« WE ARE NOT READY »*). C'est le seul élément qui demande un générateur d'images.

---

## 7 bis. Les règles YouTube qui concernent ce format (vérifiées le 3 novembre 2026)

**Monétisation (« inauthentic content », anciennement « repetitious content », renommée le 15 juillet 2025)**
- La règle vise le contenu **produit en masse, générique ou répétitif**, qui *« looks like it's made with a template »*.
- Est refusé : le contenu IA fait à partir de modèles génériques qui donne une impression de production en masse, *« without adding the creator's original, authentic insights or perspective »*.
- Est autorisé : utiliser l'IA pour retravailler un script ou générer un visuel de fond, ou garder la même intro et la même outro si le reste change.
- **La page ne dit rien des voix de synthèse.** Elle interdit en revanche les personnages IA qui se présentent comme des experts humains sur des sujets sensibles (santé, droit, finance, politique).
- Elle cite aussi comme problématiques les **visuels réalistes qui font croire à une fausse catastrophe naturelle**.

**Déclaration des contenus IA (« Disclosing use of GenAI content »)**
- **À déclarer** (Studio → Attributs → « AI use : Yes ») : tout contenu **réaliste** généré ou modifié, par exemple *« a realistic depiction of a tornado… moving toward a real city that didn't actually happen »*, ou une scène réaliste qui n'a pas eu lieu.
- **Pas à déclarer** : le contenu non réaliste ou entièrement animé (*« an AI-generated or altered animation of a missile in a fully animated video »*), l'aide au script, les sous-titres, le clonage de **sa propre** voix.
- Déclarer **ne limite ni l'audience ni la monétisation**. Ne pas déclarer, de façon répétée, peut mener à des sanctions, jusqu'à l'exclusion du Programme Partenaire.

**Pour ce format :**
- Le style **motion design / low-poly** (cartes, globes, schémas) est **non réaliste** : pas de déclaration obligatoire.
- Une **image photoréaliste générée** d'une catastrophe sur une vraie ville (miniature ou plan) **doit être déclarée**.
- Les étiquettes « SIMULATION » et le contrat d'honnêteté ne sont pas qu'un style : ils empêchent que la vidéo passe pour une vraie catastrophe.
- Chaque vidéo doit être une **vraie recherche avec ton angle**, et pas une variation d'un modèle : c'est ce que vise la règle.

Sources : [Règles de monétisation des chaînes](https://support.google.com/youtube/answer/1311392?hl=en) · [Déclarer les contenus générés par IA](https://support.google.com/youtube/answer/14328491?hl=en)

## 8. La check-list avant publication

- [ ] Durée 12 à 15 min, script ≈ durée × 150 mots
- [ ] Les 9 temps sont présents, la boucle est plantée **et** payée
- [ ] Au moins 3 chiffres par minute, chacun rendu concret, avec des sources nommées
- [ ] Chronologie réelle à jour au mois de publication
- [ ] Réel et inventé séparés au début et à la fin
- [ ] Environ 5 changements de scène par minute, une information nouvelle toutes les 3 à 5 s
- [ ] Étiquette « SIMULATION » ou « HISTOIRE RÉELLE » sur chaque plan
- [ ] Voix réécoutée en entier (dates, nombres, homonymes), titre relu
- [ ] Musique libre de droits, volume final entre −14 et −16 LUFS
- [ ] Une fin qui se partage : un geste concret ou une vraie question
- [ ] Sujet **naturel ou historique** plutôt que géopolitique (annonceurs, débats partisans)
- [ ] Image photoréaliste générée d'un événement qui n'a pas eu lieu ? → « AI use : Yes » dans Studio

---

## 9. Exemple appliqué : « Et si la crue de 1910 revenait à Paris ? » (12 min)

*Les faits marqués ⚠️ sont à vérifier et à sourcer avant l'écriture finale.*

| # | Temps | Contenu |
|---|---|---|
| 1 | 0:00 | Paris, [mois], 4 h du matin. Inès, 27 ans, agente RATP à Châtelet, fait sa ronde. Une flaque en bas de l'escalier, alors qu'il n'a pas plu depuis trois jours. Puis l'eau qui remonte par les grilles. *« La Seine vient d'entrer dans le métro. »* |
| 2 | 0:30 | Contrat : « Inès est inventée. Mais la crue de 1910 est réelle. Les plans d'évacuation sont réels. Chaque chiffre vient de [l'OCDE, la Préfecture de police, Météo-France / Vigicrues]. » |
| 3 | 0:50 | Janvier 1910 : la Seine monte à **8,62 m au pont d'Austerlitz**, les Parisiens circulent en barque. Puis 1955, 1982, juin 2016 (≈ 6,1 m ⚠️), l'exercice européen **EU Sequana** de mars 2016. |
| 4 | 2:30 | Faisons le calcul : le débit de la Seine en crue, comparé à des piscines olympiques par seconde ⚠️. **Boucle :** « Retenez ce chiffre : la hauteur à laquelle le métro ferme. » ⚠️ |
| 5 | 3:30 | Jour 1, 2, 3 : la cote monte de quelques centimètres par heure. Carte de Paris avec les zones inondées en bleu, puis « tout dépend d'où vous habitez » : les quais, le 15ᵉ, le 13ᵉ, la banlieue. Inès ferme les grilles de sa station. |
| 6 | 6:00 | Escalade : électricité coupée par précaution, métro fermé, hôpitaux évacués, réseau d'eau sous tension. Choix impossible : couper le courant de quartiers entiers, ou risquer les transformateurs ? Impact estimé par l'OCDE (2014) : jusqu'à **5 millions de personnes** touchées et **jusqu'à 30 Md€** de dégâts ⚠️. |
| 7 | 9:30 | Retournement : l'eau redescend en 10 jours, mais ce qui paralyse la ville pendant des semaines, ce sont les **coupures d'électricité et les réseaux noyés**. « La hauteur à laquelle le métro ferme revient maintenant. » |
| 8 | 10:15 | Inès, trois semaines plus tard, redescend l'escalier de Châtelet et regarde la marque de l'eau sur le mur. |
| 9 | 10:45 | La vérité : rien de tout ça n'est arrivé, mais une crue comme celle de 1910 a environ 1 chance sur 100 de se produire chaque année ⚠️. Fin concrète : « Cherchez votre adresse sur la carte des zones inondables. Ça prend 30 secondes. » |
