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


# ---------- moteur 3D : instant de l'événement visuel, calé sur le mot (l'image précède le mot de 0,1 s) ----------
EVENT_WORD = {2: "refuse", 10: "indisponibles", 12: "encaisser", 15: "refusent", 19: "erreur", 20: "impossible", 21: "bip",
              22: "refusée", 23: "Aucun", 25: "refus", 26: "saturé", 29: "invisibles", 31: "inaccessibles", 6: "huit"}

# bruitages réels (sfx_real) : (nom, ancre, décalage s, gain) ; ancre = "err" (événement), "start" ou "w:<début de mot>"
REAL_SFX = {
    2: [("metro_refuse", "err", 0.0, 0.8)], 5: [("digital_clock", "start", 0.3, 0.5)], 6: [("monitors_off", "w:huit", -0.6, 0.6)],
    7: [("departures_board", "w:annuler", -0.4, 0.6)], 10: [("notification", "err", 0.0, 0.5), ("notification", "err", 0.5, 0.4), ("notification", "err", 1.0, 0.35)],
    12: [("card_declined", "err", 0.0, 0.75)], 15: [("atm_error", "err", -0.3, 0.7)], 17: [("monitors_off", "w:serveurs", -0.3, 0.55)],
    19: [("computer_error", "err", -0.4, 0.6)], 20: [("metro_refuse", "err", 0.0, 0.6)], 21: [("card_declined", "err", 0.0, 0.8)],
    22: [("metro_refuse", "err", 0.0, 0.6), ("child_crying", "w:pleure", -0.2, 0.45)], 23: [("notification", "err", 0.0, 0.45)],
    25: [("atm_error", "err", -0.3, 0.7)], 26: [("phone_ring_fail", "start", 0.3, 0.5), ("phone_busy", "err", 0.0, 0.55)],
    29: [("notification", "err", 0.0, 0.45)], 31: [("computer_error", "err", -0.4, 0.55)], 32: [("shop_bell", "start", 0.1, 0.6)],
    33: [("pen_paper", "start", 0.4, 0.7)], 35: [("door_knock", "start", 0.2, 0.5)], 42: [("cash_coins", "start", 0.1, 0.6), ("pen_paper", "start", 1.6, 0.7)],
    50: [("servers_up", "w:retir", -0.2, 0.6)], 51: [("typing_fast", "start", 0.2, 0.5)], 55: [("radio_tune", "start", 0.0, 0.5)],
    56: [("terminals_on", "w:rallument", -0.2, 0.6)], 63: [("pen_paper", "w:notez", 0.0, 0.6)],
}
REAL_AMB = {1: "amb_apartment", 2: "amb_station", 20: "amb_station", 22: "amb_station", 7: "amb_queue", 12: "amb_store", 21: "amb_store",
            15: "amb_street", 24: "amb_queue", 25: "amb_street", 17: "amb_servers", 30: "amb_servers", 50: "amb_servers", 51: "amb_servers",
            19: "amb_apartment", 31: "amb_hospital", 33: "amb_hospital", 32: "amb_store", 36: "amb_apartment", 41: "amb_street",
            42: "amb_store", 44: "trucks_idle", 45: "amb_supermarket", 54: "amb_apartment", 55: "radio_fm", 63: "amb_apartment"}

# ---------- sources citées : la carte apparaît sur le mot qui la nomme (nom en toutes lettres, pas de logo de marque) ----------
CITES = {
    4: [("Orange", "ORANGE", "Panne · France · 2021"), ("Rogers", "ROGERS", "Panne · Canada · 2022"),
        ("Cloudflare", "CLOUDFLARE", "Panne · monde · 2025"), ("CrowdStrike", "CROWDSTRIKE", "Panne · monde · 2024")],
    5: [("CrowdStrike", "CROWDSTRIKE", "Logiciel de sécurité"), ("Windows", "MICROSOFT WINDOWS", "Ordinateurs touchés")],
    6: [("Microsoft", "MICROSOFT", "Source du chiffre")],
    7: [("Delta", "DELTA AIR LINES", "Plus de 5 000 vols annulés")],
    8: [("Parametrix", "PARAMETRIX", "Assureur · estimation des pertes")],
    9: [("Amazon", "AMAZON WEB SERVICES", "Panne du 20 octobre 2025")],
    10: [("Cloudflare", "CLOUDFLARE", "Panne du 18 novembre 2025")],
    11: [("Rogers", "ROGERS", "Panne du 8 juillet 2022"), ("Interac", "INTERAC", "Paiement par carte de débit")],
    13: [("Européenne", "BANQUE CENTRALE EUROPÉENNE", "Enquête sur les paiements"), ("France", "BANQUE DE FRANCE", "Citée par")],
    27: [("Orange", "ORANGE", "Panne du 2 juin 2021")],
    33: [("Corbeil", "HÔPITAL DE CORBEIL-ESSONNES", "Cyberattaque · 2022")],
    47: [("TeleGeography", "TELEGEOGRAPHY", "Source")],
    52: [("CrowdStrike", "CROWDSTRIKE", "Juillet 2024")],
}
# phrases clés écrites en grand, mot à mot sur la voix : (phrase de la scène, texte affiché ; « | » = retour à la ligne)
KEYLINES = {
    4: (3, "ET SI INTERNET|S'ARRÊTAIT 72 HEURES ?"),
    49: (3, "LA LUMIÈRE BRILLE,|MAIS LES DONNÉES NE PASSENT PLUS."),
    50: (0, "LE DÉTAIL|QUI CHANGE TOUT."),
    53: (2, "C'EST LA VITESSE|DE L'ERREUR."),
}
