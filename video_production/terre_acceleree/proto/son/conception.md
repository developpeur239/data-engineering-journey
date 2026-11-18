# Son du prototype de Nice : fiche d'ingénieur du son

Pas de voix off : **le son raconte**. Le spectateur doit *entendre* que quelque chose cloche avant de le lire.

## Règle de l'utilisateur (validée)

Trop de sons perdent le spectateur. **On n'entend que ce qu'on voit.**

- **Continu** = ce que l'image montre en permanence : **l'eau** (ressac sur les galets → la mer qui aspire en reculant → l'eau qui
  s'égoutte du fond découvert) et le **tic-tac du compteur**, dont le tempo suit la vitesse du compteur
  (60 + 25·log2(1 + minutes affichées par seconde) : 62 bpm au début, 172 à la fin du prototype ; dans le film long, le compteur
  défile moins vite, donc l'accélération est plus douce).
- **Ponctuel** = seulement au moment où on le voit : une voiture qui passe à l'écran (calculé : visible de 3,9 à 4,7 s), les gens
  qui réagissent (11 s) puis descendent sur les galets (12,7 s), chaque bateau qui touche le fond (8 instants tirés de la scène).
- Retirés : mouettes, chien, alarme, vent, grondement, poissons, foule et circulation en continu (on ne les voit pas).

## Mixage

- Distance réelle : l'eau qui recule perd du volume, des aigus et gagne de la réverbération ; les bateaux, de plus en plus loin.
- Tic-tac à gauche (côté compteur), alterné tic (aigu) / tac (plus grave).
- Respiration (−4 dB sur l'eau) sous le sous-titre « À Nice, la mer se retire. ».
- −14 LUFS, crête −1,5 dBTP.

## Bibliothèque (ElevenLabs, `bibliotheque.py`)

20 sons, environ 3 minutes au total, stéréo 48 kHz. Chacun est ramené à −23 LUFS avant le mixage, puis dosé en dB dans `mix.py`.
Coût mesuré : environ 1 290 crédits ElevenLabs (compteur de 14 982 à 16 272).

## Limite

Je ne peux pas écouter : je contrôle par mesures (volume, crête, spectre) et par le calage sur l'image.
**L'écoute finale est la tienne**, au casque et sur téléphone.
