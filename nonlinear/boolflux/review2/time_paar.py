"""Wall time of the unseeded Paar rebuild, old (9f4c8df) vs new, on NIST AES skeletons.
    taskset -c 18 python3 time_paar.py"""
import glob, time
from common import REPO, core, skeleton
from test_synth import OLD
ops = core.Model.load("nist").ops()
fs = sorted(glob.glob(str(REPO / "nonlinear/nist/aes-sbox/*.circ.txt")))[::3]
to = tn = 0.0
for f in fs:
    sk = skeleton.extract(core.read_ncff(f))
    for up, po in ((True, False), (True, True)):
        t = time.perf_counter(); a = OLD["synthesize"](sk, ops, use_paar=up, paar_outputs=po); to += time.perf_counter() - t
        t = time.perf_counter(); b = skeleton.synthesize(sk, ops, use_paar=up, paar_outputs=po); tn += time.perf_counter() - t
        assert a.gates == b.gates and a.outputs == b.outputs
print(len(fs), "circuits; old %.2f s, new %.2f s, ratio %.2f" % (to, tn, to / tn))
