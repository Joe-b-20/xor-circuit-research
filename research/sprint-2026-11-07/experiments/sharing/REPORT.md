# The eight-group identity G = 108 + delta - S: exact statement, measurements, proofs, sub-maps, verdict

Sprint 2026-11-07, agent "sharing". Folder `~/xs-campaigns/2026-11-07-sprint/sharing/` (nothing written in the
repository). Work window 22:11-00:30 UTC on the WSL clock; one python process at a time under nice 8 on a machine
at load 21-24 / 20 threads (all wall times below are pessimistic).

Scripts: `lib.py` (loaders, cones, sharing statistics), `groups.py` (group structure), `measure.py` (S, delta on
repo and sampled circuits), `wiring_dep.py` (wiring dependence, triple unions, sharing pattern), `cone_core.py`
(smallest sub-circuit inside a cone), `xorsat.py` + `run_sat.py` (generic value-set SAT, CaDiCaL 1.9.5 via
pysat, child process with wall limit), `group_minima2.py` (group minima by SAT), `reverse.py` (constructive
transposition: minimum group circuits), `submaps.py` (pair sub-maps by SAT), `closure_dfs.py` (exact closure
deficiency: the lower-bound tool that worked), `driver*.sh` (sequencing). Data/logs: `groups.json`,
`measure.log/json`, `wiring_dep.log/json`, `cone_core.log`, `minima.jsonl`, `group_minima.log`,
`group_minima2.log`, `reverse.log`, `closure.log/jsonl`, `submaps.log/jsonl`, `driver.log`.

Labels: [proved] complete argument in this file; [finite-checked] exact computation by a named script;
[measured] data from real circuits; [conjecture] supported by data, no proof; [guess]. Archive files were treated
as unverified notes; everything below was re-derived or re-measured.

## 0. Summary

1. The identity is exact and elementary [proved, Section 2], but with S counted WITH MULTIPLICITY it is an
   accounting tautology: S - delta = 108 - G for every dead-gate-free circuit. "A sharing cap S <= c + delta
   valid for all circuits" is literally the statement "G >= 108 - c". The route re-labels the lower-bound
   problem; it does not reduce it.
2. The eight group minima 12,16,12,16,16,12,12,12 are correct [proved: transposition identity + distinct-column
   count; upper bounds by explicit verified circuits, Section 3]. The sprint's SAT encoding cannot finish even the
   8-input / 11-gate UNSAT in 10 minutes, so the proof, not SAT, carries the lower bounds.
3. Real circuits [measured, Section 4]: repo 88@5 has S = 41, delta = 21; 4314 distinct sampled 88s have
   S in [37, 64] (median 43), delta in [17, 44] (median 23), S - delta = 20 always, never a dead gate. NO known
   88, 89 or 97 realises ANY group minimally: delta_g >= 1 for every group in all 4317 circuits, >= 3 for the
   weight-7 groups 1,3,4. Every circuit has 3-4 gates used by FIVE groups (bit-7 input pairs such as x7^x15).
   In the repo circuits every cone is irredundant (no proper closed subset of its values computes the group):
   the extra gates are not "a minimum circuit plus helpers", the cone is a different, shareable circuit. The
   archive's "(delta, S) = (25, 36)" is exactly the repo 97@3 (108 + 25 - 36 = 97, not 88); its "(20, 40) for
   the 88" differs from the repo 88@5 by one group membership.
4. Proved structure [Section 5]: (a) the cones of any set K of groups together contain >= m_K gates (sub-map
   minimum), hence |C_g & C_h| <= |C_g| + |C_h| - m_gh = s_gh + delta_g + delta_h; (b) a group with
   delta_g = 0 has every mask of its cone inside its own 8 or 12 support inputs, so two defect-free groups
   share only masks in the support intersection (nothing for the 13 support-disjoint pairs, <= 11 values for
   overlap-4 pairs); (c) in an inside-support circuit a gate serves at most 5 groups and only the 11 masks on
   {x7,x15,x23,x31} reach 5; (d) support-disjoint families are exact direct sums: m_{2,4,6} = 40, so G >= 40.
5. Sub-maps [Section 6, finite-checked by closure deficiency]: m_{1,3} = m_{1,4} = 32 = 16 + 16 and
   m_{0,3} = m_{0,4} = m_{2,3} = m_{1,7} = m_{3,7} = m_{4,7} = 28 = 12 + 16 EXACTLY although each of these pairs
   shares four inputs (pair sharing potential 0); (1,2), (4,5): 25 <= m <= 28 (potential <= 3); consecutive
   type-A pairs 21 <= m <= 23 (<= 2); (0,1): 21 <= m <= 25 (<= 7); (3,4): 27 <= m <= 32 (<= 5); triple
   (5,6,7): 24 <= m <= 33. Summed over all 28 pairs the pair sharing potential is <= 24 [proved from these
   numbers]: 21 of the 28 pairs cannot save a single gate by sharing. The one clean consequence is conditional:
   a circuit realising ALL eight groups minimally (delta = 0) has G >= 84 -- but no known circuit has
   delta = 0, an 87 need not, and with defects the pairwise caps collapse to G >= 84 - 6 delta.
6. Verdict [Section 7]: this route gives no lower bound above 75 with provable facts and cannot in principle
   without higher-order (triple and beyond) sub-map minima that are out of reach; the only structural constraints
   on an 87 it yields ("S = 21 + delta", the sub-map inequalities, Theorem 5) are satisfied by every 88 the
   search produces, so they are not a usable filter.

## 1. The groups (verified from the matrix) [finite-checked: groups.py]

Row i of `aes-mixcolumns.mat.txt` is output y_i, column j is input x_j; x_(8b+r), y_(8b+r) = bit r of byte b.
Group j (j = 0..7) := {y_j, y_(8+j), y_(16+j), y_(24+j)} = bit j of the four output bytes (the circulant
structure: output bit j of byte b is (02*a_b + 03*a_(b+1) + a_(b+2) + a_(b+3))_j; (02*a)_j depends on bit j-1 of
a for j in {0,2,5,6,7} and on bits {j-1, 7} for j in {1,3,4}, the xtime feedback 0x1b).

| g | rows            | row weight | support bit positions (x 4 bytes) | n_g | distinct nonbasis columns | m_g |
|---|-----------------|-----------:|-----------------------------------|----:|--------------------------:|----:|
| 0 | 0, 8, 16, 24    | 5 | {7, 0}    |  8 | 8 | 12 |
| 1 | 1, 9, 17, 25    | 7 | {7, 0, 1} | 12 | 8 | 16 |
| 2 | 2, 10, 18, 26   | 5 | {1, 2}    |  8 | 8 | 12 |
| 3 | 3, 11, 19, 27   | 7 | {7, 2, 3} | 12 | 8 | 16 |
| 4 | 4, 12, 20, 28   | 7 | {7, 3, 4} | 12 | 8 | 16 |
| 5 | 5, 13, 21, 29   | 5 | {4, 5}    |  8 | 8 | 12 |
| 6 | 6, 14, 22, 30   | 5 | {5, 6}    |  8 | 8 | 12 |
| 7 | 7, 15, 23, 31   | 5 | {6, 7}    |  8 | 8 | 12 |

Example, group 0: y0 = x7+x8+x15+x16+x24, y8 = x0+x15+x16+x23+x24, y16 = x0+x8+x23+x24+x31,
y24 = x0+x7+x8+x16+x31; group 1: y1 = x0+x7+x8+x9+x15+x17+x25, y9 = x1+x8+x15+x16+x17+x23+x25, ... (full list:
groups.py output). Two isomorphism types [finite-checked by explicit bit relabeling]: type A = {0,2,5,6,7}
(8 inputs, rows of weight 5), type B = {1,3,4} (12 inputs, rows of weight 7). Support overlaps |supp(g) & supp(h)|:

```
      0   1   2   3   4   5   6   7
 0    8   8   0   4   4   0   0   4
 1    8  12   4   4   4   0   0   4
 2    0   4   8   4   0   0   0   0
 3    4   4   4  12   8   0   0   4
 4    4   4   0   8  12   4   0   4
 5    0   0   0   0   4   8   4   0
 6    0   0   0   0   0   4   8   4
 7    4   4   0   4   4   0   4   8
```
13 support-disjoint pairs: 02 05 06 15 16 24 25 26 27 35 36 46 57. The bit-7 inputs {x7,x15,x23,x31} lie in the
supports of FIVE groups {0,1,3,4,7}; every other bit position lies in exactly two supports (bit j in groups j
and j+1 for j = 0..6, i.e. bit 0 in {0,1}, bit 1 in {1,2}, ..., bit 6 in {6,7}).

## 2. The identity: definitions, exact statement, proof, hypotheses

Circuit: straight-line program of G two-input XOR gates over x0..x31, free fanout. Every output y_i has weight
>= 5 and the rows are distinct, so the 32 outputs are 32 distinct gates. For a group g the CONE C_g is the set
of gates that are ancestors of, or equal to, the four output gates of g (inputs are not gates). Let
k(v) = |{g : v in C_g}| and D = {v : k(v) = 0} (dead gates). Define

    S     := sum over gates v with k(v) >= 1 of (k(v) - 1)     (shared units, WITH multiplicity)
    S_cnt := #{v : k(v) >= 2}                                  (the "number of shared gates" reading)
    delta := sum_g delta_g,  delta_g := |C_g| - m_g,  m_g = exact unrestricted minimum for the 4 outputs of g.

THEOREM 1 [proved]. For every circuit computing MixColumns, delta >= 0 and
        G = 108 + delta - S + |D|.
In particular G = 108 + delta - S when no gate is dead, and G >= 108 + delta - S always.
Proof. C_g with the inherited wiring is a circuit for the four outputs of g (closed under taking operands), so
|C_g| >= m_g, delta_g >= 0. Count (gate, group) incidences: sum_g |C_g| = sum_v k(v) = sum_{v: k>=1} k(v). Live
gates: G - |D| = sum_{v: k>=1} 1. Subtract: sum_g |C_g| - (G - |D|) = S. So G = sum_g |C_g| - S + |D| =
sum_g (m_g + delta_g) - S + |D|, and sum_g m_g = 108 by Theorem 2. QED

Hypotheses, exactly. (H1) m_g are the exact minima -- used only for delta >= 0 (Section 3). (H2) "no dead gates"
-- used only for equality; minimum circuits have none. (H3) S is the MULTIPLICITY count. With the count reading,
G = 108 + delta - S_cnt - sum_{v: k>=3} (k(v) - 2) + |D|; the readings differ in every real circuit (repo 88@5:
three gates with k = 5, S = 41 vs S_cnt = 32). (H4) The constant 108 belongs to these eight blocks; the identity
itself holds for any family of output blocks (with D = gates in no block's cone) -- disjointness is not needed
for Theorem 1 (it matters for the archive's two-block "m_A + m_B = m" statements, which are not used here).

Remark (tautology). Rearranged, S - delta = 108 - G + |D|. An inequality "S <= c + delta for all dead-free
circuits" IS "G >= 108 - c". The only such cap known to be true is c = 33 (the proved 75); c = 20 is the
88-optimality question itself. The identity is a bookkeeping frame; its value is only that structural facts
about cones (supports, sub-map minima) can be stated in it.

Archive numbers. The archive (xor_proof_master status/forward88) defines S and delta exactly as above and says
"(delta, S) = (20, 40)" for "the recorded 88@5"; the repo 88@5 with its file wiring gives (21, 41) [measured],
one group membership more (its value set admits a unique legal wiring: 200 random re-wirings coincide). The pair
"(25, 36)" quoted in the task is EXACTLY the repo 97@3 (delta = 25, S = 36, G = 97) [measured]:
108 + 25 - 36 = 97, so "= 88" was an arithmetic slip, not another convention.

## 3. The eight group minima [proved + finite-checked]

LEMMA 3.1 (support restriction) [proved]. Let B be a set of linear forms not depending on x_i. If a circuit for B
has a gate with operand x_i, there is a circuit for B with strictly fewer gates. Proof: substitute x_i := 0 and
propagate: a gate x_i ^ u becomes the node u (delete the gate, redirect its users and output markers to u); a
gate whose two operands have become the same node computes 0 (delete it; its users w ^ 0 become w); iterate.
Each step deletes a gate, at least one is deleted, every output keeps its value since B does not depend on x_i.
Hence a minimum circuit for group g uses only the n_g support inputs, and m_g is the minimum over circuits on
those inputs (this justifies computing "restricted to the support").

LEMMA 3.2 (transposition identity) [proved]. Let A be an m x n matrix over GF(2) with no zero row and no zero
column. Then C(A) = C(A^T) + n - m (C = minimum XOR-gate count).
Proof. Take a minimum circuit F for A: G gates, every gate live, every input used (an unused input is a zero
column). Nodes: n inputs + G gates. For a node u let d(u) = number of operand edges leaving u plus the number of
outputs designated at u; d(u) >= 1 for every node. In reverse topological order define r(u) in GF(2)^m as the
XOR of e_o over outputs o designated at u and of r(w) over gates w having u as an operand. By induction r(u)_o is
the parity of the number of paths from u to output o, i.e. the coefficient of u's value in y_o; for an input,
r(x_i) = column i of A = row i of A^T. Computing r(u) from its d(u) terms costs d(u) - 1 XORs; the total is
sum_u (d(u) - 1) = (2G + m) - (n + G) = G + m - n. This is a circuit for A^T (inputs e_1..e_m), so
C(A^T) <= C(A) + m - n. A^T has no zero row/column either, so symmetrically C(A) <= C(A^T) + n - m. QED
(A reversed node may XOR two equal values; deleting such a zero gate only strengthens the "<=".)

LEMMA 3.3 [proved]. C(A^T) >= |T(A)|, where T(A) is the set of distinct columns of A that are nonzero and not unit
vectors: each is an output of A^T that is not an input, hence a gate, and distinct values are distinct gates.

THEOREM 2 [proved]. m_g = 12 for g in {0,2,5,6,7} and m_g = 16 for g in {1,3,4}; the sum is 108.
Proof. By Lemma 3.1 work on the n_g support inputs. Each group has |T(A_g)| = 8 [finite-checked, groups.py: type
A has 8 distinct columns {0011,0110,1100,1001,0111,1011,1101,1110} over the group's four outputs; type B has 12
columns, 8 distinct, each weight-2 column twice]. Lemmas 3.2-3.3: m_g >= 8 + n_g - 4 = 12 (n_g = 8) or 16
(n_g = 12). Upper bounds: explicit 12- and 16-gate circuits, built by greedy closure of T(A_g) from the four basis
vectors (8 transposed gates, one per column) followed by the mechanical reversal of Lemma 3.2, verified by
evaluation [finite-checked: reverse.py, reverse.log, minima.jsonl]; for the type-A groups the SAT solver also
produced 12-gate circuits in 1-16 s [group_minima2.log]. QED

Independent SAT status (honest). Transposed instances "7 gates for the 8 columns" are UNSAT in < 1 s for all
eight groups [finite-checked] -- the same content as Lemma 3.3. The forward instances "m_g - 1 gates on the
support" (8 inputs / 11 gates; 12 inputs / 15 gates) did NOT finish: 9 min for group 0 in a first attempt, then
60 s limits, all TIMEOUT; even the forward 16-gate SAT instances of groups 1,3,4 timed out at 586 s. The
value-set SAT encoding is useless for UNSAT at this size on this machine; the lower bounds rest on Lemmas
3.2-3.3, which are complete proofs.

## 4. Measurements on real circuits [measured: measure.py, wiring_dep.py, cone_core.py]

Data: the three repo circuits (own file wiring) and the 88-gate value sets in hunt/samples.jsonl,
hunt/samplesC/samples.jsonl, hunt/samplesD/samples.jsonl: 4314 distinct value sets (10965 records of 88/89
gates in the three files; duplicates by value set removed). Samples store VALUE SETS only, so a wiring was
reconstructed (greedy, lib.wiring_from_values). S and delta individually depend on the wiring; S - delta =
108 - G does not. Wiring dependence probed with random legal wirings (wiring_dep.py).

### 4.1 Repo circuits

| circuit | G | S | S_cnt | delta | S-delta | cone sizes |C_0..C_7| | delta_g | k-distribution | shared units by depth | S over random re-wirings |
|---|---|---|---|---|---|---|---|---|---|---|
| 88@5 | 88 | 41 | 32 | 21 | 20 | 14,20,14,21,20,13,14,13 | 2,4,2,5,4,1,2,1 | k1:56 k2:29 k5:3 | d1:28 d2:9 d3:4 | 41 (wiring unique) |
| 89@4 | 89 | 35 | 29 | 16 | 19 | 14,20,13,19,19,13,13,13 | 2,4,1,3,3,1,1,1 | k1:60 k2:25 k3:2 k4:2 | d1:31 d2:4 | 35..43 (14 wirings) |
| 97@3 | 97 | 36 | 25 | 25 | 11 | 14,22,13,22,22,13,13,14 | 2,6,1,6,6,1,1,2 | k1:72 k2:21 k4:1 k5:3 | d1:33 d2:3 | 36..38 (16 wirings) |

Identity check 108 + delta - S = G holds in every case (dead = 0). Inputs outside the group support touched by a
cone: 0 for all groups in all three circuits (all three are "inside-support" circuits, Section 5d).

Repo 88@5 pairwise table (upper triangle |C_g & C_h|, lower triangle |C_g | C_h|, diagonal |C_g|):
```
      0   1   2   3   4   5   6   7
 0   14   9   0   3   3   0   0   3
 1   25  20   4   3   3   0   0   3
 2   28  30  14   3   0   0   0   0
 3   32  38  32  21   9   0   0   3
 4   31  37  34  32  20   3   0   3
 5   27  33  27  34  30  13   4   0
 6   28  34  28  35  34  23  14   3
 7   24  30  27  31  30  26  24  13
```
The 32 shared gates (k >= 2) of the 88@5 (wiring_dep.log): 19 at depth 1 (16 input pairs x_a ^ x_b in the same
bit position of two bytes; the three bit-7 pairs x7^x15, x15^x31, x23^x31 are used by all five groups
{0,1,3,4,7}), 9 at depth 2, 4 at depth 3; every one has its mask inside the support of every group using it.
Sharing lives on the adjacent pairs 01 (9 gates), 34 (9), 12 (4), 23 (3), 45 (3), 56 (4), 67 (3) plus the
five-group bit-7 club (3 gates = 12 units of S).

### 4.2 Sampled 88s (4314 distinct value sets, greedy wiring)

| quantity | min | median | mean | max |
|---|---|---|---|---|
| S (multiplicity) | 37 | 43 | 43.35 | 64 |
| S_cnt | 28 | 33 | 33.26 | 39 |
| delta | 17 | 23 | 23.35 | 44 |
| S - delta | 20 | 20 | 20 | 20 |
| dead gates | 0 | 0 | 0 | 0 |
| groups with delta_g = 0 | 0 | 0 | 0 | 0 |

Per-group defect histograms (delta_g = |C_g| - m_g over 4314 circuits):
delta_0: 1:1647 2:2021 3:606 4:40 | delta_1: 3:30 4:337 5:593 6:722 7:1061 8:551 9:474 10:198 11:254 12:84 13:9 14:1
delta_2: 1:3022 2:1259 4:32 7:1 | delta_3: 3:356 4:1969 5:1157 6:762 7:28 8:7 9:33 10:1 21:1
delta_4: 3:1855 4:869 5:1176 6:359 7:51 9:4 | delta_5: 1:1435 2:2879 | delta_6: 1:2340 2:1974 | delta_7: 1:2854 2:1419 3:41
Every known 88 pays 1-2 extra gates on each type-A group and >= 3 on each type-B group (group 1 typically 7).
Least-sharing wiring: for 300 random samples x 31 random wirings, min S is 37..50 (median 43), so the greedy
wiring is already near the least-sharing one; delta_min = S_min - 20 is 17..30.

Pooled multiplicity of all sample gates: k=1 62.2%, k=2 33.4%, k=3 0.6%, k=4 0.5%, k=5 3.3%, k=6 0.01% (26 gates).
Shared units by depth (pooled): depth 1: 58.5%, 2: 18.0%, 3: 13.7%, 4: 5.0%, >= 5: 4.8%.
Mask-support test: of 143490 shared gate instances, 136270 (95.0%) have their mask inside the support of every
group that uses them; the 5% tail is cancellation-based sharing, e.g. x2^x18 or x10^x26 (bit position 2) used
by groups {1,2,3} although bit 2 is outside supp(1) -- group 1 pays defect for it (Theorem 5a). The commonest
k >= 3 gates are the bit-7 pairs x23^x31, x7^x15, x7^x31, x15^x23 (each in about half of the circuits),
Gamma = {0,1,3,4,7}.

Pairwise cones over the samples (mean |C_g & C_h| upper, mean |C_g | C_h| lower, diagonal mean |C_g|):
```
      0     1     2     3     4     5     6     7
 0  13.8  10.4   0.0   3.2   3.3   0.0   0.0   3.2
 1  26.5  23.1   4.2   3.9   3.3   0.0   0.0   3.2
 2  27.1  32.2  13.3   2.9   0.0   0.0   0.0   0.0
 3  31.2  39.9  31.0  20.6   8.2   0.0   0.0   3.1
 4  30.5  39.9  33.4  32.5  20.0   3.7   0.0   3.2
 5  27.4  36.8  27.0  34.3  30.0  13.7   3.5   0.0
 6  27.2  36.6  26.8  34.1  33.5  23.7  13.5   3.2
 7  23.9  33.2  26.7  30.8  30.2  27.0  23.6  13.3
max |C_g & C_h|:  01:15 02:3 03:11 04:5 07:5 12:9 13:23 14:6 17:5 23:8 24:1 27:1 34:13 35:1 37:5 45:4 46:1 47:7 56:4 67:4, others 0
min |C_g | C_h| (witness upper bounds on the pair sub-map minima m_gh):
  01:25 02:26 03:29 04:29 05:26 06:26 07:23 12:29 13:36 14:35 15:32 16:32 17:29 23:29 24:32 25:26 26:26 27:26
  34:32 35:32 36:32 37:29 45:29 46:32 47:29 56:23 57:26 67:23
min |C_g | C_h | C_i| for some triples: 567:33 067:33 017:35 012:35 234:42 345:42 025:39 134:48
```
Support-disjoint pairs essentially never share (mean 0.0, max 1), as Theorem 5c predicts (sharing across
disjoint supports needs cancellation and costs defect). The two heavy pairs are 01 (10.4) and 34 (8.2).

### 4.3 Do the cones contain a minimum group circuit? [finite-checked: cone_core.py, repo circuits only]

c_g := size of the smallest split-closed subset of the cone's VALUE set containing the four targets (exact brute
force over subsets). c_g = m_g would mean "a minimum circuit plus extra gates"; c_g = |C_g| means the cone is
irredundant: no proper sub-collection of its values computes the group under any wiring. Result for all 24
(circuit, group) pairs of the three repo circuits: c_g = |C_g| (88@5: 14,20,14,21,20,13,14,13; 89@4:
14,20,13,19,19,13,13,13; 97@3: 14,22,13,22,22,13,13,14). The sampled-88 pass was stopped after 13 minutes
(Python brute force on the 20-23-value type-B cones is too slow); no sample numbers.

Reading of 4.1-4.3: real circuits do not "realise a group minimally and then share". Each group is realised by
an irredundant circuit with 1-7 gates more than its minimum, whose values (adjacent-byte input pairs, bit-7
pairs, their sums) are shareable; each extra gate buys about two shared units. delta ~ 17-25 and S ~ 37-45 are
both large and move together; only their difference, 20, is pinned by G = 88.

## 5. What can be proved [proved unless marked]

THEOREM 3 (sub-map / union bound). For any set K of groups, U_K := union of the C_g (g in K), with the inherited
wiring, is a circuit for the 4|K| outputs of K; hence |U_K| >= m_K := C(A_K) (A_K = rows of K, columns = union
of supports). Consequently
        |C_g & C_h| <= |C_g| + |C_h| - m_gh = s_gh + delta_g + delta_h,   s_gh := m_g + m_h - m_gh,
and G >= m_K + #(gates outside U_K) >= m_K for every K.

THEOREM 4 (direct sums). If the groups in K have pairwise disjoint supports then m_K = sum_{g in K} m_g.
Proof. A_K is block diagonal; its columns are the columns of the A_g padded with zeros, distinct across groups
(different row blocks) and 8 distinct nonbasis per group, so |T(A_K)| = 8|K| and n_K = sum n_g. Lemmas 3.2-3.3:
m_K >= 8|K| + sum n_g - 4|K| = sum (8 + n_g - 4) = sum m_g; juxtaposing minimum circuits gives <=. QED
Pairwise support-disjoint families: the 13 disjoint pairs, the triples {0,2,5}, {0,2,6}, {2,5,7} (m = 36) and
{2,4,6} (m = 40); no four groups are pairwise disjoint. Hence G >= 40 [proved] -- the sampled 88s realise
{0,2,5} with 39 gates (not 36) and {1,3,4} with 48 = 16 + 16 + 16.

THEOREM 5 (support and defect).
(a) E_g := #{v in C_g : an operand of v is an input outside supp(g)} <= delta_g. Proof: apply the substitution of
    Lemma 3.1 to all outside inputs inside the circuit C_g; each of the E_g gates is deleted, so m_g <= |C_g| - E_g.
(b) If delta_g = 0 then no gate of C_g has an outside operand, hence (induction along the topological order) every
    mask in C_g lies in the coordinate subspace of supp(g), and C_g is a minimum circuit of the group.
(c) If v in C_g & C_h and delta_g = delta_h = 0 then mask(v) is a nonzero vector inside supp(g) & supp(h). Hence:
    for the 13 support-disjoint pairs, C_g & C_h nonempty forces delta_g + delta_h >= 1; two defect-free groups
    with overlap 4 share at most 11 gates (the nonbasis masks of a 4-dimensional coordinate space).
(d) Position signature. For a nonzero mask M let Gamma(M) = {g : M inside supp(g)} and kappa(M) = |Gamma(M)|.
    From Section 1: kappa = 5 iff M is supported on {x7,x15,x23,x31} (Gamma = {0,1,3,4,7}); kappa = 2 iff M uses
    exactly one bit position j in 0..6 (Gamma = {j, j+1}), or bit positions inside {7,0} (Gamma = {0,1}), or inside
    {7,3} (Gamma = {3,4}), the kappa = 5 case excluded; kappa = 1 if M fits in exactly one support; kappa = 0
    otherwise. Call a circuit INSIDE-SUPPORT if every mask of every cone lies in that cone's support (E_g = 0 for
    all g; all three repo circuits and 95% of the sampled sharing). In an inside-support circuit k(v) <=
    kappa(mask(v)), so S <= 4 a_7 + a_2 with a_7 <= 11 the number of gates with mask in the bit-7 space and a_2 the
    number with kappa = 2 (repo 88@5: a_7 = 3 giving 12 units, 29 gates with k = 2: S = 41). In particular a gate
    can serve two groups without defect only if its mask lies in their common support: nothing for disjoint
    supports, a 4-dimensional space (11 masks) for overlap-4 pairs, an 8-dimensional space for (0,1) and (3,4).
(e) Depth: |mask(v)| <= 2^depth(v). It restricts which masks exist at a depth, not which groups may use them;
    nothing group-specific follows (every k = 5 gate in real circuits sits at depth 1 anyway).

What Theorems 3-5 give for S - delta, honestly. Every local cap has the form |C_g & C_h| <= s_gh + delta_g +
delta_h. Since k - 1 <= number of pairs inside Gamma(v), summing over gates gives
        S <= sum_{g<h} |C_g & C_h| <= sum_{g<h} s_gh + 7 delta,      hence   G >= 108 - sum_{g<h} s_gh - 6 delta.
Summing only over spanning trees of each Gamma(v) inside the support-overlap graph (max degree 4) improves the
constant to 3 delta; the coefficient of delta stays negative in every version because every pair cap contains
|C_g| = m_g + delta_g, and delta is free (17-44 in real 88s). A cap of the form |C_g & C_h| <= s_gh + (something
not growing with delta) would be needed, i.e. a proof that extra gates in a cone cannot be shared -- which is
false: the extra gates are exactly the shared ones (Section 4).

COROLLARY 5.1 (the delta = 0 case, best case of the pairwise route) [proved, using the sub-map numbers of
Section 6]. For a circuit in which every group is realised minimally (delta = 0): S <= sum_{g<h} s_gh <= 24, so
G = 108 - S >= 84. This is the strongest statement the route proves and it is conditional on delta = 0, which
no known circuit satisfies and which an 87 need not satisfy: as soon as defects are allowed the caps read
|C_g & C_h| <= s_gh + delta_g + delta_h and the same computation gives only G >= 84 - 6 delta, vacuous for
delta >= 2. Unconditionally the pairwise sub-map information forces nothing above Theorem 4's G >= 40; only
triple-and-higher sub-map minima (Bonferroni's next terms, positive sign) could add anything, and those are out
of reach (Section 6: m_{5,6,7} in [24, 33]).

THEOREM 6 (necessary conditions for an 87) [proved; consequences of Theorems 1-5 and Section 6].
(i)   S = 21 + delta >= 21 and sum_g |C_g| = 108 + delta.
(ii)  |U_K| >= m_K for every K: |C_2 | C_4 | C_6| >= 40, |C_0 | C_2 | C_5| >= 36, |C_1 | C_3| >= 32,
      |C_g | C_h| >= 28 for the six A-B pairs (0,3),(0,4),(2,3),(1,7),(3,7),(4,7), >= 25 for (1,2),(4,5), >= 27 for
      (3,4), >= 21 for consecutive type-A pairs and for (0,1).
(iii) |C_g & C_h| <= delta_g + delta_h for every pair with zero potential -- (1,3), (1,4) and the six A-B
      overlap-4 pairs -- so every gate shared across such a pair is paid for by defect; e.g. the bit-7 pairs
      shared by {0,1,3,4,7} in every known 88 cost delta_1 + delta_3 >= |C_1 & C_3| = 3.
(iv)  If some delta_g = 0 then C_g is a 12- or 16-gate minimum circuit inside supp(g), sharing only masks inside
      support intersections with defect-free partners.
(v)   [measured, not proved] every known 88/89/97 has delta_g >= 1 for all g and >= 3 for g in {1,3,4}; an 87 with
      the same property has delta >= 14 and S >= 35 (at least 35 shared units on 87 gates, at least 3 gates of
      multiplicity 5 or many of multiplicity 2).
[conjecture] (v) holds for every 88 and any 87: no optimal circuit realises a group minimally, because a minimum
12/16-gate group circuit (reversal of a closure sequence, Section 3) offers too few shareable values.

## 6. The sub-map route: exact and bounded sub-map minima [finite-checked: closure_dfs.py, submaps.py]

Method. For a set K, by Lemma 3.2 m_K = C(A_K^T) + n_K - 4|K| and A_K^T has only 4|K| inputs. Moreover
C(A_K^T) = |T_K| + e_K, where e_K is the CLOSURE DEFICIENCY of T_K: the least number of non-target values a
circuit must create so that every target is the XOR of two earlier values (a circuit with |T_K| + e gates has
exactly e non-target gate values; a circuit with fewer would contradict Lemma 3.3). closure_dfs.py searches
e = 0, 1, 2, ... exactly: greedy target closure is sound because adding a target costs one gate whenever it is
added and only enlarges the available set, extras are XORs of two available values (every circuit value is one),
states are memoised; failure at e_max proves e_K >= e_max + 1 and m_K >= |T_K| + e_max + 1 + n_K - 4|K|. Upper
bounds: the smallest cone union among the 4317 real circuits, or the direct sum. SAT (xorsat.py on the transposed
instance): (0,2) at 23 gates is excluded by |T| alone; (6,7) at 22 gates TIMEOUT after 584 s; (0,1) at 24 and
(3,4) at 31 were cancelled to save time (no result). The Python DFS reaches e_max = 4 in about a minute for the
12-target pairs but timed out at e_max = 5 for (6,7) (300 s); runs at e_max = 5, 6 for (0,1) and (6,7) were
still queued when this report was written: later lines of closure.log/closure.jsonl supersede the lower bounds
in the table (each such line is an exact statement of its own; "timeout" lines prove nothing).

| K | n_K | |T_K| | e_K | m_K lower bound | m_K upper bound | pair potential s = sum m_g - m_K |
|---|---|---|---|---|---|---|
| 13 support-disjoint pairs | 16 / 20 | 16 | 0 | exact 24 (A-A), 28 (A-B) | = | 0 [proved, Thm 4] |
| (1,3), (1,4)  B-B, overlap 4 | 20 | 20 | 0 | EXACT 32 = 16 + 16 | 32 (= 36/35 in samples) | 0 |
| (6,7), (5,6), (0,7)  A-A consecutive | 12 | 12 | >= 5 | 21 | 23 | <= 2 |
| (0,1)  A inside B | 12 | 12 | >= 5 | 21 | 25 | <= 7 |
| (1,2), (4,5)  A-B overlap 4 via bit 1 / bit 4 | 16 | 12 | >= 5 | 25 | 28 | <= 3 |
| (0,3), (0,4), (2,3), (1,7), (3,7), (4,7)  A-B overlap 4 | 16 | 16 | 4 | EXACT 28 = 12 + 16 | 28 | 0 |
| (3,4)  B-B overlap 8 | 16 | 16 | >= 3 (e_max 4: timeout 100 s) | 27 | 32 | <= 5 |
| (5,6,7)  A-A-A | 16 | 16 | >= 4 | 24 | 33 | <= 12 |
| {0,2,5}, {0,2,6}, {2,5,7} | 24 | 24 | 0 | exact 36 | 36 | 0 |
| {2,4,6} | 28 | 24 | 0 | exact 40 | 40 | 0 |

Scope: the lower bounds are statements about the sub-map for every circuit (any depth, any cancellation); the
upper bounds are witnesses, not optima. Observations: (1,3) and (1,4) are "direct sums in disguise": all 20
columns of A_{13} are distinct nonbasis, so the two weight-7 groups cannot save a single gate by sharing
although they share four inputs -- yet every real 88 shares 3-4 gates between them (the bit-7 pairs), paid by
delta_1 + delta_3 >= 3 (Theorem 6 iii). All six A-B pairs overlapping in one bit position are exact direct sums
too (m = 28 = 12 + 16; closure deficiency exactly 4 with 16 distinct columns). Summing the table,
sum_{g<h} s_gh <= 13*0 + 2*0 + 6*0 + 3*2 + 7 + 2*3 + 5 = 24 [proved from the table]: 21 of the 28 pairs have
zero sharing potential, and the whole pairwise potential of the map is at most 24 gates.

What the sub-map numbers give for the whole map. (1) Monotonicity: G >= m_K; the best proved value is 40 ({2,4,6}).
(2) Combination needs intersection caps; Section 5 shows each carries the defects, and Corollary 5.1 shows that
even with all defects zero the pairwise caps stop at 74. (3) Structurally the numbers are informative: the pair
potentials total <= 34 while real 88s carry S = 37-64 shared units -- the surplus is multi-group sharing of
defective cones (one bit-7 pair gives 4 units at once), which is why sum s_gh cannot bound S.

## 7. Verdict

- Can this route give a lower bound above 75? No -- not with any fact proved here or in the archive, and not in
  principle at the pairwise level: the identity is a tautology (S - delta = 108 - G), and every structural cap
  on sharing has the form "shared <= potential + defects", which cancels against the +delta of the identity.
  The pairwise potentials are tiny (total <= 24: zero for 21 of the 28 pairs -- the 13 support-disjoint ones,
  (1,3), (1,4) and all six A-B pairs overlapping in one bit position -- and at most 2, 3, 5, 7 for the other
  seven), so in the hypothetical defect-free case the route would give G >= 84; but
  defects are free, every known circuit has 17-44 of them, and one defective bit-7 pair is worth four units of
  S at once (five groups per gate). The obstruction is therefore not the circulant overlap of supports by
  itself; it is that extra (defect) gates are exactly the shared gates and nothing charges them only once.
  Beating 75 this way would need triple/quadruple sub-map minima (12-16 outputs) entering with a positive sign,
  where the exact tools stop (m_{5,6,7} in [24, 33] after the DFS; SAT times out at 22 gates for a pair).
- Structural constraints on an 87 that are PROVED (Theorem 6): S = 21 + delta, sum |C_g| = 108 + delta, the
  sub-map inequalities of Section 6, defect-paid sharing between 1-3 and 1-4 and between the A-B overlap-4 pairs,
  Theorem 5 for any defect-free group. Every 88 the search produces satisfies all of them with S - delta = 20, so
  they do not filter anything.
- Facts the search could use only as heuristics [measured / conjecture]: no known 88 realises a group minimally
  (delta_g >= 1, >= 3 for weight-7 groups); the shared structure is always the same (adjacent-byte input pairs at
  depth 1, bit-7 pairs shared by five groups, 4-9 gates shared between 0-1 and 3-4, nothing across disjoint
  supports, 5% cancellation sharing); an 87 resembling the 88s has delta >= 14 and S >= 35; an 87 NOT resembling
  them would have to realise some group minimally or share across supports by cancellation -- both unobserved.
- The useful by-product: closure deficiency on the transposed map (closure_dfs.py) gives exact sub-map lower
  bounds in seconds where SAT fails (m_{1,3} = 32 exactly; pair gaps of 2-5 gates). A C implementation with
  larger e could pin the pair minima exactly and attack triples, but by Corollary 5.1 pinning pairs changes
  nothing; only triples and beyond could move the bound, and only if their minima turn out far above the
  pairwise predictions.
