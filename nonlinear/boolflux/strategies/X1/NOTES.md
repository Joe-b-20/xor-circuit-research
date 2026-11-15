# X1: AND merge / split move (2026-11-15)

Evidence labels: [C] proved / exact within the stated case, [H] heuristic or empirical,
[V] verified circuit (all 256 inputs, two verifiers via `campaigns/aes_check.py` or `hub.common.verify`).
Code: this directory + `hub/ops/x1_merge.py`.  Data: `~/xs-campaigns/2026-11-15-study/X1/`.
Clock: all times UTC as shown by `date -u` in WSL.

## 1. Representation: the product program

Atoms: 1, the 8 inputs, one atom per AND output.  Every linear signal of a circuit is an affine
form over the atoms (bitmask).  A circuit is `ands[k] = (L_k, R_k)` (forms over other atoms) and 8
output forms; the XOR network is forgotten and rebuilt on demand (`x1lib.py`: `extract`,
`materialise` = Paar pair sharing + depth-greedy chains; or kept and patched locally, `x1patch.py`).
(H3's "skeleton" is the same object; H3 studies exact window re-solves, X1 the moves below.)

Exact identities (GF(2), functions on the 256 inputs):

- **dep** [C]: if the tables of {1, x, products} are linearly dependent, the last product (dependency
  order) of a dependency is an XOR of the other atoms: -1 AND.  Define
  `A_eff = dim span{1, x, products} - 9`; any circuit can be rewritten with A_eff ANDs.
- **flip** [C]: p_i = a*b_i + l_i, p_j = a*b_j + l_j (a = shared operand direction modulo constants,
  found in span{L, R, L+R}; l affine in the operands - this absorbs the "shift" identities
  a*b = a*(a+b) + a).  New product q = a*(b_i+b_j); p_i = q + p_j + l_i + l_j.  Substituting this in
  every form that reads p_i keeps the AND count.  Needs: p_j does not depend on p_i.
- **merge** [C]: a flip between two ANDs read by exactly the same forms leaves p_j unread: -1 AND
  (this is AND(a,b) xor AND(a,c) = AND(a, b xor c) in general position).
- **split** [C]: p_i = a*(b+c) + a*c for any form c not depending on p_i: +1 AND.
- **redec** [C]: two ANDs read by the same forms, no shared factor: ab + cd = (a+c)*b + c*(b+d).
- Invariant [C]: flips do not change span{1, x, products}; a split adds one dimension.
  **CORRECTION (X1b, 03:20 UTC, after X3b NOTES 10.1):** the original line said "flips and redec do not
  change span{1, x, products}". That is false for redec. ab + cd = (a+c)b + c(b+d) replaces span{ab, cd}
  by span{ab + cb, cb + cd}. The sum ab + cd stays in the span, but one dimension (ab, or cd) is swapped
  for one that contains cb, which is in general outside the old span. Same count, one dimension changed.
  This is where most of X1's ">150 new spans" come from: 27 of 28 product dimensions are shared with the
  start (X3b: re-decompositions of g124's sink pair {g17, g26}). The span hash is therefore a weak
  novelty test. X1b filters by H1/X3b's U subspace instead (x1b_ufilter.py, section 8).
  So with flips alone, dependencies can never appear if there were none, every reduction is a merge,
  and only circuits whose products are sums of the original products (+ affine) are reachable.
  Splits are what leaves the span ("split-then-merge").

## 2. Static reductions on existing circuits (`x1patch.py`, `t_survey.py`, `t_patch.py`)

Local patches that keep the rest of the XOR network: dep (AND gate -> XOR tree over existing signals,
greedy cover of the dependency by existing linear signals, shallowest first) and merge (one new AND on
operands built from the four old operand signals).  Chains are followed (`x1_merge.reduce_chain`).

Survey of the hub archive snapshot (01:36 UTC, 2311 records, 455 cells):
- cell minima: 72 of 455 have a static reduction (35 dep, 20 merge); whole archive: 298 of 1774
  scanned members.  They are almost all products of `join` (transplants bring redundant ANDs that the
  kernel's 1-3 divisor resubstitution cannot see: the dependencies have many terms).
- None of the published or best A28 circuits has a dependency or a mergeable pair [C: dep and
  equal-usage/shared-factor merge only].  A28-AD5 has one equal-usage pair without a shared factor
  (H3's dependent sink pair {g17, g26}).
- Factor-sharing pairs (flip graph edges): BP32 33, A31 18, A30/A29(hub) 4-5, A28 3-4, umizame A29 0.
- Verified A reductions at A <= 31 (all dominated by existing front points; in `found/`) [V]:
  29/4/176/14 -> 28/4/176/15, 29/4/136/24 -> 28/4/134/24, 29/5/131/20 -> 28/5/130/20,
  29/5/134/20 -> 28/5/132/20, 29/5/127/30 -> 28/5/126/30 (kernel polish: 28/5/124/27 = published),
  30/4/144/17 -> 29/4/143/17, 30/5/137/18 -> 29/5/136/18.
- 59/4/159/10 (three archive copies) has 3 dependent ANDs: 56/4/160/12 after the patch, kernel repair
  reaches 56/4/156/11 in 12 s, not GD 10 so far.

## 3. Hub operator `hub/ops/x1_merge.py`

Common CLI.  Scans archive members not yet in its ledger (`DIR/x1_scanned.json`), newest first (35 % of
the job), follows dep/merge chains, emits reduced circuits that place, and polishes up to 2 hits per job
with the kernel under (A', AD_source, GD_source) (repair mode if the patch raised the depth).  Hits are
ranked by the frontier gain they would have at the source's depths (with 4 gates of optimism).

## 4. Join scan with the rank objective (`joinscan.py`)

Every transplant (hub join, all cuts) between distinct AND skeletons of the archive members with
A <= 30 (122 skeletons), scored by A_eff instead of (A, AD, G, GD).  See results below.

## 5. Flip / split walk (`x1walk.py` Python, `bfw.c` + `x1walkc.py` C, ~100-200k steps/s)

Random walk: merge when possible; else random flip between factor-sharing ANDs; with probability psplit
(while A <= best + plus) a split whose new AND shares a factor with another AND j, followed by a forced
flip with j; redec with probability predec on equal-usage pairs; return to a pool of best-A states after
`horizon` steps.  New bests are materialised and verified.

Calibration [V]: **Boyar-Peralta 32 (NIST a32-ad5-g104) -> 31 -> 30 -> 29 ANDs in 0.2 s** (seed 1,
plus 1, psplit 0.02), circuits 29/5/242/31 etc. verified (G is large: the XOR network is rebuilt
naively; the kernel can polish it).  The Python walk (800 steps/s, splits undone at once by a bug in
the move order) found nothing in 45 s.

Results: see section 6 (updated as runs finish).

## 7. X1b takeover (~03:00 UTC 2026-11-15)

Agent X1b took over from X1 (model usage limit) at about 03:00 UTC, same directories.
State found at 03:00: units x1-camp (camp27, walkcamp from 6 A28, 3 runs done, no 27), x1-joinscan
(joinscan30, 70/122 fronts, best A_eff 28 = nothing below 28), x1-survey2 (389 cells done) and x1-spangen
(spangen1, 11/16 spans) all on CPU 10.  03:01 UTC: stopped x1-camp, x1-joinscan, x1-survey2 (one busy
process per CPU); kept x1-spangen (it is task 2 directly, ~15 min left).
- survey2 (3 s walks, 389 cell minima): 264 cells reduced, but never below 29 (counts by (start A -> reached A):
  32->29 48, 31->29 32, 33->30 32, ...); no A28 start and no A29 start was reduced [H].  The 137 "LOWER"
  lines are A 29-31 at AND depth 7 (dominated by 28/5).
- camp27 (3 slices of 300 s from NIST/best A28): no 27; 27 same-A pool circuits (A28-AD5, G 178-219).
- joinscan30: 3996 joins scored, best A_eff 28 (no join product has a 27-dimensional product span).

## 8. X1b: AND-space registries, U filter, x1b_camp (03:00-06:30 UTC)

Tools (this directory):
- `x1b_family.py [--ref F]... FILES`: span = span{1, x, AND tables} (canonical hash), per-level-prefix spans,
  H3's product-multiset key, shared product dimensions with references.
- `x1b_registry.py` / `x1b_uregistry.py`: registries of known spans / known U subspaces (A <= 29 / A <= 28) over NIST,
  hub best, hub archive, H3 found, X1 outputs.  Data: `X1/x1b/registry.json`, `uregistry.json`, `ureg-table.jsonl`.
- `x1b_ufilter.py`: H1/X3b U subspace (V_N + S1-parts of the outputs), junk ranks, exact 9-cover of U (copied logic of
  `strategies/X3/x3b_junk.py`; the SAT branch of G's cover_sat, 9 - dim U >= 3, is skipped because it stalled
  for minutes on the AD4 files: cover9 = None there).
- `x1b_harvest.py FOUND TAG FILES`: aes_check + .bfx/.circ.txt/.json into found/.
- `x1b_camp.py`: walk (bfw.c, reservoir-sampled dumps of new spans at the best A) -> materialise -> span registry ->
  U filter -> every new U saved (kernel polish for the first --npolish per run, else the rebuilt circuit), each
  aes_check'ed into found/ with names `...-x1b-span-<span>[-raw][-NU][-C9]`; reductions saved as `...-x1b-red-...`.
- bfw.c change (X1b): the dumps are a reservoir sample over the whole run (before: the first 16 new spans, all
  close to the start).  Old source kept as bfw.c.pre-x1b.

Facts:
- [C] All A28 circuits known before tonight (NIST 13, hub best 10, hub archive A28 members, H3 found: 270 files incl. X1's)
  have one of 6 spans (all NIST's: 3 AD4, 3 AD5) and one of 6 U subspaces (3 AD4 with dim U 6, 3 AD5 with dim U 7 or 8);
  the dim-8 U (5c6ab826b44e) occurs only in walk/join products (X1 camp27 pool, 3 archive members).
- [C] H3's 28/5/210/31 = NIST g128 span at every level prefix (new multiset only; X3b: member re-basis of g128).
- [C, X3b] the 11 spangen A28s have g124's U, junk rank 3, c5 = 0, no 9-cover: their span changes are redec /
  value-at-0 / stage-1 re-choices.  The span hash is a weak novelty test; U is the filter.
- **[V, C for the invariants] NEW A28 FAMILY 9+5+14** (03:19 UTC, first x1b_camp run, 90 s walk from NIST
  a28-ad5-g128-gd20, no AD cap, seed 1007973927): `X1/x1b/c29/found/aes-sbox-a28-ad5-g158-gd27-x1b-span-2cabef6153f4`
  (aes_check OK, 28/5/158/27, dominated in G).  Profile 9|1|2|2|14, H1 roles S1 9 / MID 5 / LAST 14; stage 1 = 9 of
  g124's 10 stage-1 products; dim U 7, U cap U_g124 = 6, U new (ae8547e553f6), jc(U) 3, c5(U) 1, **9-cover(U) True**.
  The extra (28th) AND sits in the last layer (NIST AD5: 10+5+13, NIST AD4: 9+6+13).  A 13-member last layer over
  this prefix would give 27; H1 (exact 14 -> 13) and H3 (slack-1 windows) take it from here (coordinator 03:2x).
