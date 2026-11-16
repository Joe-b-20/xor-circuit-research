# Published S-box circuits

Best published circuit sizes for the functions in [sboxes.json](sboxes.json), by gate library,
with sources. BoolFlux's model files in [../models/](../models/) implement these libraries. Sizes
are upper bounds unless marked optimal. Where the source could not be read and the number comes
from a later paper or an abstract, the row says "via".

## Gate libraries

| Library | Gates (each costs 1) | NOT | Source |
|---|---|---|---|
| MC | AND (any nonlinear 2-input gate); XOR, NOT free | free | Stoffelen, FSE 2016, Sect. 2; Courtois–Hulme–Mourouzis 2011, Def. 2 |
| BGC (`bgc`) | AND, OR, XOR | 1 | Stoffelen 2016, Sect. 3 |
| GC (`gc6`) | AND, OR, XOR, NAND, NOR, XNOR | 1 | Stoffelen 2016, Table 4; Zhang–Huang 2023, Table 2 |
| NIST (`nist`) | AND, XOR, XNOR | 1 (as in [circuits/README.md](../../../../circuits/README.md)) | NIST circuit complexity project |
| GE | cell area, NAND2 = 1, library-specific | 0.5–0.75 GE | Wei et al. 2024, Table 9 |

## 4-bit S-boxes

| S-box | Library | Best published | Optimal? | Source |
|---|---|---|---|---|
| PRESENT | MC | 4 | yes | CHM11, Thm. 1 |
| PRESENT | BGC | 14 | not known | CHM11, Fig. 1; also Sov23 |
| GIFT | BGC | 11 | not known | GIFT-COFB specification; Sov23 |
| GIFT | GC | 10 | not known | GIFT-COFB specification, Sect. 5 |
| SKINNY-64 | GC | 8 (4 NOR + 4 XOR) | GE-optimal (Lu21, via abstract) | SKINNY specification |
| SKINNY-64 | BGC | 11 | not known | Sov23 |
| PRINCE | BGC | 16 | not known | Sov23 |
| Midori Sb0 / Sb1 | BGC | 13 / 15 | not known | Sov23 |
| Piccolo | MC / BGC / GC | 4 / 10 / 8 | all optimal | Sto16, Tables 1, 3, 5 |
| RECTANGLE | MC | 4 | yes | Sto16, Table 1 |
| RECTANGLE | BGC | 12 | optimum in [11, 12] | Sto16, Table 3; ZH23 |
| RECTANGLE | GC | 11 | yes | ZH23, Table 11 |
| PRIDE | MC / BGC / GC | 4 / 8 / 8 | all optimal | Sto16 |
| LAC | MC / BGC / GC | 4 / 11 / 10 | | Sto16 |
| KLEIN, Noekeon | BGC | 17, 12 | not known | Sov23 |
| Serpent S0–S7 | BGC | 14, 14, 13, 15, 15, 15, 14, 16 | not known | Sov23 |

Every bijective 4-bit S-box has MC ≤ 5 (Zajac–Jokay 2014, via abstract), every 4-variable
Boolean function MC ≤ 3 (Boyar–Matthews–Peralta 2013).

## 5-bit S-boxes

| S-box | Library | Best published | Optimal? | Source |
|---|---|---|---|---|
| Ascon | MC | 5 | yes | Sto16, Table 1 |
| Ascon | BGC / GC | 16 / 15 | optimum in [12, 16] / [12, 15] | ZH23, Tables 10, 11 |
| Keccak χ | MC | 5 | yes | Sto16, Table 1 |
| Keccak χ | BGC / GC | 13 / 13 | optimum in [12, 13] / [11, 13] | Sto16, Table 3; ZH23 |
| Minalpher | MC; BGC / GC | 5; 17 / 14 | BGC in [12, 17], GC in [11, 14] | Sto16; ZH23 |
| ICEPOLE | MC | 6 | yes | Sto16, Table 1 |
| PRIMATEs | MC | 7 | yes (ZH23) | Sto16, Sect. 4; ZH23 |

## AES S-box

The NIST library and its counts are those of NIST's circuit repository, pinned at commit
`3d807741f937d29d3bef4f32f142ccda0cda9070`: 104 forward S-box circuits (folders `aes-sbox/`,
`sbox/`, `old-2020/`), mirrored in [search/nonlinear/seeds/](../../seeds/). The comparison of
our circuits with all of them is in [circuits/README.md](../../../../circuits/README.md). The
earlier circuits in that library from the literature:

| Circuit | G | A | Depth | AND depth | Source |
|---|---|---|---|---|---|
| Boyar–Peralta | 115 | 32 | 28 | 6 | ePrint 2009/191; BMP13, Sect. 4 |
| Boyar–Peralta, 2 XORs fewer | 113 | 32 | 27 | 6 | NIST `aes-sbox-fwd-g113-a32-d27-ad6.slp` |
| Boyar–Peralta, depth 16 | 128 | 34 | 16 | 4 | ePrint 2011/332 |
| Boyar–Find–Peralta, depth 16 | 125 | 34 | 16 | | Cryptogr. Commun. 2019 (via RTA18, Tables 10–11) |
| inverse S-box, Boyar–Peralta | 121 / 127 | 34 | 21 / 16 | 4 | NIST `aes-sbox-rev-*.slp` |

In other cell libraries (areas not comparable with gate counts): Canright 2005, 200 GE;
Reyhani-Masoleh–Taha–Ashmawy 2018, 182.25 GE (smallest) and 208 GE (fastest) in a 65 nm library;
Maximov–Ekdahl 2019 (TCHES 2019(4)) with XOR/XNOR/NAND/NOR/MUX cells.

## Components

| Function | Result | Source |
|---|---|---|
| GF(2⁴) inversion | MC 5; 5 AND + 11 XOR | BMP13, Sect. 2.1 |
| GF(2⁴) multiplication | 9 AND (bilinear complexity μ₂(4) = 9); unrestricted MC not established | Chudnovsky–Chudnovsky 1988; Ballet et al. 2021; Boyar–Find 2018 |
| majority of 3 | MC 1; 4 gates over {AND, XOR}, optimal | Knuth, TAOCP 4A, 7.1.2 |
| full adder | MC 1; 5 gates (4 XOR + 1 AND), optimal | Knuth, TAOCP 4A, 7.1.2 |

## References

- **BMP13**: Boyar, Matthews, Peralta, "Logic minimization techniques with
  applications to cryptology", J. Cryptology 26, 2013.
- **CHM11**: Courtois, Hulme, Mourouzis, ePrint 2011/475.
- **Lu21**: Lu, Wang, Hu, Fan, Wu, Wang, INDOCRYPT 2021, ePrint 2021/1644.
- **RTA18**: Reyhani-Masoleh, Taha, Ashmawy, TCHES 2018(2), 298–336,
  https://doi.org/10.13154/tches.v2018.i2.298-336.
- **Sov23**: Sovyn et al., CEUR-WS Vol-3504, paper 3, Table 7 (heuristic BGC).
- **Sto16**: Stoffelen, "Optimizing S-box implementations for several criteria using SAT
  solvers", FSE 2016, ePrint 2016/198.
- **Wei24**: Wei, Sun, Liu, Hu, Zhang, IACR Communications in Cryptology 1(4), 2024, https://cic.iacr.org/p/1/4/20.
- **ZH23**: Zhang, Huang, "Optimizing S-box implementations using SAT solvers: revisited",
  ePrint 2023/1721.
- Zajac, Jokay, Cryptogr. Commun. 6(3), 2014, https://doi.org/10.1007/s12095-014-0100-y.
- NIST circuit complexity project:
  https://csrc.nist.gov/projects/circuit-complexity/list-of-circuits; repository
  https://github.com/usnistgov/Circuits.
