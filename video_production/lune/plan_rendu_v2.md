# Plan de rendu v2 : « Le Dernier Écho » (dossier V12)

But de la v2 : **plus de qualité à l'écran, moins de fabrication et moins d'aller-retours**. Elle remplace la v1
sur quatre points : texte verrouillé avant toute génération, décors fusionnés, animatique avant tout rendu animé,
schémas faits en 2D. Le découpage scène par scène et les choix de style de la v1 restent valables sauf mention.

## 0. Ce que la v2 change

| | v1 | v2 | Gain |
|---|---|---|---|
| Décors ou effets à créer | 10 (dont 2 G) | **5 (dont 1 G)** | environ 40 % de fabrication en moins |
| Durée de voix | environ 14 min 30, non tranché | **12 min, mesurée avant génération** | une seule génération ElevenLabs (environ 11 000 crédits au lieu de 13 000, sans regénération) |
| Validation | sur vidéo rendue | **sur animatique** (une image par plan + voix) | les erreurs de cadre et de rythme coûtent une image, pas un rendu |
| Schémas (orbite, laser, marées, carte, compteurs) | studio 3D | **2D Tesseract** (rendu en secondes) | 10 blocs sortis du rendu 3D image par image |
| Angles de caméra | libres par plan | **3 angles fixes par décor**, réutilisés | réglage fait une fois ; le cache resservira |

## 1. Règles de production

1. **Verrouiller avant de générer.** Aucune voix finale tant que le texte n'est pas à environ 1 800 mots (section 2).
   Le débit réel de Nicolas se mesure sur **un seul bloc** (environ 70 mots, environ 400 crédits) avant de couper.
   La v1 supposait 150 mots/min sans l'avoir mesuré.
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
   schémas se font dans Tesseract (projet modifiable, export MP4 en quelques secondes), aux couleurs de la chaîne et en
   Bricolage. À vérifier d'abord : insérer un MP4 dans `render.py` (P).

## 2. Coupes pour tenir 12:40 (environ 380 mots)

Calcul à 150 mots/min, à corriger avec le débit mesuré. Les blocs suivants débordent de leur créneau. On coupe
d'abord là où l'émotion a besoin d'air :

| Bloc | Mots | Débord | Priorité |
|---|---|---|---|
| 10:47–11:00 (mère et garçon sur la hauteur) | 95 | +25 s | **1** : moment-clé, il faut de la place pour « Je suis là » et la pause |
| 03:47–04:00 (seau, première réplique) | 71 | +15 s | 1 |
| 04:28–05:00 (voiture, « pourquoi elle grossit ? ») | 118 | +15 s | 1 |
| 05:25–05:47 (collègue, Léa reste) | 93 | +15 s | 1 |
| 11:26–11:50 (planète incandescente) | 94 | +14 s | 2 : l'image suffit |
| 06:30–07:00 (sirènes, course) | 107 | +13 s | 2 |
| 08:31–09:00 (limite de Roche, 1994) | 101 | +11 s | 2 |
| 09:27–09:48 (dernier tir laser) | 80 | +11 s | 2 |
| 00:42–01:00, 02:47–03:00, 09:48–10:00 | 71, 57, 54 | +10 s chacun | 3 |
| 05:00–05:25, 09:00–09:27 | 84, 85 | +9 s, +7 s | 3 |

Les blocs 00:00–00:42, 07:00–07:30 et le final ont de la marge : on les garde, la marge sert aux silences. Les coupes
sont à valider par l'auteur : je propose des versions courtes, je ne réécris rien sans accord.

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

1. Mesurer le débit sur un bloc, valider les coupes, puis générer la voix finale (une fois) et les 2 répliques
   féminines (test, puis génération).
2. Construire les décors 1 et 2, sortir les images fixes des blocs Calern, puis l'animatique partielle.
3. Construire les décors 3 et 4, puis l'animatique complète. **Point de validation avec toi.**
4. Faire les schémas 2D (Tesseract).
5. Construire le décor 5 (collision).
6. Animer et rendre en 720p, bloc par bloc ; le son (`fx.py`, `sfx_real.py`) suit au fil des blocs.
7. Rendre en 1080p une seule fois, faire le contrôle final, puis la miniature.

## 6. Points ouverts

1. **Coupes** : valider la liste de la section 2 (environ 380 mots).
2. **Point d'impact** (déclinaison de la Lune) : à fixer avant le décor 5.
3. **Archives de 1994** : les images NASA sont en général libres. Celles d'ESA/Hubble sont sous CC BY 4.0, donc
   crédit obligatoire. À vérifier image par image.
4. **Voix de Léa et de la mère** : choisir deux voix féminines (test de 2 répliques).
5. **Style des personnages** : tu m'avais dit de ne pas copier les silhouettes noires de Last Soul. Ce plan les garde
   parce que l'essai `perso_marc.html` a été validé. À confirmer.
