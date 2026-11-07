"""s15_write_report.py: emits REPORT.md (the deliverable) from the text below. Run: python3 -I s15_write_report.py"""
import os

OUT = os.path.join(os.path.expanduser("~"), "xs-campaigns/2026-11-07-sprint/q89/REPORT.md")

TEXT = r'''# Why the recorded MixColumns 89@4 circuits behave unusually

Folder: `~/xs-campaigns/2026-11-07-sprint/q89/` (scripts `s*.sh`, `s*.py`, outputs `s*.out`, `s4_summary.json`,
`states_{89,90,91}.json`, `s7_structure.json`, `s8_capfan.json`). 2026-11-07, about 90 minutes, one process at
`nice 10`, repo read-only. Marks: **[measured]** = computed here or in a named script/file; **[proved]** =
proof given; **[derived]** = follows from marked facts; **[guess]** = interpretation; **[archive]** = the owner's
unverified notes (`import/zip`), used as hints only. "L0" = the remove1-neutral closure of the repo 89@4 at
depth cap 4 (the "sealed pocket").

Premise correction up front: the task text says v8 "reaches 89@4 from NIST's 90@4 in minutes". The record says the
opposite. v8 (control run, 2026-10-31) found 89@4 from the **July 91@4** at 914 s; the adopt side moved every
worker onto NIST's 90@4 and never left 90 [measured: `~/xor-circuit-research/circuits/aes-mixcolumns/logs/aes-mixcolumns-xor89-depth4/found.json`
("seed": July 91@4, 914 s), `search/HISTORY.md` lines 137-139 and 189-191]. Part 3 treats the real question: why the
July lineage leads there and NIST's does not.

---------------------------------------------------------------------------------------------------------

## Part 1. Properties shared by the recorded 89@4 circuits [measured]

Source census: every `g89-d4-*.json`, `g90-d4-*.json`, `g91-d4-*.json` under `~/xs-campaigns` (records, pools,
hits; `.verification.json` siblings and the `import/` archive excluded) plus the repo record. Value sets rebuilt
from the gate lists; other maps' depth-4 records (274 files from `2026-10-30-nist`) drop out because they do not
contain the 32 MixColumns targets. Script `s4_collect.py` -> `s4.out`, `s4_summary.json`.

### 1.1 The 89@4 records

| quantity | value | source |
|---|---:|---|
| record files (MixColumns, 89 gates, depth 4) | 526 | `s4_summary.json` "89".records |
| from: 11-04-12h v9c 317, 10-31-adopt control 156, 10-31-long aes-lowdepth 32, 11-04-mc87 from89 11, 11-03-waits repair 7, 11-03-12h foundation 2, repo 1 | | `sources_by_campaign` |
| distinct value sets | **90** | |
| distinct modulo the Z4 byte rotation | **81** | |
| rotation classes with more than one member | 9 | |
| per-depth gate profile (least levels from the value set) | **26 / 22 / 29 / 12 in all 90** | `profiles` |
| distinct level-1 (weight-2) sets | 2 (81 states share one, 9 share its one-byte rotation) | `distinct_L1_sets`, `s7.out` |
| distinct level-3 sets / level-4 sets | 2 / 1 (the level-4 set is the 12 level-4 outputs, rotation-invariant as a set) | `per_level` |

The 81 states with the main first layer are exactly L0 [measured, `s8.out`: the remove1-neutral closure of member 0
at cap 4 is complete at 81 states, 648 neutral edges, 8 per state, 0 down edges; agrees with
`~/xs-campaigns/2026-11-05-views/barrier/REPORT.txt` 2.2]. The other 9 distinct states are byte-rotations (by one
byte) of L0 members: their first layer is `rot8(L1)` exactly, and they came only from the foundation searches'
*validation* runs, which pin "the 89's set rotated by one byte" (`2026-11-03-12h/foundation/README.txt`, rule F4;
hits of kind `validation` in `2026-11-04-12h/foundation2/run/hits.jsonl`, `2026-11-03-12h/foundation/run/hits.jsonl`,
`2026-11-03-waits/repair/run/hits.jsonl`) [measured, `s7.out`, `s10.out`]. So: **every recorded 89@4 lies in L0 or in
one rotated copy of L0**; no second family is on record. (The barrier report's "510 records, 81 distinct" did not
include these 9 rotated validation hits, nor the 7 + 2 foundation/repair hits and mc87; otherwise its count agrees.)

### 1.2 Inside L0: the 53-value core and the 4 x 3 product [measured, `s7.out`]

- 53 helper values are in all 81 states ("53-value core"): the 26 level-1 pairs, 18 level-2 values, the 9 level-3
  helpers. 12 level-2 values are variable, each present in exactly 27 states.
- The 12 variable values form **4 slots of 3 mutually exclusive choices**, and all 3^4 = 81 choice tuples occur
  exactly once (`distinct choice tuples: 81`). So L0 is an exact product of four independent 3-way factors.
- Each slot is the re-pairing of one **3-leaf XOR tree** whose leaves are two level-1 pairs and one input and whose
  root is a fixed weight-5 level-3 helper present in every state (`s14_fix.py` output):

  | slot | leaves | root (constant helper) | the 3 level-2 choices |
  |---|---|---|---|
  | 0 | x2+x10, x7+x15, x27 | x2+x7+x10+x15+x27 | x2+x7+x10+x15 / x2+x10+x27 / x7+x15+x27 |
  | 1 | x11+x19, x15+x23, x20 | x11+x15+x19+x20+x23 | x11+x19+x20 / x11+x15+x19+x23 / x15+x20+x23 |
  | 2 | x18+x26, x23+x31, x11 | x11+x18+x23+x26+x31 | x11+x18+x26 / x11+x23+x31 / x18+x23+x26+x31 |
  | 3 | x3+x27, x7+x31, x4 | x3+x4+x7+x27+x31 | x3+x4+x27 / x4+x7+x31 / x3+x7+x27+x31 |

  Leaves at levels (1, 1, 0) give a root at level 3 under every pairing, so the cap never objects; this is why these
  four factors survive the cap (Part 2.4).
- The 8 neutral remove1 moves of every state are exactly the 4 slots x 2 alternative choices [measured, `s8.out`;
  `2026-11-06-89at4/REPORT_B.txt` 2 says the same].

Check of the archive claims (`import/zip/guides/RECENT_CONVERSATION_FINDINGS.md` 1, and the circuit-space-views
pointer): "all 89@4 have profile 26/22/29/12" **true** (526 records, not 156). "81 circuits, one exact first
layer, differing in 4 second-layer choices" **true as a description of L0** and of all unrotated records; the 4
choices are the 4 slots above, 81 = 3^4 is exactly four independent 3-leaf re-pairings. "53-value core" **true**.
Scope: L0's three byte-rotations are three more plateaus of 81 (one of them has 9 recorded members), so the
number of known 89@4 circuits is 324, and nothing here shows that no other 89@4 family exists.

### 1.3 The 90@4 and 91@4 records for comparison [measured, `s4_summary.json`, `s7.out`]

| | 90@4 | 91@4 |
|---|---:|---:|
| record files | 13,141 | 4,881 |
| distinct value sets / modulo rotation | 5,798 / 5,796 | 3,970 / 3,970 |
| distinct per-depth profiles | 60 (most common 23/25/29/13: 1,569) | 101 (most common 26/22/29/14: 1,022) |
| distinct level-1 sets | **183** | 214 |
| first-layer size histogram | 21: 4, 22: 161, 23: 4,075, 24: 1,277, 25: 209, **26: 72** | 19: 4 ... 25: 821, 26: 2,766 |
| level-4 set sizes | 10-16 | 10-20 |
| states whose level-1 set is the 89's (any rotation) | **0** | 0 |
| largest overlap with the 89's 26 pairs | 24 (72 states), 23 (82 states), then 16-20 | |

- The 72 distinct 90@4 states with 26 first-layer gates all share one level-1 set: the 89's minus {x8+x24, x1+x8}
  plus {x8+x16, x0+x16}, i.e. the "rescue"/0.28 lineage (`2026-11-02-why` 56 states, `2026-11-02-v9b` 17). They
  share 48-49 of their 58 helpers with the union of L0 [measured, `s7.out`]. So the archive statement "no 90@4
  inspected had more than 25 first-layer gates" is **false on the full data** (true only for the 10-31 adopt
  records, which was the data at the time).
- The 90@4 landscape is not one family: 183 first layers, 5,796 rotation classes; the 89@4 is 1 family. That contrast
  is the measured core of "unusual".

---------------------------------------------------------------------------------------------------------

## Part 2. Properties mathematically required of every 89@4 (or any depth-4) circuit

Notation: n_L = gates at least level L; h_L = non-output helpers at level L; G = gates. MixColumns outputs have
weight 5 (20 outputs) or 7 (12 outputs) [measured, `s7.out`, from the matrix file].

**2.1 [proved]** A value at level L has support at most 2^L. So no output is at level <= 2 (weights 5 and 7 exceed
4), and every output of a depth-4 circuit is at level 3 or 4. The weight-16 bound at level 4 does not bind.

**2.2 [proved]** In a trimmed depth-4 circuit no helper is at level 4 (nothing could use it within depth 4), and no
output is at level 1 or 2. Hence n_1 = h_1, n_2 = h_2, n_4 = outputs at level 4, and
G = 32 + h_1 + h_2 + h_3. The family: 89 = 32 + 26 + 22 + 9 (20 outputs at level 3, 12 at level 4). NIST 90@4
(22/26/28/14): 90 = 32 + 22 + 26 + 10. So "89 vs 90" is a one-helper difference in an identity that lets the three
helper levels trade against each other; nothing in the identity fixes h_1.

**2.3 [derived, support arithmetic]** A level-3 output y = p xor q with p at level 2 (weight 1-4) and q at level
<= 2. Weight 5: the only splits are 4+1, 3+2 (disjoint) or 4+3 with one cancelled bit; weight 7: 4+3 disjoint or
4+4 with one cancellation. A level-2 value of weight 4 is the sum of two disjoint level-1 pairs; of weight 3, a
pair plus an input. Hence every weight-5 output at level 3 needs at least 2 level-1 pairs inside its support, every
weight-7 one at least 3 (or 4 with a cancelling pair); an output at level 4 needs only 1. A pair lies inside at most
6 target supports (4 pairs do; 44 lie in 3, 108 in 2; `2026-11-02-why/foundations/REPORT.md` 1.4), so the covering
bound from 2.3 is h_1 >= about 7-10 for the family's 20 level-3 outputs, far from 26. **The counting argument does
not bite.** Consistently, depth-4 circuits with 21-26 first-layer gates exist at 90 and with 19-26 at 91
[measured, 1.3]. Whether an 89@4 can have fewer than 26 first-layer gates is **open**: 26 is a property of the one
found family, not a derived requirement. A real answer needs an exact search over first layers (SAT/ILP), not
available in this budget.

**2.4 What the depth cap does to neutral moves [proved + measured].** A remove1 neutral move removes helper h
and adds one repair w such that all targets are again realizable within the search cap. Every repair valid at cap 4
is valid at a higher cap, so the cap-4 fan of a state is a subset of its uncapped fan, and the cap-4 plateau is a
subset of the uncapped neutral closure [proved]. Measured on L0 members (`s8_capfan.py`, pes_lib exact remove1):

| search cap | neutral remove1 moves per L0 state | down moves | neutral closure of member 0 |
|---|---:|---:|---|
| 4 (the engine's cap-4 setting, slack 0) | 8 (all to depth 4) | 0 | **81, complete** |
| 5 (search cap 6 with the engine's default slack) | 15 (8 at depth 4, 7 at depth 5) | 0 | >= 3,096 after 1,500 expansions, not complete |
| none | 15 | 0 | >= 6,117 after 1,500 expansions (depths 4-10), not complete |

So "sealed" is the cap: at cap 4 the plateau is 81 states with 8 exits each; without the cap the same circuit sits
in a plateau at least 75 times larger. No down move was found from any of the 1,500 + 1,500 expanded uncapped states
either, so leaving 89 downward needs more than a short remove1 walk (Part 3.2 shows the full engine does it in
minutes). Why these 4 factors and no others survive the cap: a 3-leaf re-pairing moves the middle node between
levels; with leaves (1,1,0) the root stays at level 3 whichever pairing, so the cap allows all 3 choices; the 7 extra
uncapped moves produce depth-5 states, i.e. re-pairings that push a root or a consumer to level 5 [derived from 2.4
and the slot table].

**2.5 [derived]** "One step up and everything falls back" is a plateau property, not a depth-window one. The engine's
depth window (reject non-improving moves more than 2 levels deeper than the chain best; `engine/loop.py` line 98,
626) is inactive at cap 4 with slack 0: the ValueSet itself refuses values deeper than 4
(`core/objective.py`: search_cap = depth_cap + slack, slack 0 for cap 4 since `hard_cap_margin` leaves no room;
`2026-10-31-adopt/runs/control/settings/campaign.json` "objective.soft_depth_slack": null). Gate acceptance allows
+1 steps within best+2 at p 0.15 (`engine/acceptance.py` Threshold; settings `max_uphill` 1, `best_window` 2,
`uphill_p` 0.15), so a chain at 89 may roam 90-91. What is small is not the window but the number of distinct states
the capped moves can reach there: B1 = 16,173, D1 = 76,626 [measured, barrier REPORT 2.2], and every one of them
descends only into L0 [checked there].

**2.6 Archive lower-bound attempts [archive, status only].** `AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23` and
`AES_DEPTH4_RECURSIVE_ACCOUNTING_PUSH2_2026-10-23` (READMEs, REPORT.txt, FINAL_LAYER_STATUS.txt) state themselves
that the rigorous total lower bound stays at 75 (unrestricted) and that no depth-4 bound above it was proved; their
"84" results are conditional on specific output-parent incidences, and the "N + 4p + kappa >= 81" is a coupled
geometry constant, not a gate count. `RECORD_89_vs_90_structural_report.md` concerns an unrestricted 89 at depth
10 (the July "RECORD_89"), not the 89@4. None of these constrains h_1 at depth 4. Nothing in this part was taken
from them.

---------------------------------------------------------------------------------------------------------

## Part 3. Behaviour caused by the search procedure

### 3.1 Catchment: the level-1 set decides, and only two lineages ever had it [measured]

Every one of the 526 records traces to one of two entries into L0 (`s9.out`, `s11.out`, DECISIONS/HISTORY files):

1. **Control mc-cap4-01, 2026-10-31, 914 s, seed July 91@4** (repo logs). The July 91@4 shares only 18/26 of the
   89's pairs; the plateau walk at 91 swapped 8 pairs and arrived at the 89's exact first layer, then one
   `walk.remove1` gave -2 [measured, `2026-11-02-why/foundations/REPORT.md` 1.2, from `dossier.json` values_before].
   The 156 adopt/control records are this worker plus the 4 others that pulled its state (`sharing = "pull"`).
2. **v9c mc-cap4-04, 2026-11-04-12h, 6,881 s, seed NIST 90@4** -- the only engine run that reached 89@4 from a
   NIST-seeded worker. It did so after a stall restart at 6,041 s onto shelf member `08226d6b72c8`, a 90@4 from
   mc-cap4-07 with layout (26, 23, 30, 11) whose level-1 set already equalled the repo 89's
   [`2026-11-04-12h/DECISIONS.md` 2026-11-04 ~03:45 entry; restart event in
   `runs/v9c/workers/mc-cap4-04/events.jsonl` t = 6041.27], then 840 s of `walk.remove1`; with `sharing.adopt_seconds
   = 10` the other 9 workers were in L0 within 13 s (first records 6,881-6,894 s). The 317 v9c records are this one
   event. v9c's novelty acceptance (`mask_beta` 40) is the plausible reason mc-cap4-07 drifted 14 first-layer units
   from NIST [guess].

Everything else seeded in L0 directly (`2026-10-31-long` aes-lowdepth and `2026-11-04-mc87` from89 use
`ours-g89-d4.json` / `mc-g89-d4-repo.json`) or pinned the 89's first layer (foundation/repair hits).
Walks that did not have the first layer never got there: the 10-29 hunts (`2026-10-29-hunt89at4`, `-hunt2-89at4`:
1,034 g90-d4 record files, 0 g89), the adopt side, v9b, v9c-12h, v9e, 11-06-layout, 11-06-w500 (7,656 g90 files, 0
g89) [measured census `s2.out`, `s5` output, `s4_summary.json`]. The pinned-completion experiments quantify it: the
89's first layer completes to 89 in 6/10 x 300 s; NIST's to 90 in 11/11; any one pair dropped or swapped, 92+ in
18/18 [measured there, `2026-11-02-why/foundations/REPORT.md` 3.2-3.4; repair B1-B2 adds: from the "rescue" set the
89 is 3 single-pair steps away with every intermediate at 90, and the cross pair x1+x8 must come first].

So "catchment" means: the basin of L0 under the engine is, to the precision of the data, the set of states carrying
L0's first layer (plus the band D1 above it); a walk's first layer moves one pair at a time at zero cost only
(`walk.remove1` repairs), and the first-layer landscape between NIST's set and the 89's is +2 to +4 at equal effort
[measured, foundations 3.5]. The rarity of 89@4 is the rarity of landing on that first layer, not of descending once
there.

### 3.2 "One step up and fall back": exact under the cap, false without it [measured]

- Under cap 4: exact for the whole +1 band and its remove1 closure (barrier REPORT 2.2), for random +1 envelope
  climbs up to 3 steps (1,000/1,000 each) and 98% at 4 steps (`2026-11-06-89at4/REPORT_A.txt`). It is not caused by
  the depth window (2.5); it is the capped move set (2.4).
- Without the cap, with the full engine, L0 is **not** a trap: the 4 mc87 `from89` workers (depth_cap none, seeded
  with the repo 89@4) each reached 88 gates within 131-640 s (depths 7-9 first; 3 of 4 by `walk.remove1`, 1 by
  `lns.rebuild`), and their first 88s keep only 17-19 of the 26 pairs with |L1| = 21-22; their 257 88-gate records
  span |L1| 16-23 and overlap 9-20 with the 89's pairs [measured, `s12` output; files under
  `~/xs-campaigns/2026-11-04-mc87/runs/mc87/workers/from89-*/records/`]. Their 11 89@4 records all carry the exact
  89 first layer: the chains sat in L0 first, then left through depth-5+ states. Leaving downward meant dropping
  first-layer pairs, which at cap 4 no single move can do (study B: 17 of the 26 pairs have no remove1 or
  envelope replacement at depth <= 4 in any of the 81 states).

### 3.3 What the 2026-11-06 study measured, exactly, and where its words exceed it

Study A (`catch.py`, `A.jsonl`, 3,530 tries): start = random L0 member; up = k random expand-envelope edits with
dgates = +1 and depth <= 4; down = BFS over exact remove1 neutral-and-down moves at depth <= 4, bounded at 5,000
states, stopping at the first state with <= 89 gates. Measured: k = 1-3 all 1,000 tries return to L0; k = 4: 295/300
home, 5 cut; k = 5: 31/150 home, 119 cut; k = 6: 1/80 home, 79 cut; no try ended at another 89 or below.
Exceeds evidence: (i) "the drop at k = 5, 6 is the budget, not the funnel ending" is marked [guess] there and stays a
guess (no try at k >= 5 with a larger bound was run); (ii) the envelope is a superset of what the real Expand does
(barrier REPORT 7), and the engine also climbs by lns/structural moves, so the "walls" are those of R1 + envelope,
not of the engine; (iii) descents stop at the first <= 89 state, so "only L0" means "L0 is the nearest 89 in BFS
order", not that no other 89 is reachable from those band states; (iv) "L0 is the bottom of a wide funnel" and
"the first-layer choice that leads into it is made far from it" are interpretations; the measured content is 3.1.

Study B (`l1cost.py`, `l1cost.json`): exact for the stated move classes in all 81 states: no pair can be removed by
remove1 at depth <= 4; 6 pairs have +1 envelope replacements in every state, 3 in some, 17 in none; the bounded
"ban" BFS from the +1 replacements of the 6 pairs exhausted 324-648 states, all at 90. Exceeds evidence: "the
first layer is locked from the inside" is correct for single capped moves; the guess "the depth cap is the cause" is
now supported (2.4, 3.2). DESIGN.md's "holds all 510 recorded 89@4 circuits" should read 526 records, 90 distinct,
of which 9 are in rot8(L0), not in L0 (1.1).

---------------------------------------------------------------------------------------------------------

## Synthesis

**What is unusual [measured].** At 90 gates the depth-4 landscape has 183 first layers and ~5,800 plateaus' worth of
distinct states on record; at 89 there is one family (81 states, 53-value core, 4 free re-pairings) and its byte
rotations, reached by two events in all runs, both from a state that already carried the family's 26-pair first
layer. The family's plateau is 81 states under the cap but >= 6,117 states uncapped, and the uncapped engine
leaves it for 88 in minutes.

**Candidate explanations and the evidence that separates them.**

| explanation | for | against / open |
|---|---|---|
| E1 [guess]: 89 at depth 4 is possible only over this first layer (26 pairs forced) | no other 89@4 family in ~10^4 worker-hours; every perturbed first layer completes to 92+ (300 s runs) | Part 2 finds no argument forcing 26 or this set; 90@4 exists with 21-26 pairs; completions are upper bounds (July set: 93 found, 91 known) |
| E2 [derived + measured]: the cap-4 move set makes first layers nearly immobile at 89-90 (one pair at a time, +2..+4 to cross), so the family is reachable only from first layers already equal to it | study B, foundations 3.4-3.5, repair B1, 3.1 entries, s8 | does not say whether other families exist |
| E3 [derived + measured]: "sealed" = small capped plateau; uncapped the same circuit is in a large connected region with exits to 88 | s8 (8 vs 15 moves; 81 vs >= 6,117), mc87 from89 4/4 to 88 | exits to 88 need depth 6+; at cap 5 the closure is also large but no exit was found in 1,500 expansions |

E2 + E3 are established; E1 is open and is the only one that would make 89@4 "special" rather than "the cap's
artefact plus a rare first layer".

**Falsifiable predictions.**

1. [tested now, confirmed] An uncapped chain started inside L0 reaches 88 within minutes and its 88s keep <= 19 of
   the 26 pairs. mc87 from89: 4/4 workers, 131-640 s, 17-19 pairs kept [measured, 3.2]. Sharper version, testable
   now in ~15 min: a bounded exact remove1 BFS from L0 with no cap reaches 88 within 20,000 states (s8 saw no
   down edge in 1,500); if not, the exit is through lns/expand only.
2. [testable now on existing files, ~10 min] Every 90@4 whose first layer is exactly the 89's (any rotation) lies in
   D1 and descends to L0 by remove1 alone. Test objects: the four 90s with layout (26, 22, 30, 12) that the pinned
   completions stopped at (`2026-11-02-why/foundations/analyze_mc.out`, `out/`), and the v9c shelf member if its
   90 state is recoverable from mc-cap4-07's records. A failure would show a second 90-level trap over the same
   first layer, i.e. the basin is not "first layer = L1".
3. [needs a run: 10 x 300 s pinned completions, one core-hour] Pinning the 89's first layer at cap 5 (slack 0)
   completes to 89, not 88: the 88@5 plateaus have first layers of 19-23 pairs sharing <= 6 with the 89's
   (`foundations` 1.2 table, s12 overlaps 9-20). If 88 appears over the 89's first layer at cap 5, E1 is wrong in
   the strong form (the first layer is not what makes 89 cheap; the cap is).
4. [needs a run: a 2 h cap-4 campaign from NIST 90@4 with v9c settings] The time to 89@4 is the time to a 90@4
   carrying one of the four rotations of the 89's first layer, and the four rotations are hit equally often
   (symmetry); every arrival will pass through D1. One arrival in 20 worker-hours so far (3.1) is the base rate.

**What transfers to the unrestricted 87 question, and what is depth-4 only.**
- Depth-4 only: the 81-state plateau, the immobile first layer (study B), the single family, "one step up falls
  back", the 26/22/29/12 profile. All of these follow from the capped move set (2.4) and vanish without the cap
  (3.2). Nothing from the 89@4's rigidity should be read as evidence about 87.
- Transfers [derived]: (a) plateaus are exact products of 3-leaf re-pairings (here 3^4; the repo 88@5 is 2 x 3^7
  [barrier REPORT 2.1]), so plateau size counts free re-pairings, not "room to move"; (b) a `remove1` walk moves the
  first layer one pair at a time at zero cost only, so a new family whose first layer differs in several pairs is
  reached only where there is slack (+2 above the floor, as the 914 s walk at 91 did) or by moves that rebuild
  several pairs at once; (c) records cluster into few lineages traceable to few entry events (3.1), so record counts
  overstate coverage by two orders of magnitude (526 records, 2 events); (d) at the 88 level the landscape is far
  more connected (95 plateaus, joins at <= 90 in real chains [barrier REPORT 2.1]), so an 87, if it exists, is more
  likely to be reached by the uncapped walk than an 89@4 ever was at cap 4 -- the 89@4's rarity is not a model for
  87's.

## Files

`s1_sources.sh`, `s2_archive_census.sh`, `s3_archive_read.sh`, `s5_engine_census2.sh`, `s6_engine_seeds.sh`,
`s9_misc.sh`, `s10_seeds_hits.sh`, `s11_v9c_entry.sh` (source dumps -> `s*.out`); `s4_collect.py` (census ->
`s4_summary.json`, `states_*.json`); `s7_structure.py` (product structure -> `s7.out`, `s7_structure.json`);
`s8_capfan.py` (cap comparison -> `s8.out`, `s8_capfan.json`); `s12_entry_exit.py` (from89 first layers, shelf
restart); `s14_fix.py` (slot roots, shelf entry); `s15_write_report.py` (this file). All read-only on the repo and
campaign folders.
'''

with open(OUT, "w", newline="\n") as fh:
    fh.write(TEXT.replace("\r\n", "\n"))
print("wrote", OUT, len(TEXT.splitlines()), "lines")
