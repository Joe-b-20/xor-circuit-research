# Clean supply and coset occupancy cannot be maximized separately

2026-11-13, continuing reviewed commit `4f4d918`. Hand proofs with independent machine
reviews, not formal verification or human certification. The joint 0/1 interval under
its stated hypothesis remains 21 to 22. **Unrestricted MixColumns remains 75 to 88.**

**Subsequent progress:** [the frontier pass](../frontier/README.md) closes the rank-one branch and proves that rank-two suppliers cannot use an even coset to complete the diagonal span. The remaining-pattern discussion below records this earlier pass.

## The new coupled bound

[Theorem T](SUPPLY.md) proves that a ten-gate producer with four available values in one
nonzero clean-diagonal coset has clean-diagonal rank at most one. Equivalently, two
independent clean diagonals force every nonzero coset to contain at most three available
values. Both resources are counted in the same physical circuit, including its inputs
and free values. Neither a universal rank-one cap nor a universal three-value coset cap
is asserted.

For an even-own-parity coset, tight counting forces three independent entry labels and
no repeated ordinary projection except at entries. Equal free displacements in two
different projection fibres would require two disjoint subsets of independent labels
to have the same nonzero sum. That is impossible.

For an odd-own-parity coset, the small number of remaining even gates limits available
three-value XOR relations. In the tight boundary case, two clean directions would
require four equations around an affine plane. Their sum is zero, so they cannot all
be gate equations of an acyclic circuit: physical gate equations are independent by
their latest-node pivots. This dependence supplies the cost obstruction that a count
of individually available sums would miss.

The surviving ten-producer/eleven-consumer patterns are now:

* clean rank one, with four nonclean labels in one coset and one clean label;
* clean rank two, with two or three nonclean labels in one coset and two independent
  actual clean suppliers.

These are necessary patterns, not constructed 21-gate circuits. The other split,
eleven producer-side gates and ten consumer-bearing gates, still asks for an augmented
supplier with three independent diagonals in eleven gates.

## A general relation-rank framework

[RELATIONS](RELATIONS.md) turns the physical-gate observation into a general theorem.
Use odd values as graph vertices and colour an edge by the physical even value equal
to its endpoint sum. Let partial be the binary incidence map, chi record edge-colour
parities, and Z span the formal even-only triple relations. The rank of all available
three-node equations is exactly

    number of odd vertices - number of graph components
      + dim(Z + chi(cycle space)).

The number of non-entry gates cannot exceed this rank. Cycles whose colours occur with
even multiplicities give genuine dependencies, even though each edge separately is a
valid XOR. The resulting bounds incorporate both coset populations and the rank of the
actual even values. In particular, with n ordinary inputs, entry count is at least
`number of graph components + even-value rank - n`.

## Two clean diagonals are possible, but do not complete the interface

[EXPORTS](EXPORTS.md) gives an event-free ten-gate producer that already supplies two
independent clean diagonals. Together with the existing lower bound for three diagonals,
this makes the maximum clean-diagonal rank at ten gates exactly two. It refutes a
rank-one shortcut and shows why the coupled theorem needs its coset hypothesis.

For this particular producer, every within-one-coset difference is in the span W of its
two clean diagonals. It therefore cannot supply the third independent clean direction
needed by a cheap consumer. Its joint optimum is exactly **22**, with an explicit
matching completion. This is a fixed-producer result, not the unrestricted joint optimum.

[SUPPLY_PROFILE](SUPPLY_PROFILE.md) states the general principle. For a fixed supplier,
let W span its actual clean values and let Delta_C span differences within one supplied
coset. If W is proper and `W+Delta_C` is proper for every nonzero coset, a consumer needs
at least two gates beyond the cost with the entire required clean space free. Entry
deletion proves this: at most one extra gate permits only one nonclean quotient direction.

## Feedback and the augmented-supplier reduction

The same note proves a chronological span lemma. If a consumer has so far read only
labels in W, all its signals have free-side parts in W. A cancellation of its ordinary
part can create a new physical supplier value, but cannot create the first independent
clean direction outside W. Such a direction must first be produced by an operation
whose two operands are already on the supplier side.

This closes an implicit step in the (11,10) joint reduction. A putative extra supplier
could have been a consumer-block exit; the lemma shows that it cannot supply the missing
independent direction that way. A viable (11,10) profile really yields an eleven-gate
source-only augmented supplier. The argument also makes the fixed-producer 22 result
valid with possible feedback, rather than assuming all additional suppliers were built
before the consumer.

## Judgment and next obligation

The strongest next question is whether the two remaining mixed supply patterns can be
realized at ten producer gates. The new relation-rank framework can account for several
populated cosets and for dependencies between valid pair sums. It should be used with
the actual entry labels and causal supply, not as another independent charge to add to
existing repair counts. The eleven-versus-twelve augmented supplier remains a separate
concrete target; its reduction is now explicit even in the presence of feedback.

## Reviews and direct checks

Independent reviews cover [the tradeoff](reviews/supply-review.md),
[relation rank](reviews/relations-review.md), [supplier profiles and causality](reviews/profile-review.md),
and [the two-diagonal construction and fixed-producer optimum](reviews/exports-review.md).

Run the two checks from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/tradeoff/check_exports.py
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/tradeoff/check_tradeoff.py
```

They directly verify the displayed ten-/22-gate constructions, two specified relation
graphs, and the specified producer's deficient supply profile. The [saved linear-algebra
results](check-results.json) show four affine-plane relations of rank three and seven
relations on three even directions of rank four. No search over circuits or computer-driven
case elimination was used. EXPORTS records a draft verifier's free-mask membership
bookkeeping; the saved verifier uses a direct predicate and evaluates only the stated
construction. Universal claims rest on the hand proofs.
