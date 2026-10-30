# Evidence: the 2026-10-28 xorsearch campaigns

Six campaigns, 20 workers each, all on the first version of xorsearch (one frozen source digest),
about 110 CPU-hours in total. Every record was re-verified with the old verifiers
(`search/target.py`, `tools/circuit.py`). This file summarises what the logs showed and which code
changes followed. The analysis scripts and per-run tables are listed at the end.

| target | start | time | frontier reached | records going in |
|---|---|---|---|---|
| aes_sbox_bottom | NIST | 1 h | 28@5, 29@4 | 28@5, 29@4 |
| fox_mu4 | NIST | 1 h | **122@6, 121@9** | 125@7, 124@12 |
| joltik | NIST | 1 h | **44@4, 43@6**, 42@9 | 44@5, 43@8, 42@9 |
| fox_mu8 | NIST | 1 h | **520@9, 519@11** (plus 519@10 held, never recorded) | 538@9, 537@10, 536@11 |
| invmixcolumns | NIST | 2 h | 96@8, 95@9, **93@11, 91@12, 90@13**, 89@16, 88@20 (plus 92@11 held, never recorded) | 95@9, 91@14, 89@16, 88@19 |
| mixcolumns | random roots | 2 h | 98@3, 97@4, 89@5, 88@6 | 97@3, 89@4, 88@5 |

## Weighting improvements by how hard they were

Not every improvement is worth the same: on MixColumns, 92 -> 91 at depth 5 is easy and 89 -> 88 is
not. Let gap = gates - G*(depth), where G*(depth) is the best known gate count at that depth or
shallower. The time a worker stayed at a worker-best level before improving grew by about x2.3 per
gate of gap, then flattened:

| gap | 1 | 2 | 3 | 4 | 5-11 |
|---|---|---|---|---|---|
| mean time to the next improvement | 4,393 s | 1,616 s | 827 s | 272 s | 80-200 s |

So the weight is max(2.3^-gap, 0.035). The engine's scheduler now uses it on best-type rewards
(`scheduler.reference` holds the campaign's goal points). The move ranking was the same under this
weighting, under 2^-gap and unweighted.

## What found improvements, per CPU

These are fleet totals. The ratio is the weighted share of improvements divided by the CPU share,
so 1.0 is average.

| move | CPU | worker bests | steps on record lineages | ratio |
|---|---|---|---|---|
| walk.remove1 | 12.4% | 610 | 116 | 3.2 |
| lns.rebuild | 11.2% | 380 | 96 | 3.6 |
| depth.repair | 1.7% | 147 | 38 | 5.6 |
| walk.expand | 2.5% | 54 | 13 | 0.86 |
| structural.translate | 13.7% | 44 | 12 | 0.17 |
| structural.cores | 13.3% | 44 | 11 | 0.16 |
| structural.backward | 13.1% | 4 | 2 | <= 0.11 |
| structural.component | 13.0% | 2 | 0 | <= 0.11 |
| structural.interface | 12.9% | 1 | 1 | <= 0.11 |
| walk.window | 3.4% | 17 | 4 | 0.03 |
| walk.hub | 0.6% | 1 | 0 | 0 |
| depth3.anneal | 2.1% (MixColumns only) | 9 | 3 | - |

"Steps on record lineages" counts each step on the parent chain of the 21 final frontier points:
296 steps, 250 of them remove1, LNS or depth.repair.

Within the moves:
- **walk.remove1**: the repair path is 6.6% of CPU and carries 40% of the weight. Victims with no
  repair are 54-77% of calls and zero yield.
- **lns.rebuild**: greedy-only proposals are 5.5% of CPU for 37% of the weight. Any proposal that
  ran the deadline beam is 5.4% for 2.8%. A big destroy followed by the beam cost 47 ms for almost
  nothing. Peel was in 43% of LNS improvements. kshake made about 4,900 proposals and no
  improvements.
- **depth.repair**: successful rebuilds are 0.4% of CPU for 10% of the weight.

## What went wrong, and the fix for each

1. **The scheduler's floor counted proposals, not time.** Five 30-40 ms structural moves were held
   at the 2% floor each and took 66% of the fleet's CPU, next to a 0.8 ms walk.
   Fix: weights and the floor are cost shares (`engine/scheduler.py`). Removed: component,
   interface, hub. Then also backward and window. Translate and cores are at about 2% of time
   and run no burst.
2. **Soft depth slack trapped capped chains.** The key is (gates, depth) and the search cap is
   the cap + 2, so a cap-3 MixColumns chain fell into the 88-90@5 basin within a minute. After
   that, every 97-99@3 proposal was rejected as uphill. Capped workers spent 50.5% of their
   CPU-weighted time on an infeasible chain best that beat their worker best, and 77% of
   MixColumns capped time came after the worker's last feasible improvement. Fixes:
   - `objective.hard_cap_margin`: slack is 0 at or just above the minimum depth and grows by one
     per level (`core/objective.py`).
   - A new feasible worker best is always accepted, and it re-anchors an infeasible chain best
     (`engine/loop.py`).
   - A repair that runs out of budget reverts to the worker best (`phase.repair_revert`). In the
     logs, 134 of 403 repairs used the whole 20,000-proposal budget and failed.
3. **Valid circuits deeper than the cap were never recorded.** Checkpoints held a fox_mu8 519@10
   (better than any record) and an InvMixColumns 92@11; several other points were held 200-1,300 s
   before anyone recorded them. Fix: frontier points are recorded at their own depth
   (`engine/loop.py`, `campaign/records.py`); the worker best stays feasible.
4. **Restarts nearly never fired.** There were 9 restarts in 240 worker-hours. An infeasible chain
   best counted as the incumbent, which tripled the stall allowance to 6,000 s and exempted the
   chain from the root budget. The improvement rate after a loose point fell from 21/h (1-5 min)
   to 0 after 30 min. Fixes:
   - The incumbent must be feasible.
   - Stall timer 900 s, x2 for incumbents; root budget 3,600 s.
5. **Sharing could never help capped workers.** There were 0 pulls with 65 distinct 88 DAGs
   pooled, because the pool filtered by the real cap. Fix: pulls are allowed up to the search cap,
   and a pulled over-cap elite starts in repair.
6. **Free chains drifted deep.** An InvMixColumns 88@20 chain spent 90% of 100 minutes at depth
   28-36 and made no depth tie-break; record-level tie-breaks came from within one level of the
   best. Fix: `engine.depth_window` = 2.
7. **The depth-3 annealer was switched off by its own chain.** With the chain at depth 5, it
   annealed a stale partition and proposed its uphill final states (0.1% accepted, 3.2 CPU-h).
   The v1 code reached 97@3 in 38-337 s per core with a 150k anneal followed by an
   iterated-local-search tail; the anneal alone ends near 100. Fix: `depth3.anneal` runs v1's
   seed loop (anneal, ILS, fresh seed) on a private partition and proposes only partitions
   smaller than the chain. The root builder runs one period plus 300 ILS rounds.
8. **A constructed root was never recorded.** One cap-3 worker ended 2 h with no best while
   holding a 101@3 root. Fix: a constructed initial root is reported as the chain's first
   discovery.
9. **Scheduler memory and phases.**
   - Credit decayed per proposal (half-life 30-75 s), so tight improvements 1,000-4,000 s apart
     were forgotten. The half-life is now 900 s of chain time.
   - Credit learned on the plateau also reshaped the repair phase, diluting depth.repair to 17-59%.
     The repair phase is no longer adaptive.

## First checks after the fixes

MixColumns from random roots:

| | baseline (20 workers, 2 h) | 4 cap-3 workers, 6 min | 12 workers, 15 min |
|---|---|---|---|
| 97@3 | never (98@3 at 34 s, then nothing) | all 4 workers; first at 12 s | at 12.5 s |
| 89@5 | 1,077 s | - | 340 s |
| 88@6 | 3,461 s | - | 304 s |
| best at depth 4 | 97@4 | - | 93@4 |

## Sources

All of these are outputs of the analysis, kept outside this repository (not included):
- `agents/mech/` (engine mechanics, weighting, lost circuits)
- `agents/mcdeep/` (the MixColumns and InvMixColumns deep dive, with experiments)
- `agents/old97/` (the v1 annealer, reproduced and ablated)
- `agents/prof/` (profiles, coverage, speed patches)
- `analysis.json` / `summary.txt` (per-move tallies and lineages)

Run directories: `~/xs-campaigns/2026-10-28/runs/<target>/`.
