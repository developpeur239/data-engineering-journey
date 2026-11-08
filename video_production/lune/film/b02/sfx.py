"""Bloc 2 : ambiance extérieure (ElevenLabs, une seule génération, cache b02/sfx_real/)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "panne_internet"))
import sfx_real  # noqa: E402

sfx_real.LIBRARY["amb_plateau_nuit"] = ("High limestone plateau in Provence at night, very quiet: soft crickets, a gentle breeze in "
                                        "low bushes, a calm open-air stillness, no traffic, no animals barking, no music, seamless ambience", 10.0, 0.45)
print(sfx_real.generate(HERE, ["amb_plateau_nuit"]))
