"""Découpage des blocs 5 à 13 (écrit les bXX/shots.json). Mêmes conventions que b01–b04 : temps = ancres sur les mots."""
import json
import sys
from pathlib import Path

FILM = Path(__file__).resolve().parent
LAB = {"texte": "SIMULATION HYPOTHÉTIQUE", "de": 0, "pos": [58, 60], "police": "InstrumentSans-Bold.ttf", "taille": 24, "couleur": [214, 220, 226]}


def P(id, debut, st, texte, intention, camera=None, reglages=None, **kw):
    return {k: v for k, v in dict(id=id, debut=debut, set=st, texte=texte, intention=intention, camera=camera, reglages=reglages, **kw).items() if v is not None}


def cam(a, b, p0, p1):
    return [[f"#{a}", *p0], [f"#{b}", *p1]]


def carte(txt, de, a, reste=None, y=900):
    out = [{"texte": txt, "de": de, "a": a, "fondu": 0.4, "pos": [90, y], "police": "InstrumentSans-Bold.ttf", "taille": 46, "couleur": [236, 240, 245], "fond": True}]
    if reste is not None:
        out.append({"texte": "impact dans {}", "reste": reste, "de": de, "a": a, "fondu": 0.4, "pos": [90, y + 80], "police": "FragmentMono-Regular.ttf", "taille": 40, "couleur": [255, 226, 170], "fond": True})
    return out


def amb(fichier, a, jusqua, rms=-32, fi=0.5, fo=0.6):
    return {"fichier": fichier, "a": a, "boucle": True, "jusqua": jusqua, "rms": rms, "fondu_entree": fi, "fondu_sortie": fo}


S = "../sons/sfx_real/"
P2 = "../../prototype/son/sfx_real/"
RUE_JOUR = "film/b03/rue_jour.png"
H = 3600; J = 86400
B = {}

# ------------------------------------------------------------------ bloc 5 « Le deuxième jour » (48 h)
B["b05"] = dict(
    look="jour", voix=[{"id": "v1", "at": 0.6}, {"id": "v2", "at": "v1.end+1.2"}, {"id": "g1", "at": "v2.end+0.9"}, {"id": "v3", "at": "g1.end+1.8"}],
    fin="v3.end+1.8",
    plans=[
        P("A", 0, "astres.Ciel", "Quarante-huit heures après le début de la chute, la Lune paraît légèrement plus grande.", "la même rue, la Lune un peu plus grande",
          cam("A", "B", (1760, 720, 1.5), (1900, 340, 2.4)), {"image": RUE_JOUR, "horizon": 900, "lune": [1897, 193, 80], "lueur": 0.2}),
        P("B", "v1:pas-0.1", "astres.Ciel", "Pas assez pour provoquer la panique à elle seule.", "la ville continue, calme",
          cam("B", "C", (1376, 768, 1.0), (1376, 740, 1.05)), {"image": RUE_JOUR, "horizon": 900, "lune": [1897, 193, 80], "lueur": 0.2}),
        P("C", "v1:mais-0.1", "astres.Photos", "Mais suffisamment pour que des millions de personnes commencent à comparer leurs photographies.",
          "deux photos : avant, ce soir", cam("C", "D", (960, 540, 1.0), (960, 540, 1.05)), {"mode": "telephones", "comparer": "v1:comparer"}, look="nuit"),
        P("D", "v1:les-0.1", "scenes.Ecran2", "Les gouvernements ont désormais reçu les mêmes conclusions. Il n'existe aucun moyen connu d'arrêter la collision.",
          "le rapport, ligne après ligne", cam("D", "E", (960, 540, 1.0), (1000, 560, 1.06)),
          {"mode": "rapport", "l0": "v1:gouvernements", "l1": "v1:conclusions-0.4", "l2": "v1:il-0.2", "l3": "v1:aucun"}, look="nuit"),
        P("E", "v1:les#3-0.1", "scenes.Carte", "Les évacuations s'étendent dans plusieurs régions côtières.", "la côte se teinte de rouge",
          cam("E", "F", (960, 540, 1.0), (1100, 560, 1.15)), {"zones": "v1:évacuations"}, look="nuit"),
        P("F", "v1:les#4-0.1", "astres.Ciel", "Les routes se remplissent.", "l'embouteillage du soir",
          cam("F", "G", (1376, 768, 1.0), (1376, 800, 1.08)), {"image": "film/b05/embouteillage.png", "horizon": 760, "lune": [1950, 980, 40], "lueur": 0.0}),
        P("G", "v2-0.3", "scenes.Voiture", "Dans une voiture immobilisée au milieu d'un embouteillage, nous retrouvons le petit garçon de la plage. Au-dessus des voitures, la Lune commence à apparaître dans le ciel du soir.",
          "le garçon à la vitre ; la Lune se lève", cam("G", "H", (1376, 768, 1.0), (1300, 760, 1.08)), {"vue": "garcon", "lune": "v2:lune", "lune_r": 44, "lune_xy": [1900, 330]}),
        P("H", "g1-0.3", "scenes.Voiture", "« Maman… pourquoi elle grossit ? »", "lui, de profil, les yeux sur la Lune",
          cam("H", "I", (1150, 820, 1.5), (1200, 800, 1.6)), {"vue": "garcon", "lune_r": 46, "lune_xy": [1900, 330]}),
        P("I", "v3-0.4", "scenes.Voiture", "Sa mère connaît la réponse. Mais elle continue de chercher une manière de la lui dire.", "elle, au volant, silencieuse",
          cam("I", "J", (1100, 850, 1.6), (1080, 860, 1.7)), {"vue": "mere", "lune_r": 46, "lune_xy": [1900, 330]}),
        P("J", "v3:et-0.1", "astres.Ciel", "Et pendant que ces familles essaient de s'éloigner de la mer,", "on recule : toute l'autoroute arrêtée sous la Lune",
          cam("J", "K", (1500, 700, 1.4), (1376, 768, 1.0)), {"image": "film/b05/embouteillage.png", "horizon": 760, "lune": [1900, 330, 46], "lueur": 0.25}),
        P("K", "v3:les-0.1", "scenes.Porte", "les astronomes comprennent que la partie la plus dangereuse de la chute n'a pas encore commencé.",
          "Calern, la nuit : Léa devant ses écrans", cam("K", "K.end", (1900, 900, 1.4), (2150, 1000, 1.7)), {"lea": True}, look="nuit"),
    ],
    textes=[{**LAB, "a": "v3.end+1.8"}] + carte("48 h après le début de la chute", "v1-0.2", "#B", 2 * J + 19 * H + 36 * 60),
    son=[amb(P2 + "amb_calern_jour.wav", 0, "#C", -36), amb(S + "amb_embouteillage.wav", "#F", "#K", -30), amb(P2 + "amb_calern_nuit.wav", "#K", "v3.end+1.8", -34),
         {"petit": "bip", "a": "v1:aucun", "gain": -13}],
)

# ------------------------------------------------------------------ bloc 6 « Le quatrième jour »
B["b06"] = dict(
    look="jour", voix=[{"id": "v1", "at": 0.6}, {"id": "v2", "at": "v1.end+1.2"}, {"id": "c1", "at": "v2.end+0.7"},
                       {"id": "c2", "at": "c1.end+5.6"}, {"id": "l1", "at": "c2.end+0.9"}, {"id": "v3", "at": "l1.end+1.4"}],
    fin="v3.end+1.6",
    lea={"frappe": [["v3:décider", "v3.end+1.6"]], "regard_ecran": [["v3:enregistrer", "v3.end+3"]]},
    plans=[
        P("A", 0, "astres.Ciel", "Au quatrième jour, le changement est impossible à ignorer.", "la Lune, deux fois plus grande, au-dessus des toits",
          cam("A", "B", (1760, 700, 1.5), (1900, 360, 2.2)), {"image": RUE_JOUR, "horizon": 900, "lune": [1897, 230, 150], "lueur": 0.3}),
        P("B", "v1:et-0.1", "astres.Ciel", "Et la vitesse de rapprochement de la Lune augmente.", "on la voit grossir pendant le plan",
          cam("B", "C", (1900, 360, 2.2), (1900, 340, 2.3)), {"image": RUE_JOUR, "horizon": 900, "lune": [1897, 230, 150], "croissance": 0.025, "lueur": 0.3}),
        P("C", "v1:les-0.1", "scenes.Energie", "Les scientifiques envisagent toutes les possibilités… dérisoires face à la masse et à l'énergie de mouvement de la Lune.",
          "nos moyens, minuscules, face à la Lune", cam("C", "D", (960, 540, 1.0), (980, 540, 1.06)),
          {"lanceurs": "v1:missiles", "nucleaire": "v1:arsenal", "lune": "v1:l’énergie", "derisoire": "v1:dérisoires"}, look="nuit"),
        P("D", "v1:il-0.1", "astres.Espace", "Il ne reste qu'une certitude. La collision aura lieu.", "la Lune et la Terre, face à face",
          [["#D", 960, 540, 1.0], ["#E", 900, 540, 1.1]], {"terre": [700, 580, 300], "lune": [["#D", 1650, 360, 90], ["#E", 1500, 420, 110]]}, look="espace"),
        P("E", "v2-0.3", "scenes.Ecran2", "À Calern, l'observatoire reçoit un ordre d'évacuation.", "l'ordre clignote", cam("E", "F", (960, 540, 1.0), (960, 560, 1.06)),
          {"mode": "evacuation"}, look="nuit"),
        P("F", "c1-0.6", "scenes.Porte", "COLLÈGUE : « On doit partir. »", "le collègue à la porte, Léa à ses écrans ; alarme",
          cam("F", "G", (1376, 800, 1.0), (1300, 820, 1.05)), {"collegue": True, "lea": True, "alarme": "#F"}, look="nuit"),
        P("G", "c1.end+0.3", "noir", "(insert : le SMS de Camille, Léa écrit puis efface)", "le téléphone, en gros plan",
          calques=[{"type": "sequence", "chemin": "insert/%05d.png", "a": "#G"}]),
        P("H", "c2-0.4", "scenes.Porte", "COLLÈGUE : « Tu ne peux plus rien changer. »", "on reste sur Léa qui écoute",
          cam("H", "I", (2300, 1060, 2.0), (2300, 1060, 2.1)), {"collegue": True, "lea": True, "alarme": "#F"}, look="nuit"),
        P("I", "l1-0.3", "scenes.Porte", "LÉA : « Je sais. Mais on peut encore comprendre ce qui nous arrive. »", "contrechamp : le collègue à la porte, qui l'écoute",
          cam("I", "J", (420, 1100, 2.4), (420, 1100, 2.5)), {"collegue": True, "lea": True, "alarme": "#F"}, look="nuit"),
        P("J", "v3-0.3", "scenes.Porte", "Son collègue hésite. Puis il s'en va.", "il passe la porte", cam("J", "K", (1376, 800, 1.0), (1376, 800, 1.04)),
          {"collegue": True, "lea": True, "alarme": "#F", "part": "v3:puis"}, look="nuit"),
        P("K", "v3:léa-0.1", "scenes.Porte", "Léa reste seule.", "la salle vide autour d'elle", cam("K", "L", (1800, 900, 1.3), (2050, 980, 1.6)),
          {"lea": True, "alarme": "#F"}, look="nuit"),
        P("L", "v3:la-0.2", "astres.Ciel", "La Lune restera visible depuis Calern jusqu'aux derniers instants.", "l'observatoire sous une Lune énorme",
          cam("L", "M", (1376, 768, 1.0), (1500, 700, 1.1)), {"image": "film/b02/calern_exterieur.png", "horizon": 900, "lune": [2150, 330, 245], "lueur": 0.4}, look="nuit"),
        P("M", "v3:et-0.1", "calern.Poste", "Et Léa vient de décider d'enregistrer les dernières mesures de sa chute.", "elle se remet au clavier",
          [["#M", 820, 900, 1.8], ["#M.end", 840, 890, 1.95]], look="nuit"),
    ],
    textes=[{**LAB, "a": "v3.end+1.6"}] + carte("Quatrième jour", "v1-0.2", "#B", 19 * H + 36 * 60),
    son=[amb(P2 + "amb_calern_jour.wav", 0, "#C", -36), {"synth": "riser", "args": [2.0], "a": "v1:non-2.0", "gain": -22, "normalise": False},
         {"petit": "bip", "a": "v1:dérisoires", "gain": -13}, amb(S + "alarme.wav", "#E", "#L", -30, 0.2, 0.8),
         {"fichier": P2 + "notification.wav", "a": "#G+0.4", "gain": -12}, {"fichier": P2 + "phone_typing.wav", "a": "#G+2.0", "gain": -20, "fondu_sortie": 0.4},
         amb(P2 + "amb_calern_nuit.wav", "#L", "v3.end+1.6", -34)],
    silences=[],
)

# ------------------------------------------------------------------ bloc 7 « Six heures avant l'impact »
B["b07"] = dict(
    look="nuit", voix=[{"id": "v1", "at": 0.6}, {"id": "v2", "at": "v1.end+1.3"}], fin="v2.end+2.0",
    plans=[
        P("A", 0, "astres.Ciel", "Six heures avant la collision, la Lune est environ quatre fois plus proche qu'au début de sa chute.",
          "au-dessus de l'autoroute, une Lune énorme", cam("A", "B", (1700, 600, 1.6), (1500, 700, 1.2)),
          {"image": "film/b05/embouteillage.png", "horizon": 760, "lune": [1750, 360, 300], "lueur": 0.45}),
        P("B", "v1:les-0.1", "scenes.Force", "Les forces responsables des marées sont devenues des dizaines de fois plus puissantes.",
          "× 75 : une force", cam("B", "C", (960, 540, 1.0), (960, 540, 1.05)), {"v1": "#B", "v75": "v1:dizaines"}),
        P("C", "v1:et-0.1", "maree.Rapproche", "Et les océans commencent à réagir d'une manière que personne n'a jamais observée.",
          "les océans se déforment", cam("C", "D", (960, 540, 1.0), (900, 550, 1.1)), {"rapproche": "#C-2.6", "puissant": "v1:réagir"}),
        P("D", "v1:certaines-0.1", "astres.Ciel", "Certaines côtes voient l'eau avancer très loin à l'intérieur des terres. Des routes disparaissent. Des bâtiments se retrouvent isolés.",
          "la ville sous l'eau, la Lune au-dessus", cam("D", "E", (1376, 768, 1.0), (1300, 820, 1.12)),
          {"image": "film/b07/cote_inondee.png", "horizon": 860, "lune": [1450, 300, 260], "lueur": 0.35}),
        P("E", "v1:ailleurs-0.1", "astres.Ciel", "Ailleurs, la mer se retire brutalement, laissant des bateaux couchés sur la vase.",
          "le port est à sec", cam("E", "F", (1376, 800, 1.1), (1500, 860, 1.25)),
          {"image": "film/b07/port_vase.png", "horizon": 880, "ciel": "texture", "lune": [1750, 330, 260], "lueur": 0.35}),
        P("F", "v2-0.3", "maree.Differentiel", "Il ne s'agit pas d'une seule vague traversant la planète. Les océans réagissent différemment selon les régions, la forme des côtes et les mouvements de l'eau.",
          "pas une vague : des océans déformés", cam("F", "G", (960, 540, 1.0), (980, 545, 1.06)), {"fleches": "#F+0.3", "oceans": "v2:océans"}),
        P("G", "v2:mais-0.1", "astres.Ciel", "Mais partout, les conditions deviennent imprévisibles. Sur une autoroute… la voiture de la mère et de son fils n'avance toujours pas.",
          "l'autoroute, toujours bloquée", cam("G", "H", (2000, 880, 1.6), (1800, 860, 1.5)),
          {"image": "film/b07/autoroute_eau.png", "horizon": 760, "lune": [1750, 330, 300], "lueur": 0.4}),
        P("H", "v2:audelà-0.1", "astres.Ciel", "Au-delà des champs, une immense étendue d'eau reflète le ciel. Là où, quelques heures auparavant, il n'y avait que des terres.",
          "on découvre l'eau à perte de vue", cam("H", "H.end", (900, 800, 1.5), (1376, 768, 1.0)),
          {"image": "film/b07/autoroute_eau.png", "horizon": 760, "lune": [1750, 330, 300], "lueur": 0.4}),
    ],
    textes=[{**LAB, "a": "v2.end+2.0"}] + carte("6 h avant l'impact", "v1-0.2", "#B", 6 * H),
    son=[amb(S + "amb_embouteillage.wav", 0, "#B", -32), amb(P2 + "amb_plage.wav", "#D", "#F", -28), amb(S + "amb_embouteillage.wav", "#G", "v2.end+2.0", -32),
         {"synth": "riser", "args": [2.0], "a": "v1:brutalement-1.6", "gain": -22, "normalise": False}],
)

# ------------------------------------------------------------------ bloc 8 « Même la terre se déforme »
B["b08"] = dict(
    look="nuit", voix=[{"id": "v1", "at": 0.8}, {"id": "v2", "at": "v1.end+1.3"}], fin="v2.end+2.0",
    plans=[
        P("A", 0, "scenes.Seisme", "Le bitume se soulève. Une fissure apparaît. Elle s'étend jusqu'au pied d'un immeuble.",
          "la chaussée bombe, la fissure court vers l'immeuble", cam("A", "B", (1150, 1250, 2.0), (900, 1200, 1.8)),
          {"souleve": "v1:soulève", "fissure": "v1:fissure", "duree_fissure": 3.2}, secousses=[{"a": "v1:soulève", "force": 6}, {"a": "v1:fissure", "force": 8}]),
        P("B", "v1:un#2-0.2", "scenes.Seisme", "Un craquement retentit. Puis une partie de la façade s'effondre.", "un pan de façade tombe",
          cam("B", "C", (800, 800, 1.6), (850, 900, 1.5)), {"souleve": "#A", "fissure": "#A", "effondre": "v1:façade-0.3"},
          secousses=[{"a": "v1:craquement", "force": 14}, {"a": "v1:façade", "force": 18, "duree": 0.8}]),
        P("C", "v1:certaines-0.1", "scenes.Seisme", "Certaines régions commencent à céder sous les contraintes qui déforment la planète.", "la rue abîmée, la Lune géante",
          cam("C", "D", (1376, 768, 1.0), (1376, 700, 1.08)), {"souleve": "#A", "fissure": "#A", "effondre": "#A"}),
        P("D", "v1:car-0.1", "scenes.Croute", "Car la Terre n'est pas parfaitement rigide. Aujourd'hui déjà, l'attraction de la Lune soulève et abaisse légèrement le sol. Habituellement, ces mouvements passent inaperçus.",
          "le sol aussi a ses marées", cam("D", "E", (960, 540, 1.0), (960, 540, 1.06)), {"rigide": "v1:rigide", "sol": "v1:soulève#2"}),
        P("E", "v2-0.3", "scenes.Force", "Mais à une heure et demie du contact, les forces… presque mille fois leur intensité initiale. Cela ne veut pas dire que le sol monte mille fois plus haut…",
          "× 940, mais une force", cam("E", "F", (960, 540, 1.0), (980, 540, 1.05)), {"v1": "#E", "v75": "#E+0.3", "v940": "v2:mille", "hauteur": "v2:veut"}),
        P("F", "v2:ici-0.1", "scenes.Seisme", "Ici, certaines déformations suffisent à endommager les infrastructures.", "la rue fissurée",
          cam("F", "G", (1200, 1150, 1.6), (1100, 1100, 1.5)), {"souleve": "#A", "fissure": "#A", "effondre": "#A"}),
        P("G", "v2:mais#2-0.1", "astres.Ciel", "Mais pendant que la Terre se déforme… les astronomes découvrent quelque chose d'encore plus inquiétant. La Lune aussi commence à changer.",
          "la Lune, de près : une première ligne sombre", cam("G", "G.end", (2150, 400, 2.2), (2150, 380, 3.0)),
          {"image": "film/b02/calern_exterieur.png", "horizon": 900, "lune": [2150, 380, 330], "fract": [["v2:changer-0.6", 0.0], ["v2.end+2", 0.25]], "lueur": 0.4}),
    ],
    textes=[{**LAB, "a": "v2.end+2.0"}] + carte("1 h 30 avant l'impact", "v1-0.3", "v1:fissure", 1 * H + 30 * 60),
    son=[amb("../b01/sfx_real/amb_ville_nuit.wav", 0, "#D", -32), {"fichier": S + "craquement.wav", "a": "v1:craquement-0.2", "gain": -8},
         {"fichier": "../../prototype/son/sfx_real/space_rumble.wav", "a": "v1:soulève-0.2", "gain": -18, "fondu_sortie": 1.0},
         amb("../b01/sfx_real/amb_ville_nuit.wav", "#F", "#G", -32), amb(P2 + "amb_calern_nuit.wav", "#G", "v2.end+2.0", -34)],
)

# ------------------------------------------------------------------ bloc 9 « Quelque chose apparaît sur la Lune »
B["b09"] = dict(
    look="nuit", voix=[{"id": "v1", "at": 0.6}, {"id": "v2", "at": "v1.end+1.3"}], fin="v2.end+1.8",
    lea={"frappe": [["v1:léa", "v1:compare.end"]], "regard_ecran": [["v1:compare", "v1:compare+5"]]},
    plans=[
        P("A", 0, "calern.Poste", "À Calern, Léa compare deux photographies prises à quelques minutes d'intervalle.", "Léa à son poste",
          [["#A", 820, 900, 1.8], ["#B", 860, 880, 2.0]]),
        P("B", "v1:sur-0.1", "astres.Photos", "Sur la première, une région de la surface lunaire semble intacte. Sur la seconde, une immense ligne sombre traverse le paysage. Elle agrandit l'image… Un autre observatoire transmet une photographie. La même anomalie apparaît.",
          "les deux photos ; la ligne sombre ; la confirmation", cam("B", "C", (960, 540, 1.0), (1150, 540, 1.15)),
          {"mode": "calern", "seconde": "v1:seconde", "zoom": "v1:agrandit", "transmise": "v1:transmet"}),
        P("C", "v1:léa#2-0.1", "calern.Poste", "Léa ne peut pas encore confirmer ce qu'elle voit.", "elle fixe l'écran", [["#C", 860, 860, 2.2], ["#D", 880, 850, 2.4]]),
        P("D", "v1:mais-0.1", "astres.Ciel", "Mais les scientifiques redoutent une explication. La Lune pourrait commencer à se fracturer.", "la Lune, les fractures s'étendent",
          cam("D", "E", (2150, 420, 2.0), (2150, 400, 2.4)),
          {"image": "film/b02/calern_exterieur.png", "horizon": 900, "lune": [2150, 400, 360], "fract": [["#D", 0.25], ["#E", 0.5]], "lueur": 0.4}),
        P("E", "v2-0.3", "scenes.Roche", "La Terre attire plus fortement sa face proche que sa face éloignée… la limite de Roche.", "les deux flèches inégales, la limite",
          cam("E", "F", (960, 540, 1.0), (960, 540, 1.06)), {"fleches": "v2:attire", "limite": "v2:roche"}),
        P("F", "v2:en-0.1", "scenes.Comete", "En 1994, les fragments d'une comète déchirée par Jupiter se sont écrasés sur la planète.", "histoire réelle",
          cam("F", "G", (960, 540, 1.0), (1050, 540, 1.1))),
        P("G", "v2:mais-0.1", "scenes.Roche", "Mais la Lune est un monde rocheux, pas une boule de liquide. Rien ne garantit qu'elle se brisera. Pourtant, les fractures s'étendent.",
          "les fractures apparaissent", cam("G", "H", (1100, 560, 1.15), (1150, 560, 1.25)), {"fleches": "#G", "limite": "#G", "fractures": "v2:fractures"}),
        P("H", "v2:et-0.1", "astres.Ciel", "Et une question apparaît. Que se passera-t-il si la Lune commence à se disloquer avant de toucher la Terre ? La réponse arrive plus vite que prévu.",
          "la Lune fissurée au-dessus de Calern", cam("H", "H.end", (2000, 500, 1.6), (1376, 768, 1.0)),
          {"image": "film/b02/calern_exterieur.png", "horizon": 900, "lune": [2150, 380, 420], "fract": 0.7, "deform": 0.2, "lueur": 0.45}),
    ],
    textes=[{**LAB, "a": "v2.end+1.8"}, {"texte": "Histoire réelle", "de": "#F", "a": "#G", "pos": [1500, 60], "police": "InstrumentSans-Bold.ttf", "taille": 24, "couleur": [244, 200, 110]}],
    son=[amb(P2 + "amb_calern_nuit.wav", 0, "v2.end+1.8", -34), {"petit": "bip", "a": "v1:seconde", "gain": -13}, {"petit": "bip", "a": "v1:transmet", "gain": -13},
         {"synth": "riser", "args": [2.0], "a": "v2:prévu-1.8", "gain": -22, "normalise": False}],
)

# ------------------------------------------------------------------ bloc 10 « Le dernier écho »
B["b10"] = dict(
    look="nuit", voix=[{"id": "v1", "at": 0.6}, {"id": "l1", "at": "v1.end+1.6"}, {"id": "v2", "at": "l1.end+1.2"},
                       {"id": "v3", "at": "v2.end+2.4"}, {"id": "v4", "at": "v3.end+1.0"}], fin="v4.end+1.8",
    lea={"frappe": [["v4:léa", "v4:mesure.end"]], "regard_ecran": [["v4:léa-1", "v4:mesure+2"]]},
    plans=[
        P("A", 0, "scenes.Porte", "À Calern, les lumières vacillent. Une alarme retentit dans le bâtiment. Léa n'a plus beaucoup de temps.",
          "la salle clignote ; Léa seule", cam("A", "B", (1700, 860, 1.2), (2100, 980, 1.6)), {"lea": True, "vacille": "v1:vacillent", "alarme": "v1:alarme"},
          secousses=[{"a": "v1:vacillent", "force": 5}]),
        P("B", "v1:elle-0.1", "scenes.Ecran2", "Elle enregistre un message vocal. « Je suis désolée. Je t'aime. » Elle l'envoie. Quelques secondes passent.",
          "le message vocal, puis « Écouté », puis le silence", cam("B", "C", (960, 540, 1.0), (960, 540, 1.08)),
          {"mode": "vocal", "rec": "l1-0.3", "envoi": "v2:l’envoie", "ecoute": "v2.end+0.6"}),
        P("C", "v3-0.3", "astres.Ciel", "Elle retourne vers le laser. Contre toute attente… le système fonctionne encore. Le réflecteur lunaire est toujours accessible.",
          "l'observatoire sous la Lune immense, le laser repart", cam("C", "D", (1376, 768, 1.0), (1500, 600, 1.12)),
          {"image": "film/b02/calern_exterieur.png", "horizon": 900, "lune": [1900, 380, 620], "fract": 0.8, "laser": "v3:fonctionne", "coupole": [985, 470], "lueur": 0.5}),
        P("D", "v3:léa-0.1", "schemas.Laser", "Léa lance une dernière impulsion. 0,06 seconde. Il y a cinq jours… deux secondes et demie. À présent… neuf mille kilomètres…",
          "0,06 s : la Lune est presque là", cam("D", "E", (960, 540, 1.0), (960, 540, 1.04)),
          {"distance": "v3:impulsion", "depart": "v3:impulsion", "reflecteur": "v3:impulsion", "arrivee": "v3:impulsion+0.6", "retour": "v3:006",
           "aller_retour": "v3:neuf", "duree": 0.06, "distance_txt": "environ 9 000 km", "final_txt": "aller-retour : 0,06 seconde", "lune_r": 260}),
        P("E", "v4-0.3", "calern.Poste", "D'après les calculs, il reste une vingtaine de minutes avant le contact des deux astres. Léa sauvegarde la mesure.",
          "elle sauvegarde", [["#E", 820, 900, 1.8], ["#F", 850, 880, 2.0]]),
        P("F", "v4:les#2-0.1", "astres.Ciel", "Les immenses fractures sont désormais visibles à l'œil nu. Une partie du bord lunaire change de forme.",
          "la Lune fracturée, le bord qui s'étire", cam("F", "F.end", (1700, 560, 1.4), (1800, 520, 1.6)),
          {"image": "film/b02/calern_exterieur.png", "horizon": 900, "lune": [1900, 380, 640], "fract": 1.0, "deform": 0.8, "lueur": 0.55}),
    ],
    textes=[{**LAB, "a": "v4.end+1.8"}] + carte("19 min avant l'impact", "v4-0.2", "v4:sauvegarde", 19 * 60),
    son=[amb(S + "alarme.wav", "v1:alarme-0.2", "#C", -30, 0.2, 0.6), {"petit": "bip", "a": "l1-0.3", "gain": -16}, {"petit": "bip", "a": "v2:l’envoie", "gain": -15},
         {"petit": "laser", "a": "v3:impulsion", "gain": -13}, {"petit": "bip", "a": "v3:006", "gain": -11}, amb(P2 + "amb_calern_nuit.wav", "#C", "v4.end+1.8", -34)],
    silences=[{"de": "l1-0.4", "a": "l1.end+0.2"}, {"de": "v2.end+0.4", "a": "v3-0.3"}],
)

# ------------------------------------------------------------------ bloc 11 « La Lune se brise »
COLL = "film/b11/colline.png"
GENS_LOIN = [{"sprite": "b04/mere_dos.png", "x": 690, "y": 1062, "s": 0.115}, {"sprite": "b04/garcon_dos.png", "x": 775, "y": 1064, "s": 0.093, "k": 1}]
GENS_PRES = [{"sprite": "b04/mere_dos.png", "x": 1000, "y": 1560, "s": 0.62}, {"sprite": "b04/garcon_dos.png", "x": 1330, "y": 1570, "s": 0.47, "k": 1}]
B["b11"] = dict(
    look="nuit", voix=[{"id": "v1", "at": 0.6}, {"id": "v2", "at": "v1.end+1.3"}, {"id": "v3", "at": "v2.end+1.4"}, {"id": "g1", "at": "v3.end+0.9"},
                       {"id": "m1", "at": "g1.end+1.4"}, {"id": "v4", "at": "m1.end+1.8"}], fin="v4.end+1.6",
    plans=[
        P("A", 0, "astres.Ciel", "Au début, cela ressemble à une ombre. Puis un immense bloc se détache. Et un autre…", "la Lune commence à se briser",
          cam("A", "B", (1900, 520, 1.5), (1850, 560, 1.4)), {"image": COLL, "horizon": 900, "lune": [1950, 460, 640], "fract": 1.0, "morceaux": "v1:bloc", "duree_morceaux": 55, "vers": [-0.2, 1.0], "lueur": 0.6}),
        P("B", "v1:des-0.1", "astres.Espace", "Des morceaux de croûte et de roche se séparent de la masse principale. Certains, arrachés du côté faisant face à la Terre…",
          "vue de l'espace : les blocs partent vers la Terre", [["#B", 960, 540, 1.0], ["#C", 1000, 540, 1.08]],
          {"terre": [620, 600, 330], "lune": [["#B", 1450, 470, 210], ["#C", 1350, 500, 220]], "morceaux": "#B-3"}, look="espace"),
        P("C", "v2-0.3", "astres.Ciel", "Depuis le sol, le spectacle est impossible à confondre avec une pluie de météores ordinaire. Des fragments gigantesques apparaissent dans le ciel…",
          "la colline sous la pluie de fragments", cam("C", "D", (1376, 768, 1.0), (1300, 700, 1.05)),
          {"image": COLL, "horizon": 900, "lune": [1950, 460, 640], "fract": 1.0, "morceaux": "#A+2.0", "duree_morceaux": 55, "vers": [-0.2, 1.0],
           "meteores": "v2:fragments-1.0", "lueur": 0.7, "gens": GENS_LOIN}),
        P("D", "v2:les-0.1", "astres.Ciel", "Les premières collisions projettent d'immenses quantités de matière. Des ondes de choc traversent l'atmosphère.",
          "lueurs d'impacts à l'horizon", cam("D", "E", (1700, 820, 1.5), (1600, 800, 1.4)),
          {"image": COLL, "horizon": 900, "lune": [1950, 460, 640], "fract": 1.0, "morceaux": "#A+2.0", "duree_morceaux": 55, "vers": [-0.2, 1.0],
           "meteores": "#C", "lueur": 0.8, "gens": GENS_LOIN}, secousses=[{"a": "v2:ondes", "force": 10, "duree": 0.9}]),
        P("E", "v3-0.3", "astres.Ciel", "Sur une hauteur, la mère et son fils se sont arrêtés. « Est-ce qu'on est assez loin ? » « Je suis là. »",
          "eux deux, de dos, face au ciel qui se brise ; le silence après « Je suis là »", cam("E", "F", (1300, 1000, 1.25), (1250, 1000, 1.35)),
          {"image": COLL, "horizon": 900, "lune": [1950, 460, 640], "fract": 1.0, "morceaux": "#A+2.0", "duree_morceaux": 55, "vers": [-0.2, 1.0],
           "meteores": "#C", "lueur": 0.8, "gens": GENS_PRES}),
        P("F", "v4-0.3", "astres.Espace", "Mais la masse principale de la Lune approche toujours. Et désormais, plus rien ne sépare les deux mondes.",
          "la Lune brisée tout contre la Terre", [["#F", 960, 540, 1.0], ["#F.end", 860, 560, 1.15]],
          {"terre": [620, 600, 330], "lune": [["#F", 1250, 520, 230], ["#F.end", 1080, 560, 240]], "morceaux": "#B-3"}, look="espace"),
    ],
    textes=[{**LAB, "a": "v4.end+1.6"}],
    son=[{"fichier": "../../prototype/son/sfx_real/space_rumble.wav", "a": "v1:bloc-0.2", "gain": -14, "fondu_sortie": 1.0},
         amb(S + "vent_colline.wav", "#C", "#F", -30), {"fichier": S + "impacts.wav", "a": "v2:collisions-0.3", "gain": -10, "fondu_sortie": 1.5},
         {"fichier": "../../prototype/son/sfx_real/space_rumble.wav", "a": "#F", "gain": -14, "fondu_sortie": 2.0}],
    silences=[{"de": "m1.end+0.1", "a": "v4-0.2"}],
)

# ------------------------------------------------------------------ bloc 12 « La collision » (+ 4 s de noir)
B["b12"] = dict(
    look="espace", voix=[{"id": "v1", "at": 2.6}, {"id": "v2", "at": "v1.end+1.2"}], fin="v2.end+5.2",
    plans=[
        P("A", 0, "astres.Espace", "La Lune frappe la Terre à près de dix kilomètres par seconde…", "le contact", [["#A", 960, 540, 1.0], ["#B", 860, 560, 1.1]],
          {"terre": [700, 600, 340], "lune": [[0, 1300, 450, 250], ["v1:frappe", 1060, 520, 250]], "contact": "v1:frappe", "morceaux": -30}),
        P("B", "v1:c’est-0.1", "astres.Espace", "C'est un monde de plus de trois mille kilomètres de diamètre. Au point de contact… incandescente. Puis d'immenses panaches… des milliers de kilomètres.",
          "l'incandescence, les panaches", [["#B", 860, 560, 1.1], ["#C", 960, 540, 1.0]],
          {"terre": [700, 600, 340], "lune": [[0, 1300, 450, 250], ["v1:frappe", 1060, 520, 250]], "contact": "v1:frappe", "morceaux": -30}),
        P("C", "v2-0.3", "fixe.Image", "L'énergie libérée dépasse de plusieurs millions de fois celle de l'impact qui a contribué à la disparition des dinosaures.",
          "la planète frappée", cam("C", "D", (1376, 768, 1.0), (1300, 760, 1.12)), {"image": "film2d/images/decor_espace.png", "poussiere": False}),
        P("D", "v2:des-0.1", "astres.Espace", "Des ondes de choc traversent la Terre… Ce n'est pas la fin de la Terre. C'est la fin de notre monde.",
          "la Terre transformée", [["#D", 960, 540, 1.0], ["#E", 1000, 560, 1.15]],
          {"terre": [700, 600, 340], "lune": [[0, 1300, 450, 250], ["v1:frappe", 1060, 520, 250]], "contact": "v1:frappe", "morceaux": -30},
          filtres=[{"type": "fondu_noir", "de": "v2:monde", "a": "v2.end+0.9"}]),
        P("E", "v2.end+1.0", "noir", "[silence 4 s]", "le noir ; l'étiquette disparaît"),
    ],
    textes=[{**LAB, "a": "v2.end+0.9"}],
    son=[{"synth": "riser", "args": [3.0], "a": "v1:frappe-3.0", "gain": -18, "normalise": False},
         {"fichier": S + "impacts.wav", "a": "v1:frappe", "gain": -6, "fondu_sortie": 2.0},
         {"fichier": "../../prototype/son/sfx_real/space_rumble.wav", "a": "v1:frappe+0.2", "gain": -10, "fondu_sortie": 3.0},
         {"fichier": "../../prototype/son/sfx_real/space_rumble.wav", "a": "v2", "gain": -16, "fondu_sortie": 3.0}],
    silences=[{"de": "v2.end+1.0", "a": "v2.end+5.2"}],
)

# ------------------------------------------------------------------ bloc 13 « Retour brutal à la réalité »
B["b13"] = dict(
    look="jour", voix=[{"id": "v1", "at": 10.6}, {"id": "v2", "at": "v1.end+1.6"}, {"id": "v3", "at": "v2.end+1.0"}], fin="v3.end+2.6",
    plans=[
        P("A", 0, "scenes.Porte", "[Calern en plein jour, Léa au travail]", "coupe franche : la vie normale",
          cam("A", "B", (1700, 900, 1.3), (1800, 920, 1.4)), {"image": "film2d/images/decor_calern_jour.png", "lea": True, "lea_xy": [2200, 1440, 0.40]}),
        P("B", 4.0, "scenes.Porte", "[le collègue passe et sourit]", "le collègue, une tasse à la main",
          cam("B", "C", (1500, 950, 1.5), (1450, 950, 1.55)), {"image": "film2d/images/decor_calern_jour.png", "lea": True, "lea_xy": [2200, 1440, 0.40],
                                                               "collegue": True, "collegue_xy": [1450, 1420, 0.30]}),
        P("C", 7.0, "littoral.PlageFin", "[la plage ensoleillée ; le garçon court vers l'eau avec son seau, sa mère le rejoint] Heureusement… tout cela n'était qu'une simulation.",
          "le soulagement", cam("C", "D", (1376, 900, 1.25), (1376, 800, 1.0)), {"course": 8.0, "mere": 10.0}),
        P("D", "v2-0.3", "schemas.Laser", "Aujourd'hui, la Lune est toujours là… La lumière part de la Terre. Puis elle revient. Deux secondes et demie.",
          "le laser, comme au bloc 2", cam("D", "E", (960, 540, 1.0), (960, 540, 1.04)),
          {"distance": "v2:distance", "depart": "v2:part", "reflecteur": "v2:impulsions", "arrivee": "v2:puis", "retour": "v2:demie", "aller_retour": "v2:demie+0.4"}, look="nuit"),
        P("E", "v3-0.2", "scenes.Recul", "Et chaque année, elle s'éloigne de nous d'environ 3,8 centimètres. La Lune ne tombe pas vers la Terre. Elle s'en éloigne.",
          "+ 3,8 cm par an", cam("E", "E.end", (960, 540, 1.0), (1000, 540, 1.05)), {"eloigne": "v3:éloigne", "fin": "v3:éloigne#2"}, look="nuit",
          filtres=[{"type": "fondu_noir", "de": "v3.end+1.0", "a": "v3.end+2.6"}]),
    ],
    textes=[],
    son=[amb(P2 + "amb_calern_jour.wav", 0, 7.0, -32, 0.0, 0.3), {"petit": "clic", "a": 1.2, "repete": 14, "intervalle": 0.19, "gain": -20},
         amb(P2 + "amb_plage.wav", 7.0, "#D", -28, 0.0, 1.0), {"petit": "laser", "a": "v2:part", "gain": -14}, {"petit": "bip", "a": "v2:demie", "gain": -12}],
)

if __name__ == "__main__":
    which = sys.argv[1:] or list(B)
    for b in which:
        d = {"_doc": f"Bloc {b[1:]} : voir plans_reste.py (source du découpage).", **B[b]}
        (FILM / b / "shots.json").write_text(json.dumps(d, ensure_ascii=False, indent=1))
        print("écrit", b)
