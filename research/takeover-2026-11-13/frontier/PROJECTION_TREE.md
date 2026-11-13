# A tree normal form when three even own directions are present

2026-11-13. Hand proof; no enumeration of trees or circuits. This describes a constrained
class of optimal producers rather than proving that every ten-gate producer belongs to it.

Use the ten-gate first-sheet model from [RANK_ONE](RANK_ONE.md). All free entry labels are
even, there are three or four entries, and the four ordinary target projections are the
triples E_c. Suppose the span of the own-block projections of physical even gates has
dimension three.

## Seven first occurrences and three independent entries

At least three distinct nonzero even own masks and the four distinct target triples
must occur. Each requires a first-occurrence gate, while each entry repeats the own
mask of its earlier nonfree operand. Ten gates and at least three entries therefore
force exactly seven first occurrences and three entries. There are precisely three
distinct even own masks v_1,v_2,v_3, and they are independent. There is no other repeated
own projection except at an entry. The three free entry labels are an independent basis
of the even free-block space, since they span the required rank-three target labels.

Project the free block to zero and bypass the three entries. Exactly seven gates remain,
with distinct non-input own masks: the three v_i and four E_c. They form an ordinary
circuit for the four triples that also exposes the three independent even masks.

## The projected relations form a spanning tree of a cube

The odd own values are exactly the four coordinate units and four triples, the eight
points of the odd affine space. Join two of these points when their sum is one of the
three even basis masks v_i. The full possible graph is the three-dimensional cube:
translation by the independent v_i supplies its three edge directions.

Each of the seven projected gates selects one such edge. An even gate adds two odd
values, and an odd gate adds one even value to one odd value. No gate adds two physical
even values, because a sum of two independent basis masks is not one of the three
available even masks. A given relation can be executed only once by acyclicity and
distinctness of node values.

The selected edges have no cycle. Summing their endpoint differences around a cycle
gives zero; independence of v_1,v_2,v_3 would make every edge direction occur an even
number of times. The corresponding formal gate equations would then sum to zero.
Actual gate equations are independent by their latest-node pivots. This is a contradiction.

There are seven selected edges on eight vertices, so they form a spanning tree. This
is a structural conclusion, not a classification or enumeration of the cube's trees.
Of its seven edges, three create an even basis value and four create an odd target.

## Lifting the tree back to physical values

Let A be the number of odd non-output gates in the original producer. There are four
first-occurrence odd gate masks, namely the target triples, and all remaining odd
gates are entries. Hence the number of odd entries is A. This is a count equality,
not an identification of the nodes: a first-occurrence triple may be an intermediate,
followed by an entry that produces its designated output. There are e=6-A physical
even gates and 3-A even entries.

The three first even gates have independent own projections. Every other physical even
gate is an entry in one of those own-mask fibres. Within a fibre, subtracting an entry
value from its earlier nonfree operand gives its free label. Hence the physical even
values span the three first even values together with all 3-A even-entry labels.
The first three values have independent own projections, and the entry labels are
independent pure-free vectors. Therefore

    rank(physical even values) = 3+(3-A) = e.

In particular these physical even values are independent, even if some share an own
projection. There are no even-only three-value relations.

Build a graph on the original physical odd values, including ordinary inputs. Its seven
non-entry gates give seven edges, coloured by their physical even sum. The edges again
form a forest: a cycle would yield a zero sum of colours, independence of physical even
values would force every colour to occur evenly, and the gate equations would be
dependent. There are 8+A odd vertices, so this forest has exactly A+1 components.

Now add the A odd-entry edges, each joining an entry value to its earlier same-own-mask
operand. These edges connect every odd own-projection fibre into a tree. Contracting
those fibres gives the connected projected cube tree. Thus the graph after adding the
odd-entry edges is itself connected, with 8+A vertices and 7+A edges: it is a tree.

The two graphs have different roles. The seven-edge forest records physical non-entry
equations. The larger tree also includes the paid free displacements at odd entries.
Neither treats a virtual diagonal difference as an available gate.

## Relevance to the remaining rank-two producer

If the actual clean-diagonal span W has rank two, a physical even own mask outside
the corresponding two-dimensional own span makes its coset capable of supplying a
third virtual diagonal direction. Thus this particular even-coset route forces the
rank-three hypothesis above; see [RANK_TWO](RANK_TWO.md).

The normal form leaves only A=1,2,3 for a rank-two producer, since the no-odd-helper
case is excluded there. The same note excludes A=3 using connected components and the
unique named-pair sums. Therefore an even-coset escape, if it exists, has one or two
odd helpers, respectively five or four independent physical even values. The possible
odd-coset escape when the own even span stays rank two is a separate unresolved route.
[Theorem E2](EVEN_ESCAPE.md) subsequently excludes the one- and two-helper cases as well,
so a rank-two clean producer cannot have three independent even own directions.

The older ten-gate construction with three independent pure even masks is a control:
the rank-three hypothesis itself does not force an eleventh gate. Its two odd entries
and one even entry fit this normal form. The theorem constrains how such an optimal
producer can supply additional demands.
