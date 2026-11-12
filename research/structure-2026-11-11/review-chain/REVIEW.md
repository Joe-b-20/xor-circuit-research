# Review of the uniform chain argument (chain/REPORT.md sections 1-2, RECORD 16)

Independent machine review, 2026-11-12 (phase 3). The reviewer was a separate model instance (Opus) that
did not write the reviewed text; briefed to challenge, not confirm. Saved by the main agent from the
reviewer's final message, with light formatting. Not a human review and not a formal verification. The
only program (`mirror_check.py`) checks the mirror form on hand-built circuits; it proves nothing.

**Verdict.** No counterexample found. Theorem 1 (M_l >= M_(l-1) + 9, hence M_l >= 9l + 2) and Corollary
16.2 are correct as stated, given M_1 = 10 and M_2 = 20, which were reviewed earlier and are proved for the
abstract mirror-form minimum (any circuit containing the required vectors with the export span), not only
for mirrors of actual circuits; that is the form the induction needs. The repairs are wording and
bookkeeping; the proof does not change.

## Item 1. Mirror form and translation to full circuits: correct, three small gaps

- Count: K gates, tau entries, z_i read once; reads 2K + 4l, signals 4l + tau + K, each read at least once
  (own units appear in some target's own part; gates are ancestors; z_i read by its entry); |T| = K - tau.
- Required vectors: adjoint of unit c of block b_k = E_c on w^k + p_c on w^(k+1) (k < l), E_c on w^l for
  k = l; weights 3 or 5, so they are gates.
- Export condition: only sheet 1 has a free part; Phi l_(1,c) = s_c and Phi l_(k,c) = 0 for k >= 2, but the
  l_(k,c) need not vanish, so zeta_i may be nonzero on groups 2..l. The left kernel lies in
  {x : x on group 1 is 0 or 1111}, so Even(w^1) + 0 is in the span of the zeta. "A space containing
  Even(w^1) + 0" is exactly right; the proof never assumes exports on group 1 only.
- **Gap 1a (wording).** K = |T| + tau for the cleaned circuit (K >= |T| + tau originally). M_l is defined
  as the mirror minimum (REPORT 1) and as the local minimum (RECORD 16); they coincide by the duality lemma
  (|B| = r = 4l); only "local minimum >= M_l" is needed.
- Restriction (Q_m): with block 0 free, the gates that are ancestors of an output of sheets 1..m-1 and
  nonzero on blocks 1..m-1 form a local circuit with unchanged values (operands: counted gates, own units,
  or vectors with zero part on blocks 1..m-1, i.e. on block 0, free). L(Q_m) >= M_(m-1) >= 9m - 7.
- **Gap 1b.** "Ancestor of an output" must include the output gates themselves.
- **Gap 1c (MixColumns runs).** Sheets 1..6, block 0 free, block 7 zeroed: exactly a chain of six, >= 56,
  correct. Sheets 5, 6, 7, 0 with block 4 free: the report does not say what happens to blocks 1, 2, 3; left
  alone, an operand could be a vector on blocks 1-4 with zero own part, which is not a base signal of the
  model. **Repair:** set blocks 1, 2, 3 to zero (sheets 5, 6, 7, 0 do not involve them). Then >= M_4 >= 38.
- Arithmetic of Cor. 16.2 confirmed: 9m - 7 exceeds 7m - 1 + ceil(16m/11) for m >= 13, equal at 11, 12
  (92, 101), smaller at 10 (83 against 84).

## Item 2. Lemma 1 (f + tau >= M_(l-1)): correct, one repair

A gate with omega != 0 is an entry (duplicate), or has both operands in one fibre (then omega = 0), or is a
first gate with operands in two different fibres. Fibre roots precede the operands, so R is well ordered;
R has f gates with distinct nonzero values containing every occurring omega; the shorter chain's required
vectors are there (level l-1 projects to E_i on w^(l-1)).
- **Gap 2a.** An export with omega = 0 projects to 0, not to a signal of R. Repair: drop such exports;
  tau' <= tau remain and still span Even(w^1) + 0, so f + tau >= f + tau' >= M_(l-1).

## Item 3. Lemma 2 (D + N >= 9): correct; the D = N = 4 case closes more simply than cited

- e >= 3 (s-parts of omega != 0 signals are label sums; the p_i span Even(w^l)); D >= e.
- e = 3: labels a basis of Even(w^l), nonzero even, hence pure gates distinct from the odd E_i: N >= 7.
- e >= 4, D = N = 4: every duplicate is an entry, fibres are trees with four edges in all; pure signals are
  the units of w^l and the four E_i, all odd; each E_i is an exit along a tree path of odd length; length 1
  repeats a value, length 5 needs five edges, so all four paths have exactly 3 edges and are different. A
  forest with four edges has at most two 3-edge paths (sum over edges xy of (deg x - 1)(deg y - 1): path 2,
  chair 2, star 0; disconnected fewer). Impossible, with no time order and no use of the label identities.
- The cited argument (sharing/REPORT.md Lemma 3.2) is also correct and uses only the last level.

## Item 4. Hidden l = 2 properties: none found

Lemma 2 uses only the last group and the level-(l-1) s-parts; Lemma 1 only the definition of M_(l-1).

## Confirmed statement

For a chain of l >= 2 adjacent sheets (block j-1 free, nothing else free) every local circuit containing
the 4l targets has at least M_(l-1) + 9 gates; with M_1 = 10, M_2 = 20: M_l >= 9l + 2. In every circuit for
Q_m (m >= 3) at least 9m - 7 gates are ancestors of an output of sheets j+1..j+m-1 (outputs included) and
nonzero on one of their own blocks. MixColumns: sheets 1..6 (block 0 free, block 7 zeroed) at least 56;
sheets 5, 6, 7, 0 (block 4 free, blocks 1-3 zeroed) at least 38.

## Over-claims and notes

None in sections 1-2 or Cor. 16.2. The tight-case description of chain/REPORT section 3 is outside this
review. The D = N = 4 step is correct but terse; the 3-edge-path count is a one-line replacement.
