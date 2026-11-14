# Independent review: shared multi-output preparation

2026-11-14. Independent machine review of the complete
[MULTI_OUTPUT_STARTUP.md](../MULTI_OUTPUT_STARTUP.md). All universal arguments
and specified symbolic families were checked without circuit search or
enumeration. This is not formal verification or a literature-novelty claim.

## Exact accounting and target credit

The complete ancestor union retains both operand ports of every gate. Every
even node has a reader because all selected roots are odd. Therefore the
even-port equation and undirected cycle identity are exact, including
repeated reads, repeated values, and canceled ancestors. Eliminating E_C
gives the stated formula for O_C+d_C.

For an arbitrary union, the number q_C of all distinguished required odd
first occurrences in that union is the correct target credit. Selected
roots may themselves be ancestors of later roots. Replacing q_C by merely
the number of selected roots would generally be false; the note explicitly
avoids doing so.

For the first k distinguished odd target appearances, q_C=k. A different
distinguished odd occurrence in an ancestor cone would have appeared before
its root and hence belong to that same prefix. All other odd occurrences
count toward H_C, including duplicate target values, and H_C<=H globally.
This prefix must be relative to the entire required odd set used to define H.

## Target-dependent profile

The weighted union of supported coordinates is at most a+2f. If target
supports intersect, their cones share that actual input node. Thus physical
components satisfy c<=kappa(S), with the stated direction; canceled inputs
or other shared ancestors can join additional components. Nonnegative cycle
and even-fanout terms may then be dropped, and integrality gives b_lambda(S).

For each k, the actual first-k target set is one admissible subset in B_k.
Taking a minimum over those subsets and then a maximum over k is valid.
No cone charges from different prefixes are added. The one-target term is
nonnegative under the stated non-input odd-target hypothesis.

The support-rank interpretation is also correct: pair-difference subspaces
on weighted support sets merge exactly when their formal vertex sets overlap.
Their summed dimension is weighted union size minus overlap components.
This rank concerns formal input support, not physically supplied gate values.
Combining the profile with r and mu yields the stated whole-circuit bound;
the maximum with the even target count does not double-count even gates.

## Overlap and sharp families

The union lower bound from row sizes minus pair intersections remains valid
with higher intersections, since j-binomial(j,2)<=1. Pairwise intersection
makes every nonempty target overlap graph connected, proving the corollary.

For complete-graph stars, the k-target union formula is exact. Its concave
quadratic is maximized at k=v-3 or v-2, giving the displayed ceiling formula.
The comparison with the first-target bound is accurate. The separate total
cost v(v-2) follows both from direct computation for the upper bound and
transposition of all pair sums for the lower bound; no sharpness claim for
the H+d profile is made.

For the common odd core and disjoint even private groups, the full-union
bound is a+sum(b_i-1). The explicit circuit has exactly H=a and
d=sum(b_i-1), including the case a=0 where the core is an input. Its n-1
total gates are optimal by the connected full ancestor union. The common
core is counted once, so the construction directly checks the intended
sharing behavior and contains the earlier amplification family.

## Exact scope limitation for total-parity MixColumns

The specified sheet ordering proves B_*=1 without minimizing by enumeration.
The first-sheet union sizes are 5,7,8,8 with connected overlap. After j full
sheets, 1<=j<=6, blocks 0 through j-1 and block 7 supply 4(j+1) inputs.
The next p rows add at most min(4,p+2) own-block coordinates, while all
foreign blocks are already present. Thus each k=4j+p prefix has union size
at most 2k+3 and remains connected. The final sheet adds no input. These
prefixes give B_k<=1 for every k; minimum row weight five gives B_1=1.

The eight bit-position blocks are a compatible parity partition because
each row is odd on its own block and even on every foreign block. Therefore
s-c_max<=24. The standalone separated rank-plus-profile certificate under
total parity is at most 32+24+1=57. This does not limit other parity choices,
joint constraints on actual rank and supply, or retained physical cycle and
fanout terms. The saved note makes these distinctions explicitly.

The complete note passes review. Its general progress and its particular
MixColumns limitation are both stated accurately; no new MixColumns lower
bound is claimed.
