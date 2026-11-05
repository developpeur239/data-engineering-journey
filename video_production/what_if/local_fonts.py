"""Télécharge les polices Google du studio What If et réécrit fonts.ts pour les charger en local.
    python local_fonts.py <public/fonts> <src/engine/fonts.ts>
"""
import re
import subprocess
import sys
from pathlib import Path

out, fonts_ts = Path(sys.argv[1]), Path(sys.argv[2])
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
URL = ("https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800"
       "&family=Fragment+Mono&family=Kalam:wght@400;700&display=swap")
css = subprocess.run(["curl", "-sS", "-A", UA, URL], capture_output=True, text=True, check=True).stdout
faces = []
for subset, body in re.findall(r"/\* (\S+) \*/\s*@font-face \{(.*?)\}", css, re.S):
    if subset != "latin":
        continue
    fam = re.search(r"font-family: '([^']+)'", body).group(1)
    w = re.search(r"font-weight: (\d+)", body).group(1)
    src = re.search(r"url\((\S+?\.woff2)\)", body).group(1)
    name = f"{fam.replace(' ', '')}-{w}.woff2"
    subprocess.run(["curl", "-sS", "-o", str(out / name), src], check=True)
    faces.append((fam, w, f"fonts/{name}"))
entries = "\n".join(f"  {{ family: '{f}', weight: '{w}', file: '{p}' }}," for f, w, p in faces)
fonts_ts.write_text(f"""import {{ loadFont }} from '@remotion/fonts';
import {{ staticFile }} from 'remotion';
import {{ STUDIO }} from '../studio.config';

// Polices Google servies en local depuis public/fonts (rendu hors ligne).
const LOCAL = [
{entries}
];
for (const f of LOCAL) loadFont({{ family: f.family, url: staticFile(f.file), weight: f.weight }});
if (STUDIO.titleFont) loadFont({{ family: STUDIO.titleFont.family, url: staticFile(STUDIO.titleFont.file), weight: STUDIO.titleFont.weight }});

export const FONT = {{
  title: STUDIO.titleFont ? STUDIO.titleFont.family : 'Bricolage Grotesque',
  ui: 'Fragment Mono',
  hand: 'Kalam',
}};
""")
print(f"{len(faces)} polices locales, fonts.ts réécrit")
