# Independent review: saturated tails

2026-11-14. Independent machine review of [SATURATED_TAILS.md](../SATURATED_TAILS.md), including the saturated-core corollary added during review. This is an argument audit, not formal verification or human certification. No circuit enumeration or search was used.

**Verdict:** the general coloop theorem, the saturated-core corollary, and the two twelve-consumer necessary conditions are valid under their stated hypotheses. They leave a genuine one-tail, multiple-return case open.

## Projection and ancestry

For an arbitrary basis of actual quotient-label occurrences, projection along their full span fixes `D` and kills all selected labels. Each selected entry is bypassed to its earlier consumer-bearing operand. Every surviving projected edge therefore follows a path already present in the original relaxed consumer graph. Cutting zero-consumer source operands matters: those ports remain external after projection, so no dependency through a source return is introduced into a consumer target cone.

An unselected original node outside the relaxed target cones consequently cannot become a target ancestor. If it survives copying, it is a dead paid node; if projection already makes it free or redundant, that is already an additional saving. Either way, besides the `c` selected deletions there would be another deletion, contradicting the projected minimum `L_D`. This reasoning does not require all original gates to lie in target cones and does not silently discard exit-only computation in the full circuit.

Since every quotient basis must select every outside node, these nodes are entries whose quotient-label occurrences are coloops. The occurrence formulation is essential: repeated quotient images cannot individually be coloops. Thus the number of outside nodes is at most `c`.

## The target core remains saturated

Let there be `m` outside nodes. The actual inside labels span `U_Y` containing `D`, by causal induction in the cut target core. All remaining actual labels are the `m` outside entry labels. Their quotient images are independent modulo `U_Y/D`: a dependence would express one coloop using other actual occurrences. Therefore `dim(U_Y/D)=c-m`, while the core has exactly `K-m=L_D+c-m` gates. This proves the added corollary without an assumption about whether the outside computation is globally useful.

## Twelve-consumer application

For a total at most 21 with `K=12`, the reviewed rank-four source floor forces actual entry rank five, and the full-diagonal supply inequality forces at most two original nonzero physical `D` values. Two outside nodes would leave a ten-gate saturated target core with entry span exactly `D`. Its actual entry labels must span the rank-three target source space, requiring at least three distinct nonzero original physical `D` values. This contradicts the supply bound. Hence at most one outside node remains.

With one outside node, the corollary gives a target core with eleven gates and entry rank four. It is correct to keep this as an interface constraint: the original source may still need the outside node, so the earlier joint eleven-gate theorem cannot be applied directly to this core.

## Normalization and the single-return reassociation

Bypassing zero-valued or later duplicate-valued nodes uses only earlier available values. It is causal and cannot increase either the total gate count or the number of consumer-bearing gates. If this changes `K=12` to a smaller budget, the already proved ten- and eleven-consumer bounds exclude the candidate; fewer than ten consumer gates are impossible by the local consumer bound. Thus the proof may assume a reduced twelve-consumer candidate.

Its unique outside entry `v=u+h` has no consumer-bearing reader: any such reader would either be another outside node or make `v` an original target ancestor. It is neither a source output nor a consumer output, so its remaining uses are exits. Reduction ensures that distinct remaining exit gates produce distinct nonzero values unavailable earlier. In particular, a redundant return of a label already supplied before its entry cannot count as a necessary reader.

If there is only one reader `f=v+w`, then `w` cannot depend on `v`: the only first edge of such a dependency would lead through `f`, creating a cycle. At the original time of `f`, all of `u,w,h` are available, and the reassociation `g=u+w`, `f=g+h` preserves the original value. Both new gates have zero consumer part. It replaces one source gate by at most two and removes one consumer gate, without increasing the total. If `g` is zero or already available, it needs no new gate. The resulting consumer budget is at most eleven, giving the claimed contradiction.

Thus any surviving outside entry must feed at least two distinct nonredundant return values. This does not establish that those multiple returns can be removed at zero overhead, and the paper correctly retains that limitation.
