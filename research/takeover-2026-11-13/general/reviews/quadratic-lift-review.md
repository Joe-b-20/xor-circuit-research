# Independent review: quadratic lift and its limitation

2026-11-14. Primary-agent hand review of
[QUADRATIC_LIFT_LIMIT.md](../QUADRATIC_LIFT_LIMIT.md), developed independently by
another agent. A second independent reviewer also checked the symbolic argument.
This is machine review, not formal verification or a literature-novelty claim.

The coordinate quadratic lift has the stated polarization a wedge b in
characteristic two. Recursively expanding lifted gate results counts a gate's
local defect with exactly its output path-parity vector. This proves the tensor
identity for arbitrary fanout and cancellation, including outputs that are also
used internally. The zero lifts at coordinate inputs leave no omitted terms.

The odd-list formula follows by appending two vectors: its increment is
s wedge u+s wedge v+u wedge v=(s+u) wedge (u+v). For coordinate row supports,
selecting a common triple leaves the quadratic form on the odd-length list
consisting of that triple's sum and the remaining coordinates. Thus the prescribed
shared triple costs one atom and the rest costs (w-3)/2 per row.

The saved MixColumns row formula has twenty rows of weight five and twelve of
weight seven. Within each of the sixteen designated row pairs, the two own-block
coordinates and one neighboring-block coordinate displayed in the note belong to
both supports. Their shared triple contributes one common simple bivector with
influence equal to the sum of the two row units. The remaining atoms retain their
individual row influences. The count is 5*6+3*10=60, equivalently 76 separate
row atoms minus sixteen saved atoms. This establishes an explicit ceiling for the
relaxation; it makes no claim that sixty is its optimum.

Consequently even an exact lower-bound analysis of this unconstrained tensor rank
cannot recover the existing 75 circuit bound. The distinction from a sixty-gate
circuit is essential and correctly stated: the atom model does not pay for the
availability of parents or require one network realizing all influences. The
negative conclusion concerns this specified relaxation, not every quadratic or
higher-order method with additional constraints.
