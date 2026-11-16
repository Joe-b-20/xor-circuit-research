# Reproduce aes-sbox-a32-ad4-g111-gd25-T05-P5-1 (T05, A/AD/G/GD = 32/4/111/25)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T05/aes-sbox-a32-ad4-g111-gd25-T05-P5-1.circ.txt
```

- class (T05): tradeoff:and_depth_for_gates; status: known-by-23:50 (P5; new vs archive); reproduced by night:T05; pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P5; strategies/P5/NOTES.md; at 2026-11-15T19:50:15Z; seed 91; after 302 s
- start: `nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g111-gd25-T05-P5-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P5/starts/ad4-111-25-cert.circ.txt`, sha256 49d67b7b0ba7; OK 32/4/111/25)
- method: p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode gate, caps A<=32 AD<=4 GD<=30, kernel bfx-94a75e2c18 repair_keep 1
- code: {"git": "8922cac + uncommitted strategies/P5", "kernel_sha256": "e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0"}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P5, seed 91, 302 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
env F_BFX="$HOME"/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 python3 "$REPO"/nonlinear/boolflux/strategies/P5/p3_pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T05/logs/aes-sbox-a32-ad4-g111-gd25-T05-P5-1/start.circ.txt --cap 30 --cap-ad 4 --cap-a 32 --mode gate --seconds 300 --seed 91 --out "$HOME"/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert111-r1-gate30
```
