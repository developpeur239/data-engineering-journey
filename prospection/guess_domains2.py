"""Étape 4b : 2e passe de devinette de domaines (variantes TLD, sans www, indices manuels)."""
import json, re
from guess_domains import fetch, norm
HINTS = {  # domaines suggérés par les recherches web ou noms commerciaux
 "478077233":["macanders.eu","menway.com"], "514085430":["decorgnoletagnes.fr"], "423992882":["rh-partners.fr","rhpartners.fr"],
 "797993110":["enr-search.com","enrsearch.com","enr-search.fr"], "898196969":["tech-a-way.com","techaway.fr","tech-a-way.fr"],
 "130409790":["lifesciencehires.com","life-science-hires.com","technicalhires.com"], "951160449":["karisma-europe.com","karismaeurope.com"],
 "481034858":["karisma-services.fr","karismaservices.fr"], "944785419":["boutdetalent.fr","bout-de-talent.fr"],
 "789383940":["llrh-consulting.fr","ll-rh-consulting.fr","llrhconsulting.fr"], "930391651":["haidma.com","haidma-recruitment.com"],
 "930266879":["konopkatalent.com","konopka-talent.com"], "930414511":["gawinski-selection.com","gawinskiselection.com"],
 "130190002":["mhconnect.fr","mh-connect.fr"], "102079985":["mada-recrutement.fr","mada-rh.fr"], "995127875":["pct-recrutement.fr"],
 "940038052":["medicall-recrutement.fr","medicallrecrutement.fr"], "952707651":["triangle-medical.fr","trianglemedicalsolutions.com"],
 "930210430":["agencepaulina.fr","agence-paulina.fr"],
}
if __name__ != "__main__": raise SystemExit
cands = json.load(open("candidates.json")); res = json.load(open("sites_guess.json"))
import concurrent.futures as cf
def variants(r):
    out = list(HINTS.get(r["siren"], []))
    n = norm(r["nom"]); names = re.findall(r"\(([^)]+)\)", n) + [re.sub(r"\(.*?\)", "", n)]
    for b in names:
        w = [x for x in re.split(r"[^a-z0-9]+", b) if x and x not in ("sarl","sas","s","a")]
        if not w or len(" ".join(w)) < 4: continue
        for s in {"".join(w), "-".join(w)}:
            for t in ("fr","com","eu","io","co"): out.append(f"{s}.{t}")
    return list(dict.fromkeys(out))
def check(r):
    if res.get(r["siren"]): return r["siren"], res[r["siren"]]
    key = [x for x in re.split(r"[^a-z0-9]+", norm(re.sub(r"\(.*?\)","",r["nom"]))) if len(x) > 3 and x not in ("recrutement","conseil","conseils","consulting","search")][:1]
    for d in variants(r):
        for pre in ("https://www.", "https://"):
            u, h = fetch(pre + d + "/")
            if not h: continue
            low = norm(h[:200000])
            if any(k in low for k in ("recrut","talent","candidat","chasse")) and (d in HINTS.get(r["siren"],[]) or all(k in low for k in key)):
                return r["siren"], u
            break
    return r["siren"], None
with cf.ThreadPoolExecutor(16) as ex: res2 = dict(ex.map(check, cands))
json.dump(res2, open("sites_guess.json","w"), indent=1)
for r in cands:
    if res2[r["siren"]] and not res.get(r["siren"]): print("NEW", r["nom"][:45], "->", res2[r["siren"]])
print(sum(1 for v in res2.values() if v), "sites")
