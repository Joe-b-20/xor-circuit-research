# Nonclean feedback directions have an entry-cost lower bound

2026-11-13. Hand proof combining chronological span with entry deletion. No circuit
search or enumeration. This concerns the rank of returned values, not the number of
exits or the size of a cancelled block.

## General theorem

Partition inputs into source coordinates and ordinary consumer coordinates `z`. Source
values actually read by consumer-bearing gates are entry labels. Let `U` span all these
labels, and let `D` be the span of the source parts of the required consumer outputs.
Let `L_D` be the minimum cost of those consumer outputs when every vector in `D` is free.
Count only gates with nonzero consumer part, and write their number as `K`.

Let `F` be the span of the values returned by all zero-consumer exits, each the sum of
two consumer-bearing values with equal nonzero consumer part.

**Theorem FX.**

    K >= L_D + dim((F+D)/D).                                (1)

More strongly, before any exit appears its value is in the span of earlier actual entry
labels. A return cannot create a new entry-space direction by itself.

The chronological statement follows by induction on consumer-bearing gates: their
source parts are combinations of the entry labels already read. It implies `F subset U`.
The outputs imply `D subset U`. Granting all actually read labels free, the nonzero
consumer gates form a valid consumer circuit. The [entry-deletion theorem](../compatibility/QUOTIENT.md)
gives

    K >= L_D + dim(U/D).

Since `F subset U`, inequality (1) follows. The proof permits arbitrary intermediate
cancellation and repeated use of feedback values. It does not presume that source
operations or returned values were all created before the consumer started.

## Consequences for the two-sheet problem

Here `L_D=10` and `D={v(b)+v(a): v even}`. If the consumer has `10+c` gates, the image of
all its exits modulo `D` has rank at most `c`. Thus ten consumer-bearing gates can return
only diagonal values. Eleven can return at most one independent nonclean direction.
These are statements about all returned values together, not a separate allowance for
each exit.

The four first-sheet rows `U_i=E_i(b)+s_i(a)` are independent modulo `D`. Applying
`rho(beta,alpha)=beta+alpha` sends them to the four triple masks `E_(i+1)`, which are
independent: their matrix `I+J`, with `J` all ones, squares to the identity over `F_2`.
A combination in `D` has residue zero, so only the empty combination can belong to `D`.

If `k` of these first-sheet row values are themselves produced as consumer-block exits,
their independent quotient directions belong to `F`, and therefore

    K >= 10+k.

In particular ten consumer gates cannot directly return a first-sheet row, eleven can
return at most one, and returning all four rows directly requires at least fourteen
consumer-bearing gates. A row can still have exit ancestors without being an exit
itself. These restrictions do not count those ancestor paths and do not settle the
unrestricted joint minimum.
