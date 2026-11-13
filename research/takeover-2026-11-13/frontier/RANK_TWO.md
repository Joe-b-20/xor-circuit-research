# Rank-two clean supply and possible missing directions

2026-11-13. Hand argument for ten-gate first-sheet producers. No circuit search or finite-family checks. This isolates necessary conditions for a rank-two supplier to complete the diagonal span with a nonclean coset. It neither proves universal deficiency nor supplies a compatible eleven-gate consumer.

**Later closure in this pass:** [Theorem E2](EVEN_ESCAPE.md) excludes all remaining even-coset escape cases. The preliminary reductions below supply its zero- and three-helper cases. Only the odd-coset route remains open.

Use the first-sheet targets \(U_c=E_c(b)+s_c(a)\) and the clean even diagonal \(D=\{(v,v):v\text{ even}\}\). Let \(W\subset D\) be the span of the clean values actually available from the producer, and suppose \(\dim W=2\). Write \(W_b=\{v:(v,v)\in W\}\) for its own-block projection. For each nonzero coset \(C\) of \(D\), let \(\Delta_C\) be the span of differences of its available values. A consumer with at most eleven gates can use at most one nonclean coset, by [the quotient-rank bound](../compatibility/QUOTIENT.md), and must have \(W+\Delta_C=D\) for that coset. The fixed rank-two producer of [EXPORTS](../tradeoff/EXPORTS.md) has \(\Delta_C\subseteq W\) for every coset. The arguments below describe what must differ in any rank-two producer that escapes that particular obstruction.

## Every rank-two producer has an odd helper

Call a gate odd or even according to its nonzero own-block mask. By parity confinement, its free part is even. The named odd values \(N\) are the four own inputs and the four required outputs. They occupy distinct odd residues under \(\rho(\beta,\alpha)=\beta+\alpha\), and their only nonzero relation is their total sum. Hence any nonzero value has at most one representation by an unordered pair of distinct named values.

Suppose there is no odd non-output gate. Each required own triple appears for the first time at its designated gate, so no output gate is an entry. Each must use a physical even value with its odd operand and result as the two named endpoints of its pair representation. These four even values are distinct: one named pair can supply at most one physical gate, and different named pairs cannot give the same value. Each has nonzero residue, since its two named endpoints have distinct residues.

The first physical even gate is an additional nonclean value. It must add two distinct own inputs: no previous even gate exists, no odd non-output gate exists, and no odd output can be an entry or precede every even gate. The two input residues are different, so the first even gate is nonclean. Its named-pair representation consists of two inputs, not one of the four pairs involving a target as the gate result. Thus it differs from all four even values counted for the outputs.

With four odd gates there are six even gates. At least five are nonclean, so at most one is clean. Therefore a ten-gate producer of clean rank two necessarily has an odd non-output gate. This tightens the no-odd-helper cap in [RELATIONS](../tradeoff/RELATIONS.md) by using the causal origin of the first even value.

## Even cosets and the own projection span

Let \(P_b\) be the span of the own masks of all physical even gates. The physical clean gates show \(W_b\subseteq P_b\). A nonzero coset with odd free-part parity contains at most one available value and contributes no difference. On values with even free part, cosets are the fibres of \(\rho\).

An even physical gate \((\beta,\alpha)\) with nonzero residue \(r=\beta+\alpha\) shares its coset with the free value \((0,r)\). Their difference is \((\beta,\beta)\). Conversely every even-coset difference has own projection in \(P_b\), because each endpoint is a physical even gate or the free representative of that coset. It follows that some nonzero even coset has \(W+\Delta_C=D\) if and only if \(P_b\) has dimension three. In the forward direction an escaping difference requires an even own projection outside \(W_b\). In the reverse direction some physical even gate has own mask outside \(W_b\), and it cannot be clean by the definition of \(W\).

If this even-coset escape occurs in ten gates, the producer has a restricted own-fibre structure. At least three distinct nonzero even own masks are needed, in addition to the four distinct own triples. They require seven distinct first-occurrence gates. Each entry repeats an earlier own mask, and the target free rank requires at least three entries. The ten-gate budget therefore gives exactly seven first-occurrence gates and three entries. There are exactly three distinct even own masks and they form a basis of the even subspace. All other gates are entries. Their three free labels form a basis of the even free space.

In this structure, nodes with a fixed own mask form a tree rooted at the first occurrence of that mask, or at the ordinary input for a unit mask. Each entry edge adds its own free label. A difference within one fibre equals the sum of labels on the unique tree path. Entry paths in distinct fibres use disjoint occurrences. This restricts where the clean diagonal gates can appear, but the fibre count alone does not show that \(P_b\) has dimension two.

### Three physical even gates cannot realize the even escape

Suppose \(P_b\) has rank three and there are exactly three physical even gates. By the preceding first-occurrence count there are three entries and at least seven independent formal non-entry equations. The three even values have independent own masks and thus are independent as full values. Two are the independent clean values \(h_1,h_2\); the third, \(k\), must have a nonzero residue \(r\), since otherwise the clean rank would be three. There are eleven odd nodes, the eight named nodes and three odd helpers.

Use the odd-pair graph of [RELATIONS](../tradeoff/RELATIONS.md). Its edges preserve a residue (colour \(h_1\) or \(h_2\)) or toggle \(r\) (colour \(k\)). Thus its components lie in the four residue pairs \(\{s,s+r\}\), each containing two named nodes. By independence of the three even values, the even-colour evaluation kernel is zero, and the formal relation rank is the ordinary incidence rank. At least seven independent non-entry equations on eleven odd nodes force at most four components. There are already at least four by the residue pairs, so each pair class must be connected.

Each of these four classes needs a \(k\)-edge joining its two residues. Translation by \(k\) is a matching. At most one of its edges is wholly named, by the named-pair uniqueness, and at most three involve a helper because there are only three helpers. Thus it has exactly four edges, one per class. One class has a named-to-named \(k\)-edge, and each other class has one helper and a \(k\)-edge between that helper and the named node at the opposite residue. In each of the latter classes, the remaining named node can connect only by a clean edge to the helper of the same residue. Its colour must be \(h_1\) or \(h_2\). It follows that the four named residue-pair sums are \(k\) and three values in the two-element set \(\{k+h_1,k+h_2\}\). Two of these named pairs would have equal sum, a contradiction.

Consequently an even escape requires at least four physical even gates. This excludes exactly three even gates and leaves larger even-gate populations to a separate argument.

## The remaining odd-coset route

If \(P_b=W_b\), every even coset is deficient. An odd non-entry gate changes its own mask by one of the even own masks, and an odd entry does not change it. Hence every odd node has an own mask in \(b_i+W_b\) for some ordinary input \(b_i\) reached along its odd ancestry. Within any odd residue, a difference outside \(W\) can only join nodes whose own masks belong to distinct cosets of \(W_b\).

One can make this criterion concrete when \(W_b\) omits the full own parity. Then \(W_b\) consists of the even masks on some three-coordinate subset \(I\): its three nonzero masks are pairs, and two independent pairs cannot be disjoint because their sum would be the full parity. Write \(j\) for the coordinate outside \(I\). In this case an odd same-residue pair gives a difference outside \(W\) exactly when its own components on \(j\) differ. The own triple \(E_j\) can trace its odd ancestry only to one of the inputs in \(I\), while the other triples must trace to \(b_j\). The fixed residue condition still concerns the full free and own masks, so this projected ancestry statement does not exclude a crossing between the two classes.

Thus a complete rank-two supply proof would need to exclude three independent physical even own masks, and then exclude an odd same-residue pair crossing the remaining own classes. The three-even-gate case of the first exclusion is proved above. The other even cases are subsequently closed in [EVEN_ESCAPE](EVEN_ESCAPE.md); the odd escape remains open.
