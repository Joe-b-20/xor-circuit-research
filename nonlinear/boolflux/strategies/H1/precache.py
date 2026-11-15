"""Precompute nbhd.py reductions (NQ, NA normal forms) of all 1275 members for given gammas and
store them in ~/xs-campaigns/2026-11-15-study/H1/nbhd/cache_<gamma>.pkl (agent H1)."""
import pickle, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import nbhd
D = Path("/home/joebachir20/xs-campaigns/2026-11-15-study/H1/nbhd")
for g in sys.argv[1:]:
    t = time.time()
    c = {m: nbhd.red(m, g) for m in nbhd.ALL}
    pickle.dump(c, open(D / ("cache_%s.pkl" % g), "wb"))
    print(g, len(c), round(time.time() - t, 1), "s", flush=True)
