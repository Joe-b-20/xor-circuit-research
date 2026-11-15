# R1 status (window exact resynthesis)

- ab1 (v1) done 01:26 UTC: base 0 vs base+wres 0 new frontier points; wres 0 admissions in 583 windows. Not adopted.
- 01:26 UTC: A/B ab2 running (v2 = op_wres2.py: equal-cost exploration + sideways adoption + 40% kernel polish of
  adopted structures), CPU 17 base / CPU 18 test, snapshot ab2-snap (t=1794705986, 2299 records, 455 cells,
  front 85), frozen-ab2, wres2 --seconds 60. Ends ~02:27 UTC.
- Side tests (30 s each, pinned to CPU 18 during ab2, i.e. against the test arm): relax-mode windows (deadlines
  from GD+1..2) on 28/4/135/18: 29 windows, nothing; kernel with GD cap +1 on 28/4/135/18 and 28/5/137/17:
  no G reduction in 30 s.
- Best so far: nothing claimed.
