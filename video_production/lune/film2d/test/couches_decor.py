"""Sépare le décor de Calern (jour) en couches : fond vu par les ouvertures (ciel, collines) et salle.
Le fond est prolongé sous la salle (inpainting) pour que le décalage de parallaxe ne révèle jamais de trou."""
from pathlib import Path
import numpy as np, cv2
from PIL import Image

HERE = Path(__file__).resolve().parent
src = np.array(Image.open(HERE.parent / "images/decor_calern_jour.png").convert("RGB")).astype(np.int16)
r, g, b = src[..., 0], src[..., 1], src[..., 2]
H, W = r.shape
zone = np.zeros((H, W), np.uint8)
cv2.fillPoly(zone, [np.array([(1040, 0), (1720, 0), (1650, 760), (1100, 770)])], 1)      # ciel entre les deux moitiés du dôme
cv2.rectangle(zone, (215, 740), (470, 900), 1, -1)                                         # ciel de la porte
hsv = cv2.cvtColor(src.astype(np.uint8), cv2.COLOR_RGB2HSV_FULL).astype(np.float32)   # teinte 0–255
hue, sat, val = hsv[..., 0] * 360 / 255, hsv[..., 1] / 255, hsv[..., 2] / 255
bg = (hue > 178) & (hue < 222) & (sat > 0.11) & (val > 0.74)          # ciel : bleu clair saturé (le télescope blanc est exclu)
m = (bg & (zone > 0)).astype(np.uint8)
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
Image.fromarray(m * 255).save(HERE / "masque_fond.png")
# fond : on remplit tout ce qui n'est pas « fond » autour des ouvertures (bande de 60 px), à mi-résolution
half = cv2.resize(src.astype(np.uint8), (W // 2, H // 2), interpolation=cv2.INTER_AREA)
mh = cv2.resize(m, (W // 2, H // 2), interpolation=cv2.INTER_NEAREST)
hole = ((mh == 0) & (cv2.dilate(mh, np.ones((61, 61), np.uint8)) > 0)).astype(np.uint8)
fill = cv2.inpaint(cv2.cvtColor(half, cv2.COLOR_RGB2BGR), hole, 9, cv2.INPAINT_TELEA)
fill = cv2.cvtColor(cv2.resize(fill, (W, H), interpolation=cv2.INTER_CUBIC), cv2.COLOR_BGR2RGB)
fond = np.where(m[..., None] > 0, src.astype(np.uint8), fill)
Image.fromarray(fond).save(HERE / "couche_fond.png")
a = cv2.GaussianBlur((1 - m).astype(np.float32), (3, 3), 0)
salle = np.dstack([src.astype(np.uint8), (a * 255).astype(np.uint8)])
Image.fromarray(salle, "RGBA").save(HERE / "couche_salle.png")
print("fond", m.mean().round(3))
