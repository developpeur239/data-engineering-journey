# Le Dernier Écho : méthode de production des 12 blocs

But : produire chaque bloc d'une minute avec le même niveau de qualité, sans multiplier les coûts ni les rendus.
Un bloc réussi sert de modèle aux onze autres : mêmes outils, mêmes règles, mêmes contrôles.

## Chaîne de fabrication (par bloc `bXX/`)
1. **Voix** : `bXX/voix.json` (texte exact du V13, une entrée par passage) → `vN.wav` (ElevenLabs, Nicolas, eleven_v4,
   stabilité 0,7, similarité 0,5). On génère une seule fois, après validation du texte.
2. **Minutage** : `python3 -m moteur.mots bXX` → `bXX/mots.json`. Whisper donne les temps, mais on garde toujours les
   mots du script (alignement lettre par lettre, robuste aux élisions). **Contrôle obligatoire** : le rapport signale
   les mots non reconnus, les mots tombant dans un silence, les fins de phrase sans pause et chaque nombre (à vérifier
   à l'oreille). Rien ne part en rendu tant que le rapport n'est pas propre ou vérifié.
3. **Plans** : `bXX/shots.json`. Chaque plan : `id`, `debut` (ancre), `set` (décor), `texte` (passage de voix),
   `intention` (ce que le plan doit faire ressentir), `camera` (images clés), `reglages` (paramètres du décor),
   `filtres`, `secousses`, `calques`. Le son du bloc est dans `son` et `silences`, les textes à l'écran dans `textes`.
   Les temps sont des **ancres sur les mots** (`"v2:cratères"`, `"v3:percuter-2.0"`, `"#D"`, `"v4.end+0.4"`) :
   si une voix est regénérée, tout se recale tout seul.
4. **Contrôle visuel** : `python3 -m moteur.core bXX --planche` (une image par plan) et `--images 120,400` (instants
   précis) avant tout rendu complet. Rendu complet : `python3 -m moteur.core bXX` (4 cœurs, ≈ 7 min par minute de film).
5. **Son** : le moteur place voix, bruitages et ambiances, baisse le fond sous la voix, applique les silences protégés,
   puis normalise. Référence de travail : **−14 LUFS intégrés, crête réelle ≤ −1,5 dBTP** (`style.json`). Ce n'est
   pas une règle YouTube : le rapport affiche aussi l'écart voix / fond pendant la parole, à vérifier à l'écoute.

## Architecture hybride : qui fait quoi
| Élément | Moyen | Règle |
|---|---|---|
| Dessins fixes riches (décors, poses de personnages, plans spectaculaires de la Lune) | Images générées (Kie, ≈ 12 crédits) | Seulement ce qui ne bouge pas et n'interagit pas. Pas d'objet qu'un personnage touche dans le décor (chaise, porte, téléphone) : ces objets sont des calques séparés. |
| Tout mouvement : caméra, respiration, marche articulée, bouches, rideaux, nuages, foule, écrans, fenêtres | Code (`decors/*.py`, `moteur/`) | Gratuit, modifiable, identique d'un bloc à l'autre. |
| Schémas, chiffres, cartes, compteurs (laser, orbite, marées, « 2,5 s », « 4 j 20 h ») | Code (moteur ou Tesseract) | Toujours synchronisés sur le mot prononcé. |
| Volumes 3D simples (Terre et Lune en sphères, mouvements de caméra dans un décor simple) | Rendu 3D ou code, importé comme calque `sequence` | Uniquement si le rendu tient le budget de temps. Pas de personnages en 3D : mesuré ici à 10 s par image en Cycles, et les mains 3D n'ont pas convaincu. |

**L'étalonnage commun** (`style.json`, appliqué à chaque image) harmonise les couleurs, la vignette et le grain. Il ne
répare pas une perspective fausse, une chaise en double ni des proportions différentes : ces problèmes se règlent à
la source (image, placement, échelle).

## Règles de mise en scène
- L'intention narrative décide du découpage : une révélation peut tenir 6 s, une suite de réactions se découpe court.
  Repère : 10 à 15 plans par minute, sans obligation.
- Chaque plan bouge (poussée lente, panoramique, respiration de caméra) et a de l'atmosphère (poussière, brume, nuages).
- La narration est illustrée phrase par phrase : la coupe ou l'événement tombe sur le mot (ancre), pas « à peu près ».
- Personne ne parle bouche figée : synchro labiale sur la voix réelle (feuille d'exposition) dès qu'une bouche est
  visible. Le narrateur n'est jamais synchronisé.
- « Simulation hypothétique » visible jusqu'au noir de la collision ; jamais au retour à la réalité.

## Décors réutilisables
- `decors/nuit_ville.py` : `Chambre`, `Fenetre`, `Rue` (bloc 1 ; la rue et la fenêtre resserviront pour la ville).
- À venir : Calern nuit/jour (intérieur, console, laser, extérieur), littoral à niveau d'eau réglable, module Lune
  (taille, fissures, fragmentation), collision vue de l'espace.

## Coûts du bloc 1 (référence)
5 images (≈ 60 crédits Kie), 704 caractères de voix, 3 bruitages ElevenLabs (17 s). Tout le reste : code.
