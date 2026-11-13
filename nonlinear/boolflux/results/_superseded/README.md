Results from the first sanity runs (2026-11-13), made before runs kept a snapshot of their
sources, so their commands do not pin the code. Kept for the record; not claimed. Each case was
re-run with the final code (see results/reports/sanity-2.md): maj3 and fulladd give the same
gate counts in the xag model, GF(2^4) inversion 17 gates with 5 AND (this file: 16), GF(2^4)
multiplication 32 gates with 9 AND (this file: 31). Both verifiers accept these circuits.

chi3-*: computed chi with a_0 = least significant bit (a built-in target, removed), not the
chi3 table of benchmarks/sboxes.json (a_0 = most significant bit). Found by the independent
audit (audit/AUDIT.md). Correct for the bit-reversed function; re-run against the spec table.
