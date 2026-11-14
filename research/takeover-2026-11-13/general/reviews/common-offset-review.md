# Independent review: common offsets and joint preparation

2026-11-14. Independent machine review of the complete
[COMMON_OFFSET_PREPARATION.md](../COMMON_OFFSET_PREPARATION.md). I reconstructed
the common-offset law, the actual-prefix example, and both joint resource
frontiers. No circuit search, representation search, or enumeration was used.
This is not formal verification, human certification, or a novelty assessment.

## Exact common-offset law

The assumptions ell_S(h)=q and ell_S(t_i)=q+1 imply that h costs q-1 gates
from the actual dictionary while each target alone costs q. The supplied
translate u_i=t_i+h therefore gives a continuation with q-1 preparation gates
and m target gates. No target can already have appeared in that shorter
preparation, since doing so would contradict its single-target minimum.

In every competing continuation, the first target requires at least q gates,
and every other distinct target needs a later first-production gate. This
proves the matching q+m-1 lower bound without assuming that the competitor
produces h. The case q=1 is included: h is already available, the distinct
targets are absent, and exactly m gates are necessary. All operands used in
the construction are supplied or physically computed.

## Actual prefix and unchanged individual frontiers

The prefix for each i consists of 2r odd-plus-odd pairs, 2r-1 even accumulation
gates, and one odd gate, for a total of 4r. Its entire intermediate dictionary
is retained. The common offset h is not among those available values, although
each translated target u_i=h+t_i is available.

The quotient sends both a_j and every x_(i,j) to A_j, and each z_i to its own
Z_i. Every even dictionary member maps to zero, while every odd member maps
to one unit. The target image has weight 2r+1, forcing at least 2r+1 odd terms
in any dictionary representation. Its single-target point therefore has
K_R>=r and P_R>=r. The original target-coordinate representation attains both.
The full single-target Pareto theorem then gives the unique nondominated point
(r,r), permitting arbitrary cancellation and sharing in a continuation.

The same quotient gives ell(h)=2r and proves h absent. It also shows the
required non-input targets are absent from S_1, which is needed for the
first-production arguments. The common-offset law yields the exact remaining
binary cost m+2r-1.

## The initial joint frontier

In a compatible parity partition, one target block of size 2r+1 meets at most
r+1 parts: exactly one intersection is odd and every other nonempty intersection
uses at least two coordinates. Counting such intersections over the disjoint
blocks, and allowing all 2r unused a_j coordinates to form extra parts, gives
at most m(r+1)+2r parts. With all initial coordinates counted, the even rank is
therefore at least rm. The number K of odd-plus-odd gates is at least this rank.
Mixing different target blocks or unused anchors does not invalidate the upper
bound on the number of parts.

The full target union has m(2r+1) supported coordinates and m overlap components.
The multi-output preparation theorem consequently gives H+d_EE>=m(r-1), hence
P=O+d_EE>=rm. Independent target formulas attain K=P=rm. These two inequalities
are unrestricted and do not invoke a direct-sum theorem.

## The prepared joint frontier

Any continuation producing all targets also produces any one of them, so its
total K is at least r by the unchanged individual frontier. The interval up
to the first target uses at least r units of P. Each of the other m-1 targets
then needs a later odd gate at its first occurrence, giving P>=m+r-1.

Pairing the 2r anchors uses r odd-plus-odd gates; combining those even pairs
uses r-1 even-plus-even gates; attaching h to the m supplied u_i uses m odd
gates. Thus (K,P)=(r,m+r-1) is attainable and simultaneously minimizes both
coordinates. It is the complete joint Pareto frontier, not just a total-cost
or weighted-price witness. The formulas include r=1 and m=1 without exception.

## Interpretation and scope

The ratio 2rm/(m+2r-1) becomes unbounded when m=r grows. The prefix cost 4rm is
explicitly real and excluded only because the comparison concerns remaining
complexity at two actual states. The note correctly disclaims an end-to-end
improvement for these disjoint targets.

The full dictionary metrics are not claimed equal. For i!=j, t_i+t_j has
initial word length 4r+2 but prepared length two through u_i+u_j. No individual
supplied value contains both z_i and z_j, so the latter length is exact. Thus
the example identifies lost relations among targets rather than contradicting
the exact single-target theorem.

Retaining the a_j and x_(i,j) identity outputs while replacing z_i by t_i makes
a square all-odd involution: the core coordinates remain fixed and the same
even sum is added twice to each z_i. The identities require no new gates, so
the continuation counts and frontier comparison are unchanged.

The complete note passes review. It distinguishes actual shared preparation,
individual cost profiles, joint remaining cost, and total end-to-end cost.
No new numerical MixColumns bound or restricted circuit assumption is asserted.
