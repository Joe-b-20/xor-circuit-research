# Reproduce aes-sbox-a28-ad5-g129-gd19-T03-P1-1 (T03, A/AD/G/GD = 28/5/129/19)

```bash
python3 nonlinear/boolflux/campaigns/aes_check.py nonlinear/boolflux/results/targets/T03/aes-sbox-a28-ad5-g129-gd19-T03-P1-1.circ.txt
```

- class (T03): other; status: known-by-23:50 (P1; new vs archive); pinned NIST dominating: none
- found by: campaign 2026-11-15-targets, agent P1; strategies/P1/NOTES.md; at 2026-11-15T17:15:02Z; seed 23; after not logged per step by this version (run total 900 s; step 241 of 480) s
- start: `nonlinear/boolflux/results/aes/aes-nist-hub-pull-g130-a28-gd19-ad5.circ.txt` (sha256 e074f95080a8)
- method: {'engine': 'strategies/P1/unionsat2.py (span-pooled SAT LNS, glucose4)', 'pool': {'circuits': 111, 'forms': 1174, 'templates_pooled': 2396, 'templates': 7941, 'and_templates': 252, 'D': 19, 'closure': 1, 'start': '/home/joebachir20/xcr-boolflux/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g130-a28-gd19-ad5.circ.txt'}, 'operator_chain': [{'op': 'unionsat2-LNS', 'run': 't03-d19', 'seed': 23, 'step': 241, 'file': 'runs/usat2/t03-d19-out/us2-a28-ad5-g129-gd19-s23-241.circ.txt'}]}
- code: {"git": "8922cacae4d4314968c5ce9baa740dea7aa38935", "unionsat2_sha256": "929fdfbcf8679c5630cdcb55dc1bd863c4f092429758b48662e94f2018c57ca4"}
- reproduction: Run t03-d19 (17:03:28-17:18:30 UTC, CPU 10, unit xs-P-P1-lns2seq2). Code = unionsat2.py as of 17:03 UTC (not snapshotted); logically identical to runs/code/unionsat2-f3f9ce6e.py with --restrict 0 --side 0.3 --closure-max 6000. Pool = starts_fam.json rows + DATA/shared/*.bfx whose .json t precedes 17:03:28 UTC (111 circuits in the span). Per-step log: runs/usat2/t03-d19.log (step number in the file name: ...-s23-<step>).

## Re-run

`command.sh` here (recorded command; repository paths as `$REPO`):

```bash
cd "$HOME"/xs-campaigns/2026-11-15-targets/P1/runs/usat2 && python3 "$REPO"/nonlinear/boolflux/strategies/P1/unionsat2.py --lns "$REPO"/nonlinear/boolflux/results/aes/aes-nist-hub-pull-g130-a28-gd19-ad5.circ.txt --starts "$HOME"/xs-campaigns/2026-11-15-targets/P1/starts_fam.json --extra "$HOME"/xs-campaigns/2026-11-15-targets/P1/shared --D 19 --cap-ad 5 --seconds 900 --lns-sec 20 --seed 23 --out t03-d19-best.circ.txt --outdir t03-d19-out --log "$HOME"/xs-campaigns/2026-11-15-targets/P1/runs/usat2/lns2.jsonl
```
