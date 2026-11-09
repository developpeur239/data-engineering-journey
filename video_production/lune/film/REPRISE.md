# Le Dernier Écho : fiche de reprise (à lire en premier dans une nouvelle session)

Branche de travail : `claude/modest-brahmagupta-fqowhp` (reprise de `claude/optimistic-ptolemy-jq9t7e`). Méthode complète : `film/README.md`. Texte de la voix : `texte_voix_V13.md`
(validé). Plan général : `plan_rendu_v2.md`.

## Où on en est
| Élément | État |
|---|---|
| Bloc 1 « Le dernier ciel » (00:00–01:00, 50 s) | **Validé.** `b01/shots.json`, décors `decors/nuit_ville.py` |
| Test Léa (clavier, téléphone, regard) | **Validé** : méthode des personnages (`test_lea/`) |
| Bloc 2 « Le premier signal » (01:00–02:00, 58 s) | Rendu et corrigé (son de fond retiré, Léa retouchée), **en attente de validation finale** |
| Bloc 3 « Le compte à rebours » (02:00–03:00, 62,5 s) | Rendu, **en attente de validation** : schémas `decors/compte.py`, rue de jour `decors/ville_jour.py`, plage `decors/littoral.py` |
| Blocs 4 à 12 | À faire, un par un |

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

## Étape suivante : bloc 4 « Le premier jour » (03:00–04:00)
Après validation du bloc 3. Réutilisables : plage (`littoral.Plage`, image existante), rue de jour (`ville_jour.Rue`,
enfants détourés `b03/enf_*.png`), compteur à rebours du moteur (texte avec `"reste"`, toujours le temps restant avant
le contact ; repères dans plan_rendu_v2 § 7.1 bis).

## Coûts engagés à ce jour (film)
Bloc 1 : 5 images, 704 car. de voix, 3 bruitages. Test Léa : 2 images. Bloc 2 : 1 image, 936 car., 1 bruitage. Bloc 3 : 2 images (rue de jour, enfants), 1 045 car., 2 bruitages (ambiance matin, avion).
