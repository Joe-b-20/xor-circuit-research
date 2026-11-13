"""Paar rebuild time old vs new on ANF-start skeletons (large).  taskset -c 18 python3 time_paar2.py"""
import time
from common import core, skeleton, starts, targets
from test_synth import OLD
for tgt, model in (("aes", "nist"), ("present", "bgc"), ("gf16-mul", "xag")):
    ops = core.Model.load(model).ops(); n, m, table, _ = targets.load(tgt)
    sk = skeleton.extract(starts.anf(n, m, table, ops))
    for up, po in ((True, False), (True, True)):
        t = time.perf_counter(); a = OLD["synthesize"](sk, ops, use_paar=up, paar_outputs=po); to = time.perf_counter() - t
        t = time.perf_counter(); b = skeleton.synthesize(sk, ops, use_paar=up, paar_outputs=po); tn = time.perf_counter() - t
        print(tgt, "K", len(sk["ands"]), up, po, "identical", a.gates == b.gates and a.outputs == b.outputs, "old %.2f s new %.2f s x%.1f" % (to, tn, to / tn))
