# L2 notes (log analyst, pre-hub era; 2026-11-15)

Deliverables: `WHAT-WORKED-BEFORE.md`, `DOC-AUDIT.md`. This file records method, the checks I
ran, and what went wrong on my side. Data and outputs: `~/xs-campaigns/2026-11-15-study/L2/`.

## Method

1. Read the briefs, README, HOW-IT-WORKS, HISTORY, bench/REPORT, runs/, DOCS-TODO, CHECKPOINT,
   the NOTES of tracks C, D (README), E, F, G, the campaign STATUS files, and the status files
   of H1-H4, R1-R2, T1, T2 (not edited).
2. Recounted from records instead of copying the notes:
   - `m3.py`, `m4.py`: every AES manifest entry (86): sha256 of the file, existence of the run
     record, caps against metrics, mechanism classes, provenance gaps.
   - `e2.py`: lineage of all 61 admissions of track E long1 / low1 from `admitted/*.json`
     (output `e2.out`); `e3.py`: polish and pull job yields per AND class.
   - `s1.py`: the sp1 join sweep (24,443 results) by AND count and parent pair.
   - `p1.py`: the pinned set through `aes_check.published()`, the 41-tuple count, goal table.
   - `strategies/E/analyze_stages.py` on the pinned set (`stages.out`) and on the pre-hub
     low-AND results.
   - Track D window counts from `D/t1..t4/*/log.jsonl`; track C sweep state from `C/logs`.
3. Three checks with short jobs on CPU 12 (below).

## Checks

### 1. Paired cap probe (goal E recipe) [C, n = 3 per arm]
`probeE.sh`: `erun.py` from N:a32-ad5-g107-gd22, 100 s, seeds 1-3, caps AD <= 6 and GD <= 31,
cap A31 (unreachable) against cap A32. Both arms reach 106 in 3 of 3 runs; seeds 1 and 3 follow
the same path in both arms. So the unmet A31 cap of the 2026-11-14 job is not what produced
32/5/104/29; the released depth cap is. Table in WHAT-WORKED-BEFORE.md section 6.

### 2. Re-run of recorded joins [C]
`rejoin.py`: the first A31 join (sp1) and all 29 join admissions of long1 and low1, rebuilt from
the recorded parents and cut levels with `strategies/E/splice2.py` at f9fe6f7: 30 of 30 identical
kernel text. The manifest's "deterministic construction ... not re-run" entries can now say
"re-run 2026-11-15, identical".

### 3. The "deterministic command" behind 28/4/133/20
(a) [C] Today's code. `cli.py run --target aes --model nist --start nonlinear/nist/aes-sbox/
aes-sbox-a28-ad4-g134-gd20-xx106-41.circ.txt --objective cost,gd --cap-a 28 --cap-ad 4 --cap-gd 20
--iters 100000 --seeds 5 --jobs 1` at f9fe6f7 (code 91246b4809fd, kernel seed 5): ends its
100,000 iterations at 134 gates, no improvement (`det1/`). The 2026-11-13 run with code
b0e56ecb18fe reached 133 at iteration 56,529. The command alone does not reproduce the result.
(b) [C] The run's own binary (`frontier-fwd-3/.../bin/bfx`) with a copy of its cfg, only the
in / out paths changed (`det_old.sh`, output `det_old/`): 133 at iteration 56,529 again, and the
final `r0-s5.best.bfx` is byte-identical to the stored one. (c) [C] Today's code with `--set skip_noop=0` added to the command of (a) (`det3/`): 133 at
iteration 56,529, gate list and outputs identical to the stored circuit (the .bfx files differ
only in the number format of the final comment line). So the result is deterministic; what
breaks the replay under today's defaults is the no-op filter (default since 7ae20c8), as
USAGE.md says for the 108 replay. The manifest's wording ("the command gives the same
circuit") needs "with `--set skip_noop=0` on later code, or with the run's snapshot".
I ran (c) only after first reporting (a) and (b) as "not reproducible with later code"; that
first wording was too strong and is corrected in all files.

## Things that went wrong on my side

- First tool call hung on a `cat >` without input (stopped, no effect).
- An edit script failed half-way on a line-wrap mismatch; nothing was written; redone by hand.
- The determinism runs took 9 minutes of wall time each on the shared CPU 12 (19 % of a CPU),
  far over the 2-minute rule for analysis agents, although they are 45 CPU-seconds each. I
  stopped the second today's-code run (`det2/ABORTED.txt`) and ran the snapshot test instead.
- A smoke test of the queued zdfs command timed out twice at 110 s before printing (set-up is
  14-18 s of CPU; CPU 12 had about eight processes on it). The third try, detached with a 7 min
  limit, finished in 182 s of wall time: members 1275, dimE 24, "done" (`queue/smoke_ad4_g170.log`).
  The wrapper `cgamma_job.sh` itself was not run end to end.
- My first reading of 32/5/104/29 ("an unreachable cap makes the kernel walk") was wrong; the
  paired probe corrected it before the report.

## Failed or empty searches (so nobody repeats them)

- No run record before the hub has an A cap below its start's A on an A28 circuit, or an
  AND-first objective on AES (grep over all `summary.json` and `.cfg` files of the two
  2026-11-13 campaign folders).
- No log for SAT windows on NIST 103 exists under `D/`.
- `E/asmall1` (ejection chains from A29 starts) has no result files: killed by the 05:09 outage.
