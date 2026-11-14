# One shared odd intermediate can save arbitrarily many gates

2026-11-14. Structural proofs for an explicit family of target maps, allowing
arbitrary XOR circuits, sharing, and cancellation. No circuit search or enumeration.
The family was proposed independently by the reviewing agent; the primary agent
reconstructed its proofs. No literature-novelty claim is made.

The unrestricted optimum below is the main result. A comparison with circuits
having no extra odd value quantifies why suppressing one kind of intermediate
cannot be assumed to cost a bounded number of gates. This comparison is a direct
obstruction to such an unrestricted reduction, rather than a separate restricted
lower-bound program.

## The target family and two constructions

For m>=1 use the 2m+3 coordinate inputs

    x,a,b,c_1,d_1,...,c_m,d_m

and require the m distinct values

    y_i = x+a+b+c_i+d_i.                                  (1)

Use total parity. Every input and target is odd. The following circuit computes
all targets in 2m+2 gates:

    p=a+b,                 h=x+p,
    q_i=c_i+d_i,           y_i=h+q_i       (1<=i<=m).       (2)

Its only odd gate value besides the targets is h. Its m+1 even gate values
p,q_1,...,q_m are independent. In the notation of
[the general parity account](ODD_COMPONENT_DEFECT.md), it has

    H=1,       r=m+1,       delta=E-r=0.

There is also a circuit with no odd helper:

    p=a+b,
    q_i=c_i+d_i,           e_i=p+q_i,       y_i=x+e_i.     (3)

It costs 3m+1 gates, with even rank m+1 and even redundancy delta=m.
All lower bounds below apply to arbitrary implementations, not only these forms.

## Every circuit needs even rank at least m+1

By the parity partition theorem, the span of computed even values is the space
of vectors even on every part of an input partition. Every target has odd support
in exactly one part. We show that every compatible partition has at most m+2
parts, and that this maximum is attained.

Let q be the number of parts meeting the three core inputs x,a,b.

If q=3, their image in the component quotient is the sum of three distinct unit
vectors. To make y_i have a unit image, c_i and d_i must lie in two distinct
core parts. Indeed, their two unit contributions must cancel two of those three
odd coordinates; any outside part or a repeated part cannot do so. Thus there
are no parts outside the core, and the total is three, at most m+2.

If q<=2, the three core inputs have a unit image: either all are in one part,
or two share a part and the third is in another. Each private pair c_i,d_i can
then meet at most one part outside the core. Two distinct outside parts would
leave three odd component coordinates in y_i. Every outside part contains some
private input, so there are at most m outside parts. The total is at most q+m,
hence at most m+2.

The partition consisting of {x}, {a,b}, and the m pairs {c_i,d_i} is compatible
and has m+2 parts. Therefore c_max=m+2, and in every circuit

    r=(2m+3)-c >= m+1.                                   (4)

This bound concerns the actual span of physical even values. It does not make
arbitrary pair sums available as free operands.

## Named pair sums cannot be shared without an odd helper

Let N consist of the coordinate inputs and the required targets. Every nonzero
sum of two distinct elements of N has a unique unordered representation.
Equivalently, no four distinct elements of N sum to zero.

To prove this, classify a putative four-element relation by how many targets it
contains. With no target it is impossible by input independence. With one target,
three inputs cannot cancel its five coordinates. With two distinct targets, the
common core cancels and four distinct private coordinates remain, which two inputs
cannot cancel. With three targets, six private coordinates and the common core
remain, which one input cannot cancel. With four distinct targets, their eight
private coordinates remain. These are symbolic arguments for every m; no instance
or circuit family is enumerated.

Suppose now that H=0: the only physical odd values are inputs and required targets.
We may reduce repeated or zero gate values without increasing size or introducing
an odd helper. Let k be the number of odd-plus-odd even gates and d the number
of even-plus-even gates, so E=k+d.

Every odd gate and every odd-plus-odd even gate uses a relation between an even
physical value and a pair of named odd values. A fixed even value has at most
one such pair. That one relation can be executed only once: after two of its
three values produce the third, all three already exist, and executing it again
would duplicate a value. Hence the m odd target gates and k odd-plus-odd gates
require at least m+k distinct even gate values. Therefore

    m+k <= E=k+d,       d>=m,       delta>=m.              (5)

Here delta=mu+d from the general parity account, so the final inequality permits
arbitrary cycles and cancellation. The proof does not presume a forest.

Combining (4) and (5), every no-odd-helper circuit has

    G=m+E=m+r+delta >= 3m+1.                              (6)

Construction (3) attains this. If the original circuit was not reduced, applying
the same argument after reduction only strengthens its size lower bound.

## Exact unrestricted optimum and the amplification

For an arbitrary circuit let H count odd gate occurrences beyond one occurrence
of each required target. Its exact gate accounting is

    G=m+H+r+delta.

The [general first-odd-target theorem](FIRST_ODD_TARGET_TRADEOFF.md) applies
because every target has weight five. It gives H+d>=1, hence H+delta>=1.
Combining this with (4) gives G>=m+(m+1)+1=2m+2 directly for all circuits.
Construction (2) thus proves

    L(T_m)=2m+2       for every m>=1.                     (7)

For m>=2, no optimal circuit can have H=0, since 3m+1>2m+2. Equality in (7)
then forces

    H=1,       r=m+1,       delta=0.                      (8)

This characterizes gate populations, not the value or wiring of the odd helper.
No claim is made that every optimum uses precisely h=x+a+b.

The cost of forbidding all odd helpers is therefore exactly

    (3m+1)-(2m+2)=m-1.

One shared odd intermediate suffices to avoid an unbounded amount of repeated
even work. In particular there is no universal constant allowance for transforming
every one-odd-helper circuit into a circuit for the same targets with no odd
helpers. The transformed circuit may otherwise be completely reorganized and may
use arbitrary cancellations; its lower bound is still (6).

## Why this matters to the unrestricted program

The result gives an exact combined-cost statement, and identifies why an
intermediate's value cannot be judged by its own creation cost alone. In (2),
the two-gate core computation is reused across all m targets. Removing its odd
intermediate forces m separate even combinations, as proved for all circuits.

The earlier complementary-sum family admits a one-for-one exchange between odd
helpers and even redundancy. This family shows that such an exchange rate is
not universal: one odd helper can replace many dependent even gates. Both results
concern unrestricted optimal circuits for whole target families.

The theorem does not establish a new MixColumns bound or a universal target-only
tradeoff invariant. It supplies a required stress test for any proposed removal,
repair, or accounting theorem that assigns a fixed price to a shared intermediate.

Independent review: [shared-helper amplification](reviews/shared-helper-review.md).
