# Exact joint cost 22 and a block-monotone MixColumns lower bound of 85

2026-11-13. Hand deductions from [the augmented minimum twelve](PROOF.md), the reviewed
ten-gate producer closure, and the local 10/13 sheet bounds. These are restricted
results. **The unrestricted MixColumns interval remains 75 to 88.**

## The joint two-sheet problem

Let `a` be a free four-coordinate block, with ordinary blocks `b,b'`. Require

    U_c = E_c(b)+s_c(a),
    Y_c = E_c(b')+s_c(b)+s_c(a).

Assume that no ancestor of any `U_c` has nonzero `b'` part. This allows arbitrary
cancellations inside the first-sheet computation and in the consumer; it only excludes
consumer-block feedback into the first-sheet target cones.

**Theorem J22.** The minimum joint cost under this hypothesis is exactly 22 gates.
There is an event-free 22-gate circuit attaining it.

Normalize away free-only, zero, duplicate and dead values. Let `C_0` be the union of gate
ancestors of the four `U_c`, and let `G_1` count all gates with nonzero `b'` part. The
hypothesis makes these sets disjoint. The local sheet lemma gives `|C_0|>=10` and
`G_1>=10`, the latter even when all actually supplied values off `b'` are granted free.

If `|C_0|=10`, [Corollary J10](../crossing/ODD_CLOSURE.md#joint-cost-when-the-first-sheet-cone-has-ten-gates)
already gives at least 22, including possible additional supplier gates and exits.
If `|C_0|>=12`, the disjoint count with `G_1>=10` gives 22 immediately.

A total of at most 21 could therefore only have `|C_0|=11`, `G_1=10`, and no other paid
gates. The [entry-deletion bound](../compatibility/QUOTIENT.md) forces every actual entry
of a ten-gate consumer to lie in its required clean space

    D={v(b)+v(a): v even}.

Its entry labels must span `D`, since its target free parts do. Three independent clean
values must therefore already occur inside `C_0`: they are neither free `a` values nor
ordinary coordinate inputs. But `C_0` would then be an eleven-gate augmented supplier,
contrary to A12. This excludes the last profile.

For attainment, the [recorded twelve-gate source](../compatibility/DIAGONALS.md#explicit-event-free-12-gate-circuit)
supplies diagonal labels `d_0=D(01)`, `d_1=D(12)`, and `d_2=D(23)`. Follow it by the
recorded ten-gate consumer for labels `d_0,d_1,d_2,d_0+d_1+d_2`. All gates are event-free,
and the first-sheet ancestors avoid `b'`. The [direct checker](check_witnesses.py)
evaluates this specified 22-gate construction.

The theorem does not exclude a cheaper unrestricted joint circuit in which first-sheet
ancestors have a nonzero `b'` part that later cancels.

## The block-monotone class

Use the standard MixColumns partition into eight four-bit blocks by bit position. A
sheet is the four output bits at one position. Call a circuit **block-monotone** if
every gate in an output's ancestor cone has block support contained in that output's
support. This is the repository's cone condition, not a requirement that supports grow
at every edge. Event-free circuits satisfy it; the converse need not hold.

The output windows are

    W_0={7,0},     W_1={0,1,7},   W_2={1,2},   W_3={2,3,7},
    W_4={3,4,7},   W_5={4,5},     W_6={5,6},   W_7={6,7}.

For each `j`, let `F_j` contain the gates in the sheet-`j` ancestor cones with nonzero
block-`j` part. The [local hand proofs](../reviews/foundations-audit.md#ten-and-thirteen-gates-for-a-single-sheet)
give `|F_j|>=10`. Enlarge `F_3` to `F_3^+` by also including every gate in its cones
that meets both blocks 2 and 7. Declaring all values on block 2 alone or block 7 alone
free leaves exactly this charged family in a three-block sheet computation, so
`|F_3^+|>=13`.

The own-charge families are pairwise disjoint in the block-monotone class: membership
in both `F_j,F_k` would require both `j in W_k` and `k in W_j`, which no distinct pair
of windows satisfies. The extra gates in `F_3^+` meet both 2 and 7; only `W_3` contains
both blocks, so they belong to no other output's cone.

Now replace `F_0,F_1` by `H`, the union of their ancestor gates after excluding zero and
values supported only on block 7. Granting those excluded values free gives the joint
problem with `a=7`, `b=0`, `b'=1`. The first-sheet cone avoids block 1 by block
monotonicity. Hence J22 gives `|H|>=22`.

These gates are disjoint from `F_2,F_3^+,F_4,F_5,F_6,F_7`. The union window for `H` is
`{0,1,7}`, whose intersections with `W_2,...,W_7` are respectively

    {1}, {7}, {7}, empty, empty, {7}.

The intersection `{1}` cannot meet the block-2 own charge. A pure block-7 gate is
excluded from `H`, and none of the additional sheet-3 charges can fit there because
they meet block 2. The other own-charge intersections are likewise impossible.

**Theorem M85.** Every block-monotone MixColumns circuit has at least

    22 + 13 + 5*10 = 85

gates. In particular every event-free MixColumns circuit has at least 85 gates.
This improves the earlier restricted baseline 84 by one. It is not an unrestricted
85-gate lower bound.

## Consequence for repair inequalities

Any existing theorem whose only use of a numerical baseline `B` is that a repaired
circuit is event-free may now use `B=85`. For example [simultaneous projection repair](../directions/PROJECTION.md)
gives for a reduced circuit, with its sets `V` of original values and `P` of requested projected values,

    G >= 85 + |V minus P| - |P minus V|.

This is still a repair inequality, not a general assertion `G>=85`: the correction can
be negative. Formulas involving additional charged-family slack must retain their own
proofs; the new baseline alone does not justify replacing every historical 83 or 84.
No claim that 88 is optimal follows.
