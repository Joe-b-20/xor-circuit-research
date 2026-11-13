# Independent review of the affine-completion bound

2026-11-13. Machine proof review of [AFFINE](../AFFINE.md), including its controls in [OVERLAP](../OVERLAP.md) and [MULTIWINDOW](../MULTIWINDOW.md). No circuit search or finite-family computation was used.

## Component, translation, and quotient

The connected components are on physical nonlocal operand nodes, with one edge for each selected gate having two such operands. A one-local-partner gate is assigned to the component of its nonlocal operand. Every vertex is incident to a selected gate by construction, including isolated vertices in the edge graph. A two-operand self-loop would give a zero selected value, which is excluded. Parallel physical edges cause no problem. Neither equal values at different vertices nor dependencies among the selected values invalidate the argument.

For a component with selected-value span \(K\), summing the selected values along a path expresses the difference of its endpoint operand values as an element of \(K\). Consequently all vertex values belong to the same coset \(a+K\), independent of the reference vertex \(a\). Every actual local partner belongs to that same coset because its sum with its nonlocal operand is a selected value. Geometrically feasible local completions \(E\) can include masks never available as physical operands. Taking all of them only enlarges the space \(\Delta\) used in the bound.

For \(E\ne\varnothing\), translating by a local anchor \(\ell_0\in E\) puts every vertex into \(K\). Differences of local completions also belong to \(K\). After quotienting by their span \(\Delta\), an assigned selected value is the image of a single translated vertex if it has a local partner, and the sum of two translated vertices otherwise. The selected values span \(K\), so their images span \(K/\Delta\). This proves \(\dim K-\dim\Delta\le h\). The proof makes no assumption about whether \(a\) belongs to \(K\).

Zero is a possible *geometric* local completion precisely when \(a\in K\). It is then a valid anchor, with \(\Delta=\operatorname{span}(E)\) and no need for a zero wire in the original circuit. A different anchor gives the same \(\Delta\). A selected gate with an actual zero local partner could not satisfy the hypotheses, since its result would equal its nonlocal operand. Keeping zero in the geometric set nevertheless makes the inequality valid under the stated definition of \(E\).

If there is no actual local-partner gate, the selected values are linear images of even incidence vectors on the \(h\) vertices. The even subspace has dimension \(h-1\), so \(\dim K\le h-1\), even if \(E\) happens to be nonempty. If \(E\) is empty this absence of local partners is automatic. This verifies AC0.

For AC+, append a one to each translated vertex. A one-local row acquires a one, and a two-nonlocal row acquires a zero. The span of the lifted rows projects onto \(K/\Delta\), and its kernel under that projection has dimension at most one. Hence the rank increases by at most one and is still bounded by the number of distinct physical vertices. The component counts can be added because their physical vertex sets are disjoint.

## Computing completion differences

For each window \(W\), a nonempty affine intersection of \(a+K\) with \(V_W\) is \(\ell_W+(K\cap V_W)\). Fix an eligible \(W_0\). Any difference to \(\ell_{W_0}\) decomposes into a within-window difference in \(K\cap V_W\) and the representative difference \(\ell_W+\ell_{W_0}\). Conversely the representative differences belong to \(\Delta\), and every within-window difference is the sum of two completions in that window and belongs to \(\Delta\). This proves the displayed formula (3). Changing representatives alters them only by the already included within-window directions. Changing the anchor preserves the span because every difference to the new anchor is the sum of two differences to the old anchor. Empty intersections contribute nothing.

The relation to the earlier projection theorem also holds. A projection annihilating all local completions annihilates their differences, hence factors through \(K/\Delta\). The rank of that projection on the selected span is at most the quotient dimension. If there are no completions, AC0 gives the appropriate estimate.

## Explicit controls

In the shared 156-gate MixColumns witness, take \(K=\operatorname{span}\{F_0,G_0\}\). These two rows are independent because their windows differ and both have full window support. The coset \(a+K\) consists of \(a,b,c,s_7(0)\), where \(a\) is nonlocal and the other three values are local. Indeed, \(a+F_0=b\), \(a+G_0=c\), and \(a+F_0+G_0=s_7(0)\). The differences of the last mask with \(b,c\) give \(G_0,F_0\), respectively. Thus \(\Delta=K\). AC gives zero. For both selected gates the local-partner bit is one, so their lifted quotient rows equal the same nonzero bit. AC+ gives one, equal to the hidden count of the specified witness. The calculation only uses the two selected row values and their shared operand.

In the hub family the \(r\) rows \(T_i=x+S_i\) are independent by their separate \(Z_i\) coordinates. A coset value contains \(y\), so a local completion cannot retain \(x\) and may contain at most one \(Z_i\) block. This requires a singleton index set in the expression \(a+\sum_{i\in I}T_i\) and is also sufficient. Its completions are precisely \(y+S_i\). Their differences to \(y+S_1\) have independent nonzero components on \(Z_i\) for \(i>1\), so \(\dim\Delta=r-1\). Each eligible window has zero within-window intersection with \(K\), since each contains only one completion. The quotient dimension is one. The incidence bit agrees with the one-dimensional quotient coordinate on the selected rows, so AC+ also gives exactly one. The family has one actual nonlocal operand.

## Exact event-free cost of the hub family

The \(3rm\) proof holds. Event-free support growth confines each live gate carrying a private block \(W_{ik}\) to the sole output \(A_{ik}\) that contains that block. No such gate can carry a different private block. After bypassing gates equal to a coordinate input, the first gate introducing each private coordinate on an output path reads that coordinate directly and has an operand free of all private blocks. These \(rm\) first gates are distinct. Setting every private coordinate to zero turns each into a wire. Restricting complete blocks creates no new whole-block cancellation, and bypassing equal values preserves the masks used by remaining gates. Thus the original circuit costs at least \(rm\) gates more than a restricted event-free realization.

The restricted map requires the \(rm\) distinct \(P_{ik}\) gate values, all carrying \(Y\). Each \(T_i\) cone avoids \(Y\) and is confined to \(\{X,Z_i\}\). A cone for weight \(m+1\) requires at least \(m\) binary gates: the underlying connected ancestor graph has at least \(m+1\) input nodes, while its total edge count with multiplicities is twice its gate count. Two such cones can share only a gate supported on the singleton \(X\), whose nonzero value is the original input \(x\) and can be bypassed. This gives \(2rm\) gates after restriction and \(3rm\) before it. The clean-prefix construction attains the latter. The displayed cancellation circuit therefore proves a genuine gap of at least \(r(m-1)-1\) with one hidden gate. It does not require exact unrestricted optimality.

## Correction to the comparison with an ambient quotient

The original comparison paragraph in AFFINE §3 overstated the benefit of translation. With zero included as a geometric local completion, the two quotient dimensions are exactly equal. For nonempty \(E\), choose \(\ell_0\in E\). Then
\[
\operatorname{span}(E)=\Delta+\langle\ell_0\rangle.
\]
If \(a\in K\), the coset is \(K\) and contains the local value zero. Its difference to the anchor is \(\ell_0\), so \(\ell_0\in\Delta\) and \(\operatorname{span}(E)=\Delta\). If \(a\notin K\), then \(\ell_0\notin K\), so the intersection of \(\operatorname{span}(E)\) with \(K\) is again \(\Delta\). Thus the image of \(K\) under the ambient quotient by \(\operatorname{span}(E)\) is isomorphic to \(K/\Delta\) in both cases. Translation provides a direct representation of the operand equations within \(K\); it does not improve the resulting dimension for this \(E\). This correction leaves AC, AC0, AC+, and formula (3) intact.
