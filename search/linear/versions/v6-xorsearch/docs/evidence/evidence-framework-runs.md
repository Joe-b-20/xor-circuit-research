# Evidence from generic-framework campaign runs

Scope: `three-targets20` (20 workers, 75.25 h monotonic), `joltik-depth-foxmu8-15` (15 workers, 23.38 h) and `invmixcolumns-13` (13 workers, 1.52 h). That is 1,871 CPU-hours and 30-second chunks, with 14 to 17 engines per worker in strict round-robin. I checked the round-robin: the engine recorded in every event equals `engines[chunk % n]`, with 0 mismatches. The validation runs lasted 8 to 11 s each and are excluded; their frontiers only repeat the seeds or worse points.

Event classes are recomputed per worker with that worker's objective key: **(a)** strict improvement of the worker best, **(b)** a new nondominated point that does not improve the objective, **(c)** a new DAG at an existing point. Engine-made events and adoption imports are counted separately. Time is chunk index × measured seconds per chunk (30.07 s). UTC timestamps were not used because they drift: the three-targets20 UTC span is 69.9 h against 75.25 h monotonic.

**Critical confound.** None of the three campaign source snapshots contain incumbent resync. `grep incumbent` finds no use in `runs/*/source/search/worker.py` or in `run_chunk`. Each engine kept its own private trajectory. A new or reset engine started from `worker.current_gates`, which is whatever the previously scheduled engine left behind, often a constructor's output. The only synchronization was adoption, which reset all engine states. Zero rates for some engines are therefore partly caused by this.

## Ranked recommendations

1. **Centre every move on the incumbent or a small elite pool, and never chain one engine's trajectory into another's.**
   - At the end of the runs, an engine's own best was at least 5 gates worse than its worker's best in 177 of 298 (worker, engine) slots in three-targets20 (59%). The figures were 105 of 225 (47%) in joltik-depth-foxmu8 and 128 of 182 (70%) in invmixcolumns.
   - Examples: invmixcolumns-00 legacy-paar, bp, inverse-bp, walk and lns all sat 224 to 276 gates above the worker best after inheriting a 394-gate constructor output. In fox_mu8, 5 to 13 of the 14 engines per worker ended 56 to 99 gates above.
   - Fresh starts on a new best pay off at once: 15 of 29 engine improvements were "fresh" starts at iteration ≤374. Examples: legacy-lns 130/8→129/8 at iteration 1, legacy-window at iteration 5, and v2-cores 539/10→538/10 at iteration 30. Each came immediately after adopting a circuit whose own owner's engines had not found that step.
   - 21 of 29 improvements (72%) came at most 1 h after a (re)start on a new circuit.

2. **Default portfolio = v2-lns, v2-walk, v2-translate and legacy-lns as the core; legacy-walk, legacy-window and v2-cores at low weight.**
   - These 7 engines produced 29 of 29 strict improvements. v2-lns (9) and v2-walk (8) together produced 59% of them from 13.6% of CPU.
   - Measured rates per 100 CPU-h: v2-lns 7.1, v2-walk 6.3, v2-translate 3.2, legacy-lns 2.4, legacy-walk 1.6, legacy-window 1.6, v2-cores 0.8.
   - The other 10 engines produced 0 strict improvements and used 986 of 1,871 CPU-h (52.7%).

3. **Remove or gate the dead engines.**
   - legacy-bp and inverse-bp produced 0 records of any class in 254 CPU-h, at ≤0.01 proposals per iteration.
   - v3-interface produced 1 frontier point in 127 CPU-h.
   - v3-component made 0.00 proposals per iteration on AES and Joltik while spinning through 27k to 38k iterations per chunk.
   - legacy-window made ≈0 proposals per iteration except in 2 lucky chunks.
   - Constructors (balanced, Paar) never improved anything. Their "frontier" points had a median excess of +69 gates on fox_mu4 and +595 on fox_mu8. Only 1 survived in a final frontier (fox_mu8 1116/5, which is trivial).
   - Use constructors only for the initial seed, never as scheduled moves.

4. **Scheduler: two regimes, chosen by an adaptive (bandit) rule.**
   - (a) *Burst/intensify after any new incumbent.* Immediately run every applicable local engine from the new best. In fox_mu4, 7 of the 10 global steps after the first followed the previous step within 0.12 h. fox_mu8 538/10 came 0.01 h after 539/10, and Joltik 43/9 and 43/8 came 0 h and 0.29 h after 43/10.
   - (b) *Persistent long trajectories for plateau breaking.* All 6 plateau-breaking global improvements (first improvement after a gap of 1 h or more) came from engines' *own* trajectories that had run 2.5 to 24 h without a reset, at 2,259 to 457,333 cumulative iterations. Examples: v2-walk Joltik 44/5→43/10 after 24.07 h; legacy-walk Joltik 44/6→44/5 after 16.17 h; v2-walk fox_mu4 129/7→128/10 after 13.56 h; v2-lns fox_mu8 after 9.70 h.
   - Keep a small number of long-lived walk/LNS chains that adoption does **not** reset.

5. **Change sharing.**
   - Adoption reset every engine, yet the adopter seldom made the next step. In fox_mu4, the first worker to beat an adopted point was the donor in 14 of 69 cases, the adopter in 9, a third worker in 39 and nobody in 7. In fox_mu8 the counts were donor 2, adopter 4, third 36, never 9 (51 adoptions). Only 9 of 69 and 4 of 51 adoptions were followed by any own improvement before the next adoption.
   - Every adopter of a point receives the same DAG. fox_mu8 ended with 10 workers on 4 distinct DAGs at 538/9. Joltik-depth ended with 5 workers on 1 DAG, and three-targets Joltik with 4 workers on 2 DAGs at 43/8.
   - Meanwhile 90 (fox_mu8), 103 (fox_mu4), 154 (AES 28/5) and 73 (InvMix 88/19) distinct DAGs at the best point were sitting in records. Seed adopters and restarts from this equal-point pool, not from one shared DAG.

6. **Allow depth slack for gate reduction, then repair depth.**
   - Three of the most consequential gate reductions went through a deeper intermediate:
     - fox_mu4 129/7→128/10, uncapped worker, repaired to 128/7 in 0.14 h;
     - Joltik 44/5→43/10, uncapped, repaired to 43/8 in 0.29 h;
     - fox_mu8 540/12→539/12, uncapped.
   - In total, 4 of the 6 gate reductions on FOX and Joltik came from uncapped workers, which were about 30% of workers.
   - The cap-7 Joltik workers sat at 44/5 for 75 h, because the cap ruled out 43/8.
   - Recommendation: search on gates with a soft cap (cap + 2–3), followed by a depth-squeeze or repair phase. Hard caps should apply only to publication.

7. **Check applicability against objective, gate limit and target size.**
   - Joltik depth_then_gates with gate_limit 43 = seed gates: legacy-constructor, legacy-paar, inverse-bp, legacy-anneal3, v2-anneal3 and v3-pairbank3 accepted 0 proposals. They emitted 107k to 142k over-limit witnesses per 5 sampled chunks, 100% filtered. That is 6 of 17 engines (35% of CPU) wasted by design.
   - On fox_mu8 (64 inputs, 540 gates) throughput per 30 s chunk collapsed for some engines: legacy-walk 8 iterations, inverse-bp 10, legacy-window 46, legacy-bp 48, legacy-lns 70, against v2-* at 120 to 143.
   - Gate engines by measured throughput, and by whether they can emit a feasible candidate at all.

8. **Stop or rotate rule for plateaus.**
   - Last global improvements:

     | Target | Last improvement | Run end | Plateau cost |
     |---|---|---|---|
     | fox_mu4 | 15.25 h | 75.25 h | 60 h × 8 workers = 480 CPU-h |
     | Joltik | 40.53 h | 75.25 h | 208 CPU-h |
     | AES bottom | never | 75.25 h | 452 CPU-h |
     | Joltik-depth | never | 23.38 h | 117 CPU-h |
     | InvMixColumns | never | 1.52 h | 20 CPU-h |

   - The longest productive gap observed was 24.07 h, on Joltik.
   - A rule of "no global improvement for 25 h, then switch target or apply a heavy diversification" would have saved about 280 CPU-h on fox_mu4 and about 300 CPU-h on AES. It would have lost nothing that was found.

9. **Chunk length: not tested.** Only 30 s chunks were used. Round-robin over 14 to 17 engines gives any single trajectory 1/14 to 1/17 of a worker. For example, the 24 h Joltik v2-walk chain received about 1.4 CPU-h. If productivity scales with trajectory CPU, a focused schedule would reach such steps much sooner, but that is untested.

10. **Telemetry to add** (details in section 7). Needed: cumulative per-engine counters, per-chunk start/end lines, start-circuit lineage, sub-operator identity, monotonic timestamps, and the best filtered candidate.

## 1. Per target × engine (strict / frontier / diversity, CPU)

All engines in a campaign received equal CPU through round-robin. Per engine, that was 32.2 CPU-h on AES, 42.9 on fox_mu4 and 26.5 on Joltik in three-targets20, 16.6 on fox_mu8, 6.9 on Joltik-depth and 1.4 on InvMix. Only engines with at least one strict improvement are listed; full tables are in `out/report_tables.md` and `out/engine_table.csv`.

| target (campaign) | engine | strict | workers | frontier (b) | diversity (c) | impr/CPU-h | first impr h |
|---|---|---|---|---|---|---|---|
| AES (3T) | v2-walk | 3 | 1 | 2 | 31 | 0.09 | 0.00 |
| AES (3T) | v2-lns | 2 | 1 | 2 | 204 | 0.06 | 0.01 |
| fox_mu4 (3T) | v2-lns | 4 | 4 | 52 | 458 | 0.09 | 0.03 |
| fox_mu4 (3T) | legacy-lns | 3 | 2 | 100 | 1162 | 0.07 | 0.59 |
| fox_mu4 (3T) | v2-translate | 2 | 2 | 122 | 2404 | 0.05 | 0.03 |
| fox_mu4 (3T) | v2-walk | 2 | 2 | 7 | 63 | 0.05 | 15.11 |
| fox_mu4 (3T) | legacy-window | 1 | 1 | 0 | 0 | 0.02 | 0.59 |
| Joltik (3T) | v2-walk | 3 | 1 | 1 | 47 | 0.11 | 40.24 |
| Joltik (3T) | legacy-walk | 2 | 1 | 0 | 36 | 0.08 | 0.00 |
| Joltik (3T) | v2-translate | 1 | 1 | 21 | 438 | 0.04 | 0.00 |
| fox_mu8 (JD) | v2-lns | 3 | 2 | 31 | 500 | 0.18 | 7.86 |
| fox_mu8 (JD) | legacy-window | 1 | 1 | 0 | 0 | 0.06 | 5.39 |
| fox_mu8 (JD) | v2-cores | 1 | 1 | 8 | 137 | 0.06 | 15.11 |
| fox_mu8 (JD) | v2-translate | 1 | 1 | 115 | 2084 | 0.06 | 0.00 |
| Joltik depth-first (JD) | all 17 engines | 0 | 0 | 0 | 10 | 0 | — |
| InvMixColumns (IMC) | all 14 engines | 0 | 0 | 6 | 310 | 0 | — |

Aggregated over all campaigns (`out/engine_aggregate.json`):

| engine | strict | frontier | diversity | CPU-h | strict / 100 CPU-h | frontier / 100 CPU-h |
|---|---|---|---|---|---|---|
| v2-lns | 9 | 95 | 1384 | 127 | 7.11 | 75 |
| v2-walk | 8 | 10 | 184 | 127 | 6.32 | 8 |
| v2-translate | 4 | 271 | 4982 | 127 | 3.16 | 214 |
| legacy-lns | 3 | 128 | 1948 | 127 | 2.37 | 101 |
| legacy-walk | 2 | 0 | 96 | 127 | 1.58 | 0 |
| legacy-window | 2 | 0 | 0 | 127 | 1.58 | 0 |
| v2-cores | 1 | 10 | 243 | 127 | 0.79 | 8 |
| legacy-constructor | 0 | 166 | 88 | 127 | 0 | 131 (far-worse) |
| legacy-paar | 0 | 133 | 210 | 127 | 0 | 105 (far-worse) |
| v3-pairbank3 | 0 | 30 | 114 | 33 | 0 | 90 |
| legacy-anneal3 / v2-anneal3 | 0 | 20 / 12 | 99 / 182 | 33 / 33 | 0 | 60 / 36 |
| v3-backward | 0 | 21 | 125 | 126 | 0 | 17 |
| v3-component | 0 | 7 | 43 | 127 | 0 | 6 |
| v3-interface | 0 | 1 | 0 | 127 | 0 | 1 |
| inverse-bp, legacy-bp | 0 | 0 | 0 | 127 each | 0 | 0 |

**Frontier-point quality** (median extra gates over the worker best / median depth saved):
- v2-translate: fox_mu4 +9 / −2, Joltik +2 / −1, AES +3 / −1.
- legacy-lns: fox_mu4 +6 / −2.
- v3-pairbank3: Joltik +6.5 / −3.
- legacy-constructor: fox_mu4 +69 / −7, fox_mu8 +595 / −7.

Final shared frontier points other than the best:
- v2-translate produced fox_mu4 129/6 and 130/5, Joltik 45/4, and fox_mu8 601/7.
- v2-lns produced AES 29/4, fox_mu4 141/4 and fox_mu8 540/8.
- v3-pairbank3 produced Joltik 47/3.
- InvMix frontier points came from v2-lns, legacy-lns and v2-walk.

v2-translate is the main producer of depth tradeoffs, and pairbank3 is the only useful depth-3 source.

**Sub-operators: data mostly insufficient.**
- three-targets20 records lack `engine_metrics.operator`; only engine, gate_count, depth and iteration are present.
- In the later runs, `operator` equals the engine family for walk/LNS and v3 (`value_search.propose` reports `operator: kind`). Remove-one versus remove-two and cone versus uniform destroy are never recorded per record.
- Recorded improvement operators: first-unlock (legacy-window, 1), cores (1), translate (1) and v2-lns (3), all on fox_mu8.
- depth-deadline-squeeze ran only in Joltik-depth, at 1.5k to 76k calls per sampled chunk-set, with 0 improvements.

## 2. Improvement chains (campaign-wide best)

Columns: h / worker / engine / iteration / jump / hours since the worker's last reset (adoption) / start kind / trajectory origin. "Fresh" means the engine had no state, so it started from the adopted circuit or the seed. "Own" means the engine continued its own trajectory.

**fox_mu4** (130/13 seed → 128/7):
| h | worker | engine | iter | jump | since reset | start | trajectory origin |
|---|---|---|---|---|---|---|---|
| 0.03 | 03 | v2-lns | 16 | 130/13→130/12 | – | fresh | seed |
| 0.03 | 03 | v2-translate | 205 | →130/11 | – | fresh | seed |
| 0.06 | 01 | v2-lns | 367 | →130/10 | 0.02 | fresh | adopted from 03 |
| 0.07 | 00 | v2-lns | 277 | →130/9 | 0.00 | fresh | adopted from 01 |
| 0.58 | 05 | v2-lns | 2744 | →130/8 | 0.51 | own | adopted from 00 |
| 0.59 | 03 (cap 13) | legacy-lns | **1** | 130/8→129/8 | 0.00 | fresh | adopted from 05 |
| 0.59 | 02 (uncapped) | legacy-window | **5** | 130/8→129/8 (same step, independently) | 0.00 | fresh | adopted from 05 |
| 1.54 | 04 | v2-translate | 5062 | 129/8→129/7 | 0.94 | own | adopted from 02 |
| 15.11 | 02 (uncapped) | v2-walk | 72911 | **129/7→128/10** | 13.56 | own | adopted from 01 |
| 15.23 | 01 (cap 14) | legacy-lns | 1112, 1286 | →128/9→128/8 | 0.12 | own | adopted from 02 |
| 15.25 | 00 (cap 13) | v2-walk | 319 | →128/7 | 0.01 | fresh | adopted from 01 |

**Joltik (3T)** (44/7 → 43/8): legacy-walk on joltik-02 reached 44/6 at chunk 0 (iteration 23) and 44/5 at 16.17 h (own, iteration 77,797, never reset). v2-walk on joltik-05 (uncapped) then reached **44/5→43/10** at 40.24 h, iteration 457,333, 24.07 h after its last adoption. The same trajectory went to 43/9 at 40.24 h and 43/8 at 40.53 h. Nothing improved in the remaining 34.7 h.

**fox_mu8** (540/14 → 538/9):
- v2-translate reached 540/12 at iteration 2 of the first chunk.
- legacy-window (first-unlock) made 540/12→539/12 at 5.39 h, own trajectory, 5.38 h after reset, uncapped worker.
- v2-lns reached 539/11 at 7.86 h (iteration 3009) and 539/10 at 15.10 h (iteration 11,986), on one trajectory 9.7 h old.
- v2-cores made 539/10→538/10 at 15.11 h on fox_mu8-04, *fresh* at iteration 30, 0.00 h after adopting 539/10.
- v2-lns reached 538/9 at 16.05 h (own, 0.93 h after reset).

**AES bottom**: the global best never improved; the seed was 28/5. The cap-4 worker started from the 38/4 seed. It reached 35/4 with v2-walk at iterations 63, 296 and 328, adopted 32/4 at 0.01 h, then reached 31/4 and 30/4 with v2-lns. It then adopted 29/4 at 0.28 h. 29/4 was a *frontier (b)* point of the uncapped aes-02, so frontier points from other workers act as improvements for capped workers.

**Start kinds over all 29 engine improvements:** 15 fresh and 14 own. For "own" improvements, the times since reset were 0.12, 0.12, 0.12, 0.51, 0.93, 0.93, 2.46, 5.38, 9.7, 13.56, 24.07, 24.07 and 24.35 h; one more came from a never-reset seed trajectory at 16.17 h.

**Jump size:** every strict engine improvement was −1 gate or −1 or −2 depth. The only larger jumps were the weak-seed AES cap-4 descents and the 129/7→128/10 and 44/5→43/10 trades. Gate-count reductions totalled 11: 5 on AES cap-4 from a weak seed, then 3 on fox_mu4, 1 on Joltik and 2 on fox_mu8. **In 1,871 CPU-h the framework removed 2 gates on fox_mu4, 1 on Joltik, 2 on fox_mu8 and 0 on AES, InvMixColumns and Joltik-depth.**

## 3. Improvement curves and plateaus

| target | global-best step times (h) | last step | run end | final plateau CPU-h |
|---|---|---|---|---|
| fox_mu4 | 0.03, 0.03, 0.06, 0.07, 0.58, 0.59, 1.54, 15.11, 15.23, 15.23, 15.25 | 15.25 | 75.25 | 480 |
| Joltik (3T) | 0.00, 16.17, 40.24, 40.24, 40.53 | 40.53 | 75.25 | 208 |
| AES bottom | none | – | 75.25 | 452 |
| fox_mu8 | 0.00, 5.39, 7.86, 15.10, 15.11, 16.05 | 16.05 | 23.38 | 73 |
| Joltik depth-first | none | – | 23.38 | 117 |
| InvMixColumns | none (all 13 stayed exactly at their seeds) | – | 1.52 | 20 |

The pattern is clusters followed by long plateaus.

| target | median gap between worker improvements | p90 | max |
|---|---|---|---|
| fox_mu4 | 0.023 h | 0.87 h | 12.8 h |
| Joltik | 7.7 h | 22.4 h | 22.7 h |
| fox_mu8 | 2.25 h | 7.1 h | 7.1 h |

## 4. Waste and inapplicability (last-chunk metrics from checkpoint.json)

These numbers come from **one chunk per engine per worker**: `metrics[engine]` is overwritten every chunk, and only `state.iterations` is cumulative.

- **No output at all:**
  - legacy-bp: 0.00 proposals per iteration on every target.
  - inverse-bp: 0.00 to 0.01.
  - legacy-window: 0.00 on all gates targets.
  - v3-component: 0.00 on AES and Joltik, 0.16 on InvMix.
  - v3-interface: 0.49 to 1.0 proposals per iteration but 0.00 accepted on AES and fox; 0.20 on Joltik.
- **Proposals that never change anything:**
  - v3-backward: accepted per proposal 0.01 on fox_mu4 and Joltik, 0.00 on fox_mu8.
  - v2-cores: 0.05 to 0.46 (fox_mu8 0.09; 0.92 on AES, but at only 0.01 proposals per iteration).
  - v2-lns: accepted 0.81 to 0.94, but "changed" only 0.00 to 0.21. Most accepted v2-lns proposals rebuild the identical program, which marks a structural plateau.
- **Constructors:** acceptance is 1.0 with 41 to 48% uphill. Their own best is 5 to 75 gates above the worker best. Because they leave `current_gates` far uphill, they contaminate the next engine in rotation (section 7).
- **Depth-first Joltik (gate_limit 43):** legacy-constructor filtered 126,115 candidates, legacy-paar 142,246, inverse-bp 124,330, legacy-anneal3 107,859 and v3-pairbank3 3,444, all with 0 accepted. Every worker also logged about 1,300 `record_gate_limit_rejections`. No engine made a single strict improvement in 117 CPU-h. Whether depth 7 at ≤43 gates exists is unknown, because the best filtered candidate is not recorded.
- **Scale:** on fox_mu8 the legacy value-bank engines ran 8 to 70 iterations per chunk. Their own trajectories ended about 70 gates above the incumbent in most workers.

## 5. Sharing and diversity

| target | adoptions | adopter improved before next adoption | first to beat adopted point: donor / adopter / third / never |
|---|---|---|---|
| fox_mu4 | 69 | 9 | 14 / 9 / 39 / 7 |
| fox_mu8 | 51 | 4 | 2 / 4 / 36 / 9 |
| Joltik (3T) | 14 | 1 | 6 / 1 / 4 / 3 |
| AES | 4 | 1 | 0 / 1 / 0 / 3 |

- **Per-capita view (fox_mu4):** the donor is 1 worker and beat 20% of adopted points, the adopter beat 13%, and each third worker beat about 9%. Adoption therefore does not make the adopter better than average. The donor's own trajectories are not reset, which is consistent with the persistence finding.
- **Value of adoption:** adoption's main value is the fresh-start harvest. legacy-lns found 129/8 at iteration 1 and legacy-window at iteration 5, both on circuits whose owner had not found the step. Under resync the owner would have found these steps itself.
- **Collapse at the final best point:**

  | target | final best | workers | distinct DAGs among worker bests | distinct DAGs in all records at that point |
  |---|---|---|---|---|
  | fox_mu8 | 538/9 | 10 | 4 | 90 |
  | fox_mu4 | 128/7 | 8 | 7 | 103 |
  | Joltik (3T) | 43/8 | 4 | 2 | 3 |
  | Joltik-depth | 43/8 | 5 | 1 | 3 |
  | AES | 28/5 | 5 | 5 | 154 |

## 6. Depth caps and objectives

- **fox_mu4:** caps 13, 14 and none all ended at 128/7, so the cap made no difference when the optimum lies below it. The 128-gate step itself came first on the uncapped worker, at depth 10.
- **Joltik (3T):** the cap-7 workers ended at 44/5, and the cap-8 and uncapped workers at 43/8. Only the uncapped joltik-05 found 43 gates, through 43/10.
- **AES:** the cap-4 worker is the only one with a different final best (29/4). The seed choice mattered more than the cap: 38/4 seeds under cap 5 or none adopted 28/5 within 0.01 h.
- **InvMixColumns:** caps 5 to 20 and none each kept their seed point (119/5 … 88/19). The run was too short (1.5 h) to tell whether the caps or the seeds were the binding limit.
- **depth_then_gates:** the only run is Joltik at gate_limit 43, equal to the seed gates, and it gave 0 improvements. The evidence is insufficient to judge the objective in general; the tight limit made 6 of 17 engines inapplicable.

## 7. Other findings and missing telemetry

- **Contamination mechanism** (`worker.py`): `gates = prior["gates"] if prior else self.current_gates`, and `current_gates` is the last engine's *end trajectory*. After an adoption reset, every engine after a constructor in the rotation inherits constructor junk. This is visible in invmixcolumns-00, where every engine after legacy-constructor ended 224 to 276 gates above the worker best.
- **v2-lns and v2-translate stayed near the incumbent:** 5% to 54% of their slots were ≥5 gates off, against 47% to 95% for legacy-bp, legacy-window, the constructors and v3-component/interface. They never accept uphill moves (uphill per accepted move = 0.00). This is part of why they look best: they were the only engines usually running on good circuits.
- **Verification volume:** candidates_verified per worker was 15.8M on Joltik, 11 to 15M on AES, 5M on fox_mu4 and 0.32M on fox_mu8. Its CPU cost is not measured.
- **Missing telemetry, ranked by value:**
  1. Cumulative per-engine counters (proposals, accepted, changed, uphill, filtered, wall seconds); only the last chunk survives.
  2. A per-chunk log line: engine, fresh/resumed/resynced, start (g/d) and its provenance, end (g/d), own best, iterations.
  3. Sub-operator identity and parameters on every emitted record and in counters (walk remove-1/2 and add count, LNS cone/uniform and victims, v3 move kind), plus counts of tried versus succeeded.
  4. Monotonic elapsed time in every event; UTC drifted by 7%.
  5. The best filtered (over-gate-limit or over-cap) candidate per chunk, as a near-miss signal.
  6. The age and iteration count of trajectories destroyed by an adoption reset.
  7. Verification and record-write time per chunk.
  8. A plateau metric: count of distinct equal-score programs visited, not capped at 32 stored.

*Statistical caveat:* there are only 29 strict engine improvements, 17 of them after the first 0.5 h, spread over 4 targets. Per-engine rates are ranks with wide uncertainty, and the zero rates for v3 and anneal engines are confounded by trajectory contamination.

Machine-readable outputs, all in the analysis's working folder (not included):
- `improvements.csv`: every worker-best improvement, with chain fields.
- `engine_table.csv` and `engine_table.json`: per target × engine; the JSON includes operators.
- `engine_aggregate.json`
- `frontier_point_quality.json`
- `summary.json`: global chains, adoptions and final points.
- `extra.md`: final frontier producers and per-worker engine own-best gaps.
- `extra2.json`
- `report_tables.md`: all detailed tables.
- `raw_analysis.json`: parsed events.
