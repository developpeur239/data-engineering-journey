"""Texte à l'écran épuré (inspiré de la logique de Last Soul, voir ../montage_guide.md section 10).

Deux familles seulement :
- PENSÉE / RÉPLIQUE : police arrondie (Comic Neue Bold), casse normale avec ponctuation, petite taille,
  contour fin et halo sombre flou derrière (pas de cadre). Couleur selon qui parle.
- CARTE (chapitre, citation, source, titre) : police à empattements (EB Garamond), blanc sur noir ou sur image
  assombrie, casse normale ; petites capitales espacées seulement pour une étiquette ou une signature.

Polices libres (OFL) à télécharger depuis github.com/google/fonts : ofl/comicneue/ComicNeue-Bold.ttf,
ofl/ebgaramond/EBGaramond[wght].ttf et EBGaramond-Italic[wght].ttf.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

VOICES = {  # couleur du texte selon qui parle
    "marc": (255, 255, 255),
    "autre": (120, 190, 255),
    "pensee": (214, 160, 110),   # excuse, pensée intérieure : plus discrète
    "alerte": (255, 120, 100),
}


class Typo:
    def __init__(self, fonts: Path, height: int = 1080):
        self.fonts = fonts
        self.k = height / 1080

    def _f(self, name: str, size: float) -> ImageFont.FreeTypeFont:
        return ImageFont.truetype(str(self.fonts / name), int(size * self.k))

    def thought(self, img: Image.Image, text: str, center: tuple[int, int], who: str = "marc", size: float = 44):
        """Une réplique ou une pensée, près du personnage. Halo sombre flou, aucun cadre."""
        f = self._f("ComicNeue-Bold.ttf", size)
        d = ImageDraw.Draw(img)
        x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f, stroke_width=2)
        w, h = x1 - x0, y1 - y0
        x, y = center[0] - w // 2, center[1] - h // 2
        halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
        pad_x, pad_y = int(w * 0.35 + 40 * self.k), int(h * 0.9 + 18 * self.k)
        ImageDraw.Draw(halo).ellipse((x - pad_x, y - pad_y, x + w + pad_x, y + h + pad_y), fill=(0, 0, 0, 150))
        halo = halo.filter(ImageFilter.GaussianBlur(28 * self.k))
        out = Image.alpha_composite(img.convert("RGBA"), halo)
        ImageDraw.Draw(out).text((x - x0, y - y0), text, font=f, fill=VOICES[who] + (255,),
                                 stroke_width=max(1, int(2 * self.k)), stroke_fill=(20, 20, 24, 255))
        return out

    def _spaced(self, d: ImageDraw.ImageDraw, xy, text: str, f, fill, spacing: float):
        x, y = xy
        for ch in text:
            d.text((x, y), ch, font=f, fill=fill)
            x += d.textlength(ch, font=f) + spacing
        return x

    def _spaced_width(self, d, text, f, spacing):
        return sum(d.textlength(ch, font=f) for ch in text) + spacing * (len(text) - 1)

    def card(self, img: Image.Image, lines: list[str], signature: str | None = None, label: str | None = None,
             italic: bool = False, size: float = 58, dim: float = 1.0):
        """Carte de chapitre, de citation ou de source, centrée. dim = assombrissement du fond (1 = noir complet)."""
        out = img.convert("RGBA")
        if dim > 0:
            out = Image.alpha_composite(out, Image.new("RGBA", out.size, (0, 0, 0, int(255 * dim))))
        d = ImageDraw.Draw(out)
        W, H = out.size
        f = self._f("EBGaramond-Italic.ttf" if italic else "EBGaramond.ttf", size)
        small = self._f("EBGaramond.ttf", size * 0.42)
        lh = int(size * 1.35 * self.k)
        total = lh * len(lines) + (int(90 * self.k) if signature else 0) + (int(80 * self.k) if label else 0)
        y = (H - total) // 2
        if label:
            t = label.upper()
            sp = 7 * self.k
            self._spaced(d, ((W - self._spaced_width(d, t, small, sp)) / 2, y), t, small, (200, 200, 200, 255), sp)
            y += int(80 * self.k)
        for line in lines:
            w = d.textlength(line, font=f)
            d.text(((W - w) / 2, y), line, font=f, fill=(242, 238, 230, 255))
            y += lh
        if signature:
            t = "—  " + signature.upper()
            sp = 5 * self.k
            y += int(40 * self.k)
            self._spaced(d, ((W - self._spaced_width(d, t, small, sp)) / 2, y), t, small, (190, 186, 178, 255), sp)
        return out

    def title(self, img: Image.Image, title: str, subtitle: str | None = None, size: float = 120):
        """Carte titre : grandes capitales très espacées, sous-titre en italique."""
        out = Image.alpha_composite(img.convert("RGBA"), Image.new("RGBA", img.size, (0, 0, 0, 255)))
        d = ImageDraw.Draw(out)
        W, H = out.size
        f = self._f("EBGaramond.ttf", size)
        sp = size * 0.28 * self.k
        t = title.upper()
        w = self._spaced_width(d, t, f, sp)
        y = H // 2 - int(size * 0.75 * self.k)
        self._spaced(d, ((W - w) / 2, y), t, f, (245, 242, 235, 255), sp)
        if subtitle:
            fs = self._f("EBGaramond-Italic.ttf", size * 0.3)
            ws = d.textlength(subtitle, font=fs)
            d.text(((W - ws) / 2, y + int(size * 1.45 * self.k)), subtitle, font=fs, fill=(200, 196, 188, 255))
        return out


# --------------------------------------------------------------------------- #
# Casse normale pour le texte écrit en capitales dans scenes.py (le texte n'est pas modifié, seulement son affichage)
# --------------------------------------------------------------------------- #
KEEP_UPPER = {"DNS", "AWS", "UTC", "FM", "US", "SAMU", "KO", "OK", "UE", "BCE", "ANSSI", "NOTAM", "FAA", "TV"}
PROPER = {
    "paris": "Paris", "delta": "Delta", "microsoft": "Microsoft", "windows": "Windows", "parametrix": "Parametrix",
    "canada": "Canada", "rogers": "Rogers", "orange": "Orange", "corbeil-essonnes": "Corbeil-Essonnes", "tonga": "Tonga",
    "crowdstrike": "CrowdStrike", "marc": "Marc", "france": "France", "banque": "Banque", "internet": "Internet",
    "interac": "Interac", "europe": "Europe",
}
SMALL_UNITS = {"h": "h", "min": "min"}


def sentence_case(text: str) -> str:
    """« PANNE DNS · 72 HEURES » → « Panne DNS · 72 heures ». Chaque segment séparé par « · » ou « : »
    commence par une majuscule ; sigles et noms propres gardés."""
    import re  # noqa: PLC0415
    if not text or text != text.upper():
        return text                      # déjà en casse normale : on n'y touche pas
    out = []
    start = not text.lstrip().startswith("…")
    for tok in re.split(r"(\s+|·|:|&|\?|!|\|)", text):
        if not tok or tok.isspace() or tok in "·:&?!|":
            out.append(tok)
            if tok in ("·", ":", "?", "!"):
                start = True
            continue
        core = tok.strip(".,;()…'\"«»")
        low = tok.lower()
        if core in KEEP_UPPER or any(ch.isdigit() for ch in core) and core.upper() == core and not core.isalpha():
            word = tok if core in KEEP_UPPER else low       # « 72 H » → « 72 h », « 5,4 » inchangé
        elif core.lower() in PROPER:
            word = low.replace(core.lower(), PROPER[core.lower()])
        else:
            word = low
        if start and word[:1].isalpha():
            word = word[0].upper() + word[1:]
        if any(ch.isalnum() for ch in word):
            start = False
        out.append(word)
    s = "".join(out)
    s = re.sub(r"\b(\d+) H\b", r"\1 h", s)
    return s
