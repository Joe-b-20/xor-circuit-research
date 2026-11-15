# P4 status (T05 gate-record half: G <= 102 at A <= 32, AD <= 7, GD <= 32)

Updated 2026-11-15 21:35 UTC.  All P4 jobs finished (last: conj4, ~21:35); nothing queued to run.

Best at T05 limits: 103/32 (the NIST reference itself).  No circuit below 103 gates.
Best strict: none.  Best tradeoff: none.
Saved near points (aes_check OK, new Pareto points on the pinned set, not T05 classes: G 104):
- found/p4-conj236-a32-ad7-g104-gd28 (path_certified true)
- found/p4-deep236-a32-ad7-g104-gd27 (path_certified true)

Decisive negatives (NOTES.md section 2, table ~/xs-campaigns/2026-11-15-targets/P4/NEGATIVES.md):
- the 103 is optimal (G >= 103 at any GD) for its 9 level-1 and 18 output ANDs with any 4-input
  basis of the inversion interface [C]; layers: top 18 at GD 32 (17 free), pre 15, inversion 13,
  bottom exactly 25;
- no 102 over all 19,683 operand-pair choices, complement patterns, 2,040 scaled-Frobenius
  variants [C, those families];
- no 103 at GD < 32 in that case (6 possible 18-gate inversion blocks, earliest pre, optimal
  bottom) [C].
Empirical: 21 GF(2^8) conjugates + kernel (gate / trb / mix with repair_keep 1): floor 104 [H].

Open (proposal, NOTES section 4): other rank-9 decompositions of x^17 (GF(2^4)/GF(2^2)
representations), inversion blocks with more than 4 linear inputs, non-tower layouts.
