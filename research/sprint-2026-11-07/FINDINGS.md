# Sprint 2026-11-07: findings

Each entry: observation, mechanism (plain words), prediction that could be wrong, test, what
survived, limits. Tags: [proved] [checked] [measured] [cited] [guess]. Scripts are named; raw
data lives in `~/xs-campaigns/2026-11-07-sprint/`.

## F1. Descending to 88 on MixColumns is cheap; the difficulty is entirely below 88 [measured]

- Observation (hunt, first 25 min, 12 fresh-root chains, v8 uncapped): every chain reached <= 89
  within 10-162 s of its root; 4 of 12 reached 88 within 50-216 s. (`hunt/descents.py`)
- Compare: July 2026 engine, every 88 within 3,855 s of its root, median 2,234 s (restart.root_seconds
  doc string). The v5+ incremental kernel changed the picture: 88 is minutes away from any root.
- Prediction: with hours of such descents, the number of distinct 88 plateaus reached will tell
  whether the 88 level is a small finite set (saturating curve) or vast (linear growth).
- Status: open; curve to be read from `hunt/plateaus.py`.

## F2. A 3-way plateau factor is the pairing choice of an unshared 3-input XOR tree [checked on one circuit]

- Observation: the repo 88@5's remove1 plateau is a product of 7 factors with 3 choices each
  (2,187 states) [checked, PES compress]. For a 3-input XOR s = a ^ b ^ c the intermediate can be
  a^b, a^c or b^c; those three values XOR to zero and each is used only by s.
- Prediction: in every factor the three choice values XOR to zero. Test: `hunt/factors.py` on the
  repo 88@5: 7 of 7 factors satisfy it [checked].
- Consequence: walking an 88 plateau is re-pairing seven 3-input trees. It can never change the
  circuit's structure; the 2,187 states are one circuit in seven interchangeable spellings. A
  plateau walk at the bottom is therefore pure repeated work, and the only genuine moves out are
  the +1 / +2 edits of the 49-value core (which PES explored).
- Extended to all stored PES plateaus (`hunt/pes_plateaus_check.py`, 68 files, 52 distinct 88
  plateaus modulo rotation): 424 of 424 three-way factors XOR to zero [checked]. Radices: 32
  plateaus are 3^7; 13 are 33·3^5, 3 are 45·3^4, 1 is 108·3^4, 2 are 3^6, 1 is 12933·3^2: the
  non-3 factors are coupled blocks where several trees share values.
- Vocabulary: the union of helper values over the 52 plateaus is 524 raw values = 303 modulo
  byte rotation (popcount 2: 54, 3: 99, 4: 111, 5: 98, 6: 86, 7: 45, 8+: 31). The 88 level
  speaks a small language [checked]. Whether new plateaus found by the hunt add words to it is a
  sharper novelty measure than plateau counts (to be tracked).
- Limits: the "unshared" part is inferred from the product structure (if the intermediate had
  another consumer, re-pairing would change that consumer's recipe and the factor would not be
  independent).

## F4. Across 59 maps: size and row weight predict gain over NIST; MixColumns is ordinary in every map property and an outlier only in outcome [measured, crossmap agent]

- Data: all 59 maps, properties computed from the matrices (`crossmap/props.py`), outcomes from
  circuits/ and the finder logs (`crossmap/outcomes.py`, `analyze2.py`). Protocol confound: 49
  "batch" maps had 1 NIST-seeded uncapped worker + 1 low-cap worker for 30-60 min; correlations
  below are on those 49 with partial rank correlation on log(NIST gates).
- Survives size control: max row weight (+0.63), mean row weight (+0.58), base/direct (-0.64:
  more sharing left by greedy constructors = more gain), NIST's depth slack above the minimum
  (+0.49, a property of the baseline). Does not survive: field size, matrix dimension, inverse,
  involutory, circulant/dyadic. Plateau width of the final state goes with LESS gain (-0.42).
- Mechanism offered [guess]: a remove1 improvement exists when several users of a value have
  leftovers that coincide in one buildable value; heavy rows have more common sub-sums, so more
  coincidences to find and more left behind by greedy baselines.
- Saturation: 16x16 maps saturate in under a minute, 32x32 maps over 4x4 matrices in ~5 min,
  8x8-matrix maps keep gaining ~1-2 % of NIST's gates per unit of ln(time) all hour.
- Moves: walk.remove1 made 89 % of the gates won below NIST, lns.rebuild 9 %, expand 1 %,
  structural 0.3 % (structural moves used 4.6 % of CPU).
- MixColumns: density, row weights, constructor gap all mid-class; every other 32x32 map over a
  4x4 GF(2^8) matrix gained 3.3-11 % over NIST in 1-2 worker-hours, MixColumns 0 % at depth 5 in
  >100 worker-hours. Reading: NIST's 88 is a literature-optimised point that our fresh-root
  search independently reaches and stops at (a BASELINE effect, not a map property). This is
  consistent with the plateau findings (F1, F2) but does not by itself say whether 88 is optimal.
- Falsifiable predictions recorded in `crossmap/predict.csv` (e.g. skop15-8x8-gf16 146 -> 140 at
  depth 19 in 1 h on 4 workers; no 16x16 map gains a gate). Discriminating experiment X1 (fresh
  roots vs NIST seeds at NIST's depth, 8 maps) prepared in `x1/x1.toml`, to run when cores free.

## F5. The 88 level is vast: nearly every independent descent lands on a new plateau [measured, provisional]

- Observation (hunt, first ~45 min, `hunt/plateaus.py`): 13 arrivals at 88 (41 sampled states)
  fell into 12 distinct plateaus modulo rotation; the one repeat was the same worker's chain.
  Shapes: 7 x 3^7 (2,187 states), one 3^8, one 33·15·3^5 (120,285), one 18927·15·3^2
  (2.56 M), two giants whose closure did not finish in 10-18 minutes (depth 9). The public kste
  corpus (F3) has 17,462 isomorphism classes of 88-gate circuits.
- Mechanism [guess]: the 88 level consists of a very large number of distinct cores (sets of
  49 or so values); each is reachable from a sizeable basin of roots, and the walk never
  leaves it downward. Sampling plateaus by descents at ~2 per worker-hour cannot exhaust it.
- Prediction (to test as the hunt continues): the discovery curve (distinct plateaus against
  arrivals) stays close to the diagonal for the whole 8 h; overlap with the 52 pre-sprint
  plateaus stays near zero.
- Consequence for the 87 question: whether an 87 exists is a global question about the map,
  not something more descents can settle by sampling; the useful tools are exact (SAT over a
  structured family, lower-bound arguments) rather than more local search. The search question
  "what determines reaching better circuits" has, on MixColumns, the answer "a down-exit from
  some 88 core, and none of the ~65 cores examined by +1 edits has one".

## F3. Context from the literature and a public corpus (lit agent, 2026-11-07) [cited]

- 88 XOR is now published: J. Jean, ePrint 2026/1481 (July 2026); earlier 97 (2017), 95, 94,
  92 (2019-20), 91 (2021), 89 (Sun-Yang-Li 2025). Nothing below 88 is claimed anywhere found.
  So 87 would be a new record; 88 is a tie with the literature and NIST.
- github.com/kste/mixcolumns_xor holds 18,938 88-XOR MixColumns circuits (17,462 isomorphism
  classes claimed) and a README arguing an "88-XOR barrier" from a bit-slice block decomposition
  plus SAT/MITM refutations of 87 in stated scopes (73 "double-optimal" circuits; sub-DAGs; a
  1,607-signal pool; a tropical DP). None of the refutations is a general proof; the scopes are
  circuit classes around known 88s. Being checked by the `kste/` agent against our plateaus.
