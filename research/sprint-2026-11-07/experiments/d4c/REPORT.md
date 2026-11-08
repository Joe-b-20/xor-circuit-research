# Scope C: depth-4 circuits over the 89's first layer with the level-2 layer completely free

Folder `~/xs-campaigns/2026-11-07-sprint/d4c/` (scripts `c1_facts.py` .. `c10_write_report.py`, run scripts `r_*.sh`,
outputs `*.out`, `*.json`, solver logs `c3_*.log`). 2026-11-07/08, about 2 hours of compute, one solver process at
a time under `nice -n 8` on a machine at load 25-27 (0 % idle: the solver got roughly one core); repository
read-only. Continues `d4bound/REPORT.md` (F22), whose scope C was left unresolved.

Labels as in d4bound: **[proved]** argument written here; **[finite-checked]** exact computation by a named
script; **[SAT-scoped]** exact CP-SAT result (status OPTIMAL / INFEASIBLE) over a finite model whose coverage of
the stated scope is proved here; **[open]** not decided.

---------------------------------------------------------------------------------------------------------

## 0. Verdict

**Scope C is OPEN: no depth-4 circuit with <= 88 gates over the 89's 26 pairs was found (no run produced a
feasible point with `|L2| + |H3| <= 30`, including a 300 s primal search seeded with the 89), and the exclusion
is proved only for sub-scopes.** Proved [SAT-scoped / finite-checked]: (i) every scope-C circuit has
`|H3| >= 6` and `|L2| + m >= 16` (`m` = weight-5 outputs at level 4); (ii) **over the 89's level pattern (all weight-5 outputs at level 3, all weight-7 at level 4), no circuit without a
two-helper recipe has `G <= 88`** (B0noR2b: exact core bound 31 reached in 276 s); the same statement for every level pattern (FULLnoR2b) reached only the bound shown in the table;
(iii) for the 89's level pattern with two-helper recipes allowed the exact core proof reached `|L2| + |H3| >= 25`
(`G >= 83` in that branch) in 480 s and was still climbing. So an 88 over P89, if it exists, uses at least one
level-4 output of the form 'helper + helper' (as the 89 does for its six never-level-3 outputs); that part -- the
136,824 non-pendant helper masks -- is what remains open, with the level-pattern and |L2| = k branches listed below.

Branches closed (no circuit with `|L2| + |H3| <= 30`, by INFEASIBLE status or a core bound >= 31): B0noR2b. Everything else in the branch table
of section 4 is open with the bound shown; section 5 has the full list, the completeness of the case split, and the
reading against F15 / F22.

---------------------------------------------------------------------------------------------------------

## 1. The question and its exact scope

`P89` = the 26 weight-2 masks (input pairs) of the recorded 89@4
(`circuits/aes-mixcolumns/aes-mixcolumns-xor89-depth4.circ.txt`, listed in `d4bound/d1_facts.json`).
**Scope C**: normal-form depth-<= 4 circuits of one MixColumns column (`M`, 32 x 32 over GF(2)) whose set of
weight-2 masks is **exactly** `P89`. By d4bound Lemmas 1-3 [proved there] such a circuit has level 1 = `P89`, a
level-2 layer `L2` of triples `x + p` and quartets `p + p'` over `P89` (`U2(P89)`, 1,060 candidates), a level-3
layer of helpers `H3` (non-output masks of weight 3-8, each `u + v` with `u` in `L2` and `v` an input, a pair or
a level-2 mask) and outputs, and a level-4 layer of outputs only; `G = 32 + 26 + |L2| + |H3|`. **The question
"is there a depth-4 circuit with <= 88 gates whose first layer is exactly the 89's 26 pairs" is exactly: is
`min |L2| + |H3| <= 30`?** The 89 attains 22 + 9 = 31.

Two remarks on the scope [proved]:
* *Weight-2 masks at level 3.* Over `P89` there are 470 weight-2 masks `u + v` that a level-3 gate could carry
  (pairs not in `P89`, e.g. triple + input). In normal form every weight-2 mask is a level-1 pair (d4bound
  Lemma 1 (iii)), so a circuit carrying one of them has weight-2 set `!= P89` and is outside scope C; they are
  excluded from the level-3 universe here. (d4bound's scope-C model kept them: it was a relaxation of scope C
  towards "`P89` plus extra pairs that feed only level-4 outputs", hence `|S| = 189,027` there vs 188,557 here.)
  The driver has `strict=0` for that relaxation; it was not needed.
* *Raw circuits.* A raw circuit whose level-1 gates are exactly `P89` normalises to one whose weight-2 set is
  `P89` minus dead pairs plus pairs computed at higher levels; the subset case over the family pool is d4bound's
  scope D, the superset case the relaxation above. Scope C is the normal-form statement of d4bound 5.1.

---------------------------------------------------------------------------------------------------------

## 2. The exact model and why it is complete [proved]

Fix `P = P89`. `base` = inputs u `P`; `U2` = triples/quartets over `P` (1,060: 759 triples, 301 quartets);
`V2 = base u U2` (1,118); `S = (U2 + V2) \ (V2 u {0} u {weight 2})` (188,557 masks: everything a level-3 gate
can carry in scope C); `T` = the 32 output masks. 26 outputs lie in `S` (can be at level 3 over `P89` for some
`L2`); the six `y1, y4, y11, y17, y20, y27` (bits 1, 4 of bytes 0 and 2, bit 3 of bytes 1 and 3) never can and
are at level 4 in every circuit of the scope.

**Variables.** `x_u` (`u` in `U2`): `u` is a level-2 gate. `a_s` (`s` in `S`): `s` is present as a level-3
signal (a helper, or an output computed at level 3). Auxiliary Booleans: one per construction `(u, v)` with
`u, v` both in `U2` (`c -> x_u, x_v`), one per level-4 recipe.

**Constraints.**
1. `a_s -> OR` over the constructions of `s`: `x_u` when `v` is in `base`, the construction Boolean when `v`
   is in `U2` (a level-3 gate is a level-2 gate plus a level-<= 2 signal, d4bound Lemma 2).
2. Output `o`: `a_o` (level 3; only if `o` in `S`) OR some recipe `o = s + t` with `s` in `S` present (`a_s`) and
   `t` present: `t` in `base` (free), `t` in `U2` (`x_t`), or `t` in `S` (`a_t`). A level-4 gate is an output and
   has a level-3 operand; both operands are at level <= 3 (Lemma 2); an operand that is an output is usable
   only if that output is at level 3, which is exactly `a_t`.
3. Cost `|L2| + |H3| = sum x_u + sum_(s in S \ T) a_s`, minimised, or bounded by `ub = 30` (feasibility).

**Completeness.** A scope-C circuit maps to `x_u = [u in L2]`, `a_s = [s computed at level 3]`,
constructions/recipes = the gates' operands; every constraint holds and the cost is `|L2| + |H3|` (level-3
non-outputs are the helpers, outputs at level 3 cost 0, level-4 gates are outputs). Conversely
`witness_to_circuit` (`c2_model.py`) turns a feasible point into a gate list, which `circuits/check.py` and an
independent unit-vector evaluation accept (`c5_verify.py`; exercised on the smoke witness, 89 gates, then
deleted from `found/`). So the optimum is exactly `min |L2| + |H3|` over scope C, and INFEASIBLE at `ub = 30`
under restrictions is a theorem for the restricted scope. On the 89's own 22-mask level-2 pool the model
returns 31 (`c3_smokeL89.json`), as d4bound's scope A did.

**Lossless reductions** (each keeps every scope-C circuit representable):
* weight-2 masks removed from `S` (section 1); a level-3 mask lying in `V2` is rebuilt at level 2 (d4bound 5.1);
* *fan-out-0 pruning*: in normal form every gate is an ancestor of an output (Lemma 1 (ii)) and a level-3
  helper can only feed level-4 gates, which are outputs; so a helper mask must occur in some recipe
  `o = s + t`. The 49,961 masks of `S` with no recipe are dropped from the helper universe, leaving 138,557
  [finite-checked, `c1_facts.py`]. The partner `t` of a recipe has that recipe itself, so nothing needed is lost.

**Valid cuts** (redundant for the integer model, added to help the solver; each proved):
* K1: an output at level 4 has a helper operand unless it is "adjacent level-3 weight-5 output + quartet"
  (d4bound Lemma 5). Over `P89` that exception exists for exactly two output pairs, `(y7, y15)` and
  `(y23, y31)`: of the 20 adjacent-pair quartets only these two are sums of two `P89` pairs [`c7_facts3.py`].
* K2: an output at level 3 has a level-2 parent among its candidate parents (constructions over `P89`: 2-11
  per weight-5 output, exactly 3 per realisable weight-7 output, each a triple + a disjoint quartet, so a
  weight-7 output at level 3 forces one triple and one quartet into `L2`).
* K3: a helper has a level-2 parent among its candidate parents.
* `pc5`: `|L2| + #(weight-5 outputs at level 4) >= 16`. Proof: `PC(W5) = 16` is the exact
  minimum number of level-2 masks over `P89` putting all 20 weight-5 outputs at level 3 (CP-SAT OPTIMAL,
  `c6_pc.py`); removing one output from the set to be covered lowers that minimum by at most one.
* `hmin`: at least 6 helpers among the masks that can serve one of the six never-level-3 outputs. Proof:
  `Hfree'(never6) = 6.0` (`c6b_hfree.py`, status OPTIMAL): even when every level-2 mask
  is free and every level-3-realisable output (weight 5 or 7) is a free partner, six helpers are necessary.
  Every circuit of the scope is a point of that relaxation and its helpers serving those six outputs are among
  the summed masks.

**Branch parameters** (`c3_run.py`): outputs forced to level 3 / 4; `sumx = k` (exactly `k` level-2 gates);
`j` = number of the six realisable weight-7 outputs at level 3; `m5` = number of weight-5 outputs at level 4.
A run with status INFEASIBLE at `ub = 30` proves "no scope-C circuit with those restrictions has `G <= 88`".
Solver: OR-tools CP-SAT 9.15, one worker, core-based objective (`optimize_with_core`), or max-HS where stated.
The LP relaxation of this model is useless (bound 0 in d4bound's 900 s runs, and here the LP-based mode is not
used): an output can be covered fractionally by thousands of helper pairs at 1/f each, so only integer
reasoning (cores, propagation) prices the helpers.

---------------------------------------------------------------------------------------------------------

## 3. Finite facts over P89 that shape the problem [finite-checked]

3.1 *Level-3 constructions of outputs* (`c1_facts.py`): per weight-5 output 2-11 (`U2 + pair` 25, `U2 + input` 14,
`U2 + U2` 74 in total); per realisable weight-7 output exactly 3, all triple + quartet; the six never-level-3
outputs have none. Distinct candidate level-2 parents per output: 4-17.

3.2 *Level-4 recipes and helper fan-out* (`c1_facts.py`, `c4_facts2.py`, `c8_roles.py`): one-helper recipes (`R1`,
partner in `V2`) 62-457 per output, two-level-3-signal recipes (`R2`) 1,620-9,358 per output; a level-3 mask can
serve up to 13 outputs (through `R2`) but through `V2` partners at most 4. For the **weight-7** outputs the
pendant options are scarce: per output 8-15 `R1` recipes with a free partner (input / pair), 54-203 with a
level-2 partner (which must then be in `L2`), 0-4 with a weight-5 output as partner (8 masks in all, each serving
one weight-7 output). Masks that can serve a weight-7 output without a second helper: **1,707** (24 of them
serve two, always with two level-2 partners); all other 136,824 candidate helpers serve weight-7 outputs only
in a two-helper recipe. No pair of weight-7 outputs shares a one-helper recipe with both partners free.

3.3 *Exact small optima* (`c6_pc.py`, `c6b_hfree.py`, CP-SAT OPTIMAL): `PC(W5) = 16`;
`PC(W5 + one realisable weight-7 output)` = 18, 17, 18, 18, 17, 18 for y3, y9, y12, y19, y25, y28;
`PC(W5 + all six) = 26`; `PC(the six alone) = 12`. Pure helper bounds with every level-2
mask free: `Hfree(never6) = 6`, `Hfree(all 12 weight-7) = 6` (weight-5 partners only, `c6_pc.py`);
pattern-valid versions with weight-7 partners allowed as well (`c6b_hfree.py`): `Hfree'(never6) = 6.0` [OPTIMAL],
`Hfree'(W7) = 6.0` (bound 6.0, OPTIMAL), `Hfree'(never6 + y)` for the realisable weight-7 outputs:
y3: 6.0, y9: 6.0, y12: 6.0, y19: 6.0, y25: 6.0, y28: 6.0; for two weight-5 outputs:
y0: 6.0, y7: 6.0. (An enumeration of the minimum 16-mask parent covers of W5 was
attempted in CP-SAT's enumeration mode and listed no solution in 120 s [status UNKNOWN]; the count is
not used anywhere below.)
Consequence [proved]: in every scope-C circuit `|H3| >= 6` and `|L2| + m >= 16` (`m` = weight-5 outputs at
level 4); the decoupled bound `PC + Hfree` reaches 31 only for `J` = all six realisable weight-7 outputs at
level 3 (26 + 6 = 32): **everything else is decided by the coupling between the level-2 bank and the helpers**
(helpers need level-2 parents, one-helper recipes need level-2 partners), which is what the SAT runs price.

3.4 *The 89 in these terms* (`c8_roles.py`): its 22 level-2 gates are a minimum parent cover of W5 (16 masks;
no level-2 gate feeds more than two gates) plus 6 extras (`t31, t32, t36, t38, t44, t46`) used only by helpers;
its 9 helpers (6 odd of weight 5, 3 even of weight 6) have one level-2 parent each (t55 has two); the six
realisable weight-7 outputs are "odd helper + free pair" (`R1`), the six never-level-3 outputs are
"odd helper + even helper" (`R2`); so 31 = 16 + 6 + 9, and an 88 must save one gate in the 6 + 9.

---------------------------------------------------------------------------------------------------------

## 4. Branch table [SAT-scoped where UNSAT / OPTIMAL]

All runs: scope C strict, `P89`, one CP-SAT worker, `nice -n 8`, wall limits as listed (the machine was fully
loaded, so wall seconds are roughly CPU seconds of one core). `ub = 30` rows are feasibility instances:
INFEASIBLE = "no depth-4 circuit with <= 88 gates in that branch"; "timeout, bound reached b" = the core-based
proof reached `|L2| + |H3| >= b` for the branch when stopped. `hmin` / `pc5` are the cuts of section 2.

| tag | restriction | ub | mode | limit s | cuts | status | bound | obj | verdict | wall s |
|---|---|---|---|---|---|---|---|---|---|---|
| B0core | Y3 = W5; Y4 = W7 |  | core | 480 |  | UNKNOWN | 25 |  | timeout, bound reached 25 | 480 |
| B0k16 | Y3 = W5; Y4 = W7; sumx=16 | 30 | core | 300 | hmin | UNKNOWN | 22 |  | timeout, bound reached 22 | 300 |
| B0k24 | Y3 = W5; Y4 = W7; sumx=24 | 30 | core | 300 | hmin | UNKNOWN | 30 |  | timeout, bound reached 30 | 300 |
| B0k24f | Y3 = W5; Y4 = W7; sumx=24 | 30 | portfolio 4 threads | 900 | hmin | UNKNOWN | 30 |  | timeout, bound reached 30 | 900 |
| B0maxhs | Y3 = W5; Y4 = W7 | 30 | max-HS | 240 | hmin | UNKNOWN | 6 |  | timeout, bound reached 6 | 244 |
| B0noR2 | Y3 = W5; Y4 = W7 | 30 | core | 300 | hmin | UNKNOWN | 6 |  | timeout, bound reached 6 | 299 |
| B0noR2b | Y3 = W5; Y4 = W7 |  | core | 300 | hmin | UNKNOWN | 31 |  | CLOSED: no circuit with h2+h3 <= 30 (core bound 31 >= 31) | 300 |
| BJ56 | Y3 = W5 | 30 | core | 240 | hmin,pc5 | UNKNOWN | 22 |  | timeout, bound reached 22 | 240 |
| FULLcore | none (full scope C) |  | core | 700 |  | UNKNOWN | 11 |  | timeout, bound reached 11 | 701 |
| FULLnoR2b | none (full scope C) |  | core | 300 | hmin,pc5 | UNKNOWN | 25 |  | timeout, bound reached 25 | 300 |
| LNS88 | none (full scope C) | 30 | portfolio 4 threads + hint 89 | 300 | hmin,pc5 | UNKNOWN | 10 |  | timeout, bound reached 10 | 305 |


---------------------------------------------------------------------------------------------------------

## 5. Verdict, and what it says together with F15 / F22

**Scope C is OPEN: no depth-4 circuit with <= 88 gates over the 89's 26 pairs was found (no run produced a
feasible point with `|L2| + |H3| <= 30`, including a 300 s primal search seeded with the 89), and the exclusion
is proved only for sub-scopes.** Proved [SAT-scoped / finite-checked]: (i) every scope-C circuit has
`|H3| >= 6` and `|L2| + m >= 16` (`m` = weight-5 outputs at level 4); (ii) **over the 89's level pattern (all weight-5 outputs at level 3, all weight-7 at level 4), no circuit without a
two-helper recipe has `G <= 88`** (B0noR2b: exact core bound 31 reached in 276 s); the same statement for every level pattern (FULLnoR2b) reached only the bound shown in the table;
(iii) for the 89's level pattern with two-helper recipes allowed the exact core proof reached `|L2| + |H3| >= 25`
(`G >= 83` in that branch) in 480 s and was still climbing. So an 88 over P89, if it exists, uses at least one
level-4 output of the form 'helper + helper' (as the 89 does for its six never-level-3 outputs); that part -- the
136,824 non-pendant helper masks -- is what remains open, with the level-pattern and |L2| = k branches listed below.

Branch results (details in section 4):
* Scope C, no restriction (139,591 objective literals; reference run, 700 s): **open** -- timeout after 701 s (core-based); proved lower bound in this branch `|L2| + |H3| >= 11`.
* B0 = the 89's level pattern (20 weight-5 outputs at level 3, 12 weight-7 at level 4), objective free: **open** -- timeout after 480 s (core-based); proved lower bound in this branch `|L2| + |H3| >= 25`.
* B0, max-HS mode, `ub = 30`: **open** -- timeout after 244 s (max-HS); proved lower bound in this branch `|L2| + |H3| >= 6`.
* B0 with exactly 16 level-2 gates (a minimum parent cover), `ub = 30`: **open** -- timeout after 300 s (core-based); proved lower bound in this branch `|L2| + |H3| >= 22`.
* B0 with exactly 24 level-2 gates (so at most 6 helpers), core mode: **open** -- timeout after 300 s (core-based); proved lower bound in this branch `|L2| + |H3| >= 30`.
* B0 with exactly 24 level-2 gates, 4-thread portfolio, 900 s: **open** -- timeout after 900 s (portfolio, 4 threads); proved lower bound in this branch `|L2| + |H3| >= 30`.
* B0 with no two-helper recipe (helpers from the 1,707 pendant masks), `ub = 30`: **open** -- timeout after 299 s (core-based); proved lower bound in this branch `|L2| + |H3| >= 6`.
* B0 with no two-helper recipe, pure minimisation (no `ub`), core mode: **CLOSED -- UNSAT for <= 88** [SAT-scoped] (core lower bound 31 >= 31 reached; core-based, 300 s): no circuit in this branch has `|L2| + |H3| <= 30`.
* Scope C with no two-helper recipe anywhere (8,301 pendant masks), `ub = 30` (stopped early: same stall): not completed (stopped before its limit once the `ub` stall was understood; log kept, no result file).
* m = 0 and at least 5 of the 6 realisable weight-7 outputs at level 3: **open** -- timeout after 240 s (core-based); proved lower bound in this branch `|L2| + |H3| >= 22`.
* m = 0 and 3 or 4 realisable weight-7 outputs at level 3: not run (dropped from the queue to stay inside the 2 h budget; it would have needed the pure-minimisation protocol).
* exactly one weight-5 output at level 4: not run (dropped from the queue to stay inside the 2 h budget; it would have needed the pure-minimisation protocol).
* primal lottery: scope C, `ub = 30`, the 89 as solution hint, 4-thread portfolio with LNS, 300 s: **open** -- timeout after 305 s (portfolio, 4 threads); proved lower bound in this branch `|L2| + |H3| >= 10`.

**A methodological fact that shaped the table** [measured on these runs]: every instance given the hard bound
`ub = 30` stalled at its initial-propagation bound (22, 30, 22, 6, 6: the sum of the cuts) with no further core,
whereas the two pure minimisations without `ub` (B0core: 25 in 480 s; FULLcore: 11 in 700 s) climbed steadily.
With an objective upper bound CP-SAT leaves its core loop for bound-driven search, which is hopeless here; the
right protocol for the remaining branches is pure core minimisation (read the bound, stop at 31), as in the last
run B0noR2b. Most rows of the table are therefore weaker than the method allows, and the branch budget was spent
learning this.

**Completeness of the case analysis.** Scope C = (m = 0) u (m >= 1), m = number of weight-5 outputs at level 4;
(m = 0) = union over J (the realisable weight-7 outputs at level 3) = B0 (J empty) u BJ12 u BJ34 u BJ56;
B0 = union over k = |L2| in 16..24 (k <= 24 because |H3| >= 6; k >= 16 because PC(W5) = 16);
every branch is further split by "two-helper recipe used / not used" (noR2). A branch is closed only by an
UNSAT row; every other branch stays open with the bound shown. The table tells which rows closed.

**What this says together with F15 / F22.** F22 proved 89 optimal over the 89's first layer *plus* the
family's level-2 vocabulary (scopes A, B, D). This folder sharpens the open scope C by exact structure: over
P89 the level-2 bank must contain a 16-mask parent cover of the weight-5 outputs (the 89's 22 = that cover + 6
extras used only by helpers), six helpers are forced by the six never-level-3 outputs even with the whole
level-2 universe free, helper-free level-4 outputs exist only for (y7, y15) and (y23, y31), and weight-7
outputs can be served by a single helper only through 1,707 specific masks. So an 88 over P89, if it exists,
saves its one gate in the coupling (which level-2 masks double as helper parents / partners), not in the cover
and not in the helper count; F15's observation that pinned completions over this first layer reach 89 and never
88 is consistent with, but not yet a theorem about, that coupling. None of this is a general depth-4 bound: it
is a statement about circuits whose weight-2 masks are exactly P89 (and, by Z4, its three rotations); D4 >= 75
remains the only unrestricted bound (F22).

**What would close it** (in order of cost): (1) the k = 24 and k = 23 SAT calls with a CDCL solver and a
helper universe restricted to the never6-fan set (26,024 masks), 1-2 CPU-hours each on a free machine; (2) a
helper-skeleton enumeration for |H3| = 6, 7 (pendant/R2 role assignment per output, then a tiny level-2 cover
check per skeleton); (3) for k <= 22, enumeration of minimal parent covers with the level-3 universe S(L2) computed
per cover (a few thousand tiny instances) -- all three are exact and checkable; none fits one loaded core in 2 h.

---------------------------------------------------------------------------------------------------------

## 6. Files

| file | content |
|---|---|
| `c1_facts.py` -> `c1_facts.out/.json` | universe sizes, constructions per output, recipe counts, fan-out histograms |
| `c2_model.py` | the exact model (library): universe, CP-SAT build with cuts, solve, witness -> circuit, circuit writer |
| `c3_run.py` -> `c3_TAG.out/.json/.log` | one instance per run (restrictions as key=value), witness json, solver log |
| `c4_facts2.py`, `c7_facts3.py`, `c8_roles.py` -> `.out/.json` | weight-7 recipe structure; Lemma-5 pairs, parity fan-outs, weight-5 recipe structure; the 89's role table and pendant fan-outs |
| `c5_verify.py` | witness -> `found/*.circ.txt`, `check.py` + unit-vector check (no 88 witness was found, so `found/` is empty) |
| `c6_pc.py`, `c6b_hfree.py` -> `.out/.json` | exact parent covers and pure helper bounds (with witnesses) |
| `c9_table.py`, `c10_write_report.py` | branch table; this report's assembler |
| `r_cal.sh`, `r_q1.sh` .. `r_q8.sh`, `r_*.log` | the sequential run queues (one solver process at a time; later queues replaced earlier ones as the protocol changed) |
| `c3_B0k17.log/.out`, `c3_B0k23.log/.out`, `c3_FULLnoR2.log/.out` | runs stopped before their limit (no `.json`): B0k17 / B0k23 after B0k16 and B0k24 showed the `ub` stall, FULLnoR2 after B0noR2 did |
