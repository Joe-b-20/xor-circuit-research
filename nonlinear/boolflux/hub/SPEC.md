# BoolFlux hub: shared-archive architecture (working spec, 2026-11-14)

Goal: one shared search state that linear/affine, nonlinear and joint transformations all read and
write, so that a discovery made by one move (a new intermediate function, a new AND structure, a
cheaper XOR layer) is immediately usable by every other move. Built on what measured best on
2026-11-14: front/back **joining** at shared interface functions (track E: 34 frontier admissions in
~1 h vs 2 for polishing alone, the only mechanism that lowered A on AES), the **gate kernel**
(bfx.c, exact care-set resubstitution, now strictly lexicographic), **depth pulls** under AND caps,
and **timing-aware XOR-region rebuilds** (track F trb). Components are replaced only where a
measured comparison shows an advantage.

## Shared state (on disk, one directory per campaign, e.g. `~/xs-campaigns/2026-11-14-hub/`)

1. **Archive** `archive/`: every admitted circuit, content-addressed (`<sha12>.bfx`, kernel text
   format of core.to_kernel, plus `<sha12>.json` record). A circuit is admitted only after
   `campaigns/aes_check.check`-equivalent verification (core + independent verifier, all 256 inputs,
   NIST library {AND, XOR, XNOR, NOT}, metrics agree). Record fields: `id, A, AD, G, GD, counts,
   parents [ids], operator, operator_settings, seed, run_id, code_version (git commit + dirty hash),
   cpu_s, wall_s, t_admit, verified`.
2. **Cells**: the archive keeps, for every (A, AD, GD) triple reached, the circuits with the fewest
   G (ties kept up to K = 4 distinct structures). AND count and AND depth are therefore first-class
   coordinates, not tie-breakers. The Pareto front over (A, AD, G, GD) is derived from the cells.
   `archive/cells.json` is rewritten atomically after every admission.
3. **Function bank** `funcbank/`: every distinct signal truth table (256-bit, hex) occurring in an
   archived circuit, with: cheapest known (gate level, AND level, cone AND count) and the circuits it
   occurs in; plus tags for **interface functions** (affine combinations of signals spanning the
   GF(2^4) norm N = x^17, N^-1, u = N + N^-1, the 8 outputs). Joins, rebuilds and nonlinear-basis
   generators look up and add to it.
4. **Operator statistics** `stats.jsonl`: per operator x target-cell class: attempts, CPU s,
   admissions, frontier improvements (weighted, see below).

## Operators (all read archive members, write candidates; none owns a circuit)

Common CLI: `op_<name>.py --in ID [--in2 ID] --caps A,AD,GD --objective KEYS --seed S --seconds T
--out DIR` -> candidate `.bfx` files + `record.json` (settings, timing, parents). The hub verifies
and admits. Initial set (from existing code):
- `polish`: gate kernel under caps (bfx, `lex`).
- `pull`: polish with one cap lowered (GD, AD or A) - repair mode.
- `join`: front of X / back of Y at an interface (strategies/E/splice2.py), the back's inputs rebuilt
  as affine combinations of the front's signals (function-bank lookup).
- `trb`: timing-aware rebuild of one linear region (strategies/F/trb.py).
- `linres`: re-synthesis of all linear regions of a fixed AND structure (seeded rebuild, and XORFlux
  where a region is a pure linear map), keeping shared intermediates.
- **generators** (new nonlinear structures meant to feed `join` and the linear operators): alternative
  stage-1 product sets spanning N, inversion blocks of other AND count/depth trade-offs, final
  product layers (13/17/18 products), AND-depth-3 constructions; each emitted as a complete,
  verified circuit so joins can combine it with everything else.

## Scheduler

Workers (one pinned process per CPU, launched with `~/xs-campaigns/guard/xsrun`) loop: choose an
operator and a target cell by a bandit on recent frontier gain per CPU second (with a floor so every
operator keeps being sampled), run it for a short budget, submit candidates. Gain weights favour the
research priorities: a new cell with lower A or lower AD than any archived circuit at the same other
coordinates scores highest, then lower G at a GD cap. Every job is logged (`runs/<run_id>.json`:
code version, seed, settings, parents, timing, outcome).

## Rules

- Never discard evidence: rejected/failed runs stay logged; superseded circuits stay in the archive.
- Hard caps are hard (kernel feasibility-first ranking); objectives are lexicographic (objective.py).
- Memory: every job through xsrun with XS_MEM; the hub itself under 2 GB.

## Changes made while implementing (track E, 2026-11-14 ~18:00 UTC)

- **Cell admission slack.** A circuit that is dominated by a front point enters its (A, AD, GD) cell
  only if its G is at most 6 above the G of the dominating front point(s) (`archive.NEAR_SLACK`), and
  scores gain 0.01 (`CELL_ONLY_GAIN`).  Evidence: in a 2.4-min smoke run with the plain cell rule the
  join operator admitted ~30 dominated circuits per 3-s job (cells 110 -> 560), and their gain
  (0.05 each) made join look 20x better than everything else to the bandit without moving the front.
- **Gain** (`archive.Archive.gain`): non-dominated tuple -> 8 / 4 / 2 / 1 if it lowers A / AD / G / GD
  at no worse other coordinates (max over the coordinates that apply; 1 if no archived point is
  comparable).  This is how "A and AD first, then G and GD" is encoded.
- **Kernel objective for polish/pull**: `lex a,ad,cost,gd` under the caps (AND count and AND depth
  first).  `pull` lowers one cap: GD by 1-3 (3 of 5 draws, AD cap dropped), AD by 1, or A by 1.
- **trb** is a copy (`hub/trb_impl.py`, from strategies/F/trb.py md5 714039e1), so track F's ongoing
  edits cannot break the hub; F's new operators should be added as `op_<name>.py` with the same CLI.
- **join** keeps at most 40 candidates per job (highest gain first) and joins the input with up to 300
  partners (front first, then random cell minima), both roles, all cut levels.
- **Function bank** is built and tagged (N, N^-1, u, output span) on every admission, but join does not
  need it (it computes the front span directly); it is the lookup table for the generator and linres
  operators, which are **not implemented yet**.
- Seeds: old-2020 `.slp` files are not NCFF and are not seeded.
- Code: `common.py` (verify = core + independent verifier on the NCFF text, metrics agreement, NIST
  library), `archive.py`, `funcbank.py`, `join.py`, `ops.py` + `op_{polish,pull,join,trb}.py`,
  `scheduler.py`, `seedlist.sh`, `tests/test_hub.py` (wrong circuit rejected; cell keeps min G and
  persists; join reproduces the 31/5/119/20 transplant; run and archive record fields).

## Changes in review 5 (2026-11-15; findings and evidence in `review5/HUB.md`)

- **Truth on disk.** The record files `archive/<id>.json` + `<id>.bfx` are the archive. `cells.json` and
  `index.jsonl` (one record per line, appended on admission) are caches: the cells are recomputed from
  the records on every load. Only the scheduler admits (one scheduler per campaign directory,
  `scheduler.lock`); operators open the archive read-only.
- **Distinct structures.** A circuit whose DAG equals an archived one up to gate order and operand
  order of symmetric gates (`common.structure_key`, record field `skey`) is refused as
  `duplicate-structure`. An archive filled before this rule is deduplicated in its cells on the
  scheduler's first start (`Archive.dedupe_legacy`; nothing is deleted).
- **Gain** (`Archive.gain`, `--gain value`, default): 8 when no archived circuit has A <= and AD <=
  the new tuple and some circuit meets the AD cap (the AND count at that depth drops), 4 when none
  meets the AD cap (new AND depth), 1 when only the gate depth inside (A, AD) is new, otherwise
  0.5 per gate saved (at most 3) against the best G inside the cap box A, AD, GD; 0 for dominated
  tuples. `--gain legacy` is the rule of 2026-11-14.
- **Targets** (`--target-mode tuple`, default): attempts are counted per (A, AD, G, GD) tuple, not per
  circuit id; `--tuple-caps polish=2,pull=3` (also `control.json` `"tuple_caps"`) stops an operator
  choosing a tuple after that many jobs; a front tuple without its first polish / pull gets it before
  any bandit choice (A <= 31 first, newest first). When every operator is capped everywhere the
  least-attempted tuple is used (a CPU never idles). `--target-mode id` is the old rule.
- **Join** (`--join-mode incremental`, default): the scheduler passes `--since T`; partners are all
  cell members (front or not) admitted after T, oldest first; the job reports `joined_through`, and a
  target is offered to join again only when the archive has admissions after that mark. One pass per
  (target, archive state). `--join-mode legacy`: front-first 300 partners every time.
- **CPUs.** `--cpus` defaults to the CPU affinity of the scheduler process (the list given to xsrun).
  An explicit list outside that affinity is refused unless `--cpu-allow` names it. `control.json`
  `"cpus"` is the exact active set (shrinks and grows) inside the allow list; the current set is in
  `cpus.json`. One job per CPU; a job is killed (process group) after 2 x seconds + 60 s.
- **Run ids** are `<campaign uid>.r<number>-<op>` (`campaign.json`), unique across campaigns; numbers
  continue after the highest one used in `runs/` or `jobs/`; a job directory is never reused.
- **Operator CLI contract.** Exit 0: `record.json` written with `cand_ids` (content ids of
  `cand-000.bfx`, ... in order). Exit 1: the operator failed; `record.json` carries `error`. Exit 2:
  bad command line. A candidate file not listed in `cand_ids` is not admitted. Every job gets a run
  file with `status` (ok / failed / timeout / stopped); verified candidates of a failed job are still
  admitted, with `operator_settings.job_status`. Five failures in a row suspend an operator for 10
  minutes (event `op-suspended`).
- **Lineage in every record**: operator, parents, run_id, seed, code_version (commit, `-dirty`, hash of
  hub + hub/ops + kernel + core/objective/verifier sources), operator_settings with caps, objective,
  seconds, script path and hash, scheduler version, kernel binary; seeds and ingested files carry the
  file hash and their JSON sidecar. `hub/lineage.py CAMPAIGN [--also OTHER]` audits an archive.
- **control.json** is validated as a whole and applied only if valid; keys: ops, seconds, eps, near,
  near_gap, nursery, ad3_share, tuple_caps, cpus, ingest, scripts, generators.
- **osc** keeps the input's A cap (`--caps=-,AD,GD` for the old behaviour).
