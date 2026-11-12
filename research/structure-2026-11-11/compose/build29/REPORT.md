# Constructive side of the chain of three: no 29 built; where a 29 could still come from

Delegated investigation, 2026-11-12 (phase 3), separate model instance (Opus, medium effort); saved by the
main agent from its final message. Machine work, NOT independently reviewed. No search: the scripts
evaluate hand-designed circuits (checks, not proofs).

**Review (`../../review-compose/REVIEW.md`).** The two-pair inequality is correct; alternative (a) below is
not implied (the inequality forces o2 + (b) + (c) + (d) >= 1 + dup12 + dup23, and o2 is a count, not a set
of gates). The first-contact lemma is correct only with X0 taken among the ancestors of g; its D1 ∩ D3
sentence is wrong as stated (the first contact is a duplicate in AT LEAST ONE view unless fed by an X-gate
and a b1-b2 mixer; counterexample to "both": p = x0, q = y3 + f), and "every sharing pays at least one
redundant gate seen by only one bound" over-claims (one redundant gate per first contact, not per shared
gate). Read the sections below with these corrections.

**Outcome.** No 29-gate circuit. The natural transplant of the Q_3 mechanism costs 36 (verified). An
inequality combining the two pair bounds localises where a saving would have to come from; it does not
exclude 29.

**Notation.** D_k = ancestors of a sheet-k target (targets included) nonzero on b_k.
G = 30 + over + unch - excess, over = o1 + o2 + o3 (o_k = |D_k| - 10), unch = gates in no D_k,
excess = e12 + e23 + e13 - e123 (e_ij = |D_i ∩ D_j|, e123 = |D_1 ∩ D_2 ∩ D_3|). pr_k = projection to sheet
k's local problem (sheet 1: kill b2, b3, b0 free; sheet 2: kill b0, b3, b1 free; sheet 3: kill b0, b1, b2
free). dup_k = gates of D_k whose pr_k value repeats an earlier one; |D_k| >= 10 + dup_k.

## Attempt 1: the Q_3 mechanism with b_0 in place of the wrap-around (verified: 36)

Ring blocks (rho, rho+1, rho+2) -> (b1, b2, *); * must be b3 where sheet 3 uses it as own block and the
free b0 where sheet 1 uses it as previous block.
- Relabelling only (28 gates, `lift_q3.py`): the linear system is inconsistent for all three rho (e.g. ring
  gate g20, *-part u0 + u3, is used as s_3 on the previous block by ring sheet 0 and inside E_2 on its own
  block by ring sheet 2).
- Two-version lift (`twover.py`): each gate with nonzero *-part gets a b3 copy and a b0 copy; the few gates
  cancelling the *-part are computed in one chosen version, all 2 or 4 combinations for this one circuit
  listed. Best 36 (rho = 0 or 2), verified by `vchain.py`: |D_k| = 12, 13, 14, 36 = 30 + 9 + 2 - 5.
- Account: Q_3 is 28 = 30 + 9 - 11, its 11 double charges split 2 + 3 + 6 over the windows {0,1}, {1,2}
  and the wrap window {2,0}. In the chain the wrap window does not exist; its six double-charged gates
  (serving sheet 0 in the previous-block role and sheet 2 in the own-block role) become eight duplicated
  gates, two of them uncharged b0 copies, while the over-charge 9 that paid for all eleven stays.
- The chain's only triangle-like shape: a sheet-2 gate u (on b1, b2) plus v = (b2 vector) + (free) gives a
  sheet-1 target; v is the b0 copy of a ring gate that served sheet 3 and cannot serve sheet 3 here.

## Proved by the investigator (short derivations, not reviewed)

**Two-pair inequality.** W12 = ancestors of a sheet-1 or sheet-2 target nonzero on b1 or b2; W23 likewise
for sheets 2, 3 and blocks b2, b3. Restriction gives pair circuits (kill b3 for (1,2), kill b0 for (2,3)),
so |W12| - dup12 >= 20 and |W23| - dup23 >= 20; hence e12 <= o1 + o2 + w12' - dup12 and
e23 <= o2 + o3 + w23' - dup23 with w12' = W12 \ (D1 ∪ D2), w23' = W23 \ (D2 ∪ D3). Substituting:

    G >= 30 - o2 + dup12 + dup23 - |U ∩ w12' ∩ w23'| - |w12' ∩ D3| - |w23' ∩ D1| - (e13 - e123),

U the uncharged gates. (`vchain.py` asserts the bound is <= G on every circuit it evaluates: 30 for the
standard circuit, 27 for the lift.) So a 29 needs at least one of: (a) an over-charge on sheet 2 seen as a
new gate by both pair views; (b) an uncharged gate in both pair sets (in practice a pure b2 gate used by
sheets 1 and 3 but not 2); (c) a sheet-3 gate in w12' or a sheet-1 gate in w23'; (d) gates in D1 ∩ D3
outside D2 (still limited by RECORD 11).

**First-contact lemma.** If some ancestor of a sheet-1 target is nonzero on b1 and on b2 or b3, take the
earliest such gate g = a + b, b zero on b1. Either b has no b0 part, then pr_1(g) = pr_1(a) with a in D1
(dup1 >= 1); or b is an X-gate (zero on b1, nonzero on b0 and on b2 or b3). The earliest X-gate is
X0 = W + f, f free, W zero on b0 and b1; X0 is a duplicate in pr_2 and pr_3, and in the pair view (2,3)
equals W or a unit, so it raises dup23 whenever it lies in W23. The same for sheet 2's ancestors
receiving b3 material (the earliest mixed gate is a pr_2-duplicate, or uses Y = q + r, nonzero on b1 and
b3, zero on b2, a duplicate in pr_1 and in the pair view (1,2)). For D1 ∩ D3 the first gate nonzero on
b1 and b3 is a duplicate in pr_1 and pr_3 unless its operands are an X-gate and a b1-b2 mixer. So every
sharing across a cut pays at least one redundant gate, and the cheapest forms of that redundancy are seen
as compensation by only one of the two pair bounds.

## Why the natural versions of (a)-(d) fail (argued by hand; only Attempt 1 is a verified circuit)

- Sheet 1 borrows through X = W + f (the free-end triangle): X pays in pair (1,2) but is a duplicate in
  pair (2,3); net 0, as the pair theorem says.
- (a) with X as the sheet-2 over-charge: o2 = 1 and dup23 = 1 cancel.
- (a) with a b3-entry over-charge g = a + B, B = Z(b3) + f(b0): g is new in both views and brings b3 into
  sheet 2's ancestors, but B is a duplicate in view (2,3) and outside W12: cost 2 for compensation 2.
- (b) a pure b2 gate Z used by sheets 1 and 3: using it in sheet 1 needs a first-contact redundancy.
- (d): the first contact is a duplicate for both sheets unless fed by an X-gate and a b1-b2 mixer.
- Exits across cut 1 (mirror): with three even labels K >= 30 - S, S the gates an exit saves over
  recomputing its value from labels; S >= 1 needs a fibre path of three stacked entries. With four basis
  labels, at least three odd, Lemma B charges the near side at least 1, so S >= 2 is needed. In the rigid
  case (T* = 8) the exits are delta + {0, L1, L2, L1 + L2}; with odd labels these have zero c-part and
  cannot be the B_i; using them as E's saves 1 against a cost of 2 (worked by hand, not run: three exits
  giving E_0, E_1, E_2 lead to 31).

## What could still produce a 29

Only a configuration tight everywhere. The one consistent tally found is a "hub": e12 = e23 = 2 paid by
three redundant gates (a sheet-1 first contact, a sheet-2 first contact with b3, and an over-charge on
sheet 2 seen as new by both pair views, i.e. an extra entry g = a + q with q a b1 vector): 30 + 3 - 4 = 29.
It needs one redundant gate to pay for two double charges inside a pair that still totals 20; the pair
theorem allows that, no example is known, and every natural route needs a helper that is a duplicate in
one of the views. In mirror terms this is (Y') or (Z') at the closed end together with an exit across
cut 1. A proof that such a gate can never be seen by both views would give M_3 = 30.

## Files (compose/build29/)

vchain.py (checker: charge account, pair-set counts, two-pair bound, mirror counts at both cuts),
lift_q3.py, twover.py, lift_best.txt (the verified 36), dump_chain.py, std30.txt (the standard 30).
