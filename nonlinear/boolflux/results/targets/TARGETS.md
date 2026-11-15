# Ten targeted campaigns against NIST AES S-box circuits (2026-11-15)

Skeleton (L0, 2026-11-15). Each section says what it will hold and where the material comes
from; the coordinator fills it at the end of the campaign. Section order follows XORFlux's
README / HISTORY / SEARCH-TIME pages.

## 1. The request
The user's request of 2026-11-15 ~15:10 UTC, verbatim
(`~/xs-campaigns/2026-11-15-targets/USER-REQUEST.md`), and TARGETS.json as run (with any later
change of `min_gate_gain_for_depth_cost` / `max_gate_cost_for_depth_gain` and when it was made).

## 2. Rules and definitions
Hard limits, strict, tradeoff kinds with their exact inequalities, frontier, provenance
(known / reproduced / new, baseline cut-off 2026-11-15 15:20 UTC). Source: campaigns/targets/README.md.

## 3. Results
One table per target T01..T10 (and Z), generated from the final LEDGER.json:

| A/AD/G/GD | class | vs ref dG / dGD | status | pinned NIST dominating | file | found by | start | seed | found after |
|---|---|---|---|---|---|---|---|---|---|

followed by: the pinned (G, GD) frontier within the same hard limits, the best strict and best
tradeoff in one sentence each, and for T05 the per-AND-depth table (AD 7..3: best G then GD).
A line on A <= 27 (the main objective) with the Z agent's outcome.

## 4. How each result was found
Per target: engine, mode, operator chain, caps, starts tried, CPU time spent; links to
`strategies/<agent>/NOTES.md` and to each circuit's `logs/<name>/REPRODUCE.md`.

## 5. Failed experiments and dead ends
Every run that found nothing, per agent, with its command, length and what it showed
(`~/xs-campaigns/2026-11-15-targets/<agent>/runs/`, NOTES.md). Decisive negatives with their
[C]/[H] label and the exact case a [C] covers.

## 6. Verification
aes_check.py on every file (two verifiers, 256 inputs); ledger re-check; sidecar audit
(issues found and how they were resolved); NIST pin integrity (manifest sha256).

## 7. Compute and hardware
Per agent: CPUs, wall time, CPU time; the machine table (as XORFlux circuits/SEARCH-TIME.md);
the clock caveat for WSL2.

## 8. Reproduction
Which results are deterministic commands, deterministic constructions, reproduced, or one-off
(VERIFICATION.md section 6 vocabulary); how to re-run each.
