# Prochaine session : voix et clips (à lire en premier)

Décisions prises (3 novembre 2026) :
- **ElevenLabs en direct, forfait Starter (6 $/mois, 30 000 crédits, licence commerciale)** pour la voix des Shorts
  « What If » (le skill fonctionne tel quel) ; passer au Creator quand le volume augmente.
- **Kie.ai** pour les clips vidéo IA de la vidéo longue (Kling 3.0 ≈ 0,07 $/s), et éventuellement pour la voix de la
  vidéo longue si son rendu est préféré à l'écoute.
- **Toujours écouter / regarder des extraits avant toute génération en masse.**

Clés attendues dans l'environnement (ne jamais les afficher) : `ELEVENLABS_API_KEY`, `KIE_API_KEY`
(et `MINIMAX_API_KEY` si on compare aussi MiniMax).

## Étape A — Comparer les voix de la vidéo longue (aucun rendu complet)
Projet : `video_production/panne_internet/` (`scenes.py` = script final, ne pas modifier le texte des voix ;
`render.py` = moteur, `README.md`).
1. Scènes de test : 1 (« Paris, un mardi de décembre… »), 4 (« Domain Name System », « Orange, Rogers, Cloudflare et
   CrowdStrike »), 10 (« l'application X, ChatGPT ou Spotify »).
2. Voix à comparer : ElevenLabs direct (Multilingual v2, une ou deux voix masculines adaptées au français),
   ElevenLabs via Kie.ai si l'API le permet, MiniMax `French_MaleNarrator` si la clé existe.
3. Un MP3 court par voix (les 3 scènes bout à bout), envoyé à l'utilisateur ; tableau débit / durée estimée /
   noms anglais bien prononcés (vérifiés par faster-whisper : décoder avec ffmpeg en float32 16 kHz, car PyAV est
   incompatible). Annoncer le coût de chaque appel.
4. Attendre le choix de l'utilisateur, puis ajouter le fournisseur choisi à `render.py` (comme `--tts minimax`).

## Étape B — 2 clips IA d'essai via Kie.ai (budget max 5 $)
Une image de référence de Marc (34 ans, Parisien, avec son fils de 2 ans, hiver, palette sombre bleu-vert et accent
orangé, sans texte), puis 2 clips de 5 à 8 s, sans son : scène 2 (automate du métro qui refuse sa carte) et
scène 32 (pharmacie avec son fils fiévreux). Rappeler la déclaration « AI use : Yes » dans YouTube Studio.

## Étape C — Premier Short « Et si… ? » avec le skill What If
`bash video_production/what_if/setup_studio.sh <scratchpad>/what-if-studio` (polices locales incluses ; rendu avec
`--browser-executable=/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell`).
Idée liée à la vidéo longue, par exemple « Et si Internet s'arrêtait 10 secondes ? » (vérifier d'abord sur YouTube
qu'elle n'existe pas). Suivre le `SKILL.md` du skill : script → voix → plan → **planche des plans montrée à
l'utilisateur avant l'animation** → animation → son → master. Personnages originaux (pas Pip ni Mo).

## À appliquer dès la prochaine vidéo longue (décision du 4 novembre 2026)
Les enseignements de « 1 MINUTE » / « 1 HOUR » (Last Soul) sont à appliquer dès l'écriture, pas en retouche :
analyse dans `../video_analysis/lastsoul_recette.md`, règles dans `montage_guide.md` (sections 9 et 10),
réglages déjà branchés dans le moteur (`panne_internet/raconter_sans_voix.md` : pensées, boucle accélérée,
silences complets). La vidéo « panne Internet » est publiée : on n'y touche plus.

Avant tout script (vidéo longue, Short ou court-métrage) : écrire d'abord **l'histoire en 5 lignes**
(situation, désir, conflit, changement, résultat), la faire valider, puis la développer en 10 lignes, puis
seulement découper en plans. Chaque plan doit se rattacher à l'une des 5 lignes.
Narration visuelle (tous les formats) : accroche des 10 premières secondes = contexte + question + émotion ; tension
par vagues (monter, relâcher, remonter plus haut) ; montée sonore coupée net ; « bulle » sonore pour ce qui ne se
filme pas ; plans rapides pour l'accessoire, longs pour l'essentiel ; deux couches (voyage physique et voyage
intérieur, porté par une métaphore visuelle, le son et la lumière quand il n'y a pas de voix).
