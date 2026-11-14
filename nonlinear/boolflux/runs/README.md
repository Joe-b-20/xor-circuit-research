# Run records

Run outputs are kept **outside the repository**, one folder per campaign under
`~/xs-campaigns/<date>-<name>/`. They are large: the 2026-11-13 benchmark alone has about 41,500
files. Only verified circuits that we report are copied into [../results/](../results/), each
with a sidecar that points back to its run. [INDEX.md](INDEX.md) lists every campaign folder so
far, with one line each. Campaign folders are never edited after the fact. A failed or aborted
run stays where it is, and its folder name says so (`FAILED/`, `*-aborted-*`).

## What a run record must contain

| field | where `cli.py run`, `pipe` and `flow` put it |
|---|---|
| exact source version | `OUT/src/` (copy of the kernels and the Python package) and `OUT/bin/` (binaries built from it); `summary.json` `code_sha256_12` = hash of `src/` |
| command and settings | `summary.json`: `command`, `settings` (kernel defaults plus `--set`), `objective`, `caps`, `model` and `model_gates`, `start` and `start_metrics` |
| seeds | `summary.json` `seeds`; every job's `kernel_seed` (= seed + 1000 x round) in `runs[]` |
| move traces | each job's kernel log `OUT/<tag>.log`: `best t .. it .. mv ..` lines for every improvement, `move` statistics per move type. A full move-by-move trace needs `--set tracemoves=FILE` |
| checkpoints | every job's start and best circuit (`<tag>.start.bfx`, `<tag>.best.bfx`); `best.circ.txt` and `summary.json` are rewritten after every round, so a later failure cannot lose them |
| timing | per job: `wall_s`, kernel `final.seconds`, `time_capped`, time and iteration of every improvement; per run: `wall_s`. `flow` also records the trajectory (`[t, cost, G, A, GD, AD]` rows), start-up overhead and peak RSS |
| verification | `summary.json` `best`: `core_ok`, `independent_ok`, `library_ok`, `buf_lines`, the independent verifier's metrics; `CAPS NOT MET` is written into the file and the exit code when the best is infeasible |

Scripts outside `cli.py` (the strategy tracks, the hub) must record the same things. In practice:
a sidecar JSON next to every circuit they keep, naming the start or parents, the command, seed,
settings, mechanism, time to result and the code version (a git commit, or the sha256 of
uncommitted scripts). They must also keep `aes_check.py` output next to it (`*.check.txt` /
`*.check.json`), and an event log (`log.jsonl` with time stamps) for long runs.

A run is **deterministic** when its iteration budget (`--iters`) ends every job. The time cap
`--seconds` is only a safety stop, so the same command gives the same circuit. Time-budgeted
runs (`flow`, the strategy drivers, 120 s polishes) are not bit-reproducible. Their results
are marked *one-off* in [../results/MANIFEST.json](../results/MANIFEST.json) unless they were
reached again.

## Running a campaign

- Pin every process to its own CPU (`taskset -c N`, or `flow --cpus`), one busy process per
  CPU. Timings measured under oversubscription must be marked as such (track F's NOTES list
  them).
- Launch long jobs under the memory guard (`~/xs-campaigns/guard/xsrun TRACK CPUS NAME LOG -- cmd`,
  a systemd user unit with `MemoryMax`). This was added after the 2026-11-14 05:09 UTC
  out-of-memory outage ([../HISTORY.md](../HISTORY.md)).
- Write a `STATUS.md` in the campaign folder while the campaign runs (what is running, on which
  CPUs, best so far with evidence), and a `NOTES.md` or README next to the code.
- Add the folder to [INDEX.md](INDEX.md).
- To report a circuit: `campaigns/aes_check.py` (AES), then `campaigns/curate_aes.py` and
  `campaigns/manifest.py`, then `campaigns/verify_all.py`
  ([../VERIFICATION.md](../VERIFICATION.md)).
