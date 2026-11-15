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
- r1enum speed: ~0.4-0.8 us per a (nv = 34, CPU shared during the test), so one exhaustive
  enumeration costs ~2^(nv-1) * 0.6 us: nv = 22 -> 1-2 s, nv = 27 -> ~1 min, nv = 34 -> ~1.5 h.
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
so no window "one AND + nothing" can lose an AND.  Minimal dependent sink sets (the only sink
windows with slack >= 1): A29: 1 of size 3, 4 of size 4, 11, 17, 30, 26, 11 of sizes 5-9;
A28-5: one PAIR {g17, g26}, one triple {16, 22, 24}, then sizes 5-8; A28-4: none below size 4
(6 of size 4, 10 of size 6, 8 of size 8); BP32: 8 triples, 15 of size 4, ...

### R2. Parallel re-layer with classes in Sigma_U (lay.py / batch.py) [C]
Case: new ANDs all with operands in span(x, R) (none reads another), every class mod W inside
Sigma_U; exact min-cover.  Windows: U = all sinks, and U = sinks + closure(g) for every interior
g.  Result: UNSAT (no m <= |U| - 1) for all 93 windows of A29, A28-5, A28-4, BP32, A30 and the
second umizame family a29-ad5-g139.  With U = all sinks, only 18 (A29), 19 (A28-5), 13 (A28-4)
product classes over the prefix land in Sigma at all; no smaller layer exists in this case (the
original size is the minimum).
