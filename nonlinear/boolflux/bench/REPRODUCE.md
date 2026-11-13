# Reproducing the BoolFlux method-and-performance study

All commands from the repository root on branch `boolflux-2026-11-13` (Python 3.11+, gcc; ABC only
for the external comparison). Outputs go wherever `OUT` points.

## Worked traces

```bash
# majority of 3: every accepted move, circuits before/after each improvement
python3 nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost --iters 3000 \
    --seeds 1 --jobs 1 --out OUT/maj3 --set tracemoves=OUT/maj3/moves.txt
python3 nonlinear/boolflux/bench/show_trace.py OUT/maj3/moves.txt

# AES: deterministic replay of a recorded job (NIST a36-ad4-g142-gd13 -> 131, seed 3; the job's config
# is the one written by nist_frontier.sh, i.e. cli.py run ... --cap-a 36 --cap-ad 4 --cap-gd 13
# --iters 100000 --seeds 1-8; seed 3 reaches 131 at iteration 57644)
python3 nonlinear/boolflux/cli.py run --target aes --model nist \
    --start nonlinear/nist/aes-sbox/aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt --objective cost,gd \
    --cap-a 36 --cap-ad 4 --cap-gd 13 --iters 57644 --seeds 3 --jobs 1 --out OUT/aes142 \
    --set tracemoves=OUT/aes142/moves.txt --set skip_noop=0
python3 nonlinear/boolflux/bench/show_trace.py OUT/aes142/moves.txt
```

(`skip_noop=0` reproduces the kernel the run was recorded with; the no-op filter changes the
random trajectory.)

## Rebuild penalty

```bash
python3 nonlinear/boolflux/bench/rebuild_penalty.py OUT/rebuild_penalty.json
```

## Benchmark campaign

```bash
python3 nonlinear/boolflux/bench/make_plan.py OUT/plan-v1.json --tag v1   # kernel as before the fix
python3 nonlinear/boolflux/bench/make_plan.py OUT/plan-v2.json --tag v2   # no-op filter, fast starts
python3 nonlinear/boolflux/bench/bench.py OUT/plan-v1.json OUT/v1 --cpus 0,2,4,6,8,10,12,14
python3 nonlinear/boolflux/bench/bench.py OUT/plan-v2.json OUT/v2 --cpus 0,2,4,6,8,10,12,14
python3 nonlinear/boolflux/bench/analyze.py OUT/v1 > OUT/tables-v1.md
python3 nonlinear/boolflux/bench/analyze.py OUT/v2 > OUT/tables-v2.md
```

Each CPU gets one worker process pinned with `sched_setaffinity` (all of a run's work, Python
included, stays on its CPU); a linear task runs XORFlux and BoolFlux back to back on the same CPU.
Runs are time-budgeted (wall clock), so they are not bit-reproducible; the seeds (1-5) and budgets
were fixed in the plan before running. Peak RSS is `/usr/bin/time -v` of the search processes.

## External comparator (Berkeley ABC)

See `bench/abc/ABC.md` (ABC commit `0587b343c45b8bd6dddd866fe4ac8e55e9cbda05`, scripts in
`bench/abc/scripts/`, unit-area genlibs in `bench/abc/genlib/`).

## Review bundle

```bash
bash nonlinear/boolflux/bench/make_bundle.sh OUT   # OUT/boolflux-review-bundle/ and .tar.gz
```
