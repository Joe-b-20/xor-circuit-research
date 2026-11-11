# Independent review of RECORD.md sections 1-4 (2026-11-11)

Machine review. I did not write the text under review. I derived each claim again by hand and
checked it with scripts in this directory (standard library, plus scipy for one LP check). Each
`*.out` file is the output of the script with the same name. Run from this directory with
`python3 <script>.py`.

Verdict words: CORRECT, CORRECT WITH A GAP, WRONG, OVERSTATED.

## Summary, most serious first

1. **Section 4, first bullet: WRONG.** It says the quotient route "yields only G >= L(M2) + 32,
   weaker than 56". But section 1 applied to M2 gives L(M2) >= 24. The rows of M2 are odd, distinct
   and not unit vectors, and the graph code of M2 has minimum weight 4, so c(1) <= 8 and
   L(M2) >= 16 + 16 - 8 = 24. Hence L(M2) + 32 >= 56. Since 24 <= L(M2) <= 26, the bound would lie
   between 56 and 58. It is never weaker than 56. The step "at least rank-many dead gates disappear"
   is also unproved: a drop in rank does not make a gate disappear. See item 4.
2. **Section 3, definition of the flag: WRONG (index reversed).** "The masks that vanish on
   (1+y)^(4-k) R" gives subspaces of dimensions 24, 16, 8 for k = 1, 2, 3, which form a decreasing
   chain. The block descriptions and the dimensions 8, 16, 24 belong to W_k = masks vanishing on
   (1+y)^k R. Equivalently, W_k is the set of masks lying in (1+y)^(4-k) R under the coordinate
   identification. `tools/levels.py` repeats the wrong formula in its docstring, but its code uses
   the correct block criteria.
3. **Section 1, several points: OVERSTATED.** The hand check uses 4 of the 6 two-point
   inequalities. The two it leaves out are exactly the ones that require "no single point beats 56",
   which the record does not prove. I closed the two-point case (item 1c). For three or more points
   nothing is proved.
4. **Section 2, "(at most 3 by F3)": CORRECT WITH A GAP.** F3 alone does not bound r_p; PROOF
   Lemma 4.4 (independence) is needed. "(2.1) is the F20 ledger in exact form" needs an
   independence lemma before the ledger follows from (2.1).
5. **A stronger observation that the record missed.** The recorded MixColumns 89@4 itself has
   x = 26, h + y = 31 < 32 and S = 1. So "h + y >= n" already fails for MixColumns, by its own
   recorded circuit.
6. Everything else checks out: the section 1 theorem, identity (2.1) on 73 of 73 circuits, formula
   (3.1), the ring algebra, the quotient-identity claim (for both M and M^T), and the observed counts.

---

## Item 1. Section 1

### 1a. Statement and proof: CORRECT

- **Induction.** I redid it independently.
  - E_0 = span{e_i : x_i = 0}. This is the space that is even on the singleton blocks of supp(x)
    and free outside supp(x), so P_0 consists of wt(x) singletons.
  - live + dead gives a live signal congruent to the same e_i; E does not change.
  - dead + dead gives a dead signal that is already in E_t.
  - live + live gives a dead signal equal to e_i + e_j + (an element of E_t). So
    E_{t+1} = E_t + <e_i + e_j>, which merges two blocks or changes nothing.
  - Only live + live gates raise dim E, each by at most 1. So the number of dead gates is at least
    (n - c) - (n - wt(x)) = wt(x) - c.
  - The proof is complete. It needs no normalisation: zero gates and duplicate gates are covered.
- **The claim c <= c(x).**
  - b_C != 0 because blocks are nonempty.
  - (M b_C)_o = row_o . b_C. A live row is congruent to e_i mod E, so it is odd on exactly the
    block of i; a dead row lies in E, so it is even on every block. Hence for each o at most one C
    has (M b_C)_o = 1. The supports are therefore disjoint, and the M b_C sum to Mx.
  - The input parts are disjoint blocks with sum x.
  - So the (b_C, M b_C) are c nonzero codewords with disjoint supports and sum (x, Mx). Justified.
- **Live gates.** The live outputs are wt(Mx) distinct signals, and each is a gate because no row
  is a unit vector. Correct.
- **Hypotheses.** Both are needed, and the record's set is sufficient:
  - *Unit rows.* M = (1), x = 1: the bound gives 1 + 1 - 1 = 1, but G = 0.
  - *Repeated rows.* M = [[1,1],[1,1]], x = (1,0): wt(Mx) = 2 and c(x) = 1, so the bound gives 2,
    but G = 1.
  - *A zero row* (at most one is allowed by "distinct") is dead at every x and adds nothing to
    wt(Mx) or to c(x). Harmless.
  - *A dead output row* lies in E and is even on all blocks. This is used correctly.
  - *Dead inputs* are handled by E_0.
  - The hypothesis could be weakened to "the rows live at x are distinct and not unit vectors".
- **Relation to PROOF.** x = all-ones gives Lemmas 2.1 and 2.2, and with F1 the 56. Correct. The
  "columns odd" condition is not used.

### 1b. Numerical test: no violation

`sec1_eval.py 300` was run on all 208 recorded circuits (every map), with 70,680 points in total.
The points were all-ones, every e_i and every 1 + e_i (for n <= 32), and 300 random points of
densities 0.1 to 0.9 per circuit. For each point it checks, exactly and from the definitions:

- dim E grows only at live + live gates, by at most 1;
- E equals the block-even space (by containment and dimension);
- every live signal is odd on exactly one block;
- dead gates >= wt(x) - c, live gates >= wt(Mx), and dim E_final - dim E_0 = wt(x) - c;
- the block words are nonzero, pairwise disjoint and sum to (x, Mx).

Result: **0 violations**. Equality "dead = wt(x) - c" occurred at 44 points and equality
"live = wt(Mx)" at 60 points, so the test is not vacuous. No recorded matrix has repeated or unit
rows.

### 1c. Negative remark ("several points"): OVERSTATED

- **The hand check is incomplete.** The quoted system has 4 inequalities:
  - live at x1 = 1: N_a + N_b >= 32;
  - dead at x1: N_c + N_0 >= 24;
  - dead at x2 and dead at x1 + x2: N_a + N_0 >= A and N_b + N_0 >= B.

  The live inequalities at x2 and at x1 + x2 are missing: N_b + N_c >= wt(Mx2) and
  N_a + N_c >= wt(M(x1+x2)). With N_0 = 0 and N_c = 24, a feasible point needs
  A + wt(Mx2) <= 56 and B + wt(M(1+x2)) <= 56. These say that the single-point bounds at x2 and at
  1 + x2 are at most 56, and the record does not prove that. The classes a, b, c and the values A,
  B are also not defined in the text.
- **The gap closes for two points.** (`sec1_points.py`, `sec1_dual.py`)
  - Put z = 1 + x. Every row is odd, so M1 = 1, and the single-point bound at x equals
    64 - w(z) - c(1 + z), where w(z) is the weight of the graph-code word of z.
  - Full enumeration over inputs of weight <= 5 gives 84 words of weight 6 and none lighter. For
    each of them a valid partition of supp(1 + z) with at least 7 blocks exists, so the bound there
    is at most 51. Words of weight >= 8 give at most 55.
  - So the best single point for MixColumns is exactly 56, reached only at all-ones.
  - The dual of the two-point LP has these vertices:
    - L_a + D_a (single points);
    - L_a and D_a alone;
    - (L1 + L2 + L3)/2, which is <= 32;
    - (L_a + D_b + D_c)/2 with {a, b, c} = {1, 2, 3}, which is <= (32 + 62)/2 = 47.
  - Hence the two-point LP optimum is <= 56 for every pair (x1, x2), not only for x1 = all-ones.
  - So the two-point claim is **true**, but only by this argument, not by the record's.
- **Three or more points are not proved.** With 300 random triples, using greedy (valid) lower
  bounds for c, so that each LP value is a rigorous upper bound, the maximum was 56. That is
  evidence, not a proof.
- **Corrected wording:** "For two points the LP relaxation gives at most 56 for MixColumns (proof:
  dual vertices plus the 84 weight-6 words); for three or more points this is untested beyond
  sampling."
- The "reason is structural" sentence is a heuristic, not a proved statement.

## Item 2. Section 2

### 2a. Derivation of (2.1): CORRECT

- **Line by line.**
  - The gate count is G = x + y + (n + h): producers, sums and translates.
  - There are x + n + h edges.
  - Every represented label has exactly one B-B edge. Two B-B edges with the same label signal
    would need two boundary pairs with the same XOR (excluded by the weight-4 condition), or the
    same pair twice. The same pair twice would force a gate that duplicates a boundary signal, and
    such a gate is a helper, not boundary. So #B-B = x + y - q.
  - The non-B-B edges, sorted by label, number sum_p r_p + z_r + sum_missing e_l.
  - The algebra then gives G = 2n + x - S exactly.
- **q.** It must count the even signals that label no edge. Each such signal enters S as -1 through
  (e_l - 1) with e_l = 0. Without them the identity is off by q0, which is 2 for the MixColumns 88.
  The record's "even masks are vectors (labels)" makes every even signal a label, so the definition
  is consistent. The phrase "q labels that are not the difference ..." is ambiguous on first
  reading.
- **r_p, z_r, e_l.**
  - Helper-helper edges are counted once each: in z_r if their label is represented, in e_l if it
    is missing.
  - Helper-boundary edges with a missing label are counted in e_l.
  - Correct.
- **No hidden hypothesis.** The identity holds without normalisation (`sec2_extra.py`). I added a
  duplicate output gate, an input duplicate, an unused even gate and a zero gate to the 88@5; then
  G = 93, x = 27, S = -2, and the identity still holds. "Columns odd" is not used.

### 2b. Program check: CORRECT

`sec2_identity.py` checks the hypotheses for every map: square; all rows and columns odd;
boundary vectors distinct and nonzero; no weight-3 relation; distinct pair sums. The maps that pass
are aes-mixcolumns, aes-invmixcolumns, anubis-clefia-m0, aria, clefia-m1, joltik, khazad, two klsw
inverses, lw16-4x4-gf16-inv, lw16-4x4-gf256-inv-had, three skop15 inverses and small-scale-aes.

On all 73 circuits of these maps, every quantity was computed from its definition. **(2.1) holds
on 73 of 73.** All circuits are normalised; the odd graphs are simple; every label is a matching;
no label has more than one B-B edge.

### 2c. Claims after the proof

- **(i)-(iii) as the only positive sources: CORRECT WITH A GAP.**
  - S = sum(r_p - 2) + z_r + sum_missing(e_l - 1), so its positive terms are exactly r_p = 3,
    z_r >= 1, and e_l >= 2 for a missing label.
  - But "r_p <= 3 by F3" is not enough. F3 bounds distinct triples. Two represented edges at one
    helper can carry the same triple {a, b, c}: edge p-a with label b + c, and edge p-b with label
    a + c. F3 does not exclude this.
  - It is excluded by PROOF Lemma 4.4: the four gate equations would sum to zero as formal rows. So
    cite Lemma 4.4, not F3 alone.
- **"An 87-gate circuit needs S >= x - 23": CORRECT.** G <= 87 is equivalent to S >= x - 23; at
  exactly 87, S = x - 23. With x >= 24 (Corollary 2.3) this means S >= 1.
- **Observed values: CORRECT.**

  | Circuit | n | G | x | y | h | h + y | S |
  |---|---|---|---|---|---|---|---|
  | MixColumns 88@5 | 32 | 88 | 24 | 16 | 16 | 32 | 0 |
  | InvMixColumns 88@17 (meets the hypotheses) | 32 | 88 | 24 | 11 | 21 | 32 | 0 |
  | small-scale-aes 42 | 16 | 42 | 12 |  |  |  | 2 |
  | lw16-4x4-gf256-inv-had 84 | 32 | 84 | 25 |  |  | 27 | 5 |

  For small-scale-aes, 42 = 32 + 12 - 2. For lw16-4x4-gf256-inv-had, 84 = 64 + 25 - 5.
- **Missed observation.** The MixColumns 89@4 has x = 26, h + y = 31 and S = 1 (the split is
  helpers -9, z_r 4, missing 6). So S > 0 and h + y < n already occur for MixColumns itself.
- **"Disproved: h + y >= n whenever ...": CORRECT, and fair.**
  - As a statement about all circuits of such maps, any single circuit refutes it.
  - It is also refuted in the stronger reading about minimum circuits:
    - small-scale-aes has minimum graph-code weight 6, so c(1) <= 5 and x >= 11 for every circuit.
      Any circuit with G <= 42, including a minimum one, then has h + y <= 42 - 16 - 11 = 15 < 16.
    - lw16-had has minimum weight 6, so c(1) <= 10 and x >= 22. Then h + y <= 84 - 32 - 22 = 30
      < 32.
  - That the counterexamples are constructions does not weaken the disproof.
- **"(2.1) is the F20 ledger in exact form": CORRECT WITH A GAP.**
  - Write (2.1) as G = 2n + x + 2h + q0 - K, where K = sum r_p + z_r + sum over missing labels with
    e_l >= 1 of (e_l - 1).
  - The F20 ledger uses p = hidden values (not the XOR of two odd values) and r = the rank of all
    true four-term relations among the odd values.
  - p <= q0 is immediate. K <= r needs the K edge relations to be linearly independent. That is
    plausible, by the formal-row argument of Lemma 4.4, but the record does not prove it.
  - On the recorded MC 88, MC 89, InvMC 88 and small-scale 42, p = q0 and K = r exactly
    (`sec2_ledger.py`), so the ledger is an equality there.

## Item 3. Section 3

- **Formula (3.1): CORRECT.**
  - Rebuilt from field arithmetic, it equals the repository matrix, and (3.1) matches all 32 rows
    (`sec3_algebra.py`).
  - The derivation also holds:
    - out_c = (b_{c+1} + b_{c+2} + b_{c+3}) + 2(b_c + b_{c+1});
    - xtime of w is w_{j-1}, plus w_7 at bits 0, 1, 3, 4.
- **"Multiplication by 2 + 3y + y^2 + y^3": CORRECT WITH A GAP (the convention is not stated).**
  - It holds with b(y) = sum b_c y^(-c).
  - With the FIPS convention b(y) = sum b_c y^c, the element is 2 + y + y^2 + 3y^3. This was
    checked by program both ways.
  - The structure "1 + (1+y)·unit" holds in both conventions.
- **The rest of the ring algebra: CORRECT.**
  - (1+y)^4 = y^4 + 1 = 0 in R.
  - 1 + (1+y)(3+y^2) = 2 + 3y + y^2 + y^3.
  - 3 + y^2 is a unit, with inverse 70 + 203 y^2 (checked); in general a unit because its value at
    y = 1 is 2 != 0.
- **The flag definition: WRONG.** See summary item 2. Measured dimensions:
  - (1+y)^j R has dimension 32, 24, 16, 8, 0 for j = 0..4.
  - The annihilator of (1+y)^j R has dimension 0, 8, 16, 24 for j = 0..3.
  - The record's W_k therefore has dimensions 24, 16, 8.
  - The block sets {0,t}, {0,d0,d1,t} and "even" equal the annihilator of (1+y)^k R, which is also
    (1+y)^(4-k) R itself, for k = 1, 2, 3.
- **Block descriptions and dimensions 8, 16, 24: CORRECT** for the corrected definition.
- **"MixColumns is the identity on each quotient W_k / W_(k-1)": CORRECT, and it survives
  transposition.**
  - The mask action is mu -> mu M, which is M^T on column vectors.
  - I checked (A - 1) W_k ⊆ W_(k-1) for k = 1..4 (W_0 = 0, W_4 = everything), for both A = M and
    A = M^T.
  - Reason: M^T - 1 = (1 + P) V, where P is the byte rotation and V commutes with 1 + P. The flag
    depends only on P.
- **The family Q_T and D_T: CORRECT.**
  - M2 from the matrix equals the D_T formula (`tools/m2_check.py`).
  - Q_T for a cyclic T is translation-invariant with the 5-element pattern
    {(1,0), (2,0), (3,0), (0,-1), (1,-1)}, checked by inspection.
  - The 26-gate M2 circuit is verified: 26 distinct nonzero gates, correct outputs, split
    16 outputs + 8 producers + 2 helpers.
- **"Observed on 88@5": CORRECT WITH A GAP.** Recomputed independently by `sec3_observed.py` and
  agreeing with `tools/sheets.py` and `tools/levels.py`:
  - the partition is the eight bit blocks;
  - there are 24 producers: 19 input+input, 4 helper+input, 1 helper+helper;
  - every sheet has exactly 2 helpers;
  - there are 16 sums;
  - W_2 contains 10 gate signals (rank 7) and W_1 contains 2 (rank 2).

  The gap is that "extras by sheet" depends on an unstated rule for assigning sums to sheets. With
  forward closure (the sheets of the odd gates reached through even gates), 15 sums go to a single
  sheet or to {3,4}, but one sum feeds sheets {0,1}. The counts 3, 3, 3, 3 / 4 / 16 come out only
  if that sum is credited to sheet 0. State the rule.
- **"The eight-block partition is not unique": CORRECT.**
  - The 89@4 blocks include {0,1,8,9,17,24,25} and {16}.
  - The InvMC 88 blocks include {0,1,17,24} and {8,9,16,25}.
  - Note that the InvMC 88 is a circuit for a different map. For MixColumns the evidence is the
    89@4 alone.

## Item 4. Section 4

- **Quotient by W_2: WRONG in the conclusion, and with a gap in the argument.**
  - The restriction is a circuit for M2. Correct.
  - "At least 16 output gates disappear": correct, because out(0,j) and out(2,j) restrict to the
    same value, as do out(1,j) and out(3,j).
  - "At least rank-many dead gates disappear": unproved, and "rank" is undefined. A gate survives
    whenever its restricted value is new, whatever the rank. On recorded circuits 59, 60 and 53
    gates disappear (`sec4_restrict.py`; 10, 16 and 6 of them lie in W_2). A random search did not
    find a circuit with fewer than 32 (`sec4_naive.py`, `sec4_counter.py`: minimum 47 and 43), so I
    have no counterexample to the count, only no proof of it.
  - The inequality G >= L(M2) + 32 is true in any case, but only because G >= 75 and L(M2) <= 26.
  - "Weaker than 56" is false: by section 1, L(M2) >= 24 (`sec4_restrict.py`: M2 has odd rows and
    columns, minimum graph-code weight 4, c(1) <= 8), so L(M2) + 32 >= 56.
  - **Corrected wording:** "yields at best G >= L(M2) + 32 in [56, 58] (24 <= L(M2) <= 26), far
    below 75, and the count of disappearing dead gates is not proved."
  - The stated reason is accurate. The MixColumns relation out(0,j) + out(1,j) + e(0,j) + e(1,j)
    + e(0,j-1) + e(2,j-1) [+ e(0,7) + e(2,7) for j in {1,3,4}] = 0 has weight 6 or 8. In the
    quotient it becomes out_u + out_v + u_j + v_j = 0, of weight 4.
- **Several evaluation points: OVERSTATED.** Same as item 1c.
- **"h + y = n is forced": CORRECT.** It is disproved by the other maps in section 2, and also
  directly for MixColumns by the recorded 89@4 (h + y = 31) and 97@3 (h + y = 39). The section 2
  counterexample was stated for "h + y >= n"; the 89@4 refutes that version for MixColumns too.
- **The rank of the lower flag levels as a cost: CORRECT as scoped.**
  - The 88@5 spans rank 7 of W_2 and 2 of W_1; the 89@4 spans rank 9 of W_2 and 0 of W_1.
  - So "must span W_2 / W_1" is false, and no bound can rest on it.
  - It does not exclude bounds from a partial-rank requirement. The text does not claim that.

## Scripts

| Script | Checks |
|---|---|
| `lib.py` | Circuit and matrix parsing; F_2 span |
| `sec1_eval.py` | Section 1 exact checks on all recorded circuits |
| `sec1_points.py` | Single-point maximum for MixColumns; LP samples for 2 and 3 points |
| `sec1_dual.py` | Vertices of the dual of the two-point LP |
| `sec2_identity.py` | Hypotheses per map; (2.1) from the definitions on every circuit |
| `sec2_extra.py` | (2.1) without normalisation; minimum graph-code weights; skipped folders |
| `sec2_ledger.py` | (2.1) versus the F20 ledger (p, q0, K, r) |
| `sec3_algebra.py` | (3.1); ring conventions; the flag and its annihilators; quotient action of M and M^T |
| `sec3_observed.py` | The observed 88@5 counts (and the 89@4) |
| `sec4_restrict.py` | Gates that disappear under restriction; L(M2) >= 24 |
| `sec4_naive.py`, `sec4_counter.py` | Search for circuits with few disappearing gates |

The folders qarma64, qarma128 and skinny hold no circuit, so no script tests them.
