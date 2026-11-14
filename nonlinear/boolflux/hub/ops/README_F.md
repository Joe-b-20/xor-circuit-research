# Track-F hub operators (hub/ops/)

Same CLI as hub/ops.py (`--archive DIR --in ID [--in2 ID] [--caps A,AD,GD] [--objective KEYS]
--seed S --seconds T --out JOBDIR`, write `cand-*.bfx` + `record.json`); they register into
E's `OPS` table (f_ops.py imports `boolflux.hub.ops`) and reuse its `_kernel` and `main`.
This directory has no `__init__.py` on purpose, so `boolflux.hub.ops` still resolves to E's
`ops.py`. Caps with a missing value: `--caps=-,4,14`.

| script | operator | what | measured |
|---|---|---|---|
| `op_osc.py` | osc | kernel under GD+1 (30 % of T), repair back to the caps (40 %), polish (30 %) | 122@GD14: repairs feasible 50/65, no gain in 2.9 CPU-h (F NOTES 4); 116@15 -> 125@15 in 37 s test |
| `gen_inv3.py` | gen_inv3 | replace the GF(2^4) inversion of a tower-field input by depth-3 blocks: library `inv_designs/` (13 blocks, 22-27 gates + 3 pair sums) then on-the-fly annealed blocks (random extra-input sets) | 116@GD15 -> 122@GD14 A37 directly (11 of 13 library blocks and synthesised ones); other extras give 124-129 at GD15-16 |
| `gen_bottom.py` | gen_bottom | keep the input's front + inversion, take a donor's AND-level-4 products and output layer (`--in2`, else random AD4 archive members); missing forms by table lookup | 116 + 141's bottom -> 143@GD14 A43; 116 + 148@11's bottom -> 150@GD13 |
| (E's `trb`) | trb | copy of strategies/F/trb.py | the only F A/B arm with a gain: 122 -> 121@GD14 (1/3 CPU-h); AD3: 163 -> 161@GD14, 180 -> 174@GD13 in ~2 min |

Libraries in `f_lib/` are copies of strategies/F/{depth, invspec, invsplice, invsyn, botsplice}.py
(path depth adjusted; invsplice builds the extra inputs at the inversion inputs' level).
Not packaged: `strategies/F/linres.py` (XORFlux on one linear region, exact constant handling):
on NIST 139@GD27 AD3 every layer came back at the same size (41, 20, 28, 15 gates), so no
measured advantage yet.
