# Reproduce aes-sbox-a35-ad3-g181-gd12-T07-P6-1 (T07, A/AD/G/GD = 35/3/181/12)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T07/aes-sbox-a35-ad3-g181-gd12-T07-P6-1.circ.txt
```

- class (T07): other; status: known-by-23:50 (P6; new vs archive); reproduced by M3; pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P6; strategies/P6/NOTES.md; at 2026-11-15T16:40:55Z; seed 397181; after 240.0 s
- start: `nonlinear/boolflux/results/targets/T07/logs/aes-sbox-a35-ad3-g181-gd12-T07-P6-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P6/runs/pull12c/jobs/9552bd8ad634-r0-s0/start.bfx`, sha256 5eb67aab692c; OK 35/3/204/12)
- method: P6 depth pull: 177@13 -> GF(4) one-point coordinate move (T3 gf4build keep2, points [14,25,180,72]; l3scan max Kraft 0.75 at cap 12) -> class re-basing + hybrid build --paar (204@12) -> gate kernel hub.ops._kernel caps A35 AD3 GD12, cost,gd, 240 s stage
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "kernel_bin": "/home/joebachir20/xs-campaigns/2026-11-15-targets/P6/kbin/bin/bfx-94a75e2c18", "kernel_sha256": "e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0", "p6_sha256": {"botbasis.py": "31a4984dfc2df9dbbdb1a1bb04616073a66b286fb0dfbaf4f83d09ee7bfe3b48", "harvest.py": "f2b16d930074986c4de6f66fdd1fcfbb335109af7ca53922d798e6ddc701faf5", "hybrid.py": "c74341615b780c1016c0a634229d2cbdf737511b2fe1afb4bf30880794b4055b", "kern.py": "28bf7679e76143af71014dc98473e707b030e55f2676deaa6e175f8fe2c2f2fd", "l3scan.py": "d32c19961189af0ff06eccccac8a66b7c68b040fd0020c5cbd96611632c463f1", "lvdiag.py": "a38fd5e5d732191f64f429d536b6590bde8f84d0309fe74ac75862647f0ef6d4", "oscloop.py": "5fd1c7b89df1c7cc82ab313b37269e8cdd69587828ebfeb2786bfb0312eb44fa", "paarb.py": "eff23ab3442f3966ae03291887c3127571a4abbce614f13baa1005c39764e8c9", "pullrun.py": "412edef982c5f8f510700e6184c2e91a94d6a247fc6ff6859832d73aaa5aaa22", "rebase.py": "e79391ea92846212fe185c89f6a3462139b0519bd3094d6832f39b43d60c75d5", "save.py": "6e4eb2372802a75d66b1cec41703d67e227b6de960701dc04f675e14fb5d3b42", "skelan.py": "922275086be06cb23686b97b01f164cadca884e9dc4b6de573ed40c1fab019b5", "t07rb.py": "34e6b47417508532756828447ef8cb802e81d70478a1b55f861ada689ba1b590"}}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P6, seed 397181, 240.0 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
cd "$REPO"/nonlinear/boolflux/strategies/P6 && python3 pullrun.py --parents "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g181-gd15-k075-804faabc4648.bfx "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g181-gd15-k075-ccdae0d6b0ef.bfx "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g183-gd16-k075-9fde687eed4d.bfx "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g184-gd17-k075-5450c5ece1e0.bfx "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g185-gd17-k075-87c01d282bf7.bfx "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g186-gd18-k075-af476f0d0652.bfx "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g189-gd17-k075-a2d687a2b2d3.bfx "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/l3scan/emit177/a35-ad3-g189-gd17-k075-efea83713cab.bfx --cap 12 --out "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/pull12c --builds 51 --top 2 --seconds 240 --stages 2 --seed 1231 --hours 2 --paar --evolve 1
```
