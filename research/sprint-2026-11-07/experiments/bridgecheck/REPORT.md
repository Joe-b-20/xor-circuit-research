# Adversarial check of F17 / bridge/REPORT.md

Checker: bridgecheck agent, 2026-11-07. Directory `~/xs-campaigns/2026-11-07-sprint/bridgecheck/`
(`recheck.py` -> `recheck.json`, `recheck.log`; `analyze.py` -> `analyze.log`). Everything else read-only.
One python process at a time under `nice -n 10`.

Independence of the check: the reconstruction value set -> gate list is my own code (full enumeration of
all acyclic parent assignments, no min-depth levelling), and x, y, h, q, z, s, E_B and the helper types are
recomputed from scratch (`own_profile`) and asserted equal to the package's `Circuit.analyse` on every phase
before anything else is used. The orbit itself (`canonical_transpose`) and the row slacks (`check_rows`) are the
package's, as in the bridge; I add a *circuit-level* period test (equation sets, not only profiles) and random
canonical tie-breaks, which the bridge did not do.

Corpus: 20 hunt-A 88s (first 20 `sample:A` tags of `profiles.json`, value sets re-read from
`hunt/samples.jsonl`), 10 hunt-D (`hunt/samplesD/samples.jsonl`), 7 kste (first 7 `kste:` tags, value sets
re-read from `kste/data/kste_valuesets.json`), repo 88@5, 89@4, 97@3 (true gate lists from the NCFF files, and
their value sets reconstructed as well).

---

## 1. The algebra behind claim (d)

### 1.1 What the package proves (read, not re-proved)

Notation (PROOF.md sections 3-8): d_v = fan-out of signal v (uses + 1 if output), k_v = number of odd
contributions to the adjoint a(v), f_v = max(0, d_v - ceil(k_v/2) - 1), F = sum_v f_v, F_H / F_B the sums over
helpers / boundary, x' = sum_v floor(k_v/2) = x(T(C)) for any raw transpose (Lemma 3.2, 6.1), e(C) = e_1 =
number of even+even gates of C with odd adjoint, s = q + z, wdeg_v = weighted degree of Lemma 6.2.

- Exact form of (B) (Remark after Lemma 6.2):
  `2x' + h + y + F_H = 64 + q + z + e_1 + L_H + sum_{v in B} (wdeg_v - 1)/2`, where
  **L_H = #{helpers with d_v = k_v = 1}**, and per boundary vertex `(wdeg_v - 1)/2 + f_v = max(0, d_v - 2)`.
- Lemma 8.1: for a canonical transpose, `e(T(C)) = sum_{v odd} f_v = F_H + F_B` (the even+even gates of T(C)
  are exactly the f_v gates of the accumulation trees, and such a gate has odd adjoint iff its origin is odd).
- Lemma 1.2: `h + y = G - 32 - x`.
- Lemma 7.2: `x(T(D)) = x(C)` for any raw transposes, so x alternates between a and b along any orbit.

### 1.2 Derivation of the identity

Define the **boundary excess fan-out** `E_B(C) = sum_{v in B} max(0, d_v - 2)` over the 64 boundary signals of C
(32 inputs and the 32 outputs; d_v counts the terminal use of an output, so an output with one gate use has
d_v = 2 and contributes 0). Summing the per-vertex identity over B:
`sum_B (wdeg_v - 1)/2 = E_B - F_B`. Substituting into the exact (B):

    2x' + h + y + F_H + F_B = 64 + s + e_1 + L_H + E_B.

With Lemma 8.1, `F_H + F_B = e(T(C))`, and `h + y = G - 32 - x`:

    e(T(C)) - e(C) = s + 96 - G + x - 2x' + E_B + L_H.                        (E)

This is the identity `stress.py` asserts (`identity (E)`); Lemma 8.2 is (E) with the two non-negative terms
E_B + L_H dropped (the Lemma's proof drops them by using F_H <= e(T(C)) and (B) as an inequality). (E) holds for
**every normalized circuit C of either orientation and every canonical transpose T(C)**; minimality is not
needed (it is used in the paper only to know that T(C) is normalized; the `Circuit` constructor checks that
directly). C itself need not be a canonical transpose.

Now take an orbit C_0, C_1 = T(C_0), C_2 = T(C_1), ... with canonical transposes. Write x_j, s_j, E_j, L_j,
e_j for the quantities of C_j. (E) at j and at j+1:

    e_{j+1} - e_j     = s_j     + 96 - G + x_j     - 2x_{j+1} + E_j     + L_j
    e_{j+2} - e_{j+1} = s_{j+1} + 96 - G + x_{j+1} - 2x_{j+2} + E_{j+1} + L_{j+1}

Add, and use x_{j+2} = x_j (Lemma 7.2), so x_j - 2x_{j+1} + x_{j+1} - 2x_{j+2} = -(x_j + x_{j+1}) = -(a + b):

    e_{j+2} - e_j = s_j + s_{j+1} - (a + b + 2G - 192) + (E_j + E_{j+1}) + (L_j + L_{j+1}).      (E2)

Hence, with budget := a + b + 2G - 192,

    s_j + s_{j+1} = budget - (E_j + E_{j+1}) - (L_j + L_{j+1}) + (e_{j+2} - e_j).

**The bridge's identity `s_e + s_o = budget - E_B` is (E2) under exactly two extra hypotheses:**

1. `e_{j+2} = e_j` (zero two-step drift of the potential). Period 2 of the orbit *as circuits* is sufficient
   but far from necessary: equality of the single integer e(C_{j+2}) = e(C_j) is all that is used.
   Without any periodicity hypothesis the identity still holds *on average over any stretch of the tail*,
   because e is bounded (0 <= e <= y <= G): summing (E2) over j = j_0, j_0+2, ..., j_0+2m-2 gives
   `(1/m) sum (s_j + s_{j+1}) = budget - (1/m) sum (E + L) + (e_{j_0+2m} - e_{j_0})/m`, and the last term is
   O(G/m) -> 0. So **for every real circuit of every gate count, the two-phase margin averaged over the tail is
   -(mean E_B + mean L_H) <= 0.** The inequality `s_e + s_o <= budget` is not a property of 88s; it is forced
   for every circuit by (E) and the boundedness of e.
2. Both phases canonical transposes: needed for Lemma 8.1 at each step (so for j >= 0 with C_0 arbitrary; the
   raw phase C_0 is allowed as C_j, only T must be canonical). The bridge's additional simplification
   `L_H = 0` needs the phase to be a canonical transpose (Lemma 7.4: helpers of a canonical transpose have
   fan-out >= 2, so no helper has d_v = 1); on the raw phase C_0 L_H can be positive, and the exact statement
   there is `margin = -(E_B + L_H) + drift`.

So, precisely: **E_B,total = sum over the two phases of sum_{v in B} max(0, d_v - 2)**, the number of boundary
fan-out units beyond two, and on a two-step stretch with e_{j+2} = e_j and both phases canonical,
`s_e + s_o = budget - E_B,total` exactly. No hypothesis on which phase is "even" (max-y) is needed; the identity
is symmetric in the two phases.

### 1.3 What the identity says about the drift argument

Lemma 8.3 / Proposition 11.1 exclude G by proving, from the rows, lower bounds k, l with
`k + l >= budget + 1`, so that every two-step drift is >= 1 and e is unbounded. By (E2), the true two-step
drift of any real circuit is `s_j + s_{j+1} - budget + E + L`, and e bounded forces its tail average to be 0.
Therefore for *any* circuit of *any* G the true `s_e + s_o` (tail average) equals `budget - (E_B + L_H)`.
The drift step itself has **no slack at all at any G**: it is an identity. The slack of the whole argument is
entirely in the rows, i.e. in how far the provable lower bound k + l on s_e + s_o sits below the true value
budget - E_B.

Consequently:
- "The drift mechanism saturates exactly at real 88 circuits" is not the right conclusion; the mechanism is
  saturated (margin <= 0, with equality iff E_B = L_H = 0) at every circuit, the 97@3 included (margin -36).
  What is special to the 88s is only that E_B is small (0-7), i.e. the one-step Lemma 8.2 loses little on them.
- For a hypothetical 87 the identity gives `s_e + s_o = a + b - 18 - E_B` on its tail. This is a constraint
  on what such a circuit would look like, not an obstruction: with a, b >= 24 it needs
  `s_e + s_o <= a + b - 18`, two units less of q + z per two phases than an 88 with the same (a, b, E_B).
  E_B <= 7 is a property *observed* on 88s; nothing proved transfers it to an 87. If one *assumes* an 87 has
  E_B <= 7 like the 88s, then `a + b - 25 <= s_e + s_o <= a + b - 18`; the rows at G = 87 would have to force
  k + l >= a + b - 17 to exclude it, versus the ~1-2 they force now (slack of (4.4) is 59-140 on real phases).
  The number 7 enters nowhere in an exclusion; the lever is only k + l versus budget, and E_B just measures how
  far below the budget the true s sits.
- The candidate inequality "E_B,total <= 7 on the tail of an 88" is not usable as a row anyway: E_B is not one
  of the local system's unknowns (h, y, F, q, z, n_{r,u,v}); it is a boundary fan-out statistic the rows never
  see. It could only enter through (E) as an *upper* bound on s (s = budget - E_B - ...), which goes the wrong
  way for an exclusion that needs lower bounds on s.

---

## 2. Verdicts per claim

| claim | verdict | where |
|---|---|---|
| (a) value set determines the gate list almost uniquely; 290/303 with exactly one admissible pair per value | CONFIRMED as a statement about 88s, with a caveat: the bridge's "admissible" (min-depth levelled) family under-counts the true ambiguity. Full acyclic family: 35 of 40 unique, 3 x 4, 89@4: 15, 97@3: 16 reconstructions. On 88s alternatives move x, y, q, z, F by <= 1 and the margin by <= 1 (confirmed); on the 89@4 they move x by 2, y by 2, F by 3 and the raw two-phase margin by 4 (0 to -4), so "<= 1 / <= 2" is DIFFERENT for the non-88 controls. | section 3 |
| (b) all circuits x 6 phases pass every package assertion; no row violated | CONFIRMED (40 x 6 phases + 120 random-canonical orbits x 5 phases + 44 alternative reconstructions x 3 phases; 0 assertion failures, 0 negative slacks). My from-scratch x, y, h, q, z, s, E_B and helper types equal `analyse()` on every phase. | section 3 |
| (c) orbit period 2 from the first transpose on, all 303 | DIFFERENT. As *circuits* (gate-equation sets) C_2 = C_4 in 40/40 but C_1 = C_3 only in 17/40 with the package's deterministic canonical choice, and with random canonical tie-breaks the orbit is generally not periodic at all (both C_1 = C_3 and C_2 = C_4 in 7 of 120 orbits). As *profiles*: (x, y, h, s, F, E_B, e_1) are 2-periodic from step 1 in 303/303 of the bridge's own data, but (q, z, types) only from step 2 in 14/303 (q and z trade one unit with s fixed). What the identity needs, e(C_3) = e(C_1), holds in 303/303 and in all 120 random orbits. | section 4 |
| (d) s_e + s_o = a + b + 2G - 192 - E_B, E_B in 0..7, 12/200 at 0 | CONFIRMED numerically (40/40 mine, 303/303 bridge data, every phase pair (j, j+1), j = 1..4; 120/120 random-canonical orbits), and the algebra is right (section 1), with the hypotheses stated there. The *reading* "real circuits sit below the drift budget / the mechanism saturates at 88s" is over-read: margin <= 0 is forced for every circuit by (E) and bounded e. See section 1.3 and 6. | sections 1, 4 |
| (e) tail profiles a 24-26, b 24-27, Y 14-19, V 10-17, q 10-16, z 0-7, s 12-18 | CONFIRMED on the 38 88s (a 24-25, b 24-26, Y 14-18, V 13-17, q 10-16, z 0-4, s 13-17: all inside the bridge's ranges; identical numbers to profiles.json for the 36 unambiguous circuits). | section 5 |
| (f) min row slack 10 over canonical phases (L4, L6, L12, Lemma 10.3), only Lemma 7.4 tight | CONFIRMED: min 10 over my 190 canonical phases, attained by L12 (boundary R6 rank, M, kste:0), L6 (10, Mt) and Lemma 10.3 (q + z >= 1, 10, Mt); L4 min 12 (M) / 13 (Mt) here (the bridge's 10 for L4 is on a circuit outside my 40). Helper odd-degree exactly 3 is attained in 190/190 canonical phases (slack 0). Raw phase min slack 8 (L6, kste:0), as the bridge says. | section 5 |
| (g) 16-23 odd non-output helpers; weight-2 values rigid (median 0, max 2 removed) | CONFIRMED: h = 16..23 as found (canonical 14..18); engine neutral moves 8-29 per circuit, weight-2 helpers removed by some neutral move 0 (23 circuits), 1 (5), 2 (2); no improving move. The bridge's side statement "every weight-2 value is a represented label in every circuit and phase [derived]" is FALSE: it fails in 14 of my 240 phases (5 circuits, incl. the 89@4 and 97@3 raw phases) and in 21 of the bridge's own 303 circuits (profiles.json fields w2 vs w2_rep). The "derivation" (a weight-2 value can only be built from its two inputs) is wrong: a canonical transpose can build x_i + x_j as an even+even or odd+odd accumulation gate. Harmless for the conclusions (the counts 13-20 stand), but the label should be [measured, 93 % of circuits]. | section 5 |

---

## 3. Reconstruction and the package run (claims (a), (b))

Method (`recheck.py: reconstructions`). Signals = 32 inputs + the value list. For each value every pair
(a, b), a xor b = v, of signals is a candidate (no levelling). A sound pruning removes a pair when a or b
*necessarily* depends on v (least fixpoint of "values p depends on under every remaining choice"); then a
backtracking search with cycle detection enumerates every acyclic assignment (cap 2000, never reached).
Base choice: maximal even+even count, then lexicographic. A Kahn check re-verifies acyclicity of every result.

| circuit set | values with > 1 raw pair | values still ambiguous after pruning | acyclic reconstructions | bridge n_multi (levelled) = mine |
|---|---|---|---|---|
| 20 hunt A | 61-65 per circuit | 0 (19), 11 (1) | 1 (19), 4 (1) | yes (0 / 1) |
| 10 hunt D | 63-66 | 0 (9), 11 (1) | 1 (9), 4 (1) | yes |
| 7 kste | 63-64 | 0 (6), 4 (1: kste:1) | 1 (6), 4 (1) | yes (kste:1: bridge 0, full family 4) |
| repo 88@5 | 61 | 0 | 1 | yes; true gate list == reconstruction (equation sets) |
| repo 89@4 | 57 | 5 | **15** | bridge 0 (levelled family has 1 member); full family 15 |
| repo 97@3 | 65 | 6 | 16 | bridge 2 |

Profiles over the full families: hunt A/D ambiguous circuits: (y, x) constant, q/z/F move by <= 1, raw
two-phase margin constant (-4; -3). kste:1: (y, x) in {(11, 26) x3, (10, 27) x1}, margin -5/-5/-6 (bridge
base -5, mine -6). **89@4: (y, x) in {(12, 26) x1, (13, 25) x6, (14, 24) x8}, F 11-14, E_B(C) 1-4, raw margin
0 to -4** (the true gate list is the (12, 26) member, margin -4; my base is a (14, 24) member, margin -1).
97@3: (y, x) = (20, 26) in all 16, raw margin -34 to -36 (true: -36). So the bridge's "the alternatives move
x, y, q, z, F by <= 1 and the margin by <= 2" holds for the 88s I checked but not for the 89@4 (its loose
sampler did see (24, 14) for the 89@4 - it is listed among its variants - and the report's "<= 1" is a
mis-summary of its own variant table for that circuit). For F17 this is immaterial: the 88 statistics do not
depend on it; but "a value set determines the gate list almost uniquely" should be qualified "for the 88s".

Package run: all 40 x 6 phases, the 3 x 5 x 40 random-canonical phases and 44 x 3 alternative phases ran
through `Circuit`, `analyse`, `canonical_transpose`, `check_rows` with no AssertionError and no negative row
slack. For the 36 circuits where my base reconstruction coincides with the bridge's, every one of
(ori, x, y, h, q, z, s, F, F_H, F_B, e_1, x', E_B, L_H, types, all row slacks) agrees with `profiles.json` on all
6 steps (0 differences). The 4 differing circuits (A:0202..., kste:1, 89@4, 97@3) differ only because the base
member of the family differs; their tail margins: A:0202 -4 = bridge -4; kste:1 -6 vs bridge -5; 89@4 -1 vs
bridge -4 (true gate list); 97@3 -34 vs -36.

---

## 4. Periodicity and the identity (claims (c), (d))

Deterministic canonical choice (the package's, as the bridge used), 40 circuits, equation-set equality:

| pair | equal as circuits | profile (x,y,h,q,z,F,E_B,types) equal | e_1 equal | s equal |
|---|---|---|---|---|
| C_0, C_2 | 0 / 40 | 0 / 40 | 16 / 40 | - |
| C_1, C_3 | **17 / 40** | 40 / 40 | 40 / 40 | 40 / 40 |
| C_2, C_4 | 40 / 40 | 40 / 40 | 40 / 40 | 40 / 40 |
| C_3, C_5 | 40 / 40 | 40 / 40 | 40 / 40 | 40 / 40 |

Bridge's own data (303): profile 2-periodic from step 1 in 289, from step 2 in all; the 14 exceptions differ
between C_1 and C_3 in (q, z, types) only, with s, E_B, e_1 equal (e.g. q, z = (14, 1) vs (13, 2)).

Random canonical tie-breaks (`canonical_transpose(I, rng)`, 3 seeds x 40 circuits, 5 steps): C_1 = C_3 and
C_2 = C_4 in 7 orbits, exactly one of them in 38, neither in 75. Yet y, s and E_B sequences are identical to the
deterministic orbit's in 120/120, and e(C_3) - e(C_1) = 0 in 120/120, so the tail margin equals -(E_B + L_H) in
120/120. So the right statement is: **the orbit is 2-periodic in profile from the first canonical transpose
(q, z individually from the second), and e(C_{j+2}) = e(C_j) for j >= 1 in every orbit tested; the circuits
themselves are 2-periodic only from C_2 and only for the deterministic association.**

Identity: margin = -(E_B + L_H) with L_H = 0 on canonical phases: 38/38 88s (E_B 1-6 here; the bridge's 0-7
with 12/200 at 0 re-verified on profiles.json, also on phase pairs (2,3), (3,4), (4,5): 303/303 each), 89@4
(-1 / -4 depending on the reconstruction), 97@3 (-34 / -36). On the raw pair (C_0, C_1) the margin is
-(E_B + L_H) + (e_2 - e_0) with L_H(C_0) = 0..8 and drift 0..8, equal to -(E_B + L_H) in only 16/40: the
identity in the bridge's form genuinely needs the canonical regime (section 1.2).

Lemma 8.2's upper bounds on s (used at G = 74 as S_e = min(..., 2b - a + G - 96 + V)) have slack 14-19 on the
real 88s' tails; the fan-out caps S_e, S_o have slack 40-51.

---

## 5. Profiles, helpers, rows (claims (e), (f), (g))

Tail (steps 1, 2; even = max-y phase), 38 88s: a 24/24/25, b 24/25/26, Y 14/17/18, V 13/15/17, h_e 14/15/17,
h_o 15/16/18, q_e 10/13/15, z_e 0/2/4, q_o 12/14/16, z_o 1/2/4, s_e 13/15/16, s_o 14/16/17, budget 32/33/35,
s_e + s_o 29/31/33, margin -6/-2/-1, E_B 1/2/6, even phase Mt in 36 of 38. Canonical phases: x 24-26, y 13-18,
h 14-18, q 10-16, z 0-4, s 13-17, F 13-18, E_B 0-4 (per phase; 11 and 23 on the 97@3). Raw C of the 88s:
h 16-23 (hist 16:1, 18:7, 19:7, 20:7, 21:8, 22:6, 23:2), y 8-16, q 8-15, z 1-7, s 15-17, L_H 0-3.
Helper fan-out in canonical 88 phases: 2 (2,983 helpers) or 3 (4); min odd-degree 3 in 190/190 canonical
phases, 2 in 36/38 raw phases.

Row slacks (min / median over my 190 canonical phases), rows with min < 20: L12 boundary R6 rank M 10 / 11,
Mt 13 / 16; L6 full missing incidence M 12 / 14, Mt 10 / 13; Lemma 10.3 (q + z >= 1) M 14 / 15, Mt 10 / 14;
L4 reverse EE budget M 12 / 17, Mt 13 / 15; L11 full helper incidence M 15 / 16, Mt 11 / 15; L19 dark repeated
pairs Mt 12 / 15. All q-scaling rows 44-171. Same picture and same minimum (10) as the bridge's table.

Mobility (pes_lib `fan`, 30 hunt circuits): neutral moves 8-29, improving 0; weight-2 helpers removed by
some neutral move: 0 in 23, 1 in 5, 2 in 2; total mobile helpers 4-11. Confirms the bridge's figures.

---

## 6. What F17 should say

1. Keep: corpus passes the package (b); profiles (e); slacks (f); h and rigidity (g); the identity (d) as an
   identity. Add to (a): "unique for 35 of 40 re-checked; the ambiguity families are larger than the levelled
   count (89@4: 15 reconstructions spanning x = 24..26), which matters for the controls, not for the 88s."
2. Replace (c) by: "from the first canonical transpose the orbit's profile (x, y, h, s, F, E_B, e) is
   2-periodic in all 303 (q and z individually from the second); as circuits C_2 = C_4 always but C_1 = C_3 in
   under half, and with random canonical tie-breaks the circuits are not periodic although the profile and e
   are. Only e(C_{j+2}) = e(C_j) is used."
3. Replace "real circuits sit 0-7 units BELOW the drift budget ... the potential/drift mechanism therefore
   saturates exactly at real 88 circuits" by: "By the package's exact identity (E), every circuit of every
   gate count has s_e + s_o = budget - (E_B + L_H) + (two-step drift), and bounded e forces the drift to
   average 0 on the tail; so margin <= 0 is automatic for all real circuits (the 97@3 has -36). The drift step
   of the proof has no slack at any G. What is specific to real 88s is that E_B is small (0-7), i.e. the
   one-step inequality (Lemma 8.2) loses only 0-7 units on them. The content the proof lacks is entirely in
   the rows: the provable lower bound k + l on s_e + s_o versus the true value budget - E_B (28-33 at G = 88
   against rows forcing about 1-2)."
4. On a hypothetical 87: E_B <= 7 is an observation about 88s and transfers nothing. The identity only says an
   87's tail would have s_e + s_o = a + b - 18 - E_B(87); to exclude 87 by the tail argument the rows would
   have to force k + l >= a + b - 17 for every admissible profile, which at a = b = 24 means forcing 31
   missing-label-or-H-H units per two phases where real circuits have 28-33. If one *conjectures* E_B <= 7 for
   minimum circuits, an 87 would need s_e + s_o in [a + b - 25, a + b - 18], i.e. 2 units less of q + z per
   two phases than an 88 with the same (a, b, E_B) - a description, not an obstruction, and E_B is not a
   variable of the local systems, so it cannot be turned into a row.
5. Drop the [derived] label on "every weight-2 value is a represented label"; it is false in 7 % of the
   bridge's own circuits (its own w2 / w2_rep fields show it). Nothing downstream depends on it.
6. "the alternatives move x, y, q, z, F by <= 1" should read "for the 88s"; the 89@4's family moves x by 2
   and the margin by 4.

## 7. Files

`recheck.py` (reconstruction + package run + period/identity tests; `recheck.json`, `recheck.log`;
`recheck_run1_partial.log` is the aborted first run with a slower enumerator, same numbers for the 38 it
finished), `analyze.py` -> `analyze.log` (all tables above), `xcheck.py` -> `xcheck.log` (bridge-data
cross-checks, mobility), `xcheck2.py` -> `xcheck2.log` (the 14 non-periodic profiles, identity on other
phase pairs). Total compute about 1 minute of python.
