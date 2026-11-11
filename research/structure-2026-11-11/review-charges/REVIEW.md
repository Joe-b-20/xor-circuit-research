# Independent machine review of RECORD.md section 7 (the charge theorem)

Review of 2026-11-11 by a second model instance (Opus) that did not write the section; saved by the
main agent from the reviewer's final message. A machine review, not a human review and not a formal
verification. The reviewer's code and logs are in this directory. All corrections below have been
applied to RECORD.md section 7.

**Bottom line.** The core result holds: the local lemma (9 gates impossible, 10 possible) was re-decided
two further independent ways, and the proofs of Theorem 7.1 and Corollary 7.2 are sound once three
definitional gaps are closed. Corollary 7.2 (every block-monotone MixColumns circuit has at least 80
gates) is right.

## Findings

- **A. Title "ten gates of its own": OVERSTATED.** For a general circuit the ten gates charged to one
  sheet can be the same gates charged to another. Reworded to "each sheet is charged ten gates".
- **B. "Below the block-monotone minimum 30" for Q_3: OVERSTATED.** 30 is a lower bound for that class
  at m = 3; no block-monotone 30-gate circuit is known. A rotation-symmetric 30-gate circuit found by
  SAT (`q3_sym30.txt`) has 18 violating gates.
- **C. Observed paragraph: WRONG in one detail.** Of the three mu = 0 gates of the 88, two live on blocks
  {2,7} and serve sheet 3; the third lives on blocks {3,7} and serves sheet 4. The charges and the claim
  that all three recorded circuits are block-monotone with no mu >= 2 gate are correct.
- **D. Local lemma: CORRECT; its status was overstated when written** (the second encoding's 9-gate run
  was pending). Re-decided with (i) `lemma_sat.py`: operands free vectors (zero included), units of b or
  earlier gates; no distinctness or nonzero constraints; K = 6, 7, 8 UNSAT without symmetry breaking,
  K = 9 UNSAT in 23 s with two justified symmetry breaks, K = 10 SAT; (ii) `lemma_exh.c`: exhaustive
  search, nothing with at most 9 gates (48.5 million nodes, 3.6 s), a 10-gate circuit found. The two
  methods agree on 14 random target sets. `lemma_exh.c` is recommended as the certificate.
- **E. Theorem 7.1: CORRECT WITH A GAP (definitions only).** Checked by program: the matrix equals the
  field arithmetic; formula (3.1); every sheet restricts to [b: E_c] + [a: s_c]. Gaps: "output gate" must
  be defined when a row has several carriers (use every gate whose mask is a row of the sheet);
  "ancestor" must mean the wire relation of the given circuit; the deletion step must cover zero
  operands (or use that the lemma holds with 0 available). Numerics: 4,500 function-preserving
  perturbations of the three recorded circuits, 93 % not block-monotone, 1,476 with mu >= 2 gates: the
  minimum per-sheet count was always exactly 10, under both readings of "output gate".
- **F. Corollary 7.2: CORRECT.** Sheet supports {7,0}, {0,1,7}, {1,2}, {2,3,7}, {3,4,7}, {4,5}, {5,6},
  {6,7}; no pair j != j' with each in the other's support; cancellation-free implies block-monotone; the
  formula for G is exact.
- **G. Scope: mostly fair.** The class contains all cancellation-free circuits and all recorded
  circuits (which do cancel inside blocks: 25, 16, 10 gates), is defined relative to the bit-position
  blocks, and excludes exactly the mechanism that wins at m = 3. "88 = 80 + 8 for the three extra terms"
  is a reading of totals only: sheet 0 carries 11 and sheet 4 carries 10. The Q_3 28-gate circuit and
  the Q_8 80-gate circuit were re-verified.
- **H. Attempts to break it: none succeeded.** mu >= 2 gates are easy to plant and survive
  normalisation, but each cost at least one extra gate (510 circuits from all single splits of the 88,
  smallest 89 gates). A 3,000-step walk over equal-cost rewirings never reached a mu >= 2 state. Q_4
  below 40: symmetric SAT at 36 and 38 gates timed out; undecided.

Scripts: `lemma_sat.py`, `lemma_exh.c`, `xval.py`, `check_sheets.py`, `perturb.py`, `split_nbhd.py`,
`rewire.py`, `q3_check.py`, `q4_sym.py`, `cancel_check.py`; about 64 CPU-minutes.
