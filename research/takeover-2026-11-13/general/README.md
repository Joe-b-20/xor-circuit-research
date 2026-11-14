# General arguments for unrestricted XOR circuits

2026-11-14, continuing reviewed commit `44fa588`. General structural understanding
remains the priority. Fixed-budget classifications are deferred. This phase uses
hand proofs and checks of specified constructions, without SAT, circuit search,
representation enumeration, or computer-driven case elimination.

## Shared preparation can be invisible to every separate target profile

[Common-offset preparation](COMMON_OFFSET_PREPARATION.md) gives two actual
chronological states of the same coordinate-input computation where every
target's COMPLETE individual resource frontier is unchanged, yet their joint
remaining cost differs by an unbounded factor.

Write K for odd-plus-odd gates and P for all other gates, so binary size is K+P.
For parameters r,m>=1 the individual frontier of every target is (r,r) at both
states. The exact joint frontiers are

    initially: (K,P)=(rm,rm),
    after preparation: (K,P)=(r,m+r-1).

The remaining binary costs are therefore 2rm and m+2r-1; their ratio is unbounded
when m=r grows. The prefix retains EVERY intermediate and costs 4rm gates,
charged separately. This is an information barrier for state measurements,
not a faster end-to-end circuit. The whole target map can be a square all-odd
involution, so the example does not depend on singularity or an artificial
non-coordinate initial supply.

The mechanism is exact: the prefix supplies u_i=t_i+h for a common unsupplied
h. It changes relations BETWEEN targets without shortening any target's own
resource profile. Their pairwise difference lengths do change; no equality of
the full dictionary metrics is claimed.

More generally, if an actual dictionary supplies t_i+h, with ell(h)=q and
ell(t_i)=q+1 for all m distinct targets, then exact remaining binary cost is
m+q-1. The first target forces q gates, each later target forces another, and
computing h once attains the bound. This is an unrestricted common-offset law,
not an assumption about how competing circuits are organized.

## An exact joint normal form

[Joint dictionary computation](JOINT_DICTIONARY_NORMAL_FORM.md) replaces separate
representations by one joint lift. If the actual dictionary has row matrix B
and T is the target matrix, then

    L_S(T)=min_(RB=T) L_2(R).

Each R records simultaneous representations in independent formal dictionary
labels. Lifting a real circuit preserves its shared gates; projecting a circuit
for R back to the actual values gives the converse. Dependence is retained by
RB=T, not replaced by free span access.

Exact column compression gives

    L_S(T)=min_(RB=T) [n(R)-t(R)+L_2(R_red)],

where n counts used dictionary members and t their distinct nonzero output
patterns. Some optimum first computes DISJOINT groups of dictionary members
with the same pattern, then runs a residual circuit on those group sums.
The groups can overlap in original coordinate support and their sums can be
dependent; the formal lift makes the cost statement valid nevertheless.

The residual cost is essential. For B=I the lift is uniquely T; if T already
has distinct nonzero columns, the entire original circuit problem remains.
This is an exact structural description, not an efficient algorithm or a
solution of general linear circuit complexity.

For TWO distinct nonzero targets there is a concrete exact consequence:

    L_S(u,v)=min { ell(u)+ell(v)-2,
                   min_(h!=0)[ell(h)+ell(u+h)+ell(v+h)-1] }.

Thus some optimum has one shared value h and two residual branches, or computes
the targets separately. Every term charges actual dictionary word length;
zero residuals are omitted without supplying a physical zero. This does not
justify summing pairwise bounds across many outputs, nor start a small-output
case-classification queue. The general joint normal form remains the main result.

## When shared preparation is completely effective

[Coset saturation](COSET_SATURATION.md) gives an exact positive family with no
extra odd helpers. Partition n coordinate inputs into c>=2 nonempty parts, and
require ALL vectors odd on exactly one part and even on the others. Put r=n-c.
There are c*2^r targets, including the n coordinate inputs, and

    L_2=c*(2^r-1).

Compute r actual within-part pair values forming a basis. Each required coset
is connected by addition of those basis values, so a traversal rooted at its
already available coordinates uses one gate per remaining required output.
Nothing else from the even span is free. Compatible input partitions force
at least r even rank, giving the matching unrestricted lower bound.

Every optimum has exactly r even gates and c*2^r-n odd gates, with no extra
odd gates, no even-plus-even gates, and no odd-occurrence cycles. For c>=3 its
input parity partition is the specified one. The full ancestor graph need
not be a forest. In the c=2 special case these are all odd linear forms, with
exact cost 2^(n-1)-2.

The structural lesson is closure: the paths connecting required values use
other required values, so every step after the basis is paid for is productive.
This theorem does not claim that sparse target sets, or MixColumns, have that
closure, or that an uncharged fixed basis may be imposed on an arbitrary circuit.

## Evidence, retained limits, and next direction

All three notes have independent machine reviews and primary-agent proof checks,
not formal verification, human certification, or claims of literature novelty.
[Direct checks](checks/check_joint_dictionary.py) and
[saved results](checks/joint-dictionary-result.json) verify r=m=3 (36 paid prefix
gates, remaining costs 18 and eight, unchanged single-target frontier (3,3)),
two fixed joint lifts, the corresponding seven-gate two-target shared formula,
and one nine-gate coset construction on five inputs. These are specified
construction checks, not optimization.

The [branch-value identity](BRANCH_INTERSECTION_REPAIR.md),
[one-cycle simultaneous-repair gap](CAUSAL_FOREST_QUOTIENT.md),
[exact column cloning](COLUMN_CLONING.md),
[joint pair-supply tradeoffs](PRIVATE_TAGGING_TRADEOFF.md), and
[forced even aggregation](TREE_INTERSECTION_RIGIDITY.md) remain foundations.
Keep full ancestor cycle rank separate from parity-specific mu, rank separate
from physical pair count, and appended costs separate from optimal rewiring.
The 57,58,60 ceilings limit their named certificates only, not MixColumns itself.

Next: a target-forced joint obstruction on affine sharing patterns and the
residual distinct-pattern computation. Separate target profiles, rank-only
boundaries, and a free-span model discard necessary information. The saturation
theorem identifies when all odd work can be required outputs; a useful converse
must allow competing supply bases, extra rank, even aggregation, and cancellation.
Do not obtain a restricted bound by fixing a basis without paying for it or
justifying the restriction. A different invariant is welcome. Unrestricted
MixColumns remains 75<=L<=88; 88 is not assumed optimal.

[Final scope review](reviews/joint-dictionary-progress-review.md) checks the
synthesis, checkpoint, fixed constructions, and the distinctions between
individual and joint costs, paid preparation and remaining work, and an exact
normal form and an algorithm for finding its optimum.
