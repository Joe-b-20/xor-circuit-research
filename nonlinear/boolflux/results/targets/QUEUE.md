
## P4-allM (T05, P4): DONE 20:38 UTC in the campaign (2 shards, 0 real 17-gate blocks; P4 NEGATIVES N15) - do not queue
## (original spec kept for the record)
- What: exhaustive 5-AND GF(2^4) inversion-block skeleton search with ALL 15 non-zero linear forms
  of t30..t33 free (a relaxation that covers every inversion-input basis and blocks reading extra
  D-linear signals), AND depth <= 5, maxcost 17.  0 leaves => no 17-gate block for any input
  basis => with NOTES 2.2-2.3, G >= 103 for every circuit with the 103s 9 level-1 and 18 output
  ANDs, whatever the inversion interface (any span(t30..t33) signals).
- Command: `~/xs-campaigns/guard/xsrun P <CPU> P4-allM ~/xs-campaigns/2026-11-15-targets/P4/runs/inv17/allM.log -- ~/xs-campaigns/2026-11-15-targets/P4/runs/inv17/run_allM.sh`
- CPUs: 1. Length: unknown (the identity-basis run took 1,484 s; the relaxation prunes less;
  allow 8 h, stop at the queue end). Memory: < 1 GB.
- Results: `runs/inv17/allM.log` (last lines "nodes N leaves L"), `skel_d5_m17_allM.json`.
- Success: finishes with leaves 0 (decisive [C]); any leaf = a candidate 17-gate block: splice with
  `splice_all.py` (frozen copy in runs/inv17) into the 103 and run aes_check.

## P4-deep (T05, P4): kernel lineages of GF(2^8) conjugates of the 103 (empirical)
- What: continue the best conjugate lineage (lam 236: 104@28 at 18:05) with alternating pdrive stages
  mix --cap 31 --relax 1 / gate --cap 32 (caps A32 AD7; osc runs at cap 32, so every retained state is
  inside A32/AD7/GD32), kernel bfx-94a75e2c18 with repair_keep 1.  Status at 23:30: see
  strategies/P4/STATUS.md; if still worth it, restart from the lineage best with new seeds.
- Command: `~/xs-campaigns/guard/xsrun P <CPU> P4-deepN ~/xs-campaigns/2026-11-15-targets/P4/runs/conj/deepN.log -- ~/xs-campaigns/2026-11-15-targets/P4/runs/conj/deepen.sh <START.circ.txt> <TAG> 8 900 <SEED0>`
- CPUs 1 each, 4 h, memory < 1 GB.  Results: deep-<TAG>-r*/ (best, pareto/), log lines per stage;
  deepen.sh saves (save_found.py, sidecar with path_certified, kernel sha) any G <= 102 at GD <= 32 or
  G 103 at GD <= 31 into P4/found/.
- Success: G <= 102 with GD <= 32 (primary) or 103 with GD <= 31 (strict); verify with aes_check.
  Expectation [H]: low; the exact bound of the conjugate skeletons is 103 (NOTES 2.3b), so a gain needs
  the kernel to change the AND skeleton.

## P7-loop (T09, P7): bopt shared rank-1 bottoms + A-preserving polish, more seeds
- What: `runs/bopt/overnight.sh` loop: bopt.py SA (30k it) on three fronts (NIST a45-ad4-g141-gd12, hub
  48@11 as front donor only, our 42/4/137/12), product weight 0 / 3, bbuild.py, record the build, then a
  300 s gate polish (strategies/P7/fdrive_p7.py = P1's repair_keep-1 driver, kernel P7/bin/bfx-94a75e2c18)
  with caps GD12, AD4 and A = the build's A (<= 45).  Every kernel start is inside all caps.
- Command (one per CPU, different SEED0/TAG):
  `XS_MEM=1G ~/xs-campaigns/guard/xsrun P <CPU> P7-night<N> ~/xs-campaigns/2026-11-15-targets/P7/runs/bopt/night<N>.log -- bash ~/xs-campaigns/2026-11-15-targets/P7/runs/bopt/overnight.sh $(date -d "<END UTC>" +%s) <SEED0, e.g. 20000> N<N>`
- CPUs: 1-2. Length: 8 h (about 80 seeds per CPU). Memory: < 300 MB.
- Results: builds and polished bests land in `~/xs-campaigns/2026-11-15-targets/P7/found/` with sidecars
  (rec.py / p7job.py; aes_check line inside); afterwards run `python3 strategies/P7/certify.py` and
  `python3 strategies/P7/donor.py` (path_certified / donor fields).
- Success: any verified A<=45/AD4/GD<=12 circuit with G <= 136 (beats our 42/4/137/12), or a new (A, G)
  Pareto point at GD12 (e.g. A39 with G <= 138, A38 at any G <= 141).  Expectation [H]: modest; seed
  spread of the SA model cost is 72-80, polish gains 0-6.

## P5-allbasis-d4 (T05, P5): DONE in the evening session (21:33 UTC), not needed overnight
- Result: 25 998 relaxed skeletons (48 at 17), none at <= 18 with only a 4-form basis free; see strategies/P5/NOTES.md. Kept below for reproduction only.

### (original spec) AD6 at 103 for every inversion-input basis (exact skeleton search)
- What: invskel.c (C port of the P5 5-AND inversion-block skeleton search) with ALL 15 non-zero linear
  forms of t30..t33 free (relaxation covering every inversion-input basis, as P4-allM), AND depth <= 4,
  maxcost 18 (= a 103-gate S-box with the 103 top 18 + pre 15 + 9 ANDs and bottom 18 ANDs + 25).
  0 kept => [C] no AD6 103 with the 103 top ANDs/output ANDs (bottom XOR 25 is [H], P4 NOTES 2.3).
  The depth-3 version (AD5) runs in the evening session (c_inv103all_d3_m18.log, ~30 min).
- Command: `cd ~/xcr-boolflux/nonlinear/boolflux/strategies/P5 && ~/xs-campaigns/guard/xsrun P <CPU> P5-alld4-<i> ~/xs-campaigns/2026-11-15-targets/P5/runs/alld4-<i>.log -- python3 cskel.py ~/xs-campaigns/2026-11-15-targets/P5/specs/inv103all_d4.json --depth 4 --maxcost 18 --shard <i>/<n> --bin ./invskel_c2 --out ~/xs-campaigns/2026-11-15-targets/P5/runs/c_inv103all_d4_m18_s<i>.json`
  (one unit per CPU, i = 0..n-1).
- CPUs: 1-4 (shards). Length: estimate 3-6 CPU-hours total (depth 3 shard 0/60 took 28 s; depth 4 was
  ~5x depth 3 in the 4-free model). Memory: < 50 MB.
- Results: runs/alld4-<i>.log, first line "STATS nodes N leaves L kept K ...".
- Success: all shards finish with kept 0 (decisive [C] within that case). Any kept skeleton: splice
  with strategies/P5/splice_all.py into the 103 (inputs t30..t33 free forms need the pre layer to deliver
  them: check cost) and aes_check.

## P5-ad4lin (T05 AD4 any GD, P5): kernel lineage from the A32/AD4 112/24 and the certified 113/23
- What: strategies/P5/lineage.sh: rounds of p3_pdrive gate cap GD30 (300 s) then mix cap GD26 (400 s),
  each from the lowest-G circuit so far; kernel bfx-94a75e2c18, repair_keep 1, caps A32 AD4.
- Command: `~/xs-campaigns/guard/xsrun P <CPU> P5-linN ~/xs-campaigns/2026-11-15-targets/P5/runs/linN.log -- ~/xcr-boolflux/nonlinear/boolflux/strategies/P5/lineage.sh <START> 4 <TAG> 20 <SEED0>`
  START = P5/starts/ad4-113-23-cert.circ.txt (certified lineage) or the best P5/found AD4 file.
- CPUs: 1-2. Length: 20 rounds = ~4 h each. Memory: < 1 GB.
- Results: P5/found/p5-<TAG>-...circ.txt with sidecars (path_certified; lineages from P3s 113/20 inherit path_certified false).
- Success: A32/AD4 with G <= 111 at any GD, or 112 at GD <= 23 (new Pareto points). [H] modest.

## P6-q12 (T08 GD12, P6): depth pulls from GF(4)-coordinate variants with depth slack
- What: strategies/P6/pullrun.py (level-3 class re-basing, hybrid depth-feasible build, gate kernel with
  repair_keep 1 under caps A35 AD3 GD12, cost,gd, 2 x 240 s per build, 3 builds per parent, --evolve 2).
  Parents: the coordinate variants of 177@13 whose best re-basing has max output Kraft 0.75 at cap 12
  (l3scan.py; one- and two-point moves) + found/ 181@12.  This recipe gave today's strict 35/3/181/12.
- Command (shard k of N, one per CPU):
  `XS_MEM=1G ~/xs-campaigns/guard/xsrun P <CPU> P6-q12-<k> /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/queue/log-q12-<k>.txt -- bash /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/queue/pull_job.sh q12-<k> 12 8 <1400+k> /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/queue/parents12.txt <k> <N>`
- CPUs: 2 wanted / 1 minimum. Length: 8 h (--hours), then harvest (~1 min). Memory < 300 MB (XS_MEM 1G).
  Every kernel start is inside A35/AD3/GD12 (builds are kept only inside the caps): path certified.
- Results: P6/queue/run-q12-<k>/ (pool/, jobs/, pull.jsonl); new Pareto points (A<=35, AD<=3) saved by
  harvest.py into P6/found/ with sidecar + aes_check line (run-q12-<k>/harvest.out).  If the job is
  stopped before the end, run `python3 .../strategies/P6/harvest.py .../P6/queue/run-q12-<k> --target T08`.
- Success: a found/ circuit with GD <= 12 and G <= 180 (today's best 181@12); GD 11 at any G <= 191.
  Expectation [H]: low-moderate (slack-variant pulls gave 181-188; 181 twice from one build).

## P6-q13 (T08 GD13, P6): the same recipe at cap 13
- Parents: found/ 171@13, 172@13 and 8 coordinate variants of 162@14 (P6/queue/parents13.txt).
- Command: as P6-q12 with `pull_job.sh q13-<k> 13 8 <1500+k> .../P6/queue/parents13.txt <k> <N>`.
- CPUs: 1. Length 8 h. Memory < 300 MB.  Success: G <= 170 at GD <= 13 (today's best 171@13).

## DISABLED by user 23:50 UTC (no 27-AND work): Z1-A (target Z, 27 ANDs): class-seeded semi-member gen13 over the A28 span classes
- What: H2 real-model gen13 with members + X3's 107,100 semi-members, class-seeded (gen13c), over the
  three E + K = 27 shapes that all A28 share (Z1 NOTES 2b): S9 (g131 9-span, BMP middle) K = 13;
  S10 (g124 10-span) K = 12; S9 + AD4's own 6-AND middle K = 12; gamma reps 0 1 4 5 6 7.
  Member-seeded runs of the same cases are in progress / done (runs/g13/cases.log); class-seeded
  is exhaustive for more layer types (gen13c completeness: C(m,2) + sum_c C(s_c,2) >= 32 pairs).
- Commands (one per CPU, k = 0, 1, 2; queue files already written, 6 cases each):
  `XS_MEM=4G ~/xs-campaigns/guard/xsrun Z <cpu> z1A-<k> /home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/runs/q/zA<k>.log -- bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/Z1/qrun.sh /home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/runs/q/zA<k>`
  (zA0 = S9 K 13, zA1 = S10 K 12, zA2 = S9 + 6-mid K 12; each line `G13_TIMEOUT=5400 bash .../Z1/g13case.sh NAME file:SPAN GAMMA K c semi [midfile:...]`).
  qrun exits when the queue is done only if `touch <queue>.stop`; otherwise it idles (no CPU).
- CPUs: 3. Run length: <= 6 x 1.5 h = 9 h. Memory: <= 3 GB per process (cap 4G).
- Results: one line per case in `/home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/runs/g13/cases.log`;
  covering sets are re-verified on 256 inputs, minimised, built and aes_checked by rvd_z1.py into
  `/home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/found/z1g13-*` with full sidecars (sidecar.py).
- Success: "covering N", N >= 1, with an rvd line "total ANDs 27" and "OK". "covering 0" with rc 0 =
  complete case [C, that pool]; rc 124/143 = capped, [H] only. Positive control of this pipeline:
  ctl-s9m6-semi-g1 (member-seeded) finds exactly the AD4 layer (cases.log 19:22 UTC).

## DISABLED by user 23:50 UTC (no 27-AND work): Z1-B (target Z): full-operand pair -> 1 AND windows of the AD5-type A28 layers
- What: for each distinct-span 10+5+13 A28 layer with a parallel (equal-usage) last-layer pair: one
  new AND with operands anywhere in span(x, all 26 kept ANDs) replacing the pair (= 27 ANDs).
  Exhaustive over 2^33 first operands with H3's r1enum_v5. The prefix-operand version of all 150
  pair windows is UNSAT [C] (Z1 NOTES 3); g124 {17,26} / g128 {20,27} full runs finish tonight.
- Command: `XS_MEM=1G ~/xs-campaigns/guard/xsrun Z <cpu> z1B-<k> /home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/runs/q/zB-<k>.log -- bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/Z1/qrun.sh /home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/runs/q/zB<k>`
  where zB<k> = every n-th line of `/home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/runs/q/zB`
  (52 lines = 13 windows x 4 Gray-range quarters; split e.g. `awk "NR % 4 == k"`), each line
  `bash .../Z1/pairjob.sh IN LO HI OUT`, ~1.55 h per quarter.
- CPUs: any number (52 x 1.55 h = 80 CPU-h total; 8 CPUs ~ 10 h). Memory: ~10 MB per process.
- Results: `/home/joebachir20/xs-campaigns/2026-11-15-targets/Z1/runs/pair/todo/*.q<i>.out`.
- Success: any line starting "H " (a hit = operand a; b from the linear solve, see H3 pair_post.py;
  build + aes_check by hand). "DONE ... hits 0" in all 4 quarters of a window = [C] for that window
  (kept ANDs fixed, new AND operands in span(x, kept ANDs)). Low prior: all such windows tested
  so far (H3: 2; Z1: 150 with prefix operands) are UNSAT.

## P3-pull (T04, P3): certified pulls of the A32/AD4 conjugate lineage toward 113@19 / 112@<=21
- What: staged pdrive (strategies/P3/pdrive.py = F/fdrive + hard A/AD guard, repair_keep 1, kernel
  P3/bin/bfx-4dc199db) with a 2-3 seed beam per stage (strategies/P3/repro_beam.sh), from certified
  starts only: P3/found/p3-rkG1-s3-mix19-k1-a32-ad4-g114-gd19-73e77c68fc.circ.txt (114@19),
  P3/found/p3-rkG1-s1-mix21-k1-a32-ad4-g113-gd20-6a349e2eb2.circ.txt (113@20),
  P3/starts/p5cert-112g22.circ.txt and P3/starts/p5cert-111g25.circ.txt (copies of P5 certified circuits).
- Command (one per CPU; vary SEED0 per run):
  `~/xs-campaigns/guard/xsrun P <cpu> P3-n<k> ~/xs-campaigns/2026-11-15-targets/P3/runs/n<k>.log -- ~/xcr-boolflux/nonlinear/boolflux/strategies/P3/repro_beam.sh START n<k>-s<SEED0> "mix:20:600 mix:19:600" SEED0 3`
  (START = the 113@20 above), or START = P3/starts/p5cert-111g25.circ.txt with stages
  "mix:22:360 mix:21:360 mix:20:360 mix:19:360".
- CPUs: 1-4. Run length: any (each stage x seed is one job of 6-10 min; stop with
  `systemctl --user stop xs-P-P3-n<k>`). Memory: < 200 MB per process.
- Results: every run-Pareto circuit of class strict or tradeoff is aes_checked and saved by record.py
  to P3/found/ with path_certified true (the start must be certified, see P3/starts/CERTIFIED.md).
- Success: 32/4/<=113/19 (strict, below the current 114@19) or 32/4/<=112/<=21 (tradeoff). Prior [H]:
  in the evening runs every certified lineage reached 113@20 at cap 21 and 114@19 at cap 19 within
  10-15 min, and nothing lower appeared (about 6 CPU-h).

## P1-lns (T03, T01, P1): span-pooled SAT LNS walks (unionsat2), longer rounds
- What: `strategies/P1/lns_iter.sh` = rounds of `unionsat2.py` (exact SAT recombination of every archived
  circuit in the start circuit AND span + DATA/shared, rotation closure, sideways plateau walking, hard
  caps A <= 28 and AD <= cap checked on every accepted step; no gate kernel involved), each round restarts
  from the previous best / final walked circuit and runs lnsharvest.py (found/ + shared/).
  The only P1 gain of the day (28/5/129/19, T03 class, not strict) came from this; expectation [H]: low.
- Commands (one CPU each; START129 = any `~/xs-campaigns/2026-11-15-targets/P1/found/P1-T03-a28-ad5-g129-gd19-*.circ.txt`):
  `cd ~/xs-campaigns/2026-11-15-targets/P1 && ~/xs-campaigns/guard/xsrun P <CPU> P1-qT03d19 $PWD/runs/qT03d19.log -- ~/xcr-boolflux/nonlinear/boolflux/strategies/P1/lns_iter.sh q-t03-d19 19 5 START129 12 1800 501`
  `... xsrun P <CPU> P1-qT03d20 $PWD/runs/qT03d20.log -- ~/xcr-boolflux/nonlinear/boolflux/strategies/P1/lns_iter.sh q-t03-d20 20 5 /home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad5-g128-gd20-xx100-27.circ.txt 12 1800 601 --rot-extra /home/joebachir20/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-genskel-g127-a28-gd22-ad5.circ.txt`
  `... xsrun P <CPU> P1-qT01d22 $PWD/runs/qT01d22.log -- ~/xcr-boolflux/nonlinear/boolflux/strategies/P1/lns_iter.sh q-t01-d22 22 4 /home/joebachir20/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-study-L1-l1-g131-a28-gd22-ad4.circ.txt 12 1800 701`
- CPUs: 1-3 (each line independent). Length: 12 rounds x 30 min = 6 h. Memory: < 1 GB each (measured 0.4-0.5 GB).
- Results: `P1/runs/iter/<name>/r<k>.log` (one JSON line per query), `r<k>-best.circ.txt`, `r<k>-out/pool.json`
  (exact pool list with sha256); new circuits -> `P1/found/` with sidecars (aes_check line), all -> `P1/shared/`.
- Success: a found/ sidecar with class strict: T03 G <= 127 at GD <= 20 or G 128 at GD <= 19; T01 G <= 130
  at GD <= 22, or 131 at GD <= 21, or 132 at GD <= 19 (new strict points; the archive bar is 131/22, 132/20).
  Check `grep -h IMPROVED P1/runs/iter/q-*/r*.log` and `ls P1/found/`; verify with campaigns/aes_check.py.

## P2-T06-resyn (agent P2, target T06: A<=34, AD<=4, G < 134 at GD<=13)
- What: rank-1 bottom resynthesis at GD 13. orbsearch.py takes 30600 symmetry images of each of 7
  archive bottoms on a fixed 16-AND front and keeps the Kraft-feasible ones. resyn.py builds them
  with depthsynth, reusing the front. Then fdrive_p2 trb polishes every start (repair_keep 1, kernel
  bfx-94a75e2c18). Today three such starts went 144 -> 136, 151 -> 136 and 158 -> 137 in about 2-4 min
  each. These are new basins, not yet below the 134 bar. Overnight: more fronts and more starts.
- Commands (one CPU each, sequential inside each):
  `~/xs-campaigns/guard/xsrun P 12 p2-on-t06a ~/xs-campaigns/2026-11-15-targets/P2/runs/on-t06a.log -- bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/overnight_t06.sh /home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a34-ad4-g134-gd13-xx100-43.circ.txt on-t06a 1500`
  `~/xs-campaigns/guard/xsrun P 13 p2-on-t06b ~/xs-campaigns/2026-11-15-targets/P2/runs/on-t06b.log -- bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/overnight_t06.sh /home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a34-ad4-g139-gd13-xx105-22.circ.txt on-t06b 1500`
- Run length: up to about 40 starts x 25 min per CPU. Each start is independent, so the run can be
  stopped at any time.
- Memory: < 1 GB each (the default XS_MEM 4G is enough).
- Results: verified circuits go to ~/xs-campaigns/2026-11-15-targets/P2/found/ (t06-*.circ.txt +
  .json, path_certified true). runs/on-t06a/bar.txt lists those better than 34/4/134/13.
- Success: any verified 34/4/G/13 with G <= 133 (strict against the bar). G 135-138 are only new
  frontier points.

## P2-T02-trb (agent P2, target T02: A<=28, AD<=4, G < 174 at GD<=14)
- What: the 174 came from fdrive mix stage 17 (trb-bottom) after 40 min. Seven later 45-60 min runs
  (trb, mix, conjugates, skeleton pull) did not go below 174. Overnight: many short independent trb
  seeds from the 174.
- Command (one CPU):
  `~/xs-campaigns/guard/xsrun P 12 p2-on-t02 ~/xs-campaigns/2026-11-15-targets/P2/runs/on-t02.log -- bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2/overnight_t02.sh 101 16 1800`
- Run length: 16 x 30 min = 8 h. Memory < 1 GB.
- Results: found/ (t02-*.circ.txt + .json, saved only if better than the 174 start).
- Success: a verified 28/4/G/14 with G <= 173.

## P2-T06-bopt (agent P2, target T06, after the coordinator tip from P7; untested end to end)
- What: P7's bottom annealer, copied to strategies/P2/bopt.py with two additions: --calib starts
  from the circuit's own 18-product bottom, and --exact uses the exact Y-form levels of the front
  (ylev.py) instead of P7's sum-of-base level model. In P7's model the 134's own bottom fails Kraft
  at GD13 for 7 outputs; with --exact it passes (model cost 65). Then strategies/P2/bbuild.py (P7
  copy) builds the plan and fdrive_p2 polishes it at caps GD13 AD4 A34.
- Caveat: bbuild builds Y-sums from the base Y-forms, so the built GD can come out at 14. In that
  case use polish2.sh at cap 13 (repair_keep 1), or teach bbuild to take the front's own Y-form
  realisation.
- Commands (one CPU, roughly 1-3 h per seed; 2500 iterations took more than 150 s):
  `cd /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/P2 && python3 -u bopt.py /home/joebachir20/xs-campaigns/2026-11-15-study/best-1400/aes-sbox-a34-ad4-g134-gd13-xx100-43.circ.txt --cap 13 --amax 34 --iters 20000 --seed 5 --calib --exact --out /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/bopt/s5.json`
  `python3 bbuild.py /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/bopt/s5.json /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/bopt/s5.circ.txt`
  `bash polish2.sh T06 /home/joebachir20/xs-campaigns/2026-11-15-targets/P2/runs/bopt/s5.circ.txt 34 13 gate 5 1200 t06bopt-s5`
  (run all three under ~/xs-campaigns/guard/xsrun P CPU ...)
- Success: a verified 34/4/G/13 with G <= 133.

## P6-c3 (T07, P6): GF(2^8)-conjugate pipeline on the AD3 low-G starts (gave today's strict 35/3/139/25)
- What: `runs/t07c3.sh TAG START NBEST`: P3 conj3 screen of all 2040 conjugates (read-only use of P3 code),
  the NBEST best-scoring non-identity ones -> P3 mkconj -> P6 kern.py caps A35 AD3 GD31 (200 s) -> GD27
  (2 x 200 s), repair_keep 1, every start inside A35/AD3; harvest.py saves new Pareto points (target T07).
  Today: 140@25 lam 97 k0 -> 139@25 (strict), lam 99 k0 -> 140@22.  Overnight: deeper lists (NBEST 40) on
  140@25, 139@25 (ours), 140@22 (ours), NIST 139@27/139@31, several kernel seeds per conjugate.
- Command (one per CPU):
  `XS_MEM=1G ~/xs-campaigns/guard/xsrun P <CPU> P6-c3-<tag> /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/c3-<tag>.out -- bash /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/t07c3.sh <tag> <START> 40`
  with START e.g. /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/found/aes-sbox-a35-ad3-g139-gd25-107a7c3b5078.circ.txt,
  .../found/aes-sbox-a35-ad3-g140-gd22-ecd3572a7c9b.circ.txt, /home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a35-ad3-g139-gd31-xx104-25.circ.txt.
  (Use a fresh <tag> per run: the script writes runs/c3-<tag>/.)
- CPUs: 3 wanted / 1 minimum. Length: ~3 min screen + ~10 min per conjugate (40 -> ~7 h). Memory < 300 MB.
- Results: runs/c3-<tag>/log.txt (one line per conjugate), harvest.out; P6/found/ (sidecars, aes_check, path_certified).
- Success: G <= 138 at GD <= 27 (T07 primary) or G <= 136 at GD <= 29 (tradeoff); also 139 at GD <= 24.

## P6-t07p (T07, P6): kernel seeds and conjugates from today's 138@24 / 139@23 (follow-up of P6-c3)
- What: (a) `runs/polish139c.sh`-style seed sweep (kern.py, repair_keep 1, caps A35 AD3 GD 27/25/23, 240 s
  per seed) from found/aes-sbox-a35-ad3-g138-gd24-d6946cbba230.circ.txt; (b) `runs/t07c3.sh <tag> <that file> 40`.
  Today 2 of 3 seeds from 139@23 gave 138@24.
- Command (a): copy /home/joebachir20/xs-campaigns/2026-11-15-targets/P6/runs/polish139c.sh, set S= the 138@24
  file and a new output dir, loop 40 seeds; run under `XS_MEM=1G ~/xs-campaigns/guard/xsrun P <CPU> P6-t07p ...`.
- CPUs 2 (one per part), 8 h, memory < 300 MB. Results: harvest.py into P6/found/ (target T07).
- Success: G <= 137 at GD <= 27, or 138 at GD <= 23.
