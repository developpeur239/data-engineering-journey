# DESIGN.md · Mondes du Soleil

Récit : la page commence **de nuit** (hero 3D sombre), le soleil se lève au scroll, puis la page passe **au clair**. Elle se referme sur un lever de soleil (appel à l'action final).
Choix retenus : hero sombre plein écran (réf. 1) · titres gras avec un mot en orange (réf. 3) · services en alternance image/texte avec visuels superposés (réf. 3) · galerie en tuiles de tailles variées (réf. 1) · avis en texte seul (réf. 1) · fonds alternés (réf. 2) · lueur d'horizon finale (réf. 1) · footer sombre (réf. 2). Pas de formulaire en page d'accueil.

## Couleurs
| Jeton | Valeur | Origine | Usage autorisé |
|---|---|---|---|
| `--orange` | `#F18A01` | **extrait du logo** (médiane du mot « SOLEIL ») | boutons, accents **sur fond sombre** (7,76:1 sur `--nuit`) |
| `--sable` | `#D8A975` | **extrait du logo** (couleur unie de la maison) | décor, texte sur fond sombre (9,13:1) |
| `--soleil` | `#FEDD2C` | **extrait du logo** (médiane du soleil) | lumière de la scène 3D uniquement, jamais en texte |
| `--orange-texte` | `#A35D01` | dérivé de `--orange` | mot en orange dans un titre, liens **sur fond clair** (5,09:1 sur blanc, 4,66:1 sur `--sable-pale`) |
| `--nuit` | `#0B0D10` | estimation (réf. 1) | hero, appel à l'action final |
| `--nuit-2` | `#16191E` | estimation | footer, surfaces sombres |
| `--encre` | `#14161A` | choix | texte sur fond clair (18,1:1) ; **texte des boutons orange** (7,22:1) |
| `--gris` | `#4D535B` | choix | texte secondaire sur fond clair (7,77:1 sur blanc) |
| `--gris-nuit` | `#A3A9B1` | choix | texte secondaire sur fond sombre uni (8,22:1) ; **jamais sur la scène 3D** : le ciel final s'éclaircit (mesuré à 3,27:1), on y utilise `--blanc-chaud` |
| `--blanc-chaud` | `#F5F3EF` | choix | texte principal sur fond sombre (17,56:1) |
| `--sable-pale` | `#FAF4EC` | estimation | une section claire sur deux |

**Interdits (contraste mesuré)** : `--orange` sur blanc (2,51:1), `--sable` sur blanc (2,13:1, c'est l'erreur du site actuel), texte blanc sur `--orange` (2,51:1).

## Typographie
- Titres : **Poppins** (linéale géométrique, estimation d'après la réf. 3). Corps : **Inter**. Les deux en `font-display: swap`, fichiers WOFF2 hébergés sur le site.
- H1 hero : `clamp(2.5rem, 5.2vw, 4.5rem)` · 700 · interligne 1.05 · approche −0,02em. Un seul mot en couleur.
- H2 : `clamp(2rem, 4vw, 3.25rem)` · 700 · interligne 1.1. H3 : `1.375rem` · 600 · interligne 1.3.
- Corps : `1.0625rem` (17 px) · 400 · interligne 1.6 · mesure max. 65ch. Petit texte : `0.875rem` · 400 (jamais en dessous).
- Surtitre : `0.8125rem` · 600 · majuscules · espacement +0,12em, en `--orange-texte` sur fond clair ou `--orange` sur fond sombre.
- Titres en casse normale (pas tout en majuscules comme le site actuel). Ces valeurs sont des estimations : les captures sont trop petites pour les mesurer.

## Espacements et grille
- Échelle (px) : 4 · 8 · 12 · 16 · 24 · 32 · 48 · 64 · 96 · 128.
- Marge verticale de section : `clamp(64px, 10vw, 128px)`. Gouttière latérale : 16 px (≤ 480 px), 24 px, puis 32 px (≥ 1024 px).
- Conteneur : 1200 px max ; texte courant 65ch max. Grille de 12 colonnes, espace de 24 px.
- Une idée par écran (réf. 1) : beaucoup d'espace vide autour des titres, aucun bloc collé à un autre.

## Formes
- Boutons : en pilule (`border-radius: 999px`, observé sur les réf. 1 et 3) · hauteur 48 px min. · padding 0 24 px · Inter 600 · 1rem.
  - Principal : fond `--orange`, texte `--encre`. Secondaire : contour de 1,5 px, texte de la couleur du fond opposé.
- Cartes et tuiles : rayon de 16 px. Photos : rayon de 12 px. Pastilles et badges : 999 px. (estimation)
- Focus clavier : contour de 3 px avec un décalage de 3 px, en `--orange-texte` sur fond clair et en `--orange` sur fond sombre (contraste ≥ 3:1 dans les deux cas).
- Ombres : une seule, `0 12px 32px rgb(11 13 16 / .12)`, pour les visuels superposés. (estimation)

## Mouvement
- Hero : progression du scroll lissée (`lerp` 0,08 par image). `prefers-reduced-motion` : image fixe, aucune animation.
- Apparition des sections : opacité de 0 à 1 et translation de 16 px à 0, en 500 ms `cubic-bezier(.2,.7,.2,1)`, une seule fois. (estimation)
