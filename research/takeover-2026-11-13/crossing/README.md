# The ten-gate producer branch is closed

2026-11-13, continuing reviewed commit `a7ff345`. These are hand proofs with independent
machine review, not formal verification or human certification. No circuit search was
used. **Unrestricted MixColumns remains 75 to 88.**

## What is now proved

[Theorem C and Corollary J10](ODD_CLOSURE.md) close the entire ten-gate producer branch.
A ten-gate first-sheet computation cannot support an eleven-gate second-sheet consumer.
Under the standard no-feedback hypothesis on the first-sheet target ancestors, the
joint cost is at least **22 whenever the first-sheet ancestor cone has ten gates**.
The bound is attained in that class by the existing explicit construction. It also
holds when an additional supplier could arise from cancelling the consumer block.

The general joint interval remains **21 to 22**. A hypothetical 21-gate solution must
now place eleven gates inside the first-sheet ancestor cone, already supplying three
independent clean diagonals, and use ten consumer-bearing gates. There is no remaining
ten-gate core plus a separate diagonal export route.

## Why the last mixed interface fails

The previous pass excluded clean rank at most one and confined the even intermediates
of a rank-two producer. The remaining question was whether odd intermediates could
supply the missing diagonal through a virtual difference.

The new [normal form](NORMAL_FORM.md) first proves that every ten-gate producer of
clean rank two has exactly two odd helpers, four independent physical even values,
and four entries. Two entries act on even nodes and two on odd nodes, with one odd
entry in each of the two own classes. The projected odd graph consists of two trees;
each lifts to a five-node tree when its entry edge is restored.

The key invariant is the nonzero sum of the four named residues in either own class.
It forces enough separate graph components that three or more odd helpers are
impossible. With only one helper, repeated pair representations share the same formal
relation, leaving too few independent equations. Exactly two helpers remain.

If an odd diagonal coset crossed the two own classes, the two clean even values could
together have at most one pair representation. The two nonclean values would then
need three and two representations to supply the six required non-entry equations.
Those representations necessarily contain an alternating four-cycle. Its equations
sum to zero, so they cannot all be executed independently. The crossing is impossible.

Consequently, at clean rank two, **every difference between available values in one
diagonal coset lies in the clean span already available**. One extra XOR cannot reveal
a third independent clean direction. This is a restriction on the whole supplied set,
not a count of isolated labels or a charge assigned to an uncomputed difference.

## Additional structure and the remaining augmented problem

For a clean own plane supported on three coordinates, the [causal-origin note](THREE_COORDINATES.md)
shows that both even directions must first arise in the class with three ordinary
inputs. The other class has a single ordinary input and cannot originate a new even
direction by itself.

The [restricted augmented bound](../frontier/AUGMENTED.md) now covers **every independent
even diagonal basis**, rather than only cycle-pair bases. Without block cancellations
or extra mixed intermediates, the four rows and three diagonals require at least twelve
gates. A twelve-gate example attains this bound for one basis; no uniform attainment
for every prescribed basis is claimed.

[The auxiliary theorem](AUXILIARY.md) adds a causal restriction: if two chosen diagonals
are non-cycle masks and all diagonals feed rows, one extra mixed intermediate cannot
carry both to the rows. An event-free eleven-gate candidate with that basis would need
at least two mixed auxiliaries. A small partial circuit records why the same argument
does not exclude a single non-cycle diagonal.

The unresolved augmented minimum remains eleven or twelve. Any eleven-gate solution
must now use all eleven gates in the ancestor union of the four rows, so each of its
three independent diagonals must help compute a row. If it is event-free, it must
contain an additional mixed intermediate. These are necessary conditions, not a proof
that eleven is impossible.

The next strongest direction is to account for that mixed intermediate's causal uses
inside the row cone. The required seven values are independent, so one extra mixed
value can mediate at most one physical relation between two of them. A useful argument
must combine this limitation with the pure-own work and allow cancellations explicitly
where they are not excluded. Counting three diagonal outputs as external overhead is
no longer the relevant case.

## Review and direct verification

Independent reviews cover [the normal form](reviews/normal-form-review.md),
[the supplier closure and joint consequence](reviews/closure-review.md), and
[the arbitrary-basis restricted augmented bound](reviews/augmented-basis-review.md), and
[the one-auxiliary obstruction](reviews/auxiliary-review.md).

Run the new direct check from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/crossing/check_normal_form.py
```

It evaluates the already specified two-diagonal ten-gate producer. The [saved results](check-results.json)
confirm its four-component non-entry forest, two five-node class trees, and even/odd
entry-label structure. It also checks the six-gate partial auxiliary control. These are
two fixed constructions, not a family of circuits.
All universal statements rest on the hand arguments.
