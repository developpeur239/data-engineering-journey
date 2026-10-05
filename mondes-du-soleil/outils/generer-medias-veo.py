"""
Génère les médias réalistes du hero avec l'API Gemini de Google
(Veo pour les vidéos, modèle d'image Gemini pour le bonhomme),
puis les dépose dans medias-source/ pour outils/preparer-medias.py.

Prérequis : une clé API Gemini (Google AI Studio) avec facturation
activée, dans la variable d'environnement GEMINI_API_KEY.
Veo est payant à la seconde de vidéo générée : voir la grille tarifaire
de Google avant de lancer (https://ai.google.dev/pricing).

Usage, depuis le dossier mondes-du-soleil :
    python outils/generer-medias-veo.py --modeles          # liste les modèles disponibles
    python outils/generer-medias-veo.py maison             # 3 clips enchaînés (16:9)
    python outils/generer-medias-veo.py bonhomme           # portrait + salut + regard 3x3
    python outils/generer-medias-veo.py tout
Les prompts sont ceux de MEDIAS.md.
"""
import argparse
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
SOURCE = RACINE / "medias-source"
API = "https://generativelanguage.googleapis.com/v1beta"

PROMPTS_MAISON = [
    "Photorealistic cinematic shot of a single-story house in Gironde, southwest France: cream lime-render walls, "
    "terracotta Roman tile roof, wooden shutters, small garden with lavender and an olive tree. Blue hour just before "
    "dawn, deep navy sky with a few fading stars, soft cool light, no people. The camera slowly orbits from the "
    "front-left of the house toward the front, at roof height, smooth gimbal movement. Full-frame cinema camera, "
    "35mm lens, natural colors, high detail, no text, no logos.",
    "Continue the same slow orbit around the same house. Sleek all-black monocrystalline solar panels appear on the "
    "roof one after another in a neat grid of two rows of five, each one settling gently into place, realistic black "
    "frames and mounting rails. The sky slowly brightens from navy to deep blue. Photorealistic, no people, no text.",
    "Continue the same slow orbit, ending in front of the house. The sun rises above the trees on the horizon, warm "
    "golden light washes over the facade, the black solar panels catch a bright golden reflection, and warm lights "
    "turn on inside the windows. Golden hour, photorealistic, subtle lens flare, no people, no text.",
]
PROMPT_PORTRAIT = (
    "Photorealistic waist-up portrait of a friendly French solar panel installer in his thirties, warm genuine smile, "
    "short dark hair, light stubble, wearing a charcoal grey t-shirt with a small embroidered orange logo on the chest "
    "that reads \"Mondes du Soleil\", standing straight, facing the camera, arms relaxed. Plain flat chroma-key green "
    "background (#00B140), evenly lit soft studio lighting, no shadow on the background, sharp focus, natural skin "
    "texture. Vertical 9:16 framing."
)
PROMPT_SALUT = (
    "He walks into frame from the right, stops in the center, smiles and waves hello with his right hand, then lowers "
    "his hand and looks straight at the camera, smiling. Static locked-off camera, plain flat chroma-key green "
    "background, even lighting, photorealistic."
)
DIRECTIONS = {
    "l1-c1": "top left", "l1-c2": "top", "l1-c3": "top right",
    "l2-c1": "left", "l2-c3": "right",
    "l3-c1": "bottom left", "l3-c2": "bottom", "l3-c3": "bottom right",
}
PROMPT_REGARD = (
    "Same man, same framing, same size, same lighting, same green background, same smile. Only his head and eyes "
    "turn slightly to look toward the {direction} of the frame. Natural, subtle movement."
)


# ------------------------------------------------------------------ API
def cle() -> str:
    valeur = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not valeur:
        sys.exit("Clé absente : définissez GEMINI_API_KEY dans les variables d'environnement.")
    return valeur


def requete(methode: str, chemin: str, corps=None, brut=False):
    url = chemin if chemin.startswith("http") else f"{API}/{chemin}"
    donnees = json.dumps(corps).encode() if corps is not None else None
    req = urllib.request.Request(url, data=donnees, method=methode,
                                 headers={"x-goog-api-key": cle(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=300) as rep:
            contenu = rep.read()
            return contenu if brut else json.loads(contenu)
    except urllib.error.HTTPError as e:
        sys.exit(f"Erreur API {e.code} sur {chemin} : {e.read().decode(errors='replace')[:800]}")


def modeles():
    resultat, jeton = [], ""
    while True:
        page = requete("GET", f"models?pageSize=200{'&pageToken=' + jeton if jeton else ''}")
        resultat += page.get("models", [])
        jeton = page.get("nextPageToken")
        if not jeton:
            return resultat


def choisir_modele(mot: str, methode: str, impose: str | None) -> str:
    if impose:
        return impose if impose.startswith("models/") else f"models/{impose}"
    candidats = [m["name"] for m in modeles()
                 if mot in m["name"] and methode in m.get("supportedGenerationMethods", [])]
    if not candidats:
        sys.exit(f"Aucun modèle « {mot} » disponible pour cette clé (méthode {methode}). Lancez --modeles.")
    # Le plus récent en premier (les noms portent le numéro de version)
    return sorted(candidats, reverse=True)[0]


def image_en_ligne(chemin: Path) -> dict:
    return {"bytesBase64Encoded": base64.b64encode(chemin.read_bytes()).decode(), "mimeType": "image/png"}


# ------------------------------------------------------------------ Vidéo (Veo)
def generer_video(modele: str, prompt: str, sortie: Path, ratio: str, premiere=None, derniere=None):
    instance = {"prompt": prompt}
    if premiere:
        instance["image"] = image_en_ligne(premiere)
    if derniere:
        instance["lastFrame"] = image_en_ligne(derniere)
    print(f"  Veo ({modele}) → {sortie.name}…")
    operation = requete("POST", f"{modele}:predictLongRunning",
                        {"instances": [instance], "parameters": {"aspectRatio": ratio}})
    while not operation.get("done"):
        time.sleep(10)
        operation = requete("GET", operation["name"])
    if "error" in operation:
        sys.exit(f"Veo a échoué : {operation['error']}")
    echantillons = operation["response"]["generateVideoResponse"]["generatedSamples"]
    sortie.write_bytes(requete("GET", echantillons[0]["video"]["uri"], brut=True))
    print(f"  ✔ {sortie.relative_to(RACINE)}")


def derniere_image(video: Path, sortie: Path) -> Path:
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-sseof", "-0.1", "-i", str(video),
                    "-frames:v", "1", str(sortie)], check=True)
    return sortie


# ------------------------------------------------------------------ Images (Gemini)
def generer_image(modele: str, prompt: str, sortie: Path, reference: Path | None = None):
    parties = [{"text": prompt}]
    if reference:
        parties.insert(0, {"inlineData": {"mimeType": "image/png",
                                          "data": base64.b64encode(reference.read_bytes()).decode()}})
    print(f"  Image ({modele}) → {sortie.name}…")
    reponse = requete("POST", f"{modele}:generateContent", {
        "contents": [{"parts": parties}],
        "generationConfig": {"responseModalities": ["IMAGE"]},
    })
    for partie in reponse["candidates"][0]["content"]["parts"]:
        if "inlineData" in partie:
            sortie.write_bytes(base64.b64decode(partie["inlineData"]["data"]))
            print(f"  ✔ {sortie.relative_to(RACINE)}")
            return sortie
    sys.exit(f"Aucune image renvoyée : {json.dumps(reponse)[:600]}")


# ------------------------------------------------------------------ Scénarios
def maison(veo: str, vertical: bool):
    ratio, prefixe = ("9:16", "maison-vertical") if vertical else ("16:9", "maison")
    precedent = None
    for i, prompt in enumerate(PROMPTS_MAISON, start=1):
        clip = SOURCE / f"{prefixe}-{i}.mp4"
        # Continuité : chaque clip démarre sur la dernière image du précédent
        premiere = derniere_image(precedent, SOURCE / f".{prefixe}-{i}-depart.png") if precedent else None
        generer_video(veo, prompt, clip, ratio, premiere=premiere)
        precedent = clip


def bonhomme(veo: str, imageur: str):
    (SOURCE / "regard").mkdir(parents=True, exist_ok=True)
    portrait = generer_image(imageur, PROMPT_PORTRAIT, SOURCE / "regard/l2-c2.png")
    print("  → Vérifiez la broderie « Mondes du Soleil » sur medias-source/regard/l2-c2.png avant de continuer.")
    generer_video(veo, PROMPT_SALUT, SOURCE / "bonhomme-salut.mp4", "9:16", derniere=portrait)
    for nom, direction in DIRECTIONS.items():
        generer_image(imageur, PROMPT_REGARD.format(direction=direction), SOURCE / f"regard/{nom}.png", portrait)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("quoi", nargs="?", choices=["maison", "bonhomme", "tout"])
    parser.add_argument("--modeles", action="store_true", help="liste les modèles vidéo et image disponibles")
    parser.add_argument("--vertical", action="store_true", help="génère aussi la maison en 9:16 pour mobile")
    parser.add_argument("--modele-video", help="impose un modèle Veo (sinon : le plus récent disponible)")
    parser.add_argument("--modele-image", help="impose un modèle d'image (sinon : le plus récent disponible)")
    args = parser.parse_args()

    if args.modeles:
        for m in modeles():
            if any(mot in m["name"] for mot in ("veo", "image", "imagen")):
                print(m["name"], m.get("supportedGenerationMethods"))
        return
    if not args.quoi:
        parser.error("indiquez maison, bonhomme ou tout (ou --modeles)")

    SOURCE.mkdir(exist_ok=True)
    veo = choisir_modele("veo", "predictLongRunning", args.modele_video)
    if args.quoi in ("maison", "tout"):
        maison(veo, vertical=False)
        if args.vertical:
            maison(veo, vertical=True)
    if args.quoi in ("bonhomme", "tout"):
        bonhomme(veo, choisir_modele("image", "generateContent", args.modele_image))
    print("\nTerminé. Étape suivante : python outils/preparer-medias.py --grille 3x3")


if __name__ == "__main__":
    main()
