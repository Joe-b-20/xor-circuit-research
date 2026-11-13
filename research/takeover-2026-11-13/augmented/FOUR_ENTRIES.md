# An eleven-gate augmented supplier cannot have four entries

2026-11-13. Hand proof by formal relation rank and matching. No search, enumeration, or computer-driven circuit elimination. This excludes the four-entry branch of the unrestricted augmented problem. It does not assume event-freeness or absence of mixed auxiliaries.

Use four ordinary inputs `b_i`, the free block `a`, and the required rows

    U_c=(E_c,s_c),       E_c=t+e_c,       s_c=e_c+e_(c+1),

where `t=1111`. Also require three independent even diagonal values. Put

    D={(v,v): v even},       rho(beta,alpha)=beta+alpha.

**Theorem.** No normalized eleven-gate circuit for these seven required values has exactly four actual free-entry gates.

The theorem does not need the additional conclusion that all eleven gates are ancestors of the four rows.

## Four entries leave three independent even own masks

By [the independently proved entry-label restriction](PROOF.md#every-eleven-gate-candidate-uses-even-free-labels), all actually used free labels in an eleven-gate candidate are even. Normalize away zero, duplicate, and free-only paid values. An entry is a gate with a free operand; it repeats the nonfree operand's own mask.

The four target triples and the three independent own masks of the required diagonals force at least seven distinct first-occurrence gates. Four entries fill the remaining four slots. Hence there are precisely seven first occurrences: the four triples and three independent nonzero even own masks. Every repeated own mask is created by an entry.

In particular there is no relation among three physical even values: their own masks are drawn from three independent basis vectors, and an odd number of those vectors cannot sum to zero. Thus every non-entry gate uses one even value and two odd values in its three-node equation.

Let `A` count odd non-output gates, let `H` be the physical even values, and let `O` be the physical odd nodes including the inputs. Then

    |H|=7-A,       |O|=8+A.

Exactly three members of `H` are clean: one for each of the three distinct even own masks. They are the required independent diagonal values, denoted `h_1,h_2,h_3`. Every other even value is nonclean.

The named odd nodes `N={b_i,U_c}` have distinct residues, one at each odd four-bit residue. Their only nonzero relation is their all-eight sum. Consequently named-pair sums are unique, and two three-element named sets with the same sum are identical.

All seven actual non-entry equations must be independent in formal physical-node coordinates, by their latest-result pivots.

## At most three odd helpers

Write `V=span H` and `r=dim rho(V)`. The kernel of `rho` on `V` is exactly `D`, since the three independent required diagonals span all of `D`. Therefore

    dim V=3+r.

Let `c` be the number of components of the available odd-pair graph, whose edges have sums in `H`. The [general relation-rank bound](../tradeoff/RELATIONS.md) gives

    7 <= |O|-c+|H|-dim V = 12-c-r,

so `c+r<=5`. If `r=0`, every edge preserves its residue, and the eight distinct named residues require `c>=8`, a contradiction. Hence `r>=1`. Since `3+r<=|H|=7-A`, it follows that `A<=3`.

## Zero or one helper

If `A=0`, there are four nonclean even values. Each has at most one named-pair representation, while a clean value has none. At most four non-entry equations are available, fewer than seven.

If `A=1`, write the helper as `x`. There are three nonclean even values. Each has at most one named-pair representation and one helper-to-named representation. Across all three clean values there is at most one pair: it must join `x` to the unique named node at residue `rho(x)`.

For a nonclean value having both representations,

    k_i=x+n_i=p_i+q_i,

the three named nodes are distinct, and every such equality expresses `x` as the sum of one common three-element named set `S`. This follows from the absence of a named relation on at most six members. The two formal equations for each doubled value have the same sum

    z=[x]+sum_{n in S}[n].

If there are `j>=1` doubled nonclean values, their `2j` equations therefore have rank at most `j+1`. The remaining `3-j` nonclean values contribute at most one equation each, and the clean values together contribute at most one. Total rank is at most five. If `j=0`, it is at most four. Neither reaches seven.

## Two helpers: full even-value independence is unnecessary

Suppose `A=2`, with helpers `x,y`. There are three clean values and two nonclean values `k,l`.

The three clean values have at most two odd-pair representations in total. If the helpers have different residues, there is at most one helper-to-named pair at each of those residues. If their residues agree, all possible clean pairs lie among the three nodes consisting of the helpers and their unique named node. Three such pairs would have three distinct nonzero sums adding to zero, contradicting independence of `h_1,h_2,h_3`. Thus again there are at most two.

Each nonclean value has at most three representations: one wholly named pair and at most one pair using each helper. If both have at most two, there are at most six available equations, already insufficient.

If `k` has three, the [two-helper matching lemma](../frontier/EVEN_ESCAPE.md#two-odd-helpers-saturation-forces-a-dependent-cycle) applies:

    k=p+q=x+n=y+m

for four distinct named nodes `p,q,n,m`; the other value `l` has at most two representations. If it has two, its two equations and two of the `k` equations form an alternating four-cycle and are formally dependent. The lemma uses only matching and uniqueness of three-term named expansions. It does not require independence of all physical even values.

For clarity, a second three-pair value would need its named pair in both triples `{p,q,n}` and `{p,q,m}`, forcing that pair to be `{p,q}` and the value to equal `k`. For a two-pair value, a named pair together with a helper-to-named pair gives the cycle on `x,p,q,n` or on `y,p,q,m`; two helper-to-named pairs give the cycle on `x,n,y,m`; the helper pair together with a named pair gives the cycle on `x,n,m,y`. The equations on each cycle sum to zero because every endpoint and both even labels occur twice.

If `l` has at most one representation, the total count is at most six. If it has two, at most `2+3+2=7` equations are available, but their rank is at most six. Either way seven independent physical non-entry equations are impossible. This covers both possible ranks of the five even values, including the case in which the two nonclean values have the same residue.

## Three helpers: the four named pair sums cannot close

Suppose `A=3`. The four even values are `h_1,h_2,h_3` and one nonclean value `k`. Let `r_0=rho(k)!=0`. These four values are independent, and the odd-pair graph preserves the four residue cosets modulo `<r_0>`. Each contains two named nodes, so there are at least four components. The relation-rank bound forces exactly four. Thus each residue-pair class must be connected.

Only a `k` edge changes residue within such a class, so all four classes need a `k` edge. Translation by `k` is a matching. It has at most one wholly named pair and at most one pair using each of the three helpers, hence at most four edges. Four are required, so there is exactly one in each class: one wholly named edge and three helper-to-named edges. No helper-to-helper edge can occur in this saturation, since it would use two helpers for one edge. The helpers therefore lie one each in the other three classes.

In each helper class, its two named nodes and one helper are the only nodes. The `k` edge joins the helper to the named node at the opposite residue. Connecting the remaining named node requires a clean edge from it to the helper, with color among `h_1,h_2,h_3`.

Consequently the four named residue-pair sums are

    k,       k+h_i,       k+h_j,       k+h_m.

Named-pair uniqueness makes these sums distinct, so the three clean colors are distinct: `{i,j,m}={1,2,3}`. But summing the four pairs sums all eight named nodes, which is zero. Thus

    0=k+(k+h_1)+(k+h_2)+(k+h_3)=h_1+h_2+h_3,

contradicting independence of the required diagonals.

All possible helper populations have now been excluded by relation rank or matching, proving the theorem. The proof concerns structural node classes and does not enumerate circuits or gate assignments. The three-entry branch is separate; no conclusion about it is assumed here.
