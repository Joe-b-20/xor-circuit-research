# Review of P1-P5 (compose/refute), Obstruction O (compose/mc), TWOSIDED sections 6-8

Independent machine review, phase 5 (2026-11-12), separate model instance (Opus, high effort). Saved by the
main agent, condensed. Checks (finite, no SAT), labelled CHECK: `witness.py` (own MixColumns matrix),
`p3check.py`, `p3unit.py`, `p5o3.py`. Not a human review. No counterexample to SB* found.

## 1. compose/refute
- **"Clean labels independent" restricts the class.** dangle2 is outside it (its clean labels p0..p3 sum to 0);
  the whole 6+4 ten-gate form is outside it (with independent clean labels every trace is even, so |T*| >= 7;
  |T*| = 6 needs dependent labels); for l = 2 five or more clean labels are always dependent. For e1 = 4,
  dependent labels span exactly E and Theorem S1 covers them, so P5's e1 = 4 claim stands; P1 and P4 do not
  cover the dependent case. The P5 "consequence" must read "a 29 needs e1 >= 5, near1 >= 11 and two exits, OR
  has dependent clean labels".
- **P1: correct under independence**; repair: "U_k meets the clean chain in one contiguous segment" is false
  when U_k has several components; count per component (each component's top node is the top of its segment,
  a prefix value; each gives at most e_C - 2 gates); chi <= e1 - (#components) <= e1 - 1.
- **P2: correct**; the upper bound chi <= e1 + q - 2 needs no independence; the laminar lower bound needs all
  labels independent and J = all labels; "violates SB* exactly when q >= 4" is shown only for J = all labels.
- **P3: correct and sharp** (CHECK `p3check.py` over every value set on W0..W3, X: with at most 2 other gates
  nothing contains all four E_c plus >= 4 Z+X, or 3 Z+X with spanning Z; with 3 other gates every m from 3 to
  7 is reachable).
- **P4: correct under independence** (q <= distinct zetas <= |T*| - 4 <= f1 + h1 - 4; equality excluded by
  P3; cleaning w.r.t. targets plus one exit keeps the zetas; |T**| = kept non-entry non-exit gates + 2).
  **Where it breaks for dependent labels (CHECK `p3unit.py`):** odd types allowed; with the four unit types
  the fewest gates holding E_c and W_c + X is exactly 10 (two other gates), so q = 4 fits at f1 + h1 = 8
  (near1 = 11, tau = 3), where P2 gives only chi <= e1 + 2, one more than SB* allows. The natural place to
  look for a counterexample to SB*.
- **P5: correct for e1 = 4** (in Omega1 the four zetas are distinct and nonzero, so q = 4 and P4 applies;
  o = 4 cross-sum step right, (Y) rigidity not re-derived; o = 3 CHECK `p5o3.py`: every set of three or four
  weight-3 exits, every label and exit order: exact chi <= 5).

## 2. Obstruction O
- Witness check: the block-7 witness computes MixColumns, reduced, 88 gates, no gate cancels any block; at
  block 7 f = 10, h = 14 (near 24), far = 41 ordinary + 0 exits + 23 entries = 64. **References wrong**
  (cumulative line counter of far_mc.py): "circuits_3 line 15380" is circuits_3.txt line 13114 (the real line
  15380 gives near 20 / far 68); "circuits_2 line 360" is line 313; "line 260" presumably 213.
- **Justification wrong:** "block-monotone, so its far part is a standalone instance" does not follow
  (mc.analyse's "monotone" is a different notion; circuits_1 line 40 counts as monotone yet cancels block 7);
  what is needed is no exit at that cut, checked per witness: holds for the block-7 witness, not checked for the
  mirror-group witnesses.
- **"8 suffices for any label interface" is false as written** (for the witness's interface an 8-gate near side
  would give 72 < 75); true: the minimum over interfaces is 8 (attained by the 97 at blocks 7 and 0).
- **SB*-type compositions:** with chi - e = -sigma on exit-free instances, the best constant supplier baseline is
  A = min(near + sigma), not near_min. Repair (own computation): 8 first gates and one entry per required row
  (label = that row's far part): primal blocks 0-6: 8 rows, dim W = 7; block 7: 20 rows, dim 19; mirror groups
  1, 3, 4 presumably 12 against 11; sigma = 1, A <= 9; provable bound <= 9 + far(witness): at most 73 at block 7,
  87 at the worst cuts. O survives with one gate less margin: such a composition still cannot reach 88.
- **Scope:** O constrains only inequalities claimed for ALL circuits; a supplier inequality proved only for
  optimal (or <= 87-gate) circuits is not covered. Theorem 7.1 needs only optimal circuits.

## 3. TWOSIDED sections 6-8
- Section 6 correct; section 9 should list the independence hypothesis of the new results.
- Section 7 correct (cases exhaustive; e1 <= 2 impossible; chi cancels; sufficient not necessary). Suggestion:
  the hypothesis can be weakened to optimal T.
- Section 8: the inequality |P| >= J(R) - (|R| - |S|) is correct; "exact" is a misnomer (valid for every R, no
  R shown to attain equality). "SB* is the last interface-only form" is wrong as a mathematical claim:
  phi(I) := least far cost compatible with interface I is a function of the interface alone, and
  D(I) = M_(l-1) - phi(I) gives the sharpest supplier inequality, still interface-only; within the computable
  family A = min(near + e - chi) is another refinement. Defensible: "the last refinement whose correction is a
  straight-line minimum over labels and R-values with a constant baseline"; the rest is heuristic.
