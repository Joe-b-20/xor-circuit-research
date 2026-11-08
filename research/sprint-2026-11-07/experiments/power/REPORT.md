# power: slack-1 power control for the sprint's SAT window refutations (F13, F23)

Folder `~/xs-campaigns/2026-11-07-sprint/power/`, 2026-11-07 19:10-21:10 (WSL clock), one solver child at a
time under `nice -n 8` while 16 other solver children and the hunt were running. Total compute ~115 min
(part 1 analysis 11 min, P2 anchors 3 min, generator-window analysis 6 min, solver 96 min). Nothing outside
this folder was written; `sat/` was only read (its `sat87.py` encoder and `solve_child.py` were reused
unchanged, with the request file in this folder). Tags: **[measured]** computed here (script named);
**[proved]** argument given; **[archive]** owner's label; **[guess]** interpretation.

Files: `anchors.py` (anchor set, sprint windows, containment -> `anchors.json`, `windows.json`, `pairs.json`,
`part1.txt`), `anchors_p2.py` (the six 90@4 states carrying the 89@4's first layer, from q89check), `part3.py` /
`part3b.py` (window size the generators would need -> `part3.txt`, `part3b.txt`), `run_power.py` (the solver run
-> `results.jsonl`, `run.log`), `summarize.py` -> `summary.md` (the tables appended below),
`found_96_from_97at3.json` (the one unexpected SAT, re-checked).

## 0. Result in one paragraph

The question was: if a circuit DOES have a smaller circuit nearby, do the sprint's window families (one-seed
windows k <= 10, output blocks k <= 12, two-seed windows k <= 9, instance I(K, k-1)) find it? **No.** On 28
anchors one gate above a known smaller circuit (25 hunt 89-states whose chain reached 88 within the next 30 s
sample, the repo 89@4 vs the 257 88s its seeded workers reached, the July 91@4 vs the 89@4 family it descended
to, NIST's 90@4 vs every known 88/89), **not one of the 41,057 windows the sprint's generators produce has a
kept set K contained in the known improvement** [measured, `anchors.py`], and not one is contained in any of the
22,489 known 88 circuits either. So no window of these families could have returned SAT for those improvements;
the solver run confirms it on the 1,053 one-seed windows k <= 8 that fit the budget (1,052 UNSAT, 0 timeouts;
the one SAT is on the 97@3 anchor, section 4). Over all 1,380 logged 89->88 transitions of the hunt, the
improvement differs from the anchor in **5-47 helper values (k_needed, median 17 for descents)**, and the
smallest value-set window that contains it has **k_min = 13-84, median 42** (descents; 37 for plateau
excursions) [measured, `part3b.py`] -- the archive's "mask distance median 42" [archive] reproduced on the
sprint's own data with the sprint's own instrument. The sprint's hardest finished instance is k = 12. **F13 and
F23 are correct theorems about local rigidity that carry essentially no information about 87: the likelihood
ratio P(all UNSAT | an 87 exists at the distances real improvements have) / P(all UNSAT | no 87) is 1.00-1.11
(0 hits in 28 anchors; one-sided 95 % bound on the hit rate 0.10).** The one positive: on the 97@3 (a circuit
with 9 gates of slack) a k = 4 one-seed window IS SAT and yields a new 96@4 -- the instrument does see
improvements when they are local; around the 88s and the near-optimal 89s they are not.

## 1. Instrument, anchors, and what "contained" means

Instrument (unchanged from `sat/sat87.py`, F13): for an anchor circuit S (value set, |S| = G) and a removed set W
(k = |W|) with K = S \ W split-closed, I(K, k-1) is SAT iff some split-closed value set containing K and all 32
targets has <= G - 1 values [proved in sat87]. Windows come from `sat/run_scopes.scopes` exactly as the batch
drivers call it: family A (one seed value: upward closure under the any-pair wiring, dead cone, closure repair),
family C (byte and half-byte output blocks), family B (two seeds). Filters as in `batch_driver.py` /
`batch2_driver.py`: A k <= 10, C k <= 12, B k <= 9; limits 60 s (A k <= 8), 900 s (A k = 9-10, B), 1800/900 s (C,
free <= 3 / > 3). The sprint's instance set never includes k = 1 (m = 0, trivially UNSAT: the removed value is an
output with no replacement); the first solver pass here recorded 808 such windows as ERROR (pysat rejects an
empty clause) -- they are trivially UNSAT and are excluded from every count below.

Containment [proved]: if K is contained in a known circuit V with |V| <= G - 1, then I(K, k-1) is SAT (the claim's
(<=) direction with that V). Conversely, if no known smaller circuit contains K, the window can only succeed by
finding an UNKNOWN smaller circuit. So "contained" is the condition under which the window is guaranteed to find
the known improvement; the containment rate is the power of the window family against the improvements we know.
With H(S) the helper set of S and M = H(S) \ H(V) (the anchor's values the improvement lacks), K is a subset of V
iff M is a subset of W; the smallest conceivable window is M itself plus what K then cannot compute (`part3b`:
k_min); the sprint's generator seeded with all of M gives k_gen >= k_min (`part3`). Rotations: a byte-rotated
circuit is a circuit, so containment and distances were taken over the 4 rotations of the improvement
(identity frame reported too).

Anchors [measured, `anchors.py`]:
- **hunt89 (25)**: chains delimited exactly as `graph/graph.py` (restart events in each worker's `events.jsonl`,
  chain index = restarts with t <= sample t); samples from `hunt/samples.jsonl` (arms A, B), `samplesC` (C),
  `samplesD` (D0, D4, DN); 432 chains, **1,380 logged 89->88 transitions** (234 "descents" = first arrival at 88 in
  the chain, 1,146 "excursions" = 88 -> 89 -> 88 plateau hops). Anchor = the last 89 sample before the 88, truth =
  that 88 (gap 29-33 s wall in all chosen pairs; the sampler polls every 30 s, so the 89 is the state the walk
  held one poll before the 88, not necessarily its direct parent -- the direct parent can only be closer in
  value-set terms or equal). Chosen: 20 descents round-robin over arms (tightest gap first, one per chain,
  distinct states) + 5 excursions.
- **repo89@4**: improvement = nearest (min k_needed over members and rotations) of the 257 distinct 88s the four
  mc87 `from89` workers reached from it (F15: "keeping 17-19 of its 26 first-layer pairs"; here k_needed = 19-33,
  symmetric difference >= 37). Against all 22,489 known 88s the nearest is the same (k_needed 19).
- **july91@4** (`2026-10-31-adopt/seeds/mc-july-g91-d4.json`): improvement = nearest of the 90 recorded 89@4
  states (the family v8 reached from it in 914 s): k_needed 20-21 for all 90, symdiff 38.
- **nist90@4** (`mc-nist-g90-d4.json`): no logged descent exists (F15); improvement = nearest of all known 88 and
  89@4 circuits: k_needed 13 (one kste 88), symdiff 24.
- **repo97@3**: improvement = nearest of all known 88, 89@4, 90@4 (5,798) and the July 91@4: k_needed 34.
- **p2_90@4 (6)**: the q89check population of 90@4 states carrying the 89@4's exact first layer, the six nearest
  to a recorded 89@4 (k_needed 1, 2, 2, 3, 3, 3; three of them have a direct remove1 step into L0). These are
  distance-1-to-3 anchors: the trivial end of the scale, used as the solver's positive control.

## 2. Containment [measured, `anchors.py`, `anchors_p2.py`]

| anchor group | anchors | windows A / C / B | K contained in the known improvement | K contained in ANY known smaller circuit |
|---|---:|---|---:|---:|
| hunt89 descents | 20 | 1,300 / 174 / 25,791 | **0** | 0 |
| hunt89 excursions | 5 | 313 / 42 / 5,719 | **0** | 0 |
| repo89@4, july91@4, nist90@4, repo97@3 | 4 | 294 / 44 / 7,380 | **0** | 0 |
| **all real anchors** | **29** | **41,057 windows** | **0 (0.0 %)** | **0** |
| p2_90@4 (distance 1-3) | 6 | 459 / 72 / 12,420 | 244 (190 + 51 + 1 + 0 + 0 + 2) | 244 |

"Any known smaller circuit" = the 22,489 distinct known 88s (4,314 hunt sample states, 712 mc87 records, 17,462
kste value sets, the repo 88@5), plus the 90 recorded 89@4 states for the 90/91 anchors, plus the 5,798 90@4
states and the July 91@4 for the 97@3, all four rotations each. For the 25 hunt anchors, the number of known
88s whose missing set M has |M| <= 12 (a necessary condition for any k <= 12 window) is 0-33 per anchor; even
those are never contained because the generator's W never covers M (next section).

Why not (structural, [measured]): a one-seed window is the upward closure of one value; the values an improvement
drops are spread over the circuit (several first-layer pairs plus their consumers), so the set M that must be
removed is not the closure of any one or two seeds, and its own closure is large: for the 29 real anchors k_gen =
25-66 with 10-25 outputs inside (`part3.txt`), k_min = 23-64 (`part3b.txt`). The smallest case among the 29 is
hunt89:sampleD:5320 (k_needed 7 -> k_min 23, k_gen 25, 10 outputs removed).

## 3. Distance distribution, all 1,380 hunt transitions [measured, `part1.txt`, `part3*.txt`]

| statistic (helpers, identity frame; rotation minimum identical for every pair) | descents (234) | excursions (1,146) |
|---|---|---|
| k_needed = size of H(89) minus H(88) (values any containing window must remove) | min 6, q1 13, **med 17**, q3 22, max 47 | min 5, q1 11, med 14, q3 17, max 35 |
| symmetric difference of H(89) and H(88) | min 11, q1 25, **med 33**, q3 43, max 93 | min 9, q1 21, med 27, q3 33, max 69 |
| k_min: smallest split-closed window containing the improvement (`ANYPAIR`) | min 16, q1 34, **med 42**, q3 51, max 84 | min 13, q1 31, med 37, q3 43, max 72 |
| outputs inside that minimal window | min 6, med 18, max 32 | min 6, med 16, max 29 |
| k_gen: the sprint generator seeded with all of M | min 16, q1 36, med 45, q3 55, max 89 | min 13, q1 33, med 39, q3 47, max 78 |
| pairs with k_min <= 12 (reachable by the sprint's families) | **0** | **0** |

k_needed histogram (all 1,380; 30 = >= 30): 5:4, 6:17, 7:20, 8:49, 9:65, 10:100, 11:101, 12:109, 13:113, 14:121,
15:117, 16:95, 17:95, 18:70, 19:66, 20:48, 21:39, 22:32, 23:24, 24:19, 25:13, 26:10, 27:10, 28:6, 29:10, >=30:27.
k_min histogram: 13:2, 14:2, 15:1, 16:3, 17:3, 18:5, 19:6, 20:12, 21:12, 22:12, 23:21, 24:19, 25:27, 26:26, 27:43,
28:32, 29:32, >=30:1,122. Note that k_needed <= 12 holds for 465 of 1,380 pairs (34 %), yet k_min <= 12 for none:
the kept set S \ M is never split-closed by itself -- removing the dropped helpers strands their consumers, and
the closure repair pulls in 10-30 more values, most of them outputs. The archive's control statement "mask
distance min 3, median 42, max 48" [archive] is matched here by k_min med 42 (descents) on independent data.

For comparison the sprint's refutations [measured from `sat/results*.jsonl`, distinct (circuit, W)]: 4,327
instances on 37 circuits, 4,271 UNSAT, 56 timeouts, k histogram of the UNSATs 2:48, 3:121, 4:891, 5:688, 6:623,
7:580, 8:621, 9:620, 10:58, 11:12, 12:9; nothing above k = 12 finished (timeouts at k = 10-25). The window size
needed to contain a real improvement starts at k_min = 13 and is typically 37-42 with 16-18 outputs removed --
exactly the band (k = 21-32 "mobile parts", F23) where the encoding times out.

## 4. Solver run [measured, `run_power.py`, `results.jsonl`, `run.log`]

Budget 85 + 12 min, one CaDiCaL child at a time, nice 8, sprint limits. Priority: P0 windows whose K is contained
in the known improvement (positive control; only the six p2 anchors have any), then one-seed windows k <= 8
round-robin over anchors by k, then blocks, then A k = 9-10, then two-seed windows. The P0 class took 81.5 of the
first 85 minutes (244 instances; SAT at k = 8-9 cost 40-50 s each; a planning error -- 30 would have sufficed),
so the real anchors got the one-seed windows k <= 8 only: 1,053 of their 1,157 such windows (91 %; 18 anchors
complete to k = 8, 8 to k = 7, 3 to k = 6). Blocks (k <= 12), A k = 9-10 and two-seed windows were not run for the
real anchors; the containment result covers them (none contains a known improvement). Totals: 2,321 rows, 245 SAT,
1,268 UNSAT, 0 timeouts (plus 808 k = 1 rows, trivial, excluded). UNSAT medians: k = 4: 0.2 s, 6: 0.8 s, 8: 2.6 s
(max 19 s) -- consistent with F13's frontier.

| class | anchors | instances | SAT | UNSAT |
|---|---:|---:|---:|---:|
| P0: K contained in the known improvement (p2 anchors, distance 1-3) | 3 | 244 | **244** | 0 |
| real anchors (hunt89 x 25, repo89@4, july91@4, nist90@4), one-seed k = 2-8 | 28 | 1,017 | **0** | 1,017 |
| repo97@3, one-seed k = 2-6 | 1 | 36 | **1** (k = 4 -> a 96@4) | 35 |
| p2 anchors, non-contained windows k = 2-7 | 6 | 216 | 0 | 216 |

Positive control: all 244 contained windows are SAT; 147 decode to exactly the known 89@4 (`found_equals_truth`),
97 to another 89-gate circuit (other family members or new ones); every decoded circuit re-checks with
`sat87.check_circuit` (independent of the encoder). So when the window contains the improvement the solver finds
it in 1-50 s; the zero hit rate on the real anchors is a containment failure, not a solver failure.

The one unexpected SAT: anchor repo97@3, window `A:v=00080c00` (W = {00080c00, 08000004, 08008084, 08088c84}, k = 4,
one output removed): the solver returns 3 new values and a 96-gate depth-4 circuit (re-checked independently:
96 gates, depth 4, 96 distinct values, all 32 targets; `found_96_from_97at3.json`). It is a NEW circuit, not the
known 90@4/89@4/88s (33 values outside the nearest known), and it shows what the instrument can do: a circuit
with real local slack (the depth-3 97 pays 9 gates for depth) has k = 4 improvements and the windows see them at
once. The 88s (F13: 4,271 UNSAT) and the near-optimal 89s here have none.

Hit rate: **0 of 28** anchors one gate above a known 88/89-level improvement (1 of 29 counting the 97@3, whose hit
is a different, local kind of improvement). One-sided 95 % bound on the per-anchor hit rate: p <= 1 - 0.05^(1/28)
= 0.10.

## 5. What F13/F23's refutations say about 87 [derived from the above]

- What they prove (unchanged): no <= 87 circuit contains any of the 4,271 kept sets (76-86 values each) of 37 88
  circuits; none is a one-factor or <= 3-free two-factor rewrite of four 88 plateaus (F23). Correct theorems.
- What they would need to say something about 87's existence: that an 87, if it exists, would be CONTAINED in
  such a window of some 88. Every improvement we can observe (1,380 transitions 89 -> 88, the 89@4 from the
  91@4, the 88s from the 89@4) sits at k_needed 5-47 (median 17) and k_min 13-84 (median 42) from the circuit one
  gate above it; the sprint's windows stop at k = 12; 0 of 41,057 windows around 29 anchors contain the
  improvement. If 88 -> 87 behaves like 89 -> 88 (the only calibration available; same map, same move class,
  same instrument), the probability that any F13/F23 window contains an 87 is ~0 (point estimate 0/28 anchors,
  0/1,380 pairs with k_min <= 12).
- Likelihood ratio: with P(all UNSAT | no 87) = 1 and P(all UNSAT | an 87 exists at such distances) = 1 - p,
  **LR = 1 / (1 - p) in [1.00, 1.11]** (p <= 0.10 at 95 %). F13/F23 move the odds on 87 by at most ~10 %, and the
  point estimate is "not at all" -- the same verdict the archive's fence_sat control gave ("likelihood ratio ~
  1.00" [archive]).
- Is the control clean? Caveats, in order of weight: (i) the anchors' improvements are what the walk produced
  (remove1/expand/LNS descents), so the distances describe walk-reachable improvements; an 87 reached by another
  route could in principle be closer to some 88 -- but the 97@3 hit shows the windows DO detect close
  improvements where they exist, and the archive's independent control on 89-97-gate circuits found none at
  k < 25 either; (ii) the 89 anchor is the last 30 s sample before the 88, not the direct parent: the direct
  parent is at least as close, so the distances are upper bounds on the parent's by at most the within-poll
  drift, and the minimum of k_min over 1,380 pairs is already 13; (iii) the solver stage covered only one-seed
  k <= 8 of the real anchors -- irrelevant to the conclusion, which rests on containment (exhaustive over all
  three families) and is confirmed where the solver ran (0 SAT in 1,017).
- Window sizes that would be needed: k_min >= 13 at the very least, typically 37-42 with 16-18 of the 32 outputs
  inside the window, i.e. "rebuild half the output layer and a quarter of the helpers" -- the F23 mobile-part band
  (k = 21-32) that times out, and beyond. The sprint's encoding has no operating point there (F13: hardness
  tracks the free values, 10-40 here). Power requires a different formulation (arch87's R1/R2: large windows with
  a pool, or union_sat-type pool instances, the archive's only control-passing negative), not more k <= 12
  windows on more 88s.

## 6. Findings / rejected / open

- **P1 [measured]**: 0 of 41,057 sprint windows around 29 anchors one gate above a known smaller circuit contain
  the improvement (0 contain any of 22,489 known 88s); hit rate 0/28 on the solver's one-seed k <= 8 windows.
- **P2 [measured]**: improvements sit at k_needed med 17 (descents) and k_min med 42; k_min >= 13 in every one of
  1,380 observed 89 -> 88 transitions; the sprint's frontier is k = 12. The archive's median-42 control is
  reproduced on independent data.
- **P3 [measured]**: the instrument has power where improvements are local: 244/244 SAT on contained windows of
  distance-1-3 90@4 anchors; a k = 4 window of the 97@3 produces a new 96@4.
- **P4 [derived]**: LR of F13/F23 for 87 is 1.00-1.11; the refutations are rigidity certificates, not evidence
  against an 87.
- Rejected: "a slack-1 control would show the windows find improvements when they exist" -- it does not, except
  on a slack-rich 97.
- Open: blocks, A k = 9-10 and two-seed windows were not solver-run on the real anchors (containment says they
  cannot be SAT via a known improvement; an unknown one is not excluded); the 96@4 from the 97@3 was not
  verified with the repo's `check.py` (only with `sat87.check_circuit`); whether 88 -> 87 distances resemble
  89 -> 88 distances is an assumption, the only calibration available.

Appendix: the anchor table and run tables (`summary.md`) follow. Columns: need = k_needed (identity frame),
symdiff = size of the symmetric difference of the helper sets, k_gen = the sprint generator's window seeded with
the whole missing set (part3), k_min = minimal any-pair window (part3b); "run" counts SAT/UNSAT/TIMEOUT per
family; the 808 ERROR rows in "Run totals" are the k = 1 (m = 0) windows of the first pass, trivially UNSAT, in
no other count.

## Anchor table

| anchor | kind | G | improvement | need | symdiff | k_gen | k_min | windows A/C/B (k<=10/12/9) | contained | run: SAT/UNSAT/TO (A, C, B) | SAT found |
|---|---|---:|---|---:|---:|---:|---:|---|---:|---|---|
| hunt89:sampleA:232 | hunt-descent | 89 | next 88 in chain (sampleA:240, +30.0s) | 19 | 37 | 45 | 44 | 62/9/1071 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleA:2094 | hunt-descent | 89 | next 88 in chain (sampleA:2102, +30.0s) | 13 | 25 | 43 | 42 | 68/9/1464 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleC:1035 | hunt-descent | 89 | next 88 in chain (sampleC:1040, +30.0s) | 10 | 19 | 32 | 28 | 66/9/1373 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:6105 | hunt-descent | 89 | next 88 in chain (sampleD:6113, +29.4s) | 22 | 43 | 53 | 47 | 63/7/1167 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:5612 | hunt-descent | 89 | next 88 in chain (sampleD:5622, +29.5s) | 34 | 67 | 66 | 64 | 64/11/1190 | 0 | 0/32/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:6119 | hunt-descent | 89 | next 88 in chain (sampleD:6125, +29.4s) | 16 | 31 | 37 | 36 | 65/10/1266 | 0 | 0/35/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleA:1198 | hunt-descent | 89 | next 88 in chain (sampleA:1204, +32.9s) | 17 | 33 | 47 | 42 | 69/10/1462 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleA:1539 | hunt-descent | 89 | next 88 in chain (sampleA:1545, +32.9s) | 23 | 45 | 50 | 49 | 67/9/1362 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleC:1037 | hunt-descent | 89 | next 88 in chain (sampleC:1042, +30.0s) | 15 | 29 | 35 | 35 | 64/8/1361 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:5931 | hunt-descent | 89 | next 88 in chain (sampleD:5941, +29.4s) | 26 | 51 | 61 | 58 | 65/9/1306 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:5577 | hunt-descent | 89 | next 88 in chain (sampleD:5582, +29.5s) | 12 | 23 | 49 | 43 | 63/8/1239 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:5320 | hunt-descent | 89 | next 88 in chain (sampleD:5329, +29.4s) | 7 | 13 | 25 | 23 | 64/8/1312 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleA:263 | hunt-descent | 89 | next 88 in chain (sampleA:272, +32.9s) | 9 | 17 | 35 | 32 | 68/11/1429 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleA:191 | hunt-descent | 89 | next 88 in chain (sampleA:196, +32.9s) | 10 | 19 | 28 | 24 | 66/8/1238 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleC:1222 | hunt-descent | 89 | next 88 in chain (sampleC:1228, +32.9s) | 19 | 37 | 52 | 46 | 60/7/1132 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:5806 | hunt-descent | 89 | next 88 in chain (sampleD:5815, +29.5s) | 10 | 19 | 28 | 24 | 67/9/1283 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:4592 | hunt-descent | 89 | next 88 in chain (sampleD:4600, +30.0s) | 21 | 41 | 54 | 53 | 65/9/1305 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:5707 | hunt-descent | 89 | next 88 in chain (sampleD:5715, +29.4s) | 13 | 25 | 34 | 30 | 61/5/1079 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleA:1784 | hunt-descent | 89 | next 88 in chain (sampleA:1791, +32.9s) | 13 | 25 | 32 | 32 | 69/9/1407 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleA:994 | hunt-descent | 89 | next 88 in chain (sampleA:1001, +32.9s) | 20 | 39 | 44 | 42 | 64/9/1345 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:6078 | hunt-excursion | 89 | next 88 in chain (sampleD:6087, +29.1s) | 12 | 23 | 45 | 36 | 63/8/1183 | 0 | 0/33/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:6126 | hunt-excursion | 89 | next 88 in chain (sampleD:6134, +29.4s) | 21 | 41 | 59 | 53 | 63/9/1096 | 0 | 0/35/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:6110 | hunt-excursion | 89 | next 88 in chain (sampleD:6118, +29.4s) | 10 | 19 | 38 | 31 | 63/9/1197 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:5968 | hunt-excursion | 89 | next 88 in chain (sampleD:5977, +29.4s) | 10 | 19 | 33 | 30 | 60/8/1100 | 0 | 0/34/0, 0/0/0, 0/0/0 | - |
| hunt89:sampleD:6093 | hunt-excursion | 89 | next 88 in chain (sampleD:6100, +29.4s) | 18 | 35 | 49 | 46 | 64/8/1143 | 0 | 0/37/0, 0/0/0, 0/0/0 | - |
| repo89@4 | repo | 89 | nearest of 257: from89:b89c7d62c645c41f | 20 | 39 | 43 | 42 | 78/12/2200 | 0 | 0/36/0, 0/0/0, 0/0/0 | - |
| july91@4 | seed | 91 | nearest of 90: fam89:4c97027faa4bc076 | 25 | 48 | 54 | 50 | 74/12/1847 | 0 | 0/36/0, 0/0/0, 0/0/0 | - |
| nist90@4 | seed | 90 | nearest of 22579: kste:2291 | 22 | 42 | 44 | 41 | 74/12/1870 | 0 | 0/36/0, 0/0/0, 0/0/0 | - |
| repo97@3 | repo | 97 | nearest of 28378: st90:a768b74061f331b1 | 34 | 61 | 61 | 60 | 68/8/1463 | 0 | 1/35/0, 0/0/0, 0/0/0 | {'other<=G-1': 1} |
| p2_90@4:af207a616d2e3f02 | p2 | 90 | nearest 89@4 (downs_into_L0=1, bfs_hit=L0, in_B1=False) | 1 | 1 | - | 1 | 77/12/2128 | 190 | 4/36/0, 2/0/0, 184/0/0 | {'=truth': 126, 'other<=G-1': 64} |
| p2_90@4:552d7aab3956f9e7 | p2 | 90 | nearest 89@4 (downs_into_L0=2, bfs_hit=L0, in_B1=False) | 2 | 3 | - | 5 | 76/12/2127 | 51 | 2/36/0, 0/0/0, 49/0/0 | {'other<=G-1': 32, '=truth': 19} |
| p2_90@4:347ce390b48ffb42 | p2 | 90 | nearest 89@4 (downs_into_L0=2, bfs_hit=L0, in_B1=True) | 2 | 3 | - | 8 | 78/12/2163 | 1 | 1/36/0, 0/0/0, 0/0/0 | {'other<=G-1': 1} |
| p2_90@4:8b409703a5ba2c23 | p2 | 90 | nearest 89@4 (downs_into_L0=0, bfs_hit=L0, in_B1=False) | 3 | 5 | - | 8 | 76/12/2006 | 0 | 0/36/0, 0/0/0, 0/0/0 | - |
| p2_90@4:8d5d371c8f503ffb | p2 | 90 | nearest 89@4 (downs_into_L0=0, bfs_hit=L0, in_B1=False) | 3 | 5 | - | 8 | 76/12/2006 | 0 | 0/36/0, 0/0/0, 0/0/0 | - |
| p2_90@4:c2295c93e3e5774e | p2 | 90 | nearest 89@4 (downs_into_L0=0, bfs_hit=L0, in_B1=False) | 3 | 5 | - | 6 | 76/12/1990 | 2 | 0/36/0, 0/0/0, 2/0/0 | {'=truth': 2} |

## Run totals

instances run: 2321; SAT 245, UNSAT 1268, TIMEOUT 0, ERROR 808; solver wall 96.4 min; budget-truncated instances: 382

| class | instances | SAT | UNSAT | TIMEOUT |
|---|---:|---:|---:|---:|
| P0 kept set contained in the known improvement | 244 | 244 | 0 | 0 |
| P1 contained in another known smaller circuit | 0 | 0 | 0 | 0 |
| P2 one-seed windows k<=8 (60 s) | 2077 | 1 | 1268 | 0 |
| P3 output blocks k<=12 (1800/900 s) | 0 | 0 | 0 | 0 |
| P4 one-seed windows k=9-10 (900 s) | 0 | 0 | 0 | 0 |
| P5 two-seed windows k<=9 (900 s) | 0 | 0 | 0 | 0 |

per anchor kind (non-contained windows only):

| kind | anchors | instances | SAT | UNSAT | TIMEOUT | k range | anchors with a SAT |
|---|---:|---:|---:|---:|---:|---|---:|
| hunt-descent | 20 | 1154 | 0 | 733 | 0 | 1-8 | 0 |
| hunt-excursion | 5 | 282 | 0 | 176 | 0 | 1-8 | 0 |
| repo | 2 | 120 | 1 | 71 | 0 | 1-6 | 1 |
| seed | 2 | 125 | 0 | 72 | 0 | 1-7 | 0 |
| p2 | 6 | 396 | 0 | 216 | 0 | 1-7 | 0 |

k histogram of the run (all classes): [(1, 808), (2, 154), (3, 422), (4, 232), (5, 228), (6, 167), (7, 164), (8, 115), (9, 31)]

SAT instances not contained in the known improvement (unexpected finds): 1
   repo97@3 A:v=00080c00 k=4 found [96, 4, 96] eq_truth False new outside truth 33

solve-time medians (UNSAT) per (fam, k):
  A k=2: n=153 med=0.1s max=0.1s
  A k=3: n=392 med=0.1s max=0.2s
  A k=4: n=231 med=0.2s max=0.3s
  A k=5: n=210 med=0.3s max=0.7s
  A k=6: n=106 med=0.8s max=2.9s
  A k=7: n=126 med=1.4s max=8.3s
  A k=8: n=50 med=2.6s max=19.4s
