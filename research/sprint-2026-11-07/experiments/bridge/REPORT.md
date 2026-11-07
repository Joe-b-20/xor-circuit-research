# Where do real MixColumns circuits live in the 75 proof's space?

Bridge agent report, 2026-11-07. Working directory `~/xs-campaigns/2026-11-07-sprint/bridge/`. The git
repository was read only; the proof package was used from the replayed copy `lb76/pkg_copy/` (unchanged).
All runs: one python process at a time under `nice -n 12`; total compute about 6 minutes
(`profile_real.py` 170 s, `mobile.py` 9 s, `tail.py` and `candidates.py` a few seconds each).

Labels: **[measured]** = output of a script in this folder on the real circuits; **[derived]** = my
arithmetic or a consequence of package lemmas plus measured facts; **[guess]** = unverified opinion;
**[proved in package]** = a lemma or finite fact of the 75 proof (read, not re-proved by me).

---

## 0. Summary in eight lines

1. 303 real circuits (200 sampled 88s distinct modulo byte rotation, 100 kste 88s, repo 88@5, 89@4, 97@3)
   were run through the package's own `Circuit.analyse`, `canonical_transpose` and `check_rows` for six
   steps of the transpose orbit. **Every assertion of the package passed and no row (L1)-(L23) was violated**
   on any of the 1,818 phases. [measured]
2. A value list determines the gate list essentially uniquely: in 290 of 303 circuits every value has exactly
   one admissible parent pair; in 13 one value (two in the 97@3) has two. The alternatives move x, y, q, z, F
   by at most 1 and the two-phase margin by at most 2. The repo circuits' true gate lists give exactly the
   reconstructed profiles. [measured]
3. The transpose orbit is **periodic with period 2 from the first canonical transpose on**, in all 303 circuits.
   On that tail the proof's drift inequality is an identity: `s_e + s_o = a + b + 2G - 192 - E_B`, with
   `E_B` = total boundary excess fan-out `sum_B max(0, d_v - 2)` of the two phases (L_H = 0 always). Real 88s
   have E_B = 0..7, so they sit 0 to 7 units *below* the budget the proof needs to exceed; 12 of 200 sit exactly
   on it. [derived from identity (E) + measured periodicity; verified numerically on 303 circuits]
4. Real 88 tail profiles: a in {24,25,26}, b in {24..27}, Y = 14..19, V = 10..17, h_e = 13..17, h_o = 14..20,
   q = 10..16, z = 0..7, s = 12..18 per phase. The 1,508 G = 75 survivors have Y <= 11, V <= 8, q <= 10,
   s <= 17 per two phases. The two populations are disjoint in Y and V, and overlap only partly in a, b, h. [measured]
5. No row of (L1)-(L23) is tight on a real circuit: the smallest slack over all 1,515 canonical real phases is
   10 (L4 reverse EE budget, L6, L12, Lemma 10.3), most rows have slack 20-130. The only tight statement is Lemma 7.4
   (helper degree >= 3 in a canonical transpose: slack 0 after shifting by one). [measured]
6. Hypothesis (a) confirmed with the package's definition: odd non-output helpers h = 16..23 in the sampled
   88s as found (17..23 kste), and 13..20 in every canonical transpose; the theorem "G <= 89 => h >= 3" is
   satisfied with 10+ to spare. [measured]
7. Hypothesis (b): every weight-2 even value is a represented label (it is the B-B edge between its two
   inputs); real 88s carry 13..20 of them (16..22 in T(C)), which is 55-80% of all represented labels
   (23..33). But they are **not** what the engine's neutral remove1 moves exchange: median 0 of 17 weight-2
   helpers per circuit is mobile (max 2); the 8-30 neutral moves per circuit swap one helper of weight 3-7 for
   one of weight 2-8. [measured]
8. Candidate universal inequalities: the real circuits leave the shipped rows so slack that *no* row can be
   sharpened by their evidence alone, and every simple combination of (x, y, h, q, z, F) that the real 88s
   satisfy is broken by one of the package's 13 control circuits except `q >= 7` (and trivialities). `q >= 7`
   would cut 1,017 of the 1,134 LP-feasible keys at G = 75, but I have no argument for it. [measured; conjecture]

---

## 1. Method

**Inputs.** `hunt/samples.jsonl`, `hunt/samplesC/samples.jsonl`, `hunt/samplesD/samples.jsonl`: 8,654 records,
of which 3,385 have `gates == 88` (3,383 distinct hashes); each 88 record's `values` list has exactly 88
entries: the 32 output rows plus 56 helper masks (no inputs). [measured] I drew records round-robin from the
three files, keyed each by the minimum over the four byte rotations of its sorted helper tuple, and kept the
first 200 distinct keys (A: 67, C: 67, D: 66). From `kste/data/kste_valuesets.json` (17,462 value lists) I
took 100 distinct-mod-rotation 88-value lists at random (seed 1). The three repo circuits were parsed from
their NCFF files into true gate lists.

**Reconstruction (`profile_real.py: reconstruct`).** Inputs get level 0; a value gets level L+1 when it is
the XOR of two signals of level <= L (rounds; every value of every circuit was placed, i.e. each is a XOR of
two earlier values). For each value the admissible pairs are all (a, b), a xor b = v, with both parents of
strictly lower min-level (this guarantees acyclicity). The base choice maximizes even+even gates (prefer an
even-even pair for an even value), which is the analogue of the package's canonical transpose rule; with a
fixed level structure the per-value choices are independent, so greedy is a global maximum within the
admissible family. A dead-signal repair loop re-chooses pairs if a helper ends up unused (never triggered:
0 repairs in 303 circuits). Gates are emitted in (level, mask) order; the package's `Circuit` constructor
then checks normalization, that the 32 rows are computed, and that no signal is dead.

**Dependence on the choice.** [measured]
- Values with more than one admissible pair: 0 in 290 circuits, 1 in 12 (sampled/kste), 2 in the repo 97@3.
  No even value anywhere had both an even-even and an odd-odd admissible pair, so x and y never depend on the
  choice within the admissible family.
- Variants evaluated per circuit: 8 random tie-breaks of the y-max policy, 8 random pairs, 1 x-max,
  1 lexicographic, and 3 runs of a *random topological sampler* (random build order, random pair among
  already-built signals; every acyclic reconstruction of the value set arises from some run of it). Of
  6,363 variant reconstructions, 171 (all from the 13 ambiguous circuits) differ in profile from the base.
  Differences: |dx| <= 1 (3 circuits), |dy| <= 1, |dq| <= 1, |dz| <= 1 (one case 2), |dF| <= 1, |dh(T(C))| <= 1,
  |d margin| <= 2. The 97@3's two alternatives give identical profiles.
- Repo 88@5, 89@4, 97@3: profile of the true gate list == profile of the reconstruction (all three).

So for this corpus "the profile of a value list" is well defined up to +-1 in 4% of circuits; all tables below
use the base (y-maximizing) reconstruction.

**Analysis (`profile_real.py: orbit`).** For C = reconstruction and C_1 = T(C), ..., C_5 (package
`canonical_transpose`, orientation alternating M, Mt, M, ...), record the package's `analyse()` output
(x, y, h, q, z, s, F, F_H, F_B, e1, x', E_B, L_H, helper types) and `check_rows()` slacks, plus the counts of
weight-2 even values, represented weight-2 labels and B-B edges. The two-phase quantities are reported twice:
*raw* (phases C, T(C): the circuit as found and its canonical transpose) and *tail* (phases T(C), T(T(C)): both
canonical, the periodic regime, even phase = the one with larger y, which is what the proof's tail profile is).

Scripts: `profile_real.py` (-> `profiles.json`), `summarize.py` (-> `tables.md`, the full distribution and
row tables), `tail.py` (-> `tail.json`, `tail.log`), `mobile.py` (-> `mobile.json`), `candidates.py`
(-> `candidates.log`).

---

## 2. Distributions (task 1)

### 2.1 Scalar profile of the 200 sampled 88s [measured]

Raw phases (C as found, orientation M; T(C), orientation Mt), min / median / max:

| quantity | C (M) | T(C) (Mt) |
|---|---|---|
| x | 24 / 24 / 26 | 24 / 25 / 27 |
| y | 8 / 12 / 16 | 13 / 16 / 19 |
| h | 16 / 20 / 23 | 13 / 15 / 17 |
| F | 13 / 16 / 19 | 10 / 16 / 18 |
| q | 8 / 12 / 15 | 10 / 13 / 15 |
| z | 0 / 4 / 9 | 0 / 2 / 5 |
| s = q + z | 14 / 16 / 18 | 12 / 15 / 16 |

Tail phases (even = max-y phase; Mt in 143 circuits, M in 57), min / median / max:

| quantity | even phase | odd phase |
|---|---|---|
| x (a, b) | 24 / 24 / 26 | 24 / 25 / 27 |
| y (Y, V) | 14 / 17 / 19 | 10 / 15 / 17 |
| h (h_e, h_o) | 13 / 15 / 17 | 14 / 16 / 20 |
| F | 10 / 15 / 17 | 14 / 17 / 19 |
| q | 10 / 14 / 16 | 10 / 13 / 16 |
| z | 0 / 2 / 5 | 0 / 2 / 7 |
| s | 12 / 15 / 17 | 12 / 16 / 18 |
| fan-out cap S = 3h + 2y' + y - 32 | 51 / 61 / 64 | 60 / 65 / 68 |

Two-phase (tail): budget a + b + 2G - 192 = 32 / 33 / 35; s_e + s_o = 28 / 31 / 33;
**margin s_e + s_o - budget = -7 / -2 / 0** (histogram -7:1, -6:6, -5:16, -4:29, -3:33, -2:41, -1:62, 0:12);
E_B (both phases) = 0 / 2 / 7 with margin = -E_B in all 200; L_H = 0 in all 200; actual two-step potential
drift e(C_3) - e(C_1) = 0 in all 200 (periodicity). Raw two-step drift e(C_2) - e(C_0) = 0 / 1 / 3.

Histograms of the tail pairs: (a, b): (24,24) 50, (24,25) 64, (24,26) 20, (25,24) 29, (25,25) 27, others 10.
(Y, V) ranges over 18 pairs, mode (17,16) 46. (h_e, h_o): mode (15,16) 44, (16,17) 34, (15,15) 28.
y along the orbit, e.g. (8, 15, 10, 15, 10, 15) or (12, 17, 16, 17, 16, 17): y(T(T(C))) >= y(C) in all 200
(Lemma 7.3), and y is constant on each parity class from step 1. [measured]

The 100 kste 88s are more concentrated: tail (a,b) = (24,25) in 76, (Y,V) = (17,15) in 68, (h_e,h_o) = (15,16)
in 76, (s_e,s_o) = (15,15) in 72, margin -3 in 71 (E_B = 3). They look like one family with small variations;
our sampled 88s are more spread (all 200 lie in the same box, however). [measured]

### 2.2 Helper types [measured]

Summed over the 200 sampled 88s (type (r,u,v): r represented H-B edges, u missing H-B edges, v H-H edges):

- Raw C (M): dominated by (2,1,0) 1288, (1,2,0) 746, (1,1,1) 562, (2,0,1) 409, (1,1,0) 244, (1,0,1) 236;
  r = 3 is rare (8 helpers of 4,021); 788 helpers have fan-out 1 (odd-graph degree 2) - these disappear in
  the canonical transpose (Lemma 7.4). Per circuit: n_{r=0} = 0..5, n_{r=1} = 6..13, n_{r=2} = 6..10, n_{r=3} = 0..1.
- Tail T(C) (Mt): (2,1,0) 1840, (2,0,1) 439, (1,2,0) 303, (1,1,1) 270, (3,0,0) 62; per circuit
  n_{r=0} = 0..3, n_{r=1} = 0..6, n_{r=2} = 9..14, n_{r=3} = 0..2; helper fan-out is 2 (3,036 of 3,061) or 3 (25).

So a real canonical phase is almost entirely made of degree-3 helpers of types (2,1,0), (2,0,1), (1,2,0),
(1,1,1): two represented edges and one missing or H-H edge. The survivors' local systems, by contrast, are
driven by the high-u and r = 0 / r = 3 columns (deficits, overflows, packing); those columns are nearly
empty on real circuits.

### 2.3 Repo circuits [measured]

| circuit | tail (a,b) | (Y,V) | (h_e,h_o) | (q,z) even / odd | budget | s_e+s_o | margin | E_B |
|---|---|---|---|---|---|---|---|---|
| 88@5 | (24,24) | (17,16) | (15,16) | (14,1) / (14,2) | 32 | 31 | -1 | 1 |
| 89@4 | (26,25) | (15,14) | (16,18) | (14,1) / (16,2) | 37 | 33 | -4 | 4 |
| 97@3 | (26,35) | (30,17) | (9,13) | (16,0) / (11,0) | 63 | 27 | -36 | 36 |

The 97@3 shows what a non-minimum circuit looks like in these coordinates: a huge boundary excess fan-out
(E_B = 36), b = 35, Y = 30; its margin is -36. The 88s all have E_B <= 7.

---

## 3. The rows (L1)-(L23) on real circuits (task 1 and 2)

Full tables per phase and corpus are in `tables.md`. Minimum slack over the 1,515 canonical real phases (steps
1-5 of all 303 circuits), by row [measured]:

| row | checker name | min slack, canonical M phases | min slack, canonical Mt phases | typical (median) |
|---|---|---|---|---|
| L4 | reverse EE budget | 13 | 10 | 16 |
| L5 | missing pairs | 43 | 42 | 70-80 |
| L6 | full missing incidence | 10 | 10 | 13 |
| L7 | label rank capacity | 52 | 51 | 65-73 |
| L8 | full helper budget | 58 | 50 | 60-65 |
| L9 | weighted label capacity | 24 | 21 | 30-35 |
| L10 | even signal fan-out | 55 | 53 | 68 |
| L11 | full helper incidence | 14 | 11 | 15-16 |
| L12 | boundary R6 rank | 10 | 13 | 11 (M), 16 (Mt) |
| L13 | quotient rank capacity | 75 | 78 | 92-95 |
| L14 | quotient full capacity | 77 | 78 | 94-95 |
| L15 | quotient excess capacity | 36 | 34 | 44-45 |
| L16 | full excess overflow | 24 | 21 | 29-35 |
| L17 | quotient joint deficit | 83 | 60 | 73 (Mt), 101 (M) |
| L18 | quotient full strengthened (Mt) | - | 91 | 110 |
| L19 | dark repeated pairs (Mt) | - | 12 | 16 |
| L20 | dark quotient rank (Mt) | - | 34 | 46 |
| L21, L22 | (Mt, q = 0 only) | never active (q >= 10) | | |
| L23 | packing (q = 6, 7 only) | never active on sampled 88s; q = 7 occurs in 1 kste raw phase, slack 14 | | |
| Lemma 4.3 | s <= 3h + 2F + y - 32 | 42 | 36 | 48 |
| (4.4) | 32 <= 2h + y + z + C(q,2) | 65 | 59 | 95-109 |
| Lemma 10.3 | q + z >= 1 | 13 | 10 | 14-15 |
| Lemma 7.4 | helper degree >= 3 (canonical) | 0 (as "deg >= 2" slack 1) | 0 | tight in every canonical phase |

(Exact per-phase minima are in `tables.md`; the M-phase column above is the minimum over the sampled, kste and
repo tables for steps 2 and 4, the Mt column for steps 1, 3, 5.) Raw phases C (as found) are similar (L4 min 13,
L6 min 8, L12 min 10, "deg >= 2" slack 0 in 199 of 200 because of fan-out-1 helpers, which Lemma 7.4 excludes
only after a canonical transpose).

**Reading.** [derived]
- *Nothing is tight.* Every capacity row has slack >= 10 on every real phase; the rows whose right-hand side
  grows with q (L5, L7, L13, L14, L17, L18, (4.4)) have slack 40-140 because real circuits have q = 10..16
  missing labels while the rows are built to bite at q <= 7. The rows that are tight at the G = 75 survivors
  (LP-feasible keys have q = 0..10, mostly 1..6, s <= 10) and the real circuits (q >= 10, s >= 12) live in
  different parts of (q, z) space.
- *Rows that cannot be strengthened* in the sense of "a real circuit sits on them": none of (L4)-(L23). The
  only equalities real circuits saturate are (L1)-(L3) (identities, by construction) and Lemma 7.4.
- *Rows with large slack as candidates for strengthening:* a universal row must hold for every circuit, so the
  real 88s only give an upper bound on how far a row could be tightened. For the q-scaling rows the real
  circuits are irrelevant as a constraint (the survivors are at small q); for the h- and F-scaling rows
  (L4, L8, L10, Lemma 4.3) the real slack is 10-16 (L4), 50-80 (L8), 36-53 (Lemma 4.3). L4
  (`sum f_min n <= F`) is the one row where real circuits come within 10: F = 15..17 but most real helpers
  have degree exactly 3, f_min = 0, so the left side is 0-3. A sharper form of L4 would need a lower bound
  on sum f_min, i.e. on helpers of degree >= 5, which real circuits almost never have (25 of 3,061 have
  degree 4; none higher in Mt phases). Not a lever.
- *Violations:* none. Any violation would have signalled a reconstruction bug; the three true gate lists
  agreeing with their reconstructions is the positive control.

---

## 4. Comparison with the G = 75 survivors (task 2) [measured unless marked]

Source: `lb76/g75_survivors.json` (1,508 oriented claims `(a,b,Y,V,he,ho, k,l, Se,So, budget)`),
`lb76/g75_keys.json` (1,134 LP-feasible local keys `(h,y,F,q,z,ori)`).

| coordinate | real 88 tail (N = 200) min / median / max | 75 survivors (N = 1,508) | survivors outside the real range |
|---|---|---|---|
| a | 24 / 24 / 26 | 24 / 26 / 30 | 456 |
| b | 24 / 25 / 27 | 24 / 27 / 31 | 548 |
| Y | 14 / 17 / 19 | 0 / 6 / 11 | 1,508 |
| V | 10 / 15 / 17 | 0 / 2 / 8 | 1,508 |
| h_e | 13 / 15 / 17 | 8 / 12 / 17 | 1,016 |
| h_o | 14 / 16 / 20 | 9 / 13 / 19 | 757 |
| Y + V | 25 / 31 / 36 | 0 / 8 / 17 | all |
| h_e + h_o | 28 / 31 / 36 | 18 / 25 / 35 | most |
| budget | 32 / 33 / 35 | 6 / 10 / 17 | (G differs) |
| forced s: k + l (survivors) vs real s_e + s_o | 28 / 31 / 33 | 4 / 9 / 17 | |
| even-phase orientation | Mt 143, M 57 | M 846, Mt 662 | |

Local keys: LP-feasible keys at 75 have q = 0..10 (M: mode 6, 115 keys; Mt: mode 1, 315 keys), z = 0..7
(mode 0-1), y = 0..14, F = 0..11, h = 5..19, s = 1..10. Real canonical phases: q = 10..16, z = 0..7 (mode 2),
y = 10..19, F = 10..19, h = 13..20, s = 12..18.

**Where they differ, in order of size.** [derived]
1. **y and F** (even+even gates). Real 88s spend 14-19 gates per phase on even+even XORs; at G = 75 with
   a >= 24 the identity G = 32 + x + y + h forces Y + h_e <= 19, so a survivor has Y <= 11 and is pushed to
   Y + V <= 17. The real circuits are nowhere near; their large y is what makes their labels plentiful
   (36-41 even signals) and their q large.
2. **q (missing labels) and s.** Real: q >= 10 per phase, s_e + s_o = 28..33. Survivors: forced s only
   4..17 for the two phases, and the LP-feasible keys cluster at q = 1 (Mt) and q = 3..6 (M). The real
   circuits have q large because they have many even signals and only 23-33 of them are represented
   (B-B edges), 55-80% of those being the input-pair (weight-2) values.
3. **Orientation of the even phase.** The survivors split 846 M / 662 Mt; among real 88s the max-y canonical
   phase is Mt in 72% (94% of kste). Not a contradiction (survivors are hypothetical), but the real circuits
   suggest the Mt-even branch is the natural one for low-gate circuits of this map. [guess]
4. **x (a, b).** Both populations start at the proved minimum 24; the survivors extend to 30-31, real 88s stop
   at 26-27. 456-548 survivors have a or b above anything observed.
5. **h.** Overlapping: survivors 8..17 / 9..19, real 13..17 / 14..20. The odd-helper theorems (h <= 2) are
   irrelevant to both, as lb76 already concluded.
6. **Helper types.** Survivor LPs lean on r = 0 and r = 3 columns and on high u (deficits, overflows, packing);
   real phases have n_{r=0} = 0..3, n_{r=3} = 0..2, u <= 3 (u = 3 only in 36 + 53 helpers of 7,000), and
   are 85-90% (2,1,0)/(2,0,1)/(1,2,0)/(1,1,1).

**The drift inequality on real circuits.** [derived; numerically verified on 303 circuits] From the package's
exact identity (E), `e(T(C)) - e(C) = s + 96 - G + x - 2x' + E_B + L_H`, summed over two consecutive steps of a
period-2 tail (x alternates a, b; e returns to itself):
`0 = s_e + s_o + 192 - 2G - a - b + (E_B,e + E_B,o) + (L_H,e + L_H,o)`, hence
`s_e + s_o = budget - E_B,total` (L_H = 0 by Lemma 7.4). The proof's exclusion demands s_e + s_o >= budget + 1
on every tail; real circuits sit at budget - E_B with E_B = 0..7 (12 of 200 at exactly budget). In words: **a
real 88 is at most seven boundary fan-out units from being excluded by the drift argument, and some are at
zero distance.** The information the proof lacks at G = 75 (it forces only k + l = 4..17 of a budget 6..17) is
precisely the gap between the rows' lower bounds on s and the actual s; at G = 88 that gap is 28-33 versus
rows forcing roughly 1-2 (see the slacks of (4.4), 59-140).

---

## 5. Hypothesis tests (task 3)

### (a) "Any circuit with <= 89 gates has >= 3 odd non-output helpers" [measured]

With the package's definition (odd-weight gate masks that are not output rows):
- sampled 88s as found: h = 16..23 (histogram 16:1, 17:4, 18:18, 19:41, 20:50, 21:62, 22:20, 23:4);
  kste 88s: 17..23; repo 88@5: 16; 89@4: 19; 97@3: 19.
- canonical transposes (steps 1-5): h = 13..20 (mode 15-16).
- The task brief's "16-24" is consistent (our sample tops at 23). The theorem's bound of 3 is met with a
  margin of at least 10 in every phase; it cannot be the lever for 87 or 88 by itself, as lb76 said.

### (b) Weight-2 labels, B-B edges and plateau mobility [measured]

- Weight-2 even values (input pairs) per circuit: sampled 88s as found 13 / 17 / 20 (min/median/max); kste
  15 / 16 / 22; in T(C) 16 / 19 / 22. **All of them are represented labels** in every circuit and phase: a
  weight-2 value can only be built from its two inputs (the pair is unique), and that gate is a B-B edge. [derived]
- B-B edges = represented labels = (even signals) - q: 21 / 24 / 28 in C, 25 / 28 / 33 in T(C); so weight-2
  labels are 55-80% of all represented labels, and the remaining represented labels (4-13) are even values of
  weight >= 4 joining an input to an output or two outputs.
- Mobility under the engine's neutral remove1 fan (`pes_lib.make_space('mc', None)`, `fan`; the engine's own
  count is 88 and no improving move exists for any of the 200): neutral moves per circuit 8 / 16 / 30;
  weight-2 helpers that are removed by some neutral move: **0 / 0 / 2** per circuit (fraction 0-13%);
  mobile helpers in total 4 / 8 / 11, nearly all of weight 3-7. Over 40 circuits the neutral moves are shaped
  (one removed, one added) with weight pairs (6->5) 47, (3->3) 43, (5->5) 40, (3->4) 33, (4->4) 33, ...,
  (2->3) 22, (3->2) 17, (2->2) rare (median 0 per circuit, max 2).
- Interpretation [derived]: the "re-pairing of unshared 3-input trees" picture (swap (x_i+x_j)+x_k for
  (x_i+x_k)+x_j) is a (2->2) move; it is available only when the weight-2 pair is unshared, and in a trimmed
  88 almost every weight-2 value is shared (fan-out 2). So in the proof's coordinates the plateau structure is
  *not* visible as mobility of represented weight-2 labels: the weight-2 layer is rigid (13-20 fixed B-B
  edges), and the neutral moves act one level up, exchanging one helper of weight 3-7 (typically a
  (2,1,0)/(1,2,0) helper of the odd graph, or a missing label) for another of similar weight. A plateau is
  therefore a set of circuits with identical B-B skeleton and varying middle layer, and every member has the
  same (x, y) up to the +-1 effects in section 1 [guess for "every member": checked only on the 200 sampled
  states, not along plateaus].

---

## 6. Candidate universal inequalities suggested by the real circuits

All items are **[conjecture, consistent with N real circuits]**; none is proved, and the method of section 3
cannot prove any of them. `candidates.py` checked each on all 1,515 canonical phases of the 303 real circuits
*and* on the 52 phases of the package's 13 control circuits (88-102 gates), since a universal row must hold
for non-minimum circuits too; it also counts how many of the 1,134 LP-feasible G = 75 keys each would cut.

1. **Drift saturation.** On a period-2 tail, `s_e + s_o = a + b + 2G - 192 - E_B,total` [derived, exact].
   Consequence for any attempt at 87/88: a circuit with G = 87 and the real circuits' E_B would need
   s_e + s_o = a + b - 18 - E_B, i.e. 2 fewer units of s than the 88s at the same (a, b, E_B). This is an
   identity, not a cut, but it says exactly what a "one gate fewer" circuit must trade: two fewer missing labels
   or H-H edges per two-phase cycle, or two more boundary excess fan-outs. [consistent with 303 circuits]
2. **q >= 7 in every canonical phase.** Real: q >= 10 (1,515 phases); controls: q >= 7 (52 phases). Would cut
   1,017 of 1,134 LP-feasible keys at G = 75 (478 M, 539 Mt) and so most survivors. I have no argument; the
   package proves only q + z >= 1 (Lemma 10.3) and q = 0 => z >= 8 for Mt. A proof would have to bound the
   number of represented labels (B-B edges) from above by (even signals) - 7, i.e. show that at least 7 even
   signals never join two boundary vertices. [conjecture, consistent with 316 circuits; likely false in
   general - guess]
3. **E_B,total <= 7 on the tail of an 88.** Real 88s: 0..7; the 89@4 has 4, the 97@3 has 36. Not universal
   (the 97@3 breaks any small constant); as a *minimum-circuit* property it would mean a minimum circuit's
   canonical transposes have boundary fan-outs almost all <= 2. [conjecture about minimum circuits only,
   consistent with 300 88s]
4. **x <= 26 in every canonical phase of an 88.** Real 88s: a, b in 24..27 (one circuit with b = 27).
   Survivors run to 30-31. Not universal (97@3 has b = 35). [conjecture about minimum circuits only]
5. **Helper degree distribution.** In canonical phases of real 88s, 99% of helpers have odd-graph degree 3
   (fan-out 2) and none has degree >= 5; hence sum f_min n = 0..3 against L4's right-hand side F = 10..19.
   A row of the form `sum_{deg>=5} n <= c` would be consistent with the real circuits for c >= 0, but the
   survivors' LPs do not use high-degree columns heavily, so it would cut little. [measured; not useful]

Everything else I tried (q - y, s - h, q - h, y - F, h - F lower bounds; B-B edge upper bounds; n_{r=0},
n_{r=3} bounds) is broken by at least one control circuit at the level that would matter for the survivors
(see `candidates.log`), so the real circuits do not suggest a new *universal* row with bite at G = 75.

---

## 7. Statements and their labels

| statement | label |
|---|---|
| 303 circuits, 1,818 phases pass every `analyse`/`canonical_transpose` assertion; no row violated | [measured] |
| reconstruction unique in 290/303; profile changes <= 1 per coordinate, <= 2 in margin, in 13 | [measured] |
| repo true gate lists reproduce the reconstructed profiles | [measured] |
| orbit period 2 from step 1 in all 303 | [measured] |
| s_e + s_o = budget - E_B on the tail; L_H = 0 | [derived from identity (E) [proved in package] + period 2; verified 303/303] |
| distributions of sections 2, 4, 5 | [measured] |
| row slacks; nothing tight except Lemma 7.4 | [measured] |
| survivors' coordinates (1,508 claims, 1,134 keys) | [measured, lb76 files] |
| weight-2 values are all represented | [derived] |
| mobility figures (0/0/2 weight-2 mobile helpers; move shapes) | [measured, engine's remove1 via pes_lib] |
| interpretation of plateau structure in the proof's coordinates | [derived] / [guess] where marked |
| candidate inequalities 2-5 | [conjecture]; none proved; `q >= 7` possibly false in general [guess] |
| x >= 24, G = 32 + x + y + h, Lemma 7.3 y(TT) >= y, Lemma 7.4 degree >= 3 | [proved in package], observed to hold |

## 8. Files in `~/xs-campaigns/2026-11-07-sprint/bridge/`

`REPORT.md` (this file); `profile_real.py`, `profiles.json` (303 records: values, reconstruction info, six
orbit phases with types and row slacks, two-phase summaries, 21 variant reconstructions each, true-gate-list
profiles for the repo circuits); `summarize.py`, `tables.md` (all distribution and row tables, per corpus
and phase); `tail.py`, `tail.json`, `tail.log` (tail profiles and identity check); `mobile.py`, `mobile.json`
(neutral-move mobility, 200 circuits); `candidates.py`, `candidates.log` (candidate inequalities on real and
control phases, cuts of G = 75 keys).