"""Écrit deneb_specs/*.json, deneb_specs/_config_commun.json et deneb_specs/_champs_par_visuel.json."""
import commun as c
import specs as sp

# Champs à glisser dans le puits « Valeurs » de Deneb, dans cet ordre (table gold_station_heure).
# « colonne » = colonne de la table, « mesure » = mesure du modèle (voir le fichier TMDL).
CHAMPS = {
    "01_heatmap_heure_jour": [("colonne", "heure_du_jour"), ("colonne", "jour_semaine_ordre"), ("mesure", "n_penurie"),
                              ("mesure", "n_saturation"), ("mesure", "n_service")],
    "02_rythme_journee": [("colonne", "heure_du_jour"), ("mesure", "n_penurie"), ("mesure", "n_saturation"), ("mesure", "n_service")],
    "03_carte_stations": [("colonne", "station_id"), ("colonne", "station_nom"), ("colonne", "latitude"), ("colonne", "longitude"),
                          ("mesure", "capacite_max"), ("mesure", "n_penurie"), ("mesure", "n_service")],
    "04_haltere_pannes": [("colonne", "periode"), ("mesure", "Taux pénurie sans panne"), ("mesure", "Taux pénurie avec panne"),
                          ("mesure", "Taux saturation sans panne"), ("mesure", "Taux saturation avec panne")],
    "05_meteo_barres": [("colonne", "pluie_libelle"), ("mesure", "Taux pénurie"), ("mesure", "Taux saturation")],
    "06_meteo_nuage": [("colonne", "heure_paris"), ("colonne", "temperature_c"), ("colonne", "pluie_libelle"), ("mesure", "Taux pénurie")],
    "07_meteo_courbes": [("colonne", "heure_du_jour"), ("colonne", "pluie_libelle"), ("mesure", "Taux pénurie")],
}


def main():
    dossier = c.RACINE / "deneb_specs"
    dossier.mkdir(exist_ok=True)
    c.ecrire_json(dossier / "_config_commun.json", c.config_commune())
    for nom, (fabrique, _) in sp.SPECS.items():
        c.ecrire_json(dossier / f"{nom}.json", fabrique())
    c.ecrire_json(dossier / "_champs_par_visuel.json", {
        "_lisez-moi": "Champs à placer dans le puits « Valeurs » de Deneb pour chaque spec, dans cet ordre. Les noms sont ceux "
                      "de la table gold_station_heure du modèle sémantique (colonnes ou mesures). Ne pas renommer les champs.",
        **{n: [{"type": t, "nom": f} for t, f in ch] for n, ch in CHAMPS.items()}})
    print("ok", len(sp.SPECS), "specs")


if __name__ == "__main__":
    main()
