# Script : « Et si la Lune tombait sur la Terre ? » (version 2)

Écrit le 5 novembre 2026 avec `video_analysis/format_bible.md`, puis révisé après une relecture critique : ouverture par la conséquence, histoire réelle raccourcie, scènes humaines, vrai dilemme pour Léa, trois « Vous pensez que… ? », moins de chiffres prononcés (repères : 4 jours et 19 heures, 18 000 km, 3,8 cm par an), nuance sur la limite de Roche. Personnage inventé : Léa, 31 ans, ingénieure sur une station de télémétrie laser lunaire. Chronologie de la chute calculée par nous (voir partie 4). Données : `script_data.py` ; ce fichier est généré par `build_md.py`.

## PARTIE 1 : PLAN

| # | Temps | Début | Durée | Mots (repère du prompt) | Mots écrits |
|---|---|---|---|---|---|
| 1 | Ouverture | 0:00 | 0:39 | 60 | 99 |
| 2 | Contrat | 0:39 | 0:22 | 45 | 55 |
| 3 | Vraie histoire | 1:01 | 0:34 | 210 | 87 |
| 4 | Le calcul | 1:36 | 0:35 | 120 | 88 |
| 5 | Simulation | 2:11 | 2:00 | 315 | 302 |
| 6 | Escalade | 4:12 | 3:12 | 435 | 466 |
| 7 | Retournement | 7:24 | 0:50 | 90 | 125 |
| 8 | Retour | 8:14 | 0:23 | 60 | 59 |
| 9 | La vérité | 8:38 | 1:00 | 165 | 150 |

Total : 1431 mots de voix, soit 9:38 à 150 mots/min (boucle muette de 6 s comprise).
Écarts voulus avec les proportions du prompt : ouverture plus longue (retour en arrière), histoire réelle raccourcie à environ 35 s, escalade et retournement plus longs.

## PARTIE 2 : SCRIPT

| Minutage | Temps | Étiquette | VOIX | VISUEL | SANS LE SON | SON | TEXTE À L'ÉCRAN |
|---|---|---|---|---|---|---|---|
| 0:00 | 1 | SIMULATION | Une heure et demie avant l'impact. La Lune remplit le ciel, douze fois plus large que d'habitude. | SCÈNE3D : le Mont-Saint-Michel de nuit, une Lune immense au-dessus, la mer qui monte | La Lune est beaucoup trop près | Grondement d'eau, drone sombre | Impact dans 1 h 27 |
| 0:06 | 1 | SIMULATION | Sur les côtes, la mer monte plus haut que tout ce que les digues ont connu. | SCÈNE3D : une vague passe par-dessus une digue, des lampadaires s'éteignent | La mer submerge tout | Fracas, puis coupure | — |
| 0:13 | 1 | SIMULATION | Et pourtant, la Lune ne touchera peut-être jamais la Terre en un seul morceau. | SCÈNE3D : gros plan sur une fissure à la surface de la Lune | La Lune se fend | Silence, un craquement grave | — |
| 0:18 | 1 | SIMULATION | Quatre jours plus tôt. Plateau de Calern, au-dessus de Grasse. Vingt-deux heures quatorze. | SCÈNE3D : plateau de nuit, coupole ouverte, faisceau vert vers une Lune normale | Retour en arrière : tout est calme | Vent, ronronnement de la coupole ; nappe neutre | 4 jours plus tôt · Calern |
| 0:24 | 1 | SIMULATION | Léa, trente et un ans, tire un laser sur la Lune, puis elle attend l'écho. Deux virgule cinq secondes. | SCÈNE3D : Léa (silhouette noire, écharpe ambre) devant son écran ; INTERFACE : compteur d'écho 2,510 s | Léa attend un signal | Bip discret du tir | Aller-retour : 2,51 s |
| 0:31 | 1 | SIMULATION | Ce soir, il revient trop tôt. Son collègue hausse les épaules : « C'est le capteur. Redémarre-le. » L'écho revient encore plus tôt. | INTERFACE : le chiffre passe à 2,509 puis 2,508 en rouge ; le collègue de dos | Ce n'est pas la machine | Bip d'erreur, la nappe s'arrête | Pensée de Léa : « Encore… » |
| 0:39 | 2 | SIMULATION | Ce que vous allez voir est une simulation. Léa est inventée, et ce scénario est impossible : rien ne peut arrêter la Lune. | CHIFFRE : carte titre « Simulation » | On annonce une fiction | Nappe neutre | Simulation |
| 0:48 | 2 | SIMULATION | Mais la station de Calern existe, et la physique de la chute est réelle. Nos chiffres viennent de la NASA et de nos propres calculs. Et si la Lune tombait sur la Terre ? | GLOBE : la Terre et la Lune, la Lune glisse vers nous | La question du titre | Coupure de musique : phrase dite dans le silence | Et si la Lune tombait sur la Terre ? |
| 1:01 | 3 | HISTOIRE RÉELLE | Ce qui va suivre, les astronomes l'ont déjà vu, ailleurs. En juillet mille neuf cent quatre-vingt-douze, une comète passe trop près de Jupiter. | GLOBE : Jupiter, trajectoire d'une comète qui la frôle | Une comète frôle Jupiter | Souffle | Juillet 1992 · réel |
| 1:10 | 3 | HISTOIRE RÉELLE | La gravité de la planète l'étire, puis la déchire en vingt et un morceaux. | SCÈNE3D : la comète s'étire, se fend, 21 fragments alignés | Jupiter casse la comète | Craquement grave | 21 fragments |
| 1:16 | 3 | HISTOIRE RÉELLE | Deux ans plus tard, les fragments frappent Jupiter, un par un, sous l'œil du télescope Hubble. Le plus gros laisse une cicatrice plus large que la Terre. Pour la première fois, l'humanité regarde une planète se faire frapper, presque en direct. | INTERFACE : images d'archive Hubble ; SCÈNE3D : tache sombre, la Terre à côté pour l'échelle | La blessure dépasse la taille de la Terre | Impacts moyens, puis impact fort | Juillet 1994 · Hubble |
| 1:32 | 3 | HISTOIRE RÉELLE | Et si la même chose arrivait à la Lune ? | SCÈNE3D : la Lune, seule, immobile | Et chez nous ? | Silence bref | — |
| 1:36 | 4 | SIMULATION | Faisons le calcul. La Lune tombe déjà vers nous, en permanence. Si elle ne nous touche pas, c'est qu'elle file de côté, à un kilomètre par seconde. Trois fois la vitesse du son. | COUPE : l'orbite, une flèche de chute et une flèche de côté ; à l'écran seulement : 3 474 km, 73 milliards de milliards de tonnes | Elle tombe et file en même temps | Tic-tac des chiffres | 3 474 km · 73 × 10¹⁸ t |
| 1:49 | 4 | SIMULATION | Supprimez cette vitesse, et il ne reste que la chute. D'après la loi de la gravitation, elle dure quatre jours et dix-neuf heures. | CALCUL : la flèche de côté disparaît ; compteur « 4 j 19 h » | Il ne reste qu'à tomber | Coupure de musique | 4 jours et 19 heures |
| 1:58 | 4 | SIMULATION | Voici la règle qui décide de tout. Quand la distance est divisée par deux, les marées sont huit fois plus fortes. | CALCUL : distance ÷ 2 → marées × 8 | Plus près, beaucoup plus fort | Tic | Distance ÷ 2 → marées × 8 |
| 2:07 | 4 | SIMULATION | Gardez ça en tête. Et retenez ce chiffre : dix-huit mille kilomètres. | CHIFFRE : 18 000 km, seul au centre | Un chiffre mystérieux | Impact moyen dans le blanc | 18 000 km |
| 2:11 | 5 | SIMULATION | Minute zéro. À minuit pile, la Lune perd sa vitesse. Dans le ciel, rien ne change. | CHRONO : T+00:00 ; GLOBE : la Lune immobile | Rien de visible | Nappe sombre, tic-tac lent | Minute 0 |
| 2:18 | 5 | SIMULATION | Heure quinze. Sur le plateau, l'écho revient avec vingt-cinq millièmes de seconde d'avance. Léa envoie ses mesures à Paris, à Washington, à Pékin. | INTERFACE : compteur 2,485 s ; trois fenêtres de messagerie | Elle prévient le monde entier | Bips de messages | Heure 15 · 2,485 s |
| 2:27 | 5 | SIMULATION | Trois réponses. Trois confirmations. | INTERFACE : trois coches vertes | Ce n'est pas une erreur | Silence | — |
| 2:28 | 5 | SIMULATION | Jour un, midi. Les agences spatiales annoncent la chute. Dans le ciel de Paris, la Lune a exactement la même taille que la veille. Les gens lèvent les yeux, et ne voient rien. Dans les écoles, des enfants dessinent la Lune un peu plus grosse chaque jour. | SCÈNE3D : une rue de Paris, des passants immobiles devant une Lune normale | Personne ne voit le danger | Rumeur de rue, radio | Jour 1 · midi |
| 2:47 | 5 | SIMULATION | Vous pensez que le danger commencera quand la Lune grossira dans le ciel ? Faux. Le premier signe est invisible. | SCÈNE3D : la Lune, normale ; puis un annuaire des marées posé sur une table | On se trompe de danger | Coupure, puis tic | Le premier signe est invisible |
| 2:55 | 5 | SIMULATION | Chaque jour, la marée arrive environ cinquante minutes plus tard que la veille, parce que la Lune avance sur son orbite. Sans orbite, ce retard disparaît. Dès le deuxième jour, les horaires imprimés pour l'année sont faux. | INTERFACE : l'annuaire des marées, horaires barrés un à un | Les horaires ne servent plus | Page qu'on tourne | Annuaire des marées |
| 3:10 | 5 | SIMULATION | Jour trois. La Lune paraît à peine plus grosse. Mais à la télévision, les experts ne parlent plus en années. Ils parlent en heures. | SCÈNE3D : un salon, la télévision allumée, un graphique de distance | Le temps presse | Voix de télévision étouffée | Jour 3 |
| 3:19 | 5 | SIMULATION | Tout dépend d'où vous êtes. | CERCLES : quatre cercles autour de l'Europe de l'Ouest | Le danger dépend de l'endroit | Nappe sombre | Où êtes-vous ? |
| 3:21 | 5 | SIMULATION | Premier cercle. Les côtes basses. Aux Pays-Bas, un quart du pays est sous le niveau de la mer. À Rotterdam, les habitants regardent la mer monter un peu plus haut à chaque marée. | SCÈNE3D : une digue de Rotterdam, des habitants alignés qui regardent l'eau | La mer gagne chaque jour | Vent, mer, voix lointaines | Cercle 1 · Rotterdam |
| 3:34 | 5 | SIMULATION | Leurs digues ont été construites contre les tempêtes. Pas contre la Lune. | SCÈNE3D : gros plan sur l'eau qui lèche le haut de la digue | Les protections ne suffiront pas | Clapotis | — |
| 3:39 | 5 | SIMULATION | Deuxième cercle. Les baies à grandes marées. Au Mont-Saint-Michel, la mer monte déjà de plus de dix mètres en temps normal. Les habitants de la baie regardent la règle de marée, puis chargent leurs voitures. | SCÈNE3D : la règle de marée graduée dans la baie ; une voiture qu'on charge | Ils partent | Mouettes, portière | Cercle 2 · Mont-Saint-Michel |
| 3:53 | 5 | SIMULATION | Troisième cercle. Les grandes villes. À Paris, les magasins se vident, et les routes vers le sud et vers les montagnes se remplissent. | SCÈNE3D : un rayon vide ; une autoroute saturée de phares | La population fuit | Klaxons lointains | Cercle 3 · Paris |
| 4:02 | 5 | SIMULATION | Quatrième cercle. Léa, à mille deux cent soixante-dix mètres d'altitude. Ici, aucune vague ne montera. Mais elle doit mesurer chaque kilomètre de la chute. | SCÈNE3D : Léa sur le plateau, la Lune un peu plus grosse ; son carnet ouvert | Elle est à l'abri, mais elle reste | Vent sur le plateau | Cercle 4 · Léa |
| 4:12 | 6 | SIMULATION | Heure quatre-vingt-quinze. La Lune a fait la moitié du chemin. Il lui a fallu quatre jours. L'autre moitié prendra moins de vingt et une heures. | CHRONO : T+95 h ; CARTE : la distance coupée en deux | Ça va s'accélérer | Battement de cœur lointain, drone sombre | Heure 95 · mi-chemin |
| 4:22 | 6 | SIMULATION | Distance divisée par deux : marées huit fois plus fortes. Sur les côtes, la mer monte et descend de plusieurs dizaines de mètres, deux fois par jour. À Rotterdam, les digues cèdent. Des milliers de familles montent dans les trains vers l'Allemagne, sans savoir où elles dormiront. | CALCUL : × 8 en rouge ; SCÈNE3D : la digue de Rotterdam submergée | La règle se vérifie, la digue tombe | Impact moyen, eau qui déferle | × 8 · Estimation |
| 4:40 | 6 | SIMULATION | Sur le plateau, l'écho revient en une seconde deux. D'habitude, deux virgule cinq. | INTERFACE : compteur 1,228 s ; le carnet de Léa, colonne de chiffres | Le chiffre a fondu de moitié | Bip | 1,228 s |
| 4:45 | 6 | SIMULATION | Peu de gens le savent : la Lune tourne sur elle-même. Elle nous cachait sa face arrière parce que ce tour durait exactement une orbite. Sans orbite, la face cachée commence à apparaître. Partout, les gens filment ce visage inconnu. | GLOBE : la Lune qui pivote ; SCÈNE3D : la face cachée vue d'un toit de Paris | On voit ce qu'on n'avait jamais vu | Silence presque complet | Face cachée |
| 5:01 | 6 | SIMULATION | Vous pensez que le danger ne viendra que de la mer ? Peu de gens le savent : le sol aussi a des marées. Il monte et descend de quelques dizaines de centimètres, deux fois par jour. | COUPE : la croûte terrestre qui se soulève sous une ville | Le sol bouge aussi | Grondement très grave | Le sol a des marées |
| 5:15 | 6 | SIMULATION | Avec une force huit fois plus grande, les failles déjà chargées commencent à céder. En Italie, au Japon, au Chili, la terre tremble plusieurs fois par jour. | INTERFACE : sismographe qui s'affole ; CARTE : séismes qui s'allument | Les séismes commencent | Grattement du sismographe | — |
| 5:26 | 6 | SIMULATION | Une question revient partout. Pourrait-on la dévier ? Non. Toutes les armes nucléaires du monde réunies ne représentent même pas un milliardième de son énergie de mouvement. Les agences spatiales étudient chaque idée, et toutes les simulations donnent la même réponse. | SCÈNE3D : salle de crise ; CHIFFRE : une icône de bombe face à une barre immense | Rien ne peut l'arrêter | Brouhaha, puis impact sourd | Pourrait-on la dévier ? |
| 5:42 | 6 | SIMULATION | Vingt heures avant l'impact, la préfecture ordonne l'évacuation de l'observatoire. Le téléphone de Léa sonne. C'est sa mère, à Grasse : « Descends. Viens avec nous. » | INTERFACE : alerte d'évacuation ; le téléphone qui vibre, « Maman » | On lui demande de partir | Sonnerie, puis silence | Évacuation de l'observatoire |
| 5:52 | 6 | SIMULATION | Léa a trois options. Un : partir rejoindre sa famille. Deux : monter dans les Alpes, plus haut encore. Trois : rester, et continuer à mesurer. | CHOIX : cartes 01 « Sa famille », 02 « Plus haut », 03 « Mesurer » | Elle doit choisir | Tic par option, montée tenue | Choix impossible |
| 6:01 | 6 | SIMULATION | Elle reste. Ses mesures permettent aux centres de calcul de prévoir chaque marée, heure par heure, pour ceux qui fuient les côtes. Elle envoie un dernier message à sa mère : « Je regarde pour vous. » | SCÈNE3D : Léa se rassoit, raccroche ; CARTE : prévisions de marée envoyées aux côtes | Elle reste pour les autres | Nappe sombre, plus douce | Option 03 |
| 6:14 | 6 | SIMULATION | — | BOUCLE ACCÉLÉRÉE : compteur d'écho / règle de marée / sismographe / la Lune dans le ciel / carnet, plans de 1,1 s à 0,3 s, puis plan long de Léa | Tout s'emballe en même temps | 6 s : un tic par plan sur une montée, coupure nette, silence | — |
| 6:20 | 6 | SIMULATION | Six heures avant l'impact. Un quart de la distance : marées soixante-quatre fois plus fortes. Gardez ça en tête : la Lune commence à se déformer, étirée vers nous. | CHRONO : impact −06:30 ; CALCUL : × 64 ; SCÈNE3D : la Lune légèrement ovale | La règle encore, la Lune s'étire | Impact moyen | × 64 |
| 6:31 | 6 | SIMULATION | Les océans forment deux bourrelets qui balaient les côtes à chaque rotation. De Rotterdam au Havre, les ports sont noyés puis vidés deux fois par jour. | GLOBE : deux bourrelets d'océan sur l'Europe ; SCÈNE3D : un porte-conteneurs couché, bassin vide | Les ports sont détruits | Grondement d'eau, métal qui grince | Rotterdam · Le Havre |
| 6:42 | 6 | SIMULATION | Peu de gens le savent : une planète que l'on tord se met à chauffer. Autour de Jupiter, la lune Io est pétrie ainsi : c'est le monde le plus volcanique du système solaire. Sur Terre, l'Etna et le Vésuve se réveillent. | SCÈNE3D : Io et ses volcans ; CARTE : l'Etna et le Vésuve qui s'allument | La Terre chauffe de l'intérieur | Grondements successifs | Io · Etna · Vésuve |
| 6:58 | 6 | SIMULATION | Une heure et demie avant l'impact. Un dixième de la distance : marées mille fois plus fortes. En une minute, la Lune parcourt plus de chemin que pendant ses cinq premières heures. | CHRONO : impact −01:27 ; CALCUL : × 1 000 ; même plan que l'ouverture | On rejoint l'image du début | Battement de cœur rapide | × 1 000 |
| 7:10 | 6 | SIMULATION | L'écho revient en deux dixièmes de seconde. | INTERFACE : compteur 0,202 s ; la main de Léa note dans le carnet | Le chiffre s'effondre | Bip | 0,202 s |
| 7:13 | 6 | SIMULATION | Peu de gens le savent : la Lune a ses propres séismes. Les sismographes d'Apollo en ont enregistré des milliers. Cette fois, c'est elle qui tremble, étirée par la Terre. | SCÈNE3D : sismographe d'Apollo sur le sol lunaire, l'aiguille qui s'affole | La Lune se fissure | Craquements graves | Séismes lunaires |
| 7:24 | 7 | SIMULATION | Vous pensez que la Lune va s'écraser d'un seul bloc ? Ce n'est pas certain. Et voici le détail qui change tout. | Noir, puis la Lune immense | Quelque chose d'inattendu arrive | Silence complet, 1 s avant la phrase | — |
| 7:33 | 7 | SIMULATION | Vingt et une minutes avant l'impact, elle passe sous les dix-huit mille kilomètres. Ce chiffre revient maintenant. | CHIFFRE : 18 000 km, le même que plus tôt | Le chiffre retenu revient | Impact fort | 18 000 km |
| 7:40 | 7 | SIMULATION | C'est la limite de Roche, calculée en mille huit cent quarante-huit par Édouard Roche, à Montpellier. En dessous, les marées de la Terre peuvent devenir plus fortes que la gravité qui tient la Lune ensemble. | INTERFACE : manuscrit ancien ; COUPE : la Lune traverse un cercle en pointillés | Une frontière invisible | Nappe sombre | Limite de Roche · 1848 |
| 7:54 | 7 | SIMULATION | Une Lune de roche résiste un peu plus longtemps. Mais elle se fissure, comme la comète devant Jupiter. Elle n'a plus le temps de se disperser : elle arrive fendue, précédée de fragments grands comme des villes. | SCÈNE3D : la Lune fendue, des blocs se détachent devant elle | Elle arrive en morceaux | Craquements, souffle | — |
| 8:08 | 7 | SIMULATION | À dix kilomètres par seconde, l'impact libère des millions de fois l'énergie de l'astéroïde des dinosaures. | CHIFFRE : × 10 000 000 environ ; l'astéroïde minuscule à côté | Rien ne peut y survivre | Montée puis coupure | ≈ × 10 millions |
| 8:14 | 8 | SIMULATION | Plateau de Calern. Léa envoie une dernière impulsion. | SCÈNE3D : même cadrage qu'au début ; le faisceau vert part ; lumière chaude de la Lune immense | La même nuit, le même geste, tout a changé | Silence, puis une note claire tenue | Calern |
| 8:17 | 8 | SIMULATION | L'écho revient en six centièmes de seconde. Elle l'écrit dans son carnet, à la main. | INTERFACE : 0,066 s ; gros plan sur le carnet, l'écriture | Elle note jusqu'au bout | Plume sur papier | 0,066 s |
| 8:23 | 8 | SIMULATION | Puis elle lève les yeux. La Lune remplit le ciel, dorée par le Soleil. Elle n'a jamais été aussi belle. Léa ne détourne pas le regard. Quelque part en bas, sa mère regarde la même Lune. | PLAN LONG (7 s) : Léa de dos, le ciel entièrement rempli par la Lune | Elle regarde, calme | Silence complet, puis blanc | — |
| 8:38 | 9 | HISTOIRE RÉELLE | Maintenant, la vérité. Rien ne peut arrêter la Lune. Ce scénario n'arrivera pas. | Noir ; carte titre « La vérité » | Retour au réel | Silence complet 1,2 s avant ; nappe neutre | La vérité |
| 8:43 | 9 | HISTOIRE RÉELLE | Mais chaque morceau de cette physique est réel. Et une collision géante a déjà eu lieu. Il y a quatre milliards et demi d'années, selon l'hypothèse la plus admise, une planète de la taille de Mars a percuté la Terre. Elle s'appelle Théia. | SCÈNE3D : Théia frappe la jeune Terre | Une collision géante a déjà eu lieu | Grondement lointain | Théia · hypothèse |
| 9:00 | 9 | HISTOIRE RÉELLE | La Terre a fondu, puis elle a refroidi. Et de ses débris est née la Lune. | SCÈNE3D : un anneau de débris qui se rassemble en Lune | La Lune est née d'un choc | Note claire | La naissance de la Lune |
| 9:07 | 9 | HISTOIRE RÉELLE | Aujourd'hui, elle s'éloigne. Trois virgule huit centimètres par an, mesurés au laser, depuis Calern notamment. En une vie, environ trois mètres. | INTERFACE : le vrai compteur d'écho ; une règle de 3 m | Elle s'en va doucement | Bip du laser | +3,8 cm par an |
| 9:15 | 9 | HISTOIRE RÉELLE | Et elle nous protège. D'après les travaux de l'Observatoire de Paris, elle stabilise l'inclinaison de la Terre. Donc nos saisons. | GLOBE : l'axe de la Terre stable, la Lune autour | Elle garde nos saisons | Nappe neutre | Observatoire de Paris |
| 9:23 | 9 | HISTOIRE RÉELLE | Ce soir, si le ciel est dégagé, regardez-la. Sa lumière a mis un peu plus d'une seconde pour vous atteindre. | SCÈNE3D : une fenêtre de Paris, la Lune normale, petite | Une invitation à lever les yeux | Nappe claire | — |
| 9:31 | 9 | HISTOIRE RÉELLE | Deux virgule cinq secondes, aller et retour. Comme toujours. | INTERFACE : compteur 2,510 s, en blanc | Tout est revenu à la normale | Bip doux | 2,51 s |
| 9:35 | 9 | HISTOIRE RÉELLE | Et vous, que feriez-vous de ces cinq jours ? | Noir, texte seul | Une question pour nous | Silence | Et vous ? |

## PARTIE 3 : TITRES, MINIATURE ET DESCRIPTION

**Titres**
- a) « Et si la Lune tombait sur la Terre ? Nous avons calculé chaque heure de la chute »
- b) « En 1994, Jupiter a déchiqueté une comète. Et si c'était la Lune ? »
- c) « La Lune tombe : il nous reste 4 jours et 19 heures » (51 caractères)

**Miniature** : « 4 J 19 H » en très gros (ambre). Image : le Mont-Saint-Michel au premier plan, une Lune immense et fissurée
qui remplit le haut du ciel, une flèche vers la fissure. Une seule idée : la Lune est trop près, et elle se fend.

**Description**
```
Et si la Lune perdait sa vitesse et tombait sur la Terre ? Nous avons calculé la chute, heure par heure : 4 jours et 19 heures. Et la Lune n'arriverait peut-être pas en un seul morceau.

Ceci est une simulation. Ce n'est ni une prédiction, ni une prévision : rien ne peut arrêter la Lune. Le personnage de Léa est inventé. La physique, les données et les événements réels cités (la comète Shoemaker-Levy 9 en 1994, la limite de Roche, l'hypothèse de Théia) sont réels.

En réalité, la Lune s'éloigne de la Terre d'environ 3,8 cm par an.

CHAPITRES
00:00 Une heure et demie avant l'impact
0:00 Calern, quatre jours plus tôt
0:00 1994 : Jupiter déchire une comète (histoire réelle)
0:00 Faisons le calcul
0:00 Minute zéro : la chute commence
0:00 Heure 95 : la moitié du chemin
0:00 Le détail qui change tout
0:00 Le dernier écho
0:00 Maintenant, la vérité
```
Remplacer les `0:00` par les horaires du rendu (`chapitres.txt`).

## PARTIE 4 : SOURCES ET VÉRIFICATIONS

**Calculs faits par nous** (chute radiale depuis 384 400 km, masse Terre + Lune) : durée de la chute 4,82 jours
(impact à 4 j 19 h) ; mi-distance à la 95e heure, 20,9 h avant l'impact ; quart 6,5 h avant ; dixième 1,45 h avant ;
18 000 km 21 min avant ; vitesse d'impact environ 9,9 km/s ; énergie environ 3,6 × 10³⁰ J, soit environ 9 millions de
fois l'impact de Chicxulub (4 × 10²³ J) ; énergie de mouvement à mi-distance 7,7 × 10²⁸ J ; écho laser 2,51 s
(surface à surface), 1,23 s, 0,20 s, 0,066 s ; rotation de la Lune pendant la chute environ 60° ; taille apparente
× 2, × 4, × 12, × 32. Dernière minute avant l'impact : environ 570 km parcourus, contre environ 440 km pendant les
cinq premières heures.

| Fait | Où | Source à citer |
|---|---|---|
| Diamètre 3 474 km, masse 7,35 × 10²² kg, distance 384 400 km, vitesse orbitale environ 1 km/s | temps 4 | NASA, fiche Lune |
| Éloignement de 3,8 cm par an mesuré au laser | temps 9 | NASA ; Observatoire de la Côte d'Azur (station de Calern) |
| Shoemaker-Levy 9 : brisée en juillet 1992 près de Jupiter, 21 fragments, impacts en juillet 1994, observés par Hubble, traces plus larges que la Terre | temps 3 | NASA / JPL ; ESA |
| Limite de Roche : Édouard Roche, Montpellier, 1848 ; environ 18 000 km pour une Lune fluide, moins pour une Lune rigide | temps 4, 7 | histoire de l'astronomie |
| Io, monde le plus volcanique du système solaire, chauffé par les marées | temps 6 | NASA |
| Séismes lunaires enregistrés par les sismographes d'Apollo | temps 6 | NASA |
| Hypothèse de Théia | temps 9 | NASA ; CNRS |
| La Lune stabilise l'inclinaison de l'axe terrestre | temps 9 | Laskar, Joutel et Robutel, 1993 (Observatoire de Paris) |
| Un quart des Pays-Bas sous le niveau de la mer ; marnage de plus de 10 m au Mont-Saint-Michel | temps 5 | Rijkswaterstaat ; SHOM |
| Retard quotidien de la marée d'environ 50 min | temps 5 | SHOM |
| Marées terrestres (le sol monte et descend) | temps 6 | IGN / géodésie |

**Éléments de fiction** (étiquette « Simulation ») : Léa, sa mère, l'ordre d'évacuation de l'observatoire, les scènes de
Rotterdam, du Mont-Saint-Michel et de Paris, les digues qui cèdent, les séismes et volcans déclenchés.

**[À VÉRIFIER]**
1. L'amplitude des marées terrestres (« quelques dizaines de centimètres » ; environ 30 cm souvent cité).
2. Que la station de Calern participe bien à la mesure de l'éloignement de la Lune.
3. « Toutes les armes nucléaires du monde réunies ne représentent même pas un milliardième » de 7,7 × 10²⁸ J : vérifier la puissance totale de l'arsenal mondial (quelques milliers de mégatonnes, environ 10¹⁹ J).
4. Les marées « de plusieurs dizaines de mètres » à mi-distance : estimation, signalée à l'écran.
5. Le comportement d'une Lune rocheuse sous la limite de Roche (fissuration plutôt que dispersion) : formulation prudente gardée.

## PARTIE 5 : AUTO-CONTRÔLE

| Critère | Cible | Valeur mesurée | OK ? |
|---|---|---|---|
| Mots de voix | 1 425 à 1 575 | 1431 | OK |
| Mots par phrase (moyenne) | 8 à 10 | 8.6 | OK |
| Phrases de 4 mots ou moins | ≥ 20 % | 24 % | OK |
| Chiffres par minute (voix + écran) | ≥ 3 | min 9 ; par minute [15, 27, 15, 9, 25, 11, 18, 17, 10] | OK |
| Les 9 temps dans l'ordre | oui | oui (ouverture avec retour en arrière) | OK |
| Boucle plantée (temps 4) et payée (temps 7) | oui | « Retenez ce chiffre : 18 000 km » → « Ce chiffre revient maintenant » | OK |
| Motif répété 3 fois | oui | « deux virgule cinq secondes » (l'écho) : temps 1, 6 et 9 | OK |
| Personnage aux temps 1, 5 et 8 | oui | Léa aux temps 1, 5, 6 et 8 | OK |
| Réel / inventé dit au début et à la fin | oui | temps 2 et 9 | OK |
| Dates et nombres en lettres dans VOIX | oui | oui | OK |
| Règle simple vérifiée à chaque palier | oui | ÷ 2 → × 8 ; vérifiée à × 8, × 64, × 1 000 | OK |
| Question du spectateur à voix haute | oui | « Pourrait-on la dévier ? Non. » | OK |
| Fait surprenant par palier | 1 par palier | face cachée, sol qui a des marées (mi-chemin) ; Io (quart) ; séismes lunaires (dixième) | OK |
| Phrase à contredire dans l'ouverture | oui | « C'est le capteur. Redémarre-le. » | OK |
| « Vous pensez que… ? » (certitudes renversées) | 3 | le premier signe est invisible (5) ; pas seulement la mer (6) ; pas d'un seul bloc (7, annoncé dès l'ouverture) | OK |
| Dilemme du personnage | oui | évacuation ordonnée + appel de sa mère → elle reste, ses mesures servent aux prévisions de marée | OK |
| Objets-témoins (≥ 4 plans, état qui change) | oui | compteur d'écho 2,51 → 2,485 → 1,228 → 0,202 → 0,066 → 2,51 s ; carnet de Léa ; règle de marée ; digue de Rotterdam | OK |
| Boucle accélérée | oui | temps 6, 6 s, finit sur un plan long et une coupure | OK |
| Plan long ≥ 6 s au temps 8 | oui | 7 s | OK |
| Même lieu et cadrage aux temps 1 et 8 | oui | Calern, même cadrage ; l'image de l'ouverture revient aussi au palier « une heure et demie » | OK |
| Silences complets | ≥ 2 | avant « Vous pensez que la Lune va s'écraser d'un seul bloc ? » et avant « Maintenant, la vérité » | OK |
| Colonne SANS LE SON remplie | chaque plan | oui | OK |
