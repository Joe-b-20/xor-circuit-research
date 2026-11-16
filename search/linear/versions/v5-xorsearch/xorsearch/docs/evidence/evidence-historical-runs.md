# Evidence from historical (pre-framework) XOR-circuit search runs

Scope: G1 July ladder/cascade/sub89, G2 campaign 87 (hunt waves, hunt87, cascade6), G3 InvMixColumns pipeline + BP, G4 v2 long20, G5 v3 own20. `search/runs/` was not analysed. Everything is read-only. Parsed outputs were kept outside this repository (listed at the end, not included).

**Confidence tags:** **[S]** strong (many events, or a same-code comparison). **[M]** moderate (a few events or confounded). **[W]** weak or anecdotal (n of 1 to 3, or a number I copied from a secondary summary without re-deriving it). Numbers I took from `local-inventory/METHOD_CATALOG.md` were copied there from slice reports. That catalog's own audit passed 37 of 62 sampled entries, so those numbers are marked "(catalog)".

---

## 0. Ranked recommendations for the unified algorithm

1. **Make a neutral plateau walk the main engine, and pair it with a Pareto depth tie-break.** [S]
   - Every 88 the forward search found came out of a walk chunk: 88@7, 88@8, 88@6, both 88@5s, and the cascade6 91@4.
   - My log parse attributes the improvements as follows:
     - Wave-2/3 fleets: 11/11 gate-level improvements to walk.
     - `c_naive`: 191 walk, 0 LNS, 5 ambiguous.
     - cascade6: 70 walk, 0 LNS.
     - The catalog's archive-wide figure is walk 736 vs LNS 22.
   - Inverse line, same seed, same code, about 20 h each:
     - walk-only reached 88@33;
     - alt reached 90@23 and 89@16;
     - LNS-only stalled at 96 and only went further by adopting the walk's circuits.
   - The depth tie-break turned every 88 into a shallow record within seconds (11→7 in 5.3 s, 6→5 in 6.1 s, 6→5 in 4.2 s, 10→8 in 1.2 s). Without it, 89@5 and 92@4 would have been thrown away.

2. **Keep LNS as a secondary move, given about 20–35 % of time and a cool acceptance rule. Do not treat it as the main improver.** [M]
   - In `c_naive`, LNS had about 78 % of the wall time (420 s of each 540 s cycle) but produced about 15 % of local-best drops (34 of 227, all ambiguous). That is roughly 0.7 drops per LNS CPU-hour against about 14 per walk CPU-hour.
   - LNS does have a role: it made the v2 89@4 and 90@4 ("lns rebuild"), several mid-level 93→91 and 90→89 steps, and every point on the capped inverse depth staircase.
   - Under SA (T0 1.2, cool 0.9997, reheat 4000), LNS `cur` sat 5–10 gates above best (cur 94–100 while best was 88–92). Use threshold acceptance or a cooler schedule, especially under a depth cap.

3. **Restarting from fresh random constructor roots should be the default diversity mechanism.** [S]
   - `c_naive` (07-30 log, 60.5 CPU-h): 58 naive roots; 7 reached 88 (12 %), 25 reached ≤89.
   - Time from root to 88: median 2,234 s (range 626–3,855 s).
   - Catalog: 169 restarts, 14 reached 88, all 14 in never-seen pockets, flat yield curve. Fresh-fleet descents: 52 of 1,500 reached 88.
   - Cascade6's 91@4 came from the 5th naive root of a session, 3,263 s after that restart began.
   - Defaults: a stall timer of about 2,400 s (or the equivalent iteration count), and a per-root budget of 1–2 h, because no 88 arrived later than 3,855 s after its root.

4. **Do not use continuous global reseeding or shared-pool cross-pollination by default.** [S for harm, M for zero benefit]
   - The 14 July cascade with continuous reseeding collapsed d5–d11 onto one 91@5 for about 2.7 h. That is 7 workers, about 19 CPU-h, with no progress.
   - Cross-pollination merged 3,651 times (1.07 M masks, catalog) and contributed nothing to any record. LNS chunks that cross-pollinated never improved the best.
   - Seeded fleets swarmed onto one family: 53,902 of 54,889 new 88s fell in family 3.
   - If sharing is kept, share only strict improvements, keep it within a lineage, and make it rare.

5. **Use symmetry and orbit seeding as an optional "buy a coordinate uphill" operator.** [M]
   - Two of the five 88s descend from deliberately worse ρ²-symmetric seeds: 94@5 (+6 over 88), giving 88@7 in 33 min; and 90@9, giving 88@8 in 124 min.
   - The catalog says naive uphill acceptance was measured useless.
   - For a general map: compute Aut(M) and offer an orbit-symmetrized seed generator as one root type.

6. **Drop, or give at most a 5 % budget to, the v2/v3 structured moves until they show a positive control at the frontier.** [S for zero record contribution]
   - These are translate, cores, expansion, component merge, interface basis, backward package, pairbank3 and proof-destroy.
   - In v2 (548 CPU-h), translate plus cores used 171 CPU-h (31 %). In v3 (475 CPU-h), the structural stages used 122 CPU-h (26 %).
   - Across 1,023 CPU-h the result was 2 gate improvements, both "lns rebuild", and 2 depth tie-breaks.
   - No mechanism-level best improvement is attributable to any of them.

7. **Run the depth ladder as a cascade without lifting, and start capped rungs from shallow constructors.** [M]
   - Capped LNS from a "lifted" seed (an infeasible seed projected onto the cold naive set, keeping 54–72 of 88 masks) was weak: in 19 h it reached 149@6 and 178@5, and in 72 min from 88@33 it reached only 96@12 and 96@16.
   - The cold cascade's uncapped final rung reached 91@14, and its capped rungs reached 95@9 and 101@8.
   - The forward capped-walk recipe (anneal3 root plus capped walk) gave 91@4.

8. **Instrument everything (see §7). Use iteration-denominated budgets and checkpoint before every accepted improvement.** [S]
   - Several record events cannot be attributed, and documented reruns of the naive#1958 root missed 88@5.

---

## 1. Logged improvement events

### 1a. Record and frontier events

| Record | Gen / worker | Engine (chunk) | Root / seed | Config | t since start | Gap since prev gate-level | Tie-break |
|---|---|---|---|---|---|---|---|
| 97@3 | G1 ladder d3 | anneal3 | scratch, seeds [1,2,3] | cap 3 | 235 s (reproduced at 267 s and 426 s) | 103 s (98→97) | no |
| 89@6 | G1 ladder d10 | lns (v1) | 92@7 from d9 | cap 10, 600 s chunks | 15,544 s in rung (11.03 h run) | 12,347 s | no |
| 89@5 | G1 sub89 uncapped | lns | 89@6 | uncapped | 592 s | n/a | **yes** |
| 92@4 | G1 cascade d8 | lns | 93@5 | cap 8, found at depth 4 | 1,400 s in rung | n/a | **yes** (taken by Pareto, reseeded to d4) |
| 88@7 | G2 w10_sym94 | walk (alt 300/600) | ρ²-sym 94@5, rng 1010 | default knobs, pop_glob on | 1,973 s (it 45,614 at d11) | 1,771 s | 88 at d11, then tie-break to 7 in 5.3 s |
| 88@8 | G2 d3_orb90a | walk (alt 300/600) | ρ²-sym 90@9 (derived), rng 3303 | knobs '{}', no repel | 7,453 s | 3,659 s | d10→8 in 1.2 s |
| 88@6 | G2 c_naive s4 r18 | walk (alt 120/420) | naive#2163 (139@3) | stall 2400, budget 7200 | 37 min after root | n/a | d7→6 in 0.5 s |
| 88@5 (derived) | G2 o_polish r71 | walk, first chunk | o1_c129 90@9, rng 9841 | stall 1200, budget 3600 | 85 s after root | n/a | d6→5 in 4.2 s |
| 88@5 (from scratch) | G2 c_naive s5 r16 | walk | naive#1958 (146@3), rng 1958 | as for 88@6 | 3,844 s after root | n/a | d6→5 in 6.1 s |
| 91@4 | cascade6 d4 r5 | walk (alt), 22 s into chunk | naive#40426 | cap 4 | 3,263 s after root | 1,024 s (92→91) | no |
| 90@4 | v2 w14 | "lns rebuild" | own91, rot 0 | cap 4, medium profile | 11.31 h | 11.31 h | no |
| 89@4 | v2 w07 | "lns rebuild" it 718,476 | own91 rot 2, then 90@4 adopted via 14→01→07 | cap 4, aggressive profile (deadline_p 0.4) | 16.07 h | 4.76 h | no |
| inv 89@16 | G3 a4_alt_113 | walk (first chunk) | BP 113@17 | alt 300/600 | 266 s | about 177 s | **yes** (depth-tiebreak it 147,935) |
| inv 88@33 | G3 a3_walk_106 | walk | BP 106@21 | walk only | 13,510 s | 892 s | no |
| inv 95@9 / 91@14 | G3 cascade d9 / final | lns | cold 315@5 ladder | cap 9 / uncapped | 26,122 s / 47,137 s | 3,006 s / 3,012 s | 91@14 by tie-break |

The inverse 88@19 is an algebraic re-labelling (e27 bi-generation, deterministic, no RNG). It is not a search event.

### 1b. Improvement rates by engine

| Dataset | CPU-h | Gate-level improvements | Rate per CPU-h | Notes |
|---|---|---|---|---|
| G1 ladder (v1 LNS rungs) | 133 | lns 25 | 0.19 | never below 89; ≤92 gaps median about 10,000 s |
| G2 07-26 + 07-27 seeded fleets | 74 | walk 11, lns 0 | 0.15 | LNS chunks never improved the best |
| G2 c_naive 07-30 (5 sessions) | 62 | walk 191, ambiguous 5, lns 0 (global NEW BEST) | 3.1 | from-scratch descents are mostly cheap high-level drops |
| c_naive local-best drops | 60.5 | walk 193 (46 ambiguous), lns 34 (all ambiguous) | walk ≈14 per walk-h, lns ≈0.7 per LNS-h | uses the nominal 120/420 split |
| G2 o_polish | 39 | 88: 1 of 88 roots; 89: 40 roots | n/a | roots were orbit 90s |
| cascade6 | 41 | walk 70, ambiguous 1 | 1.7 | |
| v2 long20 | 548 | 2 gate + 1 depth (lns) | 0.0055 | warm start on records |
| v3 own20 | 475 | 0 gate, 1 depth (walk) | 0 | warm start on records |

Caveat [M]: the G1 LNS was the v1 engine. The later merged engine is 17.5× faster on LNS and 21.9× faster on walk (catalog), so the comparison across generations is confounded. The G3 setA comparison (§5) is a same-code comparison.

---

## 2. Plateaus

### Flat time before improvements

- **G1 LNS rungs:** at the ≤92 level the gap between gate improvements was 340–31,000 s (median about 10,000 s). d10 sat at 89@6 from 15,544 s to 48,256 s with no change.
- **G2 walk, seeded:** 89→88 took 1,771 s (w10) and 3,659 s (d3_orb90a).
- **G2 walk, from scratch:** root→88 had a median of 2,234 s; root→89 a median of 1,577 s (range 307–3,884 s).
- **Inverse:**
  - a3 walk was flat at 90 for 12,497 s, then 89→88 took 892 s;
  - a4 alt was flat at 89@16 for about 71,100 s;
  - a2 alt was flat at 90@23 for about 71,200 s.
- **v2:** 91@4 lasted 11.3 h, 90@4 lasted 4.8 h, 89@4 then stayed flat for the remaining 11.3 h. **v3:** flat for 23.8 h on every seed.

### Equal-size states traversed

| Population | Size | Notes |
|---|---|---|
| c_naive harvest, sessions 4–5 | 37,305 distinct 88-states | 14,816 in session 5; 135 of them realize at depth 5 |
| 88@6 basin | 8,993 states at J>0.7 | 4,420 at depth 6; max pairwise J-distance 0.167; all from one worker |
| hunt87 (19.7 h) | 148,347 new 88-states | detector backlog dropped 64,421 on overflow |
| hunt-deeper wave 3 | 54,889 new 88s | 53,902 in family 3; 0 in a fourth family |
| Known corpus | about 139,878 distinct 88s | 836,598 at beat88 scale (catalog) |
| Inverse 88 level | 729 sets | one re-association orbit (6 slots × 3, 3⁶); a fresh worker re-found 670/729 in 870 CPU-s and added 0; revisits per distinct 88.0 |
| Inverse 89 / 90 levels | 538,031 / 1,611,534 distinct | |
| Old forward 88 plateau | 4,861 two-critical cores UNSAT at cap 6 | no 88@6 exists near it |
| Tabu + "away" walk (catalog) | 64 → 726 states (11×) | reach ceiling unchanged; radius ≤12 at 88@5, ≤16 at 88@6 |

### What broke plateaus

| Mechanism | Events | Strength |
|---|---|---|
| Fresh constructor root | 88@6, 88@5 (from scratch), 91@4, 7 of 58 c_naive roots reaching 88 | [S] |
| Deliberately worse symmetric seed | 88@7 (+6), 88@8 (+2) | [M] |
| Pareto depth tie-break, same mask set | every depth record | [S] |
| Reseed or adoption | spread 89@4 and 90@4 between v2 workers; inverse a1 adopted 89@16 and 88@33 | [S]; propagation only, never discovery |
| Hub move | 0 successes in about 2.24 M samples at the frontier (catalog); useful at 90→89 | [S] |

- The control audit found that the smallest window carrying a verified circuit to a strictly smaller verified one has a median of 42 values, and 44 of 45 need k≥8. So improvements at the frontier are large-neighbourhood events, and exhaustive k≤3 shells say nothing about whether an 87 exists.

---

## 3. Diversity

### Collapse

- **14 July cascade** (its config file says the reseeding "collapsed diversity"): from about 13,670 s to the 23,366 s stop, d5–d11 all held 91@5. The global best was broadcast as reseed offers to every rung, and each worker logged an ADOPTED line every 600 s.
- **Wave-3:** after 03:10 the repulsion and prospecting workers swarmed onto family 3. Repulsion with a 57-mask family core found 0 new families.
- **hunt87:** the 8,993-state family-4 basin was entered only by `c_naive`. The explorers reached 88@6 only after fam4 representatives were injected into their archive.
- **v2:** workers 01, 07 and 14 synchronised onto one 89@4 within 19 s of each other.

### What restored diversity, and how much

| Mechanism | Measured effect | Record contribution |
|---|---|---|
| Fresh roots (c_naive; catalog D5, D12) | 14/14 88-reaching restarts in new pockets, zero repeats; 2,722 new families in 747 core-h | **all from-scratch records** |
| Repulsion (D10) | 356 new 89 sets (vs 4 known), min J 0.107 | none |
| MAP-Elites archive (198 cells, 4,375 expansions) | 24,473 submissions → 585 accepted, 0 new families (catalog) | none |
| Island migration | never fired (islands within 5 gates) | none |
| Cross-pollination | 3,651 merges; silently dead in hunt87 with no log line | zero |
| Provenance share groups (v2/v3) | enforced isolation | n/a |
| Byte rotation per worker (v2) | seeds rotated 0–3 | 89@4 sources show rotations 2 and 0; no measured effect |

---

## 4. Mechanism counters in v2 and v3 (fleet totals)

**v2 long20:** 20 workers × 27.4 h = 548 CPU-h, 30 s chunks, cycle walk/lns/lns (anneal3/lns at cap 3).

| Move | Calls / iterations | Accepted | Notes | Attributable best improvements |
|---|---|---|---|---|
| walk | 63.5 M it | 6.89 M | | 0 |
| lns | 49.2 M it | 44.5 M (6.84 M changed) | 551 k uphill, 23.9 k snapbacks | 3 notes say "lns rebuild" or "lns depth" |
| deadline rebuild | 10.26 M (valid = calls) | 1.79 M improved_extraction | | unknown |
| translate | 2.73 M | 450 k | 104 h | 0 |
| cores | 1.62 M | 368 k | 67 h | 0 |
| expansion | 4.17 M | 186 k | | 0 |
| joint (d3) | 918 k | 10.9 k improved | | 0 at fleet level |
| hub | n/a | 2,571 | | 0 |
| anneal3 | 67.8 M it | n/a | | 0 |

- Diverse handoffs: 18,789; reseed adoptions: 4.

**v3 own20:** 475.5 CPU-h.

| Move | Calls | Accepted | CPU-h |
|---|---|---|---|
| component merge | 552 k | 31.9 k | 20.9 |
| interface basis | 478 k | 24.6 k | 21.3 |
| backward package | 561 k | 25.8 k | 18.7 |
| cores | 568 k | 179 k | 23.5 |
| translate | 1.01 M | 216 k | 37.3 |

- pairbank3: 513 k iterations, 131.5 k accepted. Its fixed-parent exact calls (6,414) returned 22 SAT, 1,276 UNSAT and 5,116 UNKNOWN (80 % unknown).
- proof_destroy: 1.14 M checks, 43.8 k accepted.
- advanced stage: 7,983 same-bank topology changes.
- best_updates: 22 (20 starting seeds plus one 88@7→88@5 "walk depth").

**What these numbers show:**
- Positive contribution: only LNS rebuild (the 89@4 and 90@4 events) and walk or LNS depth tie-breaks. Every other mechanism is zero at the record level. That is about 30 % of CPU.
- The v3 held-out confirmation (45 s, 3 seeds, from 102@5) found that no alternative beat the defaults.
- The 8 s screen was noise: the default scored 102/102/102 while every alternative scored ≤102.
- "Accepted" mostly counts neutral or no-op moves, so it cannot stand in for usefulness.

---

## 5. Inverse line (G3)

- **BP as a root generator:**
  - The clean-room BP produced 0 circuits: its distance metric decides ≤6, but the inverse rows have weight 11–19. Lesson: a general constructor must not assume sparse rows.
  - With the one-hop fallback (8 × 600 s) it produced 106–125. With a shared incumbent (3 × 1,800 s) it produced 97@22.
  - Useful as roots only.
- **Same seed (106@21), same knobs, 6-worker setA [M, n=1 per arm, strongest controlled comparison in the archive]:**
  - walk-only: 90 by 121 s, 88@33 at 13,510 s;
  - alt: 90@23 at 142 s, then flat;
  - LNS-only: 96@15 by 308 s, then progress only through adoption.
  - In the smoke run (about 100 s each), walk reached 89@25 while LNS reached 98@17.
- **Alt on BP 113@17:** 89@16 in 266 s, with walk making every gate-level step.
- **Diverse lineages (reseed off, about 75 min):** Yuan-91 walk reached 89@27, BP-97 alt reached 89@30. The lns worker on cascade 91@14 made no progress.
- **lift_to_cap:** logs say "NOT feasible at cap … lifted onto the cold naive set: 55/88 (cap 5), 72/88 (cap 6), 54/56 (cap 16/20) masks kept, start ≈370 masks". Results: 178@5 and 149@6 after about 19 h; 96@12 and 96@16 after 72 min from 88@33. In practice lifting throws the seed away. [M]
- **Cascade (cold 315@5, IMPROVE_BY 5):**
  - All rungs had launched by 482 s. The triggers fired almost immediately, so the ladder did not stage work in any meaningful way.
  - Coordinator reseed offers: 372. Adoptions: d6 13, d7 12, d8 21, d9 16, final 12.
  - It produced the shallow staircase (103@7, 101@8, 95@9, 91@14), which seeded walks could not reach because walks drift deep (88@33, 89@25–38).
  - Handoffs were useful for depth points, not for count.

---

## 6. Settings that mattered

| Setting | Evidence | Verdict |
|---|---|---|
| Walk/LNS chunks 120/420 s (c_naive) vs 300/600 s (waves 2/3) vs 30 s cycles (v2) | All produced records; no controlled comparison | [W]. Default to walk-heavy chunks; reseed from own best at each chunk (catalog D6: 23.3 % vs 5.6 % of ≥10-mask changes) |
| `plateau_slack_p` | Catalog: "arithmetically inert"; walk provably monotone | Remove, or implement a real non-monotone move |
| SA T0 1.2 / cool 0.9997 / reheat 4000 | LNS cur drifts +5–10 above best | Use threshold acceptance under caps (HOW.md) [M]. Catalog C3: SA-with-reheat gave about 2× drift; LAHC inert |
| `snapback` 12 (hunts) / 3 (capped inverse) / 4–8 (v2) | No comparison | [W] |
| Restart: stall 2,400 s / budget 7,200 s | 52 of 58 restarts ended on stall; all 88 arrivals ≤3,855 s after the root | Budget about 4,000 s; stall about 1,500–2,400 s [M] |
| `hub_move_p` 0.3–0.5 | Hub dead at the frontier (0 / 2.24 M), useful higher up | Anneal the probability down near the best [M] |
| LNS destroy mix | Uniform destroy: 0 accepts in 5,633; coneinj about 12× improvements/s; victim repool about 34× accepted (catalog) | Keep cone/big-injection destroys [M] |
| Exact repair prescreen `valid[:4]` | Deletes 30–37 % of true plateau edges (catalog) | Use complete enumeration [M] |
| v2 knob profiles (deadline_p 0.12 / 0.25 / 0.4) | The 90@4 came from 0.25, the 89@4 from 0.4; no event at 0.12 | [W], n=3 |
| cascade6 dyn screen (11 random configs) | Walk-only arms reached 89–91 in 1,800 s; one LNS-only arm reached 98@4; a BP root gave 103@8 | [W] |
| v3 screen | 8 s screens are uninformative; 45 s × 3 seeds showed no winner | Screens need ≥30 min × ≥5 seeds |

---

## 7. Missing telemetry, by generation, and the must-log list

**G1.**
- Seeds were [1,2,3] with per-chunk increments, and the RNG state was never saved.
- The engine source contains a later INF/emission patch; the pre-patch source is gone.
- Wall-clock budgets; no per-move counters; no CPU, Python or hash-seed record.

**G2.**
- NEW BEST lines are only global improvements. Per-restart local bests appear only in chunk reports about every 20 k iterations, so LNS-vs-walk attribution was ambiguous for 34 of 34 LNS drops and 46 of 193 walk drops.
- The sub-move (remove-1, hub, repair) is not logged.
- The harvester records only at the running best.
- Cross-pollination was silently dead: no log line said so, and `supervisor.py` as-run was not archived.
- Two processes interleaved writes into one log (cascade6 d4), and session clocks restart.
- The `orbit pick_seed` bug left a seed unused for 345 cycles without being noticed. A seed-usage histogram would have shown it.
- Reruns of naive#1958 missed 88@5, because wall-clock chunk boundaries make the trajectory non-replayable.

**G3.**
- Only `seeds[0]` is consumed per chunk, and the state at discovery was not saved.
- Coordinator offers and worker adoptions are logged in separate files.

**G4.**
- The 89@4 note says only "lns rebuild". It cannot be split into extraction vs deadline rebuild vs pool source.
- Cumulative counters have no per-move "improved best" field.
- `random_seed` is the base seed, but persisted RNG state overrides it, and the checkpoint was saved after discovery.
- CPU affinity at discovery is unknown.

**G5.**
- Same gaps as v2.
- "Accepted" mixes neutral and no-op moves.
- Screens were too short to read.

**Must-log list for the new algorithm.**

1. Per improvement event (gate or depth), log all of the following:
   - worker, restart and root id (constructor plus integer seed, or source hash);
   - engine, sub-move, and destroy-set size and positions;
   - rebuild method;
   - before and after (gates, depth) and the symmetric difference;
   - iteration, CPU-seconds since root and since the previous improvement;
   - RNG state, or a counter-based seed;
   - the parent state hash.
2. A checkpoint immediately before each accepted improving move, so the event can be replayed.
3. Per move class: calls, valid, strictly-improving, depth-improving, neutral-changed, no-op, uphill, and CPU-seconds, in time-bucketed (not only cumulative) form.
4. Deterministic iteration or CPU budgets. Chunk boundaries should be set in iterations, not wall-clock.
5. Every share or adoption event, with its source and receiver, plus the lineage graph.
6. A diversity panel at fixed intervals: pairwise Jaccard across workers, a distinct-basin count, and the fraction of workers on the modal state. Alarm when it collapses.
7. A seed and root usage histogram.
8. Harvest counts per level (distinct states and revisit ratio) with a known recording policy.
9. Environment: argv, source hash, Python and OS, CPU model, affinity, PYTHONHASHSEED.
10. A positive control for every new move: show it finds a known one-gate-above improvement before it is given fleet budget.

---

## Files

All kept outside this repository: the analysis's working folder (not included)

- `evidence-historical-runs.md` (this report)
- `g12_events.json` (G1/G2/cascade6 NEW BEST events and per-restart local-best trajectories)
- `g12_improvements.csv` (every NEW BEST with its kind, engine attribution and gap)
- `inv_events.json` (G3 worker events and adoptions)
- `v2_workers.json` (v2 per-worker BEST timeline and counters)
- `v3_counters.json` (v3 per-worker state and fleet totals)
- `catalog_CD.txt` (extract of METHOD_CATALOG families C and D)
- Parsers: `parse_g12.py`, `parse_inv.py`, `v2.py`, `v2b.py`, `v3.py`, `s13.py`, `s34.py`
