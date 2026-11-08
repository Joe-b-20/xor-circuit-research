# Near-miss anchors: constructive sat87 attempt on an 87 (R4a candidate D, R4b 18-pair state, R8 A75/A76)

Date: 2026-11-07/08 UTC.  Folder: ~/xs-campaigns/2026-11-07-sprint/nearmiss/ (scripts common.py, gen.py, run.py,
mktable.py, describe.py; instance lists inst_*.json; raw rows results.jsonl; logs run.log, run2.log; D.txt, P18.txt).
Solver: sat87.py (sprint sat/ folder, encoding and soundness as documented there), cadical195 through pysat, one
child at a time under nice -n 8.  Other sprint campaigns (satmob, satmob2, power, c3_run) were running their own
solver children on the same 20-core machine during this run, so wall times are indicative only.

## 0. Result in one line

No 87.  Every instance that finished is UNSAT; the instances that could not finish are listed with their limits.
FOUND_87 was not written and found/ is empty.

## 1. The formulation (same as the sat/ campaign)

I(K, m): K is a split-closed set of kept values (constants in the operand pool, together with the 32 inputs);
m new gates are asked for, each the XOR of two distinct earlier pool elements, such that every one of the 32
targets not in K is one of the new gates.  Proved in sat87.py: I(K, m) is SAT iff some split-closed value set
V with K u TARGETS <= V and |V| <= |K| + m exists, i.e. iff some circuit of <= |K| + m gates contains K.  So with
|K| + m = 87, UNSAT excludes every 87 (at any depth, with any wiring) whose value set contains K; it says nothing
about circuits that drop a value of K.  A SAT would have been decoded, checked with sat87.check_circuit, written
through sat/write_circ.py (NCFF file, circuits/check.py against the matrix, 32 unit-vector evaluation).

Windows.  For a seed set S inside a partial circuit with a given wiring, W = closure(S): everything that depends
on S under the wiring (upward closure), then the helpers that become dead, then whatever K = circuit minus W can
no longer compute from any pair of remaining values (so that K is split-closed).  The any-pair variant (":ap")
skips the upward closure: W is the minimal forced removal.  k = |W|; the instance is I(circuit minus W, m).

## 2. Candidate D (R4a), exactly

Source: AES_Deep_Repair_75_76_Profiles_2026_10_02/aes_deep_repair/results/selected/b87_most_exact.json is a
PROFILE (per-output rows: representative signal, target, actual, residual), not a gate list.  The gate list is the
companion b87_most_exact.known_completion.json: 90 gates = D (signals 32..118, 87 gates) + the 3-gate seed
completion; the first 87 gates reproduce every actual mask the profile cites (32/32 signals checked), and
summary.json / RESULTS.md agree (87 gates, 31 exact, residual rank 1).

Verified here (describe.py, D.txt):
- 87 XOR gates, 87 distinct values, 20 input-pair gates, depth 5; split-closed.
- 31 outputs equal the matrix rows of circuits/aes-mixcolumns/aes-mixcolumns.mat.txt; y19 = 8c840808 is absent.
- The y19 representative r = 8c840008 = y19 ^ x11 (parents x3^x19 and 8c8c0000, depth 4) feeds nothing: it is
  a dead gate.  So D is an 86-gate circuit for 31 outputs plus one useless gate, and the archive completion
  r ^ x11 = y19 is an 88.
- 56 non-target values (55 live helpers + r).  Every instance below drops r (it can always be re-created as one
  of the m new gates, so dropping it is strictly more general than keeping it).

The first question, I(D minus r, 1): is y19 one XOR of the 86 live values and the inputs?  UNSAT in 0.03 s.
Then windows: W = closure({h, r}) for every live helper h (a1; wiring closure and, when smaller, any-pair), the
cone of the parents of r (a2), pairs of helpers in the neighbourhood of y19 (a3: ancestors of r, helpers sharing
>= 3 support bits with y19, parents of the rotation images y3, y11, y27), m = |W| so that the total is 87 and y19
is required among the new gates.

## 3. The 18-pair foundation state (R4b), exactly

Source: research/18_pair_87_checkpoint/18_pair_87_checkpoint.txt (Sep 9) lists the 18 pairs and says: with the
69 rich values of the 19-pair 88, 66 regenerate, 84 values available, exactly o9, o10, o18 missing.  The 19-pair 88
is research/mixcolumns_88_19_primitive_pairs/mixcolumns_88_19_primitive_pairs.txt (full gate list g32..g119;
checked here: 88 gates, depth 6, 19 input pairs = the 18 + x1^x17, 69 rich values, all 32 outputs exact).
Reconstruction (common.foundation18): drop x1^x17, take the any-pair closure of 18 pairs + 69 rich values:
exactly 84 values, missing exactly y9, y10, y18 (the checkpoint text omits bit 10 in its o10 support list; its
own relation o18^o10 = [9,10,18,25] confirms o10 = y10).  P18.txt lists the 84 values with one greedy wiring.
Instances: I(K84, 3) (r = 0), then K = K84 minus a window W of r <= 6 values around the missing outputs
(seeds: the non-target parents and grandparents of y9, y10, y18 in the 88 wiring that survive in K84; singles
and pairs of seeds; any-pair closure, plus the wiring closure when different), m = 3 + r.

## 4. A75 / A76 (R8)

A75 = b75_most_exact (75 gates, 27 exact, missing y11, y12, y19, y27, y28), A76 = b76_nested (A75 plus the helper
h = x15^x19^x23, 76 gates, 27 exact, same five missing).  I(A75, 12) and I(A76, 11) at 900 s each: 5 targets
among 12 (11) free gates with a 75 (76)-value pool.  b76_most_exact (76 gates, 27 exact, missing y3, y11, y19,
y26, y27) was queued third and only run if the budget allowed.

## 5. What ran (timeline, budget)

00:09-00:50 UTC run.log: a0, all 14 (b) instances, D singletons in order of k (k <= 10 at 120 s).  At 00:50 the
driver was stopped (k >= 9 was timing out uniformly) and requeued (run2.log): the remaining k = 10-11 singletons
and the k = 13 cone at 120 s, the 7 neighbourhood pairs at 60 s, the three (c) instances at 900 s, then 600 s
retries of the two instances that had timed out at k <= 8.  One k = 10 instance was killed mid-run by the
restart (not counted).  Finished 01:58 UTC: 81 instance runs, 5,858 s solver wall (~98 min), 60 UNSAT, 21 TIMEOUT.
Not run for lack of budget: inst_a4.json (D singletons with k = 16-28: 80800000 any-pair 16 / wiring 17,
00008080 19/22, 00808000 23/28) and the two large cones (anc1 k = 31, anc_all k = 33).

In the tables: K = "circuit minus W (|K|)", k = |W|, m = new gates (|K| + m = 87 throughout), "targets needed" =
the outputs not in K (y19 always, for D).  Masks are hex over x0..x31 (bit j = x_j); ":ap" = any-pair closure.
Retried instances appear twice (120 s row, then the 600 s row at the end of the group).

## 6. Instance tables (generated by mktable.py from results.jsonl)

### a0 (1 instances)

| instance | K | k | m | targets needed | result | wall s | clauses |
|---|---|---:|---:|---|---|---:|---:|
| a0:r | D minus {8c840008} (86) | 1 | 1 | y19 | UNSAT | 0.2 | 15428 |

### b (15 instances)

| instance | K | k | m | targets needed | result | wall s | clauses |
|---|---|---:|---:|---|---|---:|---:|
| b:r0 | P18 minus {-} (84) | 0 | 3 | y9,y10,y18 | UNSAT | 0.2 | 46894 |
| b:h02040600:ap | P18 minus {y26,02040600} (82) | 2 | 5 | y9,y10,y18,y26 | UNSAT | 0.8 | 78721 |
| b:h02818100:ap | P18 minus {02818100,y17} (82) | 2 | 5 | y9,y10,y17,y18 | UNSAT | 0.5 | 78691 |
| b:h04040206:ap | P18 minus {04040206,y2} (82) | 2 | 5 | y2,y9,y10,y18 | UNSAT | 1.0 | 78711 |
| b:h00000206:ap | P18 minus {00000206,y26,04040206,y2} (80) | 4 | 7 | y2,y9,y10,y18,y26 | UNSAT | 4.6 | 110956 |
| b:h02000200:ap | P18 minus {02000200,y1,y26,02040600} (80) | 4 | 7 | y1,y9,y10,y18,y26 | UNSAT | 3.1 | 110956 |
| b:h02040600,h02818100:ap | P18 minus {y26,02040600,02818100,y17} (80) | 4 | 7 | y9,y10,y17,y18,y26 | UNSAT | 8.1 | 110914 |
| b:h02040600,h04040206:ap | P18 minus {y26,02040600,04040206,y2} (80) | 4 | 7 | y2,y9,y10,y18,y26 | UNSAT | 4.1 | 110942 |
| b:h02818100,h04040206:ap | P18 minus {02818100,04040206,y2,y17} (80) | 4 | 7 | y2,y9,y10,y17,y18 | UNSAT | 5.0 | 110900 |
| b:h00000206 | P18 minus {00000206,y26,02040600,04040206,y2} (79) | 5 | 8 | y2,y9,y10,y18,y26 | UNSAT | 39.3 | 127111 |
| b:h04040000:ap | P18 minus {04040000,04040206,y2,y27,y19,8c8c0000} (78) | 6 | 9 | y2,y9,y10,y18,y19,y27 | UNSAT | 76.2 | 143525 |
| b:h00000206,h02818100:ap | P18 minus {00000206,y26,02818100,04040206,y2,y17} (78) | 6 | 9 | y2,y9,y10,y17,y18,y26 | TIMEOUT @120s | 121.1 |  |
| b:h02000200,h02818100:ap | P18 minus {02000200,y1,y26,02040600,02818100,y17} (78) | 6 | 9 | y1,y9,y10,y17,y18,y26 | UNSAT | 86.8 | 143561 |
| b:h02000200,h04040206:ap | P18 minus {02000200,y1,y26,02040600,04040206,y2} (78) | 6 | 9 | y1,y2,y9,y10,y18,y26 | UNSAT | 105.8 | 143597 |
| b:h00000206,h02818100:ap | P18 minus {00000206,y26,02818100,04040206,y2,y17} (78) | 6 | 9 | y2,y9,y10,y17,y18,y26 | UNSAT | 68.2 | 143561 |

### a1 (54 instances)

| instance | K | k | m | targets needed | result | wall s | clauses |
|---|---|---:|---:|---|---|---:|---:|
| a1:hc0400000 | D minus {y7,8c840008,c0400000,y23} (83) | 4 | 4 | y7,y19,y23 | UNSAT | 0.9 | 62705 |
| a1:h20406000 | D minus {20406000,y6,y22,8c840008} (83) | 4 | 4 | y6,y19,y22 | UNSAT | 1.1 | 62697 |
| a1:h00404080 | D minus {00404080,y31,y15,8c840008} (83) | 4 | 4 | y15,y19,y31 | UNSAT | 0.8 | 62705 |
| a1:h02040600 | D minus {y26,02040600,y18,8c840008} (83) | 4 | 4 | y18,y19,y26 | UNSAT | 0.6 | 62697 |
| a1:h60000020 | D minus {y30,y6,60000020,8c840008} (83) | 4 | 4 | y6,y19,y30 | UNSAT | 0.8 | 62705 |
| a1:h008c8408:ap | D minus {008c8408,y11,y27,8c840008} (83) | 4 | 4 | y11,y19,y27 | UNSAT | 0.9 | 62649 |
| a1:h8c8c0000 | D minus {y27,84848c84,8c840008,8c8c0000} (83) | 4 | 4 | y19,y27 | UNSAT | 1.2 | 62504 |
| a1:h02818100 | D minus {02818100,y9,y17,8c840008} (83) | 4 | 4 | y9,y17,y19 | UNSAT | 0.7 | 62657 |
| a1:h88980000 | D minus {y28,88980000,8c840008,y20} (83) | 4 | 4 | y19,y20,y28 | UNSAT | 0.8 | 62657 |
| a1:h00008888 | D minus {00008888,y4,y12,8c840008} (83) | 4 | 4 | y4,y12,y19 | UNSAT | 0.8 | 62665 |
| a1:h40c0c040 | D minus {y31,40c0c040,y7,8c840008} (83) | 4 | 4 | y7,y19,y31 | UNSAT | 0.8 | 62681 |
| a1:h30103010 | D minus {y13,y21,30103010,8c840008} (83) | 4 | 4 | y13,y19,y21 | UNSAT | 0.8 | 62681 |
| a1:h00028181 | D minus {00028181,y1,y25,8c840008} (83) | 4 | 4 | y1,y19,y25 | UNSAT | 1.0 | 62657 |
| a1:h00020002 | D minus {00020002,y9,y10,y18,8c840008} (82) | 5 | 5 | y9,y10,y18,y19 | UNSAT | 0.7 | 78721 |
| a1:h01010202 | D minus {01010202,81008302,y25,y17,8c840008} (82) | 5 | 5 | y17,y19,y25 | UNSAT | 2.9 | 78510 |
| a1:h00889018 | D minus {00881098,00889018,y12,y28,8c840008} (82) | 5 | 5 | y12,y19,y28 | UNSAT | 1.5 | 78490 |
| a1:h08080404:ap | D minus {08080404,y3,y27,84848c84,8c840008} (82) | 5 | 5 | y3,y19,y27 | UNSAT | 1.9 | 78480 |
| a1:h01010001 | D minus {01010001,y0,y8,y16,8c840008} (82) | 5 | 5 | y0,y8,y16,y19 | UNSAT | 0.8 | 78731 |
| a1:h04040206 | D minus {04040206,y2,y10,y18,8c840008} (82) | 5 | 5 | y2,y10,y18,y19 | UNSAT | -0.2 | 78711 |
| a1:h00203030 | D minus {00203030,y29,y5,y13,8c840008} (82) | 5 | 5 | y5,y13,y19,y29 | UNSAT | 0.8 | 78711 |
| a1:h02000200 | D minus {02000200,y1,y26,02040600,y18,8c840008} (81) | 6 | 6 | y1,y18,y19,y26 | UNSAT | 4.9 | 94696 |
| a1:h20000020 | D minus {20000020,y5,y30,y6,60000020,8c840008} (81) | 6 | 6 | y5,y6,y19,y30 | UNSAT | 5.0 | 94732 |
| a1:h008c8408 | D minus {008c8408,y11,y27,84848c84,8c840008,8c8c0000} (81) | 6 | 6 | y11,y19,y27 | UNSAT | 7.6 | 94359 |
| a1:h08080404 | D minus {08080404,y3,y27,84848c84,8c840008,8c8c0000} (81) | 6 | 6 | y3,y19,y27 | UNSAT | 8.4 | 94383 |
| a1:h40404040 | D minus {y30,40404040,y31,40c0c040,y7,8c840008} (81) | 6 | 6 | y7,y19,y30,y31 | UNSAT | 4.6 | 94672 |
| a1:h10101010 | D minus {10101010,y13,y21,30103010,8c840008,y20} (81) | 6 | 6 | y13,y19,y20,y21 | UNSAT | 4.8 | 94648 |
| a1:h00008181 | D minus {00008181,00028181,y0,y1,y25,8c840008} (81) | 6 | 6 | y0,y1,y19,y25 | UNSAT | 6.8 | 94636 |
| a1:h00000404:ap | D minus {00000404,y2,08080404,y3,y27,84848c84,8c840008} (80) | 7 | 7 | y2,y3,y19,y27 | UNSAT | 24.9 | 110647 |
| a1:h80018100:ap | D minus {y24,80018100,81008302,y25,y16,y17,8c840008} (80) | 7 | 7 | y16,y17,y19,y24,y25 | UNSAT | 10.8 | 110872 |
| a1:h00000206:ap | D minus {00000206,y26,04040206,y2,y10,y18,8c840008} (80) | 7 | 7 | y2,y10,y18,y19,y26 | UNSAT | 7.7 | 110956 |
| a1:h00001030:ap | D minus {00001030,00203030,y29,y5,y13,y21,8c840008} (80) | 7 | 7 | y5,y13,y19,y21,y29 | UNSAT | 6.8 | 110956 |
| a1:h00404000 | D minus {00404000,00404080,20406000,y6,y31,y22,y15,8c840008} (79) | 8 | 8 | y6,y15,y19,y22,y31 | UNSAT | 81.1 | 127159 |
| a1:h00202000 | D minus {00202000,00203030,y29,y5,y13,y14,y22,8c840008} (79) | 8 | 8 | y5,y13,y14,y19,y22,y29 | UNSAT | 15.0 | 127368 |
| a1:h20002000 | D minus {20002000,y13,20406000,y21,30103010,y6,y22,8c840008} (79) | 8 | 8 | y6,y13,y19,y21,y22 | UNSAT | 35.6 | 127111 |
| a1:h00040400:ap | D minus {00040400,008c8408,y26,02040600,y18,y11,y27,8c840008} (79) | 8 | 8 | y11,y18,y19,y26,y27 | UNSAT | 45.9 | 127047 |
| a1:h00000404 | D minus {00000404,y2,08080404,y3,y27,84848c84,8c840008,8c8c0000} (79) | 8 | 8 | y2,y3,y19,y27 | TIMEOUT @120s | 121.0 |  |
| a1:h88880000 | D minus {y27,84848c84,y28,88880000,88980000,8c840008,8c8c0000,y20} (79) | 8 | 8 | y19,y20,y27,y28 | UNSAT | 118.9 | 126646 |
| a1:h80018100 | D minus {01010202,y24,80018100,81008302,y25,y16,y17,8c840008} (79) | 8 | 8 | y16,y17,y19,y24,y25 | UNSAT | 77.0 | 127015 |
| a1:h00000206 | D minus {00000206,y26,02040600,04040206,y2,y10,y18,8c840008} (79) | 8 | 8 | y2,y10,y18,y19,y26 | UNSAT | 51.1 | 127111 |
| a1:h00001030 | D minus {00001030,00203030,y29,y5,y13,y21,30103010,8c840008} (79) | 8 | 8 | y5,y13,y19,y21,y29 | UNSAT | 47.0 | 127079 |
| a1:h00008880:ap | D minus {00008880,00008888,y3,y4,y12,y27,84848c84,8c840008} (79) | 8 | 8 | y3,y4,y12,y19,y27 | UNSAT | 42.9 | 126919 |
| a1:h00008081 | D minus {00008081,00008181,00028181,y0,y1,y24,y25,8c840008} (79) | 8 | 8 | y0,y1,y19,y24,y25 | UNSAT | 46.7 | 127047 |
| a1:h04040000 | D minus {04040000,04040206,y2,y10,y18,y27,84848c84,8c840008,8c8c0000} (78) | 9 | 9 | y2,y10,y18,y19,y27 | TIMEOUT @120s | 121.0 |  |
| a1:h40400040 | D minus {y30,40400040,40404040,y14,y31,40c0c040,y22,y7,8c840008} (78) | 9 | 9 | y7,y14,y19,y22,y30,y31 | TIMEOUT @120s | 120.8 |  |
| a1:h10101000:ap | D minus {10101000,10101010,y4,y12,y13,y21,30103010,8c840008,y20} (78) | 9 | 9 | y4,y12,y13,y19,y20,y21 | TIMEOUT @120s | 121.5 |  |
| a1:h00080008:ap | D minus {00080008,00881098,00888008,00889018,008c8408,y11,y12,y27,y28,8c840008} (77) | 10 | 10 | y11,y12,y19,y27,y28 | TIMEOUT @120s | 120.9 |  |
| a1:h00040400 | D minus {00040400,008c8408,y26,02040600,y18,y11,y27,84848c84,8c840008,8c8c0000} (77) | 10 | 10 | y11,y18,y19,y26,y27 | TIMEOUT @120s | 120.9 |  |
| a1:h01010000 | D minus {01010000,01010001,01010202,y0,y8,81008302,y25,y16,y17,8c840008} (77) | 10 | 10 | y0,y8,y16,y17,y19,y25 | TIMEOUT @120s | 120.8 |  |
| a1:h10101000 | D minus {00008888,10101000,10101010,y4,y12,y13,y21,30103010,8c840008,y20} (77) | 10 | 10 | y4,y12,y13,y19,y20,y21 | TIMEOUT @120s | 121.9 |  |
| a1:h00008880 | D minus {00008880,00008888,08080404,y3,y4,y12,y27,84848c84,8c840008,8c8c0000} (77) | 10 | 10 | y3,y4,y12,y19,y27 | TIMEOUT @120s | 120.7 |  |
| a1:h10001000:ap | D minus {10001000,10101000,10101010,y4,y29,y12,y13,y21,30103010,8c840008,y20} (76) | 11 | 11 | y4,y12,y13,y19,y20,y21,y29 | TIMEOUT @120s | 120.8 |  |
| a1:h08080000 | D minus {08080000,08080404,y3,y27,84848c84,y28,88880000,88980000,8c840008,8c...} (76) | 11 | 11 | y3,y19,y20,y27,y28 | TIMEOUT @120s | 120.8 |  |
| a1:h00010100:ap | D minus {00010100,00818100,02818100,y9,y24,80018100,81008302,y25,y16,y17,8c8...} (76) | 11 | 11 | y9,y16,y17,y19,y24,y25 | TIMEOUT @120s | 120.7 |  |
| a1:h00000404 | D minus {00000404,y2,08080404,y3,y27,84848c84,8c840008,8c8c0000} (79) | 8 | 8 | y2,y3,y19,y27 | UNSAT | 126.9 | 126726 |

### a2 (1 instances)

| instance | K | k | m | targets needed | result | wall s | clauses |
|---|---|---:|---:|---|---|---:|---:|
| a2:cone(h8c8c0000) | D minus {04040000,04040206,y2,y10,y18,y27,84848c84,y28,88880000,88980000,8c8...} (74) | 13 | 13 | y2,y10,y18,y19,y20,y27,y28 | TIMEOUT @120s | 120.7 |  |

### a3 (7 instances)

| instance | K | k | m | targets needed | result | wall s | clauses |
|---|---|---:|---:|---|---|---:|---:|
| a3:h008c8408,h08080404:ap | D minus {008c8408,08080404,y3,y11,y27,84848c84,8c840008} (80) | 7 | 7 | y3,y11,y19,y27 | UNSAT | 25.0 | 110563 |
| a3:h008c8408,h88980000:ap | D minus {008c8408,y11,y27,y28,88980000,8c840008,y20} (80) | 7 | 7 | y11,y19,y20,y27,y28 | UNSAT | 6.7 | 110802 |
| a3:h08080404,h88980000:ap | D minus {08080404,y3,y27,84848c84,y28,88980000,8c840008,y20} (79) | 8 | 8 | y3,y19,y20,y27,y28 | UNSAT | 59.8 | 126887 |
| a3:h00008880,h08080404:ap | D minus {00008880,00008888,08080404,y3,y4,y12,y27,84848c84,8c840008} (78) | 9 | 9 | y3,y4,y12,y19,y27 | TIMEOUT @60s | 63.0 |  |
| a3:h00008880,h84848c84:ap | D minus {00008880,00008888,y3,y4,y12,y27,84848c84,8c840008,8c8c0000} (78) | 9 | 9 | y3,y4,y12,y19,y27 | TIMEOUT @60s | 62.9 |  |
| a3:h00008880,h008c8408:ap | D minus {00008880,00008888,008c8408,y3,y11,y4,y12,y27,84848c84,8c840008} (77) | 10 | 10 | y3,y4,y11,y12,y19,y27 | TIMEOUT @60s | 62.9 |  |
| a3:h008c8408,h88880000:ap | D minus {008c8408,y11,y27,84848c84,y28,88880000,88980000,8c840008,8c8c0000,y20} (77) | 10 | 10 | y11,y19,y20,y27,y28 | TIMEOUT @60s | 62.9 |  |

### c (3 instances)

| instance | K | k | m | targets needed | result | wall s | clauses |
|---|---|---:|---:|---|---|---:|---:|
| c:b75_most_exact | b75_most_exact minus {-} (75) | 0 | 12 | y11,y12,y19,y27,y28 | TIMEOUT @900s | 873.7 |  |
| c:b76_nested | b76_nested minus {-} (76) | 0 | 11 | y11,y12,y19,y27,y28 | TIMEOUT @900s | 872.3 |  |
| c:b76_most_exact | b76_most_exact minus {-} (76) | 0 | 11 | y3,y11,y19,y26,y27 | TIMEOUT @900s | 871.8 |  |

Total: 81 instances, 5858 s solver wall; {'UNSAT': 60, 'TIMEOUT': 21}

## 7. Conclusion

No 87 was found; FOUND_87 does not exist and found/ is empty.  What the UNSATs exclude (each one exactly: no
circuit of <= 87 gates, at any depth, whose value set contains the stated K):

(a) Candidate D.
- y19 is not one XOR of the 86 live values of D and the inputs (I(D minus r, 1)); the archive completion
  r ^ x11 is forced to be an 88 as long as all 86 live values are kept.
- One-helper windows of D with k <= 8 are excluded: for 37 of the 55 live helpers h, no 87 contains
  D minus closure({h, r}) under the wiring closure (k = 4-8); for 2 more (00040400, 00008880) the any-pair
  window (k = 8) is excluded while the wiring window (k = 10) timed out.  This covers the helper chain of r down
  to 88880000 (8c8c0000 k = 4, 88880000 k = 8), the y27 side (008c8408, 08080404, 84848c84) and every helper
  of the other bytes whose window has k <= 8.  (Helpers with identical windows were run once; the 37 count every
  helper whose window is covered.)
- Three two-helper windows in the y19 neighbourhood (k = 7-8) are excluded.
- Open (TIMEOUT at 120 s; 60 s for pairs): the 16 helpers whose window has k >= 9, which are exactly the
  input-pair gates and the depth-1/2 helpers that r and y27 share, plus the hub pairs of the other bytes:
  04040000 = x18^x26 (k = 9), 40400040 (9), 10101000 (9/10), 00080008 = x3^x19 (any-pair 10, wiring 12),
  01010000 (10), 00888008 (10/12), 08080000 = x19^x27 (11), 10001000, 00010100, 00818100 (11/12), 40400000 (12),
  00000202, 00001010 (12/13), and the three never run: 80800000 = x23^x31 (16/17), 00008080 (19/22), 00808000
  (23/28); also the cone of the parent 8c8c0000 (k = 13), four pairs with k = 9-10, and the two large cones.
  Note r = (x3^x19)^(x18^x26)^(x19^x27)^
  (x23^x31), i.e. x19 cancels inside r: D pays its y19 side through four input pairs that are shared with y27
  and y3/y11.  A rewiring of D into an 87, if one exists, is not a one-helper change with k <= 8 and not one
  of the three tested pairs: it must either change one of those shared pair gates / larger windows (the open
  list) or change two or more helpers jointly (only 7 pairs were tried).  The instances for the 600 s pass: a1:h04040000
  (k = 9), a1:h00080008:ap (k = 10), a1:h08080000 (k = 11), a2:cone(h8c8c0000) (k = 13), then the a4 list.
  Expected cost ~1 core-hour at 600 s, more for the k >= 16 windows (the sat/ campaign never finished k >= 12).

(b) The 18-pair foundation state.  All 15 runs UNSAT (one needed the 600 s retry; it finished in 68 s under
lighter load).  No 87 contains the 84 values (I(K84, 3)); and for every window of r <= 6 values around y9, y10,
y18 built from single or paired non-target ancestors (00000206, 00040400, 00818100, 02000200, 02040600,
02818100, 04040000, 04040206; any-pair and wiring closures with k <= 6), no 87 contains the remaining 78-82
values.  This replaces the checkpoint statement "only one-gate and hand-picked two-gate swaps tried" by an
exact statement: within the 18-pair foundation, no completion to 87 exists that keeps the rich interior minus
any such window of up to 6 values; a completion must rebuild more than 6 values of the rich middle (or drop
pairs).  The 84-minus-window instances with larger r were not generated (brief: r <= 6).

(c) A75 / A76.  I(A75, 12), I(A76_nested, 11), I(A76_most_exact, 11): all TIMEOUT at 900 s (~872 s wall each).
As the arch87 report expected: 11-12 free 32-bit values over a 75-value pool is beyond the plain encoding;
these say nothing.

Soundness notes.  Instances were built by the same closure code as sat/run_scopes.py (window = upward closure
under the wiring, dead helpers, then any-pair split-closure fix); every K was asserted split-closed before
encoding; m = |W| for D (and 3 + r for the 18-pair state) so that |K| + m = 87 and the missing output(s) are
required among the new gates.  The decoder/verifier path (sat87.decode, check_circuit, write_circ.py with
circuits/check.py and the unit-vector evaluation) was wired in run.py but never exercised, as nothing was SAT.
Wall times include the load of three other campaigns running solver children at the same time.
