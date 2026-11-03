"""Plan de montage scène par scène (voir ../montage_guide.md). Le texte des voix (scenes.py) n'est pas modifié.

Numéros de scène de 1 à 64. Les phrases d'une scène sont numérotées à partir de 0 (découpage sur . ? !).
"""

# Pauses ajoutées APRÈS une phrase (secondes) : respirations « ping-pong » de l'intro et moments clés
PAUSES = {
    1: {1: 0.35, 3: 0.3},
    2: {1: 0.55},                 # blanc avant la phrase-motif dite dans la coupure de musique
    4: {2: 0.45},                 # blanc avant « Et si Internet s'arrêtait soixante-douze heures ? »
    16: {1: 0.7},                # « Soixante-dix-huit minutes. » puis impact dans le blanc
    17: {0: 0.5},                 # « Minute zéro. » puis impact fort
    25: {1: 0.4},                 # blanc avant « Puis, plus rien. »
    50: {0: 0.6},                 # « Et voici le détail qui change tout. »
    53: {1: 0.7},
    54: {2: 1.4},                 # moment clé : silence avant « Son fils est tiré d'affaire. »
    57: {0: 0.6},                 # « Maintenant, la vérité. »
}

# Silence en fin de scène (défaut 0,45 s)
PAD = {2: 0.7, 4: 0.8, 49: 0.9, 54: 1.8, 55: 1.2, 64: 2.0}

# Impacts : (scène, phrase après laquelle il tombe, niveau). Toujours dans le blanc qui suit la phrase.
IMPACTS = [
    (2, 2, "medium"),             # retour après la phrase-motif
    (16, 1, "medium"),
    (17, 0, "strong"),
    (25, 2, "light"),
    (50, 0, "strong"),
    (53, 1, "medium"),
    (57, 0, "strong"),
]

# Coupures de musique : la phrase est dite dans le silence, la musique revient sur l'impact ou la coupe suivante
STOPDOWNS = [(2, 2), (4, 3), (50, 0), (57, 0)]

# Moment clé (temps 8) : image chaude, caméra presque immobile, gros plan réservé, drone clair, radio
KEY_SCENES = {54, 55}
WARM_SCENES = {54, 55}
CLOSEUPS = {17: 0, 54: 3, 57: 0}  # scène : phrase sur laquelle on passe au cadrage le plus serré

# Types de visuels où l'on ne recadre pas en cours de scène (textes ou éléments en bord d'image)
NO_COVERAGE = {"bars", "list", "choice", "circles", "title"}

# Ambiance par scène (d'après le visuel) ; elle démarre ~1 s avant la coupe (pont sonore)
def ambience_for(kind: str, p: dict) -> str | None:
    what = p.get("what")
    if kind == "person":
        return "radio" if p.get("radio") else "room"
    if kind == "device":
        if what in ("ticket", "atm", "terminal", "board", "phone"):
            return "street"
        if what in ("shelves", "warehouse", "cash", "notebook"):
            return "store"
        if what == "servers":
            return "servers"
        if what == "computer":
            return "hospital" if p.get("hospital") else "room"
        if what == "radio":
            return "radio"
    if kind in ("globe", "map"):
        return "space"
    return None


# Humeur du drone par temps du script
DRONE = {1: "neutral", 2: "neutral", 3: "neutral", 4: "neutral", 5: "dark", 6: "dark", 7: "dark", 8: "bright", 9: "neutral"}
