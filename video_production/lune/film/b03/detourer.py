"""Détoure la planche b03/enfants.png (fond gris uni) en 4 calques RGBA : enf_vert, parent_fille, enf_rayures, enf_gris.
Les trous intérieurs sont remplis (vêtements gris clair proches du fond), sauf les grands trous couleur du fond (entre les jambes)."""
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
im = np.asarray(Image.open(HERE / "enfants.png").convert("RGB")).astype(np.float32)
bg = np.median(np.concatenate([im[:40].reshape(-1, 3), im[:, :40].reshape(-1, 3)]), 0)
d = np.abs(im - bg).max(2)
m = cv2.morphologyEx((d > 34).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
for name, (x0, x1) in {"enf_vert": (200, 560), "parent_fille": (660, 1700), "enf_rayures": (1780, 2110), "enf_gris": (2170, 2550)}.items():
    sub = m[:, x0:x1]
    n, lab, st, _ = cv2.connectedComponentsWithStats(sub)
    keep = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
    ff = keep.copy(); h, w = ff.shape
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    holes = (1 - ff).astype(np.uint8)
    hn, hl, hs, _ = cv2.connectedComponentsWithStats(holes)
    for k in range(1, hn):
        reg = hl == k
        if hs[k, 4] > 1500 and d[:, x0:x1][reg].mean() < 14:              # trou couleur du fond : on le laisse vide
            holes[reg] = 0
    keep = keep | holes
    a = cv2.GaussianBlur(keep.astype(np.float32), (0, 0), 1.0)
    ys, xs = np.where(keep)
    rgba = np.dstack([im[:, x0:x1], a[..., None] * 255])[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    Image.fromarray(rgba.astype(np.uint8)).save(HERE / f"{name}.png")
    print(name, rgba.shape)
