"""Plan test (4 s) : la Lune se rapproche de la Terre, rendu image par image.

    python3 plan_espace.py      → test/plan_espace_muet.mp4

La Terre et la Lune sont de vraies sphères (cartes NASA libres de droits : Blue Marble et LRO), éclairées par le
Soleil, qui tournent sur elles-mêmes. Traitement « illustration » (lissage + aplats) pour rester proche du style 2D.
- la Lune grossit en accélérant ; compteur « temps avant contact »
- marée : la Terre s'étire vers la Lune ; nuages qui tournent plus vite que le sol
- fissures lumineuses qui s'étendent sur la Lune, puis débris arrachés de sa face tournée vers la Terre
- étoiles en trois plans (parallaxe), légère avancée de caméra, tremblement à la fin
"""
import subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
FPS, DUR, W, H = 30, 4.0, 1920, 1080
FONT = ImageFont.truetype(str(HERE.parents[1] / "prototype/fonts/InstrumentSans-Bold.ttf"), 26)
FONT_S = ImageFont.truetype(str(HERE.parents[1] / "prototype/fonts/InstrumentSans-Bold.ttf"), 22)


def stylise(img, levels):
    x = img
    for _ in range(2):
        x = cv2.bilateralFilter(x, 9, 38, 7)
    q = 256 // levels
    return ((x // q) * q + q // 2).astype(np.uint8)


earth = np.array(Image.open(HERE / "textures/terre_bluemarble_nasa.png").convert("RGB"))
earth = stylise(cv2.resize(earth, (2048, 1024)), 20)
hsv = cv2.cvtColor(earth, cv2.COLOR_RGB2HSV).astype(np.float32); hsv[..., 1] *= 1.15
earth = cv2.cvtColor(np.clip(hsv, 0, 255).astype(np.uint8), cv2.COLOR_HSV2RGB).astype(np.float32)
moon = np.array(Image.open(HERE / "textures/lune_lroc_nasa.png").convert("RGB"))
moon = stylise(cv2.resize(moon, (2048, 1024)), 22).astype(np.float32) * np.array([1.03, 1.0, 0.95], np.float32)
rng = np.random.default_rng(5)
cn = np.zeros((1024, 2048), np.float32)
for sz, sig, wgt in (((128, 128), (1.2, 3.0), 1.0), ((256, 256), (1.0, 3.0), 0.5), ((512, 512), (1.0, 2.5), 0.25)):
    o = cv2.GaussianBlur(rng.random(sz).astype(np.float32), (0, 0), sigmaX=sig[1], sigmaY=sig[0])   # étiré en longitude
    cn += cv2.resize(o, (2048, 1024), interpolation=cv2.INTER_CUBIC) * wgt
cn = (cn - cn.min()) / (cn.max() - cn.min())
clouds = cv2.GaussianBlur((np.clip((cn - 0.57) / 0.14, 0, 1) ** 1.3 * 0.75).astype(np.float32), (0, 0), 2.5)
SUN = np.array([-0.86, -0.24, 0.45]); SUN /= np.linalg.norm(SUN)


def sphere(frame, tex, cx, cy, R, rot, tilt=0.0, stretch=0.0, sdir=(1.0, 0.0), cloud_rot=None, atmo=False, cracks=None):
    x0, y0 = int(cx - R * 1.25) - 2, int(cy - R * 1.25) - 2
    x1, y1 = int(cx + R * 1.25) + 2, int(cy + R * 1.25) + 2
    X0, Y0, X1, Y1 = max(0, x0), max(0, y0), min(W, x1), min(H, y1)
    if X0 >= X1 or Y0 >= Y1:
        return
    ys, xs = np.mgrid[Y0:Y1, X0:X1].astype(np.float32)
    dx, dy = (xs - cx) / R, (ys - cy) / R
    ux, uy = sdir
    along = dx * ux + dy * uy; perp = -dx * uy + dy * ux
    along /= (1 + stretch)                                   # marée : étirement vers la Lune
    dx, dy = along * ux - perp * uy, along * uy + perp * ux
    r2 = dx * dx + dy * dy
    inside = r2 < 1
    nz = np.sqrt(np.clip(1 - r2, 0, 1))
    ct, st = np.cos(tilt), np.sin(tilt)
    nx, ny = dx * ct - dy * st, dx * st + dy * ct
    lat = np.arcsin(np.clip(ny, -1, 1)); lon = np.arctan2(nx, nz) + rot
    th, tw = tex.shape[:2]
    mu = ((lon / (2 * np.pi)) % 1) * tw; mv = (lat / np.pi + 0.5) * th
    col = cv2.remap(tex, mu.astype(np.float32), mv.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    lam = dx * SUN[0] + dy * SUN[1] + nz * SUN[2]
    light = np.clip((lam + 0.06) / 0.42, 0, 1) ** 1.1 * 1.0 + 0.03
    if cloud_rot is not None:
        cu = (((np.arctan2(nx, nz) + cloud_rot) / (2 * np.pi)) % 1) * tw
        ca = cv2.remap(clouds, cu.astype(np.float32), mv.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
        col = col * (1 - ca[..., None] * 0.85) + 245 * ca[..., None] * 0.85
    col = col * light[..., None]
    if cracks is not None:
        sc = cracks.shape[0] / 2
        ix, iy = int(round(X0 - cx + sc)), int(round(Y0 - cy + sc))
        pad = np.pad(cracks, ((8, 8), (8, 8), (0, 0)))
        cr = pad[iy + 8:iy + 8 + (Y1 - Y0), ix + 8:ix + 8 + (X1 - X0)]
        if cr.shape[:2] != (Y1 - Y0, X1 - X0):
            cr = np.zeros((Y1 - Y0, X1 - X0, 3), np.float32)
        col = col + cr * inside[..., None]
    edge = np.clip((1 - np.sqrt(r2)) * R, 0, 1)[..., None]
    reg = frame[Y0:Y1, X0:X1]
    reg[:] = reg * (1 - edge) + col * edge
    if atmo:
        rr = np.sqrt(r2)
        lit = np.clip((dx * SUN[0] + dy * SUN[1]) * 0.8 + 0.55, 0.15, 1)
        g = np.exp(-((rr - 1.0) / 0.035) ** 2) * (rr > 0.9) * lit
        halo = np.exp(-np.clip(rr - 1, 0, None) / 0.06) * (rr >= 1) * lit * 0.55
        a = np.clip(g * 0.8 + halo, 0, 1)[..., None]
        reg[:] = reg * (1 - a) + np.array([120, 175, 255], np.float32) * a


# --- fissures : réseau de lignes brisées partant de la face tournée vers la Terre (coordonnées du disque)
def make_cracks(n=7):
    out = []
    for k in range(n):
        a = np.pi + rng.uniform(-0.9, 0.9)
        p = np.array([np.cos(a), np.sin(a)]) * rng.uniform(0.35, 0.92)
        ang = a + np.pi + rng.uniform(-0.6, 0.6)
        pts = [p.copy()]
        for _ in range(14):
            ang += rng.uniform(-0.55, 0.55); p = p + 0.09 * np.array([np.cos(ang), np.sin(ang)])
            if np.hypot(*p) > 0.97:
                break
            pts.append(p.copy())
        out.append((rng.uniform(2.1, 3.1), np.array(pts)))
    return out


CRACKS = make_cracks()
STARS = [(rng.random((n, 2)) * [W * 1.2, H * 1.2] - [W * 0.1, H * 0.1], rng.random(n), d) for n, d in ((900, 0.15), (380, 0.35), (120, 0.7))]
DEBRIS = rng.random((140, 5))


def main():
    tmp = HERE / ".frames_espace"; tmp.mkdir(exist_ok=True)
    n = int(FPS * DUR)
    import sys
    only = [int(a) for a in sys.argv[1:]]
    for i in (only or range(n)):
        t = i / FPS; u = t / DUR
        s = u ** 2.3                                        # la Lune accélère
        f = np.zeros((H, W, 3), np.float32); f[:] = (4, 6, 12)
        cam = np.array([-28 * u, -10 * u])
        for pos, mag, depth in STARS:
            p = pos + cam * depth * 3
            tw = 0.75 + 0.25 * np.sin(t * 3 + mag * 40)
            xy = p.astype(int); ok = (xy[:, 0] >= 1) & (xy[:, 0] < W - 1) & (xy[:, 1] >= 1) & (xy[:, 1] < H - 1)
            bb = ((60 + 190 * mag ** 2) * tw * (0.6 + depth))[ok]; xs_, ys_ = xy[ok, 0], xy[ok, 1]
            np.add.at(f, (ys_, xs_), bb[:, None])
            big = mag[ok] > 0.93
            for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                np.add.at(f, (ys_[big] + ddy, xs_[big] + ddx), bb[big, None] * 0.4)
        ex, ey, ER = 690 + cam[0], 610 + cam[1], 330
        mr = 34 + 230 * s
        mx = 1610 + (1295 - 1610) * s + cam[0] * 1.6; my = 300 + (450 - 300) * s + cam[1] * 1.6
        dv = np.array([mx - ex, my - ey]); dv /= np.linalg.norm(dv)
        sphere(f, earth, ex, ey, ER, rot=0.9 + t * 0.065, tilt=0.4, stretch=0.06 * s ** 1.5, sdir=tuple(dv), cloud_rot=0.9 + t * 0.09, atmo=True)
        # fissures (dessinées en coordonnées du disque lunaire, orientées vers la Terre)
        size = int(mr * 2.5) + 40
        crk = np.zeros((size, size, 3), np.float32)
        base = np.arctan2(dv[1], dv[0])                    # la face « π » des fissures est tournée vers la Terre
        cR, sR = np.cos(base), np.sin(base)
        for t0, pts in CRACKS:
            k = (t - t0) / 0.9
            if k <= 0:
                continue
            m = max(2, int(len(pts) * min(1, k)))
            q = pts[:m] @ np.array([[cR, sR], [-sR, cR]])
            q = (q * mr + size / 2).astype(np.int32)
            g = min(1, k)
            cv2.polylines(crk, [q], False, (235 * g, 80 * g, 20 * g), max(2, int(mr * 0.028)), cv2.LINE_AA)
        if crk.any():
            crk = cv2.GaussianBlur(crk, (0, 0), max(1, mr * 0.018)) * 1.1
            core = np.zeros_like(crk)
            for t0, pts in CRACKS:
                k = (t - t0) / 0.9
                if k > 0:
                    m = max(2, int(len(pts) * min(1, k)))
                    q = (pts[:m] @ np.array([[cR, sR], [-sR, cR]]) * mr + size / 2).astype(np.int32)
                    cv2.polylines(core, [q], False, (255, 190, 110), 1, cv2.LINE_AA)
            crk += core * 0.8
        sphere(f, moon, mx, my, mr, rot=2.0 + t * 0.03, tilt=0.1, cracks=crk if crk.any() else None)
        # débris arrachés de la face tournée vers la Terre
        for k, (a0, sp, sz, ph, glow) in enumerate(DEBRIS):
            ts = 2.7 + ph * 1.1
            if t < ts:
                continue
            age = t - ts
            ang = np.arctan2(-dv[1], -dv[0]) + (a0 - 0.5) * 2.0
            p0 = np.array([mx, my]) + mr * 0.98 * np.array([np.cos(ang), np.sin(ang)])
            vel = (np.array([np.cos(ang), np.sin(ang)]) * (40 + 120 * sp) - dv * 60)
            p = p0 + vel * age
            rad = 1.2 + sz * 4.5 * (mr / 260)
            c = (255, 160, 80) if glow > 0.8 else (150, 145, 140)
            cv2.circle(f, (int(p[0]), int(p[1])), int(max(1, rad)), c, -1, cv2.LINE_AA)
        # lueur entre les deux astres à la fin
        if s > 0.55:
            gp = np.array([mx, my]) - dv * mr * 1.02
            yy, xx = np.mgrid[0:H:4, 0:W:4]
            gl = np.exp(-(((xx - gp[0]) ** 2 + (yy - gp[1]) ** 2) / (2 * (mr * 0.45) ** 2))) * (s - 0.55) / 0.45 * 0.5
            gl = cv2.resize(gl.astype(np.float32), (W, H))
            f = f + gl[..., None] * np.array([255, 170, 110], np.float32)
        # caméra : légère avancée + tremblement à la fin
        z = 1 + 0.05 * u * u
        shake = (rng.normal(0, 1, 2) * 4 * max(0, (u - 0.75) / 0.25))
        M = np.float32([[z, 0, (1 - z) * W / 2 + shake[0]], [0, z, (1 - z) * H / 2 + shake[1]]])
        out = cv2.warpAffine(np.clip(f, 0, 255).astype(np.uint8), M, (W, H), flags=cv2.INTER_LINEAR)
        # textes : étiquette et compteur
        im = Image.fromarray(out); d = ImageDraw.Draw(im)
        d.text((58, 60), "SIMULATION HYPOTHÉTIQUE", font=FONT_S, fill=(214, 220, 226))
        rest_h = (4 * 24 + 20) * (1 - s) + 6 * s          # de 4 j 20 h à 6 h avant le contact
        jj, hh = int(rest_h // 24), int(rest_h % 24)
        d.text((58, H - 100), "Temps avant contact", font=FONT_S, fill=(170, 180, 192))
        d.text((58, H - 70), f"{jj} j {hh:02d} h", font=FONT, fill=(240, 244, 248))
        im.save(tmp / f"{i:04d}.png")
        if i % 30 == 0:
            print("image", i, flush=True)
    if only:
        return
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(tmp / "%04d.png"), "-c:v", "libx264",
                    "-crf", "17", "-pix_fmt", "yuv420p", str(HERE / "plan_espace_muet.mp4")], check=True)


if __name__ == "__main__":
    main()
