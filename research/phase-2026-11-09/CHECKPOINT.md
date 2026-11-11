# Phase 2026-11-09: living checkpoint

Conservative post-sprint phase (main agent Fable 5.1, from 2026-11-09 ~14:30 UTC). Branch
`phase-2026-11-09` (sprint tip + main). The sprint branch `sprint-2026-11-07-linear-maps` is
untouched (tag `sprint-2026-11-07-final` = 882c962). Scripts and run data for this phase:
`~/xs-campaigns/2026-11-09-phase/` (phase 1) and `~/xs-campaigns/2026-11-10-proof/` (proof follow-up).
Evidence tags as in the sprint: [proved] [checked] [measured] [cited] [guess].

Sections 1-3 are the current state. Section 4 is the historical log: entries written while work was
running, kept verbatim and marked superseded; nothing in section 4 describes the present.

## 1. Final state of phase 1 (closed 23:20 UTC 2026-11-09; corrected 2026-11-10)

- **Circuits**: PUBLISHED on `main` and pushed 15:11 UTC 2026-11-09 (726f8d3 harvest, 1508e40 harvest
  fix, f948f19 SEARCH-TIME row, 71184a9 README). 44 circuits added, 37 dominated removed, 208 circuits;
  `circuits/check.py` 208/208, test suite 358 OK; CI run 42642167215 green. Twelve maps have a new
  any-depth minimum; the rest are depth-limited improvements. NIST-beating set unchanged (46 of 53).
- **Proofs**: PUBLISHED on `main` and pushed ~17:05 UTC 2026-11-09 (185c0cd folder
  `lower-bound-proofs/mixcolumns-lb75-open-cases/`, 400ad09 README pointer). Sprint rows 1,508 -> 686
  certified; October push5/push6 rows reconciled (same domain, keys, types, base rows; only shared row
  N1); combined 280 open claims (LP status), 406 further exclusions certified J1-free; two audits
  (recon, recon-check, both xhigh) plus a packaging agent; `verify_all.py` ~85 s, run by `proofs.yml`.
  **The lower bound stays 75.**
- **Worker count** [measured, two trials, seeds 20261109 / 20261110, 60 min per arm]: unhelpful under
  the tested conditions. 300 workers cost 17-28 % of aggregate throughput, delayed the first 88 by
  8-9x, and produced no more distinct *recorded signatures* (hunt/sig.py's cheap signature on the g88
  records, an upper bound on distinct exact plateaus, which were not computed) per wall-hour. The
  per-trajectory medians quoted in REPORT section 4 are conditional on success (over the trajectories
  that reached 88 within the hour). Practical recommendation kept: one trajectory per thread.
- **Foundation restart** (commit 8e544ba, default off, default path byte-identical, 371 tests): **no
  demonstrated benefit under the tested configuration** (swap_pairs 2, pin 150,000 proposals, `l1tree`
  constructor, stall 300 s): B1 0/12 reached 89 in both arms (pinned completions ended at 91-101);
  B2 uninformative (1 foundation restart fired); B3 no benefit on InvMixColumns. The results do NOT
  establish that crossing between foundations needs informed moves or exact search, and do NOT
  identify the restart policy as the principal cause (stall length, constructor quality and source
  quality were not separated). Recorded limitations: only `l1tree` completes under the restriction
  (`paar`, `naive`, `bp` fail; 10 of 33 restarts fell back); its roots start 20-30 gates above the
  donor. Missing positive control: zero-swap reconstruction of a known result within the actual pin
  budget was never run; if the feature is revisited, run that control first.
- **Search defaults kept** (owner, 2026-11-10): 20 workers, foundation restart disabled, no new large 87 campaign.
- Report: [REPORT-2026-11-09.md](REPORT-2026-11-09.md) (sections 4-5 corrected 2026-11-10; section 6
  superseded by the proof follow-up below).

## 2. Proof follow-up (2026-11-10, in progress)

Owner's brief (2026-11-10): before any enumeration, establish exactly how it connects to the remaining
proof obligations; produce a machine-readable coverage manifest; specify one family with a completeness
argument; run one bounded pilot with controls and an independent check; keep the bound at 75.
Work folder `~/xs-campaigns/2026-11-10-proof/`; deliverables under `research/phase-2026-11-09/proof-followup/`.

Running / in progress at the time of this commit: see the "Status" line at the end of this section
(updated with each commit).

- Scope measurements done (`scope/`): hypothetical scans with the published driver and the independent
  checker's matrices (`hypo_scan.py`): full 280 / 229 reproduced; **if every leaf with A >= 2 were
  excluded, 119 claims would stay open** (120 load-bearing keys, 52 at q = 6); if every A >= 2, q_D = 0
  leaf were excluded, 153. Killing all 229 current load-bearing keys leaves 151 claims alive on 138
  further LP-feasible keys (`hypo_kill.py lbonly`): the 229 are the first layer of a ladder, not the
  whole obligation. Integer status of the 572 open leaves with recorded solver status
  (`leaves_int.py`, HiGHS MILP, 60 s limit, all 1,388 solves ended with status 0 or 2): **164 leaves
  integer-infeasible, 408 integer-feasible**; 62 keys have only integer-infeasible open leaves; killing
  them closes 44 claims (280 -> 236). The 101 keys of the sprint's MILP classification: none is among
  the 229, one ((11,7,0,M,4,2)) is LP-feasible but not load-bearing; they were never used as exclusions
  and stay unresolved. The M^T q = 1 and M q = 2 enumerations of the sprint address no live key: no
  q <= 2 key is load-bearing (82 are LP-feasible behind the first layer) and the sprint's two q = 1
  representatives are LP-infeasible under the combined rows.
- Pairwise sharing is not an obstruction [measured, `share_pairs.py`]: anchored hubs (r = 1, 2) with no
  full-met label can share a hub-only label with the joint family independent in 361,168 (r = 1/1),
  58,172 (1/2) and 3,900 (2/2) mask pairs for M (481,440 / 83,940 / 5,748 for M^T); every value with two
  triples has 13-36 such r = 2 partners. A per-pair finite fact therefore gives no row; what remains is
  joint over whole configurations.

- Ladders done (`scope/ladder.py`, 47 min): 4,223 LP-feasible keys stand in the 280 claims' ladders
  (229 first level + 3,994 behind), 68,153 open leaves (1,637 integer-infeasible, 2 unresolved); the
  ladder evaluation reproduces every driver hypothetical (119 / 153 / 88) and adds INT 236, INT+A01 103.
  Manifest written: [proof-followup/MANIFEST.md](proof-followup/MANIFEST.md) +
  `proof-followup/scope/coverage_manifest.json`.
- Pilot agent (high) launched 21:20 UTC on the M^T q = 3 block (brief
  `~/xs-campaigns/2026-11-10-proof/PILOT_BRIEF.md`; outputs `~/xs-campaigns/2026-11-10-proof/pilot/`).

Status (22:02 UTC 2026-11-10): pilot agent running; independent review and final report not started.

## 3. Decisions and their reasons

- Published circuits by cherry-picking the sprint's own harvest commits onto main (keeps their
  provenance) plus one README commit, pushed directly (the repository has no branch protection
  and the owner's history is direct commits to main).
- Stall timers in v8 are wall-clock (`restart.stall_seconds`, `root_seconds`); for an
  oversubscribed A/B the per-trajectory policy must be in proposals (`stall_proposals`) or the
  300-worker arm restarts 15x earlier in CPU terms.
- Step 5 (17:20 UTC 2026-11-09, before the A/B result): the "foundation restart" source was chosen
  from the 2026-11-02 foundations study (design data) and evaluated on B1-B3 (evaluation data).
- 2026-11-10: the enumeration proposed in REPORT section 6 ("A >= 2 hub configurations behind the 229
  keys") does not cover the remaining problem (119 claims would survive it); the scope is revised
  before any substantial compute (section 2).

## 4. Historical log (superseded; kept verbatim from the entries written while work was running)

<details>
<summary>Entries from 2026-11-09, as written at the time</summary>

### 4.1 "Running / in progress" entries (all finished; results in section 1)

- Proof reconciliation audit agent (xhigh), started 15:17 UTC, writing
  `~/xs-campaigns/2026-11-09-phase/recon/REPORT.md`: audit of the October push5/push6 rows'
  necessity, same-universe check against the sprint's qcert4 system, combined LP scan (sprint
  rows + validated push rows) at G = 75. Known overlap: push5's 3 N3 + q <= x + y is the
  sprint's N1. Known caveat: push5 Mt "exceptional label" rows use q_eff = q - 1 / q - 2.
  [superseded: done 15:55 UTC, confirmed by recon-check 16:45 UTC, published 17:05 UTC]
- Worker-count feasibility: `workers/feas300` (300 workers, 8 min) then `feas20`, hunt-A
  configuration, 15:18 UTC. Early: 303 processes, RSS 8.2-8.5 GB total (~27 MB each), load 230.
  Analysis: `workers/throughput.py RUN_DIR`. [superseded: cost curve in section 4.2]
- Packaging agent (opus) done 15:57 UTC: `lower-bound-proofs/mixcolumns-lb75-open-cases/` (README,
  PROVENANCE, 4 addenda, 4 certificate files, 5 checkers with one path edit each, verify_all.py 8.9 s,
  SHA256SUMS; proofs.yml and lower-bound-proofs/README.md edited). UNCOMMITTED; the README's section
  on the October campaigns is a placeholder until the recon re-check lands.
  [superseded: committed and pushed as 185c0cd / 400ad09]
- A/B trial 1 launched 15:57 UTC (`chain1.sh` -> `ab_driver.sh 1 20261109 ab20 ab300`; ends ~18:00 UTC): `ab20.toml` vs `ab300.toml`, 60 min each, same campaign seed per
  trial (the 20 roots are the first 20 of the 300), restart policy in PROPOSALS (stall 1.8 M
  proposals = v8's 900 s at the measured ~2,000 proposals/s per full-speed worker; incumbent
  factor 2; root_seconds disabled in both arms). Outcomes: per-trajectory time to 88 and success
  within budget (`hunt/descents.py`), arrivals at 88 per wall-hour and per CPU-hour
  (`throughput.py`), distinct 88 signatures (`sigs_ab.py`), memory and load (`*.mem.log`).
  [superseded: both trials done; REPORT section 4]
- "The sprint branch is not pushed yet: it will be pushed with the proof update."
  [superseded: pushed 17:05 UTC]

### 4.2 "Done" entries of 2026-11-09 (kept for the record)

- 15:11 UTC: circuit harvest PUBLISHED on `main` and pushed (726f8d3 harvest, 1508e40 harvest
  fix, f948f19 SEARCH-TIME row, 71184a9 README). 44 circuits added, 37 dominated removed, 208
  circuits; `circuits/check.py` 208/208, test suite 358 OK; CI run 42642167215 green. Checked
  before publishing: provenance files of all 44 adds, no dominated pair in the collection, the
  fixed harvest script proposes nothing further over all 20 sprint run directories (hunts A-D,
  kste, translog included), NIST-beating map set unchanged (46 of 53). Twelve maps have a new
  any-depth minimum (see the README commit message); the rest are depth-limited improvements.
- 15:17-15:55 UTC: reconciliation audit (xhigh agent, `~/xs-campaigns/2026-11-09-phase/recon/REPORT.md`,
  `ROW_INVENTORY.md`): push5/push6 and the sprint use the same domain (3,708 states / 7,416 claims),
  key convention, type columns and package base rows (the missing archive `certify75.py` is the
  package's, by sha256). All 8 push5 rows and the push6 resource/budget/divisor rows have written
  necessity proofs the agent followed without finding a gap; finite facts behind R1-R6/D/P5.2-P5.4
  recomputed with its own code, F1/F2/F3/F5 only replayed via the archive's root audits (PASS). Only
  shared row: N1 = push5's P5.3. Combined LP scan: sprint-only 686 (reproduced), push-only 509
  (reproduced, identical (k,l)), intersection 419, COMBINED 280 open claims (148 M / 132 Mt) [measured];
  406 new exclusions CERTIFIED (4,653 exact certificates, two matrix constructions, J1-free). F1-free
  subset of push rows: 581. Independent re-check commissioned 16:00 UTC (`recon-check/`). Bound: 75.
- Worker-count cost curve [measured, hunt-A config, 8 min each, window 120-460 s]: 20 workers 28,100
  proposals/s (1,429 per CPU-s); 100 workers 25,500 (1,272; -10 %); 300 workers 13,700 (758; -47 %).
  RSS ~27-30 MB per worker. So 100 trajectories are nearly free, 300 cost half the compute.
- 16:00-16:45 UTC: independent re-check of the reconciliation (xhigh agent, `recon-check/REPORT.md`):
  from-scratch stdlib checker passes on all 4,653 + 43 certificates; own LP scan reproduces 686 / 509 /
  280 with identical survivor sets; proofs of P5.2-P5.8, R1-R3, (T)/B3-B5, B6, R6/D followed, no gap,
  no coding mismatch; finite facts F1, F2, F3, F5 and the census facts recomputed with own code (55 s);
  0 violations on 1,264 phases.
- ~17:05 UTC: proof update PUBLISHED on `main` and pushed (185c0cd: folder
  `lower-bound-proofs/mixcolumns-lb75-open-cases/` with addenda A-D, 4 + 2 certificate files, 6
  checkers, the October row proofs verbatim with provenance, verify_all.py ~85 s, proofs.yml step;
  400ad09: top-level README pointer). Branches `sprint-2026-11-07-linear-maps` and `phase-2026-11-09`
  pushed to origin. Bound stays 75; 280 open claims (LP status) with all validated rows combined.
- 18:03-21:05 UTC: A/B trial 2 (20 / 100 / 300). 21:07-23:08 UTC: foundation benchmark B1-B3.
  Phase closed 23:20 UTC; nothing running.

### 4.3 Worker-count A/B, trial 1 (seed 20261109, 60 min per arm, MixColumns uncapped, fresh roots,
no sharing, restart policy in proposals: stall 1.8 M, incumbent x2, root budget off) [measured]

| arm | aggregate proposals/s (per CPU-s) | chains | reached 88 | first 88 (wall s): min / median over successful trajectories | 88 arrivals per CPU-hour | g88 records / distinct recorded signatures | memory |
|---|---:|---:|---:|---|---:|---:|---|
| 20 workers | 31,400 (1,597) | 35 (15 restarted) | 23 | 77 / 632 (from root) | 1.15 | 222 / 94 | 0.7 GB |
| 300 workers | 22,700 (1,160) | 300 (0 restarted) | 54 | 673 / 2,316 | 2.7 | 234 / 93 | 8.9 GB |

Reading at the time (corrected wording): 300 trajectories cost 28 % of the throughput, delayed the
first 88 by 9x and the median successful trajectory by 3.7x, produced 2.3x more ARRIVALS at 88 per
wall-hour, and the same number of distinct recorded 88 signatures per wall-hour (93 vs 94; 0 shared).
The extra arrivals coincide with the restart-policy effect (F6); exact plateaus were not computed.
Trial 2 (seed 20261110, arms 20 / 100 / 300) confirmed the pattern (REPORT section 4).

### 4.4 Step 5 decision (17:20 UTC, before the A/B result) and benchmark plan, as written

Intervention: a "foundation restart" source in v8 (knob `restart.w_foundation`, default 0 = no
change): at a restart take the worker best or an archive elite, keep its level-1 set (weight-2
values), optionally swap k pairs for useful pairs, rebuild everything above it with the constructors
under the restriction, run the new chain PINNED (no new weight-2 value outside the set) for a fixed
number of proposals, then unpin. Mechanism it targets: the walk changes level 1 one pair at a time
and cannot cross the steep landscape between foundations (2026-11-02-why foundations §3-§5), while
the upper structure above a good foundation is cheap to rebuild (pinned completion re-finds 89@4 in
minutes from its foundation [this figure came from the 2026-11-02 prototype; it was never re-measured
with the engine's restricted constructor and pin budget]). Implementation agent (opus) started
17:20 UTC; evaluation after the A/B frees the machine (~21:10 UTC):
- B1 hard diagnostic: cap-4 MixColumns from ~10 recorded 90@4 states with DIFFERENT first layers
  (the 89's layer is never supplied; swaps are random), 1 worker each, 30 min, foundation on vs off;
  success = any 89@4 within budget, time to target.
- B2 calibration: MixColumns uncapped from fresh roots, time to 88 per chain, 6 workers x 40 min per arm.
- B3 transfer: InvMixColumns cap 5 from our 168@5 (level to reach within 40 min; 6 workers per arm);
  the foundation finding did not transfer cleanly to InvMC in the why campaign, so this is a real test.
Design data (used to choose the change) = the 2026-11-02 foundations study; evaluation data = B1-B3.
- 18:40 UTC: implemented and COMMITTED on this branch (8e544ba; default path byte-identical by
  fixed-seed digest; 13 new tests, suite 371 OK; notes in `foundation-restart/IMPLEMENTATION.md`).
  Not on main. Limitation: only the `l1tree` restricted constructor completes in practice
  (paar/naive/bp fail under the restriction); roots over a 90@4 foundation are 110-112@4.
- Benchmark queued (`~/xs-campaigns/2026-11-09-phase/foundation/chain3.sh`, starts when
  `workers/AB_DONE_t2` appears, ~21:12 UTC; log `foundation/chain3.log`, runs in `foundation/runs/`):
  phase A b1_base (12 x 30 min) + b2_base (6 x 40 min); phase B b1_found + b2_found; phase C
  b3_base + b3_found (6 + 6 x 40 min). Common timers per benchmark: B1/B3 stall 300 s, incumbent 1
  (both arms); B2 v8 timers. Foundation arms: B1/B3 every restart is a foundation restart
  (swap_pairs 2, pin 150,000 proposals); B2 w_fresh 0.5 / w_foundation 0.5. Analysis:
  `hunt/descents.py` on `foundation/runs` (time to 89 at cap 4; to 88 uncapped; InvMC levels),
  `xorflux status`, the `foundation_unpin` / `foundation_failed` events.
  [superseded: results in REPORT section 5 as corrected]

### 4.5 "Open" entries of 2026-11-09 (all resolved)

- Proof publication layout (after the audit) [resolved: 185c0cd].
- The search intervention (step 5) is chosen after the worker experiment [resolved: foundation
  restart, section 1].

</details>
