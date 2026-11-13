# Mirror exits in the unrestricted joint problem

2026-11-13. Hand deductions from the transposition model and the exact no-feedback bound. No circuit search or finite-family checks. The unrestricted joint minimum is not determined here.

## Mirror conventions

Write \(w,w'\) for the two groups of four mirror inputs and \((\omega,\sigma)\) for a mirror value. The eight required values are
\[
A_i=(E_i,p_i),\qquad B_i=(0,E_i),
\]
where \(p_i=e_{i-1}+e_i\) on the second group. The mirror also designates \(\tau\) export signals whose span contains the even diagonal
\[
D=\{(v,v):v\text{ even}\}.
\]
The primal gate budget is \(|T|+\tau\), by the [free-side transposition principle](../../structure-2026-11-11/tenth-gate/PROOF.md) and [the joint mirror description](../../structure-2026-11-11/joint01/REPORT.md). For the reverse-transposition argument we prune dead gates outside all designated cones and keep the physical wiring of the remaining gates. Denote by \(m\) the number of gates with \(\omega\ne0\), and by \(n_0\) the number with \(\omega=0\).

An **exit** is a zero-\(\omega\) gate reading a nonzero-\(\omega\) operand. Its two operands then have the same nonzero first part. An **entry** reads a zero-\(\omega\) operand and has nonzero first part. Entries and exports are different occurrences and need not count the same signals.

## A mirror exit must feed a second-group target

If no exit lies in the ancestor cones of the four \(B_i\), then
\[
|T|+\tau\ge22.
\]

To see this, reverse-transpose the mirror with eight target terminal uses and \(\tau\) export terminal uses. For each physical signal, add one contribution for every reader occurrence and one independent variable for every terminal use. Then substitute free \(a\)-block forms for the export terminal variables so that the resulting free part of the primal matrix is the desired one. This is possible because the adjoints of the \(a\) coordinates have exactly the diagonal span \(D\), contained in the export span. The input variables for the \(A_i\) terminals are the ordinary primal \(b\) inputs, and the \(B_i\) terminals are the \(b'\) inputs.

A node's reverse adjoint is computed from its readers' adjoints and terminal variables reachable forward from that node. The same property holds for every partial XOR accumulated at it. A forward path from a first-group input \(w_i\) to a \(B_j\) would have to pass from a nonzero-\(\omega\) node to a zero-\(\omega\) node, giving an exit in the \(B_j\) cone. Thus no such path exists. The reverse output at \(w_i\), and all gates used to compute it, avoid the \(b'\) terminal variables. After substituting the \(a\)-only forms, this is precisely the no-feedback hypothesis of [J22](../augmented/CONSEQUENCES.md).

For completeness, after trimming the mirror every node has at least one reader or terminal use, and each of its eight ordinary inputs is used because the required matrix has no zero input column. A literal reverse accumulation uses
\[
(2|T|+8+\tau)-(|T|+8)=|T|+\tau
\]
gates. Retain the literal reverse wiring, or bypass only a free result or a copy through its own operand. There is no need to redirect a repeated mask to an unrelated wire, which could change the ancestor cones. The literal reverse circuit has the required absence of \(b'\) from the first output cones, so J22 gives the asserted mirror lower bound. This argument only needs exits to be absent from the \(B\) cones; an exit used exclusively for an export does not obstruct it.

## Three exports require a small, exit-dependent second group

Assume a reduced mirror with \(\tau=3\) and \(|T|+\tau\le21\). The exports then form a basis of \(D\), so they are actual diagonal signals. The \(m\) nonzero-\(\omega\) gates form a circuit with the whole second group declared free. It contains the four \(A_i\) and all three diagonal exports. Reflecting the coordinate indices on both groups changes the previous-pair convention \(p_i\) to the next-pair convention of [A12](../augmented/PROOF.md) and preserves the diagonal. Thus \(m\ge12\).

The actual entry labels of this circuit must span the even subspace of the second group, since that is the span of the required free parts. If all entry labels were even, at least three distinct nonzero even labels would be present. Each is a zero-\(\omega\) gate rather than a second-group coordinate input or a \(B_i\), since those are odd. Together with the four \(B_i\), this would give \(n_0\ge7\) and total at least \(12+7+3=22\).

Therefore some actual entry label is odd. The [free-label deletion bound](../compatibility/QUOTIENT.md) applied to the augmented targets gives \(m\ge13\): project onto the even subspace along that odd label, delete its entry, and apply A12. Consequently
\[
4\le n_0\le5.
\]
The labels span the full second-group space and there is at most one nonzero even zero-\(\omega\) gate. Thus at least three independent odd labels are needed if an even label occurs, and at least four if none occurs.

When \(n_0=4\), the only zero-\(\omega\) gates are the \(B_i\). Their ordinary inputs and all these outputs are odd, so none of the four can be made by adding two zero-\(\omega\) operands. Every \(B_i\) is a direct exit.

When \(n_0=5\), suppose none of the \(B_i\) is itself an exit. The fifth zero-\(\omega\) gate must then be even, since otherwise every zero-\(\omega\) operand is odd. Write \(h\) for its second part. Every \(B_i\) is \(h\) plus an earlier odd value. If \(h\) has weight two, repeatedly adding it leaves each odd value in the two-point set consisting of a unit and that unit plus \(h\); only two triple masks belong to those sets. So \(h\) must be the all-ones mask. It is necessarily an exit, because no earlier triple can precede it and two coordinate inputs cannot produce weight four. Then each \(B_i=h+w'_i\). This characterizes the sole no-direct-exit possibility in the five-gate zero-\(\omega\) part. It does not establish its compatibility with a thirteen-gate nonzero-\(\omega\) part.

These statements do not assume that the export span equals \(D\) when more than three exports are designated. The exit criterion above applies for every \(\tau\); the subsequent budget restrictions use \(\tau=3\) explicitly.
