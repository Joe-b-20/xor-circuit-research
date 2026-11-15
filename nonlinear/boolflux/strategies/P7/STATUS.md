# P7 status (T09, T10) — final report state 2026-11-15 20:40 UTC

CPUs 18, 19. Data: `~/xs-campaigns/2026-11-15-targets/P7/` (found/ 88 sidecars, all path_certified true;
runs/ logs, plans, failed runs). Method and evidence: NOTES.md. Frontier: `python3 frontier.py`.

## Still running (unattended, self-terminating at 23:10 UTC, last seed done by ~23:20)
- CPU 19: `xs-P-P7-deep1` -> loopD (runs/bopt/overnight.sh, seeds 3000+).
- CPU 18: `xs-P-P7-ref2` (bopt --refine2 on 2 more plans) then `xs-P-P7-loopE` (overnight.sh, seeds 9000+).
  Every kernel call: strategies/P7/fdrive_p7.py (repair_keep 1), starts inside all caps, cap A = build A.
  New results land in found/ with sidecars incl. path_certified / donor fields automatically.

## Best per target
| target | best strict | best tradeoff | files (found/) |
|---|---|---|---|
| T09 (ref 45/4/141/12) | **41/4/137/12** (G -4, A -4); **39/4/138/12** (G -3, A -6) | none (GD11 not reached at A<=45) | p7-t09-a41-ad4-g137-gd12-pol-LC-aes-sbox-a45-pw3-s7002.circ.txt, p7-t09-a39-ad4-g138-gd12-build-LC-aes-sbox-a45-pw0-s7001.circ.txt |
| T10 (ref 59/4/159/10) | none | none | G at GD10 pinned in the 59 architecture (NOTES 4) |

T09 Pareto in (A, G) at GD12: 39/138, 41/137 (also 42/137, 40/139, 43/139 dominated).
All new against both the reference and the whole pinned NIST set (aes_check: published best G at GD<=12 is
141) and against our archive (best-1400 had 43/4/141/12 at GD12).
