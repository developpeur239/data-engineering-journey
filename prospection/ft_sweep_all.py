"""Balayage France Travail des métiers commerciaux pour chaque département demandé."""
import json, sys, concurrent.futures as cf
import signals_lib as S
deps = sys.argv[1].split(",")
with cf.ThreadPoolExecutor(3) as ex:
    for d, offers in zip(deps, ex.map(S.ft_sweep, deps)):
        json.dump(offers, open(f"ft_sweep_{d}.json", "w"), ensure_ascii=False)
        print(d, len(offers), flush=True)
