# Guide de montage : leçons appliquées à nos vidéos

Résumé de tutoriels de montage (Film Editing Pro) et de deux skills MIT
([mromidev/claude-animated-shorts](https://github.com/mromidev/claude-animated-shorts),
[kelano86/what-if-animation](https://github.com/kelano86/what-if-animation)), traduits en règles pour nos outils
(`panne_internet/render.py`, `panne_internet/fx.py`). Règle générale : **mesurer, pas opiner**.

## 1. Son (« sound design »)
- **Trois couches** : musique, puis ambiance et bruitages, puis sons « créatifs » pour l'invisible (émotions, mouvements).
- **La musique suit le montage** : les montées et les creux tombent sur les coupes et les moments clés, pas toutes les 8 s.
- **Une ambiance par lieu** : rien n'est silencieux (ventilation, ville lointaine, ronronnement de serveurs).
- **Jamais deux fois le même son** : variantes de hauteur, de durée, de rythme.
- **Réverbération de pièce** sur les bruitages des scènes d'intérieur (un bus de réverbération commun).
- **Retenue** : trois niveaux d'impact (fort, moyen, léger). Si tout est spécial, plus rien ne l'est.
- **Niveaux** : voix vers −12 dB (la plus forte), effets entre −10 et −30 dB, musique entre −20 et −30 dB. Master à −14 LUFS.

## 2. Émotion
- **Trouver le moment clé** et construire tout le reste pour y mener.
  Pour la panne d'Internet : le temps 8, « Son fils est tiré d'affaire ».
- **Ne pas le gaspiller avant** : pas de douceur ni de soulagement avant ce moment.
- **Ralentir** : pauses plus longues (1,5 à 2 s), caméra presque immobile, plans qui durent.
- **Contraste** : on retire tout ce qui a dominé la vidéo (bips, battement de cœur, froid, interfaces) et on le remplace
  par du silence, une lumière chaude, un accord majeur, un seul son concret (la radio).
- **Le son raconte** : le réseau est l'antagoniste, ses sons sont sa voix ; ils disparaissent au moment clé.

## 3. Techniques de bande-annonce (intro et moments forts)
- **Ping-pong voix / musique** : la voix dit, puis la musique répond dans le blanc. **Jamais un accent sur un mot.**
- **Coupure de musique (« stop-down »)** juste avant la phrase la plus importante, dite dans le silence, puis reprise forte.
  Pour la panne d'Internet : « La lumière brille, mais les données ne passent plus », « Et si Internet s'arrêtait
  soixante-douze heures ? », « Et voici le détail qui change tout », « Maintenant, la vérité ».
- **Peu de sons, bien placés** : deux bons effets valent mieux qu'un mélange confus.
- **Contrôle automatique** : aucun effet ni accent ne doit s'approcher à moins de 3 dB de la voix pendant un mot
  (comme `mixcheck.py` du skill What If). Il faut l'horodatage des mots (ElevenLabs `convert_with_timestamps` ou Whisper).

## 4. Images : couverture, inserts, direction
- **Couverture** : 2 ou 3 cadrages par scène (large, moyen, détail), coupés aux fins de phrases ; cible ≈ 5 coupes/min.
- **Inserts** (écran du terminal, horloge, notification, cadran de radio) pour régler le rythme.
- **Le cadrage le plus serré est réservé aux moments clés** ; ailleurs, cadrages plus larges.
- **Cohérence de direction (règle des 180°)** : Marc regarde toujours du même côté, le voisin reste du même côté,
  le globe tourne toujours dans le même sens, les glissés de caméra sont cohérents au sein d'une même partie.

## 5. Questions et réponses (ce qui guide chaque coupe)
- **Chaque plan pose une question ou y répond** (ou les deux). Une question naît de ce qu'on cache, une réponse de ce
  qu'on montre : le gros plan dit *qui*, le très gros plan ce qu'il *ressent*, le plan moyen ce qu'il *fait*, le large *où*.
- **Du moins vers le plus** : commencer serré (question) puis élargir (réponse). Un plan peut le faire sans coupe,
  par un **mouvement de caméra qui révèle** (zoom arrière du détail vers le lieu), comme un plan-séquence.
- **Jamais deux plans qui disent la même chose**, et l'image ne répète pas ce que dit déjà la voix : elle ajoute.
- **Test** : écrire une phrase par plan. Si la liste est ennuyeuse, le montage l'est aussi.
- **Début de scène = plus de questions, fin = plus de réponses**, en laissant une question ouverte pour la scène suivante.
- Pour la panne d'Internet, ouverture : détail de l'écran « REFUSÉ » (*que se passe-t-il ?*) → Marc avec son fils
  (*qui ?*) → la station, la ville éclairée (*où ?*), par un zoom arrière continu.

## 6. Ponts sonores (le son de la scène suivante commence avant l'image)
- **Bruitage** : on entend la scène suivante avant de la voir (une foule avant la file au distributeur, les bips d'un
  moniteur avant l'hôpital, le grésillement de la radio sous la fin du temps 7). Avance de 0,5 à 1,5 s.
- **Musique** : l'accord chaud du moment clé (temps 8) démarre sous la dernière image du temps 7.
- **Voix** : sur certaines transitions, la phrase suivante démarre 0,3 à 0,5 s avant la coupe.
- Effet : continuité, on prépare le spectateur à la suite sans le surprendre malgré lui ; à utiliser sur les
  changements de lieu et de temps, pas sur chaque coupe.

## 7. Drones (nappes tenues) plutôt qu'une musique mélodique
Une mélodie en continu en dit souvent trop ; une nappe tenue soutient sans s'imposer. Trois humeurs :
- **Sombre et menaçant** (grave, désaccordé, souffle filtré) : danger, tension. Pour la simulation et l'escalade
  (temps 5 et 6). À ne pas surutiliser.
- **Neutre, ambigu** (quintes ouvertes, timbre de cordes chaud avec un peu de tension) : peut mener vers n'importe quelle
  émotion. Pour l'ouverture, la vraie histoire, le calcul (temps 1 à 4), et comme **pont** pour entrer dans un
  passage plus musical sans que la musique « sorte de nulle part ».
- **Clair et apaisé** (registre aigu, accord majeur avec neuvième) : espoir, soulagement. Réservé au moment clé
  (temps 8), après la coupure de musique.
Les trois sont générés en code (aucun droit), avec des fondus de plusieurs secondes entre eux.

## 8. Caméra (mesures de mromidev/claude-animated-shorts)
- Glissés lissés de 18 à 40 images, poussée lente pendant les plans fixes (jamais d'image figée),
  secousse sur 7 images et petite rotation sur les impacts, coupes franches seulement sur les grands sauts.
- Contrôle qualité : `ffmpeg freezedetect` / `blackdetect` sur chaque rendu.
