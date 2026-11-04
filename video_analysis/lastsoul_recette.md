# Recette : « 1 MINUTE » (Last Soul, 1,07 M de vues)

Analyse faite le 4 novembre 2026 sur la vidéo partagée par Drive (non conservée dans le dépôt).
Outils : `analyze_video.py` (coupes, planches, volume), une image par plan, courbe du son par chapitre
(volume, graves, aigus, attaques sonores). Chiffres mesurés, interprétations signalées comme telles.

## Fiche
- Court-métrage d'animation 2D de **4 min 59**, **sans voix off**. Les rares répliques sont écrites à l'écran
  (bulles de texte), une par plan au maximum.
- Chaîne créée le 4 octobre 2026. Vidéo publiée le 11 octobre (2e vidéo). Autres vidéos : 3 000 à 60 000 vues.
- Engagement faible pour la taille : 1,4 % de likes, 0,6 commentaire pour 1 000 vues (2 à 7 sur ses autres vidéos).

## Structure (chapitres de la description)
| Partie | Début | Durée | Ce qui se passe |
|---|---|---|---|
| Big Plans | 0:00 | 1:03 | Achat des chaussures, plan « 10K EVERY DAY » sur le frigo, puis l'échec en accéléré |
| Giving Up | 1:03 | 1:07 | Il range tout, rapporte les chaussures. « Can you run one minute? » |
| One Minute | 2:10 | 0:47 | Il essaie une minute, la nuit, puis une citation sur fond noir (Épictète) |
| Day by Day | 2:57 | 1:09 | Nouveau plan « 1 MIN EVERY DAY », les cases cochées, il court sous la pluie |
| Where It Takes You | 4:06 | 0:54 | Course dans la nature, retour au magasin, titre « 1 MINUTE » à la fin |

L'échec occupe les deux premières minutes : le spectateur reconnaît son propre échec avant d'avoir la solution.

## Montage (mesuré)
- 59 coupes détectées, plan moyen 5 s (médiane 3,1 s). Coupes par minute : **24, 12, 5, 11, 7**.
  Il y en a un peu plus en réalité : plusieurs passages se terminent par un **fondu au noir**, que le détecteur ne
  compte pas comme une coupe.
- **L'accélération de l'échec** (0:35 à 0:59) : une boucle de 3 plans (réveil 5:30 et excuse écrite → main qui
  barre une case → chaussures intactes). Elle se répète en raccourcissant : 2,1 s → 1,0 s → 0,8 s → 0,6 s → 0,5 s.
  Elle se termine sur un gros plan fixe de 6,9 s sur les croix rouges. C'est le moment le plus rapide de la vidéo.
- **Le ralentissement de l'abandon** (1:03 à 2:10) : plans de 3 à 10 s, personnage recroquevillé, dialogue lent.
- **Les inserts racontent à la place d'une voix** : réveil avec date et excuse (« Too cold. », « It's Sunday. »),
  calendrier barré puis coché, étiquette « 14-DAY RETURNS », alarme renommée « RUN 1 MIN » puis « RUN 5 ».
- **Le même décor au début, au milieu et à la fin** (le comptoir du magasin, mêmes cadrages) : on mesure le
  chemin parcouru sans explication.
- **Le titre n'apparaît qu'à la fin** (« 1 MINUTE – Just start. See where it takes you. »), sur fond noir.

## Son (mesuré)
| Partie | Volume médian | Attaques sonores / min | Lecture |
|---|---|---|---|
| Big Plans | −14 dB | 42 | musique pleine, graves présents, rythmée |
| Giving Up | −25 dB | 17 | presque plus de musique, graves plats (ambiance seule) |
| One Minute | −25 dB | 47 | calme, bruitages précis (pas, minuteur) |
| Day by Day | −22 dB | 40 | la musique revient par blocs, coupée net par moments |
| Where It Takes You | −17 dB | 7 | la musique porte tout, presque plus de bruitages |

- **La musique s'arrête net à 1:01**, à la fin de l'accélération : 11 dB de moins d'un coup. C'est le passage à l'échec.
- **Silences complets** à 2:56 (avant la citation) et à 3:21 (avant le nouveau plan). Ils servent de respiration
  avant chaque nouveau départ.
- Seulement 10 coupes sur 59 tombent sur une attaque sonore : le son n'est pas collé aux coupes, il suit l'action
  (bruitages) et l'émotion (musique).
- Volume intégré −18 LUFS, plus bas que la norme YouTube (−14).

## Design
- Personnages **silhouettes noires** avec seulement deux yeux et des sourcils : l'expression passe par les
  sourcils et la posture. C'est simple à animer, et chacun peut s'y projeter.
- Décors 2D plats et propres. **Couleur au service de l'histoire** : gris et bleu froid dans l'échec, nuit et
  lampadaires pour l'effort, puis vert et lumière chaude à l'arrivée. Le rouge est réservé aux croix.
- Texte à l'écran : quelques mots par plan (bulles, notes, écrans), toujours lisibles.

## Ce qu'on reprend pour WhatIfcastFR
1. **Raconter par objets** : un objet qui change d'état (calendrier barré puis coché) remplace une phrase de voix.
   Pour nous : le terminal « REFUSÉ », la carte, le frigo, la radio.
2. **Accélérer puis couper** : une boucle de plans qui raccourcit jusqu'au point de rupture, puis la musique
   coupe net. C'est notre « stop-down », avec une accélération en plus.
3. **Contraste son par partie** : on change de niveau entre deux parties (−14 dB puis −25 dB), et un silence
   complet avant chaque nouveau départ.
4. **Revenir au même lieu** au début et à la fin pour montrer le changement sans le dire.
5. **Couleur par partie** : froid quand ça va mal, chaud au moment clé (comme notre temps 8).

## À ne pas copier
- Son style visuel (silhouettes noires) ni ses histoires : les commentaires le confondent déjà avec une autre chaîne.
- Le titre à la fin marche pour une fiction sans voix. Chez nous, la question « Et si… ? » doit rester au début.
