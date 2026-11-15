# Reproduce aes-sbox-a32-ad4-g117-gd17-T04-P3-1 (T04, A/AD/G/GD = 32/4/117/17)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T04/aes-sbox-a32-ad4-g117-gd17-T04-P3-1.circ.txt
```

- class: strict; status: new (P3); pinned NIST dominating: none
- start: `/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkK1-s2-mix17-k1/pareto/g118-gd17.circ.txt` (sha256 dddd01b7ade8eb876f87160ffd8e66b07eccf486e73cc3bdac21c5383d7f7d26)
- method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD17, kernel bfx-4dc199db, repair_keep 1
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "tree": "xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)", "kernel": "/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db", "kernel_sha256": "4dc199db6f226260b53cff84f4b441c93d39058f3b501cac24445a59822bf935"}
- seed: 2212; found after 600.0 s; found 2026-11-15T22:13:09Z
- reproduction: not stated in the sidecar

## Re-run

```bash
env F_BFX=/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/bin/bfx-4dc199db python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3/pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkK1-s2-mix17-k1/pareto/g118-gd17.circ.txt --cap 17 --cap-ad 4 --cap-a 32 --mode mix --seconds 600 --seed 2212 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/rkN1-s1-mix17-k2 
```
