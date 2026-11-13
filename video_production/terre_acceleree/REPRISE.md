# Reprise : « Et si la Terre tournait de plus en plus vite… et ne pouvait plus s'arrêter ? »

Film sans voix off, à la manière de What If Sim (« What If Earth Spun Faster and Couldn't Stop? », 1,79 M vues) :
3D en code, un compteur à l'écran, des sous-titres courts, et le son qui raconte. En français, pour la chaîne WhatIfcast.

## État

| Étape | État |
|---|---|
| Prototype de Nice (20 s) | **Validé par l'utilisateur.** `proto/` (scène Three.js, rendu image par image, son) |
| Texte du film (sous-titres, compteur, chiffres par lieu) | À écrire, puis à faire valider |
| Lieux suivants | À faire, lieu par lieu, avec 3 images d'exemple avant chaque rendu |

## Décisions validées

- **Image** : 3D Three.js rendue dans Chromium (0 crédit), environ 1 s par image en 1080p.
- **Compteur** en haut à gauche (« UNE JOURNÉE DURE », gros chiffre en Source Serif 4, 3 lignes en Inter, la dernière en orange).
  Il doit être **posé sur le ciel** : horizon vers 38 % de la hauteur. Voile léger bleuté **ancré dans le coin**, limité au bloc de texte
  (ne pas assombrir tout le ciel). La ligne orange doit rester lisible (mesure : fond environ 115, lettres environ 184).
- **Sous-titres** en bas, en italique, avec un **ovale sombre** qui épouse la phrase.
- **Repère de la scène** : nord = +z, **ouest = +x** (face à la mer vers le sud, l'ouest est à droite). Une erreur de miroir avait mis le
  coucher de soleil derrière le compteur.
- **Physique juste** : à Nice (43,7° N), la mer **baisse** quand la Terre accélère (Δh = (R²/2g)(ω² − ω0²)(cos²φ − 2/3)) ;
  à l'équateur (Kourou) elle monte. Les commentaires des concurrents relèvent les erreurs de sens : c'est notre point fort.
- **Compteur du film long** : de 24 h 00 à 1 h 24 (apesanteur à l'équateur) sur environ 8 min, lent au début, plus rapide ensuite, toujours lisible.

## Son (poste à part entière, `proto/son/`)

- L'utilisateur veut un **vrai travail d'ingénieur du son** : ne pas économiser ElevenLabs sur le son (annoncer quand même le coût).
- `conception.md` : intention, arc émotionnel, feuille de calage. `bibliotheque.py` : sons ElevenLabs. `mix.py` : mixage
  (distance, réverbération, panoramique, respirations, coupure nette finale), −14 LUFS, crête −1,5 dBTP.
- Les sons sont **calés sur les événements de la scène** (`window.etat(t)` dans `scene.js` → `etat.json`).
- **Pulsation** : un tic régulier comme un battement de cœur (72 bpm), **indépendant du compteur**. Option proposée pour le film :
  monter très lentement de 60 à 90 bpm sur 8 min.
- Le prototype a coûté environ 1 290 crédits ElevenLabs (21 sons). Je ne peux pas écouter : l'utilisateur valide à l'oreille.

## Plan du film proposé (à valider avec le texte)

0. Ouverture flash-forward : la Terre avec son anneau, « Dans 8 minutes, voici la Terre. »
1. Nice : la mer se retire. 2. Kourou (équateur) : la mer monte, on s'allège. 3. Paris : jours et nuits qui défilent, le sol penche.
4. La Terre vue de l'espace s'aplatit. 5. Retour Kourou / Nice : apesanteur à 1 h 24. 6. Final : l'anneau, puis « Est-ce que c'est réel ? ».
