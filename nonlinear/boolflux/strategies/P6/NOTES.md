# P6: targets T07 (A35/AD3/G139/GD27) and T08 (A35/AD3/G183/GD13), 2026-11-15 from 15:25 UTC

CPUs 17 and 2. Data: `~/xs-campaigns/2026-11-15-targets/P6/` (found/ = verified circuits + sidecars,
runs/ = every run with logs). Hard caps on every retained state: A <= 35, AD <= 3.
Code sha at start: xcr-boolflux 8922cac (+ this directory, uncommitted).

## 1. Depth anatomy of the GD13 AD3 circuits (`skelan.py`, facts, measured)

Skeleton arrivals (each linear form as its own Huffman tree over inputs + AND outputs; a lower bound
on GD for fixed AND functions, F NOTES 1) of NIST 183@13 and our 177@13:
- level-1 ANDs at 2-4, level-2 ANDs at 6-8, level-3 ANDs at 10 (one at 11);
- every output is an XOR of level-3 products only (no other terms); row weights of the 8 x 12
  bottom matrix: 6, 4, 4, 6, 4, 4, 2, 4.  Output Kraft sums at cap 12 (sum 2^(level - 12)):
  1.75, 1.0, 1.25, 1.5, 1.0, 1.25, 0.75, 1.0.  Two rows have weight 6 and the 11-level product
  sits in two rows: that is why both circuits are at 13 [C, Huffman/Kraft for fixed products].

## 2. Level-3 class re-basing (`botbasis.py`) [C, stated case]

The 12 level-3 products are Q_w R_c in 3 classes of 4 (T3 NOTES 1).  Replacing a class's 4 R's by
any basis of their span (new R' = XOR of old R's; product = XOR of the old products, so the outputs
stay in the span) changes the class's bottom block M_w to M_w T^-1 and the R' operand forms.
`botbasis.py` enumerates all 840 unordered bases per class, prices each new product by its Huffman
arrival (min over the trivial operand variants (Q,R), (Q,Q+R+1), (Q+R+1,R)), keeps the Pareto set of
per-output Kraft vectors and finds the best triple exactly.
Case covered: lower levels (level 1-2 ANDs and their forms) fixed, products restricted to re-bases of
the existing classes, outputs = XOR trees of products.

| parent | cap 12 max Kraft (now -> best re-basing) | cap 13 | cap 14 |
|---|---|---|---|
| NIST 183@13 | 1.75 -> **1.00** (51 feasible Pareto triples) | | |
| ours 177@13 | 1.75 -> **1.00** (51) | | |
| ours 162@14 / NIST 172@14 / NIST 157@15 | 2.5 -> 1.50 | **0.75** | |
| ours 155@15 | -> 2.00 | **1.00** | 0.50 |
| ours 147@16 | -> 3.00 | 1.50 | **0.75** |
| ours 144@17 | -> 2.25 | 1.125 | **0.56** |
| ours 143@18 / 141@19 | -> 2.75 / 3.0 | 1.375 / 1.5 | |

So the skeleton bound of 183@13 and 177@13 drops to 12 by re-basing alone, and 162@14 / 157@15 /
155@15 reach 13 (with slack 0.25 for 162/157/172).

## 3. Construction at the cap (`rebase.py`, `paarb.py`, `hybrid.py`)

- `rebase.py` (default): parent gates kept, only level-3 rebuilt: verified but GD 13 - the parent's
  own level-2 ANDs are one level later than their skeleton arrival (177: AND6-9, 21, 22, 27 at 7
  instead of 6), so the rebuilt R' cannot meet 9.  The kernel did not repair 224@13 -> 12 in 130 s
  (k1: 211@13, still infeasible).
- `rebase.py --fresh`: whole skeleton synthesised depth-tight (each operand at its Huffman level,
  cover by existing signals, Huffman trees): **35/3/246/12, aes_check OK** - the first A<=35 circuit
  at GD 12 on the pin (aes_check: "published best G at A<=35, GD<=12: none"; first AD3 GD12 at all).
- `paarb.py`: same with a depth-constrained Paar per layer: 247-253 (no gain over --fresh).
- `hybrid.py`: parent ANDs reused when the bound with their actual level stays <= cap (and their
  structural AND cone is reused too), others rebuilt at the latest feasible deadline, parent linear
  signals usable as pieces; `--paar` builds all re-based level-3 operands in one shared layer:
  177 -> 220-229@12, 183 -> 238-247@12, 162 -> 200-212@13 (cap 13), 157 -> 237@13.

## 4. Kernel polish at the cap (hard caps A35 AD3 GD12, objective cost,gd)

- k2 (kern.py, hub.ops._kernel, repo kernel bfx-94a75e2c18): 246@12 -> **200@12** in 105 s, then no
  gain in the remaining ~300 s.  found/aes-sbox-a35-ad3-g200-gd12-257dddf4b764.circ.txt (OK).
- fd1: fdrive mix from 200@12 (long kernel bfx-593fa798f5), 15:41-15:48: no gain at GD12 (osc stage:
  relaxed 178@13, repaired only to 195@13; trb bottom rebuild 200 -> 200).  Stopped.

## 5. Depth pull 14 -> 13: strict T08 improvement 35/3/175/13 (15:47 UTC)

pull13a (`pullrun.py --cap 13 --paar`, CPU 2): parent our 162@14 -> re-basing (max Kraft 0.75 at cap 13)
+ hybrid build 200@13 -> kernel (caps A35 AD3 GD13, cost,gd) **175@13 after 90 s**.
found/aes-sbox-a35-ad3-g175-gd13-9266803dcdb9.circ.txt, aes_check OK, new Pareto point on the pin;
T08 strict (183 -> 175 at GD 13; archive best was 177@13).  [H] one run.
Its anatomy: the kernel moved the slack: bottom rows have weight <= 4, but level-1 ANDs reach 4 and
level-2 ANDs 7-8, so level-3 products are at 10-11; re-basing at cap 12 only reaches max Kraft 1.5.

## T07

- t07loop (15:25-15:42, CPU 2): T3's gf4loop at caps GD27 (moves GD29), target 138@27; 5 steps, all
  141@26 / 140@25 (pool members), nothing new.  Stopped to give CPU 2 to the T08 pulls (T3 reported
  ~0 yield for this loop at GD 24-27 over a night).

## 6. GD12 gate count: pull12a and the re-basing oscillation (16:00 UTC)

- pull12a (`pullrun.py --cap 12 --paar`, CPU 17, 15:48-16:00): parent 177@13, hybrid builds 206/207/210,
  kernel stages of 240 s: 206 -> **189@12** (17 s) -> 188 -> **187@12** (stage 1).  All saved in found/
  (aes_check OK).  187@12 is a T08 permitted tradeoff (GD 13 -> 12 for +4 gates <= 8).  Stopped for:
- observation [H, 1 run]: kernel 30 s at cap 13 from 187@12 gives 177@13 and the re-basing bound of
  that circuit at cap 12 is still max Kraft 1.0 - the relaxed state stays pullable.  Hence
  `oscloop.py`: pool of GD12 circuits; step = relax (kernel cap 13, 40 s) -> re-base + hybrid at 12
  (30 random feasible triples, 2 lowest-G builds) -> kernel cap 12 (200 s); results pooled.
  osc12a runs from 16:01 (CPU 17, 2 h).
- pull13a (CPU 2): 162@14 -> 175@13 (both stages), 2nd build 207 -> 186 -> 182@13; parent 172@14 next.
- pull12b (16:03-16:23, `--evolve 1`, pool = 187@12, parents 183@13 / 177@13): re-basing moves from
  187@12 (builds 196-200, identity triple 196) -> 188, 187@12: a plateau at 187-188 [H].
- osc12a (16:01-16:05, one step): relax 188@12 -> 179@13 keeps max Kraft 1.0, but the relaxed circuit's
  lower ANDs are late in the realised circuit, hybrid builds cost 227-234 and polish only to 202.  Dropped.

## 7. GF(4)-coordinate neighbourhood priced by the depth bound (`l3scan.py`, 16:24-16:38)

T3's one-point coordinate moves (gf4build keep2) of 177@13, each priced by the best class re-basing at
cap 12: 765 distinct variants, 741 with max Kraft <= 1.0 and **8 with max Kraft 0.75** (all change point
index 2: p in {163, 173, 180, 186, 229, 235, 242, 252}; built G 181-189 at GD 15-18) [C, botbasis case].
So a coordinate change gives GD12 skeletons with slack.  pull12c (CPU 17, from 16:39): depth pulls at
cap 12 from these 8 variants.

## T07 basin test (CPU 2, 16:21-): G-first kernel (caps A35 AD3 GD27, cost,gd, 2 x 240 s) from the
low-GD families: 175@13 -> 157@24 -> 153@24; 162@14 -> 148@22 (stage 0).  These basins are far from 139.

## 8. T08 primary met: 35/3/181/12 (16:47 UTC) - strict (183@13 -> 181@12)

pull12c, parent = the coordinate variant [14, 25, 180, 72] of 177@13 (l3scan, max Kraft 0.75 at cap 12,
built 181@15) -> hybrid build 204@12 -> kernel (caps A35 AD3 GD12, cost,gd, 240 s, seed 397181) **181@12**.
found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt, aes_check OK, new Pareto point on the pin,
"published best G at A<=35, GD<=12: none".  Dominates every earlier GD12 circuit of ours (187-246).
[H] one run; the slack variants are the decisive ingredient (the Kraft-1.0 parents plateaued at 187).
T07 basin test stopped 16:44 (2 of 5 starts done: 153@24, 148@22; negative).
- pull12c second build (G206) -> 184@12; parent variant p=186 gives the identical build (same id) -> 181@12 again
  with another kernel seed (robust [H], n = 2).
- 16:55: kernel 120 s at cap 13 from 181@12 -> **172@13** (found/aes-sbox-a35-ad3-g172-gd13-ad319b23b367).
- l3scan of 162@14 at cap 13: 765 variants, all max Kraft <= 1, 597 at 0.75 (as the parent); none 0.5.
- pull13b (CPU 2, from 16:57): parents 172@13 + 4 coordinate variants of 162@14: 172@13 builds 190/191 ->
  172, **171@13** (found/aes-sbox-a35-ad3-g171-gd13-462cb948a761); variant 164@15 builds 199 -> 183@13.
- Two-point scan (l3scan on the variant [14,25,180,72], cap 12): 765 variants, 29 with max Kraft 0.75,
  none below [C, botbasis case].  pull12d (CPU 17, from 17:13): pulls from the 28 new slack variants.
- pull12d (17:13-17:48, 4 two-point slack variants done): 182@12 (x2), 185, 188 [H]: slack variants give
  181-188 after 2 stages; nothing below 181.
- polish181 (CPU 2, 17:43-17:53): kernel 300 s on 181@12, default settings and hot (T0 1.2, max_excess 14,
  stall 120k): 181 both [H].  The 171@13 / 172@13 / 181@12 skeletons all keep max Kraft 0.75 at cap 12.
- pull12e (CPU 17, from 17:49): parents 171@13, 172@13 (GD13 family of 181) at cap 12: builds 218-223
  (relaxed lower levels must be rebuilt), first result 190@12.
- 17:55 coordinator tip (P3): GF(2^8) conjugation of starts (P3 mkconj.py, used read-only).  t07conj
  (CPU 2): conjugates lam:k in {188:0, 9:4, 93:0, 37:2, 201:5} of 140@25 and NIST 139@27, kernel at caps
  A35 AD3 GD27 (cost,gd, 2 x 150 s).  First conjugate: 140@25 -> lam 188 = 148@29 before polish.
- t07conj: 140@25 conjugate lam 188 k 0 (148@29) -> kernel cap 27, 2 x 150 s: 141@27 (not below 139).
- T08 conjugates [C, skeleton Huffman case]: `cjscan.py` - for all 2040 naive conjugates of 181@12 the sum
  of the skeleton arrivals of the 23 level-1/2 ANDs grows by >= 12 levels (identity 107; next best 119:
  lam 4, 82, 87, 141), because the top forms f o G get more terms.  The conjugate of 181@12 with lam 188
  (mkconj) is 202@24 and its best re-basing bound at cap 12 is max Kraft 1.5.  Conjugation is not a
  route to GD12 here (it is a gate-count tool).  t08conj stopped after this check.
- 18:03 l3scan of NIST 183@13 at cap 12 (CPU 17): looking for slack variants in the 183 lower-level family.

## 9. Compliance 18:20 (kernel repairs and hard A/AD) - audit
- All P6 drivers (kern.py, pullrun.py, oscloop.py) now set `repair_keep 1` in every kernel call.
- Audit of every found/ circuit (certify.py; start metrics vs the stage's GD cap checked from each job's
  kernel.cfg): every kernel stage in the P6 lineages started inside all caps (builds are kept only with
  GD <= cap; stage 1 starts from the stage-0 best), so no state could leave A35/AD3 [C, by bfx.c
  1064-1077]: path_certified true for 171/172/175@13, 181/187/188/189/200/246@12.  Archive parents
  (177@13, 162@14, NIST 183@13) are used as structures; their own history is not audited by P6.
- Runs that DID start above the GD cap without repair_keep (nothing saved from them): k1 (224@13 at cap
  12), fd1 osc stages, the conjugate kernels t07conj/t08conj before 18:20 (dirs renamed *-NO-repair_keep).
  t07conj re-run from 18:22 under repair_keep 1.

## 10. More GD12 pulls (18:00-18:40)
- l3scan of NIST 183@13 at cap 12: 765 variants, 8 with max Kraft 0.75 (built 187-195).  pull12f
  (18:21-18:38, 2 of these parents): builds 207-220 -> 184@12, 186, 190: the 183 lower-level family is
  worse than 177's [H].  Stopped.
- pull12g (CPU 17, from 18:39, repair_keep 1): the 177 slack family (variant [14,25,180,72] + 23 two-point
  variants), 5 builds per parent, one 240 s stage each.
- t07conj2 (repair_keep 1): 140@25 conjugates lam:k 188:0 -> 141@27, 9:4 -> 144@24, 93:0 -> 147@25.
- t07conj2 (18:17-19:08, repair_keep 1, kernel caps A35 AD3 GD27, cost,gd, 2 x 150 s per conjugate):
  140@25 conjugates (lam:k) 188:0 141@27, 9:4 144@24, 93:0 147@25, 37:2 151@26, 201:5 147@26;
  NIST 139@27 conjugates 188:0 143@25, 9:4 144@26, 93:0 146@26, 37:2 148@26, 201:5 148@24.
  No conjugate reaches 139 or below [H, 10 conjugates x 1 seed x 300 s].  (The P3 gain came on A32/AD4
  where conjugates opened cheaper XOR layers; here the AD3 frontier circuits stay 2-9 gates above.)
- pull12g first parent (variant 180; with the SLACK3 hybrid the deterministic builds changed: 202 instead
  of 204): 5 builds, 1 stage each: 182, 185, 185, 187, 186; second parent: 187, 182, 185 [H].
- 19:09 seeds181 (CPU 2): 6 kernel seeds (240 s) from the exact 204@12 build that gave 181 twice, then
  relax13.sh (cap 13, 150 s x 2, from every distinct GD12 job best with G <= 186).
- seeds181 (19:09-19:33, repair_keep 1): 6 more kernel seeds (240 s) from the exact build 204@12 that gave
  181: 181, 182, 182, 183, 185, 182.  Together 3 of 8 runs reach 181, none lower [H]: 181 is this build's
  floor under the kernel; the 181 is reproduced under repair_keep 1 (seed 11, runs/seeds181/sd11).
- l3scan of 181@12 itself (cap 12): 765 variants, 45 with max Kraft 0.75, none lower; their keep2 builds
  inherit 181's GD12-tight lower levels, so hybrid builds start at 184 (vs 202-206 from 177's).
  pull12h (CPU 17, 19:42-): first build 184 -> 182@12.
- relax13 (CPU 2, 19:33-): cap-13 relaxations of the 18 distinct GD12 job bests (G <= 186): 181 -> 171,
  181 -> 174 so far.

## Reproduction of the T08 results (exact commands, repo 8922cac + this directory)
All from `cd ~/xcr-boolflux/nonlinear/boolflux/strategies/P6`; R = ~/xs-campaigns/2026-11-15-targets/P6/runs.
1. Coordinate variant of 177@13 (deterministic, T3 gf4build keep2): `python3 l3scan.py
   ~/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a35-ad3-g177-gd13-xx142-61.circ.txt --cap 12
   --out R/l3scan/scan177.jsonl --emit R/l3scan/emit177 --emit-max 30` -> emit177/a35-ad3-g181-gd15-k075-804faabc4648.bfx
   (points [14, 25, 180, 72]).
2. Hybrid build + kernel: the exact stage start of 181@12 is R/pull12c/jobs/9552bd8ad634-r0-s0/start.bfx
   (204@12; sha256 in the sidecar).  Built by `hybrid.py` (paar path) before the SLACK3 change of 18:35
   (set hybrid.SLACK3 = False to rebuild it; checked 20:24: hybrid(variant, feasible triple #30 =
   ((2,3,7,10), (1,4,6,12), (5,8,9,10)), cap 12, rng None, paar) reproduces the start byte-for-byte).  Kernel: `python3 kern.py R/pull12c/jobs/9552bd8ad634-r0-s0/start.bfx
   --caps 35,3,12 --seed 11 --seconds 240 --out R/seeds181/sd11/jobs` (repair_keep 1) -> 181@12 (3 of 8
   seeds reach 181; kernel bfx-94a75e2c18 = kernel/bfx.c sha1 94a75e2c18).
3. GD13: `python3 kern.py found/aes-sbox-a35-ad3-g181-gd12-d32fa4ac436b.circ.txt --caps 35,3,13 --seed 77
   --seconds 120 --out R/relax181` -> 172@13; relax13.sh r3 (start R/pull12d/jobs/3fe3b0e10373-r0-s0/best.bfx,
   182@12, seed 1303, 2 x 150 s) -> 170@13.

## 11. Last runs (19:33-21:05)
- relax13 (CPU 2): 18 distinct GD12 job bests (G 181-186) relaxed at cap 13 (2 x 150 s each, repair_keep 1):
  G at GD13 = 171 174 170 174 173 171 173 172 172 170 176 175 170 172 174 174 172 173 -> **170@13**
  three times (found/aes-sbox-a35-ad3-g170-gd13-b418123e66e8, from a 182@12 of pull12d) [H].
- pull12h/pull12i (CPU 17): slack coordinate variants of 181@12 (builds 184-188 when kept <= 195; some
  variants build at 219 and were skipped from 20:05): results 181@12 (twice, other structures), 182-186.
  So 181 at GD12 was met repeatedly from different builds and never beaten [H, ~45 kernel stages at GD12].
- pull13c (CPU 2, from 21:05): rebasing moves at cap 13 from the 170/171@13 circuits (1 h).
- 21:23 pull13c: rebasing move from 171@13 (build 172@13) -> **169@13** (found/aes-sbox-a35-ad3-g169-gd13-e0c19be5de66);
  round 1 from 169: build 171 -> 169 again.
- 21:40 CPUs 7, 8 given by the coordinator (P4 done): T07 conjugate pipeline `runs/t07c3.sh` on 140@25 (CPU 7)
  and 141@19 (CPU 8): P3 conj3 screen of all 2040 conjugates, the 12 best-scoring non-identity ones ->
  mkconj -> kernel cap GD31 (200 s) -> cap GD27 (2 x 200 s), repair_keep 1, harvest (target T07).

## 12. T07 strict: 35/3/139/25 (21:59 UTC)
c3-140 (CPU 7): conj3 screen of 140@25 (identity score 35; lam 2 k0 36; lam 97/99/189 k0 38; ...), then per
conjugate kernel cap 31 (200 s) and cap 27 (2 x 200 s), repair_keep 1:
- lam 2 k 0: 145@25 -> 142@26 -> 141@24;  lam 97 k 0: 151@30 -> **139@25** (cap-31 stage, 200 s) -> 139@25.
found/aes-sbox-a35-ad3-g139-gd25-107a7c3b5078.circ.txt, aes_check OK, new Pareto point: strict for T07
(G = 139, GD 27 -> 25); the primary G < 139 is not reached.  [H] one conjugate of 12 so far.
c3-141 (CPU 8): 141@19 conjugates: lam 2 k0 147@21 -> 143@26 -> 142@26; lam 94 k2 157@27 -> 144@25 -> 143@24.
From ~22:05: CPU 2 = t07c3.sh on the new 139@25 (its own conjugates), CPU 17 = 8 kernel seeds on 139@25
at cap 27 (G-first).
- 22:05 pull13c round 1 (rebasing move from the pool): **168@13** (found/aes-sbox-a35-ad3-g168-gd13-94a02642b2d6;
  build 186@13 from a 170@13 pool member).  T08 GD13 lineage: 177 -> 175 -> 172 -> 171 -> 170 -> 169 -> 168.
- 22:09 c3-140 lam 99 k 0: 149@27 -> 140@27 (cap 31) -> **140@22** (cap 27 stages): new A35 AD3 Pareto point
  (best known at GD <= 22 was 142); found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.  For T07 it is neither
  strict (G 140) nor a permitted tradeoff.  lam 188 k 0 of 141@19: 157@32 -> 140@25.
- pull12i summary (31 GD12 kernel stages from the 181 coordinate neighbourhood): 181 x2, 182 x8, 183 x15,
  184 x3, 185, 186 x2.
- 22:39 c3-140 lam 250 k 4 (score 39): 152@26 -> 140@27 (cap 31) -> **139@23** (cap 27 stages): T07 strict,
  dominates 139@25; found/aes-sbox-a35-ad3-g139-gd23-703f7ce121a7.circ.txt, aes_check OK, path certified.
  c3-140 so far (8 conjugates): 141@24, 139@25, 140@22, 142@25, 142@26, 139@23, ...; c3-141 (8): 142-143 @23-26,
  140@25, 141@23; c3-139b (conjugates of 139@25): 141@27, 143@25, 141@25.
- polish139b (CPU 17, from 22:24): 139@25 at caps 24/23: 140@24, 140@23, 141@23, 140@24 (no 139 below 25 this way).

## 13. T07 primary met: 35/3/138/24 (22:53 UTC)
polish139c (CPU 17): kernel (repair_keep 1, caps A35 AD3 GD27, cost,gd, 240 s) from 139@23, seed 20378 ->
**138@24**; found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt, aes_check OK, new Pareto point, path
certified.  First A<=35 AD3 circuit below 139 gates on the pin.  Full lineage: best-1400 140@25 -> P3 conj3
screen + mkconj, lam 250 k 4 (152@26) -> kernel GD31 200 s (140@27) -> kernel GD27 2 x 200 s (139@23) ->
kernel GD27 240 s seed 20378 (138@24).  Other polish139c seeds: 139@23 (seed 23170).  [H] one success.
- polish139c other seeds from 139@23: cap 25 seed 17446 -> 138@24 again; cap 27 -> 139@23 (x2); cap 22 -> 141@21.
- 23:08 c3-139b (conjugates of our 139@25) lam 189 k 0: 152@34 -> kernel cap 31 (repair_keep 1; start GD above
  the cap, inside A/AD) -> **137@28**: the lowest G of any A<=35 AD3 circuit (found/aes-sbox-a35-ad3-g137-gd28-
  23cf4c3c29d2).  T07: GD 28 > 27, and -2 gates is below the 3-gate "substantial" threshold, so neither strict
  nor a permitted tradeoff; a frontier point.  Quick polishes from it (200 s): cap 28 137@28, cap 27 139@27, 140@25.
- 23:14: all P6 jobs stopped.

## Final frontier (A35 AD3; ours new unless marked archive/NIST), all aes_check OK, path_certified
137@28, 138@24, 139@23, 140@22, 141@19 (archive), 143@18 (archive), 144@17 (archive), 147@16 (archive),
155@15 (archive), 162@14 (archive), 168@13, 181@12.
