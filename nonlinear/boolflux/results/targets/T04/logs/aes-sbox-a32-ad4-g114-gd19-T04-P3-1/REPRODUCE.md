# Reproduce aes-sbox-a32-ad4-g114-gd19-T04-P3-1 (T04, A/AD/G/GD = 32/4/114/19)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T04/aes-sbox-a32-ad4-g114-gd19-T04-P3-1.circ.txt
```

- class: strict; status: new (P3); pinned NIST dominating: none
- start: `/home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-m21/stage2.circ.txt` (sha256 db41c24e6409175ca4b1a7bd53c98a21971d060860ff2360bb3158e802451d35)
- method: pdrive mix caps A32 AD4 GD19 (stage 1 osc repair, t=102 s); lineage: archive 116@20 a43e1ae3d73f -> conjugate lam=188 k=0 (conj.py/mkconj.py) -> pdrive gate cap24 240 s (114@24) -> pdrive mix cap21 (113@20) -> this; kernel bfx-593fa798f5
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "tree": "xcr-boolflux + uncommitted strategies/P3 (and F/T2 as used)", "kernel": "/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5", "kernel_sha256": "e67fefc016decaf325f411c6302a03a8d04f2e6c0e9b9ad6ea068458751198b7"}
- seed: 3; found after 102.0 s; found 2026-11-15T17:51:44Z
- reproduction: not stated in the sidecar

## Re-run

```bash
env F_BFX=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P3/pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-m21/stage2.circ.txt --cap 19 --cap-ad 4 --cap-a 32 --mode mix --seconds 360 --seed 3 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P3/runs/pipe-conj-116g20-l188-k0-m19 
```
