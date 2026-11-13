# Independent review of AUGMENTED.md

2026-11-13. Reviewed the actual proof in `../AUGMENTED.md` and the explicit twelve-gate circuit in `../../compatibility/DIAGONALS.md`. This review uses direct algebra and structural arguments only; no circuit search or enumeration.

**Conclusion: the restricted minimum of twelve is proved, and the cited construction attains it. No substantive gap found.** The event-free and no-mixed-auxiliary hypotheses are both stated and used correctly. The proof does not settle the unrestricted augmented problem.

## The paired-row incidence condition

Take the selected diagonals to be `D_0,D_1,D_2`. A cyclic relabelling takes any three of the four cycle masks to this set while preserving the rows.

All seven designated mixed values have distinct ordinary masks, so a free-only operand cannot transform one designated mixed value into another. No XOR of two designated mixed values is designated: two rows have a nonzero diagonal defect, a row plus a diagonal retains that row's nonzero defect, and the three chosen diagonal masks are independent. The four row defects `E_(c+1)` are distinct, so the row-plus-diagonal possibility cannot produce another row. These observations justify excluding all mixed/mixed constructions of the seven targets.

Under the no-mixed-auxiliary assumption, a required gate must therefore use either a pure-own value and a free value or a previous designated mixed target and a pure-own value. In the latter possibility the free masks must agree. For `c=0,1,2`, the only two designated values with free mask `s_c(a)` are `T_c,D_c`.

Consequently whichever of this pair is produced first requires its own pure mask, respectively `E_c` or `s_c`. The later value either uses its own pure mask directly or uses the pure difference `E_(c+1)`. These are distinct values, and the pure set contains at least two members of `{s_c,E_c,E_(c+1)}`. The unpaired `T_3` must use `E_3` directly. The incidence condition thus counts physical values that must actually exist; it does not grant their differences for free.

## Incidence count and the three-triple lemma

The three incidence sets have triple multiplicities `1,2,2,1` for `E_0,E_1,E_2,E_3`, respectively. Since `E_3` is required, `x` present triples contribute at most `2x-1` incidences; the `y` present designated pairs contribute exactly `y`. At most four pure auxiliary gates would imply

    6 <= 2x-1+y <= x+3,

and hence at least three pure triples.

The assertion that three distinct four-input triples need at least five XOR gates is valid even with ordinary scalar cancellations. In a four-gate realization the three triples occupy three gates, leaving only one helper. After removing redundant operations, the first gate must be a two-input pair `p`; it is the sole helper. The only ways an odd triple can arise from the available parity types are `p+input` or `p+earlier triple`. The first form produces only the two triples containing `p`. In the second form, one of those two triples gives an input, whereas a triple not containing `p` gives the other triple not containing `p`. Therefore the first triple outside the containing pair cannot be produced. Two odd operands have even parity and cannot repair this obstruction. At most two triple outputs are possible with one helper.

This is a parity and first-occurrence argument, not a classification or search through four-gate circuits.

## Event-freeness and attainment

Event-freeness ensures that a pure-`b` node has only pure-`b` ancestors: if its two operands had nonzero `a` parts, those equal parts would cancel at the gate, creating a whole-block event. Recursing applies the same argument to every ancestor. Thus the five gates needed for the three pure triples cannot be supplied by or overlap with the seven mixed target gates. The claimed lower bound is `5+7=12`.

The cited construction has the five pure gates `p01,p23,E1,E2,E3`, followed by exactly the seven required mixed values for diagonal masks `01,12,23`. The identities `T1+E2=D12` and `D01+E1=T0` are correct. Their nonzero ordinary parts are unequal at each mixed-plus-pure gate, and only one operand has a free-block part, so neither creates a whole-block event. Cyclic relabelling covers the other omitted cycle mask.

## Scope

The conclusion concerns three selected cycle-pair diagonals and forbids auxiliary mixed gates. It therefore shows that an event-free eleven-gate solution for such a selection would require a mixed auxiliary. It neither excludes an eleven-gate solution with such an auxiliary nor covers an arbitrary independent triple of even masks. The final statement preserving the unrestricted `11<=L<=12` augmented interval is appropriate.

Minor notation only: the displayed use of `P` in the target-pair check can be made fully self-contained by saying that `P` is the cyclic coordinate shift. This does not affect the proof.
