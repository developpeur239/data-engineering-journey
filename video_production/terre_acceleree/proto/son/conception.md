# Son du prototype de Nice : fiche d'ingénieur du son

Pas de voix off : **le son raconte**. Le spectateur doit *entendre* que quelque chose cloche avant de le lire.

## Intention en trois temps

| Temps | Émotion | Ce qu'on entend |
|---|---|---|
| 0 – 6 s · la vie normale | familiarité, chaleur | ressac sur les **galets** (le son de Nice), foule détendue, circulation derrière, mouettes, vent dans les palmes |
| 6 – 14,6 s · le basculement | malaise, puis inquiétude | un grondement à peine audible, puis la mer qui **aspire** au lieu de revenir ; les vagues s'éloignent (plus faibles, plus sourdes) ; les **oiseaux partent avant les humains** ; la foule **se tait**, puis s'étonne ; les bateaux s'échouent un par un |
| 14,6 – 20 s · la menace | angoisse | une **respiration** (tout baisse 0,4 s) pour le sous-titre « À Nice, la mer se retire. », puis le grondement et le vent montent, un chien, une alarme au loin ; **coupure nette** sur un coup grave : on veut la suite |

## Règles de mixage

- **Distance réelle** : quand l'eau recule de 50 à 370 m, ses sons perdent du volume, des aigus (filtre passe-bas qui descend) et gagnent de la réverbération.
- **Espace** : la circulation est derrière nous (filtrée, discrète) ; les bateaux et les animaux sont placés à gauche ou à droite selon l'image.
- **Calage sur l'image** (`etat.json`, tiré de la scène) : chaque bateau qui s'échoue a son bruit, à l'instant où il touche le fond (12,6 · 13,0 · 13,8 · 14,2 · 15,9 · 17,1 · 17,6 · 19,4 s). Les baigneurs descendent sur les galets à 12,8 s.
- **Le silence comme effet** : la foule qui se tait à 10,6 s inquiète plus qu'un cri.
- **Contraste** : début calme (environ −18 LUFS à court terme), fin dense (environ −11), moyenne −14 LUFS, crête −1,5 dBTP.
- Aucune musique : toute l'émotion vient de sons du monde réel.

## Bibliothèque (ElevenLabs, `bibliotheque.py`)

20 sons, environ 3 minutes au total, stéréo 48 kHz. Chacun est ramené à −23 LUFS avant le mixage, puis dosé en dB dans `mix.py`.
Coût mesuré : environ 1 290 crédits ElevenLabs (compteur de 14 982 à 16 272).

## Limite

Je ne peux pas écouter : je contrôle par mesures (volume, crête, spectre) et par le calage sur l'image.
**L'écoute finale est la tienne**, au casque et sur téléphone.
