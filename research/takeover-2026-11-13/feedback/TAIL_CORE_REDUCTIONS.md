# Core entry geometry restricts a shared outside tail

**Combined result:** [six-entry frontier](SIX_ENTRY_FRONTIER.md) includes the later
four-entry, two-nonclean, and three-nonclean four-term proofs, completing outside-tail
closure below 22. The statements left open within this intermediate note are covered there.

2026-11-14. Structural hand arguments by literal transposition, physical difference pairs, and chronological affine-tree transfer. No circuit search, configuration enumeration, or computer-driven elimination.

Consider a joint candidate with at most 21 gates, twelve consumer-bearing gates, and a unique gate outside the relaxed consumer target cones. By [saturated tails](SATURATED_TAILS.md), this gate is an entry `v=u+h`, every reader is an exit, and at least two distinct nonredundant returns use it. Its eleven-gate target core has actual entry rank four and quotient rank one over the rank-three diagonal `D`.

The [eleven-gate interface theorem](../compatibility/QUOTIENT.md) gives either four or five entries in this core. This note proves four reductions:

- With four core entries, a surviving tail must have a useful return between two different entry-tree components of one ordinary-mask fibre. Exactly one fibre has two ordinary roots.
- With five core entries, the four-nonclean profile whose actual label relation has three terms cannot support a surviving tail. In fact every entry tree in such a core has at most three edges.
- A three-nonclean core whose actual label relation has three terms also cannot support a tail, by completing an original triangle and retaining one translated helper.
- Neither five-entry affine-plane profile can support a surviving tail: the four-nonclean profile with a clean fifth label, and the all-nonclean profile.

These statements do not close every five-entry profile or the remaining four-entry case with two roots.

## Any incident subset exposes its trace sum

An entry's trace is its formal source input's coefficient vector on the four consumer targets. At a consumer node `x`, select any subset of incident entry edges, and XOR their traces. If this sum is nonzero, it can be exposed on a wire of a literal transpose, with ordinary derivative equal to the nonzero ordinary mask of `x`.

There is at most one incoming entry edge at `x`. If it is not selected, accumulate the selected outgoing entry contributions first in the adjoint accumulator at `x`. If it is selected, its trace is the full adjoint of `x`; accumulate all reader and terminal contributions except the selected outgoing entry contributions. Their sum is the desired trace sum. A single contribution already supplies the wire, and a nonzero sum ensures that the required collection is nonempty.

Any binary ordering of this accumulation has the same number of XORs. The selected wire feeds the full adjoint of `x`, so literal double transposition gives ordinary derivative equal to the original ordinary mask of `x`. Deleting formal trace-output ports preserves this ordinary derivative. This is the same marked-wire argument as the [adjacent-pair lemma](TIGHT_FIBRE_WIRES.md), applied to an arbitrary incident subset. Other marked entry wires remain present.

In a six-gate ordinary mirror, two wires carrying different even helpers cannot have the same nonzero ordinary derivative. This remains the [even-wire separation theorem](TIGHT_FIBRE_WIRES.md); the incident-subset observation provides additional ways to expose a forbidden pair of wires.

## Four core entries require a return between two roots

The four actual core labels form a basis

    c,d,n,m,

where `c,d` are clean, `n,m` are nonclean, and `c,d,n+m` are independent in `D`. The seven-gate literal mirror has three independent even trace values: `n,m` have the same trace, and `c,d` have the other two traces. These three values, together with the four odd triples, exhaust its seven gate values.

Two adjacent entry edges cannot have different traces. The incident-subset lemma would expose the nonzero sum of two of these three independent even values on a mirror wire. This is a fourth even value, requiring another gate beyond the seven already necessary. Thus each connected entry component uses a single trace class. Its edges are a subset of `{n,m}`, or consist of the one `c` edge or the one `d` edge. In particular every component has at most two edges.

If `u` and every useful tail partner belong to one such component, the [affine-tree transfer theorem](AFFINE_TREE_TRANSFER.md) removes `v` without increasing the total: the connecting subtree has at most two edges, hence at most one unrequested intermediate vertex. This contradicts the already proved minimum 22 with at most eleven consumer gates. Therefore at least one useful exit `v+w` must use a partner `w` in a different entry component from `u`.

It remains to count roots, without classifying circuits. Bypassing the four entries leaves seven non-entry gates for the four ordinary triples. The first occurrences of those four triples and at least two distinct even helpers already use six non-entry gates. An entry preserves its ordinary mask, so it cannot provide any of these first occurrences. Two entry components with the same ordinary mask require a repeated root mask among the ordinary inputs and the seven non-entry results, consuming the one remaining gate. There is consequently exactly one fibre with two roots, all other fibres have one root, and there is no room for a third distinct even non-entry mask. The necessary tail return between components lies in that unique two-root fibre.

This conclusion concerns physical roots and an actual return. It does not charge the difference between the two roots as an already supplied source value.

## A three-term relation forbids a four-edge fibre

Now consider an eleven-gate core with five actual labels

    a,b,c,k,d,       c=a+b,

where `a,b,k,d` are independent nonclean values and `c` is clean. The only actual label relation is `a+b+c=0`. The five-entry interface theorem gives distinct nonzero traces. Precisely `a,b,c` have odd traces; `k,d` have the two different even traces.

Bypassing entries leaves the six-gate ordinary minimum, so every ordinary-mask fibre is one entry tree. The marked `k,d` wires carry different even helpers and therefore have different ordinary derivatives. Thus the `k,d` entries lie in different fibres, and no fibre can have five entry edges.

Suppose some fibre has four entry edges. It must contain `a,b,c` and one of `k,d`; rename that last label `k`. The other even entry `d` lies elsewhere.

The core saturates quotient cost, so every actual nonclean label has exactly one physical difference pair, its own entry edge, by [saturated quotient rigidity](SATURATED_QUOTIENT.md). In particular:

1. The `c` edge cannot meet the `a` edge: the two-edge path would give a second pair with difference `a+c=b`. Likewise the `c` edge cannot meet the `b` edge.
2. The connected four-edge tree must therefore consist of the adjacent `a,b` pair and the `c` edge joined by the `k` edge. The latter joins a vertex of the two-edge `a,b` path to a vertex of the `c` edge.
3. The `k` edge cannot attach at an endpoint of the `a,b` path. If its value at that endpoint is `q`, the opposite endpoint has value `q+c`. The two vertices across the `k` bridge have values `q+k` and `q+k+c`. Besides the bridge itself, the opposite endpoints then give a second physical pair of difference `k`.

Consequently `k` attaches at the middle vertex of the `a,b` path. This vertex is incident to all three entries `a,b,k`.

Write `alpha,beta,kappa,delta` for the traces of `a,b,k,d`. These are exactly the nonclean entries, so their traces satisfy the quotient relation

    alpha+beta+kappa+delta=0.

The incident-subset lemma at the middle vertex therefore exposes the value

    alpha+beta+kappa=delta

on a wire with the fibre's ordinary derivative. The marked `k` wire remains present with value `kappa` and that same derivative. But `delta` and `kappa` are the two distinct even helpers of a six-gate ordinary mirror. Their equal nonzero derivatives contradict even-wire separation.

No four-edge fibre exists. Since five edges were already excluded, **every entry tree in this three-term-relation core has at most three edges**. This structural statement concerns the core itself and does not assume anything about how its actual labels were supplied.

## Consequence for the outside tail

In the five-entry core every ordinary-mask fibre is one entry tree, so `u` and all useful tail partners lie in one tree. In the three-term profile just treated, its connecting subtree has at most three edges. There are at least two distinct useful partners. Besides `u` and these partners, the connecting subtree has at most one vertex whose translated value might be absent from the original physical source set.

Affine-tree transfer therefore removes the outside entry with at most one extra source gate. Its total cost does not increase, leaving at most eleven consumer gates and total at most 21, contrary to the established bound. Hence the four-nonclean, three-term core profile cannot occur in a surviving twelve-consumer tail candidate.

## A triangle plus one other label needs only one translated helper

The following repair can improve the affine-tree bound when actual entry labels are dependent. Suppose the tree paths from `u` to all useful tail partners use labels from an actual source triangle

    {a,b,c},       c=a+b,

and at most one additional actual label `k`. All three triangle values are original physical source values. Then the tail can be removed with at most one extra source gate.

Keep the original core and all other gates in order. Whenever two triangle values are available and the third is needed, compute it and retain it. This has zero net extra source cost: if the third is already supplied, reuse it; otherwise advance its original source producer and bypass that producer later. A free value is available initially. There is at most one such missing triangle completion, and any advancement is charged to a distinct original source gate.

Every tail return has the form `h+q` or `h+k+q`, where `q` is zero or a triangle value. Use the actual entry path to choose the form. The triangle part belongs to the span of triangle labels read on that path, so any necessary completion uses values available before this return. If `k` occurs, it was also read before the return. Compute and retain the helper `h+k` the first time it is needed, for at most one extra source XOR. After that, the return itself uses at most its original one source XOR. Retain repeated values and bypass their later producers as usual.

Thus all uses of `v` disappear, all other original values remain available in time, and the new source count is at most `G_0+1`, while the consumer count is at most `K-1`. This proof keeps other feedback and does not assume a source-only replay. The triangle completion is a credit for original physical values, not for virtual span membership.

Apply this to a five-entry core whose only actual label relation is `a+b+c=0`, with `a,b` nonclean and `c` clean. The other two labels have distinct even traces whenever the core has three or four nonclean entries. Their marked derivatives differ, so a fibre contains at most one of them. Every fibre's path labels therefore lie in the actual triangle plus at most one additional label. The preceding repair removes a tail without increasing total cost.

This excludes the three-nonclean, three-term core profile as well as giving an alternate tail proof for the four-nonclean three-term profile. The no-four-edge-fibre theorem above is stronger structural information for the latter profile and remains useful independently of this repair.

## Both affine-plane profiles also exclude a tail

Suppose the five core labels consist of four distinct nonclean values in an affine plane `Q=q+W`, with `dim W=2` and `W subset D`, and a fifth label `k` outside `span Q`. The fifth label may be clean or nonclean. These are the four-nonclean four-term-relation profile and the all-nonclean profile.

The [affine-fibre theorem](AFFINE_FIBRE_CLOSURE.md) gives four distinct odd plane traces and one even trace for `k`. No two plane-entry edges can be adjacent anywhere in the fibre containing `k`: their even trace sum would differ from the marked even trace of `k` while having the same ordinary derivative.

That entire fibre therefore has at most three entry edges. After removing its `k` edge, each component has only plane edges and contains no two adjacent edges. Each side of `k` can consequently have at most one additional plane edge. Every other fibre contains only distinct odd traces, so the odd-run theorem makes it a tree of diameter at most two.

Thus the tail's common ordinary-mask fibre is either a star or a tree with at most three edges. With at least two useful return partners, its connecting subtree has at most one unrequested vertex. Affine-tree transfer again gives `B<=1`, removes the tail without increasing total cost, and contradicts the eleven-consumer minimum 22.

Together with the all-distinct-odd core case already excluded in [AFFINE_TREE_TRANSFER](AFFINE_TREE_TRANSFER.md), these results eliminate the three-nonclean three-term, four-nonclean three-term, four-nonclean four-term, four-nonclean five-term, and all-nonclean core profiles from a surviving tail candidate. The other five-entry profiles and the four-entry return between different roots remain open.
