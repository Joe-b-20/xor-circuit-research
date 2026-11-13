# Continuation: what cross-window sharing actually permits

2026-11-13, continuing commit `14b89e6`. Hand proofs with independent machine reviews;
not formal verification or human certification. No SAT, circuit search, exhaustive
enumeration, exact least-gate search, or computer-driven case elimination was used.
The unrestricted statement remains **75 <= L(MixColumns) <= 88**.

## Strongest new limitation

[SPARSE.md](SPARSE.md) gives a reduced live family with two hidden gates, but a growing
advantage over every event-free circuit:

    displayed XOR circuit: 13r+3 gates,
    event-free minimum:    15r+2 gates,
    advantage:            at least 2r-1.

At the same time, every output has weight five or seven, input/output boundary vectors
have no nonzero relation of weight below six, output rows are independent, windows have
at most three blocks, and blocks have at most four coordinates. Selected events occupy
distinct maximal windows, and the designated own blocks have no reciprocal incidence.
Only one of the two hidden gates is nonlocal.

Thus no fixed multiple of hidden-gate count, or of nonlocal-gate count, bounds cancellation
savings under those combined hypotheses. This is a real cost separation, not a wasteful
circuit built merely to defeat an accounting rule. The displayed XOR circuit is not
claimed optimal; the event-free optimum is proved exactly.

The map has `12r+4` inputs and `4r` outputs. It is rectangular and has one output per own-block
family, with growing incidence through common blocks. It does not reproduce MixColumns's
four simultaneous structured rows per sheet, fixed incidence pattern, or invertibility.
[MULTIWINDOW.md](MULTIWINDOW.md) is the simpler precursor, whose exact event-free minimum is
`3rm`; it helps explain the mechanism.

The packed-private-block lower bound in SPARSE also supplies a useful proof technique:
zero coordinates successively to count deleted gates, allow intermediate events, and use
the final full-block projection to recover event-freeness. The proof explicitly preserves
original projected operand values through normalization.

## A positive theorem that counts shared operands once

[AFFINE.md](AFFINE.md) replaces separate per-window counts by one graph on the physical
nonlocal operands. In a component let `K` be the span of the selected event values.
All its operands and local partners lie in one affine coset `a+K`.

Intersect that coset with the coordinate subspaces of the actual output windows. These are
the geometrically possible local completions. Let `Delta` span their pairwise differences.
The component needs at least

    dim K - dim Delta

distinct nonlocal operand gates. If it has no actual local partner, it needs at least
`dim K+1`. A physical incidence bit can strengthen the first bound by one. The components
are disjoint, so these particular counts can be added across sheets. The completion spaces
are obtained by linear systems, without enumerating their values or invoking an optimum.

The theorem contains the earlier separation-rank bound and combines with both versions of
the visible repair inequality. In the shared-gate families, `dim Delta=r-1`, explaining
exactly why independent event values impose only one nonlocal-operand expense.

It is not a general numerical lower bound. If `K` is the full input space, the geometric
quotient is zero. It is also zero in the two-output MixColumns overlap witness below;
there the incidence bit recovers only one. The theorem makes the missing compatibility
constraint explicit rather than proving it for all MixColumns circuits.

## Internal events and actual MixColumns controls

[INTERNAL.md](INTERNAL.md) gives an exact feasibility test: an event with surviving support
`R` and cancelled support `C` can have two local operand values exactly when two output
windows containing `C` cover `R`. This is about algebraic masks, not their production cost.
It detects obstructions missed by the graph that only records pairwise block co-occurrence.

An enclosing-window rank theorem then handles internal events with different proper
supports. Its separated coordinates are the complement of all windows containing the
component's full outside signature. This is the strongest linear annihilator available
from that signature and locality alone. A stated sheet-3 event profile gives `G>=84-2m`
for `m` independent events when they are the entire visible set.

Two direct MixColumns constructions prevent overgeneralization:

- [OVERLAP.md](OVERLAP.md): a reduced 156-gate circuit has one hidden gate shared by output
  events in sheets 3 and 4. Distinct maximal windows do not make the counted gates disjoint.
- INTERNAL: a reduced 149-gate circuit has one internal visible event and no hidden gates.
  Proper support inside a window does not by itself force hidden work.

These are deliberately expensive witnesses; they do not rule out a new constraint for
small or optimal MixColumns circuits. They contradict none of the exact-visible-profile
bounds from the first pass.

## Judgment and next obligation

The coarse support-and-rank route now has sharper limits. The next useful argument must
control the cost or availability of compatible local completions, or exploit the simultaneous
four-row demands and fixed incidence of MixColumns. A new global credit based only on
event count, hidden-gate count, sparsity, or boundary distance would repeat a refuted step.

The completion-difference space is a concrete place to state such a compatibility lemma.
Its size alone is not the answer: the strong counterexample has a large difference space
and genuinely profitable sharing. Any proposed extra cost must identify gates not already
paid for, and survive that counterexample. No such universal MixColumns lemma is claimed.

## Reviews and direct checks

Read [the sparse proof review](reviews/sparse-review.md),
[second sparse review](reviews/sparse-second-review.md),
[affine review](reviews/affine-review.md),
[second affine review](reviews/affine-second-review.md),
[third affine review](reviews/affine-third-review.md), and
[internal-event review](reviews/internal-review.md).

The main agent corrected an explanatory overstatement caught during final checking:
quotienting `K` by completion differences is equivalent to taking its image modulo the
linear span of the local completions; it is not a stronger bound. The proof was unaffected,
and two reviewers checked the correction. Another wording correction restricts a
vanishing-intersection statement to eligible windows.

Run the deterministic checks from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 research/takeover-2026-11-13/continuation/check_continuation.py
```

The [results](check-results.json) record five specified constructions: the simple hub,
the reduced MixColumns overlap, the zero-hidden internal MixColumns example, a sharp
four-operand tree, and the packed sparse family at `r=2`. The last has 29 gates versus
an explicit event-free 32. All linear masks and event/visibility counts are checked;
the universal optimum and boundary-distance statements rely on the hand proofs, not
enumeration. The initial verifier mistakenly included hidden input wires in a gate count;
the saved version excludes inputs explicitly and all five cases pass.
