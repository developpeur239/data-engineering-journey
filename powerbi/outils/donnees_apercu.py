"""Données FICTIVES réalistes pour les aperçus PNG (jamais utilisées dans le rapport réel).

Les noms de champs sont ceux que Deneb recevra (nom des champs dans la liste « Valeurs » du visuel).
"""
import math
import random

import commun

R = random.Random(20261006)


def _g(h, mu, sd):
    return math.exp(-0.5 * ((h - mu) / sd) ** 2)


def taux_penurie(h, jour):
    we = jour >= 6
    if we:
        return 0.035 + 0.075 * _g(h, 12.5, 2.8) + 0.05 * _g(h, 19.0, 2.2)
    return 0.03 + 0.17 * _g(h, 8.2, 1.2) + 0.115 * _g(h, 18.2, 1.5) + 0.02 * _g(h, 13, 3)


def taux_saturation(h, jour):
    we = jour >= 6
    if we:
        return 0.03 + 0.04 * _g(h, 14, 3.2)
    return 0.025 + 0.10 * _g(h, 9.4, 1.4) + 0.045 * _g(h, 19.5, 1.8)


def heatmap():
    n_service = 1450 * 12 * 2
    out = []
    for j in range(1, 8):
        for h in range(24):
            p = taux_penurie(h, j) * R.uniform(0.93, 1.07)
            s = taux_saturation(h, j) * R.uniform(0.93, 1.07)
            ns = int(n_service * R.uniform(0.97, 1.0))
            out.append({"heure_du_jour": h, "jour_semaine_ordre": j, "n_penurie": int(ns * p),
                        "n_saturation": int(ns * s), "n_service": ns})
    return out


def rythme():
    out = []
    for h in range(24):
        ns = 1450 * 12 * 14
        p = (taux_penurie(h, 1) * 5 + taux_penurie(h, 6) * 2) / 7 * R.uniform(0.97, 1.03)
        s = (taux_saturation(h, 1) * 5 + taux_saturation(h, 6) * 2) / 7 * R.uniform(0.97, 1.03)
        out.append({"heure_du_jour": h, "n_penurie": int(ns * p), "n_saturation": int(ns * s), "n_service": ns})
    return out


REPERES = [("Gare du Nord", 48.8809, 2.3553), ("Gare de Lyon", 48.8443, 2.3744),
           ("Montparnasse", 48.8421, 2.3219), ("Châtelet", 48.8584, 2.3470),
           ("République", 48.8675, 2.3636), ("Trocadéro", 48.8629, 2.2877)]


def stations(n=1450):
    out = []
    noms = ["Rivoli", "Voltaire", "Vaugirard", "Bastille", "Oberkampf", "Ménilmontant", "Convention", "Italie",
            "Belleville", "Batignolles", "Montmartre", "Auteuil", "Bercy", "Vincennes", "Clichy", "Alésia"]
    for i in range(n):
        if R.random() < 0.62:  # Paris intra-muros, plus dense au centre
            while True:
                lat = 48.8566 + R.gauss(0, 0.028)
                lon = 2.3488 + R.gauss(0, 0.048)
                if ((lat - 48.8566) / 0.05) ** 2 + ((lon - 2.3488) / 0.085) ** 2 < 1:
                    break
        else:  # proche banlieue
            while True:
                lat = 48.8566 + R.gauss(0, 0.07)
                lon = 2.3488 + R.gauss(0, 0.11)
                if 48.77 < lat < 48.95 and 2.16 < lon < 2.54 and ((lat - 48.8566) / 0.05) ** 2 + ((lon - 2.3488) / 0.085) ** 2 > 1:
                    break
        d = math.hypot((lat - 48.8566) * 111, (lon - 2.3488) * 73)  # km au centre de Paris
        cap = int(R.choice([20, 24, 28, 30, 32, 35, 40, 44, 50, 60]))
        # plus de pénurie en périphérie le matin ; bruit par station
        f = (0.6 + 0.16 * d) * R.lognormvariate(0, 0.5)
        nom = f"{R.choice(noms)} – {R.choice(['Nord','Sud','Est','Ouest','Centre','Gare'])} {i % 90}"
        ns = int(12 * 24 * 14 * R.uniform(0.9, 1.0))
        p = min(0.7, 0.07 * f)
        out.append({"station_id": f"{10000 + i}", "station_nom": nom, "latitude": round(lat, 5),
                    "longitude": round(lon, 5), "capacite_max": cap, "n_service": ns,
                    "n_penurie": int(ns * p)})
    return out


def pannes():
    # Taux « sans panne » / « avec panne » (fractions 0-1) ; l'écart est faible mais net (démonstration)
    return [{"periode": "Heure de pointe", "Taux pénurie sans panne": 0.141, "Taux pénurie avec panne": 0.171,
             "Taux saturation sans panne": 0.083, "Taux saturation avec panne": 0.071},
            {"periode": "Hors pointe", "Taux pénurie sans panne": 0.064, "Taux pénurie avec panne": 0.073,
             "Taux saturation sans panne": 0.041, "Taux saturation avec panne": 0.044}]


def meteo_barres():
    return [{"pluie_libelle": "Sans pluie", "Taux pénurie": 0.087, "Taux saturation": 0.052},
            {"pluie_libelle": "Pluie", "Taux pénurie": 0.101, "Taux saturation": 0.043}]


def meteo_nuage():
    import datetime as dt
    out = []
    t0 = dt.datetime(2026, 9, 21)
    for d in range(14):
        base = 13 + 5 * math.sin(d / 3.0) + R.uniform(-1, 1)
        pluie_j = R.random() < 0.3
        for h in range(24):
            temp = base + 4.5 * math.sin((h - 9) / 24 * 2 * math.pi) + R.uniform(-0.6, 0.6)
            pl = pluie_j and R.random() < 0.55
            tp = taux_penurie(h, 1 if (d % 7) < 5 else 6) * (1.12 if pl else 1.0) * (1 + 0.012 * (temp - 15))
            out.append({"heure_paris": (t0 + dt.timedelta(days=d, hours=h)).strftime("%Y-%m-%dT%H:%M:%S"),
                        "temperature_c": round(temp, 1), "Taux pénurie": round(tp * R.uniform(0.9, 1.1), 4),
                        "pluie_libelle": "Pluie" if pl else "Sans pluie"})
    seuil = sum(r["temperature_c"] for r in out) / len(out)  # même logique que la mesure DAX seuil_temperature
    for r in out:
        r["seuil_temperature"] = seuil
    return out


def meteo_courbes():
    out = []
    for lib, k in (("Sans pluie", 1.0), ("Pluie", 1.13)):
        for h in range(24):
            out.append({"heure_du_jour": h, "pluie_libelle": lib,
                        "Taux pénurie": round(((taux_penurie(h, 1) * 5 + taux_penurie(h, 6) * 2) / 7) * k * R.uniform(0.96, 1.04), 4)})
    return out


# --- page « Météo · 3 ans de compteurs » : chiffres de référence fournis par l'utilisateur (Databricks), profil horaire inventé
def meteo3_halteres():
    return [{"periode": "pointe", "Passages sans pluie": 163.6, "Passages avec pluie": 141.8},
            {"periode": "journée", "Passages sans pluie": 69.8, "Passages avec pluie": 61.8},
            {"periode": "nuit", "Passages sans pluie": 13.94, "Passages avec pluie": 11.07}]


def meteo3_effet():
    return [{"type_jour": "semaine", "Effet pluie à conditions égales (%)": -0.159, "Heures de pluie": 3300},
            {"type_jour": "week-end", "Effet pluie à conditions égales (%)": -0.206, "Heures de pluie": 1318}]


def meteo3_classes():
    vals = [139.8, 152.0, 172.5, 193.9, 184.1]
    labels = ["1. moins de 5 °C", "2. 5 à 12 °C", "3. 12 à 18 °C", "4. 18 à 27 °C", "5. 27 °C et plus"]
    heures = [310, 905, 1240, 1020, 410]
    return [{"classe_temperature": l, "Passages pointe temps sec": v, "Heures pointe temps sec": h} for l, v, h in zip(labels, vals, heures)]


def meteo3_profil():
    out = []
    for h in range(24):
        sec = 8 + 160 * _g(h, 8.2, 1.1) + 190 * _g(h, 18.0, 1.5) + 60 * _g(h, 12.8, 2.4) + 30 * _g(h, 15.5, 3)
        out.append({"heure_du_jour": h, "Passages semaine sans pluie": round(sec, 1),
                    "Passages semaine avec pluie": round(sec * (0.84 + 0.02 * _g(h, 3, 3)) * R.uniform(0.985, 1.015), 1)})
    return out
