# Reproduce aes-sbox-a35-ad3-g165-gd13-T07-M3-1 (T07, A/AD/G/GD = 35/3/165/13)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T07/aes-sbox-a35-ad3-g165-gd13-T07-M3-1.circ.txt
```

- class (T07): other; status: new (M3); pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent M3; strategies/M3/NOTES.md; at 2026-11-16T01:19:00Z; seed 52; after 413.7 s
- start: `nonlinear/boolflux/results/targets/T07/logs/aes-sbox-a35-ad3-g165-gd13-T07-M3-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6.circ.txt`, sha256 cb0edda7231e; OK 35/3/168/13)
- method: {'engine': 'ops/rebase.py: gbasis class re-basing + P6 hybrid build + capped gate kernel', 'operator': 'rebase'}
- code: {"git": "d9507dda7bcc83055879fefbfafb7e729e62b22f", "tree": "xcr-boolflux working tree incl. uncommitted campaigns/targets/ops", "ops_sha256": {"bottom.py": "cdd7c0ef1041cc61babfc6a9e20b5bb6bf0a885d97f699c16a1413afdcd946e7", "common.py": "34274be7632c0df33d46fb33477dfe91a9ce445b7c538d2216209ddd53ea55cf", "conjpull.py": "3e71a87052afb17ec5014eb088e0e994624ae70d730636a34cc19d992735329e", "m3common.py": "cf043c3d649190967017da21c0be8642ee150f204affd361c17e60a90574c013", "rebase.py": "311398ea41b1e7fac75e3f623a576c81dd1776d9139d12a5019827ad4a533b21", "satlns.py": "ad843f391a2dfab788658928dd675c55c8399bc5ca6a47a62c8d78dd474f9c9a"}, "kernel": "/home/joebachir20/xs-campaigns/2026-11-16-night/bin/bfx-94a75e2c18", "kernel_sha256": "e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0", "kernel_src_sha256": "c8d293b6ee35e201e7e08d58d750c95ab14af249ee8de8013a3cd1309c244fe8"}
- reproduction: one-off: time-budgeted search (campaign 2026-11-15-targets, agent M3, seed 52, 413.7 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
cd "$REPO" && python3 nonlinear/boolflux/campaigns/targets/ops/rebase.py --in "$REPO"/nonlinear/boolflux/results/targets/T07/logs/aes-sbox-a35-ad3-g165-gd13-T07-M3-1/start.circ.txt --target T08 --seed 52 --seconds 900 --cap 13 --stages 1 --stage-seconds 200 --out "$HOME"/xs-campaigns/2026-11-15-targets/M3/runs/screen/rb-t08c13c
```
