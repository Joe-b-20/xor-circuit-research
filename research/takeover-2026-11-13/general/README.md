# General arguments for unrestricted XOR circuits

2026-11-14, continuing reviewed commit `bd1b808`. The active task is general
structural understanding. Fixed-budget casework remains deferred. This phase
uses hand proofs and checks of specified constructions, with no SAT, circuit
search, representation enumeration, or computer-driven case elimination.

## Joint computation and supply have an unavoidable cost

[Private inputs and joint tradeoffs](PRIVATE_TAGGING_TRADEOFF.md) resolve a
previous open point: the minimum ternary resource P and minimum physical
odd-plus-odd supply count k can be incompatible by an unbounded amount, even
for invertible all-odd maps.

The general extension theorem is exact. If nonzero core targets f_i receive
pairwise disjoint blocks of private coordinate inputs, with B private inputs
in total, then

    L_2(f_i + private_block_i : all i) = L_2(f_i : all i) + B.

Sequential projection removes one distinct gate per private coordinate. It
allows arbitrary mixing and cancellation in the original circuit. Taking one
private coordinate for an even row and two for an odd row embeds any nonzero-row
linear computation into an all-odd invertible involution, with known additive
overhead between m and 2m. The all-odd class remains fully expressive.

For a simple graph with v vertices, m edges and c connected components, give
edge {u,w} its own input z_e and require x_u+x_w+z_e. Retaining core identity
outputs makes this map square and self-inverse. Its exact complexities are

    L_2=2m,             L_3=m,             r_min=v-c.

The separated-minima bound misses exactly beta=m-v+c, the target graph's
cycle-space dimension. For every unrestricted implementation,

    (r-r_min) + H+d+mu >= beta.

Here H counts extra odd gates, d even-plus-even gates, and mu cycle-closing
odd-plus-odd gates; r is actual even rank. These quantities concern the physical
implementation, while beta belongs to the specified target graph.

For the complete graph K_q, a star-pair construction at r=q-1 attains every
nonnegative integer split H+d+mu=beta. A nonstar edge can be paid for through
an odd helper, an even combination, or a directly supplied redundant pair.
Every option costs the same two gates including its private output. The exact
(k,P) frontier, with k odd-plus-odd gates and P=O+d, is

    (k,P)=(K,2m-K),              q-1<=K<=m.

The true binary cost divided by r_min+L_3 tends to two in this explicit family.
This is not a universal ratio theorem. Minimum rank r and minimum P actually
can coexist here, with mu=beta; their sum still misses redundant physical supply.
It is the separate minima of k=r+mu and P that cannot coexist. This distinction
is essential when interpreting the cost gap.

## Even aggregation cannot be eliminated cheaply

[Tree intersections and rigidity](TREE_INTERSECTION_RIGIDITY.md) start with a
general equality theorem. If targets use n coordinates and their support-overlap
graph has kappa components, every circuit has G>=n-kappa. At equality its complete
ancestor graph is a forest. Every gate then combines disjoint supports, and
every nonempty intersection of physical value supports is itself a physical
value. Canceled extra input ancestors are counted in the proof, not ignored.

Duplicated private attachments can therefore force actual even suppliers.
The simple pattern has suppliers e=a+b, f=c+d, h=e+f, and at least two private
odd outputs using each supplier. Its optimum requires h=e+f: removing that
even-plus-even operation forces one extra gate after arbitrary rewiring.

For b disjoint instances on N total inputs, every unrestricted implementation
satisfies

    G>=N-b,                     G+d>=N.

The exact optimum with at most D even-plus-even gates is N-min(D,b), for integer
D>=0. In particular removing all such gates costs exactly b. The proof allows
cross-instance sharing and cancellation; mixed physical components and their
cycles are charged rather than excluded. No general direct-sum theorem is used.
A connected hierarchy also forces arbitrarily many even aggregations in every
optimum, though no additive removal-gap formula is claimed for that hierarchy.

## What a single output can and cannot explain

[The single-target Pareto theorem](SINGLE_TARGET_PARETO.md) handles any actual
supplied dictionary S, even a dependent one. For each subset R representing a
nonzero target z, let o,e count odd/even members and I be z's parity. Its formula
resource point is

    K_R=(o-I)/2,                 P_R=(o+I)/2+e-1.

Every unrestricted continuation is dominated in both resources by ONE such
representation point. Conversely every point is attainable. The exact discrete
frontier consists of their nondominated points. A formal lift chooses the same
R before any prices are assigned; the argument is stronger than separate minima
or a convex-price bound. Ordinary single-target cost is the minimum actual
representation size minus one.

This identifies where the joint problem begins: separate single-output formulas
can duplicate shared work, so they cannot be added across outputs. The note's
supplied-dictionary separation example is explicitly not claimed to describe a
full coordinate-input prefix, where earlier intermediate values remain available.

## Retained results, checks, and next direction

The [available-supply metric and ternary normal form](AVAILABLE_SUPPLY.md),
[shared multi-output preparation bound](MULTI_OUTPUT_STARTUP.md),
[parity component accounting](ODD_COMPONENT_DEFECT.md),
[complement tradeoffs](COMPLEMENT_TRADEOFF.md),
[shared-helper amplification](SHARED_HELPER_AMPLIFICATION.md), and
[causal gaps](CAUSAL_BOOTSTRAP_GAP.md) remain available foundations.
The support-only total-parity MixColumns profile is exhausted: it is exactly
one, and that standalone rank-plus-profile certificate cannot exceed 57. The
unconstrained [quadratic relaxation](QUADRATIC_LIFT_LIMIT.md) likewise has its
proved ceiling. Neither is a circuit upper bound or a new MixColumns bound.

[Direct checks](checks/check_joint_supply.py) verify one mixed K_5 construction
with H=d=mu=2 and 20 gates, its invertibility and involution, three specified
supplier-copy constructions, one connected hierarchy, and the two displayed
single-target dictionary formulas. The [saved result](checks/joint-supply-result.json)
contains no optimization. Each mathematical note has independent machine review;
these are not formal verification, human certification, or claims of novelty.

Next: generalize the joint obstruction beyond private coordinates. The forest
intersection theorem forces suppliers exactly; a useful extension must control
how reconvergence and cancellation let circuits evade several such requirements
at once. A separate charge per missing intersection is not justified. Another
invariant is welcome if it captures the same joint physical cost more directly.
Do not return to fixed-budget classification or optimize the exhausted support
profile. Unrestricted MixColumns remains 75<=L<=88; 88 is not assumed optimal.

[Final scope review](reviews/joint-supply-progress-review.md) checks this synthesis,
the checkpoint, and the specified constructions, including the distinction
between minimum rank and minimum physical pair supply.
