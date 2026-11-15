# X1 / X1b status (final, 06:15 UTC 2026-11-15; X1b took over from X1 at ~03:00 UTC)

Nothing running (CPU 10 free since 06:10 UTC).  Stopped by X1b: x1-camp, x1-joinscan, x1-survey2 (03:01),
x1b-c29 (06:10).  x1-spangen finished 03:16.

Results:
- [V] NEW A28 FAMILY 9+5+14 (profile 9|1|2|2|14, H1 roles S1 9 / MID 5 / LAST 14, new U, 9-cover(U) True, c5(U) 1):
  X1/x1b/c29/found/aes-sbox-a28-ad5-g158-gd27-x1b-span-2cabef6153f4 (first, 03:19) + 11 more in X1/x1b/c29/found/*-C9*
  (lowest G 28/5/156/28); 2 distinct 9+5 prefixes.  Handed to H1 / H3 (messages 03:2x, 04:52).
- [C] the 270 A28s known before tonight: 6 spans, 6 U's (all NIST's).  H3's 28/5/210/31 = NIST g128 span.
- [H] no 27, no A29 -> 28 reduction in 97 walk runs (27 from A29 starts, each hub-best/NIST A29 >= 2 runs).
- 16 spangen1 A28s harvested to X1/found/*-x1b-spangen1-* (aes_check OK; g124's U, not new per X3b).
- Overnight spec: QUEUE.md "X1b" (X1/queue_x1b.sh, smoke-tested 04:45, registry X1/x1b/uregistry-tonight.json).
Details: NOTES.md sections 7-8.
