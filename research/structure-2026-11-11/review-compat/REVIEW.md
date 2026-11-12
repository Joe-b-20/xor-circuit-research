# Review of compose/compat, compose/mc/OBSTRUCTION.md, compose/tri (phase 6)

Independent machine review (2026-11-12), separate model instance (Opus, high effort). Saved by the main agent,
condensed. Checks with own code: mycheck.py (own MixColumns matrix, validity, reducedness, waste),
cutcheck.py (own cut classification), p12.py (P(1,2) and restrictions), prop2.py, dump_lw.py (+ JSON gate
lists lw0..lw7, r88, r89). Not a human review.

## compose/compat
- **Prop 1: correct** (no exit: each P-gate has two pure operands; each L_b gate has two omega != 0 operands or
  is an entry; converse: F then N has no exits; letting F read block-b inputs gains nothing). It bounds
  exit-free circuits only: L_ef,b is an upper bound on L, not a lower bound.
- **Exits/acyclicity: correct, nearly definitional.** The given counterexample is not reduced (the exit value
  repeats the label). Reduced counterexample: x = u + l1, y = x + l2, exit s = y + u = l1 + l2, the far side
  builds l2 only as s + l1: all values distinct, set conditions hold, dependencies cyclic.
- **Prop 2: correct; the phi half now backed by a check** (prop2.py: a random automorphism fixing W_7 gives 32
  distinct non-unit values in A(units) with R_far, so phi(Lambda') >= 32 > 30 >= phi(units)). "The smallest
  description keeping both sides is Lambda itself" is informal, not a proved statement.
- **Prop 3: correct**, including e >= dim W (f and h gates have both operands among U_b and level values, so
  their values lie in the current span; only entries add a new direction, at most one each). nu(S_near) = 28
  exactly at block 7.
- **Prop 4: correct**; wording: "every unit-reading gate" (not only L_b gates; an exit u + x with omega(x) = u
  also reads a unit and is wasted).
- **K_7 >= 60: correct given Theorem 16.1** (with block 7 zeroed, output block 0 = [0:E_c], blocks 1..6 =
  [t:E_c] + [t-1:p_c], block 7 = [6:p_c]; sheets 1..6 with block 0 free are the chain of RECORD 16 up to the
  byte reflection; the four E_c(0) gates are block-0-only, distinct, non-unit, not among the 56; the [6:p_c]
  outputs are unused slack). Over-claim: "does not beat O's 72" mixes kinds (72 caps (T0)-bounds; it is not a
  lower bound).
- **Restriction-form obstruction: correct; circuits verify** (lw4 158 gates waste 5 at block 4; lw7 160 gates
  waste 6 at block 7; lw0 164 gates waste 6 at block 0; all compute MixColumns, reduced). lowwaste.py's
  docstring "waste is exactly 4" is false (5 or 6). K_b upper bounds confirmed (r88: R = 77 at blocks 1, 2, 4,
  5; at block 7 waste 17, R 71; r89 at block 7: waste 20, R 69). Cut classification of r88 matches the tables.
## compose/mc/OBSTRUCTION.md
- Lemma O.1 correct; "the labels span W" is a theorem (exits never feed s-parts of level gates), not only an
  observation. Templates, directions and quantifiers correct (chi <= tau_min only for exit-free T2, as
  required).
- Fixes: the table column "9 + (far - sigma)" is at the least-far witness; the text's "least values" are the
  smaller minimum over exit-free witnesses (P7 66 vs 68, M4 76 vs 78, M0 80 vs 82, M7 80 vs 84, P3 81 vs 82,
  P2 84 vs 85, M1 74 vs 75): caption must say so. "<= 86" and "<= 87" are corpus caps from checks, not
  theorems (fine for an obstruction; label them). The scope item "interface-dependent baselines escape O" is
  incomplete: by compat Prop 1, min over interfaces of (nu + phi) bounds only exit-free circuits at that cut and
  equals L_ef,b <= 88 at P7 (rec88 has no exit there); a whole-L bound of that form also needs the exit
  interface (Lambda, S, precedence).
- Spot-check P5 on rec88 confirmed (f 10, h 0, near 10; P 71, e 7, far 78; no exits; 7 labels, rank 7, span W;
  tau_min 7, sigma 0; 9 + 78 = 87).
## compose/tri headline
- **Not proved as stated.** Proved (zero blocks 3..7; ancestors of sheets 1, 2 with block-0-only values free form
  a pair circuit): P(1,2) >= 20 + (number of P(1,2) gates whose restriction is free, an input, or repeats the
  restriction of another P(1,2) gate). Correct version: for g = [2:x] + [7:y] (y != 0) an ancestor of sheet 1,
  P(1,2) >= 21 if (a) x is a unit (g restricts to an input, however built), or (b) some other P(1,2) gate
  restricts to [2:x], in particular when one operand of g lies on block 7 alone (the other operand is then
  [2:x 7:z], any z; it is nonzero on block 2 and an ancestor of sheet 1, hence in P(1,2)). The main agent's
  caution required a pure block-2 operand, stronger than needed. Open: other constructions with x non-unit;
  given P(1,2) = 20 this is equivalent to "no 20-gate pair circuit (sheets 1, 2, block 0 free) contains a
  non-unit pure-block-2 gate that is an ancestor of a sheet-1 target" (unproved). restrict7.py tags repeats
  against the first producer anywhere; only repeats within P(1,2) count (no effect on observed cases).
- Spot-check circuits_2.txt line 20 confirmed (88 gates, reduced; |P(1,2)| = 21, 20 distinct new restricted
  values; the only {2,7} gate g65 = g36 (block 2) + g40 (block 7), case (b)).
