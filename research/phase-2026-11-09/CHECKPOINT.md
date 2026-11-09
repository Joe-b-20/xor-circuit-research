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

## 2. Running / in progress

- Proof reconciliation audit agent (xhigh), started 15:17 UTC, writing
  `~/xs-campaigns/2026-11-09-phase/recon/REPORT.md`: audit of the October push5/push6 rows'
  necessity, same-universe check against the sprint's qcert4 system, combined LP scan (sprint
  rows + validated push rows) at G = 75. Known overlap: push5's 3 N3 + q <= x + y is the
  sprint's N1. Known caveat: push5 Mt "exceptional label" rows use q_eff = q - 1 / q - 2.
- Worker-count feasibility: `workers/feas300` (300 workers, 8 min) then `feas20`, hunt-A
  configuration, 15:18 UTC. Early: 303 processes, RSS 8.2-8.5 GB total (~27 MB each), load 230.
  Analysis: `workers/throughput.py RUN_DIR`.
- Planned A/B (not launched): `ab20.toml` vs `ab300.toml`, 60 min each, same campaign seed per
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
