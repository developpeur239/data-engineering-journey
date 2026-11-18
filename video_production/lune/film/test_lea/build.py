"""Test Léa (7,5 s) : assise sur sa chaise, elle tape, prend son téléphone, puis lève les yeux vers son écran.

    python3 test_lea/build.py               → test_lea/test_lea.mp4
    python3 test_lea/build.py 30 120 170    → seulement ces images (contrôle)

Méthode : animation 2D « par remplacement ». Le corps vient de l'image validée de Léa (avec SA chaise) ; l'avant-bras
est une pièce articulée au coude ; la main est l'un des 5 dessins de la planche (frappe index, frappe majeur, main
ouverte, prise du téléphone, téléphone tenu), échangés au bon moment : les doigts sont toujours dessinés, jamais
déformés. Un seul contour blanc fin est recalculé autour de la silhouette entière (corps + bras + main).
Décor : fond, clavier et écran de l'image générée ; plateau, caisson et sol complétés en code (formes plates).
"""
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
FILM = HERE.parent
LUNE = FILM.parent
sys.path.insert(0, str(FILM))
from moteur.core import H, W, cam, ease, grade  # noqa: E402

FPS, DUR = 30, 7.5
OUTL = 7                                    # contour blanc (px du décor) : fin
DH = 1760                                   # le décor est prolongé vers le bas (sol) pour voir la chaise en entier

# ------------------------------------------------------------------ décor : fond généré + bureau et sol en code
src = np.asarray(Image.open(HERE / "poste_profil.png").convert("RGB")).astype(np.float32)
SH, SW = src.shape[:2]
DESK_X, TOP, FRONT, BOT, FLOOR = 640, 1126, 1198, 1270, 1645
deco = np.zeros((DH, SW, 3), np.float32)
deco[:SH] = src
yy = np.arange(DH, dtype=np.float32)[:, None]
wall = np.array([24, 29, 38], np.float32); floor = np.array([17, 20, 27], np.float32)
below = (yy >= TOP).repeat(SW, 1)
base = np.where(yy[..., None] < FLOOR, wall * (1 - 0.25 * np.clip((yy[..., None] - TOP) / 500, 0, 1)), floor)
deco = np.where(below[..., None], base * np.ones((1, SW, 1), np.float32), deco)
deco[TOP:BOT, DESK_X:] = src[TOP:BOT, DESK_X:]                                    # plateau + clavier + chant du bureau
deco[TOP:BOT, DESK_X:DESK_X + 10] *= 0.72                                          # bout du plateau
cv2.rectangle(deco, (1960, BOT), (2380, FLOOR), (58, 66, 80), -1)                  # caisson à tiroirs
cv2.rectangle(deco, (1960, BOT), (2380, BOT + 6), (40, 46, 56), -1)
for y in (BOT + 120, BOT + 245):
    cv2.line(deco, (1975, y), (2365, y), (40, 46, 56), 3, cv2.LINE_AA)
    cv2.rectangle(deco, (2130, y - 50), (2210, y - 40), (88, 98, 114), -1)
cv2.line(deco, (0, FLOOR), (SW, FLOOR), (30, 35, 45), 2, cv2.LINE_AA)
deco[SH - 2:SH + 2] = deco[SH - 3:SH - 2]


# ------------------------------------------------------------------ Léa : corps (avec sa chaise), contour retiré
def rgba(p):
    return np.asarray(Image.open(p).convert("RGBA")).astype(np.float32)


lea = rgba(LUNE / "film2d/images/lea_profil_cut.png")
lh, lw = lea.shape[:2]
ly, lx = np.mgrid[0:lh, 0:lw]
white = lea[..., :3].min(2) > 200
solid = (lea[..., 3] > 128) & ~white
chair = ((lx < 152) & (ly > 760)) | ((ly > 1418) & (lx < 690))
forearm = (lx > 575) & (ly > 905) & (ly < 1112)                                      # avant-bras + main d'origine : remplacés
body = solid & ~chair & ~forearm
body = cv2.morphologyEx(body.astype(np.uint8), cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8)) > 0
chair_m = solid & chair
EYE = np.zeros_like(body); EYE[368:452, 640:690] = True
eye_m = EYE & (lea[..., :3].min(2) > 150)                                            # le blanc de l'œil
S = 0.6
X0, Y0 = 450 - 585 * S, TOP - 34 - 1040 * S                                          # coude à 450, juste au-dessus du plateau
ELBOW = np.array([X0 + 585 * S, Y0 + 1040 * S])


def place(img, s, x, y, rot=0.0, pivot=None, shape=(DH, SW)):
    """Image (h, w, c) → toile du décor, mise à l'échelle s, coin haut gauche (x, y), rotation autour du pivot (décor)."""
    M = np.float32([[s, 0, x], [0, s, y]])
    if rot:
        R = cv2.getRotationMatrix2D(tuple(map(float, pivot)), rot, 1.0)
        M = (np.vstack([R, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]]))[:2].astype(np.float32)
    return cv2.warpAffine(img, M, (shape[1], shape[0]), flags=cv2.INTER_LINEAR)


# ------------------------------------------------------------------ mains (planche)
CELS = {n: rgba(HERE / f"cel_{n}.png") for n in ("frappe_index", "frappe_majeur", "main_ouverte", "prise_tel", "tel_tenu", "tel_seul")}
for c in CELS.values():                                                              # reste de rose sur les bords → noir
    sp = (np.minimum(c[..., 0], c[..., 2]) - c[..., 1] > 20)
    c[sp, :3] = 30


def attach(c):
    """Point d'attache = milieu du bord gauche de la manche."""
    a = c[..., 3] > 128
    cols = np.nonzero(a.any(0))[0]; x = cols.min() + 6
    ys = np.nonzero(a[:, x])[0]
    return np.array([x, (ys.min() + ys.max()) / 2.0])


ATT = {n: attach(c) for n, c in CELS.items() if n != "tel_seul"}
CS = 0.42                                                                             # échelle des mains : ≈ 0,75 × la tête
FOREARM = 70                                                                          # coude → début de la manche (px décor)


# ------------------------------------------------------------------ chorégraphie (secondes)
T_BUZZ, T_STOP, T_GRAB, T_LIFT, T_HOLD, T_LOOK = 2.7, 3.25, 3.85, 4.15, 4.95, 6.0
GRAB_ANG, GRAB_DX = 15.0, 55.0                                                       # même longueur de bras qu'en frappe                                                       # pose de la prise


def _screen_box(c):
    """Rectangle de l'écran gris du téléphone dans un dessin (pixels gris moyens)."""
    lum = c[..., :3].mean(2); m = (c[..., 3] > 200) & (lum > 52) & (lum < 120)
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_OPEN, np.ones((7, 7), np.uint8)) > 0
    ys, xs = np.nonzero(m)
    return np.array([xs.min(), ys.min(), xs.max(), ys.max()], float)


def _grab_phone():
    """Où est le téléphone du dessin « prise » (centre de l'écran, largeur) quand la main est en pose de prise."""
    c = CELS["prise_tel"]; at = ATT["prise_tel"]; bx = _screen_box(c)
    ctr = np.array([(bx[0] + bx[2]) / 2, (bx[1] + bx[3]) / 2, 1.0])
    a = np.radians(GRAB_ANG); d = np.array([np.cos(a), np.sin(a)])
    wrist = ELBOW + d * (FOREARM + GRAB_DX)
    M = cv2.getRotationMatrix2D((float(at[0]), float(at[1])), -GRAB_ANG, CS); M[:, 2] += wrist - at
    return M @ ctr, (bx[2] - bx[0]) * CS


_pc, _pw = _grab_phone()
_sb = _screen_box(CELS["tel_seul"])
PHONE_S = _pw / (_sb[2] - _sb[0])                                                     # même taille que dans la main
PHONE_DESK = _pc
TAPS = [0.35 + k * 0.19 + 0.05 * np.sin(k * 2.3) for k in range(int((T_STOP - 0.5) / 0.19))]


def arm_state(t):
    """Angle de l'avant-bras (degrés, 0 = horizontal vers la droite, + = vers le bas), dessin de main, décalage x."""
    if t < T_STOP:                                                                    # frappe : la main se déplace un peu
        k = sum(1 for a in TAPS if a <= t)
        cel = "frappe_index" if k % 2 == 0 else "frappe_majeur"
        near = min((abs(t - a) for a in TAPS), default=1)
        press = np.exp(-(near / 0.045) ** 2)
        return -1.5 + 1.6 * press + 0.8 * np.sin(t * 1.7), cel, 40 + 10 * np.sin(t * 0.9), press
    if t < T_GRAB:                                                                    # la main s'ouvre et va vers le téléphone
        u = ease((t - T_STOP) / (T_GRAB - T_STOP))
        return -1.5 + (GRAB_ANG + 1.5) * u, "main_ouverte", (40 + 10 * np.sin(T_STOP * 0.9)) * (1 - u) + GRAB_DX * u, 0.0
    if t < T_LIFT:                                                                    # prise
        return GRAB_ANG, "prise_tel", GRAB_DX, 0.0
    if t < T_HOLD:                                                                    # elle lève le téléphone vers elle
        u = ease((t - T_LIFT) / (T_HOLD - T_LIFT))
        return GRAB_ANG + (-30.0 - GRAB_ANG) * u, ("prise_tel" if u < 0.45 else "tel_tenu"), GRAB_DX * (1 - u) + 10 * u, 0.0
    return -30.0 + 1.0 * np.sin(t * 2.1), "tel_tenu", 10, 0.0


def look(t):
    """Regard (décalage de l'œil en px natifs) et inclinaison de la tête (degrés)."""
    if t < T_BUZZ + 0.15:
        return (2, 10), 1.5                                                             # vers le clavier
    if t < T_HOLD:
        return tuple(np.array([2, 10]) * (1 - ease((t - T_BUZZ - 0.15) / 0.3)) + np.array([8, 16]) * ease((t - T_BUZZ - 0.15) / 0.3)), 2.5
    if t < T_LOOK:
        return (6, 14), 2.0                                                             # vers le téléphone
    u = ease((t - T_LOOK) / 0.45)
    return (6 * (1 - u) + 9 * u, 14 * (1 - u) - 7 * u), 2.0 - 4.5 * u                  # elle lève les yeux vers l'écran


def frame(i):
    t = i / FPS
    f = deco.copy()
    # téléphone sur le bureau (jusqu'à la prise) ; il vibre et s'allume
    if t < T_GRAB:
        ph = CELS["tel_seul"]; s = PHONE_S
        buzz = 2.5 * np.sin(t * 90) if T_BUZZ < t < T_BUZZ + 0.5 else 0.0
        sc = np.array([(_sb[0] + _sb[2]) / 2, (_sb[1] + _sb[3]) / 2])
        x = PHONE_DESK[0] - sc[0] * s + buzz; y = PHONE_DESK[1] - sc[1] * s
        p = place(ph, s, x, y)
        a = p[..., 3:4] / 255
        f = f * (1 - a) + p[..., :3] * a
        if t > T_BUZZ:                                                                  # l'écran s'allume
            glow = np.zeros(f.shape[:2], np.float32)
            cv2.ellipse(glow, (int(PHONE_DESK[0]), int(PHONE_DESK[1])), (int(_pw * 0.5), 9), 0, 0, 360, 1, -1)
            glow = cv2.GaussianBlur(glow, (0, 0), 14)[..., None] * 0.9 * ease((t - T_BUZZ) / 0.2)
            f = f * (1 - glow) + np.array([190, 235, 255], np.float32) * glow
    # Léa : respiration (le buste se soulève depuis l'assise), tête et regard
    br = 0.006 * np.sin(2 * np.pi * t / 3.6)
    (ex, ey), tilt = look(t)
    body_img = lea.copy()
    yyl = ly.astype(np.float32); xxl = lx.astype(np.float32)
    head = np.clip((760 - yyl) / 120, 0, 1)
    c, s_ = np.cos(np.radians(tilt * head)), np.sin(np.radians(tilt * head))
    px, py = 520.0, 760.0                                                                 # pivot du cou
    mx = px + (xxl - px) * c - (yyl - py) * s_
    my = py + (xxl - px) * s_ + (yyl - py) * c
    my = 1415 + (my - 1415) / (1 + br * (my < 1415))
    body_img = cv2.remap(body_img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR)
    bmask = cv2.remap(body.astype(np.uint8), mx.astype(np.float32), my.astype(np.float32), cv2.INTER_NEAREST) > 0
    emask = cv2.remap(eye_m.astype(np.uint8), mx.astype(np.float32), my.astype(np.float32), cv2.INTER_NEAREST) > 0
    body_img[emask, :3] = 22                                                             # l'œil est redessiné au bon endroit
    eye_shift = np.float32([[1, 0, ex], [0, 1, ey]])
    moved = cv2.warpAffine(emask.astype(np.uint8), eye_shift, (lw, lh), flags=cv2.INTER_NEAREST) > 0
    blink = abs(t - 1.6) < 0.06 or abs(t - 5.4) < 0.06
    if not blink:
        body_img[moved & bmask, :3] = 238
    # silhouettes dans la toile du décor
    tb = np.dstack([body_img[..., :3], np.where(bmask, 255, 0).astype(np.float32)])
    B = place(tb, S, X0, Y0)
    CH = place(np.dstack([lea[..., :3], np.where(chair_m, 255, 0).astype(np.float32)]), S, X0, Y0)
    ang, cel, dx, press = arm_state(t)
    a = np.radians(ang)
    d = np.array([np.cos(a), np.sin(a)])
    el = ELBOW + np.array([0, -br * 300])
    wrist = el + d * (FOREARM + dx * 0.0) + np.array([dx, 0]) * 0.0
    wrist = el + d * FOREARM + np.array([dx * np.cos(a), dx * np.sin(a)])
    arm = np.zeros((DH, SW), np.uint8)
    cv2.line(arm, tuple((el * 4).astype(int)), tuple((wrist * 4).astype(int)), 1, int(64), cv2.LINE_AA, 2)   # avant-bras
    cv2.circle(arm, tuple((el * 4).astype(int)), 4 * 32, 1, -1, cv2.LINE_AA, 2)
    cimg = CELS[cel]; at = ATT[cel]
    Mh = cv2.getRotationMatrix2D((float(at[0]), float(at[1])), -ang, CS)
    Mh[:, 2] += wrist - at
    hand = cv2.warpAffine(cimg, Mh, (SW, DH), flags=cv2.INTER_LINEAR)
    # un seul contour fin autour de la silhouette entière (corps + avant-bras + main) ; pas de contour sur la chaise
    sil = (B[..., 3] > 128) | (arm > 0) | (hand[..., 3] > 128)
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * OUTL + 1, 2 * OUTL + 1))
    ring = cv2.dilate(sil.astype(np.uint8), k) > 0
    ca = CH[..., 3:4] / 255
    f = f * (1 - ca) + CH[..., :3] * ca                                                  # la chaise, derrière elle
    sh = np.zeros((DH, SW), np.float32)                                                  # ombre de contact au sol
    cv2.ellipse(sh, (int(X0 + 420 * S), FLOOR + 4), (int(330 * S), 14), 0, 0, 360, 1, -1)
    sh = cv2.GaussianBlur(sh, (0, 0), 10)[..., None] * 0.55
    f = f * (1 - sh)
    f[ring] = f[ring] * 0.1 + np.array([232, 234, 238], np.float32) * 0.9
    ba = B[..., 3:4] / 255
    f = f * (1 - ba) + B[..., :3] * ba
    f[arm > 0] = (24, 24, 26)
    ha = hand[..., 3:4] / 255
    f = f * (1 - ha) + hand[..., :3] * ha
    # caméra : plan moyen qui se resserre doucement sur les mains au moment du téléphone, puis sur le regard
    u0 = ease(t / 3.0); u1 = ease((t - 3.0) / 2.0); u2 = ease((t - T_LOOK + 0.1) / 1.4)
    cx = 660 + 40 * u0 + 80 * u1 + 450 * u2
    cy = 960 - 10 * u1 - 40 * u2
    z = 1.95 + 0.08 * u0 + 0.06 * u1 - 0.97 * u2
    out = cam(f, cx, cy, z)
    return np.clip(grade(out, i, "nuit"), 0, 255).astype(np.uint8)


def main():
    tmp = HERE / ".frames"; tmp.mkdir(exist_ok=True)
    only = [int(a) for a in sys.argv[1:]]
    t0 = time.time()
    if only:
        for i in only:
            Image.fromarray(frame(i)).save(tmp / f"{i:04d}.png")
        print(f"{len(only)} images en {time.time() - t0:.1f} s")
        return
    from multiprocessing import Pool  # noqa: PLC0415
    n = int(DUR * FPS)
    with Pool(4) as pool:
        for i, im in enumerate(pool.imap(frame, range(n), chunksize=4)):
            Image.fromarray(im).save(tmp / f"{i:04d}.png", compress_level=1)
    t1 = time.time()
    # son : clics de clavier sur chaque frappe, vibration du téléphone, ambiance de salle
    SR = 48000; N = int(DUR * SR); snd = np.zeros(N)
    rng = np.random.default_rng(4)
    for a in TAPS:
        m = int(0.03 * SR); x = rng.normal(0, 1, m) * np.exp(-np.arange(m) / (0.004 * SR))
        x = np.convolve(x, [1, -0.85], "same"); i0 = int(a * SR); snd[i0:i0 + m] += x * 0.09 * rng.uniform(0.7, 1.1)
    m = int(0.45 * SR); tt = np.arange(m) / SR
    snd[int(T_BUZZ * SR):int(T_BUZZ * SR) + m] += np.sin(2 * np.pi * 160 * tt) * (np.sin(2 * np.pi * 9 * tt) > 0) * 0.12
    snd += rng.normal(0, 1, N) * 0.004
    pcm = (np.clip(snd, -1, 1) * 32767).astype(np.int16)
    wav = HERE / "son.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(wav)], input=pcm.tobytes(), check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(tmp / "%04d.png"), "-i", str(wav), "-c:v", "libx264",
                    "-preset", "slow", "-b:v", "14M", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "160k", "-shortest",
                    "-movflags", "+faststart", str(HERE / "test_lea.mp4")], check=True)
    print(f"rendu : {t1 - t0:.0f} s pour {n} images ({(t1 - t0) / n:.2f} s/image, 4 cœurs) ; encodage + son : {time.time() - t1:.0f} s")


if __name__ == "__main__":
    main()
