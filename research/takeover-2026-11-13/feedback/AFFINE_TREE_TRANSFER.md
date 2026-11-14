# Translated entry trees account for the cost of shared returns

2026-11-14. Structural hand argument using actual entry edges, chronological availability, and credits for original physical source values. No circuit search or configuration enumeration.

## Removing a single outside entry

Split circuit coordinates into ordinary consumer coordinates and a source space. A source gate has zero consumer part; let `G_0` count those gates. A consumer-bearing gate has nonzero consumer part; let `K` count them. An entry adds an actual source label to a consumer-bearing operand.

Suppose a consumer-bearing gate `v=u+h` is not a target and every reader of `v` is a source exit. First bypass any such exit whose value was already physically available before it. A useful return means a remaining first supply of a nonzero source value. Let these distinct useful return values be

    f_j=v+w_j.

Thus `u` and all `w_j` have the same ordinary consumer mask. No useful partner is `u`, since that exit would merely return the previously supplied label `h`. Assume `u` and these useful partners belong to one tree of actual entry edges after `v` is removed. Redundant readers need not satisfy this assumption because they were bypassed. Such an entry tree has a common ordinary mask; its edges carry the actual source labels that were read. Other gates and other feedback in the circuit are unrestricted.

Let `T` be the minimal subtree containing `u` and all the return partners `w_j`. Root this undirected tree at `u`. For each vertex `x` of `T`, define the source value

    t_x=h+value(u)+value(x).

The two consumer parts cancel, so this is a source value. In particular `t_u=h`, and `t_(w_j)=f_j`. Along an entry edge of label `ell`, the two translated values differ by `ell`.

Let `A` be the original physical source-value set, including inputs, permitted free values, and all original source gate values. Put

    B=|{t_x : x in T, t_x nonzero} minus A|.

**Affine-tree transfer theorem.** The circuit has a realization with the same targets, at most `K-1` consumer-bearing gates, and at most `G_0+B` source gates. In particular its total cost increases by at most `B-1`.

This is a partial feedback removal theorem. It removes this one entry and its uses while preserving other consumer gates and other feedback; it does not promise a source-only realization.

## Chronology and accounting

Keep the original gate order. Copy every consumer-bearing gate other than `v`; copy or bypass ordinary source gates and unrelated exits in that order. Replace each exit using `v` by its translated value. Retain `h` as the translated value at the root `u`.

When a return at `w_j` is first requested, walk along the path from `u` to `w_j`, retaining previously computed translates. Each missing next translate is the preceding translate XOR the actual label on that edge, using at most one source gate. An already available value is reused; zero needs no gate.

All required labels are available in time. The original entry edges point away from their original chronological tree root. The path between `u` and `w_j` lies in the union of their two original root paths. Every label on it was physically read no later than the production of `u` or `w_j`, both of which precede the return being replaced. Earlier source producers, including earlier rewritten returns, have already been preserved by induction. The new rooting at `u` changes the order of translation, not this availability statement.

Any synthetically produced translate that is an original source value can be charged to its original source producer. If that producer is earlier, the value is already available and needs no synthesis. If it is later, bypass the producer when its original position is reached; if it is the current exit, use that exit's original allowance. Original free values are available from the start. Distinct advanced source values have distinct original producers. Each distinct synthetic translate is made at most once.

Only the `B` translated values absent from `A` can therefore add source gates. The removed gate `v` has no remaining reader: every original use was an exit now supplied in the source. All targets and all other original source values are retained no later than their original uses. This proves the theorem.

## A simple bound by unrequested tree vertices

The root translate `h` and every requested return `f_j` already belong to `A`. Thus only vertices of `T` other than `u` and the requested partners can contribute to `B`. They are intermediate vertices needed to connect the requested returns in the tree. Some may also translate to original physical values and receive a credit.

If there is at most one such vertex, then `B<=1`, and the outside entry can be removed without increasing total cost. This holds whenever the relevant entry tree has diameter at most two: it is a star, and its centre is the only possible unrequested vertex after taking the connecting subtree. It also holds if that tree has at most three edges and there are at least two distinct useful return partners. With `r` partners and `d` edges in `T`, the number of possible extra vertices is `d-r`.

The theorem does not count an arbitrary dimension as a physical gate credit. Its bound concerns the particular translated values created along actual entry paths. A tree with more intermediate vertices can still have `B<=1` if those translates were originally supplied elsewhere.

## Application to the twelve-consumer frontier

For a candidate of total at most 21 with twelve consumer gates, [saturated tails](SATURATED_TAILS.md) leaves at most one outside entry. It must have at least two distinct useful returns. Its removal without increasing total cost would contradict the established minimum 22 at eleven consumer gates. Therefore, if all of its return partners belong to the entry component containing `u`, its connecting subtree must have

    B>=2.

In particular that component must have at least four entry edges. The surviving obstruction involves at least two translated intermediate values absent from the original physical source, or a return partner in a different entry component. Merely having two exits is not sufficient to create an obstruction.

If the relaxed eleven-gate target core has five entries whose traces are all odd and pairwise distinct, bypassing them leaves the minimum six-gate ordinary circuit. Each ordinary-mask fibre is an entry tree. The [odd-run theorem](TIGHT_FIBRE_WIRES.md) forbids a three-edge path, so every such tree has diameter at most two. The affine-tree transfer theorem then removes the outside entry at no increased total cost. **This core profile is excluded below 22**, even when the source contains other feedback. This is stronger than requiring all source exits to admit a source-only replay at once.

The theorem does not yet eliminate returns between separate entry components or every five-entry core profile. It supplies a physical accounting principle for their shared work.
