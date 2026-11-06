"""Plan test (4 s) : Calern de jour, rendu image par image.

    python3 plan_calern.py      → test/plan_calern.mp4

- le collègue marche vraiment (pieds posés au sol, genoux, déroulé du pied, bras qui se balance, buste qui monte et descend)
- Léa est assise sur LA chaise du décor (la sienne est retirée) : respiration, tête, mains qui tapent, clignement
- écrans animés (carte du ciel qui tourne, courbe qui se trace, valeurs qui changent)
- nuages qui passent dans l'ouverture du dôme, poussière dans la lumière, lente avancée de la caméra
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from pieces import Collegue, Lea  # noqa: E402

FPS, DUR = 30, 4.0
OUT_W, OUT_H = 1920, 1080
decor = np.array(Image.open(HERE.parent / "images/decor_calern_jour.png").convert("RGB")).astype(np.float32)
DH, DW = decor.shape[:2]
sky = (np.array(Image.open(HERE / "masque_fond.png")) > 0)
yy = np.arange(DH)[:, None].astype(np.float32)
from pieces import fill_holes  # noqa: E402
sky = fill_holes(sky) & (np.arange(DW)[None, :] > 1000)
sky_a = cv2.GaussianBlur(sky.astype(np.float32), (5, 5), 0) * np.clip((700 - yy) / 260, 0, 1)

# --- nuages : bruit basse fréquence, seuil doux
rng = np.random.default_rng(3)
noise = cv2.GaussianBlur(rng.random((260, 1400)).astype(np.float32), (0, 0), 14)
noise = cv2.resize(noise, (5600, 520), interpolation=cv2.INTER_CUBIC)
noise = (noise - noise.min()) / (noise.max() - noise.min())
cloud = np.clip((noise - 0.56) / 0.16, 0, 1) ** 1.5
cloud = cv2.GaussianBlur(cloud, (0, 0), 6)

# --- écrans (coins dans le décor, sens horaire depuis le haut gauche)
SCREENS = [np.float32([(2143, 941), (2307, 933), (2313, 1050), (2145, 1046)]),
           np.float32([(2342, 923), (2515, 915), (2516, 1058), (2342, 1055)])]
NAVY = (20, 30, 46)


def screen_left(t):
    w, h = 420, 350
    im = np.zeros((h, w, 3), np.uint8); im[:] = NAVY
    c = (210, 180)
    for r in (60, 110, 160):
        cv2.circle(im, c, r, (60, 90, 120), 1, cv2.LINE_AA)
    cv2.line(im, (c[0] - 170, c[1]), (c[0] + 170, c[1]), (50, 75, 100), 1); cv2.line(im, (c[0], 10), (c[0], 340), (50, 75, 100), 1)
    srng = np.random.default_rng(11)
    pts = srng.random((90, 2)) * [160, 2 * np.pi]; mags = srng.random(90)
    for (rr, th), m in zip(pts, mags):
        a = th + t * 0.06
        x, y = int(c[0] + rr * np.cos(a)), int(c[1] + rr * np.sin(a))
        cv2.circle(im, (x, y), 1 + int(m * 2.2), (200, 225, 245), -1, cv2.LINE_AA)
    k = int(t * 2) % 2
    tx, ty = int(c[0] + 70 * np.cos(0.9 + t * 0.06)), int(c[1] + 70 * np.sin(0.9 + t * 0.06))
    cv2.rectangle(im, (tx - 12, ty - 12), (tx + 12, ty + 12), (90, 220, 160) if k else (60, 160, 120), 2)
    cv2.putText(im, f"RA 14h{29 + int(t):02d}m  DEC -60.{int(t * 7) % 10}", (12, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 200, 230), 1, cv2.LINE_AA)
    return im


def screen_right(t):
    w, h = 460, 400
    im = np.zeros((h, w, 3), np.uint8); im[:] = NAVY
    cv2.rectangle(im, (14, 14), (w - 14, 190), (60, 90, 120), 1)
    n = int(40 + t * 55)
    xs = np.linspace(20, w - 20, 260)[: min(n, 260)]
    ys = 110 + 40 * np.sin(xs / 37 + 0.4) * np.exp(-((xs - 230) / 260) ** 2) + 8 * np.sin(xs / 7)
    cv2.polylines(im, [np.stack([xs, ys], 1).astype(np.int32)], False, (120, 210, 240), 2, cv2.LINE_AA)
    if len(xs):
        cv2.circle(im, (int(xs[-1]), int(ys[-1])), 4, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.rectangle(im, (14, 210), (220, 386), (60, 90, 120), 1); cv2.rectangle(im, (236, 210), (w - 14, 386), (60, 90, 120), 1)
    for i in range(9):
        hgt = 30 + 60 * abs(np.sin(i * 1.3 + t * 2.1))
        cv2.rectangle(im, (24 + i * 21, 376 - int(hgt)), (38 + i * 21, 376), (80, 170, 220), -1)
    xs2 = np.linspace(246, w - 24, 80); ys2 = 300 - 60 * (xs2 - 246) / 200 + 6 * np.sin(xs2 / 9 + t * 4)
    cv2.polylines(im, [np.stack([xs2, ys2], 1).astype(np.int32)], False, (150, 230, 170), 2, cv2.LINE_AA)
    cv2.putText(im, f"{1.0 + 0.0021 * np.sin(t * 3):.4f}", (250, 236), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 230, 245), 1, cv2.LINE_AA)
    return im


def warp_screen(frame, img, quad):
    h, w = img.shape[:2]
    M = cv2.getPerspectiveTransform(np.float32([(0, 0), (w, 0), (w, h), (0, h)]), quad)
    x0, y0 = quad.min(0).astype(int) - 2; x1, y1 = quad.max(0).astype(int) + 2
    M2 = np.array([[1, 0, -x0], [0, 1, -y0], [0, 0, 1]]) @ M
    sz = (x1 - x0, y1 - y0)
    warped = cv2.warpPerspective(img.astype(np.float32), M2, sz, flags=cv2.INTER_AREA)
    mask = cv2.warpPerspective(np.ones((h, w), np.float32), M2, sz, flags=cv2.INTER_LINEAR)[..., None]
    glow = 1.0 + 0.03 * np.sin(sz[0])                                  # écran légèrement lumineux
    region = frame[y0:y1, x0:x1]
    region[:] = region * (1 - mask) + warped * glow * mask


def sprite(frame, rgba, x, y):
    h, w = rgba.shape[:2]
    x, y = int(round(x)), int(round(y))
    X0, Y0, X1, Y1 = max(0, x), max(0, y), min(DW, x + w), min(DH, y + h)
    if X0 >= X1 or Y0 >= Y1:
        return
    s = rgba[Y0 - y:Y1 - y, X0 - x:X1 - x].astype(np.float32)
    a = s[..., 3:4] / 255
    frame[Y0:Y1, X0:X1] = frame[Y0:Y1, X0:X1] * (1 - a) + s[..., :3] * a


# --- poussière dans la lumière
dust = rng.random((70, 5)) * [1500, 900, 1, 1, 1] + [800, 380, 0, 0, 0]


def main():
    col, lea = Collegue(), Lea()
    LEA_S, LEA_X, LEA_Y = 0.345, 1862, 1262 - 1415 * 0.345
    COL_S, P = 0.33, 1.0
    S_full = 255.0
    S, v = S_full / COL_S, S_full / COL_S / P                      # foulée et vitesse en px natifs
    X_START = 1790.0                                                # hanche, px décor
    tmp = HERE / ".frames"; tmp.mkdir(exist_ok=True)
    n = int(FPS * DUR)
    only = [int(a) for a in sys.argv[1:]]
    for i in (only or range(n)):
        t = i / FPS
        f = decor.copy()
        # nuages
        off = int(t * 30) % 2800
        cl = np.zeros((DH, DW), np.float32); cl[0:520, :] = cloud[:, off:off + DW]
        a = cl * sky_a * 0.55
        f = f * (1 - a[..., None]) + np.array([246, 250, 255], np.float32) * a[..., None]
        warp_screen(f, screen_left(t), SCREENS[0]); warp_screen(f, screen_right(t), SCREENS[1])
        sprite(f, lea.frame(t).rgba(LEA_S), LEA_X, LEA_Y)
        hip_x = X_START - S_full * t / P
        cv = col.frame(t, P, S, v, 0.0, 0.0)
        spr = cv.rgba(COL_S)
        sprite(f, spr, hip_x - 750 * COL_S, 1440 - 1925 * COL_S)
        # poussière
        for k, (x, y, ph, sz, br) in enumerate(dust):
            px = x + 18 * np.sin(t * 0.4 + ph * 6) + t * 6; py = y - t * (4 + 6 * br) + 10 * np.sin(t * 0.7 + ph * 9)
            al = 0.10 + 0.18 * br * (0.6 + 0.4 * np.sin(t * 2 + ph * 7))
            r = 1.6 + sz * 2.4
            x0, y0 = int(px - 6), int(py - 6)
            if 0 <= x0 < DW - 13 and 0 <= y0 < DH - 13:
                g = np.exp(-(((np.arange(13) - 6 - (px - int(px)))[None, :] ** 2 + (np.arange(13) - 6 - (py - int(py)))[:, None] ** 2) / (r * r)))
                f[y0:y0 + 13, x0:x0 + 13] = f[y0:y0 + 13, x0:x0 + 13] * (1 - g[..., None] * al) + 255 * g[..., None] * al
        # caméra : fenêtre 2052×1154 qui avance doucement (×1,04) et suit un peu le collègue
        u = t / DUR; e = u * u * (3 - 2 * u)
        zoom = 1.0 + 0.04 * e
        cx, cy = 1726 - 60 * e, 917
        wv, hv = 2052 / zoom, 1154 / zoom
        sx = OUT_W / wv
        M = np.float32([[sx, 0, -(cx - wv / 2) * sx], [0, sx, -(cy - hv / 2) * sx]])
        out = cv2.warpAffine(np.clip(f, 0, 255).astype(np.uint8), M, (OUT_W, OUT_H), flags=cv2.INTER_AREA)
        Image.fromarray(out).save(tmp / f"{i:04d}.png")
        if i % 30 == 0:
            print("image", i, flush=True)
    if only:
        return
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(tmp / "%04d.png"), "-c:v", "libx264",
                    "-crf", "17", "-pix_fmt", "yuv420p", str(HERE / "plan_calern_muet.mp4")], check=True)


if __name__ == "__main__":
    main()
