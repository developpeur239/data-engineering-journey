"""Remplaçants pour la preuve Habeo : uniquement ingénieurs, chargés d'affaires, projeteurs, conducteurs de travaux.
Balayage France Travail ciblé (33/64/40, CDI) + mêmes exclusions que preuve_habeo.py."""
import json, re, concurrent.futures as cf
from datetime import date
import signals_lib as S
from preuve_habeo import ft_search, age_days, lookup, describe, INTERMEDIAIRE, GRANDS_GROUPES, TR, NAF_OK, DEPTS

METIERS2 = ["ingénieur structure", "ingénieur travaux", "ingénieur génie civil", "ingénieur d'études", "ingénieur méthodes",
            "chargé d'affaires électricité", "chargé d'affaires CVC", "chargé d'affaires génie climatique", "chargé d'affaires BTP",
            "chargé d'affaires charpente", "projeteur électricité", "projeteur courant faible", "projeteur structure",
            "dessinateur projeteur", "projeteur BIM", "conducteur de travaux", "ingénieur électricité"]
CORE = re.compile(r"ing[ée]nieur(?:e)?\b|charg[ée]e? d.affaires|projeteu?r|conduct\w* de travaux", re.I)
DEJA = {"AVENIR DECONSTRUCTION", "ROUZES NOUVELLE-AQUITAINE", "LARRIPA", "P&H Energies", "EXOES",
        "ATELIERS BAYONNAIS MECANIQUE ET SOUDURE", "ATELIERS BAYONNAIS DE MECANIQUE ET", "CREA CONCEPT"}
# écartés lors de la 1re passe (assistance technique / groupes) + bureaux de contrôle
ECARTES = re.compile(r"arial|atyx|davricourt|studiel|acaly|avnir|creatym|orona|cerexagri|unicia|iagona|lesbats|iumana|sirems|"
                     r"apave|veritas|socotec|dekra|qualiconsult|alten|segula|expleo|akkodis|assystem|ayming|aktor|"
                     r"amaris|altran|ausy|sii\b|aeroconseil|ingeliance|lgm|cerfrance", re.I)

if __name__ == "__main__":
    jobs = [(q, d) for q in METIERS2 for d in DEPTS]
    offers = {}
    with cf.ThreadPoolExecutor(4) as ex:
        for res in ex.map(lambda a: ft_search(a[0], a[1], False), jobs):
            for o in res:
                offers[o["id"]] = o
    offers = list(offers.values())
    raw = json.load(open("preuve_ft_raw.json"))["all"]
    allo = {o["id"]: o for o in raw + offers}.values()
    print("offres CDI (toutes requêtes) :", len(allo))
    keep = [o for o in allo if CORE.search(o["titre"]) and "CDI" in o["contrat"] and o["employeur"]
            and not INTERMEDIAIRE.search(o["employeur"]) and not GRANDS_GROUPES.search(o["employeur"])
            and not ECARTES.search(o["employeur"]) and o["employeur"] not in DEJA]
    by = {}
    for o in keep:
        by.setdefault(S.norm(o["employeur"]), {"employeur": o["employeur"], "dept": o["dept"], "offres": []})["offres"].append(o)
    # au moins une offre publiée dans les 15 derniers jours
    by = {k: v for k, v in by.items() if any((age_days(o) or 99) <= 15 for o in v["offres"])}
    print("employeurs avec offre <= 15 j :", len(by))
    def enrich(item):
        k, v = item
        r = lookup(v["employeur"], v["dept"])
        return k, (describe(r, v["dept"]) if r else None)
    with cf.ThreadPoolExecutor(4) as ex:
        info = dict(ex.map(enrich, by.items()))
    out, rej = [], {}
    for k, v in by.items():
        i = info[k]
        why = None
        if not i: why = "introuvable"
        elif re.match(r"78\.|70\.22", i["naf"] or ""): why = "intermédiaire"
        elif i["tranche"] not in TR: why = f"effectif {i['tranche']}"
        elif any(GRANDS_GROUPES.search(pm) for pm in i["dirigeants_pm"]) or i["categorie"] == "GE": why = "groupe"
        elif not NAF_OK.match(i["naf"] or ""): why = "NAF incohérent"
        if why:
            rej[why] = rej.get(why, 0) + 1; v["rejet"] = why; v["info"] = i
            continue
        v["info"] = i
        v["nb"] = len({re.sub(r"\W", "", S.norm(o["titre"]))[:30] + o["ville"].lower()[:5] for o in v["offres"]})
        out.append(v)
    print("rejets :", rej, "| retenus :", len(out))
    out.sort(key=lambda v: (-v["nb"], min(age_days(o) or 99 for o in v["offres"])))
    json.dump(out, open("preuve_extra.json", "w"), ensure_ascii=False, indent=1)
    json.dump([v for v in by.values() if v.get("rejet", "").startswith("effectif NN") or v.get("rejet") == "introuvable"],
              open("preuve_extra_inconnus.json", "w"), ensure_ascii=False, indent=1)
    for v in out:
        i = v["info"]
        print(f"\n## {v['employeur']} | {i['raison_sociale']} | {i['naf']} | {i['effectif']} | {i['ville_etab']} (siège {i['siege']}) | {i['categorie']}")
        print("   DIR:", "; ".join(i["dirigeants"][:3]))
        for o in sorted(v["offres"], key=lambda o: age_days(o) or 99):
            print(f"   - {o['titre'][:65]} | {o['ville']} | {o['date_txt'].strip()[:28]} | {o['url']}")
