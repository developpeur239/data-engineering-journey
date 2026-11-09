# Le Dernier Écho : fiche de reprise (à lire en premier dans une nouvelle session)

Branche de travail : `claude/modest-brahmagupta-fqowhp` (reprise de `claude/optimistic-ptolemy-jq9t7e`). Méthode complète : `film/README.md`. Texte de la voix : `texte_voix_V13.md`
(validé). Plan général : `plan_rendu_v2.md`.

## Où on en est
| Élément | État |
|---|---|
| Bloc 1 « Le dernier ciel » (00:00–01:00, 50 s) | **Validé.** `b01/shots.json`, décors `decors/nuit_ville.py` |
| Test Léa (clavier, téléphone, regard) | **Validé** : méthode des personnages (`test_lea/`) |
| Bloc 2 « Le premier signal » (01:00–02:00, 58 s) | Rendu et corrigé (son de fond retiré, Léa retouchée), **en attente de validation finale** |
| Bloc 3 « Le compte à rebours » (02:00–03:00, 62,5 s) | **Validé** : schémas `decors/compte.py`, rue de jour `decors/ville_jour.py`, plage `decors/littoral.py` |
| Bloc 4 « Le premier jour » (03:00–04:00, 63 s) | **Validé** : schémas `decors/maree.py`, `decors/littoral.py` (Plage, Port, Barriere), mère et garçon `b04/mere_*.png`, `b04/garcon_*.png` (silhouettes, seau rouge) |
| Blocs 5 à 13 (04:00–12:40) | Rendus d'une traite à la demande de l'utilisateur, **à valider dans le film assemblé**. Découpage : `plans_reste.py` ; voix : `generer_voix.py` ; images : `generer_images.py` ; bruitages : `generer_sons.py` ; décors : `decors/astres.py` (Lune et Terre texturées, fractures, fragmentation, collision), `decors/scenes.py`, `decors/littoral.py` (PlageFin) |
| Film complet | `python3 assembler.py` → `le_dernier_echo.mp4` (blocs 1 à 13 reconstruits par le moteur) |

Les vidéos `bXX/blocXX.mp4` ne sont pas dans git (trop lourdes) : `python3 -m moteur.core bXX` les reconstruit.

## Règles de l'utilisateur (non négociables)
- **Économiser l'argent avant tout** : annoncer le coût (crédits Kie ≈ 12/image, caractères ElevenLabs) AVANT de générer ;
  réutiliser décors, personnages et mains ; tout ce qui peut être fait en code l'est.
- **Qualité 2D cohérente, rien de « bizarre »** : contrôler chaque bloc par planche-contact et images clés avant le rendu
  complet ; corriger à la source (pas par l'étalonnage).
- **Avancer bloc par bloc**, envoyer chaque bloc et attendre la validation avant le suivant.
- **Arrêter l'utilisateur** si une demande mène à un mauvais résultat ou à une dépense inutile (il l'a demandé).
- **Son** : pas de fond sonore permanent (ni ronronnement ni nappe). Seulement des sons motivés par l'image (clics,
  bips, laser, pas…) et des ambiances extérieures discrètes. Voix nette au-dessus de tout ; −14 LUFS en référence de travail.
- **Personnages** : 2D articulée + mains par remplacement (5 dessins), contours discrets (2 px, faible opacité) + liseré
  de la lumière du décor, synchro labiale sur la voix réelle quand une bouche visible parle. Pas de 3D pour les personnages.
- Images générées = dessins fixes uniquement ; rien qu'un personnage touche dans un décor généré (chaise, téléphone…).
- « Simulation hypothétique » visible jusqu'au noir de la collision.

## Remettre l'environnement en route (nouveau conteneur)
```bash
pip install -q opencv-python-headless scikit-image faster-whisper fonttools brotli
```
- Clés : Kie (`KIE_API_KEY=proxy-injected`) et ElevenLabs (`ELEVENLABS_API_KEY=proxy-injected`) sont injectées par le
  proxy de l'environnement ; si ElevenLabs répond 401, redemander la clé (formulaire sécurisé, hôte `api.elevenlabs.io`,
  en-tête `xi-api-key`).
- Les scripts de génération s'exécutent depuis `video_production/panne_internet/` (modules `kie`, `render`, `sfx_real`, `fx`).
- Whisper télécharge son modèle « small » au premier lancement.

## Faire un bloc (≈ 1 h de préparation + 10 à 15 min de rendu)
1. `bXX/voix.json` (texte exact du V13) → voix ElevenLabs (Nicolas `aQROLel5sQbj1vuIVi6B`, eleven_v4, 0,7 / 0,5).
2. `python3 -m moteur.mots bXX` : minutage contrôlé (lire le rapport ; attention aux mots répétés : `"les#2"`).
3. `bXX/shots.json` : plans ancrés sur les mots ; réutiliser `decors/` (Chambre, Fenetre, Rue, Exterieur, Poste,
   Laser, Ecran, Orbite) ; actions de Léa dans `"lea"`.
4. `python3 -m moteur.core bXX --planche` puis `--images …`, corriger, puis rendu complet ; ne re-rendre que les plans
   modifiés (effacer leurs images dans `bXX/.frames/`).

## Étape suivante
Retours de l'utilisateur sur le film assemblé, bloc par bloc. Pour corriger un plan : modifier `plans_reste.py` (ou le décor),
`python3 plans_reste.py bXX`, effacer les images du plan dans `bXX/.frames/`, relancer `python3 -m moteur.core bXX`, puis
`python3 assembler.py`. Personnages : style de Léa (`decors/style_perso.py`) ; ne pas revenir aux silhouettes noires.

## Coûts engagés à ce jour (film)
Bloc 1 : 5 images, 704 car. de voix, 3 bruitages. Test Léa : 2 images. Bloc 2 : 1 image, 936 car., 1 bruitage. Bloc 3 : 2 images (rue de jour, enfants), 1 045 car., 2 bruitages (ambiance matin, avion). Bloc 4 : 3 images (plage barrée, port, mère et garçon), 951 car. + 31 car. MiniMax, 1 bruitage (port). Blocs 5 à 13 : 5 images, 7 567 car. ElevenLabs + 59 car. MiniMax, 5 bruitages.
