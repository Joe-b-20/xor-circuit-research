# Reproduce aes-sbox-a32-ad4-g113-gd20-T05-P3-1 (T05, A/AD/G/GD = 32/4/113/20)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T05/aes-sbox-a32-ad4-g113-gd20-T05-P3-1.circ.txt
```

- class (T05): tradeoff:and_depth_for_gates; status: known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05; pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P3; strategies/P3/NOTES.md; at 2026-11-15T19:42:02Z; seed 1011; after 361.0 s
- start: `nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g113-gd20-T05-P3-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P3/starts/p5cert-112g22.circ.txt`, sha256 01d9a03df1bf; OK 32/4/112/22)
- method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, kernel bfx-4dc199db, repair_keep 1
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "tree": "xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)", "kernel": "/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db", "kernel_sha256": "4dc199db6f226260b53cff84f4b441c93d39058f3b501cac24445a59822bf935"}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P3, seed 1011, 361.0 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
env F_BFX="$HOME"/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 "$REPO"/nonlinear/boolflux/strategies/P3/pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g113-gd20-T05-P3-1/start.circ.txt --cap 21 --cap-ad 4 --cap-a 32 --mode mix --seconds 360 --seed 1011 --out "$HOME"/xs-campaigns/2026-11-15-targets/P3/runs/rkG1-s1-mix21-k1 
```
