# arch87: the archive's 87 attempts against the sprint's SAT scopes

(Transcribed by the coordinator from the agent's final message, 2026-11-08 00:10 UTC; the agent could
not write this file. Helpers in this folder: lsdocs.sh, cmpinv.sh, catG.txt (excerpt of the Aug 12
catalog). Everything about the archive is its own claim with its own label, except two checks marked
[checked here]. No archive program was run.)

Sprint scopes, all instances I(K, k-1) of sat87; UNSAT means no circuit with <= 87 gates contains K:
S1 one-seed windows k <= 10; S2 output blocks k <= 12; S3 two-seed windows k <= 9; S4 mobile factors
of the plateau. Two facts used throughout: containment is monotone (an UNSAT for K covers every
split-closed set containing K); the archive's other scope types are pool (all values in P), r-outside
(at most r values outside an inventory W0: exactly the union of all sat87 scopes of W0 with r+1
helpers removed, an exhaustive version of S1-S3 at small k) and restricted class.

## 0. The finding that matters most

The archive ran the sprint's instrument in August, and its own power control failed.
- fence_sat (Aug 12 catalog, section B1) asked the same order-free value-set question as sat87. On 17
  windows of 89-97-gate circuits where a smaller circuit provably exists, it returned UNSAT on all 17.
  The owner's verdict was "likelihood ratio ~ 1.00".
- The archive's other exact -1 window solvers over all 2^32 masks also found 0 SAT on the August 88s:
  mutant_satrepair (k = 5..10, 6,472 UNSAT); xor_encoding (k = 10..13); band_hunt (global windows
  decided up to n = 11); downstep (20,893 decisions; the reduction lemma "remove k, add k-d" depends
  only on the target-free window size m).
- The meta-review gave the reason: in the controls, improving moves sat at mask distance minimum 3,
  median 42, maximum 48. Below k ~ 25 there is "no viable operating point".
- The sprint has run no slack-1 power control (the m = k check, which re-finds the 88 itself, is not
  one). F13 and F23 are correct theorems, but how much they say about 87 is unmeasured.

## 1. Attempt families (a: space; b: result in the owner's labels; c: why it stopped; d: relation to S1-S4; e: idea not yet covered)

1. Neighbourhood certificates (catalog A1, A3, A5): k <= 3 shells of fixed circuits, also of M^T;
   ~165 M "irreducible"; the A3 control could not tell a 97 from an 88 ("REFUTED-METHOD"); radius 3
   against a median transition distance of 42; inside S1/S3-type scopes at k <= 3; -> R0.
2. fence_sat (B1): frozen core + k-mask window, order-free SAT; 52 UNSAT, 0 SAT; control 17/17 UNSAT;
   same question as sat87; the ledgers are not in the archive; -> R0.
3. Exact -1 windows over 2^32 (D1, D8, A3, A6, T3): cones, disconnected co-parent windows,
   out-degree <= 2 components, global and splice forms; 0 SAT; ceilings k ~ 9-14; band_hunt timeouts at
   n = 12-14, "ONGOING"; same class as sat87 (A6 global form is exactly sat87); August anchors; -> R6,
   and the co-parent predicate as a window generator.
4. Convex sub-blocks (D5, T4 DFS): rebuild a block's externally used values in |S|-1 gates; 927 UNSAT;
   DFS B = 15 UNSAT, B = 16-17 inconclusive; weaker per window than sat87.
5. Alphabet rungs (A2, B3, D4c free-closer, D6, D7 union_sat, D14 council, T1 pools, A5): all values in
   an alphabet A, free-closer adds 1 unrestricted mask; thousands of floors at 88; union_sat r(88) <=
   8.6e-6 with a working control; PLX3: no 87 whose cross-plane masks all come from three skeletons, at
   any depth; free-closer: no 87 with <= 1 mask outside A; retired as "certification, not discovery";
   pool scope; -> R2, R7.
6. One-target-short trims (D4d, D4e): trim 88s to 86 values without one target, try to complete; 0 of
   1,630,797 complete ("corpus-conditional, exact"); -> R4.
7. Value-pool MILPs (Sep 27): 166/168/169-value pools; 205-value pool at depth <= 5; "no 87 within the
   168-value pool"; no 87@<=5 in the 205 pool; solver status only; -> R2.
8. k-foreign (Oct 15-16, PUSH9): <= 55 helpers, <= r outside inventory W0, arbitrary masks;
   four-foreign complete around canonical_00; five-foreign 26,583,317 of 32,468,436 cases excluded,
   5,885,119 open; exhaustive union of sat87 scopes at k <= 5; canonical_00 shares only 29/56 helpers
   with the archive's mixcolumns_88gates_depth5.txt [checked here]; -> R5.
9. Four-exterior (Sep 24): contains w = x7+x23; quotient modulo w; 114-value pool Q; <= 4 outside
   values; optimum exactly 88 in the family; an 87 containing w needs >= 5 quotient values outside Q;
   -> R2 with P = Q ∪ (Q+w), K = {w}.
10. <= 1 outside value pricing (Oct 14): LP over a 176-mask bank; >= 83.85 so >= 84; "cannot exclude 87".
11. Odd-helper theorems (F20): any <= 87 needs 3 <= h <= 31; does not touch real plateaus.
12. Blank exact instances (Aug 14 Z3; Oct 13 GLOBAL_87_NORMAL.cnf 182,669 vars / 1.38 M clauses; Oct 15
    SMT; Oct 23-24 mold solver): fully unrestricted; all UNKNOWN; blank solves cannot re-find known
    88@5 or 89@4; do not spend cores here.
13. Restricted classes (native-87, mold87/hub87, byte-level, sigma sector): best native 99-105; hub87 is
    an abstract graph; byte-level cannot reach 88; sigma-sector floor 90; disjoint; low value.
14. Demand-flow backbone (Aug 14-16): frozen 61-mask exterior + 22 backbone + 5 ternary repair planes
    (3^5, the F2/F23 product structure); backbone + any 4 masks impossible; manifold rigid; OPEN:
    "1,291 such triples left"; data partly lost; -> R3.
15. 18-pair foundation (Sep 9): 18 pairs + 66 regenerated rich values; o9, o10, o18 missing; only
    one-gate and hand-picked two-gate swaps tried; -> R4b.
16. Local moves on fixed 88s (Aug 28 - Sep 10): two-defect, radius-k, metamorphosis + exhaustive k = 2
    shells; no 87; dominated by S1-S3.
17. Engines and learning (walk/LNS, NRPA, evolve, Steinberg, Collapse, SK Lab): P(87 per descent) <
    2e-3, a statement about the operator class; retired.
18. Partial-circuit repair (Oct 2-8): 75/76-gate partial circuits; candidate D: 87 gates, 31 outputs,
    y19 missing; no <= 87; owner's open questions: "Rewiring D within 87 gates remains a different
    question"; 25-40 s budgets; -> R4a, R8.
19. Grammar, crossover, exchange: all >= 88; conemix_dec87 "pending".
20. Proof identities (G = 64 + c - b + p, G = 108 + delta - S): two solver "87 points" rejected as
    non-circuits; not constructive.
21. Exit search / barrier tree (Nov 5-6): +1 band of plateau B11; 0 improvements, 1,687 unresolved; the
    whole mobile part as one sat87 instance is queued in satmob campaign3.
22. Transpose (A1, A4): XOR-count(M) = XOR-count(M^T); transported images give no novelty; from-scratch
    arm "ONGOING"; add transposed 88s as extra anchors.

## 2. Ranked exact formulations not yet tried (costs on the sprint's measured frontier)

- R0 power control first (prerequisite, 2-6 core-hours): run the F13/F23 window generators with
  m = k-1 on anchors one gate above a known improvement: hunt states at 89/90 whose logged 88
  descendant gives the distance d, the 89@4 family, the own 90@4, and 97@3. If the hit rate is 0,
  F13/F23 carry likelihood ratio ~ 1, exactly as fence_sat did.
- R1 large windows only: the whole mobile part (k = 21-32) and out-degree <= 2 components (up to 28
  values on 88@5): the band where improvements live; queued in satmob campaign3.
- R2 r-outside as one SAT per (pool P, r): each of the 87 - |K| slots is a one-hot choice from P or a
  free 32-bit value, at most r free; P = one sprint plateau's union (~100 values), two plateaus, or
  canonical_00 (r = 4 should come out UNSAT, cross-checking the archive); ~20-30k variables, 1-3 M
  clauses with K empty; pilot r = 1-3 at 1,800 s: 2-4 core-hours.
- R3 the demand-flow frontier (5-10 core-hours): rebuild the 61-mask exterior (find the 88 containing
  the 27 masks of backbone_defect_bundle/core22_state_0.txt), then per backbone triple K = exterior ∪
  (backbone minus triple), 80 values, m = 7; 1,540 instances; covers the archive's 1,291 open triples
  with an unrestricted finisher. Quadruples ~200 core-hours, next sprint.
- R4 near-miss anchors, budget-neutral: R4a candidate D (AES_Deep_Repair_75_76_Profiles_2026_10_02/
  aes_deep_repair/results/selected/b87_most_exact.json; 87 gates, 31 outputs, y19 missing): instances
  I(D \ W, |W|) over helper singletons and pairs plus closure, and one-seed windows k <= 10 around y19;
  a SAT is an 87; 1-3 core-hours. R4b the 18-pair state: K = 84 values minus r rich values, m = 3 + r,
  r <= 6; under 1 core-hour. R4c the n16 near-26 module: only if R3 finds the exterior.
- R5 finish the five-foreign census with sat87: tonight the 2,397 R5 = 0 cases (k = 6, m <= 5; ids in
  strong_bound.zero_r5_ids.csv), ~1 core-hour; the 5.9 M remainder ~500 core-hours; gain: any <= 87 has
  >= 6 helpers outside canonical_00.
- R6 band_hunt's frontier on the sprint's plateaus: out-degree <= 2 components at n = 12-14, ~40 windows
  at 1,800-3,600 s: 20-40 core-hours, next sprint.
- R7 restricted large windows (class-conditional pilot): sat87 at k = 15-30 with free values limited to
  <= 3 bit-planes and xtime carry classes, or the SYL pattern class; the archive warns of blind spots.
- R8 I(A75, 12) and I(A76, 11) from the owner's question: 5 missing targets, 6-7 free values; expect
  timeouts; 2 x 4 core-hours.
- Not recommended: the blank instances.

## 3. Strongest conditional negative results (archive's own labels)

1. Four-foreign complete (PUSH9 checkpoint RESULT_REPORT.md): any circuit with <= 55 non-output helpers
   needs >= 5 helpers outside canonical_00 and must omit >= 6 of its helpers; arbitrary masks and
   parents; two implementations; five-foreign 81.9 % excluded, 5,885,119 cases open. Exhaustive at
   k <= 5, where the sprint's windows are selective.
2. Four-exterior ("audited, family-scoped"): any 87 containing x7+x23 needs >= 5 nonzero quotient values
   outside the 114-value pool Q; otherwise the optimum is exactly 88.
3. Free-closer ("SOUND", vocabulary-conditional): no <= 87 with at most 1 mask outside the region
   alphabets A, B, D, E; several rungs hold only at depth <= 13; region C undecided.
4. Value pools (HiGHS status only): no 87 inside the 168-value pool at any depth; no 87@<=5 inside the
   205-value pool.
5. Plane-local freedom PLX3: no 87 at any depth whose cross-plane masks all come from three skeletons,
   with the complete 88-mask plane-local layer free.
6. union_sat: floor 88 over 348,405 unions of two 88s, while the same test finds 88s in 0.77 % of 89∪89
   unions: the archive's only large negative with demonstrated power.
7. One-target-short corpus: 0 of 1,630,797 trims complete (corpus-conditional).
8. Odd helpers: h >= 3 for any <= 89 (F20).
9. <= 1 outside value: only >= 84.
10. Depth: any 87 has depth >= 4 since D3 >= 93; PUSH7's depth >= 5 is conditional.
11. Demand-flow: the fixed backbone + any 4 masks fails in the frozen exterior (hand-staged finishers).

Relative to the sprint: stronger in some scope: items 1 (exhaustive at k <= 5), 2 (whole-circuit
constraint given one value), 5 (an entire 88-mask layer free). Where S1-S4 are stronger: window size
(k up to 12, outputs included) and no pool. Power controls: only union_sat's works; the archive's other
controls failed, and the sprint has none yet.
