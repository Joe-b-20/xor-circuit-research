# Diagonal confinement with arbitrary consumer budget

2026-11-13. These deductions use source replay and the existing hand-proved supplier bounds. They permit arbitrary feedback and do not use circuit search.

Let `a` be a free four-coordinate block, `b` an ordinary source block, and `z` an ordinary consumer block. The required rows are

    U_c = E_c(b) + s_c(a),
    Y_c = E_c(z) + s_c(b) + s_c(a).

Here each `s_c` is even and the four source parts of the `Y_c` span the three-dimensional diagonal space

    D = { v(b) + v(a) : v has even parity }.

Count all physical gates with zero `z` part as `G_0` and those with nonzero `z` part as `K`. An **actual entry label** is the full value of a zero-`z` operand read by a nonzero-`z` gate. Zero and all values supported only on `a` are free.

## All-clean entries

**Theorem.** If every actual entry label belongs to `D`, then `G_0 >= 12`, with no restriction on `K`. This bound is sharp: the [recorded 22-gate circuit](../augmented/CONSEQUENCES.md#the-joint-two-sheet-problem) has twelve source gates, ten consumer gates, and entries in `D`.

Indeed, by induction through the nonzero-`z` gates, each of their source parts is in the span of earlier actual entry labels. The `Y_c` source parts span `D`, so those labels span `D`. Each nonzero diagonal label is neither a source coordinate input nor wholly free; it is physically supplied by a source gate.

Suppose `G_0 <= 11`. Apply [Theorem R3](RANK_THREE.md) to replay source values without the consumer. The replay preserves every original zero-`z` value, including the four `U_c` and a basis of three physical values in `D`, and uses at most `G_0+1` gates. If no exceptional two-gate replacement is needed, it uses at most eleven gates, contradicting the [augmented supplier lower bound A12](../augmented/PROOF.md).

Otherwise, at the exceptional step three independent physical values `u,v,w` in `D` are available and the exit value is `u+v+w`. The replay adds, for example, `u+v` and then `u+v+w`. These two values and `u,v,w` are five distinct nonzero members of `D`, all retained in the completed replay. It uses at most twelve gates and supplies all four `U_c`, contradicting the [five-diagonal lower bound](FIVE_DIAGONALS.md), which requires thirteen. Thus `G_0 >= 12`.

This reasoning uses no bound on consumer gates and allows source values used in `U_c` to be obtained through consumer feedback. The local sheet lower bound `K >= 10` gives total size at least 22 in the all-clean class.

## A parity projection

Identify the coordinate masks of `a` and `b`. Suppose every actual entry belongs to

    D + span{h},     h = beta(b) + alpha(a),

where `beta` has even parity and `alpha` has odd parity. Define the odd mask `sigma = alpha + beta` and the linear map on `a` masks

    P(x) = x + parity(x) sigma.

The map fixes every even mask and sends `alpha` to `beta`; hence it fixes `D` and sends `h` to `beta(b)+beta(a)` in `D`. Apply `P` to the `a` component of every input, gate value, and operand, retaining the original wiring. It is a valid XOR computation: a projected free `a` value is still free, and `b,z` inputs are unchanged. Every required output is unchanged because its `a` component is even. The `z` part of every physical gate is unchanged, while every actual entry label now belongs to `D`. Any projected zero, free, or duplicate values may be bypassed; this cannot increase the source gate count. Applying the theorem to the projected circuit therefore gives **`G_0 >= 12` in the original circuit**.

In particular, the original total is at least `22` for any `K`, and at least **23 when `K=11`**. For `K=11`, the [entry-deletion bound](../compatibility/QUOTIENT.md) confines the actual entry span modulo `D` to dimension at most one; this projection handles the indicated parity class of its possible nonclean direction, as well as the already-clean case. It does not eliminate other nonclean directions or establish an unrestricted lower bound of 22.

More generally, the same conclusion holds whenever a linear transformation of the source coordinates fixes every required output and the consumer coordinates, maps every actual entry label into `D`, maps every ordinary input to an available input or free value and every available free input to an available free value, and does not increase the number of source gates. The displayed retraction provides one concrete sufficient condition.
