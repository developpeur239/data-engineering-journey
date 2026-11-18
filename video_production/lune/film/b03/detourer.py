"""Détoure la planche b03/enfants.png (fond gris uni) en 4 calques RGBA, au style des personnages du film :
silhouette NOIRE pleine (comme Léa), contour fin et discret, et UN SEUL détail de couleur par personnage.

  enf_vert      cartable vert (et sa gourde rouge)
  parent_fille  le parent : sacoche moutarde ; la fillette : cartable jaune (deux personnes, un seul calque : ils se tiennent la main)
  enf_rayures   cartable bleu
  enf_gris      cartable rouge brique (recoloré : il était gris)
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from decors.style_perso import style_lea  # noqa: E402

HERE = Path(__file__).resolve().parent
NOIR = np.array([22, 22, 25], np.float32)                      # le noir des personnages (Léa)
CONTOUR, CONTOUR_A, CONTOUR_PX = np.array([200, 210, 225], np.float32), 0.38, 4

im = np.asarray(Image.open(HERE / "enfants.png").convert("RGB")).astype(np.float32)
bg = np.median(np.concatenate([im[:40].reshape(-1, 3), im[:, :40].reshape(-1, 3)]), 0)
d = np.abs(im - bg).max(2)
m = cv2.morphologyEx((d > 34).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))   # l'ombre grise au sol reste dehors


def fill_holes(k):
    ff = k.copy(); h, w = ff.shape
    cv2.floodFill(ff, np.zeros((h + 2, w + 2), np.uint8), (0, 0), 1)
    return k | (1 - ff)


def largest(k):
    n, lab, st, _ = cv2.connectedComponentsWithStats(k)
    return (lab == 1 + np.argmax(st[1:, 4])).astype(np.uint8) if n > 1 else k


def accent(rgb, box, test):
    """Masque d'un objet de couleur dans un rectangle (coordonnées du calque) : couleur, puis lignes internes avalées."""
    x0, y0, x1, y1 = box
    k = np.zeros(rgb.shape[:2], np.uint8)
    r, g, b = (rgb[y0:y1, x0:x1, c] for c in range(3))
    k[y0:y1, x0:x1] = test(r, g, b, rgb[y0:y1, x0:x1].mean(2)).astype(np.uint8)
    k = cv2.morphologyEx(k, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    near = cv2.dilate(k, np.ones((11, 11), np.uint8))                                      # pas plus loin que la couleur elle-même
    k = cv2.morphologyEx(k, cv2.MORPH_CLOSE, np.ones((17, 17), np.uint8))
    return fill_holes(largest(k)) & near


ACC = {   # nom : [(rectangle, test de couleur, couleur forcée ou None = couleur d'origine)]
    "enf_vert": [((0, 290, 260, 600), lambda r, g, b, l: ((g > r + 5) & (g > b + 15)) | ((r > b + 60) & (r > g + 60)), None)],
    "parent_fille": [((220, 630, 545, 910), lambda r, g, b, l: l < 26, np.array([196, 150, 64], np.float32)),
                     ((800, 650, 1010, 915), lambda r, g, b, l: (r > 170) & (g > 130) & (b < 140), None)],
    "enf_rayures": [((85, 300, 310, 590), lambda r, g, b, l: b > r + 35, None)],
    "enf_gris": [((100, 350, 345, 655), lambda r, g, b, l: (l > 95) & (l < 178), np.array([168, 72, 58], np.float32))],
}

if __name__ == "__main__":
    for name, (x0, x1) in {"enf_vert": (200, 560), "parent_fille": (660, 1700), "enf_rayures": (1780, 2110), "enf_gris": (2170, 2550)}.items():
        keep = largest(m[:, x0:x1].copy())                                                # silhouette pleine…
        holes = fill_holes(keep) - keep
        hn, hl, hs, _ = cv2.connectedComponentsWithStats(holes.astype(np.uint8))
        lowest = np.where(keep.any(1))[0].max()
        for k in range(1, hn):                                                           # … sauf l'écart entre les jambes
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
        for box, test, col in ACC[name]:
            bx = tuple(v + P for v in box)                                              # rectangle : coordonnées du calque sans marge
            a = accent(rgb, bx, test) & sil
            a = cv2.GaussianBlur(a.astype(np.float32), (0, 0), 0.8)[..., None]
            if col is None:
                src = rgb
            else:                                                                        # recolorée : garde les ombres et les lignes
                lum = rgb.mean(2, keepdims=True)
                src = col * np.clip(0.55 + lum / 255, 0.3, 1.25) if name == "enf_gris" else col * np.where(lum < 26, 1.0, 0.55)
            out = out * (1 - a) + src * a
        alpha = cv2.GaussianBlur(sil.astype(np.float32), (0, 0), 0.8)
        ring = cv2.dilate(sil, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * CONTOUR_PX + 1,) * 2)).astype(np.float32)
        ring = cv2.GaussianBlur(ring, (0, 0), 0.8)
        ra = np.clip(ring - alpha, 0, 1) * CONTOUR_A                                       # contour fin, faible opacité
        A = alpha + ra
        rgbo = (out * alpha[..., None] + CONTOUR * ra[..., None]) / np.maximum(A, 1e-6)[..., None]
        Image.fromarray(np.dstack([rgbo, A * 255]).clip(0, 255).astype(np.uint8)).save(HERE / f"{name}.png")
        print(name, rgbo.shape, "décalage", (xa - P, y0 - P))
