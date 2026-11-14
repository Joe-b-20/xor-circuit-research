# Eleven consumer gates have joint minimum twenty-two

2026-11-13, continuing reviewed commit `d8bfd65`. Structural hand proofs with independent
machine reviews, not formal verification or human certification. No circuit search,
SAT, enumeration, or computer-driven case elimination was used.

**The joint source/consumer minimum is 22 whenever the consumer uses exactly eleven
gates**, allowing arbitrary feedback and intermediate cancellation. The existing
specified circuit with eleven source and eleven consumer gates attains this bound.
The ten-consumer case was already closed at 22. Therefore any unrestricted joint
circuit below 22 must have **at least twelve consumer-bearing gates and at most nine
source-side gates**. Those larger consumer budgets remain open.

The unrestricted MixColumns interval stays **75 to 88**, and the block-monotone lower
bound stays **85**. No claim that 88 is optimal follows.

## Entry traces constrain actual return paths

The new [tight-fibre theorem](TIGHT_FIBRE_WIRES.md) concerns the physical consumer
wiring. In an eleven-gate consumer with five entries, bypassing the entries leaves
six ordinary gates for the four triples. This is the ordinary minimum, so every
ordinary mask occurs at exactly one input or non-entry root. Entry edges connect
values with the same ordinary mask into a rooted tree. An exit returns the XOR of
the entry labels along the path between its operands; all those labels were read
before the exit.

Literal transposition, with fanout represented by explicit copies, also has six XORs.
Its two even helper values cannot have wires with the same nonzero ordinary
output derivative. Each helper feeds a disjoint set of odd triple gates, whose
output adjoints are independent.

If two entry edges meet, their trace sum can be exposed on a particular wire by
choosing the local adjoint accumulation order. Its derivative is the original
vertex's ordinary mask. Two adjacent pairs on a path can be exposed simultaneously.
Thus three consecutive distinct odd traces are impossible: their two distinct even
pair sums would have equal nonzero derivatives. This is a condition on actual wires,
stronger than the algebraic consistency of a list of trace vectors.

When all five traces are odd and distinct, as in the applicable four-nonclean profile,
every fibre path has at most two entries. Every exit
is therefore already supplied or one XOR of earlier actual labels. Source replay
has no extra cost, so the no-feedback joint lower bound 22 applies to this feedback
class too. This closes the four-nonclean five-term label-relation profile that the
previous phase deliberately retained.

## The other four-nonclean profiles also close

For the [three-term relation](FOUR_NONCLEAN_PAIR_CLOSED.md), write the labels as
`n1,n2,n3,n4,c` with `c=n1+n2`. The last two nonclean entries have the two distinct
even traces. Their marked-wire derivatives differ, placing them in different
ordinary-mask fibres. No exit path can use both. Completing the original triangle
`{n1,n2,c}` costs no net extra gates: an early completion bypasses that value's later
original source gate. Every exit then combines one available triangle value and
at most one of `n3,n4`. Replay again has zero overhead, proving total at least 22.

For an [affine plane of four nonclean labels](AFFINE_FIBRE_CLOSURE.md), the fifth
label `h` has an even trace different from every pair sum of the four odd plane
traces. In the ordinary-mask fibre containing `h`, two plane-entry edges cannot
meet: exposing their even trace sum would contradict separation from `h`'s marked
wire. Consequently the only possibly expensive return has one plane edge on each
side of `h`, and there is at most one such path. Its value is

    f=h+w,       w=qi+qj,

where `qi,qj` are earlier plane labels. Every other exit costs at most its original
one XOR. Repair needs at most the single additional value `w`.

If `h` is clean, positive repair overhead supplies the clean triangle `h,w,f`.
Appending one independent plane difference supplies the fourth diagonal, giving
a forbidden twelve-gate source supplier. Zero overhead instead contradicts the
no-feedback minimum. This closes the four-nonclean affine-plane profile.

## Six physical values in one coset force another source gate

The last profile has five nonclean labels: four in an affine plane and `h` outside
its span. The same path restriction gives at most one return needing extra repair.
If no repair is needed, no-feedback 22 applies. Otherwise the returned `f=h+w` is a
sixth distinct physical value in the same diagonal coset as the five entry labels.

The new [six-value supplier theorem](SIX_COSET_VALUES.md) says that the four first
rows and six distinct available values in any diagonal coset require at least twelve
source gates. It includes values used only as exports and permits cancellation.

For an even ordinary-parity coset, five nonzero even ordinary masks plus the four
row triples and three free-entry directions already need twelve gates. An odd
ordinary-parity, odd free-parity coset needs six extra odd gates, the four rows,
and two even helpers. In the remaining tight parity case, eleven gates leave five
odd helpers crowded into one coset and only two even values. A nonclean even value
supports at most two relevant odd pairs; a clean one supports at most three. If
both are clean, their independent masks limit the formal relation rank to five.
In every case fewer than the six required non-entry equations are available.

One-gate replay of a hypothetical joint circuit below 22 would supply those six
coset values and the four rows in at most eleven source gates. This contradicts the
supplier theorem and closes the all-nonclean profile.

## Completeness and the new boundary

Earlier work handled clean entries, extra consumer gates outside the relaxed target
cones, four-entry mixed interfaces, and five-entry interfaces with two or three
nonclean labels. The three four-nonclean relation types and the all-nonclean type
are now all closed. If normalization reduces the consumer count from eleven to ten,
the earlier ten-consumer bound applies. No missing smaller-budget case is assumed away.

The [specified attaining construction](FOUR_ENTRY_CLOSURE.md#an-attained-22-gate-four-entry-pattern)
has eleven gates on each side; its [saved direct checks](four-diagonal-check.json)
confirm the eight outputs, entry rank, live gates, and event-free property. No new
construction search or numerical proof was needed in this pass.

The next mathematical question is whether spending twelve or more gates on the
consumer can reduce the source below ten enough to beat 22. The present proofs use
the six-gate ordinary mirror tightly; an extra ordinary gate can admit more masks
and different same-mask roots. That change must be analyzed rather than assumed
away. The broader lessons are that trace parity limits physical return paths, and
that a useful cancellation can force an additional export in an already crowded
source coset.

Independent reviews cover [the wire theorem](reviews/tight-fibre-source-review.md),
[the affine-fibre consequences](reviews/affine-fibre-source-review.md), and
[the six-value theorem and final implication](reviews/six-coset-review.md).
The primary agent independently checked those arguments, the three-term closure,
and the coverage of every previously open eleven-consumer profile.
