"""k of the mobile-part window per picked circuit, under wiring closure vs any-pair closure."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_scopes, sat87
info = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "circuits.json")))
for c in info:
    order = run_scopes.load(c["id"])
    run_scopes.ANYPAIR = False
    k1 = len(run_scopes.window(order, c["mobile"]))
    run_scopes.ANYPAIR = True
    W = run_scopes.window(order, c["mobile"])
    k2 = len(W)
    nt = sum(1 for t in sat87.TARGETS if t in W)
    print(c["id"], "mobile", len(c["mobile"]), "k wiring-closure", k1, "k any-pair", k2, "targets in W", nt)
