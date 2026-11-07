# Adversarial check of the qbound claims — findings

qcheck agent (xhigh effort), 2026-11-07 ~20:15-20:45 UTC. Transcribed by the coordinator from the agent's final message (the agent lost access to the WSL share before it could write this file; the last planned step, running `lp_indep.py`, was not completed by the agent and was run by the coordinator afterwards, see the end). Content otherwise unchanged apart from HTML entities.

## Verdicts

| claim | verdict |
|---|---|
| Lemma N1 `3 n_3 <= x + y - q` | **CONFIRMED** |
| (G*) for every `J >= R_6` | **CONFIRMED** (two wording remarks, no gap) |
| (L7*) `W_l + Y_l <= rank(C_l) <= 7`, `W + y_1 <= 7q` | **CONFIRMED** |
| (L12*) `sum (r-1)_+ + y_0 <= rho_6` | **CONFIRMED** |
| (I) `y_1 + y_2 + U + 2F_H <= 4q + 2F` | **CONFIRMED** |
| (Q0) `q = 0 => z >= 32 - rho_6 + h_0` | **CONFIRMED** (for M^T it is the same inequality as inside Lemma 10.3(ii), not weaker; 10.3(ii) adds `h_0 >= 4`) |
| `y -> y_2` in (L13)-(L20), (L22); `W -> W + y_1` in (L13), (L14) | **CONFIRMED** ((L18) could also take `+ y_1`, not claimed) |
| Lemma S, Corollary S2 | **CONFIRMED** |
| S1 sigma histograms, `sigma = rank(C_l) - 1`, rich-pair kinds, `top(m)` | **CONFIRMED** by independent recomputation |
| N3max = rho_6/2 (10 / 14) | **CONFIRMED** (explicit sets verified; upper bound is immediate from (L12)) |
| LP recount 1,313 (724 M, 589 M^T) / 681 keys | **REPRODUCED** with the unchanged `qb_lp.py`; rows implemented as stated |

No lower bound is claimed by qbound and none is confirmed; 1,313 claims remain open by LP status only.

## 1. Definitions
Represented/missing (Lemma 4.1 definitions, q over all x+y even signals), type (r,u,v), anchored (r>=1), full (r=3, hence a full value via Lemma 4.4 + F3), bright/dark, h_0, U_0, D_0 = U_0 - h_0, q_D, K_l, J, k_l are all used exactly as PROOF.md defines them. New: kind-0 (all three ee signals represented), kind-1 (exactly one missing and bright), y_2 = rest; `circuit_check.py` implements exactly this.

## 2. Step-by-step checks

**N1.** At one helper, equal labels are excluded by the matching property. Across two full helpers i != j with edges i-a, j-a' of the same label: the label of any odd-graph edge (odd+odd, odd+even, including the output-type edge o = b + l) has mask = XOR of its two ends, so `h_i + a = h_j + a'`. Same vertex a = a' gives h_i = h_j (impossible). Otherwise `h_i + h_j = a + a'` is a boundary-pair value, forbidden by Lemma 4.5 (F4: the six relations of two adjacent full values have rank 5, against Lemma 4.4). The XOR is symmetric, F4 is about unordered pairs and holds for both boundaries (recomputed: 360/504 adjacent pairs of rank 5, all others rank 6). Row constant `G - 32 - h - q` (only new row depending on G). Needs only normalization.

**(G*).** Retained family = references + represented H-B + missing H-B at anchored helpers + kind-0 + kind-1 gate equations: distinct gate equations, independent (so a kind-0 equation can never be a combination of the others). N = (x+y-q) + R + (U-U_0) + y_0 + y_1. Touched non-boundary coordinates m = (x+y-q) + (h-h_0) + (q-q_D): unanchored helpers and dark labels untouched because a missing H-B row at an anchored helper has a bright label and a kind-1 missing signal is bright by definition. Rank-nullity: dim V_B >= N - m = 32 - y_2 - z - D_0 + q_D (Lemma 4.2). Membership: after adding references, kind-0 rows are zero-sum sets of weight 6 (weights 2, 4 excluded by F2, weight 0 by independence), kind-1 rows E_l + (P' Δ P'') are 2/4-forms of the bright label l (pairs distinct since labels distinct). A combination with zero non-boundary part uses no reference, an even number of rows at each anchored helper (pivoting leaves the sum unchanged and yields six-sets and forms E_l + T_i^0 Δ {b}), and an even number of forms at each bright label, pairing into K_l. Hence V_B ⊆ R_6 + sum_bright K_l. Verified exactly on 2,236 phases: touched = m, dim V_B = N - m on every phase, V_B reduces to 0 modulo R_6 + sum_bright K_l. Wording remarks: "after adding references it is a subset of the gate equations" has the order reversed; the weight-0 kind-0 case should be mentioned.

**(L7*).** References + represented H-B eqs of helpers meeting l + their missing rows of label l + kind-1 eqs with missing signal l: subset of gate equations; invertible transformations give W_l + Y_l vectors in C_l, independent, <= rank(C_l) <= 7 (F6). Verified per label (explicit forms independent) on all phases.

**(L12*).** {T + T_i^0} ∪ {kind-0 rows} is the residual of an independent family after pivoting; all in R_6. Verified exactly; tight on 4 phases.

**(I).** A missing even signal l occurs in exactly d_l + 1 equations (defining gate + d_l operand uses; no terminal): U_l + V_l + ee_l = d_l + 1 <= 4 + 2 f_l by (3.2), which holds for every signal (Lemma 3.2 is about any accumulation), even+even occurrences included, as in (L10). sum ee_l >= y_1 + y_2; F_miss + F_H <= F. Verified per label on all phases.

**(Q0).** q = 0 gives y_2 = 0, U_0 = 0, q_D = 0, no bright labels; (G*) with J = R_6. M: z >= 12 + h_0 (new). M^T: z >= 4 + h_0.

**y -> y_2.** (L13)-(L15), (L17), (L18): y enters only through (G); per-label bounds are y-free. (L13*), (L14*): `W_l + Y_l <= rank(C_l) <= 7 - 2k_l` (F9); A_l = 1 forces k_l = 0 (F10) and rank <= 6 except F11's four M labels, at most two met at once, unchanged. (L19), (L20): kind rows add y_0 + y_1 to the residual count and no coordinate; kind-0 rows in R_6 ⊆ R_10; a kind-1 label is bright, has a <= 4 form, so every difference at it has weight <= 10 (equivalently by F13 it is not active), so the quotient bounds z_1 and 2(z - z_0)/3 are untouched. Verified on all 1,118 M^T phases: count identity holds and the extended family's residual is 0 modulo R_10. (L22): weights <= 8, y_2 = 0 at q = 0.

**Lemma S.** Triples of one value are pairwise disjoint (shared element gives two distinct pairs with equal XOR, against F2). T_i^0 ∪ T is a six-set through P_l. A vanishing combination of these is a vanishing combination of represented relations in which each H_i + T (T != T_i^0) appears exactly once, nontrivial, against Lemma 4.4 (correctly applied across helpers). S2 needs "no pair with sigma = 1": recomputed. Verified per label on all phases; no r >= 2 helper meets a poor label.

## 3. Independent finite facts (`qcheck/ff_check.py`, from `circuits/aes-mixcolumns/aes-mixcolumns.mat.txt`, 6 s, ALL PASSED)
F2 2,016 pair values; F3 40,704/360/80 and 40,320/504/112; F5 60/20 and 84/28; F4 360 rank-5 / 2,800 rank-6 and 504 / 5,712; F6 histograms identical to PROOF.md; S1 sigma {0:1704, 2:66, 3:228, 4:6, 5:12} and {0:1590, 2:78, 3:312, 4:12, 5:24}; `sigma(P) = rank(C_l) - 1` for all 2,016 pair values and every 4-form of a pair value is disjoint from the pair; rich pairs 122/160/30 (312) and 160/224/42 (426); REPORT's top(m) formula exact for m <= 44; N3max: explicit sets of 10 (M) and 14 (M^T) full values with 30 / 42 relations independent and pairwise non-adjacent; rank of all full-value lines = rho_6.

## 4. Independent circuit re-check (`qcheck/circ_check.py`, `circ_check.log/.json`, 23 s, PASSED)
559 circuits (13 package controls, 3 repo circuits, 303 ymax reconstructions, 240 random loose/rand reconstructions), 2,236 phases (1,118 per orientation), own odd-graph/label/type/bright/kind/rank code (reused only `stress.Circuit` and `profile_real.reconstruct*`), own R_6, R_10 (rho_10(M^T) = 29, words 84/276/1,300), sigma, C_l. All claims checked in strong form: **0 violations**. Tightness: (G*) with J = R_6 tight on 60 M + 52 M^T phases (slack range 0..6); (L12*) tight on 2 + 2; N1 slack >= 18 (M), >= 23 (M^T); (L7*) aggregate >= 24/47; (I) >= 32/41; (L13*)/(L14*)/(L15*) >= 16/18/11 (M), 56/56/26 (M^T); (L17*) >= 30/33; (L18*) >= 65; (L19*)/(L20*) >= 3/9; n_3 up to 4; no phase with q <= 6, so (Q0) and the small-q regime are untested by circuits.

## 5. LP recount (`qcheck/run_lp.sh`, `lp_rerun.log`, unchanged `qb_lp.py`)
base 1,508 (846, 662) / 1,134; Gstar 1,477 (821, 656) / 1,051; N1 1,355 (755, 600) / 755; **GstarN1 1,313 (724, 589) / 681** (by q 1:57, 2:30, 3:57, 4:72, 5:197, 6:151, 7:61, 8:54, 10:2). Implementation reviewed: y_0, y_1, y_2 are free nonnegative variables with y_0 + y_1 + y_2 = y (valid relaxation); the LP would set y_2 = y unless (I) forces y_0 >= y - (4q + 2F - U - 2 sum f_min), which then enters (L12*) and lowers y_2 in the (G)-rows; (L7*), (L12*), (I), (Q0) as `n_{r=0} <= z - (32 - rho_6)`, N1 with G = 75, `+y1 / -c y2` placed correctly in L13-L20/L22, (L2)/(L8) keep constant y (correct), pre-filters unchanged.

## 6. What a referee would still want
1. (G*) proof written in package style (family listed, independence order fixed, weight-0 case, rank-nullity step).
2. Row-by-row justification of `y -> y_2` with the facts used (F9/F10/F11 for L13*/L14*; F13 for L19*/L20*; rho_8(M^T) = 29 for L22*).
3. Statement that the new rows need only normalization (no Lemma 7.4).
4. Exact Farkas certificates (two checkers, mutation tests) for the 6,103 excluded claims; the G-dependent N1 constant in the certificate format.
5. The integer-oracle figure 1,167 is uncertified and should not be quoted as a result.
6. New rows added to the package's `stress.py`, including per-label strong forms.
7. Small-q evidence: no known circuit has q <= 6.
8. Minor wording: (Q0) M^T "weaker than 10.3(ii)"; "(G*) slack 0..10" is 0..6 here.
9. Free strengthenings: (L18) with `+ y_1`.

## 7. Independent LP implementation (`lp_indep.py`, written by the agent, run by the coordinator after the WSL restart)
See `lp_indep.log` next to this file for the output (expected: 1,134 / 755 / 1,051 / 681 keys and 1,313 survivors if the independent rows agree with `qb_lp.py`).
