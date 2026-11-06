"""Détoure les poses générées sur fond magenta (#FF00FF) : fond transparent, bords doux, sans reflet magenta."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage

for name in sys.argv[1:]:
    src = Path("images") / f"{name}.png"; dst = Path("images") / f"{name}_cut.png"
    a = np.asarray(Image.open(src).convert("RGB")).astype(float) / 255
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    mag = np.clip((np.minimum(r, b) - g - 0.2) * 2.0, 0, 1)      # 1 = magenta pur ; le rouge (bleu faible) n'est pas touché
    alpha = 1 - mag
    lab, n = ndimage.label(alpha > 0.5)                           # garde le personnage (la plus grande zone)
    if n:
        sizes = ndimage.sum(np.ones_like(alpha), lab, range(1, n + 1)); keep = lab == (1 + int(np.argmax(sizes)))
        keep = ndimage.binary_fill_holes(keep); alpha = np.where(ndimage.binary_dilation(keep, iterations=2), alpha, 0)
    edge = ndimage.binary_dilation(alpha < 0.5, iterations=20)         # bande de bord, côté personnage
    rgb = a.copy(); spill = (np.minimum(r, b) > g + 0.03) & edge          # reflet magenta : seulement sur les bords détourés
    lum = np.maximum(g, (r + g + b) / 3)   # le contour blanc teinté de rose redevient blanc cassé
    rgb[..., 0] = np.where(spill, np.minimum(r, lum + 0.02), r); rgb[..., 1] = np.where(spill, lum, g); rgb[..., 2] = np.where(spill, np.minimum(b, lum + 0.02), b)
    out = np.dstack([rgb, alpha]); ys, xs = np.nonzero(alpha > 0.5)
    Image.fromarray((out * 255).astype(np.uint8), "RGBA").crop((xs.min() - 4, ys.min() - 4, xs.max() + 5, ys.max() + 5)).save(dst)
    print("détouré", dst, Image.open(dst).size)
