# Reproduce aes-sbox-a32-ad4-g120-gd16-T05-P3-1 (T05, A/AD/G/GD = 32/4/120/16)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T05/aes-sbox-a32-ad4-g120-gd16-T05-P3-1.circ.txt
```

- class (T05): tradeoff:and_depth_for_gates; status: new (P3); pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P3; strategies/P3/NOTES.md; at 2026-11-15T22:58:51Z; seed 2222; after None s
- start: `nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g120-gd16-T05-P3-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-stage1.circ.txt`, sha256 99c3bf2a3e36; OK 32/4/117/17)
- method: pdrive mode from command.txt, repair_keep 1, kernel bfx-4dc199db (run Pareto set, frontier pass)
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "tree": "xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)", "kernel": "/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db", "kernel_sha256": "4dc199db6f226260b53cff84f4b441c93d39058f3b501cac24445a59822bf935"}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P3, seed 2222, None s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
env F_BFX="$HOME"/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 "$REPO"/nonlinear/boolflux/strategies/P3/pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g120-gd16-T05-P3-1/start.circ.txt --cap 16 --cap-ad 4 --cap-a 32 --mode mix --seconds 600 --seed 2222 --out "$HOME"/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s2-mix16-k2
```
