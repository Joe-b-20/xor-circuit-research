# Final scope review: joint supply costs and structural rigidity

2026-11-14. Independent machine review of the current
[general synthesis](../README.md), [checkpoint](../../CHECKPOINT.md),
[summary](../../SUMMARY.md), and [record, section 48](../../../structure-2026-11-11/RECORD.md).
The three mathematical notes have complete individual reviews. This pass
checks the synthesis, limitations, and specified-construction evidence. It
introduces no new research claims and performs no optimization or search.

## Mathematical scope and interpretation

The private-input extension is stated for nonzero core targets and disjoint
private coordinate blocks. Its projection proof allows arbitrary original
mixing and cancellation. The all-odd involution reduction retains core and
earlier private coordinates, so its invertibility and exact overhead agree
with the complete note. For graph-tagged maps the three exact quantities
L_2=2m, L_3=m, and r_min=v-c are distinguished, as are the target graph cycle
rank and the implementation's odd-occurrence cycle rank. The joint inequality
applies to every unrestricted implementation. The complete-graph simplex and
Pareto frontier are accurately reported, and the ratio approaching two is
confined to that family.

A consequential wording distinction was corrected during this final review.
The graph family can attain minimum rank r and minimum P=O+d simultaneously:
the direct-pair construction does so while paying mu=beta. Its rank-plus-ternary
sum is insufficient because it omits redundant physical supply, not because
those two minima conflict. The incompatible minima on a cyclic target graph
are minimum physical odd-plus-odd count k=r+mu and minimum P. I checked the
revised theorem discussion, README, checkpoint, appended record clarification,
and [available-supply note](../AVAILABLE_SUPPLY.md); they now state this
distinction explicitly. No incompatible-rank/P claim follows from this family.

The tree equality theorem counts actual input ancestors, including canceled
coordinates outside the target supports. Its componentwise conclusion is
correctly retained in the synthesis. The supplier-copy lower bound allows
cross-copy mixing and cancellation, charging their physical components and
cycles instead of imposing a decomposition. The allowance D is explicitly
a nonnegative integer. The exact removal gap for separate copies is kept
distinct from forced optimal wiring in a connected hierarchy, for which no
removal-gap formula is asserted.

The single-target theorem supplies one actual dictionary representation
that dominates a continuation in both resource coordinates. The synthesis
does not weaken this to separate minima or overstate it as a multi-output
formula. Dependence in the initial dictionary is allowed; the two-point
example is expressly not promoted to a full coordinate-input-prefix claim.
The formula points, ordinary cost, and discrete-frontier interpretation match
the complete proof and its individual review.

## Specified verification

I inspected [check_joint_supply.py](../checks/check_joint_supply.py) and the
[saved result](../checks/joint-supply-result.json). The code constructs a
fixed K_5 edge list and follows one fixed list of six nonstar choices. This
is enumeration of the edges defining that specified map, not circuit or
representation search. Direct vector evaluation checks all ten targets.
The asserted populations G=20, O=12, k=6, d=2, r=4, mu=2, and H=2 agree with
the construction. Matrix rank and direct composition check its square
invertible involution.

The three supplier-copy runs are specified choices on three copies with
30 inputs and 18 outputs. Their gate counts 27, 29, and 30 correspond to
3, 1, and 0 even aggregations. The effective even rank is six in each;
H and mu are respectively 0, 2, and 3, and O+d is always 21. These agree
with the formulas and saved assertions.

The connected example has three leaf pairs and five suppliers, with two
private targets per supplier. Its N=16, G=15, O=10, k=3, d=2, r=3, mu=0,
and H=0 match the proved hierarchy counts. The supplied-dictionary example
checks only the two displayed q=2 formulas, with resource pairs (2,2) and
(0,4), plus the one-dimensional relation space. It performs no representation
optimization and explicitly records that no coordinate-prefix claim is made.

## Remaining limits

The synthesis consistently states that unrestricted MixColumns remains
75-88. The previous 57 ceiling refers only to the exhausted support-based
certificate. The new examples establish joint-cost obstructions and general
rigidity mechanisms; they are not presented as an improved MixColumns lower
bound or as a restriction on the circuits considered. The proposed next
question is to control jointly how reconvergence and cancellation evade
physical intersection requirements, without charging each separately.

Machine review and specified verification are distinguished from formal
verification, human certification, and literature novelty. The synthesis
and checker pass this scope review. No correction remains necessary.
