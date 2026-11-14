# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`0cb775c`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Other worktrees and `search/proposals/` are preserved.
Our worktree is this chat's `work/xor-structural`.

## Active direction: general unrestricted arguments

The user explicitly redirects the research away from incremental lower-bound
improvements and restricted arguments without a specified unrestricted use.
The fixed-budget twelve-consumer case breakdown is no longer the active task.
Preserve its reviewed results; do not resume it merely because its cases are open.

The organizing problem is a general account of how sharing and cancellation trade
one kind of computation for another, counting each physical gate once. Restricted
lemmas need an explicit role in an unrestricted theorem. No assumption that 88 is
optimal, and no circuit search, enumeration, or computer-driven case elimination.

Read [the general research direction](general/README.md) first.

## Reviewed unrestricted results and their limits

[Parity components and dependent even work](general/ODD_COMPONENT_DEFECT.md):
for any parity functional, s odd coordinate inputs, c odd-graph components,
E even gates, cycle rank mu, and d even-plus-even gates,

    effective even rank r=s-c,       E-r=mu+d.

The partition-span theorem is a historical foundation, explicitly attributed.
The occurrence-graph proof gives exact physical gate accounting. For m required
odd non-input targets and H other odd gate occurrences,

    G = m+H+(s-c)+(mu+d).

The minimum EVEN-gate population for all-odd targets is exactly s-c_max over
compatible partitions. A star-pair construction attains it, possibly using many
odd gates. It has defect zero. Thus targets alone cannot force positive defect
in every circuit; the missing theorem must control the joint cost.

For arbitrary marked ports and literal transposition, quotient by the source
boundary D plus ODD occurrence aggregates. The rank q of the remaining ordinary
adjoints/even aggregates satisfies q<=mu+d. This removes the earlier assumption
of independent even helpers. Both cycle and even-plus-even terms have specified
sharp witnesses. The rank proof also has a short matrix-kernel formulation.

Important limits: occurrence aggregates are not equal-mask classes; membership
in a span grants no physical value or early availability. Internal copy-tree
partial sums can remain outside the aggregate span. Quotienting by ALL aggregates
would make q identically zero. An invertible whole-map boundary can also make the
bound vacuous. Costs from different markings or parities cannot simply be added.

[Quadratic lift limitation](general/QUADRATIC_LIFT_LIMIT.md): an exact unrestricted
tensor identity counts each physical gate once. Its unconstrained atom model
nevertheless admits a specified sixty-term MixColumns decomposition. It cannot
recover 75, because it loses the supply cost of parent values and compatibility
of their output influences. This is not a sixty-gate circuit. The direct checker
and successful output are saved under general/checks; no search is involved.

Both notes have hand proofs and independent machine reviews, not formal
verification or human certification. The primary agent independently checked them.

## What remains established

Unrestricted MixColumns remains 75<=L<=88. Earlier restricted results remain
valid: block-monotone lower bound 85; no-feedback two-sheet minimum 22; exact-ten
and exact-eleven consumer joint minima 22. The twelve-consumer candidate below 22
reduces to six target-live entries of rank five. Its charged-forest decomposition,
trace multiplicity cap, parity restrictions, and specified exclusions are retained
in [the previous frontier](feedback/CHARGED_FRONTIER.md). That local case remains
open and is deferred under the new research direction.

[Takeover summary](SUMMARY.md) and the historical
[record](../structure-2026-11-11/RECORD.md) preserve prior proofs, failed approaches,
and references, including the withdrawn local-exposure counting inference.

## Next mathematical task

Seek a target-dependent bound on the combined cost of extra odd computations,
component merging, and dependent even computations, or a different general
invariant that controls actual shared work more directly. Do not optimize parity
counts alone: their exact attainability is already understood. Do not strengthen
the unconstrained quadratic tensor rank: its sixty-term ceiling is decisive.

Any proposed application must explain how its unavoidable quantities follow from
the target map and how shared gates enter the final count once. A whole-circuit
tradeoff theorem is the objective; another fixed-budget exclusion is not.

Use Git with `-c core.filemode=false`; shared configuration is unchanged.
Stage only intended research files.
