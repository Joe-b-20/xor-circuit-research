# Measurement records (not run by verify_all.py)

**These are LP-status measurements and stress controls. They need SciPy (HiGHS) and the sprint
generators, and `verify_all.py` does not run them.** They are kept as the record of how the counts in
the main README were measured. None of them is a premise of any certified statement. The counts of
open claims (686, 509, 419, 280, 400, 282, 581) are LP status [measured]. Only the exclusions are
certified, by the certificate files in `../` and the checkers in `../../checkers/`.

| File | From | What it is |
|---|---|---|
| `push_rows.py` | recon | Transcription of the push5/push6 rows for arbitrary type lists. Its self-check against the archive generator found 1,386 keys and 110,019 rows identical. It imports the archive push6 generator and the package copy from `~/xs-campaigns/2026-11-07-sprint/lb76/` |
| `combined_scan.py` | recon | The LP scans (sprint, push, combined, ablations, open leaves) through the package driver `lp_regen.run(75)`. It imports the sprint generators (`qcert4/gen_certs3_copy.py`, functions copied from `qcert4/gen_certs4.py`), the archive push6 generator and the package copy, all from `~/xs-campaigns/2026-11-07-sprint/`, and needs SciPy |
| `scan.py` | recon-check | The independent LP scan (sprint 686 / push 509 / combined 280), with matrices from `check_combined75.matrix`. It refers to `~/xs-campaigns/2026-11-09-phase/recon` and the package by absolute paths, and needs SciPy |
| `compare_scans.json` | recon | Reproduction checks (686 = qcert4's scan, 509 = the archive's `SCREEN75_FULL_CUT.json`), the intersection 419, the 406 newly excluded claims and the open structure |
| `scan_leaves.json` | recon | The open (A, q_D) leaves of the 229 load-bearing keys of the combined scan: 572 of 9,432 |
| `stress_push.json` | recon | The push5/push6 rows on 316 circuits / 1,264 phases (13 package controls and 303 real 88-gate circuits), with each circuit's own G: 0 violations |

All files are byte-identical to the audit folders `~/xs-campaigns/2026-11-09-phase/recon/` and
`~/xs-campaigns/2026-11-09-phase/recon-check/` (see `../../PROVENANCE.md`). Their absolute paths were
not edited, because these files are records and are not meant to run from here.
