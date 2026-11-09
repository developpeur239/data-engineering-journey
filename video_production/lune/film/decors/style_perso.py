"""Style des personnages du film, d'après Léa (bloc 2) : corps et visage sombres, MAIS cheveux dans leur couleur,
yeux blancs ovales, traits fins gris (sourcils, bouche, plis des vêtements, contours intérieurs), un détail de couleur
(écharpe de Léa, seau rouge, cartables…), liseré clair autour. Appliqué à un dessin en couleur détouré (planche générée).

    out = style_lea(rgb, sil)   # rgb : dessin (h, w, 3) float ; sil : masque de la silhouette (h, w) uint8 0/1
"""
import cv2
import numpy as np

NOIR = np.array([22, 22, 25], np.float32)                     # le noir des personnages (Léa)
TRAIT = np.array([150, 158, 172], np.float32)                 # traits intérieurs gris clair
BLANC = np.array([246, 246, 242], np.float32)


def _comp(mask, min_area):
    n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
    keep = np.zeros(mask.shape, np.uint8)
    for k in range(1, n):
        if st[k, 4] >= min_area:
            keep[lab == k] = 1
    return keep


def masks(rgb, sil):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = rgb.mean(2)
    hair = (r > 50) & (r < 150) & (r - g > 16) & (g - b > 4) & (lum < 115) & (sil > 0)          # cheveux bruns / châtains
    hair = _comp(cv2.morphologyEx(hair.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8)), 1500)
    skin = (r > 205) & (g > 150) & (b > 120) & (r - b > 40) & (sil > 0)
    skin = cv2.morphologyEx(skin.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    dark = ((lum < 70) & (sil > 0)).astype(np.uint8)
    ys = np.where(sil.any(1))[0]; top, bottom = ys.min(), ys.max()
    head = np.zeros_like(dark); head[: int(top + 0.33 * (bottom - top))] = 1                   # la tête : le tiers du haut
    thick = cv2.morphologyEx(dark, cv2.MORPH_OPEN, np.ones((13, 13), np.uint8))                 # aplats sombres (≠ traits)
    dhair = _comp(thick & head & (sil > 0), 1500)                                              # cheveux noirs : à peine plus clairs
    eyes = []                                                                                  # points sombres entourés de peau
    n, lab, st, cen = cv2.connectedComponentsWithStats(dark)
    for k in range(1, n):
        x, y, w, h, a = st[k]
        if 40 < a < 2500 and w < 70 and h < 90 and head[int(cen[k][1]), int(cen[k][0])]:
            reg = (lab[max(0, y - 12):y + h + 12, max(0, x - 12):x + w + 12] == k).astype(np.uint8)
            ring = cv2.dilate(reg, np.ones((15, 15), np.uint8)) - reg
            sk = skin[max(0, y - 12):y + h + 12, max(0, x - 12):x + w + 12]
            if ring.sum() and (sk[ring > 0] > 0).mean() > 0.75:
                eyes.append((cen[k], max(w, h)))
    inner = cv2.erode(sil.astype(np.uint8), np.ones((9, 9), np.uint8))
    lines = (dark - thick) & inner & (cv2.dilate(hair | dhair, np.ones((5, 5), np.uint8)) == 0)
    return hair, dhair, lines, eyes


def style_lea(rgb, sil):
    hair, dhair, lines, eyes = masks(rgb, sil)
    out = np.zeros(rgb.shape, np.float32) + NOIR
    da = cv2.GaussianBlur(dhair.astype(np.float32), (0, 0), 0.8)[..., None]
    out = out * (1 - da) + np.array([50, 52, 62], np.float32) * da
    la = cv2.GaussianBlur(lines.astype(np.float32), (0, 0), 0.7)[..., None] * 0.6
    out = out * (1 - la) + TRAIT * la
    ha = cv2.GaussianBlur(hair.astype(np.float32), (0, 0), 0.8)[..., None]
    lum = rgb.mean(2, keepdims=True)
    hair_col = np.clip(rgb * 1.08 + (rgb - lum) * 0.25, 0, 255)                                # un peu plus vif, comme Léa
    out = out * (1 - ha) + hair_col * ha
    em = np.zeros(sil.shape, np.float32)
    for (cx, cy), s in eyes:                                                                    # yeux : ovales blancs, verticaux
        cv2.ellipse(em, (int(cx), int(cy)), (max(4, int(s * 0.55)), max(7, int(s * 1.0))), 0, 0, 360, 1, -1, cv2.LINE_AA)
    em = cv2.GaussianBlur(em, (0, 0), 0.7)[..., None]
    return out * (1 - em) + BLANC * em
