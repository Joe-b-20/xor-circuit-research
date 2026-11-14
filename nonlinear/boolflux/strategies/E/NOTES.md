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

## Pitfalls
- 05:09 outage = WSL OOM (not ours as far as measured: splice.py on 4-6 circuits peaks at 18 MB).
- `pkill -f` from a shell whose command line contains the pattern kills that shell (exit 15): use `stop.sh`
  or `systemctl --user stop xs-E-NAME`.
- export_splices' front filter lets a tuple equal to a team result through; the sidecar field
  `dominated_by_team` records it.
