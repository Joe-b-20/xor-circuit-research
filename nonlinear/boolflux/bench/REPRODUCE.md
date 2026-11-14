# Reproducing the BoolFlux method-and-performance study

All commands from the repository root on branch `boolflux-2026-11-13` (Python 3.11+, gcc; ABC only
for the external comparison). Outputs go wherever `OUT` points.

## Worked traces

```bash
# majority of 3: every accepted move, circuits before/after each improvement
python3 nonlinear/boolflux/cli.py run --target maj3 --model xag --objective a,cost --iters 3000 \
    --seeds 1 --jobs 1 --out OUT/maj3 --set tracemoves=OUT/maj3/moves.txt --set skip_noop=0
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

(`skip_noop=0` reproduces the kernel both traces were recorded with; the no-op filter, on by
default from commit 7ae20c8, changes the random trajectory.)

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

## Plans v3, v4 and the review-3 no-op A/B

All plans are in `bench/plans/` (`plan-v1.json` ... `plan-v4.json`, `plan-v5-noop-ab.json`).
`make_plan.py --tag v1|v2|v3` regenerates v1-v3 exactly; v4 (seeds 6-15 for the cells that were
unclear) and the v5 no-op A/B were written by hand from v1/v2 entries, so run them from the files:

```bash
python3 nonlinear/boolflux/bench/bench.py nonlinear/boolflux/bench/plans/plan-v4.json OUT/v4 --cpus 0,2,4,6,8,10,12,14
python3 nonlinear/boolflux/bench/bench.py nonlinear/boolflux/bench/plans/plan-v5-noop-ab.json OUT/v5 --cpus 0,17,18,19
```

The v1-v4 data were produced by the code of commits 19480fc / 1fc02c3 / 154ded8 (see REPORT.md);
running these plans with the current code uses workflow.py (review-3 fixes: feasibility-first
ranking with cap excess, rebuild-stage incumbents in the trajectory, structural no-op test).

## The same workflows from the normal CLI (`cli.py flow`)

`flow` runs workflow.search, the loop bench.py uses, one process per seed (optionally pinned):

```bash
# gate kernel only, wall budget
python3 nonlinear/boolflux/cli.py flow --target aes --model nist --start nonlinear/nist/aes-sbox/aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt \
    --objective cost,gd --cap-a 36 --cap-ad 4 --cap-gd 13 --config gate --seconds 120 --seeds 1-5 --cpus 0,2,4,6,8 --out OUT/gate
# full configuration (skeleton moves + rebuild + gate, 10 s rounds); add --adaptive for the v3 share
python3 nonlinear/boolflux/cli.py flow ... --config full --round-s 10 --adaptive --seconds 120 --out OUT/full
# rebuild only (skeleton kernel with 0 iterations), e.g. the depth repair that produced 124@GD14
python3 nonlinear/boolflux/cli.py flow --target aes --model nist --start nonlinear/nist/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt \
    --objective cost,gd --cap-gd 14 --config full --skel-set iters=0 --adaptive --seconds 120 --seeds 4 --out OUT/repair
# rebuild variants: --no-seeded (forms only) / --no-unseeded (seeded only); kernel ablations: --set mv.resub3=0 etc.
```

XOR-only models select the exact linear mode automatically in `run`, `pipe` and `flow`.
`summary.json` holds, per seed, the trajectory (every new feasible incumbent, including rebuild-stage
gains and the kernel's cleaned start), the rounds, overheads and peak RSS; `best.circ.txt` is the
best-ranked seed's circuit, verified by both verifiers (marked CAPS NOT MET if nothing met the caps).

## Plans v3, v4 and the review-3 no-op A/B

All plans are in `bench/plans/` (`plan-v1.json` ... `plan-v4.json`, `plan-v5-noop-ab.json`).
`make_plan.py --tag v1|v2|v3` regenerates v1-v3 exactly; v4 (seeds 6-15 for the cells that were
unclear) and the v5 no-op A/B were written by hand from v1/v2 entries, so run them from the files:

```bash
python3 nonlinear/boolflux/bench/bench.py nonlinear/boolflux/bench/plans/plan-v4.json OUT/v4 --cpus 0,2,4,6,8,10,12,14
python3 nonlinear/boolflux/bench/bench.py nonlinear/boolflux/bench/plans/plan-v5-noop-ab.json OUT/v5 --cpus 0,17,18,19
```

The v1-v4 data were produced by the code of commits 19480fc / 1fc02c3 / 154ded8 (see REPORT.md);
running these plans with the current code uses workflow.py (review-3 fixes: feasibility-first
ranking with cap excess, rebuild-stage incumbents in the trajectory, structural no-op test).

## The same workflows from the normal CLI (`cli.py flow`)

`flow` runs workflow.search, the loop bench.py uses, one process per seed (optionally pinned):

```bash
# gate kernel only, wall budget
python3 nonlinear/boolflux/cli.py flow --target aes --model nist --start nonlinear/nist/aes-sbox/aes-sbox-a36-ad4-g142-gd13-xx106-19.circ.txt \
    --objective cost,gd --cap-a 36 --cap-ad 4 --cap-gd 13 --config gate --seconds 120 --seeds 1-5 --cpus 0,2,4,6,8 --out OUT/gate
# full configuration (skeleton moves + rebuild + gate, 10 s rounds); add --adaptive for the v3 share
python3 nonlinear/boolflux/cli.py flow ... --config full --round-s 10 --adaptive --seconds 120 --out OUT/full
# rebuild only (skeleton kernel with 0 iterations), e.g. the depth repair that produced 124@GD14
python3 nonlinear/boolflux/cli.py flow --target aes --model nist --start nonlinear/nist/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt \
    --objective cost,gd --cap-gd 14 --config full --skel-set iters=0 --adaptive --seconds 120 --seeds 4 --out OUT/repair
# rebuild variants: --no-seeded (forms only) / --no-unseeded (seeded only); kernel ablations: --set mv.resub3=0 etc.
```

XOR-only models select the exact linear mode automatically in `run`, `pipe` and `flow`.
`summary.json` holds, per seed, the trajectory (every new feasible incumbent, including rebuild-stage
gains and the kernel's cleaned start), the rounds, overheads and peak RSS; `best.circ.txt` is the
best-ranked seed's circuit, verified by both verifiers (marked CAPS NOT MET if nothing met the caps).
