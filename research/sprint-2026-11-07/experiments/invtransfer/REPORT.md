# Which MixColumns bottom-level findings transfer to InvMixColumns 118@5 (invtransfer agent, 2026-11-07)

Scope: the INVERSE map (32x32, min depth 5 because eight outputs have weight 19), best known 118 gates at
depth 5 (repo), unrestricted 88 at depth 17 (repo) / 19 and 33 (archive). All engine calls go through
`~/xs-campaigns/2026-11-05-exit/pes/pes_lib.py` with `make_space("inv", 5)` (= `bt_lib_copy.Space("aes-invmixcolumns",
cap_real=5)`, search cap 5, remove1 top_k 16 modelled with the "binds" counter). Scripts and data in this folder:
`collect118.py` -> `records118.json`; `fan_plateaus.py` -> `fans118.json`, `plateaus118.json`,
`plateaus118_objects.json`; `oddh_sharing.py` -> `oddh118.json`; `firstlayer.py` -> `firstlayer118.json`;
`lineage.py` -> `lineage118.json`; `summarize_plateaus.py`; logs `*.log`, `run_rest.log`. One python process at a time
under `nice -n 10`; ~75 min wall. Labels: [checked] = exact computation here, [measured] = counted here, [read] = taken
from another report/file, [guess] = interpretation.

## 0. Data [measured]

- Record files named `g118-d5-*.json`: 1,772 found; 881 are `.verification.json` companions, 83 compute MixColumns
  (2026-11-06-layout MC runs passing through 118), 9 unreadable/empty, leaving **799 inverse 118@5 record files**:
  2026-10-31-adopt `adopt/inv-cap5-00..04` 158 (ring buffer of 32 per worker), 2026-11-05-inv118 `star-00..19` 640, repo 1.
  No 118 record exists in 2026-11-03-waits, 2026-11-04-12h, 2026-11-05-inv-star (from scratch, best 124), 2026-11-06-w500,
  the 12 h v9c/v9d tests or 2026-10-31-long.
- 799 files -> 519 distinct raw value sets -> **510 distinct engine states at cap 5** (trim/canonicalisation merges 9).
  All 510 are 118 gates, depth 5, `ok()`.
- Also used: repo `aes-invmixcolumns-xor{88..118}-depth{17..5}.circ.txt` (10 circuits) and the archive's
  `invmc_walk_88_depth33.json` (88 gates, depth 33, verified here by replay). The archive's depth-19 88 was not at the path
  the archive's own script names (`controls/inverse/`), only "forward_regenerated" derivatives: UNTESTED.

## 1. Per finding

### (a) Plateau = exact product of small factors; each 3-way factor an unshared 3-input XOR tree (F2) -- TRANSFERS in the product form, DOES NOT in the "3-input tree" form

- Every one of the **56 plateaus** the 510 states fall into is an exact Cartesian product (`pes_lib.compress`): 48 fully
  verified (remove1 fanned at every member, every neutral outcome a member), 8 "pairwise" here (size > 400; the
  2026-11-05-views agent closed the same 56 completely, `plateau/REPORT.txt` section 4) [checked]. Depth 5 at every member,
  all moves neutral 1-for-1.
- Shapes (choices per factor | plateaus | record files | distinct recorded states | core size):

  | shape | plateaus | files | states | core |
  |---|---:|---:|---:|---:|
  | 5x5x2x2x2 (200) | 9 | 359 | 236 | 80 |
  | 5x2x2 (20) | 20 | 72 | 29 | 82 |
  | 5x2x2x2 (40) | 8 | 70 | 26 | 81 |
  | 14x2x2 (56) | 6 | 59 | 20 | 81 |
  | 7x5x5x2x2x2 (1,400) | 5 | 19 | 19 | 79 |
  | 19x7x5x2x2 (2,660) | 3 | 99 | 98 | 78 |
  | 19x5x2x2 (380) | 3 | 114 | 75 | 79 |
  | 19x2x2 (76) | 1 | 4 | 4 | 80 |
  | 5x5x2x2 (100) | 1 | 3 | 3 | 81 |

  This reproduces the views agent's table exactly (9/3/3/20/8/6/5/1/1) [checked, independent code path through pes_lib].
- **The repo 118@5 plateau = 200 = 5 x 5 x 2 x 2 x 2, core 80 of 86 helpers** [checked]. Its factors:
  1. coupled 5-choice block, 6 values: two F2-style 3-input trees, A = {0x30, 0x10000010, 0x10000020} for consumer
     0x10000030 = x4^x5^x28 and B = {0x101000, 0x201000, 0x300000} for consumer 0x301000 = x12^x20^x21 (each triple XORs
     to 0 = the "which pair first" choice of F2), coupled because core value 0x10100010 needs 0x10000010 or 0x101000
     present: 5 of 9 combinations [checked; agrees with views `detail.py`].
  2. **K5 (free 5-way, single value): NOT a 4-input tree.** One weight-10 level-4 consumer 0xc243c041 = v_i ^ p_i with
     five fixed core partners p_i of weight 4 (0xc0004080, 0x80c00040, 0x4080c000, 0x4080c0, 0x2030001; four are byte
     rotations of one pattern), v_i of weight 8/8/8/6/8 at level 3. The five values do not XOR to 0 and the partners are
     helpers, not inputs [checked].
  3. **K2 x 2 (free 2-way, single value, level 1): a 4-input tree with one shared half.** 0x2020202 = 0x202 ^ 0x2020000
     or 0x20200 ^ 0x2000002 (and 0x8080808 likewise): y = (a^b)^(c^d) where the two alternative splits each reuse one
     CORE level-1 pair; the third balanced pairing is absent because both its pairs would be private (a 2-value change)
     [checked].
  4. K2 (mixed level): output T14 0xd8e8b8c8 (weight 15) = 0xc0e02040 ^ 0x18089888 or 0xe0800020 ^ 0x3868b8e8, the
     moving value at level 4 (weight 7) or 3 (weight 5) [checked].
- Across all 56 plateaus (219 factors) [checked]: 134 K2, 21 K5, 8 K7 single-value; 43 coupled 5-blocks (6 values),
  6 coupled 14-blocks (10 values), 7 coupled 19-blocks (12 values). **Every single-value factor (163 of 163) is a
  "partner choice": one fixed consumer y, values v_i = y ^ p_i with p_i fixed core/available values** (the generalisation
  of F2; F2's MC case is y = a^b^c with p_i the three inputs, which is why MC triples XOR to 0). In the inverse: 112 of
  134 K2 are 4-input trees with a shared half (consumer weight 4, values and partners weight 2); 22 K2 are mixed-level
  (consumer weight 3 helper plus a weight-15 output); all 21 K5 are the weight-10-consumer form above; the 8 K7 have a
  weight-7 consumer with partners of weights 1-8. **In no single-value factor are the partners inputs, and in none do the
  choice values XOR to 0.** F2's literal 3-input trees occur only inside the coupled blocks (2 per 5-block; also inside
  the 14- and 19-blocks, which contain the same triples plus 0x60000000/0x60000020/0x30000010/0x50000010 and the slot-4
  pair) [checked].
- Core/mobile from the fans [measured]: core 63-79 of 86 helpers at the 510 states (mode 72), mobile 7-23 (MC 88: core
  47-50 of 56, mobile 6-9, F23). The inverse's mobile part is proportionally similar (8-27 %) but its moves are partner
  swaps and level-1 swaps rather than tree re-pairings.

### (b) No remove1 down-step at any sampled bottom state (F11) -- TRANSFERS

- `pes_lib.fan` at all **510 distinct 118@5 states: 0 down moves; 0 binds** (the top_k = 16 cut never bound, so the
  check is exhaustive for remove1) [checked]. Neutral moves per state 4-20: {4: 23, 5: 24, 6: 7, 7: 22, 8: 3, **9: 206**,
  11: 97, 12: 6, 14: 5, 15: 43, 17: 57, 18: 11, 20: 6} (MC 88: 8-44, mode 16). Every neutral neighbour is at depth 5.
- Inside the 48 fully closed plateaus every member was fanned: **0 down moves at any of their members (48 plateaus of
  20..380 states)** [checked, `compress` downs list empty]; the 8 larger ones were fanned at seed + factor-local closures: 0.
- Consistent with the 2026-11-05 inv118 smoke note ("86 % of moves blocked, slack to +1 at once") [read].

### (c) How many distinct 118@5 plateaus; do landings repeat (F5/F12) -- TRANSFERS as "records are not one plateau"; the MC "vast level" DOES NOT transfer on this data (UNTESTED for independent arrivals)

- 510 states -> **123 cheap identities (v3, mod rotation) -> 56 exact plateaus** [checked]. v3 over-splits by 2.2x
  (MC: 1.6-2.3x), entirely on the coupled blocks: 1 class per 20/40-state plateau, 3 per 200, 5-6 per 380/2,660.
- Records per plateau: 190, 66, 44, 38, 37, 33, 32, 24, 24, 22, 20, 19, 18, 18, 15, 15, 15, 14, 14, 12, 12, 11, 11, 10,
  10, 9, 8, 7, 6, 4, 3, 3, 3, 3, 2 x 7, 1 x 15 [measured]. The repo plateau (pid 0) holds 124 of the 510 states and
  190 files (adopt 118 files + inv118 71 + repo 1).
- **Landings are not independent on the inverse.** The adopt run's 158 files lie in 2 plateaus (pid 0 and one 5x5x2x2
  plateau, 3 files); all 5 adopt workers' 118 records trace to ONE discovery: `inv-cap5-01` chain c0054 at iteration
  318,265,500, root = inv-cap5-03's 119 record `g119-d5-6d81052eef3c4e9e` (the 46 h adopt run: 120 for 40.5 h, then 119 ->
  118 in 7 s, waits BRIEF); the other four workers' first 118 records have root = that worker's `g118-d5-a87921c2...`
  or inv-cap5-03's 119s (adopt copying; moves walk.remove1 / lns.rebuild) [measured from record metadata]. The inv118
  run (640 files, 55 plateaus) is a 6 h, 20-worker star walk SEEDED with the repo 118, every centre at 118 within helper
  distance <= 0.36 of the seed [read, `inv118_report.txt`]. "30 plateaus reached by > 1 chain" counts star cycles, not
  independent descents.
- So: as recorded, the entire 118@5 level is one lineage = one circuit's remove1-plus-excursion neighbourhood: 56
  plateaus, 1 of them visited by both runs. Rate of new plateaus: 55 in ~120 worker-hours of seeded walking (0.5 per
  worker-hour; ~1 v3 class per worker-hour) against MC hunt A/B/C's 24.5-26.8 v3 classes per worker-hour at 88
  (F14) -- a 25x difference, but the procedures differ (star walk vs free chains) [measured, not like for like].
  No run has ever arrived at 118 independently (from scratch: inv-star 13 h -> 124; v9c/v9d 2 h -> 128/125; w500 6 h ->
  129; waits reruns seeded from the adopt 120 -> 119 at best), so the MC-style capture-recapture estimate cannot be
  made: **whether the inverse 118 level is vast is UNTESTED; what is tested is that nothing reaches it twice.**
- A second 119@5 family exists: 2026-10-31-long (`aes-lowdepth` group) has 144 distinct inverse 119@5 states whose
  first layer shares only 11-12 of the 118 family's 17 fixed pairs (best rotation), against 16-17 for every 119/120 of
  the adopt lineage and the waits reruns, 13-17 for the waits "bloat" 120s, 13-15 for the 2026-11-04-12h 120s
  [measured, `lineage118.json`]. So the inverse has at least two 119-level families with different first layers; only
  one of them has a known 118 below it.

### (d) Odd-helper count (F20 model) and the sharing identity G = 228 + delta - S -- TRANSFERS as identities; F20's bound is MC-specific (UNTESTED for the inverse, no inverse theorem exists)

- Odd-weight non-output helpers [measured, own wiring of the first record file per state]:
  - 118@5 (510 states, 86 helpers each): {23: 8, 24: 61, 25: 206, 26: 227, 27: 8}; gate parities (odd+odd x, even+even
    y, mixed): (25, 35, 58) x 227, (26, 35, 57) x 205, (26, 36, 56) x 61, others 10. Repo 118@5: 26 of 86.
  - unrestricted-depth inverse: repo 88@17: **21 of 56** (x/y/m 24/11/53); archive 88@33: **18 of 56** (24/14/50);
    89@15: 20; 90@12: 18; 92@11: 18; 93@10: 20; 94@9: 23; 96@8: 19; 101@7: 21 of 69; 104@6: 19 of 72.
  - MC 88s for comparison: 16-24 odd helpers of 56 (F16). The inverse 88s sit in the same band with the same helper
    count 56. The h = 0, 1, 2 theorems of F20 use MC-specific premises (x >= 24, the Sidon structure of the 66 odd
    output/input values); nothing analogous is proved for the inverse, so "any inverse circuit with <= 89 gates has >= 3
    odd helpers" is UNTESTED (the real inverse 88s have 18-21, far from the bound's regime anyway).
- Sharing identity with the archive's inverse group minima M = (23, 27, 27, 35, 35, 31, 27, 23), sum 228 [read, audited
  in the archive's `inverse_local.md`; NOT re-derived here]: **G = 228 + delta - S_mult + dead holds on all 510 118@5
  states, the 10 repo circuits and the archive 88@33** [checked]. Numbers: 118@5 own wiring: S_mult 157-166 (mode 158),
  delta 47-56 (mode 48), S - delta = 110 at every state, dead 0; cone sizes mode (24, 31, 30, 49, 44, 38, 33, 27).
  Repo 88@17: cones (24, 33, 40, 44, 42, 46, 48, 23), delta 72, S 212, S - delta 140. Archive 88@33: cones (25, 33, 39,
  50, 60, 66, 70, 23), delta 138, S 278, S - delta 140. 20 random re-wirings of the same 118 value set move S over
  157-201 and delta over 47-91 while S - delta stays 110 (111 with one dead gate) -- the identity carries no information
  beyond G, exactly as F17 found for MC (S 41, delta 21, S - delta 20 on the repo 88@5) [checked].
- Consistency check of the minima: over all 521 inverse circuits no group cone is below its claimed minimum
  (min over groups of cone - M_g is 1 in 500 states, 2 in 10, and exactly 0 only at group 7 of the two unrestricted 88s,
  cone 23 = M_7) [measured]. Reading [guess]: the inverse reaches 88 with group minima summing to 228 (vs MC's 108) by
  sharing 212-278 units (vs 41); "88 on both maps" is therefore not a consequence of the group floors.

### (e) First-layer structure of the 118@5 family (F15 contrast) -- PARTLY TRANSFERS: a rigid first layer like 89@4, but mobile within the family, unlike 89@4

- Level-1 pairs = weight-2 values of the state. Over the 510 states [measured, `firstlayer118.json`]: first-layer size 24
  (476 states) or 25 (34); **105 distinct level-1 sets (105 modulo rotation too, no two rotation-related); 35 pairs ever
  used; 17 pairs in all 510 states** (0x10001, 0x1000100, 0x10001000, 0x10100, 0x2000002, 0x20000020, 0x202000,
  0x2020000, 0x40004, 0x400040, 0x4000400, 0x40004000, 0x80000080, 0x8080, 0x80800, 0x8080000, 0x80800000: all
  "same-bit" pairs of bits 0, 1, 2, 7 across bytes), 18 in >= 90 %, 24 in >= 50 %; mean Jaccard of two distinct layers
  after best rotation 0.75. The 2026-11-06 layout report's numbers (24.1 pairs, 17 in all, 35 ever used, overlap 0.74,
  115 layers over 671 gate-deduplicated circuits) are reproduced on value sets [checked against `layout/REPORT.txt`].
- **The sprint note "InvMC has 23 level-1 sets in its 118 family" is NOT reproduced**: the counts here are 105 level-1
  sets over 510 states / 56 plateaus (39 of the 56 plateaus contain states with different first layers). No computation
  gives 23; the nearest facts are 24 pairs per layer and 24 pairs in >= 50 % of states. Treat "23 level-1 sets" as
  unsourced until its script is found.
- Why the first layer moves inside a plateau: the K2 factors (0x202 <-> 0x20200, 0x808 <-> 0x8000008, ...) and the
  coupled 5/14/19-blocks (0x30 / 0x10000010 / 0x10000020, 0x101000 / 0x201000 / 0x300000, 0x60000000 ...) are swaps of
  level-1 pairs; 10-11 level-1 pairs are mobile in the repo plateau [checked]. Contrast 89@4: one first layer (26 pairs)
  frozen across the 81-state family, with the 4 mobile slots at level 2 [read, F15/q89check]; 90@4: 183 layers over 5,798
  states; MC 88@5: 91 layers over 742 circuits, 0 pairs in all [read, layout]. The inverse family is between the two:
  17 of 24 pairs frozen across everything ever recorded at 118, the remaining 7-8 drawn from 18 candidates, and most of
  the plateau motion IS first-layer motion.

## 2. What the inverse says about the forward 87 question

1. **The inverse bottom looks like 89@4, not like MC 88** [measured + guess]: one discovery event in all recorded
   inverse work (adopt, after 40.5 h at 120), no independent arrival since (from scratch 124-129 in 2-13 h runs, 500
   workers included), one lineage of 56 neighbouring product plateaus within helper distance 0.36, cores 63-82 of 86,
   a first layer with 17 of 24 pairs frozen. MC 88 is the opposite: 146 of 146 chains land on new plateaus, ~1e5
   estimated. So "the bottom level is vast" is not a general property of bottom levels of this search; it is specific
   to MC at 88 (uncapped / slack 2 over the minimum depth).
2. **A reading that fits all four cases [guess]**: level size tracks depth slack. InvMC 118@5 (cap = minimum depth 5),
   MC 97@3 (cap = minimum 3: 50 layers / 329 circuits) and MC 89@4 (slack 1: one family) all show few, rigid families;
   MC 88 uncapped shows a vast level. If so, the forward 87 question at unrestricted depth is being asked in the regime
   where the level is largest and the search's samples say least; a capped inverse-style question ("is there a 117@5?")
   is the one where a family census can actually be completed.
3. The inverse's 88 at unrestricted depth (depth 17-33, 56 helpers, 18-21 odd helpers, S - delta = 140) matches the
   forward's 88 in gate and helper count while every other structural number differs (group floors 228 vs 108, sharing
   212-278 vs 41, output weights 11-19 vs 5-7). This makes "88 on both maps" look like a coincidence of the search's
   reach rather than a shared wall [guess]; a cheap discriminating experiment is an uncapped XORFlux campaign on the
   inverse from its 88@17 (never run; the repo best is the archive's import): finding an inverse 87 would show the engine
   can go below 88 on a map of this class, and failing in the same way would say the 88 floor is procedural.
4. Transfers that strengthen the forward picture: (i) plateau = exact product, 56 of 56 again, with the inverse adding
   new factor kinds (partner-choice K5/K7, shared-half K2, coupled 5/14/19 blocks) -- F2's "3-input tree" is the MC
   special case of "one consumer, choice of partner among available values"; a SAT/structural argument about 87 should
   be phrased on the general form; (ii) remove1 has no down-step at 510 states + every closed member on the inverse
   either, so the one-value move's blindness at the bottom is map-independent; (iii) the sharing identity and the
   odd-helper counts give no leverage on either map (identity has zero slack; real circuits sit mid-range).
5. What the inverse does NOT tell us: whether an 87 exists (no inverse bound above the trivial applies to the forward);
   whether MC's 88 plateaus connect; anything about independent inverse arrivals (none exist).

## 3. Numbers at a glance

| quantity | InvMC 118@5 (this report) | MC 88 (sprint) | MC 89@4 (F15) |
|---|---|---|---|
| distinct states recorded | 510 (799 files, 2 runs, 1 lineage) | 4,314 sampled (146+ chains) | 90 (81 mod rot.) |
| exact plateaus | 56, all products, sizes 20-2,660 | 267+ products, 2,187-3.4e6; ~1e5 est. | 1 (81 = 3^4) |
| factor kinds | K2 134, K5 21, K7 8, coupled 5/14/19: 43/6/7 | 3-way 1,425/1,425 (+ coupled 15..69k) | 3-way x 4 |
| down moves (remove1) | 0 / 510 states, 0 inside closures | 0 / 4,314 | 0 / 81 |
| neutral moves per state | 4-20, mode 9 | 8-44, mode 16 | 8 |
| core / helpers | 63-82 / 86 | 47-50 / 56 | 53 / 57 |
| first layer | 24-25 pairs, 17 fixed, 105 layers | 18.7 pairs, 0 fixed, 91 layers | 26 pairs, 1 layer |
| odd non-output helpers | 23-27 of 86; 88s: 18-21 of 56 | 16-24 of 56 | - |
| S - delta (own wiring) | 110 (118@5), 140 (88s) | 20 | - |
| independent discoveries | 1 | every chain | 2 |
