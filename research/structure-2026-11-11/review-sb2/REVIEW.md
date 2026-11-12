# Review of compose/sb2/REPORT.md (SB' counterexample, Lemma 2.1*, SB*, O2, Path Lemma, Lemma H, Q')

Independent machine review, phase 4 (2026-11-12), separate model instance (Opus, high effort), with its
own evaluator `ev2.py` (no reuse of mcheck.py or sbcheck.py). Saved by the main agent, condensed. Not a
human review.

**Verdict.** No proved statement is wrong. Lemma Q' has a wrong proof sketch for a true statement; the Path
Lemma's general distinctness claim has a gap, but its use in (3,8,0) survives; several over-claims.

1. **Counterexample to SB': correct (own evaluator).** sbx5_mc3.txt reduced (42 distinct nonzero signals),
   all 12 required vectors, P1, P2, P3 span Even(w^1) + 0; f1 = 8, h1 = 0, tau = 3, near1 = 11, e1 = 5,
   |P| = 24, far1 = 29, cost 40; label rank 5, tau_min = 5, sigma = 0; one exit X = g1_1 + n4 = u1 + u2 with
   all 5 labels before it; exact search L_near = 3, beta = 2: SB' fails (1 >= 2 false). chi = 5 exactly
   (every R has |R| >= 3 and tau_R >= 3; the stated R attains 5), so SB* holds. The exit is read by nothing
   in the file; replacing it by a used gate e3 = X + g2_0 keeps every property. Traces by hand:
   zeta1 = zeta2 = 0011, zeta3 = zeta4 = 0110, zeta5 = 1100; free adjacencies at n1, n3, one non-free at n2
   (also read by A3): the single spare T* gate, as stated.
2. **Lemma 2.1* and SB* => M_l = 10 l: correct.** Exporting R-values is legitimate (an MC_(l-1) circuit may
   export any of its signals); chi depends only on Lambda, S and entry/exit timing (one-sheet statement);
   SB' implies SB* (chi - e1 <= beta - sigma), so S1, S2 (repaired) and O2 give SB*; e1 = 3 via Theorem 4.1
   (and SB* follows there too); no exits: chi = tau_min <= e1; P' need not be reduced.
3. **Theorem O2: correct** (Lemma Q suffices, Q' not needed). Weight-1 exits are excluded silently by the
   Theorem 4.1 argument (reducedness plus independence). The proof gives chi - e1 <= 1 for every near1.
4. **Path Lemma: case analysis correct; distinctness claim has a gap; (3,8,0) conclusion holds.** For a stack
   whose lower entry has one other reader r, the forced value a(r) is carried at the end of r's
   single-reader chain, and two chains can end at the same node; a forced value can also equal a required
   trace when zeta_j + zeta_k = zeta_m. In (3,8,0) (traces A, A, B, C) the forced values 0, A+B, A+C, B+C are
   not required; every bad path (length 4, or length 3 without both labels 1 and 2) has two non-free
   adjacencies with different forced values (9 gates against at most 8); the only path where the gap would
   matter, 1-4-2, contains labels 1 and 2. Rewording: "contains labels 1 and 2" (not necessarily adjacent);
   beta <= 1 still follows.
5. **Lemma H: correct** (|T*'| exactly 6; h clean since |T*| = 7 is tight; zeta'_j = zeta_j + delta_j a(h);
   an even a(h) would need three even gates where two exist). The "Principle" paragraph is heuristic.
6. **Lemma Q': statement true, sketch wrong** (if no auxiliary was spent in dimension 3, on b4's arrival the
   vectors x + b4, x in {b1+b2, b1+b3, b2+b3}, cost 2 and b1+..+b4 costs 3). Correct proof: take a basis
   greedily in time order; an exit's basis support is then available, Lemma Q applies verbatim, dependent
   labels only help.
7. **Section 4.** Correct: tau_min = |supp E|, sigma = e1 - |supp E|; zeta_j = 0 iff j outside supp E; the
   clean traces satisfy t - 3 independent relations; f1 >= |T*| >= 4 + zeta + spare; the shallow e1 >= 5
   consequences; the deep-label remark. Over-claims: equal traces are necessary, not sufficient, for a free
   stack; "each non-free adjacency consumes a spare" is false in general (support-3 relations; coinciding
   forced values); it holds in settings like (3,8,0).
8. **Section 5: the reduction of a 29 is complete for e1 = 4.** Lemma 2.1* holds for any far side, so the
   G1/G2 split plays no role; a 29 must violate SB*. Every e1 = 4 case outside Omega1 satisfies SB*:
   o = 0 S1; o = 1 S2; o = 2 O2 (all near1); o in {3,4}: near1 = 10 impossible, near1 = 11 has tau = 3,
   (f1, h1) in {(8,0), (7,1)}, h1 = 0 settled by the review-sb repair, h1 = 1 is Omega1; near1 >= 12 Lemma Q.
   For o >= 2, t = 4 is forced. Residual (1) is right as a necessary condition (near1 = 11, far1 = 18,
   beta = 2, chi = 6). Wording: beta = 2 can also come from three weight-3 exits (e.g. {1,2,3}, {1,2,4},
   {1,3,4}) without a weight-4 exit (two weight-3 exits give beta <= 1 when o = 4, which also corrects
   review-sb point 7); "a weight-4 exit gives chi = 6" only if other exits add no even value (o = 3 with an
   extra even exit lambda1 + lambda3 gives chi = 5). Residual (2) sharpens: in the shallow case only e1 = 5
   with near1 = 10, h1 = 0, sigma = 1, beta = 2 remains; "far1 >= 20 for sbx5-type deep stacks" is shown for
   the single instance only.
Minor: the section-3 mirror check is correct; the "salvageable form" of the Omega conjecture is unproved.
