# Brief: ten targeted campaigns against NIST AES S-box circuits (+ the 27-AND objective)

Coordinator: the main session. Start 2026-11-15 ~15:30 UTC. Final report to the coordinator by
**23:30 UTC**; all your CPU jobs stopped by **23:45 UTC** unless queued (see "Overnight queue").
Rules, shell, memory safety, verification and evidence labels: read
`~/xs-campaigns/2026-11-15-study/BRIEF-COMMON.md` sections "Project and rules" — everything there
holds (LOCAL ONLY, never push, never commit (coordinator commits), never touch other branches;
`wsl.exe -e bash -lc`; every computation over a few seconds through `~/xs-campaigns/guard/xsrun` or
`xsfg`; never `pkill -f`). Ignore its schedule and CPU map; this file replaces them.
Use TRACK `P` for target campaigns and `Z` for the 27-AND agent (units `xs-P-<ID>-<name>`).

The machine-readable spec is `~/xs-campaigns/2026-11-15-targets/TARGETS.json` (targets, hard limits,
definitions, the archive baseline at 15:20 UTC). The user's own words are in `USER-REQUEST.md` here.

## Non-negotiable
- For every target, **A <= reference A and AD <= reference AD** on every retained search state and
  every recorded result. These are hard constraints, never objectives to trade. Run every engine
  with caps that enforce them (`fdrive.py --cap-a A --cap-ad AD --cap GD`, hub `--caps`, kernel caps).
- G and GD trade only as the target allows. Two separate result classes:
  - **strict**: G <= ref G and GD <= ref GD, at least one strictly better;
  - **tradeoff**: a permitted move (TARGETS.json `tradeoffs`): a substantial gain (>= 3 gates, or
    >= 1 GD level) for a small permitted cost (<= 2 extra GD levels where allowed; <= 8 extra gates
    for a depth gain where allowed). Never describe a tradeoff as dominating the reference.
- Depth-first targets (T02, T06, T08, T09, T10): reduce depth without adding gates first; record
  depth-vs-gates tradeoffs separately.
- NIST library {AND, XOR, XNOR, NOT}, NIST counting. Every saved circuit verified with
  `python3 nonlinear/boolflux/campaigns/aes_check.py FILE` (two independent verifiers, all 256 inputs).
- Keep the full Pareto frontier per target, not one winner.

## What to save (for every verified circuit)
`~/xs-campaigns/2026-11-15-targets/<ID>/found/<name>.circ.txt` plus `<name>.json` with: `target`
(T01..T10, or Z), `A AD G GD`, `start` (absolute path + sha256 of the start file), `method` (engine,
mode, operator chain), `command` (exact, absolute paths), `seed`, `elapsed_s`, `code` (git sha of
`~/xcr-boolflux` + sha256 of any kernel binary used), `aes_check` (its OK line), `utc`.
Keep logs, configs and failed runs under `~/xs-campaigns/2026-11-15-targets/<ID>/runs/`. Keep
`nonlinear/boolflux/strategies/<ID>/NOTES.md` (methods, results, failures, [C]/[H] labels) and
`STATUS.md` (what runs now, best strict / best tradeoff per target) current.

## Agents and CPUs (one busy process per CPU)
| ID | targets | CPUs now | CPUs from ~18:30 UTC |
|---|---|---|---|
| L0 | ledger, verification, documentation (no search) | short xsfg jobs on 1 | same |
| P1 | T01, T03 (A28 gate count) | 10, 11 | + 0 |
| P2 | T02, T06 (depth-first, AD4) | 12, 13 | same |
| P3 | T04 (A32/AD4/G117/GD19) | 14 | + 3 |
| P4 | T05 gate record: G < 103 at A<=32, AD<=7, GD<=32 | 15 | + 7, 8 |
| P5 | T05 AND depth: AD 6/5/4 at A<=32, G near 103 | 16 | + 9 |
| P6 | T07, T08 (AD3) | 17, 2 | same |
| P7 | T09, T10 (high A, very low depth) | 18, 19 | same |
| Z1 | 27 ANDs (main objective) | 1 | + 4, 5, 6 |
CPUs 0 and 3-9 run the 27-AND exact searches (H1, H2, H3, X1b, X3b) until their 705-minute
timeouts end (~18:30 UTC); check `~/xs-campaigns/guard/xsps` before using an added CPU.

## Starting material
- References: `~/xcr-boolflux/nonlinear/nist/aes-sbox/<ref>` (pinned 3d80774).
- Our archive: `~/xs-campaigns/2026-11-15-study/best-1400/` (best per tuple, BEST.json),
  `~/xs-campaigns/2026-11-14-hub/long/archive/*.bfx` (about 15k circuits incl. near-frontier, front.json),
  `nonlinear/boolflux/results/aes/` (curated), study `found/` folders. Any archive circuit within a
  target's hard limits is a legal start. Already-known strict improvements (T01, T02, T06, T08) are
  the bar to beat, not results of this campaign.
- Engines: `strategies/F/fdrive.py` (modes gate | osc | trb | mix; `--cap GD --cap-ad --cap-a`),
  an example wrapper in `~/xs-campaigns/2026-11-15-study/T4/queue/polish_job.sh`; the hub
  (`hub/SPEC.md`, `hub/scheduler.py`, tuple caps, `--cap-renew box`); kernel at
  `~/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5`. Earlier notes on what worked:
  `strategies/L1/`, `strategies/T1..T4/NOTES.md`, `HOW-IT-WORKS.md`, `HISTORY.md`.
- Value order inside a target, after its hard limits: the target's own priorities first.
  Across the project: 27 ANDs is still the main objective.

## Reporting
Message the coordinator only for a real result (a verified strict improvement, a permitted tradeoff
that is new, a 27-AND circuit, a decisive negative) and the final report. Short, with numbers and
file paths. A new verified circuit with A <= 27 is reported immediately.

## Overnight queue
Long unattended runs that should continue after 23:45: append a self-contained spec to
`~/xs-campaigns/2026-11-15-targets/QUEUE.md` (ID, target, exact command, CPUs, run length, memory,
where verified results land, how to judge success).
