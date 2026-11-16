# Reproduce aes-sbox-a32-ad4-g112-gd22-T04-P5-1 (T04, A/AD/G/GD = 32/4/112/22)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T04/aes-sbox-a32-ad4-g112-gd22-T04-P5-1.circ.txt
```

- class (T04): other; status: new (P5); pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P5; strategies/P5/NOTES.md; at 2026-11-15T19:09:08Z; seed 32; after 400 s
- start: `nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a32-ad4-g112-gd22-T04-P5-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert113-r1-gate30/next.circ.txt`, sha256 255936e1dfad; OK 32/4/112/25)
- method: p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A<=32 AD<=4 GD<=26, kernel bfx-94a75e2c18 repair_keep 1
- code: {"git": "8922cac + uncommitted strategies/P5", "kernel_sha256": "e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0"}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P5, seed 32, 400 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
env F_BFX="$HOME"/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 python3 "$REPO"/nonlinear/boolflux/strategies/P5/p3_pdrive.py --start "$REPO"/nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a32-ad4-g112-gd22-T04-P5-1/start.circ.txt --cap 26 --cap-ad 4 --cap-a 32 --mode mix --seconds 400 --seed 32 --out "$HOME"/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert113-r1-mix26
```
