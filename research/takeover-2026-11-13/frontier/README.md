# A producer cannot trade away clean supply without paying elsewhere

2026-11-13, continuing reviewed commit `1fffbd0`. Hand proofs and independent machine
reviews, not formal verification or human certification. The general joint 0/1 interval
under its stated hypothesis remains **21 to 22**; unrestricted MixColumns remains
**75 to 88**. No optimality claim about 88 is made.

## One clean direction cannot support a cheap consumer

[Theorem R1](RANK_ONE.md) closes the entire rank-zero/rank-one supplier branch. A fixed
ten-gate first-sheet producer whose actual clean-diagonal span has rank at most one
requires at least twelve consumer-bearing gates. Under the standard no-feedback
hypothesis on the first-sheet target cones, its joint cost is at least 22, including
when one additional supplier is allowed to arise by cancelling the consumer block.

The new incompatibility is stronger than an occupancy count. Four available values
in one nonclean coset cannot, together with the producer's one clean direction, supply
all three required diagonal directions. In the even case, the tight budget forces
independent physical even values; named-pair identities then contradict the available
relations. In the odd case, either too few pair relations exist or the necessary ones
contain a dependent cycle. A list of individually valid XORs is not enough: an acyclic
circuit must be able to execute independent gate equations.

## Two clean directions confine every even intermediate

[Theorem E2](EVEN_ESCAPE.md) proves a further structural restriction. If a ten-gate
producer supplies two independent clean diagonals, the own-block projections of **all**
its physical even gates lie in those same two directions. Every difference inside an
even diagonal coset therefore lies in the clean span already available. An even coset
cannot provide the missing third direction virtually.

The proof first establishes a [tree normal form](PROJECTION_TREE.md) under the contrary
hypothesis of three independent even own directions. Exactly seven first occurrences
and three independent entries exhaust the ten gates. Projecting away the free block
leaves a spanning tree of a three-dimensional cube. Its physical even values are
independent; the physical non-entry equations form a forest, and adding the odd-entry
edges gives a tree.

[Preliminary rank-two constraints](RANK_TWO.md) exclude zero and three odd helpers.
With one helper, short-relation rigidity of the eight named inputs and outputs leaves
at most six non-entry relations where seven are needed. With two helpers, a value
having three pair representations forces any second multiply represented value into
an alternating four-cycle. That cycle makes the seven required equations dependent.
These arguments close all cases of the contrary rank-three-own hypothesis without
enumerating trees or circuits.

## A restricted diagonal interface has exact cost twelve

[AUGMENTED](AUGMENTED.md) proves that four rows plus any three cycle-pair diagonals need
exactly twelve gates in an event-free circuit with no extra mixed intermediates beyond
the seven requested mixed values. The proof forces three pure-own triple sums, which
require at least five pure gates. A recorded twelve-gate construction attains the bound.
Thus an eleven-gate event-free solution for these diagonals would need an additional
mixed intermediate. Arbitrary diagonal bases and unrestricted mixed intermediates or
cancellations remain outside this theorem.

## What remains and what is most promising

A hypothetical 21-gate joint computation has only these unresolved routes:

* A ten-gate first-sheet producer of clean rank exactly two, with two or three nonclean
  consumer labels in an **odd** diagonal coset. Completing the diagonal span requires
  two available odd nodes of the same residue whose own masks lie in different classes
  modulo the two clean directions. The ancestry restriction is proved; such a crossing
  has neither been constructed nor excluded.
* An eleven-gate source-only augmented producer supplying three independent diagonals,
  followed by a ten-gate consumer. The existing causal-span argument justifies this
  reduction even with a possible consumer-block exit. The augmented minimum remains
  eleven or twelve.

The strongest next step is to understand the first crossing: all even operations
preserve the two own classes, but free-label entries may still place nodes from those
classes in the same diagonal coset. A useful theorem must connect that freedom to the
entry cost or the four required outputs. The new confinement theorem supplies a reason
to study those classes, rather than treating coset occupancy and clean rank separately.
The augmented problem remains a second target; its restricted twelve-gate proof now
identifies the extra mixed intermediate as an essential resource in the event-free case.

The relation-rank method is also a general direction beyond this local map: dependencies
between usable identities constrain executable sharing. Neither the cube normal form
nor the named-set rigidity is claimed for arbitrary linear maps without its hypotheses.

## Review and direct verification

Independent reviews cover [rank one](reviews/rank-one-review.md),
[the preliminary rank-two reductions](reviews/rank-two-review.md),
[the tree normal form](reviews/projection-tree-review.md),
[the one-helper exclusion](reviews/even-escape-review.md),
[the final two-helper exclusion and confinement](reviews/two-helper-review.md), and
[the restricted twelve-gate interface](reviews/augmented-review.md).

Run the one new direct check from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/frontier/check_tree.py
```

It evaluates the already specified ten-gate control with three even own directions.
The [saved results](check-results.json) give an eight-vertex projected tree, a ten-vertex
physical forest with three components, and a ten-vertex tree after adding its two odd
entry edges. This is a consistency check on one construction. Universal statements
rest on the hand proofs. No SAT, circuit enumeration, exact least-gate search, or
computer-driven elimination was used.
