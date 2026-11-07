# Sprint 2026-11-07: linear maps and the XORFlux search (shared brief for agents)

Owner: the main session (Claude). Started 2026-11-07 03:30 UTC. Hard stop: 2026-11-08 ~06:00 UTC.

## Goal of the sprint
1. A deeper, evidence-backed understanding of linear maps and how our search behaves on them:
   where it succeeds and why, where it fails, where it stalls, what makes it slow, what decides
   whether it can reach better circuits.
2. Use that to make the search faster and more effective per unit of compute.
3. The record target: a verified 87-XOR (or better) circuit for forward AES MixColumns, any depth.

## Where things are
- Repository: `~/xor-circuit-research` (WSL Ubuntu). Branch `sprint-2026-11-07-linear-maps`.
  Baseline search = v8 in `search/xorflux` (`python3 search/xorflux quick MAP --seconds N --seed S`,
  `python3 search/xorflux run FILE.toml --out DIR`; docs in `search/USAGE.md`, `search/HOW-IT-WORKS.md`,
  `search/xorflux/DESIGN.md`). Maps: `circuits/<map>/<map>.mat.txt` (59 maps); a path to any
  `.mat.txt` works as a target. Circuits + NIST comparison: `circuits/README.md`,
  `circuits/SEARCH-TIME.md`. History of everything tried: `search/HISTORY.md`.
- Prototypes (outside the repo): `~/xs-campaigns/v9-proto` (v9a..v9f knobs: adopt, shelf, room,
  escalate, star, telemetry chain samples), `~/xs-campaigns/v10-proto` (CPU-waste cuts). Read-only.
- Prior studies (read for context, do not rerun blindly): `~/xs-campaigns/2026-11-02-why/SYNTHESIS.md`,
  `~/xs-campaigns/2026-11-03-waits/SYNTHESIS.md`, `~/xs-campaigns/2026-11-05-visual/SYNTHESIS.md`
  (plateaus are exact products of independent 3-way choices), `~/xs-campaigns/2026-11-05-exit/REPORT.txt`
  (plateau exit search), `~/xs-campaigns/2026-11-05-visual/groundtruth/` (exact SAT enumeration of
  small analogues; `gt_core.py` has the SAT encoder on pysat/CaDiCaL).
- Sprint folder: `~/xs-campaigns/2026-11-07-sprint/`. Each agent works ONLY in its own subfolder
  there and writes `REPORT.txt` (plain text) plus scripts and data. Nothing is written in the repo.

## Rules
- Environment: you run on Windows; WSL is reached with `wsl.exe -d ubuntu -- bash -lc '...'`.
  Put any non-trivial shell logic or Python in files inside your folder (write them with the Write
  tool to `\\wsl.localhost\ubuntu\home\joebachir20\xs-campaigns\2026-11-07-sprint\<you>\...`) and
  run them by path; `$var` expansions in a wsl.exe one-liner are unreliable. Use LF line endings.
  Python 3.12, numpy, pysat (CaDiCaL/Glucose) are available in WSL. No internet installs needed.
- CPU: the machine has 20 threads. A 12-worker MixColumns hunt runs concurrently (do not touch
  `~/xs-campaigns/2026-11-07-sprint/hunt`). Stay within your core budget, run heavy work at
  `nice -n 10`, never kill processes you did not start.
- Evidence tags on every claim: [proved] (argument given), [checked] (exact computation, script
  named), [measured] (run data, script named), [cited] (source), [guess].
- Keep four things apart: a property of the MAP, a property of the current CIRCUIT, a property of
  the SEARCH PROCEDURE, a limitation of the IMPLEMENTATION. Evidence about one is not evidence
  about another.
- For each major explanation: (1) the observation it explains, (2) the mechanism in plain words,
  (3) a prediction that could be wrong, (4) the test on fresh evidence, (5) what survived and the
  limits. Beware hindsight: a feature that "explains" a success after the fact is not a predictor
  unless it was fixed before the outcome was known.
- Report numbers in small tables; be concrete; name the script that produced every number.
- Finish with: findings, rejected explanations, open questions, and the next experiment you would
  run and why.
