# A sharp joint lower bound on hidden operands

Independent research direction, 2026-11-13. This is a hand argument, independently machine-reviewed in `../reviews/hidden-review.md` and `../reviews/hidden-second-review.md`; it is not formal verification or human certification. No search, enumeration, or computer-driven case elimination was used. It does not change the published statement `75 <= L(MixColumns) <= 88`. The result is a bound for specified event profiles, not a claim that 88 is optimal.

## The issue resolved

The previous window credit guarantees a hidden operand for certain visible events, but the same operand may be credited repeatedly. The theorem below controls that reuse jointly. It uses independence of the **event values**, not ranks of the components cancelled at those events. This distinction is essential: the quadratic-capacity construction in `copies/COPIES.md` has many independent cancellation copies but dependent pair-sum event values.

The main results are a sharp operand-forest bound and a componentwise projected-rank bound. For one, two, three, or four visible output events from any one of the six maximal-window MixColumns sheets, they force at least one, two, three, or three **distinct nonlocal operand gates**, respectively. Those gates are all hidden in the sense of `visible/VISIBLE.md`. The previous individual window credit by itself supplies only one distinct gate, however many of those events it is applied to.

## Definitions

Fix a partition of the input coordinates into blocks and a family of output windows `W_i`. Every designated output is supported inside its assigned window. The block support of a value `v` is `B(v)`.

A value is **local** if its block support is contained in some output window. Otherwise it is **nonlocal**. This definition concerns the value, not its ancestry. Include a singleton window for any input block not otherwise covered. This changes no co-occurrence edge and ensures that every nonlocal operand is a gate, rather than an input.

The co-occurrence graph joins two different blocks exactly when some output window contains both. Let `W` be an output window that is also a maximal clique of this graph.

Let `T` be a selected set of event gates. Assume:

1. Every selected gate has block support exactly `W`.
2. The selected gate values are linearly independent over `F_2`.
3. For every block `d` of `W`, the projections onto `d` of the selected values are pairwise distinct.

An event is a gate whose operands have the same nonzero component on at least one block, which disappears in their sum. The selected gates need not be outputs, and need not be visible for the combinatorial theorem. When they are visible, every nonlocal gate is hidden by Lemma S of `visible/VISIBLE.md`.

Let `t=|T|`. Let `A` be the set of distinct nonlocal operand nodes used by the selected event gates, and put `h=|A|`. Form the undirected loopless multigraph `K` with vertex set `A`, putting one labelled edge for each selected physical event whose two operands belong to `A`. Parallel edges, if allowed in a later generalization, count separately and form two-edge cycles. Include isolated vertices, and write `c` for the number of connected components of `K`. The stated distinctness assumptions already exclude parallel edges, but this convention also covers the general capacity extension below.

## Theorem H

Under these assumptions,

    t <= 2h - c.

In particular, if `t>0`,

    h >= ceil((t+1)/2).

All counts are of physical nodes and gates. Distinct target values ensure that a selected edge cannot be repeated with the same operand pair.

### Proof, part 1: every selected event has a nonlocal operand

Take a selected event `f=a+b` and a block `q` cancelled at it. Since the support of `f` is exactly `W`, `q` lies outside `W`. Maximality of the clique `W` implies that some `d in W` is not adjacent to `q`; otherwise `W union {q}` would be a larger clique.

Both operands contain `q`. At least one operand contains `d`, because `f` does. That operand meets two blocks which no output window contains together. It is nonlocal. Consequently every selected event corresponds either to an edge of `K` or to a pair consisting of one node of `A` and one local operand.

### Proof, part 2: a nonlocal operand has at most one local-partner event

Fix `a in A`. Since `W` itself is an output window and `a` is nonlocal, choose `q in B(a) \ W`. Again choose `d in W` not adjacent to `q`.

If a selected event has value `f=a+b` with `b` local, then `f` vanishes on `q`, so `b` contains `q`. Because `b` is local, it cannot contain `d`. Hence

    projection_d(f) = projection_d(a).

The right side is fixed. Assumption 3 allows at most one selected value with this projection. Therefore each node of `A` is used by at most one selected event with a local partner. There are at most `h` such events.

This is a joint reuse statement. It does not assign a private payment to every event: a nonlocal gate may still be an operand in several events with other nonlocal operands.

### Proof, part 3: independent event values force a forest

The edge corresponding to a selected event with operands `a,b in A` has vector label `val(a)+val(b)`, namely the event value. Around any undirected cycle, the sum of the edge labels is zero, since every vertex value occurs twice.

Assumption 2 excludes every such cycle. Thus `K` is a forest and has `h-c` edges. Adding the at most `h` local-partner events proves `t <= (h-c)+h`.

For `t>0`, part 1 gives `h>0`, so `c>=1`, proving the stated rounded bound. QED.

## Rank-defect form

The same argument can retain linear dependencies rather than discarding the theorem. Omit assumption 2, let `r` be the rank of the selected event values and `nu=t-r`, and retain assumptions 1 and 3. Then

    t <= 2h - c + nu,
    equivalently r <= 2h - c.

Indeed, if `m` is the number of nonlocal/nonlocal edges, the cycle space of `K` has dimension `m-h+c`. Extending an edge-cycle coefficient vector by zeros on all other selected events embeds this cycle space into the kernel of the linear map sending selected-event coordinates to their values. Consequently `m-h+c <= nu`. The local-partner count is still at most `h`.

The full-rank statement is stronger when the actual number of selected events matters. The rank-defect form identifies the precise obstruction: cycles among shared operands require dependencies among the event values. It does not charge a copy rank to the operand gates.

More generally, if a different argument bounds the number of selected local-partner events at each nonlocal operand by `lambda`, the same proof gives

    t <= (lambda+1)h - c + nu.

The separation and blockwise-distinctness argument above supplies `lambda=1` without any enumeration.

## Theorem HR: hidden work from a component's separated projections

There is another bound that needs neither event-value independence nor blockwise projection distinctness. Retain only the assumption that every selected event has support exactly the same maximal-clique output window `W`.

Every selected event has a nonlocal operand, by part 1 of Theorem H. Build its nonlocal-operand multigraph `K` as before. Assign each selected event to the component containing its nonlocal operand; an event with two nonlocal operands gives an edge, so its two operands belong to the same component. Write `A_i` for a component's vertex set, `h_i=|A_i|`, and `T_i` for its assigned events. The sets `T_i` partition `T`.

All nonlocal values in component `i` have an identical projection `z_i` outside `W`: their difference along an edge is the selected event value, which is supported inside `W`. Moreover `z_i` is nonzero, since a nonlocal value cannot be supported inside the output window `W`.

Define the separated blocks of this component by

    D_i = { d in W : some q in B(z_i) is not adjacent to d }.

Maximality of the clique `W` gives `D_i` nonempty. Then

    h_i >= rank { projection_(D_i)(val(f)) : f in T_i },

and, summing distinct physical vertices,

    h >= sum_i rank { projection_(D_i)(val(f)) : f in T_i }.       (HR)

**Proof.** If an event assigned to component `i` has a local partner `b`, then the event vanishes outside `W`, so the outside-`W` projection of `b` is `z_i`. Hence `b` contains every block `q` in `B(z_i)`. Locality forces `b` to vanish on every `d in D_i`, since no output window contains such a `d` together with its incompatible `q`.

Consequently the `D_i`-projection of each assigned event is either the projection of its one nonlocal operand, or the sum of the projections of its two nonlocal operands. All these event projections lie in the span of the `h_i` projected physical vertex values. Its dimension is at most `h_i`. This proves the component bound, and the component vertex sets are disjoint, proving the sum. QED.

This rank is not a rank of available values modulo inputs, nor a rank of cancelled copies. The proof first makes all local partners vanish on the selected coordinates. The only remaining sources for the selected projected event values are the actual nonlocal operand gates in the component. Thus inputs and retained local gates do not form an uncharged spanning baseline on those coordinates.

The coordinate set `D_i` may contain several blocks; taking their joint projection can be stronger than taking the maximum of the individual block ranks. The estimate is determined by the actual component and selected values, with no optimal subcircuit or search over completions as an oracle.

## Sharpness as a hidden-work theorem

The factor two and the component correction are attained by a family with exactly `h` hidden gates, not merely by an abstract labelled graph.

Fix any integer `h>=1` and any tree on vertices `1,...,h`. Use three input blocks:

* `B` has independent coordinates `u_1,...,u_h`.
* `D` has independent coordinates `v_1,...,v_h,z_1,...,z_h`.
* `C` has the coordinate `q`.

Compute and designate as outputs the local values

    l_i = q + v_i,
    b_i = q + z_i.

Compute the `h` nonlocal gates

    a_i = l_i + u_i = q + v_i + u_i.

The selected output events are

    y_i  = a_i + b_i = u_i + v_i + z_i,               i=1,...,h,
    y_ij = a_i + a_j = u_i + u_j + v_i + v_j,         ij an edge of the tree.

There are `t=2h-1` selected events. Every one cancels block `C`. The output windows are exactly `W={B,D}` and `U={C,D}`, so `W` is a maximal clique and `B,C` do not co-occur. The only nonlocal gates are the `a_i`; every path from one to an output passes through a selected event. Hence there are exactly `h` hidden gates and no hidden events. The local gates `l_i,b_i` are retained because they are designated outputs.

The hypotheses hold:

* Every selected value has support exactly `W`.
* The block-`B` projections are the distinct units `u_i` and distinct tree-edge sums `u_i+u_j`; none coincide.
* The block-`D` projections are the distinct `v_i+z_i` and distinct `v_i+v_j`; none coincide.
* In a relation among selected values, the coordinate `z_i` first forces the coefficient of `y_i` to vanish. The remaining relation among tree-edge vectors `u_i+u_j` is zero only with all coefficients zero, by deleting a leaf successively. Thus all selected values are independent.

The graph `K` is the prescribed tree, so `c=1` and equality `t=2h-c` holds. For `h=1` the tree is the single isolated vertex and the same statement holds.

Replacing the tree by any forest with `c` components preserves the proof: use its `h-c`
edges and the same `h` one-local events. Leaf deletion works separately in each component,
and `t=2h-c`. Thus the component correction, as well as the factor two, is sharp.

The construction is a symbolic family verified by these displayed identities. No finite-family test is needed. It shows that stronger universal hidden-work constants need additional features of MixColumns or its output family.

## MixColumns consequence

The six windows

    W_1={0,1,7}, W_3={2,3,7}, W_4={3,4,7},
    W_5={4,5},   W_6={5,6},   W_7={6,7}

are maximal cliques of the co-occurrence graph, as established by the hand argument in `visible/VISIBLE.md` section 4.1.

In one sheet, the four row values have own-block components `E_c`, the sum of the three coordinates other than `c`, and components `s_c=e_c+e_(c+1)` on each other block of the window. Both lists consist of four distinct nonzero vectors, giving assumption 3.

The four `E_c` are linearly independent. Their matrix is `I+J`, with `J` the all-ones `4 x 4` matrix; over `F_2`, `J^2=4J=0`, so `(I+J)^2=I`. Consequently any selected subset of the four rows is independent already on its own-block projection.

Therefore, if `1<=t<=4` of the four designated outputs of any one of sheets `1,3,4,5,6,7` are event gates, the circuit has at least

    ceil((t+1)/2)

distinct nonlocal gates used as their operands. In particular, **four such output events force at least three hidden gates**.

These output events are visible by their trivial paths to themselves, and every nonlocal operand is in `Q` or `E\F`: a nonlocal gate cannot reach any designated output along a path containing no later event. Other visible events and any number of hidden events are permitted. The bound is on the hidden gates for the entire circuit and must not be added independently for different sheets without controlling overlap between their operand sets.

The theorem does not apply automatically to sheets 0 and 2, whose windows are not maximal cliques. No claim about these two sheets is made here.

### The component ranks give the stronger hidden-work profile

For one MixColumns sheet, every proper subset of its four rows is linearly independent on every window block. On the own block all four `E_c` are independent. On every other block, the four `s_c` are the edge vectors of a four-cycle: their only nonzero relation is the sum of all four, since at each coordinate the two incident-edge coefficients must agree. Thus any subset of `k<4` has rank `k` on every block, and all four have rank at least three on every block.

Apply Theorem HR. For any component receiving fewer than four selected output rows, projection onto its nonempty `D_i` has rank exactly the number assigned: already any one block of `D_i` gives that rank. The vertex sets of different components are disjoint. Therefore

    t:                 1  2  3  4
    hidden gates >=:   1  2  3  3.

For `t=4`, if the selected events are assigned to more than one component, every component receives a proper subset and the lower bound is four. It is also four if the sole component's `D_i` contains the own block. Thus the possible three-gate case requires one nonlocal-operand component, and all its separated coordinates must be off the own block.

This refinement uses the ranks of the projected MixColumns rows. It does not contradict the general sharpness family: in that family the separated block is `B`, and the `2h-1` target projections have rank exactly `h`. Hence Theorem HR is also attained by the displayed family.

## Combination with joint reconstruction

Assume a reduced MixColumns circuit whose complete visible-event set `F` consists of `t` designated output gates of one of the six maximal-window sheets, with `1<=t<=4`. Hidden events are unrestricted. The preceding theorem supplies

    H = |E\F| + |Q| >= h_t,
    (h_1,h_2,h_3,h_4) = (1,2,3,3).

The companion `JOINT.md` supplies the shared-piece accounting. Any two different own-block triples `E_c,E_d` have a common pair of inputs. Computing this pair once and adding the two remaining inputs takes three gates instead of four. Pair the selected triples, leaving one unpaired if `t` is odd. This explicit construction gives

    Delta_83 >= floor(t/2),
    Delta_84 >= floor(t/2).

The original penalties from `visible/VISIBLE.md` are `kappa=2` for these output events except on sheet 3, where `kappa=3`. A sheet-1 output is a borrower with `x=2`; all other listed sheets have `x=0`. Thus, using the better of the 83 and 84 forms:

    sheet 1:             G >= 83 - 2t + h_t + floor(t/2),
    sheet 3:             G >= 84 - 3t + h_t + floor(t/2),
    sheets 4, 5, 6, 7:   G >= 84 - 2t + h_t + floor(t/2).

| Sole visible sheet | `t=1` | `t=2` | `t=3` | `t=4` |
|---|---:|---:|---:|---:|
| 1 | `G>=82` | `G>=82` | `G>=81` | `G>=80` |
| 3 | `G>=82` | `G>=81` | `G>=79` | `G>=77` |
| 4, 5, 6, 7 | `G>=83` | `G>=83` | `G>=82` | `G>=81` |

There is a small descendant-set point in applying these penalties. If an output of sheet `j` reaches another sheet by an event-free continuation, its full support `W_j` must lie in that other sheet's window. Maximality of `W_j` excludes a strict enlargement, and the eight MixColumns windows are distinct. Hence each selected output event has `J(f)={j}`, exactly the descendant set used in the displayed penalties.

These are conditional class bounds. They leave the unrestricted published interval unchanged, and are not evidence that a circuit meeting any of these bounds exists.

## Limits and comparison with the historical failures

* This proves a lower bound on hidden work, whereas Theorem V and its private chains constrain only the retained part.
* The proof handles all selected events together. It does not assume one private operand per event and does not charge each cancellation component separately.
* It uses a physical operand graph, block separation, and event-value independence. A single hidden gate may still be reused with many hidden partners; those pairings form a forest in the independent-target case.
* It does not prove that arbitrary visible-event collections have independent values or blockwise distinct projections. Internal visible values can violate either property.
* Applying the theorem separately to many sheets can reuse the same hidden gates. No multi-sheet sum is asserted.
* For all 32 outputs visible, a global conclusion stronger than the separate per-sheet bounds needs a bound on how one nonlocal operand can serve several sheets. That question remains open here; no guessed global capacity is used.
* The sharpness family rules out replacing the factor two solely from maximality of the window, projection distinctness, and independence. Stronger constants must use additional structure.
