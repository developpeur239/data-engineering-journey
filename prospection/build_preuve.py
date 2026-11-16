"""Construit preuve_habeo.csv et preuve_habeo.html à partir de preuve_candidats.json / preuve_enrich.json.
La sélection finale et les compléments (téléphones vérifiés sur les sites, dirigeants derrière les holdings)
sont documentés ci-dessous."""
import csv, html, json, re
from datetime import date, timedelta

TODAY = date(2026, 11, 16)
NAF = {"16.10A": "Sciage et rabotage du bois", "25.11Z": "Fabrication de structures métalliques (chaudronnerie)",
       "43.29B": "Installation d'ascenseurs et équipements", "43.11Z": "Travaux de démolition / déconstruction",
       "43.21A": "Travaux d'installation électrique et CVC", "43.22B": "Installation thermique et climatisation",
       "71.12B": "Ingénierie, études techniques", "41.20B": "Construction de bâtiments",
       "43.32B": "Menuiserie métallique et serrurerie"}
# Sélection : employeurs directs, 10-250 salariés, hors filiales de grands groupes et hors sociétés
# d'assistance technique (Arial Industries, Atyx, Davricourt, Studiel, Acaly, AVNIR, Creatym écartées).
SELECTION = {
    "LESBATS SCIERIES D AQUITAINE": {"nom": "Lesbats Scieries d'Aquitaine", "ville": "Saint-Perdon / Léon (40)", "dirigeant": "Paul LESBATS (Président) ; Benoît LESBATS (Directeur général)",
                                     "tel": "05 58 49 20 40", "site": "https://www.lesbats.com/"},
    "ATELIERS BAYONNAIS MECANIQUE ET SOUDURE": {"ville": "Bayonne (64)", "dirigeant": "Patrick ALONSO, Baptiste ALONSO, Benjamin ALONSO (Gérants)",
                                                "tel": "", "site": "", "alias": ["ATELIERS BAYONNAIS DE MECANIQUE ET"], "nom": "ABMS – Ateliers Bayonnais Mécanique Soudure"},
    "IUMANA": {"ville": "Arbonne (64)", "dirigeant": "Jean-Pierre ZOLEZZI (Président)", "tel": "", "site": ""},
    "AVENIR DECONSTRUCTION": {"nom": "Avenir Déconstruction", "ville": "Artigues-près-Bordeaux (33)", "dirigeant": "Jean-Philippe RENIER (Président)",
                              "tel": "05 57 77 13 13", "site": "https://www.avenirdeconstruction.com/"},
    "CREA CONCEPT": {"nom": "Créa Concept", "ville": "Bidart / Biarritz (64)", "dirigeant": "Florent FORTE, Cédric MACHEFERT, Stéphan MACHEFERT (Gérants)",
                     "tel": "", "site": "https://www.creaconcept.fr/", "note": "bureau d'études qui propose aussi de l'assistance technique"},
    "P&H Energies": {"ville": "Le Barp (33)", "dirigeant": "Thomas POULAIN (Président de P et H Groupe, holding présidente)",
                     "tel": "", "site": "", "nom": "P&H Énergies"},
    "LARRIPA": {"ville": "Bassussarry (64)", "dirigeant": "Michel LARRIPA (Président)", "tel": "05 59 42 42 43", "site": "https://www.larripa.fr/"},
    "EXOES": {"ville": "Gradignan (33)", "dirigeant": "Arnaud DESRENTES (Président d'Exoes Group, holding présidente) ; Rémi DACCORD (Directeur général du groupe)",
              "tel": "09 72 50 30 86", "site": "https://exoes.com/"},
    "SIREMS SERVICE": {"ville": "Le Pian-Médoc (33)", "dirigeant": "Olivier PIERRE (Président via Holding FP3G)", "tel": "", "site": ""},
    "ROUZES NOUVELLE-AQUITAINE": {"ville": "Eysines (33)", "dirigeant": "Dominique DELESTAING (Directeur général)", "tel": "", "site": ""},
}


def real_date(o):
    """Date de publication recalculée au 16/11 depuis le libellé France Travail (« il y a N jours »)."""
    m = re.search(r"il y a (\d+) jour", o["date_txt"])
    if m:
        return TODAY - timedelta(days=int(m.group(1)))
    if "hier" in o["date_txt"]:
        return TODAY - timedelta(days=1)
    if "aujourd" in o["date_txt"]:
        return TODAY
    return None


cands = {v["employeur"]: v for v in json.load(open("preuve_candidats.json"))}
enrich = json.load(open("preuve_enrich.json"))
rows = []
for key, s in SELECTION.items():
    v = cands[key]
    offers = list(v["offres_toutes"])
    for a in s.get("alias", []):
        offers += cands[a]["offres_toutes"]
    for o in offers:
        o["_d"] = real_date(o)
    # Offres HelloWork localisées dans la zone, si elles n'existent pas déjà sur France Travail
    seen = {re.sub(r"\W+", "", o["titre"].lower())[:30] for o in offers}
    for t, d, u, loc in enrich.get(key, {}).get("hw_local", []):
        k = re.sub(r"\W+", "", t.lower())[:30]
        if k not in seen and d:
            seen.add(k)
            offers.append({"titre": t, "_d": date.fromisoformat(d), "url": u, "ville": loc, "source": "HelloWork"})
    offers.sort(key=lambda o: o["_d"] or date(2000, 1, 1), reverse=True)
    def tkey(t):
        t = re.sub(r"\(?[hf]/[hf]\)?", " ", t.lower())
        t = re.sub(r"\b(?:de|d|des|du|la|le|l)\b|['’]", " ", t)
        return re.sub(r"[^a-z]", "", __import__("unicodedata").normalize("NFKD", t).encode("ascii", "ignore").decode())[:30]
    distinct = {tkey(o["titre"]) + ("|" + o.get("ville", "") if tkey(o["titre"]) else "") for o in offers}
    distinct = {d.split("|")[0] + ("|" + d.split("|")[1].lower()[:5] if "|" in d else "") for d in distinct}
    oldest = min(o["_d"] for o in offers if o["_d"])
    recent = offers[0]
    i = v["info"]
    rows.append({
        "entreprise": s.get("nom", i["raison_sociale"].title() if key.isupper() else key),
        "siren": i["siren"], "ville": s["ville"], "effectif": i["effectif"] + " salariés",
        "activite": f"{NAF.get(i['naf'], i['naf'])} ({i['naf']})",
        "poste_recherche": " ; ".join({tkey(o["titre"]): re.sub(r"\s*\((?:H/F|F/H)\)|\s*H/F|\s*F/H", "", o["titre"]).strip() for o in offers}.values()),
        "date_publication": recent["_d"].strftime("%d/%m/%Y"),
        "en_ligne_depuis": f"{(TODAY - oldest).days} jours" ,
        "lien_offre": recent["url"],
        "autres_liens": " ".join(o["url"] for o in offers[1:4]),
        "nb_offres_ouvertes": len(distinct),
        "dirigeant": s["dirigeant"], "telephone_standard": s["tel"], "site_web": s["site"], "note": s.get("note", ""),
        "_score": len(distinct) * 2 + (3 if (TODAY - oldest).days >= 21 else 0),
    })
rows.sort(key=lambda r: (-r["_score"], -r["nb_offres_ouvertes"]))

cols = ["entreprise", "siren", "ville", "effectif", "activite", "poste_recherche", "date_publication", "en_ligne_depuis",
        "lien_offre", "autres_liens", "nb_offres_ouvertes", "dirigeant", "telephone_standard", "site_web", "note"]
with open("../preuve_habeo.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=cols, delimiter=";", extrasaction="ignore")
    w.writeheader(); w.writerows(rows)

# ---------------------------------------------------------------- page HTML (sans téléphones)
e = html.escape
trs = "\n".join(f"""      <tr>
        <td><strong>{e(r['entreprise'])}</strong><span class="sub">{e(r['activite'].split(' (')[0])}</span></td>
        <td>{e(r['ville'])}</td>
        <td class="num">{e(r['effectif'].replace(' salariés', ''))}</td>
        <td>{e(r['poste_recherche'])}</td>
        <td class="num">{e(r['date_publication'])}</td>
        <td class="num">{r['nb_offres_ouvertes']}{' <span class="tag">en ligne depuis ' + e(r['en_ligne_depuis']) + '</span>' if int(r['en_ligne_depuis'].split()[0]) >= 21 else ''}</td>
        <td>{e(r['dirigeant'])}</td>
        <td><a href="{e(r['lien_offre'])}">Voir l'offre</a></td>
      </tr>""" for r in rows)
page = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>10 PME qui recrutent vos profils cette semaine</title>
<style>
  :root {{ --bg:#ffffff; --fg:#1d2430; --muted:#5d6878; --line:#e3e7ee; --head:#f4f6f9; --accent:#1f5f8b; --tag:#fff4e0; --tagfg:#8a5300; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#14181f; --fg:#e7ebf1; --muted:#9aa6b6; --line:#2a313c; --head:#1b2029; --accent:#7db7e0; --tag:#3a2e17; --tagfg:#f3c77a; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
  main {{ max-width:1180px; margin:0 auto; padding:40px 16px 32px; }}
  h1 {{ font-size:26px; margin:0 0 6px; letter-spacing:-.01em; }}
  .lead {{ color:var(--muted); margin:0 0 24px; max-width:820px; }}
  .wrap {{ overflow-x:auto; border:1px solid var(--line); border-radius:8px; }}
  table {{ border-collapse:collapse; width:100%; min-width:900px; }}
  th, td {{ text-align:left; vertical-align:top; padding:10px 12px; border-bottom:1px solid var(--line); }}
  th {{ background:var(--head); font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); font-weight:600; }}
  tr:last-child td {{ border-bottom:none; }}
  td.num {{ white-space:nowrap; }}
  .sub {{ display:block; color:var(--muted); font-size:13px; }}
  .tag {{ display:inline-block; margin-top:4px; padding:1px 6px; border-radius:4px; background:var(--tag); color:var(--tagfg); font-size:12px; white-space:nowrap; }}
  a {{ color:var(--accent); }}
  .method {{ color:var(--muted); font-size:13px; margin-top:18px; max-width:900px; }}
  footer {{ margin-top:28px; padding-top:14px; border-top:1px solid var(--line); color:var(--muted); font-size:14px; }}
</style>
</head>
<body>
<main>
  <h1>10 PME qui recrutent vos profils cette semaine</h1>
  <p class="lead">Gironde, Pyrénées-Atlantiques et Landes · CDI · offres publiées directement par l'employeur au cours des 15 derniers jours.
  Entreprises de 10 à 250 salariés, hors grands groupes et hors intermédiaires.</p>
  <div class="wrap">
  <table>
    <thead><tr><th>Entreprise</th><th>Ville</th><th>Effectif</th><th>Poste(s) recherché(s)</th><th>Publiée le</th><th>Offres ouvertes</th><th>Dirigeant</th><th>Offre</th></tr></thead>
    <tbody>
{trs}
    </tbody>
  </table>
  </div>
  <p class="method">Sources : offres France Travail et HelloWork relevées le {TODAY.strftime('%d/%m/%Y')} ; effectifs et dirigeants issus du registre
  public des entreprises (API recherche-entreprises). « En ligne depuis » signale un poste ouvert depuis au moins 3 semaines.</p>
  <footer>Préparé par [Prénom Nom] – prospection téléphonique pour cabinets de recrutement</footer>
</main>
</body>
</html>
"""
open("../preuve_habeo.html", "w", encoding="utf-8").write(page)
for r in rows:
    print(r["nb_offres_ouvertes"], "|", r["en_ligne_depuis"], "|", r["entreprise"][:40], "|", r["ville"], "|", r["effectif"], "|",
          r["poste_recherche"][:70], "|", r["date_publication"], "|", r["telephone_standard"])
