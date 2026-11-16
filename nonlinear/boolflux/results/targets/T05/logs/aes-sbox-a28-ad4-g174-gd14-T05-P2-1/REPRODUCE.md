# Reproduce aes-sbox-a28-ad4-g174-gd14-T05-P2-1 (T05, A/AD/G/GD = 28/4/174/14)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T05/aes-sbox-a28-ad4-g174-gd14-T05-P2-1.circ.txt
```

- class (T05): tradeoff:and_depth_for_gates; status: known-by-23:50 (P2; new vs archive); reproduced by night:T02; pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P2; strategies/P2/NOTES.md; at 2026-11-15T16:21:12Z; seed 1; after 2437.0 s
- start: `nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a28-ad4-g174-gd14-T05-P2-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a28-ad4-g175-gd14-xx147-68.circ.txt`, sha256 0d8760cc1198; OK 28/4/175/14)
- method: strategies/F/fdrive.py mode mix (gate/osc/trb), stage 17 trb-bottom (timing-driven bottom-region rebuild + kernel), caps GD14 AD4 A28, kernel bfx-593fa798f5
- code: {"xcr-boolflux": "8922cacae4d4314968c5ce9baa740dea7aa38935 + uncommitted strategies/P2, strategies/F, strategies/T4", "kernel": "/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5", "kernel_sha256": "e67fefc016decaf325f411c6302a03a8d04f2e6c0e9b9ad6ea068458751198b7"}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P2, seed 1, 2437.0 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
env F_BFX="$HOME"/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5 python3 "$REPO"/nonlinear/boolflux/strategies/F/fdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a28-ad4-g174-gd14-T05-P2-1/start.circ.txt --cap 14 --cap-ad 4 --cap-a 28 --mode mix --seconds 7200 --seed 1 --out "$HOME"/xs-campaigns/2026-11-15-targets/P2/runs/t02mix1
```
