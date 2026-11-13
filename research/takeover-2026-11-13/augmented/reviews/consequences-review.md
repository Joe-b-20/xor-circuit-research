# Line review of the exact joint cost and the 85-gate bound

2026-11-13. Independent machine proof review of [CONSEQUENCES](../CONSEQUENCES.md). No circuit search or finite-family checks were run. The prior [exactness review](exactness-review.md) contains the full independent reconstruction.

## Joint cost

After normalization, the first-sheet ancestor union \(C_0\) avoids \(b'\), so its gates are distinct from the counted \(b'\)-bearing gates. Restricting to the second sheet's cones and treating every off-\(b'\) operand as free gives the ten-gate lower bound on the latter count, even if a zero-\(b'\) gate is a consumer-block exit. The first-sheet cone itself costs at least ten. J10 excludes a ten-gate cone at total 21 or below. A cone of at least twelve already costs 22 together with the consumer. The remaining budget is precisely eleven in the first cone and ten bearing \(b'\), leaving no additional paid supplier gate.

The ten-gate consumer's actual entry labels must lie in its required diagonal space, by the quotient/deletion bound. These labels span the diagonal space because the output free parts do. No nonzero diagonal is a base coordinate or a wholly free value. Thus three independent diagonal gates must occur inside the eleven first-cone gates. A12 excludes that supplier. The specified twelve-gate supplier and ten-gate consumer attain the resulting 22 under the no-feedback hypothesis. Their event-freeness also proves attainment within the narrower joint block-monotone class.

## Disjoint counting

The set \(H\) for sheets 0 and 1 is the union of the two output cones, including their outputs, less the zero gates and the gates supported on block 7 alone. The cone property places all its values on blocks 7, 0, and 1. Omitting the excluded gates is legitimate when every block-7 mask is free. The resulting first-sheet cone avoids block 1, so J22 applies to \(H\). This does not require support growth at intermediate edges.

For each \(j\) outside \(\{0,1,3\}\), the sheet charge counts only gates nonzero on block \(j\) in the sheet-\(j\) output cones. Distinct own-charge families cannot overlap, because two distinct own indices never appear in each other's windows. The enlarged sheet-3 family additionally counts its cone gates nonzero on both 2 and 7. A gate with both blocks cannot belong to another sheet cone, since only \(W_3\) contains both. These families have sizes at least \(10,13,10,10,10,10\) for sheets 2 through 7.

An intersection with \(H\) would have support contained in \(\{0,1,7\}\cap W_j\). For \(j=2\) this is \(\{1\}\), which cannot carry block 2. For \(j=3,4,7\) it is \(\{7\}\), which is excluded from \(H\) and lacks the extra sheet-3 condition. For \(j=5,6\) the intersection is empty. Hence all counted gates are disjoint and their total is at least \(22+13+5\cdot10=85\). This uses the cone definition of block monotonicity and does not require a direct-sum principle.

## Generic repair baseline

Every event-free repaired circuit is block-monotone, so a repair theorem using only an event-free lower bound can take \(B=85\). For the projected-value form, \(B\le|P|\) and the reduced circuit has \(G=|V|\), giving
\[
G\ge85+|V\setminus P|-|P\setminus V|.
\]
If \(V\) is defined as distinct nonzero non-input original gate masks, the weaker displayed inequality also holds unreduced, with the optional extra term \(G-|V|\) as in PROJECTION. The improvement does not automatically alter older bounds that count additional slack from specific gate families. None of these deductions changes the unrestricted interval \(75\le L\le88\).
