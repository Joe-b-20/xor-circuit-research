# xor-circuit-research

[![checks](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/checks.yml/badge.svg)](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/checks.yml)
[![lower-bound proofs](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/proofs.yml/badge.svg)](https://github.com/Joe-b-20/xor-circuit-research/actions/workflows/proofs.yml)

Small, shallow circuits for parts of ciphers: XOR circuits for linear maps and Boolean circuits
with AND gates for the AES S-box and its inverse (also with a direction bit), the two searches
that found them (XORFlux and BoolFlux), how those searches came to be, and two lower-bound proofs
for AES MixColumns.

**208 XOR circuits for 59 linear maps, 73 Boolean circuits for the AES S-box, 53 for its inverse
and 9 for the S-box with a direction bit.** A circuit
is written **G@D**: G two-input gates, with every output at depth at most D (inputs are at depth
0). For the S-box, G counts every gate (AND, XOR, XNOR, NOT) and the number of AND gates and the
AND depth are given with it: NIST's four metrics. Fewer gates is better, and so is a lower depth;
a circuit at a lower depth also counts for every higher one.

## Selected results

Each of these has fewer gates than NIST's circuit for the same map, at the same or a lower depth
(for the S-box: with the same number of ANDs and the same AND depth, unless the row says
otherwise), or reaches a depth NIST's circuits do not, or (for the S-box) needs fewer ANDs at
the same gate depth. NIST's circuits are those of its
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
| AES S-box, 28 ANDs, AND depth 4 | **174@14**, **132@20**, **131@22** | 176@14, 134@20, 132@22 |
| AES S-box, 32 ANDs, AND depth 4 | **114@19**, **111@25** | 117@19 |
| AES S-box, 32 ANDs, AND depth 5 | **108@19**, **105@24** | 109@20, 107@22 |
| AES S-box, 33 ANDs, AND depth 4 | **115@15**, **107@20** | 116@15, 108@20 |
| AES S-box, 34 ANDs, AND depth 4 | **134@13** | 139@13 |
| AES S-box, 35 ANDs, AND depth 3 | **165@13**, **160@14**, **155@15** | 183@13, 172@14, 157@15 |
| AES S-box, AND depth 3, gate depth 12 | **181@12** with 35 ANDs | none (lowest gate depth at AND depth 3: 13) |
| AES S-box, AND depth 4, gate depth 12 | **135@12** with 38 ANDs | 141@12 with 45 ANDs |
| AES inverse S-box, 28 ANDs, AND depth 4 | **153@15**, **143@16**, **135@18**, **133@20** | 156@15, 150@16, 135@20 |
| AES inverse S-box, 32 ANDs, AND depth 4 | **124@15**, **122@16**, **119@18** | 135@15, 128@16 |
| AES inverse S-box, 33 ANDs, AND depth 4 | **122@14**, **117@15**, **110@18** | 123@14, 118@15, 114@18 |
| AES inverse S-box, 34 ANDs, AND depth 4 | **130@13** | 134@13 |
| AES inverse S-box, 35 ANDs, AND depth 3 | **154@14**, **151@15**, **149@17**, **145@19** | 190@14, 157@15 |
| AES inverse S-box, AND depth 3, gate depth 13 | **163@13** with 35 ANDs | none (lowest gate depth at AND depth 3: 14) |
| AES inverse S-box, AND depth 4, gate depth 12 | **136@12** with **40 ANDs** | 141@12 with 45 ANDs |
| AES inverse S-box, AND depth 4, gate depth 11 | **143@11** with **46 ANDs** | 148@10 with 55 ANDs |
| AES S-box with direction select, 36 ANDs, AND depth 6 | **181@23**, **179@24**, **177@27** | none below gate depth 26; 187@27 |
| AES S-box with direction select, AND depth 5 | **238@25**, **183@40** with 43 ANDs | none (lowest AND depth: 6) |

For 46 of the 53 maps taken from NIST's repository, we have a circuit with fewer gates than
NIST's at the same or a lower depth; on the other maps NIST is ahead at some depths. Our
InvMixColumns 118@5 is at the lowest depth possible for InvMixColumns, whose heaviest row has
19 ones. Our MixColumns 97@3 and 88@5 equal NIST's. Against NIST's 104 forward AES S-box circuits, each of our
73 S-box circuits is a new point, and 22 of NIST's 33 Pareto points are dominated by one of ours
(as good in all four metrics and better in at least one); at the other 11 we have only circuits
equal to NIST's, which are not listed. Against NIST's 91 inverse S-box circuits, each of our 53
inverse circuits is a new point, and 22 of NIST's 33 inverse Pareto points are dominated by one of
ours; they come from the runs of 2026-11-16 and 11-17, published with their logs. Against NIST's 9
circuits for the S-box with a direction bit, each of our 9 is a new point and 3 of NIST's 9 Pareto
points are dominated by one of ours; they are built from our forward circuits.
None of ours has fewer than 28 ANDs (NIST's open target is 27) or fewer than 103 gates (we have
103 at gate depth 29, NIST at 32), and all of them descend from NIST's circuits. We don't claim any circuit
is optimal or the best known. The complete comparison, map by map and depth by depth, is in
[circuits/](circuits/README.md#circuits) (the S-box and its inverse in their own sections: [S-box](circuits/README.md#aes-s-box), [inverse](circuits/README.md#aes-inverse-s-box), [with direction select](circuits/README.md#aes-s-box-with-direction-select)); the time and hardware behind each linear-map circuit
are in [circuits/SEARCH-TIME.md](circuits/SEARCH-TIME.md).

## Contents

| Section | What is in it |
|---|---|
| [circuits/](circuits/README.md) | the smallest circuit our searches found at each depth, per linear map, and our AES S-box and inverse S-box circuits (also with a direction bit), in NIST's file format, each with its logs, next to NIST's circuits; one independent checker for all of them |
| [search/](search/README.md) | the two searches: [XORFlux](search/linear/README.md) for XOR circuits of linear maps and [BoolFlux](search/nonlinear/README.md) for Boolean circuits with AND gates, each with how it works, how to use it and how it came to be |
| [lower-bound-proofs/](lower-bound-proofs/README.md) | two proofs: AES MixColumns needs at least 75 XOR gates, and at least 93 at depth 3; and the certified open cases of the 75 proof at G = 75 (no new bound) |

**Proof status:** the lower-bound proofs were developed with language-model assistance and
have not been peer reviewed; their checkers replay the finite computations, not the
mathematical arguments, so a passing check is not a certification of the proofs. The folder
[mixcolumns-lb75-open-cases](lower-bound-proofs/mixcolumns-lb75-open-cases/) records certified partial
progress inside the 75 proof at G = 75 (open claims 1,508 -> 686 with the November rows, 280 with the
October rows added); it raises no bound.

**Current research status (11 November 2026):** the proved bounds are unchanged: AES MixColumns needs
at least 75 XOR gates (75 ≤ L ≤ 88) and at least 93 at depth 3 (93 ≤ D₃ ≤ 97). The work toward 76 is
incomplete. At G = 75, 7,136 of the 7,416 oriented claims are excluded by exact certificates and 280
are open. The exclusions also assume that the 75 proof's framework applies at G = 75, which has not
been reviewed independently, and they rest on new rows whose proofs have had language-model review
only. [ACCOUNTING-G75.md](lower-bound-proofs/mixcolumns-lb75-open-cases/ACCOUNTING-G75.md) lists these
obligations. Work in progress, including experimental search-engine changes that are not on `main`, is
on the branch [`phase-2026-11-09`](https://github.com/Joe-b-20/xor-circuit-research/tree/phase-2026-11-09/research/phase-2026-11-09)
(`research/phase-2026-11-09/CHECKPOINT.md`); the sprint of 7-8 November is kept as the tag
`sprint-2026-11-07-final`.

Maps (59): AES MixColumns and InvMixColumns, the AES S-box bottom linear layer, FOX MU4 and
MU8, and every linear map of NIST's
[circuit repository](https://github.com/usnistgov/Circuits/tree/master/data/slp/2021-linearmaps)
(ARIA, Twofish, Grøstl, CLEFIA, Khazad, Whirlpool, Joltik, Skinny, PRINCE, QARMA and 37 MDS
matrices from the literature). S-box circuits are compared with every forward AES S-box circuit
of NIST's repository at commit
[3d80774](https://github.com/usnistgov/Circuits/tree/3d807741f937d29d3bef4f32f142ccda0cda9070/data/slp/aes)
(104 circuits), inverse S-box circuits with its 91 inverse ones and the ones with a direction bit
with its 9, all kept verbatim in
[search/nonlinear/seeds/](search/nonlinear/seeds/).

## Checks

Every push runs, on GitHub ([checks](.github/workflows/checks.yml)), the independent circuit
checker, which checks every linear-map circuit against its matrix and every S-box circuit (ours
and NIST's) by truth table, with the standard library only and none of the search code
(`python3 circuits/check.py`), and the XORFlux and BoolFlux test suites. The lower-bound
checkers run separately ([proofs](.github/workflows/proofs.yml)): the quick checks on every
change to `lower-bound-proofs/`, the full depth-3 replay (12 minutes on GitHub's runners)
monthly and on request.

## License

[Apache License 2.0](LICENSE), except where a folder has its own license file:
`lower-bound-proofs/mixcolumns-lb75/`, `lower-bound-proofs/mixcolumns-lb93-depth3/supplement/`,
`search/linear/versions/v1-mixcolumns-pipeline/` and the v2–v4 framework versions are MIT. Data
from NIST's circuit repository and circuits from published work keep their own terms; see
[NOTICE](NOTICE).
