# Final scope review: physical intersection repair and its joint limitation

2026-11-14. Independent machine review of the current
[general synthesis](../README.md), [checkpoint](../../CHECKPOINT.md),
[summary](../../SUMMARY.md), and [record, section 49](../../../structure-2026-11-11/RECORD.md).
The three mathematical notes have complete individual reviews. This pass
checks the synthesis and specified-construction evidence against those proofs.
It is not formal verification, human certification, or a novelty assessment.

## The positive theorem retains physical availability

The synthesis correctly uses the full ancestor multigraph cycle rank beta,
with both operand ports retained. It does not substitute the parity-specific
odd-occurrence cycle rank mu. The common branch count is beta+k-c, obtained
from actual reader and terminal ports. The Boolean-function identity sums
ordinary physical values with their local reader defects; internal terms
cancel by the original gate equations. Its shared dictionary consists of
actual occurrences, not arbitrary elements of their span.

For two ports, the coordinate product has no terminal correction and gives
the support intersection. A connected cone union provides at most beta+1
dictionary terms. The resulting at-most-beta appended-gate statement is
correctly confined to nonzero intersections. Distinct marked occurrences
permit the selected branch values before the later result. Coincident ports
and zero-output conventions are not silently folded into that strict timing
claim.

The sharp examples distinguish two claims. The block quotient proves an exact
word length from the specified dictionary, and hence an exact appended cost.
Private attachments make a displayed all-odd square implementation optimal,
but this is not promoted to a lower bound after freely rewiring an enlarged
target problem. The synthesis repeats this distinction where needed.

## Causal forest and simultaneous repair

The forest quotient retains the causal equations for the shadow inputs. The
same original gate occurrences supply their earlier source values, and the
triangular kernel basis records that chronology. A small kernel is not described
as providing arbitrary linear forms for free.

For the one-cycle family, the original and enlarged target problems have exact
costs 2m+2 and 3m, with arbitrary rewiring allowed in both minima. Thus m-2 is
the extra optimal total cost, rather than a claim about blindly appending one
gate for each missing value. The example has full beta=1 but d=mu=0. Its m-1
missing intersections are independent and individually one XOR away; neither
that raw rank nor the simultaneous repair cost has a constant charge per beta.
The square map is correctly called invertible, without claiming an involution.

Column cloning supplies the exact binary-size reduction used in those proofs.
The broader co-occurrence projection statement keeps a temporary root in each
component missed by the retained set. No direct-sum assumption or preservation
of gate parities is inferred. The treatment of zero targets is explicit.

## Rank-only ceiling

The boundary span for all normalized Boolean functions is exactly the space
of indicators of the distinct nonunit column-pattern classes. The corrected
boundaries for non-normalized functions remain in that same span. Its rank-only
consequence is therefore G>=n+p-k. With n<=32,
p<=min(32,2^k-k-1) bounds this certificate by 58: k<=5 gives at most 53 and
k>=6 gives at most 64-k<=58. This requires no row-subset enumeration.

The synthesis properly limits this conclusion to the named boundary-rank
certificate. It does not rule out stronger constrained branch decompositions,
all nonlinear invariants, or a numerical MixColumns improvement by other means.
The earlier 57 and 60 ceilings are likewise retained with their named scopes.

## Specified verification

I inspected [check_intersection_repair.py](../checks/check_intersection_repair.py)
and its [saved result](../checks/intersection-repair-result.json). The imported
earlier helper module supplies definitions only; its main routine is guarded.
The checker constructs two fixed parameter examples and one fixed repaired
construction. It performs no circuit, representation, or parameter search.

For m=4 it verifies ten inputs, ten original gates, twelve repaired gates,
three independent missing masks, and the displayed inverse of the square map.
The parity graph has mu=0 while the selected pair's full ancestor union has
beta=1. The branch certificate has two terms, as expected. Every required
original and added intersection mask is evaluated directly.

For t=3 it verifies the sharp square involution on 21 inputs with 22 gates.
Its two designated cones contain 11 inputs and 12 gates, hence beta=2, and
the branch identity selects three terms. The block quotient sends all computed
values to zero while the intersection has three nonzero quotient coordinates,
which checks the stated dictionary-length lower certificate without optimizing
representations. Direct composition checks the involution.

For both examples the spanning-forest routine cuts the specified nonforest
operand ports, computes all formal masks, and verifies projection back to every
ordinary value. The kernel relations have the asserted rank and depend only
on earlier shadows. Reader lists preserve duplicate ports; neighbor sets are
used only to determine component connectivity, where multiplicity is irrelevant.

The reported results agree with the constructions and proofs. Unrestricted
MixColumns remains 75-88, and the next task is stated as joint computation from
one common physical dictionary, not further restricted casework. The synthesis
and specified evidence pass this review; no consequential correction remains.
