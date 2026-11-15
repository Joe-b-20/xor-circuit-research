# P1: targets T01 and T03 (A28 gate count), 2026-11-15 from 15:22 UTC

Targets (TARGETS.json; the user's words in USER-REQUEST.md are authoritative):
- **T01** ref NIST 28/4/132/22. Hard A <= 28, AD <= 4. Primary G < 132 at GD <= 22; also >= 3-gate
  reductions at GD <= 24 (tradeoff); ideal both lower. Archive bar (already known, not ours):
  28/4/131/22, 132/20 (strict); 133/19, 135/18, 138/17.
- **T03** ref NIST 28/5/128/20. Hard A <= 28, AD <= 5. Primary G < 128 at GD <= 20; also GD < 20 at
  G <= 128; no tradeoffs. Archive: nothing strict; near 127/22, 130/19, 126/24, 125/25, 124/27.

Code here (`strategies/P1/`), data in `~/xs-campaigns/2026-11-15-targets/P1/`. CPUs 10, 11 (+0 from
~18:30 after xsps). Kernel: hub kernel built from the current `kernel/bfx.c` (sha1 94a75e2c18) into
`DATA/bin/bfx-94a75e2c18` (sha256 e4f373f7...).

Labels: [C] = counted / exhaustive within the stated case; [H] = heuristic or empirical.

## Hard limits: how they are enforced
- Every kernel call carries cap.a 28 and cap.ad = target AD (asserted in `p1run.py Worker.kernel`).
  The kernel never leaves a feasible state for an infeasible one (bfx.c: "feasibility first"), and
  every start is inside the limits, so every kernel state is inside them; outputs are re-checked.
- gen_skel kicks, trb rebuilds and joins are dropped unless A <= 28 and AD <= cap before anything is
  done with them (no repair of out-of-limit states). No A29 starts, no AD-cap-off pulls (T1 used both).
- The pool admits only A <= 28, AD <= cap; T03 pools include AD4 circuits (AD4 <= 5 is legal).

## 1. Starting material (`survey.py` -> DATA/starts.json, 15:38 UTC)
18,490 candidate files (hub archives, results/aes, NIST pin, best-1400, study found/, T1 scratchpool,
targets found/); 489 distinct circuits with A <= 28, AD <= 5 [C, counted]. (A first version also
globbed R1's 1.5 M scratch .bfx files and was stopped; R1/found is covered.)
- AD4 (G, GD) front: 131/22, 132/20, 133/19, 135/18, 138/17, 141/16, 153/15, 175/14. Lowest G at
  any GD is 131 (at GD 22, 23, 25, 26, also NIST 131/31) [C, archive].
- AD5 front: 124/27, 125/25, 126/24, 127/22, 128/20, 130/19, 133/18, 136/17, 150/15.
`reftuples.py` -> DATA/reftuples.json: 1,488 tuples (pinned NIST + all hub archive records +
BEST.json + survey) used for the "new on archive" test.

## 2. Skeleton depth bound vs gate depth (F's `skeldepth.py`) [C, per circuit]
| circuit | GD | skeleton bound |
|---|---|---|
| 28/4/131/22 | 22 | 16 |
| 28/4/132/20, 133/19, 135/18, 138/17 | 20/19/18/17 | 16 |
| 28/4/175/14 | 14 | 14 |
| 28/5/125/25, 126/24 | 25/24 | 17 |
| 28/5/127/22, 130/19, NIST 128/20 | 22/19/20 | 18 |
| 28/5/133/18, 136/17 | 18/17 | 17 |
The bound is the depth if every AND operand / output form is its own Huffman XOR tree (same AND
functions). Unlike the GD 12-15 circuits of track F (bound = GD), the A28 circuits at GD 19-25 have
4-8 levels of slack: their depth is set by XOR sharing, not by the AND skeleton. So GD can be lowered
at the same 28 AND functions; the question is only how many gates the sharing loss costs.

## 3. Runs
- smoke (15:32, CPU 11, 200 s, T03 from NIST 128/20, ref = pin only): trb, pullD -> 28/5/130/19 and
  131/19 (archive tuples); sidecar / aes_check / harvest-on-SIGTERM path works.
- skres probe r1 (CPU 11): skeleton of 28/5/125/25 rebuilt by T4's reqsynth at cap 20 -> 243/18 (huff:
  293/17, boolflux skeleton.synthesize: 196/32); then kernel at caps 28/5/20.
- w10 (CPU 10, 15:39 UTC, 7.4 h, seed 1001): p1run T01, pool 166 legal AD4 starts.
- skres probe r1 result: rebuilt 243/18 -> kernel 120 s 132/20 -> 131/20 at 254 s -> 131/20 at 378 s [H]:
  the kernel recovers ~110 gates from a sharing-free XOR layer in 2 min and lands 3 above NIST 128/20.
- p1synth.py (own timing-driven Paar over the whole skeleton, ALAP-planned AND levels): 206-243 gates
  for D 20-22 and still 199 at D 40 (125/25 skeleton: 64 targets, 453 terms; the circuit has 97 linear
  gates). [H] Cancellation-free pair merging is ~75 linear gates worse than the kernel-optimised layers:
  the published / archive layers rely on XOR cancellation. Kept only as a diversity generator (op skres).
- w10 (T01) stopped 15:57 after 4 jobs (deep 134/22, osc 132/21-23, skel 132/24; nothing new) to give
  CPU 10 to the T03 screen; T01 resumes on CPU 0 from ~18:30.
- scr10 (CPU 10, 15:57): screen.py T03, every distinct AD5 start with G <= 131, GD >= 21 (~100), kernel
  40 s at caps 28/5/20, then 2 x 2 x 240 s polishes of the best 6. First 7 (124/27, 125/25 starts):
  131-133 @20 in 40 s; one 125/25 start gave no feasible circuit in 40 s.
- pswap.py (new move, "last-layer basis swap"): a final product z = AND(p, q) (no AND in its fan-out)
  is replaced by AND(p, p^q) = z^p, AND(p^q, q) = z^q, AND(~p, q) = z^q, AND(p, ~q) = z^p or
  AND(~p, ~q) = z^p^q^1, the correction folded into the readers, then (p .5) the bottom linear
  region re-synthesised by trb (timing-driven Paar). Same A and AD. Kicks of NIST 128/20 land at
  137-143 @21, of 131/22 at 137-138 @22-23; then two kernel runs at the caps (p1run op pswap).
- w11c (CPU 11, 16:02, seed 1103, 7 h): p1run v3 T03 (ops pswap, skres, deep, pullD, osc, trb, join,
  skel, polish, gfree), pool 221 (G <= 134). (w11 / w11b: 16 min, 3 jobs, stopped for v3.)

## 4. Exact recombination by SAT (unionsat.py v1, unionsat2.py v2) - new move
Idea: circuits with the same AND span share a basis [1, x, z1..z28]; every signal of every such
circuit is a coordinate vector over it. Pool their gates as templates (f = a^b, XNOR, NOT, AND p =
L*R with the ODC variants (L, L^R^1), (L^R^1, R)), plus a closure (every XOR/XNOR of two pooled forms
that is itself a pooled form). SAT: availability a(f, l) per form and gate level, outputs at level
<= D, at most 28 AND templates, at most K templates in all. LNS: force the current circuit's
templates outside a neighbourhood (random / level window / fan-in cones / ANDs with cones and
readers), ask for K = G - 1 (improve) or K = G with one freed template dropped (sideways).
Every SAT answer is decoded, verified on 256 inputs and accepted only inside A <= 28, AD <= cap,
GD <= D. [C, per query]: UNSAT = no circuit from the forced + pooled templates with G <= K, GD <= D.
- Spans (rank of the union of 1 + inputs + AND tables; 37 = same span) [C]: the five A28/AD4
  families checked (404a49fc 131/22, 132/20; 378a3983; 9299e1d9 133/19; 857de3da; 044d97ee) share one
  span; AD5: {0f804ba8 (NIST 128/20, 127/22), 856c980f} and {ed95fc41 (124/27, 125/25), 52aee05a}.
- v1 (one family, identical AND functions): descent from scratch at D 20 went 154 -> 132 in 3 s and
  stalled at K 103; LNS runs lns1, lns2 (16:20-16:43) answered UNSAT to every query.
  **Those UNSAT answers are void**: pysat ITotalizer numbers its auxiliary variables from max(lits)+1
  by default, which collided with the pool's variables (self-test "the start circuit satisfies the
  encoding" failed). Fixed in both files (top_id = pool.top). Logs kept in runs/usat/.
- v2 self-test passes; smoke (D 20 from NIST 128/20, no closure, 5 s per query, 60 s): 21 queries,
  2 sideways SAT (other 128/20 circuits), improving queries UNSAT or UNKNOWN.
- lns2seq2 (CPU 10, 16:44): unionsat2 with closure (from NIST 128/20: 108 circuits in the span,
  1,170 forms, 31,525 templates, 252 AND templates), 900 s each: T03 D20 from NIST 128/20, T01 D21
  from 132/20, T03 D19 from 130/19, T01 D22 from 131/22, T01 D19 from 133/19.
  * t03-d20-nist (full closure, 31.5k templates, 20 s per query): 35 queries in 900 s, 24 of the
    improving ones UNKNOWN, 2 sideways SAT. Too large: closure capped at 6,000 added templates from
    then on (`--closure-max`), smaller neighbourhoods.
  * t01-d21 (42.6k templates): 7 queries, all UNKNOWN; killed after 4 min.
  * **t03-d19** (17:03-17:18, closure 6,000 -> 7,941 templates, 111 circuits in the span, seed 23,
    side 0.3, no restriction): 480 queries; improving queries 0 SAT / 332 UNSAT / 19 UNKNOWN,
    sideways 68 SAT / 28 UNSAT / 1 UNKNOWN. A sideways query (K = G with one freed template dropped,
    which admits G < K too) returned **28/5/129/19** at step 241 (6.2 s), from the hub's 130/19
    (results/aes/aes-nist-hub-pull-g130-a28-gd19-ad5.circ.txt). aes_check OK, not dominated by the
    archive or the pin (archive had 130/19 at GD 19; NIST 128/20 has GD 20). Not strict for T03
    (G 129 > 128) and T03 permits no tradeoff: a frontier point, one gate from the T03 secondary goal
    128/19. 9 distinct 129/19 structures saved by lnsharvest.py into found/ (sidecars; their
    'command' field points at the run log; the code version of this run = unionsat2.py before v2.1,
    i.e. --restrict 0, side 0.3, closure-max 6000, pool = starts_fam + shared at 17:03).
  * [H] the productive queries are the sideways ones: plateau walking inside the pooled templates;
    improving queries with K = G - 1 were all UNSAT/UNKNOWN in this run.
- v2.1 (17:05): `--restrict 1`: in each query only templates producing a freed form or with both
  operands among the current circuit's forms are allowed (the rest assumed unselected): queries take
  0.0-0.1 s (17 per s), sideways SAT ~40 %. v2.2 (17:28): neighbourhood scale 1-3, restrict level
  2 (two-step new forms) on a third of the queries, side share 0.6, only every 200th sideways circuit
  written to the out dir (v2.1 wrote all of them: 1,819 files in 4 min). Code snapshots per version
  in DATA/runs/code/ (unionsat2-<sha8>.py).
- Since 17:29: CPU 10 lns2seq6 (seed 61): T03 D19 from the 129/19 (2400 s), T03 D20 from ed95-span
  130/20 (shared/ff71b4b88695, made by the T03 screen/worker from 124/27-type starts), T03 D20 from
  NIST 128/20, T01 D21 from 132/20. CPU 0 lns2seq7 (seed 71): T01 D21 from 132/20, D22 from 131/22,
  D19 from 133/19, D20 from 132/20 (1200 s each). (CPU 0 was idle at 16:57: the 27-AND job there had
  ended; T01 kernel worker w0 ran 16:57-17:19, 5 jobs, best 132/21.)

## 5. GF(2^8) conjugate starts (coordinator tip 17:50: method of P3, which gave T04 114@19)
For G(z) = lam z^(2^k): S(x) = Mout (S(G x) + c) + c with Mout the matching affine map, so a circuit C for
S gives another circuit for S with inputs through G, C unchanged, outputs through w -> Mout(w + c) + c;
the top and bottom linear layers are re-synthesised (P3 mkconj: BP on the top, trb passes). A and AD are
unchanged (same AND structure), the XOR layers - and so the kernel landscape - differ.
Copies of P3 conj.py, mkconj.py, bottom.py in strategies/P1/conj/ (import paths changed only; P3 sha256
cac9b262 / 94202a43 / e3aa6480). Pipeline `conjpipe_p1.sh`: mkconj -> fdrive gate at cap G1 (240 s) ->
fdrive mix at cap D2 (360 s) -> mix at cap D3 (360 s), every kernel call with --cap-a 28 --cap-ad AD,
kernel DATA/bin/bfx-94a75e2c18; every stage best through `p1rec.py` (found/ with sidecar if new, shared/).
- conj11 (CPU 11, 17:54): T03, caps 24 / 20 / 19, starts NIST 128/20, 127/22 (genskel), NIST 124/27, LNS
  129/19 x lam 188, 37, 99 (k 0). First conjugate: NIST 128/20, lam 188 -> 157/25.
- conj0 (CPU 0, 17:54): T01, caps 24 / 22 / 20, starts 131/22 (L1), 132/20 (T1), NIST 132/22, 131/23 x lam
  188, 37, 99. First conjugate: 131/22, lam 188 -> 159/33.
  (CPU 0 LNS seq7 stopped 17:54 during t01-d22-a; t01-d21-a finished: 897 queries, 132/21 plateau, 0
  improvements; CPU 11 scr11 stopped after 1 of 44 starts.)

## 6. Hard-limit audit (18:10): kernel repairs could pass through A29 / AD+1 internally
The first conjugate pipeline wrote a stage best 29/5/139/19 (fdrive mix at cap 19 from a GD 20 start):
the kernel penalty is the SUM of cap excesses, so while repairing GD it may buy depth with an AND above
cap.a (bfx.c review5 S2), and fdrive writes best.circ.txt for an infeasible circuit with lower G.
Consequences, stated plainly:
- Every recorded result was always inside the limits (p1rec.py / p1run legal() / unionsat2 acceptance
  check every output; that 29/5 circuit was rejected, never recorded, never used as a start).
- But kernel-internal states during GD repairs (p1run pullD / osc / skres / gfree jobs whose start was
  above the job GD cap, the screens, the first conjugate stages) were not guaranteed inside A <= 28,
  AD <= cap: 10 such kernel OUTPUTS appear as ILLEGAL_KERNEL_OUTPUT in runs/w0, w11, w11c, scr10 logs
  (discarded). The SAT LNS (unionsat2) never involves the kernel; its 129/19 chain starts from the hub
  130/19 and every accepted step is checked.
- Fix: repair_keep 1 in every kernel call from 18:10 (p1run.py sets HO.KDEFAULTS; fdrive_p1.py = copy of
  F/fdrive.py with repair_keep 1 and best.circ.txt only inside the A / AD caps). With repair_keep no move
  may raise the excess of any single cap, so from a start inside A/AD no state leaves them.
  Pipelines conj0 / conj11 restarted as conj0b / conj11b (18:11) with fdrive_p1.py. [Coordinator note:
  other tracks using fdrive / hub pulls from GD-infeasible starts have the same exposure.]

- conj0b / conj11b (18:11-18:35, lam 188): T03 127/22 lam 188 -> 157/27 -> s1 135/23 -> s2 137/20; T01 132/20
  lam 188 -> 162/27 -> 143/24 -> 140/22. First (v1) items: T03 NIST lam 188 157/25 -> 138/24 -> 140/20;
  T01 131/22 lam 188 159/33 -> 143/24 -> 143/22. All far above the archive.
- Screen of all 2040 conjugates (P3 conj3.py copy in P1/conj/, BP top + Paar bottom proxy, 2 runs; 2 min
  per circuit, runs/conj3/) [H, proxy costs]: for every A28 start the identity is clearly best: NIST
  128/20 identity 49 vs next 53 (lam 186 k0, lam 122 k1); 127/22 50 vs 54 (lam 181 k2); 131/22 55 vs 59
  (lam 16 k0, 77 k4, 232 k4); 132/20 54 vs 58 (lam 40 k7). (In P3 the 117 had a conjugate tying the
  identity; lam 188 was the winner there and is far down the list here.) So the A28 circuits sit in
  their best linear basis by this proxy; the conjugate landscape costs ~4 proxy gates more.
- conj0c / conj11c (18:36): the screened lams (T03: NIST 186/0, 122/1, 2/0; 127/22 181/2, 2/0, 61/0;
  T01: 131/22 16/0, 77/4, 232/4; 132/20 40/7, 30/1, 20/7). First starts 148/26 (T03) and 150/26 (T01)
  instead of 157-162 with lam 188.
- iter10 (CPU 10, 18:36): lns_iter.sh: T03 D20 from NIST 128/20 with rotation closure of 128/20 and of
  127/22 (--rot-extra), 2 x 1200 s; then T03 D19 from a 129/19, 4 x 900 s (restart each round from the
  round best / final walked circuit, lnsharvest between rounds).
- conj0c / conj11c item 1 (screened lams): T03 NIST lam 186 k0: 148/26 -> 132/24 -> 137/20 -> 134/19; T01
  131/22 lam 16 k0: 150/26 -> 139/22 -> 135/21 -> 137/20. Stopped 18:56 [H]: in 9 conjugate pipelines
  (lam 188 and the screened best) the A28 conjugates land 5-9 gates above the archive at every GD.
  Consistent with the screen: unlike P3 117, the A28 circuits have no conjugate that ties the identity.
- 18:56: CPU 11 lnsT03d19 = unionsat2 (v2.4: restrict mix 0/1/2, rotation closure, side 0.6) at D 19 from
  10 distinct (AND-family, tuple) starts with GD <= 19, G <= 133 (130/19 x2 families ... 133/19), 600 s each;
  CPU 0 lnsT01 = same at D 22 (GD 21-22 starts) / D 21 (GD <= 20 starts) from 11 distinct AD4 starts with
  G <= 133. Rationale: the only gain so far (129/19) came from an LNS on a start nobody had walked.
- 18:56-20:50 diverse-start LNS (lnsT03d19: 10 starts at D 19; lnsT01: 11 AD4 starts at D 22 / D 21, 600 s
  each): only local descents inside other families (131/19 -> 130/19, 132/19 -> 131/19, 133/19 -> 132/19);
  nothing new on the archive. iter10 (T03 D 20 from NIST 128/20 with rotation closure of 128/20 + 127/22,
  2 x 1200 s; then D 19 from a 129/19, 4 x 900 s): 128/20 and 129/19 plateaus only.
- scr10c (20:31-20:47, kernel with repair_keep, caps 28/5/19, 90 s): 9 of the 44 LNS 129/19 structures:
  9 x 129/19 -> 129/19 [H]: the 129/19 structures are kernel fixed points at cap 19. Stopped.
- iter10b (20:47): LNS from a 129/19 with the settings of the run that found it (--restrict 0 --side 0.3
  --rot 0), 6 x 900 s. iter11 (20:46): D 19 from another 129/19, 4 x 900 s, then D 20 from the ed95 130/20.
  iter0 (20:50): T01 D 22 from 131/22 3 x 900 s, then D 21 from 132/20 3 x 900 s.

## 7. Final (22:30 UTC)
Per target (archive = state at 15:20 + everything archived since; [C] = verified circuit / counted):
- **T01** (ref 28/4/132/22): best strict = archive 28/4/131/22 and 132/20 (known, not P1); P1 found no new
  strict point and no permitted tradeoff (G <= 129 at GD 23-24). A28/AD4 (G, GD) front unchanged:
  131/22, 132/20, 133/19, 135/18, 138/17, 141/16, 153/15, 175/14.
- **T03** (ref 28/5/128/20): no strict improvement (nothing <= 127 at GD <= 20, nothing <= 128 at GD <= 19).
  New frontier point **28/5/129/19** [C: aes_check OK, not dominated by the archive or the pin; it
  dominates the archive 130/19], 1 gate from the T03 secondary goal, not a T03 result class (T03 permits
  no tradeoff). Front with it: 124/27, 125/25, 126/24, 127/22, 128/20, **129/19**, 133/18, 136/17, 141/16, 150/15.
What worked [H]: span-pooled SAT LNS (unionsat2) with sideways (plateau) queries: the only gain.
What did not [H, counts]: p1run kernel workers (~60 jobs, 3 CPU-h; best only archive tuples), kernel
screens at the target caps (from 28 starts at cap 20: 130-134 @20; 9 LNS 129/19 at cap 19: fixed points),
skeleton re-synthesis + kernel (skres: 131-132 @20), last-layer basis swap + kernel (pswap: 130-131),
GF(2^8) conjugates (9 pipelines incl. screened lams: 5-9 gates above the archive at every GD; screen of
all 2040 conjugates: the identity is the best linear basis of every A28 start by 4 proxy gates).
SAT LNS totals (all runs, 57 logs): 26,719 queries; improving (K = G - 1): 2 SAT, 11,419 UNSAT, 452 UNKNOWN;
sideways: 10,376 SAT, 4,218 UNSAT, 252 UNKNOWN; 8 improving steps in all (129/19 from 130/19 once; the
rest local descents to archive tuples). Each UNSAT is [C] only for its query (forced templates + pool).
