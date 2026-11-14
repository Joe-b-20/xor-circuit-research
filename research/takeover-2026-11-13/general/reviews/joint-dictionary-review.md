# Independent review: joint dictionary lifts and two-target cost

2026-11-14. Independent machine review of the complete
[JOINT_DICTIONARY_NORMAL_FORM.md](../JOINT_DICTIONARY_NORMAL_FORM.md).
I reconstructed the joint lift, column compression, two-output optimum, and
shared-value distance formula. No circuit search, representation enumeration,
or computer-driven elimination was used. This is not formal verification,
human certification, or a literature-novelty assessment.

## The formal lift is joint and preserves every physical gate

Replacing each supplied dictionary member by its own independent formal input
preserves the actual continuation's parent pointers and gate count. Projection
back to the supplied values recovers every gate, including actual zero values
that may lift to nonzero formal values. All final formal rows project to the
required nonzero targets, so they satisfy the same matrix constraint R B=T.
This gives the lower bound by one common lifted circuit, not separate lifts
that duplicate shared gates. Conversely executing any circuit for a feasible
R on the actual dictionary supplies T with no more gates. Hence the equality
of the actual optimum with the minimum lifted complexity is exact.

Dependence among dictionary members remains in R B=T. No additional vector
of their span is treated as an available operand. Known targets, unused
dictionary entries, and repeated target rows cause no exception.

## Column compression retains the residual circuit problem

For every fixed lift, the exact column-cloning theorem separates n(R)-t(R)
group-sum gates from the complexity of the reduced distinct-pattern matrix.
The groups partition supplied members by incidence in the joint target
representations. They need not have disjoint original-coordinate supports.
Projected group sums can coincide or be zero; the displayed construction
still computes each actual sum in the charged number of gates and projects
the residual circuit correctly. Such coincidences can only make this
particular implementation cheaper, consistent with the outer minimum.

The note correctly retains L_2(R_red). For an independent dictionary and an
already column-reduced target matrix, that term is the entire original
complexity problem. Thus the identity is not overstated as an efficient
algorithm, a rank formula, or a resource-preserving parity normal form.

## Exact complexity of two formal target supports

For nonempty support sets A,B, their union has one support-overlap component
when they intersect and two otherwise. The full ancestor count gives the
claimed lower bound |A union B|-kappa, with no cancellation restriction.
The construction first sums the common group once and separately sums the
exclusive groups, attaching each nonempty exclusive group to the common
value. Its count is exactly union size minus one in the overlap case, or
the sum of the two individual formula sizes when disjoint.

The same count covers an empty exclusive group: that target is already the
common value. It also covers a supplied target represented by a singleton.
No physical zero is required merely to represent an omitted empty arm.
The joint-lift equality therefore proves the exact dictionary formula for
all competing continuations, including those with arbitrary internal sharing.

## The shared-value metric formula

For nonzero h, computing h and then its two residual arms costs at most
ell(h)-1+ell(u+h)+ell(v+h). A zero residual means its target equals h and is
omitted; this includes h=u or h=v. The separate-computation term handles the
disjoint alternative. All nonzero intermediate values are charged through
their actual dictionary lengths.

For the reverse comparison, choose optimal joint supports A,B. If they
are disjoint, separate shortest representations cannot cost more. Otherwise
their common group C cannot sum to zero: removing C leaves two nonempty,
disjoint representations of the same nonzero targets and lowers the cost
strictly. Thus h=XOR(C) is nonzero. The common and exclusive groups represent
h,u+h,v+h, so their sizes bound the corresponding word lengths. This proves
the other inequality and the claimed equality.

The minimizing metric representations need not be disjoint, which is harmless:
the upper construction can execute their formulas separately, while the
lower comparison uses the disjoint groups from an optimal joint lift. The
argument never assumes individually shortest representations share optimally.

The full note passes review. It distinguishes exact two-target cost from
additive bounds over many pairs, actual dictionaries from free spans, and
structural characterizations from algorithms for finding the minimum. It
makes no new numerical MixColumns claim.
