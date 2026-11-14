# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`bd1b808`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Our isolated worktree is this chat's `work/xor-structural`.
Other worktrees and `search/proposals/` are preserved.

## Direction and current judgment

General unrestricted mathematics is the priority. The user rejects incremental
numerical bounds and restricted casework without a clear unrestricted payoff.
The twelve-consumer queue remains deferred. No SAT, circuit enumeration, exact
search, or computer-driven elimination. Hand arguments, supporting linear algebra,
and direct checks of specified constructions are allowed.

Read [the general synthesis](general/README.md) first. The latest phase establishes
joint cost laws and exact obstructions to two tempting simplifications.

## Joint computation and supply

[Private tagging](general/PRIVATE_TAGGING_TRADEOFF.md): appending B disjoint private
coordinate inputs across nonzero core targets increases exact binary complexity
by B. Sequential projection deletes one distinct gate per private coordinate,
even if the original circuit mixes them and cancels. One/two private coordinates
per row embed arbitrary nonzero-row computation into an all-odd invertible
involution with exact known overhead between m and 2m.

For graph-tagged targets x_u+x_w+z_e, with v vertices, m edges and c components,

    L_2=2m,       L_3=m,       r_min=v-c.

Core identity outputs make the map invertible without changing these values.
The separate-minima gap is exactly beta=m-v+c. Every unrestricted circuit obeys

    (r-r_min)+H+d+mu>=beta.

For K_q every nonnegative integer split H+d+mu=beta is attained at r=q-1 and
total optimum 2m. The exact (k,P) frontier is (K,2m-K), q-1<=K<=m, with k counting
OO gates and P=O+d. The ratio L_2/(r_min+L_3) tends to two in this family only.
The minima of k and P are incompatible. The minima of rank r and P can coexist
here, with mu=beta: their sum still misses redundant physical supply. Do not
claim that this example proves incompatibility of minimum rank and minimum P.

## Tree rigidity and unavoidable even aggregation

[Tree intersections](general/TREE_INTERSECTION_RIGIDITY.md): G>=n-kappa for n
supported coordinates and kappa target support-overlap components. Equality
forces a forest ancestor graph; every nonempty intersection of physical supports
is a physically present value. Extra canceled input ancestors are counted.
The componentwise statement applies even when other components have cycles.

For the three-supplier pattern e=a+b, f=c+d, h=e+f, duplicate private odd outputs
force all suppliers and force the EE gate in every optimum. With b disjoint
copies on N inputs, every circuit satisfies G>=N-b and G+d>=N, allowing arbitrary
cross-copy mixing. Exact optimum under d<=D is N-min(D,b), D a nonnegative integer.
Removing all EE costs exactly b; minimal copies give 9b versus 10b. No direct-sum
assumption. A connected binary hierarchy also forces its optimal wiring and
arbitrarily many EE gates; no removal-gap formula is claimed for that hierarchy.

## Single-target frontier and scope

[Single target](general/SINGLE_TARGET_PARETO.md): for any actual dictionary S and
nonzero z, representation R with o odd/e even members and I=parity(z) has
(K_R,P_R)=((o-I)/2,(o+I)/2+e-1). Every unrestricted continuation is dominated by
one such point in both coordinates; every point is attainable by a formula.
This gives the exact discrete frontier and every nonnegative price combination.
The same representation is chosen before assigning prices. Individual target
formulas cannot be summed across outputs without preserving shared work.
The two-point dictionary example is not a coordinate-prefix or whole-map claim.

## Evidence, retained work, and next task

All three notes have independent machine reviews linked within them. The primary
agent also checked the proofs. These are not formal verification or human
certification; no literature-novelty claim is made. A
[final scope review](general/reviews/joint-supply-progress-review.md) checks the
synthesis, specified evidence, and the distinction between rank and pair count.
[Specified checks](general/checks/check_joint_supply.py) and
[saved results](general/checks/joint-supply-result.json) verify a mixed K_5 example
(H=d=mu=2, G=20), its square involution, three supplier-copy constructions, a
connected hierarchy, and both one-target dictionary constructions. No search.

Retained: [ternary normal form](general/AVAILABLE_SUPPLY.md),
[multi-output preparation](general/MULTI_OUTPUT_STARTUP.md),
[parity accounting](general/ODD_COMPONENT_DEFECT.md), and earlier exact families.
The total-parity support certificate for MixColumns is capped at 57; its profile
is exactly one. This is a certificate ceiling, not a MixColumns circuit bound.
The old restricted 85/local 22 arguments remain historical, not the active queue.

Next: find a joint cost mechanism beyond private-coordinate separation. The
forest theorem forces shared intersections physically; general circuits can
avoid that rigidity through reconvergence/cancellation. A useful extension must
control their combined effect, not charge every missing intersection independently.
A different framework is allowed. Unrestricted MixColumns remains 75<=L<=88.

History: [summary](SUMMARY.md), [record](../structure-2026-11-11/RECORD.md).
Use Git with `-c core.filemode=false`; shared configuration is unchanged.
Stage only intended research files.
