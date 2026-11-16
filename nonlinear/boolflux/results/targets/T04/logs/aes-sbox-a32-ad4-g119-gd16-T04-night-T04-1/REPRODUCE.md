# Reproduce aes-sbox-a32-ad4-g119-gd16-T04-night-T04-1 (T04, A/AD/G/GD = 32/4/119/16)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T04/aes-sbox-a32-ad4-g119-gd16-T04-night-T04-1.circ.txt
```

- class (T04): other; status: new (night:T04); pinned NIST dominating: none
- found by: night runs 2026-11-16, run T04; at 2026-11-16T08:12:15Z; seed 247057; after 383.3 s
- start: `nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a32-ad4-g119-gd16-T04-night-T04-1/start.circ.txt` (copy of `~/xs-campaigns/2026-11-16-night/T04/found/conjpull-a32-ad4-g117-gd17-b83f9deb89.circ.txt`, sha256 b83f9deb895d; OK 32/4/117/17)
- method: ops/conjpull.py: GF(2^8) conjugate (P3 conj3 screen + mkconj build) then staged kernel pulls m:-1:600,m:-1:600 (fdrive semantics; kernel bfx-94a75e2c18, repair_keep 1 unless a stage says rk0/rk1); search states may exceed caps, recorded circuits inside A<=32 AD<=4
- code: {"git": "d9507dda7bcc83055879fefbfafb7e729e62b22f", "tree": "xcr-boolflux working tree incl. uncommitted campaigns/targets/ops", "ops_sha256": {"bottom.py": "cdd7c0ef1041cc61babfc6a9e20b5bb6bf0a885d97f699c16a1413afdcd946e7", "common.py": "34274be7632c0df33d46fb33477dfe91a9ce445b7c538d2216209ddd53ea55cf", "conjpull.py": "3e71a87052afb17ec5014eb088e0e994624ae70d730636a34cc19d992735329e", "m3common.py": "cf043c3d649190967017da21c0be8642ee150f204affd361c17e60a90574c013", "rebase.py": "311398ea41b1e7fac75e3f623a576c81dd1776d9139d12a5019827ad4a533b21", "satlns.py": "afff86f40d1bee2d152da428202198a041530e41baa4353ec0e55071f25b25d9"}, "kernel": "/home/joebachir20/xs-campaigns/2026-11-16-night/bin/bfx-94a75e2c18", "kernel_sha256": "e4f373f70f9698878db48476337876b68a02935d850117816faf0c561aa467a0", "kernel_src_sha256": "c8d293b6ee35e201e7e08d58d750c95ab14af249ee8de8013a3cd1309c244fe8"}
- reproduction: one-off: time-budgeted search (night runs 2026-11-16, run T04, seed 247057, 383.3 s); not bit-reproducible. command.sh re-runs it from start.circ.txt; check any result with aes_check.py.

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
/usr/bin/python3 "$REPO"/nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in "$REPO"/nonlinear/boolflux/results/targets/T04/logs/aes-sbox-a32-ad4-g119-gd16-T04-night-T04-1/start.circ.txt --target T04 --seed 247057 --seconds 1260 --out "$HOME"/xs-campaigns/2026-11-16-night/T04/runs/T04/conjpull-677 --conj id --schedule m:-1:600,m:-1:600 --repair-keep alt
```
