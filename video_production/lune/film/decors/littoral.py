"""Littoral : Plage (bloc 3 « Dans les océans », puis bloc 4). Image existante film2d/images/decor_plage.png (aucune
nouvelle génération). Mouvement en code : reflets qui scintillent sur l'eau, écume qui avance et recule doucement,
légère brume de chaleur à l'horizon. Plus tard : niveau d'eau réglable (bloc 4)."""
from pathlib import Path

import cv2
import numpy as np

from decors.commun import load_rgb, noise_tex

LUNE = Path(__file__).resolve().parents[2]


class Plage:
    def __init__(self, bloc):
        self.img = load_rgb(LUNE / "film2d/images/decor_plage.png")
        h, w = self.img.shape[:2]
        r, g, b = (self.img[..., k] for k in range(3))
        yy = np.mgrid[0:h, 0:w][0]
        water = ((b - r) > 14) & (yy > h * 0.22) & (yy < h * 0.75)                  # la mer : bleutée, sous l'horizon
        water = cv2.morphologyEx(water.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
        self.water = cv2.GaussianBlur(water.astype(np.float32), (0, 0), 4)
        foam = (r > 228) & (g > 228) & (b > 228) & (yy > h * 0.36) & (yy < h * 0.75)                   # l'écume blanche du bord
        self.foam = cv2.GaussianBlur(foam.astype(np.float32), (0, 0), 3)
        self.glint = noise_tex(h // 4, w // 4, 3, 21)

    def render(self, t, shot, bloc):
        f = self.img.copy()
        h, w = f.shape[:2]
        sh = int(6 * np.sin(t * 0.9)), int(4 * np.sin(t * 0.7 + 1))               # reflets qui bougent
        g = np.roll(np.roll(self.glint, sh[0] + int(t * 9), 1), sh[1], 0)
        g = cv2.resize(np.clip((g - 0.72) / 0.12, 0, 1) ** 2, (w, h))
        a = (g * self.water * (0.35 + 0.15 * np.sin(t * 2.3)))[..., None]
        f = f * (1 - a) + np.array([245, 250, 255], np.float32) * a
        dy = 6 * np.sin(2 * np.pi * t / 4.2)                                        # l'écume avance et recule
        M = np.float32([[1, 0, -dy * 0.6], [0, 1, dy]])
        fo = cv2.warpAffine(self.foam, M, (w, h))[..., None] * 0.5
        f = f * (1 - fo) + 250 * fo
        return f
