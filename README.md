# xor-circuit-research

[![checks](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/checks.yml/badge.svg)](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/checks.yml)
[![lower-bound proofs](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/proofs.yml/badge.svg)](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/proofs.yml)

Small, shallow XOR circuits for linear maps used in ciphers, the search that found them
(XORFlux), how that search came to be, and two lower-bound proofs for AES MixColumns.

**208 circuits for 59 maps.** A circuit is written **G@D**: G two-input XOR gates, with every
output at depth at most D (inputs are at depth 0). Fewer gates is better, and so is a lower
depth; a circuit at a lower depth also counts for every higher one.

## Selected results

Each of these has fewer gates than NIST's circuit for the same map, at the same or a lower
depth. NIST's circuits are those of its
[circuit repository](https://github.com/usnistgov/Circuits) and
[list of circuits](https://csrc.nist.gov/projects/circuit-complexity/list-of-circuits).

| Map | Ours | NIST |
|---|---|---|
| AES MixColumns | **89@4** | 90@4 |
| AES InvMixColumns | **118@5**, **104@6**, **89@15**, **88@17** | 119@5, 106@6, 91@15, 90@20 |
| ARIA | **384@4** | 387@7 |
| Twofish | **108@8** | 111@8 |
| CLEFIA M1 | **99@10** | 103@10 |
| Grøstl | **364@11** | 410@12 |
| Whirlpool | **391@9** | 425@11 |
| Khazad | **340@15** | 366@18 |
| SKOP15 8×8 MDS over GF(2⁴) | **146@14** | 170@19 |
| JPST17 8×8 MDS over GF(2⁸), inverse | **493@11** | 528@11 |
| KLSW17 8×8 MDS over GF(2⁸) | **347@6**, **321@10** | 364@11 |
| KLSW17 4×4 MDS over GF(2⁸) | **64@6** | 72@7 |

For 46 of the 53 maps taken from NIST's repository, we have a circuit with fewer gates than
NIST's at the same or a lower depth; on the other maps NIST is ahead at some depths. Our
InvMixColumns 118@5 is at the lowest depth possible for InvMixColumns, whose heaviest row has
19 ones. Our MixColumns 97@3 and 88@5 equal NIST's. We
don't claim any circuit is optimal or the best known. The complete comparison, map by map and
depth by depth, is in [circuits/](circuits/README.md#circuits); the time and hardware behind
each circuit are in [circuits/SEARCH-TIME.md](circuits/SEARCH-TIME.md).

## Contents

| Section | What is in it |
|---|---|
| [circuits/](circuits/README.md) | the smallest circuit our search found at each depth, per map, in NIST's file format, each with its logs and the version that found it, next to NIST's circuits; an independent checker |
| [search/](search/README.md) | XORFlux, an adaptive search for size- and depth-efficient XOR circuits: [how it works](search/HOW-IT-WORKS.md), [how to use it](search/USAGE.md) and [the path to the current version](search/HISTORY.md) |
| [lower-bound-proofs/](lower-bound-proofs/README.md) | two proofs: AES MixColumns needs at least 75 XOR gates, and at least 93 at depth 3; and the certified open cases of the 75 proof at G = 75 (no new bound) |

**Proof status:** the lower-bound proofs were developed with language-model assistance and
have not been peer reviewed; their checkers replay the finite computations, not the
mathematical arguments, so a passing check is not a certification of the proofs. The folder
[mixcolumns-lb75-open-cases](lower-bound-proofs/mixcolumns-lb75-open-cases/) records certified partial
progress inside the 75 proof at G = 75 (open claims 1,508 -> 686 with the November rows, 280 with the
October rows added); it raises no bound.

Maps (59): AES MixColumns and InvMixColumns, the AES S-box bottom linear layer, FOX MU4 and
MU8, and every linear map of NIST's
[circuit repository](https://github.com/usnistgov/Circuits/tree/master/data/slp/2021-linearmaps)
(ARIA, Twofish, Grøstl, CLEFIA, Khazad, Whirlpool, Joltik, Skinny, PRINCE, QARMA and 37 MDS
matrices from the literature).

## Checks

Every push runs the independent circuit checker (`python3 circuits/check.py`) and the XORFlux
test suite on GitHub ([checks](.github/workflows/checks.yml)). The lower-bound checkers run
separately ([proofs](.github/workflows/proofs.yml)): the quick checks on every change to
`lower-bound-proofs/`, the full depth-3 replay (12 minutes on GitHub's runners) monthly and on
request.

## License

[Apache License 2.0](LICENSE), except where a folder has its own license file:
`lower-bound-proofs/mixcolumns-lb75/`, `lower-bound-proofs/mixcolumns-lb93-depth3/supplement/`,
`search/versions/v1-mixcolumns-pipeline/` and the v2–v4 framework versions are MIT. Data from
NIST's circuit repository and circuits from published work keep their own terms; see
[NOTICE](NOTICE).
