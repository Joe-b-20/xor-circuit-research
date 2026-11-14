# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`656980c`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Isolated worktree: this chat's `work/xor-structural`.
Other worktrees and `search/proposals/` are preserved.

## Direction

General unrestricted mathematics is the priority. The user rejects incremental
numerical bounds and restricted casework without an unrestricted payoff. The
fixed-budget queue remains deferred. No SAT, circuit enumeration, exact search,
or computer-driven elimination. Supporting linear algebra and checks of specified
constructions are allowed. Read [the synthesis](general/README.md) first.

## Current positive theorem: physical intersection repair

[Branch identity](general/BRANCH_INTERSECTION_REPAIR.md): for k marked outputs,
reverse path-parity vectors eta_v and actual reader/terminal degree d_v satisfy
sum(d_v-1)=g-a+k=beta+k-c. For any phi with phi(0)=0, the sum of ordinary values
times their local phi reader-defects telescopes to the transformed input column
patterns plus terminal correction. Only d_v>=2 occurrences contribute. All such
boundaries share ONE physical branch dictionary of size at most beta+k-c.

For two outputs choose phi(s,t)=st: their nonzero support intersection has an
actual-dictionary representation of length at most beta+1, and needs at most
beta appended XORs. Here beta is the FULL ancestor cycle rank; it is not mu of
the odd-occurrence graph. Zero-intersection repair is excluded unless a separate
zero convention is supplied. Distinct marked occurrences permit all selected
branch values before the later marked result.

The bound is sharp at every beta=t-1. The block quotient maps each of c_i,a_i,b_i
to one unit and all computed values to zero, forcing t terms for sum c_i.
Private attachments give sharp specified optimal all-odd involutions on 7t inputs
with 8t-2 gates. This proves appended cost from that dictionary, not a lower
bound after freely rewiring an enlarged target set.

## Causal forest quotient and exact simultaneous-repair obstruction

[Forest quotient](general/CAUSAL_FOREST_QUOTIENT.md): cut beta nonforest operand
edges, replacing their reads by formal shadow inputs. The same gates form a
forest. Projection back has kernel dimension beta, with triangular causal basis
s_l+U_l, where U_l is the formal value at the earlier cut source. These are paid
prior computations, not arbitrary free boundary forms.

For m>=2 take r,z,a_i,b_i. Compute e_i=a_i+b_i, prefixes p_j=r+sum_(i<=j)e_i,
e_0=r+z, q=p_m+e_0. Targets p_j,q plus free r,b_i identities form an invertible
all-odd map. Exact L_2=2m+2, beta=1, while d=mu=0. The m-1 independent missing
intersections c_2,...,c_m each cost one XOR p_j+r. Requiring all of them changes
exact complexity to 3m, an unbounded m-2 penalty despite full rewiring. The map
is not asserted to be an involution. Raw count/rank of missing intersections and
constant total repair cost per cycle are therefore invalid lower-bound premises.

## Exact column reduction and the rank-only limitation

[Column cloning](general/COLUMN_CLONING.md): with n active columns in t identical
nonzero classes, L_2(M)=n-t+L_2(M_red). Sequential projections delete one distinct
gate per clone; class sums attain it. General retained-coordinate projection is
L_2(M)>=n-|X|-kappa_0+L_2(M|X), with kappa_0 the input co-occurrence components
missed by X. Binary-size statements only; zero target rows are omitted by the
stated convention, and no parity-resource preservation is asserted.

For all normalized Boolean functions in the branch identity, the boundary span
is exactly the span of p distinct nonunit column-pattern indicators. Rank alone
gives G>=n+p-k, the ordinary transposition count. For 32 inputs its maximum over
all selected-row subsets is at most 58, from p<=min(32,2^k-k-1). Higher degrees
cannot improve THAT rank certificate. This is not a circuit bound or a limitation
on all nonlinear methods. The earlier 57/60 ceilings also have their named scopes.

## Evidence and next task

All three notes have independent machine reviews linked within them, and the
primary agent checked the arguments. No formal verification, human certification,
or literature-novelty claim. A
[final scope review](general/reviews/intersection-progress-review.md) checks the
synthesis and specified evidence. [Specified checks](general/checks/check_intersection_repair.py)
and [saved results](general/checks/intersection-repair-result.json) verify m=4
(original10/repaired12 gates, missing rank3, full beta1/odd mu0), t=3 sharp
optimal involution (21 inputs/22 gates, pair beta2, representation3), branch
identities, causal shadow projections, and kernel ranks. No search.

Next: a joint cost for several combinations from the SAME physically supplied
branch dictionary. Cheap individual repair and a small linear kernel do not
control simultaneous preparation. Raw missing rank and unconstrained boundary
rank are exhausted. Preserve actual supply, shared coefficients, and chronology,
or introduce a different invariant. Unrestricted MixColumns remains 75<=L<=88.

Prior [joint supply](general/PRIVATE_TAGGING_TRADEOFF.md),
[forced EE](general/TREE_INTERSECTION_RIGIDITY.md), and
[ternary](general/AVAILABLE_SUPPLY.md) results remain. Minimum rank and minimum
ternary cost may coexist while mu pays a gap; do not confuse rank with physical
pair count. History: [summary](SUMMARY.md), [record](../structure-2026-11-11/RECORD.md).
Use Git with `-c core.filemode=false`; shared configuration is unchanged.
Stage only intended research files.
