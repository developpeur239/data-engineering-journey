"""Planche de comparaison : la référence 2D (personnage recadré) à côté des rendus face / trois-quarts / profil."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

here = Path(__file__).resolve().parent
name, box = sys.argv[1], tuple(int(v) for v in sys.argv[2].split(","))   # ex. lea 100,260,450,860
ref = Image.open(here.parents[1] / "references_design/personnages/reference_2d.png").convert("RGB").crop(box)
views = [Image.open(here / "renders" / f"{name}_{v}.png").convert("RGB") for v in ("face", "trois_quarts", "profil")]
H = 900
tiles = [ref.resize((int(ref.width * H / ref.height), H))] + [v.resize((int(v.width * H / v.height), H)) for v in views]
W = sum(t.width for t in tiles) + 20 * (len(tiles) + 1)
sheet = Image.new("RGB", (W, H + 110), (40, 42, 46)); d = ImageDraw.Draw(sheet)
font = ImageFont.truetype(str(here.parents[1] / "prototype/fonts/InstrumentSans-Bold.ttf"), 34)
x = 20
for t, lab in zip(tiles, ["Référence 2D", "3D · face", "3D · trois-quarts", "3D · profil"]):
    sheet.paste(t, (x, 90)); d.text((x, 30), lab, fill=(235, 236, 238), font=font); x += t.width + 20
out = here / "renders" / f"{name}_comparaison.png"; sheet.save(out); print(out)
