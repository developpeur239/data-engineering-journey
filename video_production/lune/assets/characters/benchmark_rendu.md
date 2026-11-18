# Benchmark de rendu (machine de cette session : 4 cœurs, sans carte graphique)

Scène testée : Léa assise au clavier, 960×540, mesure sur 10 images (après la première).

| Moteur | Réglages | Temps par image | 5 s à 24 i/s | 12 min à 12 i/s |
|---|---|---|---|---|
| Cycles + contour Freestyle | 10 échantillons, débruitage | **10,1 s** (12,3 s avant l'allègement des maillages) | 20 min | 24 h |
| Workbench | aplats mats, ombre légère, contour d'objet | **1,33 s** (2,65 s avant allègement) | 2 min 40 | 3 h 10 |
| EEVEE | pilote OpenGL logiciel (Mesa llvmpipe) | **17,5 s sur un simple cube** | inutilisable | inutilisable |

- **Workbench sur un simple cube : 0,11 s par image.** Sur la scène de Léa, l'essentiel du temps n'est donc pas le
  dessin de l'image. C'est le recalcul de la scène à chaque image : déformation des maillages par le squelette,
  cinématique inverse, écriture du PNG.
- **Allègement des maillages :** mains de 61 000 à 13 600 faces, cheveux de 50 000 à 24 000. Aucune différence
  visible ; Cycles gagne 18 % et Workbench 50 %.
- **Objectif de 0,1 s par image :** il n'est pas atteignable avec Blender sur cette machine.

Recommandation : rendre la production finale sur une carte graphique. Une machine avec carte NVIDIA, ou une carte
graphique louée à l'heure, doit permettre EEVEE ou Cycles sur GPU, mais le temps réel n'a pas été mesuré : il faut
refaire ce benchmark sur cette machine avant de s'engager. Ici, Workbench ne sert qu'aux prévisualisations et à
l'animatique.
