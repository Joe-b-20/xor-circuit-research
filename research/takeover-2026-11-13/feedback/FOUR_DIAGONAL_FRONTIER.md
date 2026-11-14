# Four diagonals close the four-entry feedback case

2026-11-13, continuing reviewed commit `4adbf01`. These are structural hand proofs
with independent machine reviews, not formal verification or human certification.
No circuit search, enumeration, or computer-driven case elimination was used.

Four first-sheet rows together with independent clean diagonals `c,d,e` and the extra
value `c+d` need at least **thirteen source gates**. One specified choice attains
thirteen. This closes the four-entry mixed eleven-gate consumer case at **22 total
gates**, even with feedback. A specified construction attains 22 with eleven gates
on each side. Any eleven-consumer candidate below 22 must now have five mixed entries
and physical clean rank at most two on the source side. The five-entry class and
larger consumer budgets remain open. Unrestricted MixColumns remains **75 to 88**;
the block-monotone lower bound remains **85**.

## Why another physical value forces another gate

The [four-diagonal theorem](FOUR_DIAGONALS.md) requests a clean triangle `c,d,c+d`
and an independent fourth value `e`. Three independent diagonals alone have minimum
twelve. The fourth value adds no rank; its cost comes from how physical gates must
connect the requested values.

At a hypothetical twelve gates, first occurrences of ordinary masks and entry counts
leave only a few populations of odd helpers and even values. Formal gate relations
and pair uniqueness exclude all but one tight population. There, the residue graph
forces seven odd-pair equations and the clean triangle equation. The independent
fourth diagonal is absent from them, so it must use the sole even entry and have no
readers. The remaining three entry labels have rank at most two: matching ordinary
masks either makes two labels equal or makes their sum zero. The four required rows
need three independent free directions, and the isolated fourth entry cannot supply
the missing direction. This proves the contradiction.

An entry can therefore be forced to spend its direction on a terminal export. Counting
all entry labels together would miss that the row outputs cannot use it. The proof
combines physical pair relations, ordinary first occurrences, and reachability of
free information; it does not treat virtual span as free supply.

## Consequences with arbitrary feedback

For a [four-entry mixed basis](FOUR_ENTRY_CLOSURE.md), write the clean labels `c,d`
and nonclean labels `n,m`. The sum `e=n+m` completes a basis of the clean diagonal.
Replay the source chronologically, retaining `c+d` and `n+m` for at most two extra
XORs. Every exit splits between the fixed groups `{c,d}` and `{n,m}`, so the replay
preserves all source values. It contains the four required diagonals and hence needs
thirteen gates. The original source therefore needs at least eleven; an eleven-gate
consumer gives total at least 22.

The same note resolves a scope gap in the preceding four-entry reduction. The local
entry/trace theorem assumes every counted gate lies in a consumer target cone.
A global consumer-bearing gate may instead exist only to supply a source exit.
Cut at zero-consumer-part operands before defining those cones. If only ten of the
eleven gates remain, their entries are clean, and the sole outside gate can introduce
at most one distinct nonclean label. A separate chronological replay proves source
cost at least eleven for that class. If all eleven remain, the interface theorem
applies and gives four or five mixed entries; the four-entry pattern is now excluded
below 22. The older proof has been corrected to state its basis-pattern hypothesis
explicitly. No unproved trimming assumption is retained.

A [rank-four supply theorem](RANK_FOUR_SUPPLY.md) sharpens the remaining case: whenever
actual entry labels span four dimensions containing the diagonal and three independent
clean diagonals are already physical source values, the source needs at least eleven
gates. Select an entry basis chronologically and pair it in two groups. Replay adds
at most two pair sums. If either sum was an original physical value, its later copy
can be bypassed, leaving an impossible eleven-gate augmented supplier. Otherwise
pairing by clean/nonclean quotient class forces either a clean triangle plus an
independent fourth value, or five distinct diagonals, within twelve replay gates.
Both are impossible. Thus a candidate below 22 with eleven consumer gates has source
physical clean rank at most two, even though its entry span contains rank-three `D`.

## The remaining question

A candidate of total at most 21 with exactly eleven consumer-bearing gates must have:

- Five actual entry occurrences spanning four dimensions, with one nonclean quotient
  direction over the rank-three clean diagonal.
- Every consumer-bearing gate in the target cones after cutting zero-part source ports.
- Original physical clean diagonals spanning at most two dimensions.
- The five-entry trace/label restrictions from [the interface theorem](../compatibility/QUOTIENT.md),
  and the unique-pair and return restrictions from [collision accounting](ENTRY_RETURN_RIGIDITY.md).

These are necessary conditions, not evidence that a smaller circuit exists. A useful
next direction is to compare the five entries' unique label relation with their trace
relation, and ask when a replay sum must already be paid for later in the source.
Another is to derive a consumer collision forced by returning a missing clean direction.
Either route must respect causal supply: a virtual clean difference of nonclean values
is not automatically an original physical source value. Larger consumer budgets need
separate arguments. There is no claim that the full joint minimum is 22 or that 88 is
optimal for MixColumns.

## Review and specified checks

The source proof received [one independent review](reviews/four-diagonals-review.md)
and [a second independent review](reviews/four-diagonals-second-review.md).
Reviews also cover [feedback consequences and the cone correction](reviews/four-diagonal-consequences-review.md)
and [rank-four physical supply](reviews/rank-four-supply-review.md). The primary agent
checked the proofs, especially the undirected odd-entry matching, the isolated export,
and the chronological replay credits.

The [direct checker](check_four_diagonals.py) evaluates only two specified constructions:
a thirteen-gate source supplying one required diagonal pattern, and a 22-gate joint
circuit with eleven source and eleven consumer gates. The [saved results](four-diagonal-check.json)
confirm their outputs, entry ranks, live gates, and absence of whole-block cancellation.
These calculations establish the constructions, not the universal lower bounds.
