# Reproducing a circuit

Every circuit here is verified independently ([Check](README.md#check)). Re-running the search
that found it is a separate matter: most BoolFlux runs had a time budget, and many ran on code
with uncommitted changes. The four examples below were replayed on 2026-11-16 from a public
commit, on one or two hardware threads of the laptop in [SEARCH-TIME.md](SEARCH-TIME.md#hardware)
while other work used its other threads. For every other S-box circuit, `found.json` in its logs
says what was recorded: `command` and `seed` with their sources, and `code.exact_code`, the public
commit that has the code of the run, or that it is unknown.

| Example | Circuits (A/AD/G/GD) | Method | Commit | Time | Outcome |
|---|---|---|---|---|---|
| [1](#1-gate-kernel-iteration-budget) | 33/4/110/18, 33/4/108/19, 32/5/108/20 | gate kernel, `cli.py run` | `e5bab59` | 3.5 min each | the same file, byte for byte, except the output path in its `% command:` line |
| [2](#2-conjugation-and-staged-pull) | 34/4/122/14 | conjugation and staged pull | `d72204c` | 10 min | the same gate list |
| [3](#3-re-basing) | 35/3/165/13 | re-basing | `d72204c` | 15 min | the same gate list |
| [4](#4-hub-depth-pull) | 35/3/155/15 | hub depth pull | `8922cac` | 1.5 min | the same file, byte for byte |

Examples 2–4 stop on a time budget, not an iteration count. Their kernels follow the same
trajectory for the same seed; the replays reached the circuit later than the original runs
(75 s instead of 39 s, 236 s instead of 208 s, 20 s instead of 13 s) and still within the budget.
A slower or busier machine can run out of time first and end on a worse circuit; in example 3 the
last stage, which the budget cuts short, ended on 35/3/167/13 instead of the original's 166.

## Set-up

Linux (we used WSL2, Ubuntu 24.04), Python 3.12, gcc 13 and git; `taskset` (util-linux) pins
a run to a CPU, and can be dropped. The kernels are compiled on first use. Each example runs in
a worktree of the commit it names; the start files come from the logs in the current tree:

```bash
git clone https://github.com/Joe-b-20/xor-circuit-research xcr && cd xcr && X=$PWD
L=$X/circuits/aes-sbox/logs                       # published logs
gates() { for f; do grep -E '^(AND|XOR|XNOR|NOT) ' "$f" | sha256sum; done; }   # gate-list digests
```

Paths inside the old commits are the ones before the restructure of 2026-11-16 (`nonlinear/...`,
see [Conventions](README.md#conventions)).

## 1. Gate kernel, iteration budget

The three circuits labelled deterministic. Each run's own code snapshot (7 files, code
`b0e56ecb18fe`) is identical to commit `e5bab59`; every job ends on its 100,000-iteration
budget, so the result does not depend on the machine.

```bash
git -C $X worktree add $X-e5bab59 e5bab59 && cd $X-e5bab59
taskset -c 0,1 python3 nonlinear/boolflux/cli.py run --target aes --model nist \
  --start nonlinear/nist/aes-sbox/aes-sbox-a33-ad4-g110-gd20-xx77-4.circ.txt --objective cost,gd \
  --cap-a 33 --cap-ad 4 --cap-gd 20 --iters 100000 --seeds 1-8 --jobs 8 --out OUT/g110
grep -v '% command:' OUT/g110/best.circ.txt | sha256sum
```

| Start (`--start`) | Caps `--cap-a --cap-ad --cap-gd` | Result | `sha256` without the `% command:` line |
|---|---|---|---|
| `aes-sbox-a33-ad4-g110-gd20-xx77-4` | 33 4 20 | [33/4/110/18](aes-sbox/aes-sbox-a33-ad4-g110-gd18-xx77-26.circ.txt) | `bae80c6fd21db8c7582a0c7b60b3c723c30399c8ef3684e6a52bca8215da98f3` |
| `aes-sbox-a33-ad4-g108-gd20-xx75-5` | 33 4 20 | [33/4/108/19](aes-sbox/aes-sbox-a33-ad4-g108-gd19-xx75-22.circ.txt) | `6e5ddeef56d02ca5fb7cbc4dd05a801bb96e5fcb5533243e635990d1aefa1b73` |
| `aes-sbox-a32-ad5-g109-gd20-xx77-4` | 32 5 20 | [32/5/108/20](aes-sbox/aes-sbox-a32-ad5-g108-gd20-xx76-35.circ.txt) | `dad7dd236509ba8555b3c0a2ce5e149c894a7298b467527768af3de93d16fbb3` |

Each took 200–210 s for 8 jobs on 2 threads. The replay also gave each seed's best circuit
(`r0-s<S>.best.bfx`) unchanged, and the run's per-seed logs are in the circuit's logs.

## 2. Conjugation and staged pull

[34/4/122/14](aes-sbox/aes-sbox-a34-ad4-g122-gd14-xx88-38.circ.txt), from a 34/4/123/14 circuit
of an earlier job. The night run recorded commit `d9507dd` plus the `sha256` of its operator
scripts and kernel source; all of them are identical at `d72204c`. The targets file and the
kernel folder are set by environment variables:

```bash
git -C $X worktree add $X-d72204c d72204c && cd $X-d72204c
export XS_TARGETS_JSON=$PWD/nonlinear/boolflux/results/targets/TARGETS.json XS_NIGHT=$PWD/OUT/night
mkdir -p $XS_NIGHT
N=aes-sbox-a34-ad4-g122-gd14-xx88-38
taskset -c 0 python3 nonlinear/boolflux/campaigns/targets/ops/conjpull.py --in $L/$N/run-start.circ.txt \
  --target T06 --seed 756285 --seconds 900 --out OUT/conj --conj id --repair-keep 0 --schedule m:13:600
gates OUT/conj/conjpull-a34-ad4-g122-gd14-*.circ.txt
```

Expected digest `df3fd7d32a58c85d1be8a66b08c03255932f09b81659ca7c4b85784b9dbe136f`, the gate list
of the circuit as first recorded (`record` in its `found.json`). The job runs its 600 s stage to
the end.

## 3. Re-basing

[35/3/165/13](aes-sbox/aes-sbox-a35-ad3-g165-gd13-xx130-60.circ.txt), from a 35/3/166/13 circuit,
same commit and variables as example 2:

```bash
N=aes-sbox-a35-ad3-g165-gd13-xx130-60
taskset -c 1 python3 nonlinear/boolflux/campaigns/targets/ops/rebase.py --in $L/$N/run-start.circ.txt \
  --target T08 --seed 17292 --seconds 900 --out OUT/rebase --cap 13 --stages 1 --stage-seconds 200
gates OUT/rebase/rebase-a35-ad3-g165-gd13-*.circ.txt
```

Expected digest `99fa3cfe090968bac5d66940c44fa543c4b5b2fc1da01d87f9248177acd8220a`, again the
gate list as first recorded; the job runs its 900 s budget to the end. `OUT/rebase/rebase.jsonl` shows the same rebuilt start (`925ef601cda9`) and stage seed (21499)
as the run's `rebase.jsonl.gz` in the logs.

## 4. Hub depth pull

[35/3/155/15](aes-sbox/aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt), one hub job: a depth pull
of a 35/3/143/18 circuit. The hub recorded code version `8922cac+1df9fcd2fb` (no uncommitted
changes; the hash, recomputed at `8922cac`, is the same). A pull reads only its input from the
hub archive, so a one-circuit archive made from the published input is enough:

```bash
git -C $X worktree add $X-8922cac 8922cac && cd $X-8922cac
N=aes-sbox-a35-ad3-g155-gd15-xx120-56; ID=23da8f1d7865
mkdir -p OUT/hub/archive && cp $L/$N/input.bfx OUT/hub/archive/$ID.bfx && cp $L/$N/input.json OUT/hub/archive/$ID.json
taskset -c 0 python3 nonlinear/boolflux/hub/op_pull.py --archive OUT/hub --in $ID --seed 44669964 \
  --seconds 90 --out OUT/hub/jobs/pull
sha256sum OUT/hub/jobs/pull/cand-000.bfx
```

Expected `c81bf65c562f49a4d655c3cb493550b827805f771104df5abcf54380d361fb3f`, the circuit exactly as
the hub first recorded it (`record.sha256` in its `found.json`); `OUT/hub/jobs/pull/record.json`
names the same archive id, `d29215c169ac`, and the same lowered cap (GD 15) as the run's
`job-record.json`. The replay's last improvement came at 20 s, the original's at 13 s.
