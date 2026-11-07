# Depth-4 lower bound for one AES MixColumns column: model, proved structure, scoped exact facts

Folder `~/xs-campaigns/2026-11-07-sprint/d4bound/` (scripts `d1_facts.py`, `d2_scoped.py`, `d3_subset.py`,
`d4_post.py`, `d5_write_report.py`; outputs `*.out`, `*.json`). 2026-11-07, about 2.5 hours, one process at a
time under `nice -n 8` on a machine at load 20-27; repository read-only.

Labels. **[proved]** = argument written here (or a named package lemma whose proof I checked applies);
**[finite-checked]** = exact computation by a named script in this folder; **[SAT-scoped]** = exact CP-SAT
optimum over a finite model whose coverage of the stated scope is proved here; **[archive]** = the owner's
unverified notes under `import/zip`, hints only; **[conjecture]** / **[guess]** as marked.

---------------------------------------------------------------------------------------------------------

## 0. Verdict

* Best bound on the gate count of depth <= 4 circuits that I can justify: **75** [proved: the unrestricted
  bound of `lower-bound-proofs/mixcolumns-lb75`, replayed clean by the lb76 agent today]. **Nothing above 75
  is proved here for depth 4 in general**; section 8 says precisely why the depth-4 structure alone does not
  reach 76, and section 9 what would.
* New proved structure (sections 2-3), valid for every depth-4 circuit: the exact layer grammar;
  `G = 32 + p + h2 + h3`; the pair / late-birth trade-off `p + b >= 24`; the complete list of the only way a
  level-4 output can avoid a level-3 helper (20 output pairs, all weight 5, same bit position, cyclically
  adjacent bytes, with a quartet co-parent).
* New scoped exact facts (section 5) [SAT-scoped]: over the recorded 89's first two layers, and over its first
  layer with the level-2 layer free inside the 81-state family's 30-value pool, **89 is optimal** (minimum
  `h2 + h3 = 31`, attained only with `h2 = 22, h3 = 9`, 20 outputs at level 3). With the pairs themselves droppable (any subset of the 26, level-2 from the family pool) the minimum of `|L1| + |L2| + |H3|` is **57**, i.e. `G >= 89`: dropping pairs never pays inside the family's shallow vocabulary. Over the first layer
  alone with the level-2 layer completely free, the exact question is **open**: the 1.9 x 10^5-mask model is too large for one CP-SAT worker or one HiGHS LP solve in 11-15 minutes (no bound proved).
* Route C (transfer of the depth-3 recipe proof) is quantified as intractable in its unconditioned form: the
  last-gate recipe space of one output is 285 (weight 5) / 35 (weight 7) at depth 3 and **1,123,414 / 592,114**
  at depth 4 [finite-checked]. The tractable form is the first-layer-conditioned model of section 5.

---------------------------------------------------------------------------------------------------------

## 1. Model and scope (exact)

**Map.** `M` is the 32 x 32 matrix over GF(2) of one forward MixColumns column
(`circuits/aes-mixcolumns/aes-mixcolumns.mat.txt`); row `i` is the mask of output `y_i` over inputs
`x_0..x_31` (`x_(8b+r)` = bit `r` of byte `b`). Twenty rows have weight 5 (bit positions 0, 2, 5, 6, 7 of each
byte) and twelve have weight 7 (bit positions 1, 3, 4) [finite-checked, `d1_facts.py` F1]. The rows are
linearly independent.

**Circuit.** A straight-line program over `x_0..x_31`; each gate is the XOR of two earlier signals; a signal is
identified with its mask in GF(2)^32. Level: inputs 0, a gate 1 + max of its operands' levels. The circuit
computes `M` if every row of `M` is the mask of some signal (an *output*); outputs may be any gate and may feed
later gates. `G` = number of gates. Fan-out, cancellation, intermediate masks, output order are free. **Scope of
every statement: output depth <= 4** (every output at level <= 4) and nothing else. `D4` = min `G` over such
circuits; known `75 <= D4 <= 89`.

Notation: `p` = number of weight-2 gates (pairs); `h2` = number of level-2 gates; `h3` = number of level-3
gates that are not outputs; `Y3`, `Y4` = outputs at level 3, 4; `k = |Y4|`; `b` = number of level-3 helpers born
from two odd operands.

---------------------------------------------------------------------------------------------------------

## 2. Normal form and layer grammar [proved]

**Lemma 1 (normal form, lossless).** Every depth-4 circuit with `G` gates can be transformed into a depth-4
circuit with at most `G` gates in which (i) all masks are distinct and nonzero, (ii) every gate is an ancestor
of an output, (iii) every weight-2 mask is a level-1 gate on two raw inputs.
*Proof.* Delete gates that are not ancestors of outputs. For duplicated masks keep a copy of minimum level and
redirect every use to it: a redirected gate's new operands have level no larger than the old ones, so by
induction on level no level increases and no cycle arises. After that, a zero mask would need equal operands,
impossible. For a gate whose mask has weight 2, replace its two operand wires by the two raw inputs of its
mask: value unchanged, level becomes 1, nothing downstream changes. Each step keeps the outputs, never
increases `G` or any level, and strictly decreases `G` or the sum of levels, so the process terminates. QED.
(Same argument as `mixcolumns-lb93-depth3/PROOF.md` Lemma 1 and the archive's `PAIR_COMPONENT_THEOREM.txt` 1.)

**Lemma 2 (layer grammar).** In a normal-form depth-4 circuit:
* level 1 = exactly the pairs `x_i + x_j`;
* level 2 = triples `x + P` (`x` not in the pair `P`) and quartets `P + P'` (disjoint pairs), nothing else;
* level 3 = masks of weight 3..8, each the XOR of a level-2 gate and a signal of level <= 2;
* every level-4 gate is an output; no output is at level <= 2; so every output is at level 3 or 4.
*Proof.* A level-2 gate has operands among inputs and pairs, at least one pair: input + pair is a triple or a
weight-1 duplicate; pair + pair is a quartet, a weight-2 mask (then level 1 by (iii)) or zero. A level-`L`
signal has weight <= `2^L`, so level-3 masks have weight <= 8, and weights 0, 1, 2 are excluded by (i), (iii);
outputs (weight 5, 7 > 4) are at level >= 3. A non-output gate at level 4 has all descendants at level >= 5,
so it is no ancestor of an output, contradicting (ii). QED.

**Lemma 3 (accounting).** `G = 32 + p + h2 + h3` (the gates are the pairs, the level-2 gates -- none an output
--, the level-3 non-outputs and the 32 output gates). In the parity bookkeeping of the 75 proof (`x` = gates
with two odd operands, `y` = two even operands, `h` = odd non-outputs, `G = 32 + x + y + h`) Lemma 2 gives
[proved, by the same case analysis] `x = p + b` with `b` = level-3 helpers born odd + odd (input + triple of
weight 4, triple + triple of weight 4 or 6); `y` = quartets + level-3 helpers born even + even (pair + quartet,
quartet + quartet; weights 4, 6, 8); `h` = triples + level-3 odd helpers (weights 3, 5, 7). Level 2 has no
odd + odd gate, and a level-4 gate is an odd output, hence odd + even.

---------------------------------------------------------------------------------------------------------

## 3. Unconditional inequalities at depth 4

**Lemma 4 (pairs trade against late births).** Every normal-form depth-4 circuit has `p + b >= 24`; hence
`p + h3 >= 24` and `G >= 56 + h2 + (h3 - b)`.
*Proof.* `mixcolumns-lb75/PROOF.md` Lemma 2.1 (partition lemma), Lemma 2.2 and finite fact F1 prove for **any**
circuit computing `M` -- the induction over gates and the graph-code word enumeration use no minimality and
no depth assumption -- that the number `x` of odd + odd gates is at least `32 - c >= 24`, `c <= 8` being the
number of blocks of the even-span partition. At depth 4, `x = p + b` (Lemma 3). QED. [proved, citing the
package; `lb76/REPORT.md` item 1: `ALL CHECKS PASSED`, 137.5 s, today.]

Remarks. (a) The archive's depth-4 pair bound `p >= 12` [archive, `PAIR_COUNT_12_PROOF.txt`] is weaker than
Lemma 4 whenever `b <= 12`; the recorded 89 has `b = 0, p = 26` [finite-checked, F2]. (b) Lemma 4 says that a
depth-4 circuit with few pairs must buy them back with level-3 even helpers born from two odd signals, each
usable only by level-4 outputs (Lemma 2).

**Lemma 5 (level-4 outputs without a level-3 helper).** Let `o` be an output at level 4 none of whose two
operands is a level-3 helper. Then `o` has weight 5 and `o = y + q` with `y` an output at level 3, `|o + y| = 4`,
and `q = o + y` a quartet of the circuit (a level-2 gate). Exactly 20 unordered output pairs `{o, y}` qualify:
for each of the five weight-5 bit positions, the four pairs of cyclically adjacent bytes; no output pair has
`|o + y| < 4` and the pairwise-sum weights are 4 (20 pairs), 6 (54), 8 (96), 10 (198), 12 (120), 14 (8)
[finite-checked, F1; `d4_post.py` (d)].
*Proof.* `o = s + t` with `s` at level 3; by assumption `s` is an output `y`. `t` has level <= 3 and is not a
level-3 helper, so it is an input, pair, triple or quartet (weight <= 4) or a level-3 output `y'`; the latter
gives `o + y + y' = 0`, against independence of the rows. So `|o + y| = |t| <= 4`; the finite list has `|o + y| = 4`
for all 20 pairs, so `t` is a weight-4 level-<= 2 signal, a quartet. QED.
*Corollary 5.1.* Every weight-7 output at level 4 has a level-3 helper operand; a weight-5 output at level 4
either has one or is "adjacent same-bit level-3 output + quartet".

**Lemma 6 (what level-3 outputs need).** A level-3 output is `a + b` with `|a|, |b| <= 4`, at least one of
`a, b` a level-2 gate; the possible `(a, b)` are the 285 (weight 5) / 35 (weight 7) final-parent decompositions
of the depth-3 proof [finite-checked, F3, regenerated here with the same counts]. One weight-3 or weight-4 mask
is a possible final parent of at most 6 outputs (weight-3 masks: 1..6; weight-4 masks: 1..4) and of at most 2
weight-7 outputs [finite-checked, F3]. Hence `h2 >= |Y3 ∩ weight-7|` [proved from the finite facts: each such
output needs two level-2 parents, each parent serves at most two of them]. The exact pair-free "parent cover"
minima are [finite-checked, `d4_post.py` (c), CP-SAT]:

| level-3 output set `Y3` | minimum number of level-2 masks that can serve as their last-gate parents (pairs free) |
|---|---|
| all 32 outputs at level 3 | **25** (proved minimum) |
| the 20 weight-5 outputs at level 3 | **10** (proved minimum) |
| the 12 weight-7 outputs at level 3 | **15** (proved minimum) |
 For the 89's choice `Y3` = the 20 weight-5 outputs the pure parent cover needs 10 level-2 masks (the 89 uses 22: its extra level-2 gates feed level-3 helpers); for all 32 it needs 25 (the depth-3 proof's `T + Q >= 34` is stronger because it couples parents to pairs); for the 12 weight-7 outputs alone it needs 15, so **any depth-4 circuit with all weight-7 outputs at level 3 has `h2 >= 15`** [finite-checked].

**What these give unconditionally.** `G >= 56 + h2 + (h3 - b)`, `h2 >= |Y3 ∩ weight-7|`, and `h3 >= 1` once a
weight-7 output is at level 4 (Corollary 5.1). The adversary's best case for these inequalities puts all 12
weight-7 outputs at level 4 and shares level-3 helpers; nothing bounds helper fan-out (a helper `s` serves `o`
and `o'` whenever `o + o' = t + t'` for available `t, t'`, which may themselves be level-3 signals). The
unconditional yield is `G >= 57` [proved], far below 75. I record this to make explicit that **the depth-4 layer
grammar by itself prices neither the level-2 bank nor the level-3 helpers**.

---------------------------------------------------------------------------------------------------------

## 4. The recorded 89@4 in these terms [finite-checked, `d1_facts.py` F2]

| quantity | value |
|---|---|
| gates by level | 26 / 22 / 29 / 12 |
| `p` | 26 (= all odd + odd gates: `x = 26`, so `b = 0`) |
| `h2` | 22 = 13 triples (odd) + 9 quartets (even) |
| `h3` | 9 = 6 odd helpers of weight 5 + 3 even helpers of weight 6, all even + even or odd + even born |
| outputs | all 20 weight-5 at level 3; all 12 weight-7 at level 4 |
| level-4 operands | 6 outputs have two level-3 helper operands, 6 have one helper + one level-<= 2 operand; no output reuse |
| level-3 helper fan-out | each of the 9 helpers feeds exactly 2 level-4 outputs |
| 75-proof bookkeeping | `x = 26, y = 12, h = 19` |

The circuit sits exactly on Lemmas 2-5: it never uses the helper-free option of Lemma 5, and realises
`p + b = 26 >= 24` with no late births.

---------------------------------------------------------------------------------------------------------

## 5. Scoped exact theorems [SAT-scoped]

### 5.1 The conditioned model and its completeness [proved]

Fix a pair set `P`. For a normal-form depth-4 circuit whose set of weight-2 masks is **exactly** `P`:
* its level-2 gates lie in `U2(P)` = triples `x + P_i`, quartets `P_i + P_j` over `P` (Lemma 2);
* every level-3 mask lies in `S(P) = (U2 + V2) \ (V2 ∪ {0})`, `V2 = inputs ∪ P ∪ U2` (Lemma 2: one operand is a
  level-2 gate, the other has level <= 2); a level-3 gate carrying a mask of `U2` can be rebuilt at level 2 from
  `P` at the same cost, so excluding `V2` is lossless;
* an output is at level 3 iff it is `u + v`, `u` a present level-2 gate, `v` a present level-<= 2 signal;
* an output at level 4 is `s + t`, `s ∈ S(P)` present (a level-3 helper or a level-3 output), `t ∈ S(P) ∪ V2` present;
* `G = 32 + |P| + |L2| + |H3|`.
`d2_scoped.py` builds the CP-SAT model: one Boolean per candidate level-2 mask, per level-3 mask (helper or
output), per construction (operand pair) and per level-4 recipe `{s, t}`; "present => some construction with
present operands", "output => a level-3 construction or a level-4 recipe"; minimise `|L2| + |H3|`. Every circuit
of the scope maps to a feasible point of the same cost, so the optimum is a valid lower bound for the scope,
and the solver's witness is a circuit, so it is exact. `d3_subset.py` adds a Boolean per pair (cost 1, with the
level-2 constructions requiring their pairs): scope "weight-2 set is a **subset** of `P`", which is closed under
dead-gate deletion and is the robust form. The model is equivariant under the byte rotation `Z4`, which maps
the target set onto itself [finite-checked, `d4_post.py` (a)], so each statement transports to the three
rotated pair sets.

Instance sizes for `P = P89` (the 89's 26 pairs) [finite-checked, F5, `d2_C.out`]: `|U2| = 1060` (759 triples,
301 quartets), `|S| = 189,027`, 581,886 constructions, 169,165 level-4 recipes; 26 of the 32 outputs are
level-3-realisable over `P89` for *some* level-2 choice and 6 never are (y1, y4, y11, y17, y20, y27, weights [7, 7, 7, 7, 7, 7]).

### 5.2 Results

| scope | optimum | witness | solver | consequence |
|---|---:|---|---|---|
| A: weight-2 set = `P89`; level-2 gates = the 89's 22 (all forced present) | **31** = `h2 + h3` | `h2 = 22, h3 = 9`, 20 outputs at level 3 | CP-SAT OPTIMAL, 0.1 s | `G >= 89`: no 88 keeps the 89's shallow bank |
| B: weight-2 set = `P89`; level-2 gates any subset of the 30 masks of the 81-state family L0 (18 core + 4 x 3 slot values) | **31** | same profile | CP-SAT OPTIMAL, 0.8 s | `G >= 89` over the family's whole level-2 pool |
| D (`d3_subset.py`, pool L0): weight-2 set **any subset** of `P89`, level-2 gates any subset of the 30 family values, pairs cost 1 | **57** = `|L1| + |L2| + |H3|` | `|L1| = 26, |L2| = 22, |H3| = 9`, 20 outputs at level 3 | CP-SAT OPTIMAL | `G >= 32 + 57 = 89` |
| C: any subset of all 1060 triples/quartets over `P89` | **not resolved** (CP-SAT 1 worker, default linearisation, 900 s: feasible 65.0, proved bound 0; CP-SAT 1 worker, linearization_level 2, 660 s: status FEASIBLE, feasible 144.0, proved bound 0; LP relaxation (scipy/HiGHS, 886,046 variables, 1,580,115 rows): time limit 700 s reached, no value) | the solver's best circuits are far above 31 | not proved | no scoped exclusion of 88 over `P89` alone |

Scripts and outputs: `d2_scoped.py A|B|C` -> `d2_A.out`, `d2_B.out`, `d2_C.out`, `d2_scopeA.json`, `d2_scopeB.json`
(witness value sets); `d2_scoped.py C 660` with `linearization_level = 2` -> `d2_C_lin2.out`; `d2_scoped.py C 700 lp` ->
`d2_C_lp.out`; `d3_subset.py 300 <P89> P89 L0` -> `d3_P89-L0pool.out/.json`. One CP-SAT worker per run under `nice -n 8`.

**What these exclude, exactly.** A/B: there is no depth-4 circuit with <= 88 gates whose weight-2 masks are
exactly the 89's 26 pairs and whose level-2 masks are among the 22 (resp. 30) listed values, and by `Z4` none
over the three rotated copies. D: the same with any subset of the 26 pairs (so a trimmed sub-circuit of the
family's vocabulary cannot be 88 either). They say nothing about circuits with a different pair set, in
particular not about exchanges of one pair for another (the subset case over the family pool is scope D); and scope C (level-2 layer completely free
over `P89`) is not resolved (see the row). How this relates to q89: q89 measured that all 526 recorded 89@4
carry this first layer and that pinned completions over it reach 89 but never 88; A/B/D turn "never 88 inside
the family's vocabulary" into a theorem, while the free-level-2 statement over `P89` remains a run observation (scope C unresolved); scopes A, B, D make it a theorem inside the family's level-2 pool.

---------------------------------------------------------------------------------------------------------

## 6. Route C: is a depth-4 analogue of the depth-3 recipe proof tractable?

The depth-3 proof works because each output has a tiny last-gate recipe space: parents of weight <= 4, 285 / 35
decompositions, 53,280 complete recipes over 8,393 helper masks; one 61,673-variable 0/1 system with valid
cutting planes and exact Farkas certificates.

At depth 4 [finite-checked, F4]: a last-gate parent may have weight up to 8, and the unordered splits
`{a, o + a}` with `|a|, |o + a| <= 8` number **1,123,414** per weight-5 output and **592,114** per weight-7 output
(factors 3,900 and 17,000 over depth 3). Each level-3 parent has its own decompositions into two level-<= 2
signals (hundreds each), and a level-4 output can combine two level-3 helpers (the 89 does, for 6 of 12). An
unconditioned complete-recipe model has on the order of 10^9-10^10 recipe variables: not an LP one can write
down, let alone certify.

What *is* tractable is the model conditioned on the first layer (section 5): with `P` fixed, the level-3
universe is 1.9 x 10^5 and the recipe lists 1.7 x 10^5 in total. The restricted versions (A, B, D) solve in
seconds; the free version (C) builds in 31 s but a single CP-SAT worker proves no bound in 900 s -- the
exactness is there, the strength of the LP relaxation is not (section 9 item 1 says how to push it). A full
depth-4 bound by this route needs (i) an enumeration of pair sets up to symmetry under `p + b >= 24`, hopeless
as stated, or (ii) a conditioning coarser than the pair set that keeps the recipe space small (section 9, 2).

---------------------------------------------------------------------------------------------------------

## 7. The archive's depth-4 attempts: what they tried and where they stopped [archive, unverified]

`AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23` (REPORT.txt, `depth4_structure/`, `depth4_layer_bound/`,
`depth4_accounting/`) and `AES_DEPTH4_RECURSIVE_ACCOUNTING_PUSH2_2026-10-23` (README.txt,
`layer/FINAL_LAYER_STATUS.txt`, `accounting/`). Both say in their first lines that the rigorous total bound
stays at 75 and that no 88@4 exclusion was obtained. Their content, as read:
* the same normal form and layer grammar as section 2 ("late OO births" = my `b`);
* a component-signature lemma (modulo the pair-graph components a level-3 odd signal has unit signature, a
  late birth joins two components, so a depth-4 output has signature weight 1 or 3), and from it with the
  complete census of graph-code words of weight <= 8 (84 of weight 6, 276 of weight 8, as in the 75 and 93
  packages) `c <= 20` components and `p >= 12`;
* local "full helper" census results (`F3 + 2F5 <= 10`, `FA + 2FB + 2FC <= 10 + R`), a coupled geometry constant
  `N + 4p + kappa >= 81` (not a gate count), and an aggregate LP/MILP over helper-type counts in which integer
  75-gate profiles survive for every `q = 1..15`;
* the obstacle they name: the 75 proof's transposition / stabilisation steps do not preserve depth, so
  depth-4 rows cannot be appended to the 75 certificate.
None of this was needed for sections 2-5 and I verified none of it. Lemma 4 is stronger than their `p >= 12` in
the regime that matters and needs only the verified 75 package.

---------------------------------------------------------------------------------------------------------

## 8. Best bound and the obstacle

**Bound.** `D4 >= 75` [proved, unrestricted]. For depth 4 specifically I prove no number above 75.

**Why not 76 from the depth-4 structure.** Three independent reasons, each sufficient:
1. The only depth-specific restrictions that hold unconditionally are the layer grammar and its consequences
   (Lemmas 2-6). They bound `p + b`, the level-2 parents of *level-3* outputs and the helper-free option of
   level-4 outputs; they bound neither the fan-out of level-3 helpers nor the level-2 bank behind level-4
   outputs. Their yield is `G >= 57`. A circuit that puts most outputs at level 4 is, for these lemmas, almost
   unrestricted -- and the 89 already puts 12 there.
2. The 75 proof gets from 69 to 75 through the raw transpose (accumulation trees, `lb75/PROOF.md` Lemma 3.1:
   a signal of fan-out `d` becomes a `d`-leaf tree in the transpose), the global maximum `Y`, double
   transposition and a Farkas system on helper-type counts. The transpose of a depth-4 circuit has no depth
   guarantee (its depth depends on the fan-outs and tree associations), so depth-4 rows are legal only in the
   original orientation, where the rows available are those of reason 1; and the lb76 agent showed today that
   the package's inequalities cannot exclude 75 even unrestricted (1,508 oriented claims survive).
3. The recipe route that proves 93 at depth 3 needs the first layer to be effectively known (section 6). The
   first layer is exactly what is free at depth 4 (90@4 circuits exist with 21-26 pairs; the 89 has 26; Lemma 4
   allows as few as `24 - b`).

**What is proved beyond 75.** Structural: Lemmas 2-6 for every depth-4 circuit, in particular `p + b >= 24` and
the 20-pair characterisation of helper-free level-4 outputs. Scoped: the exact optima of section 5, which make
the recorded 89 provably optimal among depth-4 circuits over its own first two layers and over the family's
level-2 pool (with droppable pairs, scope D).

**Conjecture** [conjecture, from q89's data and section 5]: `D4 = 89`. The support is one first layer out of 183
recorded ones and the scoped optima above; it is not strong.

---------------------------------------------------------------------------------------------------------

## 9. What a longer campaign would do

1. **Finish scope C, then run it per first layer.** The free-level-2 model over `P89` is exact but its LP
   relaxation is weak. Three cheap strengthenings, all sound: (a) add the valid rows of section 3 as
   constraints (each weight-7 output at level 4 needs a present level-3 helper operand; `h2 >= |Y3 ∩ weight-7|`);
   (b) branch on the level of the 12 weight-7 outputs first (`2^12` cases, most killed by (a) and by the six
   never-level-3 outputs), each case a far smaller model; (c) 8 CP-SAT workers when the machine is free. With
   scope C closed for `P89`, run the same for the 183 recorded 90@4 first layers and the 26 x 470 single-pair
   exchanges of `P89`: every layer with optimum `h2 + h3 <= 30` is a direct lead for the search engine (the
   solver returns the circuit), every other one a theorem. Minutes per 26-pair layer once (a)-(b) are in;
   21-23-pair layers have larger `U2` relative to the budget [guess: hours].
2. **Condition on the pair-graph partition, not the pair set.** With `b = 0` the even-span partition has
   `c <= 8` blocks whose words `(1_C, M 1_C)` are disjoint graph-code words; the depth-3 proof enumerates exactly
   these partitions (275,354 + 22,060 + 110,712 at `p = 26`). For a partition, all pairs inside its blocks are
   candidates; `U2` and `S` grow but stay finite, and a per-partition optimum `>= 44` for every partition would be
   `D4 >= 76`. The `b > 0` case adds late births joining blocks (the archive's signature lemma bounds it). This is
   the only route I see to a full depth-4 bound; it is a multi-day computation [guess].
3. **A depth-3 sub-map bound for the level-3 outputs.** For any depth-4 circuit `p + h2 >= H3(Y3)`, where
   `H3(Y)` is the optimum of the depth-3 complete-recipe model restricted to the outputs `Y` (level-3 outputs of
   a depth-4 circuit are depth-3 outputs over the same shallow bank). `H3(all 32) = 61` gives `k = 0 => G >= 93`;
   a table over subsets would give "a depth-4 circuit with `G <= 88` has at least `k_min` outputs at level 4". The
   package ships the checker, not the LP generator, so this needs a re-implementation of the base model (one or
   two days); the parent-cover numbers of section 3 are its pair-free part.
4. **Do not** try to append depth-4 rows to the 75 certificate's transposed or stabilised phases (reason 2).

---------------------------------------------------------------------------------------------------------

## 10. Files

| file | content |
|---|---|
| `d1_facts.py` -> `d1_facts.out`, `d1_facts.json` | map facts F1, 89 census F2, depth-3 decompositions and parent capacities F3, depth-4 split counts F4, conditioned universe sizes F5 |
| `d2_scoped.py` -> `d2_A.out`, `d2_B.out`, `d2_C.out`, `d2_C_lin2.out`, `d2_C_lp.out`, `d2_scopeA.json`, `d2_scopeB.json` | the conditioned exact model and its optima (A, B), the unresolved C (two CP-SAT settings, one LP attempt) |
| `d3_subset.py` -> `d3_P89-L0pool.out`, `d3_P89-L0pool.json` | droppable pairs (weight-2 set a subset of `P89`), family level-2 pool (scope D) |
| `d4_post.py` -> `d4_post.out` (first run, killed by its timeout while buffering), `d4_post_lin2.out`, `d4_post.json` | rotation invariance, never-level-3 outputs over `P89`, parent-cover instances, structure of the 20 pairs |
| `r1.sh`, `d5_write_report.py` | run script; this report's assembler (numbers are read from the files above) |
