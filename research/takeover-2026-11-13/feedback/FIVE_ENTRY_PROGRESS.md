# Source credits narrow the five-entry frontier

**Later result:** [the eleven-consumer closure](ELEVEN_CONSUMER_CLOSED.md) excludes
all four remaining profiles below total 22. The reductions below remain valid;
statements that these profiles are open record the preceding phase.

2026-11-13, continuing reviewed commit `577d8bc`. Structural hand proofs and independent
machine reviews, not formal verification or human certification. No circuit search,
enumeration, or computer-driven case elimination was used.

The five-entry eleven-consumer cases with two or three nonclean labels now require
at least **22 total gates**, allowing arbitrary feedback. A candidate below 22 with
exactly eleven consumer-bearing gates must have **four or five nonclean labels**.
A general source-replay theorem explains the mechanism: group completion is charged
only for values absent from the original source computation, provided the split
respects every chronological entry prefix. Unrestricted MixColumns remains **75 to
88**, and the block-monotone lower bound remains **85**.

## Producing a value early can pay for its own repair

The [credited replay theorem](CREDITED_REPLAY.md) applies to any linear XOR circuit.
Split the actual entry space as a direct sum `U=P+Q`, and require every earlier-entry
span to split in the same way. Let `A` be the original physical source-value set,
including inputs and free values. Define

    B = |(P minus {0}) minus A| + |(Q minus {0}) minus A|.

Every original source value, together with all of `P` and `Q`, has a source-only
realization using at most `G_0+B` gates. The same allowance removes feedback from
the whole computation while preserving its consumer entry labels.

Maintain both groups as entries arrive. The prefix condition ensures an entry has
at least one component already available in its group; subtracting that component
supplies the other. Every exit then needs at most one XOR of available group values.
A synthetic group value that equals an original source value advances that value's
production, and its later original gate can be bypassed. Distinct advanced values
receive distinct later credits. Only genuinely missing physical values contribute
to `B`. A virtual member of the original span receives no such credit.

A chronological greedy basis recovers the earlier rank-only repair bound. The new
formulation also permits useful groups that are not simply formed from the earliest
entry basis, and uses later original values without assuming their operands are
already accessible. Its prefix hypothesis is essential.

## Two and three nonclean labels are excluded below 22

With [at most two distinct nonclean labels](TWO_NONCLEAN.md) in a rank-four entry span,
three physical clean directions already force source cost eleven. Otherwise choose
a chronological clean basis `c,d` and the two nonclean values `n,m`. The groups
`{c,d,c+d}` and `{n,m,n+m}` cost at most two new values to complete. They supply a
clean triangle and the independent diagonal `n+m`, which require thirteen source
gates. Therefore `G_0>=11`. This argument allows repeated clean entries and any
consumer budget. If the original clean plane already contains its full physical
triangle, a credit strengthens the source bound to twelve.

With [three nonclean labels](THREE_NONCLEAN.md), the five-entry trace theorem forces
the two clean labels `c,d` to be independent and two nonclean labels to satisfy
`n1+n2=t`, with `t` one of `c,d,c+d`. The third nonclean label is `k`. Choose `n1`
as the earlier of the related pair. The fixed planes `span{c,d}` and `span{n1,k}`
then split every entry prefix. The only potentially missing group values are
`c+d` and `n1+k`. If a required clean component appears before its original gate,
compute it from already available values and recover that cost later. The resulting
supplier again contains a clean triangle and an independent fourth diagonal in
`G_0+2` gates, so `G_0>=11`.

The last argument is where simply naming a desired clean basis would fail. Such a
basis may not be available at an early exit. The theorem constructs the missing
component in time and accounts for its original producer explicitly.

## Remaining profiles and one stronger restriction

The [remaining label geometries](FOUR_FIVE_FRONTIER.md) are necessary algebraic
conditions, not claims that a consumer or joint circuit realizes each one:

| Nonclean entries | Unique label relation | Additional proved restriction below 22 |
| --- | --- | --- |
| Four | Two nonclean labels sum to the clean label | Exactly ten source gates; physical clean rank exactly one |
| Four | All four nonclean labels sum to zero | They form an affine plane; exits before the outside clean label is read have no replay overhead |
| Four | All five labels sum to zero | Not excluded; the four nonclean labels form a basis |
| Five | Four nonclean labels sum to zero | Affine plane plus an outside nonclean label; exits before that outside label is read have no replay overhead |

All still have five distinct actual labels, entry rank four, all eleven consumer
gates in relaxed target cones, and physical clean rank at most two. The first row
has the stronger rank-one condition. For that row, two plane groups need at most
one new completion. Any second independent original clean value would let this
replay retain a clean triangle and an independent fourth diagonal within twelve
source gates, contradicting the thirteen-gate bound.

The all-five-label relation must be retained. The unique relation on traces has
nonclean support, whereas the unique relation on labels has odd-trace support.
When all five traces are odd, only the four nonclean traces are required to sum
to zero. Confusing the two relations would wrongly discard this open case.

## Why five eventual labels do not remove the timing problem

[Five-label timing](FIVE_LABEL_TIMING.md) proves that five distinct rank-four values,
once physically available, need at most one additional XOR to make every value
in their span obtainable with at most one XOR. But this does not control earlier
exits. A fixed symbolic example has four initial source basis values, three returned
triple sums, and a fifth actual entry read only after those returns. Its three source
exit gates require five source-only gates: overhead exactly two, even offline.

This is a source-value-preservation example, not a gap between optimal full circuits.
It does not realize the eleven-gate four-row consumer. Its returned nonclean label
is later read verbatim, which the eleven-gate collision theorem forbids. Thus the
counterexample identifies the need for timing and consumer constraints together;
it does not refute a stronger result for the remaining specialized profiles.

## Judgment and review

The most transferable result is the explicit credit for later original physical
values. For the remaining affine-plane interfaces, cheap replay before the outside
label is read localizes any difficulty to the later part of the consumer. The
five-term relation needs a separate analysis of the six-gate transpose and actual
entry positions; its algebraic consistency is not enough to establish feasibility.
These are useful next directions, without assuming 22 is the unrestricted joint
minimum or 88 is optimal for MixColumns.

Independent reviews cover [the general replay theorem](reviews/credited-replay-review.md),
[two- and three-nonclean closure](reviews/two-three-nonclean-review.md),
[the detailed three-nonclean proof](reviews/three-nonclean-review.md),
[the remaining profiles](reviews/four-five-frontier-review.md), and
[the timing theorem and fixed example](reviews/five-label-timing-review.md).
The primary agent independently checked the chronology and credits. This pass used
symbolic verification only; earlier direct construction checks remain unchanged.
