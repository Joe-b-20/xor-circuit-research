# results/targets: curated circuits of the targeted AES S-box campaign (2026-11-15)

Layout for publication, following XORFlux's `circuits/` standard (one folder per target, the
circuit named by its numbers, a run record per circuit). Filled by the coordinator at curation
time from `~/xs-campaigns/2026-11-15-targets/<agent>/found/`; nothing here is written by a search.

```
results/targets/
  README.md                       this file: layout and conventions
  TARGETS.md                      the campaign page: request, rules, one results table per target,
                                  methods, failed experiments, compute (section plan inside)
  LEDGER.md, LEDGER.json          final output of campaigns/targets/ledger.py (generated, not edited)
  T01/ ... T10/, Z/               one folder per target (Z: the 27-AND objective)
    README.md                     the target: reference, hard limits, priorities, frontier table
    aes-sbox-a<A>-ad<AD>-g<G>-gd<GD>-<ID>-<agent>-<k>.circ.txt
                                  the circuit, NIST circuit file format (NCFF), header comments:
                                  Not a NIST-issued circuit / Found by / Started from / Logs
    aes-sbox-...-<k>.json         its sidecar (campaigns/targets/SIDECAR-TEMPLATE.json)
    logs/aes-sbox-...-<k>/        run record:
      found.json                  version, code, run, seed, time, start, lineage, list of log files
      REPRODUCE.md                filled campaigns/targets/REPRODUCE-TEMPLATE.md
      aes_check.json              aes_check.py --json output for the circuit
      command.sh                  the exact command; config files of the run
      start.circ.txt              copy of the start circuit when it is not a pinned NIST file or a
                                  file already in results/ (else its path + sha256 in found.json)
      run.log.gz, trace.jsonl.gz  the job's own logs, compressed
```

`<k>` is a 1-based index for several circuits of one agent with the same tuple.

## What goes in

Every circuit of a target's final (G, GD) Pareto frontier and of its strict and tradeoff Pareto
sets, as computed by `campaigns/targets/ledger.py run` inside the hard limits A <= ref A,
AD <= ref AD. Points with status **known** are not copied again: the target README links the
existing file (results/aes/, best-1400, hub archive id). Points **reproduced** by the campaign
are listed with the file they reproduce. Dominated campaign circuits stay in the campaign
folders, not here.

## Checks

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/*/*.circ.txt
python3 nonlinear/boolflux/campaigns/targets/ledger.py run      # recompute classes, frontiers, status
```

## Conventions

- Library {AND, XOR, XNOR, NOT}; NIST counting (every gate counts, NOT included). A = #AND,
  AD = AND depth, G = #gates, GD = gate depth; inputs have depth 0.
- Pin: NIST Circuits commit 3d807741f937d29d3bef4f32f142ccda0cda9070 (`nonlinear/nist/PIN.md`).
- strict / tradeoff / other and the thresholds: TARGETS.json of the campaign, copied into
  TARGETS.md at curation. A tradeoff never dominates its reference.
- Evidence labels [C] / [H] as in VERIFICATION.md.

## Campaign record copied here (2026-11-15, coordinator)
`LEDGER.md` / `LEDGER.json` (final ledger run 23:3x UTC: classes strict / tradeoff / other, path
certification, provenance, comparison with the pinned NIST set), `TARGETS.json` (rules and thresholds),
`USER-REQUEST.md` (the request verbatim), `BRIEF.md` (agent brief), `COMPLIANCE-1820.md` (kernel repair
rule and the donor ruling), `QUEUE.md` (overnight proposals). Each `T??/` folder holds the campaign
circuits on that target's frontier within its hard limits, so one circuit can appear under several
targets (for example 28/4/174/14 is within the limits of T01-T05); its class for each target is in
`LEDGER.md`, not necessarily in the copied sidecar.
