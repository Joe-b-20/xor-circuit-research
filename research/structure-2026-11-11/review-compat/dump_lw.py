"""CHECK helper: run compose/compat/lowwaste.py for block K and dump its gate list (JSON) for independent checking."""
import json, os, runpy, sys
K = sys.argv[1]
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "compose", "compat")
sys.path.insert(0, D)
sys.argv = ["lowwaste.py", K]
ns = runpy.run_path(os.path.join(D, "lowwaste.py"))
json.dump(ns["gates"], open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "lw%s.json" % K), "w"))
