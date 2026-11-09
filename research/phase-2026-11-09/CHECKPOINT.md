# Phase 2026-11-09: living checkpoint

Conservative post-sprint phase (main agent Fable 5.1, from 2026-11-09 ~14:30 UTC). Branch
`phase-2026-11-09` (sprint tip + main). The sprint branch `sprint-2026-11-07-linear-maps` is
untouched (tag `sprint-2026-11-07-final` = 882c962). Scripts and run data for this phase:
`~/xs-campaigns/2026-11-09-phase/`. Order of work set by the owner: publish circuits, reconcile
and publish the proof state, test the many-workers hypothesis, one evidence-driven search change.
Evidence tags as in the sprint: [proved] [checked] [measured] [cited] [guess].

## 1. Done

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

## 2. Running / in progress

- Proof reconciliation audit agent (xhigh), started 15:17 UTC, writing
  `~/xs-campaigns/2026-11-09-phase/recon/REPORT.md`: audit of the October push5/push6 rows'
  necessity, same-universe check against the sprint's qcert4 system, combined LP scan (sprint
  rows + validated push rows) at G = 75. Known overlap: push5's 3 N3 + q <= x + y is the
  sprint's N1. Known caveat: push5 Mt "exceptional label" rows use q_eff = q - 1 / q - 2.
- Worker-count feasibility: `workers/feas300` (300 workers, 8 min) then `feas20`, hunt-A
  configuration, 15:18 UTC. Early: 303 processes, RSS 8.2-8.5 GB total (~27 MB each), load 230.
  Analysis: `workers/throughput.py RUN_DIR`.
- Packaging agent (opus) done 15:57 UTC: `lower-bound-proofs/mixcolumns-lb75-open-cases/` (README,
  PROVENANCE, 4 addenda, 4 certificate files, 5 checkers with one path edit each, verify_all.py 8.9 s,
  SHA256SUMS; proofs.yml and lower-bound-proofs/README.md edited). UNCOMMITTED; the README's section
  on the October campaigns is a placeholder until the recon re-check lands.
- A/B trial 1 launched 15:57 UTC (`chain1.sh` -> `ab_driver.sh 1 20261109 ab20 ab300`; ends ~18:00 UTC): `ab20.toml` vs `ab300.toml`, 60 min each, same campaign seed per
  trial (the 20 roots are the first 20 of the 300), restart policy in PROPOSALS (stall 1.8 M
  proposals = v8's 900 s at the measured ~2,000 proposals/s per full-speed worker; incumbent
  factor 2; root_seconds disabled in both arms). Outcomes: per-trajectory time to 88 and success
  within budget (`hunt/descents.py`), arrivals at 88 per wall-hour and per CPU-hour
  (`throughput.py`), distinct 88 signatures (`sigs_ab.py`), memory and load (`*.mem.log`).

## 3. Decisions and their reasons

- Published circuits by cherry-picking the sprint's own harvest commits onto main (keeps their
  provenance) plus one README commit, pushed directly (the repository has no branch protection
  and the owner's history is direct commits to main).
- The sprint branch is not pushed yet: it will be pushed with the proof update, whose
  certificates and checkers live in `research/sprint-2026-11-07/experiments/`.
- Stall timers in v8 are wall-clock (`restart.stall_seconds`, `root_seconds`); for an
  oversubscribed A/B the per-trajectory policy must be in proposals (`stall_proposals`) or the
  300-worker arm restarts 15x earlier in CPU terms.

## 3a. Worker-count A/B, trial 1 (seed 20261109, 60 min per arm, MixColumns uncapped, fresh roots,
no sharing, restart policy in proposals: stall 1.8 M, incumbent x2, root budget off) [measured]

| arm | aggregate proposals/s (per CPU-s) | chains | reached 88 | first 88 (wall s): min / median | 88 arrivals per CPU-hour | g88 records / distinct signatures | memory |
|---|---:|---:|---:|---|---:|---:|---|
| 20 workers | 31,400 (1,597) | 35 (15 restarted) | 23 | 77 / 632 (from root) | 1.15 | 222 / 94 | 0.7 GB |
| 300 workers | 22,700 (1,160) | 300 (0 restarted) | 54 | 673 / 2,316 | 2.7 | 234 / 93 | 8.9 GB |

Reading: 300 trajectories cost 28 % of the throughput, delayed the first 88 by 9x and the median
trajectory by 3.7x, produced 2.3x more ARRIVALS at 88 per wall-hour (its trajectories never reach
the post-arrival stall period, which the 20 arm spends hopping between 88 plateaus through 89), and
exactly the same number of distinct 88 plateau signatures per wall-hour (93 vs 94; 0 shared). So the
extra arrivals are the restart-policy effect in disguise (F6), not more exploration. No 87 in either
arm. Trial 2 (seed 20261110, arms 20 / 100 / 300) runs 18:02-21:10 UTC to check this holds.

## 3b. Step 5 decision (17:20 UTC, before the A/B result; revisit if the A/B wins convincingly)

Intervention: a "foundation restart" source in v8 (knob `restart.w_foundation`, default 0 = no
change): at a restart take the worker best or an archive elite, keep its level-1 set (weight-2
values), optionally swap k pairs for useful pairs, rebuild everything above it with the constructors
under the restriction, run the new chain PINNED (no new weight-2 value outside the set) for a fixed
number of proposals, then unpin. Mechanism it targets: the walk changes level 1 one pair at a time
and cannot cross the steep landscape between foundations (2026-11-02-why foundations §3-§5), while
the upper structure above a good foundation is cheap to rebuild (pinned completion re-finds 89@4 in
minutes from its foundation). It keeps the configuration that made an elite good and discards the
unproductive upper walk instead of restarting from scratch. Implementation agent (opus) started
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

## 4. Open

- Proof publication layout (after the audit): a self-contained extension folder under
  `lower-bound-proofs/` with the four addenda, the certificates (about 4.4 MB of JSON), the
  independent checkers made self-contained (they currently import from `~/xs-campaigns`), a
  `verify` wrapper, and a human-readable account of the combined state; CI `proofs.yml` runs on
  changes under `lower-bound-proofs/`.
- The search intervention (step 5) is chosen after the worker experiment; candidates from the
  evidence: foundation (level-1) macro-moves with pinned re-completion (2026-11-02-why
  foundations), a dead-room check replacing the blind stall timer (why/seeds), a shelf lineage
  one gate behind (v9c).
