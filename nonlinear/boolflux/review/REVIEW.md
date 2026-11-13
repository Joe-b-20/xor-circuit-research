# BoolFlux correctness review (2026-11-13)

Scope: `kernel/bfx.c` (sha256 `53788d0c…`, the version with the cap penalty, i.e. after the
coordinator's mid-review change), `kernel/skel.c` (`0736146…`), `core.py`, `skeleton.py`,
`starts.py`, `targets.py`, `cli.py` (version with the all-sources `kernel_hash`),
`independent/verify.py`. Nothing outside `review/` was modified. Review binaries were compiled
from the sources into `review/` (`bfx`, `skel`, plus `bfx_asan`/`skel_asan` built with
`-fsanitize=address,undefined`).

**Bottom line.** I found no path that saves or reports a circuit that does not compute the
target: the kernel re-simulates every candidate, `state_refresh` and the final guard
re-simulate, `cli` re-checks with `core`, and `independent/verify.py` re-checks the written NCFF.
All ~1,700 randomized kernel runs and 89 published NIST circuits gave matching functions and
matching metrics in all three implementations. The findings are about the constraint guarantee,
the verification guarantee, and reproducibility.

## Findings

### Major

**M1. The cap penalty is not lexicographic, so a feasible state (and the best) can be replaced
by an infeasible one.** `bfx.c:109,157` (`VIOL_PENALTY 1e6`), acceptance `bfx.c:707,714`.
An infeasible candidate's objective is `base + 1e6*viol + 1e4*vsum`. The improvement branch
(`bobj < mcur.obj`) and the best update (`mcur.obj < mbest.obj`) do not check feasibility, so a
move that saves more than about 1e6 objective units while breaking a cap is accepted as an
improvement and becomes `best`. Depth caps are safe in practice, because candidates are pruned
exactly by required level and in a feasible state `req = max(RGc,LGc) = RGc`. The AND cap
`cap.a` is not pruned and depends only on the penalty. Reproduction (feasible start, infeasible
result):

```
# review/tmp/pen.start                  # review/tmp/pen.cfg
n 3 / m 1 / g 3                          in pen.start  out pen.out  iters 50  seconds 100  seed 1
6 0 1      (t = x0 ^ x1)                 cost.6 3e7  cost.8 1e7  cost.7 1e7  cap.a 2  w.cost 1
8 0 2      (u = x0 & x2)                 T0 0  stall_it 1000  Tperiod_it 100
8 3 4      (o = t & u)
o 5
-> start  cost 5e7 A 2 feas 1
-> final  cost 3e7 A 3 obj 3.1e7 feas 0     (t replaced by NAND(x1,x2), valid on t's care set)
```

With the stock unit-cost models one move saves at most a few units, so this does not happen in
the current campaigns: 0 occurrences in 1,000+ fuzz cases with costs 0.5..2, or with costs of 1e5
and `cap.a = A0`. It does happen with large per-gate costs, as in the reproduction above, or with
a scaled `w.cost`. `cli run` then exits with "CAPS NOT MET", and `pipe` drops the job.
Consequence: the kernel's claim that it never leaves the feasible set once there is false.
*Fix:* compare `(viol, vsum, obj)` lexicographically, or require `m.feas >= mcur.feas` in the
improvement branch too and never let an infeasible state replace a feasible `best`. A penalty
derived from the data (larger than the start objective plus `max_excess`) would also work.

**M2. Caps and metrics are checked by only one implementation.** `cli.py:75-82, 248-262`
(run), `cli.py:393-405` (pipe). The independent verifier runs without the caps, although
`verify.py` supports `--max-GD/--max-AD/--max-A`. `independent_metrics` is stored in
`summary.json` but never compared with `core`'s metrics. So whether the caps hold, and the
reported G/A/GD/AD/cost, rest on `core.Circuit.metrics` alone. That falls short of the "two
independent verifiers" guarantee for constraints. No disagreement was found: the metrics agreed
on all 89 NIST circuits (`review/check_nist.py`) and on every fuzz case.
*Fix:* pass `--max-GD/--max-AD/--max-A` for the configured caps to `verify.py`, and fail if
`{G, A, GD, AD, cost}` differ between `core` and the independent verifier.

**M3. Reproducibility: the recorded hash does not pin the binary that ran.**
`cli.py:36-49`. All `cli` processes share one `kernel/bfx` and `kernel/skel`, and any `cli`
invocation rebuilds them in place when the source is newer (mtime test). A multi-round
`run`/`pipe` that is running when someone edits `bfx.c` (this happened during this review, while
the depth-2 and small-1 campaigns were running) launches its later rounds with the new binary. Its
`summary.json` still holds the hash computed at its start. The hash is also of uncommitted
working-tree files, and no copy of them is kept, so a recorded `kernel_sha256_12` cannot later be
mapped to source. Concurrent rebuilds by two `cli` processes can also race (gcc writing a
binary while another process execs it).
*Fix:* compile into the run directory, or copy the binary there (or into a content-addressed
cache) and run that copy. Store the sources (or commit + `git diff`) and the binary hash with the
run. Minor: the NCFF comment says "kernel bfx.c sha256", but the value now hashes 7 files.

### Minor

- **m1. Weighted gate depth diverges between kernel and Python.** `gdw.<op>` (settable via
  `--set`, `bfx.c:260`) changes the kernel's GD and its `cap.gd` check, but `core`, `cli` and
  `verify.py` always count 1 per gate. The kernel's `feas` can then disagree with `cli`'s. Caught
  by the final `feasible` check. *Fix:* forbid `gdw.*` in `cli`, or pass it everywhere.
- **m2. A valid start with an internal constant gate is rejected.** `bfx.c:206,643`. For
  example `27: NOR(x3,g24)`, `28: NOR(x3,g24)`, `43: XNOR(27,28)` (=1), from fuzz case
  `review/tmp/c23_8.start`, gives exit 2 "start circuit cannot be cleaned". This happens because
  strash merges 27/28 and `f(x,x)` is constant. It fails loudly and never happens with ANF or NIST
  starts. *Fix:* propagate constants, or say why in the error.
- **m3. `dmax 0` crashes.** It makes `ndiv = 0`, and then `DIV[rndint(ndiv)]` (`bfx.c:506`)
  divides by zero (SIGFPE). *Fix:* clamp `dmax >= N`.
- **m4. Objective weights are lexicographic only within limits.** `cli.py:111` gives key i
  weight 1e-4i. A 4th key gets weight 1e-12, which is below the kernel's 1e-9 tolerance
  (`bfx.c:703,707`), so it is silently ignored. The order is also only strict while each lower
  key's total is under 1e4 relative to the key above. That holds today (AES ANF start G = 1247).
  *Fix:* reject more than 3 keys, or compare tuples.
- **m5. An infeasible best is still written as `best.circ.txt`.** In `run`, when the caps are
  not met, the file is written with a comment naming the caps (`cli.py:241-246`). The tally shows
  the real GD, but someone who reads only the file can take it as a capped result. Example:
  `~/xs-campaigns/2026-11-13-boolflux/depth-2/gd13-from-...-gd14-.../best.circ.txt` (GD 14 under
  "caps {'GD': 13}"). *Fix:* write it as `best-INFEASIBLE.circ.txt`, or add a "CAPS NOT MET"
  comment.
- **m6. A `--model PATH` model is verified against the wrong file.** `verify_file` calls
  `Model.load(model.name)` and passes `models/<name>.json` to the independent verifier
  (`cli.py:76,81`). A model given by path whose name is not a stock file crashes after the
  search, before `summary.json` is written. One whose name matches a stock model is verified
  against the stock library. *Fix:* pass the model file path through.
- **m7. `cli verify` crashes on gates outside the model.** `core.Circuit.metrics` raises
  `KeyError` (`core.py:93`), for example on a file with ORN checked under `xag`. The exit code
  is nonzero, but the remaining files are not checked. *Fix:* use `model.cost.get(op)`; the
  library check already reports the problem.
- **m8. The verification claims in `DESIGN.md` are wider than what runs.**
  (a) Only `best.circ.txt` is checked by both verifiers. Per-job `*.best.bfx`, pool circuits and
  skeleton syntheses are checked by `core` only.
  (b) For non-AES targets the independent verifier gets its table from `targets.py`
  (`cli.py:59-63`), so the target definition is shared. Only evaluation and metrics are
  independent there.
- **m9. Runs that stop on the time cap are not flagged.** A kernel stopped by `seconds` is
  not reproducible, but `cli` does not compare `final.iters` with `--iters`. 0 of 950 campaign
  runs so far stopped this way. *Fix:* mark such runs in `summary.json`.
- **m10. `skeleton.synthesize` assumes AND and XOR are allowed.** It emits AND and XOR without
  checking the library (`skeleton.py:163,169`). With no NOT it uses NAND(x,x), which adds to A
  and AD (`:120`). It raises when the library has XNOR but no NOT (`:119`). An exception in a
  `pipe` job aborts the whole `pipe` (ThreadPool `map`). None of the stock models is affected.
- **m11. Config values cannot contain spaces.** `fscanf("%s %s")` (`bfx.c:251`, `skel.c`) means
  an `--out` path with a space is misparsed, and the kernel fails with "unknown key".

## Review of the cap-handling change (coordinator's questions)

- *Can a feasible state now be replaced by an infeasible one?* Not through depth caps.
  Required-level pruning is exact, and in a feasible state `RGc[s] >= LGc[s]`, so `req` is
  unchanged. Not through neutral moves (their objective must be equal) or uphill moves (they need
  `m.feas >= mcur.feas`). Restarts go to `best`. The one way is M1: an improvement that outweighs
  the 1e6 penalty, in practice only via `cap.a` (or depth caps with fraig, which never deepens).
- *Can the reported best be infeasible when the start was feasible?* Only through M1. With
  unit costs it cannot happen: 0 occurrences in all fuzz runs.
- The repair path works: 300+ fuzz cases started outside their caps, and about 75 % were
  repaired in 200 to 3,000 iterations. Every result reported `feas 1` exactly when the caps held,
  as checked by my own metric code. The `vsum`/height computation is correct for unary NOT
  (b == a). `eval_cand` returning 1 for infeasible candidates is safe, because infeasible
  candidates only win through the penalty-ordered objective. `cli run` now ranks infeasible jobs
  last, since kernel objectives include the penalty, and exits nonzero on CAPS NOT MET.

## What was tested and found correct

- **`review/fuzz_bfx.py`** (about 1,700 gate-kernel cases over several seeds, n = 1..10, 4..150
  gates, random library subsets of all 9 ops, random costs, caps at or below the start's metrics,
  outputs that are inputs or duplicated, every knob randomized, 100 cases under ASan/UBSan):
  - the output computes the start's function;
  - every op is in the library, operands are topological, and NOT has b == a;
  - the kernel's reported cost/G/A/GD/AD equal recomputed values, and its `feas` is exact;
  - from a feasible start the result is feasible and its objective is not worse than the start;
  - the same config twice gives byte-identical output;
  - the NCFF round trip (`core.write_ncff`, then `verify.py --fn --model`) passes;
  - core, independent and own metrics agree, with no sanitizer reports.

  The only failures were m2 (rejected start).
- **`review/fuzz_skel.py`** (490 skeleton cases, 40 under ASan):
  - AND forms only use earlier positions and have no constant operands;
  - the kernel's Y forms reproduce the targets exactly, and the reported K is correct;
  - the `cap.ad` respected;
  - the same config twice gives byte-identical output;
  - `skeleton.synthesize` for xag/nist/gc/bgc computes the target, stays in the library, respects
    `cap.ad`, and never has more ANDs than the skeleton.
- **Reading the code** confirmed these are correct:
  - op encodings (`apply`, `op_nl`, `op_sym`, ANDN 4 / ORN 13 and their mirrored forms 2/11);
  - the care-set computation;
  - level-1/2/3 candidate construction, including the lane-wise target for a nonlinear root and
    both orientations;
  - hash tables (exact compare after the hash, load ≤ 0.5, PCAP vs PHT size);
  - rebuild (iterative DFS cycle detection, stack bound, `f(x,x)` folding, symmetric
    canonicalisation);
  - fraig (exact equality, never deeper);
  - MFFC, budgets, and buffer sizes (CARE[1024] at W = 1024, order[1024] vs cand_cap);
  - in skel: elimination invariant (distinct pivots, rows zero at earlier pivots),
    dependent-AND substitution, `mdel` renumbering, `remap_after_delete` order (higher deleted
    first), leaf detection, AD, and `restore()` re-analysing;
  - `nl_decompose`, `extract`, and the hex word layout (`write_skel`/`read_skel`).
- **`review/check_nist.py`:**
  - the AES tables in `targets.py` and `verify.py` are identical;
  - all 89 NIST circuits pass `core` and the independent verifier;
  - G/A/GD/AD/cost agree, including XNOR-0 NOT and BUF handling;
  - the `write_ncff` round trip preserves both function and metrics.
- **`cli.py`:**
  - `run` (present/gc, 2 rounds) and `pipe` (chi3/nist, 2 rounds) were each run twice;
    `best.circ.txt` was identical apart from the `--out` path in the comment;
  - `cli verify` on a tampered file gives FAIL with exit 1 (core=False, indep=False);
  - `verify_independent` maps unparseable output and nonzero exit codes to not-ok;
  - the independent verifier's own 36 unit tests pass.

## Resolution (coordinator, 2026-11-13)

| Finding | Status |
|---|---|
| M1 penalty not lexicographic | fixed in bfx.c: an improvement, a neutral move and a new best must not be less feasible than the current state / best; review/tmp/pen.cfg now ends feasible (A=2) |
| M2 caps and metrics only checked by core | fixed in cli.verify_file: caps go to independent/verify.py as --max-GD/AD/A, and its G, A, GD, AD, cost and counts must equal core\x27s or independent_ok is False; S-box targets go to it as the spec table (--table benchmarks/sboxes.json) |
| M3 hash does not pin the binary | fixed: every run/pipe copies its sources to OUT/src, builds private OUT/bin/{bfx,skel}, and records the hash of that snapshot (code_sha256_12) |
| m3 dmax 0 | fixed (guard) |
| m4 more than three objective keys | now an error |
| m6 --model PATH | verify_file uses the given file |
| m7 verify KeyError | fixed (cost of an unknown gate is NaN, library check fails) |
| m9 time cap | each job records time_capped |
| m1, m2, m10, m11 | open, documented: gdw.* is not used by any campaign; constant gates, non-AND/XOR libraries and paths with spaces are rejected loudly |
| m5 infeasible best written | run exits nonzero with CAPS NOT MET; pipe never selects an infeasible job |
| m8 DESIGN claims | DESIGN.md Verification section reworded |
