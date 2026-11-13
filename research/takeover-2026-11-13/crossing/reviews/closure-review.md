# Independent review of the ten-gate supplier closure

2026-11-13. Machine proof review of [ODD_CLOSURE](../ODD_CLOSURE.md). No circuit search or family checks were run.

## Crossing and relation rank

In the rank-two normal form there are eight named odd nodes, exactly one at each odd residue, and two additional odd helpers. Thus an odd residue with a crossing must include a helper. If the helper residues differ, each enlarged residue has only its named node and helper. A crossing uses one of those two possible pairs, and its sum cannot be in the clean span \(W\), since its own part is outside \(W_b\). Only the other pair can be clean. If the helper residues agree, the one enlarged residue has three nodes. A crossing splits them between the two own classes, so at most one pair stays inside an own class. All other residues are singletons. This verifies the total capacity of one odd-pair relation for the two clean physical even values together.

There are two nonclean even values. Each gives at most three odd-pair equations by matching and named-pair uniqueness. If neither attains three, the total including clean pairs is at most five. If one attains three, the two-helper lemma gives the other at most two. In the case of two, an alternating four-cycle makes four of the available equations formally dependent. Hence the total count at most six has rank at most five. The four physical even values are independent, so even-only equations supply no further rank. Six non-entry equations are required and are independent by their latest-result pivots. This contradicts a crossing.

It follows that every odd same-residue difference belongs to \(W\). The even case follows from E2, which places all physical even own parts inside \(W_b\), and the free representative in an even coset has zero own part. A coset of odd free parity contains at most one available value, because only free values have that parity and a coset meets their space at most once. Thus Theorem C covers all cosets of \(D\).

## Fixed supply and joint cost

With clean rank two, the actual clean labels and the differences between all nonclean labels in one coset lie in \(W\). The span of clean labels together with any such nonclean labels intersects \(D\) only inside \(W\). An eleven-gate consumer permits at most one nonzero quotient direction, and its required labels span \(D\). This is impossible. The independent rank-one result covers rank zero and one, and the augmented lower bound rules out rank three for ten-gate producers. Hence every fixed ten-gate producer needs at least twelve consumer-bearing gates.

In the joint problem under no feedback to first-sheet targets, the ten-gate first-sheet cone provides just such a producer. If there is no additional zero-consumer gate, the fixed-supply lower bound applies even if the producer and consumer are interleaved, because granting the consumer every first-sheet node only enlarges its supply. Two or more additional zero-consumer gates give 22 by the ten-gate consumer minimum.

One additional zero-consumer gate at total at most 21 leaves exactly ten consumer-bearing gates. Every actual consumer entry is then clean by the entry-deletion bound. If the original clean rank is at most one, adding one value cannot reach rank three. If the original rank is two, a new clean value from two zero-consumer operands belongs to \(W\) by Theorem C. If the extra gate is an exit from two consumer-bearing operands, earlier actual clean entries all come from the original supplier and lie in \(W\). Their producer-side parts and those of all earlier consumer-bearing nodes remain in \(W\) by induction. The exit's producer-side value is therefore also in \(W\). The one extra gate cannot supply the missing direction in either case. This establishes J10.

The recorded 22-gate completion attains the bound in the exact first-cone-ten class. Its two additional supplier-side gates are outside the ancestor union of the original first-sheet outputs. Their downstream uses do not change that union.

## The remaining augmented core

A hypothetical 21-gate no-feedback joint circuit must have at least ten consumer-bearing gates and at least ten first-cone gates. J10 excludes exactly ten first-cone gates. Thus the first cone would have eleven gates, with no extra zero-consumer gate outside it, and the ten consumer-bearing gates would have to read three independent clean directions already available inside that cone.

For an eleven-gate circuit computing the four first-sheet rows and three independent clean diagonals, the row cone has at least ten gates. If it had exactly ten, at most one extra physical value could be supplied. At rank two Theorem C excludes enlargement by an appended gate. The same conclusion holds when that gate is interleaved with the ten cone gates, because at its time both operands come from the eventual cone's available set or the base values. It cannot be an ancestor of a cone gate, by definition of the ancestor union. At rank at most one one new value is insufficient by dimension. Hence an eleven-gate augmented supplier must have all eleven gates in the row ancestor union. This does not exclude that final case, and the unrestricted joint bound remains 21 to 22.
