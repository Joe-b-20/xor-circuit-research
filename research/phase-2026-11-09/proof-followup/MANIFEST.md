# Residual coverage manifest: the 280 open claims at G = 75

Phase 2026-11-09, proof follow-up, 2026-11-10. Machine-readable form: [`scope/coverage_manifest.json`](scope/coverage_manifest.json)
(4.8 MB; one entry per claim and per key). Everything in this document is LP or MILP **status** with the
published combined rows (sprint Addenda A-D plus the October push5/push6 rows), computed with the
independent checker's matrices (`check_combined75.matrix`) and the package driver (`lp_regen.run`).
Nothing here is a certificate, and **the lower bound stays 75**. Evidence tags: [measured] unless stated.

## 1. Objects and definitions

- **Claim**: an oriented claim (scalar state, orientation) of the package's final test at G = 75; the
  state is `(a, b, Y, V, h_e, h_o, l_e, l_o, S_e, S_o, budget)`. A claim is open iff `k <= S_e`,
  `l <= S_o` and `k + l <= budget`, where `k` (`l`) is the least level `s = q + z` at which some even
  (odd) phase key is LP-feasible. 280 claims are open (148 M, 132 M^T); 196 have `k + l = budget`
  exactly (shortfall 0), 66 shortfall 1, 15 shortfall 2, 3 shortfall 3.
- **Key**: `(h, y, F, orientation, q, z)`, a local linear system on helper type counts `(r, u, v)`.
  Even-phase keys of a claim are `(h_e, Y, V, ori, q, z)`, odd-phase keys `(h_o, V, Y, other, q, z)`.
- **Leaf**: `(A = a, q_D = d)`, the exact hub case (`a` full-met missing labels) and dark case (`d` dark
  labels) of a key's case tree (Addenda B-D). A key is excluded iff every leaf is excluded (D.8). A leaf
  is *open* if its case system is LP-feasible; it is *integer-feasible* if the case system has a
  nonnegative integer solution (HiGHS MILP, status recorded; "infeasible" only on status 2).
- **Ladder** of a claim: the LP-feasible even keys at every level `l_e <= s <= min(S_e, budget - l_o)`
  and odd keys at `l_o <= s <= min(S_o, budget - l_e)`. The claim stays open as long as some feasible
  even level `s_e` and odd level `s_o` with `s_e <= S_e`, `s_o <= S_o`, `s_e + s_o <= budget` remain.
  The published "229 load-bearing keys" are only the FIRST level of each side (`s_e = k`, `s_o = l`).
- **Hypotheses** (used to measure coverage, each applied to every leaf of every ladder key): A01 = every
  leaf with `A >= 2` excluded; A01_or_dark = every leaf with `A >= 2` and `q_D = 0` excluded; A0 = every
  leaf with `A >= 1` excluded; INT = every integer-infeasible leaf certified; INT_A01 = INT and A01.

## 2. The counts, reconciled

| quantity | value | what it is |
|---|---:|---|
| open claims | 280 | LP status, driver scan (reproduced today, 109 s) |
| first-level keys ("load-bearing") | 229 | feasible even keys at level `k` and odd keys at level `l` of the 280; exactly one even and one odd key per claim |
| first-level open leaves | 572 | of the 229 keys' 9,432 leaves; by A: 66 / 81 / 115 / 167 / 98 / 38 / 7 for A = 0..6; by q_D: 481 at 0, 91 at 1 |
| first-level leaves with A = 2..4 | 380 | a concentration statement about the 572, not a coverage statement |
| first-level leaves with q_D = 0 | 481 | likewise |
| first-level leaves integer-infeasible / feasible | 164 / 408 | MILP, all 1,388 solves ended with status 0 or 2 (60 s limit never hit) |
| first-level keys with only integer-infeasible open leaves | 62 | certifying them dead would close 44 claims (280 -> 236) |
| ladder keys (all levels) | 4,223 | 229 first level + 3,994 behind it; 82 of them have only integer-infeasible open leaves |
| ladder open leaves | 68,153 | by A: 11,085 / 11,344 / 11,556 / 10,758 / 9,269 / 6,977 / 4,593 / 1,951 / 544 / 76 for A = 0..9; integer status 1,637 infeasible, 66,514 feasible, 2 unresolved (time limit) |
| keys per claim (both ladders) | 2 to 59, median 30 | levels per claim 2 to 8 |
| the sprint's 101 MILP-classified keys | 0 in the first level, 1 in the ladders | `(11,7,0,M,4,2)`, behind the first level; never used as exclusions; unresolved |

The driver-based hypothetical scans (`scope/hypo_scan.py`) and the ladder-based evaluation
(`scope/ladder.py`, no driver) give identical open-claim counts under every hypothesis both compute:

| hypothesis | open claims | first-level keys after | note |
|---|---:|---:|---|
| none (published state) | 280 | 229 | |
| A01: all A >= 2 leaves excluded | **119** | 120 (80 of them not among the 229) | the enumeration proposed in REPORT section 6 would at most reach here |
| A01_or_dark: all A >= 2, q_D = 0 leaves excluded | 153 | 147 | |
| A = 2..4 leaves excluded | 169 | 162 | |
| A0: all A >= 1 leaves excluded | **88** | 95 | 88 claims live on A = 0 configurations; no hub argument applies |
| INT: all integer-infeasible leaves certified | 236 | | pure integrality, no geometry |
| INT and A01 together | 103 | | |
| kill the 229 first-level keys outright | 151 | 138 new | the first level is not the obligation |
| kill every M^T q = 3 key (66) | 272 | | the pilot family; 8 claims |
| kill every M q = 4 key (63) / M^T q = 4 key (26) | 280 / 263 | | |
| kill every q = 5 key (210) / q = 6 (84) / q >= 7 (129) | 231 / 246 / 240 | | |

## 3. "Concentrated at A = 2..4 with no dark label" versus "covered"

The first statement is true of the 572 first-level leaves (380 at A = 2..4, 481 at q_D = 0, 340 both).
The second would mean that excluding those leaves closes every claim. It is false on two counts:

1. 62 of the 229 first-level keys have an open leaf with `A <= 1` (14 have only such leaves), so they
   survive any hub-case argument; and 3,994 further keys stand behind the first level. Excluding every
   leaf with `A >= 2` of every ladder key leaves 119 claims open.
2. Excluding every leaf with `A >= 1` still leaves 88 claims open (73 of shortfall 0), carried by keys
   whose A = 0 leaves are LP-feasible: 1,319 distinct ladder keys have such a leaf on those claims; at
   the first level they are M q = 6 (31), M^T q = 4 (17), M^T q = 3 (10), M q = 7 (10), M^T q = 7 (9),
   M^T q = 6 (8), M q = 8 (6), M^T q = 8 (3), M q = 9 (1). In an A = 0 configuration no missing label
   meets a full helper; hub capacity (H2), the joint family at full helpers (J, J1), the label-class
   rows P1-P5 and LIM are all vacuous or already applied. These claims need arguments about hubs that
   share hub-only labels among themselves, or about the even gates and chronology, or integer arguments.

Consequently the enumeration proposed in REPORT-2026-11-09 section 6 ("the A >= 2 hub configurations
behind the 229 load-bearing keys") does not cover the remaining problem and is not pursued as stated.

## 4. Per-claim entries (what the JSON holds)

For each claim: the state and orientation; `k, l, S_e, S_o, budget`, shortfall; `bound_needed` (the
inequality that must fail: for the 196 shortfall-0 claims one more level step on either side suffices;
for the others the number of steps on each test); `feasible_level_pairs` (every `(s_e, s_o)` that keeps
it open: all must disappear); both ladders, level by level, each key with its layer, number of open
leaves, least A among them, whether it has an A = 0 leaf, and whether all its open leaves are
integer-infeasible; `open_under_hypothesis` for the six hypotheses; and the derived flags
`covered_by_A_ge_2_enumeration`, `covered_by_any_hub_route_A_ge_1`, `closable_by_integer_certificates_alone`.
For each key: layer, open leaves with `(A, q_D, integer status)`, the claims and levels it serves, and
whether the sprint's MILP classification named it.

Justification for leaving configurations out: a key or leaf is absent from a claim's entry only if its
case system is LP-infeasible (the published rows exclude it as a relaxation, [measured] here, and
certified where the published certificate files cover it) or if its level cannot satisfy
`s_e <= S_e`, `s_o <= S_o`, `s_e + s_o <= budget` (then it cannot keep the claim open by the definition
of the final test). No configuration is excluded for being unlike known circuits.

## 5. Items that no longer address a live obligation, and items that stay unresolved

- **M^T q = 1 with 7-8 full helpers; M q = 2 with ten** (specified in the sprint, never run): no key
  with `q <= 2` is at the first level of any claim; the sprint's q = 1 representatives
  `(19,0,0,Mt,1,5)`, `(18,1,1,Mt,1,4)`, `(12,5,1,Mt,1,4)`, `(11,7,1,Mt,1,4)` are LP-infeasible under the
  combined rows; 82 M q = 2 and M^T q = 1 keys are LP-feasible only behind the first level (e.g.
  `(10,9,F,Mt,1,5)`, `(11,7,F,Mt,1,5)`), listed in the ladders where they occur. Removed from the
  immediate task; they return only if the levels in front of them are closed.
- **The 101 keys classified integer-infeasible by the sprint's MILP oracle (status unrecorded)**: the
  published 280 count never used them. None is a first-level key; one is in a ladder. Their status
  stays unresolved. Today's leaf survey (status recorded) is a different measurement and also not a
  certificate.
- **The package's 5,908 claims excluded at G = 75 by LP status only**: not certified; a bound of 76
  would need certificates for them as well as for the 280 (published README).
- **Two leaves hit the MILP time limit** (`(13,4,0,M,9,0)` at `(A, q_D) = (6, 7)`;
  `(11,5,1,Mt,8,0)` at `(0, 3)`): recorded as unresolved, counted as open.

## 6. Per-pair sharing is not an obstruction [measured, `scope/share_pairs.py`]

For anchored hubs (r = 1, 2) with no full-met label, the Lemma-J family of two hubs sharing a hub-only
label (their represented triples and the mixed vector `H + H' + P(h + h')`) is independent for many
mask pairs: M 361,168 (r = 1/1), 58,172 (1/2), 3,900 (2/2) value pairs; M^T 481,440 / 83,940 / 5,748.
Every value with two triples has 13-36 partners of class 2/2. So no finite fact on pairs yields a row
(the sprint's J1 is special to limit hubs, `r + m = 3`). Whatever obstruction exists must be joint
over the whole configuration of label-carrying helpers.

## 7. How this feeds the pilot

The pilot family is the M^T q = 3 block (21 first-level keys; 66 LP-feasible keys in the ladders;
whole-block closure would close 8 claims). It was chosen because a COMPLETE enumeration of its label
configurations is small (three labels, three label pairs) and because its open leaves include A = 0,
1 and 2, so the method is tested on exactly the configurations the hub route misses. Its results bear
on the 280 only through the ladders: a key's exclusion raises a claim's level only when it is the last
feasible key at that level.
