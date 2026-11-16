# XOR search campaigns

Python 3.10+, standard library. One process per worker.

## Joltik depth and FOX Mu8: 15 workers

| Target | Inputs → outputs | Workers | Starting circuit | Objective |
|---|---:|---:|---:|---|
| Joltik | 16 → 16 | 5 | Local 43 / 8 | Reduce depth; retain at most 43 XORs |
| FOX Mu8 | 64 → 64 | 10 | NIST 540 / 14 | Reduce XOR count |

All five Joltik workers start at 43@8 and rank depth first. Their depth cap is 8; the first goal is at most 43 XORs at depth 7. Larger exploratory circuits may occur in checkpoints, but cannot become saved records or shared improvements.

FOX Mu8 uses four workers capped at depth 14, three at 15 and three unrestricted. [Seed sources and exact matrices](targets/README.md) include the local Joltik discovery evidence and pinned NIST files.

```bash
python3 search/run.py prepare --config search/configs/joltik-depth-foxmu8-15.json --out search/runs/joltik-depth-foxmu8-15
python3 search/run.py run search/runs/joltik-depth-foxmu8-15
```

Preparation starts no workers. Skip it if that directory is already prepared. Runs continue until stopped; add `--seconds 86400` for a 24-hour session.

```bash
python3 search/run.py summary search/runs/joltik-depth-foxmu8-15
python3 search/run.py stop search/runs/joltik-depth-foxmu8-15
python3 search/run.py run search/runs/joltik-depth-foxmu8-15 --resume
python3 search/run.py verify-run search/runs/joltik-depth-foxmu8-15
```

For automatic summary refresh:

```bash
watch -n 5 python3 search/run.py summary search/runs/joltik-depth-foxmu8-15
```

## Original three-target profile: 20 workers

| Target | Inputs → outputs | Seed XORs / depth | Workers |
|---|---:|---:|---:|
| AES S-box bottom | 18 → 8 | 28 / 5; 38 / 4 | 6 |
| FOX Mu4 | 32 → 32 | 130 / 13 | 8 |
| Joltik | 16 → 16 | 44 / 7 | 6 |

Seeds use the [pinned NIST repository](https://github.com/usnistgov/Circuits/tree/8366158a4324ef902ce740f29ddc9f7ebb1018b2), checked 24 October 2026. AES seeds are compatible Boyar–Peralta tails extracted from full S-box circuits; NIST has no separate bottom-layer listing. [Matrices, extraction and attribution](targets/README.md).

Depth starts at zero on every input. AES searches the linear part; its four output complements remain explicit metadata. These metrics do not measure the full S-box.

The earlier profile remains available:

```bash
python3 search/run.py prepare --out search/runs/three-targets20
python3 search/run.py run search/runs/three-targets20
```

Use the same summary/stop/resume commands with this campaign's directory. `status` returns full JSON. `prepare --plan --config PATH` previews a profile; `--pin-cpus` assigns distinct available logical CPUs. Oversubscription is rejected by default.

After editing the source, resume with the frozen launcher:

```bash
python3 search/runs/three-targets20/source/search/run.py run search/runs/three-targets20 --resume
```

## Search

Workers rotate through applicable [legacy, inverse, v2 and v3 methods](engines/README.md). Sharing requires the same target matrix and an improvement under the receiving worker's objective and limits.

```mermaid
flowchart LR
  S[Verified NIST or local seeds] --> W[Independent worker trajectories]
  W --> E[Rotate applicable engines]
  E --> V[Reconstruct and verify XOR DAG]
  V --> R[Records and target frontier]
  R --> W
  E --> C[Checkpoint RNG and engine state]
  C --> W
```

## Saved evidence

| Path inside a campaign | Contents |
|---|---|
| `config.json`, `source.tar.gz`, `source/` | Resolved defaults, seeds, target hashes, commit and exact source bytes |
| `sessions/` | Commands, Python/OS, CPU model, worker allocation and exit status |
| `workers/*/worker.log`, `discoveries.jsonl` | Progress, imports, discoveries and sharing events |
| `workers/*/checkpoint.json` | Current trajectory, each engine's RNG/state, best circuit and frontier |
| `workers/*/records/` | Circuit JSON, NIST-style NCFF, verification and starting RNG evidence |

Equal-quality circuits use an exact DAG hash with fixed inputs/outputs; gate order, temporary names and swapped XOR operands do not create new structures. The default retains up to 32 structures per objective point per worker. Seed imports and shared circuits are labelled separately from discoveries.

Resume restores saved state. Time-limited proposals and concurrent sharing can change trajectories between separate runs, even with the same initial seed.

## Check

```bash
python3 -m unittest discover -s search/tests -p 'test_*.py'
```

[Source notices](NOTICE.md). Campaign output under `search/runs/` stays outside Git and distribution checksums.
