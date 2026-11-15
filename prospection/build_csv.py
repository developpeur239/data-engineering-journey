"""Étapes 4-7 : fusionne données API + recherches web, calcule score/signal, exporte le CSV trié."""
import json, csv
from datetime import date
TODAY = date(2026, 11, 15)
cands = json.load(open("candidates.json"))
# Exclusions additionnelles identifiées pendant la recherche web
EXCLURE = {"478077233": "groupe (marque du groupe Menway, siège Paris)",
           "921801924": "en liquidation (liquidateur nommé)",
           "984848796": "activité hors recrutement (artisanat/bois, NAF erroné)"}
# Enrichissement manuel : site, téléphone, spécialité, score 0-3, note, source
# Barème score_btp_industrie : 3 = BTP/industrie affiché comme spécialité principale ;
# 2 = BTP/industrie/ingénierie parmi les secteurs clés ; 1 = mention secondaire ou indice indirect ; 0 = autre / inconnu.
E = {
 "979403524": ("https://www.habeo-recrutement.fr/", "06 31 14 06 35 / 07 86 60 27 29", "BTP & Industrie (Bordeaux & Bayonne) : ingénieurs structure, chargés d'affaires MOE TCE, projeteurs CFO/CFA", 3, "Spécialiste affiché BTP/industrie ; offres actives (HelloWork, France Travail)"),
 "988375853": ("https://skillcore-industrie.fr/", "", "Recrutement industriel : techniciens, ingénieurs, managers (aéronautique, nucléaire, maintenance)", 3, "Cabinet 100% industrie, basé Bordeaux (siège Arcachon), fondateur Steven Clos"),
 "938596210": ("https://www.highring.fr/", "06 87 63 19 97", "Cadres & profils techniques : construction, travaux, génie civil, ingénierie, énergie", 3, "Offres type Ingénieur Travaux ; 17 rue Professeur Démons 33000"),
 "879464725": ("https://maherecrutement.fr/", "05 56 91 26 77", "Chasse de tête cadres, multi-secteurs dont BTP/construction, industrie, ingénierie", 2, "90+ recrutements/an, 4,9/5 (174 avis Google)"),
 "533868477": ("https://www.phi-rh.fr/", "05 57 99 01 77", "Multi-spécialiste : logistique, industrie, ingénierie, BTP, finance, santé (PHI Santé)", 2, "10-19 salariés"),
 "514085430": ("https://www.decorgnoletagnes.fr/", "05 35 54 27 82", "Généraliste ; vin & spiritueux, agroalimentaire, industrie, défense", 1, "Immeuble La Fabrique, 11 rue de Gironde 33300"),
 "106932684": ("https://valtonrecrutement.fr/", "06 67 46 08 79", "Généraliste (CDI/CDD/missions), mentions BTP/industrie", 1, "Créé 07/2026"),
 "817899339": ("", "", "Comptabilité/audit/paie majoritairement ; quelques postes ingénierie (RAMS)", 1, "Indeed le classe aérospatial & défense ; 3-5 salariés"),
 "930376538": ("https://www.mahay-consulting.fr/", "", "Recrutement sur-mesure « de l'industrie au… » (site Wix peu lisible)", 1, "Consultante indépendante, 10 ans d'expérience"),
 "939159166": ("https://www.keypoints-recrutement.fr/", "", "IT/digital, finance, commercial ; un peu d'ingénierie", 1, ""),
 "880208590": ("https://www.bonne-recrue.com/", "", "Vin & spiritueux, finance, commerce, un peu d'industrie", 1, ""),
 "343463063": ("https://www.grandest-recrutement.com/", "03 69 61 34 93", "Généraliste (tertiaire, IT, BTP, industrie, transport)", 1, "Site basé à Molsheim (67) : lien avec l'établissement de Belin-Béliet à vérifier"),
 "130190002": ("", "", "Enseigne « MH Connect / Manufacture » → probable orientation industrie", 1, "Créé 09/2026, aucune présence web trouvée"),
 "797993110": ("", "", "Enseigne « ENR Search » → probable énergies renouvelables", 1, "Aucune présence web trouvée"),
 "513361402": ("https://www.skillink.com/", "01 83 81 86 20", "Tech, digital & innovation", 0, "Siège Paris, bureau Bordeaux"),
 "897735288": ("https://www.connity.fr/", "", "Écosystème digital / numérique", 0, ""),
 "988173308": ("https://recrutis-rh.com/", "", "Personnel soignant (santé)", 0, ""),
 "106560188": ("", "", "Santé (enseigne Recrutis)", 0, "Lié à Recrutis RH"),
 "880483037": ("https://duo-venandi.fr/", "06 25 01 85 74", "Expertise comptable & audit", 0, ""),
 "990681686": ("https://odas-conseil.fr/", "06 26 45 89 57", "Finance, profils rares", 0, "Créé 08/2025"),
 "100796929": ("https://www.cristalconseils.fr/", "07 70 05 30 40", "Management de transition PME/ETI", 0, ""),
 "898102751": ("https://maerajanin.fr/", "07 56 86 26 88", "Bilan de compétences / sophrologie", 0, "Pas vraiment un cabinet de recrutement"),
 "109803544": ("https://www.earlybirdtalent.com/", "", "Inconnue (site « prochainement disponible »)", 0, "Créé 09/2026"),
 "928485374": ("https://raretalents.fr/", "", "Inconnue (site « coming soon »)", 0, ""),
 "951246842": ("", "", "Recrutement data/IA, RPO (freelance Malt)", 0, ""),
 "130409790": ("", "", "Sciences de la vie (d'après le nom)", 0, "Filiale de TECHNICAL HIRES (président)"),
 "952707651": ("", "", "Médical (d'après le nom)", 0, ""), "940038052": ("", "", "Médical (d'après le nom)", 0, ""),
 "790961494": ("", "", "Médical probable (d'après le nom)", 0, ""),
 "901822403": ("", "", "Généraliste (annuaire blog-rh)", 0, "155 av. d'Eysines 33110 Le Bouscat ; 5/5 (7 avis)"),
}
def signal(r):
    d = date.fromisoformat(r["date_creation"]); s = []
    if (TODAY - d).days < 3 * 365: s.append(f"créé il y a < 3 ans ({d.strftime('%m/%Y')})")
    return " ; ".join(s)
rows = []
for r in cands:
    if r["siren"] in EXCLURE: continue
    site, tel, spec, score, note = E.get(r["siren"], ("", "", "Inconnue (aucune présence web trouvée)", 0, ""))
    rows.append({"nom": r["nom"], "siren": r["siren"], "date_creation": r["date_creation"], "tranche_effectif": r["tranche_effectif"],
                 "ville": r["ville"], "adresse": r["adresse"], "dirigeants": r["dirigeants"], "site_web": site, "telephone": tel,
                 "specialite": spec, "score_btp_industrie": score, "signal": signal(r),
                 "recrute_business_manager": "non trouvé", "notes": note})
rows.sort(key=lambda x: (-x["score_btp_industrie"], -int(x["date_creation"].replace("-", ""))))
with open("../cabinets_bordeaux.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter=";"); w.writeheader(); w.writerows(rows)
print(len(rows), "cabinets ->", "cabinets_bordeaux.csv")
