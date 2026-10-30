# Local Joltik seed: 43 XORs, depth 8

This is the earliest recorded qualifying `new_search_record` in the stopped `three-targets20` campaign: worker `joltik-05`, 26 October 2026, 06:20:23 UTC, engine `v2-walk`. It is not a NIST record.

[origin.json](origin.json) records the run ID, original paths, source commit/archive hashes, selection evidence, and SHA-256 of every preserved file. `original/` contains the source archive, accepted configuration, session/environment records, all six Joltik discovery logs, and the selected circuit with its verification, NCFF, and RNG sidecars.

The original frozen verifier reproduces its verification sidecar exactly. Current strict matrix verification and NCFF replay also pass. Original chunk-start RNG state is preserved; callback-time state was not recorded.

The built-in NIST seed remains 44 XORs/depth 7. The local seed is available only through an explicit seed override.
