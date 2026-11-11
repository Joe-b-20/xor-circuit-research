# Certificates at G = 75 for the claims excluded by the 75 proof's own rows

**Added 11 November 2026. The lower bound stays 75.**

The [75-gate package](../../mixcolumns-lb75/) ships exact certificates for G = 74 only. At G = 75 its
rows (L1)-(L23) exclude 5,908 of the 7,416 oriented claims and leave 1,508 open, and until now the
5,908 exclusions were an LP status. This folder gives them exact integer Farkas certificates, so every
claim of the G = 75 domain that is counted as excluded anywhere in the parent folder now has one.

| File | What it is |
|---|---|
| `CERTIFICATES_PKG75_G75.json` | all 7,416 claims with their bounds (k, l) and an `excluded` flag; 15,742 certificates (key, nonnegative integer weights) |
| `check_pkg75.py` | the checker: standard library, exact integer arithmetic, no optimizer |
| `gen_pkg75.py` | the generator (needs NumPy and SciPy; not run by `verify_all.py`) |
| `published_sets.json` | the claim identifiers of the five certified sets of the parent folder and of the 280 open claims |
| `CHECKED_PKG75_G75.json` | the checker's report from the recorded run |

## Check

`../verify_all.py` runs the checker as its last stage (about 3 s). Alone, from the repository root:

```sh
python3 lower-bound-proofs/mixcolumns-lb75-open-cases/package-rows-g75/check_pkg75.py
```

(this rewrites `CHECKED_PKG75_G75.json` in place with the same content). The checker

1. writes the rows (L1)-(L23) itself, from the row list of the package's `lp_regen.rows_for`, not from
   `certify75.system`, which the generator used, and verifies every certificate: nonnegative integer
   weights, a nonnegative combination on every type column (827,190 coefficients), weighted right side
   at most -1;
2. enumerates the scalar domain at G = 75 itself (3,708 states) and requires the file's claims to be
   exactly that domain times {M, M<sup>T</sup>}, each once;
3. for every claim marked excluded, requires a certificate or a direct exclusion for every key below the
   stated bounds (33,536 certificate references) and requires the final test to fail at (k, l);
4. compares identifiers with `published_sets.json`: the 5,908 excluded claims are disjoint from the
   published sets, and the 1,508 open claims are exactly their union.

`../verify_all.py` then checks `published_sets.json` against the certificate files of the parent
folder: the five certified sets are the claim lists of those files, and the six sets are pairwise
disjoint. The 280 "open" claims are therefore identified as exactly the claims of the domain that no
certificate file excludes. That they are LP-feasible under all published rows is a measurement.

Mutation tests, run once on 2026-11-11 and not part of `verify_all.py`: a zeroed weight, a dropped
referenced certificate (5 of 5), a loosened bound, an open claim marked excluded and a dropped claim
were all rejected.

## What this does and does not show

It removes a mechanical gap: the 5,908 exclusions no longer rest on a solver status. It does not show
that the 75 proof's framework applies at G = 75. The package words its sections 10-11 for "G is 73 or
74"; that the same chain of lemmas holds for a minimum circuit with 75 gates has been read by one
language-model agent and not reviewed independently. See [`../ACCOUNTING-G75.md`](../ACCOUNTING-G75.md).

## Provenance

Generated and checked on 2026-11-11 in the proof follow-up of the phase of 9 November 2026, by the main
language-model agent under the author's direction. Originals:
`research/phase-2026-11-09/proof-followup/package75/` on the branch `phase-2026-11-09` (commit
`94cc603`; tag `phase-2026-11-09-pilot-q3`). The certificate file, the checker, `published_sets.json`
and the report are byte-identical to the originals; the generator differs in one line (the path of the
package, made relative to this folder). Generation took 21 s; 0 keys were left uncertified.
