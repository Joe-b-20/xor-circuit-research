# Five diagonal values rule out a tight ten-gate consumer

2026-11-13. Hand proofs by first occurrences and formal relation rank. No circuit search or finite-family checks. The resulting joint bound concerns circuits with exactly ten consumer-bearing gates.

## Five clean values need at least thirteen source gates

Use the first-sheet model with four ordinary coordinates \(b_i\), a disjoint free block \(a\), and the four required values \(U_c=(E_c,s_c)\), with own triple \(E_c\) and free adjacent pair \(s_c\). Let
\[
D=\{(v,v):v\text{ is even}\}
\]
be the three-dimensional clean diagonal.

**Lemma.** A circuit computing all four \(U_c\) and containing five distinct nonzero values of \(D\) needs at least thirteen gates, even with unrestricted cancellation.

Suppose at most twelve gates suffice. Bypass free, zero, and duplicate values and trim to the required values. The four own triples and the five distinct even own masks of the supplied diagonals give nine distinct non-input own masks. Each needs a first-occurrence gate. An entry, a gate reading a free operand, repeats the own mask of its other operand. The free parts of the four rows have rank three, so there must be at least three entries disjoint from the first occurrences. Thus the budget forces exactly twelve gates and three entries. The three entry labels span the even free space because the target row labels already span it. Hence every computed free part is even.

Let \(H\) be the set of physical gates with even own mask, \(O\) the odd nodes including the ordinary inputs, and \(V=\operatorname{span}H\). Write \(\rho(\beta,\alpha)=\beta+\alpha\) and \(r=\dim\rho(V)\). Any five distinct nonzero members of a three-dimensional binary space span it, since a plane contains just three nonzero values. Hence \(D\subseteq V\). The kernel of \(\rho\) on the even-free-part space is \(D\), so
\[
\dim V=3+r.
\]

The eight named odd values, the four ordinary inputs and the four rows, have distinct residues: the units and the four triples. Their only nonzero relation is the sum of all eight. Indeed the free part of a relation can vanish only if it selects none or all of the four adjacent pairs. In the latter case the four own triples sum to the full own parity, forcing all four inputs. In particular a nonzero value has at most one representation by an unordered pair of distinct named values.

Form the available odd-pair graph with vertex set \(O\), putting an edge between two odd nodes when their sum lies in \(H\). Let \(c\) be its component count, including isolates. The [formal relation-rank bound](../tradeoff/RELATIONS.md) gives
\[
9\le |O|-c+|H|-\dim V=13-c-r.
\]
For clarity, every non-entry gate yields a formal three-node equation, either one even and two odd nodes or three even nodes. Actual non-entry equations are independent by their latest-result pivots. Projection of the available equation span to the odd coordinates has rank \(|O|-c\), by graph incidence. Its kernel lies in the formal evaluation kernel on even nodes, of dimension \(|H|-\dim V\). This gives the bound, including any even-only equations.

Every edge preserves residue modulo \(\rho(V)\). The named residues occupy all \(2^{3-r}\) odd residue cosets, so \(c\ge2^{3-r}\). Together with \(c+r\le4\) this forces \(r\ge2\). At least two physical even values must therefore have nonzero residue. There are at least five clean even values, so there are at least seven even gates. The four odd row gates leave room for at most one additional odd gate.

- **No additional odd gate.** There are eight even gates, at most three nonclean. Every odd pair is named. Clean values have no named pair, since named residues are distinct. Each nonclean value has at most one named pair. The odd-pair equations therefore have rank at most three. Even-only equations have rank at most \(|H|-\dim V\le3\), giving at most six independent equations in total.
- **One additional odd gate.** There are seven even gates, exactly five clean and two nonclean. Across the clean values there is at most one pair, joining the lone helper to the unique named node of the same residue. Each nonclean value has at most one named pair and at most one pair involving the helper, since a fixed sum determines its other endpoint. The odd-pair equations have rank at most five. Even-only equations have rank at most \(|H|-\dim V\le2\), giving at most seven in total.

Both alternatives contradict the nine independent non-entry equations required at twelve gates. This proves the thirteen-gate lower bound. No attainment claim is needed.

## The joint consequence

For the unrestricted joint problem use ordinary source block \(b\), free block \(a\), and consumer block \(z\). The first-sheet rows are \(U_c\). The consumer rows have own triples on \(z\) and source parts spanning \(D\), with their sole all-four relation. Suppose exactly ten physical gates have nonzero \(z\) part. Regarding all other operands as free makes them a ten-gate local sheet. The [entry-deletion bound](../compatibility/QUOTIENT.md) forces every actual entry label into \(D\), and the labels span \(D\). These labels are values physically supplied by zero-\(z\) gates, since a nonzero diagonal is neither an ordinary source coordinate nor wholly free.

Assume the total size is at most 21, so at most eleven gates have zero \(z\) part. Apply [rank-three source replay](RANK_THREE.md). If every source gate can be replayed at its original one-gate cost or less, the result supplies \(U_c\) and three independent diagonal entry labels in at most eleven gates, contrary to [A12](../augmented/PROOF.md). The replay must therefore encounter the exceptional step. At that step three independent physical diagonal values \(u,v,w\) are available, and the exit has value \(u+v+w\). The replay supplies a pair sum, say \(u+v\), then the exit value. These are two new distinct nonzero diagonal masks, neither equal to the three basis values. The five values remain physically available in the complete source-only replay. Its size is at most twelve. This contradicts the five-value lemma.

**Corollary.** Every unrestricted joint circuit with exactly ten consumer-bearing gates has at least 22 total gates. The [specified 22-gate no-feedback circuit](../augmented/CONSEQUENCES.md) attains 22 in this class. The proof allows exits and feedback into the first-sheet cones. It does not exclude a circuit with eleven or more consumer-bearing gates at smaller total cost.

The explicit ternary-exit consumer of [the ternary consumer](TERNARY_CONSUMER.md) remains compatible with this result. It demonstrates that ten consumer-bearing gates can generate a hard exit from a supplied basis. The obstruction here is the cost of preserving the source rows and physical diagonal values in a tight joint budget, not an impossibility of the local exit.
