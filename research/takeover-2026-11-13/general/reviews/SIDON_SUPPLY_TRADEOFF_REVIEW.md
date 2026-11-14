# Independent review: parity-resolved Sidon supply tradeoff

2026-11-14. Independent symbolic review of
[SIDON_SUPPLY_TRADEOFF.md](../SIDON_SUPPLY_TRADEOFF.md), including its
multiplicity extension and exact affine-incidence family. I also reconstructed
the relevant projection argument in [COLUMN_CLONING.md](../COLUMN_CLONING.md)
and compared the proof mechanism with
[SIDON_REPAIR.md](../../feedback/SIDON_REPAIR.md) and Section 4 of the archived
75 proof. No circuit enumeration, SAT, exact search, or computer-driven case
elimination was used. This is machine review, not formal verification, human
certification, or a literature-novelty assessment.

**Verdict:** the complete mathematical argument passes review. I found no
consequential gap or necessary source correction. The claims concern arbitrary
binary XOR circuits on the stated coordinate inputs; the Sidon condition is a
hypothesis on the prescribed boundary, not on competing internal values.

## First occurrences and terminal-parent gates

Total coordinate parity makes every input odd. A gate first producing a
non-input odd target therefore has one odd and one computed even operand.
Its even operand cannot be zero, since then the odd parent would already have
the target value. Marking only the first occurrence of each distinct target
makes the identity G=m+H+E exact without requiring circuit normalization.

A terminal-parent target gate has an unordered pair {u,y} of distinct boundary
values and even label u+y. A Sidon boundary permits at most one such pair for
each label. That pair cannot support two marked gates in opposite directions:
whichever endpoint is produced first must already exist as the other gate's
parent. Equivalently, orienting the pair both ways contradicts chronological
first occurrence. This argument also covers an input endpoint and recomputed
occurrences of boundary values. Charging distinct labels to E gives at most E
terminal-parent marks even if the circuit contains repeated even values.

Every other odd parent is a nonterminal odd value whose first production is
one of the H unmarked odd gates. There are consequently at most H such values.
Using values, rather than physical occurrences, for the graph vertices is
legitimate and only reduces the vertex count. An ordered choice of odd and
even values has a unique sum, so the graph is simple. Every edge has a distinct
target label because precisely one marked gate is retained for each target.

## Four-cycle and multiplicity counts

In the Sidon case a four-cycle gives four distinct edge labels whose XOR is
zero. It is therefore impossible. The pair-of-right-neighbors count is

    sum_h binom(deg(h),2) <= binom(E,2).

Padding by isolated vertices to the physical budgets H and E is harmless.
For H>0, Cauchy gives b^2 <= H*b + H*E*(E-1), and solving this quadratic gives
(2). Swapping the graph sides gives (3). For H=0, b=0 directly; E=0 is
incompatible with m>=1 in this input model. No use is made of an independent
even basis, a bound on EE gates, or a relation between an internal helper and
other helpers.

For the multiplicity extension, a fixed nonzero even label has at most alpha
boundary pairs and hence at most alpha terminal-parent marks. The direction
argument still limits each pair to one mark. For two distinct even vertices
e_1,e_2, each common helper h gives the target pair
{h+e_1,h+e_2}, of fixed nonzero difference e_1+e_2. Different common helpers
cannot give the same unordered pair: that would repeat a globally unique
marked target label on distinct edges. Thus at most nu helpers are common
neighbors. This proves the claimed capacity count, even though four-cycles
are now permitted, and yields (7).

The definition alpha=nu(A_0) counts input-input pairs as well as pairs touching
T; this may weaken the bound but does not invalidate it. Since m>=1 and every
target is a non-input value, A_0 contains distinct values and alpha>=1. When
T has one member, nu=0 is the correct convention and (7) remains valid. The
separate one-target qualification in the Sidon specialization is appropriate.

## Constants and asymptotic interpretation

For nonnegative integer resources, the quadratic root gives

    b <= H + sqrt(nu)*E*sqrt(H).

With nu=1 and s=E+H, maximizing (s-H)*sqrt(H) gives the stated maximum
2*s^(3/2)/(3*sqrt(3)) at H=s/3. Squaring only the positive part of m-s makes
(5) genuinely equivalent to (4), including the case m<=s. Since at least one
even gate is necessary, s>=1; the subsequent relaxation to m<=2*s^(3/2) and
integer ceiling in (6) are sound. Formula (8) follows from
alpha*E+H<=alpha*s and the same maximization.

For uniformly bounded alpha and nu, (8) implies overhead Omega(m^(2/3)).
This is an asymptotic statement for fixed multiplicity bounds, as the wording
states. Using both quadratic inequalities could improve constants, but the
note expressly claims only the exponent, so this is not an omitted proof
obligation.

## Ordinary inputs and the affine-incidence family

Over F_q, two distinct points lie on at most one nonvertical line, by solving
the two incidence equations (and directly treating equal x coordinates).
The graph is simple, has q^2 vertices on each side, degree q at every vertex,
and exactly q^3 edges. These symbolic facts hold for every prime q, including
q=2, and ensure that every coordinate block is active.

Each target has one complete private three-coordinate point block and one
complete private two-coordinate line block. Targets are distinct and have
weight five. The source's five cases establish the stronger assertion that
ordinary inputs together with targets form a Sidon boundary:

- Four distinct inputs cannot sum to zero.
- A target cannot equal three inputs because its weight is five.
- Two distinct targets differ in at least four coordinates, so cannot sum
  to two distinct inputs.
- Three targets leave at least one entire point block: the total number of
  point-block occurrences is odd, so their block coefficients cannot all
  cancel. The resulting vector has at least three nonzero coordinates and
  cannot be a coordinate input.
- Four distinct targets sum to zero exactly when their four incidence edges
  have even degree at every vertex. A nonempty simple bipartite even graph
  with four edges is a four-cycle, excluded above.

The case distinction is a symbolic proof by possible relation type, not a
finite verification or a listing of target subsets.

## Exact circuit cost and sharpness

Before block substitution, each incidence target is a distinct pair of
independent coordinate inputs. Every target needs its own gate, and a gate
per pair attains the bound, so the reduced cost is exactly m. Replacing each
point coordinate by three inputs and each line coordinate by two inputs adds
exactly 2*q^2+q^2 gates by column cloning.

For completeness, the unrestricted lower half of that cloning claim follows
by retaining one coordinate in each block and projecting away the others.
At every projection an incident required target still contains both the
coordinate being removed and its retained block representative. It remains a
non-input target, so the first current gate having coefficient one in the
removed coordinate becomes a copy and can be deleted. These successive
projections delete 3*q^2 distinct current gates and leave the reduced pair
problem. This applies to arbitrary rewiring and cancellation, not only to
the displayed construction.

In the construction each point block contributes one even pair and one odd
triple helper; each line block contributes one even pair; each incidence
contributes one marked odd target. Therefore H=q^2 and E=2*q^2. The even pairs
have disjoint supports across their blocks, so they are independent. There
are no EE gates, and all 2*q^2 even gates increase the even rank. Hence the
stated d=mu=0 and even rank 2*q^2 are also valid for this construction.

Equation (9) proves exact total complexity m+3*m^(2/3) along the unbounded
sequence m=q^3. Together with (6), it establishes sharpness of the universal
overhead exponent for the stated boundary class. It does not establish a
sharp lower-bound constant, or constrain the even rank of every optimum.

## Relation to the existing Sidon argument

The old auxiliary-count proof puts inputs and auxiliary values into one
graph, with vertex budget R=d+A, and forbids four-cycles using target Sidon
relations. The new proof keeps the same extremal graph mechanism but uses
parity to make a bipartite graph of computed odd helpers and computed even
suppliers. The stronger input-and-target boundary hypothesis separately
controls terminal-parent production, removing the free input count from the
resource inequality. Thus it is correctly described as a refinement and
tradeoff, not a new Sidon technique or an unconditional replacement for the
old target-only statement.

The cited Section 4 of the 75 proof already uses uniqueness of boundary-pair
differences. That connection is accurate. The new note proves no new
MixColumns-specific boundary fact and claims no improvement of 75<=L<=88.
Its unrestricted conclusion and its limits are stated consistently.
