# Independent review: common-anchor graph costs and the flag barrier

2026-11-14. Independent symbolic review of
[COMMON_ANCHOR_GRAPH.md](../COMMON_ANCHOR_GRAPH.md), checked against the
[odd-component theorem](../ODD_COMPONENT_DEFECT.md) and
[chronological flag account](../FLAG_RELATION_TRANSPORT.md). No graph search,
vertex-cover optimization, order enumeration, SAT, or circuit search was used.
This is machine review, not formal verification, human certification, or a
literature-novelty assessment.

**Verdict:** the exact cost, parity-resource consequences, relation-space
classification, and subset-optimized flag barrier pass review. The source
correctly attributes the exact cost theorem instead of presenting it as new.

## Primary-source attribution

I inspected the linked January 2011 manuscript by Boyar, Matthews, and Peralta,
[Logic Minimization Techniques with Applications to Cryptology](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=908384).
Section 3.1.1, Lemma 1, explicitly gives the cover/program equivalence for
forms z+x_i+x_j and an algorithm extracting a cover from a program. Section
3.1.2 restates the optimum as the number of forms plus the minimum cover size.
The manuscript's model permits linear straight-line programs over arbitrary
fields. Thus the binary exact-cost law in this note is already established
there. The present parity-partition derivation, resource deductions, and use
as a test of the flag invariant are clearly distinguished from that provenance;
no novelty claim is made for them either.

## Unrestricted lower bound and attainment

Total coordinate parity makes every input odd and leaves no initially even
coordinate subspace. The odd-component theorem therefore assigns every
arbitrary competing circuit a compatible input partition with even rank
r=n-c. Its physical even gate count is at least r, even when suppliers are
dependent, values are recomputed, or EE gates occur.

Let C_0 be the graph vertices in the anchor's partition block. If an edge
has no endpoint in C_0, its endpoints must occupy the same other block;
otherwise its target has odd support in three different parts. Selecting all
of C_0 and all but one vertex from each other part covers every edge. Its size
is exactly |C_0|+sum_B(|B|-1)=r. Hence every circuit has r>=tau(F), and the m
distinct non-input odd outputs require m separate odd gate occurrences.
This proves G>=m+tau(F) without fixing any helper basis or circuit form.

A minimum cover gives tau(F) actual anchor-pair helpers and one gate per edge
output. Those helpers are independent, because each includes its own vertex
coordinate. The associated anchor block and singleton remaining parts have
rank tau(F). Thus total complexity, minimum even gate count, and minimum
compatible-partition rank all have the claimed exact values. Isolated vertices
and the zero-edge case cause no exception. The simple loop-free hypothesis
prevents repeated edge outputs or input-valued loop targets.

## Consequences for every optimum

Substitution into G=m+H+r+mu+d is valid because H counts odd occurrences beyond
one first production per target. All extra terms are nonnegative. Equality at
m+tau(F) therefore forces H=mu=d=0 and r=tau(F), with exactly tau(F) independent
even gates and m odd gates. Every optimal compatible partition extracts a
minimum vertex cover by the same rule.

This is not a uniqueness theorem for helper values. It also does not imply
that all optimal formulas avoid algebraic cancellation. For a triangle, the
five-gate circuit

    p=x_1+x_2;   t_12=a+p;
    q=x_2+x_3;   t_23=a+q;   t_13=t_12+q

is optimal, has zero parity defect, uses no anchor-pair helper, and cancels
x_2 at the last gate. The source correctly avoids requiring its displayed
cover-star shape of every optimum.

## Initial closure of a selected edge set

For a bipartite selected graph with v active vertices and c nonempty components,
the vertex incidence part of its target span is the even-coordinate space on
each component. The anchor coefficient is determined by the sum of parities
on one chosen side of each bipartition. This gives dim W=v-c.

A coordinate singleton cannot satisfy these constraints. A coordinate pair
belongs to W exactly when its two vertices are on the same side of the same
component. Pairs involving the anchor or distinct components do not qualify.
The within-side even spaces have total dimension v-2c, giving dim(W/R)=c.
Each target remains outside R and has length three, while every shorter
W-value is in R by definition. The escape minimum is therefore exactly three.

If any selected component has an odd cycle, summing its targets gives the
anchor a. Every selected edge then gives the pair t_uv+a=x_u+x_v in W. These
short generators span all target values, so R=W. This is a global collapse:
one odd cycle saturates the closure even for other selected-edge components.
The source includes this point and does not incorrectly add a separate
bipartite deficiency after the anchor enters the span.

## Exact flag minima and arbitrary subset selection

For a wholly bipartite graph, initial q at an output prefix equals its number
of active components. Only an edge starting a new active component increases
q. Every final active component needs such a start; processing a spanning tree
and then remaining edges within each component attains exactly one start per
component. Thus the order minimum of Phi is c.

For a nonbipartite graph, start with one odd cycle in cyclic order. The first
edge increases q to one, subsequent path edges preserve it, and closing the
cycle makes q zero permanently. Every ordering has at least the initial
increase because its first target is a non-input triple. Thus the minimum is
one. In every order the first cut has escape length three, so the minimum
escape term Delta_* is also three and adds no correction.

For a connected original graph with m edges, a selected nonempty p-edge
subgraph has at most m-p+1 active components: each deleted edge increases
component count by at most one, and ignoring isolated vertices only weakens
the bound. A bipartite selection's certificate p+c is therefore at most m+1;
a nonbipartite selection's certificate p+1 is also at most m+1. The full
selection attains m+1, whether the original graph is bipartite or not.
Consequently the claimed maximum over selections of their order-minimized,
distance-augmented flag certificates is exactly m+1.

This conclusion is specifically about the stated target-only certificate.
It does not bound all lower-bound methods, the known exact cost m+tau(F),
or potential stronger accounting of neutral auxiliary work. Adding omitted
required outputs again would double-count gates that are permitted to advance
the selected flag. The source makes that limitation explicit.

## Path example and invertible embedding

For an m-edge path, alternating vertices give a cover of size ceil(m/2), and
ceil(m/2) disjoint edges give the matching lower bound. The exact unrestricted
cost is therefore m+ceil(m/2). The targets are independent since the path's
edge incidence vectors are independent. In their natural order, within-side
pair generators x_j+x_(j+2) form two disjoint path chains and have rank i-1
on the i-edge prefix. Thus every prefix has q_i=1 and the flag bound is m+1.
The gap grows even though every target has coordinate weight three.

Retaining a and x_1 as identity outputs and replacing x_(i+1) by t_i gives a
square all-odd invertible map: x_(i+1)=t_i+a+x_i recovers inputs successively.
These identity outputs cost no gates. The barrier therefore persists under
this embedding and is not caused by singularity or a long individual target.

The note draws the warranted lesson: relation accessibility and physically
supplied even directions measure different work. It claims no new numerical
MixColumns bound and no restriction on competing implementations.
