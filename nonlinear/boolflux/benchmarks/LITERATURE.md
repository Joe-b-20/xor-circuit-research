# S-box circuit literature: best published sizes (compiled 2026-11-13)

Tables are in `sboxes.json`. This file collects published circuit sizes and states the
cost model for each one. Evidence tags:

- **[read]**: I read the number in the primary text (pdftotext of the PDF, or the HTML page).
- **[secondary]**: the number comes from a later paper or slides that quote it.
- **[unverified]**: the source was not readable here. Treat the number as a lead only.

IACR ePrint, ToSC and TCHES PDFs (and their RUB mirrors) were behind bot-protection pages,
so I could not read them. Stoffelen's FSE 2016 paper was read from the author's copy. The
Reyhani-Masoleh et al. TCHES 2018 paper was read from the DNB archive copy.

## 1. Cost models (definitions)

| Model | Gates counted (each costs 1) | NOT | Source |
|---|---|---|---|
| MC (multiplicative complexity) | number of nonlinear 2-input gates; XOR/XNOR/NOT are free | free | Stoffelen FSE'16 Sect. 2 [read]; CHM'11 Def. 2 [read] |
| BGC (bitslice gate complexity) | AND, OR, XOR, NOT (2-input, plus unary NOT); NAND/NOR/XNOR **excluded** | counted | Stoffelen FSE'16 Sect. 2 and Table 2 [read]; CHM'11 Def. 1 calls this "GC" |
| GC (gate complexity) | all 2-input gates AND, OR, XOR, NAND, NOR, XNOR (and constants); fan-in <= 2 | no NOT gate in the encoding (a NOT would have to be a gate) | Stoffelen FSE'16 Sect. 2 and Table 4 [read] |
| Depth (Stoffelen) | longest input-output path in a GC-type circuit with layer width <= w | - | Stoffelen FSE'16 Sect. 3.5 [read] |
| NIST circuit-complexity | basis {AND, XOR, XNOR} (+NOT); size = #gates; MC = #AND; AND-depth; gate depth | AES entries: G = #AND + #XOR + #XNOR, no NOT column; SHA-256 entries do count NOT | csrc.nist.gov list-of-circuits [read] |
| GE (area) | sum of cell areas normalised to NAND2 = 1; library-specific; multi-input cells allowed | 0.5-0.75 GE | LIGHTER/PEIGEN/Wei et al./Jia et al. |

Stoffelen's encoding notes [read]:
- Every gate in the MC encoding may take an affine combination of earlier signals. So MC
  counts AND gates with free XOR/NOT, and an OR counts as nonlinear.
- In BGC/GC, each gate input is a single earlier signal.

UMC 180 nm GE costs (Wei et al. CiC 2024 Table 9 [read]):

| Cell | GE |
|---|---|
| NOT | 0.67 |
| AND, OR | 1.33 |
| NAND, NOR | 1.00 |
| NANDN, NORN | 1.67 |
| XOR | 2.67 |
| XNOR | 2.00 |
| NAND3, NOR3 | 1.33 |
| AND3, OR3 | 2.33 |
| XOR3, XNOR3 | 4.67 |

Table 9 of the same paper also gives TSMC 65/28, SMIC 130/65, Nangate 45/15, STD90 350 nm
and STM 65.

General bounds:
- Every bijective 4x4 S-box has MC <= 5 (Zajac and Jokay, Cryptogr. Commun. 6(3), 2014,
  https://doi.org/10.1007/s12095-014-0100-y). [secondary: abstract via search]
- Every 4-variable Boolean function has MC <= 3 (Boyar, Matthews, Peralta, J. Cryptology
  2013, Sect. 2.1, https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=908384). [read]
- Maximum MC is 3 for B4 (8 classes), 4 for B5 (48 classes) and 6 for B6 (150367 classes)
  (NIST list-of-circuits; https://eprint.iacr.org/2018/002). [read on the NIST page]

## 2. 4-bit S-boxes

Key sources:
- **Sto16**: Stoffelen, FSE 2016, https://ko.stoffelen.nl/papers/fse2016-sboxoptimization.pdf
  (ePrint 2016/198). Exact SAT results.
- **CHM11**: Courtois, Hulme, Mourouzis, https://eprint.iacr.org/2011/475 (IMA copy read).
- **Sov23**: Sovyn et al., CEUR Vol-3504 paper 3, Table 7. Heuristic BGC over
  {AND, OR, XOR, NOT}. It also lists the LIGHTER/PEIGEN BGC ("L/P"). Upper bounds only.
- **Wei24**: Wei, Sun, Liu, Hu, Zhang, IACR CiC 1(4) 2024, https://cic.iacr.org/p/1/4/20.
  Gives GE for LIGHTER, PEIGEN and its own tool under one library each.
- **Lu21**: Lu, Wang, Hu, Fan, Wu, Wang, INDOCRYPT 2021, https://eprint.iacr.org/2021/1644.
  SAT search for minimum GE with 2-, 3- and 4-input gates.

The user's "Lu, Mesnager, Cui, Fan, Wang" reference appears to be a different paper. It is
an STP-based S-box *design* paper (DCC 2022) [unverified]. The GE-optimality SAT paper is
Lu21.

| S-box | Model | Best published | Optimal? | Source |
|---|---|---|---|---|
| PRESENT (=LED) | MC | 4 | yes, UNSAT for 3 | CHM11 Thm 1 [read] |
| PRESENT | BGC | 14 (2 AND, 2 OR, 9 XOR, 1 NOT) | upper bound; no optimality proof found | CHM11 Fig. 1 [read]; Sov23 and L/P also 14 [read] |
| PRESENT | GE | 21.32 GE UMC180 (L/P); 22.25 SMIC65; 24.00 TSMC65 (LIGHTER) | heuristic | Wei24 Tables 3, 10 [read] |
| GIFT | BGC | 11 (designers' bitsliced code: 3 AND, 1 OR, 6 XOR, 1 NOT) | upper bound | GIFT-COFB spec SubCells [read]; Sov23 = 11 [read] |
| GIFT | GC | 10 "with XNOR" | upper bound | GIFT-COFB spec Sect. 5 text [read] |
| GIFT | MC | <= 4 (3 AND + 1 OR in the designers' code) | bound only | derived from the spec code |
| GIFT | GE | 16.00 GE UMC180 (L/P) | heuristic | Wei24 Table 10 [read] |
| SKINNY-64 S4 | GC | 8 (4 NOR + 4 XOR, spec definition) | GE-optimal per Lu21 [secondary: abstract]; exact GC not stated | spec; Lu21 |
| SKINNY-64 S4 | BGC | 11 ({AND,OR,XOR,NOT}); 10 with ANDN | heuristic | Sov23 [read] |
| SKINNY-64 S4 | GE | 13.32 UMC180; 13.00 SMIC65; 13.99 TSMC28 (Wei) | Lu21: literature implementation optimal | Wei24 Tables 3, 4, 10 [read] |
| PRINCE | BGC | 16 (L/P 18); 16 with ANDN (L/P 17) | heuristic | Sov23 [read] |
| PRINCE | MC | <= 5 (generic bound only) | open here | Zajac-Jokay |
| Midori Sb0 (=MANTIS/CRAFT) | BGC | 13 (L/P 14) | heuristic | Sov23 [read] |
| Midori Sb0 | GE | 19.99 UMC180 (Wei; L/P 20.66); 13.98 TSMC28 (Wei; LIGHTER 28.00) | heuristic | Wei24 Tables 3, 10 [read] |
| Midori Sb1 | BGC | 15 (L/P 17) | heuristic | Sov23 [read] |
| Piccolo (=Joltik) | MC | 4 | yes | Sto16 Table 1 [read] |
| Piccolo | BGC | 10 (1 AND, 3 OR, 4 XOR, 2 NOT) | yes | Sto16 Table 3 [read] |
| Piccolo | GC | 8 (2 OR, 1 XOR, 2 NOR, 3 XNOR) | yes | Sto16 Table 5 [read] |
| Piccolo | depth | 4 (w = 2) | UNSAT at k=4,w=1 and k=3,w=10 | Sto16 Table 6 [read] |
| Piccolo | GE | 12.99 UMC180 | optimal per Lu21 | Wei24 Table 10 [read]; Lu21 |
| RECTANGLE | MC | 4 | yes | Sto16 Table 1 [read] |
| RECTANGLE | BGC | in {10, 11, 12}; 12-gate circuit (4 OR, 7 XOR, 1 NOT) | open in Sto16 | Sto16 Table 3 [read] |
| RECTANGLE | GC | in {10, 11}; 11-gate circuit | open in Sto16 | Sto16 Table 5 [read]. Zhang-Huang 2023 (https://eprint.iacr.org/2023/1721) says it determines GC of RECTANGLE and its inverse; value not readable here [unverified] |
| RECTANGLE | depth | 3 (w = 6) | UNSAT at k=3,w=4 | Sto16 Table 6 [read] |
| RECTANGLE | GE | 18.00 GE (library not given in the abstract) | SAT-minimal in Lu21 model | Lu21 abstract [read]; L/P 18.33 UMC180 (Wei24) |
| PRIDE (=Prost) | MC / BGC / GC | 4 / 8 (4 AND, 4 XOR) / 8 | all proven | Sto16 Tables 1, 3, 5 [read] |
| KLEIN | BGC | 17 (L/P 17) | heuristic | Sov23 [read] |
| Noekeon | BGC | 12 (L/P 12) | heuristic | Sov23 [read] |
| Serpent S0..S7 | BGC | 14, 14, 13, 15, 15, 15, 14, 16 (with ANDN: 14, 14, 13, 14, 14, 14, 14, 15) | heuristic | Sov23 [read]; L/P equal except S3/S4/S5/S7 with ANDN |

Other Sto16 4-bit results [read]:
- LAC: MC 4, BGC 11, GC 10.
- Minalpher: MC 5, BGC >= 11.

Lowest possible area of any optimal 4-bit S-box (Jia et al., ToSC 2025(1), ePrint 2025/386,
UMC 180 nm) [read: abstract]:

| Gates allowed / constraint | Minimum area | Depth |
|---|---|---|
| 2-, 3- and 4-input gates | 11 GE | 3 |
| no 4-input gates | 12 GE | 4 |
| no fixed points | 12.33 GE | same |
| all coordinates of degree 3 | 14 GE (14.33 GE without fixed points) | 8 |

## 3. 3-bit and 5-bit S-boxes

| S-box | Model | Best published | Optimal? | Source |
|---|---|---|---|---|
| PRINTcipher (3-bit) | GE | 9.00 UMC180 (PEIGEN = Wei); 8.99 Nangate45 (Wei) | Wei's 3-bit search is systematic | Wei24 Tables 10, 11 [read] |
| chi3 | - | no dedicated result found | - | compute it yourself |
| Ascon | MC | 5 | yes | Sto16 Table 1 [read] |
| Ascon | BGC | <= 22 (designers' code: 11 XOR, 5 AND, 6 NOT); 17 if ANDN counts as 1 | upper bound | Ascon v1.2 spec Fig. 5 [read] |
| Ascon | other | Feng et al. (IEEE TCAS-I 2024) report 1 fewer instruction than the best known (their software model); Lu21 gives Ascon GE results (values not read) | - | [secondary] |
| Keccak chi5 | MC | 5 | yes | Sto16 Table 1 [read] |
| Keccak chi5 | BGC | <= 13 (3 AND, 2 OR, 5 XOR, 3 NOT); naive 15 (5 NOT + 5 AND + 5 XOR) | upper bound | Sto16 Table 3 [read] |
| Keccak chi5 | GE | 17 GE UMC180 (Lu21: 17.66; designers 23.33) | SAT-based | Jia et al. 2025 abstract [read] |
| PRIMATEs | MC | in {6, 7}; 7-AND circuit; combined circuit 4 AND, 3 OR, 31 XOR, 5 NOT | conjectured 7 | Sto16 Sect. 4 [read] |
| ICEPOLE | MC | 6 | yes | Sto16 Table 1 [read] |

Sto16 got no GC results for its 5-bit S-boxes [read].

## 4. 8-bit S-boxes other than AES

| S-box | Model | Best published | Source |
|---|---|---|---|
| SKINNY-128 S8 | GC | <= 16 (8 NOR + 8 XOR, spec construction); MC <= 8 | SKINNY spec Fig. 2 [read] |
| SKINNY-128 S8 | GE | 26.67 GE UMC180, "first optimized implementation" | Jia et al. 2025 abstract [read] |
| SM4, Camellia | - | not researched here (both have tower-field circuits in the literature) | - |

## 5. AES S-box

Notation: G = total gates, A = #AND (or NAND), X = #XOR + #XNOR, D = gate depth,
AD = AND-depth.

The NIST model applies to the first part of the table: 2-input {AND, XOR, XNOR}, NOT not
counted (G = A + X).

### {AND, XOR, XNOR} circuits

| Circuit | G | A | X | D | AD | Source |
|---|---|---|---|---|---|---|
| Boyar-Peralta (SEA 2010 / BMP J. Cryptol. 2013) | 115 | 32 | 83 | 28 | 6 | ePrint 2009/191; BMP Sect. 4 [read]; NIST `aes-sbox-fwd-g115-a32-d28-ad6.slp` |
| Boyar-Peralta, improved by 2 XORs in 2013 ("forward 2", "Boyar-Op113") | 113 | 32 | 81 | 27 | 6 | NIST `aes-sbox-fwd-g113-a32-d27-ad6.slp` [read]; RTA18 Tables 10-11 [read] (CAD gives depth 27; BFP17 states 28) |
| Boyar-Peralta depth-16 (SEC 2012) | 128 | 34 | 94 | 16 | 4 | ePrint 2011/332; NIST `g128-a34-d16-ad4` [read]; RTA18 [read] |
| Boyar-Find-Peralta depth-16 ("Boyar-Dp16-2"; BFA 2017, Cryptogr. Commun. 2019) | 125 | 34 | 91 | 16 | critical path 13 XOR + 3 AND | RTA18 Tables 10-11 [read] |
| Inverse S-box (Boyar-Peralta) | 121 / 127 | 34 | 87 / 93 | 21 / 16 | 4 | NIST `aes-sbox-rev-g121-a34-d21-ad4`, `g127-a34-d16-ad4` [read] |

The 32-AND structure is three GF(2^4) multiplications at 9 AND each plus one GF(2^4)
inversion at 5 AND (NIST project page [read]).

### NIST list-of-circuits entries added 2026

Source: https://csrc.nist.gov/Projects/circuit-complexity/list-of-circuits [read].
Files are `aes-sbox-a*-ad*-g*-gd*-xx*-*.circ.txt`.

| A | AD | G | GD | X | Metric |
|---|---|---|---|---|---|
| 32 | 5 | **104** | 30 | 72 | A/G |
| 32 | 5 | 109 | 20 | 77 | A/GD |
| 33 | 4 | 105 | 25 | 72 | AD/G |
| 33 | 4 | 108 | 20 | 75 | AD/GD |
| 28 | 5 | 124 | 27 | 96 | A/G |
| 28 | 4 | 131 | 32 | 103 | A/AD/G |
| 28 | 4 | 177 | 14 | 149 | A/AD/GD |
| 34 | 4 | 124 | 15 | 90 | - |
| 35 | 3 | 157 or 139 | 15 or 31 | 122 or 104 | - |
| 36 | 4 | 137 | 14 | 101/102 | - |
| 38 | 4 | 148 | 13 | 110 | - |
| 45 | 4 | 151 | 12 | 106 | - |
| 51 | 4 | 157 | 11 | 106 | - |

Notes on this list:
- The page credits the A = 28 circuits to Milad Nasr (2026-09-24).
- The page states targets A <= 27, G <= 100, and G <= 110 with GD <= 14.
- The a35 and a36 rows are internally inconsistent on the page (file names vs. columns),
  so check the files directly.

### Other gate libraries (not comparable to the NIST count)

| Circuit | Cell composition | Area | Delay | Source |
|---|---|---|---|---|
| Canright 2005 | 80 XOR/XNOR + 34 NAND + 6 NOR | 200 GE | - | RTA18 Table 10 [read] |
| RTA18 lightweight (combined) | 63 XOR2/XNOR2 + 3 XOR3 + 27 NAND2 + 4 OAI32 + 7 NOR2 + 4 NOT | 182.25 GE | - | RTA18 Table 10 [read] |
| RTA18 lightweight (all-structural) | 69 X + 39 NAND2 + 4 NAND3 + 3 NOR2 + 4 NOT | 188 GE | CPD 16 XOR + 4 NAND + 1 NOT | RTA18 Tables 10-11 [read] |
| RTA18 fast | 79 X + 39 NAND2 + 4 NAND3 + 3 NOR2 + 4 NOT | 208 GE | CPD 11 XOR + 5 NAND + 1 NOT | RTA18 Tables 10-11 [read] |

- RTA18 is Reyhani-Masoleh, Taha, Ashmawy, TCHES 2018(2) 298-336,
  https://doi.org/10.13154/tches.v2018.i2.298-336.
- GE values use the 65 nm costs XOR 2, AND/OR 1.25, NAND/NOR 1, NAND3 1.25, NOT 0.75.
- RTA18's point is that AND-to-NAND rewriting alone makes the 113-gate circuit 194 GE
  instead of 202 GE.

**Maximov-Ekdahl, TCHES 2019(4) 91-125** (ePrint 2019/802) [unverified]:
- They claim the smallest and fastest forward, inverse and combined AES S-boxes, using
  XOR/XNOR/NAND/NOR/MUX cells and "floating multiplexers".
- I could not read their gate counts (PDF blocked). The slides give only GF(2^4)-level
  numbers (Section 6).
- Wei24 later cut ME19's 4x4 tower-field sub-block from 18.31 GE to 16.65 GE (STD90/MDL90
  350 nm). They call the result the lightest AES S-box known [read], but give no total.

## 6. Sanity-check components

### GF(2^4) inversion
- MC = 5 [read]. Proof: one AND for a degree-2 term, then one per degree-3 output.
- Circuit: 5 AND + 11 XOR = 16 gates.
- Earlier constructions: Paar 10 AND + 15 XOR; Canright 9 AND/NAND + 14 XOR/XNOR, later
  8 NAND + 2 NOR + 9 XOR/XNOR.
- All of the above: BMP J. Cryptol. 2013 Sect. 2.1.
- Maximov-Ekdahl slides [secondary]:
  - [BP12] inversion: 17 gates, depth 4 over {AND, XOR}.
  - New: 9 gates, depth 3 with MUX cells (about 6 MUX + NAND + NOR + XNOR).
  - New: 15 gates, depth 3 with ordinary 2-input gates.
- RTA18 normal-basis inverter: 12 NAND2 + 4 NAND3 + 4 XOR2 + 4 NOT, delay 3 NAND + 1 NOT
  (Prop. 2) [read].

### GF(2^4) multiplication
- 9 AND suffice (Karatsuba-type; used 3x in the 32-AND AES circuit, NIST page [read]).
- 9 is the bilinear rank over GF(2).
- arXiv 2608.30238 (2026) claims 9 is also the unrestricted MC of 4-term binary polynomial
  multiplication [secondary; not independently reviewed].
- XOR count of an optimal GF(2^4) multiplier: no reliable source found.
- RTA18 two output multipliers sharing one operand: 17 XOR + 10 NAND (Canright 20 XOR +
  9 NAND) [secondary: RTA18 slides].

### Full adder and majority
Checked by my own exhaustive search (`small_exhaustive.py`), which agrees with Knuth,
TAOCP 4A Sect. 7.1.2:

| Function | MC | Size over B2 / {AND,OR,XOR,NOT} | Size over {AND, XOR} (+const 1) |
|---|---|---|---|
| maj3 | 1 | 4, optimal | 4, optimal: ((a^b)&(a^c))^a |
| full adder (sum, carry) | 1 | 5 (2 XOR, 2 AND, 1 OR), optimal | 5 (4 XOR + 1 AND), optimal |

Other references, numbers not read: Ullrich et al. 2011 (SKEW, optimal bitsliced 4x4
search); Bolzer-Duval-Minier 2025 (ePrint 2025/1505, {AND, XOR} at AND-depth 1, up to
9 bits); Zhang-Huang 2023 (ePrint 2023/1721, new bounds for the Sto16 S-boxes).

## 7. Zhang-Huang 2023 (read from the PDF supplied by the user, 2026-11-13)

Zhang, Huang, "Optimizing S-box Implementations Using SAT Solvers: Revisited", ePrint 2023/1721.
Definitions (Sect. 2): BGC over {XOR, OR, AND, NOT}; GC over {XOR, XNOR, AND, OR, NAND, NOR}
plus NOT (Table 2 and Remark 2) - no ANDN/ORN, so our model gc (which has ANDN and ORN) is not
the literature GC; models/gc6.json is.  [k1, k2] = UNSAT at k1-1, SAT at k2.

| S-box | BGC (Sto16 -> ZH23) | GC (ZH23) | MC |
|---|---|---|---|
| Ascon | - -> [12, 16] | [12, 15] | 5 |
| Keccak chi5 | <= 13 -> [12, 13] | [11, 13] | 5 |
| RECTANGLE | [10, 12] -> [11, 12] | 11 (determined; Sto16 [10, 11]) | 4 |
| RECTANGLE^-1 | - | 11 | - |
| Minalpher | [11, inf] -> [12, 17] | [11, 14] | 5 |
| ICEPOLE | [12, 26] | [12, 21] | 6 |
| PRIMATEs | [12, 27] | [12, 23] | 7 (determined) |

Depth (k, w) SAT results (ZH23 Table 12): Ascon (3, 6), Keccak (2, 10).
