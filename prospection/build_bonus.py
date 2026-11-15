"""Cabinets (hors liste API) qui publient une offre commerciale/consultant pour leur propre compte, d'après les
balayages France Travail des 6 départements. Exclut grands réseaux, intérim, employeurs masqués et réseaux
recrutant des indépendants (franchise / portage)."""
import json, re, csv, collections
import signals_lib as S
from pipeline_multi import RESEAUX, INTERIM
RESEAU_INDEP = re.compile(r"mercato|experts de l.emploi|job direct|orient.action|ikiway|alveor|impactup|voluntae|"
                          r"slash|mistertemp|work&you|avantage|supplay|actual|start people|temporis|talent crit|hays|"
                          r"michael page|manpower|groupe lip|formatique|solutec", re.I)
rows = json.load(open("ft_offres_internes_cabinets.json"))
mine = {S.norm(r["nom"]) for r in csv.DictReader(open("candidates_multi.csv", encoding="utf-8-sig"), delimiter=";")}
by = collections.defaultdict(list)
for o in rows:
    e = o["employeur"]
    if not e or RESEAUX.search(e) or INTERIM.search(e) or RESEAU_INDEP.search(e):
        continue
    if re.search(r"ind[ée]pendant|freelance", o["titre"], re.I):
        continue
    by[S.norm(re.sub(r"[^\w ]", " ", e)).strip()].append(o)
out = []
for k, L in by.items():
    L.sort(key=lambda o: o["date"] if o["date"] not in ("", "30j+") else "0")
    o = L[-1]
    d = o["date"]
    force = 3 if d and d != "30j+" and S.recent(d) else 2
    out.append({"employeur": o["employeur"], "departements": ", ".join(sorted({x["dep"] for x in L})),
                "nb_offres": len(L), "force_signal": force,
                "signal_fort": " | ".join(f"« {x['titre']} » ({x['lieu']}, {x['date_txt'].strip()}) {x['url']}" for x in L[:3]),
                "dans_liste_api": "oui" if any(S.employer_match(o["employeur"], m) for m in mine) else "non"})
out.sort(key=lambda r: (-r["force_signal"], -r["nb_offres"]))
with open("../cabinets_bonus_qui_recrutent.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter=";"); w.writeheader(); w.writerows(out)
for r in out: print(r["force_signal"], "|", r["employeur"][:35], "|", r["departements"], "|", r["nb_offres"], "|", r["dans_liste_api"], "|", r["signal_fort"][:110])
