# P3: target T04 (NIST aes-sbox-a32-ad4-g117-gd19-xx85-6), campaign 2026-11-15-targets

## Summary (final, 2026-11-15 ~23:20 UTC; details and times below)
Certified = every kernel stage of the lineage ran with repair_keep 1 or started inside all caps, or an
exact traced replay shows every accepted state inside A32/AD4 (sidecar path_certified true).
| class | A/AD/G/GD | file (P3/found/) | certified |
|---|---|---|---|
| strict (primary, G < 117 at GD <= 19) | **32/4/114/19** | p3-rkG1-s3-mix19-k1-...-73e77c68fc, p3-rkH1-s3-mix19-k1-...-b9c4889e69 | yes |
| strict, both G and GD lower | **32/4/115/18** | p3-rkI1-s1-mix19-k1-...-b8154f67b2 | yes |
| tradeoff (>= 3 gates for +1 GD) | **32/4/113/20** | p3-rkG1-s1-mix21-k1-...-6a349e2eb2 (+3 more) | yes |
| tradeoff | 32/4/113/21, 114/20 | p3-rkG1-s1-mix21-k2-..., p3-rkH1-s2-... | yes |
| strict (equal G, GD -2) | 32/4/117/17 | p3-rkN1-s1-mix17-k2-...-99c3bf2a3e | yes |
| other frontier | 32/4/120/16, 112/22 | p3-rkN1-s2-mix16-k2-...-331d7b06d7, p3-rkH1-s1-mix23-k1-...-b8095ec160 | yes |
| strict, earlier | 115/19, 116/19 | p3-rkD1-..., p3-c115-p19a-... | yes (116@19 by audit replay) |
| NOT certified (A=33 kernel states, audit L3) | 113/20, 113/21, 114/19 (first finds) | p3-pipe-conj-..., p3-pipe116m19-... | no; not claimed |
What worked: GF(2^8) conjugation (x -> lam x^(2^k), lam 188) of the A32/AD4 family gives the kernel
a different linear basis; gate at a loose cap, then mix pulls one or two levels at a time.
What failed: plain trb at cap 19 (T2 plateau), anneal over bottom decompositions (builder too
coarse), generic SAT for tensor rank, packing / gadget models as predictors of built cost, further
conjugation of the already-conjugated circuit.

Hard limits A <= 32, AD <= 4. Primary: G < 117 at GD <= 19. Tradeoff class: G <= 114 at GD 20-21.
Data: `~/xs-campaigns/2026-11-15-targets/P3/` (starts/, runs/, found/). Code here. NIST pin 3d80774.
Kernel for every kernel stage: `~/xs-campaigns/2026-11-14-hub/long/bin/bfx-593fa798f5`
(sha256 e67fefc0...). Evidence labels: [C] computed/exhaustive within the stated case, [H] heuristic.

## Archive at the start (census.py over all hub archives, A <= 32, AD <= 4) [C, counts]
Best G per GD at A32/AD4: 125@15, 125@16, 120@17, 119@18, 117@19 (= NIST), 116@20, 116@21, 115@22-25,
114@26-31. No A31 circuit with AD <= 4 exists in the archive; A28-A30 AD4 circuits have G >= 128.
So the strict box needs one gate below the NIST circuit at its depth; the tradeoff box needs the
114 level at GD <= 21 (now at GD 26).

## Structure (regions.py, bottom.py) [C, computed]
- AND / linear gates per AND level: every A32/AD4 circuit of the family is 9,2,4,17 ANDs with
  linear 18,17-18,3,16,28-30; every NIST A33/AD4 circuit (105@25 ... 116@15) is 9,2,4,18 with
  linear 18-21,17-18,3-4,9,25-32. The A32 circuits pay about +7 L3 and +3 L4 linear gates for the
  17th product saved: NIST 33/4/108/20 vs 32/4/117/19.
- Bottom model (bottom.py): X = 8 input bits, Y = 4-dim inversion-output space (span of the
  last-level AND operands modulo span(1, X); the same function space in every circuit of the family).
  The 79 monomials 1, y_i, x_j, y_i y_j, y_i x_j, x_i x_j are linearly independent as truth tables,
  so identities in this space are exact. Every output is a pure bilinear form in (Y, X) plus a
  constant: a 4 x 8 x 8 tensor T (identical for the 117 and the A33 circuits in a common Y basis).
- The A33 bottom is bilinear: 18 products (u.Y)(v.X), 9 Y-forms used twice (GF(16) Karatsuba for
  y*a and y*c). NIST 105@25 and 108@19 (archive) have the same 18-term decomposition.
- The 117 bottom is NOT bilinear: 12 standard products + 5 mixed products ((Y+X form) * (Y+X form))
  whose Y*Y parts cancel and whose X*X parts are cancelled by adding two level-1 ANDs (a4, a6) into
  the outputs; plus the linear term y0+y2 in four outputs. This quadratic trick replaces the 6 products
  of one GF(4) block (y1, y3, y1+y3) by 5. Cost: 7 mixed L3 forms + 2 correction XORs.

## Method (new; not plain kernel polish)
1. `qflip.py`: flip-graph walk (Kauers-Moosbauer style) on quadratic decompositions of the bottom:
   terms (L, R, w) with affine L, R over (1, X, Y); fixed terms = the front's level-1 ANDs (only
   their output mask may change). Moves preserve the exact sum: share flips, w flips, L*R = L*(L+R+1),
   plus transitions, reductions (zero / constant operand, equal product functions merge).
2. `build.py`: front (all gates of AND level <= 3 of a circuit) + a decomposition -> full circuit:
   operand forms by a BP-style greedy over exact distances, output layer by Paar pair merging with
   level tie-breaks, checked on all 256 inputs. Calibration (calib.py): the 117's own decomposition
   rebuilds to 120@19 / 120@20 / 122@19 (seeds), the A33 one to 111-112 (original 108): the builder
   is ~3-4 gates worse than the polished originals, so built costs are compared with 120, not 117.
3. `qanneal.py`: Metropolis on rank-17 decompositions, cost = built G + 3 * max(0, GD - 19);
   candidates with built G <= 119 saved and passed to the kernel (job.sh, pdrive gate mode).
4. `pdrive.py` = strategies/F/fdrive.py + hard A/AD guard (a stage result above the caps is never
   retained, nor written as best).

## Runs (UTC 2026-11-15)
- 15:30-15:38 trb19a: pdrive trb, cap 19, from NIST-equivalent 117@19 (79bccd2434fd), seed 1:
  4 stages (top, 2 random, bottom rebuild), every kernel stage back to 117@19. Stopped for the
  bottom work. [H] Same plateau as T2's 32/4/19 walks.
- 15:35 rank_sat.py R=18 (plain CNF, CaDiCaL): no answer in 120 s although a rank-18 solution is
  known: generic SAT is too slow for this tensor; replaced by flip walks.
- 15:42-15:46 q16a: qflip walk from the 117 (rank 17), target rank 16, maxrank 18: 600k steps,
  no rank 16. Stopped (rank 16 = A31, not a T04 gate result) to give the CPU to the anneal.
- 15:46-16:02 qa1 (anneal, T 1.0, built-cost objective): no decomposition built below 120 (the
  calibration value of the 117 itself) in 16 min; stopped. hist.py: along a plain qflip walk the
  built G of rank-17 decompositions rises to 131-150 within ~100 flips [H, 150 samples]: the 117
  decomposition is a deep local optimum for one-flip moves, and the builder noise (+-2) is larger
  than the gains sought. Not pursued further as an annealer.
- [C, computed] Every A32/AD4 circuit checked (NIST-equal 117@19, 116@20, 114@26, 119@18) has the
  SAME function-level bottom: the same 17 products, the same 2 level-1 corrections and the same
  linear terms; they differ only in XOR layers (and L*R = L*(L+R+1) operand variants). The kernel
  never changed the bottom decomposition.
- yyspan.py [C]: of the 105 products s*t of two distinct nonzero Y-forms, 6 lie in the span of the
  front signals, each needing >= 10 of them: Y*Y parts must cancel between products.
- rank_sat.py / ufix.py: plain CNF for the bilinear rank (R = 18 known feasible, also with the
  Y-form multiset fixed to the A33 one) gives no answer in 120-250 s: generic SAT is not usable for
  the rank question here. Lower bound [C]: every Y-slice M(y) has rank 8, so the Y-form multiset of
  any bilinear decomposition is a binary [R, 4, >= 8] code: R >= 15 (Griesmer).
- pack.py / packwalk.py: one-AND packing of the A33 bilinear bottom, (A'+t)(B'+s) with the level-1
  AND A*B as correction. [C, computed] In the A33 decomposition every level-1 operand plane holds the
  two X-forms of ONE Y-form pair, so no packable pair exists directly; a 20k-step rank-18 flip walk
  found none either [H].

## Conjugates (conj.py, conj3.py, mkconj.py): a different starting landscape
GF(2^8) inversion satisfies inv = H o inv o G for G(z) = lam z^(2^k), H(w) = (lam w)^(2^(8-k));
so S(x) = Mout (S(G x) + c) + c with Mout = A H A^-1, c = 0x63. Every circuit has 2040 conjugates
that keep its AND structure and middle layers and change only the top layer (forms f -> f o G) and
the output layer (Mout). conj3.py screens all 2040 of the 117 (BP heuristic on the 20 top targets,
Paar proxy on the 8 outputs over the 20 bottom leaves): identity = top 17 + bottom 35 (proxy) = 52;
the best sums are 52 (identity; lam 188 k 0: top 22 + bottom 30; lam 9 k 4: 20 + 32), then 53 x3,
54 x8 [H, heuristic costs].
- 16:11 q1: kernel (pdrive gate, cap 26, 300 s) from conjugate starts (mkconj: BP top + trb):
  lam 188 k 0: 126@26 -> **32/4/114/23** in 168 s (found/p3-cj188c26-...; aes_check OK). Not a T04
  class (GD 23 > 21) but a new A32/AD4 Pareto point: the archive had 115@22-25 and 114@26-31.
  lam 9 k 4: 128@25 -> 116@25; lam 93 k 0: 126@26 -> 119@24 (300 s each): lam 188 stands out.
- 16:27-16:42 cj188-p21: pdrive mix cap 21 from the 114@23: **32/4/115/20** at t = 105 s (osc
  repair), then no change to 900 s (found/p3-cj188-p21-...). Not a T04 class (2 gates for +1 GD,
  the coordinator's rule needs 3) but it dominates the archive's 116@20 and 115@22.
- 16:42 the GD19 pull did not start (job.sh lost its exec bit after an edit from Windows; fixed);
  restarted from the 115@20 in q3.
- 16:42 c115-p19a: pdrive mix cap 19 seed 2 from the 115@20: **32/4/116/19 at t = 145 s** (stage 1,
  osc: kernel at cap 20, then the penalised repair to 19). aes_check OK, new Pareto point on the
  pinned set, **strict T04 improvement** (G 116 < 117 at GD 19, A 32, AD 4).
  found/p3-c115-p19a-a32-ad4-g116-gd19-20c5d2b662.circ.txt. Total CPU from the 117 to this:
  ~3 s conjugation + 300 s (gate cap 26) + 105 s (to the 115@20) + 145 s = ~9 min of one CPU [H:
  one lineage, one seed per step].
  Why it works [H]: all archive A32/AD4 circuits share one function-level bottom and sit on the
  same plateau (T2: 117@19 in every walk); the conjugate keeps the AND structure but moves the top
  and output layers to another linear basis, where the kernel finds cheaper XOR layers (L1 15-16
  and L4 28 in the conjugate lineage vs 17-18 and 30).
  found/...-b49b2addfa is the same circuit as ...-20c5d2b662 (identical gates, only the comment line
  differs: the job's end-of-run record of best.circ.txt); record.py now skips gate-identical files.
- 16:57-17:12 c115-p21b (mix cap 21 seed 3 from the 115@20): 115@20 only (no 114@<=21).
- 17:38 conjpipe (CPU 14) on the lam 188 conjugate of the archive 116@20 (a43e1ae3d73f):
  gate cap 24, 240 s: 127@22 -> 114@24; mix cap 21, 360 s: 116@21 (120 s), 115@21 (181 s),
  113@21 (298 s, trb bottom), **113@20** (362 s): tradeoff class (4 gates for +1 GD) and the lowest G
  at A32/AD4 at any GD in the archive (was 114); mix cap 19 from it: **114@19 at t = 102 s**: strict,
  3 below NIST 117@19 and 2 below every pinned NIST circuit at GD <= 19 (best 33/4/116/15).
- 18:13 compliance (coordinator note COMPLIANCE-1820.md): kernel bfx-593fa798f5 has no repair_keep;
  a kernel stage that starts above the GD cap (every pull / osc repair) ranks by the SUM of cap
  excesses, so intermediate kernel states may have left A32/AD4. pdrive's guard only checked the
  retained stage results. So 116@19, 115@20, 113@20/21 and 114@19 are within limits but their search
  paths are NOT certified (sidecars: path_certified false); 114@23 (one gate stage from a start
  inside all caps) is certified. Stopped chain3 (pipe at conj-119g18) and chain4.
  From 18:15 every kernel call uses repair_keep 1: pdrive DEFAULTS repair_keep 1, kernel
  P3/bin/bfx-4dc199db (= repo kernel/bfx, bfx.c sha256 c8d293b6; an unknown key would abort).
  Re-derivations (repro.sh, same conjugate starts and staged pipeline, new seeds): rkA1/rkA2
  (CPU 14), rkB1 (117 lineage) and rkA3 (CPU 3, once free).
- 18:16-19:10 repair_keep re-derivations from the conjugate starts (repro.sh / repro_beam.sh):
  rkA1 (116@20 conjugate: gate24 -> mix21 -> mix19): 116@23 -> 116@21 -> 118@19; rkA2 (beam 2):
  115@23 -> 115@21 -> 118@19; rkC1 (from the certified 114@24, mix21 beam): 115@21. Not reproduced.
- 19:12-19:31 **audit replays** (pdrive_replay.py = pdrive as it ran, original kernel bfx-593fa798f5,
  unlimited per-stage time so iteration-bounded stages replay exactly, kernel keys trace/tracemoves;
  audit_check.py). [C, per replayed stage: every accepted kernel state is in the trace]
  - L1 (114@23 -> mix cap 21 seed 1, stage 1): result gate-identical to found 115@20; 55,310
    accepted states, max A 32, max AD 4 -> certified.
  - L2 (115@20 -> mix cap 19 seed 2, stage 1): gate-identical to found 116@19; 58,897 states, max A 32,
    AD 4 -> certified (the 116@19 lineage: constructed conjugate, feasible-start gate stage, L1, L2).
  - L4 (113@20 -> mix cap 19 seed 3, stage 1): gate-identical to found 114@19; 58,868 states inside.
  - L3 (114@24 -> mix cap 21 seed 2, the run of 113@21 / 113@20): stage 2 replays gate-identically to
    found 113@21; **stage 1 (osc: repair from 115@22 to cap 21) accepted states with A = 33** (first
    at s1b.trace '0.138 164 resub3 124 33 21 4'). So 113@21, 113@20 and 114@19 are within limits but
    their search path left A32: not certified (sidecars path_certified false). Stage 3 (time-limited
    originally) was not replayed to the end (stopped: the lineage is already not certified).
- 19:15-19:25 rkD1 (certified 114@23 -> mix cap 21, beam seed k2, repair_keep 1): **32/4/115/19**
  at t = 357 s (stage 3 gate, inside cap 21): strict, path certified
  (found/p3-rkD1-s1-mix21-k2-a32-ad4-g115-gd19-d0eb6a2b7f). k1 seed: 115@20.
- 19:37-20:10 certified re-derivation from P5's certified A32/AD4 circuits (coordinator's
  suggestion; byte copies in starts/p5cert-112g22, p5cert-111g25; P5 lineage: NIST 117 -> conjugate
  lam 188 -> P5 gate/mix stages with repair_keep 1). repro_beam.sh, beam 2, repair_keep 1:
  - rkG1 from 112@22: mix21 -> 113@20 (both seeds; also 113@21, 114@20) -> mix20 113@20 -> mix19
    **114@19** (t = 332 s, stage 3 gate; also 115@19).
  - rkH1 from 111@25: mix23 -> 112@22 -> mix21 113@20 (both seeds) -> mix19 **114@19** (t = 288 s,
    trb bottom; also 115@19).
  All path_certified true; the uncertified 113@20 / 113@21 / 114@19 are thus reproduced as tuples
  by different circuits with certified paths (sidecars: reproduces, start_lineage).
- 20:08-21:13 follow-ups from certified circuits (repair_keep 1, beams of 2-3 seeds):
  rkI1 (114@19 -> mix19, trb19): 114@19 again, plus **32/4/115/18** (k1, certified; G and GD both
  below the NIST reference; archive best at A32/AD4/GD18 was 119); rkJ1 (P5 111@25 -> mix22 ->
  mix21 -> mix20): 113@21 -> 113@20 -> 113@20; rkJ2 (114@19 -> mix19, 3 seeds): 114@19 x3.
  [H] 113@20 and 114@19 are a firm plateau for this kernel in this basis: 7 certified lineages (2
  starts from P5, 2 from ours) all end there.
- 21:13-22:59 depth side and more seeds (all certified, repair_keep 1): rkK1/rkK2 (cap 18 from
  115@18 / 114@19): 115@18, 116@18; mix17: 118@17, 119@17; rkN1 (from 118@17): mix17 **117@17**
  (strict: equal G, 2 levels lower), mix16 120@16 and 121@16 (archive best at GD16 was 125);
  rkN3 (117@17 -> mix16): 120@16, 121@16; rkI2 / rkN2 (113@20 -> mix20 -> mix19, 900 s beams):
  114@19 every time. frontier.py --record saved the certified (G, GD) frontier points not yet in
  found/ (112@22, 120@16). Final certified frontier: 112@22, 113@20, 114@19, 115@18, 117@17, 120@16.
- 20:52 conj3 screen of the certified 114@19: the identity is now the best conjugate (proxy 48 vs
  >= 51 for all 2039 others); rkL (lam 2 k 0 conjugate of the 114@19: gate24 -> mix21 -> mix19):
  115@23 -> 116@20 -> 117@19. Stopped after one conjugate (the basis reached by lam 188 is locally
  best for this circuit).
- 17:12-17:27 c116-m19 (mix cap 19 seed 4 from the 116@19): 116@19 only (one further 116@19
  structure in its pareto/, gate-identical to the start? -> not saved twice).

## Gadget SAT (gadget.py) [C within the model, H for the built costs]
Model: the 12 standard products of the 117 fixed; the 5-product block replaced by k ANDs of affine
forms over (1, Z = the whole X space here, Y), output masks, corrections = the 9 level-1 ANDs;
exact degree-2 identity per output; linear residual: X part must vanish, a Y part costs one XOR
per output. Cost = operands that are not existing front signals + outputs with a Y-linear residual.
The 117's own block: 7 new operands + 4 linear outputs = 11.
- k 5, cost <= 11: SAT in 42 s (7 + 4); built (gbuild.py) 124-125 vs 120 for the 117 itself.
- k 5, cost <= 10: SAT in 7 s (10 new operands, 0 linear, 18 ones in the masks); built 126-127.
  The model cost does not predict the built G: the output masks (output-layer sharing) dominate.
- k 5, cost <= 8: unknown after 600 s (CaDiCaL, no budget). cost 9 not run.
- **k 4 (A31 AD4), cost <= 20 (non-binding): UNSAT in 2.6 s.** [C, in this model: the 12 standard
  products of the 117 fixed; any 4 ANDs of affine forms over (1, X, Y); the 9 level-1 ANDs as
  corrections; X-linear residual forced to 0] the 117's 5-product block cannot be done with 4 ANDs.
  It says nothing about other standard parts, other fronts or other decompositions.
