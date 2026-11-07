# New universal inequalities for the MixColumns lower-bound machinery, and their effect at G = 75

qbound agent report, 2026-11-07 (about two hours). Working directory `~/xs-campaigns/2026-11-07-sprint/qbound/`. The git repository was read only; the proof package was used from the replayed copy `lb76/pkg_copy/` (unchanged; `lp_regen.py` and `stress.py` imported). One python process at a time under `nice -n 12`; total compute about 12 minutes.

Labels on every claim: **[proved]** (proof written below, package lemmas and finite facts used as black boxes), **[finite-checked]** (computed exactly by a script here), **[measured]** (script output on known circuits or on the LP model), **[conjecture, consistent with N circuits]**, **[guess]**. No lower-bound improvement is claimed: coverage at G = 75 was not re-verified in certificate style, and every scan leaves survivors.

(Transcribed by the coordinator from the agent's final message, 2026-11-07 ~20:00 UTC; the agent could not write this file itself. Content unchanged apart from HTML entities.)

## 0. Results in ten lines

1. **Survivor table for hypothetical rows `q >= c`** (package LP model, keys filtered): c = 1..8 kills 0 / 11 / 76 / 332 / 676 / 1,026 / 1,305 / 1,466 of the 1,508 claims; `q + z >= 9` per phase kills all 1,508. [measured]
2. No `q >= c` is provable in this framework: `q` is forced only through `q + z = sum_H d_v + y - 32` (4.1); real circuits have `q >= 10` because they have `y >= 10`, `h >= 13`, not by a label obstruction. [proved identity; measured]
3. **New row (N1) [proved]:** `3 n_3 <= x + y - q` (the represented edges of full helpers carry pairwise distinct labels). The LP's small-q survivors are built from 7-13 full helpers per phase (real circuits: 0-3). (N1) alone cuts LP-feasible keys 1,134 -> 755 (the `q = 1` M^T cluster 323 -> 63) and claims 1,508 -> 1,355.
4. **New family (G\*) [proved]:** the package's elimination inequality (G) with even+even gates of represented labels retained: `y -> y_2` in (L13)-(L20),(L22); plus `L12*: sum(r-1)_+ + y_0 <= rho_6`, `L7*: W + y_1 <= 7q`, `y_1 + y_2 + U + 2F_H <= 4q + 2F`, and for `q = 0` in M: `z >= 12 + h_0`. (G\*) with `J = R_6` has slack 0 on some real phases; every package row has slack >= 10 there.
5. **Rich-label lemma [proved] + [finite-checked]:** at a represented label with pair P, `sum_{i meets l}(r_i - 1)_+ <= sigma(P)` (rank of weight-6 zero-sum sets through P); `sigma = 0` for 1,704/2,016 pairs (M), 1,590 (M^T), else 2..5. Every represented label at an `r >= 2` helper is one of 312 (M) / 426 (M^T) rich pairs; confirmed on all 1,264 phases of 316 circuits. Its aggregate LP row adds nothing at G = 75.
6. **Combined (package + G\* + N1):** 1,508 -> **1,313** claims (724 M, 589 M^T); keys 1,134 -> **681**. With integrality of the local systems as oracle (branch-and-bound, not certificates): **1,167** claims (636 M, 531 M^T), 497 keys.
7. **Negative finite fact:** the largest set of full values with independent relations has exactly `rho_6/2` elements (10 M, 14 M^T): L12 is tight as a rank statement. [finite-checked]
8. All new rows: zero violations on 13 controls (52 phases) + 303 real circuits (1,212 phases). [measured]
9. Surviving configurations: 7-10 full helpers using nearly every even signal as a label (M^T q = 1-3; M q = 2); at q = 5-6, five or six (3,1,0) helpers plus an unanchored hub carrying 4-6 missing labels (section 7).
10. Finite searches that would decide them: section 8.

## 1. Survivor table (step 1) [measured]

`kill_table.py` runs the package `lp_regen.py` model at G = 75 (3,708 states, 7,416 oriented claims; baseline 1,508 survivors, 1,134 LP-feasible keys `(h,y,F,q,z,ori)`), declaring a key infeasible when it violates the row.

| hypothetical row (every phase) | surviving claims (M, M^T) | LP-feasible keys left (of 1,134) |
|---|---|---|
| none | 1,508 (846, 662) | 1,134 |
| q >= 1 | 1,508 (846, 662) | 1,103 |
| q >= 2 | 1,497 (839, 658) | 780 |
| q >= 3 | 1,432 (806, 626) | 740 |
| q >= 4 | 1,176 (676, 500) | 594 |
| q >= 5 | 832 (465, 367) | 475 |
| q >= 6 | 482 (262, 220) | 270 |
| q >= 7 | 203 (109, 94) | 117 |
| q >= 8 | 42 (21, 21) | 56 |
| q + z >= 2 / 3 / 4 / 5 | 1,498 / 1,432 / 1,176 / 832 | 1,098 / 1,042 / 932 / 750 |
| q + z >= 6 / 7 / 8 | 485 / 207 / 42 | 506 / 290 / 141 |
| **q + z >= 9** | **0** | 32 |
| q + z >= 11 | 0 | 0 |
| q >= 4 / 5 / 6 / 7 on M^T phases only | 1,216 / 958 / 655 / 374 | 762 / 744 / 633 / 595 |
| q >= 4 / 5 / 6 / 7 on M phases only | 1,480 / 1,358 / 1,038 / 636 | 966 / 865 / 771 / 656 |
| q >= y / y-1 / y-2 / y-3 / y-4 | 776 / 949 / 1,125 / 1,288 / 1,396 | 514 / 601 / 697 / 798 / 907 |
| q + z >= y / y+1 / y+2 / y+3 | 776 / 589 / 432 / 293 | 672 / 590 / 493 / 403 |
| 2q + z >= 4, q + 2z >= 4 | 1,497, 1,397 | 1,042, 1,010 |

`q >= 1` kills nothing (the 31 `q = 0` keys are never load-bearing); survivors need about `q >= 6` on every phase or `s >= 9`. Data: `kill_table_g75.json`, `kill_table.log`.

## 2. What q counts and why no `q >= c` is provable here

A label is represented if some gate joins two boundary signals with it (`l = b + b'` odd+odd, or output `o = b + l`), missing otherwise; each represented label has exactly one B-B edge (Lemma 4.1/F2). From Lemma 4.2 and (4.1):

    q + z = sum_{v in H} d_v + y - 32,    equivalently    q = y - 32 + x_H + o_H,

(`x_H` = odd+odd gates with a helper operand, `o_H` = outputs whose odd operand is a helper; `#B-B = (x - x_H) + (32 - o_H)`). Lemma 7.4 gives `q + z >= 2h + y - 32` = (L2) with degree >= 3. On real 88s (`y = 14..19, h = 13..20`) this forces `s >= 8..18`; measured `q = 10..16` is just that. Survivors have `y <= 11`, so (4.1) allows `s ~ 0`, and the package proves only `q + z >= 1` (Lemma 10.3). Hypothetical phases consistent with every package lemma have `q = 1` (section 7). Hence `q >= c` (c >= 1): **[conjecture, consistent with 316 circuits; no proof route]**; `q >= 7`: **[guess, probably false on hypothetical tails]**. The provable statements below act on the helper types a small-s phase must contain.

## 3. Row (N1) [proved]

**Lemma N1.** In every normalized circuit of either orientation, `3 n_3 <= x + y - q`; in a local system at `G` gates, `sum_{r=3} 3 n_{r,u,v} <= G - 32 - h - q`.

*Proof.* A full helper `i` with represented edges `i-a_1, i-a_2, i-a_3` has labels `h_i + a_j`, distinct because at one vertex the label determines the other end (Lemma 4.1). If full helpers `i != j` shared a represented label `l` via `i-a`, `j-a'`, then `a != a'` (else `h_i = h_j`) and `h_i + h_j = a + a'` is a boundary-pair value, contradicting Lemma 4.5 (F4). So the full helpers' represented edges carry `3 n_3` distinct represented labels. []

Needs only normalization and F2-F4 (via Lemmas 4.1, 4.4, 4.5): valid on every phase and on the controls.

**Why it bites.** Baseline LP vertices (`qb_lp.py vertex`): key `(14,3,3,1,1,Mt)` uses 12-13 type-(3,0,0) helpers, `(13,4,4,1,2,Mt)` 11, `(12,5,5,1,3,Mt)` 10-11, `(13,4,4,3,2,M)` 10, `(12,5,5,2,3,M)` 9, limited only by L12. With `h = 14, y = 3` at G = 75 there are 29 even signals and 28 represented labels, so `n_3 <= 9`: the first four keys become infeasible, the last survives with `n_3 = 9`.

**Effect:** claims 1,508 -> 1,355 (755 M, 600 M^T); keys 1,134 -> 755 (by q: 0:31, 1:323->63, 2:40, 3:146->64, 4:119->82, 5:205, 6:153, 7:61, 8:54, 10:2). **Known circuits:** `n_3 = 0..1` (M), `0..3` (M^T) real, `0..4` controls; slack 18..45.

## 4. The (G\*) family [proved]

Lemma 10.2 proves (G) `32 - dim J <= y + z + D_0 - q_D + sum_bright k_l` by retaining references, represented H-B equations and anchored missing H-B equations; `y` is the price of dropping the even+even equations.

**Definitions.** An even+even gate `l'' = l + l'` is *short of kind 0* if all three signals are represented, *kind 1* if exactly one is missing and bright (has a missing H-B edge at an anchored helper); `y_0`, `y_1` their numbers, `y_2 = y - y_0 - y_1`.

**Lemma G\*.** For every normalized circuit and every `J >= R_6` (with `k_l` as in Lemma 10.2):

    (G*)   32 - dim J <= y_2 + z + D_0 - q_D + sum_{l bright} k_l;
    (L7*)  W_l + Y_l <= rank(C_l) <= 7 at every missing label (Y_l = kind-1 gates with missing signal l), hence W + y_1 <= 7q;
    (L12*) sum_i (r_i - 1)_+ + y_0 <= rho_6;
    (I)    y_1 + y_2 + U + 2F_H <= 4q + 2F;
    (Q0)   q = 0  =>  z >= 32 - rho_6 + h_0   (M: z >= 12 + h_0; M^T: z >= 4 + h_0, weaker than Lemma 10.3(ii)).

*Proof of (G\*).* Retain Lemma 10.2's family plus all kind-0 and kind-1 equations; after adding references (invertible) it is a subset of the gate equations, hence independent, of size `(x+y-q) + R + (U-U_0) + y_0 + y_1`. Non-boundary coordinates touched: the `x+y-q` represented labels, `h - h_0` anchored helpers, `q - q_D` bright labels (a kind-1 gate's missing signal is bright, so no new coordinate). So the span contains at least `R + U - U_0 + y_0 + y_1 - (h-h_0) - (q-q_D) = 32 - y_2 - z - U_0 + h_0 + q_D` independent boundary relations (Lemma 4.2). Reduced rows: represented H-B `H_i + T`; missing H-B `H_i + B_b + E_l`; kind-0: sum of three boundary pairs, a zero-sum set of weight <= 6, in `R_6` (weights 2, 4 excluded by F2); kind-1: `E_l + D`, `D` a 2- or 4-subset with XOR `l`, a form in `C_l`. A combination with vanishing non-boundary part uses an even number of rows at each anchored helper; adding the pivot `H_i + T_i^0` turns them into `T + T_i^0` (in `R_6`) and forms `E_l + T_i^0 + B_b`; at each bright label the forms used pair into differences in `K_l`. So the residual lies in `R_6 + sum_bright K_l`, dimension <= `dim J + sum k_l`. []

*(L7\*):* all forms of `l` (H-B forms and kind-1 forms) are reduced rows of one independent family, so independent, in `C_l`, rank <= 7 (F6). *(L12\*):* the `(r_i - 1)` differences and the `y_0` kind-0 rows are the residual of an independent family after pivoting: independent, in `R_6`. *(I):* each gate counted by `y_1 + y_2` contains a missing signal; a missing label occurs in `d_l + 1 <= 4 + 2f_l` equations ((3.2), as in (L10)): its `U_l` H-B edges, H-H edges and even+even occurrences; sum, use `F_miss + F_H <= F`. *(Q0):* `q = 0` gives `y_2 = 0, U_0 = 0`; apply (G\*) with `J = R_6`. []

**Consequences for the rows.** In (L13)-(L18) `y` enters only via (G); in (L19), (L20), (L22) (M^T, modulo `R_10`) only because even+even equations are dropped, and kind-0 rows (weight <= 6) and kind-1 rows (forms of size <= 4, differences of weight <= 10) lie in `R_10`; by F13 an active six-form label has no 2/4-form, so L20's per-label bound is untouched. Hence all these rows hold with `y -> y_2`, and (L13), (L14) with `W -> W + y_1`.

**Effect:** G\* alone: claims 1,508 -> 1,477, keys 1,134 -> 1,051 (all 31 `q = 0` keys die by (Q0)). G\* + N1: **1,313 claims (724 M, 589 M^T), 681 keys** (by q: 1:57, 2:30, 3:57, 4:72, 5:197, 6:151, 7:61, 8:54, 10:2). **Known circuits:** (G\*) with `J = R_6` slack 0..10, exactly 0 on some real M^T phases and control phases; (L12\*) 6..15 real, 0 on a control phase; (L7\*) >= 24; (I) >= 32; no violation on 1,264 phases. Two new rows are tight on real circuits while every package row has slack >= 10: they cannot be sharpened further without breaking on a real circuit.

## 5. Rich labels [proved] + [finite-checked]

**Lemma S.** For a boundary pair `P` let `sigma(P)` = rank of the weight-6 zero-sum boundary sets containing `P`. In every normalized circuit, at every represented label `l` with pair `P_l`: `sum_{i : H-B edge at i with label l} (r_i - 1)_+ <= sigma(P_l)`.

*Proof.* Helper `i` meeting `l` via `i-a_i` carries `H_i + T_i^0`, `T_i^0 = {a_i} ∪ P_l`. Any other triple `T` of `h_i` is disjoint from `T_i^0` (a shared element leaves two distinct pairs with equal XOR, against F2), so `(H_i + T_i^0) + (H_i + T) = T_i^0 ∪ T` is a weight-6 zero-sum set through `P_l`. These sums are independent: a vanishing combination is a vanishing combination of represented relations in which each `H_i + T` (`T != T_i^0`) occurs at most once, against Lemma 4.4. []

**Finite fact S1** (`pair_sigma.py`): sigma histogram M `{0:1704, 2:66, 3:228, 4:6, 5:12}`, M^T `{0:1590, 2:78, 3:312, 4:12, 5:24}` (`sigma = rank(C_l) - 1` for the pair value; every 4-form of a pair value is disjoint from its pair by F2). Rich pairs by kind: M 122 input-input, 160 input-output, 30 output-output; M^T 160 / 224 / 42. `top(m)` (sum of m largest sigma): M `5m` (m <= 12), `60 + 4(m-12)` (<= 18), `84 + 3(m-18)`; M^T `5m` (<= 24), `120 + 4(m-24)` (<= 36), `168 + 3(m-36)`.

**Corollary S2 [proved].** Every represented label at an `r >= 2` helper is rich (sigma >= 2); `6 n_3 + 2 n_2 <= top(x + y - q)`. **Checks:** no `r >= 2` helper meets a poor represented label on any of the 1,264 phases. The aggregate row changes nothing at G = 75 (survivors' `x + y - q = 27..31`, `top >= 100` vs `6n_3 + 2n_2 <= 60`). Its value is qualitative: only 15 % of pairs can label repeated helpers, which a realizability search needs.

**Negative finite fact N3max** (`full_helpers.py`): the largest set of full values with independent relations has exactly `rho_6/2` elements, 10 (M) and 14 (M^T): randomized greedy finds such sets, the Lovasz matroid-parity rank over GF(2^32) (three seeds; a substitution never exceeds the generic rank) gives 20 and 28, and an exact DFS closes immediately. L12 cannot be sharpened on `n_3` as a rank statement; (N1) is what limits full helpers.

## 6. Controls

`circuit_check.py`: all quantities of sections 3-5 on four orbit steps of the 13 controls and 303 real circuits (same `ymax` reconstruction, package `Circuit`/`analyse`/`canonical_transpose`); 1,264 phases; violations of (N1), (G\*/R_6), (L12\*), (L7\*), (I), Lemma S: **none**. No phase has `q = 0` (`q >= 7` everywhere), so (Q0) is not exercised. `qb_lp.py` in `base` mode reproduces the package model exactly (1,508 survivors, the same 1,134 keys).

## 7. What survives, and the obstacles

After G\* + N1, keys concentrate at `q = 5, 6` (348 of 681). Vertices (`step3.log`): `(11,5,5,5,0,Mt)`: five (3,1,0) (L6 tight: each missing label meets one full helper) plus (2,2,0),(2,3,0),(1,3,0),(1,4,0). `(10,6,6,6,0,M)`: six (3,1,0), three (2,2,0), a fractional unanchored hub (0,6,0)/(1,5,0) carrying all six missing labels (L23 tight). `(12,5,5,2,3,M)`: seven (3,0,0) + two (3,1,v) (`n_3 = 9`, N1 tight 27 <= 29), (1,2,0), (2,1,3).

**Obstacle 1 (full helpers using all labels).** Nine compatible full values (sets of 10 exist) occupying 27 of 29 represented labels; every package lemma holds. Excluding it needs: the 27 labels are specific rich pairs inside the helpers' triples, each needing its own B-B gate, with 9 defining and 18+ use gates acyclic in a phase with `x = 26, y = 5`. Type counts cannot see this.

**Obstacle 2 (hub helpers).** Type (0,6,0) at `q = 6`: `h = b_j + l_j` for six missing labels; with L6 tight `h = f_j + (boundary pair)` for six distinct compatible full values. A finite question (section 8 b).

**Obstacle 3 (dark labels).** For M^T `q = 1`, the case split *bright* (`z + D_0 >= 3`) / *dark* (`y_2 + z + D_0 >= 5`) from (G\*) is stronger than the LP rows (which drop `q_D`); not implemented.

**Integrality.** 497 of 681 keys are integer-feasible; with the integer oracle the scan leaves 1,167 claims (636 M, 531 M^T) — branch-and-bound, not certificates.

**Unused two-phase constraint.** By identity (E) and Lemma 7.4, a constant-profile tail has phases with `E_B,e + E_B,o <= shortfall <= 4`: nearly every input used at most twice, every output at most once. Real 88s have `E_B = 0..7`, so no contradiction, but none of (L1)-(L23) or the new rows exploit it. [derived]

## 8. Finite searches that would decide the remaining configurations

(a) **Full-helper label budget:** enumerate sets of `n_3 = 7..10` (M) compatible full values, the `3^{n_3}` label choices (one pair per triple), and test the even-signal budget `x + y - q` against the remaining helpers' rich-label needs and kind-0 six-set relations (L12\*).
(b) **Hub helpers:** for each odd value `h`, the maximum number of pairwise compatible full values `f` with `h + f` a boundary pair; one pass over 80 x 2016 (M).
(c) **Dark-label case split:** local systems per `q_D = 0..q` keeping the `-q_D` terms, with `q - q_D <= U - U_0 <= 4(q - q_D) + 2F` and the split `y_2 = y_2^dark + y_2^multi`, `y_2^dark <= 4q_D + 2F`, `y_1 + y_2^dark + 2y_2^multi <= 4q + 2F - U - 2F_H`; each case Farkas-certifiable.
(d) **Integrality:** certify the 184 LP-feasible / integer-infeasible keys by branch-and-bound trees with Farkas leaves.
(e) **Boundary fan-out:** joint two-phase model with `E_B,e + E_B,o <= budget - k - l`; an output used once has a single-gate accumulation tree, fixing its transpose helper's type.

## 9. Statements and labels

| statement | label |
|---|---|
| survivor table (section 1) | [measured] |
| `q + z = sum_H d_v + y - 32`, `q = y - 32 + x_H + o_H` | [proved] (Lemma 4.2, (4.1)) |
| real `q >= 10` forced by `y, h` via (4.1) | [measured] 1,212 phases, [derived] |
| `q >= c` universally | [conjecture, consistent with 316 circuits]; `q >= 7` [guess: likely false on hypothetical tails] |
| (N1) | [proved] (Lemmas 4.1, 4.5) |
| (G\*), (L7\*), (L12\*), (I), (Q0), `y -> y_2` in (L13)-(L20),(L22) | [proved] (Lemma 10.2's argument, Lemma 4.4, F2, F6, F13, (3.2)) |
| Lemma S | [proved] (Lemma 4.4, F2) |
| sigma histograms, `top(m)`, rich-pair counts | [finite-checked] |
| N3max = rho_6/2 | [finite-checked] |
| LP effects 1,508 -> 1,477 / 1,355 / 1,313; keys 1,134 -> 1,051 / 755 / 681 | [measured] |
| integer oracle: 497 keys, 1,167 claims | [measured] (not certified) |
| zero violations on 316 circuits / 1,264 phases; tightness | [measured] |
| surviving configurations, obstacles | [measured] + [derived] |
| `E_B <= shortfall` on a hypothetical tail | [derived] from identity (E) |
| any bound beyond 75 | **not claimed** |

## 10. Files in `~/xs-campaigns/2026-11-07-sprint/qbound/`

`kill_table.py`, `kill_table.log`, `kill_table_g75.json`; `qb_lp.py` (variants `base`, `Gstar`, `N1`, `N7`, `INT`; modes `scan`, `vertex`, `milp`), `scans.log`, `scan_*_g75.json`, `step3.log`, `milp_GstarN1_g75.json`; `full_helpers.py`, `full_helpers.log`, `full_helpers_M_Mt.json`; `pair_sigma.py`, `pair_sigma.log`, `pair_sigma.json`; `circuit_check.py`, `circuit_check.log`, `circuit_check.json`; drivers `run_vertices.sh`, `run_step2.sh`, `run_step3.sh`.
