# Review of repair/REPAIR.md (phase 11)

**This is a machine review** by an independent agent (Opus 5.5), 2026-11-13. It is not a human review and not
a formal verification. No search was run: no SAT, no exhaustive or finite-family check, no case enumeration,
no least-gate search, no BFS/Dijkstra over value sets. The only computations were:
- direct construction and evaluation of specified circuits;
- read-only measurement of the named corpus circuits.

Own code: `rv.py` (output `rv_out.txt`) and `rv_detail.py` (output `rv_detail_out.txt`). They share nothing
with `repair.py` except the corpus loader `clib.load`. The MixColumns matrix was re-implemented and checked
equal to `clib.ROWS`.

Every repaired circuit was built explicitly and checked to compute the map and to contain no event.
- `joint`: Lemma 1 taken literally (D placed first, then normalised).
- `seq`: Theorem P as stated. Repeatedly take the first event of the current normalised circuit, replace it in
  place, normalise again, and record the per-event overhead sigma_e.

## Verdicts

| claim | verdict |
|---|---|
| Lemma 1, normalisations, Theorem 1 | CORRECT WITH FIXES (minor: reducedness in Theorem 1; one sentence on Cor 17.4) |
| 1.2 sequential repair | CORRECT |
| Compatibility with Cor 17.4, status of 84 | CORRECT |
| Theorem 2 and its MixColumns consequences | CORRECT WITH FIXES (the "triangle at a sheet-1 output" sentence) |
| Section 3 sharpness family | CORRECT |
| Lemma Z | CORRECT |
| Theorem P | CORRECT WITH FIXES: the definition of s_e is ambiguous (one reading is false), and the proof has two gaps. With the fixed definition the bound is sharper than the note says. |
| Section 4 table | CORRECT (reproduced; one entry depends on the procedure) |
| Section 5 / 6 | CORRECT WITH FIXES (the "true saving 2" wording on Q_3) |
| Section 8 corrections | CORRECT. The counterexample is verified, and the corrections are applied. Two small leftovers remain in `copies/`. |
| Section 7 next direction | Justified in substance. As worded ("bound s_e") it cannot work; it needs a trade-off form. A precise first lemma is given below. |

## 1. Lemma 1, 1.2, and compatibility with Corollary 17.4

**Lemma 1 holds.** Every step checks out:
- A retained gate reads nodes whose values are its original operand values, so it is still not an event.
- D reads only inputs, so the new order is topological.
- Duplicate reuse redirects readers to an earlier node of equal value. Operand values do not change, so the
  result stays event-free, and the earlier node precedes all readers.
- Pruning only deletes gates.
- An event-free gate is never 0. An input-valued gate is a duplicate of that input.

`rv.py` checks the structural claim directly on every test circuit:
- the raw size is G - |E| + K;
- no retained gate is an event;
- the map is computed;
- after normalisation the circuit is still event-free.

**Fix 1.** Theorem 1 says "every MixColumns circuit", but Lemma 1 assumes C is reduced. The reason is that an
event with a = b has value 0, which no D computes. Either state Theorem 1 for reduced C, or add "(reduce first:
every lower bound may assume reduced circuits, ACCOUNT section 0)". Theorem 2 already uses reducedness.

**1.2 (sequential repair) is correct.**
- Gadgets read only nodes before e that carry their original values.
- Retained gates are unchanged.
- The count is G - |E| + sum K_e.

It is a routine extension of Lemma 1.

**Event-free implies block-monotone.** Write B(v) for the set of blocks on which v is nonzero. Always
B(a + b) is a subset of B(a) u B(b). A block in the union but missing from B(a + b) is exactly an event. So
with no events, B(a + b) = B(a) u B(b), supports grow along every edge, and every ancestor's support lies
inside every descendant's support. That is RECORD 7's definition: for an output gate o and an ancestor g,
B(g) is inside B(o).

**Corollary 17.4 needs nothing else from the repaired circuit.** Its only hypotheses are:
- the circuit computes the 32 rows as gate values;
- the circuit is block-monotone.

The note says Cor 17.4 "needs no reducedness". I did not re-audit the local proofs (17.2, 17.3, 9.1) for this
claim, and it is unnecessary. The repaired circuit can be normalised (reduced and fully live) without losing
event-freeness, so it satisfies any reducedness the local proofs might use.

**Fix 2 (wording).** Replace "That theorem needs no reducedness: its local problems allow zero and repeated
values" with: "the repaired circuit may in any case be taken reduced, since normalisation preserves
event-freeness."

**Status of 84 (stated accurately in the note).** It is proved by hand given Theorem 17.3 and the decomposition
of RECORD 9. That chain rests on:
- the hand proof of the ten-gate lemma;
- transposition Lemma 3.1 and the partition lemmas;
- Theorems 9.1, 17.2 and 17.3.

All of these have had machine review only. Theorems 1 and 2 inherit exactly that status. The 80 baseline of
the charge identity is not affected. The unrestricted 75 and the 88 are not affected.

## 2. Theorem 2 and its MixColumns consequences

**Theorem 2 is correct.**
- A chain over the w(e) inputs of val(e) joins disjoint bit supports. So two operands never have equal nonzero
  parts on a block, and the chain is event-free.
- Reuse only lowers K, so K <= sum (w - 1), which gives G >= 84 - sum (w - 2).

**Row weights.** My own matrix gives weight 5 for sheets 0, 2, 5, 6, 7 and weight 7 for sheets 1, 3, 4, for
all four rows of each sheet.

**The numerical consequences are correct:** 79, 81, 84 for weight-2 events, "G <= 78 => sum >= 6", and
"G <= 80 with one event => w >= 6".

**Fix 3.** "The triangle event of the near-88 circuits ... sits at a sheet-1 output" is true for only four of
the five lines.

| line | where the triangle event sits |
|---|---|
| 783, 7451, 7651 | output (1,1), weight 7 |
| 1451 | output (3,1), weight 7 |
| circuits_3.txt:3001 | node 100: an internal weight-5 gate on B(a) = {2,7}, B(b) = {1,2}, not an output |

Correspondingly, "the 84 - s target of phase 10 holds with s = 5" holds only for a sole triangle event that sits
at a weight-7 output. A sole internal triangle event of weight w gets only 84 - (w - 2). The note's sentence
"for every circuit whose sole event is at such an output" is accurate. The sentence about the near-88 circuits
and the phrase "the target holds" need this qualifier.

## 3. Sharpness family

**The hand proof is correct.** It can be made one line more explicit. With singleton blocks, event-free means
the two operands of every gate have disjoint supports. So the ancestor cones of the two operands are disjoint
(every cone node's support lies inside its operand's support), and a node of weight k has at least k - 1 gates
in its cone. The cone of T avoids x, and the n gates p_i contain x and are distinct, so G >= 2n - 1.

**Verified directly for n = 2, 3, 5, 8, 12:**
- the original circuit has n + 1 gates, is reduced and fully live, and has the single event T;
- the hand construction (q_2..q_n, p_1, p_i = x + q_i) has 2n - 1 gates, is event-free and computes the map;
- the joint direct, sequential direct and sequential projection repairs all give 2n - 1.

Small fix: the table says "n = 2..12", but only n = 2, 3, 5, 8, 12 were checked.

## 4. Lemma Z and Theorem P

**Lemma Z is correct.** Suppose pi_d(Pu) = pi_d(Pv) != 0. Then d is not in C, so pi_d(u) = pi_d(v) != 0, which
contradicts u + v being a non-event. The gadget's gates, including the final one, are therefore event-free.

**The definition of s_e is ambiguous, and one natural reading is false.** I measured three readings. Here
"present" means "already the value of some node".

| reading | what s_e counts | used by | status |
|---|---|---|---|
| R1 | shared ancestors, inputs included; present = value of any node | `repair.py` | valid but loose: the shared cancelled inputs and any gate with P(u) = 0 always count, although they cost nothing |
| R2 | shared gate ancestors with P(u) != 0 that are not present, where val(e) itself does not count as present | the note's prefix-family text ("p_2, ..., p_n") | valid, and tighter |
| R3 | as R2, but val(e) counts as present | | FALSE |

**Counterexample to R3 (A1).**
- Inputs x, y, z, each its own block.
- Gates g1 = x + y, g2 = g1 + z, e = g2 + x = y + z; outputs g1, g2, e.
- R3 gives s_e = 0 (P(g2) = y + z is "present" as e) and delta_e = 0, so the bound is -1. That would mean an
  event-free circuit of 2 gates.
- But there are 3 distinct non-input outputs, so every circuit needs 3 gates.

R3 also fails on the prefix family, because P(p_n) = val(T). The note's prefix computation silently uses R2,
while its code uses R1.

**Proof gap (a): reuse of later nodes.** The construction says "reuse a node whose value equals P(u), if one
exists". The gadget may read only nodes before e, because a node after e can be a descendant of e and reading
it creates a cycle. When P(u) equals the value of a later node z, the gadget must build a new gate. R1 and R2
then do not count it, and the bound survives only because z becomes a duplicate of the new gadget node and is
removed by reuse. That death is missing from the proof.
- **A2** (prefix sums g1..g4 of x, y1..y4, e = g4 + x, then d3 = e + y4 and d2 = d3 + y3, all outputs):
  - e's gadget creates 3 gates, while R2 gives s_e = 1 (bound 0);
  - the overhead is 0 only because d3 and d2 become duplicates;
  - without those deaths the count is +2.
- **A3** (blocks {x}, {y, y'}, {z}; the later node d = e + y' is not an event) shows the same with a later
  non-event node.

**Proof gap (b): why dominated ancestors die.** "No gadget node carries content on C, so none reads it" is not
enough. One also needs that every reader of a dominated C-carrier is either:
- e;
- another ancestor of e, which carries C by event-freeness of e's ancestry and is again dominated;
- or dead, which cannot happen in a fully live circuit.

So the current circuit must be normalised (reduced and fully live) before each event. Otherwise reusing a dead
node with value P(u) revives it at an uncounted cost.

**Corrected statement (proved; I checked every step).** Let:
- the current circuit be reduced and fully live;
- e be its first event;
- s_e be the number of shared gate ancestors u of e with content on C whose projection P(u) is nonzero and is
  not the value of any node other than e;
- delta_e be as in the note.

Then the projection gadget followed by normalisation has overhead sigma_e <= s_e + delta_e - 1.

*Proof.* Each C-carrying ancestor u adds at most one gate. This happens only when P(u) is not the value of a
node before e; equal projections give one gate. The final gate is added only when delta_e = 1 and val(e) was
not produced earlier. Every new gate is offset by a death, except the ones s_e counts and the final gate:
- (i) e dies;
- (ii) every dominated C-carrier dies, by (b);
- (iii) every node after e whose value equals a new gadget node's value dies as a duplicate. These nodes are
  distinct and are neither dominated nor e.

What is left is at most s_e new gates from shared ancestors, plus delta_e for the final gate, minus 1 for e.
QED

R1 also bounds the overhead. A shared gate whose projection is val(e) forces a shared cancelled input, which
pays for it.

**Measurements.** I checked sigma_e against all three readings for every event of every test circuit (`seq`
repairs). R1 and R2 are never violated. R3 is violated on the prefix family, A1, A2, A3 and A5.

**Consequence: the formula is sharper than the note says.** With R2, on 783 / 7451 / 7651 the formula alone gives
2 (G >= 82), not 5.
- The shared C-carriers of 783's event (`rv_detail_out.txt`) are:
  - inputs 18 and 26, and gate 36 (pure block 2), all with P = 0;
  - gates 54 and 64, whose projections are present;
  - gates 74 and 76, whose projections are absent.
- So s_e = 2 and delta_e = 1, and the bound is 2, which equals the measured overhead.

On Q_3 the per-event R2 bounds (2, 2, 2, 3; total 9) equal the measured sequential overheads.

**Fix 4.**
- Replace the definition of s_e by R2 (or state R1 explicitly).
- Add (a) and (b) to the proof.
- Require normalisation between events.
- Replace "On the triangle circuits the simple bound s_e + delta_e - 1 equals 5 ... adds nothing" by "with
  this definition the bound is 2 on the three triangle circuits, equal to the explicit overhead". The old
  value 5 comes from `repair.py`'s R1 count.
- The prefix sentence should read: s_T = n - 1 counts p_2..p_n under R2 (under R1 it counts p_2..p_(n-1) and
  x). The bound is then n - 2, which is exact because the 2n - 1 lower bound is proved.

**Other attacks, all found sound.**
- Several cancelled blocks: the witness has C of size 5-6.
- P(a) = 0 or P(b) = 0: A1, and the exits in 1451 and 3001.
- delta = 1 with a dominated partner: A4, overhead -1.
- Interacting sequential events: A5, with three events, one of which reads another's gadget.
- Multiple events processed in order: the overheads add, provided the circuit is normalised between events.

## 5. Table of section 4, re-measured with my own code

All circuits listed in the note were re-measured. The first three rows are the triangle circuits
(circuits_2.txt:783 and circuits_3.txt:7451, 7651).

| circuit | G | reduced, live | events | sum(w-2) | joint L1: K, raw, normalised | seq direct | seq projection | R2 bounds |
|---|---|---|---|---|---|---|---|---|
| 783 | 88 | yes | 1 | 5 | 6, 93, 92 | 92 | 90 | 2 |
| 7451 | 88 | yes | 1 | 5 | 6, 93, 92 | 92 | 90 | 2 |
| 7651 | 88 | yes | 1 | 5 | 6, 93, 92 | 92 | 90 | 2 |
| 1451 | 88 | yes | 2 | 9 | 11, 97, 96 | 96 | 93 | 2, 3 |
| 3001 | 88 | yes | 2 | 7 | 9, 95, 95 | 95 | 93 | 2, 3 |
| r88 / r89 | 88 / 89 | yes | 0 | 0 | 0 | same | same | none |
| witness (block order) | 521 | yes | 32 | 120 | 146, 635, 146 | 146 | 197 | up to 20 (never violated) |
| Q_3 q3_28 (nibble blocks; rows [j: E_c] + [j-1: s_c]) | 28 | yes | 4 | 13 | 16, 40, 39 | 39 | 37 | 2, 2, 2, 3 |

Every entry of the note's table is reproduced, with one exception. The witness projection repair gives 197
here and 199 in `repair.py`. This is procedure-dependent: I normalise between events and always take the first
event. Both repairs are valid explicit circuits, and the note's conclusion uses the direct repair (146), which
agrees.

**Fix 5.** The Q_3 row (section 4) and section 5 both say "the actual saving is 2", but the event-free minimum
for Q_3 is unknown; 30 is only a lower bound (RECORD 7: no block-monotone 30-gate circuit is known). Write
"saving at least 2 below the bound 30".

## 6. Section 8 and the phase-10 corrections

**The counterexample is verified with my own construction.** It has:
- 148 gates, reduced and fully live;
- the single event e (node 34, cancelling block 7, value x_(1,0) + x_(2,0)).

When block 7 is zeroed:
- a falls in category I (its image is x_(1,0));
- b is retained with image y + z;
- e falls in category D, as a duplicate of b.

**Applied correctly:** COPIES section 6 (restriction bullet) and the phase-11 note, RECORD 25, SUMMARY (phase
10 and 11), CHECKPOINT. The wording on C5, Corollary Z, Theorem F and Proposition R is in place.

**Remaining inconsistencies:**
1. `copies/review/REVIEW.md` still asserts (verdict table and fix 5) that an event is never removed when its
   block is zeroed. COPIES section 10 still says this fix was "applied". Add one line to COPIES section 10, and
   optionally a header note to that review, saying that fix 5 was itself wrong (phase 11).
2. COPIES section 0, last bullet ("whose use as a route to bounds has a ceiling"), and section 10 ("the ceiling
   of Proposition R") conflict with the phase-11 wording in section 8 ("not a general impossibility ceiling").
   Replace "ceiling" with "proof obligation".
3. RECORD 25 cites section 26, which does not exist yet (expected).

## 7. What is new, and the next direction

**What is new.**
- **Sequential reuse:** correct but routine.
- **Theorem P:** genuinely useful once fixed. With R2 it reproduces the measured overhead exactly on every
  tested circuit: prefix family, triangle circuits, Q_3.
- **The interpretation "only shared cancelled content costs":** correct as a statement about repair overhead,
  hence as an upper bound on saving. Precisely, the cost is the shared C-carrying gates whose nonzero clean
  projections are not already computed, plus delta, minus 1.

It is still a per-circuit statement. The note correctly says that no class bound beyond Theorem 2 follows.

**The next direction, as worded, cannot work.** Section 7 says "bound s_e by the window structure". No bound on
s_e alone can hold for a class, because wasteful circuits with the same event profile can have any number of
shared C-carriers. A class statement "sole event at a sheet-j output => G >= 84 - t_j" therefore needs a
trade-off: every counted carrier must be paid for elsewhere in the block-monotone accounting, or the circuit is
large anyway. I recommend stating the target that way.

**A precise first step (Lemma W; reviewer; proved by hand here).** Let e be the only event of a reduced circuit,
with val(e) a sheet-j row, and let u be an ancestor of e that reaches an output o' of sheet j' on a path
avoiding e. Then:
- B(u) is inside (W_j u C) n W_j';
- if u carries a cancelled block c, then c is in W_j'.

*Proof.* Supports grow along the event-free path from u to o'. They also grow along event-free ancestry up to
the operands, whose block union is W_j u C. QED

For the triangle (j = 1, C = {2}) this confines every shared carrier to:
- blocks {1,2}, serving sheet 2;
- blocks {2,7}, serving sheet 3;
- block 2 alone.

That is exactly what 783 shows. s_e then counts the {1,2}- and {2,7}-carriers in e's cone whose pure-block-1 or
pure-block-7 parts are not computed. This turns the J9 / Theorem K programme into a concrete local question
inside the sheet-2 and sheet-3 families. For example: can absent pure-1 projections of {1,2}-carriers be shown
to cost a gate in F_2 or in J_01?

**The two-event regime** is correctly identified as forced for G <= 78. The tested two-event circuits (1451 and
3001: a triangle event plus a {0,7} exit, R2 bounds 2 + 3) suggest treating the exit as a second application
of Lemma W, with C = {7}.

## Required fixes (summary)

1. Theorem 1: state it for reduced C, or add the reduction step.
2. Cor 17.4 compatibility: replace "needs no reducedness" with "the repaired circuit may be taken reduced".
3. Section 2: the triangle event is at a weight-7 output in four of the five lines. circuits_3.txt:3001 has an
   internal weight-5 triangle event. Qualify "the 84 - s target holds".
4. Theorem P:
   - define s_e as R2 (or R1 explicitly); R3 is false (A1);
   - add the duplicate deaths of later nodes (a) and the event-free-ancestry step for dominated deaths (b);
   - require normalisation between events;
   - correct "simple bound equals 5" to 2 on the triangle circuits;
   - correct the prefix-family justification.
5. Q_3: "actual saving is 2" becomes "at least 2 below the bound 30".
6. Table: "n = 2..12" becomes "n = 2, 3, 5, 8, 12". Note that the witness projection count is
   procedure-dependent (197 vs 199).
7. copies/: annotate the phase-10 review's fix 5 as wrong, and replace "ceiling" for Proposition R in
   sections 0 and 10.
