"""s17_addendum.py: appends the P2 result (s16_p2.py -> s16.out, s16_p2.json) to REPORT.md as a dated addendum."""
import os

OUT = os.path.join(os.path.expanduser("~"), "xs-campaigns/2026-11-07-sprint/q89/REPORT.md")
TEXT = r'''

---------------------------------------------------------------------------------------------------------

## Addendum 2026-11-07 (later the same day): prediction P2 tested -- **falsified**

Script `s16_p2.py` -> `s16.out`, `s16_p2.json`. One process, nice 10, about 4 minutes. Move model: pes_lib exact
remove1 (R1) and the expand envelope at search cap 4, as in the barrier report and study A.

**Test objects [measured].** Every 90-gate depth-4 state on disk whose first layer is exactly the 89's 26-pair set
(any byte rotation; rotated into L0's frame): 12 distinct states. None is a run record (0 of the 5,798 recorded
90@4 states have the set, as in 1.3); all 12 come from pinned completions: the four (26,22,30,12)/(26,23,30,11)
traps `a-pin-s1/s3/s6/s7` and `path14-s1` (`2026-11-02-why/foundations/out/`), five validation runs of the
foundation searches (`2026-11-03-12h/foundation/run/runs/e00000-r0,r1` twice each as distinct states,
`2026-11-04-12h/foundation2/run/runs/e00000-r2`; these pin the one-byte-rotated set, shift 24 back), and two repair
runs (`2026-11-03-waits/repair/run/runs/ctl89-r0`, `x_rc_b0_010313-r2`).

**Result [measured].**

| test | count (of 12) |
|---|---:|
| in B1 (one envelope step up from an L0 member; B1 regenerated here: 16,173 states, same as the barrier count) | **0** |
| hash in the barrier's D1 file (`band_mc89d4full_w0.json`; only its 16,173 band-level nodes carry a hash, the deeper D1 nodes do not, so this is the B1 test again) | 0 |
| direct remove1 step down into L0 | **0** |
| any remove1 step down at all | 0 (11 states have 14-16 neutral moves, 1 has 4) |
| bounded BFS over non-increasing R1 moves (bound 5,000, the study-A bound at which k <= 4 climbs return 98-100%) reaching L0 or any <= 89 | **0**: 11 cut at 5,000 states, 1 exhausted a 9-state region with no exit ("stuck") |

So no 90@4 over the 89's exact first layer that the completions produced is in the +1 band of L0, and none
descends to L0 by remove1 within the study-A budget; one is proved not in D1 (its whole non-increasing R1 region is
9 states at 90 with no way down, while every D1 state has an R1 path down). Full D1 membership of the other 11 was
not decided by hash (file limitation) but is excluded in practice by the 5,000-state descents.

**What distinguishes them [measured].** All 12 share the 26 pairs and 46-49 of L0's 53 core values. Eleven of them
are one construction: they lack the core values x15+x16+x23, x1+x8+x15+x16+x23, x9+x15+x23+x25,
x8+x9+x15+x24+x25+x31 (and mostly x0+x7+x17+x24+x31) and instead carry x1+x8+x16, x0+x7+x8+x23, x15+x17+x23+x25,
x9+x15+x17+x23+x25 plus one or two weight-5/6 values; i.e. a different level-2/3 realisation of the outputs that use
x0, x1, x7-x9, x15-x17, x23-x25, x31 (the y1/y9/y17/y25 and y7/y15/y23/y31 region) that costs one gate more. The
twelfth (second `e00000-r0` state) replaces a different core region (x2/x3/x7/x11/x12/x18-x20/x23/x26-x28) and sits
in a tiny 9-state 90-plateau. L0's basin is therefore **not** "first layer = the 89's set": the same first layer
supports at least two other 90-level families that the capped moves do not connect to L0. The entry criterion for
L0 is finer than level 1 (it needs most of the 53-core, in particular the x15+x16+x23 construction), which is
consistent with the completions reaching 89 in only 6 of 10 pinned runs and with the v9c arrival (3.1) having
needed 840 s of walking after the restart onto a first-layer-equal 90.

**Consequences for the report.** 3.1's phrase "the basin of L0 is, to the precision of the data, the set of states
carrying L0's first layer (plus D1)" is too strong: the first layer is necessary in all data but not sufficient;
over the right first layer the completions still split 6:4 between L0 and 90-level traps that are not in L0's
band. E2 stands (first layers are immobile at 89-90); E1 is unchanged (open). Predictions 3 and 4 stand as
written; prediction 2 is answered.
'''
with open(OUT, "a", newline="\n") as fh:
    fh.write(TEXT)
print("appended", len(TEXT.splitlines()), "lines to", OUT)
