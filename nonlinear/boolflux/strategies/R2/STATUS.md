# R2 status

- 00:24 UTC: A/B base arm running (`xs-R-r2-abbase`, CPU 19, 1 h, ~/xs-campaigns/2026-11-15-study/R2/abbase),
  restarted clean (first start 00:18 aborted: CPU 19 shared with misplaced hub jobs 00:19-00:25).
- Test arm (`xs-R-r2-abtest`, ab_test.sh) is only a waiter until the base unit ends (~01:25), then 1 h
  with aslack (frozen copy). Sequential, not concurrent.
- Best so far: no verified circuit claimed (operator produces correct near-front alternatives; no A reduction).
