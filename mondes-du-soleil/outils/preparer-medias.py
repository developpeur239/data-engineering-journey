"""
Prépare les médias réalistes du hero à partir des fichiers générés (Flow…)
et écrit assets/medias.js, lu par la page. Voir MEDIAS.md.

Fichiers attendus dans medias-source/ (tous facultatifs) :
  maison-1.mp4, maison-2.mp4…   vidéo de la maison (16:9), plusieurs
                                clips enchaînés dans l'ordre alphabétique
  maison-vertical-1.mp4…        même scène en 9:16 pour mobile (sinon,
                                recadrage automatique au centre)
  bonhomme-salut.mp4            le bonhomme qui arrive et salue, sur fond vert
  regard/grille.png             grille des directions du regard (fond vert),
                                découpée selon --grille (5x5 par défaut)
  ou regard/l1-c1.png … l5-c5.png  une image par direction
                                (l = ligne de haut en bas, c = colonne de gauche à droite)

Usage, depuis le dossier mondes-du-soleil (ffmpeg doit être installé) :
    python outils/preparer-medias.py
    python outils/preparer-medias.py --images-sequence 150 --grille 3x3
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "medias-source"
SORTIE = RACINE / "assets"


def ffmpeg(*args):
    commande = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *map(str, args)]
    resultat = subprocess.run(commande, capture_output=True, text=True)
    if resultat.returncode != 0:
        sys.exit(f"Erreur ffmpeg : {resultat.stderr.strip()}\nCommande : {' '.join(commande)}")


def duree(video: Path) -> float:
    sortie = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
        capture_output=True, text=True,
    )
    return float(sortie.stdout.strip())


def tri_naturel(chemins):
    return sorted(chemins, key=lambda p: [int(t) if t.isdigit() else t for t in re.split(r"(\d+)", p.name)])


def url(chemin: Path) -> str:
    return chemin.relative_to(RACINE).as_posix()


def extraire_sequence(videos, dossier: Path, nb_images: int, filtre: str, qualite: int):
    """Découpe une ou plusieurs vidéos (enchaînées) en nb_images images WebP."""
    if dossier.exists():
        shutil.rmtree(dossier)
    dossier.mkdir(parents=True)
    total = sum(duree(v) for v in videos)
    ips = nb_images / total
    images = []
    with tempfile.TemporaryDirectory() as tmp:
        for n, video in enumerate(videos):
            ffmpeg("-i", video, "-vf", f"fps={ips:.4f},{filtre}", "-c:v", "libwebp",
                   "-quality", qualite, f"{tmp}/v{n:02d}-%04d.webp")
        for i, image in enumerate(tri_naturel(Path(tmp).glob("*.webp")), start=1):
            cible = dossier / f"img-{i:03d}.webp"
            shutil.move(image, cible)
            images.append(url(cible))
    return images


def detourage(couleur: str, similarite: float) -> str:
    """Filtre ffmpeg : fond vert rendu transparent, débordement vert retiré."""
    return f"chromakey=color={couleur}:similarity={similarite}:blend=0.05,despill=type=green"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--images-sequence", type=int, default=120, help="nombre d'images de la vidéo maison (défaut 120)")
    parser.add_argument("--grille", default="5x5", help="colonnes x lignes de la grille du regard (défaut 5x5)")
    parser.add_argument("--couleur-fond", default="0x00B140", help="couleur du fond à détourer (défaut vert 0x00B140)")
    parser.add_argument("--similarite", type=float, default=0.15, help="tolérance du détourage (défaut 0,15 ; monter si un liseré vert reste)")
    parser.add_argument("--apparition", type=float, default=0.78, help="moment d'arrivée du bonhomme, de 0 à 1 (défaut 0,78)")
    parser.add_argument("--hauteur-bonhomme", type=int, default=720, help="hauteur des images du bonhomme en px")
    args = parser.parse_args()

    if not shutil.which("ffmpeg"):
        sys.exit("ffmpeg est introuvable : installez-le (https://ffmpeg.org) puis relancez.")
    colonnes, lignes = (int(x) for x in args.grille.lower().split("x"))
    medias = {
        "sequence": {"ordinateur": [], "mobile": []},
        "bonhomme": {
            "apparition": args.apparition, "ips": 24, "salut": [],
            "regard": {"colonnes": colonnes, "lignes": lignes, "tete": [0.5, 0.22], "images": []},
        },
    }

    # 1. Vidéo de la maison
    horizontales = tri_naturel(p for p in SOURCE.glob("maison*.mp4") if "vertical" not in p.name)
    verticales = tri_naturel(SOURCE.glob("maison-vertical*.mp4"))
    if horizontales:
        medias["sequence"]["ordinateur"] = extraire_sequence(
            horizontales, SORTIE / "sequence/ordinateur", args.images_sequence, "scale=1600:-2", 70)
        if verticales:
            medias["sequence"]["mobile"] = extraire_sequence(
                verticales, SORTIE / "sequence/mobile", args.images_sequence, "scale=720:-2", 68)
        else:
            medias["sequence"]["mobile"] = extraire_sequence(
                horizontales, SORTIE / "sequence/mobile", args.images_sequence,
                "crop='min(iw,ih*9/16)':ih,scale=720:-2", 68)
        print(f"Maison : {len(medias['sequence']['ordinateur'])} images (ordinateur et mobile)")

    filtre_bonhomme = f"{detourage(args.couleur_fond, args.similarite)},scale=-2:{args.hauteur_bonhomme},format=yuva420p"

    # 2. Salut du bonhomme
    salut = SOURCE / "bonhomme-salut.mp4"
    if salut.exists():
        dossier = SORTIE / "bonhomme/salut"
        if dossier.exists():
            shutil.rmtree(dossier)
        dossier.mkdir(parents=True)
        ffmpeg("-i", salut, "-vf", f"fps=24,{filtre_bonhomme}", "-c:v", "libwebp",
               "-quality", 80, dossier / "img-%03d.webp")
        medias["bonhomme"]["salut"] = [url(p) for p in tri_naturel(dossier.glob("*.webp"))]
        print(f"Salut : {len(medias['bonhomme']['salut'])} images détourées")

    # 3. Grille du regard
    dossier_regard = SOURCE / "regard"
    if dossier_regard.exists():
        sortie = SORTIE / "bonhomme/regard"
        if sortie.exists():
            shutil.rmtree(sortie)
        sortie.mkdir(parents=True)
        with tempfile.TemporaryDirectory() as tmp:
            grille = next(iter(dossier_regard.glob("grille.*")), None)
            if grille:
                from PIL import Image  # pip install pillow
                planche = Image.open(grille).convert("RGB")
                lc, hc = planche.width // colonnes, planche.height // lignes
                for l in range(lignes):
                    for c in range(colonnes):
                        planche.crop((c * lc, l * hc, (c + 1) * lc, (l + 1) * hc)).save(f"{tmp}/l{l + 1}-c{c + 1}.png")
                sources = Path(tmp)
            else:
                sources = dossier_regard
            images = []
            for l in range(1, lignes + 1):
                for c in range(1, colonnes + 1):
                    fichier = next(iter(sources.glob(f"l{l}-c{c}.*")), None)
                    if not fichier:
                        sys.exit(f"Image du regard manquante : regard/l{l}-c{c}.png (grille {colonnes}x{lignes})")
                    cible = sortie / f"l{l}-c{c}.webp"
                    ffmpeg("-i", fichier, "-vf", filtre_bonhomme, "-c:v", "libwebp", "-quality", 80, cible)
                    images.append(url(cible))
        medias["bonhomme"]["regard"]["images"] = images
        print(f"Regard : {len(images)} directions ({colonnes}x{lignes})")

    js = json.dumps(medias, indent=2, ensure_ascii=False)
    (SORTIE / "medias.js").write_text(
        "/* Médias du hero : fichier GÉNÉRÉ par outils/preparer-medias.py (voir MEDIAS.md). */\n"
        f"window.MDS_MEDIAS = {js};\n",
        encoding="utf-8",
    )
    print("assets/medias.js mis à jour. Pensez à régénérer l'aperçu : python outils/apercu-autonome.py")


if __name__ == "__main__":
    main()
