# Independent review of the four-entry feedback conditions

2026-11-13. Line-reviewed `../FOUR_ENTRY_FEEDBACK.md` against the four-entry interface theorem, A12, the five-diagonal bound, and `../ENTRY_MATCHING.md`. This is a hand review without circuit search or configuration enumeration.

**Conclusion: the necessary conditions are proved with the stated scope. No substantive gap found.** In particular, chronology survives earlier feedback, the assertion about exactly two original nonzero diagonal values concerns physical availability rather than only their span, and the projected return lies in the unique two-root fibre.

## Chronological grouped replay

The four-entry mixed-interface theorem supplies an actual basis `c,d,n,m`, with `c,d` clean and `n,m` nonclean. Consequently the decomposition of any source part in this basis is unique. Causal induction through consumer-bearing gates puts each exit in the span of labels already read before it. Its unique representation therefore cannot involve a future basis label.

This justifies the proposed two-group replay without assuming source-first scheduling. If an exit needs `p=c+d`, both labels have already been physically supplied in the original chronology and their source values have already been preserved by replay. The same is true for `e=n+m`. Earlier source values may themselves have depended on exits; induction over source-side gates already reproduces them before the later label or exit needs them. Neither pair sum is treated as free before its paid computation.

Each original source gate costs at most its original one-gate allowance. The two designated pair sums cost at most one extra gate each, retained thereafter. Appending either missing sum at the end is valid because all four actual labels are then supplied. Thus all original source values together with both pair sums have a source-only realization of size at most `G_0+2`. It contains the four source rows and the independent clean values `c,d,e`, so A12 gives `G_0>=10`.

## Equality and physical diagonal availability

At total at most twenty-one with eleven consumer-bearing gates, `G_0=10`. If either `e` or `p` were an original source value, replay saves a gate in either temporal order. An earlier original production avoids the extra pair computation. If the pair is synthesized first, its later original paid production can be bypassed. Nonzero diagonal values cannot be source coordinate inputs or wholly free `a` values, so this credit always refers to a paid gate. Appending the pair only after replay is included in the earlier-production alternative. The resulting at-most-eleven-gate augmented source circuit would contradict A12.

Thus neither `e` nor `p` is originally present. If any other nonzero diagonal besides `c,d,e,p` were originally present, the at-most-twelve-gate replay containing both pair sums would contain five distinct nonzero diagonals and the four source rows, contradicting the five-diagonal bound. Since `c,d` are actual entry values, the original physical nonzero diagonal set is exactly `{c,d}`. This is stronger than merely bounding the rank of that set, and the proof supports the stronger assertion.

An original clean exit would therefore have to return `c` or `d`. In the independent label basis, that value's unique representation uses the same label. Causal span induction requires that label to have been supplied and read earlier, so the exit cannot be its first production and is redundant in a reduced circuit. The argument does not assume that all diagonal labels were supplied before consumer computation began.

Every remaining nonclean exit has exactly one of `n,m` in its representation. If it does not also contain both `c,d`, its value is one earlier label or one XOR of two earlier labels. If all exits had this form, source replay would require no extra pair computation, and appending `e` alone would give an augmented source supplier in at most eleven gates. Therefore an exit `n+c+d` or `m+c+d` is necessary.

## Projection and the location of the return

For a return `n+c+d`, projection along `m` fixes `D`, kills the actual `m` entry, and sends `n` to `e`. It preserves the four consumer targets. Exactly ten consumer-bearing gate slots remain, with entries `c,d,e`; their own masks are unchanged. Any additional duplicate, bypass, or dead gate would contradict the ten-gate local minimum. If the removed entry was an exit operand, its projected value is supplied by its nonfree parent. The two projected exit operands remain distinct because their difference is the nonzero three-label sum `e+c+d`.

The three-entry matching theorem applies to this projected local circuit. Within any single one-root fibre, matching entry edges allow at most one entry, so a same-own pair in that fibre could differ only by one actual label. The required three-label difference therefore lies in a fibre with at least two roots. This use is local to the operands' fibre and does not require every other fibre to have one root.

At least two distinct nonzero even own masks are necessary. With just one, its first occurrence is the sum of two own input units, and every odd own mask thereafter is either a unit or a unit translated by that pair. Only two of the four triples can occur. Two even masks and four triples give six first-occurrence non-entry gates; seven non-entry gates are available. Three even masks would use all seven slots as first occurrences and leave every fibre with one root, which is impossible here. Thus exactly two even own masks occur and there is precisely one additional non-entry occurrence of an existing own mask.

That one extra occurrence creates exactly one two-root fibre, and it must contain the projected return operands. If the repeated own mask is a coordinate unit, its ordinary input counts as the first root; the conclusion still holds. No assumption that the roots are both paid first occurrences is needed.

## Scope

These arguments constrain a hypothetical twenty-one-gate joint circuit with eleven consumer-bearing gates and the four-entry mixed interface. They do not show that its required nonclean return or its source computation is realizable, and they do not exclude the profile. The five-entry mixed case remains outside the statement. The note's final limitation is therefore appropriate.
