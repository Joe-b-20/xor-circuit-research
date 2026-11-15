# Reproduce aes-sbox-a32-ad4-g112-gd22-T05-P5-1 (T05, A/AD/G/GD = 32/4/112/22)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T05/aes-sbox-a32-ad4-g112-gd22-T05-P5-1.circ.txt
```

- class: tradeoff:and_depth_for_gates; status: new (P5); pinned NIST dominating: none
- start: `/home/joebachir20/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert113-r1-gate30/next.circ.txt` (sha256 255936e1dfadbf9a336c5c7f1b5b270338d17b517521f657ec823be4dfe7a55e)
- method: p3_pdrive.py (P3 copy of strategies/F/fdrive.py + hard A/AD guard) mode mix, caps A<=32 AD<=4 GD<=26, kernel bfx-94a75e2c18 repair_keep 1
- code: {"git": "8922cac + uncommitted strategies/P5", "kernel_sha256": "e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0"}
- seed: 32; found after 400 s; found 2026-11-15T19:09:08Z
- reproduction: not stated in the sidecar

## Re-run

```bash
env F_BFX=/home/joebachir20/xs-campaigns/2026-11-14-hub/long/bin/bfx-94a75e2c18 python3 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P5/p3_pdrive.py --start /home/joebachir20/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert113-r1-gate30/next.circ.txt --cap 26 --cap-ad 4 --cap-a 32 --mode mix --seconds 400 --seed 32 --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P5/runs/lin-cert113-r1-mix26
```
