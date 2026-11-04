"""Miniatures alternatives (1280x720) pour « Tester et comparer » de YouTube.

B : la miniature actuelle (Marc) garde son visage, mais le fond devient un distributeur qui affiche « REFUSÉ »
    et le texte « HEURE 2 » (moment de la vidéo où les distributeurs refusent tout).
C : l'Europe vue de l'espace, de nuit, à moitié éteinte, avec « JOUR 2 » (passage mondial de la vidéo).

    python thumbnails.py --source <miniature_actuelle.png> --textures <dossier> --fonts <dossier> --out <dossier>
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from channel_art import AMBER, CYAN, NAVY, Globe, draw_network, glow_layer, halo, stars

W, H = 1280, 720
YELLOW = (255, 214, 30)
RED = (255, 48, 48)


def big_text(img: Image.Image, xy, text: str, font: ImageFont.FreeTypeFont, fill, outline=(150, 60, 0), glow=AMBER):
    """Gros texte façon miniature : halo, contour épais, ombre portée."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((xy[0] + 8, xy[1] + 10), text, font=font, fill=(0, 0, 0, 200), stroke_width=10, stroke_fill=(0, 0, 0, 200))
    shadow = layer.filter(ImageFilter.GaussianBlur(10))
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(g).text(xy, text, font=font, fill=glow + (255,), stroke_width=14, stroke_fill=glow + (255,))
    g = g.filter(ImageFilter.GaussianBlur(18))
    top = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(top).text(xy, text, font=font, fill=fill + (255,), stroke_width=7, stroke_fill=outline + (255,))
    out = Image.alpha_composite(img, shadow)
    out = Image.alpha_composite(out, g)
    return Image.alpha_composite(out, top)


def thumb_b(source: Path, fonts: Path, out: Path):
    base = Image.open(source).convert("RGBA").resize((W, H), Image.LANCZOS)
    # nouveau fond à droite : un distributeur de billets, dessiné en suréchantillonnage
    ss = 2
    atm = Image.new("RGBA", (W * ss, H * ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(atm)
    S = lambda *v: tuple(int(x * ss) for x in v)
    # mur sombre
    d.rectangle(S(520, 0, W, H), fill=(22, 14, 20, 255))
    for y in range(0, H, 34):
        d.line(S(520, y, W, y), fill=(40, 28, 36, 255), width=ss)
    # caisson du distributeur
    d.rounded_rectangle(S(640, 230, 1250, 760), radius=18 * ss, fill=(38, 40, 46, 255), outline=(70, 72, 80, 255), width=3 * ss)
    d.rounded_rectangle(S(690, 290, 1200, 600), radius=10 * ss, fill=(12, 12, 16, 255))
    # écran rouge
    d.rounded_rectangle(S(712, 310, 1178, 580), radius=6 * ss, fill=(70, 6, 10, 255))
    f_small = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Bold.otf", 26 * ss)
    f_big = ImageFont.truetype(str(fonts / "Anton-Regular.ttf"), 128 * ss)
    f_sub = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 28 * ss)
    def ctext(y, t, f, fill):
        w = d.textlength(t, font=f)
        d.text(((945 * ss - w / 2), y * ss), t, font=f, fill=fill)
    ctext(328, "DISTRIBUTEUR  ·  RETRAIT", f_small, (255, 170, 170, 255))
    ctext(372, "REFUSÉ", f_big, (255, 255, 255, 255))
    ctext(530, "Autorisation impossible", f_sub, (255, 190, 190, 255))
    # fente de carte et clavier
    d.rounded_rectangle(S(820, 640, 1070, 660), radius=6 * ss, fill=(10, 10, 12, 255), outline=AMBER + (255,), width=2 * ss)
    atm = atm.resize((W, H), Image.LANCZOS)
    # halo rouge autour de l'écran
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(glow).rounded_rectangle((700, 300, 1190, 590), radius=10, outline=RED + (255,), width=18)
    glow = glow.filter(ImageFilter.GaussianBlur(26))
    glow = Image.alpha_composite(glow, glow)
    right = Image.alpha_composite(atm, glow)
    # fondu entre Marc (gauche) et le nouveau fond (droite)
    gx = np.arange(W, dtype=np.float32)
    ramp = np.clip((gx - 540) / 80, 0, 1)
    mask = Image.fromarray((np.tile(ramp, (H, 1)) * 255).astype(np.uint8), "L")
    keep = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    keep.paste(right, (0, 0), mask)
    img = Image.alpha_composite(base, keep)
    # Marc repasse devant le distributeur (sa main et son épaule, à gauche du fondu)
    marc = base.copy()
    mm = Image.fromarray((np.tile(1 - np.clip((gx - 560) / 40, 0, 1), (H, 1)) * 255).astype(np.uint8), "L")
    marc.putalpha(mm)
    img = Image.alpha_composite(img, marc)
    f_title = ImageFont.truetype(str(fonts / "Anton-Regular.ttf"), 172)
    img = big_text(img, (672, 26), "HEURE 2", f_title, YELLOW)
    img.convert("RGB").save(out / "miniature_B_heure2_refuse.png", optimize=True)
    return img


def thumb_c(g: Globe, fonts: Path, out: Path):
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    rad = np.exp(-(((gx - 820) / 700) ** 2 + ((gy - 430) / 500) ** 2))
    bg = np.zeros((H, W, 4), np.uint8)
    bg[..., 0] = np.clip(NAVY[0] + 12 * rad, 0, 255)
    bg[..., 1] = np.clip(NAVY[1] + 26 * rad, 0, 255)
    bg[..., 2] = np.clip(NAVY[2] + 48 * rad, 0, 255)
    bg[..., 3] = 255
    img = Image.alpha_composite(Image.fromarray(bg, "RGBA"), stars(W, H, 260, seed=21))
    cx, cy, R = 830, 470, 430
    lon0, lat0 = 12, 38
    h = halo(R, width=0.16, alpha=230)
    img.alpha_composite(h, (cx - h.width // 2, cy - h.height // 2))
    on = g.render(R, lon0, lat0, light=(0.2, 0.2, -1.0), night_gain=6.0)
    off = g.render(R, lon0, lat0, light=(0.2, 0.2, -1.0), night_gain=0.12)
    # frontière de la panne : ligne irrégulière en diagonale, l'est déjà éteint
    yy, xx = np.mgrid[-R:R, -R:R].astype(np.float32)
    rng = np.random.default_rng(4)
    wob = sum(a * np.sin(yy / R * f + p) for a, f, p in zip(rng.uniform(8, 22, 4), (5, 9, 17, 31), rng.uniform(0, 6, 4)))
    edge = xx + 0.35 * yy + 10 + wob  # passe à l'est de Paris
    m = np.clip(0.5 - edge / 6, 0, 1)  # 1 = encore allumé
    on_a = np.asarray(on, np.float32)
    off_a = np.asarray(off, np.float32)
    off_a[..., :3] *= 0.35  # côté éteint plus sombre
    mix = on_a * m[..., None] + off_a * (1 - m[..., None])
    globe = Image.fromarray(mix.astype(np.uint8), "RGBA")
    img.alpha_composite(globe, (cx - R, cy - R))
    # liseré ambre le long de la frontière
    front = Image.new("RGBA", (2 * R, 2 * R), (0, 0, 0, 0))
    band = np.exp(-(edge / 3.5) ** 2) * (np.asarray(on)[..., 3] / 255)
    fa = np.zeros((2 * R, 2 * R, 4), np.uint8)
    fa[..., :3] = AMBER
    fa[..., 3] = (band * 200).astype(np.uint8)
    front = Image.fromarray(fa, "RGBA")
    glowf = front.filter(ImageFilter.GaussianBlur(8))
    img.alpha_composite(glowf, (cx - R, cy - R))
    img.alpha_composite(front, (cx - R, cy - R))
    img = Image.alpha_composite(img, glow_layer((W, H), lambda d, s: draw_network(d, g, cx, cy, R, lon0, lat0, s, width=2.6), 3))
    f_title = ImageFont.truetype(str(fonts / "Anton-Regular.ttf"), 210)
    img = big_text(img, (48, 30), "JOUR 2", f_title, AMBER, outline=(110, 50, 0))
    tag = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 34)
    d = ImageDraw.Draw(img)
    d.text((58, 300), "T+48:00:00", font=tag, fill=CYAN + (230,))
    img.convert("RGB").save(out / "miniature_C_jour2_europe.png", optimize=True)
    return img


def sheet(imgs: dict, out: Path):
    """Les miniatures côte à côte, en grand et à la taille d'un téléphone (environ 170 px de large)."""
    cols = len(imgs)
    sh = Image.new("RGB", (cols * 660 + 20, 640), (245, 245, 245))
    d = ImageDraw.Draw(sh)
    f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 22)
    for i, (name, im) in enumerate(imgs.items()):
        x = 20 + i * 660
        d.text((x, 10), name, font=f, fill=(20, 20, 20))
        sh.paste(im.convert("RGB").resize((640, 360), Image.LANCZOS), (x, 45))
        sh.paste(im.convert("RGB").resize((170, 96), Image.LANCZOS), (x, 430))
        sh.paste(im.convert("RGB").resize((246, 138), Image.LANCZOS), (x + 190, 430))
    sh.save(out / "comparaison_miniatures.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True, help="miniature actuelle (version A)")
    ap.add_argument("--textures", type=Path, required=True)
    ap.add_argument("--fonts", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    g = Globe(a.textures)
    imgs = {"A (actuelle)": Image.open(a.source).convert("RGBA").resize((W, H), Image.LANCZOS),
            "B : HEURE 2 + REFUSÉ": thumb_b(a.source, a.fonts, a.out),
            "C : JOUR 2 + Europe": thumb_c(g, a.fonts, a.out)}
    sheet(imgs, a.out)


if __name__ == "__main__":
    main()
