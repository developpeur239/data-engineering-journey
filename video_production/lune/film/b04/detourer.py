"""Détoure la planche b04/mere_garcon.png en 4 calques au style des personnages du film (silhouette noire pleine,
contour fin et discret) : mere_dos, mere_accroupie, garcon_dos, garcon_profil. Seul détail de couleur : le SEAU ROUGE
du garçon (le fil rouge du film, plan_rendu_v2 § 4). Même procédé que b03/detourer.py."""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decors.style_perso import style_lea  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from b03.detourer import CONTOUR, CONTOUR_A, CONTOUR_PX, NOIR, fill_holes, largest  # noqa: E402

im = np.asarray(Image.open(HERE / "mere_garcon.png").convert("RGB")).astype(np.float32)
bg = np.median(np.concatenate([im[:40].reshape(-1, 3), im[:, :40].reshape(-1, 3)]), 0)
d = np.abs(im - bg).max(2)
m = cv2.morphologyEx((d > 34).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
RED = lambda r, g, b: (r > g + 70) & (r > b + 70)  # noqa: E731

if __name__ == "__main__":
    for name, (x0, x1) in {"mere_dos": (140, 600), "mere_accroupie": (760, 1450), "garcon_dos": (1600, 2110),
                           "garcon_profil": (2210, 2640)}.items():
        keep = largest(m[:, x0:x1].copy())
        holes = fill_holes(keep) - keep
        hn, hl, hs, _ = cv2.connectedComponentsWithStats(holes.astype(np.uint8))
        lowest = np.where(keep.any(1))[0].max()
        for k in range(1, hn):                                                           # écart entre les jambes : vide
            reg = hl == k
            if hs[k, 4] > 600 and d[:, x0:x1][reg].mean() < 14 and hs[k, 1] > lowest - 0.3 * (lowest - np.where(keep.any(1))[0].min()):
                holes[reg] = 0
        keep = keep | holes
        ys, xs = np.where(keep)
        y0, y1, xa, xb = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        P = CONTOUR_PX + 2
        sil = np.pad(keep[y0:y1, xa:xb], P)
        rgb = np.pad(im[:, x0:x1][y0:y1, xa:xb], ((P, P), (P, P), (0, 0)))
        out = style_lea(rgb, sil.astype(np.uint8))                                       # style de Léa (cheveux, yeux, traits)
        if name.startswith("garcon"):                                                    # le seau rouge (et son anse sombre reste noire)
            a = RED(rgb[..., 0], rgb[..., 1], rgb[..., 2]).astype(np.uint8)
            a = cv2.morphologyEx(a, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
            a = fill_holes(largest(a)) & sil
            a = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 0.8)[..., None]
            out = out * (1 - a) + rgb * a
        alpha = cv2.GaussianBlur(sil.astype(np.float32), (0, 0), 0.8)
        ring = cv2.dilate(sil, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * CONTOUR_PX + 1,) * 2)).astype(np.float32)
        ring = cv2.GaussianBlur(ring, (0, 0), 0.8)
        ra = np.clip(ring - alpha, 0, 1) * CONTOUR_A
        A = alpha + ra
        rgbo = (out * alpha[..., None] + CONTOUR * ra[..., None]) / np.maximum(A, 1e-6)[..., None]
        Image.fromarray(np.dstack([rgbo, A * 255]).clip(0, 255).astype(np.uint8)).save(HERE / f"{name}.png")
        print(name, rgbo.shape)
