# Reproduce aes-sbox-a32-ad4-g117-gd17-T04-P3-1 (T04, A/AD/G/GD = 32/4/117/17)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T04/aes-sbox-a32-ad4-g117-gd17-T04-P3-1.circ.txt
```

- class (T04): strict; status: known-by-23:50 (P3; new vs archive); reproduced by night:T04, night:T05; pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P3; strategies/P3/NOTES.md; at 2026-11-15T22:13:09Z; seed 2212; after 600.0 s
- start: `nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a32-ad4-g117-gd17-T04-P3-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P3/runs/rkK1-s2-mix17-k1/pareto/g118-gd17.circ.txt`, sha256 dddd01b7ade8; OK 32/4/118/17)
- method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD17, kernel bfx-4dc199db, repair_keep 1
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "tree": "xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)", "kernel": "/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db", "kernel_sha256": "4dc199db6f226260b53cff84f4b441c93d39058f3b501cac24445a59822bf935"}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P3, seed 2212, 600.0 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
env F_BFX="$HOME"/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 "$REPO"/nonlinear/boolflux/strategies/P3/pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a32-ad4-g117-gd17-T04-P3-1/start.circ.txt --cap 17 --cap-ad 4 --cap-a 32 --mode mix --seconds 600 --seed 2212 --out "$HOME"/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s1-mix17-k2 
```
