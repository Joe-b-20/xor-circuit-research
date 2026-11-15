# R1 status (window exact resynthesis -> exact window AND removal)

- wres (SAT window resynthesis): ab1 and ab2 0 vs 0 new frontier points; 28 fixed-target jobs on goal-near tuples
  0 strictly better. Not recommended.
- mc1.py (rank test + exhaustive flat products) and seq2.py (sequential 3->2) remove ANDs exactly in windows:
  dozens of verified A-1 circuits from A = 29..35 archive circuits; the A = 28 front shows none.
- NEW verified A = 28 front points (aes_check OK, new on the NIST pin, not dominated by the final hub archive):
  28/4/134/19 and 28/5/126/24 in ~/xs-campaigns/2026-11-15-study/R1/found/ (AND removal + kernel grind).
- 04:04-05:05 UTC: A/B ab3 = base vs base + andrm (op_andrm.py, generator), CPUs 17/18, snapshot ab3-snap.
  (test arm control.json had a quoting error for its first ~40 s: first job ran with base ops only.)
