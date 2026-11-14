# Independent review: parity components and transport defect

2026-11-14. Independent machine review of the structural statements in
[ODD_COMPONENT_DEFECT.md](../ODD_COMPONENT_DEFECT.md). Hand arguments only;
no circuit enumeration or exact search. This is not formal verification or a
claim of literature novelty.

## Scope and attribution

The partition description of the even-value span is an existing foundation:
[causal Lemma 2.2](../../../structure-2026-11-11/causal/REPORT.md) states it for
cyclic sets, and [the cyclic audit, section 3.2](../../../structure-2026-11-11/cyclic/REPORT.md)
supplies an order-free argument for the component parity statements. The new
note must distinguish that foundation from its executable-graph proof, exact
cycle accounting, and marked-transport extension. No unrestricted MixColumns
lower-bound improvement follows from these identities alone.

## Partition span and exact physical defect

Let a parity functional lambda select s of the coordinate inputs as odd. The
remaining coordinate inputs span W0 and are initially even. Make one vertex for
each odd input and odd gate occurrence; append an edge at each odd gate, and
join the two odd parents of every odd-plus-odd even gate. Even-plus-even gates
add no graph edge. Every component contains an odd input, because an odd gate
always attaches its new vertex to an earlier odd parent.

Let P be the partition of odd input indices induced by the final components.
Inducting through the original circuit proves that an even value has even
weight on every part, while an odd occurrence has odd weight exactly on its
component's part. This induction is valid with the final partition: the two
parents of an odd-plus-odd gate are in the same final component. Conversely,
the difference between two input units in one component is the sum of edge
labels on a connecting path. Every such edge label is an even value already
present in the circuit. These differences, together with W0, span precisely
the vectors even on every part. Thus the even-value span modulo W0 has rank
r=s-c, where c is the component count.

If O is the number of odd gates, k the number of odd-plus-odd gates, and d
the number of even-plus-even gates, the graph has s+O vertices and O+k edges.
Its cycle rank is mu=k-s+c=k-r. Therefore E-r=mu+d exactly, where E=k+d.
This counts physical gate occurrences. Duplicate values do not invalidate it.
Loops and parallel edges may be retained using the usual multigraph cycle
rank and binary incidence equations. When s=0 the graph is empty, r=mu=0,
and every gate is even-plus-even; the formulas remain valid.

## Exact minimum even-gate count for odd targets

For an all-lambda-odd required target set, call P compatible if each target
has odd support on exactly one part of P. A circuit's component partition is
compatible, hence E>=s-c_max, where c_max is the maximum compatible part count.

This bound on the *number of even gates* is attained. Choose one odd input
root in each part, and compute the star pairs e_i+e_root for every other index
in that part. There are s-c_max pairs, independent modulo W0. Each required
target is one chosen root plus a combination of those pairs and the initially
even coordinates. Accumulate that combination starting at its root. Every
new gate in this accumulation is odd. Empty sums simply use the input root.
Thus no further even gate is needed.

The attainment does not minimize total gates. It can introduce many odd
helpers. For distinct non-input odd targets numbering m, writing H for all
remaining odd gate occurrences gives the exact accounting

    G = m + H + s-c + mu+d.

Consequently an improvement beyond the target-only parity bound must control
the joint tradeoff involving H, the partition, and the defect. The note must
not mistake the attained even-gate minimum for an attained total minimum.

## Marked transport: the quotient must use only odd aggregates

Attach actual source labels as formal ports at physical copy-tree positions
and transpose literally. Keep different value occurrences separate even when
their ordinary masks agree. Let S_v be the sum of labels on one occurrence's
copy tree. Assume the source parts of the reversed designated targets belong
to D; reversed ordinary terminal inputs have zero source part.

The useful base space is A=D+span(S_v for odd occurrences v). At an odd
vertex, the sum of incident full adjoint edge fluxes equals S_v plus the
boundary contribution. Hence the edge fluxes satisfy homogeneous graph
conservation modulo A. After choosing a spanning forest, its tree fluxes
are sums of chord fluxes by cuts. The mu chord fluxes therefore span all
odd-gate and odd-plus-odd gate adjoints modulo A. The d even-plus-even gate
adjoints supply at most d additional directions. If Q denotes the span of
ordinary gate-adjoint source parts, this proves

    dim((A+Q)/A) <= mu+d = E-r.

For an even computed occurrence, its aggregate equals its root adjoint plus
the sum of reader adjoints and ordinary terminal contributions. For an
initial even coordinate occurrence, replace its root by the designated
reverse target, whose source part is in D. Thus all even aggregates also
belong to A+Q. Conversely, reverse-topological adjoint recursion puts every
gate adjoint in the span of all occurrence aggregates. It follows that
A+Q equals D plus the span of all occurrence aggregates.

Including *all* aggregates in the base quotient from the outset would make
the proposed transport statement vacuous: then Q is already in that base
space by the same recursion. The corrected odd-only quotient is essential.

Q concerns ordinary gate-adjoint roots and non-port reader contributions,
not arbitrary partial accumulators inside a copy tree. Modulo A+Q, a physical
copy-tree wire can still carry a subset sum of its own occurrence's port
labels. No early availability or separate source-gate credit follows.

## Direct sharp examples

On three inputs compute h12=x1+x2, h23=x2+x3, and h13=x1+x3, and designate
these as ordinary outputs. Attach one source port with the same nonzero
actual label a to each helper. There are no odd ports. Each reversed input
boundary receives a+a=0 in source part, so take D=A=0. All three helper
adjoints have source part a. Thus the transport rank is one, attained with
E-r=3-2=1, mu=1, and d=0.

For the other defect mechanism, compute h13=h12+h23 instead. With the same
three ports, the h13 adjoint has source part a while h12 and h23 each have
source part a+a=0. Boundary source parts are again zero. This attains rank
one with mu=0 and d=1. Independent copies with independent labels attain
arbitrary sums of these defects. These specified constructions require no
search and show that both physical defect terms are necessary.

## Review conclusion

The corrected odd-aggregate transport theorem and exact gate decomposition
are valid for unrestricted XOR circuits. They remove the earlier independent-
even-helper hypothesis by measuring its failure with actual circuit gates.
They do not yet supply a target-only lower bound on the remaining tradeoff,
and they do not automatically charge local repeated-port paths. Those are
the substantive open issues for an unrestricted complexity argument.

The accounting concerns one chosen parity functional at a time. Taking the
maximum of separately valid lower bounds is legitimate; adding accounts for
different parities would require an additional argument controlling overlap
of their physical gate charges. The star construction also shows that every
all-odd target set admits some circuit with zero even defect, at the possible
expense of many odd helpers. Target geometry therefore cannot force positive
defect alone without incorporating that tradeoff.

## Final-note check

I read the complete saved main note, including its second, matrix proof. The
boundary identity is the literal marked network's linear transfer equation:
each occurrence aggregate contributes its ordinary value tensored with that
aggregate. Modulo D and the odd aggregates, the even aggregate coefficients
lie in the relation space of the even occurrence matrix. Including initially
even coordinates, that matrix has n-s+E columns and rank n-s+r, so its nullity
is E-r. Its coefficient rank is exactly q by the proved aggregate-space
equality. This supplies an independent proof of the rank inequality.

One wording correction was requested: the span of initially even coordinate
inputs is an algebraic quotient space, not a set of physically free computed
sums. The proof and attainment construction already respect this distinction
by adding actual coordinate inputs one at a time. With that clarification,
the final theorem statements, witnesses, attribution, and scope pass review.
