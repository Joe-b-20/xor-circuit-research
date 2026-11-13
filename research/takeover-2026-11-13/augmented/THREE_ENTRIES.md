# Eleven augmented gates cannot use three entries

2026-11-13. Hand proof for the unrestricted augmented-sheet problem. No circuit search, enumeration, or finite-family checks. The proof allows intermediate whole-block cancellations.

Require the four rows \(U_c=(E_c,s_c)\) and three independent clean diagonal values on blocks \(b,a\), with \(b\) ordinary and \(a\) free. Take a normalized eleven-gate circuit and suppose it has three entries. The three actually used free labels span the required three-dimensional even space, so all are even. This also follows from the independent normalization in [PROOF](PROOF.md). Let \(D\) be the three-dimensional clean diagonal and \(\rho(\beta,\alpha)=\beta+\alpha\), whose kernel on the even-free-part space is \(D\).

Write \(H\) for the physical even-own gate values, \(V=\operatorname{span}H\), \(r=\dim\rho(V)\), and \(A\) for the number of odd non-output gates. Since the three independent clean values belong to \(H\), the kernel of \(\rho\) on \(V\) is exactly \(D\). Thus \(\dim V=3+r\). The eight named odd values \(N\) are the four own inputs and four required rows. They occupy the eight odd residues once each, and their only nonzero relation is their all-eight sum. In particular they have no relation on at most six members and a nonzero value has at most one representation by a named pair.

There are \(7-A\) physical even gates and \(8+A\) physical odd nodes including inputs. In the available odd-pair graph, an edge has an even physical value as its endpoint sum. Let \(c\) be the number of components. The [formal relation-rank bound](../tradeoff/RELATIONS.md) gives
\[
8\le (8+A)-c+(7-A)-(3+r)=12-c-r.
\]
Every edge preserves residue modulo \(\rho(V)\), so \(c\ge 2^{3-r}\). Thus \(r\ge2\): ranks zero and one would give \(c+r\ge8\) and \(c+r\ge5\), respectively. As \(7-A\ge3+r\), there are at most two odd helpers.

## Zero or one odd helper

With \(A=0\), all odd values are named. A clean even value has no named pair because the named residues are distinct. There are at most four nonclean even values, and each has at most one named pair. The actual count of even-only gates is at most \(|H|-\dim V\le2\) by [the even-span bound](../tradeoff/RELATIONS.md). Thus there are at most six non-entry gates, contradicting eight.

With \(A=1\), call the helper \(x\). There are six even values, at least three clean and at most three nonclean. Across all clean values there is at most one odd-pair equation: its endpoints must be \(x\) and the unique named node of the same residue. A nonclean value has at most one named pair and one helper pair. If both exist, it has the form
\[
h=p+q=x+n
\]
for three distinct named values \(p,q,n\). This writes \(x\) as the sum of their three-element set, which is unique because the named values have no nonzero relation of length at most six. Thus all nonclean values with both representations use the same named triple \(S\). For each such even value the sum of its two formal equations is the same formal vector, consisting of \(x\) and all members of \(S\). If there are \(d\ge1\) such values, their \(2d\) equations span at most \(d+1\) dimensions. Adding the other nonclean values and the clean pair gives an odd-pair relation rank at most \((d+1)+(3-d)+1=5\). With no such doubled value the rank is at most four. The even-only relations have formal rank at most \(|H|-\dim V\le1\), since they evaluate to zero on \(H\). Hence the total non-entry rank is at most six, again contradicting eight.

## Two odd helpers

With \(A=2\), there are five even values. The bound \(3+r\le5\) forces \(r=2\), and \(V\) has dimension five. Thus the even values are independent, exactly three are clean, and the two nonclean values \(k,l\) have independent residues. There are no even-only equations.

The component bound gives \(c\le2\). There are already two residue cosets modulo \(\rho(V)\), each containing four named odd nodes, so each coset must be connected. Project a connected coset onto its four named residues. Clean edges collapse, whereas nonclean edges change residue. A connected graph on the four residue vertices needs at least three nonclean edges before projection. Consequently at least six nonclean odd-pair edges are needed across the two cosets.

For each of \(k,l\), translation is a matching, permitting at most one named pair and at most one pair per helper. Therefore each has at most three pairs. To reach six nonclean edges both would need three. This is impossible by the [two-helper saturation argument](../frontier/EVEN_ESCAPE.md): a three-pair value has a named pair plus two helper-to-named pairs, so writes each helper as the sum of the named pair and one further named node. Each helper's three-element named expansion is unique. The two expansions intersect precisely in the original named pair, because their additional named nodes are distinct. Any other three-pair value would need its named pair in that same intersection, forcing it to be the first even value.

This excludes two helpers and exhausts the three-entry hypothesis. The argument proves that any eleven-gate augmented supplier has four entries: seven distinct own first occurrences are already required by the four own triples and three distinct even diagonal masks, giving an upper bound of four entries. It does not by itself rule out that four-entry branch.
