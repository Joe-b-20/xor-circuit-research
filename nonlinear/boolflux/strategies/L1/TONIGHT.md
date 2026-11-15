# Tonight's work scored with the L1 measures (L1b), pass 2 at 05:50 UTC (pass 1 was 04:25)

Data: `l1b_score.py` output `~/xs-campaigns/2026-11-15-study/L1/l1b-score-0550.txt` (pass 1: -0424.txt;
tonight.py cache of 13,217 circuit files, 10,798 distinct verified new circuits, each checked with boolflux.core on all 256 inputs, NIST library).
Baseline = long hub archive at its stop (01:30 UTC) + the NIST pin 3d80774.
Every circuit named below was re-checked by me with `campaigns/aes_check.py` (OK, two verifiers).

Labels: [C] = counted from the files and logs named (a count, not a statement about the search space);
[H] = interpretation. "n too small" means fewer than about 5 independent successes: such a rate says
nothing about the next 12 hours.

## 1. Goal boxes A-G, baseline -> now [C]

Distance = G excess + GD excess over the goal box, among circuits inside the goal's A and AD caps.

| goal | baseline best (distance) | now best (distance) | moved by | what moved it |
|---|---|---|---|---|
| A <= 27 | min A 28 (1 AND) | min A 28 (1 AND) | - | nothing; no 27 anywhere |
| B 28/4/130/22 | 131/23, 132/22 (2) | **28/4/131/22 (1)** | T1 | T1 `deep` (one 480-s gate-kernel run at the goal caps 28/4/22) from 28/4/132/24 (02:57). See note 4.1. No further move by 05:50 |
| C 28/5/127/19 | 128/20 (2) | 128/20 (2) | - | unchanged; new 28/5/126/24 (R1) is a front point but not nearer C (GD +5) |
| D 32/4/116/19 | 116/20, 117/19 (1) | same (1) | - | unchanged (T2 walks reach 117/19 again) |
| E 32/6/102/31 | 104/29 (2) | same (2) | - | unchanged |
| F 35/3/138/26 | 139/27, 140/25 (2) | same (2) | - | unchanged; T3's new 142/20, 142/19, 144/18 lie below the box's GD cap but are 4-6 gates over its G cap, and no nearer than 140/25 |
| G 44/4/140/11 | 34/4/134/13 (2) | same (2) | - | by distance unchanged; but see below |

Goal G, other reading [C]: before tonight, nothing inside the A, AD and GD caps of G (A <= 44, AD <= 4,
GD <= 11) existed, ours or published (lowest A at GD 11 was 48). T4 now has 28 circuits there. The best
is **42/4/285/11** (G excess 145; it was 42/4/297/11 at 04:25). This puts T4 inside three of the four
caps for the first time; it does not reduce the distance.

## 2. Front points tonight [C]

35 front points (not dominated by the baseline or by an earlier circuit of tonight), all of the kind
"fewer gates under the same caps" or "a smaller GD in the class". None lowered the smallest A overall,
and none lowered the smallest AD at a given A. V = L1 value model (tier(A, AD) x size; WHAT-WORKS.md section 0).

| agent | front points | V | of which A <= 31 | points (A/AD/G/GD) |
|---|---|---|---|---|
| R1 | 4 | 153.6 | 4 | 28/4/134/19, 28/4/133/19, 28/5/126/24, 29/5/130/18 |
| T1 | 2 | 89.6 | 2 | 28/4/132/20, 28/4/131/22 |
| T4 | 22 | 69.3 | 0 | GD 11 class from A 47 down to A 42 (best 42/4/285/11), and 42/4/230/12 |
| X2 | 2 | 44.8 | 2 | 30/4/129/21 (goal arm, `jump`), 29/4/128/23 (generic arm, polish) |
| T3 | 4 | 13.7 | 0 | 35/3/142/20, 35/3/144/19, 35/3/142/19, 35/3/144/18 (low-GD loop) |
| R2 | 1 | 2.0 | 0 | 39/3/172/13 |
| T2, X1, H2, H3, H4 | 0 | 0 | 0 | - |

V per allocated CPU-h (CPU map x wall since start, an upper bound on CPU used): R1 14.0, X2 10.5,
T4 8.1, T1 7.0, T3 1.6, R2 0.4, others 0. [H] Every agent's V rests on 1-4 points, except T4's. T4's
22 points form one staircase from one recipe and one family. At this n the ranking is not stable.
R1's 28/4/133/19 (05:14, third grind run) is 3 gates over goal B's G cap, so B stays at distance 1.

## 3. Operators and recipes that moved a goal box or lowered A or AD

### 3.1 Moved a goal box [C]
| recipe | agent | jobs / CPU-h | result | n |
|---|---|---|---|---|
| long gate-kernel polish at the goal caps (T1 `deep`, 360-480 s) on A28 AD4 starts from T1's all-pairs join pool | T1 | 7 logged deep jobs, 0.67 CPU-h, plus the unlogged one (~0.03 CPU-h to the hit) | B: 2 -> 1 (28/4/131/22) | 1 success. Too small for a rate |
| GD-pull at A28 (T1 `pullD`: kernel at GD cap = start GD - 1/-2, AD cap off with p 0.3-0.5) | T1 | 59 jobs, 1.79 CPU-h | 28/4/132/20 (front, not nearer B than 131/23) and 1 AD reduction 28/5/134/22 -> 28/4/134/21 (dominated) | 1 front point |
| depth-synth bottom with rank-2 products and shared junk, then kernel polish under GD 11 (T4) | T4 | ~8.5 CPU-h allocated | first circuits with A <= 47 at GD 11; A 48 -> 42 at GD 11; best 42/4/285/11 | 22 front points from one family. G is 145 over the box, and the polish gains are now 4-11 gates per hour |
| low-GD AD3 loop (T3: GF(4) one-point moves + level-1 exchange walks + kernel at GD cap 17-21) | T3 | 2 CPUs from ~03:30, ~5 CPU-h | 4 front points at A35 AD3 GD 18-20 | not a goal box (F needs G <= 138); n = 4 |

### 3.2 Lowered A (result vs its own start; move-level) [C]
| recipe | agent | starts -> results | A reductions | to A <= 31 | any result on the front? |
|---|---|---|---|---|---|
| exact window AND removal: rank test + exhaustive flat products (mc1) and sequential 3->2 (seq2) on archive circuits, then kernel "grind" | R1 | 38,000 windows (minutes of CPU) + three grind runs, ~2 CPU-h | 94 (mc1) + 60 (seq2) result files with A - 1 | 92 | yes, after grind: 28/4/134/19, 28/4/133/19, 28/5/126/24 (from the A29 join products 29/4/136/24 and 29/5/127/30), and 29/5/130/18. The raw A - 1 circuits are all dominated. As a hub operator (andrm, A/B ab3, 1 CPU-h per arm) it gave 0 vs 0: the hub gives it front targets only, and those have no removable window |
| static dep / merge patch (x1patch) on archive members | X1 | seconds | 7 | 7 (A29 -> A28) | no, all dominated |
| X1 walk (flip / split / merge) on BP32, NIST A32 AD7 | X1 | ~2.8 CPU-h allocated, all walks | 100 "lower" + 5 walk files with A - 1 to A - 3 | 100 (32 -> 29, 30) | no: G 228-310 |
| aslack window redesign (hub operator) | R2 | A/B test arm 29 jobs, 0.47 CPU-h; fixed-target 39 jobs, 0.65 CPU-h; then goal run (30 jobs) and A descents for G and F (~1.5 CPU-h) | 2 admitted (40/3 -> 39/3, 37/3 -> 36/3); raw A-reduced windows 120 in the A/B, 32 in the fixed-target study; descents gave 35/3/140/26, 143/22 and 50/4/148/11 | 0 | only 39/3/172/13 (V 2); the descent results are dominated (35/3/140/26 equals a baseline tuple; 50/4/148/11 is dominated by NIST 49/4/148/11) |
| deep2 window re-solve (exact in its case) | H3 | 128 windows, ~0.9 CPU-h logged | 1 (29/5/134/17 -> 28/5/210/31) | 1 | no; same AND span as 61 archive circuits (NIST g128 family) |
| hub gen_skel / osc / pull / polish / join (as by-products in the A/B arms) | R1, R2, X1, X2 | ~8 CPU-h of A/B arms | 13 jobs, mostly A >= 34 | 1 (32/5 -> 31/6 by gjoin) | no |
| X1b walk + new-U filter (x1b_camp) from A28 / A29 starts | X1 | CPU 10, 03:17-06:37 | phase 1: 46 runs (36 from A28, 11 from A29), 0 A reductions | 0 | no; its output is new A28 structure families (3.4), not A reductions |

### 3.3 Lowered AD [C]
1 by T1 pullD (28/5/134/22 -> 28/4/134/21, dominated), 3 by T1 screen polishing of H2's AD6 builds (28/6 -> 28/5,
G 154-157), 3 by hub polish in the A/B arms (32/7 -> 32/6). None on the front at a new smallest AD.

### 3.4 New AND structures at A <= 29 [C]
The baseline holds 6 A28 spans span(1, x, ANDs) (3 AD4, 3 AD5); X1b counted the same. At 05:50
tonight's circuits hold 170 A28 spans (3 AD4, 157 AD5, 10 AD6), and 162 of them are new. Sources: X1 walks,
spangen and x1b_camp (144 new AD5 spans, lowest G 133@26); X1b's 9|1|2|2|14 family (11 new-U, 9-coverable
circuits on 2 distinct 9+5 prefixes); H2's 9|5|14 layers from exact gen13 (69 distinct-span layers), which
T1 then polished (8 + 9 spans; best 28/5/150/30 per T1 and 28/6/149/31). Every new-span A28 is at least
20 gates above the A28 front. H3's 28/5/210/31 and R1's three A28 front points lie in old spans. [H] The new
spans matter for goal A only as starts for 28 -> 27 searches. None is a front point. Exact 28 -> 27 tests on
them so far are all negative, each in its stated case: H3 pair {18, 19} -> 1 on the X1b family, full operand
space, UNSAT [C]; H1-d O2 on X1b g158 and 10 H2 builds, no candidate; X3b by hand on s58, s59 and g158, at
best 28. H3's pair test on H2's family was still running at 05:50.

## 4. Strict notes

1. **28/4/131/22 was an orphan.** It is the best point for goal B, and the only point tonight that
   moved a goal box. Until about 04:30 it existed only as T1's scratch working file
   `T1/run1/scratch/w2/dp/best.bfx` (02:57 UTC): worker w2 was stopped at 03:04 before the job ended, so
   the point was not in T1's job log, T1 found/ or hub best/. I copied it, with start, kernel.cfg,
   kernel.log, aes_check JSON and a sidecar, to
   `~/xs-campaigns/2026-11-15-study/L1/found/rescued/aes-sbox-a28-ad4-g131-gd22-t1-w2-deep-orphan.bfx`.
   T1 has since harvested it (T1/found/front, id 73d90cb694de), and t1run v3.3 now harvests killed jobs.
   [H] The general risk remains: every job that writes its best only at the end loses that best when it
   is stopped. That applies to T4 polish_job.sh and to the L1 / X2 harvest steps overnight.
2. Front points are not goal progress. 34 of the 35 are not nearer any goal box. T4's points have
   A > 35, so the value model weights them low, although they are the only progress toward goal G.
3. The generic hub operators in the A/B arms (about 8 CPU-h in R1, R2, X1 and X2 together) made 1 front
   point, X2 gen2 polish 29/4/128/23 (about 0.13 per CPU-h; the hub-era rate was 1.14). The X2 goal arms
   made 1 more, `jump` 30/4/129/21 (1 job). This agrees with L1's hub-era finding that mature points are
   kernel fixed points.
4. The A-reducing moves work almost only where the extra AND is locally redundant: join products, seeds
   and walk outputs. R1 reports that the A = 28 front shows no removable window; R2 had 0 A reductions on
   A <= 35 front circuits; H3 had 1 SAT in 128 windows. No move lowered the A of a front circuit at A <= 31.
   The value of R1's route comes from the grind after the A - 1 step: 3 of the 4 R1 front points.
5. CPU-h per agent is allocated time, not measured time. Measured CPU appears only for hub-style runs,
   T1's job log and R2's fixed-target log.
