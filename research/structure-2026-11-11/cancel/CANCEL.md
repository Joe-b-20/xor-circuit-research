# When does cancellation-mediated sharing need extra work? (phase 8)

Main agent (Opus 5.5), 2026-11-12. Status words: **proved** = hand argument here (main agent; machine review
in `review/REVIEW.md`, not human review, not formal verification); **check** = read-only evaluation of given
circuits (recorded circuits, kste corpus lines, rotation/circuits/*.txt); scripts in this directory. No SAT, no
search, no exhaustive enumeration, no least-gate computation (by the main agent or the reviewer). Nothing here
changes 75 <= L(MixColumns) <= 88. Review fixes (section 6) are already applied in the text.

**Phase-9 update (`SUPERPOSITION.md`).** Conjecture G is REFUTED for MixColumns and for Q_m (m >= 4): a reduced,
fully live circuit (global parity, then remainders) has 66 distinct charged gates (8m + 2 for Q_m). Theorem K
and Lemma W stand. Read K as a classification of partner shapes: confinement is a support condition (not
membership in F_l, which needs ancestry); a one-chase-exit closure in MixColumns needs a non-confined or
escaping partner, not necessarily an uncharged one; the chase-exit count is per selected pair of paths from
one shared gate, not a count of distinct expenses. K gives no constraint on cost or reuse.

## 0. Setting and the fixed counted families

A *sheet system* (exact form used here): inputs in blocks of four; a set of sheets, each sheet j with an own
block (distinct sheets have distinct own blocks; other blocks may be unowned, such as a chain's free block) and
four rows that all have the same block support W_j, the *window*, containing j and at least one non-own block;
each row is E_c on the own block plus s_c on every other window block, so that the ten-gate lemma (RECORD 7, 10)
gives |F_j| >= 10 (a sheet with W_j = {j} would be a bare E-sheet, cheaper than 10; phase-9 repair). Examples:
MixColumns (W_0 = {7, 0}, W_j = {j-1, j} plus 7 for j in {1, 3, 4}), the rotation model Q_m (W_j = {j-1, j} mod
m), chains of adjacent sheets with a free first block. For a circuit C: A_j = ancestors of sheet j's rows, the
rows included; F_j = gates of A_j nonzero on block j; m(g) = number of j with g in F_j; E = sum_j (|F_j| - 10),
R = sum_g (m(g) - 1)^+, U = number of gates in no F_j. Identities (bookkeeping, not mechanisms):
|union F_j| = 10 s + E - R and G = 10 s + E - R + U (s sheets). The distinct-charge conjecture (phase 7) is
E >= R; a total bound G >= 10 s needs only E + U >= R. Kept apart throughout: G; |union F_j|; the charged union
of a pair; the pair theorems' family P(j, k); the restricted pair problem. (Check, tri3.py: after zeroing blocks
3..7, the corpus pair circuits for sheets 1, 2 have charged union 19 in 163 of 763 sampled circuits while their
restricted gate count is 20 in all of those: a pair union of 19 is not a 19-gate pair circuit.)
An *exit* is a gate whose support lacks a block present in an operand; that block is *cancelled* there and lies
in both operands with equal nonzero parts. Along a path a block disappears only at an exit.

## 1. Lemma W (window over-charge; proved)

Let rho_j keep the own block j and one actual non-own block n_j of W_j (for MixColumns and Q_m, n_j = j - 1),
zeroing all others (block 7 too for sheets 1, 3, 4 of MixColumns). Then
|F_j| - 10 >= c_j := |F_j| - #(distinct values of rho_j(F_j) that are not a unit of block j).
*Proof.* rho_j maps sheet j's rows to E_c(j) + s_c(n_j). Gates of A_j outside F_j project to vectors on block
n_j alone (free for the lemma); gates of F_j stay nonzero on block j. Keeping the first occurrence of each
distinct projected value gives a circuit for the projected rows whose gates nonzero on block j are the distinct
values of rho_j(F_j) other than block-j units; the ten-gate lemma gives at least 10 of them. QED (This is the
charge theorem with its slack kept.)

**Refuted principle W1: "every double charge collapses in a window projection, so E >= c >= R".** Check
(collapse.py; "collapsed at j" = rho_j(g) is a block-j unit or equals rho_j of an EARLIER gate of F_j): Q_3
(28 gates): c = 5 < R = 11, six double-charged gates collapse in neither projection (five under the symmetric
reading "equal to any other gate of F_j"); MixColumns: in every sampled triangle circuit two of the three double
charges collapse in neither projection (symmetric reading: 2 or 1), and circuits_3.txt line 7451 has c = 2 < R = 3
(E = 5); the reviewer finds six such circuits in its sample. The refutation c < R does not depend on the
convention: the slack of Lemma W does not by itself pay for double charges.

## 2. Theorem K (cancellation chase; proved)

Gamma = directed graph on the sheets with an edge x -> y (x != y) when x lies in W_y (the own block of x is in
the window of y); gamma = its directed girth (infinite if Gamma is acyclic). An operand a' of an exit e is
*confined with own block l* if l is in B(a') and B(a') is inside W_l (for example: a' is charged to sheet l and
has an exit-free path to a row of sheet l); it is an *escape* at e if every such l is cancelled at e (pure-block
operands are escapes; so is the operand of a gate a + a, which has value 0).
Let g be charged to two sheets j != k, and let pi_j, pi_k be paths from g to a row of sheet j and of sheet k.
The *chase exits* of pi_j are defined inductively: if k is in W_j there are none; otherwise the first exit of pi_j
(after g) cancelling block k is the first chase exit e_1; if its off-path operand a'_1 is confined with an own
block l_1 not cancelled at e_1 (choose one), the next chase exit is the first later exit of pi_j cancelling l_1,
if any; and so on. Symmetrically on pi_k with j in place of k. Call the pair (pi_j, pi_k) a *plain charged
closure* of g if at every chase exit the off-path operand is confined and not an escape.

**Theorem K.** If (pi_j, pi_k) is a plain charged closure of g with t_j and t_k chase exits, then Gamma has a
directed cycle of length at most t_j + t_k + 2. Equivalently t_j + t_k >= gamma - 2; if Gamma is acyclic, no
double-charged gate has a plain charged closure.
*Proof.* Along pi_j: if k is in W_j, the edge k -> j. Otherwise block k (present in g) is cancelled at e_1, so it
lies in the on-path operand and in a'_1, which is inside W_(l_1) for the chosen l_1: edge k -> l_1 (l_1 != k
since k is cancelled at e_1 and l_1 is not; l_1 != j since k lies in W_(l_1) but not in W_j). As l_1 is in
B(a'_1) and not cancelled, it lies in B(e_1), and e_1 is on pi_j. Either l_1 is never cancelled later, so it lies
in the row's support W_j (edge l_1 -> j, or l_1 = j), or it is cancelled at the next chase exit e_2 and the same
step gives l_1 -> l_2. The chase exits come in path order, so after at most t_j steps the chase reaches j: a
directed walk from k to j of length at most t_j + 1. Along pi_k, a walk from j to k of length at most t_k + 1.
Together a closed walk of length at most t_j + t_k + 2 in a loopless digraph, which contains a directed cycle of
at most that length. QED

What the theorem uses: block supports, two specific paths, and the windows; no values and no gate order beyond
the paths. Exits already needed for an output or another sheet, partners computed for other purposes, several
shared values using the same exit, and several patterns on the same paths are all allowed (only supports enter;
the bound is per gate and per pair of paths). It assigns no cost: it restricts the *shape* of closures whose
partners are themselves plain charged work.

**Values of gamma (proved by listing).** Q_2: 2. Q_3: 3. Q_m: m. Chains: acyclic. MixColumns: Gamma is the
8-cycle x -> x+1 plus 7 -> 1, 7 -> 3, 7 -> 4; every directed cycle passes through 7 (0 -> 1 -> ... -> 6 is a
path), giving 7,4,5,6 (length 4), 7,3,4,5,6 (5), 7,1,...,6 (7), 7,0,...,6 (8): gamma = 4. The phase-7 triangle
{1, 2, 3} is an undirected 3-cycle of window intersections (blocks 1, 2, 7), not a directed one: its block-7
edge joins two s-parts (sheets 1 and 3 both carry s_c on block 7) and neither own block lies in the other's
window.

**Corollaries (proved).** (a) If gamma >= 3, no double-charged gate has exit-free paths to both its sheets
(t_j = t_k = 0 would need a 2-cycle); this is J9's "equivalently" sentence, and it contains phase 7's
"no double service in block-monotone circuits" for J8's definition (no exits at all). With chase exits it also
covers RECORD Cor. 7.2's class (support containment, exits allowed): there k in B(g) lies in W_j, so the chase
stops at once. (b) MixColumns (gamma = 4): every plain charged closure has at least two chase exits; a double
charge whose chosen paths have at most one chase exit in total has, at that exit, an off-path operand that is not
confined with an own block or is an escape. (c) Chains: no double-charged gate has a plain charged closure; on
any two paths some chase exit has a non-confined or escaping off-path operand (the chain's free vectors, on the
unowned block, are never confined).

## 3. What the circuits show (check, partners.py, qstudy.py; confirmed by the reviewer's own code)

- Q_3 (rotation/circuits/q3_28.txt, 28 = 30 + E 9 - R 11, U = 0): four exits (g21, g25, g30, g35) carry the
  cancellations of all eleven double charges; at the needed cancellations there are 20 off-path instances:
  14 confined and non-escaping, all of them charged work of the third sheet (example: g16, charged to sheets 0
  and 1, reaches sheet 0 through g21 = g18 + g20, where g20 = [1:0011 2:1001] is charged to sheets 1 and 2, lies
  inside W_2 = {1, 2} and keeps its own block 2, which lies in W_0: walk 1 -> 2 -> 0, closed by 0 -> 1), and 6
  escapes. One chase exit per closure, as gamma = 3 permits.
- Q_2 (16 = 20 + 4 - 8): no exits; the windows coincide (a 2-cycle). Q_4, Q_8 recorded (40, 80): no double
  charges.
- MixColumns (every 25th kste circuit plus the recorded 88, 89, 97: 763 circuits; the reviewer's every 50th:
  384): double charges occur only in the triangle circuits (598 here; three gates on {1, 2} charged to sheets 1
  and 2), and at every needed cancellation the off-path operand is an uncharged gate that is not confined
  (0 escapes; 1,794 instances here, 915 in the reviewer's sample); one exit and one partner close all three.
  The partner is typically [2:s 7:s] (support {2, 7}, inside W_3 but without sheet 3's own block 3); in about a
  third of the circuits its support is {0, 2, 7}, and its block-2 part is sometimes d_0 = {0, 2} rather than an
  s. (Exits on these paths that cancel a block not being chased can have confined operands, e.g. {0, 7} gates
  charged to sheet 0 cancelling block 7 in circuits_3.txt lines 1451, 3001; they are not chase exits.)
This is consistent with corollary (b): the observed one-exit closures in MixColumns use uncharged partners,
while in Q_3 they use the third sheet's charged work. That a charged closure saves a gate is not proved.

## 4. Other principles tested

- **W2 "every exit costs a gate"**: false (Q_3: four exits, and it saves two gates).
- **W3 "each uncharged partner pays for the double charges it closes" (U >= R in triangle circuits)**: false in
  the sample: one partner closes three double charges, and (E, R, U) = (10, 3, 1) occurs (about 50 circuits in
  the reviewer's sample); compensation there comes from E.
- **W4 "compensation is pair-local"**: false in the F-form (phase 7, circuits_2.txt line 783). Observation: after
  zeroing blocks 4, 5, 6, the charged union of sheets 1, 2, 3 is at least 30 in all 763 sampled circuits
  (tri3.py; least 30, in 33 circuits): compensation inside the triangle triple in the sample, not a theorem.

## 5. Conjecture, scope, and what is missing

**Conjecture G (sheet systems as defined in section 0).** If gamma >= 4, then |union_j F_j| >= 10 s in every
circuit. Status: REFUTED in phase 9 (`SUPERPOSITION.md`): MixColumns has a circuit with 66 distinct charged
gates and Q_m (m >= 4) one with 8m + 2. The total-cost statements below remain open; they no longer follow from a
distinct-charge bound. Original text, kept for the record: Since G >= |union F_j| it would give L(MixColumns) >= 80 (published 75),
L(Q_m) >= 10 m for m >= 4 (hence = 10 m with the known upper bound; 9m - 7 is known) and M_l >= 10 l for chains
(hence = 10 l with the known construction; 9l + 2 known; M_3 is 29 or 30). Q_2 and Q_3 lie outside its
hypothesis (gamma = 2, 3; they save 4 and 2), so they do not test it; what Theorem K shows is that the girth is a
proved difference between them and MixColumns that controls one-exit charged closures. It is not proved that
the girth controls savings: gamma = 4 still permits two-exit charged closures.
**Missing argument (exactly).** A cost for the closures Theorem K leaves open: (i) closures with a chase exit
whose off-path operand is not plain charged work (uncharged, or charged only through further exits): the
MixColumns triangle; (ii) escapes, including pure-block operands; (iii) plain charged closures with at least
gamma - 2 chase exits. For (i) the cost cannot be one gate per closed double charge (W3), and an uncharged
partner counts only towards G, not towards |union F_j|; a proof of the distinct-charge form must find the
compensation in E, while a proof of G >= 80 may also use U. Which holds is open; on every sampled circuit both
hold (least |union F_j|: 81, circuits_3.txt line 7651, with E 4, R 3, U 7; the "82" of RECORD 22 was wrong).
**Scope.** Theorem K holds for every circuit of every sheet system as defined in section 0; its conclusion is
about the shape of closures, not about G or |union F_j|. Corollary (b) covers all MixColumns circuits. Section 3
is about the listed circuits only; the corpus frequencies are observations, not a normal form (the main sample
also contains a variant circuit, phase 7).
**Compared with earlier counts.** Parity (56) evaluates at one point; restriction and gate elimination (57, 64,
the phase-7 caps) use value sets of projections; the 80 count uses projections to windows and controls double
charges only in block-monotone circuits; Lemma W is that count with its slack. Theorem K adds the relation
between the windows (the graph Gamma and its girth) and where cancellations sit on paths, which none of these
uses.

## 6. Review status

`review/REVIEW.md` (machine review, own code, own sample): Theorem K CORRECT (wording fixes: hidden assumptions
of section 0, chase-exit form, acyclic case); corollaries and girths CORRECT WITH FIXES (definitions of
block-monotone and of plain charged closure); Lemma W CORRECT WITH FIXES (notation, unit wording, the W1
convention); numbers confirmed except "least |union F_j| 82" (81) and the operand counts (both operands had been
counted); overclaims on "predicts", "no extra gate" and "what distinguishes Q_3" removed above.
