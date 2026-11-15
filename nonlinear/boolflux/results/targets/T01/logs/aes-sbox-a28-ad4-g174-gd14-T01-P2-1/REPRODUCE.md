# Reproduce aes-sbox-a28-ad4-g174-gd14-T01-P2-1 (T01, A/AD/G/GD = 28/4/174/14)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T01/aes-sbox-a28-ad4-g174-gd14-T01-P2-1.circ.txt
```

- class: other; status: new (P2); pinned NIST dominating: none
- start: `/home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a28-ad4-g175-gd14-xx147-68.circ.txt` (sha256 0d8760cc11984bac27875a9d31044f9d705ae102d51deb6028261efe06bc7169)
- method: strategies/F/fdrive.py mode mix (gate/osc/trb), stage 17 trb-bottom (timing-driven bottom-region rebuild + kernel), caps GD14 AD4 A28, kernel bfx-593fa798f5
- code: {"xcr-boolflux": "8922cacae4d4314968c5ce9baa740dea7aa38935 + uncommitted strategies/P2, strategies/F, strategies/T4", "kernel": "/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5", "kernel_sha256": "e67fefc016decaf325f411c6302a03a8d04f2e6c0e9b9ad6ea068458751198b7"}
- seed: 1; found after 2437.0 s; found 2026-11-15T16:21:12Z
- reproduction: not stated in the sidecar

## Re-run

```bash
env F_BFX=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/F/fdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a28-ad4-g175-gd14-xx147-68.circ.txt --cap 14 --cap-ad 4 --cap-a 28 --mode mix --seconds 7200 --seed 1 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/t02mix1
```
