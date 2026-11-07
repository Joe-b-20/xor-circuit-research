# Adversarial check of F15 / q89 ("Why 89@4 is unusual")

Folder `~/xs-campaigns/2026-11-07-sprint/q89check/`. 2026-11-07, about 80 minutes, one process at `nice 10`,
read-only outside this folder. Own code throughout (`c1_census.py`, `c2_plateau.py`, `c2d_ownmodel.py`,
`c3_p2.py`, `c4_p2_classify.py`, `c5_ownclosure.py`; outputs `c*.out`, `c*_result.json`, `c1_states_{89,90}.json`,
`c3_L0.json`). The q89 scripts were read only for file locations and the record format. `pes_lib`
(`~/xs-campaigns/2026-11-05-exit/pes`) was used for the remove1 fan and the expand envelope, as instructed; a
pes_lib-free value-set model was written as a cross-check (c2d/c5).

Conventions fixed from the raw files: the matrix `aes-mixcolumns.mat.txt` is 32 rows of 32 bits, bit j = input
x_j; a record's value set is rebuilt from `gates` (operand indices, inputs 0..31 first); a state = the set of
non-input values; gates = distinct non-input values; depth = least-level assignment; byte rotation = cyclic shift
of the 32-bit mask by 8, 16, 24 (checked: these and only these shifts map the target set onto itself; the repo
`.circ.txt` outputs y0..y31 equal the matrix rows in order). `make_space("mc", 4)` gives ValueSet search cap 4, so
`fan()` is already capped at 4 there (search cap 6 for cap_real 5, none for None); no extra cap was needed.

## Verdicts

| claim | verdict | my numbers |
|---|---|---|
| (1a) 526 files, 90 distinct, 81 mod rotation, all 26/22/29/12 | **CONFIRMED** | 620 `g89-d4` files found, 95 are other maps (2026-10-30-nist, targets absent) -> 525 + repo = 526; 90 distinct value sets; 81 rotation classes (9 classes with 2 members); profile (26,22,29,12) in all 90; first layer 26 in all 90; exactly 2 level-1 sets: the repo's (81 states) and its 8-bit rotation (9 states) |
| (1b) the 81 are one cap-4 remove1 plateau: closure 81, 8 neutral/state, 0 down; 53 constant helpers; 4 slots x 3 | **CONFIRMED** | pes_lib closure from the repo state: 81 states, complete, 8 neutral moves in every state (648 edges, all outcomes depth 4), 0 down moves, top_k never binds; closure == the 81 record states with the repo's L1 (the 9 others are 8-bit rotations of L0 members); 53 helpers in all 81, 12 variable values each in 27 states, 4 mutually exclusive triples, 81 distinct choice tuples; own model (section 2) agrees |
| (2) 90@4: 13,141 files, 5,798 distinct, 183 first layers, sizes 21-26, none equal to the 89's, max overlap 24, 72 states with 26 | **CONFIRMED** | 13,220 files, 79 other maps -> 13,141; 5,798 distinct (5,796 mod rotation); 60 profiles, most common (23,25,29,13) x 1,569; 183 level-1 sets; sizes {21: 4, 22: 161, 23: 4,075, 24: 1,277, 25: 209, 26: 72}; 0 states with the 89's L1 under any rotation; overlap histogram (max over rotations) 24: 72, 23: 82, 21: 16, 20: 18, 19: 338, 18: 2,150, 17: 2,943, <=16: 179; the 72 size-26 states share one L1 = the 89's minus {x1+x8, x8+x24} plus {x0+x16, x8+x16} |
| (3) 8 neutral at cap 4 vs 15 at cap 5 / none; closure 81 vs >= 3,096 / >= 6,117 | **CONFIRMED** (my bounds smaller, same direction) | fans on 3 L0 members: cap 4: 8 (all depth 4); cap 5 (search cap 6): 15 = 8 to depth 4 + 7 to depth 5; none: 15, same split; 0 down moves in all; bounded closures (400 expansions, my budget): cap 5 >= 1,531 (expanded depths 4: 33, 5: 349, 6: 18), none >= 1,763 (depths 4-9), neither complete, 0 down moves seen |
| (4) all records trace to two entry events | **COULD NOT CHECK** | not re-derived (budget; needs event-log reading, not record arithmetic). The per-campaign record counts (adopt 156, v9c 317, long 32, mc87 11, foundation/repair 9, repo 1) agree with q89 |
| (5) P2: 12 distinct 90@4 states carry the 89's exact first layer, none in L0's +1 band | **DIFFERENT in scope, same result for the trap population** | 26 distinct 90-gate depth-4 states with the 89's L1 (any rotation) on disk; of these 1 is in B1, 3 have a direct remove1 step down into L0, 11 descend to L0 by a bounded remove1 BFS; the 8 that are run-final states of completions that ended at 90 (q89's population) all fail: 0 in B1, 0 down, cut at 3,000 states. Section 4 |

## 1. Census (c1_census.py -> c1.out, c1_summary.json)

- 89@4: files scanned 620, accepted 526 (`2026-10-31-adopt` 156, `2026-10-31-long` 32, `2026-11-03-12h` 2,
  `2026-11-03-waits` 7, `2026-11-04-12h` 317, `2026-11-04-mc87` 11, repo 1); rejected 95 (other maps). No record
  had duplicate gate values, a depth field other than 4, or a least-level depth other than 4.
- 90@4: files scanned 13,220, accepted 13,141 (14 campaigns; w500 7,656, layout 1,890, 11-04-12h 1,152, ...);
  rejected 79 (other maps). All 5,798 distinct states have least-level depth 4.
- Record counts match q89 exactly; so do the dedup counts, profiles, first-layer histogram and overlaps.

## 2. Plateau and cap (c2_plateau.py -> c2.out; c2d_ownmodel.py -> c2d.out; c5_ownclosure.py -> c5.out)

- pes_lib at search cap 4: closure of the repo state = 81 states, complete, 8 neutral / 0 down in every state,
  10 s. L0 equals the set of record states whose level-1 set is the repo's; the 9 remaining record states are the
  8-bit rotations of L0 members (c3.out line 2).
- Structure: 53 constant helpers, 12 variable values, each in exactly 27 states; the 12 split into 4 mutually
  exclusive triples; 81 distinct choice tuples. Triples (same as q89's slot table):
  {x2+x7+x10+x15, x2+x10+x27, x7+x15+x27}, {x11+x19+x20, x11+x15+x19+x23, x15+x20+x23},
  {x11+x18+x26, x11+x23+x31, x18+x23+x26+x31}, {x3+x4+x27, x4+x7+x31, x3+x7+x27+x31}; all at level 2.
- Own value-set model (no pes_lib): remove helper h; "stuck" = values with no least level <= 4 afterwards; a repair
  is one new value w with the set admissible again (every value at level <= 4); greedy trim; every admissible w is
  enumerated (no top_k, no smallest-size preference), so its neutral set is a superset of any one-value-repair
  engine variant. On the repo state and two other L0 members it returns exactly pes_lib's 8 neutral outcomes
  (same removed/added pairs: the 4 slots x 2 alternatives) and 0 down moves; 319 of 327 candidate repairs are
  inadmissible at cap 4. Note for anyone re-deriving this: "stuck" must be defined by depth, not by closure
  (after removing a slot value every value still has some two-term decomposition, only deeper), and the
  candidate set must be the union over stuck values (dependents recover transitively); otherwise the model
  finds nothing (my first two attempts, c2b/c2c, failed exactly that way).
- Own-model closure of the whole plateau: see the appended line at the end of this file (c5.out).
- Cap 5 / none: 15 neutral moves per member (8 to depth-4 states, 7 to depth-5 states), 0 down. Bounded closures
  at 400 expansions: >= 1,531 (cap 5) and >= 1,763 (none), consistent with q89's >= 3,096 / >= 6,117 at 1,500
  expansions. The direction "the cap halves the fan and shrinks the plateau from thousands to 81" holds.

## 3. 90@4 first layers (c1.out)

183 distinct level-1 sets over 5,798 states; sizes 21-26; the only 26-gate first layer among 90@4 states (72
states) differs from the 89's by swapping {x1+x8, x8+x24} for {x0+x16, x8+x16}; 0 states carry the 89's L1 under
any rotation. The archive sentence "no 90@4 had more than 25 first-layer gates" is indeed false on the full data.

## 4. P2 recheck (c3_p2.py -> c3.out, c3_result.json; c4_p2_classify.py -> c4.out)

Population: every 90-gate, depth-4 state with the 89's 26-pair level-1 set up to rotation, from (a) the 5,798
record states (0 hits, confirming q89) and (b) every `best` event with g = 90, d = 4 and a `values` list in the
pinned-completion logs (`2026-11-02-why/foundations/out/*.jsonl`, `2026-11-03-12h/foundation/run/runs/*.jsonl`,
`2026-11-04-12h/foundation2/run/runs/*.jsonl`, `2026-11-03-waits/repair/run/runs/*.jsonl`; 3,901 files, 110 such
events). Rotated into L0's frame: **26 distinct states**, one per source file (16 foundations/out, 3 foundation,
5 foundation2, 2 repair). B1 regenerated with pes_lib's expand envelope from all 81 L0 members: 16,173 states
(same as q89 and the barrier report).

| test | all 26 | the 8 run-final traps (run ended at 90) | the 18 transient (run ended at 89) |
|---|---:|---:|---:|
| in B1 | 1 | 0 | 1 |
| direct remove1 step down into L0 (cap 4) | 3 | 0 | 3 |
| bounded BFS over non-increasing remove1 moves (3,000 expansions) reaches L0 | 11 | 0 | 11 |
| BFS exhausted a 9-state region with no exit | 4 | 0 | 4 |
| BFS cut at 3,000 (5,322-7,650 states seen) | 11 | 8 | 3 |

No BFS reached any <= 89 state other than L0. The 8 traps (path14-s1, a-pin-s1/s3/s6/s7, foundation e00000-r0/r1,
repair ctl89-r0) behave exactly as q89's 12 did: not in B1, no down move, no descent within budget. So q89's
falsification of P2 stands for the population it tested (run-final 90s). But the sentence "12 distinct 90@4
states carry the 89's exact first layer and none lies in L0's +1 band" must not be read as "no 90@4 over this
first layer connects to L0": 11 of the 26 such states on disk descend into L0 by remove1 alone (3 in one step,
one of them from inside B1), and 4 more transient states sit in 9-state 90-plateaus with no remove1 exit while
their own runs still ended at 89 (so the completion left those pockets by a move other than remove1). Count
difference: q89 reports 12 trap states, I find 8 run-final ones (q89 lists two distinct states each for
foundation e00000-r0 and r1 and one from repair `x_rc_b0_010313-r2`; my scan keyed on `best` events found one
state per file and no 90 event with the 89's L1 in that repair file; not resolved in budget, the conclusions do
not depend on it).

## 5. Where the q89 report over-reads

1. P2 addendum: "the same first layer supports at least two other 90-level families that the capped moves do
   not connect to L0" is supported (8 traps + 4 nine-state pockets). The implicit converse, that first-layer
   equality never puts a 90 in L0's remove1 basin, is wrong: 11/26 are in it, 1 in B1 itself. The 6:4 split of
   pinned completions is therefore between "entered L0's remove1 basin" and "landed in a disconnected 90 pocket",
   both over the same first layer; "the entry criterion is finer than level 1" is right, but the 90s that do
   enter are on disk and were not counted.
2. Claim (3)'s closure numbers (>= 3,096 / >= 6,117) are lower bounds at an arbitrary expansion budget; they
   establish "much larger than 81", not a size. Confirmed in that reading only.
3. "The 8 neutral remove1 moves are exactly the 4 slots x 2" is confirmed under pes_lib's engine model and under
   my model that enumerates every one-value repair at cap 4. Neither covers multi-value repairs, so "the plateau
   is 81" is a statement about single-value-repair moves, as q89 says.
4. Claim (1): "81 modulo rotation" is a count of rotation classes among the 90 recorded states; 324 = 4 x 81
   "known circuits" is arithmetic on the symmetry, which q89 labels correctly.
5. Claim (4) (two entry events) was not re-derived here.

## Files
`c0_probe.py`, `c0b_probe.py` (format discovery), `c1_census.py` -> `c1.out`, `c1_summary.json`, `c1_states_89.json`,
`c1_states_90.json`; `c2_plateau.py` -> `c2.out`, `c2_result.json` (its own-model section is superseded by c2d);
`c2b_debug.py`, `c2c_debug.py` (failed model attempts, kept for the record); `c2d_ownmodel.py` -> `c2d.out`,
`c2d_result.json`; `c3_p2.py` -> `c3.out`, `c3_result.json`, `c3_L0.json`; `c4_p2_classify.py` -> `c4.out`,
`c4_result.json`; `c5_ownclosure.py` -> `c5.out`.

## Appendix: own-model closure (c5.out)

OWN-MODEL cap-4 closure: 81 states, complete=True, expanded 81, neutral per state {8: 81}, down moves 0, equals pes_lib L0: True, 148s
