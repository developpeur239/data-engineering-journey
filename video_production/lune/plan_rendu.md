# Plan de rendu : « Le Dernier Écho » (dossier V12)

Transformation du dossier de préproduction V12 (`Le_Dernier_Echo_Dossier_Preproduction_V12.docx`) en plan de
fabrication pour notre moteur : studio 3D en code (`video_production/panne_internet/3d/studio`), rendu image par image,
montage et son par `render.py`, `fx.py` et `edit_plan.py`. La durée n'a pas été corrigée (environ 14 min de voix
estimées pour 12:40 annoncées) : à trancher avant l'enregistrement.

Légende de faisabilité :
- **Tel quel** : le moteur sait déjà le faire (décor, appareil ou effet existant, à habiller).
- **Simplifié** : faisable si l'on change la mise en scène (indiqué dans la colonne).
- **À créer** : nouveau décor ou effet à coder. Taille : P (quelques heures), M (une journée), G (plusieurs jours).

## 1. Choix de style communs

| Élément | Choix | Pourquoi |
|---|---|---|
| Personnages | **Silhouettes noires profondes**, émotion par la forme des yeux blancs (essai : `3d/perso_marc.html`) | Lisible, cohérent sur 12 min, aucun défaut de visage ; validé avec l'essai de Marc |
| Léa | Silhouette, cheveux attachés, **écharpe ambre** (signe de la chaîne) | Reconnaissable en plan large |
| La mère | Silhouette, cheveux longs, manteau clair (un ton gris) | Se distingue de Léa |
| Le garçon | Petite silhouette, **seau rouge** toujours avec lui (plage → voiture → colline → plage finale) | Objet-témoin du fil mère / enfant |
| Le collègue | Silhouette simple, sans accessoire | Rôle bref |
| Décors | 3D au rendu plat (3 tons), fonds clairs ou lumineux pour que les silhouettes se détachent ; la nuit, lumière de Lune bleutée très forte | Règle Last Soul : le personnage se détache du fond |
| La Lune | Sphère texturée (texture NASA déjà utilisée pour le globe), taille apparente exacte selon nos calculs (× 1,1 au jour 2, × 2 au jour 4, × 4 à six heures, × 12 à une heure et demie, × 32 aux dernières minutes) | Une seule Lune, la même partout |
| Étiquettes | « Simulation » permanente en haut à gauche de 00:00 à 11:50 ; « Histoire réelle » sur l'insert de la comète de 1994 | Dossier V12 |
| Textes | Module `typo.py` / styles du studio : cartes en EB Garamond (« Cinq jours plus tôt »), chiffres en police de données (2,5 s, 0,06 s), casse normale | Section 10 du guide de montage |

### Voix
| Rôle | Solution | Remarque |
|---|---|---|
| Narrateur | ElevenLabs « Nicolas – Narrator » (déjà en cache pour la vidéo Internet, réglages connus) | Environ 2 000 mots : environ 12 000 crédits |
| Garçon (3 répliques), collègue (2), Léa (« Je sais. Mais on peut encore comprendre… ») | **Bulles de texte** (Comic Neue, halo sombre) près du personnage, sans voix | Les silhouettes n'ont pas de bouche : rien à synchroniser ; pas de voix d'enfant générée ; logique Last Soul |
| Léa : « Je suis désolée. Je t'aime. » | **Voix réelle** (voix féminine ElevenLabs, ou enregistrement humain) | C'est un message vocal : le son a un sens dans l'histoire |
| Mère : « Je suis là. » | **Voix réelle**, très douce | Phrase-clé du dénouement, à ne pas écrire seulement |
| Sœur | Notifications écrites sur l'écran du téléphone (appareil `phone` existant) | Comme prévu au dossier |

## 2. Découpage scène par scène

| Bloc (dossier) | Plans | Décor | Personnages et poses | Textes à l'écran | Son | Faisabilité |
|---|---|---|---|---|---|---|
| 00:00–00:18 | Noir → chambre de nuit → approche de la fenêtre | Chambre : `apartment` en version nuit, lumière de Lune par la fenêtre | Aucun visage : caméra subjective | « Fiction scientifique — scénario hypothétique » | Souffle, nappe basse | **Tel quel** (habillage nuit) |
| 00:18–00:42 | Contrechamp : Lune énorme, rues bleutées, passants | Rue : `street` de nuit + Lune × 12 | Foule de silhouettes immobiles, quelques téléphones levés | — | Ville étouffée, montée | **Simplifié** : foule en silhouettes répétées, sans animation de marche (P) |
| 00:42–01:00 | Foule figée → gros plan Lune → noir → carton | Même rue ; espace pour la Lune | — | Carte : « Cinq jours plus tôt » (EB Garamond) | Coupure sur « percuter », silence 1–2 s | **Tel quel** |
| 01:00–01:30 | Observatoire → Léa au poste → infographie aller-retour | **Calern : coupole, console, faisceau laser vert** | Léa assise, de trois quarts | Compteur d'écho « 2,51 s » | Ventilation, clavier, impulsion | **À créer** : décor de l'observatoire (M) |
| 01:30–02:00 | Écran des écarts → Léa au téléphone → deux observatoires → orbite qui s'efface | Console de Calern ; `phone` ; schéma | Léa debout, téléphone à l'oreille | Compteur : 2,51 → 2,49 s | Deux bips, appel | **Tel quel** une fois Calern créé |
| 02:00–02:26 | Orbite normale → arrêt du mouvement → trajectoire de chute ; compte à rebours | `globe` (Terre et Lune dans l'espace) + flèches | — | « 4 j 20 h » | Pulsation au chiffre | **Tel quel** |
| 02:26–02:47 | Montage quotidien : aéroport, école, café, ciel calme | `airport` ; école et café = `street` de jour avec façades | Silhouettes qui passent (marche existante, `walk`) | — | Ambiances de chaque lieu | **Simplifié** : école et café montrés de l'extérieur, sans intérieur (P) |
| 02:47–03:00 | Écrans scientifiques → graphique des marées → plage | Console de Calern ; graphique | — | Courbe de marée | Pont sonore vers le ressac | **Tel quel** |
| 03:00–03:33 | Plage, marégraphe, schéma de l'attraction inégale | **Plage de jour** (sable, mer en plan d'eau animé) | — | Schéma : face proche / face éloignée | Ressac, oiseaux | **À créer** : plage (M) |
| 03:33–03:47 | Graphique d'écarts modestes → barrière → plage évacuée | Plage | Agents en silhouette installant une barrière | — | Barrière métallique, annonces lointaines | **Tel quel** une fois la plage créée |
| 03:47–04:00 | Seau → mère et enfant → enfant face à la mer → visage de la mère | Plage | Mère tenant la main du garçon ; garçon avec le seau | Bulle du garçon : « Mais elle est comme d'habitude. » | Ressac, pause 1 s | **Tel quel** (poses `stand`, `reach`) |
| 04:00–04:28 | Téléphones comparant la Lune → conférence officielle muette → embouteillages | `monitors` (salle de presse) ; autoroute | Silhouettes avec téléphones | — | Flashes, moteurs | **À créer** : autoroute avec voitures-blocs (M) |
| 04:28–05:00 | Intérieur voiture → deux photos → regards mère / enfant → autoroute vue de haut | Intérieur de voiture simplifié (vitre + tableau de bord) ; `phone` | Garçon assis, téléphone en main | **Deux photos côte à côte** à l'écran du téléphone ; bulle : « Maman… pourquoi elle grossit ? » | Trafic, pause après la question | **Simplifié** : intérieur réduit au cadre de la vitre (P) |
| 05:00–05:25 | Lune au-dessus d'une ville → salle de crise → schémas | `street` + Lune × 2 ; `monitors` | Silhouettes autour d'une table | Schéma : bombes face à l'énergie de la Lune | Nappe grave, alerte | **Tel quel** |
| 05:25–05:47 | Collègue à la porte → notification → saisie puis effacement → regard vers le laser | Calern | Collègue debout à la porte ; Léa assise | Bulles : « On doit partir. » / « Tu ne peux plus rien changer. » / Léa : « Je sais. Mais on peut encore comprendre ce qui nous arrive. » ; SMS de la sœur à l'écran | Notification unique, touches, porte | **Tel quel** une fois Calern créé |
| 05:47–06:00 | Le collègue sort → Léa seule → télescope orienté | Calern | Léa seule, plan fixe | — | Porte qui se ferme | **Tel quel** |
| 06:00–06:30 | Lune basse → côtes inondées → mer retirée ailleurs, bateaux couchés ; carte simple | Port : quai, bateaux-blocs, plan d'eau qui monte ou se retire ; carte | — | « Force de marée × 60 environ » (jamais une hauteur) | Vagues, vent | **À créer** : port (M) ; carte **tel quel** |
| 06:30–07:00 | Autoroute → sirènes → horizon inondé → mère et enfant → course | Autoroute + plan d'eau au loin | Conducteurs qui sortent ; **mère et garçon qui courent** | — | Deux sirènes, portières, pas | **Simplifié** : course vue de côté et de loin, à contre-jour (la marche `walk` accélérée suffit) (P) |
| 07:00–07:30 | Fissure en gros plan → immeuble → infographie des marées terrestres | Route et façade | — | Aucun chiffre (hypothèse dramatique) | Craquement, gravats | **Simplifié** : la fissure qui traverse la route jusqu'au pied de l'immeuble ; la façade qui s'effondre est remplacée par des débris qui tombent dans le cadre (P) |
| 07:30–08:00 | « × 940 » comme intensité de force → rues fissurées → disque lunaire | Rue + Lune × 12 | — | « Force de marée × 940 environ — pas une hauteur » | Grondement sourd, pause | **Tel quel** |
| 08:00–08:31 | Deux photographies comparées, ligne sombre | Console de Calern ; images de la Lune | Léa penchée sur l'écran | — | Réception de données, zoom | **À créer** : texture de fracture sur la Lune (M) |
| 08:31–09:00 | Animation de l'attraction inégale → **insert d'archive : comète de 1994 (Hubble)** → surface qui se fracture | `globe` ; image d'archive NASA / ESA | — | Étiquette « Histoire réelle » sur l'insert | Tension, fracture très discrète | **Tel quel** pour l'animation ; images d'archive libres de la NASA (vérifier la licence de chaque image) |
| 09:00–09:27 | Téléphone : message de la sœur → enregistrement vocal → « Écouté » | Calern, lumières qui vacillent | Léa assise, téléphone en main, yeux fermés une seconde (paupières de la silhouette) | SMS à l'écran ; statut « Écouté » | Notification, bips d'enregistrement, **voix réelle de Léa** | **Tel quel** (`phone`) |
| 09:27–09:48 | Console → laser → trajet → « 0,06 s » en grand | Calern ; schéma du trajet | Léa à la console | Compteur « 0,066 s » ; réflecteur d'Apollo 14 | Tir, retour très rapproché | **Tel quel** |
| 09:48–10:00 | Sauvegarde → sortie → Lune énorme → bord qui se déforme | Extérieur de Calern, Lune × 32 | Léa debout, de dos (plan long) | — | Clic, la musique s'arrête | **À créer** : bord de la Lune qui se déforme (inclus dans la fragmentation) |
| 10:00–10:28 | Bord irrégulier depuis la Terre → coupe spatiale de la fragmentation → trajectoires | Ciel + Lune ; `globe` | — | — | Musique massive, sons côté Terre seulement | **À créer** : fragmentation de la Lune en blocs (G) |
| 10:28–10:47 | Fragments dans le ciel → traînées dans l'atmosphère → impacts lointains | Ciel de nuit | — | — | Souffles, impacts décalés | **À créer** : traînées incandescentes (M) |
| 10:47–11:00 | Mère et enfant sur la hauteur → ciel déchiré → plan large des deux astres | **Colline de nuit**, route inondée en contrebas | Mère agenouillée qui serre le garçon (seau à ses pieds) | Bulle du garçon : « Est-ce qu'on est assez loin ? » | **Voix réelle de la mère** : « Je suis là. », pause | **À créer** : colline (P) ; pose agenouillée (P) |
| 11:00–11:26 | Plan large depuis l'espace → contact → panaches incandescents | Espace : Terre et Lune | — | — | Impact stylisé, aucun son réaliste dans le vide | **À créer** : collision (G) |
| 11:26–11:50 | Débris → planète incandescente → éclair blanc → noir | Espace | — | — | Apogée puis coupure totale | **Simplifié** : enveloppe incandescente par halo et particules, sans simulation physique (M) |
| 11:50–12:01 | Noir 4 s → plein jour : Léa au travail, le collègue sourit | Calern de jour | Léa à la console ; collègue qui passe | — | Silence, puis clavier | **Tel quel** |
| 12:01–12:15 | Plage ensoleillée : même garçon, même seau, la mère au bord de l'eau | Plage de jour | Garçon et mère, calmes | — | Vagues, rire discret, musique douce après la révélation | **Tel quel** |
| 12:15–12:40 | Léa à la console → aller-retour → « 2,5 s » → Lune normale → fondu | Calern ; ciel | Léa | « 2,51 s » | Impulsion et écho, note tenue | **Tel quel** |

## 3. Ce qu'il faut construire (par ordre de priorité)

| # | Élément | Taille | Utilisé dans | Remarque |
|---|---|---|---|---|
| 1 | **Silhouettes dans le studio** : porter l'essai `perso_marc.html` (yeux dessinés, visée des bras, poses) dans `people.js`, avec les quatre personnages | M | Toute la vidéo | Les poses existent déjà (`stand`, `sit`, `walk`, `reach`, `carry`) ; il manque « agenouillé » et « téléphone à l'oreille » |
| 2 | **Observatoire de Calern** : coupole, télescope, console, faisceau laser, extérieur nuit et jour | M | 9 blocs | Le décor le plus présent |
| 3 | **La Lune géante** : même sphère à toutes les tailles, éclairage, fissures (texture qui s'étend), bord qui se déforme | M | 8 blocs | Réutilise les textures du globe |
| 4 | **Fragmentation** de la Lune en blocs qui se détachent et suivent leur trajectoire | G | 10:00–10:28 | Le plan-clé du retournement |
| 5 | **Plage** (de jour, puis évacuée) | M | 4 blocs | Plan d'eau animé, sable, barrière |
| 6 | **Autoroute** : voitures-blocs, embouteillage, plan d'eau qui envahit l'horizon | M | 3 blocs | |
| 7 | **Port** : quai, bateaux couchés, eau qui monte ou se retire | M | 06:00–06:30 | |
| 8 | **Collision** vue de l'espace, puis planète incandescente | G | 11:00–11:50 | Effet stylisé, pas de simulation physique |
| 9 | Traînées incandescentes des fragments | M | 10:28–10:47 | |
| 10 | Colline de nuit, intérieur de voiture réduit, fissure de route | P | 3 blocs | |

Ce qui existe déjà et sert tel quel : `apartment` (version nuit), `street`, `airport`, `monitors`, `globe`, `phone`
(SMS, photos, statut « Écouté »), étiquettes, cartes de texte, bulles de pensée, compteur de chiffres, boucle accélérée
et silences de `edit_plan.py`, ponts sonores et nappes de `fx.py`.

## 4. Plan son
| Couche | Contenu | Source |
|---|---|---|
| Voix | Narrateur (Nicolas) ; deux répliques en voix réelle (Léa, la mère) | ElevenLabs |
| Ambiances | Chambre, ville étouffée, observatoire (ventilation), plage (ressac, oiseaux), autoroute (trafic), port, colline (vent) | `fx.ambience` (à compléter : plage, autoroute, port) |
| Bruitages | Impulsion laser et écho (bips de plus en plus rapprochés), notifications, enregistrement vocal, barrière, portières, sirènes (deux, distinctes), craquement, gravats, souffles et impacts des fragments | `sfx_real.py` et `fx.py` (à compléter : sirènes, laser) |
| Musique | Nappes : neutre (jours 1-2), sombre (jour 4 → fragments), puis apogée et **coupure totale** sur « notre monde » ; aucune musique dans le noir de 4 s ; musique douce seulement après la révélation finale | `fx.drone` et coupures de `edit_plan.py` |
| Règle de l'espace | Aucun son « réaliste » dans le vide : seulement des sons côté Terre ou un grondement subjectif | Dossier V12 |
| Silences protégés | 00:42 (1–2 s), après la question du garçon, après « Écouté », noir de 4 s à 11:50 | `edit_plan.SILENCE_BEFORE` et pauses |

## 5. Points ouverts avant de lancer la fabrication
1. **Durée** : environ 14 min de voix pour 12:40 annoncées (dossier non corrigé sur ce point). Une coupe d'environ 2 min
   réduirait aussi la fabrication (moins de plans).
2. **Point d'impact exact** (selon la déclinaison de la Lune) pour orienter les plans de l'espace : à fixer avant le n° 8.
3. **Images d'archive de 1994** : vérifier la licence de chaque image NASA / ESA retenue.
4. **Voix de Léa et de la mère** : choisir les deux voix féminines (test de 2 répliques avant de générer).
