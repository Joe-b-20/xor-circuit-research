# How BoolFlux works (from the code)

Paths are relative to `nonlinear/boolflux/`. Line numbers refer to commit `19480fc` on
`boolflux-2026-11-13`.

## 1. What came from XORFlux, what was replaced, what is new

BoolFlux imports no XORFlux code (the package modules and kernels never reference `search/`; only
the benchmark scripts in `bench/` run XORFlux as a separate process). What it shares is design.

| XORFlux v8 (`search/xorflux/`) | BoolFlux | status |
|---|---|---|
| state = one *chain* per worker, an incrementally indexed value set of linear forms (`core/valueset.py`) | one correct circuit per kernel process, full truth tables of every signal, recomputed per candidate (`kernel/bfx.c`: `sim`, `state_refresh`) | idea kept, representation replaced |
| main move: plateau *walk* = remove helper gates and repair the forms exactly (`moves/walk.py`) | *resubstitution*: replace one gate's function by 0-3 new gates that agree with it on its exact care set (`find_cands`, `eval_cand`) | idea kept (remove + exact repair), generalised to any gate type and to don't-cares |
| LNS: destroy part of the circuit, rebuild from a candidate bank (`moves/lns.py`) | none at gate level; the closest analogue is the skeleton stage + rebuild | dropped |
| neutral (plateau) moves accepted; soft depth slack then depth repair (`engine/acceptance.py`, `moves/depth.py`) | neutral moves accepted; hard caps, exact required-level pruning; a penalised repair mode for starts that break a cap | kept / replaced |
| phases burst / plateau / repair (`engine/phase.py`) | no phases; one fixed move mix (`mv.resub1/2/3` weights) and a sawtooth annealing temperature | replaced |
| restarts from fresh randomised roots, elites or shared DAGs on stall (`engine/restart.py`) | restart from the chain's own best after `stall_it` iterations without a new best | simplified |
| coordinator, frontier, pull-on-stall sharing between workers (`campaign/`) | none inside a run; `cli.py run/pipe --rounds` restarts all jobs from a pool of distinct best circuits between rounds | replaced by round-level pooling |
| dossiers with move trace and replay seed (`engine/dossier.py`) | `summary.json` (seed, iteration of each improvement), source snapshot per run, optional `tracemoves` log with circuits before/after each improvement | replaced |
| verified records | every candidate re-simulated in the kernel; two independent verifiers on reported circuits | kept, extended |
| — | AND-skeleton search (`kernel/skel.c`), skeleton extraction and rebuild (`skeleton.py`), configurable gate library and costs, exact linear mode | new |

## 2. Search state and correctness (gate level, `kernel/bfx.c`)

- **State**: `cur`, a straight-line program over `N` inputs; gate `j` is `(op, a, b)`, op a 4-bit
  truth table, operands earlier signals (`Gate`, `Circ`, l.82). `Vcur` holds the complete truth table of
  every signal (`2^N` bits; `W` 64-bit words; `sim`, l.93). `state_refresh` (l.334) also computes
  levels, required levels from the caps, and fanout counts.
- **Target**: the start circuit's output tables (`TGT`, set in `main`). Every candidate circuit is
  re-simulated on all simulated patterns (all 2^N inputs, or the N+1 patterns of linear mode) and
  compared with `TGT` (`eval_cand`, l.608) before `fraig` runs; a mismatch aborts. An accepted
  circuit is checked again after `fraig` by `state_refresh` (l.334).
- **Exact linear mode** (`linear 1`; `bench/bench.py` sets it for XOR-only libraries, `cli.py` does
  not, which is correct but slower): signals are
  simulated on the `N+1` patterns `0, e_0, ..., e_{N-1}` only. Every gate is affine, an affine
  function is determined by those values, and an XOR circuit's observability of a signal does not
  depend on the input, so this is exact, not a sample.

## 3. Candidate generation (one move)

1. Pick a gate `s` uniformly (`main` loop) and a move level (`resub1/2/3`, weights 1:2:1).
2. **Care set** (`tfo_care`, l.362): flip `s`'s table, re-simulate its transitive fanout, OR the
   output differences. `CARE` = the input patterns on which `s` matters. Divisors = all signals
   outside the fanout cone (no cycles), shuffled, at most `dmax` (220).
3. **MFFC cost** (`mffc_cost`, l.389): cost of the gates that die if `s` is replaced; the new
   expression may cost at most `MFFC + uphill` (`budget`).
4. **Required levels**: `req = max(required(s), level(s))` for gate depth and AND depth, so a
   candidate never breaks a depth cap (and never deepens `s` in repair mode). The AND-count cap is
   not pruned; it is enforced by acceptance (a feasible state is never left).
5. **Candidates** (`find_cands`, l.479), all compared with `s` on `CARE` only:
   - level 0: an existing divisor equal to `s` on the care set;
   - level 1: every `op(d1, d2)` over the first `pdiv` (90) divisors, every library op and
     orientation, plus `NOT d` (`build_pairs`, l.432: a hash table of masked values);
   - level 2a: `XOR/XNOR(op(d1,d2), d3)`: one hash lookup of `s ^ d3` per divisor;
   - level 2b: `op2(op(d1,d2), d3)` with `op2` and `d3` sampled (`op2` from every binary library op,
     XOR/XNOR included; `nl_samples` = 12 per move): per input pattern the
     required value of the inner gate is derived from `op2`'s truth table (forced, or free when
     `op2` ignores it there), then all pair values are scanned against it;
   - level 3: `XOR/XNOR(op(d1,d2), op'(d3,d4))` via hash lookups of `s ^ pair`.
   Up to `cand_cap` (40) candidates are kept by reservoir sampling.
6. **Rebuild** each candidate (`rebuild`, l.167): redirect `s` to the new root, DFS from the
   outputs (topological order, dead gates dropped), simplify gates with equal operands,
   structural hashing; then the re-simulation check; then `fraig` (l.580) merges any gate whose
   complete function equals an earlier signal that is not deeper; then metrics.
   **Correctness condition**: the new root equals `s` on every pattern where `s` is observable, so
   every output is unchanged on every input; the re-simulation confirms it.

## 4. Acceptance, annealing, repair, restarts

- Objective: lexicographic weights (`cli.objective_weights`: 1, 1e-4, 1e-8) over cost, G, A, GD,
  AD, plus `1e6 * violation + 1e4 * per-gate excess` when a cap is broken (`metrics`, l.123).
- Selection (main loop): the best strict improvement if any (never from feasible to infeasible);
  else a random equal-cost candidate (plateau walk; `neutral 0` disables it) when no uphill
  candidate exists, when the temperature is 0, or otherwise with probability 0.75; else a random
  uphill candidate accepted with
  `exp(-delta/T)`, `T = T0 (1 - phase)` with a sawtooth over `Tperiod_it` iterations, never more
  than `max_excess` above the best.
- **No-op filter** (`skip_noop`, added after the traces, on by default from commit 7ae20c8): a
  candidate whose rebuilt circuit is gate-for-gate identical to the current one is discarded
  instead of counting as a neutral move. This changes the random trajectory, so runs recorded
  before 7ae20c8 replay only with `skip_noop 0`. `odc 0` disables care sets for observable signals
  (an unobservable signal can still be replaced by anything).
- **Repair**: a start that violates a cap is searched with the penalty; required levels are
  relaxed to "not deeper than now" so moves exist; the summed per-gate excess rewards shortening
  any too-deep path.
- **Restart**: after `stall_it` (60,000) iterations without a new best, `cur` returns to `best`.
- Determinism: all randomness from one seeded xoshiro256** (`seed_rng`); with an iteration budget
  and iteration-based schedules (`Tperiod_it`, `stall_it`, as `cli.DEFAULTS` sets; the kernel's own
  defaults are wall-clock based) a run is reproducible exactly.

## 5. Skeleton level and rebuilding

- **Extraction** (`skeleton.extract`): every nonlinear gate is `((a^p)&(b^q))^r`; walking the gates
  in order gives each signal an affine form over (1, x, g_0, g_1, ...); ANDs become `(L, R)` form pairs.
- **Skeleton kernel** (`kernel/skel.c`): state = the AND list; `analyze` (l.119) evaluates every AND,
  Gaussian elimination over all basis tables, checks every output table is in the span, deletes
  dependent ANDs by substitution. Moves: `mv_swap` (l.254) replaces a leaf AND by any product
  `L*R` congruent to it modulo the span of the rest (`find_products`, l.210: all pairs of input-linear
  forms, then random pairs over forms built from existing operands); `mv_merge` (l.275) replaces two
  leaves with equal output usage by one product congruent to their sum (cuts K by one);
  `mv_split` (l.310), `mv_perturb` (l.330). Objective K + 0.02 E (E = unshared XOR count).
- **Rebuild** (`skeleton.synthesize`): two algorithms.
  - *From forms* (the original): each needed form (AND operands per AND level, then outputs) is
    built greedily from already-built signals (largest overlap first), optionally after Paar's
    pair-frequency heuristic; constants become XNOR/NOT.
  - *Seeded with the parent* (added in this round; `parent_forms`, `synthesize(parent=...)`):
    every parent signal is given its form in the new skeleton's basis when its exact function is
    still there (inputs; parent ANDs whose core truth table is one of the new ANDs; linear gates
    whose operands map). Those parent gates are copied first, ANDs reuse their parent operands,
    and only the forms the skeleton moves broke are built greedily; unused copies are swept.
- **Penalty investigation** (`bench/rebuild_penalty.py`; data in the review bundle,
  `data/rebuild_penalty.json`):
  rebuilding an *unchanged* skeleton from forms costs +31 to +72 gates on NIST AES circuits
  (104 -> 152, 131 -> 203, 142 -> 173): the systematic part of the reported 40-50 gate penalty was the
  rebuild algorithm, not the AND moves. The seeded rebuild reproduces every unchanged skeleton
  exactly (+0). After skeleton moves the seeded penalty grows with the number of AND functions
  changed (1 accepted move: +0 to +19; 25-90 moves: +45 to +100), because every XOR that combined a
  changed AND's output has to be rebuilt. Under the benchmark settings the skeleton kernel returned
  its input skeleton unchanged in 11 of 12 AES cases (review2, M3): no move lowers K + 0.02 E, so
  the stage's output is the start and, with the old rebuild, the whole loss was rebuild cost.
  `emit_current 1` returns the drifted skeleton instead.

## 6. Worker coordination

There is no communication inside a run. `cli.py run` and `pipe` start one kernel process per seed
(up to `--jobs` at once); after each round the distinct best circuits (up to `--pool`, by objective)
become the start circuits of the next round's jobs, round-robin; the best over all rounds is
reported. In `pipe` a fraction `--skel-share` (default 0.5, by a golden-ratio sequence over the job
index) of the jobs run skeleton kernel + rebuild (seeded and unseeded variants, the cheapest kept)
before the gate kernel; the rest run the gate kernel only. The benchmark driver's `full`
configuration instead alternates skeleton and gate stages inside one job (`bench/bench.py`).
Campaign scripts (`campaigns/*.sh`) run independent `cli.py` commands.
