# XOR-circuit search: where the time goes, and a faster core

All numbers were measured on CPython 3.12.3 (WSL, the only interpreter installed), best-of-5 per call unless noted. Nothing under the repo was modified. The scripts, profiles and prototypes were kept outside this repository (not included).

Seeds used (live value sets from `common.replay`):

| case | target | inputs | outputs | value-set size \|S\| | depth |
|---|---|---|---|---|---|
| joltik44 | joltik | 16 | 16 | 44 | 7 |
| invmc88 ("MixColumns-size") | invmixcolumns | 32 | 32 | 88 | 19 |
| foxmu4_130 | fox_mu4 | 32 | 32 | 130 | 13 |
| foxmu8_540 ("FOX Mu8-size") | fox_mu8 | 64 | 64 | 540 | 14 |

## 1. `run_chunk` profiles (10 s per engine, cap=None)

Setup (`prof_engine.py`, `run_profiles.sh`): each run used an `on_candidate` callback that does `target.normalise` + `target.verify(cap)`, i.e. the worker's verification work without its file I/O. Plain-run rates (no profiler):

| engine | joltik it/s (prop/s) | invmc88 it/s (prop/s) | fox_mu8 it/s (prop/s) |
|---|---|---|---|
| legacy-walk | 55.0 (0.1) | 9.0 (0.1) | **0.4** (0.0) |
| legacy-lns | 177.8 (177.7) | 48.0 (47.9) | **4.7** (4.6) |
| v2-walk | 216.0 (1.9) | 61.0 (0.0) | 3.0 (0.0) |
| v2-lns | 33.7 (33.7) | 27.7 (27.7) | 22.1 (22.1) |
| v2-translate | 26.1 (25.7) | 23.8 (23.6) | 19.5 (13.5) |
| v3-component | 24.2 (24.2) | 23.6 (22.3) | 19.6 (18.4) |
| legacy-window | 374.0 (0) | 40.3 (0) | 2.6 (0) |
| inverse-bp | 308.4 (3.1) | 24.6 (0) | 14.0 (0) |

The v2-* and v3 engines are capped near 25 it/s by `proposal_seconds=0.04`, so for them the useful question is how much search fits in each 40 ms, not iterations per second.

### Top hotspots (% of run_chunk time, under cProfile)

| engine | fox_mu8 | invmc88 |
|---|---|---|
| legacy-walk | `common.legacy_extract` **95.2% self** (62 calls in 10 s; up to 17 extracts per iteration, each running an O(passes·n²) level fixpoint) | legacy_extract 90.6% self |
| legacy-lns | legacy_extract 85.6% self | legacy_extract 73.4%; deepcopy 4.6%; emit/verify 7.2% |
| v2-walk | `deadline_search._earliest` **89.8% self** (869 full level-BFS calls, one per menu) | _earliest 59.9%; `append` 11.5%; deepcopy 9.1% |
| v2-lns | `reconstruct` 42.6% self (its O(n²) recipe-alternatives loop); _earliest 21.1%; _emit 8.8%; replay 11.7% | `_emit` 34.1% self (10,113 calls from `complete_partial`); reconstruct 13.3% |
| v2-translate | _earliest 33.3%; _emit 9.8%; `_unaffected_values` 4% | _emit 22.3%; reconstruct 5.7% |
| v3-component | `_Constructor.ensure` 35% cum; `_normalise` 21.2% cum; `verify_steps` 14.7%; `_Budget.check` 15.4% cum | ensure 70.8% cum; sort/lambda 15.7%; Budget.check 11.5% |
| legacy-window | `sorted()` 38.4% + genexpr 30.7% + any 18.8%: `closure()` re-sorts `available` for every probe | same pattern (97.3% in closure) |
| inverse-bp | `distance` 44%; **stop lambda + time.monotonic 35.2%** (11.6M calls); bit_count 11.9% | same (34.5% stop) |

### Non-search overhead (`overheads.py`, % of run_chunk)

| profile | replay of each proposal | deepcopy | emit + callback | stop() calls |
|---|---|---|---|---|
| v2-lns fox_mu8 | **11.7%** | 6.4% | 5.0% | 0 |
| legacy-lns joltik | 6.1% | **28.5%** | 7.4% | 1.7% |
| v2-walk joltik / invmc88 | 0.1 / 0.0% | **21.7 / 9.1%** | 0.2% | 0.4% |
| v2-translate fox_mu8 | 4.1% | 2.7% | **10.4%** | 0 |
| v3-component invmc88 | 2.2% | 1.5% | 5.8% | 5.2% (+ Budget.check) |
| inverse-bp (all targets) | 0% | 0.3–4.4% | 0.2% | **30–35%** |

Unit costs behind these, measured with `bench_primitives.py` and `bench_idioms.py`:

- `common.replay` of every proposal: 174 µs (invmc88), 1.26 ms (fox_mu8). The proposal already came out of `_emit`, so this is a second full replay.
- `copy.deepcopy(auxiliary)` with a 2048-int pool: 300 µs per iteration. `list(pool)` does the same job in 4.3 µs.
- `value_search` pool update `sorted(set(pool)|set(values)|additions)[-2048:]`: 454 µs per iteration.
- Worker candidate path (normalise + verify; `worker.candidate` actually verifies twice, inside normalise and again in `check`): 587 µs (invmc88), 3.28 ms (fox_mu8). `emit` also deep-copies the gates: 67 / 394 µs.
- `stop()` lambda: 72 ns per check (95 µs per 1000) vs 18 ns with a counter guard (`bench_micro [d]`, x4.0).
- `effective_knobs`/`_kernel_metadata` (inspect + ast): about 0.2% per chunk. Negligible.

## 2. Duplicated primitives, head-to-head on identical value sets

"bank" means S minus 3 victims plus 30 random pair sums of kept values, which is an LNS bank.

### Earliest-arrival levels (exact; all variants agree, checked by `test_vcore.py`)

| implementation | invmc88 S | invmc88 bank | fox_mu8 S | fox_mu8 bank |
|---|---|---|---|---|
| `relax_reference` (passes × n² fixpoint) | 5.75 ms | 9.75 ms | 72.3 ms | 80.1 ms |
| `common.legacy_extract` level fixpoint | 7.52 ms | 12.5 ms | **115.0 ms** | **128.5 ms** |
| `engines.relax` (level BFS) | 206 µs | 331 µs | 5.62 ms | 6.25 ms |
| `deadline_search._earliest` | 321 µs | 491 µs | 7.47 ms | 8.10 ms |
| **`vcore.earliest_scan`** (BFS + popcount bound) | **169 µs** | **290 µs** | **3.56 ms** | **4.02 ms** |
| vcore re-level from the triple index | 193 µs | 288 µs | **1.59 ms** | **1.67 ms** |
| `common.replay` (seed gates) | 174 µs | – | 1.26 ms | – |

`relax` is 28x faster than `relax_reference` on invmc88, which matches the campaign's 18.9x claim. The legacy-walk/legacy-lns kernel in `search/engines/common.py` still uses the slow fixpoint, and is **32x slower than `earliest_scan` on fox_mu8**.

**Winner for a one-shot bank:** `earliest_scan`. It is relax plus two exact refinements: level 1 iff popcount is 2, and a value only joins the active list at level ceil(log2 popcount). That gives 1.2–1.6x over relax and 2.1x over `_earliest`. **Winner for a maintained state:** the triple index.

### Closure / realisability (cap=None)

| | invmc88 | fox_mu8 |
|---|---|---|
| `historical_extra.window.closure` | 1.55 ms | 22.5 ms |
| `engines._closure_core` | 237 µs | 7.67 ms |
| `engines.feasible_at(None)` | 189 µs | 5.28 ms |
| `vcore.earliest_scan` | **158 µs** | **3.57 ms** |

### Remove k values, then get the exact stuck set (80 queries, k = 1 or 2)

| | invmc88 | fox_mu8 |
|---|---|---|
| full `_closure_core(S−D)` | 193 µs | 7.84 ms |
| `engines._WalkState.remove_query` | 128 µs | 506 µs |
| full `relax(S−D)` (capped search) | 178 µs | 5.44 ms |
| **vcore `remove` + `restore`** (any cap, exact levels) | **66 µs** | **42 µs** (186x vs full, 12x vs WalkState) |

### Complete single-value repair enumeration (equal sets to `_repair_candidates`)

| | invmc88 (mean stuck 20.4) | foxmu4_130 (9.8) | fox_mu8 (6.3) |
|---|---|---|---|
| `engines._repair_candidates` (fresh n²/2 pair-sum set + O(k²) unlock per candidate) | 968 µs | 1.46 ms | 33.3 ms |
| vcore (lazy pair-sum counter + triple-index unlock) | 991 µs (x1.0) | 679 µs (x2.2) | **2.29 ms (x14.5)** |
| vcore without counter | 6.8 ms | 7.4 ms | 83.6 ms |

### Greedy top-down rebuild (`_extract` semantics, cost classes 1/2/3)

| | invmc88 | fox_mu8 |
|---|---|---|
| `common.legacy_extract` | 14.4 ms | 136.6 ms |
| `engines.relax` + `_extract` | 1.24 ms | 26.5 ms |
| **vcore incremental** (add 30 extras + extract + remove extras) | **814 µs** | **2.21 ms (x12 vs _extract, x62 vs legacy)** |
| vcore extract alone on an indexed bank | 109 µs | 800 µs |

Result quality is the same: on 80 identical banks (`check_extract.py`) the mean size delta was +0.55 (legacy_extract), +0.61 (`_extract`) and +0.60 (vcore), and the share that did not get worse was 0.62 / 0.60 / 0.60.

### Peel to 1-minimal, and trim

| | invmc88 | fox_mu8 |
|---|---|---|
| `engines._peel` (feasible_at per removal, restart after each success) | 42.3 ms | **7.26 s** |
| vcore `Circuit(set)` + `peel` + `trim` | 6.08 ms | **39.4 ms (x184)** |
| `trim_masks` / `_trim_at_cap` | 324 µs / 1.03 ms | 8.1 / 25.8 ms |
| vcore `live()` | 13.8 µs | 166 µs |

### Emit / normalise / hash

On fox_mu8: `vcore.gates()` takes 397 µs, against 3.28 ms for normalise + verify. `vcore.dag_sha256()` produces a hash **bit-identical** to `verify()['dag_sha256']` (checked on 60 states) in 588 µs. A `frozenset` key takes 44–52 µs. On invmc88 the same three cost 35 µs, 69 µs and 8 µs.

**`deadline_search.reconstruct` setup** (`bench_reconstruct.py`): on fox_mu8 the recipe-alternatives loop takes **18.2 ms** and the setup before it (normalise + `_earliest` + `_emit`) another 7.8 ms. That is about 26 ms of every 40 ms v2 proposal spent before the beam starts. Built from the triple index, the alternatives take 0.26 ms (x70) and are identical.

## 3. Prototype: `vcore.Circuit`, a triple-indexed value set (`vcore.py`)

**First finding: Python idioms don't fix this.** On CPython 3.12 with 64-bit masks, `set.isdisjoint(map(v.__xor__, A))`, `filter`/`compress` chains and `set.update(map(...))` measured **0.8–0.9x of a plain for-loop** (`bench_idioms.py`). The cost floor is about 25–60 ns per XOR plus lookup, so speedups have to come from doing fewer pair tests.

**Key structure.** For U = inputs ∪ S, keep `tri[v] = {x ∈ U : v ^ x ∈ U}`. Every relation a ^ b ^ c = 0 is symmetric, so `tri[v]` lists both v's recipes and the values v helps build. It is very sparse on real circuits:

- 89 triples for 88 values (invmc88), 545 for 540 (fox_mu8), 1,119 for 1,100.
- Mean 2.5 triples per value, maximum 7.

On top of the index the state keeps:

- exact earliest `level` (≤ cap; missing means unrealizable or "stuck");
- one witness parent per value, `par`;
- witness children, `kids`;
- optionally, a lazy pair-sum counter `p2`.

| operation | cost | how |
|---|---|---|
| build | one O(\|U\|²/2) pass: 13.6 ms (540), 48.6 ms (1100) | find triples, then Knuth/Dijkstra levelling |
| `add(w)` | one O(\|U\|) scan, 35–74 µs | new triples, then heap-based decrease propagation |
| `remove(D)` | O(descendants × degree) | re-levels only witness descendants; returns an `Undo` |
| `restore(undo)` | exact inverse (levels depend only on U) | no deepcopy, no journal of the whole state |
| `extract` | O(Σ degree) | recipes come from `tri`, not an O(n) scan per value |
| `repair_candidates` | O((\|stuck\| + \|removed\|) · \|U\|) | (stuck ⊕ avail) ∩ pairsums(avail) − U, using the counter with pairs that touch unrealized or removed values subtracted temporarily |
| `unlocks(w)` | O(\|stuck\| + Σ degree) | cascades through the triple index |

**The counter must be lazy.** Kept up to date eagerly, it made remove+restore 476 µs instead of 42 µs on fox_mu8. As a committed-state cache with `p2_sync()` only on accepted moves, speculative queries pay nothing.

### Correctness

`test_vcore.py` ran 300 iterations per case on all five seeds, each with cap None, the seed depth and the seed depth + 1. It checked:

- levels against `relax`, `_earliest` and the legacy fixpoint on random banks;
- stuck sets against `_closure_core` and `relax`;
- full invariant recomputation (`check()`);
- repair sets equal to legacy `_repair_candidates`, with and without the counter;
- extract output feasibility and peel 1-minimality against legacy `feasible_at`;
- every emitted circuit through `target.verify`: equivalent, gate_count == live count, depth matches, 0 dead gates.

Totals: 3,825 removes, 2,359 adds, 1,242 repair enumerations, 381 extract+peel runs and 866 verifies, all passing. In addition, the prototype loops run with `VERIFY_ALL=1` verified **14,486 accepted states** with `target.verify`, all equivalent.

### End-to-end prototype loops (`proto_search.py`, 10 s)

The loops use the same neighbourhoods as the current engines; they are not tuned new algorithms. The LNS loop reproduces legacy-lns semantics exactly (pool, costs, SA, noise-free tie-break). Its accept-rate and delta profile match legacy: 63% accepted vs 66%, and both drift to 93 gates on invmc88.

| loop | joltik | invmc88 | fox_mu8 | current engine at fox_mu8 |
|---|---|---|---|---|
| walk (remove 1–2, then exact repairs, score up to 16) | 3,824 it/s | 695 it/s | **119 it/s** | legacy-walk 0.4, v2-walk 3.0 (x298 / x40) |
| LNS (destroy 1–4 / cone, then extract) | 1,211 it/s | 751 it/s | **285 it/s** | legacy-lns 4.7 (x60); v2-lns 22 (40 ms beam) |
| with cap = seed depth | 4,158 / 1,189 | 701 / 750 | 119 / 285 | – |

The fox_mu8 walk found a **539-gate** circuit (seed 540) within 10 s, and the foxmu4 walk found 129 (seed 130). Both were verified.

What still costs time in the prototypes (`prof_proto.py`):

- **Walk:** `repair_candidates` takes 90%. Generating X plus subtracting touched pairs is about 2 ms on fox_mu8.
- **LNS:** `extract` 43%, `add` of extras 31% (an O(\|U\|) scan each), and the legacy pool sort 7%.

## 4. Pair-sum sets: when they are affordable (`bench_scaling.py`, 64 inputs)

| \|S\| | p2 entries | counter MB | set MB | build ms | sync µs per changed value | triple index MB / build ms |
|---|---|---|---|---|---|---|
| 100 | 12.8k | 0.96 | 0.89 | 2.3 | 34 | 0.12 / 1.7 |
| 300 | 63.5k | 4.5 | 4.0 | 11.3 | 76 | 0.32 / 5.8 |
| 540 | 177k | 15.7 | 13.7 | 37.9 | 123 | 0.49 / 13.6 |
| 800 | 365k | 31.8 | 27.8 | 84.1 | 224 | 0.78 / 27.6 |
| 1100 | 664k | 41.6 | 53.6 | 141.5 | 309 | 1.01 / 48.6 |

That is about 65–90 bytes per entry. At 1,100 values a lazily synced counter costs 42 MB per process (0.84 GB across 20 workers) and 0.3 ms per committed change.

**Recommendation:** enable the counter only for walk/repair engines, and only when \|U\| ≤ ~1,200. Never enable it for LNS, which doesn't need it. Building a fresh pair-sum set per repair call, as the legacy code does, costs 29.5 ms at 540 values and 154 ms at 1,100, so it is the wrong choice above roughly 150 values. At MixColumns size (\|stuck\| ≈ n/5) the counter only matches it.

## 5. Recommended core and API

```python
def earliest_scan(values, n, cap=None, parents=False) -> tuple[dict, dict | None, list]
    # one-shot exact levels for an arbitrary bank (replaces relax/_earliest/legacy fixpoint)

class Undo:  __slots__ = ('removed', 'tri', 'old', 'stuck')

class Circuit:
    def __init__(self, n, targets, values, cap=None, pairsums=False, lazy=True)
    # mutation (exact, incremental)
    def add(self, w, partners=None) -> bool
    def remove(self, D) -> Undo            # .stuck = newly unrealizable values (left in U)
    def restore(self, undo) -> None        # exact inverse; replaces deepcopy/journal
    def trim(self) -> None                 # drop witness-dead and stuck non-targets
    def discard_stuck(self) -> None
    def p2_sync(self) -> None              # call after accepting a move
    def enable_pairsums(self) -> None
    # search primitives
    def extract(self, cost: dict, rng, noise=0.0) -> set | None   # cost classes; inputs/chosen = 0
    def peel(self, rng, stop=None) -> None                         # 1-minimal
    def repair_candidates(self, stuck, forbid=()) -> list[int]     # complete, exact buildability
    def valid_repairs(self, stuck, forbid=()) -> list[int]         # == engines._repair_candidates
    def unlocks(self, w, stuck) -> bool
    # queries / output
    def ok(self) -> bool; def live(self) -> set; def depth(self) -> int
    def values(self) -> list; def key(self) -> frozenset
    def gates(self) -> tuple[list[list[int]], list[int]]           # level-ordered, live only
    def dag_sha256(self, matrix_sha256) -> str                     # == verify()['dag_sha256']
    def check(self) -> bool                                        # tests only
```

Engine-loop rules, each backed by a measurement above:

1. **No per-proposal replay or deepcopy.** A `Circuit` is valid by construction. Only call `target.verify` when emitting a candidate that is new on the frontier, and dedupe first with `key()`/`dag_sha256()`. This saves 1.3 ms replay + 0.4 ms gate deepcopy + 3.3 ms normalise/verify per fox_mu8 proposal.
2. **Speculate with `remove`/`add` and undo with `restore`/inverse operations.** Commit only accepted moves, and `p2_sync()` only then.
3. **Keep auxiliary state as plain bounded lists/sets owned by the engine,** serialised to JSON only at checkpoints. Use `list(pool)` (4 µs) instead of deepcopy (300 µs), and a bounded deque/set instead of re-sorting the pool every iteration (454 µs).
4. **Build v2 deadline reconstruct on `tri`:** alternatives x70 faster, and `earliest_scan` instead of `_earliest`. Make `complete_partial`'s repeated `_emit` incremental (it was 34% of v2-lns on invmc88).
5. **Check the clock every 64–256 operations, not per operation** (x4; it was 35% of inverse-bp). Do the same for v3's `_Budget.check`.

### Micro-optimisations (`bench_micro.py`, CPython 3.12)

These measurably help:

- one `rng.random()` per pair instead of two `randrange` calls: **x8.0**;
- bucket lists instead of `heapq` for small-integer levels: **x8.3** (124 vs 15 µs per 540 items; `_resolve`/`_lower` still use heaps, which is the next easy win);
- counter-gated stop checks: **x4.0**;
- a running minimum instead of `min()` over a list of tuples: **x2.5**;
- avoid `try/except KeyError` when misses are common: **3.3x slower** than `in` or `get`;
- `sorted()` inside a probe loop (legacy-window): 38% of that engine;
- algorithmic pruning: the popcount level bound is free, and filters should be ordered cheapest-and-most-selective first. Putting `unlocks` before the exact test made repair **13x slower**.

These do not matter on 3.12:

- binding `self.level.get` to a local: 0.93x;
- `in` vs `.get`: within noise;
- generator vs list comprehension: 1.08x;
- inlining a small helper: 1.15x;
- `map`/`isdisjoint` idioms: 0.8–0.9x, i.e. slower.

All of these were measured on 3.12 only, the one interpreter on the machine. Local binding typically matters more on 3.10, so keep it in the hottest loops.

**Not prototyped:** the depth-three annealer, pair-bank, BP constructors and the v3 constructor rewrite. For BP, the fix is the stop() gating plus the `pair_values` set built once per step, which is already the case.

## Files (not included)

- **Core:** `vcore.py`
- **Legacy ports and data:** `legacy_kernels.py` (generic-n ports of the reference kernels), `seeds.py`
- **Tests:** `test_vcore.py`
- **Benchmarks:** `bench_primitives.py` (+ `bench_primitives.out`), `bench_idioms.py`, `bench_scaling.py`, `bench_micro.py`, `bench_hash.py`, `bench_reconstruct.py`
- **run_chunk profiling:** `prof_engine.py`, `run_profiles.sh`, `hotspots.py`, `overheads.py`, `profiles/*.prof|*.txt`, `profiles_results.jsonl`
- **Prototype loops:** `proto_search.py`, `run_proto.sh`, `proto_results.txt`, `prof_proto.py`
- **Diagnostics:** `check_extract.py`, `debug_lns.py`, `prof_repair.py`
