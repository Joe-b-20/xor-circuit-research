# What complete row sets force

**Later continuation:** [actual supplier compatibility](../compatibility/README.md).
The new coset-cap theorem excludes the wholly nonclean eleven-gate interface after any
ten-gate first sheet. The general joint 21-to-22 gap remains open.

2026-11-13, continuing reviewed commit `eb9191a`. The new results have hand proofs and independent machine reviews. They are not formally verified or human-certified. The unrestricted interval remains **75 <= L(MixColumns) <= 88**; no optimality of 88 is assumed.

## Exact local costs distinguish supplying values from using them

[PORTS](PORTS.md) treats one four-row sheet whose own parts are the four triples `E_c` and whose neighboring parts are the cycle pairs `s_c`. There are `p` ordinary neighboring blocks, supplied as coordinate inputs, and `f` free neighboring blocks, each supplying all of its single-block vectors at no cost. Outputs contain all these neighboring terms simultaneously. The exact paid cost, even allowing unrestricted cancellation, is

    6                 if p=f=0;
    3f+7              if p=0, f>=1;
    4p+3f+8           if p>=1.

Matching constructions are event-free. This includes the old 10/13 free-neighbor lemmas and gives the mixed case `L(1,1)=15`. In the transpose, every free block demands three independent even traces. They can share the same extra mirrored gate; once an ordinary neighbor is present, four adjacent-pair traces are already required. This explains the different marginal costs without assuming that gates used by different global sheets are disjoint.

## A tight sheet forces its source interface

[FOUR_ROWS](FOUR_ROWS.md) considers a different situation: `r` disjoint own blocks each produce `k>=2` alternative four-row sets `E_c(Z_i)+s_c(X_j)`, one set per source block. Any event-free circuit has at least

    (6+4k)r + min(r,4k)

gates, and the bound is exact for `r>=4k`. Each sheet needs `6+4k` own-block-carrying gates. Equality forces all `4k` physical source pairs. If any source pair is absent, every sheet pays at least one extra gate; if all are present, the circuit pays for them outside the sheet charges. This is a concrete theorem that connects a tight local bound to a globally paid interface.

For a tagged two-source family retaining output weights 5/7, boundary relation distance six, and small blocks/windows, the event-free optimum is `22r+8` for `r>=8`. The natural shared-translation circuit has `22r+12` gates and eight hidden gates. Thus the simplest full-four-row lift of the earlier [sparse sharing counterexample](../continuation/SPARSE.md) loses its savings. This is a result about that architecture and map, not a prohibition on cancellation in other four-row circuits. The 28-gate `Q_3` counterexample to generic sheet additivity still applies.

## The parity partner is forced, but can already be paid for

[COMPLETIONS](COMPLETIONS.md) specializes the affine-completion theorem to actual MixColumns row spans. For a single maximal-window sheet, a component's local completion set is empty, a singleton, or a pair differing by the own-block parity. The pair requires all four rows and lies inside one foreign window; merely switching between windows creates no further direction.

If four designated output events use only three nonlocal operands, their equations form a three-vertex path with two local partners at the endpoints. Those partners differ by the own-block parity. At least one is a physical gate in another window containing the own block. However, a specified 145-gate MixColumns circuit has exactly those four output events and exactly three hidden gates: the parity partner is retained and charged to sheet 6. The hidden-work lower bound is sharp for this profile, and the partner cannot automatically be charged again.

The same note gives exact symbolic equations for two-sheet window intersections, including the two-dimensional `R^2` kernel that is missed by simple rank-three reasoning. A specified sheets-2/3 profile forces six hidden operands; after repair credits this only gives 74 and does not improve the known unrestricted bound.

## A rigid interface without clean suppliers

[JOINT01](JOINT01.md) proves a sharp eleven-gate theorem for a four-triple sheet whose
required free labels span a three-dimensional space D, but whose actual entry labels
all avoid D. Equality forces five labels in one affine coset, with five influence traces
of rank four: four odd and one even. An explicit eleven-gate construction attains the
bound when an outside-D label is available. This identifies an exact supply obligation
instead of treating arbitrary combinations of available values as free.

For the actual joint 0/1 problem, a ten-gate first-sheet circuit already contains a clean
diagonal value. The note gives it explicitly, refuting a tempting shortcut. The joint
21-to-22 gap stays open: the new theorem covers interfaces avoiding every clean label,
while mixed interfaces and the eleven-gate augmented first-sheet problem remain unresolved.

## Judgment

The useful shift is from asking only how many hidden operands exist to asking what an implementation at its local minimum must expose as an interface. The source-saturation theorem gives one exact instance. The parity-partner witness explains why geometrically forced local values are insufficient by themselves: they may already be useful, retained, and charged elsewhere.

For actual MixColumns, a new numerical improvement still needs a compatibility argument across its fixed windows that counts physical work once. The exact local formulas and completion geometry are inputs to such an argument, not a substitute for it. The unresolved joint-sheet 21-versus-22 problem remains a focused test; further hidden-count refinements should first survive the explicit sharp witness.

## Review and direct verification

Independent reviews: [ports](reviews/ports-review.md), [second ports review](reviews/ports-second-review.md), [source saturation](reviews/source-saturation-review.md), [completion geometry and witness](reviews/completions-review.md), and [joint interface](reviews/joint01-review.md). A review prompted explicit re-trimming after free-value redirections in the port proof; this ensures the transposition reader count is applied only to live signals. The first free neighbor's four-gate cost is distinguished from the three-gate increment for later neighbors.

Run from the repository root:

```sh
python3 research/takeover-2026-11-13/row-cost/check_row_cost.py
python3 research/takeover-2026-11-13/row-cost/check_completions.py
python3 research/takeover-2026-11-13/row-cost/check_joint01.py
```

[Saved results](check-results.json) cover eight specified local constructions and the tagged `r=8` translation/clean constructions (188 versus 184 gates). The separate completion verifier checks all 32 MixColumns masks, reducedness, liveness, the exact four events and three hidden gates, and retention of the parity partner. The joint-interface verifier checks both displayed circuits, their entry counts, and the eleven-gate example's label and trace ranks. The universal lower bounds are the hand proofs, not these examples. No SAT, circuit search, exhaustive enumeration, exact least-gate search, or computer-driven case elimination was used.
