# Foundation restart: implementation notes (2026-11-09)

A new, opt-in restart source for XORFlux v8. It is off by default (`restart.w_foundation = 0`),
and with defaults the engine follows exactly the trajectory it followed before (tested, below).
Not committed; working tree of branch `phase-2026-11-09`.

The level-1 set of a circuit is its set of weight-2 values (XORs of two inputs). Evidence for
the mechanism: `~/xs-campaigns/2026-11-02-why/SYNTHESIS.md` (Q1, proposal 1a) and
`foundations/REPORT.md` sections 1, 3 and 5. On MixColumns at cap 4, holding the 89@4 level-1 set
fixed and rebuilding everything above it re-found 89@4 in 9 of 13 runs. The walk changes level 1
one pair at a time and does not cross between foundations. The prototype was a monkeypatched
copy of the engine (`foundations/complete.py`, `l1root.py`); this is the in-engine version.

## Mechanism

1. **Choosing the source.** `"foundation"` is the fifth member of `restart.SOURCES`, and
   `RestartController.order` treats it like the other four. It is *available* when a root
   constructor module exists and the worker has a worker best or a distinct archive elite. It is
   in `OPT_IN`: with weight 0 it is never tried, not even in the last-resort list used when every
   weighted source is unavailable. The engine adds `avail["foundation"]` only when the weight is
   positive. At weight 0, `order()` draws exactly what it drew before (tested).
2. **Donor** (`Engine._foundation_source`). With probability `restart.foundation.elite_p` the
   donor is a distinct archive elite, chosen with the existing `archive.sample_diverse`.
   Otherwise it is the worker best. If the chosen kind is missing, the other kind is used.
3. **Allowed set A.** L is the donor's weight-2 values; weight-2 output rows always belong. Two
   perturbations are applied:
   - `swap_pairs = k`: remove k random members of L and add k random *useful* pairs that are
     not in L. A useful pair is two inputs that occur together in some output row, the same
     list as `useful` in `complete.py`.
   - `drop_pairs = d`: remove d further members with no replacement.

   Weight-2 rows are never removed. The perturbation does not depend on the map (no rotation
   orbits).
4. **Restricted root** (`construct.build_restricted_root`). Constructors from
   `restart.foundation.constructors` (default `["l1tree", "paar", "naive"]`) are tried in order,
   and the first one that completes wins:
   - `l1tree` ports `l1root.build_root`. It builds each row separately as a tree of depth at most
     cap over pairs of A (level 1) and single inputs (level 0), and never creates a forbidden
     intermediate. It first tries a random maximal matching. If that fails, it tries a cheap
     cancellation representation with at most 4 pairs, with 200 tries per row.
   - Any `ROOTS` constructor (naive, paar, bp, anneal3) runs unchanged. Its recipes whose output
     is a forbidden weight-2 value are dropped before `emit`, so it completes only if the
     remaining recipes still reach every row.

   Every root is checked by `verify_gates`, and its level-1 set is asserted to be within A. If
   no constructor completes, a `foundation_failed` event is logged, the source returns None, and
   the controller moves on to the next source, as it does for any other source that fails.
5. **Pinned phase.**
   - `ValueSet.restrict_level1(A)`: `add` refuses (returns False) a weight-2 value outside A,
     and `repair_candidates` filters such values out, so `valid_repairs` and the walk never see
     them. This is the same semantics as the `_add` and `repair_candidates` patches in
     `complete.py`, but as a per-state attribute (`l1allow`, a new slot), not a monkeypatch.
     Members of A may still be removed and re-added.
   - The engine keeps the pin in `Engine._pin`. `_make_state` applies the restriction to every
     state it builds while pinned: improvement rebuilds, polish rebuilds, canonical checkpoints
     and resume.
   - `_restart` builds candidate states without the old pin. It ends a running pin
     (`foundation_unpin`, reason `restart`) before it starts the new chain.
   - The checkpoint carries `foundation_pin` only while a pin is active, so all other
     checkpoints are unchanged.
   - Dossiers written while pinned carry `replay.level1_allowed`, and `replay_dossier` puts the
     rebuilt state under the same restriction.
6. **Unpin.** At the first periodic check (every `engine.periodic_every` = 64 proposals) after
   `pin_proposals` proposals, the restriction is lifted. Proposal counts make this replayable.
   It costs nothing in `step()`. The chain then continues as an ordinary chain. Acceptance,
   moves, stall timers and records are unchanged, and the stall timers can cut a pinned chain
   like any other chain.

## Knobs (`config explain restart`)

| knob | default | meaning |
|---|---|---|
| `restart.w_foundation` | 0.0 | weight of the source (0: never used) |
| `restart.foundation.elite_p` | 0.5 | probability that the donor is an archive elite instead of the worker best |
| `restart.foundation.swap_pairs` | 0 | number of level-1 pairs replaced by random useful pairs |
| `restart.foundation.drop_pairs` | 0 | number of level-1 pairs removed with no replacement |
| `restart.foundation.pin_proposals` | 200,000 | length of the pinned phase, in proposals |
| `restart.foundation.constructors` | `["l1tree","paar","naive"]` | restricted constructors, tried in order |

On MixColumns at cap 4, 200,000 proposals is about 300 s at the historical ~700 proposals/s.
That is the length of the prototype's completion runs.

## Events (also in `telemetry/schema.md`)

- **`restart`** with `source = "foundation"`. Its `root` holds `donor_kind` (`best`/`elite`),
  `donor` (point; seq/origin for an elite), `level1` (the donor's set), `level1_size`,
  `swapped_out`, `swapped_in`, `dropped`, `allowed_size`, `pin_proposals`, `constructor`
  (the one that completed), `tried`, `seed`, `build_s`, and `improvement` (the donor's
  improvement id, used as the lineage parent).
- **`foundation_unpin`** has these fields:
  - `reason` (`proposals` or `restart`), `engine_chain`, `proposals`, `pin_proposals`;
  - `chain_best`, `chain`, `allowed_size`, `level1_size`;
  - `level1_equals_allowed` (whether the current state's level-1 set equals A);
  - `level1_missing` (members of A it dropped);
  - `best_level1_equals_allowed`.
- **`foundation_failed`** has `reason`, `constructors` and the donor and perturbation fields.

## Tests (`search/xorflux/tests/test_engine_foundation.py`, 13 tests, about 15 s)

- **(a) Default path.** `DefaultPathTest` runs 1,500 proposals on small-scale-aes at cap 4 with
  seed 11, default knobs, `stall_proposals` 150 (3 restarts), structural moves off, and
  `scheduler.cost = work`, with the moves passed in their fresh-process order (see Limitations).
  It hashes every StepResult, the final values and the restart
  sources. The hash `2fd16afc…442e1d` was computed on the unmodified code: on the untouched tree
  (`git stash`) and on the modified tree, with identical results. During that run the test also
  checks four things:
  - `ValueSet.restrict_level1` is never called;
  - `Engine._foundation_source` is never called (it is patched to raise);
  - no state has `l1allow` set;
  - the checkpoint has no `foundation_pin`.

  `ControllerTest.test_default_order_draws_are_unchanged` checks that `order()` returns the same
  lists and leaves the RNG in the same state with and without an available `foundation` entry.
- **(b) The restriction.** `ValueSetRestrictionTest` checks:
  - adds outside A are refused;
  - 300 random journaled remove/add/rollback/commit edits never leave A, and
    `repair_candidates` never offers a forbidden pair;
  - `check()` passes, including a new level-1 invariant;
  - members of A can be dropped and re-added;
  - restricting a state that already violates A raises an error;
  - lifting the restriction re-enables the adds.
- **(c) The restricted root builder.** `RestrictedRootTest` checks:
  - `l1tree` gives verified roots within A on small-scale-aes at cap 4 (5 seeds);
  - naive completes when every useful pair is allowed;
  - naive and l1tree both fail for empty A, which raises ValueError (the engine turns that into
    None);
  - the fallback order is followed;
  - an unknown constructor name raises.
- **(d) A foundation restart on the real stack** (`FoundationRestartTest`, small-scale-aes, cap
  4, pin 300) checks:
  - the restart event's fields;
  - A = L − swapped − dropped + swapped-in;
  - for every proposal of the pin, level-1 ⊆ A and the state carries the restriction;
  - the unpin comes at proposals 300–363 (the periodic check), with one `foundation_unpin`
    (reason `proposals`), after which the restriction is lifted;
  - pinned dossiers that can be replayed do replay;
  - a restart during the pin ends it (reason `restart`) and re-pins the new chain;
  - checkpoint/resume during a pin keeps it and continues step for step;
  - when no constructor completes, `foundation_failed` is logged and the restart falls back to
    `best`.
- **(e) The controller.** `ControllerTest` checks that `foundation` is in `order()` only when
  `w_foundation > 0` and it is available, and that it is absent from the all-zero-weights
  last-resort list.

## Results

- **Full suite**, modified tree, final run: `Ran 371 tests in 203.473s`, `OK (skipped=1)`. That
  is 358 + 13 new tests. The skip is the slow depth-3 control that needs `XORFLUX_SLOW=1`.
  - Baseline before the change: `Ran 358 tests in 339.614s`, `FAILED (failures=1, skipped=1)`.
    That run overlapped my first edits and one extra engine run, and the name of the failing
    test was not captured.
  - An intermediate run of the modified tree failed `test_per_step_overhead` (81.7 µs against
    its 60 µs limit, under load average above 200). That test runs on fake states, which never
    use the restriction, and it passed in the two later runs, so load is the likely cause of the
    baseline failure too, but this is not verified.
- **Smoke, foundation on** (one worker, nice 5, small-scale-aes cap 4, 40 s,
  `--set restart.w_foundation=1.0 --set restart.stall_proposals=2000 --set
  restart.stall_seconds=0 --set restart.foundation.pin_proposals=1500`):
  - At proposal 4,416 a foundation restart (donor `best`, |L| = 13) built a 56@4 `l1tree` root in
    0.02 s.
  - The pinned chain reached 46@4 within the pin.
  - `foundation_unpin` came after 1,536 proposals (reason `proposals`). The current level-1 set
    had shrunk from 13 to 9, so it no longer equals A.
  - No errors. The next restart drew `fresh` (w_fresh 0.6 against w_foundation 1.0).
  - With the requested `stall_proposals=20000` no restart happened in 40 s (13 k proposals on
    the loaded machine), hence 2000.
- **Smoke, default path** (the same command without the foundation knobs), modified tree against
  untouched tree (`git stash`):
  - modified: 10,372 proposals in 40.9 s, first restart at proposal 4,416 (fresh/naive), 2
    restarts, 7 improvements;
  - untouched: first restart at 4,544 (fresh/bp), 2 restarts, 7 improvements;
  - both reached best 45@3 or 45@4.

  Default scheduling charges measured seconds, so these runs are not deterministic. They agree
  as far as such runs can, and the deterministic hash test is the real check.
  - Note: a default `fresh` restart that drew `anneal3` at cap 4 spent 25–43 s building its root
    in these runs. That is existing behaviour, not part of this change, and it pushed two smoke
    runs past 60 s of wall time.

## Overhead of the restriction check on the unpinned path

An unrestricted state pays one attribute load and an `is not None` test per `add` and per
`repair_candidates`. `step()` is unchanged, and the unpin test sits in `_periodic`.

All numbers below are CPU time with nice 5, measured while the 20-thread experiment ran.

| measure | before | after |
|---|---|---|
| `add` of a value already in U (cheapest add; invmc88, min of 7) | 190.3 ns | 201.4 ns (+11 ns) |
| `add` + rollback of 200 new values (invmc88) | 5,515 µs | 5,536 µs (+0.4%, noise level) |
| deterministic 1,500-proposal engine run (min of 3; see (a)) | 2.547 s | 2.541 s |

The first two rows come from `bench_guard.py`, which loads both kernels in one process. The
third comes from `bench_pin.py` macro. Both scripts are in the session scratchpad and are not
committed. Per real add (~27 µs) the guard costs about 0.04%. Wall-clock micro timings of the
same operations varied 5–8x between repeats under the load, so they are not reported.

## Limitations and open points

- **The generic constructors almost never complete under the restriction.** Each probe rebuilt
  with a different seed over its donor's own level-1 set (3 donors per map):
  - on MixColumns cap 4: paar, naive and bp failed 3 of 3; l1tree built 110–112@4 at once;
  - on small-scale-aes cap 4: paar, naive and bp failed 3 of 3; l1tree built 52@3–4.

  They are kept in the list only as a cheap fallback (paar and naive fail in milliseconds; bp
  takes about 1 s, so it is not in the default list). In practice `l1tree` is the constructor.
- `l1tree` caps its cancellation fallback at 4 pairs. The prototype went to 6 in the second half
  of the tries, and 6 was the slow part: C(26,6) = 230 k combinations per row. Sets with many
  drops can therefore fail where the prototype might not have. The failure is logged and falls
  back to the next source.
- **Pin semantics.** This is the prototype's "free" variant: the chain may use any subset of A.
  The "pinned" variant that forces every pair of A (A appended to the target rows) is not
  implemented. In the 2026-11-02 runs both variants reached 89 on the 89's set: free 2 of 3,
  pinned 6 of 10 (300 s) and 3 of 3 with restarts.
- **Interaction with the other timers.**
  - The stall timers keep running during the pin, so `stall_proposals` or `stall_seconds`
    shorter than the pin cut it, with reason `restart`.
  - The new chain starts well above the worker best (for example 56 against 45), so it is not
    an incumbent and also falls under `root_seconds` (3,600 s by default, longer than a typical
    pin).
- **Not tested on the target problem.** No MixColumns or InvMixColumns campaign was run here.
  The evidence says the idea is MixColumns-specific until shown otherwise, and it is open
  whether drawing donors from the worker's own best and archive finds new foundations or only
  re-completes the known ones. With `swap_pairs = 0` the source re-completes the donor's own
  foundation. With swaps it explores nearby sets, where the prototype found +3 gates per
  swapped pair within 300 s.
- **Pre-existing problem found while testing: the move order depends on import order.** This
  is not part of this change. `moves.base.load_all()` returns `REGISTRY`, which is filled in
  module import order:
  - in a fresh process the order is `walk.remove1, walk.expand, lns.rebuild, depth.repair, ...`;
  - after `unittest discover` has imported every test module, it is `depth.repair, lns.rebuild,
    walk.remove1, ...`.

  The scheduler indexes moves by that order, so the same seed gives a different trajectory
  depending on what was imported first. The default-path digest was `2fd16afc…` standalone but
  `9b812cea…` inside the full suite, on the old code as well as on the new. The test now passes
  its moves in the fresh-process order (`FRESH_MOVE_ORDER`). Campaign workers import in a fixed
  order, so they are stable. A canonical, sorted registry order would remove the problem, but
  it would change every default trajectory, so it was not done here.
- **Lineage.** The lineage parent of a foundation chain is the donor's
  improvement id when one is known (`root.improvement`). A foundation chain is not a copy of the
  donor, so a lineage reader should treat it as a rebuild.
