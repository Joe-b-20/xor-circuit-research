# Brief, phase 2 (2026-11-16 00:00 UTC): improve the method, run overnight, get ready for main

Read first: `BRIEF.md` (this folder; rules on shell, memory safety (xsrun/xsfg), verification,
saving, sidecars, reporting still hold), `TARGETS.json` (updated 23:50 UTC), `USER-REQUEST.md`,
and the agents' notes `nonlinear/boolflux/strategies/P1..P7/NOTES.md`. LOCAL ONLY: never push, never
commit (the coordinator commits), never touch other branches. Linux via `wsl.exe -e bash -lc`, scripts
written to files. Never `pkill -f`/`pgrep -f`.

## User decisions at 23:50 UTC (authoritative)
1. **No 27-AND work** of any kind until the user says otherwise.
2. **Search states may exceed caps.** The optimiser may go above the A, AD, G and GD limits during a
   search as long as it comes back and the RECORDED result is inside the target's hard limits
   (A <= ref A, AD <= ref AD) and better. `repair_keep` is a tuning option, not a rule; path
   certification is informational only.
3. **Improve the method before launching anything new**, using the logs and what was learned today.
4. T03 and T05 may trade depth for gates (TARGETS.json: T03 gates_for_depth GD <= 22 with >= 3 gates
   saved, and also report any G <= 123 at any GD; T05 any G <= 102 at any GD is a new overall record).
5. Overnight runs: **one target at a time with all 20 CPUs** (sequential blocks), not-yet-improved
   targets first, then improved ones. **All runs stop by 13:30 UTC** (08:30 Eastern).
6. The branch must be **ready to push to main by 14:00 UTC** (09:00 Eastern): clean, documented,
   verified. The coordinator asks the user before any push.

## What worked today (the facts to build on; details in strategies/P*/NOTES.md)
- P3 (T04 117->114@19, 115@18, 113@20) and P6 (T07 139->138@24): GF(2^8) conjugation of a start
  (inputs x -> lam*x^(2^k), matching affine output map; AND structure unchanged; P3 conj.py/conj3.py
  screen + mkconj.py), then STAGED kernel pulls: loose GD cap (24-31) gate mode, then mix at
  tighter caps one or two levels at a time. Lineages take 15-40 CPU-min and plateau; 7 lineages all
  stopped at 113@20/114@19.
- P6 (T08 183->181@12, 168@13): exact re-basing of the three level-3 GF(4) classes (botbasis.py),
  depth-feasible hybrid rebuild (hybrid.py), GF(4) coordinate moves priced by the re-basing depth
  bound (l3scan.py), then capped kernel.
- P7 (T09 141->136@12): keep the NIST front, rebuild the bottom as shared rank-1 products
  (bopt.py annealing with an exact per-output depth check, bbuild.py), then A-capped polish.
- P1 (T03 129@19): span-pooled SAT LNS (unionsat2.py), productive in "sideways" mode.
- P4/P5: exact negatives for T05 inside the 103's own layout (NEGATIVES.md); T10 rigid in the 59@10
  layout (P7 NOTES s.4); T02 GD13 and T06 GD12 need new AND functions (P2 NOTES).

## Agents and CPUs, 00:00-02:45 UTC (tests only; one busy process per CPU)
| ID | job | CPUs |
|---|---|---|
| M1 | log analysis -> settings for the night | 17 (short jobs) |
| M2 | general conjugate + staged-pull pipeline, and the sequential overnight runner | 0-7 |
| M3 | re-basing (P6) and shared-bottom rebuild (P7) as general operators | 8-12 |
| M4 | SAT LNS (P1) as a general operator | 13-16 |
| L1 | ledger update for the new rules; the morning one-command curation/verification | 18 (short) |
| D1 | documentation for main | none |
| D2 | repository cleanup and merge plan for main | 19 (tests) |
Reports to the coordinator by **02:45 UTC** (M1-M4, L1), D1/D2 by **12:30 UTC** with an interim at 02:45.

## Operator contract (M2, M3, M4 must all implement it, so the runner can mix them)
`python3 nonlinear/boolflux/campaigns/targets/ops/<name>.py --in START.circ.txt --target Txx
 --seed S --seconds T --out DIR [--cpus 1] [op-specific flags]`
- reads limits from TARGETS.json for Txx; may exceed caps internally; writes to DIR only circuits
  that pass aes_check AND are inside the target's hard limits (A, AD), as `<name>-a..-ad..-g..-gd..-<hash>.circ.txt`
  with a full sidecar (BRIEF.md fields + `op`, `params`, `parent` file + sha256);
- writes DIR/result.json (best per (G, GD), wall time, exit status); exits within T + 60 s;
- one CPU per process unless --cpus; memory under 2 GB (runs under xsrun with XS_MEM).
Code goes in `nonlinear/boolflux/campaigns/targets/ops/` (one file per operator, plus shared helpers
in `ops/common.py`, owned by M2: M3/M4 may add helpers in their own files). Copy from strategies/P*;
do not edit other agents' strategies folders.
