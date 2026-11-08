"""Miniatures YouTube (1280x720) à partir d'images propres du studio 3D (render.py --stills ... --clean).

    python thumbnails.py <dossier_images_propres> <police Bricolage .ttf> <sortie>

Trois formats : POV / curiosité (cercle rouge), temps (horodatage au milieu de l'histoire), tableau d'enquête.
Règles : 2 à 4 mots maximum, texte très gros et contrasté, un seul point focal, lisible en petit (test à 320 px).
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

W, H = 1280, 720
ORANGE, RED, WHITE, NAVY = (245, 165, 36), (255, 70, 75), (245, 246, 247), (12, 18, 28)


def font(path, size, wght=800, wdth=100):
    f = ImageFont.truetype(str(path), size)
    try:
        axes = f.get_variation_axes()
        vals = []
        for ax in axes:
            n = ax.get("name", b"")
            n = n.decode() if isinstance(n, bytes) else str(n)
            vals.append({"Weight": wght, "Width": wdth}.get(n, ax.get("default", ax["minimum"])))
        f.set_variation_by_axes(vals)
    except Exception:
        pass
    return f


def cover(im, w=W, h=H, focus=(0.5, 0.5)):
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    x = int((im.width - w) * focus[0]); y = int((im.height - h) * focus[1])
    return im.crop((x, y, x + w, y + h))


def text_block(img, xy, text, f, fill=WHITE, stroke=10, shadow=True, anchor="la"):
    d = ImageDraw.Draw(img)
    if shadow:
        sh = Image.new("RGBA", img.size, (0, 0, 0, 0)); ds = ImageDraw.Draw(sh)
        ds.text((xy[0] + 6, xy[1] + 10), text, font=f, fill=(0, 0, 0, 200), anchor=anchor, stroke_width=stroke, stroke_fill=(0, 0, 0, 200))
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(10)))
    d.text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=(8, 10, 14))


def vignette(img, k=0.55):
    """Bords assombris en douceur (le centre reste intact)."""
    import numpy as np  # noqa: PLC0415
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    a = (np.clip((r - 0.55) / 0.75, 0, 1) ** 1.6 * 255 * k).astype("uint8")
    shade = Image.new("RGBA", img.size, (0, 0, 0, 0)); shade.putalpha(Image.fromarray(a))
    img.alpha_composite(shade)


def zoom(im, z, cx, cy):
    """Recadrage serré autour du sujet (cx, cy en fraction de l'image)."""
    w, h = im.width / z, im.height / z
    x0 = min(max(0, im.width * cx - w / 2), im.width - w); y0 = min(max(0, im.height * cy - h / 2), im.height - h)
    return im.crop((int(x0), int(y0), int(x0 + w), int(y0 + h)))


def pov(src: Path, fnt: Path, out: Path):
    """Format POV / curiosité : la carte refusée, un cercle rouge sur l'écran, « 72 H SANS INTERNET »."""
    im = cover(zoom(Image.open(src / "s02_5.70.jpg").convert("RGB"), 1.35, 0.68, 0.42))
    im = ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.3)).enhance(1.15)).enhance(1.15).convert("RGBA")
    vignette(im, 0.5)
    d = ImageDraw.Draw(im)
    cx, cy, r = 660, 478, 118                        # la croix rouge de l'écran
    for w_, col in ((24, (255, 255, 255, 110)), (12, RED)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w_)
    d.line([(cx + r * 0.75, cy - r * 0.75), (930, 330)], fill=RED, width=12)      # flèche du texte vers le refus
    text_block(im, (1240, 40), "72 H", font(fnt, 250, 800, 75), ORANGE, anchor="ra")
    text_block(im, (1240, 330), "SANS", font(fnt, 120, 800, 75), anchor="ra")
    text_block(im, (1240, 450), "INTERNET", font(fnt, 120, 800, 75), anchor="ra")
    im.convert("RGB").save(out / "miniature_A_pov.jpg", quality=92)


def time_fmt(src: Path, fnt: Path, out: Path):
    """Format temps : un instant au milieu de l'histoire (heure 06), le père et son fils devant la machine."""
    im = cover(zoom(Image.open(src / "s22_5.50.jpg").convert("RGB"), 1.45, 0.47, 0.46))
    im = ImageEnhance.Brightness(ImageEnhance.Contrast(ImageEnhance.Color(im).enhance(1.25)).enhance(1.12)).enhance(1.15).convert("RGBA")
    vignette(im, 0.5)
    d = ImageDraw.Draw(im)
    f = font(fnt, 70, 700, 100)
    d.rounded_rectangle([56, 52, 470, 140], 14, fill=(10, 12, 16, 220), outline=RED, width=5)
    d.ellipse([84, 82, 112, 110], fill=RED)
    d.text((132, 96), "HEURE 06", font=f, fill=WHITE, anchor="lm")
    text_block(im, (60, 380), "PLUS RIEN", font(fnt, 150, 800, 75))
    text_block(im, (60, 540), "NE MARCHE", font(fnt, 150, 800, 75), ORANGE)
    im.convert("RGB").save(out / "miniature_B_temps.jpg", quality=92)


def pinboard(src: Path, fnt: Path, out: Path):
    """Tableau d'enquête : quatre preuves reliées au fil rouge, au centre « 72 H »."""
    rnd = random.Random(7)
    board = Image.new("RGBA", (W, H), (150, 102, 58, 255))
    px = board.load()
    for y in range(H):                                   # liège : grain tacheté
        for x in range(0, W, 2):
            n = rnd.randint(-28, 28); c = px[x, y]
            v = (max(0, min(255, c[0] + n)), max(0, min(255, c[1] + n)), max(0, min(255, c[2] + n // 2)), 255)
            px[x, y] = v; px[min(W - 1, x + 1), y] = v
    board = board.filter(ImageFilter.GaussianBlur(0.8))
    shots = [("s17_5.00.jpg", (40, 40), -6), ("s02_5.70.jpg", (900, 30), 5), ("s24_6.00.jpg", (60, 400), 4), ("s07_6.00.jpg", (880, 395), -5)]
    labels = ["CROWDSTRIKE · 2024", "CARTE REFUSÉE", "DISTRIBUTEURS", "5 000 VOLS ANNULÉS"]
    pins = []
    fl = font(fnt, 26, 700, 100)
    for (name, (x, y), ang), lab in zip(shots, labels):
        ph = cover(Image.open(src / name).convert("RGB"), 340, 210)
        card = Image.new("RGBA", (370, 290), (246, 243, 236, 255)); card.paste(ph, (15, 15))
        ImageDraw.Draw(card).text((185, 258), lab, font=fl, fill=(30, 30, 30), anchor="mm")
        sh = Image.new("RGBA", (card.width + 40, card.height + 40), (0, 0, 0, 0)); ImageDraw.Draw(sh).rectangle([20, 26, card.width + 20, card.height + 26], fill=(0, 0, 0, 150))
        sh = sh.filter(ImageFilter.GaussianBlur(12)).rotate(ang, expand=True, resample=Image.BICUBIC)
        rc = card.rotate(ang, expand=True, resample=Image.BICUBIC)
        board.alpha_composite(sh, (x - 20, y - 14)); board.alpha_composite(rc, (x, y))
        pins.append((x + rc.width // 2, y + 18))
    d = ImageDraw.Draw(board)
    cx, cy = W // 2, H // 2 + 10
    for (x, y) in pins:                                  # fil rouge vers la note centrale
        d.line([(x, y), (cx, cy - 80)], fill=(200, 20, 30), width=5)
    for (x, y) in pins + [(cx, cy - 80)]:
        d.ellipse([x - 13, y - 13, x + 13, y + 13], fill=(215, 30, 40), outline=(120, 10, 15), width=3)
        d.ellipse([x - 5, y - 9, x + 1, y - 3], fill=(255, 150, 150))
    note = Image.new("RGBA", (460, 300), (0, 0, 0, 0)); dn = ImageDraw.Draw(note)
    dn.rectangle([0, 0, 459, 299], fill=(250, 248, 240, 255))
    dn.text((230, 120), "72 H", font=font(fnt, 190, 800, 75), fill=(200, 20, 30), anchor="mm")
    dn.text((230, 245), "SANS INTERNET", font=font(fnt, 52, 800, 85), fill=(20, 20, 24), anchor="mm")
    note = note.rotate(-3, expand=True, resample=Image.BICUBIC)
    board.alpha_composite(note, (cx - note.width // 2, cy - note.height // 2 + 20))
    d = ImageDraw.Draw(board)
    d.ellipse([cx - 14, cy - 94, cx + 14, cy - 66], fill=(215, 30, 40), outline=(120, 10, 15), width=3)
    board.convert("RGB").save(out / "miniature_C_enquete.jpg", quality=92)


def preview(out: Path):
    """Planche de contrôle : les trois miniatures en grand et à la taille réelle d'un écran de téléphone (320 px)."""
    ims = [Image.open(out / n) for n in ("miniature_A_pov.jpg", "miniature_B_temps.jpg", "miniature_C_enquete.jpg")]
    sheet = Image.new("RGB", (640 * 3 + 40, 360 + 40 + 180), (18, 18, 18))
    for i, im in enumerate(ims):
        sheet.paste(im.resize((640, 360), Image.LANCZOS), (10 + i * 650, 10))
        sheet.paste(im.resize((320, 180), Image.LANCZOS), (10 + i * 650, 390))
    sheet.save(out / "planche_miniatures.jpg", quality=88)


if __name__ == "__main__":
    src, fnt, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    out.mkdir(parents=True, exist_ok=True)
    pov(src, fnt, out); time_fmt(src, fnt, out); pinboard(src, fnt, out); preview(out)
    print("ok")
