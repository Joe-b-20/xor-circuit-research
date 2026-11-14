# Independent review of credited source replay

2026-11-13. Reviewed `feedback/CREDITED_REPLAY.md` independently by symbolic proof. No searches, enumerations, or construction campaigns were used. This is a machine review, not formal verification or human certification.

**Verdict:** the general theorem and its accounting are sound. One small clarification was requested in the three-nonclean example: its five labels must explicitly be assumed to span rank four, ensuring that the displayed two planes form a direct sum. The intended application already has that hypothesis. This does not affect the general theorem. Primary-agent integration note: the example now explicitly assumes rank four and names `c,d` as clean labels, incorporating the requested clarification.

## Prefix splitting

For a fixed `U=P direct-sum Q`, suppose the previous entry span already splits. Adding an entry `ell=p+q` increases the entry-span rank by at most one. Its projection spans grow by zero, one, or two directions. If both `p` and `q` are new on their respective sides, their direct sum grows by two, so it cannot equal the new entry span. If at least one component is in its previous projection span, that component belongs to the previous entry span; subtracting it from `ell` supplies the other component in the enlarged entry span. The new prefix therefore splits. Induction from the zero prefix proves the stated equivalence.

The condition is about spans of earlier entries, not mere eventual availability of the chosen group directions. The theorem correctly keeps this chronological hypothesis separate from membership in the final space.

## Causal construction

At each entry the full label has already been supplied by replay of its earlier source producer, or is initially available. Prefix splitting ensures one component is in a maintained projection space; the other can therefore be computed from two physically available values. Completing the newly enlarged subgroup uses only that new component and values already maintained. There is no use of a future operand.

At a source exit, both consumer operands have source parts in the span of earlier actual entries. Their sum is consequently in that span, which splits into the two maintained projection spaces. Both components are physically available and require at most the original one XOR. Ordinary source gates likewise use already replayed source operands. This induction remains valid when an entry label's original source production has consumer feedback ancestors.

At the last entry the projection spaces are all of `P,Q`; finishing the original source schedule preserves every source value. Computing this source-only circuit before the original consumer-bearing graph gives the claimed no-feedback realization, with the same labels and consumer gate count.

## Credits and the original value set

Every synthetic result lies in the nonzero group union and is created at most once. If it belongs to the original physical availability set `A`, it cannot be an original base value: inputs and all permitted free values were available from the start. It also cannot have an already replayed original producer, since that would make it available and suppress the synthetic gate.

Thus every such synthetic value has a later original source gate whose output is exactly that value. Choosing its first original producer assigns distinct credit gates to distinct synthetic masks. That later gate can be bypassed whether it was an ordinary source gate or an exit. No credit is taken merely because a value lies in the span of original values. This validates

    cost <= G_0 - |R intersect A| + |R|
         <= G_0 + |((P union Q) minus {0}) minus A|.

The two groups meet only at zero, so the last cardinality is exactly the stated sum `B`. Original duplicates cause no difficulty: crediting one later producer is sufficient, and any additional bypasses only improve the estimate.

## Rank-only bound and applications

A chronological greedy entry basis spans every prefix using the basis elements selected by that time. Assigning those basis elements to two fixed groups therefore gives prefix splitting. Each group's basis elements are actual original values, so for dimensions `p,q` the missing-value count is at most

    (2^p-1-p)+(2^q-1-q).

Balancing the dimensions recovers the stated rank-only allowance. Additional original physical group values correctly improve the bound.

In the three-nonclean example, with its rank-four hypothesis made explicit, `P=span{c,d}` and `Q=span{n,k}` are disjoint planes. Every entry except `m` belongs to one group. Choosing `n` as the earlier member of the related pair makes the `Q` component of `m=n+t` already present. Hence the prefix condition holds, and only `c+d` and `n+k` can be missing group values. The general theorem reproduces the dynamic completion and later-production credits of `THREE_NONCLEAN.md`.

If all entry labels lie in the union of the two groups, every prefix splits immediately. The four-nonclean pair-relation example therefore has premium at most one when one group is entirely original and the other has only its pair sum missing. The review does not extend this conclusion to the other four-nonclean trace patterns.
