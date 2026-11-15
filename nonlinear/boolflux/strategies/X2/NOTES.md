# X2: goal-directed hub scheduler (2026-11-15)

Brief: BRIEF-COMMON.md + BRIEF-ADDENDUM-0135.md (~/xs-campaigns/2026-11-15-study/). CPU 11. Data in
~/xs-campaigns/2026-11-15-study/X2/. Code: hub/goals.py, hub/scheduler_goal.py (new files; no shared module
edited), strategies/X2/ (mksnap.sh, arm.sh, ab_compare.py, runs_table.py).

## Design

### Goal list and value (hub/goals.py)
- GOALS = the user's ordered list A-G as caps (A, AD, G, GD), None = free. Meets = every coordinate <= cap.
- Distance of a circuit m to goal g [design choice, H]: deficit d = max(0, m - cap) per coordinate;
  key = (dA, dAD, dG + dGD, dG), lexicographic. An AND over the cap outranks any AND-depth excess, which
  outranks any gate/gate-depth excess; G and GD excess are summed (both must reach 0; on the A28 fronts one GD
  level costs ~1-3 gates), ties broken towards lower G. scalar = 1000 dA + 100 dAD + dG + dGD (same order while
  dG + dGD < 100).
- State value of an archive = per goal (in priority order) the min key over all records; states compare
  lexicographically over the goals (state_key), so progress on a higher goal outranks anything on a lower one.
- Stepping stones (credited, counted): a circuit violating exactly one coordinate of g, by at most
  A 1 / AD 1 / G 15 / GD 4 (e.g. 28-AND, AD4, GD <= 22, G <= 145 for goal B; every 28-AND circuit for goal A).
  Note: a dominated circuit never has a smaller key than its dominator (the deficit is monotone), so stepping
  stones matter only as start points (structural diversity), not as distance.

Baseline (snap0 = long archive at 01:38 UTC, 2311 records, front 85):
| goal | best | key | stones |
|---|---|---|---|
| A <= 27 | 28/4/131/23 | (1,0,0,0) | 84 |
| B 28/4/130/22 | 28/4/131/23 | (0,0,2,1) | 23 |
| C 28/5/127/19 | 28/5/128/20 | (0,0,2,1) | 18 |
| D 32/4/116/19 | 32/4/116/20 | (0,0,1,0) | 36 |
| E 32/6/102/31 | 32/5/104/29 | (0,0,2,2) | 98 |
| F 35/3/138/26 | 35/3/139/27 | (0,0,2,1) | 173 |
| G 44/4/140/11 | 34/4/134/13 | (0,0,2,0) | 53 |
(The archive has points the brief did not list as "best now": 28/5/128/20 for C, 35/3/139/27 for F,
34/4/134/13 for G.)

### Scheduler (hub/scheduler_goal.py, subclass of scheduler.Scheduler)
- Goal per job: stride scheduling on CPU seconds (smallest used/share); default shares A .10, B .20, C .15,
  D .15, E .10, F .10, G .10, plus 'generic' .10 = the original bandit choice unchanged. Met goals drop out
  unless keep_met.
- Operator per goal: epsilon-greedy (eps 0.25) on (reward + 0.5)/(CPU s + 120) over the last 40 jobs of that
  (goal, op); reward = 5 x step_gain of the goal's archive best + per admitted candidate step_gain(target key ->
  candidate key) + 0.05 per stepping stone; step_gain 8 (dA) / 4 (dAD) / 1 per unit of dG + dGD (max 4) /
  0.25 (G-for-GD trade). Ops: A {pull, polish, join, gen_skel}; B-G {polish, pull, trb, join, osc, gen_skel}.
- Target per goal: records with scalar <= best + 10 or stepping stones, nearest 40 (400 for A); weight
  exp(-(s - best)/3)/(1 + attempts(goal, op, target)).
- Caps per job: polish/osc get the goal's caps (outside -> kernel repair); pull = the hub's pull with the
  goal caps as base (it lowers one cap relative to the target itself); gpull (op_polish.py) steps one coordinate toward
  the goal (first violated of A, AD, GD by 1, GD by 1-2; satisfied coordinates at the goal cap; if only G is
  violated GD is capped 1-2 below the target's); trb/join/gen_skel unchanged. Objective always a,ad,cost,gd.
- Any admitted circuit meeting a goal: found/ NCFF + JSON sidecar, aes_check.py, GOAL-MET event, GOALS-MET.txt.

## Log
- 01:38 snapshot snap0 (T = 1794706696). 01:43 smoke1 (4 min, short op budgets) on CPU 11.
- 01:44 smoke1: mechanics OK (15 jobs, caps reach the kernel). Bug found: the hub's op_pull lowers one cap
  relative to the TARGET and drops the AD cap, so `--caps` from a goal is only its base; added operator
  `gpull` = op_polish.py with goal-stepped caps (pull kept as well, with goal caps as base). Also the first
  launch happened before control.json was read: run() now reads control first.
- 01:46 smoke2 (90 s, goals A+B only): gpull caps checked in kernel.cfg (cap.a 27, cap.ad 5 for goal A on a
  28/5 target). Unit check of goal_caps: C 28/5/128/20 -> gpull (28,5,19); B 29/4/130/22 -> (28,4,22);
  B 28/4/133/20 (only G over) -> (28,4,19); G 48/4/151/11 -> (47,4,11); F 35/4/120/20 -> (35,3,26).
- 01:47 A/B launched (unit xs-X-x2-ab, CPU 11, XS_MEM 3G): ABBA order, 0.92 h per arm, all from snap0, same
  control (ops polish,pull,join,trb,osc,gen_skel; nursery 0.3; ad3_share 0.3; no ingest):
  gen1 (scheduler.py, seed 9), goal1 (scheduler_goal.py, seed 9), goal2 (seed 11), gen2 (seed 11).

## Retrospective on the generic hub (strategies/X2/retro.py on 2026-11-14-hub/long; retro_long.txt) [H]
- 6134 jobs, ~56 CPU-h. Over the whole long campaign the hub-made records improved a goal's best key ONCE
  (goal B: polish 28/4/131/23, 20:09 UTC 11-14); every other goal best in the snapshot came from seeds/ingest
  (or was admitted before the walk's first record). So goal-best improvements are rare events (~1 per 50
  CPU-h for the generic scheduler): a 1-CPU-hour arm is expected to show 0 in both arms, and the A/B
  measures mainly the secondary quantities (steps toward a goal, stepping stones, near-goal admissions).
- Jobs whose target was near a goal (scalar <= 10 or stepping stone), step reward per CPU-h: C trb 16.5,
  D join 10.5, E join 16.8 / gen_skel 8.0, F join 7.3, G trb 6.5 / pull 3.4; polish 0.4-2.0 everywhere,
  osc ~0. Small numbers of jobs (22-230 per cell); priors only.
- L1 (q5.txt): 34% of the generic hub's CPU went to targets with A >= 32 outside every goal window
  (0.7 value/CPU-h, L1's value), against 157/CPU-h for goal-C-window targets: supports goal targeting [H].

## 02:05-02:20 changes after L1's counts (relayed by the coordinator), before the goal arms start (02:43)
L1 facts [C counts on hub logs]: (1) Archive.gain is not a value signal; (2) op_join partners = front first,
truncated to 300, so stepping stones are never partners, repeat joins on one target are waste; (3) yield per
tuple drops with attempts (polish 2.31/0.92/0 front adm per CPU-h on attempts 1/2/3; pull 2.08/2.19/1.29/0);
28/5/127/22 got 0 jobs; (4) A >= 33 targets 54% of CPU, nothing at A <= 32; A <= 29 targets made the A28/A29
gains; osc poor and uncapped; (5) at goal-near tuples 90 s kernel jobs under the tuple's own caps never
improved G; pull (GD-1, AD cap off) on A28/A29 originals did.
Changes (all in hub/scheduler_goal.py + new strategies/X2/op_gjoin.py; shared modules untouched):
- reward was already goal distance (goals.step_gain), never Archive.gain (1): unchanged.
- `gjoin` (op_gjoin.py): join with partners from the goal pool (env X2_GOAL; nearest 80, one record per
  tuple first, + 40 random cell minima with |A - A_in| <= 1); the scheduler rewrites the admitted records'
  parents to [front, back] (the hub's finish() does that only for op 'join'). Plain join kept at prior 0.3 (2).
  Test: goal D target 32/4/116/20, 120 partners, 971 joins tried in 4.4 s, 5 candidates; in smoke4, 5 gjoin
  jobs admitted 4 (37/4/130/13 x2, 31/6/122/22, ...), parents recorded.
- tuple caps per front state (3): polish 2, gpull 3, pull 3, osc 2, join 1, gjoin 1, trb 3, gen_skel 3,
  counted over all copies of a tuple (key: op, tuple, goal for capped ops, front version; reset when the front
  changes); ops with no open tuple in the goal's pool are skipped; with prob 0.7 the nearest tuple with no job
  yet is taken (fresh first: starved points like 28/5/127/22 get their first job at once).
- pull now runs exactly as the hub's pull (no --caps) (5); gpull keeps the goal step; osc keeps goal caps
  (incl. the A cap) (4); bandit priors pull 1.0, gpull .75, polish/trb/gjoin/gen_skel .5, join .3, osc .25.
- shares toward A <= 29 (4): A .12, B .22, C .18, D .14, E .10, F .08, G .08, generic .08.
Contamination note: smoke3 (~70 s), the gjoin test (~5 s), smoke4 (~45 s) and the retro/ab_compare analyses
ran on CPU 11 while arm gen1 was running there (gen1 lost roughly 1-2 CPU-min of ~55). Noted, not corrected.

## 02:15-02:25 second round, after L1's WHAT-WORKS.md (coordinator message), still before goal1 starts
- Operator choice: probability proportional to (goal reward + PRIOR) / (CPU s + 120) (eps 0.1 uniform), not
  argmax: with no reward yet the CPU split follows the prior. PRIOR = L1 6.1's suggested split: pull .40,
  gen_skel .18, polish .15, gpull .10, jump .07, trb .07, gjoin .05 (join .03, osc .02 if listed).
  Sample over 2000 draws, goal B: pull 38 %, gen_skel 18 %, polish 14 %, gpull 10 %, jump 7 %, trb 7 %, gjoin 6 %.
- Goal ops: B-G {pull, gpull, jump, polish, trb, gjoin, gen_skel}; A {pull, gpull, polish, gjoin, gen_skel};
  osc and plain join dropped (L1 findings 8, 9).
- New op `jump` (L1 finding 5, coordinator point 3: every 29/4 and 30/4 front point came from pulls that ended one
  AND above the A cap with AD one lower): op_polish.py with caps (A+1, AD-1, max(GD, goal GD)) on a jump pool =
  records with A <= goal A, AD = goal AD + 1, G <= goal G + 15, GD <= goal GD + 6, ranked by the goal scalar of
  (A+1, AD-1, G, GD). Pools: B from 28/5/128/20 (-> 29/4, then pull/gpull A to 28), D from 31/5/118/19,
  F from 33/4/107/20 and 34/4, G from 32/5/127/15, E from 32/7; none for A and C. smoke5: jump job on
  31/5/115/24 with caps (32,4,24) ran (no admission in 10 s).
- polish never on seed/ingested targets (L1 finding 3); tuple caps now trb 1, gen_skel 2, jump 2.
- Smoke5 (45 s) also ran on CPU 11 during gen1.

## 02:25-02:35 compatibility with the review5 merge (coordinator: C3 rewrites parts of the hub, merged ~06:45)
- launch() no longer copies Scheduler.launch: it calls super().launch(cpu, busy) with choose_op / choose_target
  answered by the goal layer (stashed pick), and for goal jobs temporarily points S.SCRIPTS[op] at the wrapper
  strategies/X2/op_goal.py, which appends --caps / --objective (env X2_REAL, X2_CAPS, X2_OBJECTIVE) and execs
  the real script; X2_GOAL in the env for gjoin. Run ids, job dict, pinning are the hub's. If a newer launch
  does not call choose_op/choose_target, the event `goal-compat-warning` is logged.
- main(): --cpus optional (default: process affinity), unknown options passed through to the base scheduler's
  args, and attributes this parser does not define read as None (so new base options do not crash it).
- Remaining dependencies on Scheduler internals: self.ar (rec, cells, front, circuit, dir), self.hist,
  self.secs, self.attempts, self.rng, self.dir, self.version, self.log, S.SCRIPTS, S.DEFAULT_SECONDS,
  S.WINDOW, run(), finish(), seed(), control(), write_front(), choose_op(), choose_target(), launch().
- smoke6/smoke7 (CPU 11, ~1 min each, during gen1): kernel.cfg shows the caps (jump 32/4/24 on 31/5/115/24),
  op_info of gjoin shows goal D, no compat warnings. Also overnight/jobtest2 (goal_job.sh end to end,
  after fixing a KeyError: goal bests were computed before seeding; jobtest-fail1 kept).

## 02:43-02:50 review5 compatibility (C3's X2-COMPAT.md: unpatched, the 02:36 file ran on review5 with the goal
layer bypassed: base launch serves fresh_target first, and reads self.scripts, not S.SCRIPTS)
- Adopted C3's fix natively: if the base has start_job (review5), goal jobs go to start_job(cpu, op, why, tid,
  extra=['--objective', ..., '--caps=A,AD,GD'], env=X2_GOAL); generic share = super().launch; op check uses
  self.scripts; gjoin parent rewrite skipped (review5 records join parents). Old base: wrapper path unchanged.
  op_goal.py passes --caps=VALUE (a value may start with '-').
- Reward: only candidates with a tuple not yet in the archive count (r5smoke1 showed gjoin earning 4.1 for
  copies of better existing tuples). goal1 (started 02:43) runs the 02:36 code; goal2 (03:40) runs this one.
- Snapshot of the 02:43 file: strategies/X2/scheduler_goal.0243.py. md5 now c4802cb9.
- r5smoke1 (overlay X2/r5tree built by strategies/X2/overlay_r5.sh, CPU 11, 54 s, during goal1): 8 jobs (gjoin
  D x5, polish B caps 28/4/22, gpull B 28/4/22, generic polish), 0 goal-compat-warning.

## A/B interim (arms 1-2 of 4) [H, single 0.9 CPU-h arms]
- gen1 (generic, 93 jobs, 0.82 CPU-h): +21 records, 0 new front points, every goal best unchanged; new records
  within 3 of a goal best: G 3; new stepping-stone tuples: F 2.
- goal1 (02:36 code, 53 jobs, 0.87 CPU-h): +15 records, 1 new front point 30/4/129/21 (new vs snapshot front +
  NIST) made by `jump` (goal B, caps 29/4/24 on a 28/5 target; the kernel ended one AND above its cap, as in
  L1 finding 5; 1 jump job in the arm); every goal best unchanged; within 3 of a goal best: A 7, B 3, E 1, G 1;
  new stepping-stone tuples: A 3, E 1, F 1. CPU by op: pull 1214 s, gen_skel 751, polish 550, gpull 272,
  trb 109, osc 98 (generic), jump 95, join 48 (generic), gjoin 4. 0 compat warnings.
- 03:43 goal_met path exercised (strategies/X2/test_goalmet.py, fake in-process goal Z = 40/6/200/40 on a scratch
  copy goalmet-test/): NCFF + sidecar + aes_check.json written to found-test/, aes_check_ok True for
  28/4/131/23, GOALS-MET.txt line written. (~10 s on CPU 11 during goal2.)

## A/B result (01:47-05:29 UTC, CPU 11, ABBA, 4 arms x 0.92 h from snap0; strategies/X2/final_eval.sh;
## X2/ab_final.txt, ab_final.json, ab_final_l1eval.txt, retro_<arm>.txt) [H]
| arm | code | jobs | CPU-h | +records | goal bests changed (A-G) | new front pts (vs snap front + NIST) | L1 front adm / V | new records within 3 of a goal best (A,B,C,D,E,F,G) | new stepping-stone tuples |
|---|---|---|---|---|---|---|---|---|---|
| gen1 | scheduler.py, seed 9 | 93 | 0.82 | 21 | none | 0 | 0 / 0 | 0,0,0,0,0,0,3 | F 2 |
| goal1 | goal 02:36, seed 9 | 53 | 0.87 | 15 | none | 1: 30/4/129/21 (jump) | 1 / 22 | 7,3,0,0,1,0,1 | A 3, E 1, F 1 |
| goal2 | goal 02:50, seed 11 | 53 | 0.89 | 22 | none | 0 | 0 / 0 | 6,2,1,0,2,1,1 | A 2 |
| gen2 | scheduler.py, seed 11 | 46 | 0.91 | 13 | none | 1: 29/4/128/23 (polish) | 1 / 22 | 0,0,0,0,0,0,0 | F 1 |
- Primary metric (goal distance, lexicographic over goals A > B > ... > G): IDENTICAL in all four arms; no arm
  moved any goal's best key (A 1000, B (0,0,2,1), C (0,0,2,1), D (0,0,1,0), E (0,0,2,2), F (0,0,2,1), G (0,0,2,0)).
  No goal met. Front points: generic 1, goal 1 (L1's value 22 each). L1 goal-near admissions: 0 in every arm.
- Secondary: records within 3 of a goal's best: goal arms 13 + 13, generic 3 + 0. This mostly measures where the
  CPU went (by construction of goal targeting): the A column counts 28-AND records, the B ones are 28/4
  stepping stones near 131/23. It is not evidence of faster progress to any goal.
- Conclusion [H]: on 2 x 0.9 CPU-h per configuration the goal scheduler is NOT measurably better on goal-box
  distance than the generic one (both 0 improvements; L1: 1-CPU-h arms cannot separate configurations, 11/20
  identical blocks show 0 front admissions). What it does show: the goal layer runs as designed (CPU split by
  goal and prior, goal caps reach the kernel, tuple caps, fresh-first, 0 compat warnings), and the one new
  front point in the goal arms came from the new `jump` move (1 of 1 jump jobs in goal1; 0 of 0 in goal2).
- Both new front points saved and checked: X2/found/ab/aes-sbox-a30-ad4-g129-gd21-efbf58c4f532.circ.txt and
  aes-sbox-a29-ad4-g128-gd23-442582ae7d35.circ.txt, aes_check OK, new Pareto points on the pinned set (not goals;
  29/4/128/23 dominates nothing the brief lists, 30/4/129/21 neither). (A first save_found.py run wrote sidecars
  with aes_check_ok false because of a wrong script path; fixed and re-run, sidecars overwritten.)

## 05:29-05:44 review5 real-length check (r5check1: strategies/X2/r5check.sh on overlay X2/r5tree = review5
## package + current X2 files; CPU 11; 0.25 h; 30 weak seeds (x2test.list) so goal progress can happen)
- 10 jobs at real op seconds (90 s kernel, 60 s gen_skel), campaign uid run ids, gain value / tuple mode /
  incremental join (review5 defaults), 0 goal-compat-warning, exit 0.
- 2 goal-progress events, both gpull under goal-stepped caps (28,4,20): goal B best 28/4/137/21 (0,0,7,7) ->
  28/4/135/20 (0,0,5,5) -> 28/4/133/22 (0,0,3,3). gpull for goal G on 38/4/121/15 ran with caps 44/4/13 (GD step
  2), goal A gpull with caps 27/4/-. Not meaningful as search results (weak seeds); it checks the mechanics.
