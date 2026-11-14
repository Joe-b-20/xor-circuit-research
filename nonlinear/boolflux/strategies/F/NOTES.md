# Track F: the low gate-depth frontier (GD <= 14, 13, 12)

Work of 2026-11-14 (push ending 16:00 UTC). Campaign outputs in
`~/xs-campaigns/2026-11-13-aes/F/` (found circuits in `found/` with JSON sidecars and aes_check
output; live status in `STATUS.md`). Kernel used: a private snapshot of `kernel/bfx.c`
(sha256 7c53f2e4...) built in `~/xs-campaigns/2026-11-13-aes/F/snap/boolflux/kernel/bfx`.

## 1. Depth analysis (facts, measured)

Tools: `depth.py` (levels, required levels for a cap, regions, per-output critical path),
`skeldepth.py` (AND-skeleton depth bound), `kraft.py` (which forms cannot meet a cap).

Regions: L0 = linear gates with no AND in their fan-in (top), Ak = ANDs of AND level k,
Lk = linear gates after AND level k.

| circuit | critical path (all 8 outputs) | skeleton bound |
|---|---|---|
| NIST 116@GD15 A33 | top 2, A1, mid 3, A2, L2 1, A3, L3 2, A4, bottom 3 | 15 |
| NIST 127@GD14 A33 | top 2, A1, mid 2, A2, L2 1, A3, L3 2, A4, bottom 3 | 14 |
| ours 124@GD14 A38 | top 3, A1, mid 2, A2, A3 (no L2), L3 2, A4, bottom 3 | 14 |
| ours 131@GD13 A36 | top 2, A1, mid 2, A2, A3, L3 3, A4, bottom 2 | 13 |
| NIST 133@GD13 A35 | top 2, A1, mid 2, A2, L2, A3, L3 2, A4, bottom 2 | 13 |
| NIST 141@GD12 A45 | top 2, A1, mid 2, A2, L2, L3 2, A4, bottom 2 | 12 |

- Skeleton bound = the depth reached if every linear form (AND operand, output) over the basis
  (inputs, AND outputs) is built as its own depth-optimal XOR tree from its terms' arrival levels
  (Huffman). It is a lower bound on GD for any circuit with the same AND functions. For every
  frontier circuit it equals the circuit's GD, so **a cap repair cannot be done by XOR-layer
  resynthesis**: some AND functions must change.
- 116's 8 outputs at cap 14 have Kraft sums 1.125-1.75 over their 18-product terms (6 products
  at level 12, 12 at level 11): even with all products at level 11, S5 (11 terms) cannot meet 14.
- The GF(2^4) inversion interface (4 inputs, 9 outputs y0..y3, y0^y2, y1^y3 and the three pair
  sums) is the same set of functions in 116, 127, 131, 133 and 141. 127 is literally 116 from
  the inversion inputs on, one level earlier (its front costs 12 more top-layer gates).
  122 (below) keeps 116's front and bottom and uses a depth-3 inversion (4 + 6 ANDs instead of
  2 + 4).

## 2. What failed (measured)

- AND distribution (AND(a^b, c) = AND(a,c) ^ AND(b,c), and both operands split, reusing
  existing products; `skelxf.py`, `skelbeam.py`): no single transform lowers any output of 116's
  skeleton below 15; a beam search of up to 8 transforms (+8 ANDs) lowers the Kraft excess
  2.35 -> 1.26 but not the bound. Distribution preserves Kraft sums unless terms cancel.
- Union-graph mapping (`union.py`: all 141 verified pool circuits' gates as hyperedges over
  exact functions, depth-constrained area-flow mapping): only reproduces GD10-ish covers of
  169-176 gates; area flow cannot see the sharing of whole cones.
- Direct splices (`splice.py`, `try_splice.py`: base circuit, signals replaced by equal-function
  donor signals by region): 116 front + 133 back = 130 gates at GD15 (133's back uses its own
  early mid-layer signals); 133 + 116's inversion outputs = 127@GD14. No gain.

## 3. Gains

### 3.1 122@GD14 A37 by the gate kernel from 124 (baseline mechanism)
`found/e1-gate-from124-g122-a37-gd14-ad4.circ.txt`. Old kernel snapshot (bfx.c sha256 7c53f2e4),
hard caps GD14 AD4, 300k iterations, seeds 1-4 (`e1_relaxed.sh`): all 4 seeds reached 122 at
25.5 / 32.6 / 70.7 / 123.4 s. The 124 came from a 120 s run that had not converged.
Same experiment from other feasible starts (E1, 300k x 4 seeds each): 127@14 -> 126,
131@13 -> 128@14, 133@13 -> 126@14; cap 13: 131 -> 131, 141@12 -> 137; cap 12: 141 -> 141,
148@11 -> 143.

### 3.2 Depth-3 GF(2^4) inversion block (design)
`invspec.py` extracts the inversion interface; `invsyn.py` / `invbatch.py` synthesise it;
`invsplice.py` replaces the block in a base circuit (input order found by permutation search).
- Targets (16-bit tables over the 4 inversion inputs): y0..y3, y0^y2, y1^y3 at depth <= 3 and
  the pair sums y0^y1, y2^y3, y0^..^y3 at depth <= 4.
- Fact (exhaustive, `invfeas.py`): from the 4 inputs alone, y2 and y3 (and others) are **not**
  depth-3 computable over {AND, XOR, XNOR, NOT}. One extra level-0 linear input x2^x3 makes all
  six reachable; most pairs of extras do too.
- Extras the 116 front can deliver at level 6 (`extradepth.py`, Huffman over the skeleton
  forms): every XOR of inversion inputs except x1^x2, x0^x1^x2, x0^x1^x3, x1^x2^x3.
- Annealed designs (cost = gates excluding extras): extras {x0^x2, x1^x3} (= 116's t38, t37):
  **22 gates (10 AND) + 3 pair-sum XORs**, reached by every seed (1-4, 200k-300k iterations);
  {x2^x3}: 27 + 3; {x1^x3, x2^x3}: 24 + 3; {x0^x1, x2^x3}: 27 + 3.
  116's own depth-4 block: 21 gates including t37, t38.
- Splice into 116 with each extra built as one XOR of two existing level-<=5 signals
  (x0^x2 = t25 ^ t31-style cancellation found by table lookup): **122 gates, GD14, A37, AD4**,
  constructive, no search (`found/invsplice-116-g122-a37-gd14-ad4.circ.txt`, aes_check OK).
  Ties the kernel result; 116 - 21 + 22 + 3 + 2 = 122.
- Same block spliced into 127 / 133 / 131 / 140 / 142: 133-143 at GD14 (no gain: those already
  have a fast front, the block is +6 over their inversions).

### 3.3 Bottom layers differ in speed
141@GD12's bottom is 4 levels from the inversion outputs (28 ANDs + 25 linear gates = 53),
116's is 5 levels (18 + 32 = 50). Splicing 116's (depth-4, 21-gate) inversion into 141 gives
**138@GD13 A43** (`inv/sp-141b-116y.circ.txt`), a new GD13 structure (best GD13 is our 131).
Kernel runs from it at caps 13 and 14 are in `inv/h141c13`, `inv/h141c14` (137@13 after 22 min,
134@14 after 15 min: not competitive).
Reverse transplant (`botsplice.py`: 116 front + inversion, donor bottom): 141's bottom gives
143@GD14 (A43): the donor's products need ~24 gates of top-layer forms 116 does not have;
148@11's bottom gives 150@GD13. Kernel runs in `bot/bs141c14`, `bot/bs148c13`.

### 3.4 Which inversion outputs must be early (`fastset.py`, `invlate.py`)
With 116's bottom unchanged, cap 14 needs 7 of the 9 inversion outputs one level earlier; every
minimal set contains y0^y1^y2^y3 (or both y0^y2, y1^y3). Relaxed specs (only y0..y3 at depth
3, rest as late XORs; `invlate.py`, helper targets via `--force3`): 15-gate cores but
y0^y1^y2^y3 then cannot be at depth 4 with <= 2 extra gates; the complete designs cost 28-29
with extras vs 27 for the full spec. So 122 is the floor of this route.

## 4. Search A/B on 122@GD14 (equal CPU, same start)

`fdrive.py` modes, 1 job = 1 CPU-hour, start = the e1 122, cap GD14 AD4, kernel stages of
200k iterations restarted from the job's best (`campaign.py`, `plan_ab.py`; data `ab/`,
summary `abstat.py ab`).

| arm | round 1 best | notes |
|---|---|---|
| gate-old (kernel 7c53f2e4) | 122 | |
| gate-new (kernel 0659eb9, lex cost,gd) | 122 | |
| osc (cap 15 then repair to 14, then cap 14) | 122 | repairs feasible 17/23; relaxed stage reaches 118@15 |
| trb (timing-driven regional rebuild + kernel) | 122 | 44 kicks, mean +3.5 gates |
| mix (gate/osc/trb rotating) | 122 | repairs 8/12, 10 kicks |

No arm improves on 122 in one CPU-hour: success rate 0/5, time-to-result undefined. Kernel
from the second (splice) 122: 0/2 jobs of 1 h. Rounds 2-3 (4 arms, mix dropped) run 15:34-17:34.

### Final A/B numbers (stopped 17:28 UTC; round 3 at 54 of 60 min)

| arm | CPU-hours | runs improving on 122 | result | other |
|---|---|---|---|---|
| gate-old (kernel 7c53f2e4) | 2.9 | 0/3 | 122 | |
| gate-new (kernel 0659eb9, lex cost,gd) | 2.9 | 0/3 | 122 | no old/new difference visible |
| osc (cap 15 then repair, then cap 14) | 2.9 | 0/3 | 122 | repairs back to GD14 feasible 50/65 |
| trb (timing-driven regional rebuild + kernel) | 2.9 | **1/3** | **121** at 1407 s (round 2, bottom-region rebuild) | 124 kicks, mean +3.5 gates |
| mix | 1.0 | 0/1 | 122 | |

`found/ab-r2-trb-g121-a37-gd14-ad4.circ.txt`: aes_check OK on pin 3d80774, new Pareto point,
+4 below the published best at GD<=14 (now 125, A33). Track D found a different 121 the same
afternoon. n = 3 per arm: trb's 1/3 vs 0/9 for the others is suggestive, not significant.

### Final repair baseline (rebuild-only workflow, 300 s runs, repo kernel 0659eb9)
GD14 -> 13: **2/35** runs met the cap (137 and 136 gates, both from D's 125@GD14 A33; 0/8 and
0/7 from the two 122s, 0/4 each from D's 121, E's 123 and 126). GD13 -> 12: **0/10** (131, E's 130).
No repair produced a GD13 below 129/131 or a GD12 below 141.

### Timing conditions (oversubscription)
One busy process per CPU from 16:20 UTC on. Before that, CPU 6 ran 2-5 processes at once, so
these timings are slowed (wall time, roughly 2-5x): inversion batches b1/b3/t2/t3/late, spg1/2,
sprep1/2 (the "~250 s" repair of the splice), h141c13/14, bs141c14/bs148c13, and rep6 runs s1
(15:5x-16:20). Unaffected (one process per CPU): e1 (CPUs 1-4, 04:4x), A/B rounds 1-3 (CPUs 1-4 /
1-5), rep5 (CPU 5), pool3, and pool6 / rep6 after 16:20.

## 5. Cap-repair baseline (rebuild-only workflow, `repair.sh`, repo HEAD 0659eb9)

300 s runs, GD14 -> 13 from both 122s and GD13 -> 12 from 131, seeds 1-12 (`rep/rep5.log`).
First runs: 122 (e1) -> best 131@GD14 infeasible; 122 (splice) -> 129@GD14 infeasible.
Contrast: the GD15 splice of the depth-3 inversion (extras at level 7, skeleton bound 14)
was repaired to 122@GD14 by the plain kernel in ~250 s in 2/2 seeds (`inv/sprep*`), while
116@GD15 (skeleton bound 15) repairs in 1/35 runs of 120 s: **repair is fast exactly when the
start's skeleton bound already meets the cap**.

## 6. AND depth 3 (phase from 17:28 UTC, CPUs 1-3)

- Structure of the published AD3 circuits (`ad3study.py`, NIST 172@GD14 A35 = 11 + 12 + 12 ANDs):
  A1 products (degree 2) span the GF(2^4) norm N (all 4 bits in span{1, x, A1}); A2 products have
  degree 4; every A3 product is AND(Q, R) with Q in the N-quadratic span and R in
  span{N-linear x x-linear} (degree 3); the outputs (degree 7) are sums of the 12 A3 products. The
  inversion outputs y never exist as signals: y_j(N) t(x) is regrouped as sum Q(N) (l(N) t(x)).
- Polishing under AD<=3 with fdrive trb (timing-driven XOR-region rebuild + kernel):
  180 -> **174@GD13 A40** and 163 -> **161@GD14 A38** within ~2 min each (aes_check OK, new
  Pareto points; published 183@13 and 172@14 at A35); A<=35 line 163 -> 162@GD14 so far.
- `linres.py` (XORFlux per linear layer, exact constants via XOR/XNOR polarity choice): on NIST
  139@GD27 AD3 each layer returns at its current size (41, 20, 28, 15 gates): the layers are
  region-optimal already; gains come from cross-region moves (trb + kernel).
