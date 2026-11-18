# Méthode qualité : comprendre la référence, puis aller plus loin (sans la copier)

La référence (« What If… », 11 min, 4K) n'est pas copiée : ni son texte, ni ses plans, ni sa charte exacte.
On en retient les **principes** qui font sa qualité, puis on les pousse plus loin sur les détails que les
débutants négligent. Ce document sert de cahier des charges pour chaque scène.

## 1. Ce qui fait la qualité de la référence (principes)
1. **Le réel matérialisé en 3D** : chaque chose dont parle la voix existe à l'écran comme un objet ou un lieu.
2. **Mouvement continu** : peu de coupes (19 en 11 min), la caméra ne s'arrête jamais, les éléments entrent un par un.
3. **Graphisme sobre et hiérarchisé** : 1 titre, 1 sous-titre, 1 chiffre ; étiquette d'état (simulation / réel) constante.
4. **Code couleur stable** : rouge = danger/simulation, cyan = réel/fonctionne, orange = repère, gris = contexte.
5. **Clair-obscur** : personnages simples mais éclairés comme au cinéma.

## 2. Nos améliorations (ce qui est déjà codé)
| Domaine | Détail négligé par les débutants | Ce que fait notre moteur |
|---|---|---|
| Synchro image / voix | Les événements tombent « à peu près » sur la phrase | **Horodatage mot à mot** de la voix (faster-whisper, recalé sur le script) : l'écran passe au rouge sur « refuse », le chiffre apparaît sur le mot qui le prononce, le titre sur le mot qu'il reprend. L'image précède le mot de 0,1 s (le cerveau perçoit alors l'image et le son ensemble). |
| Synchro image / son | Bruitages posés sans viser l'image | Chaque bruitage réel est calé sur **son propre transitoire** (détection d'attaque) et sur l'instant de l'événement visuel ; mêmes horloges pour l'image et le son. |
| Transitions | Coupes sèches ou fondus partout | **Filé directionnel** (flou + glissé, 0,2 s) entre deux plans d'un même temps, calé sur un souffle ; **noir court** seulement aux changements de temps du récit ; ponts sonores (l'ambiance du plan suivant démarre 1 s avant la coupe). |
| Émotion | Visages figés | Expressions pilotées par le récit (inquiétude des sourcils et de la bouche, soulagement, pleurs de l'enfant avec larmes), **clignements**, respiration, regard qui se lève vers l'écran au refus. |
| Personnages | Mannequins sans détails | Peau à reflet doux (sheen), iris et pupilles, paupières, pommettes, mâchoire, lunettes, barbe, mains avec pouce, genoux et coudes articulés, vêtements distincts (manteau à revers, blouse, tablier). |
| Lumière et couleur | Même étalonnage partout | **Étalonnage par temps du récit** : bleu froid (simulation), rouge sourd (escalade), chaud au retour (temps 8) ; lumière qui raconte (écran rouge sur le visage de Marc). |
| Texture d'image | Image « numérique » trop propre | Grain animé discret, vignettage, ombres douces. |
| Texte à l'écran | Typographie approximative | Espaces fines insécables avant « ? ! : », séparateurs de milliers, police à chasse fixe pour les chiffres, marges constantes (104 px), contraste garanti (dégradé sous les titres), apparition avec flou + glissé de 18 px. |
| Mixage | Effets qui couvrent la voix | Effets baissés **seulement** sous les syllabes, coupures de musique sur les phrases clés, impacts dans les blancs, -14 LUFS, crête < -1 dB. |
| Réel / inventé | Confusion | Étiquette « HISTOIRE RÉELLE » (cyan) ou « SIMULATION » (rouge) sur chaque plan, mention « RECONSTITUTION » sur les scènes réelles mises en images. |

## 3. Pistes suivantes (par ordre d'impact)
1. Plusieurs plans par phrase longue (gros plan / plan large) dans les scènes 3D les plus longues.
2. Profondeur de champ (flou d'arrière-plan) sur les gros plans de visages.
3. Synchronisation labiale approximative (bouche qui suit l'énergie de la voix quand un personnage parle).
4. Musique : thème court qui revient au temps 1, au temps 7 (« 78 minutes ») et au temps 8.
