"""Construit la preuve Habeo (v2) :
  - ../preuve_habeo.csv          : version complète, usage interne (dirigeants, téléphones, liens)
  - ../preuve_habeo_client.html  : version à montrer au client (sans dirigeants ni téléphones)
Chaque poste est affiché avec SA date de publication (recalculée au 16/11/2026 depuis « Publié il y a N jours »).

v2 : Lesbats, Iumana, Sirems (métiers techniciens) et Créa Concept (assistance technique mise en avant)
remplacés par SMC2, Hydrogène de France, Proditec et Altereo (ingénieurs / chargés d'affaires / projeteurs).
"""
import csv, html, json, re
from datetime import date, timedelta

TODAY = date(2026, 11, 16)
NAF = {"25.11Z": "Chaudronnerie, structures métalliques", "43.11Z": "Démolition / déconstruction",
       "43.21A": "Installation électrique et génie climatique", "43.22B": "Génie climatique (CVC)",
       "71.12B": "Ingénierie, bureau d'études", "43.32B": "Menuiserie métallique", "35.11Z": "Énergie (centrales hydrogène)",
       "26.70Z": "Fabrication d'équipements industriels"}
POSTE = re.compile(r"ing[ée]nieur|charg[ée]e? d.affaires|projeteu?r|conduct\w* de travaux|chef de chantier|technicien", re.I)

# Sélection finale (SIREN vérifiés dans l'API recherche-entreprises ; téléphones relevés sur le site de l'entreprise)
SELECTION = [
    {"emp": ["AVENIR DECONSTRUCTION"], "nom": "Avenir Déconstruction", "siren": "413824319", "ville": "Artigues-près-Bordeaux (33)",
     "effectif": "200-249", "naf": "43.11Z", "dirigeant": "Jean-Philippe RENIER (Président)", "tel": "05 57 77 13 13",
     "site": "https://www.avenirdeconstruction.com/"},
    {"emp": ["ROUZES NOUVELLE-AQUITAINE"], "nom": "Rouzes Nouvelle-Aquitaine", "siren": "450773262", "ville": "Eysines (33)",
     "effectif": "20-49", "naf": "43.32B", "dirigeant": "Dominique DELESTAING (Directeur général)", "tel": "", "site": "",
     "note": "rattachée au Groupe FR (classé ETI)"},
    {"emp": ["LARRIPA"], "nom": "Larripa", "siren": "481665479", "ville": "Bassussarry (64)", "effectif": "10-19", "naf": "43.22B",
     "dirigeant": "Michel LARRIPA (Président)", "tel": "05 59 42 42 43", "site": "https://www.larripa.fr/"},
    {"emp": ["P&H Energies"], "nom": "P&H Énergies", "siren": "880205497", "ville": "Le Barp (33)", "effectif": "10-19", "naf": "43.21A",
     "dirigeant": "Thomas POULAIN (Président de P et H Groupe, holding présidente)", "tel": "", "site": ""},
    {"emp": ["EXOES"], "nom": "Exoes", "siren": "512584806", "ville": "Gradignan (33)", "effectif": "20-49", "naf": "71.12B",
     "dirigeant": "Arnaud DESRENTES (Président d'Exoes Group, holding présidente) ; Rémi DACCORD (Directeur général du groupe)",
     "tel": "09 72 50 30 86", "site": "https://exoes.com/"},
    {"emp": ["ATELIERS BAYONNAIS MECANIQUE ET SOUDURE", "ATELIERS BAYONNAIS DE MECANIQUE ET"],
     "nom": "ABMS – Ateliers Bayonnais Mécanique Soudure", "siren": "344577069", "ville": "Bayonne (64)", "effectif": "20-49",
     "naf": "25.11Z", "dirigeant": "Patrick ALONSO, Baptiste ALONSO, Benjamin ALONSO (Gérants)", "tel": "", "site": ""},
    {"emp": ["SMC2"], "nom": "SMC2", "siren": "450758404", "ville": "Bordeaux (33) – siège Mornant (69)", "effectif": "50-99",
     "naf": "71.12B", "dirigeant": "Samuel GUILLERMARD et Nicolas ROBIN (Gérants de SMC2 Group, holding présidente)",
     "tel": "04 78 67 60 56", "site": "https://www.smc2-construction.com/",
     "note": "constructeur de bâtiments à structure textile/bois ; poste basé à Bordeaux"},
    {"emp": ["HYDROGENE DE FRANCE"], "nom": "Hydrogène de France (HDF Energy)", "siren": "789595956", "ville": "Blanquefort (33)",
     "effectif": "50-99", "naf": "35.11Z", "dirigeant": "Damien HAVARD (Président-directeur général)", "tel": "05 56 77 11 11",
     "site": "https://www.hdf-energy.com/"},
    {"emp": ["PRODITEC"], "nom": "Proditec", "siren": "342874013", "ville": "Pessac (33)", "effectif": "20-49", "naf": "26.70Z",
     "dirigeant": "Christophe RIBOULET (Gérant de CECOFI, holding présidente)", "tel": "05 57 89 17 20", "site": "https://proditec.com/"},
    {"emp": ["ALTEREO"], "nom": "Altereo", "siren": "453686966", "ville": "Villenave-d'Ornon (33)", "effectif": "100-199",
     "naf": "71.12B", "dirigeant": "Gilles BRUNSCHWIG (Président d'Altercapital, holding présidente)", "tel": "", "site": "",
     "note": "rattachée au groupe Altercapital (classé ETI)"},
]


def pub_date(o):
    t = o.get("date_txt", "")
    m = re.search(r"il y a (\d+) jour", t)
    if m:
        return TODAY - timedelta(days=int(m.group(1)))
    if "hier" in t:
        return TODAY - timedelta(days=1)
    if "aujourd" in t:
        return TODAY
    return None  # « plus de 30 jours » : date exacte inconnue


def clean_title(t):
    return re.sub(r"\s*\((?:H/F|F/H)\)|\s*[HF]/[HF]\b", "", t).strip(" -")


def tkey(t):
    t = re.sub(r"\b(?:de|d|des|du|la|le|l)\b|['’]", " ", clean_title(t).lower())
    return re.sub(r"[^a-zàâçéèêëîïôûùüÿ]", "", t)[:30]


pool = json.load(open("preuve_ft_raw.json"))["all"]
for v in json.load(open("preuve_extra.json")):
    pool += v["offres"]
rows = []
for s in SELECTION:
    offers = {o["id"]: o for o in pool if o["employeur"] in s["emp"] and POSTE.search(o["titre"]) and "CDI" in o.get("contrat", "CDI")}
    uniq = {}
    for o in sorted(offers.values(), key=lambda o: pub_date(o) or date(2000, 1, 1), reverse=True):
        uniq.setdefault((tkey(o["titre"]), o["ville"].lower()[:5]), o)
    offs = sorted(uniq.values(), key=lambda o: pub_date(o) or date(2000, 1, 1), reverse=True)
    assert offs and pub_date(offs[0]) and (TODAY - pub_date(offs[0])).days <= 15, s["nom"]
    postes = [f"{clean_title(o['titre'])} (publiée le {pub_date(o).strftime('%d/%m') if pub_date(o) else 'il y a > 30 j'})" for o in offs]
    oldest = min((pub_date(o) for o in offs if pub_date(o)), default=None)
    rows.append({**s, "activite": f"{NAF.get(s['naf'], s['naf'])} ({s['naf']})", "offres": offs,
                 "poste_recherche": " ; ".join(postes), "date_publication": pub_date(offs[0]).strftime("%d/%m/%Y"),
                 "plus_ancienne": oldest.strftime("%d/%m/%Y") if oldest else "", "lien_offre": offs[0]["url"],
                 "autres_liens": " ".join(o["url"] for o in offs[1:]), "nb_offres_ouvertes": len(offs)})
rows.sort(key=lambda r: (-r["nb_offres_ouvertes"], r["date_publication"][3:5] + r["date_publication"][:2]), reverse=False)

cols = ["nom", "siren", "ville", "effectif", "activite", "poste_recherche", "date_publication", "plus_ancienne", "lien_offre",
        "autres_liens", "nb_offres_ouvertes", "dirigeant", "tel", "site", "note"]
with open("../preuve_habeo.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.writer(f, delimiter=";")
    w.writerow(["entreprise", "siren", "ville", "effectif", "activite", "poste_recherche", "date_publication (plus récente)",
                "date_premiere_offre", "lien_offre", "autres_liens", "nb_offres_ouvertes", "dirigeant", "telephone_standard", "site_web", "note"])
    for r in rows:
        w.writerow([r.get(c, "") for c in cols])

# ---------------------------------------------------------------- page client (sans dirigeants ni téléphones)
e = html.escape


def postes_html(r):
    return "".join(f'<div class="poste">{e(clean_title(o["titre"]))} <span class="d">publiée le '
                   f'{pub_date(o).strftime("%d/%m/%Y") if pub_date(o) else "il y a plus de 30 jours"}</span> '
                   f'<a href="{e(o["url"])}">voir l\'offre</a></div>' for o in r["offres"])


trs = "\n".join(f"""      <tr>
        <td><strong>{e(r['nom'])}</strong><span class="sub">{e(r['activite'].split(' (')[0])}</span></td>
        <td>{e(r['ville'])}</td>
        <td class="num">{e(r['effectif'])}</td>
        <td>{postes_html(r)}</td>
        <td class="num">{r['nb_offres_ouvertes']}</td>
      </tr>""" for r in rows)
page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>10 PME qui recrutent vos profils cette semaine</title>
<style>
  :root {{ --bg:#ffffff; --fg:#1d2430; --muted:#5d6878; --line:#e3e7ee; --head:#f4f6f9; --accent:#1f5f8b; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#14181f; --fg:#e7ebf1; --muted:#9aa6b6; --line:#2a313c; --head:#1b2029; --accent:#7db7e0; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  main {{ max-width:1100px; margin:0 auto; padding:40px 16px 32px; }}
  h1 {{ font-size:26px; margin:0 0 6px; letter-spacing:-.01em; }}
  .lead {{ color:var(--muted); margin:0 0 24px; max-width:820px; }}
  .wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:8px; }}
  table {{ border-collapse:collapse; width:100%; min-width:760px; }}
  th, td {{ text-align:left; vertical-align:top; padding:10px 12px; border-bottom:1px solid var(--line); }}
  th {{ background:var(--head); font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); font-weight:600; }}
  tr:last-child td {{ border-bottom:none; }}
  td.num {{ white-space:nowrap; }}
  .sub {{ display:block; color:var(--muted); font-size:13px; }}
  .poste + .poste {{ margin-top:6px; }}
  .d {{ color:var(--muted); font-size:13px; white-space:nowrap; }}
  a {{ color:var(--accent); font-size:13px; white-space:nowrap; }}
  .method {{ color:var(--muted); font-size:13px; margin-top:18px; max-width:900px; }}
  footer {{ margin-top:28px; padding-top:14px; border-top:1px solid var(--line); color:var(--muted); font-size:14px; }}
</style>
</head>
<body>
<main>
  <h1>10 PME qui recrutent vos profils cette semaine</h1>
  <p class="lead">Gironde et Pyrénées-Atlantiques · CDI · ingénieurs, chargés d'affaires, conducteurs de travaux, projeteurs ·
  offres publiées directement par l'employeur au cours des 15 derniers jours. Entreprises de 10 à 250 salariés,
  hors grands groupes et hors intermédiaires.</p>
  <div class="wrap">
  <table>
    <thead><tr><th>Entreprise</th><th>Ville</th><th>Effectif</th><th>Poste(s) recherché(s)</th><th>Offres</th></tr></thead>
    <tbody>
{trs}
    </tbody>
  </table>
  </div>
  <p class="method">Offres relevées sur France Travail le {TODAY.strftime('%d/%m/%Y')} et vérifiées en ligne le jour même ;
  effectifs issus du registre public des entreprises.</p>
  <footer>Préparé par [Prénom Nom] – prospection téléphonique pour cabinets de recrutement</footer>
</main>
</body>
</html>
"""
open("../preuve_habeo_client.html", "w", encoding="utf-8").write(page)
for r in rows:
    print(r["nb_offres_ouvertes"], "|", r["nom"][:32], "|", r["ville"], "|", r["effectif"], "|", r["poste_recherche"][:110], "|", r["tel"])
