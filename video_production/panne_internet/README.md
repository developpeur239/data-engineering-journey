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
4. **Sorties** : `video.mp4` (1920x1080, 24 i/s), `sous-titres.srt`, `chapitres.txt` (pour la description).

## Limites de cette version
- La voix est une **synthèse vocale** : à remplacer idéalement par ta propre voix (même découpage par scène).
- Les « scènes 3D » du script sont rendues en **illustrations 2D stylisées**, pas en 3D.
- La miniature n'est pas générée (image photoréaliste : à déclarer « AI use : Yes » si elle est générée par IA).
