# Prototype « Et si la Terre tournait de plus en plus vite ? » (20 s, Nice)

Scène 3D en Three.js rendue image par image dans Chromium (sans crédit Kie ni ElevenLabs), compteur et
sous-titres à l'écran à la place d'une voix off, son monté avec des bruitages déjà générés.

```sh
npm install                 # three, polices Source Serif 4 et Inter
node render.cjs 0 20 0.0333333333 frames     # 600 images (≈ 3 s/image en logiciel)
node render.cjs 0 20 5 /tmp/apercu           # images clés pour vérifier
python3 son.py              # son.wav (−14 LUFS)
./monter.sh                 # prototype.mp4
```

Physique : la surface des océans suit le potentiel centrifuge. Δh = (R²/2g)(ω² − ω0²)(cos²φ − 2/3), avec
R²ω0²/2g ≈ 11 km. À Nice (43,7° N), cos²φ − 2/3 = −0,144 : quand la Terre accélère, la mer baisse
(≈ 390 m pour une journée de 21 h 30). Modèle simplifié : pas d'auto-gravitation de l'eau ni de déformation de la croûte.
La baisse visible à l'écran est compressée (36 m à la fin) ; le chiffre affiché est le vrai.
