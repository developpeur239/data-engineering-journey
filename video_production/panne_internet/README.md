# Production : « La panne mondiale d'Internet : les 72 premières heures »

Vidéo générée entièrement en code, à partir du script validé (sources : `video_analysis/sources_panne_internet.md`).

- `scenes.py` : le script final, scène par scène (voix, étiquette, texte à l'écran, type de visuel).
  Seules deux corrections ont été appliquées au script validé : « quatre-vingt-dix départements »
  et la précision sur les 11 800 appels d'urgence (11 % des appels).
- `render.py` : le moteur de rendu.

## Fabrication

```bash
pip install piper-tts pillow numpy
# voix française Piper (fr_FR-siwis-medium) : https://huggingface.co/rhasspy/piper-voices
# contours des pays : ne_110m_admin_0_countries.geojson (Natural Earth, domaine public)
python render.py --work build --geo countries.geojson --voice fr_FR-siwis-medium.onnx
python render.py ... --only 1-5 --preview   # aperçu rapide en 960x540
```

1. **Voix** : synthèse locale Piper, une piste par scène (mise en cache), légèrement ralentie (~150 mots/min).
2. **Images** : motion design dessiné image par image (Pillow) — étiquettes SIMULATION / HISTOIRE RÉELLE,
   gros chiffres animés, chrono, globe en projection orthographique, cartes (Natural Earth), cercles de distance,
   cartes de choix, interfaces (terminal, distributeur, téléphone, ordinateur, tableau des départs, radio…).
3. **Son** : voix + nappe d'ambiance générée par le programme (aucune musique sous droits), compression légère,
   normalisation à −15 LUFS.
4. **Globe réaliste** (option `--textures <dossier>`) : textures Terre de jour, lumières de nuit et nuages
   (images NASA, domaine public, copies du dépôt three.js : `examples/textures/planets/earth_atmos_2048.jpg`,
   `earth_lights_2048.png`, `earth_clouds_1024.png`), éclairage, halo d'atmosphère, lumières qui s'éteignent pendant la panne.
   Panneaux de données (`hud`), coordonnées (`coords`) et mention « ILLUSTRATION » sous les scènes dessinées.
5. **Caméra et son** (`fx.py`) : règles de caméra inspirées des mesures du dépôt MIT
   [mromidev/claude-animated-shorts](https://github.com/mromidev/claude-animated-shorts) — glissé d'entrée lissé (24 images),
   poussée lente continue (aucun plan figé), secousse sur 7 images et petite rotation sur les mots-clés (`IMPACTS`).
   Bande-son synthétisée : souffles de transition, impacts, bips d'erreur, tic-tac des chiffres, montée avant le
   retournement, battement de cœur pendant l'escalade, nappe musicale dont l'intensité suit le script, baissée
   automatiquement sous la voix ; mixage final à −14 LUFS.
6. **Sorties** : `video.mp4` (1920x1080, 24 i/s), `sous-titres.srt`, `chapitres.txt` (pour la description).

## Voix MiniMax (option)

```bash
export MINIMAX_API_KEY="..."        # clé de ton compte MiniMax (platform.minimax.io → API Keys)
python render.py --work build --geo countries.geojson --tts minimax --minimax-voice French_MaleNarrator
```

- Modèle par défaut : `speech-2.8-hd`, avec `language_boost` réglé sur le français.
- Voix françaises disponibles : `French_MaleNarrator` (narrateur, par défaut), `French_Male_Speech_New` (homme posé),
  `French_CasualMan`, `French_FemaleAnchor`, `French_Female_News Anchor`, `French_MovieLeadFemale`.
- Options : `--minimax-speed 0.95` (débit), `--minimax-emotion calm` (facultatif).
- Pas de réécriture phonétique : MiniMax est multilingue. La table `PRONUNCIATION` ne sert qu'à Piper.
- Service payant, facturé au nombre de caractères (le script fait environ 9 000 caractères).

## Limites de cette version
- La voix est une **synthèse vocale** (les noms anglais sont réécrits phonétiquement pour la voix seulement, table `PRONUNCIATION` de render.py) : à remplacer idéalement par ta propre voix (même découpage par scène).
- Les « scènes 3D » du script sont rendues en **illustrations 2D stylisées**, pas en 3D.
- La miniature n'est pas générée (image photoréaliste : à déclarer « AI use : Yes » si elle est générée par IA).

## Scènes 3D (three.js)

`3d/ville.html` : ville de nuit procédurale (fenêtres qui s'éteignent, lampadaires allumés, écrans en erreur).
`3d/render3d.js` la filme image par image (navigateur sans écran, WebGL logiciel) :

```bash
NODE_PATH=$(npm root -g) node 3d/render3d.js 3d/ville.html ville.mp4 8 1280 24
```
