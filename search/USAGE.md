# Using XORFlux (v8)

How to run XORFlux v8, configure it, add a map and read its output. How it works is in
[HOW-IT-WORKS.md](HOW-IT-WORKS.md).

It needs Python 3.11 or newer and nothing outside the standard library. **Run every command
from the repository root.** (`python3 -m xorflux ...` from inside `search/` also works.)

## Quick start

```bash
python3 search/xorflux map list                                # the maps in circuits/
python3 search/xorflux quick aes-mixcolumns --seconds 60       # one worker, in this terminal
python3 search/xorflux quick joltik --seconds 60 --depth-cap 5

python3 search/xorflux run search/campaigns/joltik.toml --out search/runs/joltik --detach
python3 search/xorflux status search/runs/joltik

python3 -m unittest discover -s search/xorflux/tests -t search # tests, about 2 minutes
```

A map is named after its folder in `circuits/` (`aes-mixcolumns`, `aria`, `twofish`, `grostl`,
`clefia-m1`, ...; `map list` shows all 59); a path to any `.mat.txt` file works too. Every
command has `--help`.

## Commands

| Command | Does |
|---|---|
| `plan FILE.toml` | resolve and check everything (maps, seeds, knobs, CPUs) and print the plan; starts nothing |
| `run FILE.toml --out DIR [--seconds 2h] [--detach]` | freeze source, settings, map and seeds into `DIR`, then start the coordinator from that frozen copy |
| `status DIR` | frontier, pool, diversity, one row per worker |
| `stop DIR [--wait 120]` | workers checkpoint and exit |
| `resume DIR [--seconds N] [--detach]` | continue from the checkpoints (campaign time carries on) |
| `verify DIR` | check the frozen files and re-verify every record independently |
| `report DIR` | CSV tables and a self-contained `DIR/report/report.html` |
| `quick MAP [--seconds N] [--depth-cap D] [--seed S]` | one worker in this process, no coordinator; writes `search/runs/quick-MAP-TIME/` |
| `map list`, `map show NAME`, `map new NAME ...` | the maps in `circuits/`; add one ([below](#adding-a-map)) |
| `config explain [SECTION]`, `config show` | the knobs ([below](#configuration)) |

Use `--detach` for any run you do not watch. Without it, the coordinator lives in your
terminal and stops when the terminal closes (Ctrl-C stops it cleanly). `--seconds` takes
`3600`, `90m` or `2h30m`, and `0` means until stopped. A frozen run keeps running the code it
was frozen with, so editing `search/xorflux/` during a campaign is safe.

## Campaigns

`search/campaigns/<map>.toml` holds a campaign with the settings that were run for that map
(1 hour, 20 workers in groups by depth cap; 2026-10-29, and 2026-10-30 for ARIA, Twofish,
Grøstl and CLEFIA M1). Seed paths in them are relative to the file, and the seed circuits
are in `search/seeds/<map>/` (NIST's circuits are named `nist-g<G>-d<D>.json`). A plan with
more workers than free CPUs is refused. Add `--set campaign.allow_oversubscription=true` to
run it anyway, or lower `count`.

A campaign file:

```toml
[campaign]
name = "my-run"
seed = 1
duration = "2h"
sharing = "pull"

[set]
"restart.stall_seconds" = 1200.0

[[workers]]
name = "cap7"
target = "fox-mu4"              # a map name or a .mat.txt path
count = 4
depth_cap = 7                   # or "none"; a list cycles over the group's workers
seeds = ["target"]              # "target" (search/seeds/<map>/), "root", or a circuit JSON path
[workers.set]
"objective.soft_depth_slack" = 3
```

Campaign files that show more features are in [xorflux/examples/](xorflux/examples/).

## Configuration

Every tunable value is a *knob*. Each knob is declared next to the code that reads it, with
its type, legal values and a doc string. You never need to edit code to change one:

```bash
python3 search/xorflux config explain                  # every knob section
python3 search/xorflux config explain restart          # the knobs of one section
python3 search/xorflux config show > mine.toml         # every knob as an editable profile
python3 search/xorflux plan search/campaigns/fox-mu4.toml --settings   # what each worker will get
```

Values stack from the lowest to the highest priority, and each value remembers which layer
set it:

| Where | Scope |
|---|---|
| `search/xorflux/config/profiles/*.toml` (`default`, `quick`, `large`, `depth`) or your own profile file | every campaign that lists the profile in `profiles = [...]` |
| `[set]` in a campaign file | the campaign |
| `objective` / `depth_cap` / `gate_limit` and `[workers.set]` in a `[[workers]]` group | one group |
| `per_worker = [{...}, ...]` | single workers (the list cycles) |
| `--set key=value` on `run`, `plan`, `quick`, `config show` | one run |

TOML has no null, so write `"none"` (`--set objective.depth_cap=none`). The knobs that matter
most:

| Knob | What it does |
|---|---|
| `objective.depth_cap`, `objective.soft_depth_slack` | the real cap records must meet, and the extra depth allowed while searching |
| `moves.<family>.<move>.weight` | prior share of each move (`config explain moves`) |
| `restart.stall_seconds`, `restart.root_seconds` | when a stalled chain restarts, and how long one root may be followed |
| `restart.w_fresh`, `w_elite`, `w_shared`, `w_best` | where a restart starts from |
| `sharing.mode` | `pull` (take pool elites at restarts) or `off` |
| `phase.burst_budget`, `phase.repair_budget` | length of the burst and repair phases |
| `engine.record_polish_nodes` | node limit of the own-depth polish of new points (0 turns it off) |
| `scheduler.reference` | (gates, depth) points used to weigh improvements by how close they are to them (the campaigns set their goal points) |

**Foundation restarts (off by default).** `restart.w_foundation` (default 0) adds a restart
source that keeps the *level-1 set* (the XORs of two inputs) of the worker best or an archive
elite, builds a fresh root over it, and pins it: for `restart.foundation.pin_proposals`
proposals no other level-1 value can be added (members may still be dropped), then the chain
continues as an ordinary one. `swap_pairs` / `drop_pairs` perturb the set first. The
`restart` event names the donor and the set; `foundation_unpin` reports the chain best at the
unpin. Try it with `--set restart.w_foundation=1.0`; `config explain restart` lists the knobs.
Evidence: 2026-11-02 foundations study (MixColumns cap 4: holding the 89@4 level-1 set fixed
re-found 89@4 in 9 of 13 runs; not shown for InvMixColumns).

## Adding a map

```bash
python3 search/xorflux map new twofish-mds --gf 0x169 --bytes "01 ef 5b 5b; 5b ef ef 01; ef 5b 01 ef; ef 01 ef 5b"
python3 search/xorflux map new groestl-p --gf 0x11b --circulant "02 02 03 04 05 03 05 07"
python3 search/xorflux map new my-map --rows my-matrix.txt          # 0/1 rows, NIST or plain
python3 search/xorflux map show twofish-mds
python3 search/xorflux quick twofish-mds --seconds 300
```

`map new` writes `circuits/NAME/NAME.mat.txt` (use `--circuits DIR` to try a map somewhere
else first). An element matrix over GF(2^m) is given in hex with its field modulus. `m` is the
degree of the modulus, and bits follow the AES convention: input `x_(m*b+r)` is bit `r` (least
significant first) of input element `b`, and the same for outputs. A map file uses NIST's
matrix format, with one extension for affine maps: an optional extra line of one 0/1 constant
per output row (`y_i = row_i·x ⊕ c_i`; the search works on the linear part).

For a campaign, copy a file from `search/campaigns/` and change `target`. To start from known
circuits, put their JSON files in `search/seeds/NAME/` (`seeds = ["target"]`) or list their
paths. `python3 circuits/add.py RUN_DIR/workers/WORKER/records/gG-dD-HASH.json` adds a
recorded circuit to `circuits/` with its logs, and checks it.

## Output

```
DIR/
  plan.json, settings/, targets/, seeds/, source/   what was frozen (the run is reproducible from these)
  status.json, campaign.jsonl                       coordinator summary and events (frontier, pool, diversity)
  pool/<map>.json                                   distinct verified circuits per (gates, depth) point
  report/                                           `report` output
  workers/<id>/
    records/g<G>-d<D>-<dag>.json                    a recorded circuit (+ .ncff, + .verification.json)
    records.jsonl                                   index of the worker's records
    dossiers/<id>.json                              one per improvement: move trace, state before/after, replay seed
    events.jsonl                                    the worker's events (epochs, improvements, plateaus, restarts)
    status.json, checkpoint.json, error.json        live state, resumable engine state, failure (if any)
```

A record is one distinct circuit at a nondominated (gates, depth) point. It is written only
after it verifies. Each `frontier` event in `campaign.jsonl` names the record, the worker
that found it and the dossier that explains it:

```bash
jq -r 'select(.ev=="frontier") | "\(.t|floor)s \(.point.gates)@\(.point.depth) \(.by) \(.move)"' DIR/campaign.jsonl
```

All fields are listed in [xorflux/telemetry/schema.md](xorflux/telemetry/schema.md).
