"""Calcule signal_fort / force_signal à partir des données brutes et écrit le CSV trié.
Usage : python3 build_signals.py <csv_source> <signals_raw.json> <csv_sortie> [annotations.json]

Barème force_signal :
  3 = fort   : offre commerciale/consultant pour son propre compte publiée il y a ≤ 90 j (date vérifiée),
               ou fondateur issu d'un grand cabinet installé depuis < 12 mois
  2 = moyen  : offre interne encore en ligne mais date exacte inconnue (> 30 j sur France Travail),
               ou lancement < 12 mois avec site actif, ou nouvelle agence / associé daté < 12 mois
  1 = faible : cabinet créé il y a 12-36 mois, lancement < 12 mois sans présence web,
               forte activité (≥ 20 offres clients en ligne), ou implantation/associé non daté
  0 = aucun signal détecté
"""
import csv, json, re, sys
import signals_lib as S
from datetime import date
TODAY = date(2026, 11, 15)


def months(d):
    d = date.fromisoformat(d)
    return (TODAY.year - d.year) * 12 + TODAY.month - d.month


def evaluate(row, raw, ann):
    sigs = []  # (force, texte)
    if raw:
        seen = set()
        for j in sorted(raw["jobs"], key=lambda j: j.get("date") or "", reverse=True):
            own, why = S.classify(j["titre"], j.get("description", ""))   # reclassement avec les règles à jour
            key = S.norm(j["titre"])[:40]
            if not own or key in seen:
                continue
            seen.add(key)
            freelance = re.search(r"ind[ée]pendant|freelance", j["titre"], re.I)
            n_dup = sum(1 for x in raw["jobs"] if S.norm(x["titre"])[:40] == key)
            label = "Recrute des consultants indépendants/freelance (réseau)" if freelance else "Offre interne"
            dup = f" ×{n_dup} annonces" if n_dup > 1 else ""
            if j.get("date") and j["date"] != "30j+" and S.recent(j["date"]):
                sigs.append((2 if freelance else 3, f"{label} « {j['titre']} »{dup} ({j['source']}, publiée le {j['date']}) {j['url']}"))
            elif j.get("date") == "30j+":
                sigs.append((2, f"{label} « {j['titre']} » encore en ligne ({j['source']}, publiée il y a > 30 j) {j['url']}"))
        if raw.get("n_offres_hellowork", 0) >= 20:
            sigs.append((1, f"Forte activité : {raw['n_offres_hellowork']} offres clients en ligne sur HelloWork"))
    for a in ann.get(row["siren"], []):
        sigs.append((a["force"], a["texte"]))
    m = months(row["date_creation"])
    if m < 12:
        has_web = bool(row.get("site_web")) or bool(raw and (raw["jobs"] or raw.get("n_offres_hellowork")))
        sigs.append((2 if has_web else 1, f"Lancement récent : créé le {row['date_creation']} ({m} mois)"
                     + ("" if has_web else ", aucune présence web trouvée")))
    elif m < 36:
        sigs.append((1, f"Cabinet jeune : créé le {row['date_creation']} ({m} mois)"))
    sigs.sort(key=lambda x: -x[0])
    return (sigs[0][0] if sigs else 0), " | ".join(t for _, t in sigs)


if __name__ == "__main__":
    src, raw_f, out = sys.argv[1:4]
    ann = json.load(open(sys.argv[4])) if len(sys.argv) > 4 else {}
    raw = json.load(open(raw_f))
    rows = list(csv.DictReader(open(src, encoding="utf-8-sig"), delimiter=";"))
    for r in rows:
        if int(r["score_btp_industrie"]) >= 1:
            r["force_signal"], r["signal_fort"] = evaluate(r, raw.get(r["siren"]), ann)
        else:
            r["force_signal"], r["signal_fort"] = "", "non analysé (score_btp_industrie = 0)"
        r.pop("signal", None); r.pop("recrute_business_manager", None)
    rows.sort(key=lambda r: (-(r["force_signal"] if r["force_signal"] != "" else -1), -int(r["score_btp_industrie"]),
                             -int(r["date_creation"].replace("-", ""))))
    cols = ["nom", "siren", "force_signal", "signal_fort", "score_btp_industrie", "specialite", "date_creation", "tranche_effectif",
            "ville", "adresse", "dirigeants", "site_web", "telephone", "notes"] + [c for c in rows[0] if c.startswith("departement")]
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=[c for c in cols if c in rows[0]], delimiter=";", extrasaction="ignore")
        w.writeheader(); w.writerows(rows)
    print(len(rows), "lignes ->", out)
