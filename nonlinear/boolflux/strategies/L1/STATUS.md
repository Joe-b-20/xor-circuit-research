# L1 status (log analyst, hub era; CPU 12, short xsfg jobs only)

- DONE 02:15 UTC. Nothing running. Report: `WHAT-WORKS.md`; method and mistakes: `NOTES.md`.
- Overnight spec: entry "L1" in `~/xs-campaigns/2026-11-15-study/QUEUE.md` (`focus_job.sh`, launch path
  smoke-tested only; configuration untested).
- Data: `~/xs-campaigns/2026-11-15-study/L1/` (cache.json, struct.json, q1-q7.txt, smoke1/,
  overnight/smoke2/, harvest-test/, evaltest/). Smoke directories are test evidence, not results.
- Sent to the coordinator: early notice (hub gain flaw, join partner list, starvation, CPU vs value) and
  one correction of two numbers in it.

## L1b (took over ~03:00 UTC, tasks: TONIGHT.md at ~04:30 and ~06:00, QUEUE-REVIEW.md by 06:15)
- Scripts: l1b_score.py (goal distances A-G, front points, move-level A/AD reductions, A<=29 AND spans, CPU-h),
  l1b_span1.py (span of given files vs baseline), l1b_run.sh (guarded short steps on CPU 12).
- Outputs: ~/xs-campaigns/2026-11-15-study/L1/l1b-score-HHMM.txt. Nothing long-running.
- 06:00 UTC L1b DONE: TONIGHT.md (pass 2, 05:50 data), QUEUE-REVIEW.md (vetting of 25 entries + 20-CPU allocation).
  Rescued orphan circuit: ~/xs-campaigns/2026-11-15-study/L1/found/rescued/ (28/4/131/22, since harvested by T1 too).
  Nothing running.
