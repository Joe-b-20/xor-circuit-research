# xor-circuit-research

Small, shallow XOR circuits for linear maps used in ciphers, the search that found them
(XORFlux), how that search came to be, and two lower-bound proofs for AES MixColumns.

| Section | What is in it |
|---|---|
| [circuits/](circuits/README.md) | the smallest circuit our search found at each depth, per map, in NIST's file format, each with its logs and the version that found it, next to NIST's circuits; a checker. Not claimed optimal or best known |
| [search/](search/README.md) | XORFlux, an adaptive search for size- and depth-efficient XOR circuits: [how it works](search/HOW-IT-WORKS.md), [how to use it](search/USAGE.md) and [the path to the current version](search/HISTORY.md) |
| [lower-bound-proofs/](lower-bound-proofs/README.md) | two proofs: AES MixColumns needs at least 75 XOR gates, and at least 93 at depth 3 |

Maps so far (59): AES MixColumns and InvMixColumns, the AES S-box bottom linear layer, FOX MU4
and MU8, and every linear map of NIST's
[circuit repository](https://github.com/usnistgov/Circuits/tree/master/data/slp/2021-linearmaps)
(ARIA, Twofish, Grøstl, CLEFIA, Khazad, Whirlpool, Joltik, Skinny, PRINCE, QARMA and 37 MDS
matrices from the literature).

## License

[Apache License 2.0](LICENSE), except where a folder has its own license file:
`lower-bound-proofs/mixcolumns-lb75/`, `lower-bound-proofs/mixcolumns-lb93-depth3/supplement/`,
`search/versions/v1-mixcolumns-pipeline/` and the v2–v4 framework versions are MIT. Data from
NIST's circuit repository and circuits from published work keep their own terms; see
[NOTICE](NOTICE).
