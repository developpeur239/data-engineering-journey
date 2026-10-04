/* ==================================================================
   Médias du hero : fichier GÉNÉRÉ par outils/preparer-medias.py.
   Ne pas modifier à la main (sauf pour tester) : voir MEDIAS.md.
   Listes vides = la scène 3D et le bonhomme provisoire s'affichent.
   ================================================================== */
window.MDS_MEDIAS = {
  // Vidéo réaliste découpée en images, lue au rythme du scroll
  sequence: { ordinateur: [], mobile: [] },
  bonhomme: {
    apparition: 0.78,          // progression du hero à laquelle il arrive (lever du soleil)
    ips: 24,                   // images par seconde de l'animation de salut
    salut: [],                 // images détourées (fond transparent) du salut
    regard: {
      colonnes: 5, lignes: 5,  // grille des directions du regard
      tete: [0.5, 0.22],       // position de la tête dans l'image (fractions largeur, hauteur)
      images: [],              // ligne par ligne, de haut-gauche à bas-droite
    },
  },
};
