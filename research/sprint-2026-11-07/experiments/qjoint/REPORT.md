# Joint hub configurations at G = 75: vertex classification, the joint gate-equation family, finite fact J1, the label-class rows, survivor recount

qjoint agent, 2026-11-08 (about 2 h; transcribed by the coordinator from the agent's final message,
the agent could not write this file). Working directory ~/xs-campaigns/2026-11-07-sprint/qjoint/.
Read only: the repository, lb76/pkg_copy/, qbound/, qreal/, qhub/, qhubcheck/, qcert3/, bridge/.
qhubcheck/lp_qhc.py was copied to qj_lp.py and extended by patch_qj_lp.py; qhub/hub2.py's geometry was
re-implemented in qj_geo.py; lp_regen.py, stress.py and bridge/profile_real.py imported unchanged. One
python process at a time under nice 8; total compute about 15 min.

THE LOWER BOUND REMAINS L(M) >= 75. The final scan leaves 686 oriented claims open by LP status and no
certificate-style coverage was produced for the rows of this report. J1 has ONE implementation (no
second independent one yet); the MILP oracle's status was not recorded (a 20 s time-limit hit would
count as "infeasible").

## 0. Results in ten lines

1. Vertex classification [measured]: of the 551 load-bearing keys, 450 have an integer-feasible case
   system (HiGHS MILP on every LP-feasible (hub, dark) case) and 101 are LP-feasible but
   integer-infeasible (by q 1: 2, 2: 10, 3: 22, 4: 39, 5: 8, 6: 3, 7: 14, 8: 2, 9: 1; M 64, M^T 37),
   among them both load-bearing M^T q = 1 keys. Integer solutions split into configurations in which
   hubs are forced to meet and share full helpers (115 keys in every dumped solution, 287 in some) and
   configurations with no hub forced to meet a full helper at all.
2. The joint family [proved]: for any set of hubs meeting full helpers, the union of the per-hub
   families F(h_k, R_k, S_k) with shared full-helper coordinates, plus one mixed vector H_k + H_k' +
   P(h_k + h_k') per pair of hubs sharing a hub-only missing label, is linearly independent in any
   normalized circuit containing the configuration (C1's pivot steps applied to all hubs at once;
   Lemmas 1.1, 4.1, 4.4 and its proof, 4.6; F2, F3).
3. Finite fact J1 [finite-checked, both orientations, one implementation]: two LIMIT hubs (non-full
   helpers with r + m = 3) never share a missing label: neither the same full-met label (0 independent
   joint families among M 4,224 / M^T 13,728 candidate pairs) nor a hub-only label (exhaustive over all
   2,016 pair-value neighbours of every limit configuration with every partner configuration: the
   largest partner class r' + m' that can share a hub-only label with a limit hub is 2). Two r = 2
   limit hubs cannot share a hub-only label at all (M: 34 PV-pairs among 12 values, 0 independent; M^T:
   76 among 24, 0).
4. Realizable locally [finite-checked]: two limit hubs CAN share a full helper when they meet it at
   different labels (M: 672 / 96 / 1,040 / 128 independent pairs in the classes (0,3)-(1,2), (0,3)-(2,1),
   (1,2)-(1,2), (1,2)-(2,1); M^T also (0,3)-(0,3): 1,728), and two r = 0 hubs with m = 2 can share a
   full-met label (M: 27,072 independent pairs). "Several hubs on the same few full helpers" is not
   excludable by local conditions; "limit hubs sharing labels" is.
5. Lemma P (label-class rows P1-P5) [proved]: in the exact hub case A = a the missing labels split into
   a full-met class and a hub-only class; Lemma 4.6 (pairs of labels co-occur at most once), the packing
   numbers D(a,3,2) and the per-label rank (proof of (L7)) give five rows on the type counts with the
   per-type interval m in [max(0, u - (q - a)), min(u, 3 - r)].
6. Row LIM [proved from J1 + Lemma 4.6]: in case A = a the types with u = (3 - r) + (q - a) are limit
   hubs carrying every hub-only label: at most one such helper when a < q; label-disjoint (sum u n <= q)
   when a = q.
7. Circuit check [measured]: 13 controls + 303 real circuits, 1,264 phases: 0 violations of P1-P5,
   LIM, J1, H2; A = 0 and no limit hub on every phase (only P3 / P4-hub-only exercised; min slack 15 / 5).
8. Recount on the 551 load-bearing keys [measured]: P1-P5 alone 551 -> 452; with LIM 551 -> 388.
9. Full scan [measured]: claims 789 -> 686 (M 372, M^T 314), a subset of the 789 with identical (k, l)
   on 633; shortfall 0/1/2/3: 382 / 221 / 59 / 24; 36,573 keys touched, 814 LP-feasible, 483 load-bearing
   (M 235, M^T 248). Cumulative: 1,508 -> 1,313 -> 996 -> 863 -> 789 -> 686.
10. The M^T q = 1 family: its two load-bearing keys are integer-infeasible; the enumeration of 7-8-sets
    of compatible full values was not run. The bound stays 75.

## 1. Vertex classification [measured] (qj_vert.py, vertices.json, vert_summary.log)
For each of the 551 load-bearing keys and each LP-feasible (hub, dark) case: three LP vertices and two
integer solutions (HiGHS MILP, 20 s limit; status not recorded). Per solution: n_3, full helpers with
u >= 1, A, hub types with m_lb = max(0, u - (q - A)) and m_ub = min(u, 3 - r), forced-sharing indicator
share_lb = max(0, sum n m_lb - nf1), L5 slack. 450 keys integer-feasible; 101 not (candidates for
branch-and-bound certificates). Of 1,860 integer solutions: no hub forced to meet a full helper in
many (M q = 4: 96, q = 5: 132; M^T q = 2: 37, q = 3: 57, ...); hubs forced to share full helpers in
others (M q = 4: 90, q = 5: 100, q = 6: 107; M^T q = 3: 52, q = 4: 130, ...); L5 slack 0 in 1,687 of
1,860. Dominant forced-sharing shapes: (2,2,0) hubs with exactly one full-met label together with r = 0
or 1 hubs with m >= 2, almost always with L5 tight; whenever m_lb = m_ub the hub is a limit hub.

## 2. The joint gate-equation family [proved]
Configuration: hubs k = 1..K with masks h_k, represented triples R_k (|R_k| = r_k <= 2), full-met
missing labels met through edges to full helpers f in S_k (distinct by Lemma 4.6; pairs P(h_k + f)
by F2); X = the hub pairs sharing a hub-only label (then h_k + h_k' is a pair value). Gate equations:
(1) the B-B reference of every represented label on a represented edge of a hub or of a full helper
of S; (2) the represented H-B equations of the hubs and of the full helpers of S; (3) for every
full-met label met by f and hubs k_1..k_t the t + 1 missing H-B equations; (4) for {k, k'} in X the
two missing equations of their shared label. Equations of pairwise distinct gates, hence independent
as formal vectors (Lemma 1.1, proof of Lemma 4.4). Pivot 1 (references), pivot 2 (full-met labels: add
f's row to each hub row, delete f's row), pivot 3 (hub-only shared labels: add hub k's row to hub k''s,
delete hub k's row; a hub-only label met by a single hub is deleted). Result: F_joint = {H_f + T} ∪
{H_k + T : T in R_k} ∪ {H_k + H_f + P(h_k + f)} ∪ {H_k + H_k' + P(h_k + h_k') : {k,k'} in X} is
independent in any normalized circuit containing the configuration. FM's per-label condition is a
projection; Lemma 4.5 among the full helpers is implied (F4); Lemma 4.6 restricts which
configurations exist; Lemma O1 was not re-applied.

## 3. The finite searches [finite-checked] (qj_pairs.py, pairs_{M,Mt}.json; qj_limit.py, limit_{M,Mt}.json)
Hubs with r + m >= 2 enumerated from H2's tables (M 13,116 / M^T 24,036 configurations with F(h,R,S)
independent). Pair search over every full value f and every pair of configurations sharing f (M
2,338,252 pairs, M^T 5,136,484): independence of F_joint by sharing mode (same label at f / different
labels; plus a shared hub-only label when h_1 + h_2 is a pair value). Limit search: every limit
configuration (M 192 / 352 / 48 at r = 0/1/2; M^T 480 / 720 / 96) against (a) every hub-only partner
h' = h + p over all 2,016 pair values with every partner configuration and (b) every same-label partner;
M 2,773,888 joint tests, M^T 6,498,128. Results: same-label pairs with both hubs at the limit: 0
independent in every class pair ((0,3)-(0,3): 0 / 1,152 M, 0 / 4,608 M^T; (0,3)-(1,2): 0 / 2,144 and
0 / 6,656; (1,2)-(1,2): 0 / 672 and 0 / 1,824; ...); same-label pairs below the limit are plentiful
((0,2)-(0,2): 27,072 / 58,944 M); different-label pairs of limit hubs exist ((0,3)-(1,2): 672 / 2,624 M;
(0,3)-(0,3): 1,728 / 0 M^T); different labels plus a shared hub-only label with both at the limit: 0.
Largest partner class of a limit hub: hub-only sharing 1 (r = 0), 1-2 (r = 1), 2 (r = 2); same-label
sharing 2 in all classes. J1 HOLDS in both orientations.

## 4. New rows, proofs, circuit check, recount
Lemma P [proved]: with Λ_A the A full-met labels and Λ_0 the q - A others, m_i = |L_i ∩ Λ_A|, e_i =
u_i - m_i; by Lemma 4.6 every pair of missing labels lies in at most one helper's label set:
(P1) sum_{r<3} C(m_i,2) + sum_{r=3} C(u_f,2) <= C(A,2); (P2) sum_{r<3} m_i e_i <= A (q - A);
(P3) sum_{r<3} C(e_i,2) <= C(q - A, 2); (P4) #{helpers with |L_i ∩ Λ_A| >= 3} <= D(A), #{non-full with
e_i >= 3} <= D(q - A), D(a) = D(a,3,2) = floor(a/3 floor((a-1)/2)) minus 1 for a ≡ 5 mod 6 (D(3..10) =
1, 1, 2, 4, 7, 8, 12, 13); (P5) sum_{r<3} r_i m_i <= top(A) - 3A (per-label rank, proof of (L7)/(L7*),
FM's table). LP form in the exact hub case A = a with the per-type interval [m_lb, m_ub], replacing each
term by its minimum over the interval. Row LIM [proved given J1]: in case A = a a non-full type with u =
(3 - r) + (q - a) is a limit hub carrying all hub-only labels: at most one such helper when a < q
(Lemma 4.6 for a <= q - 2, J1 for a = q - 1); label-disjoint when a = q (sum u n <= q).
Circuit check (qj_circ.py): 1,264 phases, 0 violations of P1-P5, J1, H2, LIM (A = 0 everywhere).
Recount (qj_lp.py variant GstarN1HUB2DARKPKFMJOINTLIM, exact integer hub cases A = 0..q with P1-P5 and
LIM in each): load-bearing keys 551 -> 452 (P1-P5) -> 388 (+ LIM); claims 789 -> 686 (372 M, 314 M^T),
subset of the 789, identical (k, l) on 633; 814 LP-feasible / 483 load-bearing keys. What dies: the M^T
q = 4 cluster (175 -> 64 load-bearing keys) and the M q = 3-4 keys whose solutions needed limit hubs
sharing labels. What survives: q = 5-6 (limit hubs with sub-limit partners, and solutions with no
forced hub), the q = 2-3 many-full-helper keys, the M^T small-h q = 7-8 keys.

## 5. The M^T q = 1 family
Its load-bearing representatives (11,7,1,1,4,Mt), (12,5,1,1,4,Mt) are LP-feasible but
integer-infeasible [MILP oracle, not certified]; the planned enumeration of jointly independent
7-/8-sets of full values against the even-signal budget with Lemma S's capacities was not run. The M
q = 2 keys with ten full helpers plus one hub and the M^T q = 2-3 keys with 8-9 are integer-feasible:
open, global [conjecture: decided by the label-sharing geometry].

## 6. Labels
Vertex classification [measured, MILP oracle]; F_joint independence [proved]; J1 and the pair/limit
tables [finite-checked, one implementation]; Lemma P and LP forms [proved]; LIM [proved from J1];
exact split exhaustive [proved]; 0 violations [measured]; recounts [measured]; q = 1 and n_3 = 8-10
families [conjecture]; any bound beyond 75: NOT claimed.

## 7. Files
qj_vert.py/.out, vert_summary.log, vertices.json; qj_geo.py; qj_pairs.py/.out, pairs_{M,Mt}.json;
qj_limit.py/.out, limit_{M,Mt}.json; patch_qj_lp.py, qj_lp.py, fm_tab_{M,Mt}.json, scan_JOINTLIM.out,
lp_qhc_scan_GstarN1HUB2DARKPKFMJOINTLIM.json, lp_qhc_keysfull_...JOINTLIM.json, lp_qhc_keys_...json;
qj_circ.py/.out/.json; run_chain1.sh, run_chain3.sh, chain1.out, chain3.out.
Next referee-grade steps: a second implementation of J1; Farkas certificates for the 103 newly excluded
claims / the 163 keys killed on the load-bearing set; the two global label-sharing searches.
