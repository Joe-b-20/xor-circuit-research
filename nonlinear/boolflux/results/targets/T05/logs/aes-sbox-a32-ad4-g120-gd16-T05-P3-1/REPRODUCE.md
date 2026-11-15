# Reproduce aes-sbox-a32-ad4-g120-gd16-T05-P3-1 (T05, A/AD/G/GD = 32/4/120/16)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T05/aes-sbox-a32-ad4-g120-gd16-T05-P3-1.circ.txt
```

- class: tradeoff:and_depth_for_gates; status: new (P3); pinned NIST dominating: none
- start: `/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-stage1.circ.txt` (sha256 99c3bf2a3e36fea46efa04f22ce505c4464f7c6f9f2d15d034b2c2f67cf478e0)
- method: pdrive mode from command.txt, repair_keep 1, kernel bfx-4dc199db (run Pareto set, frontier pass)
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "tree": "xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)", "kernel": "/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db", "kernel_sha256": "4dc199db6f226260b53cff84f4b441c93d39058f3b501cac24445a59822bf935"}
- seed: 2222; found after None s; found 2026-11-15T22:58:51Z
- reproduction: not stated in the sidecar

## Re-run

```bash
env F_BFX=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3/pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-stage1.circ.txt --cap 16 --cap-ad 4 --cap-a 32 --mode mix --seconds 600 --seed 2222 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s2-mix16-k2
```
