# Odd-helper parity theorems for AES MixColumns: restatement, replay, independent recomputation, h = 0 / 1 derivations, h = 3 status

Date: 2026-11-07. Working directory: `~/xs-campaigns/2026-11-07-sprint/oddh/`.
Source under review: `~/xs-campaigns/2026-11-07-sprint/import/zip/research/AES_Research_Fleet_Checkpoint_2026_10_06/AES_MixColumns_Two_Odd_Helpers_90/`
(23 Sep 2026; `proof/TWO_ODD_HELPERS_90.md`, three C++ checkers, `results/`). Copy of the package in `archive_copy/`.

Labels: **[proved]** = I checked every step of the argument myself; **[finite-checked]** = a finite fact about the fixed
matrix that my own script (`indep.py`) computed from the repo matrix file, independently of the archive's code;
**[replayed]** = the archive's own checker, rebuilt and rerun here, agreeing with its stored output;
**[read, not checked]** = taken from the archive text; **[guess]** = my estimate.

---

## 0. Verdict in six lines

1. The h = 2 theorem (exactly two odd signals other than inputs and outputs => G >= 90) holds up: the written reduction
   is sound [proved]; all three archive checkers compile, pass, and reproduce their stored JSON byte for byte [replayed];
   every finite fact I recomputed from the repo matrix agrees (3,592,052 candidate pairs; rank histogram
   113,892 / 3,444,740 / 30,572 / 2,848; max r = 6; dim R6 = 20; quad capacities 2,046 / 291 / 36; single-helper table)
   [finite-checked].
2. The lost h = 0 proof is recovered: **h = 0 => G >= 92** [proved + finite-checked]. Beyond the 75 proof's F1-F3 and
   dim R6 = 20 it needs only a check of 1,360 label triangles (joint rank <= 7 against a required 15).
3. The lost h = 1 proof is recovered: **h = 1 => G >= 91** [proved + finite-checked]. It needs the single-helper table
   (recomputed, section 5.3) and, for the single open case (p = 3, u a "full" value), 64 triangles per rotation orbit
   of full helper (joint rank 6 against 15; for the d(u) = 3 orbit a capacity ceiling 12 against 13 closes it with no
   triangle at all).
4. Hence **every MixColumns circuit with G <= 89 has at least three odd helpers**; a hypothetical 87 has h >= 3.
   All of it rests on F1 (x >= 24) from the 75 package, which I did not rerun.
5. The general ledger behind all three theorems is `G >= 88 + 2h + p - r` together with `H >= 12 + h + p - d`
   (section 2.5) [proved]; it is sharp only at small h, where the helper-tuple enumeration is finite.
6. **h = 3 => G >= 89 is not proved** and is not a 20-minute computation. The four-relation rank domain for the
   required r >= 6 is *infinite* at p = 0 (any third helper next to a rank-6 pair), and at p >= 1 the finite r >= 7
   domain has more than 10^8 survivors (section 6) against 2,848 at h = 2. I enumerated 5.3 x 10^8 structured
   triples: max r = 9, never 10.

---

## 1. Setting (same model as the 75 proof)

Normalized acyclic two-input XOR circuit for the 32 x 32 MixColumns matrix: 32 inputs, G gates, all 32 + G masks
distinct and nonzero, every gate used, each row carried by exactly one gate (PROOF.md Lemma 1.1; normalizing an
arbitrary circuit never increases G or h, and the bounds 92 / 91 / 90 decrease with h, so the statements hold for
un-normalized circuits too). A signal is *odd/even* by the Hamming weight of its mask; inputs and outputs are odd.
B = the 64 boundary values (inputs + outputs). The h *odd helpers* are the odd gate values that are not outputs.
x = odd+odd gates, y = even+even gates (both even results), odd+even gates have odd results, so (Lemma 1.2)
**G = 32 + x + y + h**; e = x + y is the number of even gate values.

Facts from the 75 package that are used: **F1** x >= 24 [read, not checked: the 1,485,213-state partition enumeration;
the archive reports rerunning it, `partition24_recheck.json`]; **F2** Sidon: the 2,016 pairwise XORs of B are distinct
[finite-checked]; **F3** a value has at most 3 representations as an XOR of a boundary triple, histogram
40,704 / 360 / 80 [finite-checked]; **F5** the weight-6 zero-sum subsets of B are 60 unions of two equal-XOR disjoint
triples spanning R6 of dimension 20 [finite-checked].

---

## 2. The h = 2 theorem, restated so a careful reader can follow it

**Theorem** (archive, 23 Sep 2026). A normalized circuit with exactly two odd helpers u, v has G >= 90.

### 2.1 Why G = 34 + x + y
The odd gate results are exactly the 32 outputs and the two helpers: 34. Every other gate is odd+odd (x) or
even+even (y). So G = 34 + x + y = 34 + e. [proved; Lemma 1.2 with h = 2]

### 2.2 Formal gate equations
Give every signal a formal coordinate; gate g = a + b is the row E_g + E_a + E_b. The G rows are linearly independent:
in a nonempty subset the latest gate's result coordinate occurs in no other chosen row. So their span V has dim G.
[proved]

Let O = B u {u, v} (66 odd values). A gate row is *mixed* if it has two odd coordinates and one even one: this covers
odd+odd gates (even coordinate = result) and odd+even gates (even coordinate = operand); there are x + 34 of them.
The y even+even rows are *all-even*. An even gate value l is *exposed* if l = a + c for some a, c in O (as masks) and
*hidden* otherwise; p = number of hidden even gate values. A hidden value occurs in no mixed row (such a row says
l = a + c), so hidden values live only in all-even rows. [proved]

### 2.3 The four-term ledger: y >= 34 + p - r
For each exposed l fix a representation l = a_l + c_l and the row S_l = E_l + E_{a_l} + E_{c_l} (not necessarily a
circuit row). The e - p rows S_l are independent (distinct pivots E_l). A circuit mixed row E_l + E_a + E_c differs
from S_l by E_a + E_c + E_{a_l} + E_{c_l}: a *true four-term relation on O* (four distinct elements of O with XOR 0)
or 0. Let r = rank of all true four-term relations on O (vectors in F_2^66). All mixed rows lie in
span{S_l} + (four-term relations), dimension <= (e - p) + r; the all-even rows add <= y. Hence

    G = e + 34 <= (e - p) + r + y,   i.e.   y >= 34 + p - r.                                (1)

With F1: **G >= 92 + p - r**, so G <= 89 forces **r >= p + 3**. [proved]

### 2.4 r <= 6 for every helper pair [proved + finite-checked]
A four-term relation on O is a 4-subset of O with XOR 0. None lies inside B (Sidon). The others are {u} u T with T a
boundary triple of XOR u (w_u <= 3 of them by F3), {v} u T (w_v <= 3), or {u, v, a, b} with u + v = a + b (delta in
{0, 1}, unique by Sidon). So

    r <= w_u + w_v + delta <= 7.                                                              (2)

r >= 4 needs delta = 0 and w_u + w_v >= 4, or delta = 1 and w_u + w_v >= 3; either way one helper has w >= 2 (440
values) and the other is a triple value (41,144) or that helper XOR one of the 2,016 pair values: a finite domain of
3,592,052 unordered pairs after removing boundary values and repeats [finite-checked = archive]. Exact ranks of the
<= 7 rows: r = 3 : 113,892; 4 : 3,444,740; 5 : 30,572; 6 : 2,848; **never 7** [finite-checked = archive]. Pairs
outside the domain have r <= 3 by (2). So r <= 6 always, and (1) alone gives only G >= 86 + p: the theorem needs a
second, finer ledger. My (w_min, w_max, delta, r) histogram equals the archive's `detailed_histogram` cell for cell:
the 2,848 rank-6 pairs are 2,800 with profile (3, 3, 0) and 48 with (2, 3, 1); two full values at pair distance give
rank 5 (360 pairs; this is the 75 proof's F4).

### 2.5 The quotient ledger, and its general-h form
Adjoin the e - p rows S_l and eliminate the exposed even coordinates (substitute l = a_l + c_l). The circuit rows keep
rank >= G - (e - p) = 34 + p, now over the 66 O-coordinates plus p hidden coordinates. A projected mixed row is a
four-term relation on O (or 0); a projected all-even row with no hidden coordinate is a true relation on O of weight
<= 6. Let S6(O) = span of all true relations on O of weight <= 6, R6 = S6(B) (dim 20), d = dim S6(O)/R6. Everything
without a hidden coordinate lies in S6(O); writing H for the rank, modulo S6(O), of the projected rows that carry a
hidden coordinate,

    34 + p <= 20 + d + H,   i.e.   H >= 14 + p - d.                                           (3)

For general h (O has 64 + h elements; x + 32 + h mixed rows; G = 32 + h + e) the same two computations give

    y >= 32 + h + p - r,     G >= 88 + 2h + p - r,     H >= 12 + h + p - d.                   (4)  [proved]

Hidden-carrying rows after substitution are of three kinds: (i) one hidden w plus four O-coordinates (w is the XOR of
four distinct elements of O; distinctness because a repeated element would make w exposed); (ii) two hidden plus two
O-coordinates (w + w' exposed); (iii) three hidden (w + w' + w'' = 0). Modulo S6(O): for fixed w, kind-(i) rows differ
by differences of 4-representations of w; c(w) := rank modulo S6(O) of those differences (*capacity*), so kind (i)
contributes <= 1 + c(w); for a fixed pair, kind-(ii) rows differ by a four-term relation on O, so <= 1 per pair and
only if w + w' is exposed; kind (iii) <= 1 when p = 3 and is exclusive with the three pair rows (if w'' = w + w' then
w + w' is hidden). [proved]

*Capacity bound.* 4-representations of w from O = B u {u, v}: four boundary values (differences have rank <= 3 modulo
R6: the quad capacity; 36 values attain 3 [finite-checked]); u + boundary triple (all representations of w + u as
triples are congruent modulo R6: <= 1 new dimension); v + triple (<= 1); u + v + boundary pair (unique: <= 1). So
**c(w) <= 6**, and c(w) >= 3 needs a nonzero quad difference space (2,373 *active* labels) or all three helper kinds at
once (then w = u + v + pair, <= 2,016 candidates): the archive's small complete domain for high capacity. [proved]

### 2.6 Case split on p, assuming G <= 89 (so r >= p + 3 and (3))
* **p = 0.** H = 0, so d >= 14 is needed. d <= d(u) + d(v) + a(u + v) with d(t) = dim S6(B u {t})/R6 (single-helper
  table: d <= 7, 5, 3, 3 for w(t) = 0, 1, 2, 3 [finite-checked, section 5.3]) and a(s) <= 4 (reference + quad capacity
  3), a(s) = 1 if s is a pair value (its other 4-representations differ by elements of R6 [finite-checked: 0 exceptions]).
  delta = 1 needs w_u + w_v >= 2: d <= 5 + 5 + 1 = 11. delta = 0 needs w_u + w_v >= 3: every pattern gives <= 13 except
  (3, 0) with d(u) = 3, d(v) = 7: 4 x 4 = 16 pairs, each with d = 10 [replayed by both checkers]. **Impossible.**
* **p = 1.** r >= 4, so the pair is in the finite domain, where d <= 8 [replayed]. Need H >= 15 - d with
  H <= 1 + c <= 7, hence d >= 8: exactly 16 pairs, capacity ceiling 2, H <= 3. **Impossible.** [proved + replayed]
* **p = 2.** r >= 5. H <= 2(1 + C) + 1 with C the pair's capacity ceiling; need H >= 16 - d. Over the nine (r, d, C)
  rows with r >= 5 the maximum of d + 2(1 + C) + 1 is 13 (row (5, 4, 3)). **Impossible.** [replayed]
* **p = 3.** r = 6: 2,848 pairs, d in {2, 4, 5} (2,558 / 284 / 6). Need H >= 17 - d. d = 4: C <= 2, H <= 9 + 3 = 12 < 13.
  d = 2: C <= 3, H <= 12 + 3 = 15 = required; d = 5: C <= 2, H <= 9 + 3 = 12 = required. Equality needs three
  maximum-capacity labels with all three pair sums exposed; the *joint* rank of each such triangle is computed:
  174,180 triangles, ranks 6 / 7 / 9 (d = 2, needs 15) and 6 (d = 5, needs 12). **Impossible.** [replayed]
* **p >= 4.** r >= 7 contradicts 2.4. **Impossible.** [proved]

Therefore no two-helper circuit has G <= 89. [proved, modulo the finite facts listed in 2.7]

### 2.7 Premise ledger

| premise | status here |
|---|---|
| gate-row independence; parity accounting; hidden values only in all-even rows; capacity/pair/pure bounds | [proved] |
| F1 x >= 24 | [read, not checked] (75 package; archive reports a rerun) |
| F2 Sidon, F3 multiplicities, 60 six-relations, dim R6 = 20 | [finite-checked] |
| quad capacity <= 3, histogram 2,046 / 291 / 36, 2,373 active; pair values have no extra 4-representation outside R6 | [finite-checked] |
| candidate domain 3,592,052; rank histogram; max r = 6; detailed histogram | [finite-checked] + [replayed] |
| single-helper table d(t) <= 7 / 5 / 3 / 3, exactly 4 values each at (0, 7) and (3, 3) | [finite-checked] |
| (r, d) table, capacity table, the 16 extreme pairs (d = 10), 174,180 triangles | [replayed] (two checkers + audit) |
| five 88-gate controls with 17-22 odd helpers | [read, not checked] (needs the missing zip); our own 88s: 16-24 (`oddhelpers.py`) |

*What the checkers compute.* `verify_two_helpers_primary.cpp`: rebuilds AES from byte arithmetic, all 2-/4- and
3-/5-subsets of B, the candidate pairs and r for each, d for r >= 4 (annotations projected onto the 12 weight-7 output
coordinates; the audit avoids this shortcut), the capacity ceiling for r >= 5 or d = 8, and asserts every histogram.
`verify_two_helpers_triangles.cpp`: the 16 extreme pairs, the 2,848 rank-6 pairs, and all equality triangles (for the
six d = 5 pairs it enumerates all C(66, 4) = 720,720 quadruples). `independent_two_helper_audit.cpp`: a different AES
construction (xtime formulas), full 64-coordinate incidence, explicit R6, 128-bit rows, byte-rotation symmetry
(verified against every output row) for capacity/triangle work; asserts equality with the primary numbers.

---

## 3. Replay of the archive checkers [replayed]

*Inputs:* none. All three programs rebuild the matrix internally and agree with the repo file
`circuits/aes-mixcolumns/aes-mixcolumns.mat.txt` (asserted in `indep.py`). The missing `recovered_originals/*.zip` is
needed only by the *support* stage of `run_checks.py` (x >= 24 partition recheck, 75 certificate, five 88 controls);
that stage could not be run. The theorem's own checks do not depend on it. The x >= 24 fact lives in the repo's own
75 package (`lower-bound-proofs/mixcolumns-lb75/`, `checks/finite_facts.py`) if a rerun is wanted.

Compiled `g++ -O2 -std=c++17` (assertions live), run one at a time under `nice -n 8` (`run_checkers.sh`, log
`run/checkers.log`, machine under load average ~20-26):

| checker | wall | exit | result |
|---|---:|---:|---|
| verify_two_helpers_primary | 159.6 s | 0 | JSON identical to `results/reproduction/primary.json` |
| verify_two_helpers_triangles | 14.4 s | 0 | JSON identical to `results/reproduction/triangles.json` |
| independent_two_helper_audit | 84.0 s | 0 | JSON identical to `results/independent_audit.json` |

All report `all_checks_pass: true`. Side tables `two_helper_cap3_candidates.tsv`, `two_helper_pairs_r4_ge5.tsv`,
`two_helper_short_critical.tsv`, `two_helper_triangle_pairs.tsv` are byte-identical to the archive;
`two_helper_caps.tsv` is identical after sorting (its row order follows an `unordered_set`). **PASS.**

---

## 4. Independent recomputation [finite-checked] (`indep.py` -> `indep_results.json`)

Plain-Python GF(2) vectors built from the repo matrix file (cross-checked against byte arithmetic), no code shared
with the checkers. Run time: facts + h0 2 s; pairs + h1 47 s; d-table 45 s.

| quantity | mine | archive |
|---|---:|---:|
| distinct boundary pair sums | 2,016 | 2,016 |
| triple multiplicities 1 / 2 / 3 | 40,704 / 360 / 80 | same |
| weight-6 relations; rank R6 | 60; 20 | 60; 20 |
| 2-/4-subsets of B | 637,392 | 637,392 |
| quad difference ranks mod R6: 1 / 2 / 3 | 2,046 / 291 / 36 (active 2,373) | same |
| pair values with a 4-representation outside pair + R6 | 0 | (implicit: a(s) = 1) |
| candidate pairs for r >= 4 | 3,592,052 | 3,592,052 |
| r histogram 3 / 4 / 5 / 6 / 7 | 113,892 / 3,444,740 / 30,572 / 2,848 / 0 | same |
| detailed (w_min, w_max, delta, r) histogram | 16 cells, all equal | `detailed_histogram` |
| single-helper table (w, d) counts | section 5.3 | d <= 7 / 5 / 3 / 3; four at (0, 7); four at (3, 3) |
| single-helper spectrum size | 6,603,808 non-boundary values | 6,603,808 |
| byte rotation preserves B | yes | asserted by the audit |

So the key finite fact of 2.4, **max r = 6 over all helper pairs**, is confirmed on the full domain, not a sample.

---

## 5. The lost h = 0 and h = 1 proofs, derived here

Both use ledger (4), the finite facts above, and small new checks; exposed/hidden, capacity and the pair/pure bounds of
2.5 apply verbatim with O = B u H.

### 5.1 h = 0 => G >= 92 [proved + finite-checked]
O = B. By Sidon there is no four-term relation on B: **r = 0**. Ledger (4): y >= 32 + p and **G >= 88 + p**.
Quotient: S6(B) = R6 (d = 0) and **H >= 12 + p**, H the rank modulo R6 of the hidden-carrying rows. A hidden w has only
boundary-quad representations, so c(w) <= 3 and kind (i) gives <= 4 per hidden value; kind (ii) <= 1 per pair with
exposed sum; kind (iii) <= 1, exclusive with the pairs.
* p = 0: 12 <= 0; p = 1: 13 <= 4; p = 2: 14 <= 8 + 1. All impossible.
* p = 3: 15 <= 12 + 3, equality only if all three labels have quad capacity 3 (the 36 rank-3 labels, none of which is a
  pair value) and all three pair sums are boundary-pair values. Check (`stage_h0`): of the C(36, 3) = 7,140 triples,
  1,360 have at least one exposed pair (1,152 / 144 / 64 with one / two / three); the exact joint rank modulo R6 of
  (3 references + 9 differences + pair rows) is 7 / 6 / 6 respectively, never 15. Impossible.
* p >= 4: G >= 92 directly.

So every h = 0 circuit has p >= 4 (independently of G) and **G >= 92**.

### 5.2 h = 1 => G >= 91 [proved + finite-checked]
O = B u {u}. Four-term relations on O are u + boundary triple: r = w(u) <= 3 (distinct triples give independent rows).
Ledger (4): y >= 33 + p - w(u), **G >= 90 + p - w(u)**, **H >= 13 + p - d(u)** with d(u) = dim S6(B u {u})/R6.
Capacity: boundary quads (<= 3) plus u + triple (<= 1): c(w) <= 4, kind (i) <= 5 per hidden value. Suppose G <= 90;
then p <= w(u).
* p = 0: needs d(u) >= 13; d(u) <= 7 for every odd u (5.3). Impossible.
* p = 1: w(u) >= 1 so d(u) <= 5; H >= 14 - d(u) >= 9 but H <= 5. Impossible.
* p = 2: w(u) >= 2 so d(u) <= 3; H >= 12 but H <= 2 x 5 + 1 = 11. Impossible.
* p = 3: w(u) = 3 (u is one of the 80 *full* values; G = 90, x = 24, y = 33 exactly) and H >= 16 - d(u), with
  H <= 3 + sum c_i + (exposed pairs <= 3). Check (`stage_h1`), per rotation orbit of full u (20 orbits): d(u) exactly
  (one orbit of 4 values has d = 3, the 19 others d = 1); exact capacity modulo S6(O) of every label that can have
  c >= 1 (active quad labels, and u + triple values that also have a quad representation; 2,132-2,613 labels per u;
  capacity ceiling 2 for the d = 3 orbit, 3 otherwise); joint rank of every triangle that could reach the requirement,
  including a capacity-0 third label pinned by two exposure constraints. d = 3 orbit: ceiling 3 + 6 + 3 = 12 < 13,
  nothing to check. d = 1 orbits: requirement 15 forces three capacity-3 labels with three exposed pairs, 64 triangles
  each, joint rank 6. Impossible.
* p >= 4: G >= 90 + 4 - 3 = 91.

So **G >= 91** whenever h = 1.

### 5.3 The single-helper table d(u) [finite-checked] (`stage_h1tab`)
d(u) = [w(u) >= 1] + rank modulo R6 of the differences between the 3- and 5-subset representations of u. Exact for the
41,144 triple values; for w = 0, d(u) <= number of 5-subset representations (<= 6 unless >= 7), exact for the 4,888
values with >= 7.

| w(u) | d(u) histogram | max |
|---:|---|---:|
| 1 | d = 1: 38,584; 2: 784; 3: 388; 4: 752; 5: 196 | 5 |
| 2 | d = 1: 300; 3: 60 | 3 |
| 3 | d = 1: 76; 3: 4 | 3 |
| 0 | 5-subset multiplicity up to 14; among the 4,888 values with >= 7 representations: d = 1: 3,312; 2: 240; 3: 340; 4: 320; 5: 672; **7: 4** | 7 |

This is exactly the archive's table including "exactly four values with w = 0, d = 7 and four with w = 3, d = 3".

---

## 6. Extension to h = 3 [not proved; partial enumeration]

Ledger (4) with h = 3, O = B u {u, v, t} (67 values): **G >= 94 + p - r** and **H >= 15 + p - d**. Four-term relations
on O: helper + triple (<= 3 each), two helpers + pair (<= 1 each), three helpers + one boundary value (<= 1), so

    r <= w_u + w_v + w_t + delta_uv + delta_ut + delta_vt + eps <= 13,   r <= r(u, v) + w_t + delta_ut + delta_vt + eps <= 12.  [proved]

G <= 88 requires **r >= 6 + p**. Capacity: c(w) <= 3 + 3 + 3 + 1 = 10, so kind (i) <= 11 per hidden value.

**Why the h = 2 recipe does not transfer directly.**
* p = 0: r >= 6 is satisfied by every (u, v) with r(u, v) = 6 (2,848 pairs) together with an *arbitrary* t: the rank
  domain is infinite. The case must be closed through the quotient ledger alone (H = 0 forces d(O) >= 15), and the
  natural analytic bound d(O) <= d(u, v) [<= 5 on rank-6 pairs] + d(t) [<= 7] + a(u + t) + a(v + t) [<= 4 each] +
  a_3(u + v + t) [<= 2] = 22 does not close it. The residual enumeration runs over t in (u xor quad values) u
  (v xor quad values) u (5-subset values with large d), about 1.3 M values per pair, 712 pair orbits under byte
  rotation: ~10^9 short-relation ranks, each far costlier than a four-term rank. Hours to days of CPU [guess].
* p >= 1: r >= 7 forces all three helpers to be anchored (w >= 1, or adjacent to another helper, or u + v + t in B), a
  finite domain whose bulk I enumerated below. The problem is the survivor count: already (full, full, triple value) gives
  1.14 x 10^8 triples with r = 7, each of which would need its (r, d) entry and capacity ceiling. At h = 2 the analogous
  survivor set (r >= 4) had 3.48 M members and the sharp cases numbered 2,848.
* The task's "64^3 / 6" is not the right size: helpers are arbitrary odd 32-bit masks, not members of a 64-value
  vocabulary; the finite domains come from the anchoring inequality above, as at h = 2.

**What I ran** (`h3_rank.cpp`: exact rank of the <= 13 relation rows per triple, `nice -n 8`, total 312 s wall;
`run/h3_rank.json`):

| domain | triples | time | r histogram | max r |
|---|---:|---:|---|---:|
| D1: all 3-subsets of the 440 repeated values (w >= 2) | 14,100,680 | 9 s | 4: 1,200; 5: 321,432; 6: 7,417,392; 7: 5,251,720; 8: 1,049,304; 9: 59,632 | 9 |
| D2: (u, v) both full x t any triple value (w_t >= 1) | 130,008,720 | 91 s | 6: 14,657,568; 7: 114,136,144; 8: 1,043,104; 9: 171,904 | 9 |
| D3: (u, v) both repeated x t adjacent to u (t = u + pair) | 388,123,200 | 218 s | 4: 3.48 M; 5: 245.8 M; 6: 122.3 M; 7: 15.93 M; 8: 632,352; 9: 8,192 | 9 |
| D4: (u, v) both full x t adjacent to both | 133,968 | 1 s | 6: 89,280; 7: 36,432; 8: 7,552; 9: 704 | 9 |

Rank 9 is attained by three pairwise non-adjacent full values (profile (3, 3, 3, 0, 0): 56,320 of the C(80, 3) = 82,160
full triples) and by a few adjacent profiles with weight sum 8; adjacency never pushes r above the weight sum, as at
h = 2 (two adjacent full values have rank 5, not 7). **No triple with r >= 10 was found** in 5.3 x 10^8 triples
[finite-checked on these domains; the universal bound remains r <= 12, proved].

**What is proved for h = 3.** Only the ledger: G >= 94 + p - r [proved], so a <= 88 circuit with three odd helpers
needs four-term rank r >= 6 + p among its 67 odd values (r >= 7 + p for an 87), and r <= 12 universally; on the
enumerated domains r <= 9, which would cap p at 3 (2 for an 87) there. A complete proof of h = 3 => 89 would need, as at
h = 2: (a) a universal r bound via the finite r >= 7 domain (D2/D3 are its bulk; the remaining profiles with two or
three adjacencies are small), (b) an (r, d) table and capacity ceilings over >= 10^8 survivors or a new analytic
pruning, (c) joint-rank triangle checks for p up to r_max - 6, and (d) the analytic p = 0 case with its ~10^9-term
residual enumeration. My estimate: a day or two of C++ plus CPU-hours to CPU-days; not a 20-minute job [guess].

---

## 7. What the theorems say about an 87 (and an 88)

* Any circuit with G <= 89 has **h >= 3 odd helpers**: h = 0 => 92 [proved here], h = 1 => 91 [proved here],
  h = 2 => 90 [archive; replayed, finite facts independently confirmed]. All three rest on F1 (x >= 24).
* Known 88s are nowhere near this boundary: 16-24 odd helpers in our hunt samples (`oddhelpers.py`), 17-22 in the
  archive's five controls. The theorems rule out hypothetical very regular circuits, not the kind search finds.
* Ledger (4) read at G = 87: `87 >= 88 + 2h + p - r` gives **r >= 2h + 1 + p**. With h >= 3 the four-term relations among
  the odd values of an 87 have rank at least 7 + p, i.e. its helpers must be unusually interlocked (many boundary-triple
  representations, helper adjacencies, three-helper relations). If h = 3 => 89 were established, an 87 would need
  h >= 4 and r >= 9 + p.
* Upper side (x >= 24, y >= 0): h <= G - 56, so an 87 has 3 <= h <= 31.
* Reliability of the archive on this item: good. Every number I could recompute matched; the write-up's reductions are
  correct; its only shortcoming is packaging (the zero/one-helper proofs and the support zip are missing), which this
  report repairs for h = 0 and h = 1.

---

## 8. Files

* `archive_copy/` - checkers, proof, results, run_checks.py copied from the import tree (archive untouched).
* `setup.sh`, `run_checkers.sh`, `run/checkers.log`, `run/verify_two_helpers_*.json`, `run/independent_two_helper_audit.json`, `run/*.tsv` - compile and replay.
* `indep.py`, `indep_results.json`, `run/indep_pairs_h1.log`, `run/indep_h1tab.log` - independent recomputation, h = 0 and h = 1 finite checks, single-helper table.
* `h3_rank.cpp`, `run/h3_rank`, `run/h3_rank.json`, `run_stage2.sh`, `run/stage2.log` - h = 3 sub-domain enumeration.
