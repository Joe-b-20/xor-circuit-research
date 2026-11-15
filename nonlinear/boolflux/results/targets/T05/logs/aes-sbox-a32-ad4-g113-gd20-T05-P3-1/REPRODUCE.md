# Reproduce aes-sbox-a32-ad4-g113-gd20-T05-P3-1 (T05, A/AD/G/GD = 32/4/113/20)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T05/aes-sbox-a32-ad4-g113-gd20-T05-P3-1.circ.txt
```

- class: tradeoff:and_depth_for_gates; status: new (P3); pinned NIST dominating: none
- start: `/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-g24/stage1.circ.txt` (sha256 26e4e09ee8bbc9cd5ab49f0f7ebaa5fc5d8aacf49c24785f4ee2ebed5e2f112b)
- method: pdrive (strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A32 AD4 GD21, kernel bfx-593fa798f5
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "tree": "xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)", "kernel": "/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5", "kernel_sha256": "e67fefc016decaf325f411c6302a03a8d04f2e6c0e9b9ad6ea068458751198b7"}
- seed: 2; found after 362.0 s; found 2026-11-15T17:48:11Z
- reproduction: not stated in the sidecar

## Re-run

```bash
env F_BFX=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3/pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-g24/stage1.circ.txt --cap 21 --cap-ad 4 --cap-a 32 --mode mix --seconds 360 --seed 2 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-m21 
```
