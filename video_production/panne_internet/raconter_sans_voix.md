# Raconter sans la voix : ce qui a été branché dans le rendu (4 novembre 2026)

Origine : analyse de « 1 MINUTE » et « 1 HOUR » de Last Soul (`video_analysis/lastsoul_recette.md`) et règles du
guide de montage (`video_production/montage_guide.md`, sections 9 et 10). On reprend sa logique, pas son style.

Les deux moteurs ont été modifiés : le moteur 3D (studio three.js, celui de la vraie vidéo) et le moteur 2D
(plus rapide, pour les tests). Tous les réglages sont dans `edit_plan.py`.

## 1. Texte à l'écran épuré
- Les textes d'habillage de `scenes.py`, écrits en capitales, s'affichent en **casse normale**
  (« Panne DNS · 72 heures », « Machines Windows », « Marc — inventé »). Sigles et noms propres gardés
  (`typo.sentence_case`). **`scenes.py` n'est pas modifié** : seul l'affichage change.
- Cartes titre et phrases clés en **EB Garamond** italique (« *Et si Internet s'arrêtait 72 heures ?* »).
- Étiquette « Simulation / Histoire réelle » plus petite et plus discrète.
- Le texte des objets (écran du terminal, du téléphone, tableau des départs) reste comme sur un vrai appareil.

## 2. Pensées de Marc (`THOUGHTS`, moteur 3D)
Police arrondie (Comic Neue), 2 à 4 mots, halo sombre, sans cadre, à la fin d'une phrase de la voix (environ 3 s).

| Scène | Pensée | Vérifiée à l'image ? |
|---|---|---|
| 2 | « Allez… passe. » | non |
| 22 | « Pas maintenant… » | non |
| 26 | « Décroche… » | oui (placée à côté du téléphone) |
| 32 | « S'il vous plaît. » | non |
| 41 | « Ça suffira ? » (pensée intérieure, ocre) | non |

**À valider par l'utilisateur** : ces textes ont été ajoutés, ils ne viennent pas du script. Les garder, les
modifier ou les supprimer dans `edit_plan.THOUGHTS`. Les scènes 2, 22, 32 et 41 contiennent Marc en 3D : vérifier
avec `--stills` que la pensée ne cache pas un visage, et régler sa position `(x, y)` si besoin.

## 3. Boucle accélérée (`LOOPS`)
- Après la scène 26 : 8 plans de refus déjà vus (ordinateur, automate, terminal, distributeurs, téléphone),
  de plus en plus courts (1,1 s → 0,26 s), un bruitage à chaque coupe sur une montée.
- Puis Marc, son fils dans les bras, en plan long de 2,8 s dans un **silence total**. Ensuite la vraie
  histoire d'Orange 2021 (scène 27).
- Durée totale : 7,6 s, sans voix. Fabriquée à partir des scènes déjà rendues (`build_loops` dans `render.py`).
  Sous-titres et chapitres décalés automatiquement.

## 4. Silences complets (`SILENCE_BEFORE`)
- 1 s avant la scène 50 (« Et voici le détail qui change tout »).
- 1,2 s avant la scène 57 (« Maintenant, la vérité »).
- Ni musique, ni bruitage, ni ambiance pendant ces instants.

## Tests faits dans cette session
| Test | Résultat |
|---|---|
| Moteur 3D, images de contrôle des scènes 3 à 6 et 26 | casse normale, phrase clé en serif, pensée lisible |
| Moteur 2D, scènes 19 à 27 avec la boucle | boucle à sa place, 2,5 s de silence total sur le plan long, image et son calés |
| Moteur 2D, scènes 48 à 50 | silence total d'environ 1 s avant la scène 50 |
| Mixage | 0 effet qui approche la voix à moins de 3 dB, volume final −14 LUFS |

Non testé : les scènes avec Marc en 3D (fichiers Mixamo absents de cette session).

## Pour le rendu complet avec la voix Nicolas
1. Ajouter au dossier `--assets` du moteur 3D (fichiers libres) :
   - `fonts/EBGaramond.ttf` et `fonts/EBGaramond-Italic.ttf` (github.com/google/fonts, `ofl/ebgaramond`) ;
   - `fonts/ComicNeue-Bold.ttf` (`ofl/comicneue`) ;
   - `vendor/addons/utils/SkeletonUtils.js` (paquet npm three@0.160.0, `examples/jsm/utils`).
2. Lancer dans une session qui a les personnages Mixamo. Les voix ElevenLabs sont en cache : aucun crédit
   n'est redépensé.
3. Vérifier les pensées des scènes 2, 22, 32 et 41 avec `--stills`.
