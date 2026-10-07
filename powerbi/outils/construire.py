"""Reconstruit tout le projet Power BI à partir de palette.json, puis lance les validations.

    python3 construire.py            # génère + valide
    python3 construire.py --apercus  # + rend les PNG (vl-convert-python et Pillow requis)
"""
import subprocess
import sys

ETAPES = [["verifier_palette.py"], ["generer_theme.py"], ["generer_specs.py"], ["generer_modele.py"], ["generer_rapport.py"],
          ["generer_design.py"], ["generer_reparation.py"], ["valider_specs.py"], ["valider_pbir.py"], ["verifier_coherence.py"]]
if "--apercus" in sys.argv:
    ETAPES.insert(6, ["rendre_apercus.py"])
for e in ETAPES:
    print("==>", " ".join(e))
    r = subprocess.run([sys.executable, *e], cwd=__file__.rsplit("/", 1)[0] or ".")
    if r.returncode:
        sys.exit(f"échec : {' '.join(e)}")
print("Tout est généré et validé.")
