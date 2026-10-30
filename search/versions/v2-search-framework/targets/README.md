# Verified linear targets

Pinned official [NIST Circuits commit](https://github.com/usnistgov/Circuits/tree/8366158a4324ef902ce740f29ddc9f7ebb1018b2), observed on the default `master` branch, 24 October 2026.

| Target ID | Inputs → outputs | Active seed XORs / depth |
|---|---:|---|
| `aes_sbox_bottom` | 18 → 8 | 28 / 5; 38 / 4 |
| `fox_mu4` | 32 → 32 | 130 / 13 |
| `joltik` | 16 → 16 | 44 / 7 |

All inputs have depth zero. AES measures the standard Boyar–Peralta bottom **linear part**, with formal final-product inputs `z0…z17`. It excludes the affine complements `[0,1,1,0,0,0,1,1]` (`S0` is MSB). These depths do not describe the full nonlinear S-box or actual product arrival times.

- [Source catalog](nist/source_catalog.json): 65 unchanged files, commit URLs, Git blobs, SHA-256 hashes.
- [AES scan](nist/aes_bottom_scan.json): 61 complete forward S-box sources; nine compatible sources, six distinct tails. Only the two nondominated tails are active seeds; others remain extraction evidence.
- Every complete source passed all 256 AES inputs. Compatible tails passed exact input-permutation and affine-reattachment checks.
- FOX/Joltik replay matches the separate official `.mat` rows. Their original circuit comments swap `vecRows`/`vecCols`; comments do not define these targets.

Rebuild from preserved bytes and test, without network access or search:

```sh
python3 -B search/targets/import_nist.py
python3 -B -m unittest search.tests.test_targets
```

`search.target.target_path()` resolves IDs or JSON paths; seed paths are relative to `search/`. Target matrix hashes use canonical JSON `{input_count,rows}`. `verify` rejects malformed explicit outputs; only gates-only candidates infer outputs. `dag_sha256` requires unique signal values and fixes input/output order; `circuit_sha256` preserves program order.
