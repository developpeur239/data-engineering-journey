"""
Génère apercu-autonome.html : la page d'accueil en UN SEUL fichier
(styles, scripts, Three.js, images et polices intégrés), pour la montrer
sans serveur ni dossiers annexes (téléphone, pièce jointe, aperçu).

Usage, depuis le dossier mondes-du-soleil :
    python outils/apercu-autonome.py

Ce fichier sert uniquement à l'aperçu : pour la mise en ligne et
l'intégration WordPress, utiliser index.html, style.css et script.js.
"""
import base64
import mimetypes
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
mimetypes.add_type("image/webp", ".webp")
mimetypes.add_type("font/woff2", ".woff2")


def data_uri(chemin: str) -> str:
    fichier = RACINE / chemin
    type_mime = mimetypes.guess_type(fichier.name)[0] or "application/octet-stream"
    return f"data:{type_mime};base64,{base64.b64encode(fichier.read_bytes()).decode()}"


html = (RACINE / "index.html").read_text(encoding="utf-8")
css = (RACINE / "style.css").read_text(encoding="utf-8")
js = (RACINE / "script.js").read_text(encoding="utf-8")
three = (RACINE / "vendor/three.min.js").read_text(encoding="utf-8")

# Polices : url("assets/fonts/...") -> data URI
css = re.sub(r'url\("(assets/fonts/[^"]+)"\)', lambda m: f'url("{data_uri(m.group(1))}")', css)

# Images : on garde une seule taille par image (src), sans srcset
html = re.sub(r"\s*<source [^>]*>", "", html)
html = re.sub(r'(<img [^>]*?)src="(assets/[^"]+)"', lambda m: f'{m.group(1)}src="{data_uri(m.group(2))}"', html)
html = re.sub(r'\s+loading="lazy"', "", html)

# En-tête : préchargements et icônes inutiles en fichier unique
html = re.sub(r'\s*<link rel="preload"[^>]*>', "", html)
html = re.sub(r'\s*<link rel="(?:icon|apple-touch-icon)"[^>]*>', "", html)
html = html.replace('<link rel="stylesheet" href="style.css">', f"<style>\n{css}\n</style>")

# Scripts : Three.js puis script.js, intégrés en fin de page
html = html.replace(
    '<script src="script.js" defer></script>',
    f"<script>\n{three}\n</script>\n  <script>\n{js}\n</script>",
)

# Marqueur : les polices sont déjà intégrées (pas de chargement hors ligne)
html = html.replace('<html lang="fr">', '<html lang="fr" data-autonome>', 1)
html = html.replace(
    "<head>",
    "<head>\n  <!-- Aperçu autonome généré par outils/apercu-autonome.py : ne pas modifier à la main -->",
    1,
)

reste = re.findall(r'(?:src|href)="(?:assets|vendor)/[^"]+"', html)
assert not reste, f"Références externes restantes : {reste}"

sortie = RACINE / "apercu-autonome.html"
sortie.write_text(html, encoding="utf-8")
print(f"{sortie.name} : {sortie.stat().st_size / 1024 / 1024:.1f} Mo")
