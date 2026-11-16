# Verified linear targets

Pinned official [NIST Circuits commit](https://github.com/usnistgov/Circuits/tree/8366158a4324ef902ce740f29ddc9f7ebb1018b2), observed on the default `master` branch, rechecked 27 October 2026 (unchanged commit).

| Target ID | Inputs → outputs | Active seed XORs / depth |
|---|---:|---|
| `aes_sbox_bottom` | 18 → 8 | 28 / 5; 38 / 4 |
| `fox_mu4` | 32 → 32 | 130 / 13 |
| `fox_mu8` | 64 → 64 | 540 / 14 |
| `joltik` | 16 → 16 | 44 / 7 |
| `invmixcolumns` | 32 → 32 | NIST 119 / 5, 107 / 6, 102 / 7, 96 / 8; local 95 / 9, 91 / 14, 89 / 16, six distinct 88 / 19 |

All inputs have depth zero. AES measures the standard Boyar–Peralta bottom **linear part**, with formal final-product inputs `z0…z17`. It excludes the affine complements `[0,1,1,0,0,0,1,1]` (`S0` is MSB). These depths do not describe the full nonlinear S-box or actual product arrival times.

- [Source catalog](nist/source_catalog.json): 67 unchanged files, commit URLs, Git blobs, SHA-256 hashes.
- [AES scan](nist/aes_bottom_scan.json): 61 complete forward S-box sources; nine compatible sources, six distinct tails. Only the two nondominated tails are active seeds; others remain extraction evidence.
- All 61 complete forward AES sources passed all 256 inputs. Compatible tails passed exact input-permutation and affine-reattachment checks.
- FOX/Joltik replay matches the separate official `.mat` rows. Their original circuit comments swap `vecRows`/`vecCols`; comments do not define these targets.

Rebuild from preserved bytes and test, without network access or search:

```sh
python3 -B search/targets/import_nist.py
python3 -B -m unittest search.tests.test_targets
```

`search.target.target_path()` resolves IDs or JSON paths; seed paths are relative to `search/`. Target matrix hashes use canonical JSON `{input_count,rows}`. `verify` rejects malformed explicit outputs; only gates-only candidates infer outputs. `dag_sha256` requires unique signal values and fixes input/output order; `circuit_sha256` preserves program order.

The explicit [local Joltik seed](seeds/joltik/local_g43_d8_217e20b57859.json) has **43 XORs / depth 8**. It is a search result, not a NIST record; the built-in Joltik default stays 44 / 7. [Portable origin evidence](local/joltik_g43_d8_217e20b57859/origin.json) preserves the earliest recorded discovery, original witness/sidecars, configuration, source archive/commit, session/environment, and chunk-start RNG state. Callback-time RNG state was not recorded.

## AES inverse MixColumns

`invmixcolumns` uses one AES column, byte order unchanged and bit `8*byte+bit` LSB-first. Its rows are reconstructed over GF(2⁸), modulus `0x11b`, with first coefficient row `[0x0e,0x0b,0x0d,0x09]`.

The search matrix hash uses canonical JSON. The older [benchmark](../../benchmarks/invmixcolumns.json) hashes packed little-endian row masks; the rows are identical, but the two encodings have different hashes.

Seeds combine pinned official NIST circuits with the [local inverse records](../../records/invmixcolumns/README.md). Original bytes and provenance are preserved by the [offline importer](import_invmixcolumns.py). The six 88@19 seeds have distinct fixed-interface DAGs. Seed order matches the 13-worker profile's depth caps.

The [NIST table](https://csrc.nist.gov/Projects/circuit-complexity/list-of-circuits), checked 28 October 2026, lists 121@5. Its pinned GitHub repository also supplies 119@5; the campaign uses that smaller verified circuit.
