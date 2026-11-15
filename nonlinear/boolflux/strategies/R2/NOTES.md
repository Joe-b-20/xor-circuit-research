# R2: affine-slack window redesign (hub operator `aslack`), 2026-11-15

Code: `aslack.py` (window, span algebra, product search, re-synthesis), `op_aslack.py` (hub operator,
common CLI + `--npolish`, `--hunt`), `calib.py` (per-window calibration). `aslack_v1.py` = first
version (used by calib1). Frozen copy used in the A/B: `frozen-ab/` (md5 in data dir).
Data: `~/xs-campaigns/2026-11-15-study/R2/`.

## Method

Representation: all functions are 256-bit truth tables (Python ints); spans are GF(2) row echelon
dicts (leading-bit pivots), one elimination per test.

1. **Window**: S = k ANDs at one AND level L (2-5; "hunt" mode up to 8), seed AND plus ANDs with the
   most shared operand-cone leaves / downstream readers (25%: random). Same level => antichain. D =
   linear gates reachable from S through linear gates only, optionally limited to depth dd (0-3) or
   full. Targets T = signals of S u D read outside S u D, or outputs.
2. **Requirement.** Each target's affine form over D's leaves and S is split into a fixed part (leaves
   that depend on S or have AND level > L; kept as is) and g_t over (1, C, S), where C = slack signals:
   independent of S (not in TFO(S)), AND level <= L ("wide": every such signal; "local": D's leaves +
   S's operand cones), deduplicated by table. V = span(1, C), R = span{g_t mod V}, r = dim R.
   New products q_j = a_j * b_j with a_j, b_j affine over O = slack signals of AND level <= L-1.
   Requirement: R subset of span{q_j mod V}. Hence m >= r, and an A reduction needs r < k.
   AND depth cannot increase (new ANDs at level <= L, targets use signals of level <= their own).
3. **Search.** For a fixed operand a, b -> a*b mod V is GF(2)-linear in b, so one elimination of
   {a*o_i} against W = V + R (R pivots tagged with R coordinates) gives every b in span(O) with
   a*b in V + R, and its R tag. Operand candidates a: all single signals (both polarities), random
   pairs, original operands first; when dim span(O) <= 10 (AND level 1: affine functions of x)
   EVERY non-constant affine a is enumerated (then the search for m = r products is exhaustive for
   that window). Pick: greedy spanning set of tags, cheapest-first with noise (3 picks per window);
   operands re-decoded sparsely over O (shallow signals first).
   Hunt extension (heuristic): when k - r >= 2, add e random "free" products z to R (m = r + e < k),
   so products may leave V + R.
4. **Re-synthesis** of only the window's linear logic: per target, new form = fixed part + q's +
   V-part, the V-part decoded sparsely over C (random elimination orders, half shallow-first; fewest
   terms, then lowest gate level) both directly and as "old V-part + correction", the smaller kept.
   Operand rows + target rows -> shared pair merging (Paar, count >= 2) -> each row combined
   lowest-level-first. Kept gates are re-emitted lazily (topological), dead gates removed (live()).
   Every rebuilt circuit is checked on all 256 inputs inside the operator; the hub verifies again.
5. **Operator** (`--seconds T`): 45% of T on windows (30% chaining: next window from the best raw
   result), then the best `--npolish` (3) raw results (lexicographic objective under the caps, at most
   2 per (A, G)) polished with the gate kernel (hub `ops._kernel`, same settings as op_polish).
   Candidates: raw + polished circuits the archive would place, highest hub gain first.

## Results

### Calibration 1 (aslack_v1, 14 front circuits of the long archive, 392 windows, 00:14 UTC) [H]
`calib1.jsonl` (stopped early at 392 of 750 windows to free CPU 19 before 00:20).
- 366/392 windows spanned (m = r products found), 366/366 rebuilt circuits correct on 256 inputs.
- Time per window: mean 0.34 s, median 0.26 s, max 3.9 s (wide C at level 4-5: 100-120 signals).
- r < k in 26/392 windows (dimP = k always: no product is redundant mod V). (k, r, L): (5,4,1) x12,
  (3,2,1) x5, (4,3,1) x4, (5,3,1) x2, (5,4,4) x2, (4,3,4) x1. None of these had a spanning set of r
  products, i.e. no A reduction.
- r = k in the other windows: then an A reduction inside the window is impossible for ANY products
  (R in span(q) mod V needs m >= r) [C, within the window model of item 2: fixed S, D, targets, C].
- New intermediate nonlinear values: in 231/366 spanned windows at least one new product differs from
  every old product of S (1 new: 149, 2: 62, 3: 18, 4-5: 2).
- Raw G change (before polish): dd 0: mean +1.6, 23/57 equal; dd 1: +2.1, 21/75 equal; dd 2: +3.6,
  2 lower; dd 3: +4.9; full D: +11.3 (re-synthesising large linear layers is worse than the polished
  original). GD rose in 226/366 (v1 decoding ignored levels; v2 decodes shallow-first).

### A-hunt (exhaustive at level 1) [C within the window model, per window]
Tests on 8e7cd56e3482 (32/4/125/15), windows up to k = 8: r < k is easy to reach with larger windows
(e.g. (8,6,1), (7,5,1), (5,4,1)), but for every level-1 window tested (exhaustive over all affine
operands a, all b by elimination) no set of r products spans R: no A reduction with m = r. The free-
product extension (m = r + e < k, random z) found nothing in 16 tries [H].

### Operator tests (30 s, snapshot) [H]
- 1b0f3813aa19-like 28/5/124/27 (test1): 51 correct rebuilds, best raw = input metrics; candidates
  are dominated near-front points (G +2..6, GD +2..4).
- 8e7cd56e3482 32/4/125/15 (test2): 91 distinct raw circuits, best raw ties the input (125/15) with a
  different structure; candidates 125/16, 126/16.
All candidates pass hub.common.verify.

### A/B (hub style, 1 CPU, arms one after the other, same snapshot `snap` (long @ 00:15 UTC), seed 8)
- First base run 00:18-00:24 ABORTED (kept as `abbase-aborted-0018`): CPU 19 was shared with hub jobs
  placed on CPUs 17-19 by mistake (00:19-00:25, coordinator) and with my operator tests.
- base arm `abbase`: restarted 00:24 UTC from a fresh copy of `snap`; polish,pull,join,trb,osc,gen_skel,
  nursery 0.3, ad3_share 0.3; 1 h.
- test arm `abtest`: same + aslack (60 s, frozen copy), launched by `ab_test.sh`, which waits (sleep
  loop, ~0 CPU) until the base unit has ended. The two units are both "active" during the base arm, but
  only the base arm computes: the arms run ONE AFTER THE OTHER at ~1 CPU each (coordinator asked
  00:23; checked: the abtest unit held only bash + sleep, 60 ms CPU). No operator tests of mine on
  CPU 19 while an arm runs.
- (results pending)

## Failures / limits
- A reduction: never found. Necessary condition r < k holds in ~7% of 2-5-AND windows (level 1 mostly).
- Full-D windows re-synthesise whole linear layers and lose 5-20 gates vs the polished original.
