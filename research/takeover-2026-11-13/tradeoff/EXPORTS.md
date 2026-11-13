# Diagonal export capacity at ten sheet gates

2026-11-13. Hand construction and proof; no SAT, enumeration, exact-gate search, or computer-driven case elimination. This resolves the diagonal-export capacity of a ten-gate one-sheet circuit. It does not resolve whether eleven gates can supply three independent diagonals, and it does not change the unrestricted MixColumns bound.

## Result

Let `b_0,...,b_3` be ordinary input coordinates, let all vectors on a disjoint four-coordinate block `a` be free, and write

    E_c(b) = sum_{d != c} b_d,
    s_c(a) = a_c+a_(c+1),
    T_c = E_c(b)+s_c(a),
    D(v) = v(b)+v(a).

Indices are modulo four. Consider nonzero even four-bit masks `v`. Among circuits computing all four `T_c` with at most ten paid gates, the largest possible rank of the `v` for which a physical node of value `D(v)` is present is **exactly two**.

The upper bound is the earlier hand-proved result `L>=11` for the four sheet targets plus three independent diagonal nodes ([Theorem A](../../structure-2026-11-11/joint01/REPORT.md), with its [review corrections](../../structure-2026-11-11/joint01/review/REVIEW.md)). It counts actual diagonal values, not merely virtual linear combinations of available labels. The construction below attains two at the ten-gate local-sheet lower bound. Thus a ten-gate producer cannot supply three independent diagonals, but it can supply two with **no extra gate cost**.

## An optimal event-free producer with two diagonals

Use the free labels `s_0(a),...,s_3(a)` and compute

    p01 = b0+b1,              p23 = b2+b3,
    E1  = p23+b0,             E3  = p01+b2,
    D01 = p01+s0(a),          D23 = p23+s2(a),
    T0  = D01+E1,             T2  = D23+E3,
    T1  = E1+s1(a),           T3  = E3+s3(a).

These are ten gates. For example, `D01+E1` has own mask `(b0+b1)+(b0+b2+b3)=b1+b2+b3=E_0` and free mask `s_0`; the row-2 identity is analogous. The diagonal masks `01` and `23` are distinct and independent. Every gate is event-free: the final uses of `D01` or `D23` combine unequal own-block components and only one operand carries free-block content. The values are distinct non-inputs and every gate serves a designated row or diagonal. A direct evaluation of this one prescribed circuit confirmed all four rows, both diagonals, ten distinct gates, and event-freeness.

This is a counterexample to any proposed statement that one diagonal value already costs an extra gate or that a ten-gate producer can expose at most one independent diagonal. It is also compatible with the three-diagonal lower bound: `D(01)+D(23)=D(0123)` is only a **virtual** third value unless another physical gate is paid, and it is linearly dependent on the first two in any case.

## A single-gate extension cannot complete this particular producer

This observation is narrower than the open 11-versus-12 question. Let a value be written as `(u|v)`, with `u` its `b` mask and `v` its `a` mask, and identify the coordinates to define its defect `delta(u|v)=u+v`. A value is diagonal exactly when its defect is zero. To create a diagonal with one XOR gate, the two available operands must have equal defect.

The non-diagonal physical values of the ten-gate producer have the following defects:

    p01: 01,      p23: 23,
    E1: E1,       E3: E3,
    T0: E1,       T1: E2,       T2: E3,       T3: E0.

Each `b_i` input has a distinct unit defect. Every `a`-only vector is freely available. A single new gate cannot produce a third independent *even* diagonal:

* The only equal nonzero defects between existing non-diagonal paid values are the two displayed pairs: `T0+E1=D01` and `T2+E3=D23`, already present.
* Adding a free `a` vector to an existing value leaves its own mask unchanged. If this produces a new even diagonal, that own mask must be one of `01,23`, already giving `D01,D23`; the other non-diagonal own masks in the construction are triples. The same reasoning covers ordinary input operands, whose own masks have odd weight.
* The two existing zero-defect paid nodes XOR to `D(0123)`, which is dependent on `D01,D23`. Combining one of them with a nonzero-defect value is not diagonal. Zero/free-zero operands only repeat an existing value.

Thus even allowing arbitrary free `a` labels, no **single appended gate** gives the third independent even diagonal. A hypothetical eleven-gate solution must use a different ten-gate precursor or a different interleaving; this is not a proof that all such solutions fail.

## Relation to the eleven-versus-twelve interface

[DIAGONALS.md](../compatibility/DIAGONALS.md) gives an explicit twelve-gate event-free circuit for all four rows and three independent diagonals. It also proves an exact thirteen-gate result if an event-free circuit is additionally required to contain all four pure-own triples. An eleven-gate candidate cannot be ruled out by either restricted argument. The projection/entry-label bound in [QUOTIENT.md](../compatibility/QUOTIENT.md) supplies a separate necessary condition: any eleven-gate circuit for the three-diagonal problem can use only even free labels. Whether that condition can be combined with causality and fibre reuse to exclude eleven remains open.

## Fixed-producer joint consequence: 22 gates

The main agent observed the following stronger consequence, using the one-coset entry restriction of [QUOTIENT.md](../compatibility/QUOTIENT.md); the general fixed-supplier certificate and feedback argument are in [SUPPLY_PROFILE.md](SUPPLY_PROFILE.md). It applies to the specific ten-gate producer above, not to all ten-gate producers. The proof below handles a possible consumer-block-cancelling exit when there is one additional supplier gate.

For the second sheet, let the clean free-side subspace be the three-dimensional even diagonal

    D = {v(b)+v(a) : v has even weight},
    W = span{D01,D23}.

The consumer may read any producer node, any ordinary `b` input, and any free `a`-only vector. For this particular available set:

1. Every available value already in `D` lies in `W`.
2. In **every** coset of `D`, differences of any two available values lie in `W`.

For (2), use the defect table above, remembering that same `D`-coset also requires equal own-part parity. The only equal-defect pairs of existing non-diagonal paid values are `E1,T0` and `E3,T2`, with differences `D01,D23`. A pure-`a` vector can match the defect and own parity of `p01` or `p23`, again giving the respective diagonal; it cannot pair in a `D`-coset with a value of odd own weight. Two different pure-`a` values never differ by a nonzero diagonal. The available diagonal values differ only within `W`. Ordinary `b` units give no additional same-coset pairs. These observations also prove (1).

**Completion-difference deficit.** More generally, suppose an available set has clean values contained in a proper subspace `W<D` and every within-one-coset difference lies in `W`. A collection of available labels contained in `D` plus at most one nonclean `D`-coset cannot span `D`: its intersection with `D` is generated by its clean members and pairwise differences within that nonclean coset, all in `W`. The entry-label projection bound says an eleven-gate four-row consumer uses labels from at most one nonclean coset. Its target free parts span `D`, contradiction. This uses actual available values and does not charge their virtual differences as gates.

Consequently, if no additional zero-consumer-block gate is allowed, this specific producer needs at least twelve consumer-bearing gates. With at least two additional zero-consumer-block gates, the ten-gate consumer lower bound already gives at least 22. The remaining 21-gate boundary has exactly one extra zero-consumer-block gate `g` and ten consumer-bearing gates. The entry projection bound forces every actual consumer entry label to be clean, and the labels must span the three-dimensional `D`.

Before `g`, the only available zero-consumer-block values are in the original producer availability set. Every clean one is in `W`. By induction in gate order, the producer-side part of every earlier consumer-bearing signal is in `W`: consumer inputs have part zero; a gate reading one zero-consumer operand uses a clean entry in `W`; a gate reading two consumer-bearing operands adds two parts already in `W`.

There are two possibilities for `g`. If it reads two zero-consumer-block operands, the single-gate defect argument above shows that any clean value it produces belongs to `W`. If it reads consumer-bearing operands, it must read two with equal nonzero consumer parts; their producer-side parts are both in `W`, so `g` is in `W` too. Thus `g` cannot produce a clean value outside `W`, even if it is a consumer-block-cancelling exit. A nonclean `g` cannot be read as an entry by this ten-gate consumer. Consequently every actual entry lies in `W`, contradicting the rank-three target span.

The fixed-producer joint circuit therefore needs at least 22 gates, including possible feedback. This is a statement about a circuit containing these ten prescribed producer gates and no other initial zero-consumer-block work; it is not a lower bound for an arbitrary ten-gate producer.

An explicit 22-gate completion exists: add `E2=p01+b3` and `D12=T1+E2` to the ten-gate producer. The three available independent diagonal labels are then `d0=D01`, `d1=D12`, and `d2=D23`, with `d3=d0+d1+d2`. For consumer own inputs `z_0,...,z_3`, use the ten-gate circuit

    g = z2+z3,
    h = g+z1,
    U = h+d0,
    V = z0+d1,
    W = z3+d2,
    row0 = U,
    row1 = g+V,
    row2 = (W+z0)+z1,
    row3 = (U+V)+W.

The four rows have own triples `E_0,...,E_3` and free parts `d0,d1,d2,d0+d1+d2`, as required. All operations are event-free at block level. Together with the preceding lower bound, this proves the specified fixed-producer joint optimum is exactly 22, even with feedback.

**Verifier method note.** An initial draft of the fixed-construction verifier represented availability in the four-bit free block by storing its 16 masks. This was membership bookkeeping for one specified circuit, not a circuit search, a family check, or case elimination. The saved [verifier](check_exports.py) instead uses a direct bit-mask test and directly checks only the displayed ten- and 22-gate constructions.
