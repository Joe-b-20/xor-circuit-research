# Independent review of the two-diagonal producer

2026-11-13, primary agent reviewing the separately developed [EXPORTS](../EXPORTS.md).
This is a machine review, not formal verification or human certification.

The ten displayed gates compute all four required rows and the independent even
diagonals D01 and D23. In particular, `D01+E1` has own mask E0 and free label s0;
`D23+E3` has own mask E2 and free label s2. All gates are distinct, live, and event-free.
Combined with the recorded augmented-sheet lower bound eleven for three independent
diagonals, this establishes exact maximum clean-diagonal rank two at ten gates.
It does not say that every two-dimensional diagonal basis can be supplied at that cost.

The defect table is correct, and the comparison with arbitrary free values includes
own parity: equality of defect alone permits odd diagonals, whereas the relevant D
contains only even diagonals. The actual within-D-coset differences all lie in
W=span(D01,D23). The available clean values also lie there. Thus the general
[supplier-profile certificate](../SUPPLY_PROFILE.md) excludes a consumer of at most
eleven gates when the supplied set is fixed.

The remaining total-21 split with one extra zero-consumer-block gate cannot be dismissed
merely as a single appended gate on the original supplier. That extra gate might be a
consumer-block-cancelling exit. The saved proof addresses this: ten consumer-bearing
gates force every actual entry label into D; before the extra gate, all such labels
are in W. Every earlier consumer-bearing signal then has its supplier-side part in W.
An exit can therefore only produce another W value. If the extra gate instead reads
two zero-consumer-block operands, the within-coset difference test gives the same result.
It cannot supply the missing third clean direction. This verifies the lower bound even
with feedback, under the stated fixed-producer interpretation.

The displayed completion adds E2 and D12, then uses exactly ten consumer gates with
the three supplied diagonal labels. The consumer identities are respectively
`E0+d0`, `E1+d1`, `E2+d2`, and `E3+d0+d1+d2`. Thus twenty-two is attained.
The direct verifier independently checks every output mask, gate distinctness, liveness,
and event-freeness in this specified construction. It does not search for an optimum;
the lower bound is the hand argument.
