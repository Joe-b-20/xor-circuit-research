# X1 / X1b status (updated 04:55 UTC 2026-11-15; X1b took over from X1 at ~03:00 UTC)

CPU 10, one busy job:
- `x1b-c29` (since 03:17, restarted 03:21 and 03:22 for patches): x1b_camp.py = walk + span registry + U filter
  + polish + aes_check, from H3's A28, all A29 of hub best/, NIST A29 and NIST A28 (run script X1/x1b/run_c29.sh,
  output X1/x1b/c29/, log X1/x1b/c29.log).  Phase 1 03:22-04:44 (46 runs: 36 from A28, 11 from A29, no reduction, no 27); phase 2 04:49-06:37.
- X1's spangen1 finished 03:16 (16 A28s, harvested to X1/found/*-x1b-spangen1-*, all aes_check OK).

Stopped 03:01 UTC by X1b: x1-camp (camp27), x1-joinscan (joinscan30), x1-survey2 (see NOTES section 7).

Best / findings:
- [V] NEW A28 FAMILY 9+5+14 (9|1|2|2|14, new U, 9-cover(U) True): X1/x1b/c29/found/aes-sbox-a28-ad5-g158-gd27-x1b-span-2cabef6153f4
  (reported 03:2x); more variants with other new U's in c29/found/*-NU-C9*.
- [C] the 270 A28s known before tonight have 6 spans / 6 U's; H3's 28/5/210/31 = NIST g128 span (NOTES 8).
- 11 new-U 9-coverable 9+5+14 A28s in X1/x1b/c29/found/*-C9* (list sent 04:52); they share 2 distinct 9+5 prefixes.
- Overnight spec: QUEUE.md "X1b" section, script X1/queue_x1b.sh.
- Smoke test of queue_x1b.sh: 04:45 UTC, X1/queue-x1b-smoke/ (1 run, 2 NU-C9 saved, aes_check OK). An accidental
  first launch into X1/queue-x1b/ was stopped after ~1 min and moved to X1/queue-x1b-smoke-aborted/ (queue dir is clean).
