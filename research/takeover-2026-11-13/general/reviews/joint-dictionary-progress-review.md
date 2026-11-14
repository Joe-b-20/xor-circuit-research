# Final scope review: joint dictionary computation and closure

2026-11-14. Independent machine review of the current
[general synthesis](../README.md), [checkpoint](../../CHECKPOINT.md),
[summary](../../SUMMARY.md), and [record, section 50](../../../structure-2026-11-11/RECORD.md).
The three complete mathematical notes have separate independent reviews. This
pass checks the synthesis and specified-construction evidence against those
arguments. It is not formal verification, human certification, or a novelty
assessment.

## Actual preparation and the individual-profile barrier

The synthesis correctly distinguishes initial remaining cost, prepared remaining
cost, and the cost of reaching the prepared state. The prefix is an actual
coordinate-input computation retaining every intermediate. Its 4rm gates are
explicitly charged separately, and no end-to-end improvement is claimed.

The quotient sends every supplied even value to zero and every supplied odd
value to a coordinate unit. Each target has quotient weight 2r+1, forcing at
least 2r+1 odd dictionary members in every representation. Together with the
original coordinate representation, this gives the complete individual
frontier (r,r) at both states. The comparison is not merely about one chosen
representation or one gate-price choice.

The stated joint frontiers (rm,rm) and (r,m+r-1) match the complete proofs.
The initial lower bounds retain arbitrary mixing of the disjoint target blocks
and unused anchor inputs. At the prepared state, the first target forces r
units of P and every subsequent odd target forces another, while one target
already forces K>=r. The displayed common-offset computation attains both.

The resulting ratio is unbounded along m=r, but only for remaining cost at
the two stated boundaries. Pairwise target differences become much shorter,
so the full dictionary metrics are explicitly not claimed equal. The square
all-odd involution retains free coordinate identity outputs and does not alter
these continuation counts.

## Joint normal form and its unresolved residual

The joint lift uses one common formal circuit and therefore retains its shared
gates. The matrix constraint RB=T encodes dependence in the actual dictionary;
it does not supply its span as free operands. Column compression yields the
exact disjoint-member-group preparation cost plus a residual distinct-pattern
network. The groups may overlap in ordinary coordinate supports and project
to dependent values, as the synthesis correctly allows.

The residual is not omitted or declared solved. The B=I example demonstrates
that it can be the entire original circuit problem. Neither representation
minimization nor the residual complexity is claimed efficiently computable.

The two-target formula charges the helper h through its actual dictionary
length and omits zero residual arms without requiring a physical zero. It is
an exact consequence of the general normal form, not an imposed restriction
on competing circuits. The synthesis explicitly forbids summing independent
pair bounds across outputs or turning this into a restricted casework queue.

## Saturation by a paid difference basis

The target family is the full union of c>=2 unit-pattern cosets of the space
even on each coordinate part. The r=n-c basis values are physically computed.
Traversal uses only these supplied basis members and already reached targets;
the remaining even span is not granted for free. Complete target closure is
the reason each subsequent odd gate can produce a required output.

The compatible-partition lower bound and exact resource identity justify all
the reported every-optimum claims: even rank r, E=r, and H=d_EE=mu=0. Input
partition uniqueness is limited to c>=3. The absence of odd-occurrence cycles
is not promoted to a full-ancestor forest claim. The synthesis does not impose
this target closure or a fixed uncharged supply basis on MixColumns or on
arbitrary sparse target maps.

## Specified verification

I inspected [check_joint_dictionary.py](../checks/check_joint_dictionary.py)
and its [saved result](../checks/joint-dictionary-result.json). The imported
helper module provides definitions; its main routine is guarded. The checker
uses fixed r=m=3 and one fixed five-input coset example, with no circuit,
representation, or parameter search.

For the common-offset example it verifies 27 coordinate inputs, all 36 prefix
gates and their retained values, target absence at the prefix boundary, the
supplied translates, and h's absence. The initial construction has resources
(9,9) and 18 gates; the prepared suffix has (3,5) and eight gates. The quotient
checks certify the stated individual (3,3) frontier without optimizing over
representations. The changed two-target difference representation is checked.

The two fixed lifts have respectively 21 used members with three patterns,
and nine used members with four patterns. Their preparation counts 18 and five
agree with the displayed group constructions; the latter residual contributes
three target gates. The seven-gate two-target shared budget is the corresponding
common-helper formula with six anchor terms and two supplied one-term arms,
not a result of a least-gate search. Matrix rank and direct composition verify
the square involution.

For the partition of sizes 2,2,1, the explicit nine-gate circuit produces twelve
distinct values satisfying the required unit part-parity condition. Equality
with the known coset cardinality proves complete coverage without enumerating
all vectors. The counts E=2, O=7, even rank two, and H=d_EE=mu=0 agree with the
theorem and saved assertions.

The synthesis and specified evidence pass this review. Previous full-cycle,
parity-cycle, rank, and physical-pair distinctions remain intact, and certificate
ceilings retain their named scopes. Unrestricted MixColumns stays 75-88. No
consequential correction remains necessary.
