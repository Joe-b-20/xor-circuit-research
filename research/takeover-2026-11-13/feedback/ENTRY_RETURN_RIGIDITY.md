# Consumer cost controls source-coset collisions and entry returns

2026-11-13. Hand proof by linear projection and chronological bypasses. No circuit search or configuration enumeration. This constrains feedback at an eleven-gate consumer without assuming that source work precedes consumer work.

## General consumer model

Use ordinary consumer coordinates `z` and a disjoint source-value space. Count all `K` physical gates whose `z` part is nonzero. An entry is one such gate with a zero-`z` operand, its actual source label. The required consumer outputs have nonzero `z` parts; let `D` span their source parts and let `L_D` be their minimum cost when every value of `D` is freely supplied.

When examining the consumer, grant every actually read zero-`z` operand freely. The resulting nonzero-`z` graph is a valid consumer circuit. It may retain gates used only by exits; none of the arguments below require deleting them in advance. A linear projection on the source part that fixes `D` preserves the required consumer outputs and leaves every ordinary `z` mask unchanged.

A label is **nonclean** if it is outside `D`. Let `U` span the actual entry labels, so every consumer-bearing source part belongs to `U` and `D` is a subspace of `U`. For the unique-pair statement below, physical values are normalized to remove duplicate gates. The general collision theorem also permits duplicates and counts them as separate physical gate nodes.

## General source-coset collision defect

Let `V` contain one node for each ordinary consumer coordinate input and each counted consumer-bearing gate. Free copy wires are not additional nodes. Choose any source subspace `C` with

    C subset U,       C intersect D = {0}.

Group nodes of `V` by their full value modulo `C`, where `C` has zero consumer-coordinate part. Count physical nodes with multiplicity, even if two gate values coincide. Define

    delta_C = sum over occupied C-cosets (number of nodes in the coset - 1).

**Collision-defect theorem.**

    K >= L_D + delta_C.                                    (CD)

Extend `C` to a complement of `D` in `U` and project source parts onto `D` along that complement, leaving ordinary consumer coordinates fixed. The target values are unchanged. Every `C`-coset of nodes becomes one projected value; distinct `C`-cosets may merge further, which only helps the bound.

Keep the earliest physical representative of each projected value and bypass every later gate with that value. A coset contains at most one ordinary input, because all its nodes have the same consumer mask and the coordinate inputs have distinct masks. All bypassed later representatives are therefore paid gates. This removes at least `delta_C` gates. Redirecting in topological order preserves every projected mask, and no projected consumer-bearing value becomes zero because its ordinary part is unchanged. The resulting consumer uses only source labels in `D` and still computes its required targets. Its cost is at least `L_D`, proving (CD).

This measures all physical source-coset collisions, not just entry occurrences. Repeated label use and equal-own internal values can contribute to the same quotient class, and the class size accounts for their combined effect without double counting. No assumption of source-first scheduling or target-cone trimming is needed.

## A causal extension of entry deletion

Suppose a zero-`z` exit returns a nonzero source value `f`. Choose a set `I` of actual entry occurrences strictly after that exit. Let `C` span their labels, and assume

    C intersect D = {0},       f in C.

Then the order-refined bound is

    K >= L_D + |I| + 1.                                    (1)

The exit's two earlier consumer-bearing operands already give one `C`-coset collision. Each chosen later entry adds a physical node to the same `C`-coset as its earlier nonfree operand, increasing the collision defect by one. Hence `delta_C>=|I|+1`, and (CD) proves (1). Equivalently, the usual [entry-deletion lemma](../compatibility/QUOTIENT.md) bypasses the chosen later entries, while the exit's earlier operands provide one additional distinct gate bypass. Chronological separation ensures that these deletions do not count the same gate twice.

In particular, if `K=L_D+1`, a nonclean exit cannot subsequently be read verbatim as an actual entry label. Taking `I` to be that later occurrence would force two deletions.

## The stronger unique-pair theorem

**Theorem.** Suppose `K<=L_D+1` and a nonclean value `f` is actually read at an entry

    v=u+f,

where `u,v` are consumer-bearing values. Then this is the only entry occurrence of label `f`, and `{u,v}` is the unique unordered pair of distinct physical consumer-bearing values whose difference is `f`.

Apply (CD) to `C=<f>`. Normalized distinct values occur in classes of size at most two, so `delta_C` counts unordered physical pairs with difference `f`. The entry edge `{u,v}` already uses the entire allowance `delta_C<=1`.

For clarity, translation by `f` is a matching: different pairs cannot share an endpoint, because a fixed endpoint has the unique partner obtained by adding `f`. A second physical pair would therefore be disjoint from `{u,v}` and give `delta_C>=2`, a contradiction. A second occurrence of the actual entry label likewise supplies two entry deletions directly, contradicting the same one-gate allowance.

This proves the unique-pair statement. It uses the numerical lower bound only after two explicit physical gate deletions; it does not count a virtual pair as a paid gate.

## Consequences for exits and the eleven-gate joint frontier

Any exit returning this `f` must read the unique pair `{u,v}`. But `f` was already physically supplied before the entry that produced `v`, and hence before that exit. Such an exit merely recomputes an existing source value and can be bypassed in the full circuit. If an exit were claimed as the first supplier of `f`, causality would fail: it would require `v`, which already read `f`.

Consequently a reduced circuit with `K=L_D+1` has no exit whose returned value equals a nonclean actual entry label. Every such label must originate from source base availability or from a source-side operation on two zero-consumer operands. That operation may still have exit ancestors; the theorem does not exclude indirect feedback into a label's computation.

For the unrestricted MixColumns 0/1 joint problem, `L_D=10` and

    D={v(b)+v(a): v even}.

Thus an eleven-gate consumer has unique physical pair support for every nonclean entry label, and no nonredundant exit can directly supply any of those labels. This applies to the four- and five-entry nonclean interfaces of [QUOTIENT](../compatibility/QUOTIENT.md), including repeated use of other clean labels and gates serving exit ancestors. The complete source budget remains a separate issue; the result alone does not prove a joint lower bound of twenty-two.

## A further restriction in the all-nonclean five-entry interface

The existing [all-nonclean interface theorem](../row-cost/JOINT01.md#exact-cost-of-avoiding-every-clean-entry-label) gives five distinct labels in one affine coset of `D`: four labels form an affine plane `q+W`, with `dim W=2`, and their sole relation is their all-four sum; the fifth label `h` is outside their linear span. Their total span is `U=D+<h>`.

The nonclean coset `h+D` is the disjoint union of `q+W` and `h+W`. All four values of the first plane and the one value `h` of the second are actual entry labels. The unique-pair theorem excludes every one of them as a nonredundant exit value. Since every exit belongs to the actual entry-label span by causal induction, a nonclean exit in this interface can therefore return only one of

    h+w,       w in W minus {0}.

There are three such values. This is a restriction on the returned values themselves, not an enumeration of possible circuits or a charge for their virtual differences. Clean exits are not confined to this plane by the argument.
