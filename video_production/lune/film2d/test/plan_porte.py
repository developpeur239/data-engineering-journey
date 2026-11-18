"""Plan test (2,5 s) : le collègue dans la porte dit « On doit partir. », bouche synchronisée sur sa vraie voix.

    python3 plan_porte.py      → test/plan_porte.mp4 (+ test/bouches.png : la planche des formes de bouche)

Synchronisation : la piste de voix (voix_prototype/A2_collegue.wav) est analysée image par image.
- volume → ouverture de la bouche ; silence → bouche fermée (son arc inquiet d'origine)
- timbre sombre (« on », « ou ») → bouche ronde ; timbre clair (« i ») → bouche étirée
- creux brusque au milieu de la phrase (« p » de « partir ») → lèvres serrées
- la bouche change toutes les 2 images (15 par seconde, comme en animation 2D) et anticipe le son de 1 image
Le personnage respire et cligne des yeux ; la caméra avance doucement.
"""
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from assemble import SFX, SR, fade, load, loop, norm, put, rms  # noqa: E402

FPS, DUR, W, H = 30, 2.5, 1920, 1080
VOICE_AT = 0.3
LUNE = HERE.parents[1]
MOUTH_C = (387, 438)          # centre de la bouche dans l'image native
EYES = [(288, 318), (478, 318)]

col = np.array(Image.open(HERE.parent / "images/collegue_porte_cut.png").convert("RGBA"))
decor = np.array(Image.open(HERE.parent / "images/decor_calern_nuit.png").convert("RGB")).astype(np.float32)
# on efface la bouche d'origine (elle sera redessinée) : on garde son arc pour la forme « fermée »
base = col.copy()
x0, y0 = MOUTH_C[0] - 52, MOUTH_C[1] - 26
reg = base[y0:y0 + 52, x0:x0 + 104]
reg[reg[..., :3].max(2) > 25, :3] = 0          # tout le trait, antialiasing compris
ORIG_MOUTH = col[y0:y0 + 52, x0:x0 + 104].copy()


def mouth_mask(shape, s):
    """Forme de bouche en blanc, dans une vignette 104×52 (sur-échantillonnée ×4 pour l'antialiasing)."""
    k, (w, h) = 4, (104, 52)
    m = np.zeros((h * k, w * k), np.uint8)
    cx, cy = w * k // 2, h * k // 2
    if shape == "m":                      # lèvres serrées : trait droit, un peu plus court
        cv2.line(m, (cx - 26 * k, cy + 2 * k), (cx + 26 * k, cy + 2 * k), 255, 9 * k)
    elif shape == "o":                    # rond
        cv2.ellipse(m, (cx, cy + 2 * k), (int(17 * k * (0.75 + 0.25 * s)), int((12 + 11 * s) * k)), 0, 0, 360, 255, -1, cv2.LINE_AA)
    elif shape == "i":                    # étirée
        cv2.ellipse(m, (cx, cy + 3 * k), (34 * k, int((5 + 6 * s) * k)), 0, 0, 360, 255, -1, cv2.LINE_AA)
    else:                                 # ouverte, de la plus petite à la plus grande (le haut reste inquiet, en arc)
        hh = int((5 + 19 * s) * k); ww = int((22 + 10 * s) * k)
        pts = []
        for a in np.linspace(0, np.pi, 24):              # lèvre supérieure : arc vers le haut (bouche triste)
            pts.append((cx - ww * np.cos(a), cy - 3 * k - 5 * k * np.sin(a)))
        for a in np.linspace(0, np.pi, 24):              # lèvre inférieure : arc vers le bas
            pts.append((cx + ww * np.cos(a), cy - 3 * k + hh * np.sin(a)))
        cv2.fillPoly(m, [np.array(pts, np.int32)], 255, cv2.LINE_AA)
    return cv2.resize(m, (w, h), interpolation=cv2.INTER_AREA).astype(np.float32) / 255


def analyse(voice):
    """Forme de bouche par image (30 i/s) à partir de la voix."""
    hop = SR // FPS; n = len(voice) // hop
    win = np.hanning(hop * 2)
    amp, cen = [], []
    freqs = np.fft.rfftfreq(hop * 2, 1 / SR)
    for i in range(n):
        seg = voice[i * hop: i * hop + hop * 2]
        seg = np.pad(seg, (0, hop * 2 - len(seg)))
        amp.append(np.sqrt((seg ** 2).mean()))
        sp = np.abs(np.fft.rfft(seg * win)); band = (freqs > 150) & (freqs < 6000)
        cen.append((sp[band] * freqs[band]).sum() / (sp[band].sum() + 1e-9))
    amp = np.array(amp) / (max(amp) + 1e-9); cen = np.array(cen)
    out = []
    for i in range(n):
        a = amp[i]
        if a < 0.1:
            out.append(("ferme", 0)); continue
        nb = amp[max(0, i - 3):i + 4]
        if a < 0.32 and nb.max() > 0.6 and 0 < i < n - 1:     # creux bref entre deux syllabes fortes : « p »
            out.append(("m", 0)); continue
        s = float(np.clip((a - 0.1) / 0.75, 0, 1))
        if cen[i] < 1100:
            out.append(("o", s))
        elif cen[i] > 2600:
            out.append(("i", s))
        else:
            out.append(("ouvert", s))
    return out, amp, cen


# feuille d'exposition de « On doit partir. » : syllabes lues sur la forme d'onde (temps en s depuis le début de la voix)
#   on 0,07–0,30 · d 0,30 · oi 0,33–0,42 · (t)p 0,43–0,48 · a 0,50–0,57 · t 0,57 · i 0,60–0,69 · r 0,70–0,80
DOPE = [(0.0, "ferme"), (0.06, "o"), (0.30, "petit"), (0.33, "o"), (0.37, "ouvert"), (0.43, "m"), (0.50, "ouvert"),
        (0.57, "petit"), (0.60, "i"), (0.70, "petit"), (0.82, "ferme")]


def dope_track(amp, n):
    out = []
    for i in range(n):
        t = i / FPS
        sh = [s for t0, s in DOPE if t0 <= t + 1e-6][-1]
        a = float(amp[i]) if i < len(amp) else 0.0
        s = float(np.clip((a - 0.1) / 0.75, 0.15, 1))
        if sh == "petit":
            out.append(("ouvert", min(s, 0.25)))
        elif sh in ("ferme", "m"):
            out.append((sh, 0))
        else:
            out.append((sh, s))
    return out


def main():
    voice = load(LUNE / "voix_prototype/A2_collegue.wav")
    _, amp, cen = analyse(voice)
    shapes = dope_track(amp, len(amp))
    # planche des formes (pour vérification)
    demo = [("ferme", 0), ("ouvert", 0.2), ("ouvert", 0.6), ("ouvert", 1.0), ("o", 0.6), ("i", 0.6), ("m", 0)]
    tiles = []
    for sh, s in demo:
        face = base[300:560, 250:530].copy()
        if sh == "ferme":
            face[y0 - 300:y0 - 300 + 52, x0 - 250:x0 - 250 + 104] = ORIG_MOUTH
        else:
            mm = mouth_mask(sh, s)
            r = face[y0 - 300:y0 - 300 + 52, x0 - 250:x0 - 250 + 104, :3].astype(np.float32)
            face[y0 - 300:y0 - 300 + 52, x0 - 250:x0 - 250 + 104, :3] = (r * (1 - mm[..., None]) + 250 * mm[..., None]).astype(np.uint8)
        bg = np.full(face.shape[:2] + (3,), (120, 160, 120), np.float32); a = face[..., 3:4] / 255
        tiles.append((bg * (1 - a) + face[..., :3] * a).astype(np.uint8))
    Image.fromarray(np.hstack(tiles)).save(HERE / "bouches.png")

    # cadrage : le plan « collègue à la porte » du prototype, plus serré pour qu'on voie la bouche
    CS = 0.7116                                       # échelle « cover » du décor dans build_film.py
    cx_d, cy_d = (152 + 19.2) / CS, (655 + 6.5) / CS   # coin haut gauche du collègue dans le décor (px natifs du décor)
    ch_d = 340 / CS                                    # hauteur du collègue dans le décor
    sc = ch_d / col.shape[0]
    tmp = HERE / ".frames_porte"; tmp.mkdir(exist_ok=True)
    n = int(FPS * DUR)
    for i in range(n):
        t = i / FPS
        k = int(((t - VOICE_AT) * FPS + 1) // 2 * 2)   # +1 image d'avance, changement toutes les 2 images
        sh, s = shapes[k] if 0 <= k < len(shapes) else ("ferme", 0)
        spr = base.copy()
        mx, my = x0, y0
        if sh == "ferme":
            spr[my:my + 52, mx:mx + 104] = ORIG_MOUTH
        else:
            mm = mouth_mask(sh, s); r = spr[my:my + 52, mx:mx + 104, :3].astype(np.float32)
            spr[my:my + 52, mx:mx + 104, :3] = (r * (1 - mm[..., None]) + 250 * mm[..., None]).astype(np.uint8)
        if abs(t - 1.95) < 0.06:                       # clignement après la réplique
            for ex, ey in EYES:
                e = spr[ey - 30:ey + 30, ex - 22:ex + 22]; e[e[..., :3].min(2) > 150, :3] = 0
        # respiration + petit mouvement de tête quand il parle
        hgt, wid = spr.shape[:2]
        yy, xx = np.mgrid[0:hgt, 0:wid].astype(np.float32)
        br = 0.005 * np.sin(2 * np.pi * t / 3.2)
        talk = 0.0 if sh == "ferme" else s
        head = np.clip((600 - yy) / 120, 0, 1)
        my_ = hgt + (yy - hgt) / (1 + br) - head * (3 * talk + 2 * np.sin(2 * np.pi * t / 2.3))
        spr = cv2.remap(spr, xx, my_.astype(np.float32), cv2.INTER_LINEAR)
        # composition dans le décor
        f = decor.copy()
        small = cv2.resize(spr, (int(wid * sc), int(hgt * sc)), interpolation=cv2.INTER_AREA).astype(np.float32)
        X, Y = int(cx_d), int(cy_d); hh, ww = small.shape[:2]
        a = small[..., 3:4] / 255
        f[Y:Y + hh, X:X + ww] = f[Y:Y + hh, X:X + ww] * (1 - a) + small[..., :3] * a
        u = t / DUR; e = u * u * (3 - 2 * u)
        zoom = 1.0 + 0.05 * e
        wv, hv = 540 / zoom, 304 / zoom
        ccx, ccy = cx_d + ch_d * 0.30, cy_d + ch_d * 0.30
        sx = W / wv
        M = np.float32([[sx, 0, -(ccx - wv / 2) * sx], [0, sx, -(ccy - hv / 2) * sx]])
        out = cv2.warpAffine(np.clip(f, 0, 255).astype(np.uint8), M, (W, H), flags=cv2.INTER_CUBIC)
        Image.fromarray(out).save(tmp / f"{i:04d}.png")
    # son : ambiance de nuit + la réplique
    N = int(SR * DUR); snd = np.zeros(N)
    put(snd, fade(loop(rms(load(SFX / "amb_calern_nuit.wav"), -32), DUR), 0.2, 0.2), 0)
    put(snd, norm(voice, 0.6), VOICE_AT)
    pcm = (np.clip(snd * 1.4, -1, 1) * 32767).astype(np.int16)
    wav = HERE / "son_porte.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "s16le", "-ar", str(SR), "-ac", "1", "-i", "-", str(wav)], input=pcm.tobytes(), check=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(tmp / "%04d.png"), "-i", str(wav),
                    "-c:v", "libx264", "-crf", "17", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-shortest",
                    "-movflags", "+faststart", str(HERE / "plan_porte.mp4")], check=True)
    print("formes :", [(round(i / FPS, 2), sh, round(s, 2)) for i, (sh, s) in enumerate(shapes)])


if __name__ == "__main__":
    main()
