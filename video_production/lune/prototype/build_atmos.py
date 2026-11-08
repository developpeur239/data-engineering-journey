"""Assemble atmos.html : atmos_src.html + les interfaces d'écran (drawLLR, drawOrbit) prises dans refs.html."""
from pathlib import Path

here = Path(__file__).parent
refs, src = (here / "refs.html").read_text(), (here / "atmos_src.html").read_text()
grab = lambda n: refs[refs.index(f"function {n}("): refs.index("\n}\n", refs.index(f"function {n}(")) + 3]  # noqa: E731
(here / "atmos.html").write_text(src.replace("/*SCREENS*/", grab("drawLLR") + grab("drawOrbit")))
print("atmos.html")
