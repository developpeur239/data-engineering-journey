"""Outils communs aux décors : nuages, brume, poussière, masque de ciel, déformation locale, fenêtres allumées."""
import cv2
import numpy as np
from PIL import Image

rng = np.random.default_rng(7)


def noise_tex(h, w, sig, seed):
    r = np.random.default_rng(seed)
    n = np.zeros((h, w), np.float32)
    for k, wt in ((1, 1.0), (2, 0.5), (4, 0.25)):
        o = cv2.GaussianBlur(r.random((h // (8 // k) + 1, w // (8 // k) + 1)).astype(np.float32), (0, 0), sig / (8 // k) * k)
        n += cv2.resize(o, (w, h), interpolation=cv2.INTER_CUBIC) * wt
    return (n - n.min()) / (n.max() - n.min())


_r = np.random.default_rng(3)                               # voiles de nuages : longs, fins, horizontaux (défilent en x)
CLOUD = np.zeros((512, 4096), np.float32)
for (hh, ww), sx, sy, wt in (((96, 768), 9, 1.6, 1.0), ((192, 1536), 9, 1.8, 0.45)):
    o = cv2.GaussianBlur(_r.random((hh, ww)).astype(np.float32), (0, 0), sigmaX=sx, sigmaY=sy)
    CLOUD += cv2.resize(o, (4096, 512), interpolation=cv2.INTER_CUBIC) * wt
CLOUD = (CLOUD - CLOUD.min()) / (CLOUD.max() - CLOUD.min())
CLOUD = cv2.GaussianBlur(np.clip((CLOUD - 0.58) / 0.2, 0, 1) ** 1.8, (0, 0), 3)
FOG = noise_tex(400, 4096, 40, 9)
DUST = rng.random((90, 4))


def dust(f, t, box, n=60, alpha=0.22):
    x0, y0, x1, y1 = box
    for k, (a, b, c, d) in enumerate(DUST[:n]):
        px = x0 + (a * (x1 - x0) + 14 * np.sin(t * 0.35 + c * 6) + t * 4) % (x1 - x0)
        py = y0 + (b * (y1 - y0) - t * (3 + 5 * d) + 9 * np.sin(t * 0.6 + c * 9)) % (y1 - y0)
        al = alpha * (0.4 + 0.6 * d) * (0.65 + 0.35 * np.sin(t * 1.7 + c * 7))
        r = 1.8 + 2.6 * c
        ix, iy = int(px), int(py)
        g = np.exp(-(((np.arange(15) - 7 - (px - ix))[None, :] ** 2 + (np.arange(15) - 7 - (py - iy))[:, None] ** 2) / (r * r)))[..., None]
        reg = f[iy - 7:iy + 8, ix - 7:ix + 8]
        if reg.shape[:2] == (15, 15):
            reg[:] = reg * (1 - g * al) + np.array([235, 242, 255], np.float32) * g * al


def sky_mask(img, ylim, xr=(0, 99999)):
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    lum = (r + g + b) / 3
    hh, ww = lum.shape
    yy, xx = np.mgrid[0:hh, 0:ww]
    m = (((b - r > 6) & (lum < 120)) | ((lum > 175) & (np.abs(b - r) < 40))) & (yy < ylim) & (xx >= xr[0]) & (xx < xr[1])
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.5)


_CL = {}


def clouds(f, mask, xoff, strength, y0=0):
    h = mask.shape[0]
    w = f.shape[1]
    if h not in _CL:
        _CL[h] = cv2.resize(CLOUD, (CLOUD.shape[1], h))
    xo = int(xoff) % (CLOUD.shape[1] - w)
    c = _CL[h][:, xo:xo + w]
    a = (c * mask * strength)[..., None]
    f[y0:y0 + h] = f[y0:y0 + h] * (1 - a * 0.42) + np.array([150, 160, 178], np.float32) * a * 0.42




def warp_local(img, A, shape, pad=4):
    """warpAffine limité au rectangle d'arrivée (bien plus rapide que sur toute l'image)."""
    h, w = img.shape[:2]
    pts = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float32) @ A.T
    x0, y0 = np.floor(pts.min(0)).astype(int) - pad; x1, y1 = np.ceil(pts.max(0)).astype(int) + pad
    x0, y0 = max(0, x0), max(0, y0); x1, y1 = min(shape[1], x1), min(shape[0], y1)
    if x0 >= x1 or y0 >= y1:
        return None, 0, 0
    A2 = A.copy(); A2[0, 2] -= x0; A2[1, 2] -= y0
    return cv2.warpAffine(img, A2, (x1 - x0, y1 - y0), flags=cv2.INTER_AREA), x0, y0


def load_rgb(p):
    return np.asarray(Image.open(p).convert("RGB")).astype(np.float32)


def load_rgba(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.float32)
