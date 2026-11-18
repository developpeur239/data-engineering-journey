"""Bruitages ElevenLabs du bloc 1 (une seule génération, cache dans film/b01/sfx_real/)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "panne_internet"))
import sfx_real  # noqa: E402

sfx_real.LIBRARY.update({
    "reveil": ("Close intimate sound: a person waking up suddenly in bed at night, a sharp surprised inhale then slow "
               "breathing, cotton duvet and sheets rustling as they sit up, quiet bedroom, no voice, no music", 4.0, 0.6),
    "parquet": ("Three slow bare footsteps on an old creaking wooden parquet floor in a quiet bedroom at night, "
                "one floorboard creaks, no music", 3.0, 0.6),
    "amb_ville_nuit": ("Small French town at night, very quiet street, faint distant dog barking once, soft wind, "
                       "an eerie stillness, no traffic, no music, seamless ambience", 10.0, 0.45),
})
print(sfx_real.generate(HERE / "b01", ["reveil", "parquet", "amb_ville_nuit"]))
