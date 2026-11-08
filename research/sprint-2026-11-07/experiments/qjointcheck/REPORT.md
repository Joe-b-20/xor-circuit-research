# Adversarial check of the qjoint claims (F_joint, finite fact J1, Lemma P / rows P1-P5, row LIM, recount 686) — findings

qjointcheck agent, 2026-11-08 ~02:00-02:30 UTC (condensed transcription by the coordinator from the
agent's final message; the agent could not write this file; every script, log and JSON it names is in
this directory). Read: qhubcheck, qcheck, qrealcheck reports; qjoint/REPORT.md and scripts; PROOF.md
sections 1, 4, 10. Read-only outside qjointcheck/; one python process at a time under nice 10; ~15 min.

## Verdicts

| claim | verdict |
|---|---|
| F_joint independent in any normalized circuit containing the configuration | CONFIRMED (all three pivots; listed equations pairwise distinct in every sharing mode; nothing depends on which end of a pair is the hub's). Wording defect: for t >= 3 hubs at one hub-only label the pivot yields t - 1 mixed vectors (a spanning tree), not one per pair (the three pair vectors sum to zero); J1 and LIM use two hubs only |
| finite fact J1 (two limit hubs never share a missing label, full-met or hub-only; two r = 2 limit hubs never share a hub-only label) | CONFIRMED by an independent implementation (jc_geo.py: own boundary parse, pair values, triples, full values, N(h), limit configurations enumerated directly, lowest-bit elimination, NO Lemma-4.6 pre-skip), both orientations: identical limit-configuration counts (192/352/48; 480/720/96), 0 independent limit-limit pairs in every class pair for both sharing kinds (75,192 / 208,272 hub-only pairs tested; 4,544 / 14,816 same-label), identical realizable different-label counts, qj_limit's partner tables reproduced number for number |
| Lemma P rows P1-P5 and LP forms in the exact case A = a | CONFIRMED (Lemma 4.6 co-occurrence; D(a,3,2) verified exhaustively for a <= 9; P5 from the (L7) rank argument and the FM table; interval minimisation a valid relaxation for every row, the concave m(u - m) term taking the minimum of both ends) |
| row LIM (three cases) | CONFIRMED given J1 (a <= q - 2 by Lemma 4.6 alone; a = q - 1 by J1 hub-only; a = q by J1 full-met) |
| recount 686 (372 M, 314 M^T), 814 / 483 keys, 551 -> 452 -> 388 | REPRODUCED verbatim and independently (lp_qjc.py with own rows, brute-force interval minima, exhaustive packing numbers): identical survivor set and (k, l) on all 686, identical key sets |
| 0 violations on real circuits; synthetic A >= 1 configurations | CONFIRMED: 212 real phases (own extraction) 0 violations, A = 0 and no limit hub everywhere; synthetic two-hub phases: every realizable kind has independent examples satisfying every row (P2, P3, P4h, H2, J1, LIM tight), every J1-excluded kind is dependent and violates LIM |

No gap and no counterexample. The bound remains L(M) >= 75; 686 oriented claims stay open by LP status;
no certificates exist for the 103 newly excluded claims.

## Notes
- Lemma-4.6 configurations are automatically dependent (two shared labels give two pairs with equal
  XOR, which F2 makes equal), so qjoint's pre-skips skipped only dependent families (320 / 1,088
  same-label pairs, 4,384 / 14,272 hub-only pairs, all dependent when tested here).
- What the new rows kill on the 551 load-bearing keys: P1-P5 remove 99 (led by (q = 4, M^T) 56), LIM 64
  more ((4, M) 53, (3, M^T) 11).
- J1 rests on gate-equation independence only (C1 / F_joint), not on O1, X or the degree budget.
- Not checked: the MILP vertex classification and the q = 1 / n_3 = 8-10 conjectures.

## What a referee would still want
Lemma J, Lemma P and LIM in package style with the spanning-tree statement; J1 in finite_facts.py style
naming both implementations; Farkas certificates for the 103 newly excluded claims (per (a, d) case)
with two checkers and mutation tests; the relaxation argument per row written out; evidence or proof
that a normalized circuit with A >= 1 exists at all (every measured phase has A = 0, so the A >= 1
branches are tested only on synthetic configurations).

## Files
jc_geo.py, jc_j1.log, jc_j1_{M,Mt}.json, jc_partners.log, jc_partners_{M,Mt}.json; jc_patch_lp.py,
qj_lp_recount.py, lp_qjc.py, fm_tab_{M,Mt}.json; run_chain1.sh, chain1.out, recount_scan.out,
recount_lb_*.out, jc_lb_*.out, jc_scan.out, lp_qhc_keys_*.json, lp_qhc_keysfull_*.json,
lp_qhc_scan_*.json; jc_circ.py, jc_circ.log, jc_circ.json, jc_synthetic.json.
