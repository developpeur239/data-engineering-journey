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
    "07_meteo_courbes": [("colonne", "heure_du_jour"), ("colonne", "pluie_libelle"), ("mesure", "Taux pénurie")],
    # page « Météo · 3 ans » : champs de la table gold_velo_meteo_heure
    "09_meteo3_effet_conditions_egales": [("colonne", "type_jour"), ("mesure", "Effet pluie à conditions égales (%)"), ("mesure", "Heures de pluie")],
    "10_meteo3_classes_temperature": [("colonne", "classe_temperature"), ("mesure", "Passages pointe temps sec"), ("mesure", "Heures pointe temps sec")],
    "11_meteo3_profil_horaire_semaine": [("colonne", "heure_du_jour"), ("mesure", "Passages semaine sans pluie"), ("mesure", "Passages semaine avec pluie")],
}


def main():
    dossier = c.RACINE / "deneb_specs"
    dossier.mkdir(exist_ok=True)
    c.ecrire_json(dossier / "_config_commun.json", c.config_commune())
    for nom, (fabrique, _) in sp.SPECS.items():
        c.ecrire_json(dossier / f"{nom}.json", fabrique())
    c.ecrire_json(dossier / "_champs_par_visuel.json", {
        "_lisez-moi": "Champs à placer dans le puits « Valeurs » de Deneb pour chaque spec, dans cet ordre. Les noms sont ceux "
                      "de la table gold_station_heure du modèle sémantique (specs 01 à 05 et 07) ou gold_velo_meteo_heure (specs 09 à 11) (colonnes ou mesures). Ne pas renommer les champs.",
        **{n: [{"type": t, "nom": f} for t, f in ch] for n, ch in CHAMPS.items()}})
    print("ok", len(sp.SPECS), "specs")


if __name__ == "__main__":
    main()
