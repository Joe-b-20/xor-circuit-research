# Clean rank two confines every supplied diagonal difference

2026-11-13. Hand proof using physical relations; no SAT, circuit enumeration, exact-gate search, or computer-driven case elimination. This closes the ten-gate producer branch of the joint problem. It does not exclude an eleven-gate first-sheet core.

## Supplier theorem

Use the first-sheet model with ordinary inputs `b_0,...,b_3`, every vector of a separate block `a` free, and four targets

    U_c = E_c(b)+s_c(a),       s_c=e_c+e_(c+1).

Write a value as `(beta,alpha)` and put

    D = {(v,v): v is even},       rho(beta,alpha)=beta+alpha.

Let `Sigma` consist of every physical value of a ten-gate producer, the ordinary inputs, and all free `a` values. Let `W=span(Sigma intersect D)` be its actual clean span.

**Theorem C.** If `dim W=2`, then for every coset `C` of `D`,

    u,v in Sigma intersect C  implies  u+v in W.                 (1)

Thus no pair of actually available values hides a third independent diagonal direction. In particular one appended XOR gate cannot enlarge the clean span. The theorem concerns all available operands; it does not grant arbitrary combinations of them for free.

The even-coset part is [Theorem E2](../frontier/EVEN_ESCAPE.md). It places every physical even own mask in the two-dimensional `W_b`, the own projection of `W`. Differences inside an even coset therefore project into `W_b` and belong to `W`. On the even-free-part space, cosets of `D` are precisely fibres of `rho`; all paid producer values have even free part. An odd-free-part coset contains at most one available value, a free value, so contributes no difference.

It remains to exclude an odd coset containing two nodes whose own masks differ outside `W_b`.

## A crossing removes a clean pair

By [the normal form](NORMAL_FORM.md), the producer has four entries, four independent physical even values, and exactly two odd helpers beyond the eight named inputs and outputs. The even values consist of two clean values `h_1,h_2` and two nonclean values `k,l`. Six independent non-entry equations are required. There are no even-only equations because the four physical even values are independent.

The own odd masks have two classes modulo `W_b`. A clean sum in `W` joins only nodes in the same own class. The eight named nodes have distinct residues, one at each odd residue. Call the two helpers `x,y`.

Suppose an odd residue class contains nodes from different own classes. Then the **total** number of pair representations of `h_1,h_2`, across all residues, is at most one:

* If `rho(x)!=rho(y)`, each populated residue has just its helper and its unique named node. At least one such pair crosses own classes and cannot sum to either clean value. The other contributes at most one pair.
* If `rho(x)=rho(y)`, only that three-node residue class can contribute clean pairs. A crossing splits its nodes into two own classes of sizes two and one, leaving only one within-class pair.

Every other residue contains a single named node, hence no clean pair. This proves the collective bound; it does not merely bound each clean value separately.

## The remaining relations cannot be independent

Each of `k,l` has at most three odd-pair representations: one wholly named pair and at most one pair using each helper. The representations of a fixed nonzero value form a matching.

If both values have at most two representations, at most `1+2+2=5` equations are available, below the six required. Otherwise, say `k` has three. The [two-helper saturation argument](../frontier/EVEN_ESCAPE.md#two-odd-helpers-saturation-forces-a-dependent-cycle) proves:

1. `l` has at most two representations.
2. If it has two, those two relations together with two of the `k` relations form an alternating four-cycle, whose four formal equations sum to zero.

For completeness, the argument uses `k=p+q=x+n=y+m` with four distinct named nodes `p,q,n,m`. Each helper has a unique three-term named expansion, since the named nodes have no nonzero relation on at most six members. A second three-pair value would need its named pair in both triples `{p,q,n}` and `{p,q,m}`, forcing equality with `k`. For a two-pair value the possibilities are a named pair plus one helper pair, two helper-to-named pairs, or the helper pair plus a named pair. Matching and the same short-relation property give an alternating four-cycle in each case. No circuit shapes are enumerated.

If `l` has at most one pair, the total count is again at most five. If it has two, at most six equations are available but their rank is at most five because of the cycle. Actual gate equations are independent by their latest-result pivots. Neither alternative can supply six non-entry gates.

This contradiction excludes an odd crossing. An odd same-residue difference therefore has own part in `W_b`, and, being diagonal, belongs to `W`. Together with the even case this proves (1).

## Consequences for a consumer and for one extra supplier

A fixed ten-gate producer of clean rank two now satisfies the [supplier-profile deficiency certificate](../tradeoff/SUPPLY_PROFILE.md): its actual clean values lie in the proper subspace `W<D`, and every within-one-coset difference lies in `W`. An at-most-eleven-gate consumer can read clean labels plus labels from at most one nonclean quotient direction. Such labels cannot span the required `D`. Hence at least twelve consumer-bearing gates are needed.

Clean rank at ten gates is at most two. The [rank-one theorem](../frontier/RANK_ONE.md) already proves the same twelve-gate consumer bound at clean rank zero or one. Therefore **every ten-gate first-sheet producer requires at least twelve consumer-bearing gates when its supply is fixed**.

For rank two, (1) also shows that no single appended source-only gate can provide a clean value outside `W`: two operands whose sum is clean lie in the same `D` coset. At rank at most one, a single additional value can raise clean rank only to at most two. Thus no ten-gate first-sheet producer can be extended by one gate to supply three independent diagonals.

## Joint cost when the first-sheet cone has ten gates

Consider the two-sheet problem with additional ordinary block `b'`. Assume no ancestor of a first-sheet target has nonzero `b'` part. Let `C_0` be the union of the gate ancestors of the four first-sheet targets, and suppose it has ten gates. The second-sheet target free parts span `D`; their consumer-own projections are the four triples on `b'`.

**Corollary J10.** Every such joint circuit has at least 22 gates. The bound is attained in this class by the recorded [22-gate construction](../tradeoff/EXPORTS.md#fixed-producer-joint-consequence-22-gates).

Indeed every consumer-bearing computation needs at least ten gates. If there are no additional zero-`b'` gates beyond `C_0`, the fixed-supplier result needs at least twelve. If there are at least two additional zero-`b'` gates, the total is already at least `10+2+10=22`.

The only remaining total of at most 21 would have one extra zero-`b'` gate `g` and ten consumer-bearing gates. The entry-deletion bound then forces every actual consumer entry to be clean, and these labels must span `D`.

If the initial clean rank is at most one, one extra value cannot supply rank three. If it is two, let its span be `W`. Before `g`, every clean entry is in `W`. By induction, every earlier consumer-bearing node has its producer-side part in `W`. If `g` is a consumer-block-cancelling exit, it adds two such parts and remains in `W`. If `g` reads two zero-`b'` operands, they are already supplied by `C_0`, ordinary inputs, or the free block; Theorem C places their sum in `W` whenever it is clean. Thus `g` cannot supply the missing direction in either case. This contradicts the rank-three entry requirement.

## The remaining eleven-gate core

The general joint lower bound remains 21. A hypothetical joint circuit of size 21 must now have eleven gates in `C_0`, ten consumer-bearing gates, and three independent clean diagonals already inside `C_0`. In particular it has no separate export gate or consumer-block exit supplying the third direction.

Likewise, any eleven-gate augmented supplier of all four first-sheet rows and three independent diagonals must have all eleven gates in the ancestor union of the four rows. If that union had ten gates, its one remaining gate could not extend the clean rank to three, by the preceding argument. Thus every requested diagonal in such an eleven-gate solution is already used in the first-sheet computation.

The unrestricted augmented minimum remains eleven or twelve. The 22-gate joint bound proved here assumes a ten-gate first-sheet cone; it does not prove a general joint lower bound of 22 or alter `75<=L(MixColumns)<=88`.
