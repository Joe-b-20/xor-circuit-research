# Review of shared-helper amplification

2026-11-14. Independent machine review of [SHARED_HELPER_AMPLIFICATION.md](../SHARED_HELPER_AMPLIFICATION.md). I reconstructed the bounds and both constructions symbolically. No search or enumeration was used. This is not formal verification or human certification.

## Result

The unrestricted optimum 2m+2, the no-odd-helper optimum 3m+1, and the resulting unbounded m-1 penalty are proved for every m>=1 under their stated hypotheses. The optimum population statement for m>=2 is valid. No material mathematical gap found.

## Constructions and parity rank

The first construction uses the shared odd triple x+a+b, m private pair sums, and m output additions. Its m+1 even values have disjoint pair supports and are independent; its odd gate population is the m outputs plus one helper. It therefore has total 2m+2 and zero even defect.

The second construction keeps every non-output gate even. Its p and the m private pairs span a rank-(m+1) space, and its m values p+q_i are dependent even additions. Its total is 3m+1, with H=0 and delta=m. All supplied values are physical, causal XOR results.

The compatible-partition proof covers all possibilities for the locations of the three core coordinates. With three distinct core parts, each private pair must cancel two core unit images, so no outside part occurs. With at most two core parts, the core has unit image and each private pair can meet at most one outside part. This bounds the component count by m+2. The displayed partition attains it, so r>=m+1 is exact as a rank requirement. This argument is applied to arbitrary circuit partitions, not to the two constructions alone.

## The named-pair obstruction

The set of all coordinate inputs and required outputs has no relation on four distinct elements. The proof by the number of selected outputs is valid for every m; private coordinates ensure that two or more distinct targets leave the indicated nonzero support. Thus every nonzero sum of two distinct named odd values has a unique unordered pair representation.

When H=0, every odd physical value is named. In a reduced circuit, an equation on one even value and its unique named pair can be used to create a new value at most once. In particular an even value created by adding its two named odd endpoints cannot later generate a new odd target using that same pair: both endpoints already existed. This is the chronological content behind the count m+k<=E=k+d and d>=m.

Reduction is legitimate here. Removing duplicate, zero, or dead gates creates no new odd helper and preserves the required targets. The reduced lower bound is therefore a lower bound for the original circuit's size. If one also wants the original defect inequality, deleting a collection of even gate values lowers their rank by no more than their number, so the original delta is at least the reduced delta.

## Unrestricted optimum

I checked the final saved proof, which directly applies [FIRST_ODD_TARGET_TRADEOFF.md](../FIRST_ODD_TARGET_TRADEOFF.md): every output has total-parity weight five, so H+d>=1. Since delta=d+mu and r>=m+1,

    G=m+r+H+d+mu >= 2m+2.

Thus the general first-target theorem proves the unrestricted lower bound without using the no-odd-helper comparison. The latter comparison independently quantifies the obstruction to removing the shared odd value.

As a cross-check, the former population argument is valid too: H>=1 and the rank bound give at least 2m+2, while H=0 and the named-pair obstruction give at least 3m+1. The final note uses the stronger general theorem as its unrestricted proof.

For m>=2, H=0 is strictly more costly than 2m+2. At equality H>=1, r>=m+1 and delta>=0 force H=1, r=m+1 and delta=0. For m=1 both displayed constructions have cost four; the note correctly excludes that case from its unique population claim.

## Scope

The gap compares whole circuits for the same target map and allows complete reorganization and arbitrary cancellation. Hence it refutes a universal constant-overhead removal of an odd helper. It does not merely compare the two specified wirings.

The note does not prescribe the odd helper's value in every optimum, does not add local bounds across overlapping groups, and makes no new numerical MixColumns claim. The restricted comparison has a direct unrestricted purpose: it proves why a uniform removal price cannot account for shared intermediates.
