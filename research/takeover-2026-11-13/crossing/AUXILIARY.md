# Two non-cycle diagonals require more than one mixed auxiliary

2026-11-13. Hand argument; no SAT, enumeration, exact-gate search, or computer-driven case elimination. This gives a necessary condition for a restricted eleven-gate augmented interface; it does not settle the general 11-versus-12 problem.

## Statement

Use the augmented-sheet model of [AUGMENTED](../frontier/AUGMENTED.md): ordinary inputs `b_0,...,b_3`, an independent free four-coordinate block `a`, four required rows

    T_c = E_c(b)+s_c(a),

and three required independent even diagonals `D(v)=v(b)+v(a)`. A value is *mixed* if it is nonzero on both blocks.

Assume the circuit is reduced and event-free, and every required diagonal is an ancestor of at least one required row. If at least two of the diagonal masks are not among the four cycle pairs `s_0,...,s_3`, then the circuit cannot have exactly one mixed gate `H` besides the seven required mixed nodes. The earlier no-mixed-auxiliary lower bound also excludes zero such gates at total size 11. Thus an event-free eleven-gate candidate in this profile must have **at least two mixed auxiliary gates**.

For a normalized hypothetical eleven-gate circuit, the recently established ten-gate producer confinement makes the diagonal-ancestry condition necessary: if one designated diagonal were outside the row cones, deleting it would leave a ten-gate row producer already containing the other two independent diagonals, and its available values could not acquire the third independent diagonal with one additional gate. See [ODD_CLOSURE](ODD_CLOSURE.md#the-remaining-eleven-gate-core). The present lemma is conditional on that separately proved fact; it does not re-prove it. The restricted [AUGMENTED theorem](../frontier/AUGMENTED.md) also implies that an event-free eleven-gate candidate needs at least one mixed auxiliary. This note concerns the subcase in which there is exactly one.

## Independence and a one-service fact

Write `I` for the identity, `J` for the all-ones four-by-four matrix, and `P e_c=e_(c+1)` for the cyclic shift. The seven required values are linearly independent. Indeed, if a linear combination of rows with coefficient vector `u` plus a diagonal combination `D(v)` vanishes, its own and free components give

    (I+J)u + v = 0,          (I+P)u + v = 0.

Subtracting yields `(J+P)u=(I+J)P u=0`. Both `I+J` and the cyclic shift `P` are invertible, so `u=0`, and then independence of the three diagonal masks gives `v=0`.

Consequently a fixed distinct mixed auxiliary `H` can be paired with a required node to produce at most **one** required node. If two such gates existed, their equations would give two representations of `H` as XORs of two required values. Independence makes the unordered pairs identical. The only way the two distinct gates could then use that same pair would be in opposite directions, a causal cycle. This is the physical one-service fact; it does not count a virtual sum as an available gate.

## Proof of the causal restriction

Let `X=D(v)` and `Y=D(w)` be two required non-cycle diagonals. Their masks lie among `02,13,0123`, the three nonzero vectors of one two-dimensional subspace; consequently `v+w` is another non-cycle mask. Their free parts are each unique among the seven required values.

By event-freeness, every path from either mixed node to a row remains in mixed nodes. The only mixed nodes are the seven required values and `H`. The next node after `X` or `Y` cannot be a required target with a pure-`b` or free-`a` other operand: a pure-`b` operand preserves its unique free part, while a free operand preserves its own mask, and no other required target matches the preserved component. Nor can it be the sum of two required nodes, by independence. Thus each of `X,Y` must either be a direct operand of `H`, or be a direct operand of a required gate whose other operand is `H`—a **service** by `H`. The one-service fact above allows at most one such service gate.

If `H` has no required mixed operand, both `X,Y` would need a service, impossible.

If `H` has two required mixed operands `R,S`, then it has no service: an equation `H+R'=S'` with required nodes would, by their independence, use the same unordered pair `{R,S}` and would require an already earlier parent to be recomputed from the later `H`, a causal cycle. Both `X,Y` must therefore be the two parents of `H`, so `H=X+Y=D(v+w)`. Its mask is non-cycle and is not the third required diagonal mask, because the three diagonal masks are independent. `H` cannot reach a required row by adding a pure-`b` value, since its free part is non-cycle; it cannot reach a required diagonal that way, since no required diagonal has free part `v+w`. Adding a free-`a` value preserves its even own mask `v+w`, which is neither a row's odd triple nor a required diagonal's own mask. Adding a required mixed value cannot yield a new required target because there is no service. Event-freeness leaves no path from `H` to a row, contradicting the ancestry of `X,Y`.

Finally suppose `H` has exactly one required mixed operand `R`; its other operand `p` is pure-`b` or free-`a`. If `R` is neither `X` nor `Y`, both would need a service, impossible. If `R=X`, then `Y` must have a service, so some required target `Q` satisfies `Q=H+Y` and therefore

    X + Y + Q = p.

The result `Q` is distinct from `X,Y` by order and reducedness. If `Q` is a row, the left side has odd nonzero own part, and its free part is `v+w+s_c`, nonzero because `v+w` is non-cycle. If `Q` is a diagonal, the three required diagonals are independent, so the left side is a nonzero diagonal with content on both blocks. In either case it is mixed and cannot equal pure `p`. The case `R=Y` is symmetric. This exhausts the possible operands of `H` and proves the claim.

## Why one non-cycle diagonal is not excluded by this reasoning

The following six gates are a partial event-free circuit showing that a non-cycle diagonal can reach a required row through a source-entry auxiliary:

    p01 = b0+b1,
    E2  = p01+b3,
    p02 = b0+b2,
    D02 = p02+(a0+a2),
    H   = E2+(a1+a2),
    T0  = H+D02.

Indeed `H+D02` has own mask `E_0` and free mask `s_0`. No whole block is cancelled. Here `H` has only pure-`b` and free-`a` operands, and `D02` is an ancestor of `T0`. This partial example is not a complete eleven-gate augmented circuit; it only shows why the causal argument above cannot replace “at least two” by “at least one” without additional hypotheses.

## Scope

The result is a causal branch restriction, not a general gate lower bound beyond the known 11. It leaves open one-mixed-auxiliary candidates with zero or one non-cycle diagonal, candidates with more mixed auxiliaries, and circuits containing whole-block events. It does not assert a new joint or unrestricted MixColumns bound.
