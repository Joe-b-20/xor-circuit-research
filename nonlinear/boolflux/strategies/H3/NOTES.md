# H3: general-model window re-solve (exact, around known circuits)

Evidence labels: [C] exact / exhaustive within the stated case; [H] heuristic or empirical;
[V] verified circuit (campaigns/aes_check.py, all 256 inputs).  Data and logs:
`~/xs-campaigns/2026-11-15-study/H3/` (jsonl per run, one line per window).

## Model and window

General model: ANDs g_1..g_K in order, g_i = a_i & b_i with a_i, b_i affine in the inputs and
g_<i; outputs affine in inputs and all g.  A circuit is reduced to its AND skeleton
(`skeleton.extract`): each AND's two operand forms over (1, x, earlier ANDs).

Window: a set U of ANDs **closed under consumers** (every AND reading a member of U is in U).
Then R = all \ U is a self-contained sub-circuit; we keep R's AND functions and ask for m new
ANDs f_1..f_m (any chain order, operands in span(x, R_op, f_<l), R_op = R unless stated) with
every output in span(1, x, R, f).  Any non-closed "delete W" re-solve with consumers re-solved is
this with U = closure(W).  Notation: W = span(1, x, R), T = span(outputs mod W), r = dim T,
slack = |U| - r.  Constants in operands are irrelevant for the span (a(b+1) = ab + a), and so is
the basis choice of the pair {a, b} (a(a+b) = a + ab).

Basic facts used (all [C], elementary linear algebra):
- RANK BOUND: m new ANDs add at most m dimensions, so m >= r.  Windows with slack <= 0 for
  m = |U| - 1 are impossible.  Single sinks, and sink sets that are independent mod the rest, are
  rigid for this reason (most small sink sets: see analyze1.txt).
- LEMMA 1 (slack 1): if r = m, the m new classes mod W form a basis of T, so every new AND has its
  class mod W inside T.
- LEMMA 2: the products available after choosing new ANDs with classes S (mod W) depend only on S
  when R_op = R (two witnesses of the same class differ by c + v, c constant, v in V); with R_op a
  proper subset, the state is the operand space span(1, V, f) itself (chain.py keys on that).

## Tools (this directory)

| file | what |
|---|---|
| `wsat.py` | skeleton/basis code, CNF encoding of the window problem (coefficient variables for all operands, truth tables over 256 rows, output span via an information set of W), decoder -> NCFF; `finish()` builds and re-solves a circuit from kept + new ANDs |
| `run.py` | SAT driver (CaDiCaL 1.9.5 via pysat, forked child killed at the time limit) |
| `r1enum.c` | exact enumerator: every product a*b (a, b in V) whose class mod W lies in W+X \ W_s; a over a hyperplane of V (each 2-dim span{a,b} meets it), b by linear algebra (kernel of the check rows); random-combination filter, no false negatives |
| `lay.py`, `batch.py` | parallel re-layer: all products with class in Sigma_U, then exact junk/min-cover analysis |
| `chain.py`, `chainbatch.py` | slack-1 windows, chains allowed: BFS over operand spaces (exact) |
| `deep.py` | any-slack windows with new classes restricted to Sigma_U: saturation + BFS |
| `analyze.py` | levels, consumers, closures, rank/slack per closure, minimal dependent sink sets |

## Calibration

- SAT (wsat.py/run.py, CaDiCaL): A28-AD5 (g124) window U = {g17, g26} (a dependent sink pair,
  r = 1) -> m = 1: 5263 vars / 37k clauses, TIMEOUT 600 s.  Same window, m = 2 (positive
  control, the original is a solution): no answer in 320 s.  BP32 (a32-ad5-g104) U = {15, 22, 23}
  (r = 2) m = 2: 12k vars / 83k clauses, TIMEOUT 600 s.  [H] CDCL without XOR reasoning does not
  handle these parity-dense instances; pysat's interrupt is not honoured by CaDiCaL (fixed by a
  forked child).  The SAT route was dropped for the enumeration route below.
- r1enum speed (r1enum_v3, AVX2 elimination; v1/v2/v3 give identical hit lists on a control with
  hits): ~1.1-1.6 us per a on an unshared CPU, so one exhaustive enumeration costs
  ~1.6 us * 2^(nv-1): nv = 22 -> 2-4 s, nv = 27 -> 77 s, nv = 31 -> 29 min, nv = 34 -> ~4.5 h.
  (v4/v5 register-resident Gauss-Jordan variants were slower; kept for the record.)
- Positive controls [V]: lay.py on A29 with U = all 15 sinks, m <= 15: re-finds a 15-product
  layer (file found/h3-ctl-a29-a29-ad5-g241, aes_check OK).  chain.py with m = |U| on sink
  windows {15}, {17}, {20}, {15,17}, {14,16,19} of A29: SAT, circuits verified (ctl2-1 file OK).
  deep2.py with |U| allowed on A29 window sinks + closure(g12) (16 ANDs): SAT with 1 + 15 new
  ANDs, a different A29 at AD 6 (found/h3-d2-a29-ad5-g137-gd32-12-a29-ad6-g262, aes_check OK).

## Results

Every UNSAT below is [C] only for the stated window, operand space and case; it says nothing
about circuits whose kept part R differs.  Files: "A29" = NIST aes-sbox-a29-ad5-g137 (umizame
family), "A28-5" = aes-sbox-a28-ad5-g124 (10|1|2|2|13), "A28-4" = aes-sbox-a28-ad4-g131-gd31
(9|2|4|13), "BP32" = aes-sbox-a32-ad5-g104 (9|1|2|8|12), "A30" = aes-sbox-a30-ad4-g147.
Families (families.py: same AND tables modulo affine functions) - circuits in one family give
identical window problems; 37 families among the NIST and hub A28-A32 files.

### R1. Window structure (analyze1.txt) [C]
Slack (|U| - rank of outputs mod span(rest)) of every consumer closure of one AND: >= 3 for all
A29 and A28-5 closures except A28-5 g14 (closure 9, slack 1); A28-4 >= 2 (g12, g13: 10 ANDs,
slack 2); BP32 g12, g13 closures (9 ANDs) slack 1.  Every single last-level AND has slack <= 0,
so no window "one AND + nothing" can lose an AND.  A set S of last-level ANDs has slack >= 1 iff
it is dependent mod the rest; minimal dependent sets have slack exactly 1 (these are the sink
windows run below; non-minimal slack-1 sets were NOT run).  Minimal dependent sets: A29: 1 of size 3, 4 of size 4, 11, 17, 30, 26, 11 of sizes 5-9;
A28-5: one PAIR {g17, g26}, one triple {16, 22, 24}, then sizes 5-8; A28-4: none below size 4
(6 of size 4, 10 of size 6, 8 of size 8); BP32: 8 triples, 15 of size 4, ...

### R2. Parallel re-layer with classes in Sigma_U (lay.py / batch.py) [C]
Case: new ANDs all with operands in span(x, R) (none reads another), every class mod W inside
Sigma_U; exact min-cover.  Windows: U = all sinks, and U = sinks + closure(g) for every interior
g.  Result: UNSAT (no m <= |U| - 1) for all 93 windows of A29, A28-5, A28-4, BP32, A30 and the
second umizame family a29-ad5-g139.  With U = all sinks, only 18 (A29), 19 (A28-5), 13 (A28-4)
product classes over the prefix land in Sigma at all; no smaller layer exists in this case (the
original size is the minimum).

### R3. Slack-1 windows, chains allowed, operands restricted to the non-last-level ANDs (chain.py,
ops = nosinks) [C]
Case: U = a minimal dependent set of last-level ANDs (or a slack-1 closure), m = |U| - 1 new ANDs
in any chain order with operands in span(x, R_op, earlier new ANDs), R_op = kept ANDs that have
an AND consumer in the original (the prefix; the other last-level ANDs are kept but not used as
operands).  Exact BFS over operand spaces.  All UNSAT:
- A29 (NIST g137): all 100 windows (sizes 3-9), 306 enumerations (chain1.jsonl).
- BP32 (a32-ad5-g104): all 252 windows (8 triples ... size 9, closures cl12, cl13) (chain2.jsonl).
- A28-5 (g124): pair {17, 26}, triple {16, 22, 24}, closure cl14, 8 sets of sizes 5-6 (chain1.jsonl;
  rest not run: they are in the overnight full-operand set).
- A30 (a30-ad4-g147): 18 of 100 windows (stopped for higher priorities).
- New A28 g210 (R7): 3 windows; the two 9+5+14 A28s: 21 windows (R8).
In most windows no product over the prefix has its class in T \ 0 (the BFS ends at the start
state); the largest BFS reached 24 operand spaces.  The kernel-truncation guard was added after the
chain1/chain2 runs (they had a silent limit of 10 kernel dimensions per hit; no hit had more than a
few states, so this is unlikely to matter, but those UNSATs are not re-checked with the guard).

### R4. Slack-1 windows with the FULL operand space (chain.py, ops = all) [C]
Case as R3 but operands in span(x, all kept ANDs, earlier new ANDs): the complete neighbourhood
"same kept ANDs, |U| - 1 new ANDs anywhere, any chain".  UNSAT, in every case not a single product
over the kept ANDs has its class in T \ 0:
- A28-5 closure(g14) (9 ANDs -> 8; 77 s); BP32 closure(g12) and closure(g13) (9 -> 8; 1714 s and
  1498 s); L2's hub A29 g135 closure(g15) and g134 closure(g10) (9 -> 8; 158 s, 125 s).
- A28-5 sink set {15, 16, 17, 18, 21, 22, 23, 27} (8 -> 7, a 27 if SAT): level-1 products with
  class in T DO exist (7 operand spaces after 3 enumerations, 677 s); UNDECIDED (CAP; a rerun with
  maxstates 400 was stopped at 03:23 for the pair run below; in the overnight a28 set).
- X1b 9+5+14 pair {18, 19} -> 1 and H2 pair {20, 21} -> 1: UNSAT (R8).
- Everything else with nv <= 34: overnight (QUEUE.md H3).

### R5. Deep windows: <= 1 new interior AND + one parallel layer, classes in Sigma_U (deep2.py) [C]
Case: U = all last-level ANDs plus the closure of one interior AND g (and U = all sinks); kept
ANDs R; new ANDs = A (|A| <= 1, operands in span(x, R)) then B (operands in span(x, R, A), no B
reads another B), every class mod W in Sigma_U; |A| + |B| <= |U| - 1; exact min-cover.
- UNSAT: A28-5 (16 windows), A28-4 (16), A29 g137 (15), BP32 (16), hub A29-AD4 g130 (17), A30
  (part), the new A28 g210 (16), and in sweep-day/ (X1b span families) the A28 structures of
  NIST g131-gd31, g141, g176, g124, g128 (79 windows).
- SAT: hub A29 g134, window sinks + closure(g7) -> the A28 of R7.

### R6. Relaxing Sigma_U (X3's critique) - pool-extended target (pool.py, lay_pool.py)
X3 is right that R2/R5 only re-arrange the junk inside Sigma_U.  Exact relaxation in general is
out of reach by enumeration (for slack >= 2 the junk direction of the first non-T AND is an
arbitrary product class, i.e. one would have to list all ~2^(2 nv) products).  Two partial steps:
- pool.py [C]: X3's 108,375 member/semi-member products (gamma = 0 witnesses of semi_members.tsv,
  operands in span(1, x, n), n = x^238 lies in W for the A28-AD5 prefix) taken literally over the
  A28-AD5 prefix: every one has its own junk (108,375 distinct junk vectors, junk span 52), and none
  equals an original last-layer class (0/13) - the tensor witnesses carry different x(x)x and n(x)n
  parts than the circuit's products, which are absorbed in X3's quotient but not by a fixed prefix.
- lay_pool.py [C for the enumeration]: target Sigma' = Sigma_sinks + D, D = span of the pool
  classes (dim Sigma' = 60 instead of 13), every product over the full prefix space (not only pool
  products) with class in Sigma': 2,824,491 classes (96,194 hit operands a), 2,824,476 distinct
  junk vectors in a 52-dim junk space, none junk-free.  The BFS min-cover hit its cap at depth 1
  (> 100k junk subspaces), so the question "12 of these with junk span <= 4" (a 4-flat containing
  >= 12 junk points) is UNDECIDED; it needs a flat-search algorithm, not BFS.  Log lay_pool.jsonl.

### R7. A 29 -> 28 reduction [V] (deep2.py, 02:58 UTC)
Source: hub best `aes-sbox-a29-ad5-g134-gd17-xx105-51` (AND profile 10|2|3|4|10, the kernel pull
product L2 pointed to).  Window U = all 10 last-level ANDs + consumer closure of g7 (15 ANDs: g7,
g10, g14, g17-g28); kept 14 ANDs; new: 1 interior AND (operands over span(x, kept)) + 13 parallel
products; 14 < 15.  Result `~/xs-campaigns/2026-11-15-study/H3/found/h3-d2-a29-ad5-g134-gd17-7-a28-ad5-g210.circ.txt`:
A 28, AD 5, G 210, GD 31, aes_check OK (coordinator re-checked).  Profile 10|1|2|2|13.  X1b
(span test, x1b_family.py): span{1, x, ANDs} and all per-level spans equal those of NIST
aes-sbox-a28-ad5-g128-gd20, so it is a re-bracketing of a known A28 AND space, not a new space
(my families.py product-multiset key was too fine; the sweep now uses X1b's span test).
On this A28: deep2 amax 1, all 16 windows UNSAT; slack-1 chain windows running (new28.jsonl).

### R8. The two 9+5+14 A28s (coordinator 03:20): X1b span-2cabef6153f4 (28/5/158/27), H2 s59 (28/6/585/33)
Both have 14 last-level ANDs with output rank 8 mod the prefix (slack 6 for "14 -> 13"; not a
slack-1 window).  Slack-1 sub-windows: each has one dependent PAIR (X1b {18, 19}; H2 {20, 21});
minimal dependent sets of size <= 5: X1b 1 + 2 + 1 + 5, H2 1 + 2 + 2 + 7 (all slack-1 sets incl.
non-minimal ones: {2: 1, 3: 14, 4: 89/90, 5: 338/350, ...}, slack1sets.py).
- ops = prefix (nosinks), all 21 minimal dependent sets of size <= 5 (c14.jsonl): UNSAT [C].
- X1b pair {18, 19} -> 1 AND with the FULL operand space (x + all 26 kept ANDs, any class):
  exhaustive r1enum over 2^33 operands a, split into two ranges on CPUs 14/15 (pair/pairA.out,
  pairB.out; input pair/in-x1b-18-19-all.txt; post-processing pair_post.py).  Result: UNSAT [C]
  (0 hits over all 2^33 operands a, 2 x 1.45 h, done 04:50): no single AND with operands anywhere in
  span(x, 26 kept ANDs) replaces g18 + g19 (kept ANDs fixed).
- H2 pair {20, 21} -> 1, same test (x + 26 kept ANDs): UNSAT [C] (0 hits over 2^33, 2 x 1.5 h,
  done 06:00; pair/pairC.out, pairD.out).
- deep2 amax 1 on both (classes in Sigma_U): all 15 + 15 windows UNSAT [C] (c14_deep2.jsonl, c14_deep2b.jsonl).
- Overnight: QUEUE.md H3 `job.sh c14` (all minimal dependent sets of both, full operands).

### Scope notes (X3b critique, 04:25)
- Every "no 27" / UNSAT statement here is for a FIXED kept part: the kept ANDs (in R8: the 14-AND
  prefix of the 9+5+14 circuits, and the non-window last-level ANDs) keep their exact functions;
  only the window's ANDs are replaced.  Nothing here bounds circuits with a different prefix.
- Chained new ANDs: chain.py (R3, R4, R8 and the overnight sets a28 / a29 / c14 / x1) allows ANY
  chain among the new ANDs (new ANDs may read earlier new ANDs; BFS over operand spaces).  deep2.py
  (R5, R7, overnight `deep` and H3b sweep) does NOT: its new interior ANDs read only span(x, kept)
  and its top layer is parallel (no top AND reads another top AND).  So chained top ANDs are covered
  only for slack-1 windows.
- The sidecar of 28/5/210/31 said "chain slack-1 re-solve" (a label bug in chain.build when called
  from deep2); corrected to deep2 (amax 1) at 04:25, original kept in old/; code fixed.

### Overnight dedicated run (06:10)
The undecided A28-AD5 window {15,16,17,18,21,22,23,27} (8 -> 7) has its own uncapped script:
`~/xs-campaigns/2026-11-15-study/H3/overnight/g124w8.sh` (chain.py, ops all, maxstates 1e9, no maxenums;
log overnight/g124w8.jsonl, PROGRESS lines in the xsrun log).  Removed from the a28 shards (--skip).
Smoke-tested 2 x 30 s on CPU 14.  Per-depth enumeration cost ~3.6 min (nv 28) doubling per depth up
to ~3.8 h (nv 34); total depends on BFS breadth (unknown).
