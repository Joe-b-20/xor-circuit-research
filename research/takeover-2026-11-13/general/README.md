# General arguments for unrestricted XOR circuits

2026-11-14, continuing reviewed commit `4136cf8`. General structural understanding
remains the priority. Fixed-budget classifications are deferred. This phase uses
hand proofs and checks of specified constructions, without SAT, circuit search,
representation enumeration, or computer-driven case elimination.

## One gate activates at most one empty output layer

[Flag relation transport](FLAG_RELATION_TRANSPORT.md) resolves overlapping
relation credit for nested subspaces. Along a flag, adjoining one value changes
the relation ranks on a single interval. In layer dimensions this moves one
rank unit from a later layer to an earlier one; crossing many cuts is one move.

There is a stronger law for flags formed by successively spanning required
outputs. Every strict output step has dimension one. Its layer is occupied
exactly when the actual dictionary has a word of length at most two in that
prefix subspace but outside the preceding one. This witness persists, so an
occupied output layer never becomes empty. Let Phi count initially empty
layers. A gate can activate at most one of them.

Choose the flag from the circuit's ACTUAL first-production order. A required
output gate activates no layer: earlier prefixes are already spanned and later
prefixes contain its result. Thus, with M selected absent outputs,

    G = M + Phi + Z,

where Z counts auxiliary gates that leave the empty-layer count unchanged.
This is exact, allows cancellation and dependent dictionaries, and counts other
required outputs among auxiliaries if they were not selected. For a target-only
bound, minimize Phi over possible orders; choosing a favorable order without
justification is invalid. Before the first activation, a distance argument also
forces Z>=Delta_*-3, where Delta_* is the minimum escape length of any initially
unsaturated cut in that SAME flag. Single parities and the prepared common-offset
family attain the resulting bound.

The abstract transport relaxation requires exactly Phi moves; a greedy proof
attains this by filling deficits from later surplus layers. Actual dictionary
and operand constraints are essential to force further work. A full-rank family
on B disjoint four-coordinate blocks has exact unrestricted cost 5B for 4B
outputs, proving the auxiliary count sharp even when competitors mix blocks.
For a complete coordinate-input basis flag, bare Phi<=n-ceil(log2(n+1)); the
32-output bare certificate is at most 58. This ceiling excludes the separate
distance correction and is not a bound on MixColumns complexity.

## A known exact graph law exposes the remaining physical cost

[Common-anchor graphs](COMMON_ANCHOR_GRAPH.md) recover the known
Boyar–Matthews–Peralta theorem: for graph edges uv and targets a+x_u+x_v,
exact unrestricted cost is m+tau(F), with tau the minimum vertex-cover size.
The note cites the primary paper and gives a short binary parity-partition
proof. Every compatible input partition yields a cover of size equal to its
rank; a cover supplies actual helpers a+x_v attaining that count. Every optimum
has even rank tau, no excess odd gates, no EE gates, and no odd-graph cycles.
This does not imply cancellation-free wiring; a five-gate triangle optimum
explicitly cancels a variable and uses no anchor-pair helper.

The new diagnostic is exact too. For any selected edge set, the initial
short-relation deficiency is its number of active components if the selected
graph is bipartite, and zero if any odd cycle is present. An odd cycle supplies
the anchor as a span relation, making all edge directions accessible to the
closure, without physically preparing their helpers.

For EVERY connected graph, the maximum of the distance-augmented chronological
flag certificate over selected target subsets is only m+1, after the necessary
minimum over orders. The true cost remains m+tau(F). On a path this is
m+ceil(m/2), even though every output has weight three; retaining two identity
outputs makes the map square, invertible, and all odd. This is a precise limit
of that certificate, not of all subspace methods or of an argument that first
proves a useful circuit normalization.

The distinction is physical: accessible relations and one representative per
output layer do not determine how many intermediate values must actually be
computed. The parity-partition account detects this missing cost in the graph
family. A more general argument must retain it while allowing all sharing.

## Independent directions force preparation outside the target subspace

[Subspace preparation](SUBSPACE_PREPARATION.md) gives a joint state invariant
for ANY actual supplied dictionary S and target subspace W. Let R(S) be the
span of supplied W-values and differences of supplied values equal modulo W.
Exactly those W-values can be recovered without producing new outside-W values;
their physical computation inside W can still cost gates.

A gate producing a value in W cannot enlarge R. An outside gate can enlarge it
by at most one dimension, and only when its quotient value repeats an available
one. If the required W-values span W, put q=dim(W/R(S)). For q>0 let Delta be
the shortest S-word representing any value in W outside R(S). Then every
unrestricted continuation uses

    outside-W gates >= q+Delta-3.

The first independent relation forces Delta-2 outside gates; each remaining
independent relation forces another. Dependent dictionaries, cancellation, and
all intermediate choices are allowed. Granting an already known subspace is
used only as a lower-bound relaxation, with an absorption lemma preserving the
minimum escape distance. More generally, if R_[k] is the span of W-values with
S-word length at most k>=2 and R_[k] is proper, then

    outside-W gates >= dim(W/R_[k])+k-2.

This is a rank profile of joint short representations, not separate output costs.
For coordinate inputs and a target span of dimension r and minimum nonzero
weight D>=3, it gives at least r+D-3 gates outside that span. With M required
non-input outputs in the span, total cost is at least M+r+D-3. In particular,
m independent weight-three targets whose span contains no weight-one or
weight-two vector have exact unrestricted cost 2m. Any saving for independent
triples therefore requires a low-weight combination of the whole target set;
pairwise overlap alone does not settle the question.

The common-offset example below now has a positive explanation. Its paid prefix
raises dim R from zero to m-1 without shortening any target's individual
frontier. One direction remains, at distance 2r+1. The theorem forces 2r-1 outside
gates plus m target gates, exactly the remaining cost m+2r-1.

For W equal to the whole input space, R(S)=W and this obstruction is vacuous.
Proper subspaces still constrain arbitrary full circuits, but their outside
counts overlap and cannot simply be added. This is a general preparation law,
not a new MixColumns lower bound or an efficient algorithm for the rank profile.

## Sparse target differences limit sharing, without fixing a supply basis

[The supply tradeoff](SIDON_SUPPLY_TRADEOFF.md) refines the repository's existing
Sidon counting argument by gate parity. Let m non-input odd targets be required,
H count other odd gates, and E count all even gates. If inputs together with
targets have no four distinct values summing to zero, then

    m <= E + (H+sqrt(H^2+4*H*E*(E-1)))/2.

First-target gates with an input or target odd parent use distinct even values.
The others form a bipartite graph between extra odd values and supplied even
values; a four-cycle would contradict the target relations. This charges both
resources and permits arbitrary cancellation, EE gates, redundant supply, and
choice of basis. A general version replaces uniqueness by the maximum number
of boundary/target pairs with each difference, so it applies to all odd maps.

Writing s=H+E, the Sidon case gives 27*max(m-s,0)^2<=4*s^3 and in particular
G>=m+ceil((m/2)^(2/3)). An explicit affine-incidence family with m=q^3 weight-five
targets has exact unrestricted complexity m+3*q^2 by column cloning. Thus the
overhead exponent 2/3 is sharp for this target class. This is a refinement of
an existing graph mechanism, not a literature-novelty claim or a numerical
improvement for MixColumns. The hypothesis restricts the specified targets;
it does not restrict how a competing circuit is allowed to compute them.

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

The previous three notes have independent machine reviews and primary-agent proof checks,
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

The new [subspace review](reviews/subspace-preparation-review.md) and
[sharing review](reviews/SIDON_SUPPLY_TRADEOFF_REVIEW.md) independently audit the
hand proofs. [Specified checks](checks/check_subspace_and_sidon.py) and
[saved results](checks/subspace-sidon-result.json) verify the actual quotient
rank evolution, sharp coordinate examples, the prepared eight-gate continuation,
and the q=3 incidence construction (27 targets, 54 gates, H=9,E=18). No circuit,
representation, or codeword search is used. The
[final scope review](reviews/subspace-sidon-progress-review.md) checks the synthesis.

The latest [flag proof review](reviews/flag-relation-transport-review.md),
[adversarial review](reviews/flag-relation-adversarial-review.md), and
[graph review](reviews/common-anchor-graph-review.md) check the transport,
monotonicity, exact accounts, source attribution, and certificate limits.
[Specified checks](checks/check_flag_and_anchor.py) and
[saved results](checks/flag-anchor-result.json) verify fixed interleaved blocks,
a seven-edge path, and a cancelling triangle, with chronological rank traces.
No orders, target subsets, representations, or circuits are searched.
[Final scope review](reviews/flag-anchor-progress-review.md).

Next: the physical cost of supplying several useful representatives inside an
already accessible relation space. Couple preparation with parity partitions or
actual dictionary structure; rank transport alone has the explicit graph-family
limit above. Non-nested overlap also remains open. Do not return to a fixed
basis or fixed-budget classification. Unrestricted MixColumns remains 75<=L<=88;
88 is not assumed optimal.
