> Note (coordinator): this report audited the result set as of 20:19 UTC. Afterwards the chi3 results were re-run against the spec table, header tallies were corrected, and 13 more AES results were added from the circuits new in e6ac0d0. `audit.py --second-opinion` was re-run on the final set (`run-final.log`): 12 surviving tuples, strict depth caps 13, 14, 18, 19, no disagreements.

# Independent audit of BoolFlux circuit claims (2026-11-13)

Snapshot: files as on disk at 2026-11-13T20:19:29Z. Every audited file's sha256 and mtime is in
`audit.json`. The `results/` tree changed while this audit ran: `results/_superseded/`,
`results/nist-format/`, `results/MANIFEST.json` and `*.circ.fn.json` files appeared between
20:11 and 20:13 UTC. A new campaign (`frontier-fwd-3`) was running at 20:15 UTC, so result
files written after the snapshot are not covered. Rerun `audit.py` to refresh.

## Method

- **Code.** `audit.py` uses only the Python standard library. It imports nothing from
  `nonlinear/` and reads no metric numbers from the optimizer. It does its own parsing
  (ranges such as `x0:x7`, comments `%`/`#`, constants `0`/`1`, several circuits per file
  flagged), its own structural checks (single assignment, operands defined earlier, inputs
  never assigned, outputs assigned, no constant outputs, no outputs that are inputs, no
  `~`/`!` tokens, BUF flagged, dead gates, constant-operand and identical-operand gates
  flagged), and its own metrics.
- **Targets.** The AES S-box is computed from FIPS-197: brute-force inverse mod 0x11B with
  0 -> 0, then the affine map with 0x63. It is self-checked on S(00)=63, S(01)=7c, S(53)=ed,
  S(10)=ca, S(ff)=16 and on being a permutation. It equals the `aes` table in
  `benchmarks/sboxes.json`. maj3, fulladd (carry = MSB, sum), gf16-mul (a = high nibble,
  mod x^4+x+1) and gf16-inv (mod x^4+x+1, 0 -> 0) are computed from their definitions. The
  small S-boxes are `table[x]` from `sboxes.json`. Bit order is msb/msb throughout.
- **Functional check.** All 2^n inputs, done twice: bitsliced truth tables (2^n-bit integers)
  and a separate scalar evaluation for each input. Both must agree with the target.
- **Metrics (NIST accounting).** G = gate lines excluding BUF (NOT and XNOR-with-0 count as
  gates). A = AND+NAND+OR+NOR+ANDN+ORN. GD = longest path, every gate +1, inputs and
  constants at 0. AD = most nonlinear gates on any path. XX = #XOR+#XNOR. Also #XNOR, #NOT,
  XNOR with a constant operand, dead gates, and gates per gate level / AND level (checked
  against NIST headers that list them).
- **Basis.** AES results must use only {AND, XOR, XNOR, NOT}. The small models are bgc
  {AND OR XOR NOT}, gc6 {AND OR XOR XNOR NAND NOR NOT}, nist {AND XOR XNOR NOT},
  xag {AND XOR NOT} and gc (all, including ANDN/ORN).
- **Published set.** `nist/aes-sbox/*.circ.txt` (78), `nist/old-2020/aes-sbox-fwd-*.slp` (3)
  and `nist/sbox/aes-sbox-fwd-*` (21 .circ.txt/.ncff.txt): 102 files, 90 distinct tuples.
- **Pareto analysis** on (A, AD, G, GD), lower is better, verified circuits only. A result
  *survives* when no published circuit is <= on all four and no other result is strictly
  better. Identical result tuples count once.
- **Second opinion.** `independent/verify.py --json` was run on all 230 files (published,
  results, nist-format copies and superseded files). It agrees with this audit on ok, G, A,
  GD, AD and dead gates for every file. For small targets it was given this audit's own
  tables (`fn/*.json`).

## Findings

### AES forward S-box: which claims survive against the refreshed baseline (e6ac0d0)

All 36 `results/aes/*.circ.txt` files pass the exhaustive check. All use only
{AND, XOR, XNOR, NOT}, with no BUF, no dead gates, no constant or uncomputed outputs and no
free inversions. Five of them use `XNOR t a 0` as NOT, once each. Their G, A, GD and AD match
their file names, headers and `summary.json`, and every result meets its own caps.

| status | files |
|---|---|
| **survives** (new Pareto point on the published set) | 6 files, 5 tuples |
| equals a published tuple (not new) | 4 |
| dominated by a published circuit | 26 |

The surviving tuples (A, AD, G, GD):

| tuple | file(s) | strictly better than (published) |
|---|---|---|
| (28, 4, 131, 26) | `aes-nist-cost_gd-gd32-ad4-a28-g131-a28-gd26-ad4`, `...-gd36-ad4-a28-g131-a28-gd26-ad4` (two different circuits, XNOR 50 / 46) | a28-ad4-g131-gd31/gd32/gd36 and others |
| (32, 5, 108, 20) | `aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5` | a32-ad5-g109-gd20 and others |
| (33, 4, 108, 19) | `aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4` | a33-ad4-g108-gd20 and others |
| (33, 4, 110, 18) | `aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4` | a33-ad4-g110-gd20 and others |
| (41, 4, 126, 14) | `aes-nist-cost_gd-gd14-g126-a41-gd14-ad4` | none: a new trade-off point (fewer G at GD 14, but A 41 against 33) |

The four that equal a published tuple are (28,4,176,14), (28,4,153,15), (28,4,132,22) and
(35,3,139,27). Each improves its own start (a28-g177-gd14, a28-g154-gd15, a28-g132-gd23,
a35-ad3-g139-gd31), but NIST now publishes the same tuple.

### Smallest G under a gate-depth cap (A, AD free), caps 9..40

Results are **strictly better at GD <= 14, 18 and 19 only**:

| cap | published best | result best |
|---|---|---|
| 14 | 127 (A33 AD4, a33-ad4-g127-gd14) | **126** (A41 AD4 GD14) |
| 18 | 116 (A33 AD4 GD15) | **110** (A33 AD4 GD18) |
| 19 | 116 (A33 AD4 GD15) | **108** (A33 AD4 GD19) |

At cap 20 both are 108. At the other caps the published circuit is better, or there is no
result: 148 vs 150 at 11, 141 vs 146 at 12, 133 vs 137 at 13, 116 vs 122 at 15-17, and
106/105/104/103 vs 108 at 22-40. At cap 10 NIST has 159 (A59) and there is no result. At
cap 9 there is nothing on either side.

### Errors found

1. **chi3 results fail against the specified target.** `results/chi3/chi3-bgc-...g7...` and
   `chi3-gc6-...g7...` do not compute `table` from `sboxes.json` under msb/msb. They match
   that table only under lsb/lsb, i.e. they implement `table_a0_lsb` = [0,3,6,1,5,4,2,7]. The
   `.circ.fn.json` files that appeared next to them hold exactly that table. For example y0 =
   x0 ^ (x1 & ~x2), whereas the specified b_0 = a_0 ^ (~a_1 & a_2) with x0 = a_0. LEDGER.md,
   `results/MANIFEST.json` and `ledger-rows.jsonl` list both as verified. Reversing the input
   and output orders (x0<->x2, y0<->y2) gives the specified function with the same metrics, so
   the counts (G 7, A 3, GD 3, AD 1) stand once relabelled. As filed, the files are wrong.
   `independent/verify.py` against the `sboxes.json` table also rejects them.
2. **NOT vs XNOR-with-0 bookkeeping (counts only, G unaffected).** The headers, `summary.json`
   and `results/MANIFEST.json` of 5 AES results report `NOT=1` and one XNOR fewer than the file
   holds. The file writes `XNOR t a 0`. Affected: gd11-ad4-a51-g152, gd11-g152-a51,
   gd15-ad4-a30-g181, gd36-ad4-a30-g140, nocap-g717. Their `nist-format/` copies write a real
   `NOT`, so their `xxn` names are right. Note that the XX of the `results/aes` file (#XOR+#XNOR
   as written) is one higher than the XX in the NIST-style name.
3. **Stale bookkeeping.** `ledger-rows.jsonl` points to 4 files that were moved to
   `results/_superseded/`: fulladd-gc g5, gf16-inv-xag g16, gf16-mul-xag g31 and maj3-gc g4.
   All 4 still pass (G 5/16/31/4). `results/MANIFEST.json` does not list those 4. That is
   consistent with them being unclaimed.

No published circuit fails. All 102 verify, and none disagrees with its own file name,
circuit name, header tally (counts, depths, per-level histograms) or `nist/MANIFEST.json`. One
published circuit (a30-ad4-g205-gd15, both copies) has an XNOR with a constant operand. No
published file has dead gates or BUF.

All 36 `nist-format/` copies verify, carry correct NIST-style names, and are gate-for-gate
identical to a `results/aes` file once `XNOR a 0` is read as `NOT a`. Every `results/aes`
file has one copy.

For information only: 13 AES results contain gates that compute the same function as (or the
complement of) an earlier gate: 1 to 5 each, including 1 in the gd14-g126 survivor. Such gates
are usually kept for depth, but they are worth a look as possible savings. The published files
contain 61 such gates in total.

### Small S-boxes and functions

All 50 claimed small results other than chi3 verify. All use only gates allowed by the model
in their file name, and none uses XNOR-with-constant in a model without XNOR. The recounted
G/A/GD/AD match each file's name, header and summary. Per S-box (G):

| S-box | bgc | gc6 | S-box | bgc | gc6 |
|---|--:|--:|---|--:|--:|
| PRESENT | 14 | 13 | Serpent S0 | 14 | 13 |
| GIFT | 11 | 10 | Serpent S1 | 14 | 13 |
| SKINNY-64 | 11 | 8 | Serpent S2 | 13 | 12 |
| PRINCE | 16 | 15 | Serpent S3 | 15 | 15 |
| Midori Sb0 | 13 | 12 | Serpent S4 | 15 | 13 |
| Midori Sb1 | 16 | 15 | Serpent S5 | 15 | 14 |
| Piccolo | 10 | 8 | Serpent S6 | 14 | 13 |
| RECTANGLE | 12 | 11 | Serpent S7 | 16 | 14 |
| KLEIN | 17 | 15 | PRINTcipher | 6 | 6 |
| Noekeon | 12 | 10 | chi3 | 7 **(fails)** | 7 **(fails)** |
| PRIDE | 8 | 8 | Ascon | 16 | 15 |
| Keccak chi5 | 13 | 13 | | | |

Functions (xag model): maj3 G4 A1. fulladd G5 A1. gf16-inv G17 A5 and G15 A6. gf16-mul
G32 A9 and G30 A14. The full A/GD/AD per file is in the generated tables below.

### Comparison with LEDGER.md (read last)

LEDGER.md (mtime 19:37 UTC) was written against an older NIST snapshot. The results'
MANIFEST says the starts came from NIST commit 0876577, with "46 forward circuits" in
`aes-sbox/`, where e6ac0d0 has 78. Its AES claims do not hold against e6ac0d0:

- **3b "18 results are new on NIST's published set".** Against e6ac0d0, 6 files (5 tuples)
  are new. Of the 10 selected rows marked "yes", only 3 survive: 32 5 108 20, 28 4 131 26 and
  33 4 110 18. 28 4 153 15 and 28 4 176 14 equal published tuples. 32 5 129 15 is dominated
  by a32-ad4-g127-gd15. 36 4 134 14 is dominated by a33-ad4-g127-gd14. 39 4 137 13 is
  dominated by a35-ad4-g133-gd13. 45 4 146 12 is dominated by a45-ad4-g141-gd12. 49 4 150 11
  is dominated by a49-ad4-g148-gd11.
- **3c depth caps.** The ledger claims improvements at GD <= 11, 12, 13, 14, 18 and 19. Its
  published bests at 11-14 are stale: it gives 157/151/148/137 where e6ac0d0 has
  148/141/133/127. Only 14, 18 and 19 remain strict improvements. The ledger's "GD 10: none
  published (min GD 11)" is also stale: NIST now has GD-10 circuits (159 G, 163 G).
  `reports/aes-depth-caps.md` has the same stale published column.
- **3a.** Recounts agree (717 G A264 GD50 AD19; 108 G A33 AD5 GD26/GD23) and so does the
  conclusion "not new". In the 717-gate circuit, "NOT 1" is an `XNOR t a 0` in the file.
- **Sections 1-2.** Every G value agrees with the recount. The exception is the claim that
  chi (3-bit) "passed both verifiers": it fails against `sboxes.json` `table` (error 1). The
  ledger's "Every circuit listed here ... passed both verifiers" is false for chi3 under the
  stated target and bit order.

## Files

- `audit.py`: the auditor. Run `python3 -I nonlinear/boolflux/audit/audit.py --second-opinion`
  from the repo root.
- `audit.json`: machine-readable output (per-file metrics, checks, hashes, claims, Pareto
  status, depth caps, ledger and manifest comparisons, second opinion).
- `AUDIT-tables.md`: the generated tables, reproduced below. `run.log` is the console output.
  `fn/*.json` are the small-target tables passed to `verify.py`.

---

<!-- generated by audit.py at 2026-11-13T20:19:29Z; do not edit by hand -->
## Published forward AES circuits (recomputed)

| file | ok | A | AD | G | GD | XX | XNOR | NOT | XNOR-const | dead | name/header/manifest disagreement | flags |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|---|
| aes-sbox/aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt | yes | 28 | 4 | 131 | 31 | 103 | 43 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g131-gd32-xx103-47.circ.txt | yes | 28 | 4 | 131 | 32 | 103 | 47 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g131-gd36-xx103-28.circ.txt | yes | 28 | 4 | 131 | 36 | 103 | 28 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt | yes | 28 | 4 | 132 | 22 | 104 | 40 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g132-gd23-xx104-27.circ.txt | yes | 28 | 4 | 132 | 23 | 104 | 27 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g134-gd20-xx106-41.circ.txt | yes | 28 | 4 | 134 | 20 | 106 | 41 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g141-gd16-xx113-27.circ.txt | yes | 28 | 4 | 141 | 16 | 113 | 27 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt | yes | 28 | 4 | 153 | 15 | 125 | 29 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g154-gd15-xx126-28.circ.txt | yes | 28 | 4 | 154 | 15 | 126 | 28 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt | yes | 28 | 4 | 176 | 14 | 148 | 25 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad4-g177-gd14-xx149-24.circ.txt | yes | 28 | 4 | 177 | 14 | 149 | 24 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt | yes | 28 | 5 | 124 | 27 | 96 | 26 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt | yes | 28 | 5 | 128 | 20 | 100 | 27 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a28-ad5-g150-gd15-xx122-23.circ.txt | yes | 28 | 5 | 150 | 15 | 122 | 23 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt | yes | 29 | 5 | 137 | 32 | 108 | 22 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a29-ad5-g139-gd35-xx110-20.circ.txt | yes | 29 | 5 | 139 | 35 | 110 | 20 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a29-ad5-g182-gd16-xx153-29.circ.txt | yes | 29 | 5 | 182 | 16 | 153 | 29 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a29-ad5-g184-gd16-xx155-26.circ.txt | yes | 29 | 5 | 184 | 16 | 155 | 26 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a30-ad4-g147-gd36-xx117-13.circ.txt | yes | 30 | 4 | 147 | 36 | 117 | 13 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a30-ad4-g205-gd15-xx175-54.circ.txt | yes | 30 | 4 | 205 | 15 | 175 | 54 | 0 | 1 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt | yes | 32 | 4 | 117 | 19 | 85 | 6 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad4-g127-gd15-xx95-7.circ.txt | yes | 32 | 4 | 127 | 15 | 95 | 7 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad4-g137-gd18-xx105-7.circ.txt | yes | 32 | 4 | 137 | 18 | 105 | 7 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt | yes | 32 | 5 | 104 | 30 | 72 | 5 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g105-gd26-xx73-5.circ.txt | yes | 32 | 5 | 105 | 26 | 73 | 5 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g107-gd22-xx75-4.circ.txt | yes | 32 | 5 | 107 | 22 | 75 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt | yes | 32 | 5 | 109 | 20 | 77 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g110-gd22-xx78-3.circ.txt | yes | 32 | 5 | 110 | 22 | 78 | 3 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g110-gd23-xx78-3.circ.txt | yes | 32 | 5 | 110 | 23 | 78 | 3 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g122-gd16-xx90-15.circ.txt | yes | 32 | 5 | 122 | 16 | 90 | 15 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g127-gd15-xx95-20.circ.txt | yes | 32 | 5 | 127 | 15 | 95 | 20 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g128-gd15-xx96-21.circ.txt | yes | 32 | 5 | 128 | 15 | 96 | 21 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g131-gd15-xx99-17.circ.txt | yes | 32 | 5 | 131 | 15 | 99 | 17 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad5-g133-gd15-xx101-19.circ.txt | yes | 32 | 5 | 133 | 15 | 101 | 19 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | yes | 32 | 7 | 103 | 32 | 71 | 10 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | yes | 33 | 4 | 105 | 25 | 72 | 6 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | yes | 33 | 4 | 106 | 22 | 73 | 5 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt | yes | 33 | 4 | 108 | 20 | 75 | 5 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a33-ad4-g110-gd20-xx77-4.circ.txt | yes | 33 | 4 | 110 | 20 | 77 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt | yes | 33 | 4 | 116 | 15 | 83 | 7 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a33-ad4-g127-gd14-xx94-23.circ.txt | yes | 33 | 4 | 127 | 14 | 94 | 23 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a33-ad4-g128-gd14-xx95-20.circ.txt | yes | 33 | 4 | 128 | 14 | 95 | 20 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a34-ad4-g110-gd22-xx76-3.circ.txt | yes | 34 | 4 | 110 | 22 | 76 | 3 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a34-ad4-g124-gd15-xx90-4.circ.txt | yes | 34 | 4 | 124 | 15 | 90 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a34-ad4-g125-gd15-xx91-4.circ.txt | yes | 34 | 4 | 125 | 15 | 91 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a34-ad4-g128-gd15-xx94-4.circ.txt | yes | 34 | 4 | 128 | 15 | 94 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a34-ad4-g140-gd13-xx106-27.circ.txt | yes | 34 | 4 | 140 | 13 | 106 | 27 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a34-ad4-g142-gd13-xx108-28.circ.txt | yes | 34 | 4 | 142 | 13 | 108 | 28 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt | yes | 35 | 3 | 139 | 27 | 104 | 38 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g139-gd31-xx104-25.circ.txt | yes | 35 | 3 | 139 | 31 | 104 | 25 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g141-gd25-xx106-37.circ.txt | yes | 35 | 3 | 141 | 25 | 106 | 37 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g147-gd20-xx112-36.circ.txt | yes | 35 | 3 | 147 | 20 | 112 | 36 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g148-gd20-xx113-35.circ.txt | yes | 35 | 3 | 148 | 20 | 113 | 35 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g157-gd15-xx122-31.circ.txt | yes | 35 | 3 | 157 | 15 | 122 | 31 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g172-gd14-xx137-30.circ.txt | yes | 35 | 3 | 172 | 14 | 137 | 30 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad3-g183-gd13-xx148-29.circ.txt | yes | 35 | 3 | 183 | 13 | 148 | 29 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt | yes | 35 | 4 | 133 | 13 | 98 | 21 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a35-ad4-g135-gd13-xx100-21.circ.txt | yes | 35 | 4 | 135 | 13 | 100 | 21 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a36-ad4-g134-gd13-xx98-20.circ.txt | yes | 36 | 4 | 134 | 13 | 98 | 20 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a36-ad4-g137-gd14-xx101-22.circ.txt | yes | 36 | 4 | 137 | 14 | 101 | 22 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a36-ad4-g138-gd14-xx102-22.circ.txt | yes | 36 | 4 | 138 | 14 | 102 | 22 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a36-ad4-g141-gd13-xx105-21.circ.txt | yes | 36 | 4 | 141 | 13 | 105 | 21 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt | yes | 36 | 4 | 142 | 13 | 106 | 19 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a38-ad4-g148-gd13-xx110-24.circ.txt | yes | 38 | 4 | 148 | 13 | 110 | 24 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a39-ad4-g148-gd13-xx109-24.circ.txt | yes | 39 | 4 | 148 | 13 | 109 | 24 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt | yes | 45 | 4 | 141 | 12 | 96 | 25 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a45-ad4-g147-gd12-xx102-29.circ.txt | yes | 45 | 4 | 147 | 12 | 102 | 29 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a45-ad4-g151-gd12-xx106-26.circ.txt | yes | 45 | 4 | 151 | 12 | 106 | 26 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a46-ad3-g250-gd15-xx204-4.circ.txt | yes | 46 | 3 | 250 | 15 | 204 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a47-ad3-g186-gd22-xx139-7.circ.txt | yes | 47 | 3 | 186 | 22 | 139 | 7 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a47-ad3-g225-gd15-xx178-4.circ.txt | yes | 47 | 3 | 225 | 15 | 178 | 4 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt | yes | 49 | 4 | 148 | 11 | 99 | 23 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a49-ad4-g149-gd11-xx100-23.circ.txt | yes | 49 | 4 | 149 | 11 | 100 | 23 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a49-ad4-g164-gd11-xx115-32.circ.txt | yes | 49 | 4 | 164 | 11 | 115 | 32 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a51-ad4-g157-gd11-xx106-28.circ.txt | yes | 51 | 4 | 157 | 11 | 106 | 28 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a53-ad4-g157-gd11-xx104-31.circ.txt | yes | 53 | 4 | 157 | 11 | 104 | 31 | 0 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt | yes | 59 | 4 | 159 | 10 | 97 | 30 | 3 | 0 | 0 |  |  |
| aes-sbox/aes-sbox-a60-ad4-g163-gd10-xxn103-29-4.circ.txt | yes | 60 | 4 | 163 | 10 | 99 | 29 | 4 | 0 | 0 |  |  |
| old-2020/aes-sbox-fwd-g113-a32-d27-ad6.slp | yes | 32 | 6 | 113 | 27 | 81 | 4 | 0 | 0 | 0 |  |  |
| old-2020/aes-sbox-fwd-g115-a32-d28-ad6.slp | yes | 32 | 6 | 115 | 28 | 83 | 4 | 0 | 0 | 0 |  |  |
| old-2020/aes-sbox-fwd-g128-a34-d16-ad4.slp | yes | 34 | 4 | 128 | 16 | 94 | 4 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad5-g139-gd35-xx110-20.circ.txt | yes | 29 | 5 | 139 | 35 | 110 | 20 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad5-g140-gd37-xx111-14.ncff.txt | yes | 29 | 5 | 140 | 37 | 111 | 14 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad5-g141-gd32-xx112-14.ncff.txt | yes | 29 | 5 | 141 | 32 | 112 | 14 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad5-g161-gd24-xx132-1.ncff.txt | yes | 29 | 5 | 161 | 24 | 132 | 1 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad5-g184-gd16-xx155-26.circ.txt | yes | 29 | 5 | 184 | 16 | 155 | 26 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad5-g184-gd20-xx155-2.ncff.txt | yes | 29 | 5 | 184 | 20 | 155 | 2 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad6-g138-gd38-xx109-14.circ.txt | yes | 29 | 6 | 138 | 38 | 109 | 14 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad6-g138-gd38-xx109-14.ncff.txt | yes | 29 | 6 | 138 | 38 | 109 | 14 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad6-g139-gd33-xx110-14.ncff.txt | yes | 29 | 6 | 139 | 33 | 110 | 14 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad6-g154-gd27-xx125-1.ncff.txt | yes | 29 | 6 | 154 | 27 | 125 | 1 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a29-ad6-g181-gd21-xx152-2.ncff.txt | yes | 29 | 6 | 181 | 21 | 152 | 2 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a30-ad4-g147-gd36-xx117-13.circ.txt | yes | 30 | 4 | 147 | 36 | 117 | 13 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a30-ad4-g205-gd15-xx175-54.circ.txt | yes | 30 | 4 | 205 | 15 | 175 | 54 | 0 | 1 | 0 |  |  |
| sbox/aes-sbox-fwd-a32-ad5-g110-gd23-xx78-3.circ.txt | yes | 32 | 5 | 110 | 23 | 78 | 3 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a34-ad4-g110-gd23-xx76-3.circ.txt | yes | 34 | 4 | 110 | 23 | 76 | 3 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a34-ad4-g128-gd15-xx94-4.circ.txt | yes | 34 | 4 | 128 | 15 | 94 | 4 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a36-ad4-g138-gd14-xx102-22.circ.txt | yes | 36 | 4 | 138 | 14 | 102 | 22 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a39-ad4-g148-gd13-xx109-24.circ.txt | yes | 39 | 4 | 148 | 13 | 109 | 24 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a45-ad4-g151-gd12-xx106-26.circ.txt | yes | 45 | 4 | 151 | 12 | 106 | 26 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a46-ad3-g250-gd15-xx204-4.circ.txt | yes | 46 | 3 | 250 | 15 | 204 | 4 | 0 | 0 | 0 |  |  |
| sbox/aes-sbox-fwd-a47-ad3-g225-gd15-xx178-4.circ.txt | yes | 47 | 3 | 225 | 15 | 178 | 4 | 0 | 0 | 0 |  |  |

Published Pareto front on (A,AD,G,GD), verified circuits only: (28,4,131,31), (28,4,132,22), (28,4,134,20), (28,4,141,16), (28,4,153,15), (28,4,176,14), (28,5,124,27), (28,5,128,20), (28,5,150,15), (32,4,117,19), (32,4,127,15), (32,5,104,30), (32,5,105,26), (32,5,107,22), (32,5,109,20), (32,5,122,16), (32,7,103,32), (33,4,105,25), (33,4,106,22), (33,4,108,20), (33,4,116,15), (33,4,127,14), (34,4,140,13), (35,3,139,27), (35,3,141,25), (35,3,147,20), (35,3,157,15), (35,3,172,14), (35,3,183,13), (35,4,133,13), (45,4,141,12), (49,4,148,11), (59,4,159,10)

## AES results: recount and Pareto status

Tuple = (A, AD, G, GD). `pub<=`: verified published circuits with all four <= (= marks an identical tuple).

| result (file stem after `aes-nist-cost_gd-`) | verified | basis | A | AD | G | GD | XX | XNOR | NOT | XNOR w/ 0 | dead | pub<= | own strictly better | own identical | status |
|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|---|---|---|---|
| gd11-ad4-a49-g150-a49-gd11-ad4 | yes | ok | 49 | 4 | 150 | 11 | 101 | 51 | 0 | 0 | 0 | aes-sbox-a49-ad4-g148-gd11-xx99-23, aes-sbox-a49-ad4-g149-gd11-xx100-23 | - | - | **dominated-by-published** |
| gd11-ad4-a51-g152-a51-gd11-ad4 | yes | ok | 51 | 4 | 152 | 11 | 101 | 38 | 0 | 1 | 0 | aes-sbox-a49-ad4-g148-gd11-xx99-23, aes-sbox-a49-ad4-g149-gd11-xx100-23 | gd11-ad4-a49-g150-a49-gd11-ad4 | gd11-g152-a51-gd11-ad4 | **dominated-by-published** |
| gd11-ad4-a53-g152-a53-gd11-ad4 | yes | ok | 53 | 4 | 152 | 11 | 99 | 38 | 0 | 0 | 0 | aes-sbox-a49-ad4-g148-gd11-xx99-23, aes-sbox-a49-ad4-g149-gd11-xx100-23 | gd11-ad4-a49-g150-a49-gd11-ad4, gd11-ad4-a51-g152-a51-gd11-ad4, gd11-g152-a51-gd11-ad4 | - | **dominated-by-published** |
| gd11-g152-a51-gd11-ad4 | yes | ok | 51 | 4 | 152 | 11 | 101 | 46 | 0 | 1 | 0 | aes-sbox-a49-ad4-g148-gd11-xx99-23, aes-sbox-a49-ad4-g149-gd11-xx100-23 | gd11-ad4-a49-g150-a49-gd11-ad4 | gd11-ad4-a51-g152-a51-gd11-ad4 | **dominated-by-published** |
| gd12-ad4-a45-g146-a45-gd12-ad4 | yes | ok | 45 | 4 | 146 | 12 | 101 | 37 | 0 | 0 | 0 | aes-sbox-a45-ad4-g141-gd12-xx96-25 | - | gd12-g146-a45-gd12-ad4 | **dominated-by-published** |
| gd12-g146-a45-gd12-ad4 | yes | ok | 45 | 4 | 146 | 12 | 101 | 46 | 0 | 0 | 0 | aes-sbox-a45-ad4-g141-gd12-xx96-25 | - | gd12-ad4-a45-g146-a45-gd12-ad4 | **dominated-by-published** |
| gd13-ad4-a38-g139-a38-gd13-ad4 | yes | ok | 38 | 4 | 139 | 13 | 101 | 36 | 0 | 0 | 0 | aes-sbox-a35-ad4-g133-gd13-xx98-21, aes-sbox-a35-ad4-g135-gd13-xx100-21, aes-sbox-a36-ad4-g134-gd13-xx98-20 | gd13-g138-a38-gd13-ad4 | - | **dominated-by-published** |
| gd13-ad4-a39-g137-a39-gd13-ad4 | yes | ok | 39 | 4 | 137 | 13 | 98 | 41 | 0 | 0 | 0 | aes-sbox-a35-ad4-g133-gd13-xx98-21, aes-sbox-a35-ad4-g135-gd13-xx100-21, aes-sbox-a36-ad4-g134-gd13-xx98-20 | - | - | **dominated-by-published** |
| gd13-g138-a38-gd13-ad4 | yes | ok | 38 | 4 | 138 | 13 | 100 | 48 | 0 | 0 | 0 | aes-sbox-a35-ad4-g133-gd13-xx98-21, aes-sbox-a35-ad4-g135-gd13-xx100-21, aes-sbox-a36-ad4-g134-gd13-xx98-20 | - | - | **dominated-by-published** |
| gd14-ad4-a28-g176-a28-gd14-ad4 | yes | ok | 28 | 4 | 176 | 14 | 148 | 81 | 0 | 0 | 0 | =aes-sbox-a28-ad4-g176-gd14-xx148-25 | - | - | **equals-published** |
| gd14-ad4-a36-g134-a36-gd14-ad4 | yes | ok | 36 | 4 | 134 | 14 | 98 | 36 | 0 | 0 | 0 | aes-sbox-a33-ad4-g127-gd14-xx94-23, aes-sbox-a33-ad4-g128-gd14-xx95-20, aes-sbox-a35-ad4-g133-gd13-xx98-21, aes-sbox-a36-ad4-g134-gd13-xx98-20 | - | - | **dominated-by-published** |
| gd14-ad4-a36-g135-a36-gd14-ad4 | yes | ok | 36 | 4 | 135 | 14 | 99 | 49 | 0 | 0 | 0 | aes-sbox-a33-ad4-g127-gd14-xx94-23, aes-sbox-a33-ad4-g128-gd14-xx95-20, aes-sbox-a35-ad4-g133-gd13-xx98-21, aes-sbox-a35-ad4-g135-gd13-xx100-21, aes-sbox-a36-ad4-g134-gd13-xx98-20 | gd14-ad4-a36-g134-a36-gd14-ad4 | - | **dominated-by-published** |
| gd14-g126-a41-gd14-ad4 | yes | ok | 41 | 4 | 126 | 14 | 85 | 40 | 0 | 0 | 0 | - | - | - | **survives** |
| gd15-ad3-a46-g207-a46-gd15-ad3 | yes | ok | 46 | 3 | 207 | 15 | 161 | 87 | 0 | 0 | 0 | aes-sbox-a35-ad3-g157-gd15-xx122-31, aes-sbox-a35-ad3-g172-gd14-xx137-30, aes-sbox-a35-ad3-g183-gd13-xx148-29 | - | - | **dominated-by-published** |
| gd15-ad3-a47-g190-a47-gd15-ad3 | yes | ok | 47 | 3 | 190 | 15 | 143 | 59 | 0 | 0 | 0 | aes-sbox-a35-ad3-g157-gd15-xx122-31, aes-sbox-a35-ad3-g172-gd14-xx137-30, aes-sbox-a35-ad3-g183-gd13-xx148-29 | - | - | **dominated-by-published** |
| gd15-ad4-a28-g153-a28-gd15-ad4 | yes | ok | 28 | 4 | 153 | 15 | 125 | 64 | 0 | 0 | 0 | =aes-sbox-a28-ad4-g153-gd15-xx125-29 | - | - | **equals-published** |
| gd15-ad4-a30-g181-a30-gd15-ad4 | yes | ok | 30 | 4 | 181 | 15 | 151 | 71 | 0 | 1 | 0 | aes-sbox-a28-ad4-g153-gd15-xx125-29, aes-sbox-a28-ad4-g154-gd15-xx126-28, aes-sbox-a28-ad4-g176-gd14-xx148-25, aes-sbox-a28-ad4-g177-gd14-xx149-24 | gd14-ad4-a28-g176-a28-gd14-ad4, gd15-ad4-a28-g153-a28-gd15-ad4 | - | **dominated-by-published** |
| gd15-ad4-a34-g122-a34-gd15-ad4 | yes | ok | 34 | 4 | 122 | 15 | 88 | 39 | 0 | 0 | 0 | aes-sbox-a33-ad4-g116-gd15-xx83-7 | - | - | **dominated-by-published** |
| gd15-ad5-a32-g129-a32-gd15-ad5 | yes | ok | 32 | 5 | 129 | 15 | 97 | 40 | 0 | 0 | 0 | aes-sbox-a32-ad4-g127-gd15-xx95-7, aes-sbox-a32-ad5-g127-gd15-xx95-20, aes-sbox-a32-ad5-g128-gd15-xx96-21 | - | - | **dominated-by-published** |
| gd16-ad5-a29-g174-a29-gd16-ad5 | yes | ok | 29 | 5 | 174 | 16 | 145 | 61 | 0 | 0 | 0 | aes-sbox-a28-ad4-g141-gd16-xx113-27, aes-sbox-a28-ad4-g153-gd15-xx125-29, aes-sbox-a28-ad4-g154-gd15-xx126-28, aes-sbox-a28-ad5-g150-gd15-xx122-23 | gd15-ad4-a28-g153-a28-gd15-ad4 | - | **dominated-by-published** |
| gd20-ad4-a33-g108-a33-gd19-ad4 | yes | ok | 33 | 4 | 108 | 19 | 75 | 22 | 0 | 0 | 0 | - | - | - | **survives** |
| gd20-ad4-a33-g110-a33-gd18-ad4 | yes | ok | 33 | 4 | 110 | 18 | 77 | 26 | 0 | 0 | 0 | - | - | - | **survives** |
| gd20-ad5-a32-g108-a32-gd20-ad5 | yes | ok | 32 | 5 | 108 | 20 | 76 | 35 | 0 | 0 | 0 | - | - | - | **survives** |
| gd22-ad3-a47-g167-a47-gd22-ad3 | yes | ok | 47 | 3 | 167 | 22 | 120 | 50 | 0 | 0 | 0 | aes-sbox-a35-ad3-g147-gd20-xx112-36, aes-sbox-a35-ad3-g148-gd20-xx113-35, aes-sbox-a35-ad3-g157-gd15-xx122-31 | - | - | **dominated-by-published** |
| gd22-ad4-a34-g110-a34-gd20-ad4 | yes | ok | 34 | 4 | 110 | 20 | 76 | 22 | 0 | 0 | 0 | aes-sbox-a33-ad4-g108-gd20-xx75-5, aes-sbox-a33-ad4-g110-gd20-xx77-4 | gd20-ad4-a33-g108-a33-gd19-ad4, gd20-ad4-a33-g110-a33-gd18-ad4 | - | **dominated-by-published** |
| gd23-ad4-a28-g132-a28-gd22-ad4 | yes | ok | 28 | 4 | 132 | 22 | 104 | 50 | 0 | 0 | 0 | =aes-sbox-a28-ad4-g132-gd22-xx104-40 | - | - | **equals-published** |
| gd23-ad5-a32-g110-a32-gd22-ad5 | yes | ok | 32 | 5 | 110 | 22 | 78 | 25 | 0 | 0 | 0 | aes-sbox-a32-ad5-g107-gd22-xx75-4, aes-sbox-a32-ad5-g109-gd20-xx77-4, =aes-sbox-a32-ad5-g110-gd22-xx78-3 | gd20-ad5-a32-g108-a32-gd20-ad5 | - | **dominated-by-published** |
| gd27-ad6-g108-a33-gd23-ad5 | yes | ok | 33 | 5 | 108 | 23 | 75 | 30 | 0 | 0 | 0 | aes-sbox-a32-ad5-g107-gd22-xx75-4, aes-sbox-a33-ad4-g106-gd22-xx73-5, aes-sbox-a33-ad4-g108-gd20-xx75-5 | gd20-ad4-a33-g108-a33-gd19-ad4, gd20-ad5-a32-g108-a32-gd20-ad5 | - | **dominated-by-published** |
| gd31-ad3-a35-g139-a35-gd27-ad3 | yes | ok | 35 | 3 | 139 | 27 | 104 | 31 | 0 | 0 | 0 | =aes-sbox-a35-ad3-g139-gd27-xx104-38 | - | - | **equals-published** |
| gd32-ad4-a28-g131-a28-gd26-ad4 | yes | ok | 28 | 4 | 131 | 26 | 103 | 50 | 0 | 0 | 0 | - | - | gd36-ad4-a28-g131-a28-gd26-ad4 | **survives** |
| gd32-ad5-a29-g135-a29-gd28-ad5 | yes | ok | 29 | 5 | 135 | 28 | 106 | 50 | 0 | 0 | 0 | aes-sbox-a28-ad4-g132-gd22-xx104-40, aes-sbox-a28-ad4-g132-gd23-xx104-27, aes-sbox-a28-ad4-g134-gd20-xx106-41, aes-sbox-a28-ad5-g124-gd27-xx96-26, aes-sbox-a28-ad5-g128-gd20-xx100-27 | gd23-ad4-a28-g132-a28-gd22-ad4, gd32-ad4-a28-g131-a28-gd26-ad4, gd36-ad4-a28-g131-a28-gd26-ad4 | - | **dominated-by-published** |
| gd35-ad5-a29-g136-a29-gd30-ad5 | yes | ok | 29 | 5 | 136 | 30 | 107 | 56 | 0 | 0 | 0 | aes-sbox-a28-ad4-g132-gd22-xx104-40, aes-sbox-a28-ad4-g132-gd23-xx104-27, aes-sbox-a28-ad4-g134-gd20-xx106-41, aes-sbox-a28-ad5-g124-gd27-xx96-26, aes-sbox-a28-ad5-g128-gd20-xx100-27 | gd23-ad4-a28-g132-a28-gd22-ad4, gd32-ad4-a28-g131-a28-gd26-ad4, gd32-ad5-a29-g135-a29-gd28-ad5, gd36-ad4-a28-g131-a28-gd26-ad4 | - | **dominated-by-published** |
| gd36-ad4-a28-g131-a28-gd26-ad4 | yes | ok | 28 | 4 | 131 | 26 | 103 | 46 | 0 | 0 | 0 | - | - | gd32-ad4-a28-g131-a28-gd26-ad4 | **survives** |
| gd36-ad4-a30-g140-a30-gd32-ad4 | yes | ok | 30 | 4 | 140 | 32 | 110 | 67 | 0 | 1 | 0 | aes-sbox-a28-ad4-g131-gd31-xx103-43, aes-sbox-a28-ad4-g131-gd32-xx103-47, aes-sbox-a28-ad4-g132-gd22-xx104-40, aes-sbox-a28-ad4-g132-gd23-xx104-27, aes-sbox-a28-ad4-g134-gd20-xx106-41 | gd23-ad4-a28-g132-a28-gd22-ad4, gd32-ad4-a28-g131-a28-gd26-ad4, gd36-ad4-a28-g131-a28-gd26-ad4 | - | **dominated-by-published** |
| nocap-g108-a33-gd26-ad5 | yes | ok | 33 | 5 | 108 | 26 | 75 | 21 | 0 | 0 | 0 | aes-sbox-a32-ad5-g105-gd26-xx73-5, aes-sbox-a32-ad5-g107-gd22-xx75-4, aes-sbox-a33-ad4-g105-gd25-xx72-6, aes-sbox-a33-ad4-g106-gd22-xx73-5, aes-sbox-a33-ad4-g108-gd20-xx75-5 | gd20-ad4-a33-g108-a33-gd19-ad4, gd20-ad5-a32-g108-a32-gd20-ad5, gd27-ad6-g108-a33-gd23-ad5 | - | **dominated-by-published** |
| nocap-g717-a264-gd50-ad19 | yes | ok | 264 | 19 | 717 | 50 | 453 | 195 | 0 | 1 | 0 | aes-sbox-a28-ad4-g131-gd31-xx103-43, aes-sbox-a28-ad4-g131-gd32-xx103-47, aes-sbox-a28-ad4-g131-gd36-xx103-28, aes-sbox-a28-ad4-g132-gd22-xx104-40, aes-sbox-a28-ad4-g132-gd23-xx104-27, aes-sbox-a28-ad4-g134-gd20-xx106-41, aes-sbox-a28-ad4-g141-gd16-xx113-27, aes-sbox-a28-ad4-g153-gd15-xx125-29, aes-sbox-a28-ad4-g154-gd15-xx126-28, aes-sbox-a28-ad4-g176-gd14-xx148-25, aes-sbox-a28-ad4-g177-gd14-xx149-24, aes-sbox-a28-ad5-g124-gd27-xx96-26, aes-sbox-a28-ad5-g128-gd20-xx100-27, aes-sbox-a28-ad5-g150-gd15-xx122-23, aes-sbox-a29-ad5-g137-gd32-xx108-22, aes-sbox-a29-ad5-g139-gd35-xx110-20, aes-sbox-a29-ad5-g182-gd16-xx153-29, aes-sbox-a29-ad5-g184-gd16-xx155-26, aes-sbox-a30-ad4-g147-gd36-xx117-13, aes-sbox-a30-ad4-g205-gd15-xx175-54, aes-sbox-a32-ad4-g117-gd19-xx85-6, aes-sbox-a32-ad4-g127-gd15-xx95-7, aes-sbox-a32-ad4-g137-gd18-xx105-7, aes-sbox-a32-ad5-g104-gd30-xx72-5, aes-sbox-a32-ad5-g105-gd26-xx73-5, aes-sbox-a32-ad5-g107-gd22-xx75-4, aes-sbox-a32-ad5-g109-gd20-xx77-4, aes-sbox-a32-ad5-g110-gd22-xx78-3, aes-sbox-a32-ad5-g110-gd23-xx78-3, aes-sbox-a32-ad5-g122-gd16-xx90-15, aes-sbox-a32-ad5-g127-gd15-xx95-20, aes-sbox-a32-ad5-g128-gd15-xx96-21, aes-sbox-a32-ad5-g131-gd15-xx99-17, aes-sbox-a32-ad5-g133-gd15-xx101-19, aes-sbox-a32-ad7-g103-gd32-xx71-10, aes-sbox-a33-ad4-g105-gd25-xx72-6, aes-sbox-a33-ad4-g106-gd22-xx73-5, aes-sbox-a33-ad4-g108-gd20-xx75-5, aes-sbox-a33-ad4-g110-gd20-xx77-4, aes-sbox-a33-ad4-g116-gd15-xx83-7, aes-sbox-a33-ad4-g127-gd14-xx94-23, aes-sbox-a33-ad4-g128-gd14-xx95-20, aes-sbox-a34-ad4-g110-gd22-xx76-3, aes-sbox-a34-ad4-g124-gd15-xx90-4, aes-sbox-a34-ad4-g125-gd15-xx91-4, aes-sbox-a34-ad4-g128-gd15-xx94-4, aes-sbox-a34-ad4-g140-gd13-xx106-27, aes-sbox-a34-ad4-g142-gd13-xx108-28, aes-sbox-a35-ad3-g139-gd27-xx104-38, aes-sbox-a35-ad3-g139-gd31-xx104-25, aes-sbox-a35-ad3-g141-gd25-xx106-37, aes-sbox-a35-ad3-g147-gd20-xx112-36, aes-sbox-a35-ad3-g148-gd20-xx113-35, aes-sbox-a35-ad3-g157-gd15-xx122-31, aes-sbox-a35-ad3-g172-gd14-xx137-30, aes-sbox-a35-ad3-g183-gd13-xx148-29, aes-sbox-a35-ad4-g133-gd13-xx98-21, aes-sbox-a35-ad4-g135-gd13-xx100-21, aes-sbox-a36-ad4-g134-gd13-xx98-20, aes-sbox-a36-ad4-g137-gd14-xx101-22, aes-sbox-a36-ad4-g138-gd14-xx102-22, aes-sbox-a36-ad4-g141-gd13-xx105-21, aes-sbox-a36-ad4-g142-gd13-xx106-19, aes-sbox-a38-ad4-g148-gd13-xx110-24, aes-sbox-a39-ad4-g148-gd13-xx109-24, aes-sbox-a45-ad4-g141-gd12-xx96-25, aes-sbox-a45-ad4-g147-gd12-xx102-29, aes-sbox-a45-ad4-g151-gd12-xx106-26, aes-sbox-a46-ad3-g250-gd15-xx204-4, aes-sbox-a47-ad3-g186-gd22-xx139-7, aes-sbox-a47-ad3-g225-gd15-xx178-4, aes-sbox-a49-ad4-g148-gd11-xx99-23, aes-sbox-a49-ad4-g149-gd11-xx100-23, aes-sbox-a49-ad4-g164-gd11-xx115-32, aes-sbox-a51-ad4-g157-gd11-xx106-28, aes-sbox-a53-ad4-g157-gd11-xx104-31, aes-sbox-a59-ad4-g159-gd10-xxn100-30-3, aes-sbox-a60-ad4-g163-gd10-xxn103-29-4, aes-sbox-fwd-g113-a32-d27-ad6, aes-sbox-fwd-g115-a32-d28-ad6, aes-sbox-fwd-g128-a34-d16-ad4, aes-sbox-fwd-a29-ad5-g139-gd35-xx110-20, aes-sbox-fwd-a29-ad5-g140-gd37-xx111-14, aes-sbox-fwd-a29-ad5-g141-gd32-xx112-14, aes-sbox-fwd-a29-ad5-g161-gd24-xx132-1, aes-sbox-fwd-a29-ad5-g184-gd16-xx155-26, aes-sbox-fwd-a29-ad5-g184-gd20-xx155-2, aes-sbox-fwd-a29-ad6-g138-gd38-xx109-14, aes-sbox-fwd-a29-ad6-g138-gd38-xx109-14, aes-sbox-fwd-a29-ad6-g139-gd33-xx110-14, aes-sbox-fwd-a29-ad6-g154-gd27-xx125-1, aes-sbox-fwd-a29-ad6-g181-gd21-xx152-2, aes-sbox-fwd-a30-ad4-g147-gd36-xx117-13, aes-sbox-fwd-a30-ad4-g205-gd15-xx175-54, aes-sbox-fwd-a32-ad5-g110-gd23-xx78-3, aes-sbox-fwd-a34-ad4-g110-gd23-xx76-3, aes-sbox-fwd-a34-ad4-g128-gd15-xx94-4, aes-sbox-fwd-a36-ad4-g138-gd14-xx102-22, aes-sbox-fwd-a39-ad4-g148-gd13-xx109-24, aes-sbox-fwd-a45-ad4-g151-gd12-xx106-26, aes-sbox-fwd-a46-ad3-g250-gd15-xx204-4, aes-sbox-fwd-a47-ad3-g225-gd15-xx178-4 | gd11-ad4-a49-g150-a49-gd11-ad4, gd11-ad4-a51-g152-a51-gd11-ad4, gd11-ad4-a53-g152-a53-gd11-ad4, gd11-g152-a51-gd11-ad4, gd12-ad4-a45-g146-a45-gd12-ad4, gd12-g146-a45-gd12-ad4, gd13-ad4-a38-g139-a38-gd13-ad4, gd13-ad4-a39-g137-a39-gd13-ad4, gd13-g138-a38-gd13-ad4, gd14-ad4-a28-g176-a28-gd14-ad4, gd14-ad4-a36-g134-a36-gd14-ad4, gd14-ad4-a36-g135-a36-gd14-ad4, gd14-g126-a41-gd14-ad4, gd15-ad3-a46-g207-a46-gd15-ad3, gd15-ad3-a47-g190-a47-gd15-ad3, gd15-ad4-a28-g153-a28-gd15-ad4, gd15-ad4-a30-g181-a30-gd15-ad4, gd15-ad4-a34-g122-a34-gd15-ad4, gd15-ad5-a32-g129-a32-gd15-ad5, gd16-ad5-a29-g174-a29-gd16-ad5, gd20-ad4-a33-g108-a33-gd19-ad4, gd20-ad4-a33-g110-a33-gd18-ad4, gd20-ad5-a32-g108-a32-gd20-ad5, gd22-ad3-a47-g167-a47-gd22-ad3, gd22-ad4-a34-g110-a34-gd20-ad4, gd23-ad4-a28-g132-a28-gd22-ad4, gd23-ad5-a32-g110-a32-gd22-ad5, gd27-ad6-g108-a33-gd23-ad5, gd31-ad3-a35-g139-a35-gd27-ad3, gd32-ad4-a28-g131-a28-gd26-ad4, gd32-ad5-a29-g135-a29-gd28-ad5, gd35-ad5-a29-g136-a29-gd30-ad5, gd36-ad4-a28-g131-a28-gd26-ad4, gd36-ad4-a30-g140-a30-gd32-ad4, nocap-g108-a33-gd26-ad5 | - | **dominated-by-published** |

### Surviving tuples (duplicates collapsed)

- (28,4,131,26): aes-nist-cost_gd-gd32-ad4-a28-g131-a28-gd26-ad4.circ.txt, aes-nist-cost_gd-gd36-ad4-a28-g131-a28-gd26-ad4.circ.txt
  - strictly dominates published: aes-sbox-a28-ad4-g131-gd31-xx103-43.circ.txt, aes-sbox-a28-ad4-g131-gd32-xx103-47.circ.txt, aes-sbox-a28-ad4-g131-gd36-xx103-28.circ.txt, aes-sbox-a29-ad5-g137-gd32-xx108-22.circ.txt, aes-sbox-a29-ad5-g139-gd35-xx110-20.circ.txt, aes-sbox-a30-ad4-g147-gd36-xx117-13.circ.txt, aes-sbox-fwd-a29-ad5-g139-gd35-xx110-20.circ.txt, aes-sbox-fwd-a29-ad5-g140-gd37-xx111-14.ncff.txt, aes-sbox-fwd-a29-ad5-g141-gd32-xx112-14.ncff.txt, aes-sbox-fwd-a29-ad6-g138-gd38-xx109-14.circ.txt, aes-sbox-fwd-a29-ad6-g138-gd38-xx109-14.ncff.txt, aes-sbox-fwd-a29-ad6-g139-gd33-xx110-14.ncff.txt, aes-sbox-fwd-a29-ad6-g154-gd27-xx125-1.ncff.txt, aes-sbox-fwd-a30-ad4-g147-gd36-xx117-13.circ.txt
- (32,5,108,20): aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt
  - strictly dominates published: aes-sbox-a32-ad5-g109-gd20-xx77-4.circ.txt, aes-sbox-a32-ad5-g110-gd22-xx78-3.circ.txt, aes-sbox-a32-ad5-g110-gd23-xx78-3.circ.txt, aes-sbox-fwd-a32-ad5-g110-gd23-xx78-3.circ.txt, aes-sbox-fwd-g113-a32-d27-ad6.slp, aes-sbox-fwd-g115-a32-d28-ad6.slp
- (33,4,108,19): aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt
  - strictly dominates published: aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt, aes-sbox-a33-ad4-g110-gd20-xx77-4.circ.txt, aes-sbox-a34-ad4-g110-gd22-xx76-3.circ.txt, aes-sbox-fwd-a34-ad4-g110-gd23-xx76-3.circ.txt
- (33,4,110,18): aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt
  - strictly dominates published: aes-sbox-a33-ad4-g110-gd20-xx77-4.circ.txt, aes-sbox-a34-ad4-g110-gd22-xx76-3.circ.txt, aes-sbox-fwd-a34-ad4-g110-gd23-xx76-3.circ.txt
- (41,4,126,14): aes-nist-cost_gd-gd14-g126-a41-gd14-ad4.circ.txt
  - strictly dominates published: none (new trade-off point only)

### Results equal to a published tuple (not new)

- aes-nist-cost_gd-gd14-ad4-a28-g176-a28-gd14-ad4.circ.txt (28,4,176,14) = aes-sbox-a28-ad4-g176-gd14-xx148-25.circ.txt
- aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt (28,4,153,15) = aes-sbox-a28-ad4-g153-gd15-xx125-29.circ.txt
- aes-nist-cost_gd-gd23-ad4-a28-g132-a28-gd22-ad4.circ.txt (28,4,132,22) = aes-sbox-a28-ad4-g132-gd22-xx104-40.circ.txt
- aes-nist-cost_gd-gd31-ad3-a35-g139-a35-gd27-ad3.circ.txt (35,3,139,27) = aes-sbox-a35-ad3-g139-gd27-xx104-38.circ.txt

### Header / file-name / summary.json disagreements for AES results

- aes-nist-cost_gd-gd11-ad4-a51-g152-a51-gd11-ad4.circ.txt: header: #NOT 1->0; #XNOR 37->38 | summary: #NOT 1->0; #XNOR 37->38
- aes-nist-cost_gd-gd11-g152-a51-gd11-ad4.circ.txt: header: #NOT 1->0; #XNOR 45->46 | summary: #NOT 1->0; #XNOR 45->46
- aes-nist-cost_gd-gd15-ad4-a30-g181-a30-gd15-ad4.circ.txt: header: #NOT 1->0; #XNOR 70->71 | summary: #NOT 1->0; #XNOR 70->71
- aes-nist-cost_gd-gd36-ad4-a30-g140-a30-gd32-ad4.circ.txt: header: #NOT 1->0; #XNOR 66->67 | summary: #NOT 1->0; #XNOR 66->67
- aes-nist-cost_gd-nocap-g717-a264-gd50-ad19.circ.txt: header: #NOT 1->0; #XNOR 194->195 | summary: #NOT 1->0; #XNOR 194->195

## Smallest G under a gate-depth cap

| GD cap | best published G (A,AD,G,GD) | file | best result G (A,AD,G,GD) | file | strict improvement |
|--:|---|---|---|---|---|
| 9 | None  | - | None  | - | no |
| 10 | 159 (59,4,159,10) | aes-sbox-a59-ad4-g159-gd10-xxn100-30-3.circ.txt | None  | - | no |
| 11 | 148 (49,4,148,11) | aes-sbox-a49-ad4-g148-gd11-xx99-23.circ.txt | 150 (49,4,150,11) | aes-nist-cost_gd-gd11-ad4-a49-g150-a49-gd11-ad4.circ.txt | no |
| 12 | 141 (45,4,141,12) | aes-sbox-a45-ad4-g141-gd12-xx96-25.circ.txt | 146 (45,4,146,12) | aes-nist-cost_gd-gd12-ad4-a45-g146-a45-gd12-ad4.circ.txt | no |
| 13 | 133 (35,4,133,13) | aes-sbox-a35-ad4-g133-gd13-xx98-21.circ.txt | 137 (39,4,137,13) | aes-nist-cost_gd-gd13-ad4-a39-g137-a39-gd13-ad4.circ.txt | no |
| 14 | 127 (33,4,127,14) | aes-sbox-a33-ad4-g127-gd14-xx94-23.circ.txt | 126 (41,4,126,14) | aes-nist-cost_gd-gd14-g126-a41-gd14-ad4.circ.txt | **yes** |
| 15 | 116 (33,4,116,15) | aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt | 122 (34,4,122,15) | aes-nist-cost_gd-gd15-ad4-a34-g122-a34-gd15-ad4.circ.txt | no |
| 16 | 116 (33,4,116,15) | aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt | 122 (34,4,122,15) | aes-nist-cost_gd-gd15-ad4-a34-g122-a34-gd15-ad4.circ.txt | no |
| 17 | 116 (33,4,116,15) | aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt | 122 (34,4,122,15) | aes-nist-cost_gd-gd15-ad4-a34-g122-a34-gd15-ad4.circ.txt | no |
| 18 | 116 (33,4,116,15) | aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt | 110 (33,4,110,18) | aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt | **yes** |
| 19 | 116 (33,4,116,15) | aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | **yes** |
| 20 | 108 (33,4,108,20) | aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 21 | 108 (33,4,108,20) | aes-sbox-a33-ad4-g108-gd20-xx75-5.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 22 | 106 (33,4,106,22) | aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 23 | 106 (33,4,106,22) | aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 24 | 106 (33,4,106,22) | aes-sbox-a33-ad4-g106-gd22-xx73-5.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 25 | 105 (33,4,105,25) | aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 26 | 105 (33,4,105,25) | aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 27 | 105 (33,4,105,25) | aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 28 | 105 (33,4,105,25) | aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 29 | 105 (33,4,105,25) | aes-sbox-a33-ad4-g105-gd25-xx72-6.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 30 | 104 (32,5,104,30) | aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 31 | 104 (32,5,104,30) | aes-sbox-a32-ad5-g104-gd30-xx72-5.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 32 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 33 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 34 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 35 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 36 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 37 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 38 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 39 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |
| 40 | 103 (32,7,103,32) | aes-sbox-a32-ad7-g103-gd32-xx71-10.circ.txt | 108 (33,4,108,19) | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt | no |

## Small S-boxes and functions

| target | model | file | verified | model gates ok | G | A | GD | AD | counts | dead | name/header/summary disagreement | flags |
|---|---|---|---|---|--:|--:|--:|--:|---|--:|---|---|
| fulladd | gc | fulladd-gc-cost-nocap-g5-a2-gd4-ad1.circ.txt | yes | yes | 5 | 2 | 4 | 1 | AND=1 ANDN=1 XOR=3 | 0 |  | in _superseded/ (not claimed) |
| gf16-inv | xag | gf16-inv-xag-a_cost-nocap-g16-a5-gd12-ad4.circ.txt | yes | yes | 16 | 5 | 12 | 4 | AND=5 XOR=11 | 0 |  | in _superseded/ (not claimed) |
| gf16-mul | xag | gf16-mul-xag-a_cost-nocap-g31-a9-gd7-ad1.circ.txt | yes | yes | 31 | 9 | 7 | 1 | AND=9 XOR=22 | 0 |  | in _superseded/ (not claimed) |
| maj3 | gc | maj3-gc-cost-nocap-g4-a2-gd3-ad1.circ.txt | yes | yes | 4 | 2 | 3 | 1 | AND=2 XOR=2 | 0 |  | in _superseded/ (not claimed) |
| ascon | bgc | ascon-bgc-cost-nocap-g16-a5-gd7-ad2.circ.txt | yes | yes | 16 | 5 | 7 | 2 | AND=2 NOT=1 OR=3 XOR=10 | 0 |  |  |
| ascon | gc6 | ascon-gc6-cost-nocap-g15-a5-gd4-ad1.circ.txt | yes | yes | 15 | 5 | 4 | 1 | AND=1 NAND=1 OR=3 XNOR=2 XOR=8 | 0 |  |  |
| chi3 | bgc | chi3-bgc-cost-nocap-g7-a3-gd3-ad1.circ.txt | **NO** | yes | 7 | 3 | 3 | 1 | AND=2 OR=1 XOR=4 | 0 |  | first mismatch {'output': 'y0', 'x': 1}; bit orders (in/out) that match table: ['lsb/lsb'] |
| chi3 | gc6 | chi3-gc6-cost-nocap-g7-a3-gd3-ad1.circ.txt | **NO** | yes | 7 | 3 | 3 | 1 | AND=2 OR=1 XOR=4 | 0 |  | first mismatch {'output': 'y0', 'x': 1}; bit orders (in/out) that match table: ['lsb/lsb'] |
| fulladd | xag | fulladd-xag-a_cost-nocap-g5-a1-gd3-ad1.circ.txt | yes | yes | 5 | 1 | 3 | 1 | AND=1 XOR=4 | 0 |  |  |
| gf16-inv | xag | gf16-inv-xag-a_cost-nocap-g17-a5-gd12-ad4.circ.txt | yes | yes | 17 | 5 | 12 | 4 | AND=5 XOR=12 | 0 |  |  |
| gf16-inv | xag | gf16-inv-xag-cost-nocap-g15-a6-gd12-ad5.circ.txt | yes | yes | 15 | 6 | 12 | 5 | AND=6 XOR=9 | 0 |  |  |
| gf16-mul | xag | gf16-mul-xag-a_cost-nocap-g30-a14-gd6-ad1.circ.txt | yes | yes | 30 | 14 | 6 | 1 | AND=14 XOR=16 | 0 |  |  |
| gf16-mul | xag | gf16-mul-xag-a_cost-nocap-g32-a9-gd9-ad1.circ.txt | yes | yes | 32 | 9 | 9 | 1 | AND=9 XOR=23 | 0 |  |  |
| gift | bgc | gift-bgc-cost-nocap-g11-a4-gd6-ad3.circ.txt | yes | yes | 11 | 4 | 6 | 3 | AND=3 NOT=1 OR=1 XOR=6 | 0 |  |  |
| gift | gc6 | gift-gc6-cost-nocap-g10-a4-gd10-ad4.circ.txt | yes | yes | 10 | 4 | 10 | 4 | AND=3 OR=1 XNOR=2 XOR=4 | 0 |  |  |
| keccak_chi5 | bgc | keccak_chi5-bgc-cost-nocap-g13-a5-gd6-ad2.circ.txt | yes | yes | 13 | 5 | 6 | 2 | AND=3 OR=2 XOR=8 | 0 |  |  |
| keccak_chi5 | gc6 | keccak_chi5-gc6-cost-nocap-g13-a5-gd3-ad1.circ.txt | yes | yes | 13 | 5 | 3 | 1 | AND=1 NAND=2 NOR=1 OR=1 XNOR=5 XOR=3 | 0 |  |  |
| klein | bgc | klein-bgc-cost-nocap-g17-a7-gd14-ad6.circ.txt | yes | yes | 17 | 7 | 14 | 6 | AND=4 NOT=1 OR=3 XOR=9 | 0 |  |  |
| klein | gc6 | klein-gc6-cost-nocap-g15-a7-gd14-ad7.circ.txt | yes | yes | 15 | 7 | 14 | 7 | AND=4 NAND=1 OR=2 XNOR=4 XOR=4 | 0 |  |  |
| maj3 | xag | maj3-xag-a_cost-nocap-g4-a1-gd3-ad1.circ.txt | yes | yes | 4 | 1 | 3 | 1 | AND=1 XOR=3 | 0 |  |  |
| midori_sb0 | bgc | midori_sb0-bgc-cost-nocap-g13-a4-gd11-ad4.circ.txt | yes | yes | 13 | 4 | 11 | 4 | AND=2 NOT=1 OR=2 XOR=8 | 0 |  |  |
| midori_sb0 | gc6 | midori_sb0-gc6-cost-nocap-g12-a4-gd9-ad4.circ.txt | yes | yes | 12 | 4 | 9 | 4 | AND=2 NAND=2 XNOR=2 XOR=6 | 0 |  |  |
| midori_sb1 | bgc | midori_sb1-bgc-cost-nocap-g16-a8-gd8-ad5.circ.txt | yes | yes | 16 | 8 | 8 | 5 | AND=4 NOT=1 OR=4 XOR=7 | 0 |  |  |
| midori_sb1 | gc6 | midori_sb1-gc6-cost-nocap-g15-a11-gd6-ad5.circ.txt | yes | yes | 15 | 11 | 6 | 5 | AND=2 NAND=1 NOR=6 OR=2 XNOR=1 XOR=3 | 0 |  |  |
| noekeon | bgc | noekeon-bgc-cost-nocap-g12-a5-gd7-ad3.circ.txt | yes | yes | 12 | 5 | 7 | 3 | AND=3 NOT=1 OR=2 XOR=6 | 0 |  |  |
| noekeon | gc6 | noekeon-gc6-cost-nocap-g10-a4-gd7-ad3.circ.txt | yes | yes | 10 | 4 | 7 | 3 | AND=3 NAND=1 XNOR=1 XOR=5 | 0 |  |  |
| piccolo | bgc | piccolo-bgc-cost-nocap-g10-a4-gd5-ad2.circ.txt | yes | yes | 10 | 4 | 5 | 2 | AND=1 NOT=2 OR=3 XOR=4 | 0 |  |  |
| piccolo | gc6 | piccolo-gc6-cost-nocap-g8-a4-gd4-ad2.circ.txt | yes | yes | 8 | 4 | 4 | 2 | NOR=3 OR=1 XOR=4 | 0 |  |  |
| present | bgc | present-bgc-cost-nocap-g14-a4-gd12-ad4.circ.txt | yes | yes | 14 | 4 | 12 | 4 | AND=3 NOT=1 OR=1 XOR=9 | 0 |  |  |
| present | gc6 | present-gc6-cost-nocap-g13-a4-gd10-ad4.circ.txt | yes | yes | 13 | 4 | 10 | 4 | NAND=2 NOR=2 XNOR=4 XOR=5 | 0 |  |  |
| pride | bgc | pride-bgc-cost-nocap-g8-a4-gd6-ad3.circ.txt | yes | yes | 8 | 4 | 6 | 3 | AND=4 XOR=4 | 0 |  |  |
| pride | gc6 | pride-gc6-cost-nocap-g8-a4-gd6-ad3.circ.txt | yes | yes | 8 | 4 | 6 | 3 | AND=3 NAND=1 XNOR=1 XOR=3 | 0 |  |  |
| prince | bgc | prince-bgc-cost-nocap-g16-a7-gd10-ad5.circ.txt | yes | yes | 16 | 7 | 10 | 5 | AND=2 NOT=1 OR=5 XOR=8 | 0 |  |  |
| prince | gc6 | prince-gc6-cost-nocap-g15-a9-gd9-ad6.circ.txt | yes | yes | 15 | 9 | 9 | 6 | AND=1 NAND=2 NOR=3 OR=3 XNOR=4 XOR=2 | 0 |  |  |
| printcipher | bgc | printcipher-bgc-cost-nocap-g6-a3-gd6-ad3.circ.txt | yes | yes | 6 | 3 | 6 | 3 | AND=2 OR=1 XOR=3 | 0 |  |  |
| printcipher | gc6 | printcipher-gc6-cost-nocap-g6-a3-gd6-ad3.circ.txt | yes | yes | 6 | 3 | 6 | 3 | AND=1 NAND=1 OR=1 XNOR=1 XOR=2 | 0 |  |  |
| rectangle | bgc | rectangle-bgc-cost-nocap-g12-a4-gd7-ad3.circ.txt | yes | yes | 12 | 4 | 7 | 3 | AND=2 NOT=1 OR=2 XOR=7 | 0 |  |  |
| rectangle | gc6 | rectangle-gc6-cost-nocap-g11-a4-gd8-ad4.circ.txt | yes | yes | 11 | 4 | 8 | 4 | AND=2 NOR=1 OR=1 XNOR=5 XOR=2 | 0 |  |  |
| serpent_s0 | bgc | serpent_s0-bgc-cost-nocap-g14-a4-gd10-ad3.circ.txt | yes | yes | 14 | 4 | 10 | 3 | AND=4 NOT=1 XOR=9 | 0 |  |  |
| serpent_s0 | gc6 | serpent_s0-gc6-cost-nocap-g13-a5-gd8-ad4.circ.txt | yes | yes | 13 | 5 | 8 | 4 | AND=1 NAND=2 NOR=1 OR=1 XNOR=3 XOR=5 | 0 |  |  |
| serpent_s1 | bgc | serpent_s1-bgc-cost-nocap-g14-a4-gd10-ad3.circ.txt | yes | yes | 14 | 4 | 10 | 3 | NOT=1 OR=4 XOR=9 | 0 |  |  |
| serpent_s1 | gc6 | serpent_s1-gc6-cost-nocap-g13-a4-gd12-ad4.circ.txt | yes | yes | 13 | 4 | 12 | 4 | AND=1 NAND=2 NOR=1 XNOR=3 XOR=6 | 0 |  |  |
| serpent_s2 | bgc | serpent_s2-bgc-cost-nocap-g13-a4-gd10-ad4.circ.txt | yes | yes | 13 | 4 | 10 | 4 | AND=2 NOT=1 OR=2 XOR=8 | 0 |  |  |
| serpent_s2 | gc6 | serpent_s2-gc6-cost-nocap-g12-a4-gd9-ad4.circ.txt | yes | yes | 12 | 4 | 9 | 4 | NAND=1 NOR=2 OR=1 XNOR=5 XOR=3 | 0 |  |  |
| serpent_s3 | bgc | serpent_s3-bgc-cost-nocap-g15-a7-gd9-ad4.circ.txt | yes | yes | 15 | 7 | 9 | 4 | AND=4 OR=3 XOR=8 | 0 |  |  |
| serpent_s3 | gc6 | serpent_s3-gc6-cost-nocap-g15-a6-gd13-ad5.circ.txt | yes | yes | 15 | 6 | 13 | 5 | AND=3 NOR=2 OR=1 XNOR=5 XOR=4 | 0 |  |  |
| serpent_s4 | bgc | serpent_s4-bgc-cost-nocap-g15-a5-gd9-ad3.circ.txt | yes | yes | 15 | 5 | 9 | 3 | AND=3 NOT=1 OR=2 XOR=9 | 0 |  |  |
| serpent_s4 | gc6 | serpent_s4-gc6-cost-nocap-g13-a6-gd11-ad5.circ.txt | yes | yes | 13 | 6 | 11 | 5 | AND=2 NAND=1 NOR=3 XNOR=2 XOR=5 | 0 |  |  |
| serpent_s5 | bgc | serpent_s5-bgc-cost-nocap-g15-a5-gd9-ad3.circ.txt | yes | yes | 15 | 5 | 9 | 3 | AND=3 NOT=1 OR=2 XOR=9 | 0 |  |  |
| serpent_s5 | gc6 | serpent_s5-gc6-cost-nocap-g14-a5-gd12-ad5.circ.txt | yes | yes | 14 | 5 | 12 | 5 | AND=1 NAND=2 NOR=2 XNOR=3 XOR=6 | 0 |  |  |
| serpent_s6 | bgc | serpent_s6-bgc-cost-nocap-g14-a4-gd11-ad4.circ.txt | yes | yes | 14 | 4 | 11 | 4 | NOT=1 OR=4 XOR=9 | 0 |  |  |
| serpent_s6 | gc6 | serpent_s6-gc6-cost-nocap-g13-a4-gd12-ad4.circ.txt | yes | yes | 13 | 4 | 12 | 4 | AND=2 NAND=1 NOR=1 XNOR=4 XOR=5 | 0 |  |  |
| serpent_s7 | bgc | serpent_s7-bgc-cost-nocap-g16-a6-gd10-ad4.circ.txt | yes | yes | 16 | 6 | 10 | 4 | AND=1 NOT=1 OR=5 XOR=9 | 0 |  |  |
| serpent_s7 | gc6 | serpent_s7-gc6-cost-nocap-g14-a5-gd12-ad4.circ.txt | yes | yes | 14 | 5 | 12 | 4 | AND=3 NOR=1 OR=1 XNOR=6 XOR=3 | 0 |  |  |
| skinny64 | bgc | skinny64-bgc-cost-nocap-g11-a4-gd5-ad2.circ.txt | yes | yes | 11 | 4 | 5 | 2 | AND=1 NOT=2 OR=3 XOR=5 | 0 |  |  |
| skinny64 | gc6 | skinny64-gc6-cost-nocap-g8-a4-gd4-ad2.circ.txt | yes | yes | 8 | 4 | 4 | 2 | NOR=1 OR=3 XNOR=3 XOR=1 | 0 |  |  |

## results/nist-format/ (NIST-named copies of AES results)

| file | verified | basis | (A,AD,G,GD) | XX | XNOR | NOT | name disagreement | gate-identical twin in results/aes |
|---|---|---|---|--:|--:|--:|---|---|
| aes-sbox-a264-ad19-g717-gd50-xxn453-194-1.circ.txt | yes | ok | (264,19,717,50) | 452 | 194 | 1 | - | aes-nist-cost_gd-nocap-g717-a264-gd50-ad19.circ.txt |
| aes-sbox-a28-ad4-g131-gd26-xx103-46.circ.txt | yes | ok | (28,4,131,26) | 103 | 46 | 0 | - | aes-nist-cost_gd-gd36-ad4-a28-g131-a28-gd26-ad4.circ.txt |
| aes-sbox-a28-ad4-g131-gd26-xx103-50.circ.txt | yes | ok | (28,4,131,26) | 103 | 50 | 0 | - | aes-nist-cost_gd-gd32-ad4-a28-g131-a28-gd26-ad4.circ.txt |
| aes-sbox-a28-ad4-g132-gd22-xx104-50.circ.txt | yes | ok | (28,4,132,22) | 104 | 50 | 0 | - | aes-nist-cost_gd-gd23-ad4-a28-g132-a28-gd22-ad4.circ.txt |
| aes-sbox-a28-ad4-g153-gd15-xx125-64.circ.txt | yes | ok | (28,4,153,15) | 125 | 64 | 0 | - | aes-nist-cost_gd-gd15-ad4-a28-g153-a28-gd15-ad4.circ.txt |
| aes-sbox-a28-ad4-g176-gd14-xx148-81.circ.txt | yes | ok | (28,4,176,14) | 148 | 81 | 0 | - | aes-nist-cost_gd-gd14-ad4-a28-g176-a28-gd14-ad4.circ.txt |
| aes-sbox-a29-ad5-g135-gd28-xx106-50.circ.txt | yes | ok | (29,5,135,28) | 106 | 50 | 0 | - | aes-nist-cost_gd-gd32-ad5-a29-g135-a29-gd28-ad5.circ.txt |
| aes-sbox-a29-ad5-g136-gd30-xx107-56.circ.txt | yes | ok | (29,5,136,30) | 107 | 56 | 0 | - | aes-nist-cost_gd-gd35-ad5-a29-g136-a29-gd30-ad5.circ.txt |
| aes-sbox-a29-ad5-g174-gd16-xx145-61.circ.txt | yes | ok | (29,5,174,16) | 145 | 61 | 0 | - | aes-nist-cost_gd-gd16-ad5-a29-g174-a29-gd16-ad5.circ.txt |
| aes-sbox-a30-ad4-g140-gd32-xxn110-66-1.circ.txt | yes | ok | (30,4,140,32) | 109 | 66 | 1 | - | aes-nist-cost_gd-gd36-ad4-a30-g140-a30-gd32-ad4.circ.txt |
| aes-sbox-a30-ad4-g181-gd15-xxn151-70-1.circ.txt | yes | ok | (30,4,181,15) | 150 | 70 | 1 | - | aes-nist-cost_gd-gd15-ad4-a30-g181-a30-gd15-ad4.circ.txt |
| aes-sbox-a32-ad5-g108-gd20-xx76-35.circ.txt | yes | ok | (32,5,108,20) | 76 | 35 | 0 | - | aes-nist-cost_gd-gd20-ad5-a32-g108-a32-gd20-ad5.circ.txt |
| aes-sbox-a32-ad5-g110-gd22-xx78-25.circ.txt | yes | ok | (32,5,110,22) | 78 | 25 | 0 | - | aes-nist-cost_gd-gd23-ad5-a32-g110-a32-gd22-ad5.circ.txt |
| aes-sbox-a32-ad5-g129-gd15-xx97-40.circ.txt | yes | ok | (32,5,129,15) | 97 | 40 | 0 | - | aes-nist-cost_gd-gd15-ad5-a32-g129-a32-gd15-ad5.circ.txt |
| aes-sbox-a33-ad4-g108-gd19-xx75-22.circ.txt | yes | ok | (33,4,108,19) | 75 | 22 | 0 | - | aes-nist-cost_gd-gd20-ad4-a33-g108-a33-gd19-ad4.circ.txt |
| aes-sbox-a33-ad4-g110-gd18-xx77-26.circ.txt | yes | ok | (33,4,110,18) | 77 | 26 | 0 | - | aes-nist-cost_gd-gd20-ad4-a33-g110-a33-gd18-ad4.circ.txt |
| aes-sbox-a33-ad5-g108-gd23-xx75-30.circ.txt | yes | ok | (33,5,108,23) | 75 | 30 | 0 | - | aes-nist-cost_gd-gd27-ad6-g108-a33-gd23-ad5.circ.txt |
| aes-sbox-a33-ad5-g108-gd26-xx75-21.circ.txt | yes | ok | (33,5,108,26) | 75 | 21 | 0 | - | aes-nist-cost_gd-nocap-g108-a33-gd26-ad5.circ.txt |
| aes-sbox-a34-ad4-g110-gd20-xx76-22.circ.txt | yes | ok | (34,4,110,20) | 76 | 22 | 0 | - | aes-nist-cost_gd-gd22-ad4-a34-g110-a34-gd20-ad4.circ.txt |
| aes-sbox-a34-ad4-g122-gd15-xx88-39.circ.txt | yes | ok | (34,4,122,15) | 88 | 39 | 0 | - | aes-nist-cost_gd-gd15-ad4-a34-g122-a34-gd15-ad4.circ.txt |
| aes-sbox-a35-ad3-g139-gd27-xx104-31.circ.txt | yes | ok | (35,3,139,27) | 104 | 31 | 0 | - | aes-nist-cost_gd-gd31-ad3-a35-g139-a35-gd27-ad3.circ.txt |
| aes-sbox-a36-ad4-g134-gd14-xx98-36.circ.txt | yes | ok | (36,4,134,14) | 98 | 36 | 0 | - | aes-nist-cost_gd-gd14-ad4-a36-g134-a36-gd14-ad4.circ.txt |
| aes-sbox-a36-ad4-g135-gd14-xx99-49.circ.txt | yes | ok | (36,4,135,14) | 99 | 49 | 0 | - | aes-nist-cost_gd-gd14-ad4-a36-g135-a36-gd14-ad4.circ.txt |
| aes-sbox-a38-ad4-g138-gd13-xx100-48.circ.txt | yes | ok | (38,4,138,13) | 100 | 48 | 0 | - | aes-nist-cost_gd-gd13-g138-a38-gd13-ad4.circ.txt |
| aes-sbox-a38-ad4-g139-gd13-xx101-36.circ.txt | yes | ok | (38,4,139,13) | 101 | 36 | 0 | - | aes-nist-cost_gd-gd13-ad4-a38-g139-a38-gd13-ad4.circ.txt |
| aes-sbox-a39-ad4-g137-gd13-xx98-41.circ.txt | yes | ok | (39,4,137,13) | 98 | 41 | 0 | - | aes-nist-cost_gd-gd13-ad4-a39-g137-a39-gd13-ad4.circ.txt |
| aes-sbox-a41-ad4-g126-gd14-xx85-40.circ.txt | yes | ok | (41,4,126,14) | 85 | 40 | 0 | - | aes-nist-cost_gd-gd14-g126-a41-gd14-ad4.circ.txt |
| aes-sbox-a45-ad4-g146-gd12-xx101-37.circ.txt | yes | ok | (45,4,146,12) | 101 | 37 | 0 | - | aes-nist-cost_gd-gd12-ad4-a45-g146-a45-gd12-ad4.circ.txt |
| aes-sbox-a45-ad4-g146-gd12-xx101-46.circ.txt | yes | ok | (45,4,146,12) | 101 | 46 | 0 | - | aes-nist-cost_gd-gd12-g146-a45-gd12-ad4.circ.txt |
| aes-sbox-a46-ad3-g207-gd15-xx161-87.circ.txt | yes | ok | (46,3,207,15) | 161 | 87 | 0 | - | aes-nist-cost_gd-gd15-ad3-a46-g207-a46-gd15-ad3.circ.txt |
| aes-sbox-a47-ad3-g167-gd22-xx120-50.circ.txt | yes | ok | (47,3,167,22) | 120 | 50 | 0 | - | aes-nist-cost_gd-gd22-ad3-a47-g167-a47-gd22-ad3.circ.txt |
| aes-sbox-a47-ad3-g190-gd15-xx143-59.circ.txt | yes | ok | (47,3,190,15) | 143 | 59 | 0 | - | aes-nist-cost_gd-gd15-ad3-a47-g190-a47-gd15-ad3.circ.txt |
| aes-sbox-a49-ad4-g150-gd11-xx101-51.circ.txt | yes | ok | (49,4,150,11) | 101 | 51 | 0 | - | aes-nist-cost_gd-gd11-ad4-a49-g150-a49-gd11-ad4.circ.txt |
| aes-sbox-a51-ad4-g152-gd11-xxn101-37-1.circ.txt | yes | ok | (51,4,152,11) | 100 | 37 | 1 | - | aes-nist-cost_gd-gd11-ad4-a51-g152-a51-gd11-ad4.circ.txt |
| aes-sbox-a51-ad4-g152-gd11-xxn101-45-1.circ.txt | yes | ok | (51,4,152,11) | 100 | 45 | 1 | - | aes-nist-cost_gd-gd11-g152-a51-gd11-ad4.circ.txt |
| aes-sbox-a53-ad4-g152-gd11-xx99-38.circ.txt | yes | ok | (53,4,152,11) | 99 | 38 | 0 | - | aes-nist-cost_gd-gd11-ad4-a53-g152-a53-gd11-ad4.circ.txt |

results/aes files without a gate-identical nist-format copy: none

## results/MANIFEST.json vs recount

88 entries; 7 disagree (metrics, sha256, verified flag, or nist-format twin).
- nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd11-ad4-a51-g152-a51-gd11-ad4.circ.txt: {'metric_mismatch': {'#NOT': {'claimed': 1, 'recomputed': 0}, '#XNOR': {'claimed': 37, 'recomputed': 38}}, 'sha_match': True, 'verified_claim': True, 'verified_mine': True, 'nist_format_twin_ok': True}
- nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd11-g152-a51-gd11-ad4.circ.txt: {'metric_mismatch': {'#NOT': {'claimed': 1, 'recomputed': 0}, '#XNOR': {'claimed': 45, 'recomputed': 46}}, 'sha_match': True, 'verified_claim': True, 'verified_mine': True, 'nist_format_twin_ok': True}
- nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd15-ad4-a30-g181-a30-gd15-ad4.circ.txt: {'metric_mismatch': {'#NOT': {'claimed': 1, 'recomputed': 0}, '#XNOR': {'claimed': 70, 'recomputed': 71}}, 'sha_match': True, 'verified_claim': True, 'verified_mine': True, 'nist_format_twin_ok': True}
- nonlinear/boolflux/results/aes/aes-nist-cost_gd-gd36-ad4-a30-g140-a30-gd32-ad4.circ.txt: {'metric_mismatch': {'#NOT': {'claimed': 1, 'recomputed': 0}, '#XNOR': {'claimed': 66, 'recomputed': 67}}, 'sha_match': True, 'verified_claim': True, 'verified_mine': True, 'nist_format_twin_ok': True}
- nonlinear/boolflux/results/aes/aes-nist-cost_gd-nocap-g717-a264-gd50-ad19.circ.txt: {'metric_mismatch': {'#NOT': {'claimed': 1, 'recomputed': 0}, '#XNOR': {'claimed': 194, 'recomputed': 195}}, 'sha_match': True, 'verified_claim': True, 'verified_mine': True, 'nist_format_twin_ok': True}
- nonlinear/boolflux/results/chi3/chi3-bgc-cost-nocap-g7-a3-gd3-ad1.circ.txt: {'metric_mismatch': {}, 'sha_match': True, 'verified_claim': True, 'verified_mine': False}
- nonlinear/boolflux/results/chi3/chi3-gc6-cost-nocap-g7-a3-gd3-ad1.circ.txt: {'metric_mismatch': {}, 'sha_match': True, 'verified_claim': True, 'verified_mine': False}

Result files not listed in results/MANIFEST.json: fulladd-gc-cost-nocap-g5-a2-gd4-ad1.circ.txt, gf16-inv-xag-a_cost-nocap-g16-a5-gd12-ad4.circ.txt, gf16-mul-xag-a_cost-nocap-g31-a9-gd7-ad1.circ.txt, maj3-gc-cost-nocap-g4-a2-gd3-ad1.circ.txt

## results/ledger-rows.jsonl vs recount

114 rows, 99 with a file; 6 disagree with the recount (G or verified flag).
- nonlinear/boolflux/results/chi3/chi3-bgc-cost-nocap-g7-a3-gd3-ad1.circ.txt: {'file': 'nonlinear/boolflux/results/chi3/chi3-bgc-cost-nocap-g7-a3-gd3-ad1.circ.txt', 'verified_claim': True, 'G_claim': 7, 'G_mine': 7, 'ok_mine': False, 'match': False}
- nonlinear/boolflux/results/chi3/chi3-gc6-cost-nocap-g7-a3-gd3-ad1.circ.txt: {'file': 'nonlinear/boolflux/results/chi3/chi3-gc6-cost-nocap-g7-a3-gd3-ad1.circ.txt', 'verified_claim': True, 'G_claim': 7, 'G_mine': 7, 'ok_mine': False, 'match': False}
- nonlinear/boolflux/results/fulladd/fulladd-gc-cost-nocap-g5-a2-gd4-ad1.circ.txt: {'file': 'nonlinear/boolflux/results/fulladd/fulladd-gc-cost-nocap-g5-a2-gd4-ad1.circ.txt', 'verified_claim': True, 'G_claim': 5, 'match': False, 'note': 'file listed but not found'}
- nonlinear/boolflux/results/gf16-inv/gf16-inv-xag-a_cost-nocap-g16-a5-gd12-ad4.circ.txt: {'file': 'nonlinear/boolflux/results/gf16-inv/gf16-inv-xag-a_cost-nocap-g16-a5-gd12-ad4.circ.txt', 'verified_claim': True, 'G_claim': 16, 'match': False, 'note': 'file listed but not found'}
- nonlinear/boolflux/results/gf16-mul/gf16-mul-xag-a_cost-nocap-g31-a9-gd7-ad1.circ.txt: {'file': 'nonlinear/boolflux/results/gf16-mul/gf16-mul-xag-a_cost-nocap-g31-a9-gd7-ad1.circ.txt', 'verified_claim': True, 'G_claim': 31, 'match': False, 'note': 'file listed but not found'}
- nonlinear/boolflux/results/maj3/maj3-gc-cost-nocap-g4-a2-gd3-ad1.circ.txt: {'file': 'nonlinear/boolflux/results/maj3/maj3-gc-cost-nocap-g4-a2-gd3-ad1.circ.txt', 'verified_claim': True, 'G_claim': 4, 'match': False, 'note': 'file listed but not found'}

Result files with no ledger row: 4 (fulladd-gc-cost-nocap-g5-a2-gd4-ad1.circ.txt, gf16-inv-xag-a_cost-nocap-g16-a5-gd12-ad4.circ.txt, gf16-mul-xag-a_cost-nocap-g31-a9-gd7-ad1.circ.txt, maj3-gc-cost-nocap-g4-a2-gd3-ad1.circ.txt)

## Second opinion (independent/verify.py)

230 files checked; 0 disagree with this audit on ok/G/A/GD/AD/dead.
