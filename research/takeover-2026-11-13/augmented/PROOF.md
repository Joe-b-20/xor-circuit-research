# Four rows and three independent diagonals require twelve gates

2026-11-13. Structural hand proof with independent machine review. No circuit search,
SAT, exhaustive enumeration, exact-gate optimization, or computer-driven case elimination.
The lower bound permits arbitrary sharing and cancellation, including whole-block events.

## The exact local result

Let `b_0,...,b_3` be ordinary inputs and let every vector on a separate four-coordinate
block `a` be free. Write `t=e_0+e_1+e_2+e_3`, with indices modulo four, and require

    U_c = E_c(b)+s_c(a),       E_c=t+e_c,       s_c=e_c+e_(c+1).

Also require three independent values from the even diagonal space

    D = {v(b)+v(a): v is even}.

**Theorem A12.** Every circuit containing these four rows and three independent even
diagonal values has at least twelve paid XOR gates. A twelve-gate event-free circuit
exists. Thus the minimum for supplying some independent diagonal basis is exactly twelve.
The lower bound applies to every prescribed basis; attainment for every prescribed basis
is not asserted.

The proof does not assume that the diagonals are ancestors of the four rows. It is
independent of the preceding ten-gate producer-closure theorem.

## Normalization and physical relations

Take a minimum circuit, retaining the ancestors of all seven required values. Bypass
zero, duplicate, and wholly free paid values. Write a value as `(beta,alpha)`, its ordinary
and free parts; every counted gate has `beta!=0`. An entry reads one free operand, and
`tau` counts these gates. Its ordinary mask repeats that of its earlier nonfree operand.

The free parts of the four rows span the three-dimensional even space, so `tau>=3`.
The four distinct odd triples and three distinct nonzero even diagonal masks require
seven first occurrences of non-input ordinary masks. Entries are disjoint from those
first occurrences. Therefore a circuit of size at most eleven has `tau<=4`, and every
circuit has at least ten gates.

We use [the physical relation-rank inequality](../tradeoff/RELATIONS.md). Let `O` be the
odd-ordinary physical values including the four inputs, let `H` be the even-ordinary
physical values, and let `d_H=dim span H`. Join two odd nodes when their sum is in `H`;
let `c` count graph components, including isolated nodes. Then

    G-tau <= |O|-c+|H|-d_H.                                (1)

Here all non-entry gate equations are independent in formal physical-node coordinates:
the latest result in any selected nonempty sum of equations cannot cancel. Projecting
the span of all available equations onto the odd coordinates gives incidence rank
`|O|-c`; its kernel lies in the evaluation kernel on the even coordinates, of dimension
`|H|-d_H`. This proves (1), including possible even-only equations. Also at most
`|H|-d_H` actual gates can be formed by adding two physical even values: the other
production methods must supply generators of the full even span.

When every actually used free label is even, put `rho(beta,alpha)=beta+alpha`. The eight
named odd values `N={b_i,U_c}` have residues `e_i,E_(c+1)`, the eight odd four-bit vectors
once each. Their unique nonzero relation is their all-eight sum: zero free part forces
either no row or all four rows, and in the latter case all four inputs must be included.
Thus named pairs have unique sums, and a helper has at most one three-element named
expansion.

Let `A` count the odd gates other than the four designated rows, let `V=span H`, and
let `r=dim rho(V)`. All of `D` lies in `V` because its three independent required values
are physical even gates. The kernel of `rho` on `V` is exactly `D`, so `d_H=3+r`.
Since `|O|+|H|=G+4`, (1) becomes

    c+r <= tau+1.                                         (2)

Every graph edge preserves residue modulo `rho(V)`. The eight named odd residues occupy
all `2^(3-r)` affine classes, so

    c >= 2^(3-r).                                         (3)

These bounds count physical node relations rather than treating virtual sums as gates.

## A short ten-gate exclusion

This supplies the baseline needed for parity confinement without relying on the older
augmented lower-bound proof. At ten gates, the seven first occurrences force `tau=3`.
Those three entry labels span exactly the required even free space, hence all are even.
Equations (2)-(3) force `r>=2`. There are `|H|=6-A` even gates, with rank `3+r>=5`, so
`A<=1`.

If `A=0`, every odd pair is named. A clean even value has no named pair, since named
residues are distinct. At least three even values are clean, leaving at most three
nonclean values with one pair each. There are at most `|H|-d_H<=1` actual even-only
gates. At most four non-entry gates are possible, whereas seven are required.

If `A=1`, there are five independent even values, three clean and two nonclean. No
even-only relation exists. Across all clean values, at most one pair uses the helper
and its unique same-residue named node. Each nonclean value has at most one named pair
and one helper pair. At most five relations are available, again fewer than seven.
Thus ten gates are impossible.

## Every eleven-gate candidate uses even free labels

Suppose an actual entry label `alpha` were odd. Project block `a` linearly onto its even
subspace along `alpha`. This projection fixes every required free part and kills that
entry label. The gate becomes a wire; projecting all other nodes, bypassing repeated or
free values, and pruning yields an augmented circuit of at most ten gates. Its ordinary
parts and all seven required values are unchanged. This contradicts the preceding lemma.
Therefore every actual entry label, and every computed free part, is even.

An eleven-gate candidate consequently satisfies (2)-(3) and has either three or four
entries. Both cases are excluded by the following structural arguments.

## Three entries

The [full three-entry proof](THREE_ENTRIES.md) uses (2)-(3) to get `r>=2` and at most two
odd helpers. With no helper, at most four named-pair gates and two even-only gates exist,
short of eight. With one helper, doubled nonclean pair representations share a unique
three-term named expansion. Their formal equation pairs have one common sum, limiting
odd-pair rank to five; even-only relations add at most one.

With two helpers, the five even values are independent: three clean and two nonclean.
Their graph must connect both four-residue classes. Clean edges do not change residue,
so each connected class needs at least three nonclean edges. Both nonclean values would
therefore need three pair representations. The unique three-term named expansions of
the two helpers make that impossible: their common named pair would force the two
nonclean values to coincide. Thus eight independent non-entry gates are unavailable.

## Four entries

The [full four-entry proof](FOUR_ENTRIES.md) starts with exactly seven first occurrences:
three independent even ordinary masks and the four triples. No even-only relation can
exist, because three masks drawn from an independent basis cannot sum to zero. There
are exactly three physical clean values. Equations (2)-(3) leave at most three helpers.

Zero helpers give at most four equations. One helper gives relation rank at most five
by the common three-term expansion argument. With two helpers, clean pair capacity is
at most two. If the two nonclean colors have enough pairs to reach seven equations,
their equations contain an alternating four-cycle, lowering rank to at most six.

With three helpers, only one nonclean even value remains. Four residue-pair classes must
be connected. Its matching has exactly one named edge and three helper-to-named edges.
The four named pair sums must then be `k,k+h_1,k+h_2,k+h_3` for the three independent
clean values. Summing the pairs sums all eight named nodes to zero and forces
`h_1+h_2+h_3=0`, a contradiction. Seven independent non-entry equations are impossible.

These arguments exhaust entry counts, not circuit shapes. Hence eleven gates are
impossible even with cancellation.

## Attainment and scope

The [explicit twelve-gate construction](../compatibility/DIAGONALS.md#explicit-event-free-12-gate-circuit)
computes all four rows and diagonal masks `01,23,12`. It is event-free. Its evaluation is
reproduced by [the direct checker](check_witnesses.py). This proves A12.

The result is an exact local circuit theorem. Its [joint and block-monotone consequences](CONSEQUENCES.md)
require their stated hypotheses; the unrestricted MixColumns range remains 75 to 88.
