# Second review of the even-coset exclusion

2026-11-13. Independent machine proof review of [EVEN_ESCAPE](../EVEN_ESCAPE.md), with emphasis on its two-helper case. No circuit search or finite-family checks were run.

## Saturation with two helpers

Under the contrary rank-three own projection hypothesis, the projection-tree theorem gives three entries, seven non-entry gates, and an independent set of physical even values. With two odd helpers there are four even values. Exactly two are clean, since three distinct clean physical values would require three distinct even own masks and would be independent. No even-only relation exists.

A clean odd-pair relation stays inside one residue. If the two helpers have distinct residues, each can match only its one named node of the same residue. If their residues agree, each clean value can match at most one pair in the three-node class. Thus at most two clean relations exist in either case.

A nonclean value has at most one named pair and at most one pair per helper, because translation by that value is a matching. To reach seven relations, some nonclean value \(k\) must have three. Write
\[
k=p+q=x+n=y+m.
\]
Here \(x,y\) are the two helpers, and \(p,q,n,m\) are distinct named values. Indeed, an equality of \(n\) or \(m\) with \(p\) or \(q\) would make a helper named, and \(n=m\) would give equal helpers. Thus \(x=p+q+n\) and \(y=p+q+m\) are two distinct three-element named expansions. Each expansion is unique because the named set has no nonzero relation on at most six terms.

A second value \(l\ne k\) cannot have three pairs: its named pair would have to be contained in both three-element expansions, by uniqueness, and hence equal \(\{p,q\}\). If \(l\) has two pairs, there are exactly three possibilities. A helper-helper pair exhausts both helpers and must be accompanied by a named pair. Without it, two pairs use either both helpers separately or one helper and the unique possible named pair.

- A named pair and an \(x\)-to-named pair give \(l=x+u=v+w\), so \(\{u,v,w\}=\{p,q,n\}\). The choice \(u=n\) gives \(l=k\). Up to interchanging \(p,q\), the remaining choice gives \(l=q+n=x+p\). This creates the four-cycle \(x,p,q,n,x\). For a \(y\)-to-named pair the proof uses \(m\) in place of \(n\).
- Two helper-to-named pairs give \(l=x+u=y+v\), and named-pair uniqueness forces \(\{u,v\}=\{n,m\}\). The uncrossed assignment gives \(k\), so the distinct \(l\) gives the four-cycle \(x,n,y,m,x\).
- The helper pair plus a named pair gives \(l=x+y=n+m\), and the four-cycle is \(x,n,m,y,x\).

Each cycle alternates \(k,l\). Its four formal equations sum to zero because each odd node and each even colour occurs twice. Thus even if all seven pair relations exist, they have rank at most six. If fewer exist their count already falls short. Actual non-entry equations are independent by the latest-result argument, so the two-helper case is excluded.

## Coverage and conclusion

Three independent even own directions require at least three physical even gates. Since four designated outputs are odd, the number of additional odd gates lies between zero and three. This count refers to odd helpers, without identifying their nodes with entries.

The zero-helper case in RANK_TWO uses four distinct nonclean even values for the four output relations and a fifth at the first even gate. That leaves at most one clean value. Its three-helper case uses independence of the three even values and incidence rank on the four residue pairs. Reaching seven equations would force the four distinct named pair sums to consist of \(k\) and three choices from \(\{k+h_1,k+h_2\}\), impossible. In the one-helper case of EVEN_ESCAPE, at most two independent nonclean values can have both a named pair and a helper pair. The uniqueness of a three-element named expansion gives a zero sum for any three such values, establishing the six-relation ceiling. The four cases therefore exhaust the rank-three own projection hypothesis.

The actual clean values already span two own directions. Ruling out a third physical even own direction proves equality of the physical even own span with \(W_b\). An even-coset difference has its own part in that span and lies in the clean diagonal, hence belongs to \(W\). This excludes the even-coset escape and does not exclude an odd coset crossing the two own classes. The general joint bound is unchanged.
