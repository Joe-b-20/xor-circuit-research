# Four diagonals containing a clean triangle need thirteen gates

2026-11-13. Hand proof by own-mask first occurrences, formal relation rank, and entry-label dependence. No circuit search or finite-family checks. The lower bound permits arbitrary intermediate cancellation.

## Setup and common bounds

Require the four rows \(U_i=(E_i,s_i)\) on ordinary block \(b\) and free block \(a\), and require the four clean diagonal values \(c,d,p=c+d,e\), where \(c,d,e\) are independent in
\[
D=\{(v,v):v\text{ is even}\}.
\]
**Theorem.** For every independent choice of \(c,d,e\), supplying these four rows and the four distinct diagonals \(c,d,c+d,e\) requires at least thirteen gates. The bound is attained for one such choice, as recorded at the end; attainment for every prescribed choice is not asserted.

For contradiction take a reduced circuit with at most twelve gates, trimming to all eight required values. The [augmented lower bound](../augmented/PROOF.md) forces exactly twelve. If an actual free label on \(a\) were odd, projecting the free block onto its even space along that label would preserve the targets and remove its entry gate. That would give at most eleven gates for the four rows and three independent diagonals, contradicting A12. Thus all actual entry labels are even, and every computed free part is even.

The four row triples and the four distinct even own masks of the diagonal values require eight non-input own first occurrences. An entry repeats the own mask of its earlier nonfree operand. At least three entries are needed to span the row free parts, so their number \(\tau\) is three or four.

Use \(\rho(\beta,\alpha)=\beta+\alpha\), whose kernel in the even-free-part space is \(D\). Let \(H\) be the physical even-own gate values, \(O\) the physical odd nodes including inputs, and \(V=\operatorname{span}H\). Call an even value clean if it is in \(D\). Since \(D\subseteq V\), we have \(\dim V=3+r\), where \(r=\dim\rho(V)\). If \(A\) counts the odd gates other than the four row outputs, then \(|H|=8-A\) and \(|O|=8+A\).

The eight named odd values \(N\), the four ordinary inputs and four row outputs, have distinct residues filling the odd affine space. Their only nonzero relation is their all-eight sum: vanishing free part selects either no row or all four, and the four own triples sum to own parity, so the latter case uses all four inputs. Hence each nonzero value has at most one wholly named pair, and a helper has at most one expression as a sum of three distinct named values.

Join two odd nodes when their sum is in \(H\), and let \(g\) be the component count of this available graph. The [formal relation bound](../tradeoff/RELATIONS.md) gives
\[
12-\tau\le |O|-g+|H|-\dim V=13-g-r,
\qquad\text{hence } g+r\le\tau+1.
\]
The bound counts independent physical gate equations by their latest-result pivots. The available equation span projects to the odd incidence space of rank \(|O|-g\); its kernel is in the even evaluation kernel of dimension \(|H|-\dim V\). In particular the rank of even-only equations is at most \(|H|-\dim V\). Every edge preserves residue modulo \(\rho(V)\), so \(g\ge2^{3-r}\).

We use two consequences of the named relation property. With one helper \(x\), a nonclean value having both a named pair and a helper pair writes \(x\) as a three-element named sum. For every such doubled value, its two formal equations sum to the same vector on \(x\) and that unique named triple. Thus \(j\) doubled values give rank at most \(j+1\) for \(j\ge1\). With two helpers, a nonclean value with three pairs has one named pair and both helper-to-named pairs. By the [two-helper matching lemma](../frontier/EVEN_ESCAPE.md#two-odd-helpers-saturation-forces-a-dependent-cycle), no second value can also have three pairs. If a second value has two, those equations and two equations of the first value form an alternating four-cycle, hence are dependent as formal physical-node equations.

## Three entries are impossible

With \(\tau=3\), \(g+r\le4\) forces \(r\ge2\). There are at least four clean values and at least two nonclean even values, so \(|H|\ge6\) and \(A\le2\). Nine independent non-entry equations are required.

- If \(A=0\), at most four nonclean even values give at most four wholly named pairs. Clean values give none, since the named residues are distinct. The even-only rank is at most \(8-(3+r)\le3\), for a total of at most seven.
- If \(A=1\), there are at most three nonclean even values. Their doubled-pair equations share one formal sum as described above, so all nonclean odd-pair equations have rank at most four. Across all clean values at most one pair can use the helper, joining it to the unique named node of the same residue. Even-only equations contribute at most \(7-(3+r)\le2\). The total rank is at most seven.
- If \(A=2\), there are exactly four clean values and two nonclean even values, and \(r=2\). Even-only rank is at most \(6-5=1\). If the helpers share a residue, the only possible clean pairs lie in their three-node residue class, giving at most three. Each nonclean value has at most two pairs: at most one wholly named pair, and at most one helper-to-named pair because the opposite named endpoint is unique. This gives at most seven odd-pair equations. If the helpers have different residues, there are at most two clean pairs. The two nonclean values cannot both attain three pairs, so at most five nonclean pairs exist. Again odd-pair and even-only equations have total rank at most eight.

All alternatives contradict the nine required non-entry equations.

## Four entries and at most two helpers are impossible

With \(\tau=4\), all eight non-entry gates are first occurrences. The even own masks are exactly the four specified diagonal own masks. Among them the only zero sum of three distinct masks is the own-mask triple for \(c,d,p\), since \(e\) is independent of the plane of \(c,d\). A non-entry gate with two even operands cannot use equal own masks, since its result would have own part zero. Consequently at most one actual even-only gate occurs: only the last first occurrence among the three fibres for \(c,d,p\) can be obtained from the other two. This conclusion holds even if an operand is an entry copy carrying the same own mask but a different free part.

The inequalities \(g+r\le5\) and \(g\ge2^{3-r}\) exclude \(r=0\), so \(|H|\ge5\) and \(A\le3\).

If \(A=0\), at most four wholly named pairs plus the one possible even-only gate give at most five non-entry gates. If \(A=1\), the shared formal sum gives odd-pair rank at most five as in the three-entry case, and the one actual even-only equation adds at most one. Neither reaches eight.

Suppose \(A=2\), so \(H\) has four clean and two nonclean values \(k,l\).

**Different helper residues.** There are at most two clean odd-pair equations. If neither nonclean value has three pairs, the total odd-pair count is at most six. Otherwise the second value has at most two pairs, and reaching seven odd-pair equations requires its two pairs to be present. The alternating four-cycle then lowers their rank to at most six. Adding at most one actual even-only equation cannot reach eight.

**Equal helper residues.** Let the helpers be \(x,y\). At most three clean pairs lie in the common three-node residue class, and each nonclean value has at most two pairs, as above. To reach eight gates the seven possible odd-pair equations must all be used, together with one even-only equation. In particular all three clean pairs are used, and their three distinct sums add to zero. Among the four clean values the unique such triple is \(c,d,p\). Adding the three formal clean-pair equations therefore gives precisely the formal even equation \(c+d+p=0\).

If \(r=2\), the two nonclean residues are distinct, so any even-only relation must use only clean values. The only one is already the sum of the three clean-pair equations. If \(r=1\), the two nonclean residues agree. Their helper-to-named pairs have the same opposite named endpoint \(q\), and must use different helpers since \(k\ne l\). Say \(k=x+q\), \(l=y+q\). Then \(k+l=x+y\), which is the clean value labelling the pair \(\{x,y\}\). The two helper-pair equations and that clean-pair equation sum formally to the even-only relation with \(k,l\) and \(x+y\). Every possible even-only relation is either \(c+d+p=0\) or this relation with both nonclean values, since residues must cancel. Thus whichever even-only equation is used is dependent on the seven required odd-pair equations. This contradicts their required rank eight.

## Four entries and three helpers: the odd entry labels are dependent

Suppose finally that \(\tau=4\) and \(A=3\). The five physical even values are \(c,d,p,e\) and one nonclean value \(k\). Put \(r_0=\rho(k)\ne0\). Then \(r=1\), \(\dim V=4\), and the component inequalities force \(g=4\). Thus each of the four residue pairs modulo \(\langle r_0\rangle\), containing two named nodes, must be connected in the available odd-pair graph.

Only a \(k\) edge changes residue inside one such class. Each of the four classes therefore needs one. Translation by \(k\) is a matching, with at most one wholly named pair and at most one pair using each of the three helpers. Exactly four edges are needed, so there is one wholly named pair, call it \(\{P_0,Q_0\}\), and three helper-to-named edges in the other three classes. No helper-to-helper edge can occur at equality, since it would consume two helpers for one edge. In particular
\[
P_0+Q_0=k.
\]

In each other class there are exactly its two named nodes and one helper. Name them \(P_i,Q_i,X_i\), for \(i=1,2,3\), so the helper shares the residue of \(P_i\) and
\[
X_i+Q_i=k,\qquad X_i+P_i=h_i
\]
for a physical clean value \(h_i\). The clean edge is necessary to connect the remaining named node. Named-pair uniqueness makes the three \(h_i\) distinct, because
\[
P_i+Q_i=k+h_i.
\]
Summing the four named pairs sums all eight named nodes to zero, giving \(h_1+h_2+h_3=0\). Hence the three used clean values are exactly \(c,d,p\), the unique clean triangle; \(e\) has no odd-pair representation.

There are precisely seven available odd-pair equations, four with color \(k\) and three with colors \(h_i\). The only even-only equation is \(c+d+p=0\): an equation containing the sole nonclean value \(k\) cannot have zero residue, and there is no other clean triangle. All eight non-entry gates are therefore these eight equations. In particular no non-entry gate can produce or read \(e\).

### The three odd entry edges

The value \(e\) must be produced at an entry. Its nonfree operand has the same even own mask, so it is \(k\), the only other physical even value that could share that mask. Put
\[
\eta=\beta(k)=\beta(e).
\]
There are five even gates and exactly four even own first occurrences, so this is the sole even entry. The remaining three entries are odd.

The helper own masks \(\beta(X_i)=\beta(Q_i)+\eta\) are distinct, since the named own masks are all distinct. Every odd four-bit own mask occurs at exactly one named node, either an ordinary input or a designated row. Let \(R_i\) be that named node for the helper \(X_i\):
\[
\beta(R_i)=\beta(X_i)=\beta(Q_i)+\eta.
\]
Its own fibre contains exactly \(R_i,X_i\). Because every non-entry gate is an own first occurrence, the two nodes are joined by one of the three actual odd entries, in either direction. The free label of that entry is therefore
\[
\lambda_i=X_i+R_i=Q_i+k+R_i.                         \tag{1}
\]
This is an undirected identification of the entry edge. A helper may be a first occurrence followed by an entry producing the designated row; no assumption that helpers are entry results is made.

Translation of named own masks by \(\eta\) defines a perfect matching on the eight named nodes. It pairs \(P_0\) with \(Q_0\), so it restricts to a perfect matching on the six remaining named nodes. It pairs \(Q_i\) with \(R_i\).

Consider the three-element selected set \(\{Q_1,Q_2,Q_3\}\).

* If it contains both endpoints of an own-matching pair, say \(Q_i,Q_j\), then \(R_i=Q_j\) and \(R_j=Q_i\). Equation (1) gives \(\lambda_i=\lambda_j\).
* Otherwise it selects exactly one endpoint from each of the three own-matching pairs. Its matched set \(\{R_1,R_2,R_3\}\) is its complement among those six named nodes, which is exactly \(\{P_1,P_2,P_3\}\). Therefore
\[
\lambda_1+\lambda_2+\lambda_3
 = k+\sum_{i=1}^3(P_i+Q_i)=0,
\]
because the sum of the six named nodes equals \(P_0+Q_0=k\).

Thus in every case the three odd entry labels have rank at most two. This is a matching and linear-dependence argument, not an enumeration of gate orientations.

### The fourth entry cannot supply the missing row direction

The even entry producing \(e\) is a terminal export. Every non-entry equation omits \(e\). The only even entry is the one producing \(e\), and an odd entry cannot read it as its nonfree operand because entries preserve the own mask. Hence \(e\) has no gate reader and cannot be an ancestor of any row.

The four row source parts are consequently generated using only the three odd entry labels \(\lambda_i\). Their span has dimension at most two, whereas the required row labels \(s_0,s_1,s_2,s_3\) span dimension three. This contradiction excludes the final profile and proves the thirteen-gate lower bound.

## Attainment for one choice

The [specified twelve-gate supplier](../compatibility/DIAGONALS.md#explicit-event-free-12-gate-circuit) produces the four rows and \(D(01),D(23),D(12)\). Append the one gate
\[
D(13)=D(23)+D(12).
\]
Taking \(c=D(23)\), \(d=D(12)\), and \(e=D(01)\) gives the required clean triangle \(c,d,c+d\) and an independent fourth value. The added gate does not cancel a whole block, so the thirteen-gate realization is event-free. Thus the lower bound is sharp over the stated class, without asserting attainment for every prescribed basis.
