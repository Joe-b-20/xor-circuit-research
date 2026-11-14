# An outside affine-plane entry allows at most one hard return

2026-11-13. Hand proof about physical wires and chronological source replay. No circuit search or finite-family checks. This closes the four-nonclean affine-plane profile below 22 and establishes the return condition used to exclude the all-nonclean profile.

## Setup

In the joint 0/1-sheet problem the source rows are \(U_c=(E_c(b),s_c(a))\), with block \(a\) free. The four consumer target own masks on block \(z\) are the four triples. Their source parts span the clean diagonal
\[
D=\{(v,v):v\text{ even}\}.
\]
Suppose there are eleven consumer-bearing gates, all in the relaxed target cones obtained by cutting zero-\(z\) operand ports, and five actual entries. Assume the entry labels are four distinct nonclean values in an affine plane \(Q=q+W\), where \(W\subset D\) is a two-dimensional subspace, and an outside label \(h\notin\operatorname{span}Q\). The outside label \(h\) may be clean or nonclean. These are the [four-term and all-nonclean profiles](FOUR_FIVE_FRONTIER.md).

The [five-entry trace theorem](../compatibility/QUOTIENT.md#five-entries-and-six-mirrored-gates) gives four odd plane traces and one even outside trace. The four plane labels have their four-term sum as their only relation, which makes the four plane traces precisely the odd ones. The trace matrix has rank four. Its one relation has support on the nonclean entries. Thus if \(h\) is clean, its trace is independent of the span of the four plane traces. If \(h\) is nonclean, its trace is the sum of the four independent plane traces. In either case the trace of \(h\) differs from the sum of any two plane traces.

## The fibre of the outside entry

Project the consumer to its own block and bypass its five entries. Exactly six gates remain for the four own triples. This is their minimum, so the six gates have distinct nonzero non-input masks. Every original own-mask fibre therefore has one root, an ordinary input or a non-entry gate. Its other nodes are attached by entries preserving their own masks, giving a rooted tree.

We use [the marked-wire and adjacent-entry rules](TIGHT_FIBRE_WIRES.md), which preserve individual wires of the physical consumer by expanding fanout into binary copy nodes. In the six-XOR transpose, after retaining the marks and suppressing the terminal trace ports, a marked entry wire carries its influence trace. Its ordinary derivative, the vector of output changes from perturbing that occurrence of the wire, is the original entry's own mask. If two entry edges are adjacent at an original node \(v\), an allowed order of adjoint accumulation exposes the sum of their traces on a mirror wire whose ordinary derivative is the own mask of \(v\). For sibling entries, add their two reader contributions first. For a parent-child pair, add the parent's reader and terminal contributions other than the child's trace first; their sum is the parent trace plus the child trace. In either order, the resulting partial-sum occurrence feeds the rest of \(v\)'s adjoint and has the same ordinary derivative as that full adjoint.

In a six-XOR triple-sum transpose the only nonzero even values are its two even helper values. Distinct even values cannot have equal nonzero ordinary derivatives on physical wires: their nonempty reader subsets lie in disjoint sets of odd triple gates, whose ordinary adjoints are independent by their terminal coordinates and gate order. The marked-wire rule and this separation concern the same literal transpose and its chosen accumulation orders.

Suppose two plane-entry edges are adjacent anywhere in the own fibre of the \(h\) entry. The sum of their two distinct odd traces is nonzero even. It is different from the even trace of \(h\), as shown above. The partial-sum wire and the \(h\)-entry marked wire have equal ordinary derivatives, since all nodes in that fibre have the same nonzero own mask. This contradicts separation of the two even values. Hence no two plane-entry edges are adjacent anywhere in the \(h\) fibre.

## The sole possible extra repair

The operands of an exit have the same own mask. Their difference is the sum of the labels along their unique fibre-tree path. Every label on that path was read before the exit, because the path is contained in the two root paths to its operands.

A path avoiding \(h\) consists entirely of plane labels. Its nonzero sum is either a sum of two of its plane labels, or a plane label itself. To see this, a path with two such edges has their pair sum, four edges sum to zero, and one or three edges give a plane label. In the last case the [entry-return collision theorem](ENTRY_RETURN_RIGIDITY.md) forbids a nonredundant return of an actual nonclean entry label. If the value was already supplied, replay reuses it.

A path containing \(h\) has at most one adjacent plane edge at each endpoint of the \(h\) edge and cannot extend through two consecutive plane edges. Each endpoint can have at most one plane-entry edge incident to it, by the nonadjacency just proved. Thus there is at most one path using \(h\) and two plane edges. With no plane edge or just one, the return is an already supplied label or a direct XOR of earlier labels. The sole remaining possibility uses a straddling plane pair \(q_i,q_j\), giving
\[
f=h+w,\qquad w=q_i+q_j\in W\setminus\{0\}.
\]
This identifies a candidate that may need an extra gate; it does not assert that \(f\) lacks another one-XOR representation using original source values.

Replay every exit with at most its original one gate, except that at the return \(f\), if needed, first supply \(w=q_i+q_j\) in one additional gate. These operands are already present by the path chronology. Keep the computed \(w\). If \(w\) is itself an original physical source value, including one supplied later, this extra gate carries no net cost: replay either reuses the earlier supplied \(w\) or bypasses its later original producer. No other extra masks are required. After the source replay, append the same consumer-bearing gates in their original order. They now read source values from the source-only replay, so the resulting joint circuit has no feedback into the source rows.

## Clean outside label: exclusion below 22

Assume \(h\in D\) and the original source has \(G_0\le10\) gates. If the replay is cost-preserving, the resulting no-feedback joint circuit has cost at most \(G_0+11\le21\), contrary to [J22](../augmented/CONSEQUENCES.md).

Otherwise the possible return \(f=h+w\) occurs as a physical source value, and replay supplies \(w\) with at most one extra gate. Thus it supplies the clean triangle \(h,w,f\). At the end all plane labels are physically available, so append one XOR of two plane labels to supply a nonzero \(\delta\in W\) different from \(w\). Such a pair exists because the four plane labels have all three nonzero differences in \(W\). Since \(h\notin\operatorname{span}Q\), \(\delta\) is independent of \(\langle h,w\rangle\). The four source rows, that triangle, and an independent fourth clean value are therefore supplied in at most \(G_0+2\le12\) source gates. This contradicts the [clean-triangle lower bound](FOUR_DIAGONALS.md). Hence this affine-plane profile cannot occur below 22.

## Nonclean outside label: necessary conditions below 22

When \(h\) is nonclean, \(f=h+w\) is also nonclean. The same replay gives a no-feedback circuit at cost at most \(G_0+12\), so J22 forces \(G_0\ge10\). In a circuit of total cost at most 21, \(G_0=10\), the straddling return \(f=h+w\) must occur and \(w\) cannot be an original physical source value. Otherwise the replay is cost-preserving and contradicts J22. The return must also lack a one-XOR representation from earlier available source values in the replay that copies or bypasses all other source gates, since such a representation would again avoid the only possible extra gate.

The resulting six available values in one nonzero diagonal coset are the five entry labels and the returned value \(f\). The [six-value coset bound](SIX_COSET_VALUES.md#the-all-nonclean-eleven-consumer-case) excludes supplying them alongside the four source rows within the eleven replay gates available here. The combined result closes this profile at exactly eleven consumer-bearing gates. Larger consumer budgets and the unrestricted joint minimum remain open.
