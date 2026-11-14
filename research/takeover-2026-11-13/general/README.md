# General arguments for unrestricted XOR circuits

2026-11-14, continuing reviewed commit `656980c`. General structural understanding
remains the priority. Fixed-budget casework is deferred. This phase uses hand
proofs and verification of specified constructions, without SAT, circuit search,
representation enumeration, or computer-driven case elimination.

## A general law for recovering one shared overlap

[Physical branch values](BRANCH_INTERSECTION_REPAIR.md) extend the forest
intersection theorem to arbitrary circuits. Select two physical values and take
the complete union of their ancestor cones. If its full undirected cycle rank
is beta, their nonempty support intersection can be expressed using at most
beta+1 values already physically available. Therefore at most beta additional
XOR gates suffice to produce that one intersection. The bound is sharp at every
beta, including in specified optimal all-odd invertible circuits.

The proof is an exact identity, not a restricted circuit classification. Mark
k output ports. For each occurrence v let eta_v record its reverse path-parity
vector to the ports, and let d_v count its reader and terminal ports. With g
gates, a actual input ancestors, and c components,

    sum_v(d_v-1)=g-a+k=beta+k-c.

For any Boolean function phi with phi(0)=0, form its local defect across those
reader ports. Multiplying the defect by the ordinary physical value at v and
summing cancels all internal XOR contributions. Only the transformed input
column patterns and the prescribed terminal correction remain. Degree-one
nodes have zero defect. Thus ONE common dictionary of at most beta+k-c physical
branch values represents every such corrected boundary vector.

For two outputs, phi(s,t)=st gives their support intersection and the beta+1
bound. Repeated reads, duplicate ports, cancellation, zero intermediate values,
and ancestors among the selected outputs are allowed. This beta is the cycle
rank of the FULL ancestor graph, not the parity-specific odd-graph cycle rank mu.
An empty intersection is the zero vector; the additional-gate statement is
explicitly for nonzero intersections, without assuming a free physical zero.

## Cheap individual repair does not mean cheap simultaneous repair

[The causal forest quotient](CAUSAL_FOREST_QUOTIENT.md) gives an exact structural
normal form. Cut beta nonforest operand edges and replace their reads by fresh
formal inputs. The resulting graph is a forest with the same gates. Its projection
back to the original circuit has a beta-dimensional kernel with a causal
triangular basis: each shadow input equals an actual earlier source value.
Those relations retain availability; they do not grant arbitrary free suppliers.

A one-cycle family shows how strongly one relation can be reused. On inputs
r,z,a_i,b_i, i=1,...,m, compute e_i=a_i+b_i, successive p_j=r+sum_(i<=j)e_i,
e_0=r+z, and q=p_m+e_0. Retaining r and the b_i as identity outputs makes the
map square and invertible; all outputs are odd. For m>=2,

    original exact L_2 = 2m+2,       full cycle rank beta=1.

The m-1 independent intersections c_j=sum_(i<=j)e_i, j=2,...,m, are absent.
Each is just p_j+r, so individually needs one XOR. Requiring all these values
simultaneously has exact unrestricted complexity

    repaired L_2=3m,                extra cost=m-2.

The lower bound allows complete rewiring. Thus neither missing-intersection
count nor its raw vector rank can be charged at a constant rate per cycle;
even simultaneous repair cost can grow without bound at beta=1. The example
also has d=mu=0 in the parity account. A parity forest and a full ancestor forest
are different objects. The square map is invertible, not claimed self-inverse.

## Exact projection beyond private coordinates

[Column cloning](COLUMN_CLONING.md) supplies the exact cost used in that example
and applies to arbitrary target matrices. If n active coordinate columns fall
into t identical nonzero column classes, with one representative per class in
M_red, then

    L_2(M)=n-t+L_2(M_red).

Project all other class members away: each deleted coordinate still shares a
target with its retained representative, forcing a distinct gate deletion.
Computing each class sum supplies the matching upper bound. No competitor is
assumed to group the inputs first. These are binary-size statements, not
preservation of parity resources.

More generally, for retained active coordinates X, let kappa_0 count components
of the input co-occurrence graph disjoint from X. Root a spanning forest at X
and one temporary root in each remaining component. Projection from leaves
inward gives L_2(M)>=n-|X|-kappa_0+L_2(M|X). This does not assume separate circuits
for different components. The note explicitly treats the nonzero target problem.

## A broad rank-only ceiling

The branch identity retains actual values and their coefficients. If only the
rank of its boundary vectors is kept, all Boolean functions together yield
exactly the span of the indicator masks of distinct nonunit column patterns.
If p such patterns occur in k selected rows, that span has dimension p, giving

    G>=n+p-k.

This is the ordinary transposition/distinct-output bound with a physical
interpretation. Higher-degree functions cannot enlarge this boundary span.
For any selected rows on at most 32 supported coordinates,

    n+p-k <= 32+min(32,2^k-k-1)-k <= 58.

Thus maximizing this rank-only certificate over MixColumns row subsets cannot
reach 75. This limits that certificate, not constrained branch decompositions,
all possible nonlinear methods, or circuit complexity. No subsets were searched.
The earlier support-profile ceiling 57 and quadratic relaxation ceiling 60 are
also limitations of their named certificates, not circuit upper bounds.

## Evidence, retained results, and next direction

The [specified checks](checks/check_intersection_repair.py) verify the m=4
one-cycle example and its 12-gate repaired construction, and a t=3 sharp optimal
involution on 21 inputs with 22 gates. They directly evaluate the branch
certificates, masks, ranks, displayed inverses, causal shadow projections, and
kernel bases. The [saved result](checks/intersection-repair-result.json) contains
no optimization or representation search. Each note has independent machine
review; this is not formal verification, human certification, or a novelty claim.

Retained results include [exact joint supply tradeoffs](PRIVATE_TAGGING_TRADEOFF.md),
[forced even aggregation](TREE_INTERSECTION_RIGIDITY.md),
[the single-target frontier](SINGLE_TARGET_PARETO.md),
[the ternary reformulation](AVAILABLE_SUPPLY.md), and
[parity component accounting](ODD_COMPONENT_DEFECT.md). In the earlier graph
family, minimum rank and minimum ternary work can coexist while redundant
physical pairs carry the gap; minimum physical pair count and minimum ternary
work are the incompatible minima. Keep that distinction intact.

Next: control the JOINT cost of forming several combinations from the common
physical branch dictionary. Individual repair is understood, raw missing rank
fails, and rank-only boundary functions collapse to transposition. A useful new
argument must retain physical dictionary complexity, shared coefficients, or
causal constraints that those relaxations discard. A different framework is
welcome; do not resume small-budget classification or an exhausted certificate.
Unrestricted MixColumns remains 75<=L<=88, with no assumption that 88 is optimal.

[Final scope review](reviews/intersection-progress-review.md) checks the synthesis,
checkpoint, specified evidence, and the separate meanings of physical cycle rank,
local appended repair, and unrestricted simultaneous repair.
