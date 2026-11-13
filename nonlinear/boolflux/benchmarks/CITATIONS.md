# Citations for "optimal" / "minimum" / "proved" claims (checked 2026-11-13)

Scope: every optimality claim in `LEDGER.md` (sections 1 and 2) and the related rows of
`benchmarks/LITERATURE.md`. For each claim this file gives the model it holds in, the exact source
location, and the kind of evidence. The evidence kinds are:

- **SAT**: SAT for k plus UNSAT for k-1.
- **exhaustive**: complete computer enumeration.
- **theorem**: a written proof.
- **UB only**: a circuit exists; there is no lower bound.

The last column gives wording we may use.

Evidence tags:

- **[read]**: I read the passage in the primary text.
- **[secondary]**: the passage is quoted by a later source that I read.
- **[unverified]**: I could not read the source.

## 0. Sources read for this check

| Key | Source | How read |
|---|---|---|
| Sto16 | K. Stoffelen, "Optimizing S-box Implementations for Several Criteria using SAT Solvers", FSE 2016, LNCS 9783 (ePrint 2016/198). Author copy: https://ko.stoffelen.nl/papers/fse2016-sboxoptimization.pdf | pdftotext of the author copy [read]. Section numbers below follow the author copy: Sect. 2 is the SLP problem; the cost definitions are at the start of Sect. 3. |
| ZH23 | F. Zhang, Z. Huang, "Optimizing S-box Implementations Using SAT Solvers: Revisited", ePrint 2023/1721 | pdftotext of the PDF the user supplied [read] |
| BMP13 | J. Boyar, P. Matthews, R. Peralta, "Logic Minimization Techniques with Applications to Cryptology", J. Cryptology 26(2), 2013. NIST copy: https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=908384 | pdftotext of the NIST copy [read] |
| CHM11 | N. Courtois, D. Hulme, T. Mourouzis, "Solving Circuit Optimisation Problems in Cryptography and Cryptanalysis", IMA Mathematics in Defence 2011 (ePrint 2011/475). IMA copy: https://cdn.ima.org.uk/wp/wp-content/uploads/2011/10/Solving-Optimisation-Problems-in-Cryptography-Its-Implementation-and-Cryptanalysis.pdf | pdftotext of the IMA copy [read] |
| Sov23 | Y. Sovyn, I. Opirskyy, O. Mykhaylova, "Finding a Bit-Sliced Representation of 4x4 S-Boxes based on Typical Logic Processor Instructions", CQPC 2023, CEUR-WS Vol-3504, paper 3, pp. 26-38, https://ceur-ws.org/Vol-3504/paper3.pdf | pdftotext [read] |
| BCPRRR21 | S. Ballet, J. Chaumine, J. Pieltant, M. Rambaud, H. Randriambololona, R. Rolland, "On the tensor rank of multiplication in finite extensions of finite fields and related issues in algebraic geometry", Russian Math. Surveys 76(1), 2021, 29-89; arXiv:1906.07456v2 | pdftotext of the arXiv v2 [read] |
| BF18 | J. Boyar, M. G. Find, "Multiplicative Complexity of Vector Valued Boolean Functions", Theoret. Comput. Sci. (2018); arXiv:1407.6169 (MFCS 2014 preliminary version) | ar5iv HTML [read] |
| Kul18 | A. S. Kulikov, "Improving Circuit Size Upper Bounds Using SAT-Solvers", DATE 2018, https://past.date-conference.com/proceedings-archive/2018/pdf/1066.pdf | pdftotext [read] |
| ME19-slides | A. Maximov, P. Ekdahl, TCHES 2019 talk slides, as transcribed at https://www.sambuz.com/doc/new-circuit-minimization-techniques-for-smaller-and-ppt-presentation-804804 | HTML [read]; the paper itself is blocked |

## 1. Cost models in the sources

| Model | Sto16 | ZH23 | Notes for our models |
|---|---|---|---|
| MC | Start of Sect. 3: "smallest number of nonlinear gates with fan-in 2". With {AND, OR, XOR, NOT}, the count is ANDs + ORs. The encoding (Sect. 3.2) uses AND gates whose inputs are affine combinations of the inputs and earlier ANDs. Outputs are *linear* combinations, with no constant term. | Sect. 2.2: the minimum number of ANDs over {XOR, AND, NOT}. Sect. 4.1, Eq. (9): outputs are *affine*. Remark 1 shows that Sto16's linear-output encoding can return a false UNSAT when an output ANF has the constant term 1. Sect. 6: "we verified the correctness" of all Sto16 MC values. | XOR, XNOR and NOT are free. OR counts as nonlinear. Our `A` (nonlinear gates) matches. |
| BGC | Start of Sect. 3: the smallest number of operations in {AND, OR, XOR, NOT}. NAND, NOR and XNOR are excluded. Table 2 gives the gate encoding. **NOT is counted**: Table 3's Piccolo row is 1 AND + 3 OR + 4 XOR + 2 NOT = 10. | Sect. 2.2, same definition. Table 1 gives the gate encoding. A gate input may be the constant 0, an S-box input or an earlier gate (Sect. 4.2, item 4). | Matches our `bgc` (AND, OR, XOR, NOT, each 1). Sov23's "STD" set is the same (NOT, AND, OR, XOR), and its constants 0x0000/0xffff cost 0 (Sect. 2.2). |
| GC | Start of Sect. 3: all fan-in-at-most-2 gates. Table 4 lists the gate types 0, 1, XOR, XNOR, AND, NAND, OR, NOR. **Constants are gate types of cost 1.** NOT is not a separate type. | Sect. 2.2 and Sect. 4.3: XOR, XNOR, AND, OR, NAND, NOR (Table 2, which also has the constants 0 and 1). NOT is realised as NAND(x,x) or XNOR(x,0) and **costs 1**. Remark 2: allowing NOT can lower GC (a 3-bit example drops from 5 to 4). | Equivalent to our `gc6` (the six binary gates plus NOT, each 1). The difference in how constants are handled does not matter for bijective S-boxes. Our `gc` model (with ANDN and ORN) is **not** the literature GC. |
| Depth | Sect. 3.5: the depth is "the length of the longest paths from an input gate to an output gate". The decision problem asks for depth <= k with **at most w gates per layer**. Gates use the Table 4 types (GC set), so a NOT (as NAND or XNOR) takes a layer. Table 6 gives SAT (k, w) and UNSAT boundaries. | Sect. 2.2 and Sect. 4.4: same (k, w) problem over {XOR, OR, AND, NOT, NAND, NOR, XNOR}. Table 12 gives the results. | Our GD (inputs at 0, each gate +1) is the same path notion, but we impose **no width bound w**. So Sto16 and ZH23 depth results are (k, w) statements. An UNSAT at (k, w) does not prove that depth k is impossible with wider layers. |
| CHM11 | Def. 1 calls {XOR, OR, AND, NOT} "Bitslice Gate Complexity (GC)". This is Sto16's BGC. Def. 2: MC is the minimum number of ANDs "with an unlimited number of XOR and NOT gates". | - | Do not confuse CHM11's "GC" with Sto16's GC. |

Range notation (ZH23 Sect. 6): "[k1, k2]" means UNSAT at k1 - 1 and SAT at k2. The optimum
lies in [k1, k2], and only k1 = k2 is a determination.

## 2. Claim table

| # | Claim (as written or as it may be written) | Holds? | Proof / source (with location) | Wording to use |
|---|---|---|---|---|
| 1a | maj3: 4 gates over B2, also over {AND, OR, XOR, NOT} and {AND, XOR}, minimum | Yes. The lower bound carries over: {AND, XOR}, {AND, XOR, NOT} and {AND, OR, XOR, NOT} are subsets of B2, so their minimum size is >= C_B2 = 4. A 4-gate {AND, XOR} circuit exists: ((a^b)&(a^c))^a. | **Our exhaustive search** (`small_exhaustive.py`, per LITERATURE.md Sect. 6). Knuth, TAOCP 4A, Sect. 7.1.2 lists optimum chains for small functions [unverified: not read here; Kul18 Sect. I says Knuth lists "optimum size circuits for all symmetric functions on four variables" [read]]. No primary statement of "maj3 = 4" was read. | "4 gates, 1 AND; minimum over all 2-input gates (hence over {AND, XOR}) by our exhaustive search; agrees with Knuth TAOCP 4A Sect. 7.1.2 [not re-read]." |
| 1b | maj3: MC 1 | Yes (theorem, elementary). maj3 has degree 2, so it needs at least 1 AND, and the 1-AND circuit above exists. | Degree argument (any nonlinear function needs >= 1 AND). | "MC 1 (degree 2; 1-AND circuit)." |
| 1c | Full adder (sum, carry): 5 gates over B2, minimum; hence also minimum over {AND, XOR} and {AND, OR, XOR, NOT} | Yes. | Kul18, Sect. III: "It is known that gates(SUM3) = 5 (full adder)". Here gates() is the size over all binary operations B2 (Kul18 Sect. I) [read; the paper cites no proof]. Red'kin 1981 proved 5n - 3 for the n-bit adder ADD_n, a different function [secondary: Goncharov-Kulikov-Levtsov, STACS 2026]. Our exhaustive search also gives 5. Knuth 7.1.2 [unverified]. | "5 gates (4 XOR + 1 AND), MC 1; 5 is the minimum over all 2-input gates (known, e.g. Kulikov DATE 2018 Sect. III; confirmed by our exhaustive search)." |
| 1d | Full adder MC 1 | Yes (elementary). The carry is nonlinear, and the 1-AND circuit exists. | Degree argument. | "MC 1." |
| 2a | GF(2^4) multiplication (two 4-bit inputs, modulus x^4+x+1) has bilinear complexity 9 | **Yes.** The bilinear rank does not depend on the GF(2)-basis or modulus, because a change of basis is linear on both inputs and the output. | mu_2(4) = 9: D. V. Chudnovsky, G. V. Chudnovsky, "Algebraic complexities and algebraic curves over finite fields", J. Complexity 4 (1988) 285-316, Example 3.2, proved by computer search [secondary]. BCPRRR21, Table 1 ("Exact bilinear complexities", q = 2, n = 4: mu^sym = mu = 9) and Remark 9.3 [read]. The symmetric rank is also 9, via iterated Karatsuba (same remark). General lower bound mu_q(n) >= 2n - 1 = 7 (BCPRRR21 Sect. 2). | "9 ANDs = the bilinear complexity mu_2(4) = 9 of GF(2^4) multiplication (Chudnovsky-Chudnovsky 1988, Ex. 3.2; see Ballet et al. 2021, Table 1). So 9 is minimum among bilinear circuits, in which every AND multiplies a linear form in a by a linear form in b." |
| 2b | 9 ANDs is the minimum for unrestricted circuits, i.e. the MC of GF(2^4) multiplication | **Not established.** Our ANDs may mix a and b, and may use nonlinear intermediates. | BF18 Sect. 1.2 [read]: Mirwald-Schnorr showed quadratic circuits are optimal only for quadratic (n,1)- and (n,2)-functions. BF18 Sect. 4 [read]: "It is still not known whether this is true for (n,m)-functions in general", and whether Strassen's result holds over F2 is unknown. arXiv 2608.30238 (2026, unreviewed) claims unrestricted MC 9 for 4-term *polynomial* multiplication (7 outputs). Field multiplication is a linear image of that map, so the claim gives only the upper bound 9 for the field, not a lower bound. Elementary lower bound (my derivation, not from a source): >= 4, because one output coordinate is a nondegenerate bilinear form of rank 4. | "9 ANDs; equals the bilinear complexity (minimum for bilinear circuits). Whether fewer ANDs suffice in an unrestricted XAG circuit is open as far as we know." **Drop "(minimum)" and "= MC".** |
| 3a | GF(2^4) inversion: MC = 5 | **Yes, proved, in every representation.** BMP13's argument applies to unrestricted circuits: the first AND has degree <= 2; the outputs modulo degree <= 2 span a 4-dimensional space; so at least 4 more ANDs are needed. A change of basis is linear and preserves MC. In the polynomial basis mod x^4+x+1 the map is x -> x^14, and every nonzero component has degree wt(14) = 3, so the same argument applies directly. | BMP13 Sect. 2.1, p. 7 [read]: "Under the given representation for GF(2^4), the multiplicative complexity of inversion is 5". The proof is given there (degree-3 argument, upper bound from Fig. 2). | "MC 5 (proved: Boyar-Matthews-Peralta 2013, Sect. 2.1; the bound is basis-independent)." |
| 3b | 16-gate (5 AND + 11 XOR) GF(2^4) inversion circuit published | Yes, but **in a different representation** from ours. | BMP13 Sect. 2.1, Fig. 2 [read]. Tower field: GF(2^2) = GF(2)(W), W^2+W+1 = 0, basis (W, W^2); GF(2^4) over GF(2^2) via Z^2+Z+W^2 = 0, basis (Z^2, Z^8), i.e. normal bases following Canright. The input/output bit order is (x1..x4) as defined there. Earlier circuits (same section): Paar 10 AND + 15 XOR; Canright 9 AND/NAND + 14 XOR/XNOR, then 8 NAND + 2 NOR + 9 XOR/XNOR. Upper bound only; no gate-count optimality is claimed. | "16 gates (5 AND + 11 XOR) in the Canright normal-basis tower representation (BMP 2013, Fig. 2). Not directly comparable with our polynomial-basis (x^4+x+1) circuit, because basis changes cost XORs." |
| 3c | 15 gates with ordinary 2-input gates (Maximov-Ekdahl 2019) | **Secondary only.** The basis and gate set were not read. | ME19-slides (slide 17): "a small conventional (no MUXes) circuit of 15 gates and depth 3", compared with "[BP12] ... 17 gates and depth 4 (with base gates {AND, XOR})". The paper (TCHES 2019(4), 91-125) is blocked [unverified]. | "15 gates, depth 3, 'conventional' gates (Maximov-Ekdahl 2019, slides; paper not read; basis and gate set unknown)." Do not compare it with our 15-gate xag result as the same model. |
| 4a | Piccolo (= Joltik) BGC 10, optimal | Yes (SAT). | Sto16 Table 3 (1 AND, 3 OR, 4 XOR, 2 NOT) [read]. ZH23 Sect. 6 says "We verified these results"; ZH23 Table 3 shows SAT at k = 10 and UNSAT at k = 9 [read]. Sov23 Table 1 repeats the result. | "BGC 10, optimal (SAT: Stoffelen 2016, Table 3; re-verified Zhang-Huang 2023, Table 3)." |
| 4b | Piccolo GC 8, optimal | Yes (SAT). | Sto16 Table 5 (2 OR, 1 XOR, 2 NOR, 3 XNOR) [read]. ZH23 Table 4 shows GC SAT at 8 and UNSAT at 7 [read]. | "GC 8, optimal (Stoffelen 2016, Table 5; Zhang-Huang 2023, Table 4)." |
| 4c | Piccolo MC 4 | Yes (SAT). | Sto16 Table 1. ZH23 Table 3 (MC UNSAT at 3) and Sect. 6 (verified). | "MC 4 (Sto16 Table 1)." |
| 4d | PRIDE (= Prøst; same table, checked against Sov23 Table 7 "048f15e927acbd63"): MC 4, BGC 8, GC 8, all optimal | Yes (SAT). | Sto16 Table 1 (MC 4), Table 3 (BGC 8 = 4 AND + 4 XOR; Sect. 3.3: the designers' bitsliced implementation "is indeed minimal"), Table 5 (GC 8). ZH23 Tables 3/4: BGC UNSAT at 7, GC UNSAT at 7, MC UNSAT at 3 [read]. | "MC 4, BGC 8, GC 8, all optimal (Stoffelen 2016, Tables 1, 3, 5, for the Prøst S-box = PRIDE S-box)." |
| 4e | RECTANGLE BGC in [11, 12]; our 12 | Range correct. Optimality of 12 is **open**. | Sto16 Table 3: {10, 11, 12}. ZH23 Table 10: [11, 12] [read]. | "BGC 12; the optimum is 11 or 12 (Zhang-Huang 2023, Table 10)." |
| 4f | RECTANGLE GC 11, determined | Yes (SAT). | ZH23 Table 11: 11 (Sto16 had [10, 11], Table 5). ZH23 Sect. 6: "we determined the GCs of RECTANGLE and RECTANGLE^-1" [read]. | "GC 11, optimal (Zhang-Huang 2023, Table 11)." |
| 4g | RECTANGLE MC 4 | Yes. | Sto16 Table 1; ZH23 Table 3. | "MC 4." |
| 4h | Ascon BGC in [12, 16]; our 16 | Range correct. **16 is an upper bound only.** | ZH23 Table 10 [read]; the 16-gate circuit is in ZH23 App. C. Sto16 gives no BGC for Ascon. The designers' code is 22 (LITERATURE.md), now superseded. | "BGC 16 (= best known, Zhang-Huang 2023, Table 10; optimum in [12, 16])." |
| 4i | Ascon GC in [12, 15]; our 15 | Range correct; upper bound only. | ZH23 Table 11 [read]. | "GC 15 (= best known; optimum in [12, 15], ZH23 Table 11)." |
| 4j | Ascon MC 5 | Yes (SAT). | Sto16 Table 1; ZH23 Table 3 (SAT 5, UNSAT 4) and Sect. 6 (verified) [read]. | "MC 5 (Sto16 Table 1, re-verified ZH23)." |
| 4k | Keccak chi BGC in [12, 13]; our 13 | Range correct; upper bound only. | Sto16 Table 3: "<= 13" (3 AND, 2 OR, 5 XOR, 3 NOT). ZH23 Table 10: [12, 13] [read]. | "BGC 13 (= best known; optimum in [12, 13], ZH23 Table 10)." |
| 4l | Keccak chi GC in [11, 13]; our 13 | Range correct; upper bound only. | ZH23 Table 11 [read]. Sto16 has no 5-bit GC results (Sect. 3.4). | "GC 13 (= best known; optimum in [11, 13], ZH23 Table 11)." |
| 4m | Keccak chi MC 5 | Yes. | Sto16 Table 1; ZH23 Table 3 (UNSAT 4). | "MC 5." |
| 4n | PRESENT (= LED) MC 4 | Yes (SAT). This is the MC of the S-box, not of our circuits. | CHM11 Sect. 3, Theorem 1 [read]: "The Multiplicative Complexity of the PRESENT S-box is exactly 4", with UNSAT for 3 ANDs. Caveat: ZH23 Remark 1 found an output-constant flaw in the Sto16/CHM-style MC encoding, and PRESENT (S(0) = 12) was **not** in ZH23's re-verification. The value is consistent with Zajac-Jókay, Cryptogr. Commun. 6(3) 2014 (enumeration of affine classes with MC <= 4) [secondary: Jeon et al. 2021 list PRESENT with MC 4]. | "MC 4 (Courtois-Hulme-Mourouzis 2011, Thm 1, SAT)." |
| 4o | PRESENT BGC 14 | Upper bound only. | CHM11 Fig. 1 (14 gates: 2 AND, 2 OR, 9 XOR, 1 NOT) [read]. Sov23 Table 7 STD: R = 14, L/P = 14 [read]. No lower bound found. | "BGC 14 (= best known; CHM11 Fig. 1, Sov23 Table 7)." |
| 4p | GIFT BGC 11, GC 10 | Upper bounds only. | BGC: Sov23 Table 7 STD R = 11, L/P = 11 [read]. GC 10: GIFT-COFB spec text (LITERATURE.md [read]; not re-checked here). | "BGC 11, GC 10 (best known; heuristic/spec)." |
| 4q | SKINNY-64 S4 BGC 11, GC 8 | Upper bounds only. | Sov23 Table 7: STD R = 11 (L/P 11); EXT (with ANDN) 10 [read]. GC 8 is the spec's 4 NOR + 4 XOR. Lu21's optimality claim concerns GE, not GC. Observation from Sov23 Table 7's BSL strings (not a source claim): SKINNY's coordinates equal Piccolo's except that one coordinate is complemented (1e1d vs e1e2). Piccolo's GC = 8 proof does not transfer to SKINNY automatically. | "BGC 11, GC 8 (best known; Sov23 Table 7 / spec)." |
| 4r | Midori Sb0 BGC 13; Sb1 BGC 15; PRINCE 16; KLEIN 17; Noekeon 12; Serpent S0..S7 14 14 13 15 15 15 14 16 | All are correct transcriptions. All are **heuristic upper bounds**. | Sov23 Table 7, STD columns "R" [read]. Sov23's abstract calls the method "heuristic". L/P values: Sb0 14, Sb1 17, PRINCE 18, KLEIN 17, Noekeon 12, Serpent = R. Midori Sb0 has the same table as MANTIS in Sov23. | "BGC ... (best known, heuristic: Sovyn et al. 2023, Table 7)." |
| 4s | LAC MC 4, BGC 11, GC 10 (LITERATURE.md) | Yes (SAT). | Sto16 Tables 1, 3, 5. ZH23 Sect. 6 and Tables 3/4 (UNSAT at 3 / 9 / 7). | as is |
| 4t | Minalpher MC 5, BGC >= 11 (LITERATURE.md) | Outdated. | ZH23 Table 10: BGC [12, 17]; Table 11: GC [11, 14]. MC 5: Sto16 Table 1. | "MC 5; BGC in [12, 17]; GC in [11, 14] (ZH23)." |
| 4u | PRIMATEs MC 7 | Yes (SAT). | ZH23 Table 9 (Sto16 had {6, 7}, conjectured 7) [read]. | "MC 7 (ZH23 Table 9)." |
| 5 | Any other "optimal" for a 4-bit S-box | None found beyond 4a-4g, 4n, 4s and 4u. | LEDGER Sect. 2 marks "opt" only for Piccolo, RECTANGLE GC, PRIDE, plus the RECTANGLE/Ascon/Keccak ranges. Those are all covered above. | Keep "opt" only where the source table gives a single value proved by SAT. |

## 3. What must be reworded or dropped

In LEDGER.md:

1. **Sect. 1, GF(2^4) multiplication, "9 AND = bilinear rank (minimum)".** Reword: "9 AND =
   bilinear complexity mu_2(4) (Chudnovsky-Chudnovsky 1988, Ex. 3.2; Ballet et al. 2021, Table 1):
   minimum for bilinear circuits; unrestricted MC open." Our circuit is not necessarily bilinear, so
   we must not call 9 the proven minimum for our model.
2. **Sect. 1, GF(2^4) inversion, "MC 5; 16 gates (5 AND + 11 XOR) published, basis not checked".**
   The basis is now checked. Reword: "MC 5 (proved, BMP 2013 Sect. 2.1, basis-independent); BMP's
   16-gate circuit (Fig. 2) uses Canright's normal-basis tower representation and is not directly
   comparable with our polynomial basis (x^4+x+1)."
3. **Sect. 1, inversion, "15 gates with 2-input gates claimed (ME19 slides, secondary)".** Reword
   to "15 gates, depth 3, 'conventional' (non-MUX) gates (ME19 slides; paper, basis and gate set not
   read)". Our 15 is in xag (AND, XOR, NOT), so it is not the same model.
4. **Sect. 1, maj3 / full adder "optimal".** The claim holds, but it needs a source. Cite our
   exhaustive search, and for the full adder Kulikov DATE 2018 Sect. III. Mark Knuth 7.1.2 as not
   re-read. Do not cite Knuth as the source until the table is checked.
5. **Sect. 2 caption.** Make the range notation precise: "[l, u]: UNSAT at l-1 and SAT at u
   (ZH23 Sect. 6)". "Published" values mix SAT-proved and heuristic (Sov23) numbers, so add a
   per-row tag (SAT / UB). Add the missing table tags:
   - Piccolo: Sto16 T3/T5.
   - PRIDE: Sto16 T3/T5 (as Prøst).
   - RECTANGLE: ZH23 T10/T11.
   - Keccak: ZH23 T10/T11, since that row currently has no source.
6. **Sect. 2, GIFT "10 (spec)" and SKINNY "8 (spec)".** These are upper bounds only; label them
   "UB". No change is needed otherwise.

In LITERATURE.md (corrections only; I did not edit the file):

7. **Sect. 1.** Stoffelen's definitions are at the start of **Sect. 3** of the author copy, not
   Sect. 2. Sect. 2 is the SLP problem. The table numbers (2 and 4) are right.
8. **Sect. 1 GC row.** Add: the constants 0/1 are gate types of cost 1 (Sto16 Table 4, ZH23
   Table 2), and NOT = NAND(x,x) or XNOR(x,0) costs 1 (ZH23 Sect. 4.3, Remark 2).
9. **Depth row.** Add that Sto16/ZH23 depth results are (k, w) statements with a width bound.
10. **Sect. 2 RECTANGLE GC row.** The "[unverified]" tag can be cleared: the value is 11 (ZH23
    Table 11).
11. **Minalpher line.** Update to BGC [12, 17] and GC [11, 14] (ZH23 Tables 10, 11).
12. **Sect. 3 Ascon BGC "<= 22".** Superseded: 16, with the optimum in [12, 16] (ZH23 Table 10);
    GC in [12, 15] (Table 11).
13. **Sect. 6 "9 is the bilinear rank over GF(2)".** Add the citation (Chudnovsky-Chudnovsky 1988
    Ex. 3.2 via BCPRRR21 Table 1 / Remark 9.3). Add: "unrestricted MC not established (Boyar-Find
    2018 Sect. 4)".
14. **PRESENT MC 4 (CHM11 Thm 1).** Add the caveat that PRESENT was not in ZH23's re-verification
    after the Remark 1 encoding fix. Cite Zajac-Jókay 2014 as independent support [secondary].

## 4. Papers to request (blocked or not accessible here)

| Paper | URL | Needed for |
|---|---|---|
| A. Maximov, P. Ekdahl, "New Circuit Minimization Techniques for Smaller and Faster AES SBoxes", IACR TCHES 2019(4), 91-125 | https://tches.iacr.org/index.php/TCHES/article/view/8346 (ePrint: https://eprint.iacr.org/2019/802) | Claim 3c: basis, gate set and gate list of the 15-gate GF(2^4) inversion. |
| D. V. Chudnovsky, G. V. Chudnovsky, "Algebraic complexities and algebraic curves over finite fields", J. Complexity 4 (1988) 285-316 | - (DOI not verified; Elsevier J. Complexity) | Claim 2a: primary location of mu_2(4) = 9 (Example 3.2). |
| R. Barbulescu, J. Detrey, N. Estibals, P. Zimmermann, "Finding Optimal Formulae for Bilinear Maps", WAIFI 2012, LNCS 7369 | https://eprint.iacr.org/2012/110 | Independent exhaustive confirmation of the bilinear rank of GF(2^4) multiplication, if their tables include it. |
| D. E. Knuth, The Art of Computer Programming, Vol. 4A, Sect. 7.1.2 "Boolean Evaluation" (book) | - | Claims 1a and 1c: the exact table/statement for maj3 (cost 4) and the full adder (cost 5). |
| P. Zajac, M. Jókay, "Multiplicative complexity of bijective 4x4 S-boxes", Cryptogr. Commun. 6(3) (2014) 255-277 | https://doi.org/10.1007/s12095-014-0100-y | Claim 4n (independent PRESENT MC) and the MC <= 5 bound. |
| R. Mirwald, C. P. Schnorr, "The multiplicative complexity of quadratic Boolean forms", Theoret. Comput. Sci. 102 (1992) | - (DOI not verified) | Claim 2b: the exact scope of the "quadratic circuits are optimal" result. |
