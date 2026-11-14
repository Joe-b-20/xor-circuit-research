# General arguments for unrestricted XOR circuits

2026-11-14, continuing `0cb775c`. The user's direction is to prioritize general
structural understanding and unrestricted arguments, rather than successive local
case exclusions or one-gate numerical improvements.

The twelve-consumer case program is no longer the active research target. Its
reviewed results remain available. Restricted lemmas are pursued only when their
role in a specified unrestricted argument is explicit. A numerical improvement
is welcome, but is not the organizing objective.

## What a useful next theorem must do

It must apply to arbitrary sharing and cancellation, or give a proved reduction
that covers them. The cost must concern actual computed values and respect their
availability. If several parts of the computation use the same gate, the final
account must charge it only once. A conservation or rank identity is useful only
with a clear account of what additional fact turns it into unavoidable work.

## First unrestricted continuation

[Parity components and their physical defect](ODD_COMPONENT_DEFECT.md) removes
the independent-even-helper assumption from the earlier forest argument. For any
chosen parity functional, let s be the number of odd coordinate inputs, c the
number of components in the odd-occurrence graph, E the number of even gates,
mu its cycle rank, and d the number of even-plus-even gates. Then

    E = s-c + mu+d.

The partition description of the even span was already in the saved foundational
work. The note reconstructs that foundation and connects the excess even gates
to cycles, even-only computations, and marked source transport. Even occurrence
aggregates, modulo boundary values and odd occurrence aggregates, have rank at
most mu+d. This is an unrestricted statement about one actual circuit, not a classification
of small consumer budgets. It does not charge partial copy-tree values as
separately available source operands.

For m distinct odd non-input targets and H other odd gate occurrences, the exact
whole-circuit account is

    G = m + H + s-c + mu+d.

This also identifies a limitation: every all-odd target set admits a circuit with
mu+d=0, by computing star-pair bases inside compatible components and accumulating
outputs through odd gates. That construction can use many extra odd gates.
Therefore targets alone cannot force positive even redundancy in all circuits.
The meaningful goal is a joint lower bound on extra odd work, the component
partition, and even redundancy. Optimizing one of these separately is insufficient.

## A general relaxation rejected before further investment

[The quadratic lift](QUADRATIC_LIFT_LIMIT.md) gives an exact target-dependent
tensor identity with one contribution per physical gate, allowing arbitrary
cancellation and sharing. Nevertheless its unconstrained decomposition model has
an explicit sixty-term realization for MixColumns. It cannot recover 75.
Those sixty terms are not a circuit: they grant parent values and output
influences without a common executable realization. The specified decomposition
and the proof are saved so this loss of information is not rediscovered later.

## Research judgment and unresolved task

The next main question is a general tradeoff theorem: when can reusing computed
values reduce one part of the work only by increasing another? The parity account
is one concrete framework; it is not a commitment to remain within parity methods.
A different invariant is preferable if it controls actual shared work more directly.

For the parity route, the missing theorem must constrain H+(s-c)+(mu+d) jointly
from the target map, with no fixed gate budget, no prohibition on feedback, and no
assumption of independent even helpers. The marked transport bound can support
such a theorem only where its required rank is itself justified. If the boundary
space already spans all aggregate labels, that rank is zero. Adding separate
interface inequalities without controlling shared gates is not a global proof.

The unrestricted MixColumns range remains 75 to 88. No conclusion about optimality
of 88 follows. The new notes have independent machine reviews, not formal
verification or human certification; no circuit search or enumeration was used.

Reviews: [parity and defect](reviews/odd-component-defect-review.md),
[quadratic lift and its limitation](reviews/quadratic-lift-review.md).
