# How BoolFlux got here

BoolFlux was built on 2026-11-13 and 2026-11-14 on the local branch `boolflux-2026-11-13`. Nothing
has been published or pushed. This page is a dated record of that work: what was built, what
the reviews found and how it was fixed, which measurements changed the method, and what the
2026-11-14 AES push produced, failed experiments included. Times are UTC. Commit times are
converted from the repository's -0500 timestamps.

**Sources and marks.** The commit hashes come from
`git log --format='%h %ci %s' boolflux-2026-11-13`. Other sources are named next to each claim.
Campaign records live outside the repository, in `~/xs-campaigns/2026-11-13-boolflux/` and
`~/xs-campaigns/2026-11-13-aes/` ([runs/INDEX.md](runs/INDEX.md)). The strategy code of the AES
push (`strategies/C,D,E,F/`) and the hub (`hub/`) had not been committed when this page was
written. **[V]** marks a circuit that passed both verifiers
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
| 11-14 17:40-17:47 | this documentation pass | 36 AES-push circuits curated into `results/aes/` (`campaigns/curate_aes.py`); MANIFEST.json regenerated; `verify_all.py` run: all OK |

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
ours. The other six are still on the Pareto front: 33/4/110/18, 32/4/122/18, 33/4/108/19,
32/5/108/20, 28/4/133/20 and 35/3/144/20.

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
- Every last-layer AND of the A28 circuits is a GF(4) norm. No 9-product stage 1 fits the
  published last layer or any of the 2,321 valid 13-member layers of its family **[C]**. No
  12-member GF(4)-norm last layer exists over the three fixed front spans tested **[C]**. That
  rules out 27 (and 26) only within that family. Gamma sweeps were still running.

### Track D: exact SAT resynthesis of windows (`strategies/D/README.md`, D/STATUS.md)

A failed experiment. At the frontier caps, **0 of about 3,900 windows** improved anything:
windows of up to 9-12 gates on published 103, 116, 124 (A28), 127, 133 and our 108@19, 124@14,
131@13. About 60 % were UNSAT and 40 % ran over a 30k-conflict budget. In depth mode (GD - 1),
0 of about 115 improved. With the depth cap relaxed by one, windows occasionally found a -1, and
the kernel repair back to the cap undid it every time. In the final fair test (breathe cycles
against the kernel alone, about 1,100 s each, CPUs 11-13), the two gains came from the kernel
stage, after the window stage had returned its input unchanged. They are kernel seed variance,
not window effects. Conclusion: these circuits are locally exact-optimal for windows of that
size. Products: 121@GD14 A37 (from our 124, 269 s) and 125@14 A33, both kernel results
**[V for 121; 125@14 A33 is now dominated by NIST's new a33-ad4-g125-gd14]**.

### Track E: joint AND/XOR optimisation (`strategies/E/NOTES.md`, E/STATUS.md)

- **M1, ejection chains**: an uphill kick at a gate, then up to 6 greedy repair steps. Negative:
  median 135 against 133 for the control (a36, 60 s, 5 seeds); no gain from A28 124 at cap A 30/31
  or from 104 at cap A31.
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

### Track F: low gate depth (`strategies/F/NOTES.md`, F/STATUS.md)

- **Facts.** For every frontier circuit, the depth reached by rebuilding every XOR form optimally
  equals the circuit's GD. So a cap repair cannot come from XOR-layer resynthesis alone: some
  AND functions must change. Over {AND, XOR, XNOR, NOT}, y2 and y3 of the GF(2^4) inversion are
  not depth-3 computable from its 4 inputs alone (exhaustive).
- **Failed**: AND distribution transforms (no single transform lowers the depth bound below 15;
  a beam of 8 lowers the Kraft excess but not the bound); union-graph area-flow mapping
  (169-176-gate covers); direct splices (130@15, 127@14).
- **Gains**: 122@GD14 A37 by the plain gate kernel from our 124 (4 of 4 seeds, 25-123 s); an
  independent, constructive 122 from a depth-3 inversion block spliced into NIST's 116; and
  **121@GD14 A37** from the timing-driven regional rebuild arm (`trb`, 1 of 3 one-hour runs, at
  1,407 s; 0 of 9 for the other arms) **[V]**. It is a different circuit from track D's 121.
- **Repair baseline**: GD14 -> 13 met the cap in 2 of 35 runs (137 and 136 gates), and GD13 -> 12
  in 0 of 10. Repair is fast exactly when the start's depth bound already meets the cap.
- After 17:31, AD3 runs found 161@GD14 A38 AD3 and 174@GD13 A40 AD3 (curated 17:40, both new
  points; the runs were still going).

### Main queue (`~/xs-campaigns/2026-11-13-aes/main/`)

Gate-kernel convergence runs (`cli.py flow --config gate`, 900 s x 4 seeds) under each start's
own caps. 10 of 28 starts were done when it stopped at 17:26. One gain: NIST a28-ad4-g176-gd14 ->
**175@GD14 A28** (seed 4 of 4) **[V]**. Nine starts were unchanged, among them 116@15, 106@22,
103@32 and 124@27 (`main/queue.log`).

### Where the AES results stand (pin 3d80774)

41 tuples are new on the pinned set and not dominated by another result of ours. The same 41
come from `best_table.py`, `pareto_audit.py`, MANIFEST.json and `verify_all.py`. By mechanism:
20 kernel polishes (11 of them have a join in their lineage), 7 joins, 4 depth pulls, 6 earlier
`cli.py run` results, 3 track F trb results, 1 track D kernel result and 1 main-queue result
(two circuits share 121@14). Fewest gates at a gate-depth cap, A and AD free:

| GD <= | 13 | 14 | 15 | 16 | 17 | 18 | 19 | 21 | 29 |
|---|---|---|---|---|---|---|---|---|---|
| published best G | 133 | 125 | 116 | 116 | 116 | 116 | 116 | 108 | 105 |
| ours | **129** (A36) | **121** (A37) | **115** (A33) | **113** (A33) | **112** (A33) | **110** (A33) | **108** (A33) | **107** (A33) | **104** (A32) |

Source: `pareto_audit.py` on `results/aes` (2026-11-14 17:43). NIST's targets were not reached:
A < 28, G < 103 (the record is 103 at GD 32), and about 110 at GD <= 14. All of the AES-push
results are one-off time-budgeted runs or deterministic joins. None was re-run
(MANIFEST.json `reproduction`).

## Decisions and their evidence

| decision | evidence |
|---|---|
| complete truth tables and exact care sets, never an approximate state | no review or audit found a saved circuit that computes the wrong function (reviews 1-3, audit) |
| feasibility first, then lexicographic keys, the same ranking everywhere | review 1 M1, review 3 M1/M2 |
| seeded rebuild instead of rebuilding from forms | 31-72-gate penalty -> +0 (REPORT section 3) |
| skeleton moves kept only for AND reduction (small functions) | GF(2^4) mult 9 AND needs them; 11 of 12 AES cases unchanged; track E M2 negative |
| no SAT windows in the main loop | 0 of about 3,900 windows (track D) |
| joins at interface functions as a first-class operator (hub) | track E A/B: 17 vs 3 frontier points in the same CPU time |
| every result through two verifiers, then `aes_check` against a pinned set | the 0876577 -> e6ac0d0 correction withdrew 13 of 18 claimed points |
| memory guard for every campaign job | the 05:09 OOM outage |

## Next: the hub (in progress)

[hub/SPEC.md](hub/SPEC.md) describes a shared archive that every operator (polish, pull, join,
trb, later linres and generators) reads and writes, with cells per (A, AD, GD) and a bandit
scheduler. Its implementation began on 2026-11-14 (`hub/`, campaign `~/xs-campaigns/2026-11-14-hub/`).
It is not described here as a result.
