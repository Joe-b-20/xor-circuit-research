# Shared hidden operands across maximal windows

Two explicit constructions show why one cannot add the separate hidden-operand lower bounds for different maximal output windows. The first is a five-gate **reduced** circuit. The second computes all 32 MixColumns outputs and has the same overlap. Its direct form has duplicates; the specified deterministic normalization gives a reduced 156-gate witness. It is not a competitive circuit. Both are direct symbolic constructions. No search, enumeration, or exact least-gate procedure is used.

## A reduced five-gate counterexample

Use three input blocks `B={x}`, `C={y}`, `D={p,q}`. Compute, in order,

    u = x+p,
    v = y+q,
    a = u+v = x+y+p+q,
    f = a+y = x+p+q,
    g = a+x = y+p+q.

Designate the four outputs `u,v,f,g`. Their output windows are exactly

    W={B,D},     W'={C,D}.

These are distinct maximal cliques in the co-occurrence graph; `B,C` do not co-occur in any window. The five gate values are distinct, nonzero, and distinct from the inputs; all five gates are live. Thus this is a reduced circuit in the usual sense.

The gates `f,g` are events: `f` cancels the whole `C` block and `g` cancels the whole `B` block. The gate `a` is not an event: on block `D` its two operands contain the unequal nonzero vectors `p,q`. Its support `{B,C,D}` is in no output window. Its only readers are the events `f,g`, so it is hidden. Gates `u,v` and the events `f,g` are designated outputs, hence visible. Therefore the entire hidden set is `{a}`.

The separate HR application to the output `f` forces one hidden operand for `W`; the application to `g` forces one for `W'`. Both counted operand sets are exactly `{a}`. Summing the two single-window lower bounds would incorrectly assert at least two hidden gates, whereas there is exactly one. This refutes naive additivity even for reduced circuits and even when the local partners of both selected events are coordinate inputs.

As a control, the same four outputs have an event-free four-gate circuit `u=x+p`, `v=y+q`, `f=u+q`, `g=v+p`. The counterexample is about overlap of the counted sets, not a claim that cancellation saves gates.

## The same phenomenon for two MixColumns sheets

This is a complete circuit construction for the actual MixColumns map, exhibiting just **one** hidden gate that is an operand of an output event in each of sheets 3 and 4. The direct construction uses duplicate values, but the specified normalization below gives a reduced witness with the same single hidden gate.

Write `x_{d,i}` for coordinate `i` of block `d`, with indices modulo 4, and define

    E_d(c) = sum of x_{d,i} for i != c,
    s_d(c) = x_{d,c} + x_{d,c+1}.

The relevant MixColumns output rows are

    F_c = s_2(c) + E_3(c) + s_7(c),       sheet 3,
    G_c = s_3(c) + E_4(c) + s_7(c),       sheet 4.

Build the following gates and values in this order. `U` and `V` are computed directly from their six distinct coordinate inputs by chains, with the block-7 input added as the second step:

    U = s_2(0) + x_{7,0} + E_3(0),
    V = s_3(0) + x_{7,1} + E_4(0),
    a = U+V,
    b = V+x_{7,1} = s_3(0)+E_4(0),
    c = U+x_{7,0} = s_2(0)+E_3(0),
    F_0 = a+b,
    G_0 = a+c.

The two last equalities hold because `a+b=U+x_{7,1}` and `a+c=V+x_{7,0}`. They are events: `F_0` cancels block 4, and `G_0` cancels block 2. The operands `b,c` are also events, cancelling block 7, but their values are local to windows `W_4={3,4,7}` and `W_3={2,3,7}` respectively.

The support of `a` contains blocks 2 and 4, which no output window contains together, so `a` is nonlocal. To ensure every other gate is visible, give each of `U,c,V,b` a separate event-free continuation to a designated output as follows:

    U -> F_1,    c -> F_2,    V -> G_1,    b -> G_2.

For each continuation, alter the block components to those of its target by XORing missing target coordinate inputs first and then XORing superfluous coordinate inputs. Every target component is nonzero, so no block ever disappears under this order. Each continuation is event-free, lies within the appropriate output window, and computes the indicated target. Explicitly, the four continuations need 7, 8, 5, and 8 gates, respectively.

Compute all remaining 26 output rows directly as independent chains adding the row's distinct input coordinates. Each such chain is event-free and local. All gates before `U` and `V` have event-free continuations through `U` or `V` to the four outputs above. Gates `b,c` have their own event-free continuations to outputs, and `F_0,G_0` are outputs. Every gate in the direct chains is also on an event-free path to its output. The only readers of `a` are `F_0,G_0`, both events, so `a` is hidden and is the **only** hidden gate. Its nonlocal-operand sets for `F_0` and `G_0` are both exactly `{a}`.

The construction has 159 physical gates: 10 in the `U,V` chains, five for `a,b,c,F_0,G_0`, 28 in the four continuations, and 116 in the 26 independent direct chains (six weight-7 rows and twenty weight-5 rows). A direct evaluation of this specified construction checked all 32 output masks, the 159-gate count, and the unique hidden gate. Its duplicate gate values are intentional in this initial form. Arbitrary duplicate reuse could change which physical gates are visible; the particular normalization below was checked explicitly.

## Scope

The overlap example leaves all single-window results intact. It disproves a general claim that distinct maximal windows automatically require disjoint hidden gates. A stronger result for small MixColumns circuits would need an additional compatibility or cost argument; the reduced 156-gate construction does not rule one out. The two selected output events above are accompanied by other visible events, and no statement about the exact-visible-set class bounds is contradicted.

## A reduced 156-gate MixColumns witness

The direct construction is reproducible with a fixed order: in each continuation process blocks in increasing order; within each block add missing coordinates in increasing index order, then remove extra coordinates in increasing index order. Compute the remaining rows by sheet index then row index, adding their coordinate inputs in increasing global index `4*d+i`.

Now scan the resulting gates in original topological order, redirecting a gate to the earliest input or earlier gate of the same value when one exists; redirect its readers and the designated outputs accordingly. Then delete gates with no path to an output. This is a single specified normalization of the displayed construction, not a search or a case elimination. The deterministic [direct mask and reachability check](check_overlap.py) gives **156 live gates**, all with distinct non-input values, with both designated row-0 output gates still events and exactly one hidden gate. That gate is the common nonlocal operand `a` of both events. All 32 output masks remain correct because only equal values were merged.

Thus even for a reduced circuit computing the actual MixColumns map, the two maximal-window one-event hidden bounds can refer to the very same physical gate. The witness has 156 gates, so it does not rule out a new overlap bound for much smaller circuits.

## Affine-completion control

For the MixColumns witness, let `K=span{F_0,G_0}`. The local vectors in `a+K` include `b=a+F_0`, `c=a+G_0`, and `s_7(0)=a+F_0+G_0`. Their differences include both `F_0` and `G_0`, so the span of differences of all geometrically local completions is all of `K`. Consequently the affine-completion quotient using every geometrically possible local completion has rank zero on this witness, even though its hidden count is one. This does not contradict the quotient inequality; it identifies a case where stronger eligibility conditions would be needed to recover the one-gate lower bound.
