# P1 status (T01, T03)

Updated 2026-11-15 22:30 UTC. Final.

## Running
Nothing after ~22:30 (last unit xs-P-P1-iter0 ends by itself). Overnight proposal: QUEUE.md entry P1-lns.

## Best (this campaign; archive bar in brackets)
- T01 strict: none new [archive 28/4/131/22, 132/20, known]. Tradeoff (G <= 129 at GD 23-24): none.
- T03 strict: none [archive: nothing strict]. Tradeoff: not permitted for T03.
- New frontier point (not strict, not a permitted tradeoff): **28/5/129/19** (T03 class), SAT LNS
  (unionsat2) from the hub 130/19; found/P1-T03-a28-ad5-g129-gd19-*.circ.txt (44 distinct structures).

## Hard limits
From 18:10 every kernel call has repair_keep 1 (NOTES section 6); before, kernel-internal states during
GD repairs were not guaranteed inside A <= 28 / AD <= cap (every recorded output was checked).

## Stopped / finished (logs kept under DATA/runs/)
p1run workers w10, w11, w11b, w11c, w0; screens scr10, scr11, scr10c; usat (v1, void UNSATs); LNS
lns2seq2-7, lnsT03d19, lnsT01, iter (t03-d20-rot, t03-d19-it, t03-d19-it2, t03-d19-v2cfg, t03-d20-ed95,
t01-d22-it, t01-d21-it); conjugate pipelines conj0/0b/0c, conj11/11b/11c; conj3 screen.
