# Four rows with three diagonal exports

2026-11-13. Symbolic constructions and hand proofs only; no SAT, enumeration, exact-gate search, or computer-driven case elimination. The general question remains open: the existing lower bound is 11 and the explicit upper bound is 12. Nothing here proves that 11 is impossible or changes an unrestricted MixColumns bound.

## Setup

Let `b_0,...,b_3` be ordinary inputs and let every vector on a separate four-coordinate block `a` be free. Write

    E_c(b) = sum_{d != c} b_d,
    s_c(a) = a_c+a_(c+1),
    T_c = E_c(b) + s_c(a).

The circuit must contain all four `T_c` and three independent diagonal values

    D(v) = v(b)+v(a),

where each `v` is a nonzero even four-bit vector. Both target and diagonal nodes count as paid gates. Whole-block events are allowed in the general problem. The earlier [hand proof](../../structure-2026-11-11/joint01/REPORT.md) and its [corrected review](../../structure-2026-11-11/joint01/review/REVIEW.md) give `11<=L<=12`.

## Explicit event-free 12-gate circuit

The following direct construction attains 12, with the independent diagonal masks `01`, `23`, and `12`. Here, for example, `01` means the sum of coordinates 0 and 1, and all free `a`-side sums are available at no cost.

    1   p01 = b0+b1
    2   p23 = b2+b3
    3   E1  = p23+b0
    4   E2  = p01+b3
    5   E3  = p01+b2
    6   T1  = E1+s1(a)
    7   T2  = E2+s2(a)
    8   T3  = E3+s3(a)
    9   D01 = p01+s0(a)
    10  D23 = p23+s2(a)
    11  D12 = T1+E2
    12  T0  = D01+E1

Indeed `E1+E2=b1+b2` and `p01+E1=b1+b2+b3`; the free parts of the last two gates are `s1` and `s0`, respectively. Thus gate 11 is `D(12)` and gate 12 is `T0`. The three masks `01,23,12` are independent: the first two sum to `0123`, and the third is neither of them nor their sum.

No gate cancels a whole nonzero block. In gates 11 and 12, the two nonzero `b`-parts are unequal and the `a`-part belongs to only one operand; all other gates add an input or an absent block. All twelve values are distinct and every gate is live. A direct evaluation of this one specified circuit verified the four rows, the three diagonal masks, and event-freeness; it is not a search.

The two final gates demonstrate useful export/row sharing: a mixed row and a clean triple produce a diagonal, while a diagonal and a clean triple produce another row. A counting argument that assigns a separate auxiliary gate to every such service would be false.

## An exact clean-interface obstruction

Add the hypothesis that the circuit is event-free **and** contains all four pure-own values `E_c(b)` as nodes. Under this hypothesis the minimum is exactly **13**, even though the unconstrained event-free construction above uses 12.

For the lower bound, support can only grow along event-free edges. Every ancestor of a pure-own `E_c(b)` therefore avoids block `a`, so these four values require an ordinary four-input circuit for the four triples entirely inside block `b`. That subcircuit needs at least six gates: the standard hand proof observes that its four triple outputs are odd-weight values and at least two further gates are needed to generate them. These six pure-own gates are distinct from the seven required mixed nodes: each `T_c` has nonzero `a`-part and each independent diagonal has nonzero `a`-part. Thus there are at least `6+7=13` gates.

For equality, compute `p01,p23` and all four clean `E_c` in six gates. Compute the four rows `T_c=E_c+s_c(a)` in four more. Finally compute

    D01 = p01+s0(a),
    D23 = p23+s2(a),
    D12 = T1+E2.

These thirteen gates are event-free, and the diagonal masks are independent. Hence the restricted bound is exact.

**Implication.** Any event-free 11- or 12-gate solution must avoid providing the complete clean-triple interface. This does not establish a lower bound of 12 for unrestricted circuits: a circuit with whole-block cancellation can generate pure-own nodes from mixed ancestors, so the six-gate disjoint-subcircuit argument would need additional justification there.

## Entry-label restriction on a hypothetical 11

The following consequence of the projection argument is useful without enumerating candidate circuits. Let `D` be the even subspace of the free `a` block. Every required row and diagonal has its `a` component in `D`. Normalize away paid nodes whose values are entirely free, so each remaining paid gate has at most one free operand. Let `U` be the span of the actual free operands used, and put

    q = dim((U+D)/D).

Choose `q` actual entry labels whose classes form a quotient basis. A linear projection of the `a` block onto `D` can fix `D` pointwise and kill those chosen labels. Each corresponding physical entry gate becomes a wire after projection. Reusing equal projected values and pruning yields a circuit with all required rows and diagonal values and at most `K-q` gates, with only vectors of `D` used as free operands. Hence `K >= L_D+q`, where `L_D` is the minimum for the same targets with only `D` available free.

Since restricting the free set cannot lower the known 11-gate lower bound, any 11-gate solution must have `q=0`: **every actually used free label is even**. This conclusion applies to all designated diagonal nodes, even if they are not ancestors of the four rows. It does not say that even labels suffice for an 11-gate circuit, and it is not a proof of `L>=12`.

## Remaining gap

The explicit 12-gate witness leaves the exact 11-versus-12 question unresolved. The 13-gate clean-interface result explains why simply producing all four own triples and then exporting diagonals cannot attain 12. The entry-label restriction narrows any hypothetical 11-gate circuit to even free operands, but a further causal or fibre-sharing argument is needed to exclude it or construct it.

The [independent review](reviews/diagonals-review.md) checks the proof and its scope.
Both displayed constructions are evaluated by [the direct checker](check_compatibility.py).
