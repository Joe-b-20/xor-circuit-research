# Adversarial check of the qhub claims (C1, H2, Lemma H2 / HUB2, PK4 / PK5, 863 / 166 and 789 / 116) — findings

qhubcheck agent, 2026-11-08 00:00-00:55 UTC (transcribed by the coordinator from the agent's final
message; the agent could not write this file). Read first: qcheck/REPORT.md, qrealcheck/REPORT.md;
then qhub/REPORT.md, qhub/hub2.py, hub2_check.py, qh_lp.py, qh_circ.py, logs/JSON, PROOF.md sections
1, 3, 4, 10, qreal's fullmet.py, qrealcheck's lp_qrc.py, the package's stress.py / lp_regen.py.
Everything outside qhubcheck/ read only. One python process at a time under nice 10; ~45 min compute.

## Verdicts

| claim | verdict |
|---|---|
| (1) C1: F(h, R, S) = {H_f + T} u {H_i + T : T in R} u {H_i + H_f + P_f} independent in any normalized circuit containing the configuration | CONFIRMED (every step; two wording remarks) |
| (2) finite fact H2: cap_r(h) <= 3 - r, both orientations; K_0, K_1, K_2 = 3, 2, 1; maxima attained with X = 0 | CONFIRMED by independent recomputation (h2_check.py): identical histograms, attaining counts 8 / 64 / 12 (M), 20 / 120 / 24 (M^T), X = 0 counts 8 / 16 / 12 and 20 / 24 / 24; the nine explicit witnesses pass every test, also under a stricter X |
| (3) Lemma H2 (r_i + m_i <= 3), row HUB2 (u_i <= 3 - r_i + q - A), split A = q - d / A <= 1 | CONFIRMED (split exhaustive; each case a relaxation; integer refinement A = a gives the same keys) |
| (4) PK4: #{u >= 3} <= 1 at q = 4 | CONFIRMED (exhaustive, tight) |
| (4) PK5 as implemented (coefficients 1, 2, 2 for u = 3, 4, 5, constant 2) | CONFIRMED (exhaustive, tight; the unique nontrivial facet at q = 5) |
| (4) PK5 as written in qhub REPORT ("N_3 + 2 N_4 <= 2, N_j = #{u >= j}") | WRONG as a statement in that notation (a lone u = 4 helper gives 3 > 2); the LP row is the valid one; notation slip |
| (5) recounts 996 / 381, 863 / 166, 789 / 116 | REPRODUCED verbatim (scan JSON byte-identical) and independently (lp_qhc.py): survivors 863 and 789 identical with or without FM; keys 166 / 116 identical WITH FM, 167 / 117 without |
| qhub's "FM was not applied separately" | WRONG as stated: FM7/FM9 are in every qhub variant and kill one baseline key (9,6,8,7,0,M^T) that HUB2 + DARK + PK alone do not; FM's tables recomputed here agree, so the kill is legitimate |
| (6) 0 violations on real circuits; m_i = A = 0 everywhere | CONFIRMED with own code on 13 controls + 40 real circuits (212 phases); synthetic configurations with m = 1, 2, 3 (and m = 4 mutations) exercise the rows and the C1 elimination |

No gap and no counterexample in the mathematics behind the LP rows. Two text errors (PK5 wording,
FM remark) and one bookkeeping correction (the load-bearing key set of the final scan is 551 keys,
not 53). No bound beyond 75 is claimed or confirmed.

## 1. C1, step by step
Preliminaries: h + f_j = b_j + c_j with b_j != c_j (Lemma 1.1(i)), so h + f_j is a pair value with a
unique pair P_j (F2) and f_j in N(h); the f_j are distinct (Lemma 4.6); the P_j are pairwise disjoint
(Lemma 4.5 / F4); R is an r-subset of the F3 triple list of h (Lemma 4.4). Gate-equation family: the
B-B references of the represented labels among {l_t} u {l_{j,s}}, the represented H-B equations of i
(r) and of the f_j (3m), the two missing H-B equations of every l_j (2m): pairwise distinct gate
equations, independent as formal vectors (proof of Lemma 4.4). Step 1: add each represented label's
reference to every H-B row with that label; delete the references. Step 2: add the hub's missing row
of l_j to f_j's: H_i + H_{f_j} + P_j (the formal vector of h + f_j = b_j + c_j); delete the hub's row.
What remains is exactly F(h, R, S), a subfamily of an invertible image of an independent family.
Verified on 106 synthetic configurations (rank(gate family) = #references + m + rank F). Consequences
checked: H1 is the 3m-subfamily; FM's per-label rank condition follows; the one-swap configuration is
dependent (50 tested per orientation).

## 2. H2 independent recomputation (h2_check.py, 30 s)
Own matrix parse, pair values, triple lists (F3: 40,704 / 360 / 80 and 40,320 / 504 / 112), 80 / 112
full values, N(h) for 128,068 / 177,412 odd non-boundary values, GF(2) elimination, hereditary DFS.
M: r = 0 cap histogram 1: 126,412; 2: 1,648; 3: 8 (max 3); r = 1: 0: 11,392; 1: 1,124; 2: 64 (max 2);
r = 2: 0: 428; 1: 12 (max 1). M^T: r = 0: 1: 174,320; 2: 3,072; 3: 20; r = 1: 0: 15,216; 1: 1,804;
2: 120; r = 2: 0: 592; 1: 24. Every histogram, maximum and attaining count equals qhub's; 0 violations
of cap_r <= 3 - r; X = 0 counts as qhub section 3.3. H1 cross-check (3m vectors only): max 4, cap-4
lists identical to qrealcheck's; these 8 / 20 values are exactly the r = 0 hub values of capacity 3
under C1. The nine witnesses: membership, independence (rank 12/12, 9/9, 6/6), m = 3 - r, disjoint
pairs, X = 0, constrained X = 0, O1 matching: all pass. Not re-derived: the tail identity behind
"E_B,e + E_B,o <= shortfall" (no LP row depends on it).

## 3. Lemma H2 and HUB2
r_i = 3 => m_i = 0 (Lemma 4.5). r_i <= 2: C1 + H2 give m_i <= 3 - r_i. HUB2: A = number of full-met
labels; u_i <= m_i + (q - A). Case split: ('d', d) for d = 0..q-2 (equality sum_{r=3} u n = q - d,
deletion of types with u > 3 - r + d) and ('low', 1) (sum <= 1): covers 0..q; each case a relaxation.
Integer refinement A = a, a = 0..q (HUB2X): same key sets. HUB2L valid, adds nothing.

## 4. PK4, PK5 (pk_enum.py)
Families of missing-label sets of helpers with u >= 3, pairwise meeting in <= 1 element (Lemma 10.4
from Lemma 4.6), enumerated: q = 4: 6 families; q = 5: 32; q = 6: 353; q = 7: 8,390. PK4: max 1,
valid, tight. PK5 as implemented (n_3 + 2 n_4 + 2 n_5 <= 2, n_j = #{u = j}): max 2, valid, tight, the
unique nontrivial facet. PK5 as written ("N_3 + 2 N_4 <= 2" with N_j = #{u >= j}) reads n_3 + 3 n_4 +
3 n_5 <= 2, maximum 3: WRONG as a statement; harmless. L23 rows at q = 6, 7 re-checked: valid, tight.

## 5. LP recount and independent implementation
Verbatim recount (qh_lp_recount.py): 996 (504, 492) / 381; 863 (454, 409) / 166; 789 (416, 373) /
116; scan JSON byte-identical to qhub's. Independent lp_qhc.py (base + DARK from lp_qrc.py; HUB2 /
HUB2X / PK / FM written from the statements): HUBDARK 381 keys identical; HUB2DARK (no FM) 167 keys
(+1: (9,6,8,7,0,M^T)), survivors 863 identical set and (k, l); HUB2DARKPK (no FM) 117 / 789 identical
survivors; HUB2XDARKPK 117; with own FM tables 166 / 116 identical. FM: present in all qhub variants;
the disputed key is feasible without FM only in the case A = 5, q_D = 0, with W + y_1 = 44.53 against
FM7's 44.0; FM's finite tables recomputed (rank(C_l) histograms M: 3: 3,696; 4: 692; 5: 140; 6: 108;
7: 4; M^T: 3: 4,960; 4: 1,176; 5: 144; 6: 216) identical to qreal's; with the per-label L7* (qcheck)
the rows are valid, so the kill is legitimate. Complete bookkeeping: the final scan touches 36,655
keys; 859 LP-feasible (78 in the baseline list); 551 load-bearing (M 271, M^T 280; by q 1: 2, 2: 62,
3: 95, 4: 175, 5: 66, 6: 93, 7: 37, 8: 20, 9: 1), of which the 53 baseline ones are qhub's "53".

## 6. Circuits and synthetic configurations (circ_qhc.py, 21 s)
13 controls + 40 real 88s, 4 orbit steps, 212 phases, own code: 0 violations of H2, HUB2, Lemma 4.5,
4.6, PK4, PK5, L23; max m_i = 0, max A = 0, HUB2 slack >= 7; the pair identity at helpers sharing a
missing label holds 1,718 times; the family "represented relations + t_l - 1 mixed vectors per shared
missing label" is independent on 212 / 212 phases. Synthetic maximal configurations (m = 3 - r; 35 M,
45 M^T) built explicitly: gate equations independent, the C1 elimination yields exactly F(h, R, S),
Lemma H2 holds and HUB2 holds with equality; the 8 + 8 H1 cap-4 configurations (m = 4) give dependent
gate equations and are flagged as H2 / HUB2 violations: the checker is live on m >= 1 data.

## 7. Remarks
PK5 wording (also in the qh_lp.py comment); FM is part of the LP and load-bearing for one baseline
key; key statistics 381 / 166 / 116 are baseline-restricted (honest: 859 feasible / 551 load-bearing);
the r = 0 capacity-3 hub values are exactly H1's cap-4 values; hub2_check.py limits subset sizes for
|N(h)| > 11 (my DFS recomputes them fully and agrees); for M^T every label f + c has rank <= 6.

## 8. What a referee would still want
C1, Lemma H2, HUB2 in package style with finite fact H2 in finite_facts.py and the strong forms in
stress.py; FM7/FM9 documented as rows; Farkas certificates per case of every excluded key (up to
q(q + 1) per key) with two checkers and a case-enumerating coverage checker; a normalized circuit (or
an impossibility proof at small q) with A >= 1; the tail identity re-derived if the degree budget ever
enters a row; the two text corrections and the 551-key set in place of "116 / 53".

Files: h2_check.py/.log/.json; pk_enum.py/.log; qh_lp_recount.py/.diff/.log, scan_*_q0_g75.json;
lp_qhc.py, lp_qhc_keys*.log/json, lp_qhc_scan*.log/json, lp_qhc_keysfull_*.json; fm_check.py/.log,
fm_tab_{M,Mt}.json; vert_key.py/.log; circ_qhc.py/.log/.json; run_chain*.sh, run_recount.sh.
