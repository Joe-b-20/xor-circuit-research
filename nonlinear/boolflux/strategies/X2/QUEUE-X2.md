## X2: goal-directed hub, optional third arm next to L1's focus/base arms, same seeds (goals A-G)
- purpose / goals (A-G): the hub with target choice, operator choice, caps and objective set by the user's
  goal list (hub/goals.py, hub/scheduler_goal.py; design and evidence in strategies/X2/NOTES.md). Built to
  be consistent with L1's entry: SAME seed list (L1's overnight/seed.list, built once under L1's lock),
  SAME harvest (strategies/L1/harvest.py: aes_check + sidecars into found/) and SAME evaluation
  (strategies/L1/eval_run.py), plus X2's goal-distance table (goal_dist_seeded.py). So the coordinator can
  run X2-goal, L1-focus and L1-base side by side and compare them on equal CPUs.
- how X2-goal differs from L1-focus (both: no osc, no ad3_share, nursery 0.5 for the generic part):
  | | L1 focus | X2 goal |
  |---|---|---|
  | target | hub default: front ids, fewest attempts per id; nursery 0.5 | per goal (CPU shares A .12 B .22 C .18 D .14 E .10 F .08 G .08, generic .08): the 40 records nearest to the goal (lexicographic deficit, A > AD > G+GD) or its stepping stones; fresh tuples first (p 0.7) |
  | attempts | per id (4 ids per tuple) | per (op, tuple, front state): polish 2, pull 3, gpull 3, jump 2, trb 1, gjoin 1, gen_skel 2 (L1 finding 7) |
  | operator | uniform over pull, pull, gen_skel, gen_skel, polish, trb, join | per goal, proportional to (goal-distance reward + prior)/(CPU s + 120), prior = L1 6.1 split (pull .40, gen_skel .18, polish .15, gpull .10, jump .07, trb .07, gjoin .05), eps 0.1 |
  | caps | the target's own | polish: the goal's caps; pull: the hub's pull (GD-1..3, AD off); gpull: one step toward the goal; jump: (A+1, AD-1, GD) on targets one AD level above the box (L1 finding 5); polish never on seeds |
  | join | op_join (front-first partners, truncated to 300) | gjoin: partners from the goal pool (L1 finding 8) |
  | reward | none (uniform) | goal distance steps (goals.step_gain), never Archive.gain (L1 finding 1) |
  | goal hits | harvest at the end | at admission: found/ NCFF + sidecar + aes_check.py, event GOAL-MET, DIR/GOALS-MET.txt; and harvest at the end |
- command (absolute paths):
  `XS_MEM=3G /home/joebachir20/xs-campaigns/guard/xsrun X <CPUS-X> x2-goal /home/joebachir20/xs-campaigns/2026-11-15-study/X2/overnight/goal.log -- bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/X2/goal_job.sh goal <CPULIST-X> <HOURS>`
  (<CPUS-X> for xsrun e.g. 4-7, <CPULIST-X> the same comma-separated e.g. 4,5,6,7.) The script seeds from
  L1's seed list (builds it with L1's mk_focus_seeds.py if L1's arms have not yet), runs
  `hub/scheduler_goal.py --dir .../X2/overnight/goal --cpus ... --hours ... --seed 31 --seed-list ... --ops pull,pull,gen_skel,gen_skel,polish,trb,join --eps 1.0 --nursery 0.5 --found .../X2/found/goal`
  with control.json {"ad3_share": 0.0, "keep_met": true}, then harvest, eval, goal distance.
  Hot control: `.../X2/overnight/goal/control.json` keys goal_share, generic_share, goal_ops, keep_met, goal_eps
  plus every key of the original (re-read every 30 s).
- CPUs wanted / minimum: equal CPUs per arm. 8 CPUs: X2-goal 4 + L1-focus 4. 12: X2-goal 4 + L1-focus 4 +
  L1-base 4. 14: 5 / 5 / 4. Minimum 2 for X2-goal.
- run length: 8-12 h, the same for every arm. Stop early: `systemctl --user stop xs-X-x2-goal`, then
  `STEPS="harvest eval" bash /home/joebachir20/xcr-boolflux/nonlinear/boolflux/strategies/X2/goal_job.sh goal 0 0`.
- memory per process: scheduler < 400 MB (hub scheduler measured 350 MB at 8-15 CPUs; the goal layer adds
  pools of record ids), kernel / join jobs < 100 MB. XS_MEM=3G for the whole unit (scheduler + its jobs).
- results land in / verification: hub dir `/home/joebachir20/xs-campaigns/2026-11-15-study/X2/overnight/goal/`
  (two verifiers at admission), `goal_stats.jsonl` (one line per job: goal, op, caps, reward, progress),
  `goals.json` (per-goal best, op scores, CPU used, every 5 min), `GOALS-MET.txt`; found circuits with sidecars
  and aes_check results in `/home/joebachir20/xs-campaigns/2026-11-15-study/X2/found/goal/`; `EVAL.txt` (L1),
  `GOALDIST.txt` (X2: per goal, best of the seeds -> best at the end, improvement events, new stepping-stone
  tuples). For one table over all arms: `python3 .../strategies/X2/goal_dist_seeded.py .../X2/overnight/goal .../L1/overnight/focus .../L1/overnight/base`.
  Merge into the long archive afterwards: `scheduler.py --dir .../2026-11-14-hub/long --cpus 0 --seed-only --seed-list <(ls .../X2/overnight/goal/archive/*.bfx)`.
- success criterion: any GOALS-MET line (aes_check OK). Otherwise, per goal in priority order, the best key in
  GOALDIST.txt (lexicographic over goals: the arm that is closer on the highest goal where they differ wins),
  then L1's goal-near admissions and front admissions with A <= 32 per CPU-h in EVAL.txt. Expect few events:
  in the hub era a goal's best moved once in ~56 CPU-h (X2 retro.py) and L1 counted 19 goal-near admissions
  in 65.9 CPU-h; at 4 CPUs x 10 h per arm, differences of 2x in goal-near rate are about what can be seen.
- evidence so far [H]: X2's A/B (4 arms x 0.9 CPU-h, ABBA, CPU 11, from the long archive at 01:38): goal
  distance unchanged in all arms (generic and goal alike), 1 front point per configuration, so the goal scheduler
  is NOT shown better on goal-box distance; its goal arms put 13 + 13 admissions within 3 of a goal's best vs 3 + 0
  (where the CPU went, not progress). Run it only as a comparison arm next to L1's, or not at all if CPUs are short.
- tested: the goal scheduler ran 2 x 0.9 CPU-h in X2's A/B on the current hub; on the review5 hub (overlay
  X2/r5tree = review5 package + X2's files) in r5smoke1 (54 s) and r5check1 (15 min, 30 weak seeds, real op
  seconds; result in X2/NOTES.md); goal_job.sh end to end on the current hub (overnight/jobtest2); goal_met
  path (found/ + aes_check + GOALS-MET) with a fake goal (test_goalmet.py). The 4-14 CPU configuration has not run.
- works on the merged code: scheduler_goal.py detects Scheduler.start_job (review5) and then sends goal jobs
  through it (C3's x2-compat fix adopted natively, no patch needed); review5 options (--gain, --target-mode,
  --tuple-caps, ...) pass through and default as in the base.
