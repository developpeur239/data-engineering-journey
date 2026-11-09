"""Le collègue (film2d/images/collegue_marche_cut.png, déjà généré) au style de Léa : on retire le gros contour blanc
de l'ancien design et on pose le liseré fin et discret du film (2 px, faible opacité)."""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from b03.detourer import CONTOUR, CONTOUR_A, CONTOUR_PX  # noqa: E402

im = np.asarray(Image.open(HERE.parents[1] / "film2d/images/collegue_marche_cut.png").convert("RGBA")).astype(np.float32)
a = (im[..., 3] > 128).astype(np.uint8)
white = im[..., :3].min(2) > 170
sil = cv2.erode(a, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15)))           # sans l'ancien contour blanc épais
n, lab, st, _ = cv2.connectedComponentsWithStats(sil)
sil = (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8)
rgb = np.zeros(im.shape[:2] + (3,), np.float32) + np.array([22, 22, 25], np.float32)
lines = cv2.erode((white & (sil > 0)).astype(np.uint8), np.ones((3, 3), np.uint8))  # lignes intérieures : traits gris fins
la = cv2.GaussianBlur(lines.astype(np.float32), (0, 0), 0.8)[..., None] * 0.7
rgb = rgb * (1 - la) + np.array([150, 158, 172], np.float32) * la
alpha = cv2.GaussianBlur(sil.astype(np.float32), (0, 0), 0.8)
ringa = cv2.GaussianBlur(cv2.dilate(sil, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * CONTOUR_PX + 1,) * 2)).astype(np.float32), (0, 0), 0.8)
ra = np.clip(ringa - alpha, 0, 1) * CONTOUR_A
A = alpha + ra
out = (rgb * alpha[..., None] + CONTOUR * ra[..., None]) / np.maximum(A, 1e-6)[..., None]
Image.fromarray(np.dstack([out, A * 255]).clip(0, 255).astype(np.uint8)).save(HERE / "collegue.png")
print("collegue.png", out.shape)
