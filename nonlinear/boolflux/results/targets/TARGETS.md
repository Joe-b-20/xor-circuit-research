# Ten targeted campaigns against NIST AES S-box circuits (2026-11-15 and 11-16)

This page is the record of the targeted campaigns: what was asked, the rules every result was
held to, the best result per target with its frontier, how each was found, what failed, how
everything was verified, and how to reproduce it. We do not claim that any circuit here is
optimal or the best known. They are what the search reached in the time it ran, against the
pinned NIST collection and our own archive. Published or unpublished work may have better
circuits, and more search time would likely improve several of them. The only general lower
bound on AND count we have is 13 ANDs [P] ([../../HISTORY.md](../../HISTORY.md), study phase).
No negative result on this page is a general lower bound: each holds in the exact case stated
next to it.

Labels: **[V]** a circuit that passed `campaigns/aes_check.py` (two verifiers, all 256 inputs,
NIST library and counting); **[C]** exhaustive or exact within the stated case only;
**[P]** proved; **[H]** heuristic or empirical (one or a few runs).

The numbers of sections 3, 4, 6 and 7 come from the morning ledger of 2026-11-16 13:19 UTC (code d9507dd), after the overnight runs of 2026-11-16 (02:04-13:19 UTC). The per-target text describes the results of 2026-11-15; each "Best" line ends with the state after the night, and the night's runs are in sections 5 and 7 and in [night-2026-11-16/](night-2026-11-16/) (the runner's plans and status pages).

Contents: [1 The request](#1-the-request) · [2 Rules](#2-rules-and-definitions) ·
[3 Results](#3-results) · [4 Per target](#4-per-target-pages) · [5 Failed experiments](#5-failed-experiments-and-dead-ends) ·
[6 Verification](#6-verification) · [7 Compute](#7-compute-and-hardware) ·
[8 Reproduction](#8-reproduction) · [9 27 ANDs](#9-the-27-and-objective-z)

## 1. The request

On 2026-11-15 at about 15:10 UTC the user asked for ten campaigns, each against one circuit of
usnistgov/Circuits `data/slp/aes/aes-sbox` at the pinned commit
`3d807741f937d29d3bef4f32f142ccda0cda9070`, each with its own priorities. The request is copied
verbatim in [USER-REQUEST.md](USER-REQUEST.md); the machine-readable form, with the thresholds
used, is [TARGETS.json](TARGETS.json). The agents' brief is [BRIEF.md](BRIEF.md) (phase 1,
15:30-23:45 UTC); phase 2 (from 2026-11-16 00:00 UTC) is [BRIEF2.md](BRIEF2.md) (copied here by the morning check;
until then `~/xs-campaigns/2026-11-15-targets/BRIEF2.md`).

Changes to TARGETS.json during the campaign, all by the user at 2026-11-15 23:50 UTC:

- **Search states may exceed the caps.** The optimiser may go above the A, AD, G and GD limits
  during a search, as long as the **recorded** result is inside the target's hard limits and
  better. Path certification (section 2) is informational from then on.
- **T03** may trade depth for gates: GD <= 22 with at least 3 gates saved; also report any
  G <= 123 at any GD (the pinned 28/5/124/27 has 124).
- **T05**: any G <= 102 at any GD is a new overall record.
- No work on 27 ANDs until the user says otherwise.

## 2. Rules and definitions

Every comparison uses NIST's gate library {AND, XOR, XNOR, NOT} and NIST's counting (every gate
counts, NOT included; inputs have depth 0) ([../../VERIFICATION.md](../../VERIFICATION.md)
section 3). A tuple is written A/AD/G/GD: AND count, AND depth, gate count, gate depth.

| term | definition (TARGETS.json, recomputed by the ledger on every run) |
|---|---|
| hard limits | A <= ref A and AD <= ref AD on every recorded result, never traded. Until 23:50 UTC also on every retained search state (section 2.1) |
| strict | within the hard limits, G <= ref G and GD <= ref GD, at least one strictly smaller |
| tradeoff `gates_for_depth` | ref GD < GD <= GD_max (T01 24, T03 22, T04 21, T07 29; T05 any) and G <= ref G - 3 |
| tradeoff `depth_for_gates` | GD <= GD_max < ref GD (T08 12, T09 11, T10 9) and ref G < G <= ref G + 8 |
| tradeoff `and_depth_for_gates` | T05 only: AD < 7, AD <= 6, with G or GD above the reference; best G (then GD) is reported per AND depth |
| notable (from 23:50 UTC) | T03 any G <= 123, T05 any G <= 102, at any GD inside the hard limits; listed separately. With the 3-gate threshold a T05 `gates_for_depth` tradeoff needs G <= 100, so 101-102 at GD > 32 is notable (a new overall gate record) but not a tradeoff |
| frontier | every verified circuit within the hard limits that is Pareto-minimal in (G, GD); also kept: Pareto in (A, AD, G, GD) |
| known / reproduced / new | known = tuple realised by an archive file of 2026-11-15 15:20 UTC or earlier; reproduced = a campaign circuit structurally equal to, or with the tuple of, such a file; new = neither. From phase 2 the ledger splits "new" by era: `known-by-23:50 (<agent>; new vs archive)` for the results of 2026-11-15 (snapshot of 23:50 UTC) and `new (<group>)` for the night of 11-16. This page calls both "new": both are new against the 15:20 archive and the pin |

The thresholds 3 (smallest "substantial" gate gain for a depth cost) and 8 (largest "modest" gate
cost for a depth gain) are the coordinator's provisional reading of the user's words; the user
may change them, and the ledger reads them from TARGETS.json. A tradeoff is never described as
dominating its reference. A tradeoff that a strict circuit dominates is dropped from the
tradeoff lists. A circuit that is neither strict nor a permitted tradeoff can still be a
frontier point; it is listed as `other`.

The **donor ruling** (coordinator, 18:45 UTC, [COMPLIANCE-1820.md](COMPLIANCE-1820.md)): a
construction may take part of a circuit outside the target's limits (for example the front
layers of the 48-AND hub circuit under a newly built bottom, agent P7) when no complete circuit
the builder holds, retains or outputs exceeds the limits. The donor is material, not a search
state. Such results carry `donor_outside_limits: <file>` and a builder statement in the sidecar.

### 2.1 The kernel-repair episode (18:10-23:50 UTC)

At 18:10 UTC agent P1 found that a gate-kernel stage started above its GD cap (every pull and
every `osc` repair) ranks moves by the **sum** of the cap excesses, so it may raise A or AD
above their caps while it lowers GD; and `strategies/F/fdrive.py` wrote `best.circ.txt` even for
such an infeasible circuit (`strategies/P1/NOTES.md` section 6; `kernel/bfx.c` lines 285-292 and
1064-1077). No recorded result was ever outside the limits: every agent re-checked its outputs.
But the user's rule at the time also covered retained search states. From 18:20 UTC
([COMPLIANCE-1820.md](COMPLIANCE-1820.md)):

1. every kernel call ran with `repair_keep 1` (no move raises the excess of any single cap, so
   from a start inside A/AD no state leaves them), through `strategies/P1/fdrive_p1.py` and its
   copies, with the kernel built from the repository's `kernel/bfx.c` (bfx-94a75e2c18); the hub
   kernel bfx-593fa798f5 does not know the key;
2. every saved circuit got `path_certified` true / false / unknown in its sidecar;
3. every result that was not certified was re-derived under `repair_keep 1`, or certified by an
   exact replay with a trace of every accepted kernel state (agent P3, `pdrive_replay.py`).

Outcome: P3's replays showed that the kernel stages that produced 115@20, 116@19 and the first
114@19 accepted only states with A <= 32, AD <= 4 (55,310-58,897 accepted states each), which
certified the 116@19 lineage; and that the stage before the first 113@21 / 113@20 accepted
A = 33 states, so that lineage (113@21, 113@20 and the 114@19 made from them) was not certified. Those tuples were then re-derived from certified starts (P3 rkG1, rkH1,
from P5's certified 112/22 and 111/25). At 23:17 UTC **every strict and tradeoff point of the
ledger had a certified campaign file or was known** (LEDGER.md summary). At 23:50 UTC the user
decided that search states may exceed the caps; certification is now informational only.

## 3. Results

State of the ledger at 2026-11-16 13:19 UTC (code d9507dd, 4,162 archive and 614 campaign files including the night's, 4,776 verified). "Pinned dominating" is "none" for every listed point.

| target | reference A/AD/G/GD | primary | best strict | best permitted tradeoff | status |
|---|---|---|---|---|---|
| T01 | 28/4/132/22 | G < 132, GD <= 22 | 28/4/131/22 (known), 28/4/132/20 (known) | none | primary met (by known circuits only) |
| T02 | 28/4/176/14 | GD < 14 or G < 176 | **28/4/174/14** (new, P2) | none permitted | primary (GD < 14 at G <= 176) not reached; G < 176 at GD <= 14: 28/4/174/14 |
| T03 | 28/5/128/20 | G < 128, GD <= 20 | none | none | primary (G < 128 at GD <= 20) not reached; notable G <= 123: none; frontier points first found tonight |
| T04 | 32/4/117/19 | G < 117, GD <= 19 | **32/4/114/19** (new, P3), **32/4/115/18** (new, P3), **32/4/117/17** (new, P3) | gates for depth **32/4/112/21** (new, M4) | primary met; frontier points first found tonight |
| T05 | 32/7/103/32 | G < 103, GD <= 32 | **32/7/103/29** (new, night conjpull) | AD6 32/6/104/31 (known); AD5 32/5/104/29 (known); AD4 **32/4/111/25** (new, P5) | primary (G < 103 at GD <= 32) not reached; GD < 32 at G <= 103: 32/7/103/29; notable G <= 102: none; frontier points first found tonight |
| T06 | 34/4/139/13 | GD < 13, G <= 139 | 34/4/134/13 (known) | none permitted | primary (GD < 13 at G <= 139) not reached; G < 139 at GD <= 13: 34/4/134/13; frontier points first found tonight |
| T07 | 35/3/139/27 | G < 139, GD <= 27 | **35/3/138/23** (new, night conjpull), **35/3/139/21** (new, night conjpull) | none | primary met; frontier points first found tonight |
| T08 | 35/3/183/13 | GD <= 12 | **35/3/165/13** (new, M3), **35/3/181/12** (new, P6) | none | primary met; frontier points first found tonight |
| T09 | 45/4/141/12 | G < 141, GD <= 12 | **38/4/135/12** (new, night bottom) | none | primary met; frontier points first found tonight |
| T10 | 59/4/159/10 | G < 159, GD <= 10 | none | none | primary (G < 159 at GD <= 10) not reached; frontier points first found tonight |

No circuit with A <= 27 exists in any scanned folder (section 9).

How to read these results:

- Every listed circuit is [V]. "New" and "not dominated by the pinned set" are [C] relative to
  the scanned folders and the 104 forward circuits of the pin only.
- The new points of T04, T07, T08 and T09 dominate their references; T02's 174/14 does too.
  The T04 tradeoff 113/20 has one more level than its reference and does not dominate it.
- Several frontier circuits are within the limits of more than one target (28/4/174/14 is within
  T01-T05). Their class differs per target; the copies in `T01/` ... `T10/` are the same circuit.
- Every new result was found in one or a few time-budgeted runs. None was re-run bit for bit
  except by the exact replays listed in section 8.

## 4. Per-target pages

Each page gives the reference, the limits and priorities, the best strict and tradeoff result,
the (G, GD) frontier inside the hard limits (generated from the ledger), the method that produced
the new points and how to reproduce them. Files in `Txx/` are the curated copies; files in
`../aes/` are the curated archive; `~/xs-campaigns/...` paths are campaign or archive files
outside the repository.

### T01: 28/4/132/22 (`aes-sbox-a28-ad4-g132-gd22-xx104-40`)

Hard limits A <= 28, AD <= 4. Primary G < 132 at GD <= 22; also gains of at least 3 gates at
GD <= 24 (tradeoff); ideally both lower.

- Best strict on 2026-11-15: 28/4/131/22 and 28/4/132/20, both **known** (study phase, agents L1 and T1).
  After the night (ledger 2026-11-16 13:19 UTC): strict frontier 28/4/131/22 [V] (known; reproduced in the night (T01 block)), 28/4/132/20 [V] (known; reproduced in the night (T01 block)).
- Best tradeoff on 2026-11-15: none. The known 28/4/130/24 saves 2 gates, below the threshold of 3.
  After the night (ledger 2026-11-16 13:19 UTC): best tradeoff: none.
- Method tried (agent P1, `strategies/P1/NOTES.md`): kernel workers over 166 legal starts,
  kernel screens at the target caps, skeleton re-synthesis (`skres`), last-layer basis swap
  (`pswap`), GF(2^8) conjugates, and span-pooled SAT LNS at D 21 and D 22. Nothing new: the
  LNS walks stayed on the 132/21 and 131/22 plateaus [H].

Ledger of 2026-11-16 13:19 UTC: 207 verified files within the hard limits, 121 distinct structures, 72 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 28/4/130/24 | other | -2 / +2 | known | none | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad4-g130-gd24-11cf1d89970b.bfx` |
| 28/4/131/22 | strict | -1 / +0 | known; reproduced in the night (T01 block) | none | [aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt](../aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt) |
| 28/4/132/20 | strict | +0 / -2 | known; reproduced in the night (T01 block) | none | [aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt](../aes/aes-nist-study-T1-t1-g132-a28-gd20-ad4.circ.txt) |
| 28/4/133/19 | other | +1 / -3 | known | none | [aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt](../aes/aes-nist-study-R1-r1-g133-a28-gd19-ad4.circ.txt) |
| 28/4/135/18 | other | +3 / -4 | known | none | [aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt](../aes/aes-nist-E-polish-g135-a28-gd18-ad4.circ.txt) |
| 28/4/138/17 | other | +6 / -5 | known | none | [aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt](../aes/aes-nist-E-polish-g138-a28-gd17-ad4.circ.txt) |
| 28/4/141/16 | other | +9 / -6 | known | none; equal tuple aes-sbox-a28-ad4-g141-gd16-xx113-27 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/4/153/15 | other | +21 / -7 | known | none; equal tuple aes-sbox-a28-ad4-g153-gd15-xx125-29 | [aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt](../aes/aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt) |
| 28/4/174/14 | other | +42 / -8 | new (P2); reproduced in the night (T02 block) | none | [aes-sbox-a28-ad4-g174-gd14-T01-P2-1.circ.txt](T01/aes-sbox-a28-ad4-g174-gd14-T01-P2-1.circ.txt) |

Pinned (G, GD) frontier within the same limits: 28/4/131/31, 28/4/132/22, 28/4/134/20, 28/4/141/16, 28/4/153/15, 28/4/176/14.

### T02: 28/4/176/14 (`aes-sbox-a28-ad4-g176-gd14-xx148-25`)

Hard limits A <= 28, AD <= 4. Primary GD < 14 with G <= 176; equally G < 176 with GD <= 14. No
tradeoffs. Depth first.

- Best strict on 2026-11-15: **28/4/174/14** [V], new (bar at 15:20 UTC: 28/4/175/14). Agent P2:
  `strategies/F/fdrive.py` mode mix from best-1400 `aes-sbox-a28-ad4-g175-gd14-xx147-68`, caps
  GD 14, AD 4, A 28, seed 1, stage 17 (`trb` bottom: timing-driven rebuild of the bottom linear
  region, then the kernel), 2,437 s into the run. Path certified: the stage started from a
  feasible state. After the night (ledger 2026-11-16 13:19 UTC): strict frontier **28/4/174/14** [V] (new, P2; reproduced in the night (T02 block)).
- GD 13 [C, these circuits]: every A <= 28 AD4 circuit in the archive has skeleton depth bound
  >= 14 (the least gate depth of any circuit with the same AND functions written as affine forms
  over the inputs and earlier ANDs); all 2,040 GF(2^8) conjugates of the 174 have bound >= 14; and
  the stage-1 cover of the 175 is rigid (9 classes of rank-1 products, two of them at level >= 4
  in every representation; `strategies/P2/NOTES.md` sections 1, 5, 6). So GD 13 at A28 needs
  different AND functions, not better XOR layers. This is not a bound for other AND functions.
- Further polishes of the 174 (trb seeds 5, 31, 201, 202; mix 32) and two conjugate pipelines:
  nothing below 174 [H].

Same frontier as T01 (same hard limits; ledger of 2026-11-16 13:19 UTC); here **28/4/174/14** (-2 / +0) is **strict**, every other point is `other`. Pinned frontier as T01.

### T03: 28/5/128/20 (`aes-sbox-a28-ad5-g128-gd20-xx100-27`)

Hard limits A <= 28, AD <= 5. Primary G < 128 at GD <= 20; also GD < 20 at G <= 128; no GD
increase for minor gate savings. From 23:50 UTC: tradeoff GD <= 22 with >= 3 gates saved
(G <= 125 at GD 21-22), and any G <= 123 at any GD is reported.

- Best strict on 2026-11-15: none. After the night (ledger 2026-11-16 13:19 UTC): best strict: none; new frontier points of class `other` tonight: 28/5/125/24.
- Best tradeoff on 2026-11-15: none under either rule (28/5/127/22 saves 1 gate; the pinned 28/5/124/27 has
  124). After the night (ledger 2026-11-16 13:19 UTC): best tradeoff: none; notable G <= 123 at any GD: none.
- New frontier point **28/5/129/19** [V] (agent P1), one gate from the secondary goal 128/19 and
  not a T03 class. Found by the span-pooled SAT LNS (`strategies/P1/unionsat2.py`;
  [HOW-IT-WORKS.md, "Span-pooled SAT LNS"](../../HOW-IT-WORKS.md#span-pooled-sat-lns)) at D 19 from the hub's 130/19
  (`../aes/aes-nist-hub-pull-g130-a28-gd19-ad5.circ.txt`), by a *sideways* query (K = G with one
  freed template dropped) at step 241, 6.2 s into the query. 44 distinct 129/19 structures were
  saved. The LNS never calls the kernel; every accepted step was checked inside A <= 28,
  AD <= 5, GD <= D. Its `path_certified` is "unknown" in the ledger because the sidecar does not
  set it.
- Over all 57 LNS logs: 26,719 queries; improving queries (K = G - 1) 2 SAT, 11,419 UNSAT, 452
  UNKNOWN; sideways queries 10,376 SAT. Each UNSAT is [C] for its own query only (the forced
  templates plus the pool).

Ledger of 2026-11-16 13:19 UTC: 659 verified files within the hard limits, 361 distinct structures, 214 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 28/5/124/27 | other | -4 / +7 | known | none; equal tuple aes-sbox-a28-ad5-g124-gd27-xx96-26 | `~/xs-campaigns/2026-11-14-hub/long/archive/104c1eda4172.bfx` |
| 28/5/125/24 | other | -3 / +4 | new (night, conjpull) | none | [aes-sbox-a28-ad5-g125-gd24-T03-night-T03-1.circ.txt](T03/aes-sbox-a28-ad5-g125-gd24-T03-night-T03-1.circ.txt) |
| 28/5/126/23 | other | -2 / +3 | known; reproduced in the night (T03 block) | none | `~/xs-campaigns/2026-11-15-study/T1/overnight/run/found/front/aes-sbox-a28-ad5-g126-gd23-0c61a5821a27.bfx` |
| 28/5/127/22 | other | -1 / +2 | known; reproduced in the night (T03 block) | none | [aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt](../aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt) |
| 28/5/128/20 | other | +0 / +0 | known | none; equal tuple (the reference) | `~/xs-campaigns/2026-11-14-hub/long/archive/4096beef1bbf.bfx` |
| 28/5/129/19 | other | +1 / -1 | new (P1) | none | [aes-sbox-a28-ad5-g129-gd19-T03-P1-1.circ.txt](T03/aes-sbox-a28-ad5-g129-gd19-T03-P1-1.circ.txt) |
| 28/5/133/18 | other | +5 / -2 | known; reproduced in the night (T03 block) | none | [aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt](../aes/aes-nist-hub-join-g133-a28-gd18-ad5.circ.txt) |
| 28/5/136/17 | other | +8 / -3 | known; reproduced in the night (T03 block) | none | [aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt](../aes/aes-nist-hub-trb-g136-a28-gd17-ad5.circ.txt) |
| 28/4/141/16 | other | +13 / -4 | known | none; equal tuple aes-sbox-a28-ad4-g141-gd16-xx113-27 | `~/xs-campaigns/2026-11-14-hub/long/archive/29fb319f47ad.bfx` |
| 28/5/150/15 | other | +22 / -5 | known | none; equal tuple aes-sbox-a28-ad5-g150-gd15-xx122-23 | `~/xs-campaigns/2026-11-14-hub/long/archive/09fbfd47fda3.bfx` |
| 28/4/174/14 | other | +46 / -6 | new (P2); reproduced in the night (T02 block) | none | [aes-sbox-a28-ad4-g174-gd14-T03-P2-1.circ.txt](T03/aes-sbox-a28-ad4-g174-gd14-T03-P2-1.circ.txt) |

Pinned (G, GD) frontier within the same limits: 28/4/141/16, 28/4/176/14, 28/5/124/27, 28/5/128/20, 28/5/150/15.

### T04: 32/4/117/19 (`aes-sbox-a32-ad4-g117-gd19-xx85-6`)

Hard limits A <= 32, AD <= 4. Primary G < 117 at GD <= 19; also substantial gains at GD <= 21.

- Best strict on 2026-11-15: **32/4/114/19** [V] (3 gates below the reference and 2 below every pinned
  circuit at GD <= 19); **32/4/115/18** (G and GD both lower); 32/4/117/17. All new, agent P3.
  After the night (ledger 2026-11-16 13:19 UTC): strict frontier **32/4/114/19** [V] (new, P3; reproduced in the night (T04, T05 blocks)), **32/4/115/18** [V] (new, P3; reproduced in the night (T04, T05 blocks)), **32/4/117/17** [V] (new, P3; reproduced in the night (T04, T05 blocks)); new frontier points of class `other` tonight: 32/4/119/16.
- Best tradeoff on 2026-11-15: **32/4/113/20** [V] (4 gates for +1 level; it does not dominate the
  reference). After the night (ledger 2026-11-16 13:19 UTC): best tradeoff: gates for depth **32/4/112/21** (new, M4).
- Method (`strategies/P3/NOTES.md`, sections "Conjugates" and "Runs"): GD 19 was a plateau for
  every kernel walk from the A32/AD4 family, and the four of those circuits checked have the same
  function-level bottom [C, those four]. The new points came from **GF(2^8) conjugation** of a start
  ([HOW-IT-WORKS.md, "Conjugation and staged pulls"](../../HOW-IT-WORKS.md#conjugation-and-staged-pulls)) followed by **staged pulls**:
  the lam 188, k 0 conjugate of the archive 32/4/116/20 (`a43e1ae3d73f`), kernel in gate mode at
  cap GD 24 (240 s, 127@22 -> 114@24), then mix at cap 21 (113@20 after 362 s), then mix at
  cap 19 (114@19 after 102 s). One kernel stage of that first lineage was later shown to pass
  through A = 33 states (section 2.1); the same tuples were re-derived on certified paths:
  P5's lineage NIST 117 -> lam 188 conjugate -> gate/mix rounds -> 112/22 and 111/25, then P3
  rkG1 (from 112/22: mix 21 -> 113@20 -> mix 20 -> mix 19 -> 114@19, 332 s) and rkH1 (from
  111/25: mix 23 -> 112@22 -> mix 21 -> 113@20 -> mix 19 -> 114@19, 288 s); 115/18 by rkI1 and
  117/17 by rkN1 (mix 17 from a 118@17). Seven certified lineages all stopped at 113@20 / 114@19
  [H]: a plateau for this kernel in this basis.
- The curated copies `T04/aes-sbox-a32-ad4-g114-gd19-T04-P3-1` and `-g113-gd20-T04-P3-1` are the
  first finds (`p3-pipe116m19-...-a59961d7ad`, `p3-pipe-conj-116g20-l188-k0-m21-...-db41c24e64`),
  whose search path left A32. Under the rule of 23:50 they count. The certified circuits with the
  same tuples are `P3/found/p3-rkG1-s3-mix19-k1-...-73e77c68fc` (114/19) and
  `p3-rkG1-s1-mix21-k1-...-6a349e2eb2` (113/20). At the morning curation the T04 copies are: 32/4/114/19 -> `p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt`; 32/4/113/20 -> `p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt`. These are the certified circuits (ledger representative, DOCS-TODO 32.1).
- Failed for T04 [H unless marked]: plain `trb` at cap 19 (back to 117@19); annealing over
  quadratic bottom decompositions (the builder is 3-4 gates worse than polished originals, and
  built cost rises to 131-150 within ~100 flips); generic SAT for the bilinear tensor rank (no
  answer in 120-250 s even at the known rank 18); packing and gadget models as predictors of built
  cost; further conjugation of the conjugated circuit (the identity is then the best conjugate by
  the proxy). Exact: the 117's 5-product bottom block cannot be done with 4 ANDs, in the model
  "the 12 standard products of the 117 fixed, any 4 ANDs of affine forms over (1, X, Y), the 9
  level-1 ANDs as corrections, X-linear residual 0" [C, that model only: UNSAT in 2.6 s].

Ledger of 2026-11-16 13:19 UTC: 808 verified files within the hard limits, 585 distinct structures, 261 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 32/4/111/25 | other | -6 / +6 | new (P5); reproduced in the night (T05 block) | none | [aes-sbox-a32-ad4-g111-gd25-T04-P5-1.circ.txt](T04/aes-sbox-a32-ad4-g111-gd25-T04-P5-1.circ.txt) |
| 32/4/112/21 | tradeoff:gates_for_depth | -5 / +2 | new (M4) | none | [aes-sbox-a32-ad4-g112-gd21-T04-M4-1.circ.txt](T04/aes-sbox-a32-ad4-g112-gd21-T04-M4-1.circ.txt) |
| 32/4/113/20 | tradeoff:gates_for_depth | -4 / +1 | new (P3); reproduced in the night (T04, T05 blocks) | none | [aes-sbox-a32-ad4-g113-gd20-T04-P3-1.circ.txt](T04/aes-sbox-a32-ad4-g113-gd20-T04-P3-1.circ.txt) |
| 32/4/114/19 | strict | -3 / +0 | new (P3); reproduced in the night (T04, T05 blocks) | none | [aes-sbox-a32-ad4-g114-gd19-T04-P3-1.circ.txt](T04/aes-sbox-a32-ad4-g114-gd19-T04-P3-1.circ.txt) |
| 32/4/115/18 | strict | -2 / -1 | new (P3); reproduced in the night (T04, T05 blocks) | none | [aes-sbox-a32-ad4-g115-gd18-T04-P3-1.circ.txt](T04/aes-sbox-a32-ad4-g115-gd18-T04-P3-1.circ.txt) |
| 32/4/117/17 | strict | +0 / -2 | new (P3); reproduced in the night (T04, T05 blocks) | none | [aes-sbox-a32-ad4-g117-gd17-T04-P3-1.circ.txt](T04/aes-sbox-a32-ad4-g117-gd17-T04-P3-1.circ.txt) |
| 32/4/119/16 | other | +2 / -3 | new (night, conjpull) | none | [aes-sbox-a32-ad4-g119-gd16-T04-night-T04-1.circ.txt](T04/aes-sbox-a32-ad4-g119-gd16-T04-night-T04-1.circ.txt) |
| 32/4/125/15 | other | +8 / -4 | known | none | [aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt](../aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt) |
| 28/4/174/14 | other | +57 / -5 | new (P2); reproduced in the night (T02 block) | none | [aes-sbox-a28-ad4-g174-gd14-T04-P2-1.circ.txt](T04/aes-sbox-a28-ad4-g174-gd14-T04-P2-1.circ.txt) |

Pinned (G, GD) frontier within the same limits: 28/4/176/14, 32/4/117/19, 32/4/127/15.

### T05: 32/7/103/32 (`aes-sbox-a32-ad7-g103-gd32-xx71-10`)

Hard limits A <= 32, AD <= 7. Two separate achievements: G < 103 at GD <= 32 (the overall
gate-count record; from 23:50 UTC any G <= 102 at any GD), and lower AND depth (6, 5, 4) with G
as close to 103 as possible. GD < 32 at G <= 103 is also valued.

- Best strict on 2026-11-15: none. No circuit below 103 gates at A <= 32 exists in the archive or the
  campaign. After the night (ledger 2026-11-16 13:19 UTC): strict frontier **32/7/103/29** [V] (new, night conjpull); new tonight: 32/7/103/29 (conjpull, block T05 (pass 1), from 32/7/103/32, stage t32-bottom, 03:03 UTC); notable G <= 102 at any GD: none; new frontier points of class `other` tonight: 32/7/104/26.
- Best per AND depth (`and_depth_for_gates`; G then GD):

Ledger of 2026-11-16 13:19 UTC.

| AD | best G (then GD) | status | best GD (then G) | status |
|---|---|---|---|---|
| 7 | **32/7/103/29** | new (night, conjpull) | 32/7/109/23 | known |
| 6 | 32/6/104/31 | known | 31/6/124/19 | known |
| 5 | 32/5/104/29 | known | 32/5/127/15 | known |
| 4 | **32/4/111/25** | new (P5) | **28/4/174/14** | new (P2) |
| 3 | none at A <= 32 | | | |

- New, not a T05 class: **32/7/104/27** [V] (agent P4: lam 236 conjugate of the 103, gate and
  trb stages, then a deepened mix stage; 5 levels shallower than the reference for one more gate).
- Exact negatives, agent P4 (`strategies/P4/NOTES.md` section 2,
  `~/xs-campaigns/2026-11-15-targets/P4/NEGATIVES.md` N1-N16). **Case S** = the 103's 9 level-1
  ANDs and 18 output ANDs with the same operand functions, an inversion block with inputs
  t30..t33 (or any 4-input basis of their span) and the 103's 9 output forms, x-signals injected
  from the top layer. In case S [C]: top + pre-inversion >= 33 XOR at any GD, the inversion block
  >= 13 XOR (no 17-gate block for any 4-input basis), the bottom exactly 25 XOR (transposition
  principle), so **G >= 103 and the 103 is optimal in case S**; also no 102 over all 19,683
  per-pair operand choices, all complement patterns, and the 2,040 scaled-Frobenius variants of
  the skeleton; and no 103 at GD < 32 in case S (exactly 6 inversion blocks of 18 gates exist;
  with the earliest pre-inversion arrivals and the optimal bottom the best is GD 32). Not
  covered: inversion blocks reading more than 4 linear inputs, other GF(2^4) / GF(2^2)
  representations (other rank-9 decompositions of x^17), non-tower layouts.
- Exact negatives, agent P5 (`strategies/P5/NOTES.md`), exact skeleton search for the 5-AND
  GF(2^4) inversion middle (`invskel.py`, C port `invskel.c`): [C] no 5-AND middle of AND depth
  2 computes GF(2^4) inversion (any linear input/output basis), so an A32 AD4 circuit cannot use
  the 9 + 5 + 18 tower layout with a separate inversion block; with the 103's top and bottom a
  103-gate circuit at AD6 or AD5 does not exist (depth 4 and depth 3, paid model, max cost 20:
  0 skeletons); with any inversion-input basis delivered by the pre layer the middle costs >= 19,
  so G >= 104 at AD5 and AD6 **in case S** [C, caveats in P5 NOTES]; AD3 is impossible in the
  separated tower layout [C, that layout].
- Empirical [H]: 21 GF(2^8) conjugates of the 103 and of the AD5 104/29 with kernel lineages
  (about 5 CPU-h) settle at 104; AD4 lineages from NIST 117 conjugates plateau at 111/25 and
  112/22 (two independent certified paths, about 2.5 CPU-h).

Ledger of 2026-11-16 13:19 UTC: 2,617 verified files within the hard limits, 1,711 distinct structures, 886 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 32/7/103/29 | strict | +0 / -3 | new (night, conjpull) | none | [aes-sbox-a32-ad7-g103-gd29-T05-night-T05-1.circ.txt](T05/aes-sbox-a32-ad7-g103-gd29-T05-night-T05-1.circ.txt) |
| 32/7/104/26 | other | +1 / -6 | new (night, conjpull) | none | [aes-sbox-a32-ad7-g104-gd26-T05-night-T05-1.circ.txt](T05/aes-sbox-a32-ad7-g104-gd26-T05-night-T05-1.circ.txt) |
| 32/5/105/24 | tradeoff:and_depth_for_gates | +2 / -8 | new (night, conjpull) | none | [aes-sbox-a32-ad5-g105-gd24-T05-night-T05-1.circ.txt](T05/aes-sbox-a32-ad5-g105-gd24-T05-night-T05-1.circ.txt) |
| 32/5/106/21 | tradeoff:and_depth_for_gates | +3 / -11 | new (night, conjpull) | none | [aes-sbox-a32-ad5-g106-gd21-T05-night-T05-1.circ.txt](T05/aes-sbox-a32-ad5-g106-gd21-T05-night-T05-1.circ.txt) |
| 32/5/108/20 | tradeoff:and_depth_for_gates | +5 / -12 | known; reproduced in the night (T05 block) | none | [aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt](../aes/aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt) |
| 32/5/110/19 | tradeoff:and_depth_for_gates | +7 / -13 | new (night, conjpull) | none | [aes-sbox-a32-ad5-g110-gd19-T05-night-T05-1.circ.txt](T05/aes-sbox-a32-ad5-g110-gd19-T05-night-T05-1.circ.txt) |
| 32/5/111/18 | tradeoff:and_depth_for_gates | +8 / -14 | new (night, conjpull) | none | [aes-sbox-a32-ad5-g111-gd18-T05-night-T05-1.circ.txt](T05/aes-sbox-a32-ad5-g111-gd18-T05-night-T05-1.circ.txt) |
| 32/5/115/17 | tradeoff:and_depth_for_gates | +12 / -15 | known; reproduced in the night (T05 block) | none | [aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt](../aes/aes-nist-hub-pull-g115-a32-gd17-ad5.circ.txt) |
| 32/4/119/16 | tradeoff:and_depth_for_gates | +16 / -16 | new (night, conjpull) | none | [aes-sbox-a32-ad4-g119-gd16-T05-night-T04-1.circ.txt](T05/aes-sbox-a32-ad4-g119-gd16-T05-night-T04-1.circ.txt) |
| 32/4/125/15 | tradeoff:and_depth_for_gates | +22 / -17 | known | none | [aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt](../aes/aes-nist-E-polish-g125-a32-gd15-ad4.circ.txt) |
| 28/4/174/14 | tradeoff:and_depth_for_gates | +71 / -18 | new (P2); reproduced in the night (T02 block) | none | [aes-sbox-a28-ad4-g174-gd14-T05-P2-1.circ.txt](T05/aes-sbox-a28-ad4-g174-gd14-T05-P2-1.circ.txt) |

Pinned (G, GD) frontier within the same limits: 28/4/176/14, 32/4/117/19, 32/4/127/15, 32/5/104/30, 32/5/105/26, 32/5/107/22, 32/5/109/20, 32/5/122/16, 32/5/127/15, 32/7/103/32.

### T06: 34/4/139/13 (`aes-sbox-a34-ad4-g139-gd13-xx105-22`)

Hard limits A <= 34, AD <= 4. Primary GD < 13 with G <= 139; secondary G < 139 at GD <= 13.
Depth is the main objective. No tradeoffs.

- Best strict on 2026-11-15: 34/4/134/13, **known** (a hub join of 2026-11-14). After the night (ledger 2026-11-16 13:19 UTC): strict frontier 34/4/134/13 [V] (known); new frontier points of class `other` tonight: 34/4/122/14.
- New but dominated by the 134: 34/4/135/13 (x2), 136/13 (x2), 137/13 (x2) [V], from bottom
  resynthesis (agent P2: rank-1 decompositions of the bottom tensor, built on the 134's front,
  then `trb` at the caps).
- GD 12 [C, these objects]: every A <= 34 AD4 circuit in the archive has skeleton depth bound
  >= 13; no image of the 14 known rank-1 bottoms under the 30,600 exact symmetries of the tensor
  meets the depth-12 Kraft budget on the 134, NIST 139 or 48@11 fronts; among the 2,040
  conjugates of the 134 only the identity keeps bound 13 (`strategies/P2/NOTES.md` sections 1, 2,
  6). A restricted CP-SAT model ("one product per alpha class per output") gave at best 26 bottom
  products at D 12 (A 42), an upper bound in that model only [H].

Ledger of 2026-11-16 13:19 UTC: 1,172 verified files within the hard limits, 843 distinct structures, 383 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 33/4/105/25 | other | -34 / +12 | known | none; equal tuple aes-sbox-a33-ad4-g105-gd25-xx72-6 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -33 / +9 | known | none; equal tuple aes-sbox-a33-ad4-g106-gd22-xx73-5 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -32 / +7 | known | none | [aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt](../aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt) |
| 33/4/108/19 | other | -31 / +6 | known | none | [aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt](../aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt) |
| 33/4/110/18 | other | -29 / +5 | known | none | [aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt](../aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt) |
| 33/4/112/16 | other | -27 / +3 | known | none | [aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt](../aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt) |
| 33/4/115/15 | other | -24 / +2 | known | none | [aes-nist-E-join-g115-a33-gd15-ad4.circ.txt](../aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt) |
| 34/4/122/14 | other | -17 / +1 | new (night, conjpull) | none | [aes-sbox-a34-ad4-g122-gd14-T06-night-T06-1.circ.txt](T06/aes-sbox-a34-ad4-g122-gd14-T06-night-T06-1.circ.txt) |
| 34/4/134/13 | strict | -5 / +0 | known | none | [aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt](../aes/aes-nist-hub-join-g134-a34-gd13-ad4.circ.txt) |

Pinned (G, GD) frontier within the same limits: 33/4/105/25, 33/4/106/22, 33/4/108/20, 33/4/116/15, 33/4/125/14, 34/4/139/13.

### T07: 35/3/139/27 (`aes-sbox-a35-ad3-g139-gd27-xx104-38`)

Hard limits A <= 35, AD <= 3 (AND depth 3 is optimal and preserved). Primary G < 139 at
GD <= 27; also substantial gains at GD <= 29.

- Best strict on 2026-11-15: **35/3/138/24** [V] (primary met; the first A <= 35 AD3 circuit below 139 gates
  on the pin) and 35/3/139/23. New, agent P6. After the night (ledger 2026-11-16 13:19 UTC): strict frontier **35/3/138/23** [V] (new, night conjpull), **35/3/139/21** [V] (new, night conjpull); new tonight: 35/3/138/23 (conjpull, block T07 (pass 1), from 35/3/138/24, stage k27, 07:05 UTC), 35/3/139/21 (conjpull, block p2-T07 (pass 2), from 35/3/139/22, stage k23, 12:09 UTC); new frontier points of class `other` tonight: 35/3/165/13.
- Best tradeoff on 2026-11-15: none. 35/3/137/28 [V] (the lowest G of any A <= 35 AD3 circuit we have) saves 2
  gates at +1 level: below the threshold of 3, so a frontier point only. 35/3/140/22 is a new
  frontier point too. After the night (ledger 2026-11-16 13:19 UTC): best tradeoff: none.
- Method (`strategies/P6/NOTES.md` sections 12, 13): P3's conjugation pipeline on the AD3
  starts. Screen of all 2,040 conjugates of best-1400 `aes-sbox-a35-ad3-g140-gd25` (`conj3.py`),
  the 12 best non-identity ones built (`mkconj.py`), kernel at cap GD 31 (200 s) then cap GD 27
  (2 x 200 s), `repair_keep 1`: lam 250, k 4 gave 152@26 -> 140@27 -> **139@23**; a kernel stage
  of 240 s at cap 27, seed 20378, from the 139@23 gave **138@24** (seed 17446 at cap 25 gave
  138@24 again). The sidecar's `method` field names P6's pull pipeline; the `command` field (a
  `kern.py` stage from the 139@23) is the correct one. <!-- DOCS-TODO: sidecar method label -->
- 137@28: lam 189 conjugate of our 139@25 (152@34), kernel at cap 31.
- Failed [H]: T3's GF(4)-coordinate loop at caps 27/29 (nothing new in 5 steps); G-first kernel
  from the low-GD AD3 families (153@24, 148@22: far from 139); 10 conjugates of 140@25 and NIST
  139@27 with 300 s each before the screen was used (141-151).

Ledger of 2026-11-16 13:19 UTC: 339 verified files within the hard limits, 251 distinct structures, 113 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 35/3/137/28 | other | -2 / +1 | new (P6) | none | [aes-sbox-a35-ad3-g137-gd28-T07-P6-1.circ.txt](T07/aes-sbox-a35-ad3-g137-gd28-T07-P6-1.circ.txt) |
| 35/3/138/23 | strict | -1 / -4 | new (night, conjpull) | none | [aes-sbox-a35-ad3-g138-gd23-T07-night-T07-1.circ.txt](T07/aes-sbox-a35-ad3-g138-gd23-T07-night-T07-1.circ.txt) |
| 35/3/139/21 | strict | +0 / -6 | new (night, conjpull) | none | [aes-sbox-a35-ad3-g139-gd21-T07-night-T07-1.circ.txt](T07/aes-sbox-a35-ad3-g139-gd21-T07-night-T07-1.circ.txt) |
| 35/3/141/19 | other | +2 / -8 | known | none | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g141-gd19-xx106-46.circ.txt` |
| 35/3/143/18 | other | +4 / -9 | known | none | [aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt](../aes/aes-nist-study-T3-t3-g143-a35-gd18-ad3.circ.txt) |
| 35/3/144/17 | other | +5 / -10 | known | none | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g144-gd17-xx109-43.circ.txt` |
| 35/3/147/16 | other | +8 / -11 | known | none | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g147-gd16-xx112-56.circ.txt` |
| 35/3/155/15 | other | +16 / -12 | known | none | `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt` |
| 35/3/162/14 | other | +23 / -13 | known | none | [aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt](../aes/aes-nist-F-trb-g162-a35-gd14-ad3.circ.txt) |
| 35/3/165/13 | other | +26 / -14 | new (M3) | none | [aes-sbox-a35-ad3-g165-gd13-T07-M3-1.circ.txt](T07/aes-sbox-a35-ad3-g165-gd13-T07-M3-1.circ.txt) |
| 35/3/181/12 | other | +42 / -15 | new (P6); reproduced by M3 | none | [aes-sbox-a35-ad3-g181-gd12-T07-P6-1.circ.txt](T07/aes-sbox-a35-ad3-g181-gd12-T07-P6-1.circ.txt) |

Pinned (G, GD) frontier within the same limits: 35/3/139/27, 35/3/141/25, 35/3/147/20, 35/3/157/15, 35/3/172/14, 35/3/183/13.

### T08: 35/3/183/13 (`aes-sbox-a35-ad3-g183-gd13-xx148-29`)

Hard limits A <= 35, AD <= 3. Primary GD <= 12, preferably with G <= 183; secondary G much lower
at GD <= 13. Never sacrifice AND depth 3.

- Best strict on 2026-11-15: **35/3/181/12** [V] (primary met; "published best G at A <= 35, GD <= 12: none"
  in aes_check, so the first AD3 circuit at GD 12 on the pin) and **35/3/168/13** [V] (15 gates
  below the reference at its depth; the archive had 177@13). New, agent P6.
  After the night (ledger 2026-11-16 13:19 UTC): strict frontier **35/3/165/13** [V] (new, M3), **35/3/181/12** [V] (new, P6; reproduced by M3); new frontier points of class `other` tonight: 35/3/138/23, 35/3/139/21.
- Method (`strategies/P6/NOTES.md` sections 1-3, 7, 8, 11, 12): **level-3 GF(4) re-basing**
  ([HOW-IT-WORKS.md, "Re-basing the level-3 GF(4) classes"](../../HOW-IT-WORKS.md#re-basing-the-level-3-gf4-classes-and-depth-3)). The depth anatomy showed why
  183@13 and 177@13 sit at 13: two output rows of weight 6 and one product at level 11 [C,
  Huffman/Kraft for fixed products]. Re-basing the three level-3 product classes lowers the
  skeleton bound of both to 12 [C, `botbasis.py`, that case]. A depth-feasible hybrid build at
  cap 12 plus the kernel plateaued at 187@12 from those parents [H]. The decisive step was a
  one-point GF(4)-coordinate variant of 177@13 whose best re-basing has slack (max Kraft 0.75 at
  cap 12; 8 of 765 variants, `l3scan.py` [C, botbasis case]): hybrid build 204@12, then a kernel
  stage of 240 s at caps A35 AD3 GD12 gave 181@12 (3 of 8 kernel seeds from that exact build
  reach 181, none lower [H]). Relaxing GD12 circuits at cap 13 and re-basing moves at cap 13 then
  gave the GD13 chain 177 -> 175 -> 172 -> 171 -> 170 -> 169 -> **168**.
- Conjugation is not a route to GD 12 here [C, skeleton Huffman case]: for all 2,040 conjugates
  of 181@12 the sum of skeleton arrivals of the level-1/2 ANDs grows by >= 12 levels.
- Not found: anything below 181 at GD 12 in about 45 kernel stages from different builds [H].

Same frontier as T07 (same hard limits; ledger of 2026-11-16 13:19 UTC); here **35/3/165/13** (-18 / +0), **35/3/181/12** (-2 / -1) are **strict**, every other point is `other`. Pinned frontier as T07.

### T09: 45/4/141/12 (`aes-sbox-a45-ad4-g141-gd12-xx96-25`)

Hard limits A <= 45, AD <= 4. Primary G < 141 at GD <= 12; equally GD <= 11 at G <= 141.

- Best strict on 2026-11-15: **41/4/136/12** [V] (5 gates and 4 ANDs below the reference); the fewest ANDs
  among the strict points is **39/4/138/12** [V]. Both new, agent P7; aes_check: the published
  best G at GD <= 12 is 141. After the night (ledger 2026-11-16 13:19 UTC): strict frontier **38/4/135/12** [V] (new, night bottom); new tonight: 38/4/135/12 (bottom, block T09 (pass 1), from 39/4/138/12, stage build, 09:46 UTC); new frontier points of class `other` tonight: 37/4/127/13.
- Best tradeoff on 2026-11-15: none. GD 11 at A <= 45 exists only as T4's rank-2 junk-sharing circuits
  (44/4/254/11 and others, G >= 186); no GD 11 point with G <= 149 was found.
  After the night (ledger 2026-11-16 13:19 UTC): best tradeoff: none.
- Method (`strategies/P7/NOTES.md` sections 2, 3): **shared-bottom rebuild** ([HOW-IT-WORKS.md, "Shared-bottom rebuild"](../../HOW-IT-WORKS.md#shared-bottom-rebuild-high-a-low-depth)). Keep the front of NIST 45@12 (its 17 ANDs and
  their cone), write each output as a sum of rank-1 products AND(Y_alpha, w) and anneal over
  per-output decompositions that share products between outputs, with an exact per-output depth
  check (`bopt.py`); build the bottom (`bbuild.py`: Y-sums, x-forms by a Boyar-Peralta distance
  heuristic, products, shared pairs, Huffman output trees; verified on 256 inputs); then polish
  with the gate kernel at cap A = the build's A. 39/4/138/12: a build with 22 bottom products and
  no kernel. 41/4/136/12: loop LE, seed 9005, gate polish 300 s at caps GD 12, AD 4, A 41 of a
  bopt build. Some builds use the 48@11 hub circuit's front as a donor (donor ruling, section 2;
  those sidecars carry `donor_outside_limits`).
- [C] Minimal 4-product decompositions of different outputs can share products only for the
  GF(16)-proportional output pair (y5, y6); the reference shares more because some outputs use 5
  products. GD 11 [C in the tower model]: with base Y-forms at gate level 8 every GD-11 output
  needs 4 base-Y products at level 9, so 32 products (A >= 48).

Ledger of 2026-11-16 13:19 UTC: 2,445 verified files within the hard limits, 1,854 distinct structures, 924 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 33/4/105/25 | other | -36 / +13 | known | none; equal tuple aes-sbox-a33-ad4-g105-gd25-xx72-6 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -35 / +10 | known | none; equal tuple aes-sbox-a33-ad4-g106-gd22-xx73-5 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -34 / +8 | known | none | [aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt](../aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt) |
| 33/4/108/19 | other | -33 / +7 | known | none | [aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt](../aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt) |
| 33/4/110/18 | other | -31 / +6 | known | none | [aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt](../aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt) |
| 33/4/112/16 | other | -29 / +4 | known | none | [aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt](../aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt) |
| 33/4/115/15 | other | -26 / +3 | known | none | [aes-nist-E-join-g115-a33-gd15-ad4.circ.txt](../aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt) |
| 37/4/121/14 | other | -20 / +2 | known | none | [aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt](../aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt) |
| 37/4/127/13 | other | -14 / +1 | new (night, conjpull) | none | [aes-sbox-a37-ad4-g127-gd13-T09-night-T09-1.circ.txt](T09/aes-sbox-a37-ad4-g127-gd13-T09-night-T09-1.circ.txt) |
| 38/4/135/12 | strict | -6 / +0 | new (night, bottom) | none | [aes-sbox-a38-ad4-g135-gd12-T09-night-T09-1.circ.txt](T09/aes-sbox-a38-ad4-g135-gd12-T09-night-T09-1.circ.txt) |
| 44/4/254/11 | other | +113 / -1 | known | none | [aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt](../aes/aes-nist-study-T4-t4-g254-a44-gd11-ad4.circ.txt) |

Pinned (G, GD) frontier within the same limits: 33/4/105/25, 33/4/106/22, 33/4/108/20, 33/4/116/15, 33/4/125/14, 35/4/133/13, 45/4/141/12.
Strict points of the (A, AD, G, GD) frontier in [LEDGER.md](LEDGER.md) (fewer ANDs count first): **38/4/135/12** (new, night bottom).

### T10: 59/4/159/10 (`aes-sbox-a59-ad4-g159-gd10-xxn100-30-3`)

Hard limits A <= 59, AD <= 4. Primary G < 159 at GD <= 10; ambitious GD <= 9, preferably at
G <= 159. GD 10 is the best listed depth, not a proven bound.

- Best strict on 2026-11-15: none. Best tradeoff on 2026-11-15: none. After the night (ledger 2026-11-16 13:19 UTC): best strict: none; best tradeoff: none; new frontier points of class `other` tonight: 37/4/127/13, 38/4/135/12.
- Why G is pinned in the 59@10 architecture (`strategies/P7/NOTES.md` section 4), each [C] in its
  model: stage 1 (all Kraft-feasible level-4 decompositions of the four N-coordinates into
  products of <= 2-variable affine operands: 33 / 1 / 2 / 3 per coordinate; all 198 combinations
  built, best 159); the top layer (51 distinct targets); the bottom at GD 10 with Y-forms at level
  7 (4 base-Y products per output, 32 products and 24 output XORs forced; over all 840 Y-bases
  the bottom needs 25-32 new x-forms, the circuit's own basis 26). Conjugation gives nothing new
  (N(lam x^(2^k)) = N(lam) N(x)^(2^k), so the span of the N-coordinates is the same for every
  conjugate). Open lever, not built: another N-coordinate system with all four at level 4
  ({1,3,4,8}, {1,2,4,14}, ...) needs a redesigned inversion, paid from the AND budget.
- GD 9 [H, partly C]: in this architecture bottom products are at gate level >= 8 and a rank-4
  output needs 4 of them, so GD >= 10 there.
- Failed [H]: kernel mix from the 59@10 for 13 min (relaxed states 154-157 at GD 11, never
  repaired below 159 at GD 10); kernel on the 4-input inversion sub-problem (no move from 22
  gates); SAT exact synthesis of the inversion (did not find even the known 22-gate solution in
  10-15 min).

Ledger of 2026-11-16 13:19 UTC: 2,578 verified files within the hard limits, 1,959 distinct structures, 1005 distinct tuples.

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file |
|---|---|---|---|---|---|
| 33/4/105/25 | other | -54 / +15 | known | none; equal tuple aes-sbox-a33-ad4-g105-gd25-xx72-6 | `~/xs-campaigns/2026-11-14-hub/long/archive/0f491596c734.bfx` |
| 33/4/106/22 | other | -53 / +12 | known | none; equal tuple aes-sbox-a33-ad4-g106-gd22-xx73-5 | `~/xs-campaigns/2026-11-14-hub/long/archive/26070040d746.bfx` |
| 33/4/107/20 | other | -52 / +10 | known | none | [aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt](../aes/aes-nist-hub-pull-g107-a33-gd20-ad4.circ.txt) |
| 33/4/108/19 | other | -51 / +9 | known | none | [aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt](../aes/aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt) |
| 33/4/110/18 | other | -49 / +8 | known | none | [aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt](../aes/aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt) |
| 33/4/112/16 | other | -47 / +6 | known | none | [aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt](../aes/aes-nist-hub-join-g112-a33-gd16-ad4.circ.txt) |
| 33/4/115/15 | other | -44 / +5 | known | none | [aes-nist-E-join-g115-a33-gd15-ad4.circ.txt](../aes/aes-nist-E-join-g115-a33-gd15-ad4.circ.txt) |
| 37/4/121/14 | other | -38 / +4 | known | none | [aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt](../aes/aes-nist-D-kernel-g121-a37-gd14-ad4.circ.txt) |
| 37/4/127/13 | other | -32 / +3 | new (night, conjpull) | none | [aes-sbox-a37-ad4-g127-gd13-T10-night-T09-1.circ.txt](T10/aes-sbox-a37-ad4-g127-gd13-T10-night-T09-1.circ.txt) |
| 38/4/135/12 | other | -24 / +2 | new (night, bottom) | none | [aes-sbox-a38-ad4-g135-gd12-T10-night-T09-1.circ.txt](T10/aes-sbox-a38-ad4-g135-gd12-T10-night-T09-1.circ.txt) |
| 49/4/148/11 | other | -11 / +1 | known | none; equal tuple aes-sbox-a49-ad4-g148-gd11-xx99-23 | [aes-nist-cost_gd-gd11-ad4-a49-g148-a49-gd11-ad4.circ.txt](../aes/aes-nist-cost_gd-gd11-ad4-a49-g148-a49-gd11-ad4.circ.txt) |
| 59/4/159/10 | other | +0 / +0 | known | none; equal tuple (the reference) | `~/xs-campaigns/2026-11-14-hub/long/archive/0ab3e1c5b961.bfx` |

Pinned (G, GD) frontier within the same limits: 33/4/105/25, 33/4/106/22, 33/4/108/20, 33/4/116/15, 33/4/125/14, 35/4/133/13, 45/4/141/12, 49/4/148/11, 59/4/159/10.

## 5. Failed experiments and dead ends

Runs that found nothing, or less than their start. Logs are under
`~/xs-campaigns/2026-11-15-targets/<agent>/runs/`; details in each agent's `NOTES.md`.

| when (UTC, 11-15) | agent, target | what was tried | what happened |
|---|---|---|---|
| 15:30-15:57 | P1, T01 | kernel workers over 166 legal starts | 4 jobs: archive tuples only |
| 15:39-17:00 | P1, T03 | skeleton re-synthesis + kernel (`skres`), own timing-driven Paar (`p1synth`) | 131-132 @20; cancellation-free pair merging is ~75 linear gates worse than kernel-optimised layers [H] |
| 16:20-16:43 | P1, T01/T03 | SAT LNS v1 | every UNSAT answer void: pysat's totalizer reused the pool's variable numbers; fixed in v2 |
| 16:02-22:30 | P1, T01/T03 | p1run v3 operator mix (pswap, skres, deep, pullD, osc, trb, join, skel, polish), ~60 jobs, 3 CPU-h | archive tuples only |
| 17:54-18:56 | P1, T01/T03 | 9 GF(2^8) conjugate pipelines incl. screened lams | 5-9 gates above the archive at every GD; the identity is the best basis of every A28 start by 4 proxy gates [H] |
| 15:30-16:02 | P3, T04 | plain trb at cap 19; qflip walk to rank 16; annealing of quadratic bottoms | 117@19 plateau; no rank 16 in 600k steps; no build below 120 |
| 15:35-17:00 | P3, P2 | generic SAT for tensor rank / full Brent equations | no answer in 2-18 min |
| 18:16-19:10 | P3, T04 | repair_keep re-derivations from the conjugate starts | 115@21, 118@19: not reproduced on that path (reproduced later from P5's starts) |
| 17:57-21:36 | P4, T05 | 13 conjugates of the 103, 8 of the AD5 104, kernel lineages, ~5 CPU-h | floor 104 [H] |
| 15:46-17:10 | P4/P5, T05 | own truth-table SAT encodings of the inversion block | no 13-step sanity in 300 s; replaced by the exact skeleton search |
| 15:50 | P5, T05 | first inversion cost model | ignored levels (optimistic leaf costs); fixed, run repeated |
| 17:57-22:52 | P5, T05 | AD5 lineages from NIST 104/30, 104/29 | drift upward (105-107); AD5 104 looks tight for the kernel [H] |
| 15:25-15:42 | P6, T07 | T3's GF(4)-coordinate loop at caps 27/29 | 141@26 / 140@25 only |
| 16:21-16:44 | P6, T07 | G-first kernel from the low-GD AD3 families | 153@24, 148@22 |
| 16:03-19:33 | P6, T08 | oscillation loop at caps 12/13; GD12 pulls from Kraft-1.0 parents and from the NIST 183 family | plateau 187-188; 184-190 |
| 15:23-15:40 | P7, T09/T10 | kernel mix from 59@10 and 43@12; polish of 44@11 at GD 12 | no change; 254 -> 194 |
| 18:30-20:40 | P7, T09 | bopt --refine2, randomised builds, long annealing | no new point; long SA worse than 30k-iteration seeds |
| 17:00-23:40 | P2, T02/T06 | skeleton pull (relax, rebuild, kernel); conjugate pipelines; bopt on the 134 front | 181-194 (T02), no bound-13 rebuild (T06), own bottom a local optimum (cost 65) |
| 16:07-16:52 | Z1, Z | gen13 with all 16 gammas at once | OOM-killed at the 4 GB cap |

Night of 2026-11-16 (runner blocks; `~/xs-campaigns/2026-11-16-night/`, events in `runner.events.log` and `runner2.events.log`):

| when (UTC, 11-16) | block, target | what was tried | what happened |
|---|---|---|---|
| 03:34-04:48 | T03 (pass 1) | conjpull 73, satlns 16 jobs | early-stopped after 74 of 120 min (no new point for 40 min) |
| 04:48-05:33 | T01 (pass 1) | conjpull 72 jobs | early-stopped after 45 of 60 min (no new point for 45 min); no frontier point beyond the known front (18 files written, all inside the known front) |
| 05:33-06:27 | T06 (pass 1) | conjpull 120 jobs | early-stopped after 54 of 60 min (no new point for 40 min) |
| 06:27-06:42 | T10 (pass 1) | conjpull 40 jobs | no frontier point beyond the known front (4 files written, all inside the known front) |
| 06:42-07:45 | T07 (pass 1) | conjpull 200 jobs | early-stopped after 64 of 110 min (no new point for 40 min) |
| 07:45-08:52 | T04 (pass 1) | conjpull 72, satlns 16 jobs | early-stopped after 67 of 75 min (no new point for 40 min) |
| 08:52-09:22 | T08 (pass 1) | rebase 60 jobs | early-stopped after 30 of 70 min (no new point for 30 min); no frontier point beyond the known front (8 files written, all inside the known front); job ends: no result.json 20 |
| 10:08-10:38 | T02 (pass 1) | conjpull 46 jobs | no frontier point beyond the known front (11 files written, all inside the known front) |
| 10:38-11:09 | p2-T05 (pass 2) | conjpull 40 jobs | early-stopped after 30 of 55 min (no new point for 30 min); no frontier point beyond the known front, no file written |
| 12:15-12:47 | p2-T06 (pass 2) | conjpull 58 jobs | no frontier point beyond the known front (5 files written, all inside the known front) |
| 12:47-13:15 | p2-T04 (pass 2) | conjpull 58, satlns 8 jobs | no frontier point beyond the known front, no file written; no file from conjpull (58 jobs), satlns (8 jobs) |
| 13:15-13:19 | p2-T03 (pass 2) |  jobs | no frontier point beyond the known front, no file written |
| 08:46 | T04 (pass 1) | runner drop rule | DROP start for op 4 conjpull-a32-ad4-g113-gd20-4ddf8b05f2.circ.txt (satlns.pool.n_pooled = 25 < 30) |
| 09:22 | T08, T09 (pass 1) | runner drop rule | DROP start for op 0 rebase-a35-ad3-g165-gd13-c1848d8fa7.circ.txt (3 instant failures) |
| 09:22 | T08, T09 (pass 1) | runner drop rule | DROP start for op 0 rebase-a35-ad3-g189-gd12-e6d3f5de5b.circ.txt (3 instant failures) |

Jobs that the runner ended at a block end (status `timeout` or `stopped` in their `result.json`) are not listed as failures; their files are kept. "no result.json" = launched seconds before a stall stop and ended before it wrote `result.json` (the runner then counted them as instant failures, hence the drop lines). Each "nothing" above is [H]: one night, these starts and seeds; none is a bound.

## 6. Verification

- Every circuit file in every campaign `found/` folder and in the archive is checked by
  `campaigns/targets/ledger.py run` with `campaigns/aes_check.py`'s `check()`: `core` and the
  independent verifier on all 256 inputs, metrics equal in both, gates in {AND, XOR, XNOR, NOT},
  NIST counting ([../../VERIFICATION.md](../../VERIFICATION.md) section 7). Ledger of 23:17 UTC:
  4,560 files verified OK, 0 failing. Morning ledger (2026-11-16 13:19 UTC, code d9507dd): 4,162 archive and 614 campaign files (11-15 agents, phase-2 agents and the night's `found/` folders), 4,776 verified, 0 failing; issues 0 FAIL, 2 WARN, 3 NOTE.
- Every saved circuit also carries its own `aes_check` OK line in its sidecar, written by the
  agent when it was saved.
- The pinned set: 207 manifest files, all sha256 equal to `nonlinear/nist/MANIFEST.json`
  (checked on every ledger run). The comparison set is every forward AES S-box circuit of the pin.
- The ledger's sidecar audit (LEDGER.md "Sidecar / verification issues"): at 23:17 UTC 0 FAIL,
  2 WARN (two P3 sidecars without `elapsed_s`) and 3 NOTEs (P3 circuits certified by trace
  replay). Morning ledger (2026-11-16 13:19 UTC): 0 FAIL, 2 WARN, 3 NOTE; WARN: P3 `p3-rkH1-s1-mix23-k1-a32-ad4-g112-gd22-b8095ec160.circ.txt`: sidecar missing fields: elapsed_s; P3 `p3-rkN1-s2-mix16-k2-a32-ad4-g120-gd16-331d7b06d7.circ.txt`: sidecar missing fields: elapsed_s.
- Curated copies: `python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/*/*.circ.txt`.
  At the morning curation (2026-11-16 13:23 UTC), `verify_all.py` section `targets` (the same `aes_check` on every `results/targets/*/*.circ.txt`): 57 files, 57 OK, 0 failing.

## 7. Compute and hardware

One laptop for every run: Intel Core i7-13700H (6 performance cores with 2 threads, 8 efficiency
cores: 20 hardware threads), Windows 11 with WSL2 (Ubuntu 24.04), one single-threaded process
per CPU, every job through the memory guard `~/xs-campaigns/guard/xsrun` / `xsfg`. The machine
table and the clock caveat are those of XORFlux
([../../../../circuits/SEARCH-TIME.md](../../../../circuits/SEARCH-TIME.md)): under load the WSL2
clock runs fast and is stepped back; units with a 705-minute timeout ended about 30 minutes late
(`strategies/Z1/NOTES.md` section 5). CPUs 12-19 are probably efficiency cores, so time-budgeted
jobs on them did fewer iterations.

Phase 1 (2026-11-15 15:22-23:45 UTC), CPUs per agent (BRIEF.md; CPU-hours were not measured):

| agent | targets | CPUs | wall time |
|---|---|---|---|
| P1 | T01, T03 | 10, 11, + 0 from ~17:00 | 15:22-22:30 |
| P2 | T02, T06 | 12, 13, + 15 lent 21:35-23:45 | 15:22-23:40 |
| P3 | T04 | 14, + 3 | 15:30-22:59 |
| P4 | T05 (G record) | 15, + 7, 8 | 15:30-21:35 |
| P5 | T05 (AND depth) | 16, + 9 | 15:30-22:52 |
| P6 | T07, T08 | 17, 2, + 7, 8 from 21:40 | 15:25-23:14 |
| P7 | T09, T10 | 18, 19 | 15:23-23:20 |
| Z1 | 27 ANDs | 1, + 4, 5, 6 | 15:30-23:16 |
| L0 | ledger, verification | short jobs on 1 | |

Phase 2 (2026-11-16 00:00-13:30 UTC): one target at a time on all 20 CPUs.
Runner blocks (from the event logs; one job per CPU):

| pass | block | target | state | planned min | start | end | wall min | CPUs | CPU-h (CPUs x wall) | job CPU-h (sum of job wall times) | jobs launched | files written |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | T05 | T05 | done | 90 | 02:04 | 03:34 | 90 | 20 | 30.0 | 29.6 | 121 | 64 |
| 1 | T03 | T03 | early-stopped | 120 | 03:34 | 04:48 | 74 | 20 | 24.5 | 24.3 | 89 | 30 |
| 1 | T01 | T01 | early-stopped | 60 | 04:48 | 05:33 | 45 | 20 | 15.1 | 14.9 | 72 | 18 |
| 1 | T06 | T06 | early-stopped | 60 | 05:33 | 06:27 | 54 | 20 | 17.9 | 17.7 | 120 | 6 |
| 1 | T10 | T10 | done | 15 | 06:27 | 06:42 | 15 | 20 | 5.0 | 4.4 | 40 | 4 |
| 1 | T07 | T07 | early-stopped | 110 | 06:42 | 07:45 | 64 | 20 | 21.2 | 20.9 | 200 | 14 |
| 1 | T04 | T04 | early-stopped | 75 | 07:45 | 08:52 | 67 | 20 | 22.3 | 22.1 | 88 | 24 |
| 1 | T08 | T08 | early-stopped | 70 | 08:52 | 09:22 | 30 | 20 | 10.1 | 9.7 | 60 | 8 |
| 1 | T09 | T09 | done | 45 | 09:22 | 10:08 | 45 | 20 | 15.0 | 14.7 | 76 | 16 |
| 1 | T02 | T02 | done | 30 | 10:08 | 10:38 | 30 | 20 | 10.1 | 9.7 | 46 | 11 |
| 2 | p2-T05 | T05 | early-stopped | 55 | 10:38 | 11:09 | 30 | 20 | 10.1 | 10.0 | 40 | 0 |
| 2 | p2-T07 | T07 | done | 42 | 11:09 | 12:15 | 67 | 20 | 22.2 | 21.5 | 260 | 6 |
| 2 | p2-T06 | T06 | done | 32 | 12:15 | 12:47 | 32 | 20 | 10.7 | 10.2 | 58 | 5 |
| 2 | p2-T04 | T04 | done | 28 | 12:47 | 13:15 | 28 | 20 | 9.4 | 8.8 | 66 | 0 |
| 2 | p2-T03 | T03 | done | 15 | 13:15 | 13:19 | 3 | 20 | 1.0 | 0.0 | 0 | 0 |

Pass 1 (`plan.json`): 171.2 CPU-h by the 20-CPU blocks, 168.1 CPU-h of job wall time; pass 2 (`plan2.json`): 53.4 and 50.5. Times are the WSL2 clock (section above); job CPU-h counts finished jobs only (jobs stopped at a block end report no wall time).

Files and frontier points per operator:

| pass | block | jobs per operator | files per operator | frontier points beyond the known front (STATUS) |
|---|---|---|---|---|
| 1 | T05 | conjpull 121 | conjpull 64 | 32/7/103/29 (strict), 32/7/104/26 (other), 32/5/105/24 (tradeoff:and_depth_for_gates), 32/5/106/21 (tradeoff:and_depth_for_gates) |
| 1 | T03 | conjpull 73, satlns 16 | conjpull 28, satlns 2 | 28/5/125/24 (other) |
| 1 | T01 | conjpull 72 | conjpull 18 | - |
| 1 | T06 | conjpull 120 | conjpull 6 | 34/4/122/14 (other), 34/4/123/14 (other), 34/4/124/14 (other) |
| 1 | T10 | conjpull 40 | conjpull 4 | - |
| 1 | T07 | conjpull 200 | conjpull 14 | 35/3/138/23 (strict) |
| 1 | T04 | conjpull 72, satlns 16 | conjpull 23, satlns 1 | 32/4/119/16 (other) |
| 1 | T08 | rebase 60 | rebase 8 | - |
| 1 | T09 | bottom 48, conjpull 28 | conjpull 3, bottom 13 | 37/4/127/13 (other), 37/4/128/13 (other), 39/4/135/12 (strict), 38/4/135/12 (strict) |
| 1 | T02 | conjpull 46 | conjpull 11 | - |
| 2 | p2-T05 | conjpull 40 | none | - |
| 2 | p2-T07 | conjpull 260 | conjpull 6 | 35/3/139/21 (strict), 35/3/139/22 (strict), 35/3/140/21 (other) |
| 2 | p2-T06 | conjpull 58 | conjpull 5 | - |
| 2 | p2-T04 | conjpull 58, satlns 8 | none | - |
| 2 | p2-T03 |  | none | - |

## 8. Reproduction

Vocabulary as in [../../VERIFICATION.md](../../VERIFICATION.md) section 6.

- **One-off** (time-budgeted; verified, not bit-reproducible): every kernel stage of every
  agent, so every new strict and tradeoff result above. Their `command`, `seed`, start file and
  sha256, code version (git sha + kernel binary sha256) are in the sidecar and in
  `Txx/logs/<name>/REPRODUCE.md`.
- **Reproduced as a tuple** by an independent path: 113/20 and 114/19 (T04; P3 rkG1, rkH1 from
  P5's certified starts), 111/25 (T05; P5 lin-cert113 and lin-certB from two NIST 117 lineages),
  181@12 (T08; 3 of 8 kernel seeds from the same build).
- **Exact replays**: P3's `pdrive_replay.py` re-ran four kernel stages with unlimited stage time
  so that the iteration-bounded stages replay exactly; the results were gate-identical to the
  saved 115@20, 116@19 and 114@19 (L1, L2, L4) and to 113@21 (L3, stage 2).
- **Deterministic constructions**: P6's coordinate variant (`l3scan.py`) and the 204@12 hybrid
  build behind 181@12 (rebuilt byte for byte on 2026-11-15 20:24 with `hybrid.SLACK3 = False`,
  `strategies/P6/NOTES.md` "Reproduction of the T08 results"); P7's builds from a recorded plan
  (`bbuild.py`); P1's SAT LNS answers are deterministic per query but the walk is time-limited.
- The start files of most campaign results live in `~/xs-campaigns/2026-11-15-targets/`, outside
  the repository. <!-- DOCS-TODO: copy start files into logs/ -->

## 9. The 27-AND objective (Z)

No verified circuit with A <= 27 exists in any scanned folder. Agent Z1 (15:30-23:16 UTC;
`strategies/Z1/NOTES.md`) worked on the output staircase and on exact constructions. What it
showed, each in its stated model and nothing beyond it:

- [P] For circuits whose last layer is a *sink layer* (no last-layer AND feeds another) over a
  common core E, the staircase (m_k = fewest ANDs whose span holds k independent output
  components) is m_k = |E| + d_k, where d_k are the generalized Hamming weights of the [K, 8]
  code of the layer's output-usage matrix. So waste = K - d_1 - 7 and A = |E| + K: for such
  circuits the staircase is not an independent lever, and a "waste <= 4" filter is just
  K <= d_1 + 11. [C] All 111 staircase files and the hub archive up to A30 have a sink last
  layer and a common core; none has m_1 < 16 or waste < 4.
- [P, three-stage model with X3's projection] d_1 >= 2, so m_1 >= 16 there; X1b's first
  component (16) is optimal in that model, and a 27 in that model is exactly a 13-product layer
  over a 9 + 5 prefix.
- [C, `spaneq.py`] Under the field maps x -> c x^(2^i), the stage-1 spans of X1b's 9 + 5 + 14
  circuits are images of the AD4 9-spans of NIST g131, g141 and g176: one span class S9; every
  NIST AD5 10-span contains an image of S9. **So X1b's 9 + 5 + 14 family is H2's AD4-span
  9 | 5 | 14 family up to a field symmetry**, not an independent family, and every exact result
  over one member of a class holds for the whole class.
- [C, each in its model] No covering 13-member GF(4)-norm layer over the S9 prefixes with their
  5-AND middle (all 16 gammas; also all 120 two-gamma mixtures); no 12-member layer over S9 with
  the AD4 6-AND middle (all 16 gammas); no semi-member layer in the 108,375-product pool for the
  cases run (gamma representatives); no single AND replaces the parallel last-layer pair in any
  of 150 A28 spans (operands from stage 1 and the middle), nor in NIST g124 and g128 with
  operands anywhere in the span of x and all 26 kept ANDs (2^33 each, ~12.5 CPU-h).

None of these is a lower bound on the AND count of the AES S-box. At 23:50 UTC the user stopped
all 27-AND work until further notice.
