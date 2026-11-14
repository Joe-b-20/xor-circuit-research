# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`f034b0d`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Isolated worktree: this chat's `work/xor-structural`.
Other worktrees and `search/proposals/` are preserved.

## Direction

General unrestricted mathematics is the priority. The user rejects incremental
numerical bounds and restricted casework without an unrestricted payoff. The
fixed-budget queue remains deferred. No SAT, circuit enumeration, exact search,
or computer-driven elimination. Supporting linear algebra and checks of specified
constructions are allowed. Read [the synthesis](general/README.md) first.

## New joint invariant: preparation of a target subspace

[Subspace preparation](general/SUBSPACE_PREPARATION.md). For actual dictionary S
and W spanned by required outputs, let R(S) span S intersect W and all u+v from
supplied pairs equal modulo W. R consists exactly of W-values obtainable with
no new outside-W gate, although their inside-W computation is not free.

Inside-W gates cannot enlarge R. A gate at a new nonzero quotient value cannot
enlarge R either. A gate at an existing nonzero quotient value enlarges it by
zero or one dimension. With q=dim(W/R0), final/initial nonzero quotient-value
counts t_f,t_0, and zeta the number of repeat-color gates not enlarging R,

    H_out = (t_f-t_0)+q+zeta.

For q>0 put Delta=min_{w in W minus R0} ell_S(w), necessarily at least three.
Every continuation producing a spanning set of W-values has

    H_out >= q+Delta-3.

Before the first successful collision, all inside-W values lie in R0. Grant R0
only in a lower-bound relaxation; absorption preserves the minimum escape word
length. The first collision needs Delta-2 outside gates; q-1 further collisions
need one each. Add only distinct missing W-targets to this count, not all outputs
of a larger map. Other required outside-W outputs are already counted in H_out.

More generally, for proper U containing R0, H_out>=dim(W/U)+min_{W minus U}ell_S-3.
For R_[k]=span{w in W:ell_S(w)<=k}, k>=2, R_[2]=R0; whenever R_[k] is proper,
H_out>=dim(W/R_[k])+k-2. No efficient computation of this profile is claimed.

Coordinate specialization: target span dimension r, minimum nonzero weight D>=3
imply H_out>=r+D-3. It is sharp for distance-three and distance-four families
of arbitrary dimension, and dimension one at every D. Independent weight-three
targets with no weight-one/two vector in their span have exact cost 2m; any saving
requires such a low-weight combination. This is a necessary condition, not a
sufficiency claim.

[Common-offset preparation](general/COMMON_OFFSET_PREPARATION.md) is recovered
exactly: after its real 4rm-gate prefix, R0 is the even-combination subspace of
the m independent targets, dimension m-1. Thus q=1, Delta=2r+1, forcing 2r-1
outside gates and m target gates, attained by computing the common offset.
All individual target frontiers remain (r,r); the joint invariant sees what
those profiles missed. Prefix cost remains separate from remaining complexity.

Scope: W=V gives R0=W and no bound on outside work. Proper subspaces still give
unrestricted constraints, but their outside-gate counts overlap and cannot be
added without a new argument.

## Sharing capacity without a fixed supply basis

[Supply tradeoff](general/SIDON_SUPPLY_TRADEOFF.md). On coordinate inputs with
m distinct non-input odd targets, H extra odd gates and E even gates satisfy
G=m+H+E. Let alpha be the maximum boundary-pair multiplicity of a nonzero XOR
and nu the analogous target-pair multiplicity. Then

    m <= alpha*E + (H+sqrt(H^2+4*nu*H*E*(E-1)))/2.

First-target gates with a boundary odd parent contribute at most alpha*E;
the others form a bipartite helper/even graph with common-neighbor capacity nu.
All internal values, EE work, redundant supply and cancellation are allowed.
This refines the existing Sidon argument; it is not a new graph technique.

For Sidon inputs-plus-targets, alpha=nu=1 (single-target case handled separately).
With s=H+E, 27*max(m-s,0)^2<=4*s^3 and G>=m+ceil((m/2)^(2/3)). An explicit
prime-q affine-incidence map replaces each point by three private coordinates,
each line by two, and requires their incident weight-five sums. It is a Sidon
boundary and has exact unrestricted cost q^3+3q^2 by column cloning. Therefore
the overhead exponent 2/3 is sharp. No claim about its minimum possible even
rank, and no MixColumns-specific numerical improvement, is needed.

## Evidence and next task

Both notes have independent machine reviews and primary-agent proof checks;
no formal verification, human certification, or literature-novelty claim.
[Specified checks](general/checks/check_subspace_and_sidon.py) and
[saved results](general/checks/subspace-sidon-result.json) verify quotient-rank
evolution for the sharp examples and the common-offset continuation (36 paid
prefix gates, eight remaining), and q=3 incidence (27 targets, 54 gates,
H=9,E=18, 18 column classes). No circuit, representation or codeword search.
[Final scope review](general/reviews/subspace-sidon-progress-review.md).

Next: control shared credit across several proper target subspaces, or connect
independent-relation growth to the difference-multiplicity tradeoff. Merely
summing subspace counts is invalid. Seek a general joint argument, retaining
actual supply and arbitrary competing bases; no fixed-budget casework.
Unrestricted MixColumns remains 75<=L<=88, with no assumption that 88 is optimal.

Retain [joint normal form](general/JOINT_DICTIONARY_NORMAL_FORM.md),
[coset saturation](general/COSET_SATURATION.md),
[branch repair](general/BRANCH_INTERSECTION_REPAIR.md),
[simultaneous repair gap](general/CAUSAL_FOREST_QUOTIENT.md), and
[pair-supply tradeoffs](general/PRIVATE_TAGGING_TRADEOFF.md). Keep full beta
separate from odd mu, rank from physical supply count, and remaining cost from
end-to-end cost. The 57/58/60 certificate ceilings are not circuit bounds.
History: [summary](SUMMARY.md), [record](../structure-2026-11-11/RECORD.md).
Use Git with `-c core.filemode=false`; shared configuration is unchanged.
Stage only intended research files.
