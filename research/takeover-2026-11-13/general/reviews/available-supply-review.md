# Independent review: available supply and ternary normal form

2026-11-14. Independent machine review of the complete
[AVAILABLE_SUPPLY.md](../AVAILABLE_SUPPLY.md). I reconstructed its metric,
constructions, chronological ledger, and both directions of the normal form.
No circuit search or enumeration was used. This is not formal verification
or a literature-novelty claim.

## Physical dictionary and exact update

The minimum is over subsets of the actual available dictionary. Dependence
among dictionary values causes no problem. Positive weights imply a minimum
has no cancellable zero-sum subcollection. Nonzero odd/even values have word
length at least one/two respectively, so an available value has exactly its
assigned weight.

A representation using the newly added value consists of that value plus
a representation of the remaining sum in the old dictionary. This proves
the exact update. If the value was already present, toggling it in an old
representation shows that the additional candidate cannot improve the old
minimum. Replacing a new value by its two parents increases weight by zero
for odd-plus-odd and by two for the other two parity types. Cancellations in
that replacement only reduce its weight. Thus the metric is unchanged in
the first case and decreases by zero or two in the others. The affected-set
formula follows directly from this dichotomy.

## Exact single-target cost and chronological intervals

At completion the designated target has word length equal to its parity
weight. Each paid operation lowers that fixed word length by at most two,
giving the lower bound on P. Pairing the odd terms of a minimum representation
and then combining actual even operands attains the formula. A zero or
duplicate intermediate can only make the construction shorter; the matching
lower bound still fixes its minimum resource count. All pair gates remain
physical binary gates and are omitted only from the named resource P.

For a new odd target the final gate is odd, yielding the stated H+d formula.
Precombining any chosen number of the even operands gives every split of
that resource. No claim about the first-produced target among a larger
specified set is inferred from this single-target construction.

The interval inequality uses the dictionary at the actual interval start.
Intervals between successive first productions are disjoint and may be
summed. Replacing their dictionaries by the initial one is not legitimate.
The cone argument remains valid with dependent boundary values: path parity
gives a representation using a subset of those actual values.

## Shared progress ledger

Every paid gate lowers each affected target's integer C by exactly one;
unpaid odd-plus-odd gates lower none. Telescoping each target from its initial
C to zero proves the ledger. A first-production gate necessarily affects
its own target, allowing exactly one unit to be subtracted for each of the
m target gates. Progress on other targets made by such an output gate is
correctly retained in the second sum.

The shared-triple example is checked directly: the common odd triple lowers
all m weight-five targets from C=2 to C=1, and their output gates finish them.
In the no-odd-helper construction, the m even combinations each perform one
of those reductions. This confirms unbounded preparation capacity and the
need to distinguish an exact ledger from a constant-capacity lower bound.

## Exact ternary normal form and its scope

The normal form assumes total parity on ordinary coordinate inputs and an
all-odd target set. In the forward simulation every binary even value has
a pair representation using already available odd ternary values. An
odd-plus-odd gate supplies that representation with no ternary gate. An
odd gate uses one ternary XOR. An even-plus-even gate with pairs a+b and
c+d uses the odd value a+b+c and the pair (a+b+c)+d, also costing at most
one ternary gate. Repeated operands simplify and preserve this upper bound.

Conversely, one ternary gate is one binary odd-plus-odd pair gate followed
by one odd gate. This proves equality of the optimized O+d resource with
L_3, and subtracting the number of required non-input odd targets gives
the H+d equality. The proof does not preserve total binary size, even rank,
cycle rank, or simultaneous attainment of separate minima. It is not stated
for a mixed-parity free dictionary.

The resulting lower bound L_2>=r_min+L_3 is valid, and its two illustrated
families attain the separate bounds jointly by their explicit constructions.
The three-input example correctly shows that identical word-length functions
can have different remaining binary costs: supplying one even pair can save
a physical gate while leaving every weighted word length unchanged.

The complete note passes review. Its unresolved pair-supply cost and its
absence of a new MixColumns numerical bound are stated accurately.
