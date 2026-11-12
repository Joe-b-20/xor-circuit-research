# The interface theory on MixColumns: a transfer obstruction

Delegated investigation, phase 5 (2026-11-12), separate model instance (Opus, high effort), using the
review-ring corrections; saved by the main agent, lightly condensed. Review status in RECORD 20. Status tags:
proved = elementary hand argument (investigator's, see RECORD 20 for review); check = program output on
existing circuits. Nothing changes 75 <= L(MixColumns) <= 88. Scripts (checks): mirror_mc.py (mirror, row
assertion, arc splits), labels_mc.py (labels, forced spans), corpus_mc.py (exits over the corpus; output
corpus_s10.out), detail_mc.py, rewrite_mc.py (rewiring check), chi_mc.py (exact, used only for 4 e_min
values), chi2_mc.py (greedy upper bound for chi), far_mc.py (near and far minima per cut).

**Review (`../../review-p/REVIEW.md`), corrections to section 3.** Witness references used a cumulative line
counter: the block-7 witness is circuits_3.txt line 13114 (checked: computes MixColumns, reduced, 88 gates,
no block-cancelling gate; at block 7 near 24, far 64); "circuits_2 line 360" is line 313, "line 260"
presumably 213. The justification is "no exit at that cut" (checked for the block-7 witness only), not
"block-monotone". The near minimum 8 holds for SOME interface (the minimum over interfaces), not for every
interface. For SB*-shaped bounds the best constant supplier baseline is A = min(near + sigma) <= 9 (an
instance with one entry per required row has sigma = 1), so the provable bound is at most 9 + far(witness):
at most 73 at block 7 and 87 at the worst cuts; still short of 88. O constrains only inequalities claimed
for all circuits, not ones proved only for optimal circuits.

## Setting
- Proved (rows machine-asserted): in the mirror, R^k = E(w^k) + p(w^(k+1)) for k < 7 and R^7 = E(w^7) + p on
  w^0, w^1, w^3, w^4: seven 2-windows and one 5-window {7,0,1,3,4}.
- Check: the only triangle not inside one window is {1,2,7} in the primal, {1,2,3} in the mirror.
- At a single-block primal cut an exit is exactly a gate that cancels that whole block; the corpus's
  block-cancelling gates are exits of the primal cut theory; mirror exits are the dual objects.

## 1. Cutting out a sheet or a run
**A (proved). No cut is export-type; every cut is ring-like.** Every edge of the 8-cycle lies in a window
({7,0} inside the 5-window in the mirror; sheet 0's support in the primal), so at every arc cut required rows
cross both boundaries: no tau term, no open end; Lemma R and Theorem 19.1 have no instance. An export
boundary appears only after freeing a block (the chain runs of RECORD 16, at most 56).
**B (proved). The near side costs at least 8 at every single cut, primal or mirror, and 8 suffices for any
label interface.** The block parts to be produced (E_c and s_c, or p_c in the mirror) are 8 distinct non-unit
values, each needing a first gate; with free labels every further signal of a fibre can be an entry, booked
to the far side. Attained in an actual circuit: the recorded 97 has f = 8, h = 0 at primal block 7 (e = 32)
and at block 0.
**Forced label space W_k (proved; dimensions computed):** dim W_k = 7 at mirror groups 0, 2, 5, 6, 7 and 11
at groups 1, 3, 4; 7 at primal block 2.
**Recorded 88, 89, 97 (check, both summation orders):** all three mirrors window-local, no exit across any
arc cut of length 1-3. In the 88 (fwd) groups 2, 5, 6 are chain-like (e = 7 or 8, labels of rank exactly 7,
pure on the two neighbours, near 9 or 10); groups 0, 1, 3, 4, 7 have label rank 8-16 against 7 or 11 forced;
cuts 0, 1 carry mixed labels on {3,4}, cuts 3, 4 on {0,1} (observation only). No supplied values anywhere.
**kste corpus (check; 1,890 circuits, every 10th, fwd).** Block-monotone (423): 369 have no mirror exit at
arcs of length 1-3; 54 have exits landing on {0,3,7} or {0}, inside the 5-window (primal: at cut 7, either
7 + 37 -> 3 serving sheets 3 and 4, or 07 + 017 -> 01). Non-block-monotone (1,467): 1,464 have exactly one
mirror exit gate, seen across cuts {1}, {0,1} and {0,1,7}, value on {2,3} inside window W_2; in 730 of 731
cases (every 20th circuit) its value is a whole required row R^2_c. Primal side: the exit is at block 2 with
operands {2,7}+{1,2}, {2,7}+{0,1,2,7} or {1,2}+{0,2,7}, value on {1,7} or {0,1,7} inside sheet 1's support,
serving only sheet 1; in 532 of 731 cases it is an output of sheet 1.
**Reusable exports.** A ring has no exports; their counterpart is labels the far side already holds. The
supplied values here are targets of the receiver (or a target minus its block-0 part), not reusable
intermediate sums.

## 2. Which chain hypotheses survive
Survive: the exact split (identity); the exact reconstruction principle (TWOSIDED section 8); Lemma 5.3.1 in
ring form, far >= DL(W) + e - chi_W (DL(W) = least far cost with labels spanning a space containing W; chi_W
with W_k in place of E), by the same argument (investigator's derivation). Fail: Lemma R, Theorem 19.1, S1
(no export boundary); additivity of exit-free cuts (the far side is a 7-group object containing the 5-window,
not a shorter instance with a known value); single-group landing of exits (observed exits land on 2 or 3
groups inside a window).
**Sheets 1, 3, 4.** Proved: at mirror group k in {1,3,4} each fibre p_c(w^k) must hold two required signals,
R^(k-1)_c and R^7_c, and W_k grows from 7 to 11 dimensions (the third interface). Check (all 1,898 mirrors of
949 circuits, both orders): near >= 11 at groups 1, 3, 4 against 9-11 elsewhere; in practice the third
interface is paid on the near side; by B it is not forced without an interface type.
**The {1,2,7} triangle: same shape as Q_3, different issue from the chain's.** Same: the exit lands inside a
window (primal value in sheet 1's support, mirror value in W_2). Different from sbx5: the supplied value is
the receiver's own target, not an intermediate sum; honest cost 4 or 5 earlier labels (beta = 2 or 3); exact
e_min at the cut 9 or 10 against e = 10 or 11 (4 circuits checked exactly), so little label surplus;
chi_up - e is 1 to 3 (greedy upper bound), so the ring form of 5.3.1 does not show these exits useless,
unlike sbx5 (chi - e = 0). No free rewiring (check, every 50th circuit): none of 319 block-cancelling gates
can be rewired to two non-descendant signals avoiding the cancelled block.

## 3. Outcome for 87: an obstruction
**Obstruction O (proved from B plus verified witnesses).** For any single cut k (a primal block or a mirror
group), any bound of the form cost >= near_min + Far_min(W_k), with both sides minimised over all label
interfaces, is at most 8 + (far cost of any circuit). Witnesses (each exit-free, block-monotone, verified,
so its far part is a standalone instance):

| Cut | Witness | min far | Bound |
|---|---|---|---|
| primal block 7 | kste circuits_3 line 15380 (near 24) | 64 | at most 72, below 75 |
| mirror group 1 | kste circuits_2 line 360 | 71 | at most 79 |
| mirror group 4 | circuits_2 line 260 | 73 | at most 81 |
| mirror group 3 | circuits_1 line 40 | 74 | at most 82 |
| primal block 3 | | 76 | at most 84 |
| primal blocks 0, 1; mirror group 0 | | 77 | at most 85 |
| all other cuts | recorded 88 and others | 78 | at most 86 |

**Consequence.** A perfect SB*-type comparison (supplier charge >= receiver gain) at a single cut yields at
most near_min + Far_min, i.e. at most 86 anywhere (72 at block 7): it cannot exclude 87. **Mechanism:** the
witnesses that make the far side cheap make the near side expensive (near 24 against far 64 at block 7); cost
moves across the cut through the label interface (entries against h-gates; pure against mixed labels).
**What follows.** A cut argument for MixColumns must carry the interface type as a variable,
min over types tau of [nu(tau) + phi(tau)] (a ring Lemma B with typed near baselines; programme (A) of
compose/ring, here forced), or use all cuts at once by discharging from the charge theorem (programme (B)).
**Structural restriction that remains (already known in effect):** Corollary 17.4 makes an 87 non-block-
monotone, so it has a primal exit at some single-block cut; if its gates are window-local, Lemma II.6 puts
that exit at a triangle. The corpus shows only the {1,2,7} (mirror {1,2,3}) exit supplying a target, and the
5-window exits.
**Not established:** typed values nu(tau), phi(tau); exact chi_W; whether near >= 11 at mirror groups 1, 3, 4
is forced for some definable class.
