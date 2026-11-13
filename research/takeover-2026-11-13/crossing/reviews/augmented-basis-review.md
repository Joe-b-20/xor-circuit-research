# Independent review of the arbitrary-basis restricted obstruction

2026-11-13. Reviewed the broadened `../../frontier/AUGMENTED.md` and its cited twelve-gate construction. This is a hand review of the proof, without search or enumeration.

**Conclusion: the lower bound of twelve holds for every independent triple of even diagonal masks under the stated event-free and no-mixed-auxiliary hypotheses. No substantive gap found.** The revised statement correctly claims attainment over the class, without claiming a twelve-gate construction for each fixed basis.

## Precursor requirements remain valid for arbitrary masks

The four row own masks are odd and the three diagonal own masks are distinct nonzero even masks, so all seven are distinct. A free-only operand cannot change the own mask of a preceding designated mixed value into a different target. A sum of two distinct designated mixed values cannot be designated: row defects are distinct nonzero triples, a row pair cannot be diagonal, and the three selected diagonal masks are independent.

Consequently a required target can use a previous designated mixed value only when their free masks agree and their difference is supplied as an actual pure-own value. The only agreeing pair is `T_c,D_c` for a selected cycle-pair diagonal. It forces at least two physical values from `{s_c,E_c,E_(c+1)}`. An unpaired row forces its own `E_c`; a non-cycle diagonal has a unique designated free mask and forces its own even pure precursor. A non-cycle precursor cannot coincide with a pure triple or with any cycle-pair precursor.

Thus the incidence premises extend without assuming that the diagonal basis consists of cycle pairs.

## The new two-cycle-pair case

For `k=2`, the two unpaired rows force two pure triples, and the non-cycle diagonal forces a third distinct pure value. An eleven-gate circuit would leave at most one other pure gate.

Each forced unpaired triple can belong to at most one paired incidence set: membership as `E_c` would make its index paired, so only membership as `E_(c+1)` is possible. The non-cycle precursor contributes to neither set. Meeting four required incidences would therefore require both unpaired triples to contribute and the one extra value to belong to both paired sets.

Two different paired sets overlap only when their indices are adjacent on the four-cycle, and their common member is the triple at the shared endpoint. For two adjacent selected indices, exactly one unpaired index is an endpoint of a selected edge; the other forced triple contributes nothing. Hence the required equality cannot occur. If the selected indices are opposite, the incidence sets are disjoint and the extra value cannot supply two incidences. This is the stated cycle-incidence argument and does not depend on which non-cycle mask was selected.

## The other counts, ancestry, and scope

For `k<=1`, at least three unpaired rows force three pure triples. For `k=3`, the previous incidence inequality `6<=2x-1+y` with `x+y<=4` again forces at least three pure triples. The established first-occurrence argument that three distinct four-input triples need five XOR gates applies in both cases, including scalar cancellation within the ordinary block.

Event-freeness is used correctly to isolate the pure-own ancestor subcircuit: a gate with zero free part cannot read two equal nonzero free parts without creating a whole-block event. Therefore the five required pure gates are distinct from the seven mixed target gates.

The cited twelve-gate circuit uses the independent cycle masks `01,12,23`, five pure auxiliaries, and exactly the seven designated mixed targets, and is event-free. It proves sharpness over the class. The text now explicitly avoids asserting equal cost for every prescribed independent basis and leaves unrestricted mixed auxiliaries and whole-block cancellations outside the theorem. The augmented unrestricted interval remains `11<=L<=12`.
