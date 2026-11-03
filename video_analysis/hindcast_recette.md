# Hindcast : la recette d'une chaîne qui explose

Analyse de 3 vidéos de [Hindcast](https://www.youtube.com/@Hindcast26) (2,97K abonnés, 3 vidéos, première vidéo mi-octobre 2026),
faite avec `analyze_video.py` : transcription, changements de plan, planches d'images et mesures du son.
Les vidéos, transcriptions et planches ne sont **pas** dans le dépôt : elles appartiennent à leur créateur.
Ce document sert à comprendre un format, **pas à le copier**.

| Vidéo | Vues | Durée | Mots | Débit | Parole | Plans détectés* | Volume |
|---|---|---|---|---|---|---|---|
| What If Russia Used a Nuke Against Ukraine? | **1,6M** en 12 j | 16,9 min | 2 484 | 147 mots/min | 96 % | 84 (≈ 5/min, plan médian 9 s) | −17,1 LUFS |
| What If Israel Nuked Iran? | 178K en 4 j | 11,3 min | 1 792 | 159 mots/min | 99 % | 16 (≈ 1,4/min, plan médian 16 s) | −15,2 LUFS |
| The Solar Storm That Missed Earth by 9 Days | 1,3K en 10 h | 11,4 min | 1 769 | 156 mots/min | 99 % | 56 (≈ 4,9/min, plan médian 11 s) | −16,1 LUFS |

\* *Le détecteur (seuil 0,15) sous-compte les plans : beaucoup de transitions sont des mouvements de caméra continus ou des fondus sur fond sombre. La comparaison entre les vidéos reste valable.*

**Aucune pause de plus de 0,6 s** n'est détectée : une nappe musicale tourne en continu sous la voix, qui parle 96 à 99 % du temps.

---

## 1. Le script : une structure en 9 temps, identique dans les trois vidéos

| # | Temps | Russie (1,6M) | Iran (178K) |
|---|---|---|---|
| 1 | **Ouverture sensorielle (0:00 – 0:30)** : un lieu, une heure, un détail humain, puis *quelque chose ne va pas* | Île du Sud de la Nouvelle-Zélande, 2 ans après la guerre, un soleil pâle, le blé pousse encore. *« And it all started with one decision. »* | Kashan, 3h46. Mina, 19 ans, examen dans 5 h. La chambre s'illumine, mais *« this sun is rising in the wrong part of the sky »* |
| 2 | **Contrat d'honnêteté (0:30 – 0:50)** : simulation, mais chiffres réels et sources citées | *« What you're about to see is a simulation. But nothing in it is made up. »* Essais d'armes, arsenaux, études climatiques, simulation de Princeton | *« Mina is invented. The war is invented. But the mountain is real. The missing uranium is real. »* |
| 3 | **Vraie histoire datée (1 – 3 min)** : jusqu'au mois de tournage | Nagasaki 1945, « 81 ans », 2022, 2023, nov. 2024, fév. 2026, Doomsday Clock | Dimona années 1960, SIPRI ~90 têtes, juin 2025, 28 fév. 2026, 440 kg d'uranium disparus |
| 4 | **« Let's do the math »** : un chiffre rendu concret | Moins d'1 gramme de matière, *« about the weight of a paperclip »*, un train de 3 km de TNT | 100 kt ≈ *« almost seven Hiroshimas »* |
| 5 | **Simulation minutée** : T+0 / 1 s / 3 s / 10 s, puis des **cercles de distance** | *« How bad it is depends on one thing. How far away you are. »* 1 km, 2 km, 5 km, 20 km | *« How bad it is depends on how far away you are. »* 1 km, 3 km, 5 km, 40 km (Mina) |
| 6 | **Escalade par choix impossibles** + boucles ouvertes | *« Do nothing… Answer with nuclear weapons… »* puis Article 5, Plan A, Corée du Nord, Chine | Appel à Washington : *« Did the Americans say yes? »*, *« Remember that uncertainty »*, *« Hold that thought »* |
| 7 | **Retournement** | La Chine se trompe sur ses radars, *« a mistake made under pressure in less than 15 minutes »* | *« The uranium was never in the mountain. »* |
| 8 | **Retour à l'ouverture** (boucle fermée) | Le blé de Nouvelle-Zélande, *« the last safe place on earth »* | Mina se réveille chaque nuit à 3h45 et regarde d'où vient la lumière |
| 9 | **« Now, the truth »** : réel contre inventé, une morale, une question | *« A limited nuclear war does not stay limited. »* | *« Do you use it? Tell me in the comments. »* |

### La 3ᵉ vidéo (tempête solaire) confirme la recette point par point

1. **Ouverture :** Le Caire, 12 décembre 2026, 2 h du matin. Des aurores au-dessus des pyramides, puis sur les téléphones : *« London is dark. Stockholm is dark… »*
2. **Contrat :** *« What you're about to see is a simulation. But it's built on a storm that really hit the earth. »*
3. **Histoire :** Carrington en 1859, les télégraphistes électrocutés, la tempête de 2012 qui *« missed us by about nine days »*.
4. **The math :** v = d/t (2 400 km/s), E = ½mv², puis 20 V/km × 500 km = 10 000 V.
5. **Boucle ouverte :** un transformateur met 2 ans à être remplacé. *« Remember that number. It's the key to everything that follows. »* Elle est payée à 9:01 : *« Now that number comes back. »*
6. **Simulation minutée :** minute 0, 2, 5, 10, avec un compte à rebours « TIME TO IMPACT ». La variante des cercles de distance devient *« How bad it gets depends on where you live »*, avec une carte rouge / orange / jaune.
7. **Escalade :** jour 1, semaine 1, puis un an.
8. **« Now the truth »** : 1859, 1921, 2012 et mai 2024 étaient réels.
9. **Une fin utile** au lieu d'une question : *« look up, enjoy it, and then go fill a bottle of water. »*

**À retenir :** la chaîne passe déjà de la guerre nucléaire aux **catastrophes naturelles**. Sur le plan visuel, c'est le même système : étiquettes, globe, « THE MATH » avec de vraies formules, chronos, fausse notification de téléphone. Et le rythme (≈ 4,9 plans/min) est le même que dans la vidéo à 1,6M.

### Les règles d'écriture
- **Phrases très courtes, au présent, avec des fragments** : *« No markets. No trade. For billions of people, no food. »*
- **Un chiffre toutes les 2 ou 3 phrases**, toujours rendu concret (trombone, train, Hiroshima, « hauteur des avions de ligne »).
- **Un motif répété** qui structure la vidéo : *« 81 years »* revient au début, au milieu et à la fin.
- **Des boucles ouvertes plantées tôt et payées tard** : *« Remember that… it's what decides the rest of this story. »*
- **Un personnage humain fil rouge**, même inventé (Mina) ou un lieu (le champ de blé), qu'on retrouve à la fin.
- **Des sources nommées** (Princeton, SIPRI, Nature Food 2022, l'AIEA) et une distinction réel / inventé répétée : c'est ce qui rend crédible un sujet « what if ».

---

## 2. Le visuel : un système de motion design sombre, presque entièrement faisable en code

**Le code couleur**
- Fonds noir et bleu nuit.
- **Rouge** pour le danger, ce qui est inventé et la Russie.
- **Cyan** pour ce qui est réel et l'Occident.
- **Orange** pour les explosions.

**Les éléments qui reviennent dans toutes les vidéos**

| Élément | Exemple | Faisable par Claude en code ? |
|---|---|---|
| Étiquette **« SIMULATION »** (point rouge) ou **« REAL HISTORY »** en haut à gauche, logo H en haut à droite, sur chaque image | Partout | ✅ Remotion / Motion Canvas |
| **Globe 3D** de jour ou de nuit, mouvements de caméra, arcs de missiles | Ouverture, chapitres | ✅ Three.js (textures NASA Blue/Black Marble, domaine public) |
| **Cartes vectorielles sombres** : villes étiquetées, points rouges ou cyan, trajectoires | Iran, Europe (« Plan A »), Japon | ✅ D3 + GeoJSON (Natural Earth) |
| **Gros chiffres typographiques** et grilles de points | « ~86 », « 427 kg », « ≈50 », « 1.0 KM » | ✅ Remotion |
| **Chronos et cercles de distance** | « T+1.0 µs », « 03:47 », cercles « 1.0 KM · YOU » | ✅ Remotion |
| **Cartes de choix** | « AN IMPOSSIBLE CHOICE » 01 / 02 / 03 | ✅ Remotion |
| **Schémas en coupe** | Montagne de Fordow avec échelle de profondeur, barre d'enrichissement | ✅ SVG / D3 |
| **Sous-titres de résumé** en bas de l'écran | « A PALE SUN · A GREY SKY » | ✅ Remotion |
| **Scènes 3D low-poly** | Champ de blé, immeubles, chambre, œil, personnage | ⚠️ Three.js / Blender Python : faisable mais long |
| **Champignon nucléaire et onde de choc** | Simulation | ⚠️ Particules : c'est l'élément le plus difficile |
| **Miniatures photoréalistes** (explosions, pyramides) | Miniatures | ❌ Il faut un générateur d'images |

**Rythme :** une nouvelle information visuelle (texte, chiffre, mouvement) toutes les quelques secondes, même quand le plan ne change pas.

---

## 3. Le son
- **Voix off continue**, de 147 à 159 mots/min (rythme de documentaire), sur 96 à 99 % de la durée.
- **Nappe musicale permanente** : aucun silence détecté.
- **Volume** de −15 à −17 LUFS (YouTube normalise vers −14).
- **Voix humaine ou synthétique ?** Les chiffres ne permettent pas de le savoir : **il faut écouter.**

---

## 4. Pourquoi la vidéo Russie (1,6M) a battu la vidéo Iran (178K) : hypothèses

1. **L'enjeu touche le spectateur lui-même**, et pas une région : une guerre mondiale, 5 milliards de morts de faim. Et l'ouverture pose une question personnelle, *où serais-je en sécurité ?*, qui n'a sa réponse qu'à la fin (la Nouvelle-Zélande). Cette boucle tient 16 minutes.
2. **Elle est plus longue** (16,9 contre 11,3 min) : plus de temps de visionnage et de publicités.
3. **Elle est plus variée visuellement** : environ 5 plans/min contre 1,4. La vidéo Iran est la seule à rythme lent : les deux autres sont à ≈ 5/min.
4. **Son titre et sa miniature promettent une échelle** : *« We Mapped Every Strike That Follows »*, *« 12 MINUTES TO EXTINCTION »*.
5. **⚠️ Le biais de date :** la vidéo Iran n'avait que 4 jours lors du relevé, contre 12. Elle peut encore monter.

---

## 5. Transposer la recette, sans copier

À reprendre : **la structure en 9 temps, le contrat d'honnêteté, les cercles de distance et le système visuel.**
À changer : **le sujet, la langue, la charte graphique et le nom.**

**Piste :** des catastrophes naturelles et historiques, en français. *(Hindcast a déjà traité Carrington : ne pas le refaire.)* Elles sont mieux acceptées par les annonceurs que la guerre nucléaire.

| Idée | Ouverture sensorielle | « Let's do the math » | Retournement possible |
|---|---|---|---|
| Et si l'éruption du Vésuve de 79 avait lieu aujourd'hui à Naples ? | Un livreur à Naples, 9h12, le sol qui vibre | ~700 000 habitants dans la zone rouge (3 M dans l'agglomération) | Le plan d'évacuation prévoit 72 h, l'éruption en laisse 15 min |
| Et si la crue de 1910 revenait à Paris ? | Une agente RATP à Châtelet, 4 h du matin, l'eau dans l'escalier | 8,62 m au pont d'Austerlitz, en 1910 comme pour l'exercice européen EU Sequana 2016 | L'eau monte lentement ; ce qui tue la ville, c'est la coupure d'électricité |
| Et si un astéroïde comme celui de Toungouska tombait sur Paris ? | Un matin de juin sur le périphérique | 10 à 15 Mt, 2 000 km² de forêt rasés en 1908 | On l'avait vu, mais trop tard pour dévier |

**Rappel YouTube (« inauthentic content ») :** chaque vidéo doit être une vraie recherche, avec un vrai script et une vraie voix. Ce sont les sources, la structure et la mise en scène qui font le succès de Hindcast, pas un modèle répété à la chaîne.
