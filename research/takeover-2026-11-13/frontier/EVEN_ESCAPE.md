# Rank-two clean supply confines every even own direction

2026-11-13. One structural argument, with no circuit search, enumeration, or computer-driven case elimination. This closes the even-coset route left by [PROJECTION_TREE](PROJECTION_TREE.md). The odd-coset route remains open.

**Theorem E2.** In a ten-gate first-sheet producer whose actual clean-diagonal span `W` has rank two, the own masks of all physical even gates lie in `W_b`. Consequently every even-coset difference lies in `W`, and no even coset can supply a missing diagonal direction.

The proof below excludes the remaining one- and two-helper cases under the contrary rank-three-own hypothesis. The zero- and three-helper cases are excluded in [RANK_TWO](RANK_TWO.md). At least three physical even gates would be required by that hypothesis, so these exhaust the possibilities.

## A named-triple rigidity lemma

Work over `F_2`. Let `N` be a set of distinct vectors with no nonempty relation using at most six distinct members. Let `x` be a further vector not in `N`. Suppose three distinct vectors `k_1,k_2,k_3` each have both representations

    k_i=x+n_i=p_i+q_i,       n_i,p_i,q_i in N, p_i!=q_i.

Then

    k_1+k_2+k_3=0.                                      (1)

Indeed `n_i` cannot equal either `p_i` or `q_i`, since that would make `x` a member of `N`. Thus each identity expresses `x` as a sum of three distinct named vectors. Two different three-element sets with the same sum would give a nonempty relation on at most six named members. Consequently all three sets `{n_i,p_i,q_i}` are the same set `S`. The `n_i` are distinct because the `k_i` are distinct, so they are exactly the three members of `S`. Since `x=sum S`, summing `k_i=x+n_i` proves (1).

In particular, within an independent family of `k` values, at most two values can have both a named-pair representation and a representation using `x` and one named value.

## Application to a rank-two producer with one odd helper

Use the ten-gate first-sheet model and notation of [RANK_TWO](RANK_TWO.md). Assume that the actual clean diagonal span has rank two and that the span of physical even own masks has rank three. By [PROJECTION_TREE](PROJECTION_TREE.md), there are exactly three independent free entries, seven non-entry gates, and exactly three independent even own masks. Suppose there is exactly one odd non-output gate `x`, so there are five physical even values. These five values are independent as full vectors.

The odd physical nodes are precisely `N union {x}`, where `N` consists of the four ordinary inputs and four required row outputs. The named nodes have rank seven with their all-eight sum as their unique nonzero relation, and hence satisfy the lemma's no-relation-of-size-at-most-six assumption. Normalization ensures `x` is not a named value.

Exactly two physical even values are clean. There are at least two by the actual clean rank. There cannot be three: their distinct own masks would have to be the three independent even own masks, giving clean rank three. Call the clean values `h_1,h_2`, and the remaining nonclean values `k_1,k_2,k_3`.

Each even value has at most one named-pair representation, by the named-set relation property, and at most one representation involving `x`. A clean value has no named-pair representation, because the named residues `rho(beta,alpha)=beta+alpha` are all distinct. Across the two clean values there is at most one representation involving `x`: its named endpoint must have residue `rho(x)`, which uniquely identifies that endpoint and therefore the sum.

Among the three nonclean values, at most two can have both kinds of representation. Otherwise the named-triple lemma would give `k_1+k_2+k_3=0`, contradicting independence of all physical even values. Thus the number of available odd-pair relations is at most

    1 + (2+2+1) = 6.

There are no even-only three-value relations because the physical even values are independent. Every non-entry gate therefore uses one of these odd-pair relations. A relation can be executed by at most one physical gate: its latest node is its only possible gate result. Seven non-entry gates require seven such relations, contradicting the bound of six.

## Two odd helpers: saturation forces a dependent cycle

Now suppose there are exactly two odd helpers `x,y`. The four physical even values are independent by the projection-tree theorem. Exactly two are clean, call them `h_1,h_2`, and the other two are nonclean, call them `k,l`. Seven non-entry equations are required; no even-only equation is available.

Across the two clean values, there are at most two odd-pair representations in total. If the helpers have distinct residues, each can match only its one named node of the same residue. If the helpers have the same residue, the three nodes in that residue class are the only possible clean-pair endpoints; a fixed nonzero translation has at most one pair on three nodes. Two clean values again give at most two pairs.

Each nonclean value has at most three odd-pair representations: at most one wholly named pair, and at most one pair using each helper. A pair `x+y` uses both helpers and cannot coexist with any helper-to-named pair for the same value, because translation by a fixed nonzero value is a matching.

To reach seven relations, some nonclean value, say `k`, must have three representations. Necessarily

    k=p+q=x+n=y+m,
    x=p+q+n,       y=p+q+m,                         (2)

where `p,q,n,m` are four distinct named nodes. The named nodes `n,m` cannot equal `p,q`, since a helper would then be named; and `n!=m` since `x!=y`.

The other nonclean value `l` cannot also have three representations. If it did, its wholly named pair would be contained in both triples `{p,q,n}` and `{p,q,m}` by the uniqueness of three-element named expansions proved above. Their intersection is `{p,q}`, forcing `l=k`. Thus `l` has at most two representations. The total available relations are at most `2+3+2=7`.

If `l` has fewer than two, this already contradicts the seven required gates. If it has two, their forms exhaust the following three possibilities. In every case, its two edges and two `k` edges make a four-cycle with alternating labels `k,l`.

1. **One named pair and one helper-to-named pair.** Suppose `l=x+u=v+w` with `u,v,w` named. Substituting (2) gives a relation on at most six named nodes. It must cancel identically, so `u` belongs to `{p,q,n}`. The choice `u=n` gives `l=k` and is excluded. Up to swapping `p,q`, the other case is `u=p`, `l=q+n`. The cycle is `x,p,q,n,x`, with successive sums `l,k,l,k`. The case using `y` instead follows with `m` in place of `n`.
2. **Two helper-to-named pairs.** Write `l=x+u=y+v`. Then `u+v=x+y=n+m`. Named-pair uniqueness gives `{u,v}={n,m}`. The uncrossed assignment yields `l=k`, so the distinct value uses `u=m,v=n`. The cycle is `x,n,y,m,x`, with successive sums `k,l,k,l`.
3. **The helper pair and one named pair.** Here `l=x+y=n+m` by (2) and named-pair uniqueness. The cycle is `x,n,m,y,x`, with successive sums `k,l,k,l`.

These possibilities use only matching and the absence of short named relations; they do not enumerate circuit shapes. The four cycle equations sum to zero in the formal coordinates of physical nodes: every odd endpoint and each of `k,l` occurs twice. Consequently the at-most-seven available equations have rank at most six. Actual non-entry gate equations are independent by their latest-result pivots, so they cannot supply seven gates. This excludes the two-helper case.

## Conclusion and remaining scope

The rank-three-own hypothesis allows zero through three odd helpers. [RANK_TWO](RANK_TWO.md) excludes zero and three; the preceding arguments exclude one and two. Since actual clean values already project onto the two-dimensional `W_b`, the physical even own span is exactly `W_b`. This proves E2.

All available differences inside an even diagonal coset therefore lie in `W`, by the even-coset criterion in RANK_TWO. A rank-two producer capable of supporting an eleven-gate consumer must instead use an odd coset containing nodes from distinct own classes modulo `W_b`. The existing ancestry criterion describes this remaining possibility but does not exclude it. The general joint interval remains 21 to 22 and the unrestricted MixColumns interval remains 75 to 88.
