# Reproduce aes-sbox-a35-ad3-g168-gd13-T08-P6-1 (T08, A/AD/G/GD = 35/3/168/13)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T08/aes-sbox-a35-ad3-g168-gd13-T08-P6-1.circ.txt
```

- class (T08): strict; status: new (P6); pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P6; strategies/P6/NOTES.md; at 2026-11-15T22:05:19Z; seed 473407; after 240.0 s
- start: `nonlinear/boolflux/results/targets/T08/logs/aes-sbox-a35-ad3-g168-gd13-T08-P6-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P6/runs/pull13c/jobs/66d51b7384e4-r2-s0/start.bfx`, sha256 2bab2df73bd1; OK 35/3/186/13)
- method: P6 pullrun depth pull (botbasis class re-basing + hybrid build) then gate kernel hub.ops._kernel caps A35 AD3 GD13 objective cost,gd, 240.0 s stage
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "kernel_bin": "/home/joebachir20/xs-campaigns/2026-11-15-targets/P6/kbin/bin/bfx-94a75e2c18", "kernel_sha256": "e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0", "p6_sha256": {"botbasis.py": "31a4984dfc2df9dbbdb1a1bb04616073a66b286fb0dfbaf4f83d09ee7bfe3b48", "certify.py": "eb9b1c7aa905c2fd8e63e5ea306a1aec9d95abb176badd27fc7d3647f2188b33", "cjscan.py": "b14d80126b5531d7968a7bd7ae577b93613a27611343881eddde5ffcfd76637d", "harvest.py": "f2b16d930074986c4de6f66fdd1fcfbb335109af7ca53922d798e6ddc701faf5", "hybrid.py": "c74341615b780c1016c0a634229d2cbdf737511b2fe1afb4bf30880794b4055b", "kern.py": "7cc91e0d25ed01f8b0a0ab13cce7e72f7e2d887b7a08f769667947e81de28279", "l3scan.py": "d32c19961189af0ff06eccccac8a66b7c68b040fd0020c5cbd96611632c463f1", "lvdiag.py": "a38fd5e5d732191f64f429d536b6590bde8f84d0309fe74ac75862647f0ef6d4", "oscloop.py": "bcd3537c56559ad32fce552c41fe282ae94cb9d197cc221d1bb215733eb883b9", "paarb.py": "eff23ab3442f3966ae03291887c3127571a4abbce614f13baa1005c39764e8c9", "pullrun.py": "e7e29c78644e30d9fcbfd646f27712134ca3b04206cde3cd9f2668cedffe350f", "rebase.py": "e79391ea92846212fe185c89f6a3462139b0519bd3094d6832f39b43d60c75d5", "save.py": "6915d800684086fd4e44d6d454c75e228c767ed1c25e36905dbb20374c20b4c0", "skelan.py": "922275086be06cb23686b97b01f164cadca884e9dc4b6de573ed40c1fab019b5", "t07rb.py": "34e6b47417508532756828447ef8cb802e81d70478a1b55f861ada689ba1b590"}}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent P6, seed 473407, 240.0 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
pullrun.py --parents "$HOME"/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g170-gd13-b418123e66e8.circ.txt "$HOME"/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g171-gd13-462cb948a761.circ.txt  --cap 13 --out "$HOME"/xs-campaigns/2026-11-15-targets/P6/runs/pull13c --builds 51 --top 3 --seconds 240 --stages 1 --seed 1391 --hours 1.0 --paar --evolve 2
```
