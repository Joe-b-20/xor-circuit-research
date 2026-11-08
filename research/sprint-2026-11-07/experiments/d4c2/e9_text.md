# Scope C, continued: the open branches rerun as pure core minimisation (first layer = the 89's 26 pairs)

Folder `~/xs-campaigns/2026-11-07-sprint/d4c2/`. 2026-11-08 03:25-06:00 UTC. Continues `d4c/REPORT.md` (scope C) and
`d4bound/REPORT.md` (model, Lemmas 1-5). Repository and `d4c/` read-only. One CP-SAT process at a time, 4 threads,
`nice -n 8`, every run under `timeout 1500` (solver limit 1,400 s); the machine ran other campaigns at load ~8 on
20 cores, so the 4 threads were roughly 4 cores.

Labels as in d4c: **[proved]** argument written here or in the cited report; **[SAT-scoped]** exact CP-SAT bound
over a finite model whose coverage of the stated scope is proved; **[open]** not decided.

---------------------------------------------------------------------------------------------------------

## 0. Verdict

**Scope C is still OPEN overall, but one more sub-scope is now closed, and it covers every level pattern.**

**Closed [SAT-scoped]: no circuit over P89 without a two-helper level-4 recipe has <= 88 gates.** Exact
statement: let `C` be a normal-form depth-<= 4 circuit for one MixColumns column whose set of weight-2 masks is
exactly `P89` (or the image of `P89` under a byte rotation, by `Z4`). If no level-4 gate of `C` has two level-3
non-output operands (helpers), then `C` has at least 89 gates. Proof: split by `m` (number of weight-5 outputs
at level 4) and `j` (number of the six realisable weight-7 outputs at level 3): `m = 0, j = 0` is d4c's B0noR2b
(core bound 31 at 276 s), `m = 0, j >= 1` is BJnoR2 (bound 31 at @@T:BJnoR2@@ s), `m >= 1` is MnoR2 (bound 31 at
@@T:MnoR2@@ s); the three are disjoint and exhaustive, and in each the exact model with valid cuts has minimum
`|L2| + |H3| >= 31`, i.e. `G >= 89` (section 5). The single run over the whole no-two-helper scope (FULLnoR2)
stopped at 30, one core short, which is why it was split. Consequence: **an 88 over P89, if it exists, has at
least one level-4 output that is "helper + helper"**, whatever its level pattern (the 89 has six such outputs).

**Open, with proved bounds [SAT-scoped]** (all pure minimisation, no `ub`):
* B0 (the 89's level pattern, two-helper recipes allowed, every `|L2|`): `|L2| + |H3| >= @@B:B0@@`, i.e. `G >= 84`
  in this branch (d4c: 25); reached at @@T:B0@@ s, nothing more by @@W:B0@@ s. This bound covers K24 / K23 and every
  `|L2| = 17 .. 23` sub-branch of B0 at once.
* BJ (`m = 0`, `j >= 1`, two-helper recipes allowed): `>= @@B:BJ@@`, i.e. `G >= 85` in this branch (first run of
  this family; 27 reached at @@T:BJ@@ s).
* M (`m >= 1`, two-helper recipes allowed): `>= @@MBEST@@` (first runs of this family; this is the weakest
  family and so the weakest point of the whole scope). The 4-worker run grew to 6.4 GB RSS in 257 s with under
  3 GB of the machine left and was interrupted for memory safety at bound @@B:M@@; the 2-worker rerun Mw2 (memory
  watchdog) got 12 at @@T:Mw2@@ s and nothing more by @@W:Mw2@@ s, when it was interrupted to end the session (its
  RSS had also reached 6.45 GB: the memory grows with the learned clauses, not with the worker count). Its model is the largest (139,591 objective literals, 166,337
  recipe variables: weight-5 outputs at level 4 bring their own recipes), the same size as d4c's FULLcore (11 in
  700 s).
* K24 (B0 with `|L2| = 24`, helpers restricted to `N6`, sound): stayed at its propagation bound 30 for 456 s;
  H6 (B0 with `|H3| = 6`, objective `|L2|`, closes at 25): stayed at 16 for 275 s. Both formulations fix a
  cardinality, and in both the solver found no core at all (section 6).

So the theorem "no depth-4 circuit over P89 with <= 88 gates" is **not** proved: the two-helper part of all three
families remains, with the bounds above.

@@FOUND@@

---------------------------------------------------------------------------------------------------------

## 1. Question, model, completeness (unchanged from d4c)

`P89` = the 26 pairs of the recorded 89@4. **Scope C**: normal-form depth-<= 4 circuits of one MixColumns column
whose set of weight-2 masks is exactly `P89`. Such a circuit has `G = 32 + 26 + |L2| + |H3|`, so **"a depth-4
circuit with <= 88 gates over P89" is exactly "`|L2| + |H3| <= 30`"**; the 89 has 22 + 9 = 31. By the byte
rotation `Z4` (the model is equivariant, `d4bound` 5.1, `d4_post.py` (a)) every statement below holds verbatim
for the three rotated pair sets. A raw circuit whose level-1 gates are `P89` normalises (d4bound Lemma 1) to a
circuit with at most as many gates whose weight-2 set is `P89` minus dead pairs plus pairs born at higher
levels; scope C is the normal-form statement, as in d4c section 1.

The model is d4c's `c2_model.py`, copied to `e2_model.py`; the copy changes nothing unless the new options
below are used (diff against the original: only the docstring, the `allowed=` option, the `solve` extensions).
Its completeness argument (d4c section 2) is: every scope-C circuit maps to a feasible point of the same cost,
every feasible point decodes to a circuit (`witness_to_circuit`, checked by `circuits/check.py` and a unit-vector
evaluation; `e5_verify.py` was re-exercised here on d4c's 89-gate smoke witness: `1/1 circuits ok`, file then
deleted from `found/`). Valid cuts used in every run: K1-K3 (Lemma 5, level-2 parents of level-3 outputs and of
helpers), `hmin`: at least 6 helpers among `N6` (the 26,024 masks that can serve one of the six never-level-3
outputs; `Hfree'(never6) = 6`, OPTIMAL, d4c `c6b_hfree.py`), `pc5`: `|L2| + m >= 16` (`PC(W5) = 16`, OPTIMAL,
d4c `c6_pc.py`). So **a proved bound `>= 31` in a run is a theorem for that run's branch** [SAT-scoped].

---------------------------------------------------------------------------------------------------------

## 2. Protocol

* Pure minimisation: objective minimised, **no objective upper bound**, the run stops itself as soon as the
  proved bound reaches the closing value (`best_bound_callback` -> `stop_search`), else at 1,400 s.
* One process, four full core-based subsolvers plus CP-SAT's interleaved LNS helpers. Mix 1
  (`e2_model.CORE4_MIX1`; K24, H6, B0, FULLnoR2): `core_a` (linearisation 1), `core_b` (linearisation 0, seed 7),
  `core_c` (linearisation 1, one core per iteration, seed 13), `core_d` (linearisation 0, reverse assumption
  order, seed 29). Mix 2 (`e2_model.CORE4`; BJnoR2 and every later run): the linearisation-1 workers replaced by
  `core_e` / `core_f` (linearisation 0, seeds 101 / 211), because only linearisation-0 workers had found cores
  (section 6, item 4). The mix is a solver setting only; it does not change the model or what a bound proves.
* A solution with `|L2| + |H3| <= 30` met at any time is written to `e3_TAG_sol.json` at once and then decoded,
  verified (`e5_verify.py` + `circuits/check.py`) and saved under `found/`, with `FOUND_88AT4` written.
* Queues `r1.sh` .. `r9.sh` (each replaced the tail of the previous one when a run showed the next step should
  change; the header comment of each says why; r1 first ran K24/K23 with a parameter error and an invalid-model
  error, fixed before any result, those two attempts left no files); per-run files `e3_TAG.out` (driver output + `MAXRSS`), `e3_TAG.log` (solver log),
  `e3_TAG.json` (status, bound, witness if any).

---------------------------------------------------------------------------------------------------------

## 3. Restrictions of the helper universe and why they are sound [proved]

Used only in K24 and H6 (and prepared for K23; see the table for which ran).

(a) **K24** (89's level pattern B0, `|L2| = 24`): a circuit of this branch with `|L2| + |H3| <= 30` has
`|H3| <= 6`; `hmin` gives at least 6 helpers in `N6`; so all its helpers lie in `N6`. The restricted model
(helper variables only for `N6`, recipes with an operand outside dropped) therefore contains every such circuit,
and a restricted minimum `>= 31` would close the branch. This is the restriction d4c section 5 recommended.

(b) **H6** (B0, `|H3| = 6` exactly, objective `|L2|`): `hmin` alone puts all six helpers in `N6` (no cost
assumption needed). The branch is closed iff the proved minimum of `|L2|` is `>= 25`. It contains the `<= 30` part
of K24 (there `|H3| = 6` is forced) and also every `|L2| <= 24` with six helpers.

(c) **K23** (B0, `|L2| = 23`): `|H3| <= 7` and at least 6 of them in `N6`, so at most one helper outside `N6`
(constraint `outN6max=1`; the universe itself is not cut).

No other run restricts the helper universe: B0, FULLnoR2, BJ, M use d4c's full 138,557-mask helper universe.

---------------------------------------------------------------------------------------------------------

## 4. Branch table [SAT-scoped bounds]

All runs: scope C strict (weight-2 set exactly `P89`), cuts K1-K3 + `hmin = 6` + `pc5 = 16`, pure minimisation,
4 core workers. "final proved bound" = CP-SAT's best objective bound when the run ended; for H6 (objective
`|L2|`) the closing value is 25, for all others 31. Status UNKNOWN = CP-SAT reported no optimum (no run found any
feasible point at all within its time); a run ended by its 1,400 s limit, by the stop-at-closing-value callback
(the CLOSED rows), or by an interrupt: K24 at 456 s and M2noR2 at 89 s (SIGINT, redirected to more useful runs),
M at 257 s (SIGINT for memory safety: 6.4 GB RSS and growing, under 3 GB left on the shared machine), Mw2 at
813 s (SIGINT to end the session; no bound change after 144 s),
H6 at 275 s (aborted by a second SIGINT, so no json; its bound is read from the log).

@@TABLE@@

Earlier sub-results that this report relies on (d4c, unchanged): **B0noR2b CLOSED** -- over the 89's level
pattern, no circuit without a two-helper level-4 recipe has `|L2| + |H3| <= 30` (core bound 31 at 276 s).

---------------------------------------------------------------------------------------------------------

## 5. Case split: what is closed, what is open

**The split.** For a scope-C circuit let `m` = number of weight-5 outputs at level 4 (0..20) and `j` = number of
the six level-3-realisable weight-7 outputs (y3, y9, y12, y19, y25, y28) at level 3 (the six others, y1, y4,
y11, y17, y20, y27, are at level 4 in every circuit of the scope, d4c 3.1). Then scope C is the disjoint union
of **B0** = `{m = 0, j = 0}` (the 89's level pattern), **BJ** = `{m = 0, j >= 1}` and **M** = `{m >= 1}`. Each is
further the disjoint union of its **noR2** part (no level-4 gate with two helper operands) and its **R2** part
(at least one). In the model: B0 = `fix3=W5 fix4=W7`, BJ = `fix3=W5 jmin=1`, M = `m5min=1`, noR2 = `noR2=1` (the
recipes with two non-output level-3 operands are removed, everything else unchanged). Since every run is the
exact d4c model plus these branch constraints plus valid cuts, a proved bound `>= 31` closes exactly its branch.

| part | noR2 (no two-helper level-4 recipe) | R2 (some two-helper recipe) |
|---|---|---|
| B0: m = 0, j = 0 | **CLOSED** (d4c B0noR2b, 31 at 276 s) | open, `>= @@B:B0@@` (B0 run covers B0 as a whole) |
| BJ: m = 0, j >= 1 | **CLOSED** (BJnoR2, 31 at @@T:BJnoR2@@ s) | open, `>= @@B:BJ@@` (BJ run covers BJ as a whole) |
| M: m >= 1 | **CLOSED** (MnoR2, 31 at @@T:MnoR2@@ s; its part m = 1 also closed separately, M1noR2, 31 at @@T:M1noR2@@ s) | open, `>= @@MBEST@@` (M / Mw2 runs cover M as a whole) |

The bounds in the R2 column are bounds for the whole family (the runs did not exclude noR2), which is the same
as a bound for its R2 part because the noR2 part is closed at 31.

**Theorem status.** "No depth-4 circuit over P89 (or a rotation) with <= 88 gates" would follow from bounds
`>= 31` in the three R2 cells; it is **not** established. What is established: (i) the noR2 column (statement in
section 0); (ii) every scope-C circuit has `|L2| + |H3| >= min(@@B:B0@@, @@B:BJ@@, @@MBEST@@)` (`G >= 58 +` that
minimum), the minimum over the three family bounds -- weak, because M is far behind; a scope-C 88, if it exists,
is in the R2 part of one of the three families; (iii) within B0, any circuit with `|L2| >= 20` has
`|L2| + |H3| >= |L2| + 6 >= 26` already by `hmin`, so B0's open part is a statement about the coupling of the
level-2 bank with two-helper recipes, exactly as d4c section 5 described.

**Sub-branches requested but not separately closed.** K24 (`|L2| = 24`): open at 30 (propagation bound
24 + 6; no core in 456 s). K23 and `|L2| = 17 .. 22` were not run separately: with a fixed `|L2|` the solver
starts at `|L2| + 6` and, as K24 and H6 showed, finds no core, so such runs would only repeat their propagation
bound; the B0 run bounds all of them at once (`>= @@B:B0@@`). J in {1, 2}, {3, 4}, {5, 6} are covered together by BJ
(`j >= 1`), and every `m >= 1` by M / Mw2.

---------------------------------------------------------------------------------------------------------

## 6. What the runs say about method [measured]

1. **Pure minimisation climbs only when nothing in the objective is fixed.** d4c found that every run given
   `ub = 30` stalled at its propagation bound. Here the same stall appeared without any `ub` as soon as the
   branch fixed a cardinality: K24 (`|L2| = 24`, objective effectively `|H3|`, `hmin` gives 6 at once) and H6
   (`|H3| = 6`, objective `|L2|`, `pc5` gives 16 at once) never produced a single core (456 s, 275 s). In both the
   next core is itself the hard question (does a 6-helper skeleton with that level-2 budget exist?), so the core
   loop has nothing cheap to price. Every run whose objective was free climbed (B0 22 -> 26, BJ -> 27,
   M -> @@MBEST@@, FULLnoR2 6 -> 30, BJnoR2 and MnoR2 to 31). d4c's recommended "K24 / K23 first" is therefore
   not a good use of this solver; the B0 run bounds those sub-branches anyway.
2. **The two-helper recipes are what is hard.** Without them, every family closed (64 s, 89 s for `m = 1`,
   1,175 s for `m >= 1`); with them, B0 got 4 cores in 1,400 s after the initial 22 and those cores had
   7,483-17,340 literals (helper-heavy), BJ climbed fast to 25 (59 s), then 26 at 232 s and 27 at 1,190 s
   (cores of 12,568 and 4,194 literals), against 1-2,538 literals in the no-two-helper runs (`z_cores.py`).
3. **Splitting a stalled scope into the families helped**: FULLnoR2 (one run) reached 30 at 1,373 s; its parts
   closed (BJnoR2 at 64 s, MnoR2 at 1,175 s, plus d4c's B0noR2b).
4. **Worker mix.** Mix 1 (`core_a` linearisation 1, `core_b` linearisation 0 seed 7, `core_c` linearisation 1
   single core, `core_d` linearisation 0 reverse order): in B0 and FULLnoR2 all core-found improvements came from
   the linearisation-0 workers (`core_b` 27, `core_d` 1); the linearisation-1 workers only reported the initial
   propagation bound. Mix 2 (from BJnoR2 on: `core_b`, `core_d` unchanged, `core_e` / `core_f` linearisation 0
   with seeds 101 / 211): improvements came from all four, with no single winner (BJnoR2: `core_f` 29 of 29;
   MnoR2: `core_f` 14, `core_b` 10, `core_e` 5, `core_d` 2; BJ: `core_d` 18, `core_b` 7). Memory: up to 5.2 GB
   RSS (BJ), 6.4 GB (M, in 257 s, and Mw2 with two workers): the M family needs a machine with more free memory.
5. **What would close the rest** (exact, in order of expected cost): (a) the R2 families with more wall time per
   run, which this protocol could not give (1,400 s cap): B0 needs 5 more cores; (b) split the R2 part by the
   number `r` of two-helper outputs and by which outputs use them (the 89 uses `r = 6`, exactly the six
   never-level-3 outputs): `r` small is close to noR2, which closes fast; (c) for B0 the helper-skeleton
   enumeration of d4c section 5 (2), now restricted to skeletons with at least one two-helper output.
6. **Proof standard.** All bounds are CP-SAT's proved objective bounds (core-based), not externally certified
   (no LRAT / DRAT proof was produced); same standard as d4c's [SAT-scoped] rows.

---------------------------------------------------------------------------------------------------------

## 7. Files

| file | content |
|---|---|
| `e2_model.py` | d4c's exact model with `allowed=` (helper universe), multi-core subsolvers, stop-at-bound, immediate dump of any `<= 30` solution |
| `e3_run.py` | one instance per run (d4c's keys plus `helpers=N6`, `outN6max`, `hsum`, `obj=x`, `sub=core4`, `stop`) |
| `e5_verify.py` | witness -> `found/*.circ.txt`, unit-vector evaluation, `circuits/check.py` |
| `e3_TAG.out/.log/.json` | per run: driver output (with `MAXRSS_KB`), CP-SAT log, result (H6 has no json: it aborted on a second SIGINT, its bound is read from the log) |
| `r1.sh` .. `r9.sh`, `r*.log` | the sequential queues (`STOP*` files ended a queue's tail when the next one replaced it) |
| `e8_table.py`, `e8_table.json` | branch-table collector (status, bound, bound trajectory from the logs) |
| `z_cores.py` | which subsolver found each bound improvement, core sizes |
| `e9_write_report.py`, `e9_text.md` | this report's assembler and text |
| `z_*.sh`, `z_*.py` | status / kill / API-probe helpers; `z_vtest.out` = the verifier smoke test |
| `found/` | empty unless a `<= 88` circuit was found |
