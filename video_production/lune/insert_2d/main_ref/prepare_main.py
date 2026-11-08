"""Prépare la silhouette de main générée : ongles retirés, séparations des doigts gardées, fond transparent.
    python3 prepare_main.py main_index.png main_index_silhouette.png"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

src, dst = sys.argv[1], sys.argv[2]
im = np.asarray(Image.open(src).convert("L")).astype(float)
black = im < 128
lab, n = ndimage.label(~black)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
filled = kept = 0
for i, sl in enumerate(ndimage.find_objects(lab), 1):
    if i in border or sl is None:
        continue
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    area = (lab[sl] == i).sum(); elong = max(h, w) / max(1, min(h, w))
    if area < 9000 and elong < 3.2:      # ongles : petites boucles fermées et arrondies
        black[lab == i] = True; filled += 1
    else:
        kept += 1
# arcs d'ongles encore ouverts sur le fond : on referme le noir, seulement autour du bout de l'index et du pouce
yy, xx = np.mgrid[0:black.shape[0], 0:black.shape[1]]
closed = ndimage.binary_closing(black, structure=np.ones((17, 17)))
for cx, cy in ((450, 430), (440, 925)):
    zone = (xx - cx) ** 2 + (yy - cy) ** 2 < 130 ** 2
    black[zone] = closed[zone] | black[zone]
alpha = (ndimage.gaussian_filter(black.astype(float), 0.8) * 255).clip(0, 255).astype(np.uint8)
rgba = np.zeros((*black.shape, 4), np.uint8); rgba[..., :3] = 10; rgba[..., 3] = alpha
Image.fromarray(rgba, "RGBA").save(dst)
ys, xs = np.nonzero(black); k = (xs + ys).argmin()
print(f"ongles retirés : {filled} ; séparations gardées : {kept} ; bout de l'index : {xs[k]} {ys[k]}")
