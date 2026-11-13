# Audit of the finite computations dated 2026-11-12 (disclosure accuracy)

Read-only audit; no script was run. Scope: every .py/.c/.sh under research/structure-2026-11-11/ (excluding joint/)
with mtime on 2026-11-12. Prohibition = start of the session whose first commit is 1db304c (09:24:31); 39b43aa
(00:22) is the previous session. Files first committed in 1db304c or later count as AFTER (the commit closes the
session's first stretch of work). Classes: E exhaustive/exact-minimum search, C check of given objects or read-only
corpus scan, M mixed. "Hand" = a hand argument exists in the record, or is given in section 3 below.

## 1. Scripts that search (E or M)

| script | added | vs 09:24 | what | class | statements that depend on it | hand argument? |
|---|---|---|---|---|---|---|
| review-p/p3check.py | 6390333 12:51 | after | BFS over every reachable value set on W0..W3,X with <= 2 (or 3) non-required gates; best m = #Z+X and Z-span | E | P3 "sharp" (review-p/REVIEW.md:19-21; compose/refute/REPORT.md:8; TWOSIDED.md:358-360, 365-366) | P3 itself: yes, case split, refute/REPORT.md:48-52. Sharpness (3 gates reach m = 3..7): rests only on the run; witnesses are not written in the record |
| review-p/p3unit.py | 6390333 12:51 | after | least gate count holding E_c and W_c+X (c = 0..3), search over value sets, <= 2 others | E | "exactly 10" (review-p/REVIEW.md:24-27; TWOSIDED.md:361-362, 366). The use at RECORD.md:1035, TWOSIDED.md:381 and refute/REPORT.md:13 ("fits a 10-gate mirror") needs only the UPPER bound | upper bound: explicit circuit (section 3). Lower bound 10: no hand argument in record; one is given in section 3 |
| review-p/p5o3.py | 6390333 12:51 | after | all 3- and 4-sets of weight-3 exits x every label/exit staging, DFS for exact chi (|R| <= |S|+3) | E | P5 case o = 3 (review-p/REVIEW.md:29-30; TWOSIDED.md:362-364; RECORD.md:1029) | yes: refute/REPORT.md:60-62 ("every set of three or four weight-3 exits has an R with |R|-|S| = 2 and tau_R = 3 (the four triples checked by hand)"), TWOSIDED.md:364. The run is a confirmation. Only an upper bound chi <= 5 is claimed, so exact minimality is not needed |
| compose/sb2/ncheck.py | 50ab7e1 11:45 | after | one given near circuit; exact joint L_near by Dijkstra over sets of computed vectors; also lists same-fibre pairs | M (search = the Dijkstra, unbounded in gates, tiny state space) | beta = 2 in sbx5: SB' counterexample (TWOSIDED.md:190-205; sb2/REPORT.md:47-53; RECORD.md:943; review-sb2/REVIEW.md:12-13) | upper bound explicit (TWOSIDED.md:204); lower bound L_near >= 3: not stated in the record, one line in section 3 |
| compose/sb2/sbcheck.py | 50ab7e1 11:45 | after | same, with concrete labels; plus tau_min by trying all label subsets, sigma, near1, SB' truth value | M (Dijkstra; subset loop over <= 5 labels) | same as ncheck; tau_min = 5, sigma = 0 in sbx5 | tau_min = 5: hand in section 3 |
| compose/sb/mcheck.py | 50ab7e1 11:45 | after | given MC_l circuit: classes, exits; L_near of each exit by BFS closure (limit 4 gates); tau_min by subsets | M (BFS, limit 4) | dangle2: SB refuted, beta = 1 > 0 (TWOSIDED.md:171-185; sb/REPORT.md:15-17); "mcheck 3" for sbx5 | beta = 1: hand, 3 independent labels' sum needs 2 gates (section 3) |
| compose/sb/tscan.py | 50ab7e1 11:45 | after | one hand-given T*: all summation-order signals, all equal-w^1 pairs (finite family of one object) | M | sb/REPORT.md:73-76 "Evidence on Omega2", labelled evidence + conjecture | nothing is proved from it |
| review-sb/ev.py | 50ab7e1 11:45 | after | evaluator + exit "least" by BFS (limit 5) | M (BFS) | dangle2 L_near = 2 (review-sb/REVIEW.md; TWOSIDED.md:171-172) | yes, section 3 |
| review-sb2/ev2.py | 50ab7e1 11:45 | after | same for sbx5_mc3: tau_min by subsets, L_near by BFS (<= 4) | M | review-sb2/REVIEW.md:10-14 (L_near = 3, tau_min = 5) | yes, section 3; "chi = 5 exactly" has the reviewer's hand argument (REVIEW.md:13-14) |
| compose/mc/chi_mc.py | 6390333 12:51 | after | corpus scan (stride); per exit: e_min by all label subsets, honest combo by subsets <= 6, chi_up over chains/pairings | M (subset search, per circuit, <= 11 labels) | mc/REPORT.md:8, 66-70 ("exact e_min 9 or 10 ... 4 circuits checked exactly"); marked check | observational only; honest cost = beta needs labels independent (otherwise only an upper bound) |
| compose/mc/chi2_mc.py | 6390333 12:51 | after | same with greedy e_R (upper bound) | C | mc/REPORT.md:9, 70 ("chi_up - e is 1 to 3", labelled greedy upper bound) | observational only |
| causal-pair/x_config_check.py | 1db304c 09:24 | after | for the 6 hand-derived cases, all 24 index permutations x reversal: relations, rank, det(I+N), acyclicity | M (24 instantiations of hand cases) | causal-pair/REPORT.md:9, 49-51; RECORD.md:987-991 | yes: explicit dependencies REPORT.md:40-48 (S3 written out); the 24 choices are one case by S_4 symmetry of unit labels. The "rank <= 8 also for path (3)" line has no hand dependency in the record |
| review-causal-pair/check_review.py | f3fc6f9 10:36 | after | part 1: every 5-edge tree (6) x 8^5 odd labellings x all exit-path assignments; rank of the 9 relations. Part 2: greedy closure on given value sets | E (part 1), C (part 2) | review-causal-pair/REVIEW.md:17-22, 71 ("Lemma 2 complete; all 384 rank <= 8; distinctness not needed in path (3)"); causal-pair/REPORT.md:9; RECORD.md:987-991 | completeness of the case list: hand list in pair/PROOF.md (not re-derived); the independent completeness check and "rank <= 8 in all 384, path (3) rank 7" rest only on the run. Part 2 conclusions (executable bases) are explicit orders, REVIEW.md:44-50 |
| review-joint01b/chk_b.py | 1db304c 09:24 | after | all 28 even bases x all 256 aux values: named representations, free-fibre partners; sums of 3 required vectors; p = 3 sub-case over index choices | E (tiny, 28 x 256) | review-joint01b/REVIEW.md:5 (disclosed "over all 28 even bases") | yes: REVIEW.md "N, F2, F3 by hand" |
| joint01/check_j01.py | 39b43aa 00:22 | BEFORE | all 28 bases: N, F2, independence, F3 over all beta; Part 2/3 given circuit | E (tiny) + C | joint01/REPORT.md:58 | yes: REPORT.md:50-58 hand proofs ("The hand proofs do not depend on this file") |
| joint01/review/rv1.py | 39b43aa 00:22 | BEFORE | matrix check; p = 3 last step over all bases and index choices | E (tiny) | joint01/review/REVIEW.md:5 | yes (hand in REPORT/REVIEW) |
| compose/build29/twover.py | b057c14 10:08 | after | 3 values of rho x 2^k choices for "closer" gates of the Q_3 lift; picks min gate count (36) | M (3 x 2^k, k small, enumerated) | build29/REPORT.md:32-34 "best 36" | only an upper bound is claimed (explicit lift_best.txt, verified by vchain.py), so no exhaustiveness is used; REPORT.md:4 "No search" is loose |
| review-compat/prop2.py | 1fa8a7e 13:49 | after | random automorphisms (seeded sampling) | C (sampling) | review-compat/REVIEW.md:15 "phi half backed by a check" | sampling, not exhaustive |

## 2. Scripts that only check given objects or scan a corpus read-only (C)

All of these evaluate given circuits/files, scan the kste corpus by stride, or do linear algebra on given data; none enumerates
circuits or value sets. Commit in brackets. All after the prohibition unless stated.
- 1db304c 09:24: causal-pair/loop_examples_check.py (peeling, F_2 determinant, given loops), compose/show_blocks.py, review-chain/mirror_check.py (hand circuits, seeded random summation orders).
- b057c14 10:08: compose/build29/{dump_chain,lift_q3,vchain}.py (Gaussian elimination, accounting), compose/prove3/q3_mirror.py, review-compose/bm_exit_check.py (one explicit circuit).
- f3fc6f9 10:36: compose/ring/{ring_cuts,label_types}.py + run_all.sh (honest cost = fewest labels summing, subsets of labels, per given circuit).
- 6390333 12:51: compose/mc/{corpus,mirror,labels,detail,far,rewrite}_mc.py, compose/refute/near.py, review-p/witness.py, review-ring/{mc_cols,mc_tri}.py (triangles of an 8-vertex window graph).
- 1fa8a7e 13:49: compose/compat/* (join.py is greedy completion plus explicit verification; lowwaste.py an explicit construction), compose/tri/*, review-O/*, review-compat/{cutcheck,dump_lw,mycheck,p12}.py. review-O corpus minima ("min far 64 ...") are witnesses by evaluation, each verified by witness.py/olib.py.

## 3. Hand arguments for the small exact bounds (so the record can cite them)

Gate lower bound: a vector that is the sum of k linearly independent available vectors, with all k coefficients 1, needs at least k-1 XOR gates from them (each gate merges at most two supports).
- sbx5 (TWOSIDED.md:190-205): X = L1+L2+L3+L4, labels independent, so L_near(X) >= 3; the record gives the 3-gate upper bound; beta = 3 - 1 = 2 > near1 - 10 = 1. tau_min = 5: u2+u3 = L1+L2, u1+u3 = L3+L4, u0+u3 = L5 each have a unique expression in the independent labels, together they use all five, so any span containing Even(u) contains all five; sigma = 0.
- dangle2 (TWOSIDED.md:171-185): exit value u0+u1+u2, sum of three independent labels, L_near >= 2 (upper bound 2 given); beta = 1 > near1 - 10 = 0.
- p3unit "exactly 10": upper bound x = W0+W1, y = W2+W3, E_3 = x+W2, E_2 = x+W3, E_1 = y+W0, E_0 = y+W1, W_c+X (4 gates): 10 gates. Lower bound: 8 required values need 8 gates, so show 0 or 1 other gate is impossible. The first E computed is a sum of two values among inputs, Z's = W_c+X and at most one other v; any such sum without v has W-weight <= 2 while E has 3, so it is E = v + z; v itself is built before any E exists, so has W-weight <= 2, hence z = W_i (i in E) and v = W_a+W_b, or z = Z_i and v = W_a+W_b+X. Every later E is again v + (input/Z) or E' + v (E' + E = W_d+W_e pure pair, available only as v). If v = W_a+W_b, then E_a, E_b can only come from each other (E_a + v = E_b): neither can be first. If v = W_a+W_b+X, E_a + v and E_b + v have weight 3 plus X, E_a + E_e is a pair with no X, none available: E_a, E_b cannot be made. 0 others: the first E has W-weight <= 2. So >= 2 others.
- Review fixes to the "exactly 10" proof (joint/review/REVIEW.md section 4; verdict: correct with fixes, no wrong
  step). (1) In "E = v + z": z = X is excluded (v = E + X has W-weight 3, impossible before any E), and z = W_i with
  i not in E gives W-weight 4. (2) Case v = W_a + W_b: E_a is not v + input (v + W_i contains W_a) nor v + Z_i or
  v + X (they contain X), so only E_a = E_b + v remains, and symmetrically; neither can be first. (3) Case
  v = W_a + W_b + X: E_a = E' + v needs E' = E_a + v = E_b + X, not an E; v + Z_i contains W_a or equals W_b;
  v + W_i and v + X are not E_a. (4) The ninth gate may be 0, an input or a copy of a required value: then it is
  not available before the first E with W-weight 3, and the same argument applies (a copy of an E reduces to the
  case of no other gate). Status: hand proof by a delegated model instance, machine-reviewed; not a human review.
- p5o3, p3check: hand case splits at refute/REPORT.md:48-52 (P3) and 60-62 (P5, o = 3).

## 4. Summary

(a) Statements that rested ONLY on a computation executed after the prohibition (status after the hand
proofs: section 5): (1) the lower bound "exactly 10" for four unit types (p3unit; now hand-supported by section 3; only the upper bound is used downstream); (2) the sharpness of P3 (three spare gates reach every m from 3 to 7; p3check; witnesses not recorded); (3) the review-causal-pair statements "all 384 configurations have rank <= 8, so even path (3) falls to rank alone / distinctness not needed" (check_review.py part 1, x_config_check.py); (4) the corpus observations in compose/mc and compose/compat/tri (all labelled "check"/"observed", none used in a proof). The SB' counterexample sbx5 and the SB refutation dangle2 depend on exact L_near searches (ncheck/sbcheck/mcheck/ev/ev2) but are covered by the one-line hand bound in section 3 plus the written upper-bound circuits; P3 and P5(o = 3) have hand arguments. The only (E) scripts before the prohibition are check_j01.py and rv1.py (39b43aa, 00:22).
(b) Record sentences now inaccurate:
- SUMMARY.md:239-240 "From 2026-11-12 on, by instruction, no further SAT or exhaustive computation is run in this phase" (false: p3check, p3unit, p5o3, check_review part 1, chk_b, x_config_check, and exact-minimum Dijkstra/BFS in ncheck, sbcheck, mcheck, ev, ev2 were run after it; no SAT was used).
- README.md:42-43 "In the second phase no SAT and no exhaustive computation was run" (same; also "second phase" begins 2026-11-12, so these runs are inside it).
- CHECKPOINT.md:52 "No SAT, no exhaustive enumeration ... (user instruction, still in force)": true as an instruction, but the record should say that it was not fully observed.
- RECORD.md:1138-1139 and TWOSIDED.md:358-366 disclose only review-p (three scripts); the list omits check_review.py, chk_b.py, x_config_check.py and the exact-L_near searches. "no theorem of the record depends on them except the sharpness remark and the 'exactly 10' figure" is correct for review-p once the hand argument above is cited.
- compose/sb/REPORT.md:6 and compose/sb2/REPORT.md:4 "No SAT, no search" (the checkers run exact BFS/Dijkstra minimum searches, small but searches); compose/build29/REPORT.md:4 "No search" (twover.py enumerates 3 x 2^k lifts); causal-pair/REPORT.md:4 "no enumeration of circuits" is accurate but x_config_check enumerates 24 index choices; review-causal-pair/REVIEW.md:5 calls check_review.py "checks, not proofs" without saying part 1 is a 6 x 8^5 exhaustive enumeration.
Plain disclosure (phase 8, replacing a suggested wording that said "no search over circuits"): several
exhaustive checks and exact least-gate searches were run on 2026-11-12 despite the instruction. That their
search states were value sets does not make them anything other than searches.

## 5. Dependency status after the replacements

Formerly computation-dependent, now supported by a hand argument: the lower half of "exactly 10" (section 3,
delegated, machine-reviewed with fixes); beta = 2 in sbx5, tau_min = 5, sigma = 0 there; beta = 1 in dangle2
(section 3); P3 itself and P5 case o = 3 (hand case splits existed before; the runs were confirmations).
Still resting only on a prohibited computation (kept with that status, not rerun): the sharpness of P3; the
review-causal-pair remark that all 384 configurations have rank <= 8 (so distinctness is not needed in path
(3)); the "best 36" of build29 as a minimum over the enumerated lifts (only the upper bound 36 is claimed).
Corpus observations (compose/mc, compat, tri, joint) are read-only measurements of existing circuits and keep
the status "check".
