# L2 status (log analyst, pre-hub era)

Updated 2026-11-15 02:25 UTC. CPU 12, short jobs only. **Finished; nothing running.**

Done:
- `WHAT-WORKED-BEFORE.md`: recipes with run records for every A <= 31 and goal-near pre-hub
  point, AND-level profiles, value-ranked list of what worked with CPU cost, 27 failed
  approaches with evidence and verdicts, reproducibility gaps.
- `DOC-AUDIT.md`: 4 wrong, 10 unsupported, 14 stale claims and 8 gaps in README, HOW-IT-WORKS,
  HISTORY, bench/REPORT and MANIFEST, with file:line and the supported statement.
- Checks run (`NOTES.md`): paired cap probe (6 x 100 s); re-run of 30 recorded joins (30
  identical); the command behind 28/4/133/20 (identical with its own binary and with
  today's code plus `--set skip_noop=0`; 134 with today's defaults).
- Queue entry: the 11 unfinished gammas of track C's k = 12 sweep (`QUEUE.md`, section L2;
  command smoke-tested with `--limit 20`).

Best so far: no circuit (analysis agent).
Data: `~/xs-campaigns/2026-11-15-study/L2/` (e2.out lineage, stages.out, probeE/, det1/, det_old/,
rejoin.out, queue/).
