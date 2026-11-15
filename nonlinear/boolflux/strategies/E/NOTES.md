# Track E: joint optimisation of AND structure and XOR logic (AES S-box, NIST model)

All code in this directory; campaign outputs in `~/xs-campaigns/2026-11-13-aes/E/`.
Kernels: `bfx_e` = copy of `kernel/bfx.c` at 7637b20 + ejection chains (used before the 05:09 outage);
`bfx_new` = copy of `kernel/bfx.c` at 0659eb9 (lexicographic `lex`, structural no-op filter), used for
every run after 14:30 UTC.  `skel_e` = `kernel/skel.c` + `cap.k` (AND cap) + `max_acc` (stop after N
accepted moves).

## Mechanisms

| id | what | file | verdict |
|---|---|---|---|
| M1 | ejection chain: uphill kick at a gate (50 % AND gates: AND rewired/replaced, cone with a new AND), then <= 6 greedy repair steps restricted to the signals the kick created, their consumers and operands; compound accepted only if better (or equal) | `bfx_e.c` (`chain*` keys) | negative (below) |
| M2 | skeleton kick: one AND-product move (swap/merge/split/perturb), seeded rebuild from the parent, short gate polish, accept on the polished result | `kick.py`, `skel_e.c`, `skeleton_e.py` | negative (below) |
| M3 | stage transplant with exact truth-table matching (front of X, back of Y, Y signals equal to an X front signal reused) | `splice.py` | superseded by M3b |
| M3b | stage transplant with linear interface: the cut of Y at AND level LY (signals of level <= LY read above it) is expressed in the affine span of X's front (inputs + X's ANDs of level <= LX) by Gaussian elimination, rebuilt greedily from X's existing linear signals; X front + interface + Y back, dead gates removed, checked on 256 inputs | `splice2.py`, `export_splices.py`, `run_splice.sh` | **positive: 20 new Pareto points in 4 x 50 s** |

## Why a transplant works here (analysis, `analyze_stages.py`, `layer_costs.py`, `and_roles.py`)
- Every published circuit spans the norm N = x^17 (GF(2^4) subfield element) after 9-11 level-1 ANDs;
  the BP-family circuits (A32-36) have N^-1 in their linear span after 15-18 ANDs.  These spaces of
  Boolean functions are intrinsic (independent of the tower basis), so the fronts and backs of
  different circuits meet at the same functions up to a GF(2)-linear interface.
- Different circuits optimise different stages for different (A, GD) trade-offs: e.g. the 17-final-
  product back of the A32 AD4 family (g117@GD19) behind the deeper but cheaper front of the A32 AD5
  family (g107@GD22) gives 31 ANDs (the front donor's level-4 ANDs are reused by the back).
- A28 vs A32 XOR (96 vs 71): the excess sits in the operand layer of the final 13 products (24-36 XOR
  vs 6-9), whose forms mix x and u = N + N^-1 and are not shared with the top layer; the output layers
  are similar (25-27).  Intrinsic to the 13-product construction, not under-optimisation.

## Measurements
- M1, 60 s, seeds 1-5, kernel bfx_e (old no-op filter): a36 (caps 36/4/13): chain p=0.15 median 135 vs
  control 133; chain without neutral acceptance 133 (n=5), p=0.05 134.  p104 uncapped: 104 in all arms.
  A28 124 with cap A 30/31 and p104 with cap A31 (300 s, 1-2 seeds): no improvement in either arm.
- M2: single skeleton moves cost +12..+42 gates (A28 124) / +0..+19 (p104) after the seeded rebuild;
  20-s polishes never recovered to the parent (a36, 60 s: median 135).  Short local search, with or
  without these kicks, does not move the published circuits (consistent with track D: no improving
  windows of <= 9 gates).
- M3b (sp1, 150 input circuits = pinned NIST forward circuits + team results/aes + F/found,
  104,230 splice attempts, 24,443 distinct results, 375 with need 0 vs the published set;
  ~50 s per shard on 4 CPUs, < 20 MB): 80 distinct pub-new tuples, 20 non-dominated by published,
  team or other splices, all verified by aes_check (both verifiers).  See STATUS.md for the list.

- polish1 (bfx_new, 240 s, seeds 1-2, same caps): from the A31 splice the kernel reaches 115 (A31, GD28)
  and 117 at GD20; from the A32 parents it never reaches A <= 31 (0/8 feasible).  At A32/GD19 the
  splice start gives 111 vs 112 (best parent).  At A32/GD24 both give 106.
- memetic.py (long run): splice + polish generations vs polish-only control on the 4-D frontier;
  iterated splicing (splices of splices) gives further points within minutes (31/5/116/22, 33/4/114/16).

## Final A/B, 2026-11-14 (runs stopped 17:28 UTC; NIST pin 3d80774; `ab_final.py`, data `E/ab_final.json`)
Kernel bfx_new (0659eb9) for every polish; polish 120 s under the circuit's own caps; same input pool
for the two long1 arms (140 circuits at 15:07).  Frontier point = admitted, not dominated by the pinned
published set (equality counts) and not strictly dominated inside the arm's own pool; every one was
re-checked with aes_check (both verifiers) on the new pin: all OK and new.  Files `E/found/final/`.

| arm | CPU-h | admissions (by mechanism) | /CPU-h | frontier points (by mechanism) | /CPU-h |
|---|---|---|---|---|---|
| long1 splice (join + polish) | 2.34 h x 2 = 4.7 | 41 (join 26, polish 15) | 8.75 | 17 (join 6, polish 11, of which 8 polishes of join products) | 3.63 |
| long1 control (polish only) | 2.35 h x 2 = 4.7 | 4 (polish 4) | 0.85 | 3 (polish 3) | 0.64 |
| low1 (join + polish + depth pull, A <= 31 targets, bigger pool) | 1.97 h x 3 = 5.9 | 19 (pull 10, polish 6, join 3) | 3.22 | 11 (pull 4, polish 4, join 3) | 1.86 |

- Splice arm vs control: 15 of the splice arm's 17 points are not dominated by any control point; 0 of
  the control's 3 are not dominated by the splice arm.  Join admissions arrive in the first 5 minutes
  (all 26 come from the first pass over the pool); polishes of join products keep adding points later.
- low1 (pool already contained long1's admissions, so fewer admissions are possible): A28 points
  28/5/125/25 (pull 124@GD27 -> GD26, 58 s), 28/4/131/25 (87 s), 28/4/135/18, 28/4/138/17, 28/5/137/17;
  A29 points 29/5/135/17 and 29/5/138/16 (pull of 128@GD20 under cap A28/GD17: the repair step
  traded one AND for depth); 31/5/118/19 (join), 31/5/124/17 (pull); **33/4/115/15** (join): best G at
  GD <= 15 (published 116).
- Time to result: joins are found in seconds (one pass over a member's pairs: 3-10 s); polish/pull
  improvements arrive 0-116 s into a 120-s polish (median ~60 s).
- Interpretation: the join supplies new starting points that the gate kernel cannot reach (other AND
  counts, interface positions); the kernel then lowers G and GD from them.  Control polishing of the
  already well-optimised pool is nearly exhausted (4 admissions in 4.7 CPU-h).

## Hub vs memetic splice arm, 2026-11-14 17:38-18:40 UTC (equal CPUs: 4 each, 1 h; `hub/compare.py`, `2026-11-14-hub/ab_compare.txt`)
Same seed pool (`2026-11-14-hub/seed.list`, 242 distinct verified circuits incl. all of long1/low1's
admissions).  Hub = `nonlinear/boolflux/hub/scheduler.py` (polish 90 s / pull 90 s / join 60 s / trb 30 s,
bandit eps 0.25, polish/pull objective `a,ad,cost,gd`; the repo kernel changed at 17:44-17:45 from
417e449 to f8a26e3 (review 4), so later polish/pull jobs used the fixed AND-first Metropolis step; each
job records its kernel binary `bfx-<sha1(bfx.c)>`).  Memetic = strategies/E/memetic.py --arm splice
(bfx_new = 0659eb9 copy, objective cost,gd, polish 120 s).
| arm | CPU-h | admissions | new frontier points (not dominated by pin 3d80774 or the seed pool) | per CPU-h | not dominated by the other arm |
|---|---|---|---|---|---|
| hub | 4.03 | 978 (join 918, trb 47, pull 9, polish 4) | 8 | 1.98 | 7 |
| memetic splice arm | 4.13 | 4 | 2 (39/3/174/13, 48/4/151/11) | 0.48 | 2 |
All 10 pass aes_check (OK + new).  Hub points with lineage (operators back to seeds):
33/4/107/20 = pull(join) (best G at GD<=20: published 108); 32/4/115/22 = join(pull(join), pull(join(join(join))));
32/4/119/18 = polish(join(pull, join(join))); 32/4/122/17 = pull; 32/5/116/17 = pull; 33/4/112/16 =
polish(polish); 35/3/142/24 = trb; 39/3/179/13 = join.  Operator yield in the hub (gain per CPU-h):
join 104, pull 12.5, trb 10.6, polish 8.8 - but the frontier points come from chains of operators.

## Generators, linres: A/B 2 and 3 (1 CPU-h per arm, all from the 18:47 snapshot `2026-11-14-hub/snap1847`; `hub/compare2.py`, data `ab23_compare.json`)
| arm | operators | new frontier points (aes_check OK + new) | lineage |
|---|---|---|---|
| base | polish, pull, join, trb (eps 0.25) | 1: 35/3/141/24 | pull |
| osc | base + gen_skel, gen_inv3, gen_bottom, osc (eps 0.25; bandit spent 3192 s of 3600 on osc, the generators were never sampled) | 2: 29/5/134/17, 30/4/139/16 | osc, osc |
| gen | base + gen_joinplus, gen_skel, gen_inv3, gen_bottom, osc (eps 0.5, nursery 0.4, generator slack 40) | 2: **30/4/130/20**, 32/5/115/17 | pull(pull(trb(pull(gen_skel)))), pull |
| lin | base + linres | 2: 28/5/131/19, 35/3/141/24 | trb, trb |
Per operator in the gen arm: gen_skel 5 jobs / 7 nursery admissions / 267 CPU-s, one of whose structures was
turned into the A30 point by later pull/trb/pull jobs (19 min after start); gen_joinplus 5 jobs, 3 nursery
admissions, 0 frontier; gen_inv3 6 jobs, 0 admissions (its 122@GD14-type outputs are already in the archive);
gen_bottom 21 jobs, 31 CPU-s, 0 (no suitable AD4 donors pass).  linres: 10 jobs, 8 cell admissions, 0 frontier
(both lin-arm points are trb) -> no measured advantage, not added (consistent with F's XORFlux layer result).
Adopted into the long run: osc (hot-added 19:50:45), gen_skel + nursery 0.3 (restart as hub-long3 at 20:49).
AD<=3 share: A/B 4 (20:52-21:52, snapshot `snap2051`, base = long3 configuration vs + ad3_share 0.3) with a
pre-registered rule (`hub/after_ab.py`: adopt if test >= base and >= 1 new frontier point), applied
automatically to `long/control.json`, which also gives CPUs 10-11 back to the long run.

## long3 final (hub `2026-11-14-hub/long`, 20:47:57 - 00:19:31 UTC; `hub/compare2.py`, `long3_final.{txt,json}`)
Configuration: polish, pull, join, trb, osc, gen_skel; nursery 0.3; ad3_share 0.3 from 21:52 (pre-registered
A/B 4: base 1 vs AD3-share 2 new points); CPUs 4-9, +10-11 from 21:52, +0-3 and 17-19 from 23:40 (coordinator,
user-approved); ingest of F/D/C/G found every 30 min.  Kernel bfx-593fa798f5 (repo kernel at the hub's
compile time).  Baseline = the archive at long3's start (`snap_long3start`: 1481 records, 298 cells, front 73)
plus the pinned NIST set 3d80774.  CPU-h = sum of the jobs' CPU seconds (30.1 CPU-h).

16 new frontier points, **all aes_check OK + new**, 0.53 per CPU-h (14 made by the hub, 2 ingested from F):
| A/AD/G/GD | min after start | lineage (operators back to the baseline) |
|---|---|---|
| **28/5/127/22** | 77 | gen_skel(polish) |
| 28/5/133/18 | 199 | pull |
| **29/4/131/20** | 210 | polish(gen_skel) |
| 29/4/146/15 | 192 | pull(polish) |
| **31/5/114/28** | 36 | join(base, join(base, gen_skel)) - best G at A <= 31 (was 115) |
| 31/5/115/24 | 174 | polish(join(base, gen_skel)) |
| 32/4/114/26 | 36 | join(base, gen_skel) |
| 35/3/142/21 | 93 | polish(join(ingest, base)) |
| 35/3/146/18 | 49 | polish(trb) |
| 35/3/148/17 | 151 | polish(join(polish(join(pull(polish(trb)), join(polish(trb), base))), join(polish(trb), base))) |
| 35/3/151/16 | 172 | polish(trb(polish(join(join(pull(polish), join(polish, base)), pull(polish(trb)))))) |
| 35/3/177/13 | 95 | ingest (track F) |
| 36/3/161/14 | 51 | osc |
| 37/3/155/15 | 197 | pull(pull(pull(gen_skel(join(osc, join(trb, polish)))))) |
| 37/3/160/14 | 182 | join(trb(osc), polish(pull(gen_skel(join(osc, join(trb, base)))))) |
| 40/3/172/13 | 126 | ingest (track F) |
gen_skel occurs in 8 of the 14 hub lineages (the A28 GD22, A29 AD4 GD20 and A31 G114 points among them).
Per operator (gain per CPU-h, archive gain weights 8/4/2/1 for A/AD/G/GD): join 12.1 (2830 jobs, 3.6 CPU-h),
polish 5.2 (8.4 CPU-h), gen_skel 5.0 (3.3 CPU-h), trb 5.0 (1.7 CPU-h), pull 4.7 (7.7 CPU-h), osc 1.5 (5.4 CPU-h).
long4 (same archive, CPUs 0-11, until 04:30) continues from here.

## Pitfalls
- 05:09 outage = WSL OOM (not ours as far as measured: splice.py on 4-6 circuits peaks at 18 MB).
- `pkill -f` from a shell whose command line contains the pattern kills that shell (exit 15): use `stop.sh`
  or `systemctl --user stop xs-E-NAME`.
- export_splices' front filter lets a tuple equal to a team result through; the sidecar field
  `dominated_by_team` records it.
