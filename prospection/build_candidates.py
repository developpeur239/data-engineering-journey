"""Étape 3 : normalise les données API et applique les exclusions."""
import json, re
TR = {"NN":"non renseigné","00":"0 salarié","01":"1-2","02":"3-5","03":"6-9","11":"10-19","12":"20-49",
      "21":"50-99","22":"100-199","31":"200-249","32":"250-499","41":"500-999","42":"1000-1999","51":"2000-4999"}
BIG = {"21","22","31","32","41","42","51","52","53"}  # >= 50 salariés
GRANDS_RESEAUX = r"MICHAEL PAGE|HAYS|ADECCO|RANDSTAD|MANPOWER|ROBERT WALTERS|EXPECTRA|PAGE PERSONNEL|LHH|BADENOCH|MERCURI URVAL|APEC|HARRY HOPE|WINSEARCH|SPRING|KELLY|SYNERGIE|CRIT\b|^PROFIL\b"
INTERIM = r"ADEQUAT|PLANETT|JOB INTER|INTERIM|INTÉRIM|TEMPORAIRE|PROMAN|SAMSIC|PARTNAIRE|ADOMO|OPTEAMAN"
# Structures hors cible (pas des cabinets) : groupements d'employeurs, associations d'insertion,
# agences d'hôtesses, entreprises mal codées NAF.
HORS_CIBLE = {
 "493524763":"groupement d'employeurs","880742424":"groupement d'employeurs (50-99)","348946468":"groupement d'employeurs",
 "497840587":"groupement d'employeurs viticole","497840629":"groupement d'employeurs viticole","500526322":"groupement d'employeurs",
 "441001443":"groupement d'employeurs","348114349":"association d'insertion","383666377":"Pier Import - distribution (NAF erroné)",
 "481861094":"agence d'hôtesses","752361147":"agence d'hôtesses/mannequins","819054586":"agence d'hôtesses événementielles",
}
def ville33(r):
    m = [e for e in r.get("matching_etablissements", []) if str(e.get("code_postal","")).startswith("33")]
    e = m[0] if m else r["siege"]
    return e.get("libelle_commune"), e.get("adresse")
def dirig(r):
    out = []
    for d in r.get("dirigeants", []):
        if d.get("type_dirigeant") == "personne physique":
            p = ' '.join(dict.fromkeys(d.get('prenoms','').split())); out.append(f"{p.title()} {d.get('nom','').upper()} ({d.get('qualite') or 'n.c.'})")
        else:
            out.append(f"{d.get('denomination')} ({d.get('qualite') or 'n.c.'})")
    return " ; ".join(out)
rows, excl = [], []
for r in json.load(open("raw_api.json")):
    nom = r["nom_complet"]; t = r.get("tranche_effectif_salarie")
    raison = None
    if re.search(GRANDS_RESEAUX, nom, re.I): raison = "grand réseau / groupe"
    elif re.search(INTERIM, nom, re.I): raison = "intérim / services"
    elif t in BIG: raison = "> 50 salariés"
    elif r["siren"] in HORS_CIBLE: raison = HORS_CIBLE[r["siren"]]
    ville, adr = ville33(r)
    row = dict(nom=nom, siren=r["siren"], date_creation=r["date_creation"], tranche_effectif=TR.get(t, "non renseigné"),
               ville=ville, adresse=adr, dirigeants=dirig(r))
    (excl if raison else rows).append({**row, "raison_exclusion": raison} if raison else row)
json.dump(rows, open("candidates.json","w"), ensure_ascii=False, indent=1)
json.dump(excl, open("exclus.json","w"), ensure_ascii=False, indent=1)
print(len(rows), "retenus /", len(excl), "exclus")
for e in excl: print("  EXCLU", e["nom"][:50], "->", e["raison_exclusion"])
