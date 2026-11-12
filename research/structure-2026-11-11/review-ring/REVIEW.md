# Review of compose/ring/REPORT.md

Independent machine review, phase 5 (2026-11-12), separate model instance (Opus, medium effort). Saved by
the main agent, condensed. Re-ran ring_cuts.py (both orders) on q3_28, q4_40, walk_q4_40, q5_50, walk_q5_50,
q6_60, walk_q6_60, q7_70, q8_80, walk_q8_80 and label_types.py on the 10m circuits; new checks `mc_cols.py`
(MixColumns column supports from rlib.mc_model) and `mc_tri.py` (triangles of the mirror window graph).
Not a human review.

- **1.1 Split: correct** (transposition preserves gate count, re-checked on every circuit above).
- **1.2 Near side: correct** (f >= 8: eight distinct non-unit omegas E_i(w^k), p_i(w^k); e >= 7: labels span
  Even(x) + F_2^4(y), x != y for m >= 3; arc statements: the f first gates project to an N_r instance with the
  four p_i(w^k); three p_i as exports give f + 3 >= M_r). Remark: h = 0 is always achievable (entries booked
  to the far side), so the near minimum equals N^p_r exactly (8 for r = 1).
- **1.3 Far side: correct**; DL_l >= M_(l-1) + 4 by projection (kernel contains F_2^4(y)). Over-claim: DL_1 is
  not open; DL_1 = 4 exactly (the four units of y as labels, no gates).
- **1.4 Honest replacement for rings: correct; L(S) undefined in the report.** Repair: L(S) = least
  straight-line cost of S from far units, labels placed earlier, and earlier values. Helper claim legitimate:
  units are far inputs (no staging issue); the helpers u0+u1, u2+u3 are new far gates placed at the first exit
  on that group and counted (the "+2"); every nonzero vector of F_2^4 is within one gate of units and helpers;
  no exit value is a unit (reduced). **Assumptions:** T reduced; each exit value supported on a SINGLE far
  group; summed over receiving groups far >= DL - 2 (number of receiving groups). Window-locality is not
  needed for 1.4; it is only how 2.1 obtains single-group support.
- **1.5 Failure claims.** The Q_3 example (groups 0, 1: f = 8, h = 0, one exit each, e = 9-10) is correct but
  there |L_k| = 17-18, above the observed 16: it refutes "near = 8 implies no exit", not a ring Lemma R stated
  at minimal |L_k|. "Lemma R / Theorem 4.1 fail" over-claims: no ring counterexample exists for m >= 4; their
  proofs do not transfer. "A cheapest-kind group can have a 7-label exit (beta <= 5)": not shown to exist;
  "not excluded". The m = 4 objects are valid instances of the separate problems (not mutually compatible,
  which the claim does not need); the sums are even lower (29 + DL_1 = 33 for 3-arcs). The point that the label
  interface must be carried as a variable stands.
- **2.1 Where an exit lands: correct conditional on its hypothesis, tightened.** Needed: the exit gate AND both
  operands lie in 2-windows (an operand on {k, k+1, k+2} could give an exit on {k+1, k+2}, a window).
  Triangle-freeness does not supply window-locality (u(0) + u(2) is a legal mirror gate in a general circuit).
  A cancellation-free primal circuit is mirror window-local in every summation order (a single-block primal
  signal feeds only sheets b, b+1; a signal on {b-1, b} only sheet b). The recorded circuits are window-local in
  the fwd and rev orders only, and only these 10m constructions: nothing about general circuits. The "gain at
  most 2" must stay labelled conditional wherever cited.
- **2.3 MixColumns.** (a) correct and now machine-checked: the four units of primal block 7 have mirror support
  exactly on sheets {0,1,3,4,7}; blocks b = 0..6 give {b, b+1}; mirror windows = seven 2-windows plus one
  5-window; the ring edge {7,0} exists only inside the 5-window. Over-claim: the mirror window graph has 11
  triangles, 10 inside the 5-window and exactly one cross-window ({1,2,3}, dual of the primal {1,2,7}); so
  "many more triangles" is misleading: one cross-window triangle, as in the primal. (b) correct (sheets 1, 3, 4
  meet three column families). (c) wrong as stated: pure labels (e|0) and (0|e) also span the diagonal (6
  labels instead of 3); "forcing mixed labels" at best at minimum label count, unproved. (d) not checked.
- **2.4:** data correct (all 9 single-group cuts of q4_40, q5_50 pure, f = 11 - o_y); weak evidence (same
  families).
- **Section 3 table** matches the re-runs. Script issues: label_types.py ignores the order argument;
  "min#labels None" in ring_cuts.py means more than 5 (cap), not "not in span"; Q_T variants unreadable (not
  claimed).
