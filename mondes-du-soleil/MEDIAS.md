# Médias réalistes du hero · mode d'emploi

La page est prête : il suffit de générer les médias ci-dessous, de les déposer dans `medias-source/`, puis de lancer un script.
Tant que rien n'est fourni, la scène 3D et un **bonhomme provisoire** (cadre en pointillés) s'affichent.

| Étape | Outil conseillé | Fichier à déposer dans `medias-source/` |
|---|---|---|
| 1. Vidéo de la maison (3 clips enchaînés) | Flow (Veo), 16:9 | `maison-1.mp4`, `maison-2.mp4`, `maison-3.mp4` |
| 1 bis. Même vidéo en vertical (facultatif, mieux sur mobile) | Flow (Veo), 9:16 | `maison-vertical-1.mp4`… |
| 2. Portrait de référence du bonhomme | Flow / Gemini (génération d'image) | aucun (sert aux étapes 3 et 4) |
| 3. Le bonhomme arrive et salue | Flow, « Frames to video » | `bonhomme-salut.mp4` |
| 4. Grille du regard | Gemini / Flow (retouche d'image) | `regard/l1-c1.png` … `regard/l3-c3.png` |

> **À valider par le client** : le bonhomme est une personne générée par IA, pas un salarié. Ne lui donnez ni nom ni fonction sur le site.

---

## 1. Vidéo de la maison

Réglages : **Veo, qualité maximale, 16:9, 8 s par clip, sans son**. Générez le clip 1, puis **Extend** (prolonger) pour les clips 2 et 3 afin de garder la même maison et le même mouvement de caméra. Téléchargez chaque clip en MP4 1080p.

Astuce : ajoutez une vraie photo de chantier (par ex. `assets/photos/IMG_4736.jpeg`) comme image de référence (« Ingredients ») pour coller à l'architecture girondine.

**Clip 1 · la nuit, toit nu**
```
Photorealistic cinematic shot of a single-story house in Gironde, southwest France: cream lime-render walls, terracotta Roman tile roof, wooden shutters, small garden with lavender and an olive tree. Blue hour just before dawn, deep navy sky with a few fading stars, soft cool light, no people. The camera slowly orbits from the front-left of the house toward the front, at roof height, smooth gimbal movement. Full-frame cinema camera, 35mm lens, natural colors, high detail, no text, no logos.
```

**Clip 2 · la pose des panneaux (Extend)**
```
Continue the same slow orbit around the same house. Sleek all-black monocrystalline solar panels appear on the roof one after another in a neat grid of two rows of five, each one settling gently into place, realistic black frames and mounting rails. The sky slowly brightens from navy to deep blue. Photorealistic, no people, no text.
```

**Clip 3 · le lever du soleil (Extend)**
```
Continue the same slow orbit, ending in front of the house. The sun rises above the trees on the horizon, warm golden light washes over the facade, the black solar panels catch a bright golden reflection, and warm lights turn on inside the windows. Golden hour, photorealistic, subtle lens flare, no people, no text.
```

Pour la version verticale, reprenez les mêmes prompts en **9:16** et nommez les fichiers `maison-vertical-1.mp4`, etc.

---

## 2. Portrait de référence du bonhomme

Générez une image **9:16** :
```
Photorealistic waist-up portrait of a friendly French solar panel installer in his thirties, warm genuine smile, short dark hair, light stubble, wearing a charcoal grey t-shirt with a small embroidered orange logo on the chest that reads "Mondes du Soleil", standing straight, facing the camera, arms relaxed. Plain flat chroma-key green background (#00B140), evenly lit soft studio lighting, no shadow on the background, sharp focus, natural skin texture.
```
Vérifiez l'orthographe de la broderie « Mondes du Soleil » (les IA déforment souvent le texte) : régénérez jusqu'à ce qu'elle soit exacte.
**Gardez cette image** : c'est la dernière image du salut (étape 3) et le centre de la grille du regard (étape 4).

---

## 3. Le bonhomme arrive et salue

Dans Flow, **Frames to video**, 9:16, 4 à 6 s. Image de **fin** = le portrait de l'étape 2.
```
He walks into frame from the right, stops in the center, smiles and waves hello with his right hand, then lowers his hand and looks straight at the camera, smiling. Static locked-off camera, plain flat chroma-key green background, even lighting, photorealistic.
```
Enregistrez sous `medias-source/bonhomme-salut.mp4`.

---

## 4. Grille du regard (le regard suit le curseur)

Avec Gemini (ou la retouche d'image de Flow), en partant du portrait de l'étape 2, générez **8 variantes** avec ce prompt, en changeant la direction :
```
Same man, same framing, same size, same lighting, same green background, same smile. Only his head and eyes turn slightly to look toward the [DIRECTION] of the frame. Natural, subtle movement.
```

| Fichier | Direction à écrire | | Fichier | Direction | | Fichier | Direction |
|---|---|---|---|---|---|---|---|
| `l1-c1.png` | top left | | `l1-c2.png` | top | | `l1-c3.png` | top right |
| `l2-c1.png` | left | | `l2-c2.png` | **le portrait d'origine** | | `l2-c3.png` | right |
| `l3-c1.png` | bottom left | | `l3-c2.png` | bottom | | `l3-c3.png` | bottom right |

Le cadrage doit rester **identique** d'une image à l'autre (sinon le bonhomme « saute »). Pour un regard plus fluide, une grille 5×5 est possible (outils type LivePortrait / Expression Editor), puis `--grille 5x5`.

---

## 5. Préparer et voir le résultat

Une seule fois : installer **ffmpeg** (`winget install ffmpeg` sous Windows) et **Pillow** (`pip install pillow`).

Depuis le dossier `mondes-du-soleil` :
```
python outils/preparer-medias.py --grille 3x3
python outils/apercu-autonome.py
```
Le premier script découpe la vidéo en images WebP, détoure le bonhomme (fond vert → transparent) et écrit `assets/medias.js`. Le second régénère `apercu-autonome.html`.

Réglages utiles : `--images-sequence 150` (vidéo plus fluide, plus lourde), `--apparition 0.8` (moment d'arrivée du bonhomme, de 0 à 1), `--similarite 0.2` (si un liseré vert reste autour du bonhomme).

**Poids** : 120 images de maison ≈ 6 à 8 Mo pour ordinateur, environ moitié moins pour mobile ; elles se chargent progressivement pendant le défilement.
