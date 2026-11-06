"""Bloc 1 (00:00–01:00, « Le dernier ciel ») : rendu image par image, 1920×1080, 30 i/s, puis son et assemblage.

    python3 render_b01.py                 → film/b01/bloc01.mp4
    python3 render_b01.py 120 400 900     → seulement ces images (contrôle), dans film/b01/.frames/

Aucune génération : 4 images (b01/*.png), la voix de Nicolas (b01/v1–v4.wav) et les bruitages déjà produits.
Plans : A chambre (lumière de Lune, rideaux, poussière) · B fenêtre (la Lune géante, nuages, une fenêtre s'éteint)
· C rue (figurants immobiles qui respirent, ombres, brume) · retour en arrière (tout repart à l'envers et s'éteint)
· carton « Quatre jours plus tôt ».
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
B = HERE / "b01"
LUNE = HERE.parent
sys.path.insert(0, str(LUNE / "film2d"))
sys.path.insert(0, str(LUNE.parent / "panne_internet"))
FPS, W, H = 30, 1920, 1080
FONTS = LUNE / "prototype/fonts"
F_LABEL = ImageFont.truetype(str(FONTS / "InstrumentSans-Bold.ttf"), 24)
F_CARD = ImageFont.truetype(str(FONTS / "BricolageGrotesque-Bold.ttf"), 76)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout)


# ------------------------------------------------------------------ minutage (calé sur les voix réelles)
D = {k: dur(B / f"{k}.wav") for k in ("v1", "v2", "v3", "v4")}
# repères des phrases, lus sur la forme d'onde de chaque voix (secondes depuis le début du fichier)
V1 = 1.8                         # « Imaginez que vous vous réveilliez… » pendant que les yeux s'ouvrent
LIGHT = V1 + 2.92                # « Votre chambre est éclairée. » : la lumière monte
CUT_B = V1 + 5.86                # « Par la Lune. » : coupe sur la fenêtre, la Lune géante
V2 = V1 + D["v1"] + 1.7          # on laisse la révélation respirer
A_APP, A_CRAT, A_RUES = V2, V2 + 8.86, V2 + 10.83   # « Vous vous approchez… » · « Ses cratères… » · « …transforme les rues… »
CUT_C = V2 + D["v2"] + 0.5
V3 = CUT_C + 0.9
CUT_D = V3 + 6.6                 # « Dans quelques heures… » : très gros plan sur la Lune
PERC = V3 + 8.45                 # « …percuter… » : coup sourd, secousse
V4 = V3 + D["v3"] + 1.8          # silence protégé après « …percuter la Terre. »
REW = V4 + 0.2                   # le retour en arrière commence avec la phrase
BLACK = V4 + D["v4"] + 0.4
CARD0, CARD1 = BLACK + 0.6, BLACK + 3.6
END = CARD1 + 0.8
VOICES = [("v1", V1), ("v2", V2), ("v3", V3), ("v4", V4)]


def ease(u):
    u = np.clip(u, 0, 1)
    return u * u * (3 - 2 * u)


def load_rgb(name):
    return np.asarray(Image.open(B / f"{name}.png").convert("RGB")).astype(np.float32)


def cam(img, cx, cy, zoom, out=(W, H), rot=0.0, shake=(0.0, 0.0)):
    """Fenêtre de caméra dans l'image source (2752×1536) : centre, zoom (1 = toute la largeur), roulis en degrés."""
    sh, sw = img.shape[:2]
    zoom = zoom * (1 + abs(rot) * 0.012)                  # le roulis ne doit jamais montrer les bords
    wv = sw / zoom; s = out[0] / wv
    cx = np.clip(cx, wv / 2, sw - wv / 2); hv = out[1] / s; cy = np.clip(cy, hv / 2, sh - hv / 2)
    M = np.float32([[s, 0, -(cx - wv / 2) * s + shake[0]], [0, s, -(cy - hv / 2) * s + shake[1]]])
    if rot:
        R = cv2.getRotationMatrix2D((out[0] / 2, out[1] / 2), rot, 1.0)
        M = (np.vstack([R, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]]))[:2].astype(np.float32)
    return cv2.warpAffine(img, M, out, flags=cv2.INTER_AREA if s < 1 else cv2.INTER_LINEAR)


# ------------------------------------------------------------------ éléments communs
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


# ------------------------------------------------------------------ plan A : chambre
A_img = load_rgb("chambre_nuit")
hA, wA = A_img.shape[:2]
yyA, xxA = np.mgrid[0:hA, 0:wA].astype(np.float32)
cur = np.zeros((hA, wA), np.float32)
cv2.rectangle(cur, (1390, 150), (1730, 905), 1, -1); cv2.rectangle(cur, (2010, 100), (2480, 1000), 1, -1)
cur = cv2.GaussianBlur(cur, (0, 0), 25)
cur_w = cur * np.clip((yyA - 150) / 700, 0, 1) ** 1.3                  # fixé à la tringle, libre en bas
bright_A = np.clip(((A_img.mean(2) - 150) / 70), 0, 1)                   # zones éclairées par la Lune


def keys(t, ks):
    """Interpolation adoucie entre images clés [(t, valeurs...)]."""
    if t <= ks[0][0]:
        return np.array(ks[0][1:], float)
    for a, b in zip(ks, ks[1:]):
        if t <= b[0]:
            u = ease((t - a[0]) / (b[0] - a[0]))
            return np.array(a[1:], float) * (1 - u) + np.array(b[1:], float) * u
    return np.array(ks[-1][1:], float)


def lids(t):
    """Ouverture des paupières (0 fermé, 1 ouvert) : un premier entrouvrement, un clignement, puis grand ouvert."""
    return float(keys(t, [(1.5, 0.0), (2.2, 0.5), (2.45, 0.12), (2.6, 0.12), (3.4, 1.0)])[0])


def plan_A(t):
    sway = 7 * np.sin(2 * np.pi * t / 5.3 + yyA * 0.004) + 3 * np.sin(2 * np.pi * t / 2.9 + 1.3)
    mx = (xxA - cur_w * sway).astype(np.float32)
    f = cv2.remap(A_img, mx, yyA, cv2.INTER_LINEAR)
    lk = ease((t - LIGHT) / 1.3)                                   # la lumière de Lune monte sur « …éclairée. »
    f *= ((1 - bright_A * (1 - lk) * 0.38) * (0.66 + 0.34 * lk))[..., None]
    dust(f, t, (1450, 300, 2350, 1300), alpha=0.06 + 0.18 * lk)
    # vue subjective : la tête sur l'oreiller (penchée), elle se soulève, puis le regard glisse vers la fenêtre
    cx, cy, z, rot = keys(t, [(0, 1250, 1000, 1.28, -6.0), (2.4, 1250, 990, 1.28, -6.0), (4.2, 1450, 790, 1.14, -1.0),
                              (CUT_B, 1680, 640, 1.24, 0.0)])
    rot += 0.4 * np.sin(2 * np.pi * t / 3.7)                       # respiration
    return cam(f, cx, cy, z, rot=rot)


# ------------------------------------------------------------------ plan B : fenêtre
B_img = load_rgb("fenetre_rue")
skyB = sky_mask(B_img, 800, (780, 2230))
win = (B_img[..., 0] > 190) & (B_img[..., 1] > 130) & (B_img[..., 2] < 140)
ncomp, labels = cv2.connectedComponents(win.astype(np.uint8))
sizes = np.bincount(labels.ravel())
cands = [i for i in range(1, ncomp) if 300 < sizes[i] < 20000]
target = max(cands, key=lambda i: np.mean(np.nonzero(labels == i)[1])) if cands else None   # la fenêtre allumée la plus à droite
off_mask = cv2.GaussianBlur(cv2.dilate((labels == target).astype(np.uint8), np.ones((9, 9), np.uint8)).astype(np.float32), (0, 0), 2) if target else None
win_dark = cv2.GaussianBlur(B_img, (0, 0), 1) * np.array([0.30, 0.33, 0.42], np.float32)


def plan_B(t, tl):
    f = B_img.copy()
    clouds(f, skyB[:800], 1800 - 22 * t, 0.85)
    if off_mask is not None:
        k = ease((tl - 7.2) / 0.25)[()] if np.ndim(tl) == 0 else 0
        a = (off_mask * float(k))[..., None]
        f = f * (1 - a) + win_dark * a
    T = CUT_B + tl
    cx, cy, z = keys(T, [(CUT_B, 1376, 768, 1.0), (A_APP, 1376, 768, 1.02), (A_APP + 1.6, 1440, 740, 1.14),
                         (A_CRAT, 1520, 690, 1.2), (A_CRAT + 1.5, 1835, 450, 1.95), (A_RUES, 1835, 470, 2.0),
                         (A_RUES + 2.8, 1420, 1060, 1.5), (CUT_C, 1400, 1080, 1.53)])
    walk = np.clip((T - A_APP) / 1.6, 0, 1)                         # trois pas jusqu'à la fenêtre
    bob = 7 * np.sin(np.pi * 2 * 1.9 * (T - A_APP)) * np.sin(np.pi * walk) if 0 < walk < 1 else 0.0
    return cam(f, cx, cy + bob, z)


# ------------------------------------------------------------------ plan C : rue
C_img = load_rgb("rue_lune")
skyC = sky_mask(C_img, 820)
figs = [np.asarray(Image.open(B / f"fig_{k}.png").convert("RGBA")).astype(np.float32) for k in range(4)]
FIG_X = [204, 821, 1365, 2176]                     # position d'origine dans l'image des figurants (on garde le groupe)
FIG_S, FEET, GX = 0.33, 1405, 1376 - (2549 - 204) * 0.33 / 2 - 204 * 0.33


def figurant(f, k, t, rew):
    img = figs[k]
    h, w = img.shape[:2]
    br = 0.006 * np.sin(2 * np.pi * t / (3.4 + 0.5 * k) + k * 1.7)          # respiration, décalée pour chacun
    sway = 0.35 * np.sin(2 * np.pi * t / (5.0 + k) + k)                     # balancement à peine visible
    R = np.vstack([cv2.getRotationMatrix2D((w / 2, h), sway, 1.0), [0, 0, 1]])
    Sb = np.array([[1, 0, 0], [0, 1 + br, -h * br], [0, 0, 1]])        # respiration : le corps s'étire depuis les pieds
    s = FIG_S
    x = GX + FIG_X[k] * s; y = FEET - h * s
    A = (np.array([[s, 0, x], [0, s, y], [0, 0, 1]]) @ Sb @ R)[:2].astype(np.float32)
    out = cv2.warpAffine(img, A, (f.shape[1], f.shape[0]), flags=cv2.INTER_AREA, borderValue=(0, 0, 0, 0))
    a = out[..., 3:4] / 255 * (1 - rew)
    # ombre portée vers nous (la Lune est derrière eux), écrasée et inclinée
    sh = cv2.warpAffine(img[..., 3], np.float32([[s, 0.35 * s, x - 0.35 * s * h], [0, -0.42 * s, FEET + 0.42 * s * h]]),
                        (f.shape[1], f.shape[0]), flags=cv2.INTER_AREA)
    sh = cv2.GaussianBlur(sh, (0, 0), 3)[..., None] / 255 * 0.42 * (1 - rew)
    f[:] = f * (1 - sh * 0.75)
    f[:] = f * (1 - a) + out[..., :3] * a


def plan_C(t, tl, rew):
    f = C_img.copy()
    dirn = 1.0
    xoff = 2400 - 18 * tl if rew <= 0 else 2400 - 18 * (REW - CUT_C) + 160 * (tl - (REW - CUT_C)) ** 1.6   # à l'envers, de plus en plus vite
    clouds(f, skyC[:820], xoff, 0.7)
    fx_ = int((300 + 30 * tl if rew <= 0 else 300 + 30 * (REW - CUT_C) - 140 * (tl - (REW - CUT_C)) ** 1.5)) % (FOG.shape[1] - f.shape[1])
    fog = cv2.resize(FOG, (FOG.shape[1], 360))[:, fx_:fx_ + f.shape[1]]
    yy = np.arange(360)[:, None]
    fa = (fog * np.exp(-((yy - 170) / 110) ** 2) * 0.28)[..., None]
    f[930:1290] = f[930:1290] * (1 - fa) + np.array([175, 185, 200], np.float32) * fa
    for k in range(4):
        figurant(f, k, t, rew)
    T = CUT_C + tl
    if T < CUT_D:                                                   # la rue : lente avancée
        u = ease(tl / (CUT_D - CUT_C))
        return cam(f, 1376, 860 - 60 * u, 1.02 + 0.06 * u)
    # « Dans quelques heures… » : la Lune écrase le cadre ; « percuter » : secousse ; au retour, on recule jusqu'à la rue
    z = 1.95 + 0.25 * ease((T - CUT_D) / (V4 - CUT_D))
    cx, cy = 1390, 440
    if rew > 0:
        z = z * (1 - rew) + 1.0 * rew; cy = cy * (1 - rew) + 820 * rew
    k = max(0.0, T - PERC)
    amp = 9 * np.exp(-k / 0.45) if T > PERC else 0.0
    sh = (amp * np.sin(T * 71), amp * np.sin(T * 53 + 1))
    return cam(f, cx, cy, z, shake=sh)


# ------------------------------------------------------------------ assemblage d'une image
def label(img):
    im = Image.fromarray(img); d = ImageDraw.Draw(im)
    d.text((58, 60), "SIMULATION HYPOTHÉTIQUE", font=F_LABEL, fill=(214, 220, 226))
    return np.asarray(im)


def frame(i):
    t = i / FPS
    if t < CUT_B:
        f = plan_A(t)
        o = lids(t)                                                  # paupières : flou puis net, bord courbe
        if o < 1:
            sig = 1 + (1 - o) * 14
            f = cv2.GaussianBlur(f, (0, 0), sig)
            xs = (np.arange(W) / W * 2 - 1)
            half = o * H / 2 * (0.62 + 0.38 * np.sqrt(np.clip(1 - xs ** 2, 0, 1)))
            yy = np.abs(np.arange(H)[:, None] - H / 2)
            m = np.clip((half[None, :] - yy) / 40 + 0.5, 0, 1)
            f = f * m[..., None]
    elif t < CUT_C:
        f = plan_B(t, t - CUT_B)
        if t - CUT_B < 0.5:                                          # raccord : la lumière éblouit un instant
            f = f + 90 * (1 - ease((t - CUT_B) / 0.5))
    elif t < BLACK:
        rew = ease((t - REW) / (BLACK - REW)) if t > REW else 0.0
        f = plan_C(t, t - CUT_C, rew)
        if t - CUT_C < 0.6:
            pass
        if rew > 0:                                                   # désature et s'éteint
            g = f.mean(2, keepdims=True)
            f = (f * (1 - 0.7 * rew) + g * 0.7 * rew) * (1 - rew) ** 1.2
    else:
        f = np.zeros((H, W, 3), np.float32)
    out = np.clip(f, 0, 255).astype(np.uint8)
    if t < BLACK + 0.3:
        out = label(out)
    if CARD0 <= t <= CARD1:
        a = min(ease((t - CARD0) / 0.6), ease((CARD1 - t) / 0.6))
        im = Image.new("RGB", (W, H)); d = ImageDraw.Draw(im)
        txt = "Quatre jours plus tôt"
        bb = d.textbbox((0, 0), txt, font=F_CARD)
        d.text(((W - (bb[2] - bb[0])) / 2, (H - (bb[3] - bb[1])) / 2 - 20), txt, font=F_CARD, fill=(236, 240, 245))
        out = (np.asarray(im).astype(np.float32) * a).astype(np.uint8)
    return out


# ------------------------------------------------------------------ son
def soundtrack(path):
    from assemble import SFX, fade, load, loop, norm, put, rms  # noqa: PLC0415
    import fx  # noqa: PLC0415
    SR = 48000; N = int(END * SR)
    voice, bed = np.zeros(N), np.zeros(N)
    for k, at in VOICES:
        put(voice, norm(load(B / f"{k}.wav"), 0.6), at)
    R = B / "sfx_real"
    amb = loop(rms(load(R / "amb_ville_nuit.wav"), -33), BLACK)
    inside = np.ones(len(amb)); inside[: int(CUT_B * SR)] = 0.35                                # la ville, assourdie dans la chambre
    k = np.ones(64) / 64; muff = np.convolve(amb, k, "same")
    cb = int(CUT_B * SR); amb = np.concatenate([muff[:cb] * 0.6, amb[cb:]])
    put(bed, fade(amb, 1.5, 1.5), 0)
    put(bed, norm(load(R / "reveil.wav")), 1.25, 0.32)                                         # réveil : inspiration, draps
    put(bed, norm(load(R / "parquet.wav")), A_APP + 0.05, 0.30)                                # trois pas vers la fenêtre
    put(bed, fade(fx.drone("dark", BLACK - 1.0), 3.0, 2.0), 1.0, 0.08)
    put(bed, fx.riser(2.0), PERC - 2.0, 0.10)                                                  # monte vers « percuter »
    put(bed, fx.impact(1.8), PERC, 0.45)                                                       # coup sourd
    put(bed, norm(load(SFX / "space_rumble.wav")), PERC - 0.1, 0.22)                           # grondement, puis silence protégé
    put(bed, fx.reverse_cymbal(1.6), REW + 0.4, 0.22)                                          # le temps repart en arrière
    bed[int(BLACK * SR):] *= 0
    duck = fx.duck_under_voice(bed, voice * 32768.0, SR, 1.0, margin=8.0)
    mix = (voice + duck) * 1.45
    mix = np.where(np.abs(mix) > 0.85, np.sign(mix) * (0.85 + 0.1 * np.tanh((np.abs(mix) - 0.85) / 0.1)), mix)
    pcm = (np.clip(mix, -1, 1) * 32767).astype(np.int16)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(path)],
                   input=pcm.tobytes(), check=True)


def _save(i):
    Image.fromarray(frame(i)).save(B / ".frames" / f"{i:05d}.png", compress_level=1)


def main():
    tmp = B / ".frames"; tmp.mkdir(exist_ok=True)
    only = [int(a) for a in sys.argv[1:]]
    n = int(END * FPS)
    if only:
        for i in only:
            Image.fromarray(frame(i)).save(tmp / f"{i:05d}.png", compress_level=1)
        return
    todo = [i for i in range(n) if not (tmp / f"{i:05d}.png").exists()]
    cv2.setNumThreads(1)
    from multiprocessing import Pool  # noqa: PLC0415
    with Pool(4) as pool:
        for k, _ in enumerate(pool.imap_unordered(_save, todo, chunksize=8)):
            if k % 150 == 0:
                print(f"image {k}/{len(todo)}", flush=True)
    soundtrack(B / "son_b01.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(tmp / "%05d.png"), "-i", str(B / "son_b01.wav"),
                    "-c:v", "libx264", "-crf", "16", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                    "-shortest", "-movflags", "+faststart", str(B / "bloc01.mp4")], check=True)
    print("ok", B / "bloc01.mp4", f"{END:.1f} s")


if __name__ == "__main__":
    print({k: round(v, 2) for k, v in dict(V1=V1, V2=V2, CUT_B=CUT_B, V3=V3, CUT_C=CUT_C, V4=V4, BLACK=BLACK, END=END).items()})
    main()
