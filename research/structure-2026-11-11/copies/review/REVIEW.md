# Review of copies/COPIES.md (phase 10)

**This is a machine review** by a separate model instance. It is not a human review and not formal
verification. **No search was run:** no SAT, no exhaustive or finite-family checks, no case enumeration, no
least-gate or BFS/Dijkstra computation, no subset minimisation, no corpus or transpose campaigns. What was run is
direct evaluation of specified circuits, ordinary linear algebra on them, and read-only measurements of the named
corpus lines. All of it is my own code, with my own MixColumns matrix and parsers:
- `rv_measure.py` (output `rv_measure_out.txt`): the table, the extra baselines, the zero-block test, Theorem F,
  and the block-monotone example;
- `rv_events.py` (output `rv_events_out.txt`): the events of the five corpus lines;
- `rv_cone.py` (output `rv_cone_out.txt`): the cone check of section 3.

The author's scripts were not rerun.

## 1. Verdicts

| claim | verdict | what is wrong or missing |
|---|---|---|
| C1 | CORRECT WITH FIXES | The mathematics is right, and trivial: every copy lies in V = span X. It is an overclaim that "the only linear reading of 'needed for other outputs' gives zero". A per-recipient linear baseline gives nonzero values (fix 1). |
| C2 | CORRECT WITH FIXES | "One copy per event gate" holds only for the per-event form. The (event, block) variant of section 2 is bounded by min(n, sum of \|C(e)\|), which is at most 8 x #events (witness: sum 180, rank 32). The conclusion is unchanged. |
| C3 | CORRECT WITH FIXES | Needs n >= 3: for n = 2, S + x_1 = x_2 is an input, so the circuit is not reduced. The refuted shape is only "copies cost extra gates", G >= \|Y\| + c Q0 (see section 3). |
| C4 | CORRECT WITH FIXES | The inequality and its sharpness are correct: equality for k = 5, 6, 8 with n = k(k-1)/2. The rank bound does not even need reducedness, since a copy depends only on the operand values. **Wrong:** "Q2 = 0 in every block-monotone circuit". See fix 2. |
| C5 | CORRECT | It is an observation, not an impossibility theorem. It shows that the four listed exemptions need the circuit, not that every conceivable exemption does. |
| Theorem F | CORRECT | Ancestor-closure is not needed. Output nodes with readers are handled correctly: a path ending at o is distinct from a path through o. Inputs that are outputs are handled by the trivial path. Checked on general, non-closed A. J6 is exactly the case A = pure-b signals, K = block b, where omega' = val_A and the output sum is empty because no row is pure. J7 is a corollary of J6, not an instance (section 6 wording). |
| Corollary Z | CORRECT WITH FIXES | Each sentence is true, but only for bounds that are functions of the cut-term sums at one cut. "Rank M = 32" should read "rank M_K: 32 for all columns, 4 for one block". "Matrix form of Lemma S1" is an analogy, not a derivation. The extrapolation in sections 0 and 8 is wrong (fix 3). |
| Table, section 5 | CORRECT | Every entry reproduced (section 2). One text error is in the list below the table (fix 4). |
| Section 6, J1-J5 bullet | WRONG | Convention clash. ACCOUNT's D_c zeroes block c, and an event gate is never removed there (fix 5). |
| Proposition R | CORRECT | It needs the conventions that outputs lying in S cost nothing and that H consists of nonzero values. Distinctness is not needed. It is weaker than the trivial G(C) >= L(Y u H), of which it is a lower bound. See section 4 for its limits. |
| Verdict (sections 0, 7) | CORRECT WITH FIXES | "Under every precise version examined" is literally true for the rank-of-copies measures. Not examined: the per-recipient baselines (fix 1) and the savings shape (section 3). |

## 2. Measurements (own code; all agree with the note)

| circuit | G | \|Y\| | non-out | events (at outputs) | Q0 | QX / QY | Q2 | partner cap | recipient (one node) |
|---|---|---|---|---|---|---|---|---|---|
| sanity | 5 | 2 | 3 | 2 (2) | 2 | 0 / 2 | 2 | 2 | - |
| chain n = 8 | 14 | 14 | 0 | 7 (7) | 7 | 0 / 0 | 0 | 7 | - |
| pairs k = 5, 6, 8 | 25, 39, 76 | 20, 33, 68 | 5, 6, 8 | 10, 15, 28 (all) | 10, 15, 28 | 0 / 1 | 10, 15, 28 | 4, 5, 7 | - |
| Q_3 (q3_28) | 28 | 12 | 16 | 4 (3) | 4 | 0 / 0 | 4 | 1 | 8 (2) |
| r88, r89 | 88, 89 | 32 | 56, 57 | 0 | 0 | 0 / 0 | 0 | 0 | 0 |
| 5 corpus lines | 88 | 32 | 56 | 1-2 (0-1) | 1-2 | 0 / 0 | 1 | 1 | 2 (1) |
| witness (block, wire) | 521, 616 | 32 | 489, 584 | 32 (32) | 32 | 0 / 0 | 32 | 8 | 32 (8) |

Further checks.
- **Charges.** Q_3: E 9, R 11, U 0. Witness: E 140, R 154, U 455 / 550, 66 charged gates. The identity
  G = 10m + E - R + U is asserted in the code and holds.
- **Witness events.** Every event is an output gate y = H_c + r. H_c is node 62 + c, so node 65 = H_3. Each
  H_c has eight outside-window parts of rank 8, each occupying 5 or 6 blocks, and every full remainder occupies
  7 blocks.
- **Corpus lines.**
  - Lines 1451 and 3001 each have two events. One cancels block 2. The other cancels block 7 between a {0,7}
    signal and a {0,1,7} signal, so "a {0,7} exit" is accurate.
  - In lines 7451, 7651 and 783 the only event is the sheet-1 output gate {1,2} + {0,2,7}.
- **Theorem F.** No failures on:
  - r88: 8 pure-block (J6) sets and 300 random non-ancestor-closed sets;
  - the witness: 8 + 60 sets;
  - two triangle lines: 8 + 150 sets each;
  - Q_3: 3 + 300 sets;
  - a chain whose outputs have readers and whose outputs include an input.

## 3. Adversarial findings

**(a) A per-recipient linear baseline is not zero (against C1's "only linear reading").**
- Definition: for each sheet j, take the copies of the events that are ancestors-or-self of sheet-j rows, and
  reduce them modulo the span of the other sheets' rows.
- Sum of the ranks over j: Q_3 6, triangle lines 1, witness 22, r88 and r89 0.
- So that linear reading does not vanish. It is still at most the sum over events e of #sheets(e), so the
  C2/C3 logic disposes of it: no rescue.

**(b) A block-monotone circuit with Q2 > 0 (against C4's last sentence).**
- Construction: take r88 and rebuild one sheet-2 output o = p + q (window {1,2}) as
  d = ((p + x01) + x11) + q, e = (x02 + x01) + (x02 + x11), o = d + e.
- The result is reduced, computes MixColumns, has 94 gates, and is block-monotone in RECORD 7's ancestor sense,
  the class of Theorem 9.2 and Corollary 17.4.
- It has Q2 = 2: gate e cancels block 2 between two non-output gates.
- The claim holds only for J8's definition (B(a + b) = B(a) u B(b)), where it is trivial because then there is
  no event at all.

**(c) The note examines only one shape of inequality.** C1-C5 test "copies cost gates":
G >= |Y \ X| + f(Q). They do not test the savings shape G >= B_0 - f(cancellations), and that shape has a
**sound, nontrivial base case** already in the record. In copy language:

> **Proposition V (proved from RECORD 9 and 17).** If a MixColumns circuit has no event (Q0 = 0), then
> G >= 83 (Theorem 9.2), and G >= 84 by Corollary 17.4. Equivalently, every circuit with at most 83 gates
> contains a whole-block cancellation.
> *Proof.* Always B(a + b) is contained in B(a) u B(b). If some block c of B(a) u B(b) is missing from
> B(a + b), then pi_c(a) = pi_c(b) is nonzero, so a + b is an event. With no event, supports therefore grow
> along every edge. Every ancestor's support then lies inside each descendant's support, so the circuit is
> block-monotone in RECORD 7's sense. QED

> **Localisation (proved from J9 and Corollary 7.2; checked on 8 circuits, `rv_cone_out.txt`).**
> - Every gate with mu(g) >= 2 is a proper ancestor of an event gate. Proof: g has sheets j != j', and by the
>   window inspection one own block, say j', lies outside the other sheet's window W_j. By J9 every path from g
>   to a sheet-j row contains a gate cancelling block j', and that gate cannot be g, because g is nonzero on j'.
> - Hence the deficit R = sum over g of (mu(g) - 1)^+ is supported on the ancestor cone of the events.
> - So G >= 80 - sum over g in Anc(events) of (mu(g) - 1)^+.

Both statements are sound, and both connect cancellation to gate count without an oracle. Neither is new
content; they are the record's block-monotone theorems and J9, restated. What is open, and not covered by C1-C5,
is whether there is a quantitative form, G >= 84 - c x (#events) for some constant c. Note:
- The cone in (c) can be large: 15-16 gates in the triangle 88s, 489 in the witness.
- The phase-8 refutations ("every cancellation costs a gate") do not refute this shape.
- The examined MixColumns circuits all have at least 88 gates, so they are consistent with every c >= 0 and say
  nothing about c.

I did not find a proof of any quantitative form, and no search was run to test one. **So the verdict stands for
rank-of-copies measures, but sections 0 and 8 overclaim.** "Per-object currencies (charges, copies,
transposes) ... are provably blind to removal" is false for charges, which detect the absence of removal
(Proposition V) and localise R to the event cones.

**(d) "Removal is invisible to rank" is justified only for one cut.** Corollary Z concerns one factorisation
M_K = sum of the cut terms. It says nothing about families of nested cuts or about ancestry-based arguments, which
see removal (Proposition V). The section 4 title and section 8 should say "invisible to bounds that depend only
on the terms' sum at one cut".

## 4. Proposition R and the proposed next direction

Proposition R is correct, but as a route to lower bounds it has a structural ceiling that the note does not
state. Free values never hurt, so L(Y | X u H) <= L(Y). Therefore:
- Proposition R gives at most |H \ X| + L(Y). In the superposition branch of the proposed dichotomy, a bound
  of T on circuits containing H needs L(Y | X u H) >= T - |H \ X|. This already implies the unconditional
  bound L(MixColumns) >= T - |H \ X|.
- For H = the four H_c (|H \ X| = 4), showing that such circuits need 80 would need L(MC) >= 76, and 88 would
  need 84. **The "first case" is therefore not easier than the main problem**; it contains an improvement of
  75.
- The relative charge tool is vacuous for this H (checked). For every row (c, j), row + H_c restricted to
  blocks {j - 1, j} is supported on block j - 1 alone. In the local-lemma model each row is then one gate from
  free values, so charges give 4 per sheet, which is |Y| = 32 in total.
- Proposition R credits only |H| gates, not the cost of computing H. The natural object is L(Y u H). Any
  useful version must credit H's ancestry without fixing it, and that is the oracle problem again.

Assessment: a direction with a proved base case is better justified. That is the savings shape of section 3(c):
extend Proposition V from "no event" to "few events of the observed types". The observed types are the
triangle's single block-2 cancellation at a sheet-1 output, plus the {0,7} exit of lines 1451 and 3001. Every
examined near-88 circuit has 0-2 events. The statement is local, oracle-free and precise now. Its weakness is
the many-event regime, which needs another argument; the Proposition R branch has the same gap, and no base case.
If Proposition R is kept, choose H with |H \ X| large, or work with L(Y u H) directly. Define the superposition
class first, as the note says.

## 5. Scope corrections of section 9 (read-only)

Applied accurately:
- (1) one fixed convention: SUPERPOSITION 3 and 4, RECORD 24, SUMMARY, CHECKPOINT;
- (2) "sufficient, converse not established": SUPERPOSITION, RECORD 24, CHECKPOINT; SUMMARY makes no claim;
- (3) "5 or 6 blocks, remainder 7": SUPERPOSITION table and RECORD 24; numerically confirmed;
- (5) the Q_3 marginal-cost wording: SUPERPOSITION, RECORD 24, SUMMARY;
- (6) confinement (SUMMARY:222, CHECKPOINT:62) and "exactly 10" (RECORD:1139, SUMMARY:301, FINITE_AUDIT 4(a)).

Item (4) was applied in SUPERPOSITION, and its caution is justified. With reuse, a chain can jump to an
existing node and leave an earlier chain gate dead, so liveness can fail for other orders; reducedness holds by
construction. **Remaining inconsistencies:**
- RECORD 24 still opens with "Under hypothesis H ... the circuit is reduced, fully live". This contradicts the
  correction appended at the end of the same section. Replace it with "under H the charge count is 66;
  reducedness and full liveness are verified for the two fixed orders".
- RECORD 24 cites "section 25", which does not exist yet.
- CHECKPOINT "Next steps" item 1 still recommends copy-rank.
- SUMMARY has no phase-10 entry.

## 6. Required fixes

1. **C1:** replace "the only linear reading ... gives zero" with "the global linear baselines (span X, span Y,
   staged) give zero". Add that per-recipient baselines are nonzero (Q_3 6, witness 22) but bounded by the event
   count, so C2/C3 apply.
2. **C4:** "Q2 = 0 in r88, r89 and every circuit with no whole-block cancellation (J8 sense)". Under RECORD 7's
   definition this is false (94-gate example, section 3(b)).
3. **Sections 0 and 8:** restrict "provably blind to removal" to rank-of-copies measures and single-cut rank
   bounds. State Proposition V and the cone localisation as the sound cancellation-to-cost statements that do
   exist, and the savings shape as unexamined.
4. **Section 5:** "the triangle has 1": two of the five lines (1451, 3001) have Q0 = 2.
5. **Section 6, J1-J5 bullet:** an event with cancelled block c is never removed when block c is zeroed (D_c):
   0 of 180 pairs in the witness, 0 of 7 in the corpus lines, 0 of 4 in Q_3. It is always lost, in category Z,
   when only block c is kept (D_B with B the other seven blocks), where every gate that is zero on c is lost.
   Copies are a sub-count of that large count, and the J4 average is irrelevant. Rewrite accordingly.
6. **C2:** add the (event, block) bound min(n, sum of |C(e)|). **C3:** n >= 3. **Corollary Z:** "rank M_K",
   and scope it to one cut. **Section 6:** "J7 is a corollary of J6".
7. **Section 8:** add L(Y | X u H) <= L(Y) and the resulting ceiling (section 4). Do not present the H_c case as
   easier than the main problem.
8. **Record files:** fix RECORD 24's opening "reduced, fully live" sentence and the dangling "section 25". Update
   CHECKPOINT's next steps and add a phase-10 SUMMARY entry when phase 10 is recorded.
