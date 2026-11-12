# Independent machine review of tenth-gate/PROOF.md and sharing/INDEPENDENT-SHEETS.md

Review of 2026-11-12 by a second model instance (Opus) that wrote neither text; saved by the main agent
from the reviewer's final message. A machine review, not a human review and not a formal verification.
No SAT and no exhaustive search were used; the tests are checks on given or randomly constructed
circuits and establish nothing universal. Scripts and outputs are in this directory.

## A. tenth-gate/PROOF.md

**Verdict: the proof of the ten-gate lemma is correct.** No counterexample to any step the lemma uses.

Faults found (all repaired in the file):
1. **The "general form" (duality lemma) was false as stated.** Transposition gives
   |T| = K + r - |B| - tau, not K - tau; the proof's count works because |B| = r = 4. Counterexample:
   |B| = 1, r = 2, targets b0 + a0 and b0 + a1: K = 2, while every admissible T needs w1 + w2 and
   tau >= 2, so |T| + tau >= 3. Correct statement: with P without zero row or column,
   L_local = min(|T| + tau) + |B| - r; Steps 0-3 give ">=", transposing T back gives "<=".
2. **Step 4 missed one case:** the first gate can be w_i + w_i = 0. Repair: then each E_c is a copy of an
   earlier odd signal, so the first E_c built would equal an input.
3. **"A six-gate mirrored circuit is rigid (two pair-sums)" is false** (v = w0+w1, E2 = v+w3, E3 = v+w2,
   t = E2+w2, E0 = t+w0, E1 = t+w1 has the even signals w0+w1 and 1111). The proof uses only "at most
   two even signals".
4. **"Both cases are attained" was mis-attributed:** the schemes attain tau = 3; the case tau = 4,
   |T| = 6 is attained by six gates for the E_c and four entries.

Step by step: Step 0 sound (targets are nonzero on b, never deleted; targets that are entry gates or
ancestors of targets, zero or repeated phi, entries on a unit need nothing special). Step 1 sound.
Step 2 sound (tau = 3 makes the zeta a basis of the even space). Step 3 sound (Lemma 3.1 needs only
d_v >= 1; the count is right; each a(v) is a signal of T by reverse induction; a(z_i) is literally the
signal a(eps_i); zero adjoints are harmless). Step 4 sound with the gap above. Step 5 sound.

Corollary (a sheet with nothing free costs 12): correct. The 8-gate circuit was transposed by program:
12 gates computing exactly the rows (E_c | s_c).

Tests, no discrepancy: all 12 recorded schemes with 20 random carrier choices each gave
(K, tau, |T|) = (10, 3, 7); the trivial circuit (10, 4, 6); 1,600 constructed sheet circuits containing
every edge case (phi = 0, repeated phi, x + x gates, zero and duplicate gates, targets that are entries
or ancestors of targets, zero and repeated zeta) satisfied the Step 1 value formula, (*), d_v >= 1,
|T| = K - tau, the adjoint identities, |T| >= 6, |T| >= 7 when tau = 3, and K >= 10.

The obstruction in the reviewer's words: mirrored, an entry is the set of targets it reaches (mod 2), and
that set must appear as a partial sum of the b-circuit read backwards. The a-parts force these sets to
span the even space. At its optimum of 6 gates the backward b-circuit has only two even partial sums, so
the circuit pays either a fourth entry or a seventh gate.

Further results by the mirror:
- **Theorem 9.1 (three-term sheet, 13 gates) by hand without the ten-gate lemma** (argument now in
  PROOF.md); tested on the recorded 13-gate circuit, 200 lifted ones and 600 random circuits. The same
  argument gives at least 3r + 7 for r independent free blocks.
- **J_01 >= 21 for block-monotone circuits, conditional on one finite fact (SL):** a sheet-0 circuit
  containing three diagonal gates [0: sigma_i] + [7: sigma_i] with the sigma_i a basis of the even space
  has at least 11 gates. SL is exactly the 8 UNSAT instances of REPORT-PART2 II.4 (SAT, no certificate);
  by hand only its tau = 4 case is done. Argument: let D_1 be the gates nonzero on block 1 and G_0 the
  gates zero on block 1 that meet block 0; J_01 >= |D_1| + |G_0|, |G_0| >= 10; the mirror applied to D_1
  with everything zero on block 1 free gives |D_1| >= 10, and if |D_1| = 10 then D_1 reads three such
  diagonal gates; if all three serve sheet 0 they lie in the sheet-0 circuit (then SL), otherwise one is
  an extra gate of G_0.

## B. sharing/INDEPENDENT-SHEETS.md

**Verdict: Theorems 1 and 2 are correct; nothing needs repair.**

Theorem 1: (H) implies (*): sound. Step 3: sound (the adjoint of an own-block unit depends only on the
own parts; the count is right because there are 4r own units and 4r targets). Step 4, line by line:
PROOF Lemmas 2.1-2.2 are inductions over gates needing only unit-vector inputs, so zero, repeated,
unused and x + x gates of T are harmless; exports that are inputs or zero are covered; the shape claim
holds when blocks are shared between groups; (2) holds (each block outside V contains a whole unsplit
group; kappa = 0 when V is empty); beta_P(DE) is the span of the edge vectors, of dimension |V| - kappa;
o >= |V|. (3) and Step 5 correct.

Theorem 2: the restriction step is right (a gate of A outside D has zero own part, so after restriction
it lies on F, and every vector on F is free in the model). Checked against the matrix by program:
conditions (i), (ii) for MixColumns J = {0,2,4,6}, {1,3,5}, {7} and for the even and odd sheets of Q_8;
each restricted own part is exactly E_c; (H) holds.

Small points: the three MixColumns families can overlap, so "the 80-charge count regrouped" is not a
total; D_J includes gates charged to no single sheet of J, so the theorem does not bound the union of
the per-sheet sets.

Numerics (read-only), minimum |D_J|: recorded 88: 41, 34, 10; 89: 41, 35, 10; 97: 44, 39, 11; kste
block-monotone (4,300): 40, 31, 10; kste non-monotone (14,638): 41, 32, 10; hunt records: 40/41, 31/32,
10. Q_8 (two circuits): 40 for the even and for the odd family. Nothing below 10|J|. The corpus never
tests the theorem's actual claim: no corpus circuit has a gate serving two sheets inside one family.
The full Steps 0-5 ran without failure on the restricted circuits of 3,871 corpus circuits and on
random families with r = 1..3 whose free parts were mixed by random invertible maps.

Files: mirror_lib.py, test_lemma.py and test_lemma.out, features.py, dj_check.py and dj_check_full.out.
