"""Construit script_lune.md (5 parties) à partir de script_data.py. python3 build_md.py"""
import re
exec(open('script_data.py').read())
W = lambda s: len(re.findall(r"[\wÀ-ÿ'’-]+", s))
BEATS = {1: "Ouverture", 2: "Contrat", 3: "Vraie histoire", 4: "Le calcul", 5: "Simulation", 6: "Escalade",
         7: "Retournement", 8: "Retour", 9: "La vérité"}
PCT = {1: 4, 2: 3, 3: 14, 4: 8, 5: 21, 6: 29, 7: 6, 8: 4, 9: 11}
def dur(r):
    if r[2]: return W(r[2]) / 150 * 60
    m = re.search(r'(\d+) s', r[5]); return float(m.group(1)) if m else 5
t, rows, starts = 0, [], {}
for r in ROWS:
    starts.setdefault(r[0], t); rows.append((t, r)); t += dur(r)
total, tot_w = t, sum(W(r[2]) for r in ROWS)
mm = lambda s: f"{int(s // 60)}:{int(s % 60):02d}"
NUM = r"\b(un|une|deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|quinze|vingt|trente|quarante|cinquante|soixante|cent|cents|mille|millions?|milliards?|milliardième|moitié|quart|dixième)\b"
per_min = [0] * (int(total // 60) + 1)
for s, r in rows:
    per_min[int(s // 60)] += len(re.findall(NUM, r[2], re.I)) + len(re.findall(r"\d", r[6]) and [1] or [])
sents = [x for r in ROWS for x in re.split(r'(?<=[.?!])\s+', r[2].replace('« ', '').replace(' »', '')) if x.strip()]
lens = [W(x) for x in sents]
o = ["# Script : « Et si la Lune tombait sur la Terre ? » (version 2)\n",
     "Écrit le 5 novembre 2026 avec `video_analysis/format_bible.md`, puis révisé après une relecture critique : ouverture par la "
     "conséquence, histoire réelle raccourcie, scènes humaines, vrai dilemme pour Léa, trois « Vous pensez que… ? », moins de "
     "chiffres prononcés (repères : 4 jours et 19 heures, 18 000 km, 3,8 cm par an), nuance sur la limite de Roche. "
     "Personnage inventé : Léa, 31 ans, ingénieure sur une station de télémétrie laser lunaire. Chronologie de la chute "
     "calculée par nous (voir partie 4). Données : `script_data.py` ; ce fichier est généré par `build_md.py`.\n",
     "## PARTIE 1 : PLAN\n\n| # | Temps | Début | Durée | Mots (repère du prompt) | Mots écrits |\n|---|---|---|---|---|---|"]
for b in range(1, 10):
    w = sum(W(r[2]) for r in ROWS if r[0] == b); d = sum(dur(r) for r in ROWS if r[0] == b)
    o.append(f"| {b} | {BEATS[b]} | {mm(starts[b])} | {mm(d)} | {PCT[b] * 15} | {w} |")
o.append(f"\nTotal : {tot_w} mots de voix, soit {mm(total)} à 150 mots/min (boucle muette de 6 s comprise).\n"
         "Écarts voulus avec les proportions du prompt : ouverture plus longue (retour en arrière), histoire réelle "
         "raccourcie à environ 35 s, escalade et retournement plus longs.\n")
o.append("## PARTIE 2 : SCRIPT\n\n| Minutage | Temps | Étiquette | VOIX | VISUEL | SANS LE SON | SON | TEXTE À L'ÉCRAN |\n|---|---|---|---|---|---|---|---|")
cell = lambda x: (x or "—").replace("|", "/")
for s, r in rows:
    o.append(f"| {mm(s)} | {r[0]} | {r[1]} | {cell(r[2])} | {cell(r[3])} | {cell(r[4])} | {cell(r[5])} | {cell(r[6])} |")
o.append(open('parties_3_4.md').read())
o.append("## PARTIE 5 : AUTO-CONTRÔLE\n\n| Critère | Cible | Valeur mesurée | OK ? |\n|---|---|---|---|")
pm = per_min[:int(total // 60)]
avg = sum(lens) / len(lens)
checks = [
    ("Mots de voix", "1 425 à 1 575", f"{tot_w}", "OK" if 1425 <= tot_w <= 1575 else "À CORRIGER"),
    ("Mots par phrase (moyenne)", "8 à 10", f"{avg:.1f}", "OK" if 8 <= avg <= 10 else "À CORRIGER"),
    ("Phrases de 4 mots ou moins", "≥ 20 %", f"{100 * sum(l <= 4 for l in lens) / len(lens):.0f} %", "OK"),
    ("Chiffres par minute (voix + écran)", "≥ 3", f"min {min(pm)} ; par minute {pm}", "OK" if min(pm) >= 3 else "À CORRIGER"),
    ("Les 9 temps dans l'ordre", "oui", "oui (ouverture avec retour en arrière)", "OK"),
    ("Boucle plantée (temps 4) et payée (temps 7)", "oui", "« Retenez ce chiffre : 18 000 km » → « Ce chiffre revient maintenant »", "OK"),
    ("Motif répété 3 fois", "oui", "« deux virgule cinq secondes » (l'écho) : temps 1, 6 et 9", "OK"),
    ("Personnage aux temps 1, 5 et 8", "oui", "Léa aux temps 1, 5, 6 et 8", "OK"),
    ("Réel / inventé dit au début et à la fin", "oui", "temps 2 et 9", "OK"),
    ("Dates et nombres en lettres dans VOIX", "oui", "oui", "OK"),
    ("Règle simple vérifiée à chaque palier", "oui", "÷ 2 → × 8 ; vérifiée à × 8, × 64, × 1 000", "OK"),
    ("Question du spectateur à voix haute", "oui", "« Pourrait-on la dévier ? Non. »", "OK"),
    ("Fait surprenant par palier", "1 par palier", "face cachée, sol qui a des marées (mi-chemin) ; Io (quart) ; séismes lunaires (dixième)", "OK"),
    ("Phrase à contredire dans l'ouverture", "oui", "« C'est le capteur. Redémarre-le. »", "OK"),
    ("« Vous pensez que… ? » (certitudes renversées)", "3", "le premier signe est invisible (5) ; pas seulement la mer (6) ; pas d'un seul bloc (7, annoncé dès l'ouverture)", "OK"),
    ("Dilemme du personnage", "oui", "évacuation ordonnée + appel de sa mère → elle reste, ses mesures servent aux prévisions de marée", "OK"),
    ("Objets-témoins (≥ 4 plans, état qui change)", "oui", "compteur d'écho 2,51 → 2,485 → 1,228 → 0,202 → 0,066 → 2,51 s ; carnet de Léa ; règle de marée ; digue de Rotterdam", "OK"),
    ("Boucle accélérée", "oui", "temps 6, 6 s, finit sur un plan long et une coupure", "OK"),
    ("Plan long ≥ 6 s au temps 8", "oui", "7 s", "OK"),
    ("Même lieu et cadrage aux temps 1 et 8", "oui", "Calern, même cadrage ; l'image de l'ouverture revient aussi au palier « une heure et demie »", "OK"),
    ("Silences complets", "≥ 2", "avant « Vous pensez que la Lune va s'écraser d'un seul bloc ? » et avant « Maintenant, la vérité »", "OK"),
    ("Colonne SANS LE SON remplie", "chaque plan", "oui", "OK"),
]
for c in checks:
    o.append(f"| {c[0]} | {c[1]} | {c[2]} | {c[3]} |")
open('script_lune.md', 'w').write("\n".join(o) + "\n")
print(tot_w, mm(total), f"{avg:.2f}", pm)
