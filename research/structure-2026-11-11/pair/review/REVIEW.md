# Independent machine review of pair/PROOF.md

Review of 2026-11-12 by a second model instance (Opus) that did not write the proof; saved by the main
agent from the reviewer's final message. A machine review, not a human review and not a formal
verification. No SAT and no exhaustive search over circuits; the scripts check two small algebraic or
graph-theoretic lemmas completely and test inequalities on recorded and randomly perturbed circuits,
which establishes nothing universal about circuits.

**Verdict: the theorem (pair minimum at least 20) stands as proved.** No error in the mathematics. One
wording gap (item 1). The informal section 5 over-claimed in five places, one sentence being false.
All of this is repaired in PROOF.md.

1. **Normalisation and fact (E): CORRECT WITH GAP.** "Let its readers read the earlier signal" does not
   cover a zero gate. Repair: drop a zero gate (from the exports too); each reader 0 + x equals x and
   goes by the duplicate rule; |T| + tau strictly decreases; the A_i, B_i are never zero. (E) is correct
   and does not need minimality.
2. **Lemma A and the use of Steps 0-3: CORRECT.** No gate with omega != 0 has two free operands, so
   cleaning only deletes non-ancestors and K_c <= f + D. Entry gates are exactly entries of T. Every w_i
   is read (three targets contain it); each z_j is read once; the count (2 K_c + 4) - (4 + t + K_c)
   holds for every summation order. a(g_j) = a(z_j) = zeta_j, Phi l_i = p_i, the labels span a space
   containing Even(w'). Readers with omega = 0 are correctly left out of the adjoints.
3. **Lemma B: CORRECT.** Brute force over all 20,160 ordered bases of F_2^4, computing zeta from the
   inverse of Phi: 0 failures of any statement. For o = 4 there are 7 possible zeta-sets.
4. **Steps 1-3: CORRECT.** The case split is exhaustive (t >= 6 gives D + N_0 >= 10; t = 5 is (X); t = 4
   is (Y) or K >= 20). In (Y), f + D = K_c means cleaning deleted nothing, so every entry is clean;
   f >= 7 from (I) with tau = 3, hence at most one non-entry duplicate.
5. **(*) and odd labels: CORRECT.**
6. **Configuration (Y): CORRECT.** Both bullets hold (in the second, the single remaining contribution
   may be the terminal input, excluded because zeta_j + zeta_k is not a unit). The fibre structure is
   complete. The cross-sum parity argument is right and also covers D = 4. No missed fibre structure
   found.
7. **Configuration (X): CORRECT.** Classification by brute force: exactly 6 trees with five edges, with
   3-edge-path counts 0, 3, 4, 3, 4, 3; the two with 4 are the double star and the 2,2,1 spider;
   disconnected forests have at most 2. The 5-path case, the spider and the double star arguments hold.
8. **Section 5: OVERCLAIMS** (repaired): (a) the vanishing/coinciding of traces was misattributed (a
   trace vanishes when exactly one label is odd, two coincide when exactly two are odd; three odd labels
   already force four traces); (b) in the tight case exits do exist as cross sums, the contradiction is
   parity; (c) the double star fails by parity, not by time order; (d) "pays only if the difference
   collects three or more vectors" is not proved as a primal statement; (e) "the first sheet has to
   supply the four adjacent pair-sums" is wrong in general: labels u_0, u_1, u_2, E_0 give the traces
   1100, 1111, 1010, 1001; only one of the seven possible sets consists of adjacent pair-sums.

**Numerical tests (examples, not proof).** 22 recorded pairs (MixColumns 88 on (1,2)..(7,0); q3_28,
q4_40, q8_80 on all pairs), each under the fixed order and 20 random orders: |T*| = K_c - t,
a(g_j) = zeta_j, f + D >= K_c >= (distinct nonzero even zeta) + 4 + t, D >= entries >= t,
N_0 >= 4 + distinct even labels, and Lemma B's count wherever the labels form a basis: all hold.
K = 21, 25, 24, 20, 20, 20, 21 (MixColumns 88); 23, 24, 24 (q3_28); 20 everywhere on q4_40 and q8_80.
800 randomly perturbed pair circuits: 0 failures, minimum K = 20. No tested circuit has N_0 = 4, so
configurations (X) and (Y) themselves were not exercised numerically.

Scripts (this directory): p1_algebra.py, p2_circuits.py, p3_perturb.py.
