# Léa V2 : mains à cinq doigts (compte rendu)

## Fichiers
- `build_lea_v2.py` : script Blender + Python. Il recrée Léa avec des mains à doigts, le squelette des doigts, la
  planche des mains et les deux animations. Usage : `python3 build_lea_v2.py stills | clavier | telephone`.
- `lea_v2.blend` : le modèle modifié, avec son squelette et ses cibles de cinématique inverse (IK).
- La V1 est conservée telle quelle : `build_lea.py` et `lea.blend` donnent le même résultat qu'avant. Sa seule
  modification est une option, `hands_in_body`, qui vaut `True` par défaut.
- `renders/mains_planche.png` : mains ouverte, à demi fermée et fermée, de face, de profil et de trois-quarts, plus
  une vue d'ensemble.
- `renders/lea_clavier.mp4` et `renders/lea_telephone.mp4` : les deux animations de 5 s (24 i/s, 960×540).

## Ce qui a changé
1. **Mains séparées du corps.** En V1, les mains étaient fondues dans le corps, sans doigts possibles. En V2, le bras
   s'arrête au poignet et chaque main est un objet à part (`Lea_main_G`, `Lea_main_D`), dans le même noir mat que le
   visage.
2. **Une géométrie continue.** Les doigts ne sont pas cinq cylindres collés. La paume, un poignet aplati, quatre doigts
   et le pouce sont des volumes fondus en une seule surface (remaillage voxel de 0,9 mm), puis lissés.
   - Les doigts sont courts et arrondis, ouverts en léger éventail, avec des espaces visibles.
   - Le pouce part du bord de la paume, vers l'avant.
   - La main est 18 % plus grande que le premier essai, pour rester lisible de loin, comme sur la référence.
3. **Un squelette des doigts.** Chaque main a un os de main, puis deux phalanges par doigt, pouce compris (22 os pour
   les deux mains). Les os sont orientés pour que la flexion de chaque doigt soit une rotation autour de son axe X.
   Le pouce se replie vers la paume, ce qui permet l'opposition. Chaque doigt s'anime séparément.
4. **Des poids calculés pour ne pas déformer les doigts voisins.**
   - La paume ne suit que l'os de la main, avec un fondu vers l'avant-bras au poignet.
   - Chaque doigt ne prend que ses propres sommets, avec un fondu à chaque articulation.
   - Résultat : le poing se ferme sans qu'un doigt entraîne son voisin ni froisse la paume.
5. **Bras pilotés par cinématique inverse.** Le bras et l'avant-bras amènent le poignet sur une cible. La main recopie
   l'orientation de cette cible. On place donc la main dans l'espace, et le coude suit.
6. **Le contour blanc.**
   - Celui du bras s'efface sur les derniers centimètres avant le poignet : il traversait la paume quand la main
     pivotait.
   - Le poignet de la main a été aplati à l'épaisseur de la paume : il formait une bosse dont le bord dessinait une
     ligne en arc.

## Tests
- **A, main ouverte face à la caméra :** les cinq doigts sont séparés et visibles (planche, en haut à gauche).
- **B, fermeture :** la main ouverte, puis à demi fermée, puis en poing, sans que les doigts traversent la paume.
- **C, clavier :** Léa est assise, paumes vers le bas et poignets à peine relevés.
  - Les doigts sont calés pour toucher le dessus des touches.
  - À chaque frappe, la touche réellement atteinte par le bout du doigt s'enfonce de 4,5 mm puis remonte.
  - Les mains dérivent légèrement d'une rangée à l'autre.
- **D, téléphone :**
  - Le téléphone est posé écran contre le bureau. La main s'en approche, s'ouvre et le saisit en recourbant les
    doigts sur le bord.
  - Elle le soulève en retournant la paume : l'écran (l'interface validée, en mode sombre) se retrouve face à Léa.
  - Le pouce tape trois fois, puis la main le repose à sa place.
  - Le téléphone est attaché à la main uniquement entre la prise et la pose, pour qu'il ne flotte pas.

## Limites constatées
- **Traits à la base des doigts :** on voit un léger trait blanc entre la paume et la base des doigts, dû au contour
  dans ce creux. Il sépare les doigts, mais n'existe pas sur la référence 2D.
- **Téléphone :** il est tenu de côté, et l'écran en mode sombre se lit peu dans ce plan. Le pouce qui tape est vu de
  derrière l'épaule, donc petit. Un gros plan dédié serait nécessaire pour le film.
- **Contour du corps en position assise :** des traits apparaissent aux plis des épaules et des bras. C'est une limite
  du contour par coque inversée sur un corps qui se plie.
- **Clavier :** la caméra montre Léa en entier ; les doigts sont donc petits à l'image. C'est la planche qui montre les
  mains en gros plan.
- **Doigts :** pas d'écartement latéral animé. Seules la flexion et l'opposition du pouce sont prévues.
