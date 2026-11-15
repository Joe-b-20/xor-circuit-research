# How BoolFlux got here

BoolFlux was built on 2026-11-13 and 2026-11-14 on the local branch `boolflux-2026-11-13`. Nothing
has been published or pushed. This page is a dated record of that work: what was built, what
the reviews found and how it was fixed, which measurements changed the method, what the
2026-11-14 AES push produced, failed experiments included, and the hub and the study phase of
2026-11-15. Times are UTC. Commit times are
converted from the repository's timestamps (-0500; -0400 for the October commit).

**Corrections of 2026-11-15.** The text below was checked against the run records
(`strategies/L2/DOC-AUDIT.md`, with the hub-era analysis in `strategies/L1/WHAT-WORKS.md`).
Corrected sentences carry "(corrected 2026-11-15)". Numbers that depend on the result set were
marked "(updated after re-curation)" until the curation of 2026-11-15 06:53 UTC (commit cb8fd56),
which added the hub runs, track F's last AD3 runs and the study phase. Those places now carry
"(re-curated 2026-11-15)" and give that curation; text that describes the state of 2026-11-14
keeps the numbers of the 17:54 UTC curation and says so.

**Sources and marks.** The commit hashes come from
`git log --format='%h %ci %s' boolflux-2026-11-13`. Other sources are named next to each claim.
Campaign records live outside the repository, in `~/xs-campaigns/2026-11-13-boolflux/` and
`~/xs-campaigns/2026-11-13-aes/` ([runs/INDEX.md](runs/INDEX.md)). The strategy code of the AES
push (`strategies/C,D,E,F,G/`) was committed in 377b03f and the hub (`hub/`) in 97abda7, both
after this page was first written. **[V]** marks a circuit that passed both verifiers
([VERIFICATION.md](VERIFICATION.md)) and appears in [results/MANIFEST.json](results/MANIFEST.json).
**[C]** marks an exhaustive or exact computation by track C (`strategies/C/NOTES.md`).

## Timeline

| when (UTC) | commit / record | what |
|---|---|---|
| 2026-10-31 00:38 | 4958999 (main) | `nonlinear/` added: NIST AES S-box circuits pinned at usnistgov/Circuits **0876577**, the boolcirc verifier and metrics, an AND-skeleton view |
| 2026-11-13 17:14 | 13d5cb8 | branch `boolflux-2026-11-13` created from `main` a6ef62d, with the local `nonlinear-extension` branch merged in ([CHECKPOINT.md](CHECKPOINT.md)) |
| 11-13 17:50 | 3924152 | first BoolFlux: gate kernel (exact care-set resubstitution with 0-3 new gates of any two-input type, depth/AND caps with repair, annealing), AND-skeleton kernel (swap, merge, split, perturb with exact span checks), CLI, cost models, targets and S-box tables, naive ANF starts, independent verifier, tests |
| 11-13 18:05 | 0640d28 | fixes from review 1 (below) |
| 11-13 18:15 | 3b9e0fd | model convention: NOT written as `XNOR t a 0` counts as XNOR when the two verifiers' tallies are compared |
| 11-13 18:44-18:45 | 0e06d96, cffca77 | first verified AES results; the `gc6` model (the gate complexity of Stoffelen 2016 and Zhang-Huang 2023) |
| 11-13 19:33 | 920fc4a | results, ledger, reports. Claimed against pin 0876577: 46 NIST forward circuits searched under their own caps, 33 improved, 18 new on the published set, fewest gates at GD <= 11, 12, 13, 14, 18, 19 (150, 146, 137, 126, 110, 108) |
| 11-13 20:10 | caa29af | NIST re-pinned at **e6ac0d0** (191 files). The pin had moved upstream: forward circuits in `aes-sbox/` went from 46 to 78, including 159@GD10, 148@11, 141@12, 133@13 and 127@14 |
| 11-13 20:12-20:28 | e5bab59, 9f4c8df | results manifest with provenance and three-way verification. Every comparison was redone at e6ac0d0, including runs from the 32 newly published circuits: **12 tuples survive. The claims at GD 11 and 12, and 13 of the 18 points, are withdrawn** ([CHECKPOINT.md](CHECKPOINT.md)). The independent audit's findings were fixed: chi3 bit order, NOT/XNOR header tallies, stale ledger rows. BGC and GC were separated |
| 11-13 20:59-23:02 | 3a71f0f ... 154ded8 | method-and-performance study: move trace, ablation switches, exact linear mode, parent-seeded skeleton rebuild, no-op filter, incremental Paar, benchmark driver; review 2 and its fixes |
| 11-14 00:45 | 5de0fd2, 7637b20 | study report ([bench/REPORT.md](bench/REPORT.md)); new point 124@GD14 A38 from one benchmark run **[V]** |
| 11-14 04:44-05:09 | `~/xs-campaigns/2026-11-13-aes/` | AES push begins, tracks C, D, E, F (below), with review 3 running alongside |
| 11-14 05:09 | D/STATUS.md | outage: the OOM killer stopped a 17 GB python3 (PID 3896264) and WSL went down. The process belonged to no track D job (those were 30-70 MB). Track E's `splice.py` peaked at 18 MB (E NOTES) |
| 11-14 ~14:28 | `~/xs-campaigns/guard/memguard.log` | machine restarted, work resumed under memory guards: `xsrun` (systemd units with a memory cap), per-track slices, and the `memguard` watchdog (`~/xs-campaigns/guard/`) |
| 11-14 14:27 | 0659eb9 | review 3 fixes: lexicographic ranking everywhere, repair-safe `pipe`, shared `workflow.py` and `cli.py flow`, structural no-op filter, BUF accounting, 15 regression tests |
| 11-14 15:48 | 8225691 | REPORT section 7: review-3 corrections, and the repeated no-op A/B, which showed no measurable effect |
| 11-14 17:26 | 417e449 | NIST re-pinned at **3d80774**, upstream HEAD on that day. It adds the forward circuits a33-ad4-g125-gd14 and a34-ad4-g139-gd13 and two inverse circuits. Also `refresh.py --repin`, the `aes-sbox-sel` table and `best_table.py` |
| 11-14 17:26-17:28 | E/F NOTES, main/queue.log | tracks E and F and the main queue stopped. Track C's exhaustive runs and track F's AD3 runs (started 17:31-17:34) were still running when this page was written |
| 11-14 17:40-17:54 | this documentation pass | 36 AES-push circuits curated into `results/aes/` (`campaigns/curate_aes.py`, `curated_utc` 17:54); MANIFEST.json regenerated; `verify_all.py` run: all OK |
| 11-14 17:38-18:40 | `~/xs-campaigns/2026-11-14-hub/`, 97abda7 | hub built; first A/B, hub against the memetic splice arm, 4 CPUs each for 1 h |
| 11-14 18:41 - 11-15 01:30 | `2026-11-14-hub/long`, f9fe6f7 | hub long runs (five scheduler starts) and six 1-CPU 1-hour A/B arms: 65.9 CPU-h, 7,231 jobs in all (`strategies/L1/WHAT-WORKS.md`) |
| 11-14 22:50 | `F/ad3b/` | track F's AD3 runs end: 35/3/177/13, 35/3/162/14, 35/3/142/22, 40/3/172/13, 39/3/156/15. (Re-curated 2026-11-15.) 177/13 and 162/14 are in the manifest now (`aes-nist-F-gate-g177-a35-gd13-ad3`, `aes-nist-F-trb-g162-a35-gd14-ad3`; the hub made the same tuples). The other three were not curated: 35/3/142/19 (T3), 39/3/172/13 (R2) and 37/3/155/15 (hub) dominate them |
| 11-14 ~23:55 | `C/STOPPED-gq.txt`, `C/logs/` | track C's gamma sweeps stopped to free CPUs: 10 of 16 gammas finished for the AD5 prefix and 11 of 16 for the AD4 prefix, 0 hits in each |
| 11-15 00:10-06:45 | `~/xs-campaigns/2026-11-15-study/`, d961083 (06:10) | study phase (section below): structure and algebra (H1-H4), window redesigns (R1, R2), goal-directed runs (T1-T4), new moves, a goal scheduler and a red team (X1-X3), log analysis and this page's corrections (L1, L2). Agents X1b, X3b and L1b took over X1, X3 and L1 at about 03:00-03:05 UTC |
| 11-15 01:44-03:19 (commits) | `boolflux-review5`, merged in 924b4c0 (06:44) | review 5 of the kernel (C1), the Python package (C2, finished by C23) and the hub (C3, finished by C23): `review5/KERNEL.md`, `PYTHON.md`, `HUB.md`, `X2-COMPAT.md` |
| 11-15 03:19 | `strategies/X1/NOTES.md` section 8 | first circuit with the new 9 + 5 + 14 AND structure (X1b walk from NIST a28-ad5-g128-gd20, 28/5/158/27) |
| 11-15 06:47 | `launch-0700.sh`, `launch-0700.out` | overnight queue launched on all 20 CPUs (section below) |
| 11-15 06:53-07:13 | `curated_utc` 06:53, cb8fd56 (07:13) | re-curation: 56 new entries, MANIFEST.json 194 entries, all verified; `verify_all.py` (06:57) 186 distinct AES tuples of ours, 139 not dominated by the pin, 73 Pareto among ours; [results/BEST.md](results/BEST.md) is the curated table |

## Building blocks (2026-11-13)

**The gate kernel** ([kernel/bfx.c](kernel/bfx.c)) took over XORFlux's working ideas: one chain
that never leaves the space of correct circuits, a remove-and-repair main move, neutral plateau
moves, and restarts from the best. Its core is new. Every signal carries its complete truth
table. A move picks a gate, computes its exact care set, and searches for 0 to 3 new library
gates over the signals outside its fanout cone that equal it there
([HOW-IT-WORKS.md](HOW-IT-WORKS.md)). The library is any set of two-input functions, given by
their 4-bit truth tables.

**The skeleton level** ([kernel/skel.c](kernel/skel.c)) represents the function as K products
of affine forms. It changes several ANDs together, which one-gate moves cannot do. The
GF(2^4) multiplier is the sanity case that needs it: the gate level alone went from 16 to 14
ANDs, while the merge move reached 9, the bilinear complexity ([LEDGER.md](LEDGER.md) section 1:
34 gates/16 AND -> 32/9 in 82 s).

**Models and counting** ([models/](models/)): `nist` (AND, XOR, XNOR, NOT, each 1, NIST's
accounting), `bgc`, `gc6`, `gc`, `xag`, `xor`. The convention that a NOT is written `XNOR t a 0`
and counted as one gate and one level dates from 3b9e0fd. The NIST-format copies with explicit
NOT gates came with e5bab59.

**First results, against pin e6ac0d0** ([LEDGER.md](LEDGER.md)):

- sanity cases: majority 4 gates/1 AND, full adder 5/1 (both minimum sizes), GF(2^4)
  multiplication 9 AND, GF(2^4) inversion 5 AND **[V]**;
- 23 small S-boxes from naive starts. Each equals the best published BGC or GC value, except
  Midori Sb1 BGC, which is one gate worse. None beats a published value. They are optimal
  where the published value is SAT-proved (Piccolo, PRIDE, RECTANGLE GC) **[V]**;
- AES: Boyar-Peralta's 113 improved to 108, and naive ANF 1247 to 717. NIST circuits dominate
  both. 12 tuples were new on the e6ac0d0 set, with the fewest gates at GD <= 13, 14, 18, 19:
  131, 124, 110, 108 against published 133, 127, 116, 116 **[V]**.

What happened to those 12 at pin 3d80774 (MANIFEST.json, `pinned_set`): NIST's new
a34-ad4-g139-gd13 equals our 34/4/139/13, so that tuple is no longer new. Five more (131@13 A36,
124@14 A38, 167@14 AD3, 126@15 A32, 131@26 A28) are now strictly dominated by later results of
ours. The other six were still on the Pareto front at the 17:54 curation: 33/4/110/18, 32/4/122/18,
33/4/108/19, 32/5/108/20, 28/4/133/20 and 35/3/144/20. (Re-curated 2026-11-15.) Three of them
remain: 33/4/110/18, 33/4/108/19 and 32/5/108/20. The hub's 32/4/121/17 and 32/4/119/18 dominate
32/4/122/18, T1's 28/4/132/20 and R1's 28/4/133/19 dominate 28/4/133/20, and T3's 35/3/142/19 and
35/3/143/18 dominate 35/3/144/20.

## Reviews and their fixes

| review | date | main findings | fix |
|---|---|---|---|
| [review/REVIEW.md](review/REVIEW.md) (kernels, about 1,700 randomized runs, sanitizers, 89 NIST circuits) | 11-13 | **M1** the cap penalty was not lexicographic, so a feasible best could be replaced by an infeasible one (reproduced with an AND cap). **M2** caps and metrics were checked by one implementation only. **M3** the recorded hash did not pin the binary that ran. No path saved a wrong circuit | 0640d28: feasibility-first acceptance in the kernel; the independent verifier checks caps and must agree on every metric; each run snapshots its sources and builds private binaries (`OUT/src`, `OUT/bin`, `code_sha256_12`) |
| [review2/REVIEW2.md](review2/REVIEW2.md) (commits 3a71f0f..ccb323f, benchmark fairness, MECHANICS.md) | 11-13 | **C1** the peak-RSS column compared XORFlux's whole process with BoolFlux's C kernel alone. **M1** repair progress was discarded between rounds of the full configuration. **M2** medians were taken over successful runs only. **M3** the skeleton slice did nothing on AES starts. Exact linear mode, seeded rebuild (1,694 cases) and incremental Paar (5,082 cases) were found correct. Deterministic replay works only with `skip_noop 0` | 154ded8: driver memory measured, progress kept, counts shown, round-matched adaptive share (v3), MECHANICS/REPRODUCE corrected |
| [review3/REVIEW3.md](review3/REVIEW3.md) (objectives, incumbents, selection, cleanup, BUF, timing, logs, numbers) | 11-14 | 6 major, 12 minor. **M1** `run` lost the third objective key when ranking jobs. **M2** `pipe` crashed on, or discarded, the repair of a start outside its caps. **M3** rebuild-stage gains were missing from trajectories. **M4** `skip_noop` missed 81-87 % of no-ops (it compared gate lists that `rebuild` renumbers). **M5** BUF lines made correct circuits fail verification. **M6** report and ledger sentences disagreed with the data. No saved circuit was wrong | 0659eb9 and 8225691: one ranking (`objective.py`: feasible, cap excess, path excess, keys in order) in the kernel (`lex`), cli, workflow and analysis; `pipe` keeps repair progress; `workflow.py` shared by bench and `cli.py flow`; structural no-op test; BUF dropped from compared counts; `tests/test_review3.py` |

The [independent audit](audit/AUDIT.md) of 2026-11-13 used its own evaluator and counter. It
found the chi3 bit-order error (those circuits are in `results/_superseded/`) and wrong header
tallies. Re-run on the final set (`audit/run-final.log`), it found no disagreements.

## Method-and-performance study (2026-11-13, [bench/REPORT.md](bench/REPORT.md))

Four benchmark rounds v1-v4 (1,056 runs, matched pinned CPUs; [CHECKPOINT.md](CHECKPOINT.md)), a
repeated no-op A/B v5, ablations, an external comparison with Berkeley ABC, and profiling.
What it established:

- On AES from a naive start, the mechanism that paid was global XOR-layer resynthesis from the
  AND skeleton (Paar): median 633 gates in 300 s, against 749 for local search alone and 739
  with skeleton moves added.
- **Rebuild penalty.** Rebuilding the circuit from the skeleton's forms cost 31-72 gates even
  when the skeleton was unchanged. The seeded rebuild (seeded with the parent circuit) made that
  case exact (+0). After 1-4 skeleton moves it still costs +2 to +40 gates.
- **The skeleton level does not help on good AES circuits.** Its output was the input skeleton
  in 11 of 12 AES cases. No skeleton move lowers `K + 0.02 E` there. On good AES circuits the
  gate search found 1-3 gates in 120 s.
- **No-op filter.** In a traced AES run, 38,099 of 43,958 accepted moves were renumbered no-ops,
  and only 579 changed AND structure. Filtering them had no measurable effect (v5: median 133 in
  both arms, sign test p = 1). The filter stays on because it removes wasted evaluations.
- XOR-only BoolFlux in exact linear mode is competitive with XORFlux v8 on 16-input linear maps
  and behind on two uncapped cases. ABC, a standard logic-synthesis flow, was worse on every
  target in these gate-count models (AES from NIST's 104: ABC 110, BoolFlux 104).
- Depth repair is slow: 116@GD15 -> GD 14 succeeded in 2 of 35 runs of 120 s (129 and 124
  gates). The 124@GD14 A38 run was a time-budgeted one-off.

## The AES push (2026-11-14)

Goal of the push: a significant, independently verified AES S-box result, such as G < 103,
A < 28, about 110 gates at GD <= 14, or a comparable frontier gain. Four
strategy tracks ran, each with its own CPUs, code in `strategies/<track>/` and outputs in
`~/xs-campaigns/2026-11-13-aes/<track>/`. All checking went through `campaigns/aes_check.py`.

### Track C: fewer than 28 ANDs (exact and algebraic; `strategies/C/NOTES.md`, C/STATUS.md)

No circuit below 28 ANDs. Proved or computed facts about the structure of the published A28
circuits (10|1|2|2|13 and 9|2|4|13 ANDs per level):

- The norm N = x^17 in one AND level needs exactly 9 ANDs **[C]**. k = 7 and k = 8 are
  exhaustively impossible (cover lemma, orbit reduction; the k = 8 case took 6,780 s on one CPU).
  An earlier "k = 7 UNSAT" was retracted, because it fixed a basis of the target space, which is
  unsound.
- The GF(16) inversion needs exactly 5 ANDs **[C]** (SAT: k = 4 UNSAT in 76 s).
- Every last-layer AND of the two A28 circuits examined (a28-ad5-g124 and a28-ad4-g131-gd31; the
  pin has 14 A28 files) is a GF(4) norm. No 9-product stage 1 fits the published last layer or
  any of the 2,321 valid 13-member layers of its family **[C]**. No 12-member GF(4)-norm last
  layer exists over the three fixed front spans tested, **for one gamma per front and in the
  cases dim Z = rank = 4 and dim Z = 3 [C]** (corrected 2026-11-15; `strategies/C/NOTES.md`
  section 9 lists what is not covered: dim Z = 2, other gammas, members with an independent
  N-part, non-GF(4)-norm members, other stage-1 covers). That excludes 27 (and 26) only in those
  cases of that family, and says nothing about circuits outside the three-stage model. The gamma
  sweeps that were still running were stopped at about 23:55 UTC: 10 of 16 gammas done for the
  AD5 prefix and 11 of 16 for the AD4 prefix, each with 0 hits (`C/logs/zdfs_r4_k12_*.json`);
  the rest are queued. H1 continues this line (`strategies/H1/`).

### Track D: exact SAT resynthesis of windows (`strategies/D/README.md`, D/STATUS.md)

A failed experiment, for its objective: fewer gates at fixed caps. At the frontier caps,
**0 of 3,062 recorded windows** improved anything (corrected 2026-11-15 from "about 3,900";
the surviving logs `D/t1`, `t3`, `t4` hold 3,062 windows and 3,337 SAT calls, 72 % UNSAT and
28 % over the 30k-conflict budget). The windows had 4-9 gates (5-12 in one cut-mode run) on
published 116, 124 (A28), 127, 133 and, for 180 of them before the outage, on our 108@19,
124@14, 131@13. No log exists for NIST 103. In depth mode (GD - 1), 0 of 115 improved; those
four runs were cut by the outage after 64 of 400 s. The encoding asked for one gate fewer, or
for the same number of gates with one AND fewer. It never asked for one AND fewer at a free
gate count, so it is not a test of AND removal. With the depth cap relaxed by one, windows occasionally found a -1, and
the kernel repair back to the cap undid it every time. In the final fair test (breathe cycles
against the kernel alone, about 1,100 s each, CPUs 11-13), the two gains came from the kernel
stage, after the window stage had returned its input unchanged. They are kernel seed variance,
not window effects. Conclusion (corrected 2026-11-15): no sampled window of that size could be
replaced by a smaller one, and 28 % of the SAT calls were undecided. The windows were drawn at
random, not enumerated, so this is not a proof of local optimality. Products: 121@GD14 A37
(from our 124, 269 s) and 125@14 A33, both kernel results
**[V for 121; 125@14 A33 is equalled by NIST's new a33-ad4-g125-gd14, so it is not new]**.

### Track E: joint AND/XOR optimisation (`strategies/E/NOTES.md`, E/STATUS.md)

- **M1, ejection chains**: an uphill kick at a gate, then up to 6 greedy repair steps. Negative:
  median 135 against 133 for the control (a36, 60 s, 5 seeds); no gain from A28 124 at cap A 30/31
  (one seed, 300 s per arm). On 104 at cap A31 only the control finished; the chain run and the
  A29 batch were lost in the outage. The objective was gate count throughout: chains were never
  run with an AND-first objective.
- **M2, skeleton kicks**: one AND-product move, seeded rebuild, short polish. Negative: single
  moves cost +12 to +42 gates (A28 124) or +0 to +19 (104), and 20 s polishes never got back to
  the parent.
- **M3b, joins (stage transplants)**: the front of one circuit plus the back of another, with
  the interface rebuilt as affine combinations of the front's signals. Positive. The sp1 sweep
  over 150 circuits (104,230 attempts, about 50 s per shard on 4 CPUs) gave 20 new Pareto
  points. Among them was the first **A31** point (31/5/119/20); every published circuit with
  A <= 31 has G >= 124.
- **Final A/B** (stopped 17:28, `E/ab_final.json`): the splice arm (join + polish) made
  41 admissions and 17 frontier points in 4.7 CPU-h. The polish-only control made 4 and 3. 15 of
  the splice arm's points are not dominated by any control point, and 0 of the control's are not
  dominated by the splice arm. The low1 run (joins, polishes and depth pulls aimed at A <= 31)
  added A28 and A29 points at GD 16-25 and 33/4/115/15 **[V]**.
- **Reading of that A/B** (added 2026-11-15, `strategies/L2/WHAT-WORKED-BEFORE.md`): all 26 join
  admissions came in the first 8.6 minutes of 2.3 hours, and 14 of the 17 points are those joins
  or polishes of them. Polishing published A28 circuits at their own caps changed nothing in 52
  jobs. On the A28 line the gains came from depth pulls (cap GD lowered by 1-3, AD free; 7
  admitted points from 53 jobs) and from polishing what the pulls made. The A29 points are A28
  circuits whose pull ended one AND above its cap, with a 10-AND last layer (ANDs per level
  10, 2, 3, 4, 10). 32/5/104/29 came from a 240 s kernel job from NIST 107@GD22 whose cap A31
  was never met; a paired probe on 2026-11-15 showed that the released depth cap, not the unmet
  A cap, is what produced the gain.

### Track F: low gate depth (`strategies/F/NOTES.md`, F/STATUS.md)

- **Facts.** For each of the six circuits analysed (116@15, 127@14, 124@14, 131@13, 133@13,
  141@12), the depth reached by rebuilding every XOR form optimally equals the circuit's GD. So a cap repair cannot come from XOR-layer resynthesis alone: some
  AND functions must change. Over {AND, XOR, XNOR, NOT}, y2 and y3 of the GF(2^4) inversion are
  not depth-3 computable from its 4 inputs alone (exhaustive).
- **Failed**: AND distribution transforms (no single transform lowers the depth bound below 15;
  a beam of 8 lowers the Kraft excess but not the bound); union-graph area-flow mapping
  (169-176-gate covers); direct splices (130@15, 127@14).
- **Gains**: 122@GD14 A37 by the plain gate kernel from our 124 (4 of 4 seeds, 25-123 s); an
  independent, constructive 122 from a depth-3 inversion block spliced into NIST's 116; and
  **121@GD14 A37** from the timing-driven regional rebuild arm (`trb`, 1 of 3 one-hour runs, at
  1,407 s; 0 of 10 for the other arms; with n = 3 per arm this is not significant) **[V]**. It is a different circuit from track D's 121.
- **Repair baseline**: GD14 -> 13 met the cap in 2 of 35 runs (137 and 136 gates), and GD13 -> 12
  in 0 of 10. Repair is fast exactly when the start's depth bound already meets the cap.
- After 17:31, AD3 runs found 161@GD14 A38 AD3 and 174@GD13 A40 AD3 (curated 17:40, both new
  points at the time). (Re-curated 2026-11-15.) The runs ended at 22:50 UTC with further AD3
  points (timeline). 35/3/177/13 and 35/3/162/14 are in the manifest now. 38/3/161/14 is
  dominated by the hub's 36/3/161/14 and 40/3/174/13 by R2's 39/3/172/13.

### Main queue (`~/xs-campaigns/2026-11-13-aes/main/`)

Gate-kernel convergence runs (`cli.py flow --config gate`, 900 s x 4 seeds) under each start's
own caps. 10 of 28 starts were done when it stopped at 17:26. One gain: NIST a28-ad4-g176-gd14 ->
**175@GD14 A28** (seed 4 of 4) **[V]**. Nine starts were unchanged, among them 116@15, 106@22,
103@32 and 124@27 (`main/queue.log`).

### Where the AES results stand (pin 3d80774)

(Re-curated 2026-11-15.) This section is the curation of 2026-11-15 06:53 UTC (commit cb8fd56):
the AES push, the hub runs, track F's last AD3 runs and the study phase.

**73 tuples** are new on the pinned set and not dominated by another result of ours. The same 73
come from MANIFEST.json (`aes_pareto`) and `verify_all.py` (2026-11-15 06:57 UTC);
[results/BEST.md](results/BEST.md) has 73 rows, one of them stale (29/4/130/22 instead of
29/4/129/22, [DOCS-TODO.md](DOCS-TODO.md) item 27). 79 manifest entries carry them (some tuples
have two circuits). By maker of the entries: the hub 36 (join 14, pull 13, osc 3, polish 3, trb 2,
gen_skel 1), study agents 18 (T4 6, R1 3, T1 3, T3 2, X2 2, L1 1, R2 1), track E 17, track F 3,
`cli.py` runs of 2026-11-13 3, track D 1, main queue 1.

Against the curation of 2026-11-14 17:54 UTC, which had 41 tuples: 22 of the 41 remain, 19 are now
dominated by later results of ours, and 51 tuples are new. Of the 51, 36 have a hub circuit (2 of
them also a track F circuit, 35/3/177/13 and 35/3/162/14, and 1 also an R1 circuit, 28/5/136/17)
and 15 come from study agents only (T4 6, T3 2, X2 2, R1 1, R2 1, T1 1, and 28/5/126/24 from R1
and T1, 28/4/131/22 from T1 and L1). Fewest gates at a gate-depth cap, A and AD free
(results/BEST.md):

| GD <= | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 20 | 21 | 29 |
|---|---|---|---|---|---|---|---|---|---|---|
| published best G | 133 | 125 | 116 | 116 | 116 | 116 | 116 | 108 | 108 | 105 |
| ours | **129** (A36) | **121** (A37) | **115** (A33) | **112** (A33) | **112** (A33) | **110** (A33) | **108** (A33) | **107** (A33) | **107** (A33) | **104** (A32) |

Against the 17:54 table, GD 16 went from 113 to 112 (the hub's join 33/4/112/16) and 107@20 (the
hub's pull 33/4/107/20) replaced 107@21. NIST's targets were not reached: A < 28, G < 103 (the
record is 103 at GD 32), and about 110 at GD <= 14.

Reproduction (MANIFEST.json `reproducibility`): of the 79 entries, 72 are one-off time-budgeted
jobs, among them every hub and study result and every A28 and A29 point, and none was repeated.
4 are deterministic joins of track E; on 2026-11-15 the 30 recorded joins of track E were rebuilt
from their parents and cut levels, all identical (`strategies/L2/rejoin.py`). 3 are deterministic
`cli.py` commands of 2026-11-13. Seven manifest entries are circuits that do not meet the caps of
the job that made them (`caps_met: false`, review 5 P22), and six of them are on the front:
32/5/104/29 (cap A31), and the hub pulls 32/5/115/17 (cap A31), 30/4/130/20 (cap A29),
29/4/132/19 (cap AD3), 35/3/141/24 (cap A34) and 29/4/146/15 (cap A28). The seventh,
29/5/135/17 (cap A28), is now dominated.

None of the mechanisms lowered an AND count below its family's published minimum, and none was
asked to: before the hub no kernel, window or chain run on AES had an AND-first objective or an
A cap below its start's A, apart from eight 240 s runs with cap A31 from A32 circuits
(`strategies/L2/WHAT-WORKED-BEFORE.md` sections 0 and 3). The study phase asked for fewer ANDs
directly (goal A, 27 ANDs) and found no circuit below 28. At gate depth 11 its circuits have 42-47
ANDs, where no published circuit with A <= 48 has GD <= 11 (`strategies/T4/NOTES.md`).

## Decisions and their evidence

| decision | evidence |
|---|---|
| complete truth tables and exact care sets, never an approximate state | no review or audit found a saved circuit that computes the wrong function (reviews 1-3, audit) |
| feasibility first, then lexicographic keys, the same ranking everywhere | review 1 M1, review 3 M1/M2 |
| seeded rebuild instead of rebuilding from forms | 31-72-gate penalty -> +0 (REPORT section 3) |
| skeleton moves kept only for AND reduction (small functions) | GF(2^4) mult 9 AND needs them; 11 of 12 AES cases unchanged; track E M2 negative. Not tested: a search for one product fewer on an A28 skeleton |
| no gate-saving SAT windows in the main loop | 0 of 3,062 recorded windows (track D). AND-removing windows are a different design, under test since 2026-11-15 (H3, R1) |
| joins at interface functions as a first-class operator (hub) | track E A/B: 17 vs 3 frontier points in the same CPU time, the join admissions all in the first 9 minutes. In the hub, repeat joins on the same target gave 3 frontier admissions in 3,471 jobs (`strategies/L1/WHAT-WORKS.md` finding 8) |
| A/B arms need at least 8 CPU-hours and a value measure that is not the hub's gain | twenty identical 1-CPU-hour blocks gave 0, 1, 2, 4 frontier admissions in 11, 5, 3, 1 blocks; the gain rule scored 51 of 75 admissions as "lowers A" although none lowered a class minimum (`strategies/L1/WHAT-WORKS.md` findings 1, 10) |
| every result through two verifiers, then `aes_check` against a pinned set | the 0876577 -> e6ac0d0 correction withdrew 13 of 18 claimed points |
| memory guard for every campaign job | the 05:09 OOM outage |

## The hub (2026-11-14 evening)

[hub/SPEC.md](hub/SPEC.md) describes a shared archive that every operator reads and writes, with
cells per (A, AD, GD) and a bandit scheduler (`hub/`, campaign `~/xs-campaigns/2026-11-14-hub/`).
It was built from 17:30 UTC and ran until 01:30 UTC on 11-15. Its circuits are verified at
admission and listed in `~/xs-campaigns/2026-11-14-hub/best/BEST.md`. (Re-curated 2026-11-15.)
Since the curation of 2026-11-15 06:53 UTC they are in MANIFEST.json too: 36 entries with track
`hub` (21 from the `long` archive, the rest from the A/B arms), all on the Pareto front, each a
one-off job with the hub's run-time code version. Track E's running notes are
`strategies/E/NOTES.md`; the recount of all hub logs is `strategies/L1/WHAT-WORKS.md`. From the
recount, all counted over 65.9 CPU-h and 7,231 jobs:

- 80 frontier admissions, every one "fewer gates under the same caps". None lowered the smallest
  A, the smallest AD at an A, or the smallest GD of a class. No goal box (B-G) was met.
- The mature best circuits are fixed points of the kernel: 138 polish jobs on seed circuits,
  none with lower G.
- The new 29/4 and 30/4 families were first made by pull jobs that ended infeasible.
- The scheduler's gain is not a value signal, and the one-CPU-hour A/B arms that chose the
  operators (osc, gen_skel, ad3_share) differ by counts of 1 against 2. Those choices are not
  established. osc: 347 jobs, 9.5 CPU-h, 4 frontier admissions.
- Earlier text in `strategies/E/NOTES.md` that ranks operators by "gain per CPU-h" should be
  read with this in mind.

## The study phase (2026-11-15, 00:10-06:45 UTC)

Fifteen agents worked from `~/xs-campaigns/2026-11-15-study/` (briefs `BRIEF-COMMON.md` and
`BRIEF-ADDENDUM-0135.md`), each with its code and `NOTES.md` in `strategies/<agent>/`, committed in
d961083. The goals were boxes in (A, AD, G, GD): A = at most 27 ANDs; B = 28/4/<=130/<=22;
C = 28/5/<=127/<=19; D = <=32/4/<=116/<=19; E = <=32/<=6/<=102/<=31; F = <=35/3/<=138/<=26;
G = <=44/<=4/<=140/<=11 (`strategies/T1-T4/NOTES.md`). **No goal box was met.** The notes use
[C] for exact or exhaustive within the stated case only, [P] for proved, [H] for heuristic or
measured, [V] for a verified circuit.

| agent | what | result | source |
|---|---|---|---|
| H1 | structure of the known low-AND circuits | they share one three-stage skeleton (stage 1, inversion, last layer) [C on 63 files]. The only general lower bound is 13 ANDs [P]; every earlier exact result of ours is listed with what it does not exclude. In 25 built 9 + 5 + 14 circuits (prefix fixed) the last layer cannot go from 14 to 13 by one drop or by replacing two or three members with one fewer [C, that case] | `H1/NOTES.md` sections 1, 4, 4.1, 9 |
| H2 | algebraic constructions, exact layer search (`gen13`) | the new AND structure 9 + 5 + 14: 69 covering 14-member last layers over the stage-1 span of NIST a28-ad4-g131, 69 each over g141 and g176; no 13-member layer over umizame's or ten published 9-product spans, no 12-member layer over the AD5 spans [C, member model, BMP middle, one gamma, stage 1 fixed] | `H2/NOTES.md` sections 5.6, 5.8, 6 |
| H3 | exact window re-solve around known circuits | a 29 -> 28 reduction (28/5/210/31, a re-bracketing of the AND space of NIST a28-ad5-g128); no single AND replaces the dependent pair of either 9 + 5 + 14 circuit tested (2^33 operands each) [C, kept ANDs fixed] | `H3/NOTES.md` R7, R8, scope notes |
| H4 | other representations of GF(2^8) inversion | a change of representation cannot change an AND count [P]; the non-tower constructions tried need 41-108 ANDs; the AD3 frontier is the GF(4)-norm route; 34 ANDs at AD3 not found [H overall] | `H4/NOTES.md` summary |
| R1 | SAT window resynthesis (`wres`), window AND removal (`mc1`, `seq2`) | `wres`: 0 of 1,107 hub windows improved. AND removal plus kernel grind: 28/4/133/19, 28/5/126/24, 28/5/136/17 [V] | `R1/NOTES.md` summary |
| R2 | affine-slack window redesign (`aslack`) | A reductions on redundant circuits (39/3/172/13 from 40/3/172/13 [V]); 0 of 39 fixed-target jobs near the A28-A35 fronts improved; no level-1 A reduction in 8 front circuits [C, window model] | `R2/NOTES.md` conclusion |
| T1 | goals B and C | not met; 28/4/131/22 and 28/4/132/20 [V], from GD pulls, long deep runs and joins | `T1/NOTES.md` section 5 |
| T2 | goals D and E | not met; nothing better than the starting points (about 70 kernel jobs for E, 21 walk jobs and 49 front-deadline jobs for D, 388k joins) [H] | `T2/NOTES.md` summary, final numbers |
| T3 | goal F (AD3) | not met; GF(4)-coordinate moves at level 3 and level-1 product exchanges gave 35/3/142/19 and 35/3/143/18 [V] | `T3/NOTES.md` sections 11, 15, 16 |
| T4 | goal G | A <= 44, AD 4, GD 11 met, G <= 140 not: 47/4/186/11, 46/4/203/11, 44/4/254/11, 43/4/278/11, 42/4/284/11 and 42/4/230/12 [V] | `T4/NOTES.md` |
| X1, X1b | AND merge / split / flip moves on the product program | Boyar-Peralta's 32 to 29 ANDs in 0.2 s (large G); the first 9 + 5 + 14 circuit (28/5/158/27, lowest of the family 28/5/156/28) [V]; no 27 and no A29 -> 28 in 97 walk runs [H] | `X1/NOTES.md` sections 5, 8 |
| X2 | goal-directed hub scheduler | in a 4-arm ABBA A/B of 0.9 CPU-h per arm no difference from the generic scheduler; new points 30/4/129/21 and 29/4/128/23 [V] | `X2/NOTES.md` A/B result |
| X3, X3b | red team for 27 ANDs | the degree bound is tight for inversion in GF(8) and GF(16) and fails by at least 2 in GF(32); no optimal GF(16) inversion circuit is three-stage; a parallel top layer with operands affine in x plus functions of N needs >= 10 products [C]; the critique of over-claims below | `X3/NOTES.md` sections 0, 8, 10 |
| L1, L1b | hub-era log analysis; the overnight queue review | `WHAT-WORKS.md` (findings 1-10), `TONIGHT.md`, `QUEUE-REVIEW.md` | `L1/NOTES.md` |
| L2 | pre-hub log analysis; documentation audit | `WHAT-WORKED-BEFORE.md`, `DOC-AUDIT.md`; the corrections marked on this page | `L2/NOTES.md` |

The 9 + 5 + 14 structure has 9 stage-1 ANDs, a 5-AND inversion and 14 last-layer ANDs. The
published A28 families are 10 + 5 + 13 (AD5) and 9 + 6 + 13 (AD4). Its circuits so far have
G >= 156, so none is on the frontier.

**Review 5** ran alongside, on the branch `boolflux-review5` (merged in 924b4c0):

- C1, the gate kernel (`review5/KERNEL.md`): bugs K1-K4 fixed or behind an option; speed changes
  P1-P3 with the same trajectories, about 15-20 % less CPU per iteration [H, noisy CPU]; new
  options (`xspan`, `repair_keep`, `nl_root`) off by default, and the default search is
  bit-identical to f9fe6f7 for fixed seeds and iteration counts.
- C2, finished by C23, the Python package (`review5/PYTHON.md`, P1-P26): among them curation with
  hub archives (P12), `cli.py verify` with an explicit NOT (P19), reproducibility records and
  `manifest.py --check-repro` (P21, P24), `caps_met` (P22), `code_version_commit_check` against
  377b03f (P23), atomic kernel builds and collision-free kernel seeds (P25, P26).
- C3, finished by C23, the hub (`review5/HUB.md`, `review5/X2-COMPAT.md`): a value-correct gain,
  targets by tuple with caps, incremental joins over all cell members, an A cap for osc,
  clean-up before admission (H21), and the compatibility of X2's goal scheduler with this code.

**Corrections the study phase made to earlier readings:**

- **Restricted exhaustive results are not general bounds.** Every "no 27" or UNSAT result of
  tracks C and G and of H1-H3 holds for a fixed stage-1 span or prefix, a fixed pool of
  last-layer products (the 1,275 GF(4)-norm members, sometimes the 107,100 semi-members), a 5-AND
  middle and one gamma. They say nothing about circuits outside that case. That every 28 found is
  three-stage is no evidence either, because every generator used preserves the three stages
  (`H1/NOTES.md` sections 4.1 and 7.0, `X3/NOTES.md` section 8, `H3/NOTES.md` scope notes).
- **The hub's gain was not a value signal.** Its rule scored 51 of the 75 hub-made front
  admissions as "lowers A", although none lowered the smallest A of a class
  (`strategies/L1/WHAT-WORKS.md` finding 1).
- **One-CPU-hour A/Bs cannot separate configurations.** Twenty identical 1-CPU 1-hour blocks gave
  0, 1, 2 and 4 front admissions in 11, 5, 3 and 1 blocks (`strategies/L1/WHAT-WORKS.md`
  finding 10). X2's A/B of 0.9 CPU-h arms shows the same (`X2/NOTES.md`).

**Overnight queue.** Launched at 06:47 UTC by `~/xs-campaigns/2026-11-15-study/launch-0700.sh`
(log `launch-0700.out`) on all 20 CPUs, with no agents running. The allocation and the launch
fixes are from `strategies/L1/QUEUE-REVIEW.md` sections 1-3: every job runs under
`timeout 705m` (11 h 45 min), except the uncapped H3 window `g124w8` (47 h limit), and the heavy
families are spread over track slices with their own memory caps. CPUs: 0-1 H3 windows of the
9 + 5 + 14 circuits, 2 H3 `g124w8`, 3-4 H2 layer search over H4 and Karatsuba covers, 5-6 X3b,
7 H1 14 -> 13 tests, 8-9 X1b walks, 10-12 T1 (goal B), 13-14 R1, 15-17 the hub (`long5`, review-5
code), 18 T4, 19 T3 (AD3 low-GD band). Its results are not on this page or in the manifest;
`QUEUE-REVIEW.md` section 4 lists what has to be checked by hand afterwards.
