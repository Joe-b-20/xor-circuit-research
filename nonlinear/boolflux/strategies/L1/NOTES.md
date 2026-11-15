# L1 notes (log analyst, hub era), 2026-11-15

Result: `WHAT-WORKS.md` (this directory). Overnight spec: entry "L1" in
`~/xs-campaigns/2026-11-15-study/QUEUE.md` (copy: `~/xs-campaigns/2026-11-15-study/L1/queue-entry.md`).
Data and printed tables: `~/xs-campaigns/2026-11-15-study/L1/` (`cache.json`, `struct.json`, `q1.txt` ..
`q7.txt`). No search was run; CPU 12 only, every job under 2 minutes through `xsfg H`.

## Method
1. `l1_load.py`: all archive records, run records, stats and non-admit events of the eight hub
   directories into one JSON cache (11 s). Records are identified by id across directories (the arms
   were started from snapshots of `long`, so lineages can be followed back to the seeds everywhere).
2. `l1_lib.py`: per directory, replay of the archive in admission order. An admitted circuit made in that
   directory is a *front admission* if nothing admitted earlier there, and nothing in the pinned
   published set, dominates or equals it. Cross-check (`chk_gain.py`): the 75 hub-made front admissions
   are exactly the admissions whose recorded hub gain is >= 2.
3. Value model and goal-near definition: `WHAT-WORKS.md` section 0.
4. AND structure (`q3_anc.py`, `boolflux.core.from_kernel` on the archive `.bfx`): ANDs per AND level;
   id of the reduced basis of span(1, inputs, all AND outputs) and of the same for level-1 ANDs only.
5. Kernel logs (`q7_kernel.py`): `final ... feas` and the first `best` line with objective < 1000
   (= no cap penalty) give feasibility and the time it was reached, for the 866 pull jobs.

## Scripts -> tables
`q1_ops.py` operators, phases, operator x target maker, lineage signatures, every A <= 31 front admission,
goal-near admissions. `q2_waste.py` repeats, originals vs copies, target classes, pull by lowered cap,
improvement times, overheads, utilisation, nursery, bandit choice, osc, join. `q3_anc.py` seeds and
hub-made ancestors by descendant value, AND spans, provenance of the final front. `q4_settings.py`
every value-producing job (target -> result), attempts per tuple, the A/B arms recounted, one-CPU-hour
dispersion, ad3_share before / after, bandit picks, target pool by class. `q5_goals.py` CPU by goal
window, effort per goal-near tuple, needed vs incidental operators in lineages, AND spans by class.
`q6_starve.py` front ids vs the join partner limit, jobs received by each valuable point, coverage of
the front. `q7_kernel.py` kernel dynamics. `chk_stairs.py` staircases per goal class before / after.
`chk_jump.py` class jumps (A, AD changes) of pull results. `eval_run.py` + `l1_load.py name=/dir`
judge any other hub directory with the same measures.

## Mistakes and dead ends (kept)
- First value model used the hub's own improvement rule (highest-priority coordinate for which some
  earlier point is no worse on the other three). It labelled 52 of 80 front admissions "A" and inflated
  everything; replaced by the cap-box rule. The finding that the hub's gain has this flaw came out of it.
- First goal measure (sum of G and GD excess of the best circuit per goal) never changed during the hub
  era (published circuits tie the hub's), so it showed nothing; replaced by goal-near admissions
  (non-dominated in (G, GD) inside the goal class, within 6 gates / 4 levels).
- My first notice to the coordinator misquoted the copies-vs-originals table (17.1 CPU-h / 17 front
  admissions instead of 16.85 / 20) and said repeat joins gave 2 front admissions (it is 3); a correction
  went out. The corrected reading: copies are not shown to be worse targets; what is shown is saturation
  per tuple.
- "Same A, AD and GD existed before" (`q7_kernel.py` part 3) is not informative: cells contain weak
  nursery circuits, so nearly every front admission "improves an existing cell". Not used.
- A class-jump driver (explicit caps A+1, AD-1) was considered for the queue and dropped: `chk_jump.py`
  shows the jumps already happen as by-products (31/5 -> 32/4 in 4 of 30 depth pulls) and land 3 or more
  gates above the existing 32/4 front.
- Smoke tests on CPU 12 run at roughly 15 % of a CPU (several agents share it): a 20-s gen_skel job took
  94 s wall. `smoke1` (first attempt) was killed by the 110-s timeout during seeding of 118 circuits and
  restarted with 17 seeds. The Edit tool drops the exec bit of `focus_job.sh`; the queue entry calls it
  through `bash`.

## Not done
- No test of any recommended setting. No look at tonight's T / X / R / H agents' results.
- No check whether equal-tuple copies in a lineage were needed (logs cannot tell).
