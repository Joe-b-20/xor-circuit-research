# H4 status (other representations)

Updated 2026-11-15 01:17 UTC.
* Running (unit xs-H-h4q2, CPU 16, queue ~/xs-campaigns/2026-11-15-study/H4/queue2.txt, log
  queue2.log): formal quadratic-complexity SAT for the level-3 blocks (kscal, qscal), then
  AD3 level-2 searches over 200 generated 9-product level-1 covers (screen_*.jsonl), then
  ad3mem junk searches.
* Best so far: no design <= 30 ANDs outside the GF(16)-tower pattern. The AND-depth-3 frontier
  (published A35, ours 35) is exactly the GF(4)-norm route; rebuilt it from my own level 2:
  ad3val.circ.txt (A 35, AD 3, aes_check OK). Looking for 34 at AD3 (would be a new point).
