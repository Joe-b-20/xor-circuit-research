# How we got to XORFlux v8

XORFlux v8 is the current state of work that began on 2026-06-15 with one matrix, forward AES
MixColumns (the 32×32 GF(2) matrix of one column), and only reached other maps in late July.
This page tells that path: what each stage tried, what failed and with what numbers, and which
decisions the failures led to. The search is still being developed; v8 is not the last version.

**Sources.** Unmarked claims can be checked in this repository (mostly the evidence reports
kept with v5 and v6 in [versions/](versions/)) or in the two public repositories named below.
Claims marked † come from development notes that are not part of this repository.

## Contents

- [Version numbers](#version-numbers)
- [Timeline](#timeline)
- [Before v1 (June to October 2026)](#before-v1-june-to-october-2026)
- [Versions](#versions) (v1–v8, the ones kept in this repository)
- [Failed experiments and dead ends](#failed-experiments-and-dead-ends)
- [Decisions that shaped v8](#decisions-that-shaped-v8)
- [Constructors and the generality rule](#constructors-and-the-generality-rule)
- [Compute](#compute)

## Version numbers

Version numbers in this repository (v1–v8) are not those of the two earlier public
repositories, the MixColumns records
([aes-mixcolumns-xor-circuits](https://github.com/Joe-b-20/aes-mixcolumns-xor-circuits),
v1.0.0–v4.0.1, July to October 2026) and the July method
([slp-plateau-search](https://github.com/Joe-b-20/slp-plateau-search), v1.0.0–v3.1.0), nor of
the standalone MixColumns searches aes_search 2.0.0 (this repository's v1) and 3.0.0 (found
nothing, not kept).

## Timeline

| Dates (2026) | Stage | Maps | Best new results | Kept here as |
|---|---|---|---|---|
| Jun 15–26 | NumPy Boyar–Peralta and six alternatives | MixColumns (SKINNY to calibrate) | 97 gates, no depth limit | — |
| Jun 27 – Jul 11 | circuit studio, compiled local search, language-model agents writing circuits | MixColumns | 91@6, 90@11, 89@10 (Jul 7–8) †; 98@3 † | — |
| Jul 9–17 | the agents' method turned into a program (value-set search) | MixColumns | 97@3, 92@4, 89@5, 89@6, the first records found without an agent | — |
| Jul 18–25 | first multi-matrix optimizer | S-box layers, Joltik, small-scale AES, PRINCE, InvMixColumns | S-box bottom 28@5, Joltik 46@3–44@5, InvMixColumns 89@30 † | — |
| Jul 26 – Aug 11 | campaign "87": merged fast engine, fleets | MixColumns | 88@7, 88@6, 88@5 (Jul 30), 91@4 (Jul 31); no 87 | — |
| Aug 12–18 | rented CPU pods: SAT windows, exact sub-block pricing | MixColumns | lower bound L ≥ 56 only | — |
| Aug 18 – Sep 1 | experiments e1–e17, agent fleets, block SAT | MixColumns | none; an 87 inside one block structure is UNSAT † | — |
| Sep 8–10, Sep 26 | InvMixColumns pipeline, representation search | InvMixColumns | 88@33 (walk only), a 179@5…91@14 staircase; 88@19 by relabelling forward 88s | — |
| Sep 10 – Oct 17 | lower bounds and other views | MixColumns | L ≥ 75; depth-3 bound 93 ([lower-bound-proofs/](../lower-bound-proofs/README.md)) | proofs |
| Oct 20–22 | aes_search v2.0.0 | MixColumns | 89@4 (Oct 21) | **v1** |
| Oct 22–23 | aes_search v3.0.0 | MixColumns | nothing (475 CPU-h) | — |
| Oct 24–28 | multi-engine search framework | S-box bottom, FOX MU4/MU8, Joltik, InvMixColumns | FOX MU4 128@7, FOX MU8 538@9 | **v2–v4** |
| Oct 28–30 | one chain per worker (xorsearch, renamed XORFlux) | 6 maps, then all 59 | see [circuits/](../circuits/README.md) | **v5–v8** |

## Before v1 (June to October 2026)

None of this work has a version number in this repository, and most of its code is not
included. It matters because almost every part of v8 was first tried, and often first failed,
here.

**June: greedy synthesis hits a wall.** A NumPy Boyar–Peralta implementation matched the
published 97-gate MixColumns circuit (Kranz et al. 2017) on 2026-06-15 and was checked against
a FIPS-197 oracle. Six independent attempts to go further (tie-break variants, restarts,
superoptimisation of the 97, orbit-aware and symmetric restarts) all stopped at 97 or worse,
and thirteen more plans on Jun 25–26 (window resynthesis, grafting, plateau beams, compensated
pairs, about 34 h for the last) produced no strict improvement †. Conclusion at the time: 97
was the floor of greedy distance-based synthesis.

**Late June to July 11: agents, then the first 91, 90 and 89.** A circuit studio with a
TypeScript search engine, CP-SAT on sub-blocks (tractable only up to dimension 10–11) and
compiled local-search tools ran beside language-model agents that edited circuits under an
oracle check †. A 16-worker fleet ran about 42 h (≈670 core-h) and found nothing below 91 in
483,088 circuits †. A 91@6 came on Jul 7, then 90@11 and 89@10 by LNS warm-started from
Yuan et al.'s 91 and from that 90 †. The 89 turned out not to be new: Sun, Yang and Li had
already published 89@9 (IACR ePrint 2025/1493) †. These circuits were published from Jul 10
in the records repository.

**July 9–17: from agents to a program.** An analysis of what the agents actually did found
that their main move was cancellation plus reuse (33 of the 89 gates cancel) †. That became a
standard-library Python search over **value sets** (the set of XOR values a circuit computes):
a plateau walk that removes a value and repairs exactly, LNS, a depth ladder, and `anneal3`, a
depth-3 constructor. It found 97@3, 92@4, 89@6 and 89@5, the first records found without an
agent, and a Pareto rule ("fewer gates, or equal gates at lower depth") that rescued the 89@5
and 92@4. Published as [slp-plateau-search](https://github.com/Joe-b-20/slp-plateau-search)
v1.0.0. A random-matrix transfer test of the agent method stopped at the Paar baseline †.

**July 18–25: the first multi-matrix optimizer.** A matrix registry and a self-tuning bandit
brought the AES S-box linear layers (top 23@7, bottom 28@5), Joltik (46@3, 45@4, 44@5),
small-scale AES, PRINCE/Midori and InvMixColumns (89@30) †. Hub moves were dropped after no
success in about 2.24 million samples.

**July 26 to August 11: the 88s.** A merged engine, 17.5× faster on LNS and 21.9× on walk,
alternated walk and LNS in chunks, restarted from fresh constructor roots on stall, and kept
novelty archives. It found 88@7 (Jul 26), 88@6 (Jul 28), a clean 88@5 from a naive root
(Jul 30, 3,844 s after the root) and 91@4 (Jul 31). Then a two-week hunt for 87 (NRPA,
FunSearch-style program evolution, waves of fleets on all 20 threads) found none; one wave
alone used about 3,500 core-h †. Naive roots reached 88 in 11 of 90 trials against 6 of 90 for
"cancellation" roots, which ended that hypothesis †.

**August 12 to September 1: proving instead of searching.** A week on rented CPU pods (about
32 cores each; no GPUs) ran SAT window sweeps and exact sub-block pricing over a corpus of
837,419 distinct 88-gate circuits; the only result was the lower bound L ≥ 56 †. Back on the
laptop, experiments e1–e17 and twelve agent fleets found no 87, and an exhaustive SAT check of
one block structure (about 229 core-h) proved none exists there †. August as a whole used
roughly 8,000–9,300 core-hours †.

**September: the inverse matrix.** The MixColumns pipeline, retargeted to InvMixColumns, gave
the cleanest controlled experiment of the project: from the same 106@21 start, 6 workers for
about 20 h, walk-only reached 88@33, alternating walk/LNS reached 90@23 and 89@16, and LNS-only
stalled at 96. A clean-room Boyar–Peralta produced nothing for this matrix (its distance
metric decides ≤ 6 while the rows weigh 11–19). On Sep 26, 2,394 forward 88s were shown to be
InvMixColumns 88s too after relabelling, giving 88@19 without any search.

**September 10 to October 17: bounds.** Proof attempts reached a rigorous 49 and no further
(Sep 18–19) †; the bounds 63, 69 and then 75 came on Sep 22–23 with language-model assistance,
and the depth-3 bound 93 on Oct 17. Both proofs are in
[lower-bound-proofs/](../lower-bound-proofs/README.md), with their caveats (no human peer
review). A learned-policy pilot on the laptop GPU (Oct 8–12) reached 115 and 111 gates, against
102–103 for cheap search without learning †.

## Versions

Only versions that found at least one circuit in [circuits/](../circuits/README.md#circuits)
are kept. When two versions reached the same gates and depth, the newer one is credited; a
circuit later shrunk by v8's polish stays credited to the version that found it.

| Version | What | Ran | Code | Circuits |
|---|---|---|---|---:|
| v1 | MixColumns-only pipeline (aes_search 2.0.0) | 2026-10-21/22 | [versions/v1-mixcolumns-pipeline](versions/v1-mixcolumns-pipeline/) | 0 (kept: its 89@4 came first) |
| v2 | multi-engine search framework | 2026-10-24/27 | [versions/v2-search-framework](versions/v2-search-framework/) | 1 |
| v3 | the same framework, depth-focused campaign | 2026-10-27/28 | [versions/v3-search-framework](versions/v3-search-framework/) | 2 |
| v4 | the same framework, InvMixColumns campaign | 2026-10-28 | [versions/v4-search-framework](versions/v4-search-framework/) | 0 (kept: its 168@5 was our first depth-5 InvMixColumns) |
| v5 | first `xorsearch`: one chain per worker | 2026-10-28 | [versions/v5-xorsearch](versions/v5-xorsearch/) | 1 |
| v6 | `xorsearch` as run on 2026-10-29 | 2026-10-29 | [versions/v6-xorsearch](versions/v6-xorsearch/) | 16 |
| v7 | v6 plus depth slack 1, repair exit, seed repair, remove-one dead skip | 2026-10-29/30 | [versions/v7-xorsearch](versions/v7-xorsearch/) | 10 |
| v8 | current: v7 plus the own-depth polish of new points below the search cap; renamed XORFlux | 2026-10-30 | [xorflux/](xorflux/) | 171 |
| v9 prototype | v8 plus adopt-on-improve, archive sampling past the record cap, a log-only watcher | 2026-10-31/11-02 | [diff against v8](../circuits/aes-invmixcolumns/logs/aes-invmixcolumns-xor118-depth5/v9-prototype.diff) | 1 |

**v1 (Oct 20–22): a better MixColumns pipeline.** aes_search 2.0.0 kept the July engine and
added deadline-aware reconstruction, coordinated translations, joint triple/quartet cores and
remove-1/add-2 expansion, on 20 workers split by depth. Its run found 90@4 at 11.3 h and 89@4
at about 14.5 h, then nothing for 11 h. The 89@4 grew from the July 91@4 lineage, so it is not
a from-scratch result. On 2026-10-31 v8, seeded with the same July 91@4, found an 89@4 in 15
minutes with a dossier that replays the move; that circuit replaced v1's in circuits/. Its successor, aes_search 3.0.0 (physical merges, invertible interfaces,
pair-bank depth-3 search, proof-guided LNS), ran 475 CPU-h and found **no** improvement; 80% of
its exact calls returned unknown.

**v2–v4 (Oct 24–28): many engines, one worker.** Each worker rotated round-robin through 14–17
engines (the July engine, Boyar–Peralta, the aes_search v2 and v3 kernels, constructors), each
with its own private trajectory, sharing by adoption. Over 1,871 CPU-h it removed 2 gates on
FOX MU4, 1 on Joltik and 2 on FOX MU8, and nothing elsewhere. The evidence report
([v5 docs](versions/v5-xorsearch/xorsearch/docs/evidence/evidence-framework-runs.md)) found why:
10 of 17 engines never improved anything yet took 52.7% of the CPU; 59% of engine slots
trailed the worker's best by 5 or more gates; forced adoption collapsed FOX MU8 onto 4 DAGs
while 90 existed; a capped Joltik worker sat at 44@5 for 75 h.

**v5 (Oct 28): one chain per worker.** v5 replaced all engines with one chain per worker that
every move edits, on an incremental value-set kernel 300× faster on walk (0.4 → 119 it/s on
FOX MU8), with an adaptive scheduler, burst/plateau/repair phases, restarts, pull-only sharing
and a dossier for every improvement. In 9-minute head-to-heads it found fewer gates than the
framework on all four maps tried (FOX MU4 125@7 vs 130@10, Joltik 42@9 vs 44@5, FOX MU8 536@11
vs 540@12, InvMixColumns 94@11 vs 107@6). Its first campaigns
(6 maps × 20 workers, about 110 CPU-h) exposed nine defects, listed in
[campaigns-2026-10-28.md](versions/v6-xorsearch/docs/evidence/campaigns-2026-10-28.md): a
scheduler floor that gave slow structural moves 66% of the CPU, a soft depth slack that trapped
capped chains half the time, deep valid circuits never recorded, 9 restarts in 240 worker-h, no
pool pulls, chains drifting to depth 28–36.

**v6 (Oct 29): the nine fixes.** A soft-slack ramp and repair revert, restarts after a 900 s
stall, pull-on-stall sharing, recording of points at their own depth, tightness-weighted
rewards, and native moves instead of the vendored v3 kernels. Its 1–2 h reruns found
MixColumns 97@3 at 7.5 s and 88@5 at 1,024 s, but not 89@4 (best 90@4), plus 16 kept
circuits on InvMixColumns, the S-box bottom layer, FOX and Joltik.

**v7 (Oct 29–30): slack 1 and a repair exit.** Depth slack 2 → 1, leaving repair after 5
failed tries, repairing seeds that exceed the cap, skipping dead removal victims. Restarts on
expired repairs fell from 304 to 30. MixColumns 97@3 (built by `anneal3`, see
[below](#constructors-and-the-generality-rule)) and 88@5 within 1 h; 89@4 still missed.

**v8 (Oct 30): own-depth polish.** Records below the search cap had sometimes kept gates that
could go at their own depth (5 of 32 kept circuits lost 1–2 gates), because the chain judges
removals at its deeper search cap. v8 adds an exact branch and bound (`engine/polish.py`) at
no measurable speed cost, and was run on all 53 NIST linear maps. Renamed XORFlux with no code
change; the logs of its runs still say `xorsearch`.

**v9 prototype (Oct 31 – Nov 2): adopt-on-improve.** A proposal to restart workers from the
circuits farthest from their seeds was dropped before it ran: distance favours worse
circuits, and workers started from the same circuit already ended 0.81–0.86 apart. What was
tested instead, as an A/B run of 10 workers per side from the same code (the control side
with the changes off, so v8's search), is adopt-on-improve: every worker restarts from a
strictly better verified circuit of its group as soon as one is pooled. On InvMixColumns at
depth 5, from our 168@5, the adopt side reached 120@5 in 4.1 h and 118@5 at 42.3 h, below
NIST's 119@5; the control side reached 121@5. On MixColumns at depth 4 the control side kept
the July 91@4 line and found 89@4 in 15 minutes, while the adopt side moved all its workers
to NIST's 90@4 in the first seconds and stayed there. It is not part of `xorflux/`.

## Failed experiments and dead ends

| When (2026) | What was tried | What happened |
|---|---|---|
| Jun 15 | generic evolution islands | stuck at 152 (Paar-seeded: 108) † |
| Jun 15–16 | six ways past 97 (BP tie-breaks, restarts, superoptimisation, orbit and symmetric BP, "creativity injection") | 97–116; 97 was the floor of all six |
| Jun 25–26 | 13 plans: resynthesis, grafts, plateau beams, compensated pairs | 0 strict improvements; compensated pairs about 34 h † |
| Jul 1–4 | 16-worker TypeScript fleet | ≈42 h, 483,088 circuits, none below 91 † |
| Jul 7–8 | remove-2/add-1 search; 8 agents minimising the 91 | 0 found; the agents could not cut a gate † |
| Jul 9 | the agent method on a random 16-bit matrix | stopped at the Paar baseline † |
| Jul 14 | continuous global reseeding of a depth cascade | depths 5–11 collapsed onto one 91@5 for 2.7 h |
| Jul 21–24 | hub moves | 0 successes in ≈2.24 M samples; removed |
| Jul 27–30 | exhaustive k ≤ 3/4 neighbourhoods of 88s; SAT at depth caps | all empty; an improving window needs a median of 42 values |
| Jul 30 | "depth 4 is closed for our methods" (1,244 UNSAT windows) | wrong: 91@4 a day later, 89@4 in October |
| Jul–Aug | a shared pool / cross-pollination | 3,651 merges, 1.07 M masks, no record |
| Jul–Aug | repulsion, MAP-Elites, island migration | 54k new 88s in one family; 0 new families |
| Aug 4–11 | NRPA, FunSearch-style evolution, "cancellation roots" | no 87; naive roots beat cancellation roots 11/90 vs 6/90 † |
| Aug 12–18 | rented CPU pods | 837,419 distinct 88s, only the bound L ≥ 56 † |
| Aug 18 – Sep 1 | e1–e17, 12 agent fleets, block SAT | all negative; one block structure proven to have no 87 † |
| Sep 8 | clean-room Boyar–Peralta on InvMixColumns | no circuit at all |
| Sep 8–9 | LNS without walk; lifting circuits to a depth cap | LNS stalled at 96; lifting reached 178@5 in ≈19 h |
| Oct 8–12 | learned search policy (GPU) | 115/111 vs 102–103 without learning † |
| Oct 21–22 | structured moves in aes_search v2 | 31% of its CPU, no attributable record |
| Oct 22–23 | aes_search v3.0.0 | 475 CPU-h, 0 improvements, 80% unknown exact calls |
| Oct 24–28 | 17-engine framework | 10 engines never improved anything: 986 of 1,871 CPU-h |
| Oct 24–28 | private trajectories per engine | 59% of slots ≥ 5 gates behind the best; engines inherited a constructor's 1,151 gates |
| Oct 24–28 | sharing by forced adoption | the adopter beat the adopted point 9 of 69 times; FOX MU8 on 4 of 90 DAGs |
| Oct 24–28 | hard depth caps | capped Joltik stuck 75 h; depth-first Joltik 117 CPU-h, 0 improvements |
| Oct 28 | v5 defaults | the nine defects above |
| Oct 28 | the v3 structural moves inside xorsearch | ≤ 0.11× average yield per CPU; removed |
| Oct 29 | MixColumns 89@4 at cap 4 | not found in 1–2 h by v6–v8 (best 90@4) |
| Oct 29 | a depth-4 annealer modelled on the 89@4 | not adopted: shaped around one target |

## Decisions that shaped v8

| Decision | Evidence | Since |
|---|---|---|
| Value-set state; remove-and-repair walk as the main move | walk made every 88 and the 91@4; 736 walk vs 22 LNS improvements in the July–August archive | July; v5 |
| Pareto depth tie-break | 89@5 and 92@4 would have been discarded without it | Jul 14 |
| LNS with deadline-aware rebuild as the second move | v2 LNS and walk made 17 of 29 framework improvements from 13.6% of CPU | July; v5 |
| Restart stalled chains from fresh randomized roots | 7 of 58 naive roots reached 88; every from-scratch record came from a fresh root | Jul 30 |
| An incremental kernel | walk 0.4 → 119 it/s on FOX MU8 | v5 |
| One trajectory per worker, every move acts on it | private trajectories trailed the best (59% of slots) | v5 |
| A burst of local moves after every new best | 15 of 29 improvements came within 374 iterations of a fresh start | v5 |
| Nothing from outside resets a running chain | all 6 long plateau breaks came from chains 2.5–24 h old | v5 |
| Pull-only sharing of distinct verified circuits, at restarts | forced sharing collapsed diversity twice (July, October) | v5–v6 |
| Soft depth cap, then depth repair before recording | 129@7 → 128@10 → 128@7 in 0.14 h; but slack 2 trapped capped chains | v5–v7 |
| Scheduler charged in CPU seconds, rewards weighted by closeness to goals | dead engines took 52.7% of CPU; a proposal-count floor gave slow moves 66% | v5–v6 |
| A dossier for every improvement, re-verification by worker and coordinator | the 89@4 of v1 could not be attributed or replayed | v5 |
| Own-depth polish | 5 of 32 kept circuits lost 1–2 gates the chain could not see | v8 |
| No target-shaped constructors | a method must transfer to maps it was not built for | Oct 29 |

## Constructors and the generality rule

Since 2026-10-29 the rule is that the search may only use mechanisms that transfer to linear
maps it was not designed for. A depth-4 annealer modelled on the MixColumns 89@4 was not
adopted for that reason. The depth-3 partition annealer `anneal3`, written in July for MixColumns at depth 3,
is still in v8 (`moves/depth3.py`, as a move at depth cap 3 and as a restart root), but it is
not a general mechanism. Three kept circuits are its direct output with no search move after it (MixColumns
97@3, ARIA 416@3, Joltik 46@3), and two were found by the search from its output
(jpst17-4x4-gf256-inv 94@3 and 84@4); they are marked in [circuits/](../circuits/README.md).

## Compute

Compute of the runs behind the kept circuits, with exact and estimated times for each circuit,
is in [circuits/SEARCH-TIME.md](../circuits/SEARCH-TIME.md). For the whole project:

| Stage | Machine | Compute |
|---|---|---|
| June–July | laptop (below) | single runs up to ≈34 h; ≈670 core-h of agent-era fleets †; 133 CPU-h July ladder |
| Jul 26 – Aug 11 | laptop | ≈216 CPU-h logged for the 88 fleets; one wave ≈3,500 core-h † |
| Aug 12–18 | rented CPU pods, 32 cores each | one week † |
| August total | laptop and pods | ≈8,000–9,300 core-h † |
| Sep 1 | laptop | ≈229 core-h SAT † |
| Oct 21–23 | laptop | 548–796 worker-h (v1), 475 CPU-h (aes_search v3) |
| Oct 24–28 | laptop | 1,871 worker-h (v2–v4) |
| Oct 28–30 | laptop | ≈630 worker-h (v5–v8), half of it in runs that kept no circuit |

The laptop is an Intel Core i7-13700H (14 cores, 20 hardware threads, 64 GB) under WSL2. Its
GPU (RTX 4060 Laptop) was used only for the learned-policy pilot.


## About `versions/`

`versions/` holds each older version's code exactly as it ran, for provenance; those versions
are not maintained and may expect the layout of the repository they ran in. Local paths and
the machine's hostname were replaced in their run state and documents (see
[NOTICE](../NOTICE)).
