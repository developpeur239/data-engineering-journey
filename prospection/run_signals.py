"""Applique la détection de signaux à une liste de cabinets (CSV ;) et écrit un JSON brut par cabinet.
Usage : python3 run_signals.py <csv> <ft_sweep1.json,ft_sweep2.json> <sortie.json> <score_min>"""
import csv, json, sys, concurrent.futures as cf
import signals_lib as S


def analyse(row, ft_offers):
    nom = row["nom"]
    hw_all = S.hellowork(nom)
    jobs = []
    for o in hw_all:
        if S.ROLE.search(o["titre"]):
            S.hellowork_detail(o)
            jobs.append(o)
    for o in ft_offers:
        if o["employeur"] and S.employer_match(o["employeur"], nom) and S.ROLE.search(o["titre"]):
            jobs.append(dict(o))
    for o in jobs:
        own, why = S.classify(o["titre"], o.get("description", ""))
        o.update(propre_compte=own, raison=why, recente=S.recent(o.get("date", "")))
    return row["siren"], {"nom": nom, "n_offres_hellowork": len(hw_all), "jobs": jobs,
                          "site": S.site_signals(row.get("site_web", "")), "fondateurs": S.founder_signals(row.get("site_web", ""))}


if __name__ == "__main__":
    src, ft_files, out, min_score = sys.argv[1], sys.argv[2].split(","), sys.argv[3], int(sys.argv[4])
    rows = [r for r in csv.DictReader(open(src, encoding="utf-8-sig"), delimiter=";") if int(r["score_btp_industrie"]) >= min_score]
    ft = [o for f in ft_files for o in json.load(open(f))]
    with cf.ThreadPoolExecutor(6) as ex:
        res = dict(ex.map(lambda r: analyse(r, ft), rows))
    json.dump(res, open(out, "w"), ensure_ascii=False, indent=1)
    for s, d in res.items():
        own = [j for j in d["jobs"] if j["propre_compte"]]
        if own or d["fondateurs"]:
            print(f"## {d['nom'][:50]} — HW {d['n_offres_hellowork']} offres, internes: {[(j['titre'][:40], j.get('date')) for j in own]}")
