"""Transforme audit_brut.json (audit_sites.js) en :
  - audit_sites_chauffagistes_33.csv : une ligne par site, toutes les mesures ;
  - audit_sites_chauffagistes_33.md  : rapport lisible, fuites par entreprise,
    classées par priorité de démarchage.
Usage : python prospection/rapport_audit.py
"""

import csv
import json
from pathlib import Path

HERE = Path(__file__).parent
cibles = {c["nom"]: c for c in json.load(open(HERE / "cibles_audit.json", encoding="utf-8"))}
audit = json.load(open(HERE / "audit_brut.json", encoding="utf-8"))


def leaks(a, c):
    """Liste (gravité, texte) des fuites visibles, de la plus grave à la moins grave."""
    out = []
    pays = a.get("google_ads") or a.get("meta_pixel")
    pub = " et ".join(x for x, k in [("Google Ads", "google_ads"), ("Meta", "meta_pixel")] if a.get(k))
    screens = a.get("cta_ecrans")
    if screens == "" or screens is None:
        out.append((3, "Aucun bouton devis/contact repéré sur la page d'accueil mobile"))
    elif screens > 1.5:
        out.append((3 if pays else 2,
                    f"Le premier bouton devis/contact est à {screens:.1f} écrans de défilement sur mobile"
                    + (f" alors que l'entreprise paie de la pub ({pub})" if pays else "")))
    if not a.get("tel_cliquable"):
        out.append((2, "Numéro non cliquable sur mobile (affiché en texte ou caché dans le menu)"))
    elif not a.get("tel_1er_ecran"):
        out.append((1, "Numéro cliquable, mais pas visible sans défiler ni ouvrir le menu"))
    champs = a.get("page_devis_champs")
    if champs and champs >= 15:
        out.append((2, f"Formulaire de devis long : {champs} champs (abandon fréquent)"))
    note, avis = c.get("note_google"), c.get("nb_avis_google")
    if not a.get("avis_affiches") and avis and float(note or 0) >= 4.3:
        out.append((1, f"Note Google {note}/5 ({avis} avis) non mise en avant sur le site"))
    if not a.get("rdv_en_ligne") and not a.get("chat"):
        out.append((1, "Ni prise de RDV en ligne ni chat : le visiteur doit appeler ou attendre un rappel"))
    if float(a.get("chargement_s") or 0) >= 5:
        out.append((1, f"Page lente : {a['chargement_s']} s avant affichage du contenu sur mobile"))
    return sorted(out, key=lambda x: -x[0])


rows = []
for a in audit:
    c = cibles[a["nom"]]
    L = leaks(a, c)
    pays = bool(a.get("google_ads") or a.get("meta_pixel"))
    # Priorité : paie déjà du trafic (comme dans la méthode "Boring Marketer"),
    # pas d'outil de relance visible, fuites graves, volume d'avis (activité).
    prio = (3 * pays + 2 * (not a.get("crm_emailing")) + sum(g for g, _ in L)
            + min(int(c["nb_avis_google"] or 0) // 100, 3))
    rows.append({
        "priorite": prio, "nom": c["nom_google"] or c["nom"], "raison_sociale": c["nom"],
        "ville": c["ville"], "ca": c["ca"], "note_google": c["note_google"],
        "nb_avis_google": c["nb_avis_google"], "telephone": c["telephone"], "site": a["site"],
        "dirigeants": c["dirigeants"],
        "paie_pub": ", ".join(x for x, k in [("Google Ads", "google_ads"), ("Meta", "meta_pixel")] if a.get(k)) or "non détecté",
        "outil_crm_emailing": "oui" if a.get("crm_emailing") else "non détecté",
        "cms": a.get("cms"), "chargement_s": a.get("chargement_s"),
        "cta_principal": (a.get("cta_principal") or "").replace("\n", " "),
        "cta_ecrans": a.get("cta_ecrans"), "tel_cliquable": a.get("tel_cliquable"),
        "tel_1er_ecran": a.get("tel_1er_ecran"), "formulaire_accueil": a.get("formulaire_accueil"),
        "page_devis": a.get("page_devis", ""), "page_devis_champs": a.get("page_devis_champs"),
        "rdv_en_ligne": a.get("rdv_en_ligne"), "chat": a.get("chat"),
        "avis_affiches": a.get("avis_affiches"), "simulateur_aides": a.get("simulateur_aides"),
        "fuites": " | ".join(t for _, t in L),
        "fuite_principale": L[0][1] if L else "",
        "capture_mobile": f"audit_captures/{c['siren']}.png",
    })
rows.sort(key=lambda r: -r["priorite"])

with open(HERE / "audit_sites_chauffagistes_33.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)

n = len(rows)
def count(k, v=True):
    return sum(1 for a in audit if bool(a.get(k)) == v)

md = [f"# Audit des sites : {n} chauffagistes / PAC en Gironde", "",
      "Audit fait avec un navigateur mobile (iPhone 13), page d'accueil + page devis/contact.",
      "Les détections sont automatiques : à confirmer à l'œil avant de montrer quoi que ce soit à un patron.", "",
      "## Vue d'ensemble", "",
      f"- **Pas d'outil de CRM / emailing visible** sur le site : {count('crm_emailing', False)}/{n} "
      "(donc probablement pas de relance automatique des demandes et des devis ; à confirmer en appel, "
      "certains utilisent un logiciel de devis qui ne laisse pas de trace sur le site)",
      f"- **Paient de la pub** (Google Ads ou Meta détecté) : "
      f"{sum(1 for a in audit if a.get('google_ads') or a.get('meta_pixel'))}/{n}",
      f"- **Numéro non cliquable sur mobile** (ou caché dans le menu) : {count('tel_cliquable', False)}/{n}",
      f"- **Ni prise de RDV en ligne ni chat** : {sum(1 for a in audit if not a.get('rdv_en_ligne') and not a.get('chat'))}/{n}",
      f"- **Bouton devis/contact absent ou à plus d'1,5 écran** : "
      f"{sum(1 for a in audit if a.get('cta_ecrans') in ('', None) or a.get('cta_ecrans') > 1.5)}/{n}",
      f"- **Avis Google non mis en avant** : {count('avis_affiches', False)}/{n}", "",
      "## Par entreprise (ordre de priorité de démarchage)", "",
      "Priorité = paie déjà de la pub + aucun outil de relance visible + gravité des fuites + volume d'avis.", ""]
for i, r in enumerate(rows, 1):
    ca = f"{int(r['ca']) / 1e6:.1f} M€" if r["ca"] else "CA non publié"
    md += [f"### {i}. {r['nom']} ({r['ville']})",
           f"{ca} · {r['note_google']}/5 sur {r['nb_avis_google']} avis · {r['telephone']} · {r['site']}",
           f"Dirigeant(s) : {r['dirigeants'] or 'non renseigné'} · Pub : {r['paie_pub']} · CRM/emailing : {r['outil_crm_emailing']}", ""]
    if r["fuites"]:
        md += [f"- {t}" for t in r["fuites"].split(" | ")]
    else:
        md += ["- Pas de fuite évidente sur le site : l'angle reste la relance des devis envoyés."]
    md += [f"- Capture mobile : `prospection/{r['capture_mobile']}`", ""]
(HERE / "audit_sites_chauffagistes_33.md").write_text("\n".join(md), encoding="utf-8")
print(f"{n} sites -> audit_sites_chauffagistes_33.csv / .md")
for r in rows:
    print(r["priorite"], r["nom"][:28].ljust(28), "|", r["paie_pub"][:18].ljust(18), "|", r["fuite_principale"][:95])
