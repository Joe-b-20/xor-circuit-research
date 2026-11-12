# Review of joint/ACCOUNT.md (J1-J9, census, caps, conjecture) and FINITE_AUDIT.md section 3

Machine review by a separate model instance (Opus 5.5), 2026-11-12. Not human review. Own code only (rvlib.py:
MixColumns from out_i = 2a_i + 3a_{i+1} + a_{i+2} + a_{i+3} mod 0x11b; rv_checks.py, rv_caps.py, rv_extra.py,
rv_constructions.py, rv_edge.py; outputs *_23.txt, constructions.txt). Sample: recorded 88/89/97 (output labels
y_(8b+r) checked against our rows) and every 23rd line of each kste file: 826 valid reduced circuits (824 of 88
gates; 13 sampled lines of circuits_2.txt are not MixColumns circuits and were skipped). Plus lw0..lw7, W*
(wstar.json) and my own rebuild of the lowwasteB carrier construction for every B, |B| <= 4 (162 circuits).
No SAT, no search; read-only scans and checks of explicit circuits.

## 1. Proofs

- **J1 CORRECT.** Uses reducedness (|Sigma| = G + 33), which is the global hypothesis. Verified on all 826 + 45
  circuits for every B with |B| <= 2.
- **J2 CORRECT.** Readers have one block-b operand (two would put g in V_b or make it 0); a pure-b gate reading a
  pure-c value has its other operand on exactly {b, c}; so lambda <= 2. Wording: in the description of N_b,
  h ranges over earlier gates AND surviving inputs (category I). Checked: L_b is inside the removed set, lambda <= 2.
- **J3 CORRECT** (fibre formula asserted for all 28 pairs; recorded 88 adjacent overlaps -2,1,-1,0,1,0,1,-1
  reproduced). The sentence "Locally, the double-counted gates are the lambda = 2 gates" is a heuristic (fibre
  terms also come from nonlocal coincidences and negative terms); label it so.
- **J4 identities CORRECT** (both asserted). **Consequences: fixes needed.**
  (b) "The only new content of all eight together is the correction ..." is wrong in substance: J4 is exactly the
  sum of the eight one-block identities G = U_b + |L_b| + N_b + dead_b, and lambda_2 - lambda_0 = sum_b |L_b| - G.
  So 7G >= sum K_b + lambda_2 - lambda_0 IS the average of G >= K_b + |L_b|: it has no content beyond the single
  blocks (and says nothing about the pair/triple information of J3). "No lower bound valid for all circuits" is
  trivially true (pad with dead gates); the relevant statement is: the trivial lambda_2 - lambda_0 >= -G gives back
  8G >= sum K_b, and W* shows lambda_0 can be 196 of 263 (verified: lambda_0 = 196, lambda_1 = 66, lambda_2 = 1).
  (c) "each gate removed exactly once" is right but needs its one-line reason (removal is monotone in B: equal
  images stay equal under further zeroing). "every combination of block-zeroing identities is a sum of such
  increments" should read "every D_B is a sum of increments along a chain; linear combinations of the D_B (e.g.
  J3's overlap) are SIGNED combinations of increments".
- **J6 CORRECT** for reduced circuits (zero-valued gates would lie in V_b without being pure and break the split;
  for non-reduced circuits define R_b as non-pure gates with a pure-b operand and sum over edges). Rows meet >= 2
  blocks (recomputed), so every path leaves the pure-b set; the first leaving edge is unique; omega' counts exactly
  the pure-internal prefixes even when a pure-b gate has non-pure operands; rho counts paths to the row NODES, also
  through other row nodes. Verified (all 8 blocks, all 4 units) on 871 circuits, including 31 corpus circuits and
  W* that have pure gates with a non-pure operand and 824 corpus circuits whose outputs are read by later gates.
- **J7 CORRECT.** Sheet ranks 7 (b < 7) and 16 (b = 7), total 65, recomputed; bound asserted on all circuits.
- **J8 CORRECT.** Own windows: {0,7},{0,1,7},{1,2},{2,3,7},{3,4,7},{4,5},{5,6},{6,7}; of the 28 pairs only {0,1}
  ({0,7}) and {3,4} ({3,7}) meet in >= 2 blocks; none of the 56 triples does. Corollaries correct (shared
  readers are non-pure with b in their support, so b in {0,3,7}; R_7 >= 4+3+3; no double charge). Could be
  sharpened: a pure-b gate serves only sheets whose window contains b. Asserted on all 172 sampled monotone circuits.
- **J9 CORRECT** (checked: for every outside-shared gate, no path to the sheet avoids exits). Fix the follow-on
  sentence "J8 shows exactly which sharing is free of it" to: "a gate with an exit-free path to a row of sheet j
  and one to a row of sheet k has support inside window(j) n window(k)" (J8 itself is about monotone circuits).

## 2. Numbers (stride 23; authors used 25)

- N = sum_b N_b per circuit: 0:30, 1:94, 2:451, 3:205, 4:30, 5:15, 6:1. Dead (summed over b): 0:815, 1:11.
  sum_b D_b - G: -4..16, mode -2 (450). ACCOUNT section 1 description holds.
- Census: 172 block-monotone circuits, all share multi-block gates only as J8 allows and all use both
  ({0,7}, sheets 0,1) and ({3,7}, sheets 3,4). 654 non-monotone: 620 have exactly three {1,2} gates serving
  sheets {1,2} and one {2,7} gate serving {1,3} outside the window intersections; 34 have none; no variant in my
  sample (the authors report one). Shared-delivery types: block 0/{0,1}, 3/{3,4}, 7/{0,1}, 7/{3,4} (all 826);
  7/{1,3} and 1/{1,2} (the 620); the authors' single 2/{2,3} not in my sample. **Omission:** the census counts only
  gates with >= 2 blocks; in all 620 triangle circuits one PURE block-2 gate also serves sheet 1, whose window
  {0,1,7} lacks block 2 (exit-mediated sharing by a pure gate; rv_extra.py). Monotone circuits: none.
- lw7: D_7 = 6, D_2 = 52, four diagonal units [2:e_c 7:e_c] each serving sheets 0,1,3,4,7 (block 2 lies in the
  window of sheet 3 only, so it is cancelled for four of them): confirmed. lw4: 5 charged gates of F_4 removed at 4.
- Caps (min U_B + min D_B over 997 explicit circuits): |B|=1 max 82 (authors 83, smaller sample), witnesses of
  least D_b are constructions/lw (waste 5-6); |B|=2 max 85 at {4,5},{5,6},{1,2}, all least-D witnesses are
  constructions (own D_B 11-28, 160-185 gates); |B|=3 max 88 at {4,5,6} (min U 57 and min D 31, both the recorded
  88), but for 46 of the 56 triples the least-D witness is still a construction; |B|=4 max 87, all 70 least-D
  witnesses corpus circuits. All constructions (152-229 gates) and W* compute MixColumns and are reduced.

## 3. Scope and wording (ACCOUNT.md)

- J4(b), J4(c): see above. Triage row "all eight blocks together ... equals averaging plus lambda_2 - lambda_0":
  replace by "is averaging (lambda_2 - lambda_0 = sum_b|L_b| - G)".
- J5 "from |B| = 3 on, the circuits with least known D_B are the cheap ones themselves": false at |B| = 3 except at
  10 triples (incl. {4,5,6}); true at |B| = 4. "the difficulty moves from the restricted map to the removed part"
  is interpretation; state instead "for |B| >= 3 the known circuits no longer cap the form below 88, and any
  further use needs a lower bound on D_B for circuits with <= 87 gates". State caps as sample-dependent ("at most
  83; 82 on a larger sample").
- Section 3/4 "the only sharing that uses an exit is the triangle": add the pure block-2 gate and the authors' own
  variant circuit; "Pure single-block values can be shared freely" holds only among sheets whose windows contain
  the block (a pure-2 gate reaches sheet 1 only through an exit).
- **Conjecture: fixes needed.** (i) Words and formula disagree: "charged gates number at least 80" is distinct
  charged >= 80, but the formula with "+ (uncharged gates)" is G >= 80. Pick one (both hold on my sample; least
  number of distinct charged gates 82). (ii) "mechanism-supported" overstates: J8/J9 show double service needs an
  exit, not that an exit costs; RECORD 15/17 are about P(j,j+1) (ancestors nonzero on either own block), not the
  F-form, and in the F-form pairs DO gain: |F_1 u F_2| = 19 < 20 in 166 of 826 sampled circuits (e.g.
  circuits_2.txt:783: |F_1| = |F_2| = 11, three double charges). Label: "conjecture; holds on all sampled
  circuits; no proof mechanism". (iii) The line-20 example: with ACCOUNT's own definition, |F_j| = 11,12,11,11,13,
  10,10,10, the three double charges (g55, g74, g76) lie in F_1 n F_2, |F_1 u F_2| = 20, P(1,2) = 21, 3 uncharged
  gates. So the over-charges of F_1 and F_2 alone (2 + 1) already cover the three double charges: line 20 refutes
  only the P-form principle (21 < 23), and "the compensation is spread over F_1, F_2 and F_3" is not shown by it
  (F_3's +1 is not needed). compose/tri's table (F_3 = 14, "0 in no family") uses famstat.py's ENLARGED F_3
  ({2,7} ancestors of sheet 3 added), not the definition used here, and its "+1 for F_3" is relative to a
  monotone reference circuit. The right example for F-form non-locality is circuits_2.txt:783 (F_1, F_2 over-charge
  2 < 3; the slack comes from F_0 +1, F_3 +2, F_4 +1 and 5 uncharged gates). Rewrite the "Missing argument" and the
  "Single best next direction" paragraphs accordingly ("its only realised form" also ignores the variant).

## 4. FINITE_AUDIT section 3, "exactly 10" lower bound: CORRECT WITH FIXES (no wrong step; gaps to write out)

The argument is sound: every gate value lies in {E's, Z's, v}, so (independent of order) the first E is a sum of
two values from inputs, Z's and v; without v the W-weight is <= 2; v, built before any E, has W-weight <= 2, so
v in {W_a + W_b, W_a + W_b + X}; the two cases kill E_a, E_b. Lines to add: (1) the z = X option (v = E + X has
W-weight 3) and z = W_i with i not in E (weight 4) are excluded; (2) in case v = W_a + W_b, E_a is not v + input or
v + Z (v + W_i contains W_a, v + Z_i and v + X contain X), so only E_a = E_b + v remains; (3) in case
v = W_a + W_b + X the sentence "E_a + v and E_b + v have weight 3 plus X, E_a + E_e is a pair with no X" should
read: "E_a = E' + v needs E' = E_a + v = E_b + X, not an E; v + Z_i contains W_a or equals W_b; v + W_i and v + X
are not E_a"; (4) say that the 9th gate may be 0, an input or a copy of a required value: then it is not before
the first E or has W-weight <= 2, so the same argument applies (a copy of an E reduces to the 0-others case).
The upper-bound circuit (x = W0+W1, y = W2+W3, four E's, four Z's) is correct.

## Verdict list

J1 CORRECT; J2 CORRECT (wording of N_b); J3 CORRECT (mechanism sentence = heuristic); J4 identities CORRECT,
consequences (b), (c) CORRECT WITH FIXES (J4 is the average of the one-block identities, no new content);
J5 CORRECT WITH FIXES (|B| = 3 witness sentence false); J6 CORRECT (reduced circuits); J7 CORRECT; J8 + corollaries
CORRECT; J9 CORRECT (follow-on sentence); census CORRECT WITH FIXES (pure block-2 gate omitted; variant);
conjecture statement and support WRONG AS WORDED (formula/words mismatch, F-form pairs gain, line-20
compensation claim); FINITE_AUDIT hand proof CORRECT WITH FIXES.
