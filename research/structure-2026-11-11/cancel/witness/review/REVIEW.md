# Review of SUPERPOSITION.md (phase 9)

Independent machine review (separate model instance; not human review), 2026-11-12. Own code only (`rev.py`,
`rev2.py`, `rev3.py`, `rev4.py`; outputs `rev*_out.txt`), with my own MixColumns matrix
(out_c = 2a_c + 3a_(c+1) + a_(c+2) + a_(c+3), 0x11b), construction and transposition. The author's JSON circuits
and the recorded circuits/aes-mixcolumns/*.circ.txt were loaded as data. Method: direct evaluation of specified
circuits and hand reasoning; no SAT, search, enumeration or minimisation.

## 1. Witness circuits and the rebuild: CORRECT WITH FIXES
- Both JSON files compute MixColumns; all gate values distinct, nonzero, not inputs; fully live; outputs have
  fan-out 0. wire: G 616, block: G 521. Both: |F_j| = 38 38 34 30 26 22 18 14, union 66 = 34 non-output + 32
  outputs, E 140, R 154, U 550 / 455. All as claimed. Dual identity: sum_v (d(v) - 1) = G for both; max input
  fan-out 22.
- Own rebuild (rows in sorted order): wire 616, block 521 (identical numbers), reverse-wire, 5 random global input
  orders (G 624-645) and 5 random per-row orders (G 704-705): union 66, E 140, R 154 in every case.
- Fix (a): "66 does not depend on the order" is FALSE without a proviso. The remainder supports contain output
  supports in 36 (remainder, output) pairs, so an order can make a remainder prefix equal an output. Explicit
  orders (rev2.py, rev3.py): r_(0,0) chain started with supp(y_(1,7)) gives union 69 (G 515); r_(3,0) chain
  reusing the earlier output y_(0,7) gives union 86 (G 518). Correct statement: union = 66 for every order in
  which no remainder-chain value equals an output value (created or reused).
- Fix (b): the naive "reuse a value already present" can leave dead gates when a later prefix already exists
  (reverse-wire order: 4 dead gates, e.g. [25..29] whose successor is the z_3 prefix [24..29]); prune them
  (G 612, union 66). Liveness is not automatic; it holds for the two committed circuits.
- Fix (c): build_witness.py's "no intermediate equals a target" assertion runs only when a NEW gate is created
  (it returns early on reuse), so it does not detect reuse of an existing output. The committed circuits are
  unaffected (output fan-out 0, checked here); the text should not cite the assertion as covering this.

## 2. Proposition S, hand proof: CORRECT WITH FIXES
- Global part correct: each z_c chain gate is an ancestor of z_c, hence of the three H_(c') (c' != c) via a, b, and
  each H_(c') of y_(c',0..7), so of rows of all eight sheets; it is nonzero on some block. Outputs: own part E_c.
- Remainder part correct under the proviso of 1(a): along disjoint-support gates, ancestors have support inside
  the node's support, and a remainder gate can be an ancestor of a row (c',k) only through r_(c',k) (H's ancestors
  are global), whose support misses block k. Reuse of remainder gates across chains and of z prefixes (12 gates of
  the wire witness read a z prefix) is handled. The gap: "a reused node is itself such a gate or a global" omits
  outputs, and "the ancestors of y are H and r" presumes y was created as H + r. Add the hypothesis "no remainder
  chain value equals an output value", which then must be checked per order (true for wire and block).

## 3. Rotation model Q_m: CORRECT
Rebuilt (rows E_c on block j, S_c on block j-1; block order): Q_4 G 141, union 34 = 18 + 16 = 8m + 2, E 36, R 42,
U 107; Q_5, Q_6, Q_8: G 218, 307, 521, union 42, 50, 66. Hand count 4(m-1) + 6 + 4m agrees.

## 4. Consequences and wording
- Refutation scope: CORRECT WITH FIXES. The phase-7 conjecture and Conjecture G (MixColumns; Q_m, m >= 4) are
  refuted as stated (all circuits). Add to "not refuted": every form restricted by size or by U (e.g. union >= 80
  for circuits with G <= 88, or with U <= u_0; no circuit here violates union + lambda U >= 80 for lambda >= 14/455).
  The witness has G >= 515 in every order tried, so it says nothing about near-minimal circuits.
- "Any lower bound on |union F_j| valid for all circuits is at most 66" (8m + 2 for Q_m): CORRECT.
  "No argument that bounds L through the distinct charged gates alone can improve the current bound":
  OVERCLAIM as worded; true only for unconditional bounds on |union F_j|. Rephrase: "no lower bound on
  |union F_j| valid for all circuits exceeds 66; a charge argument for L must use a size/U hypothesis or bound U".
- Theorem K compatibility: CORRECT WITH FIXES. All non-output gates are disjoint-support sums (checked on both
  files) and outputs have
  fan-out 0, so on every path from a global to a row the output gate is the only exit at all. B(r_(c,j)) = all
  blocks except j (7 blocks; block parts on W_j \ {j} are E_c + S_c != 0), windows have <= 3 blocks, so r is not
  confined; if k is in W_j there is no chase exit on that side at all (say so). Fix: in the wire witness some
  paths from a global run g -> z prefix -> remainder chain -> r -> y; there the off-path operand is H_c (8 blocks,
  also non-confined), not r. Conclusion (K is vacuous here, no plain charged closure) unchanged.
- Three interpretive corrections: CORRECT (consistent with CANCEL.md section 2: confinement is support-only, its
  converse example "charged + exit-free path => confined" holds; corollary (b) already says "non-confined or
  escape"; the per-pair scope is in the K text). The bare-E-sheet remark is correct (E_c on one block costs 6).
- Lemma S1: CORRECT (trivial: e's block-c part 0 forces a'_c = a_c).
- Table: "U >= 455" should read "U = 455 (block), 550 (wire)"; it is not a bound over orders (an order with a
  prefix hit gives U 446). Other entries consistent (R - E = 14; Q_m: 2m - 2).
- Dual identity: CORRECT; the identity itself holds for every circuit with 32 distinct output nodes; full
  liveness and used inputs are needed only for "C^T has sum (d - 1) gates". G(C^T) = G(C) is CORRECT for the raw
  transpose, which is in general NOT reduced: reader-order transposes have 181 (block) and 138 (wire) duplicate
  gate values; deduplicated they have G 339 / 478 and union 314 / 470.
- Transposition numbers: REPRODUCED but CHAIN-ORDER DEPENDENT (my transposition; sheets b of M^T, rows x_(k,b),
  own block b; M^T windows {b, b+1}, and {7, 0, 1, 3, 4} for b = 7, girth 4 via 7->6->5->4->7):
  block witness: reader order 495 (= author), reverse order 66, random orders 231-339;
  wire witness: reader 608 (= author), reverse 72, random 303-389. G = 521 / 616 in all.
  Dual test reproduced: construction for M^T (wire order) G 598, union 66; its transpose for M: reader 590,
  reverse 72, random 354. Recorded circuits (rev4.py): 88: C 85, C^T 82-87; 89: C 86, C^T 84-87; 97: C 94,
  C^T 87-94 (over 7 chain orders) - "81-86 on both sides" holds for the reader order only.
- "In these examples the work uncharged on one side is charged on the other": WRONG as a property of the
  examples; it is a property of the reader chain order. The reverse-order transpose of the block witness is
  itself a superposition circuit for M^T (union 66; deduplicated: G 495, union 66). Keep "charging is not
  invariant under transposition, while G is" only as: |union F(C^T)| is not determined by C (66..495 for one C),
  while G(C^T) = G(C) for every raw transpose.
- Open question: CORRECT WITH FIXES. The implication to L >= 80 is valid (raw transposes, G(C^T) = G(C), minimal
  circuits are live). But "no circuit superposing on both sides has been tried" is outdated: for a fixed
  transposition both sides at 66 already exist (block witness, reverse chains). Only the existential form over
  all chain orders survives, and the next-direction test must defeat every chain order, not one. The Q_3 remark
  (28 < 30 on both sides) is trivial (union <= G = 28) and is no evidence about the mechanism. The question is
  stronger than L >= 80 (it must also hold for large circuits), so refuting it would not affect L.

## Most important fixes
1. Proposition S / "66 independent of order": add the proviso "no remainder-chain value equals an output";
   counterexample orders give 69 and 86.
2. Restate the consequence: only unconditional bounds on |union F_j| are capped at 66; size- or U-restricted
   charge statements are untouched.
3. Transposition: report the chain-order range (66..495, 72..608) and drop "uncharged on one side is charged on
   the other"; the open question is meaningful only existentially over chain orders.
