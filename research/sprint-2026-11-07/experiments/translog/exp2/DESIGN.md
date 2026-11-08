# exp2 design (pre-registered 2026-11-08 ~03:33 UTC, written before launch)

Question left open by exp1: cross-seed chains shared 0 v3 nodes in 1 h against 23.7 expected under
independent wandering on N_eff = 1.3e5 nodes; same-start pairs re-met all hour. Are the seed
regions DISCONNECTED or merely FAR APART, and do same-start chains drift apart over time?

## Run

* Engine: the translog copy `translog/xorflux-translog/xorflux` (v8 in the repo untouched), plus
  the exp2 change `translog.departure` (`patch_departure.py`, `departure.diff`, default off):
  on every accepted exit from <= 88 gates the step row also carries `xid`/`xv`, the identity and
  sorted values of the 88 state left, computed from the proposal journal's net changes
  (before = after - added + removed). Smoke (60 s, 2 workers, `runs-smoke/`): 117 of 117 exits
  carry an 88-value `xv`; median |xv ^ entry state| = 10 (the neutral walk moved), median
  |xv ^ 89 state| = 3.
* `E2.toml` (from `make_toml.py`): exp1 / hunt D0 settings (v8 defaults, uncapped MixColumns,
  sharing off, `restart.enabled = false`, translog band 89 / id 88 / rotate 8 / values entry /
  values_gates 89) + `translog.departure = true`. 8 workers = 4 groups q0..q3 x 2, each group
  started on one hunt-D 88 record not used in exp1 (`seeds.json`, `pick_seeds.py`: roots and v3
  signatures distinct from exp1's and each other, four different (arm, worker) slots):
  q0 D4/free-00 anneal3#1935188101 d6, q1 DN/free-01 naive#4079938347 d5,
  q2 D0/free-02 naive#1611000713 d6, q3 D4/free-03 paar#2407742785 d6.
  Pairwise Jaccard distance of the four seeds (all 88 values, unrotated): 0.63-0.72.
* Duration: 2 h if launched by 03:38 UTC, else shortened so it ends by ~05:40 UTC (recorded in
  REPORT). `nice -n 8`, detached (`run.sh`, `driver.log`, `DONE`). No sampler (optional; the
  thread goes to the online tracker). One light analysis process (`track.py`, nice 8) runs
  alongside: it tails the eight logs, computes v3 signatures of new entry identities and writes
  5-minute snapshots.

## Definitions

* State of a chain at time t: its most recent known 88 state = the later of the last entry row's
  `v` and the last departure row's `xv` at or before t (the chain may currently be at 89/90; its
  last 88 state is what is compared).
* Distance d(A, B) between two 88 states: Jaccard distance of the HELPER sets (the 88 values minus
  the 32 target rows, i.e. 56 helpers each), minimised over the 4 byte rotations of B (the
  MixColumns symmetry used for identities). d = 0 iff same state mod rotation.
* v3 node: `plateau_sig.sig_of` signature (exp1's node; splits exact plateaus, exp1 Q2).
* Visited set of a chain: all its entry states (`v`) and departure states (`xv`). For the
  cross-seed minimum distance the visited set is thinned to one state per 5 s of campaign clock
  per chain (first state in each 5 s bin), plus every snapshot state; exact computation on the
  thinned sets with sparse products.

## Pre-registered measurements

(a) Same-start drift: for each pair q_i-00/q_i-01, d(current_a(t), current_b(t)) at t = 5, 10,
    ..., 120 min. Read: grows (monotone up), saturates (flat after some time at level L_i), or
    keeps returning to 0 (d = 0 or a shared v3 node at later snapshots).
(b) Wander: for each chain, d(current(t), start seed) at the same ticks; the maximum and the
    level at 1 h and 2 h.
(c) Cross-seed: shared v3 nodes between chains of different groups at 1 h and at the end, against
    the null M_exp = P / 1.3e5, P = sum over the 24 cross-seed chain pairs of
    (distinct v3 nodes of i) x (distinct v3 nodes of j) up to that time (Poisson 95 %).
    Same for the 4 same-start pairs (excluding the start node). And the minimum cross-seed
    distance: per 15-min window w (both chains' states in w) and cumulative (all states up to t),
    min over the 24 cross pairs and per pair; also the current-state cross distance at each tick.
(d) Exact plateau identity (`pes_lib.compress`, ~/xs-campaigns/2026-11-05-exit/pes/pes_lib.py,
    60 s per-call timeout, 30 min total budget, as exp1): for every shared v3 node (cross-seed
    first, then same-start), is the second chain's state a member of the first's exact plateau;
    and a sample of 100 consecutive (departure state xv, next entry state) hops of one chain
    (exact per-hop test now possible): is the next entry in the exact plateau of the departure
    state? Reported as yes / no / timeout counts.

## Predictions (registered)

* DISCONNECTED predicts: the cross-seed minimum distance stays bounded away from 0 (per-window
  minimum has no downward trend and stays above the same-start saturation level), and the
  same-start distance saturates at a level L below the cross-seed distance.
* FAR APART predicts: the cross-seed minimum distance shrinks over time (per-window minimum trends
  down; cumulative minimum falls faster than sampling more states alone would give, judged against
  the same statistic computed on time-shuffled windows; ultimately shared nodes appear).
* Decision rule: trend = slope of the per-window cross-seed minimum (over the 8 windows, min over
  the 24 pairs, and the median over pairs of each pair's per-window minimum) by least squares and
  Spearman rho. "Shrinks" = median-pair slope < -0.01 per 15 min with rho < -0.5 or any
  cross-seed shared v3 node / exact meeting; "bounded" = no such trend and min cross-seed
  distance > same-start saturation level + 0.05.
* Caveat registered in advance: "bounded" over 2 h does not prove disconnection (far-apart regions
  with slow mixing look the same); it can only be read as "no approach at the 2 h scale". A
  meeting or a clear downward trend falsifies DISCONNECTED; nothing in 2 h can prove it.
