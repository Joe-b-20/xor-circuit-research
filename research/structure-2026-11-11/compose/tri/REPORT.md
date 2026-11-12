# The MixColumns triangle mechanism, worked through

Delegated investigation, phase 6 (2026-11-12), separate model instance (Opus, medium effort); saved by the
main agent from its final message, condensed. Review status in RECORD 21. Checks are program runs on corpus
files (scripts below); line numbers are each file's own (starting at 1; the files have no blank lines);
sampling: every 20th line in each file (744 non-monotone, 204 block-monotone circuits). Scripts: scan_tri.py,
show_tri.py, nearest_mono.py, nearest_local.py, servesig.py, pairs.py, exituse.py, famstat.py, restrict7.py,
restrict7_stat.py, triple.py, partner.py, repair.py. [j:v] = nibble v on block j.

**Correct statement after review (`../../review-compat/REVIEW.md`).** The headline "a gate [2:x] + [7:y]
ancestor of sheet 1 with x not a unit forces P(1,2) >= 21" is NOT proved as stated. Proved: zeroing blocks 3..7,
P(1,2) >= 20 + (number of P(1,2) gates whose restriction is free, an input, or repeats the restriction of
another P(1,2) gate). Hence for g = [2:x] + [7:y] (y != 0) an ancestor of sheet 1, P(1,2) >= 21 if (a) x is a
unit, or (b) some other P(1,2) gate restricts to [2:x], in particular whenever one operand of g lies on block 7
alone (every observed corpus case). Open: other constructions with x non-unit; given P(1,2) = 20 this is the
pair-circuit statement "no 20-gate pair circuit contains a non-unit pure-block-2 gate that is an ancestor of a
sheet-1 target". (The main agent's first caution required a pure block-2 operand: stronger than needed.)

## 1. Worked example: circuits_2.txt line 20 (88 gates, not block-monotone; six gates break monotonicity:
g36, g55, g65, g74, g76, g77)

Cut: primal block 2. Exit g78 = g65 + g77.
- g65 = g36 [2:s2] + g40 [7:s2] = [2:s2 7:s2]; serves sheets 1 and 3 (sheet 3 reads it in g97, on the way to
  output (2,3)).
- g77 = g63 [0:s1 7:d1] + g76 [1:E1 2:s2] = [0:s1 1:E1 2:s2 7:d1]; serves sheet 1 only; its support {0,1,2,7}
  lies in no sheet's support (the circuit is not window-local).
- g76 ends a chain on blocks {1,2}: g55 = x9 + g36 = [1:e1 2:s2], g74 = x1 + g55 = [1:s0 2:s2],
  g76 = g70 [1:E0] + g74; each feeds a sheet-2 output: (1,2) = g55 + g89, (0,2) = g74 + x10, (3,2) = g76 + g91.
- Supplied value: g78 = [0:s1 1:E1 7:s1], exactly the target (1,1). Cancelled block-2 vector s2; on block 7
  the s2 of g65 and the d1 of g63 add to s1.
- Counts at the cut: near (nonzero on block 2) 21 = 9 first gates (carrying s2, d1, E0..E3, s1, s0, s3: the 8
  required block-2 parts plus d1) + 12 entries (labels x9, g45, g40, x1, g70, g63, x17, x25, x19, g101, g32,
  g62) + 0 non-entry duplicates; far 67 = 66 ordinary + the exit.
- The route enters labels x9, x1, g70, g63, and the partner brings g40: those five sum to (1,1), so rebuilding
  it on the far side would cost 4 gates; the route's only dedicated gates are g77 and g78.
- Sheet 1 after the supply needs (0,1), (2,1), (3,1): (3,1) = g72 + g78 with g72 = [0:t 1:d1 7:t] =
  (1,1) + (3,1) (the supplied target is reused once as an intermediate); g72 also gives (2,1) = g52 + g72;
  (0,1) = g34 + g70.
- Intermediates/exports: the only new intermediate is g77 (sheet 1 only); nothing on the route goes to another
  sheet (no exports); the exit's operands reuse signals that sheets 0, 2, 3 build anyway (g63, g76, g65).

## 2. Comparison with a block-monotone circuit

Nearest block-monotone circuit on the local region: circuits_3.txt line 593 after rotating bytes by 2 (a
symmetry); it still differs locally in 16 values (a reference, not a twin). Shared: g52/g99
[0:s0 1:e0 7:s0], g72/g87 [0:t 1:d1 7:t], (2,1) = g87 + g99. Monotone circuit: g100 = g33 [1:s1] + g99;
(3,1) = g97 [0:d1 7:d1] + g100; (0,1) = g46 [1:s3] + g100; (1,1) = g87 + (3,1); three pure block-1 gates
g33, g43, g46 shared with sheet 2. Gates serving sheet 1 only: 8 (monotone) vs 7 (exit); serving sheet 1 or
2: 21 in both.

| Circuit | F_j sizes (sheets 0-7; F_j = ancestors of sheet j nonzero on block j) | overlaps | in no family | P(1,2) |
|---|---|---|---|---|
| exit circuit | 11, 12, 11, 14, 13, 10, 10, 10 | 3 (g55, g74, g76 in F1 and F2) | 0 | 21 |
| monotone | 11, 10, 10, 13, 13, 10, 10, 10 | 0 | 1 (g97, sheet 1 only) | 20 |

Both 88: the exit circuit has 3 double charges against 4 over-charges (F1 +2, F2 +1, F3 +1); the monotone
pays one gate outside every family. Cost moves across the cut: near 21 / far 67 against 17 / 71.
Corpus (stride 20): all 744 non-monotone: exactly 3 overlaps, F2 = 11, P(1,2) >= 21 (663 at 21, 81 at 22),
the exit always reaches exactly two sheet-1 targets. Block-monotone: F2 = 10, P(1,2) = 20 (34), 21 (81),
22 (89).
Zeroing block 7 (check): sheet 1 becomes [0:s_c 1:E_c] with block 0 free, the pair problem of Theorem 15.1. In
the example the 21 gates of P(1,2) restrict to 20 distinct values that are neither free nor repeats (the
pair minimum); the only repeat is g65, restricting to [2:s2], a copy of g36; the exit becomes an ordinary pair
exit [0:s1 1:E1 2:s2] + [2:s2]. Corpus, all 744: the single repeat is always a gate on {2,7} serving sheets 1
and 3 (663: 20 new + 1 repeat; 75: 21 + 1; 6: 20 + 2). The partner's value is always [2:x] + [7:y]:
[2:s2 7:s2] (627), [2:d0 7:s3] (105), other [2:s_c 7:s_c] (11), [2:d0 7:s1] (1). So modulo block 7 the
triangle exit is a pair exit at the pair minimum; the triangle's contribution is that the cleaning partner is
a gate sheet 3 needs anyway.
Hand repair (check): replacing g77, g78 by four gates (x1 + x9, + g70, + g63, + g40 giving (1,1)) gives a
valid 90-gate block-monotone circuit (repair.py): against this repair the route saves 2 locally; the monotone
corpus circuits recover those 2 by a different global arrangement; no equal-cost local monotone rewrite found
(hand repairs only).
Is the saving matched by one specific extra gate? Depends on bookkeeping (families: 3 double charges against
over-charges spread over F1, F2, F3; pair count: g65; local repair: +2 at g77/g78; sharing/REPORT section 5
charged the three {1,2} gates to the route, but each also feeds a sheet-2 output). Forced: the totals;
P(1,2) >= 20 for every circuit; and P(1,2) >= 21 when the partner is built as [2:x] + [7:y] from those two
parts (see the caution above).

## 3. What the matrix forces and what belongs to the circuit

Forced (equation (3.1)): S1 = {0,1,7}, S2 = {1,2}, S3 = {2,3,7}; each edge of the triangle lies in a different
sheet's support and no sheet contains all three; sheet 3's rows have the same s_c on blocks 2 and 7, so
[2:s_c 7:s_c] is a natural sheet-3 gate (the M-type gate of Theorem 9.1); sheet 2's signals can carry a
block-1 part next to an even block-2 part; sheet 1 needs an E-type part on block 1 with s-type parts on blocks
0 and 7; every observed exit value has block-1 part E and block-7 part s. Lemma II.6 covers only window-local
circuits; 531 of the 744 sampled exit circuits are not window-local (the {0,1,2,7} or {0,2,7} operand).
Belongs to the circuit: which s_c is cancelled (s2 in 627, d0 in 106); which sheet-0 gate supplies the {0,7}
correction; the bracketing of the three-term sum g63 + g76 + g65 (giving the three operand classes; in
circuits_2.txt line 740 the same three are added as g76 + (g63 + g65)); where compensation lands.
Target or auxiliary: whether the exit gate equals a target is a matter of bracketing; in the most common
classes it is (1,1); in the {1,7} classes it is (target - a {0,7} vector), common to two targets (line 220:
[1:E1 7:s2], feeding (1,1) and (2,1)). Invariant: the three-term sum is a sheet-1 target, the value serves
only sheet 1, and reaches exactly two sheet-1 targets. Contrast with the chain: there reconstruction sums
become exports to other sheets; here nothing on the route goes to another sheet; reuse stays inside sheet 1
(a second target through the difference vector g72 = (1,1) + (3,1)).
Not established: an equal-cost local monotone rewrite of any exit circuit; P(1,2) >= 21 for other partner
constructions; any bound beyond 88.
