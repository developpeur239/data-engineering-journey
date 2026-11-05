# Plan de rendu v2 : « Le Dernier Écho » (dossier V12)

But de la v2 : **plus de qualité à l'écran, moins de fabrication et moins d'aller-retours**. Elle remplace la v1
sur quatre points : texte verrouillé avant toute génération, décors fusionnés, animatique avant tout rendu animé,
schémas faits en 2D. Le découpage scène par scène et les choix de style de la v1 restent valables sauf mention.

## 0. Ce que la v2 change

| | v1 | v2 | Gain |
|---|---|---|---|
| Décors ou effets à créer | 10 (dont 2 G) | **5 (dont 1 G)** | environ 40 % de fabrication en moins |
| Durée de voix | environ 13 min 43 (2 112 mots à 154 mots/min), non tranché | **environ 11 min 41 (1 799 mots, texte V13)** | une seule génération ElevenLabs (environ 11 000 crédits au lieu de 13 000, sans regénération) |
| Validation | sur vidéo rendue | **sur animatique** (une image par plan + voix) | les erreurs de cadre et de rythme coûtent une image, pas un rendu |
| Schémas (orbite, laser, marées, carte, compteurs) | studio 3D | **2D Tesseract** (rendu en secondes) | 10 blocs sortis du rendu 3D image par image |
| Angles de caméra | libres par plan | **3 angles fixes par décor**, réutilisés | réglage fait une fois ; le cache resservira |

## 1. Règles de production

1. **Verrouiller avant de générer.** Aucune voix finale tant que le texte n'est pas coupé (section 2). Le débit de
   Nicolas est connu : **environ 154 mots/min**, mesuré lors de la comparaison des 4 voix sur le script de la panne
   d'Internet. Un test sur un bloc (environ 400 crédits) reste possible si la direction « posée, proche » le ralentit.
   Ce serait une confirmation, pas une étape obligatoire.
2. **Animatique d'abord** (livrable demandé par le dossier) : `render.py --stills` donne une image par plan. On la
   monte sur la voix témoin avec les sons temporaires. On valide le rythme, les cadres et les silences protégés, puis
   seulement on anime. Relecture par **planche-contact** : une image regroupe environ 12 plans, ce qui économise du
   temps et des jetons.
3. **Un décor = un plateau à réglages** (heure, niveau d'eau, taille de la Lune, figurants). Il a 3 angles fixes :
   plan large, plan moyen, détail. La caméra reste fixe ou pousse lentement (leçon de la vidéo Internet : un plan
   figé paraît gelé, une poussée lente suffit).
4. **Plans décrits en données**, une ligne par plan (décor, angle, réglages, poses, texte, son), dans le même format
   que `scenes.py`. Pas de code écrit plan par plan.
5. **Rendu en deux passes** : 720p pour la validation, 1080p une seule fois à la fin. Rendu par bloc d'une minute,
   avec le cache par segment et `--audit` (collisions).
6. **2D pour tout ce qui explique** : aller-retour du laser, compteurs « 2,51 s » et « 0,066 s », orbite et chute,
   marées (face proche et face éloignée), énergie comparée, carte, multiplicateurs « × 60 » et « × 940 ». Ces
   schémas se font dans Tesseract (projet modifiable, export MP4 en quelques secondes). Deux conditions avant d'en
   produire un seul des 10 :
   - **Intégration testée** : un schéma d'essai inséré dans `render.py` (P). Aujourd'hui, `render.py` assemble ses
     propres segments et boucles MP4, mais n'insère pas encore de MP4 venu d'ailleurs.
   - **Même typographie que le studio** (thème `bricolage` de `index.html`, même casse normale) :
     titres en Bricolage Grotesque, textes et étiquettes en Instrument Sans, **chiffres en Fragment Mono**, cartes
     en EB Garamond, bulles en Comic Neue. Ces fichiers sont importés dans chaque projet Tesseract, avec un modèle
     unique (couleurs, tailles, marges) copié pour chaque schéma.
   - **Solution de repli** si l'un des deux échoue : faire les schémas dans le HUD HTML du studio. Ils ont alors les
     mêmes polices par construction, mais coûtent plus cher à rendre.

## 2. Coupes pour tenir 12:40 (environ 320 mots et 7 raccords)

À 154 mots/min, les 2 112 mots du V12 donnent environ 13 min 43 de voix. C'est compté comme dans
`compare_voices.py`, qui a donné les 154 mots/min (ni ponctuation, ni noms des voix). Un premier comptage, qui
incluait la ponctuation, donnait par erreur 2 182 mots et 14 min 10. Les nombres de mots du tableau ci-dessous
viennent de ce premier comptage. **Règle : la voix ne décrit jamais l'image.** On coupe les phrases qui racontent ce que l'image montre déjà, ou
ce qu'un texte à l'écran dit déjà. **Aucune réplique n'est touchée**, et l'histoire non plus. Les blocs à couper en
priorité sont justement les fils humains : on y retire la description et on garde les répliques et les silences.

| Bloc | Phrases retirées (l'image ou l'écran les montrent) | Mots |
|---|---|---|
| 00:42 | « Sur les trottoirs, des centaines de personnes regardent vers le haut. » « Personne ne parle. » « Certains filment. » (la phrase suivante commence alors par « Certains » au lieu de « D'autres ») | 16 |
| 03:47 plage | « Il tient encore son seau en plastique. » « Il regarde l'eau. » « Sa mère ne répond pas immédiatement. » « Parce que c'est justement ce qui rend la situation si difficile à comprendre. » Le silence après « Mais elle est comme d'habitude » le dit déjà. | 29 |
| 04:28 voiture | « Il regarde par la vitre. » « Il prend une photographie avec le téléphone de sa mère. » « Puis il ouvre celle qu'il avait prise la veille. » « Il rapproche les deux images. » « Sa mère regarde le ciel. » Les deux photos à l'écran disent tout. | 34 |
| 05:00 | « La Lune occupe désormais une place inhabituelle dans le ciel. » « On distingue ses reliefs avec une netteté troublante. » | 18 |
| 05:25 collègue | « Léa regarde l'écran… » « Son collègue est déjà près de la porte. » « Elle ne répond pas. » La lecture du SMS de la sœur, que le dossier veut écrit à l'écran et non lu. « Léa commence à écrire une réponse. » « Puis elle efface. » | 50 |
| 06:30 | Les deux sirènes (le son les fait entendre), les conducteurs qui sortent, « Quelqu'un pointe l'horizon », la main prise, la voiture abandonnée, la course | 33 |
| 09:00 | « Elle regarde son téléphone. » La lecture du dernier SMS (écrit à l'écran). « Léa ferme les yeux une seconde. » « Sous le message, un mot apparaît. « Écouté. » » (le statut est à l'écran, et le silence qui suit est protégé). « Léa fixe l'écran. » « Puis elle le pose. » | 44 |
| 09:27 | « La lumière part. » « Elle atteint la Lune. » « Et revient. » « Sur l'écran, un nombre apparaît. » (le compteur le montre) | 14 |
| 09:48 | « Puis elle se lève. » « Dehors, la Lune occupe une portion immense du ciel. » « Léa ne bouge plus. » | 17 |
| 10:47 colline | « Derrière eux, la route a disparu sous l'eau. » « Devant eux, la Lune semble se déchirer. » « Elle s'agenouille devant lui. » « Le prend dans ses bras. » « Au-dessus d'eux, les fragments continuent de tomber. » « Son contour est déchiré. » « Elle est immense. » La place libérée va à « Je suis là » et à la pause qui suit. | 38 |
| 11:26 | « Depuis l'espace, on voit le nuage de débris… » « La surface que nous connaissons disparaît… derrière une immense enveloppe de matière brûlante. » | 27 |
| 10:47 colline (en plus) | « Et lui répond doucement : ». On entend la question du garçon, un temps, puis « Je suis là. » | 4 |
| **Total** | | **324** |

**Raccords obligatoires.** Sans eux, une phrase perd son sujet ou son antécédent. Chaque coupe a été relue dans son
contexte, en tenant compte des phrases voisines retirées, y compris d'un bloc à l'autre.

| Bloc | Après la coupe | Raccord |
|---|---|---|
| 00:42 | « D'autres restent immobiles… » (sans « Certains filment ») | « **Certains** restent immobiles… » |
| 04:28 | « Elle connaît la réponse. », juste après la réplique sur la Lune : « Elle » peut s'entendre comme la Lune | « **Sa mère** connaît la réponse. » |
| 05:00 | « Et sa vitesse de rapprochement augmente. » : « sa » renvoie au « changement » | « Et **la** vitesse de rapprochement **de la Lune** augmente. » |
| 09:00 | « Puis elle enregistre un message vocal. » : « Puis » n'a plus rien avant lui | « **Elle** enregistre un message vocal. » |
| 09:27 | « Et retourne vers le laser. » : sans sujet (« Léa fixe l'écran. Puis elle le pose. » est retiré en fin de 09:00) | « **Elle** retourne vers le laser. » |
| 09:48 | « Les zones sombres qui traversent sa surface… » : « sa » renvoie à « la mesure », et « zones sombres » se confond avec les mers lunaires naturelles | « **Les immenses fractures sont désormais visibles à l'œil nu.** » (après l'audit V13) |
| 10:47 | « Et lui répond doucement : » : sans sujet | **Coupé** (ligne ajoutée au tableau ci-dessus) |

**À surveiller, sans changement pour l'instant :**
- **03:47 :** sans « Il regarde l'eau. », le « elle » de « Mais elle est comme d'habitude » n'a plus d'antécédent à
  l'oral. L'image de la mer et la bulle suffisent. Si la planche-contact montre une hésitation, on remet ces 4 mots.
- **05:25 :** les deux répliques du collègue se suivent sans narration entre elles. Le temps qui les sépare est porté
  par l'image : le SMS à l'écran, puis Léa qui écrit et efface.
- **09:27 :** « 0,06 seconde. » arrive juste après « Léa lance une dernière impulsion. », en même temps que le
  compteur à l'écran.

**Bilan, mesuré sur le texte appliqué (`texte_voix_V13.md`)** : 313 mots en moins. Il reste 1 799 mots, soit environ
11 min 41 de voix et environ 59 s pour les silences et le noir final. Les silences protégés en demandent environ 25.
La marge restante (environ 35 s) absorbe un Nicolas plus lent avec la direction « posée, proche » : à 145 mots/min,
on arrive à 12 min 24. Si la planche-contact montre qu'un bloc manque d'appui, on peut remettre quelques
phrases (d'abord « Il regarde l'eau. » à 03:47). Toutes les phrases ont été vérifiées mot pour mot dans le dossier V12.
Coupes et raccords restent **à valider par toi** : je ne réécris rien sans accord.

## 3. Décors : 5 à créer au lieu de 10

| # | Élément | Taille | Remplace (v1) | Sert à |
|---|---|---|---|---|
| 1 | **Silhouettes** des 4 personnages dans `people.js`, + poses « agenouillé » et « téléphone à l'oreille » | M | n° 1 | toute la vidéo |
| 2 | **Calern** : coupole, console, laser, extérieur ; réglages nuit et jour | M | n° 2 | 9 blocs |
| 3 | **Littoral** : un seul plateau, avec plage, barrière, quai et bateaux, route en contrebas et colline. Un plan d'eau à niveau réglable (marée haute, mer retirée, inondation) | M+ | n° 5, 6, 7 et 10 (plage, autoroute, port, colline) | 03:00–04:00, 06:00–07:00, 10:47, 12:01 |
| 4 | **La Lune** : un module unique (taille, fissure qui s'étend, bord qui se déforme, fragmentation en blocs, traînées en particules) | G | n° 3, 4 et 9 | 8 blocs + 10:00–10:47 |
| 5 | **Collision vue de l'espace** : le `globe` existant, un halo incandescent et des particules, sans simulation | M | n° 8 | 11:00–11:50 |

Réutilisés tels quels : `apartment` (nuit), `street` (nuit et jour, voitures-blocs pour l'embouteillage), `airport`,
`monitors`, `globe`, `phone`, étiquettes, cartes, bulles, compteurs, `edit_plan.py`, `fx.py`.

Simplifications qui ne se voient pas à l'écran :
- l'intérieur de la voiture se réduit au cadre de la vitre ;
- la course se filme de côté, de loin, à contre-jour ;
- la façade ne s'effondre pas : des débris tombent dans le cadre ;
- la foule reste immobile (de toute façon, la peur fige).

## 4. Qualité : ce qui ne se négocie pas

- **Une émotion** : l'angoisse retenue qui monte, puis le soulagement. Chaque plan sert l'une des deux.
- **Le fil du seau rouge** : il apparaît à la plage, dans la voiture, sur la colline et à la plage finale. C'est le
  seul objet en couleur vive à côté de l'écharpe ambre de Léa.
- **Une seule Lune**, à la bonne taille dans chaque bloc (× 1,1 / × 2 / × 4 / × 12 / × 32), avec une fiche de
  réglages unique.
- **Silences protégés** : 00:42 (1 à 2 s), après la question du garçon, après « Écouté », après « Je suis là », le noir
  de 4 s à 11:50, puis Léa et l'enfant AVANT « Heureusement… ».
- **Lisibilité sur mobile** : textes d'au moins 44 px en 1080p, un seul texte à la fois, 1,5 s de lecture pour 3 mots.
- **Honnêteté** : « Simulation » en permanence (00:00–11:50), « Histoire réelle » sur l'insert de 1994, aucun
  multiplicateur montré comme une hauteur d'eau.
- **Son** : aucun son réaliste dans le vide ; la musique se coupe sur « notre monde ».

## 5. Ordre de fabrication

1. Valider les coupes, puis générer la voix finale une fois. Tester puis générer les 2 répliques féminines. En
   parallèle, faire l'essai d'intégration d'un schéma Tesseract dans `render.py`, avec les polices du studio.
2. Construire les décors 1 et 2, sortir les images fixes des blocs Calern, puis l'animatique partielle.
3. Construire les décors 3 et 4, puis l'animatique complète. **Point de validation avec toi.**
4. Faire les schémas 2D (Tesseract).
5. Construire le décor 5 (collision).
6. Animer et rendre en 720p, bloc par bloc ; le son (`fx.py`, `sfx_real.py`) suit au fil des blocs.
7. Rendre en 1080p une seule fois, faire le contrôle final, puis la miniature.

## 6. Points ouverts

1. **Texte V13** : 1 792 mots, 8 phrases réécrites, une coupe en plus, aucune réplique touchée. Les deux corrections de l'audit (08:31, 09:48) sont appliquées. À valider avant de générer.
2. **Point d'impact** (déclinaison de la Lune) : à fixer avant le décor 5.
3. **Archives de 1994** : les images NASA sont en général libres. Celles d'ESA/Hubble sont sous CC BY 4.0, donc
   crédit obligatoire. À vérifier image par image.
4. **Voix des personnages** : réglé, le casting est complet (section 7.3).
5. **Style des personnages** : tu m'avais dit de ne pas copier les silhouettes noires de Last Soul. Ce plan les garde
   parce que l'essai `perso_marc.html` a été validé. À confirmer.
6. **Compte à rebours de 02:00** : réglé, 4 j 20 h est présenté comme la durée totale de la chute (section 7.1).
7. **Carte « Cinq jours plus tôt »** (00:42) : la garder sur le matin du début de la chute, ou la passer à « Quatre
   jours plus tôt » (section 7.1 bis).
8. **Étiquette « Simulation » permanente** : le dossier V12 l'impose pour l'honnêteté. L'audit propose une mention
   discrète au début, pour que la révélation finale garde sa force. Variante intermédiaire : une étiquette très
   petite et peu visible, gardée jusqu'à la collision. Décision à prendre par toi.

## 7. Après l'audit croisé (V1, V2, V13)

### 7.1 Fiche Lune unique (recalculée)
Calcul fait en chute libre depuis le repos à 384 400 km, avec la masse de la Terre et celle de la Lune.
L'observateur est sous la Lune. La chute dure **4 j 19 h 36 min** jusqu'au contact. Tous les visuels
(taille, compteurs, infographies) lisent cette fiche, et rien d'autre.

| Moment | Distance (centres) | Taille apparente | Force de marée | Écho laser |
|---|---|---|---|---|
| Anomalie (début + 17 h) | 379 000 km | × 1,0 | × 1 | 2,48 s |
| Début + 2 j | 342 000 km | × 1,1 | × 1,3 | 2,23 s |
| Début + 4 j | 185 000 km | × 2,1 | × 9 | 1,18 s |
| 6 h avant | 91 000 km | **× 4,5** | **× 75** | 0,56 s |
| 1 h 30 avant | 39 000 km | × 11,5 | × 940 | 0,21 s |
| Dernier écho (environ 19 min avant) | 17 100 km | × 35 | × 11 000 | **0,060 s** |

Corrections qui en découlent :
- **06:00 : « × 60 » devient « × 75 »** (plan V1, et valeur retenue dans nos calculs précédents).
- **La taille × 4 devient × 4,5** à six heures. Le × 12 de 1 h 30 avant est juste (× 11,5).
- **Compteur du dernier écho : « 0,060 s » au lieu de « 0,066 s ».** La voix dit « 0,06 seconde » et « environ neuf
  mille kilomètres » : cela correspond à 0,060 s (8 990 km) et à « une vingtaine de minutes » (19 min). La Lune est
  alors à × 35, pas × 32.
- **Erreur non relevée par l'audit, dans le texte (02:00) :** « Quatre jours et vingt heures. C'est tout ce qu'il
  reste ». Or la chute commence à 5 h 24 et l'anomalie apparaît à 22 h 14 : **il ne reste alors qu'environ 4 j 3 h**.
  « 4 j 20 h » est la durée totale de la chute, pas le temps restant. **Décision : 4 j 20 h est
  présenté comme la durée totale de la chute.** Dans V13, « C'est tout ce qu'il reste avant que la Lune percute la
  Terre. » devient « C'est la durée totale de sa chute, jusqu'à l'impact. ». L'infographie de 02:00 montre une barre
  « Durée de la chute : 4 j 20 h », avec un repère « déjà écoulé : 17 h » au moment de l'anomalie. Le compteur à
  rebours qui suit part donc de 4 j 3 h.
- Notes scientifiques de production : la fragmentation est **une hypothèse de mise en scène**. Le texte le dit déjà
  (« Rien ne garantit qu'elle se brisera », « un monde rocheux, pas une boule de liquide »). La comète de 1994 illustre
  les forces de marée ; elle ne prouve rien pour la Lune. Les multiplicateurs mesurent une force, jamais une hauteur
  d'eau ou de sol.

### 7.1 bis Chronologie de référence (heure de France ; J0 = jour du début de la chute)
| Repère | Date et heure | Écoulé depuis le début | Reste avant contact | Texte V13 |
|---|---|---|---|---|
| **Début de la chute** | J0 05:24 | 0 | 4 j 19 h 36 | « Quatre jours et vingt heures… durée totale de sa chute » (02:00) |
| **Détection par Léa** | J0 22:14 | 16 h 50 | 4 j 2 h 46 | Ouverture du récit (01:00) |
| Plage | J2 05:24 | 48 h | 2 j 19 h 36 | « Quarante-huit heures après le début de la chute » (04:00) |
| Quatrième jour | J4 05:24 | 4 j | 19 h 36 | « Au quatrième jour » (05:00) |
| Six heures avant | J4 19:00 | 4 j 13 h 36 | 6 h | « environ quatre fois plus proche » (06:00) |
| Une heure et demie avant | J4 23:30 | 4 j 18 h 06 | 1 h 30 | « presque mille fois » (07:30) ; Lune de l'ouverture (00:00) |
| Dernier écho | J5 00:41 | 4 j 19 h 17 | 19 min | « une vingtaine de minutes » (09:48) |
| **Contact** | J5 01:00 | 4 j 19 h 36 | 0 | (11:00) |

Règles de montage : les cartes de temps disent toujours depuis quel repère on compte (« 48 h après le début de la
chute », jamais « 48 h plus tard »). Le compteur à l'écran affiche le temps **restant avant le contact**.

**Distance et taille apparente ne se confondent pas :**
- La voix dit « environ quatre fois plus proche » (06:00). C'est une **distance** : 384 400 km divisés par 91 000 km,
  soit 4,2.
- La **taille apparente** affichée se lit dans la fiche Lune : × 4,5 à ce moment-là.
- Aucun multiplicateur prononcé ne sert de réglage visuel.

À surveiller : l'ouverture (00:42) dit « revenir cinq jours en arrière ». Or la Lune de l'ouverture est celle d'une
heure et demie avant le contact, et le récit reprend à la détection : l'écart réel est de **4 jours et 1 heure**.
« Cinq jours » n'est juste que si l'on compte depuis le début de la chute. Il faut choisir : soit on garde la phrase,
et la carte « Cinq jours plus tôt » montre le matin du début de la chute ; soit la carte devient « Quatre jours plus
tôt ». La phrase de 09:27 (« Il y a cinq jours, le même trajet prenait environ deux secondes et demie ») reste
juste (4 j 19 h).

### 7.2 Timecodes : résultat du montage, pas contrainte
D'accord avec l'audit. Les débords par bloc (02:47 : + 9 s, 08:31 : + 10 s, etc., environ 33 s au total) tiennent dans
la marge globale d'environ 59 s. Méthode économe : la **voix définitive est générée bloc par bloc** et sert aussi de
voix témoin. Si un bloc change après l'animatique, on ne regénère que ce bloc (quelques centaines de crédits). Les
timecodes du découpage sont recalés sur l'animatique, puis gelés.

Blocs à laisser respirer dans l'animatique, **sans accélérer la voix** : 08:31 (Roche, comète de 1994, fractures)
passe à environ 40 s ; 02:47 à environ 22 s. La marge globale ne garantit pas à elle seule les débords locaux. On
protège donc d'abord les pauses, les SMS et les transitions, et ce sont les plans muets qui raccourcissent.
Correction de l'audit V13 à 08:31 : « En 1994, les fragments d'une comète déchirée par Jupiter se sont écrasés sur la
planète. » La comète s'est fragmentée en 1992, et ses fragments ont frappé Jupiter en juillet 1994.

### 7.3 Décision : les personnages parlent (option A, voix ElevenLabs)
Retenue le 5 novembre 2026 : **Léa, le collègue et la mère ont de vraies voix générées sur ElevenLabs.** Cela fait
environ 8 répliques adultes, pour quelques centaines de crédits ; les durées changent peu, car les répliques sont déjà
comptées. Avant de générer, on choisit 3 voix (une par rôle) et on fait un test de 2 répliques chacune. Les SMS de la
sœur restent écrits.

**Limite pour le garçon :** ElevenLabs refuse les voix d'enfant et les voix d'adulte qui imitent un enfant dans sa
Voice Library, au nom de sa politique d'usage. Il ne faut donc pas en fabriquer une pour ce rôle. Trois solutions, à
choisir par toi :
1. **Bulles pour le garçon seulement**, avec un silence et un gros plan sur la mère qui écoute. Coût nul, et c'est
   cohérent avec l'enfant qui ne comprend pas ce qui arrive. C'est ma recommandation.
2. **Enregistrer un vrai enfant**, avec l'accord écrit de ses parents, puis l'intégrer comme un son.
4. **Une voix d'enfant synthétique MiniMax.** Son catalogue a une catégorie « Child » (des voix de synthèse
   intégrées, pas des clones), et notre moteur sait déjà appeler MiniMax (`tts_minimax` dans `render.py`, testé avec
   `compare_voices.py`). À vérifier d'abord : qu'il existe une voix de garçon en français, et ce que permettent les
   conditions d'utilisation. Il faut aussi la clé `MINIMAX_API_KEY`, absente de cette session. On teste les 3
   répliques avec 2 ou 3 voix candidates, puis on compare avec les bulles dans le prototype de la voiture.
3. Réécrire ses 3 répliques pour les faire porter par la mère (« Il me demande pourquoi elle grossit… »). C'est
   déconseillé : on perd l'innocence de la question.

**Casting complet (5 novembre 2026)**

| Rôle | Fournisseur | Voix | Réglages |
|---|---|---|---|
| Narrateur | ElevenLabs | Nicolas – Narrator (`aQROLel5sQbj1vuIVi6B`) | `eleven_v4`, réglages connus de la vidéo Internet |
| Léa | ElevenLabs | Jeanne – Narrator (`txtf1EDouKke753vN8SL`) | `eleven_v4`, stabilité 0,5, similarité 0,75 ; filtre téléphone sur le message vocal |
| Collègue | ElevenLabs | Léo – Reassuring and Dynamic (`AfbuxQ9DVtS4azaxN1W7`) | `eleven_v4`, stabilité 0,5, similarité 0,75 |
| Mère | ElevenLabs | Caroline – Warm, Sweet and Soft (`kwhMCf63M8O3rCfnQ3oQ`) | `eleven_v4`, stabilité 0,5, similarité 0,75 |
| Garçon | MiniMax | `French_MovieLeadFemale` | `speech-2.8-hd`, hauteur +4, vitesse 0,95 |

Essais : `essais_voix_adultes/` et `essais_voix_garcon/`.

**Retenu le 5 novembre 2026 : solution 4, voix MiniMax `French_MovieLeadFemale`**, modèle `speech-2.8-hd`, hauteur
+4, vitesse 0,95, `language_boost` French (essai : `essais_voix_garcon/garcon_French_MovieLeadFemale_pitch+4.mp3`).
Ses 3 répliques gardent exactement ces réglages, pour que la voix reste la même. Les voix adultes restent sur
ElevenLabs ; on harmonise le volume et l'acoustique au mixage.

Le prototype de 05:25 (7.7) teste les voix adultes. Il faut lui ajouter le plan de la voiture (04:28) pour tester la
solution retenue pour le garçon.

**Convention unique, qui remplace les bulles du plan V1 :** toutes les répliques sont **prononcées**, sans animation
des lèvres (silhouettes, plans de dos, contrechamps). Les messages de la sœur sont **lus par le spectateur** : texte à
l'écran et son de notification, sans voix.

| Bloc | Réplique | Rendu |
|---|---|---|
| 03:47 | « Mais elle est comme d'habitude. » | Voix du garçon (MiniMax) |
| 04:28 | « Maman… pourquoi elle grossit ? » | Voix du garçon |
| 05:25 | « On doit partir. » / « Tu ne peux plus rien changer. » | Voix du collègue (Léo) |
| 05:25 | « Je sais. Mais on peut encore comprendre ce qui nous arrive. » | Voix de Léa (Jeanne) |
| 05:25 | « On est sur la route. Tu nous rejoins ? » | SMS à l'écran |
| 09:00 | « On est arrêtés. Je ne sais pas où aller. » | SMS à l'écran |
| 09:00 | « Je suis désolée. Je t'aime. » | Voix de Léa, filtre téléphone |
| 10:47 | « Est-ce qu'on est assez loin ? » | Voix du garçon |
| 10:47 | « Je suis là. » | Voix de la mère (Caroline) |

### 7.4 SMS et « Écouté » : la place à l'écran
- **05:25** (11 s de voix pour 22 s) : collègue « On doit partir. » → téléphone qui s'allume (notification) → SMS en
  gros plan (au moins 3 s de lecture) → Léa écrit (saisie) → elle efface (silence) → « Tu ne peux plus rien changer. »
- **09:00** (12 s de voix pour 27 s) : la scène se joue par l'image, pas par l'interface.

| Action | Son |
|---|---|
| Le dernier SMS arrive (au moins 3 s de lecture) | Notification |
| Léa lit | Ambiance de l'observatoire, alarme lointaine |
| Elle lance l'enregistrement | Bip discret |
| « Je suis désolée. Je t'aime. » | Voix de Léa seule, **sans musique** |
| Elle envoie | Son d'envoi discret |
| « Écouté » apparaît | **Silence, au moins 2 s** |
| « Elle retourne vers le laser. » (09:27) | L'ambiance revient peu à peu |


### 7.5 Continuité de la mère et du garçon
Le plateau Littoral garde un décor technique unique. Mais il a **4 zones distinctes** : plage, autoroute, zone
inondée, colline. Chacune a son repère visuel (phare, pont, pylônes, arbre isolé), sa lumière et son angle. Une carte
du parcours, pour l'équipe seulement, fixe l'ordre et les distances. **Le garçon garde le seau à la main** en quittant
la voiture et pendant la course.

### 7.6 Le final, synchronisé à partir de la fin de la collision (T)
| T | Image | Voix | Son |
|---|---|---|---|
| 0 | Collision, lumière blanche | « C'est la fin de notre monde. » | Apogée |
| + 1 s | Noir ; l'étiquette « Simulation » disparaît | — | Coupure totale |
| + 1 à + 5 s | Noir | — | Silence absolu |
| + 5 s | Calern en plein jour, Léa au travail (coupe franche, sans fondu) | — | Clavier, ventilation |
| + 9 s | Le collègue passe et sourit | — | Ambiance |
| + 12 s | Plage ensoleillée | — | Ressac |
| + 15 s | Le garçon court vers l'eau avec son seau | — | Vagues, pas |
| + 18 s | La mère le rejoint | « Heureusement… » | Ambiance |
| + 20 s | Plan large de la plage | « … tout cela n'était qu'une simulation. » | Musique douce |

Au retour à Calern et sur la plage, il n'y a **aucune musique**, seulement les bruits ordinaires du lieu. La musique
douce ne commence qu'après « … simulation. ». Pour que le noir suivi du plein jour ne ressemble pas à une erreur de montage, le premier plan de jour est très
lumineux et sonore dès sa première image.

### 7.7 Prototype avant fabrication (30 à 45 s)
Il se place à l'étape 2 de l'ordre de fabrication, avant les décors 3 à 5. Il comprend deux passages :
1. **Le dialogue de 05:25**, avec Léa, le collègue et le SMS. Il teste les silhouettes avec des voix réelles
   (option A) ou des bulles (option B). Il n'utilise que les décors 1 et 2, déjà prévus en premier.
2. **Collision puis retour à la réalité.** La collision est provisoire (`globe` + flash blanc) : on teste le
   contraste du son et du montage, pas les effets visuels. La plage de jour est provisoire elle aussi (`street` de
   jour, ou une image fixe).

Coût : environ une journée, sans construire les décors lourds. C'est ce prototype qui tranche 7.3.
