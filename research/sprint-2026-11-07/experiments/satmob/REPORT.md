# satmob: factor-structured exact (SAT) search for an 87 on the plateau's mobile part

Folder: `~/xs-campaigns/2026-11-07-sprint/satmob/` (nothing written in the repository or in `sat/`).
Implements `sat/MOBILE_ENCODING.md` on top of `sat/sat87.py` (imported unchanged).  One solver child
at a time, `nice -n 8`, CaDiCaL 1.9.5 via pysat, on a machine at load 21-25 on 20 threads (two SAT
campaigns, a 6-process catalogue and other agents' jobs), so wall times are pessimistic by roughly 2x
against an idle core [guess from the load average].  Work window 2026-11-07 17:10 - 18:45 (WSL clock,
EST).  Labels: [proved] argument given; [checked] exact computation, script named; [measured] run
data; [guess].

Files: `mob.py` (core/mobile via `pes_lib.fan`, mobile->consumer graph, components, windows, instance
generation, driver, SAT handling), `solve_child.py` (sat87.encode + optional operand-pool restriction
by unit clauses, CaDiCaL), `campaign3.sh` (the sequence; still running when this was written, see
section 6), `analyze_samples.py`, `spans.py` (leaf-span intersections), `coverage.py`, `summarize.py`
(the tables below), `comp_<cid>.json` (per circuit: fan output, components, windows), `results.jsonl`
(one line per instance: sat87's schema + `family`, `level`, `pool`, `component`, `leaves`,
`prior_sat_campaign`), `run.log` (human log), `found/` and `FOUND_87` (empty: no SAT), `STOP` (create
it to stop the campaign between instances).

## 0. Result in one line

No 87.  Every instance the solver finished is UNSAT [measured]: all 26 single factors of four
structurally different 88 circuits (repo 88@5, sampleC:1011, sampleA:2667, sampleA:884) and every pair
of factors with <= 3 free values (44 of 44), plus the repo pairs with 4 free values that finished at
600 s; the remaining pairs (free 4-7) time out at 120 s (section 3).  Consequence [proved, section 4]:
an 87 that keeps the plateau core of any of these four circuits cannot be a rewrite of one factor,
nor of two factors with <= 3 free values; the whole-mobile-part instance itself (k = 21-32) was not
reached within the budget and stays open.

## 1. What was computed [checked: `mob.py analyze`, `comp_*.json`]

For a circuit S (88 values = 56 helpers + 32 outputs; wiring = the file's for the repo 88@5, the greedy
any-pair wiring `sat87.wiring_from_values` for hunt samples):

1. `pes_lib.fan(make_space("mc", None), helpers)` gives the remove1-neutral moves (R, A); the MOBILE
   helpers M = union of the removed sets R, the CORE C = helpers \ M.  No down move at any of the six
   circuits analysed (as in the sat/ campaign).  fan takes < 1 s per circuit here.
2. Mobile -> consumer graph: an edge m -- u for every value u of S that uses m as an operand under the
   wiring.  Its connected components are the plateau factors: on all six circuits analysed EVERY
   component is one mobile helper plus one consumer root, except one component of sampleC:1011 with
   two mobile helpers and one root (a coupled factor).  This is F2 (3-way factor = re-pairing of an
   unshared 3-input tree) seen from the wiring side: the mobile value is the tree's intermediate and
   its only user is the tree's root.  Roots are outputs (14 of 43 components) or core helpers (29): a
   helper root is in C by the definition "untouched by neutral moves" (its value stays, only its
   recipe changes).
3. Window of a set of components: seeds = their mobile values and roots; W = seeds, plus helpers whose
   users (under the wiring) all lie in W (dead cone), plus everything INPUTS u (S \ W) can no longer
   compute by ANY pair (least fixpoint, wiring independent; `run_scopes.window` with ANYPAIR=1, i.e.
   the minimal forced removal used by sat/dsizes.py).  K = S \ W is then split-closed (asserted before
   every instance).  `forced_extra` = |W| - |seeds|: when the root is a core helper, its own users
   cannot be rebuilt without it and are dragged in, typically with 2-6 outputs.
4. Instances: level 1 = one component, level 2 = a pair, level 3 = a triple, "all" = every component
   (the whole mobile part, scope (c) of sat/).  Identical W from different index sets are merged (on
   the repo, 2 of the 21 pairs have the same W as a single, because that single's forced closure
   already swallows the other factor).  Each instance is exactly sat87's I(K, |W| - 1) with K = S \ W,
   distinctness and the two sound symmetry breaks on, no pool restriction unless `pool = span` is
   stated (no production run used it yet; see section 2).

Per-component k, tW (outputs in W) and free = k - 1 - tW are listed in component order c0, c1, ...;
`values with >1 split` counts values of S with more than one XOR split inside INPUTS u S (the wiring
ambiguity of a value set; it does not affect any instance's meaning, only which consumers the graph
sees, and the any-pair closure repairs any wiring dependence of W).

Reading of the sizes [checked]: a 3-way factor whose root is an output gives k = 2-3, free = 0 (the
instance asks whether that output is one XOR of two kept values); a factor whose root is a core helper
drags that helper's dependents in: k = 4-12, free = 1-5.  The whole mobile part is k = 21-32 with free
= 10-17 on these six circuits (the same numbers as sat/dsizes.py).  So the decomposition does what
the design note promised for levels 1 and 2 (free <= 3 for most instances) but the union over all
levels is not cheaper than the whole: level >= 3 instances already have free 4-8 (repo: 34 triples,
free 2-8; 33 quadruples, free 4-10).

Leaf-span structure [checked: spans.py]: for a pair of factors (i, j), dim(span(L_i) ^ span(L_j)) over
GF(2) (L = the window's leaves) is 0 for 11 of 21 repo pairs, 11/15 on sampleC:1011, 8/15 on
sampleA:2667, 13/21 on sampleA:884, 15/28 on sampleA:1626, 14/36 on sampleA:1773.  A zero intersection
means no value lies in both trees' leaf spans; it does not by itself exclude a shared new gate in the
full-pool instance (a shared gate may lie outside both spans and cancel later) [guess: such sharing is
unlikely to save a gate, but the solver, not this argument, is what decides].

## 2. Exact meaning of every instance [proved: sat87 docstring, section 1 of sat/REPORT.txt]

For circuit S, window W, K = S \ W (INPUTS u K split-closed), I(K, |W| - 1) is SAT iff there is a
split-closed value set V with K u TARGETS <= V and |V| <= 87.  Therefore

* UNSAT (pool = full): no circuit with <= 87 XOR gates, of any depth, with any helper values, has a
  value set containing K.  Equivalently every <= 87 circuit (if any exists) misses at least one of
  the 88 - k values of K.  This is exactly the statement of the sat/ campaign's windows; only the
  choice of W differs (plateau factors instead of a seed value).
* Level 1, component i: K_i = everything but factor i's intermediate, its root and what the root's
  removal forces.  UNSAT: no 87 keeps all the other factors and the rest of the core and re-does
  factor i (with any re-sharing against the kept values) in one gate less.
* Level 2, pair (i, j): UNSAT: no 87 keeps everything outside W_i u W_j; this is the cross-factor
  re-sharing case between two trees (a value shared by the two trees would be a new gate).
* Level 3 likewise for three trees.  "all": K_all = the core minus what the helper roots force
  (65-67 values): UNSAT would say that every 87 abandons a value of the core itself -- the case the
  sat/ campaign could not reach (two 120 s timeouts at k = 24, 25).  Not reached here either (queued).
* pool = span (WEAKER, recorded separately in `pool`): the same CNF plus unit clauses forbidding, for
  every new gate, every constant operand (input or kept value) outside the GF(2) span of the window's
  leaves (the kept operands that W's gates read under the wiring).  New gates remain allowed as
  operands.  UNSAT then only says: no <= 87 circuit contains K AND builds its |W| - 1 new values from
  the leaves' span.  SAT would still be a genuine circuit.  Implemented and sanity-tested; no
  production instance had run with it when this report was written (it is queued for the whole
  mobile part of the repo circuit).
* Sanity [checked]: for repo component c3 (k = 8) the instance with m = k (one more gate) is SAT under
  both pools and the decoded circuit re-checks as an 88@5 by `sat87.check_circuit` and by the 32 unit
  vectors (full pool 43 s wall, span pool 3 s; span pool = 9 constants, 1,648 unit clauses).
* Cross-reference: every row records the sat/ campaigns' result on the identical (circuit, W) if one
  exists (`prior_sat_campaign`; read-only access to sat/results*.jsonl).  For an output root the
  any-pair closure equals the wiring closure, so many level-1/2 windows coincide with family A/B
  windows of the sat/ batches (all agree: UNSAT there too).  Where they differ the satmob window is
  smaller: a smaller W means a larger kept set K, i.e. a cheaper instance but a WEAKER statement; e.g.
  repo factor c3 is k = 8 here (UNSAT in 12 s) and k = 9 as the wiring-closure window A:v=08080000
  (timed out at 60 s in sat/).  One satmob timeout (sampleA:884 c1+c5, k = 9) is settled UNSAT by
  the sat/ batch at 900 s on the identical W.
## 3. Results [measured: summarize.py on results.jsonl at the time of writing; the campaign keeps appending]

## Results table [measured]

One row per distinct (circuit, W, pool); best record kept (UNSAT/SAT over TIMEOUT, longest TIMEOUT).  free = k - 1 - tW.  prior = the sat/ campaigns' result for the identical (circuit, W) if any (full pool only).

| circuit | scope | level | k | tW | free | pool | result | wall s | solve s | clauses | prior (sat/) |
|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|
| repo | M:c0 | 1 | 2 | 1 | 0 | full | UNSAT | 0.1 | 0.02 | 15412 | - |
| repo | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31082 | - |
| repo | M:c6 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31058 | - |
| repo | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46743 | UNSAT@60s |
| repo | M:c5 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.25 | 46743 | UNSAT@60s |
| repo | M:c4 | 1 | 5 | 2 | 2 | full | UNSAT | 1.5 | 1.34 | 62480 | UNSAT@60s |
| repo | M:c3 | 1 | 8 | 4 | 3 | full | UNSAT | 12.4 | 11.99 | 110563 | - |
| repo | M:c0+c6 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.29 | 46731 | UNSAT@60s |
| repo | M:c0+c1 | 2 | 5 | 3 | 1 | full | UNSAT | 0.5 | 0.28 | 62633 | UNSAT@900s |
| repo | M:c1+c6 | 2 | 6 | 4 | 1 | full | UNSAT | 1.0 | 0.83 | 78621 | - |
| repo | M:c0+c2 | 2 | 6 | 3 | 2 | full | UNSAT | 1.5 | 1.33 | 78430 | UNSAT@900s |
| repo | M:c0+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 1.9 | 1.75 | 78430 | UNSAT@900s |
| repo | M:c1+c2 | 2 | 7 | 4 | 2 | full | UNSAT | 3.2 | 2.96 | 94576 | - |
| repo | M:c1+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 3.3 | 3.09 | 94576 | UNSAT@900s |
| repo | M:c2+c6 | 2 | 7 | 4 | 2 | full | UNSAT | 3.8 | 3.54 | 94504 | - |
| repo | M:c4+c6 | 2 | 7 | 3 | 3 | full | UNSAT | 7.9 | 7.68 | 94323 | UNSAT@900s |
| repo | M:c1+c4 | 2 | 8 | 4 | 3 | full | UNSAT | 20.3 | 20.14 | 110577 | UNSAT@900s |
| repo | M:c2+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 15.5 | 15.84 | 110521 | UNSAT@900s |
| repo | M:c5+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 12.0 | 11.76 | 110535 | - |
| repo | M:c0+c3 | 2 | 9 | 4 | 4 | full | UNSAT | 84.2 | 83.92 | 126630 | UNSAT@900s |
| repo | M:c2+c4 | 2 | 9 | 4 | 4 | full | UNSAT | 186.6 | 187.21 | 126582 | - |
| repo | M:c4+c5 | 2 | 9 | 4 | 4 | full | UNSAT | 165.9 | 165.45 | 126582 | - |
| repo | M:c1+c3 | 2 | 11 | 6 | 4 | full | TIMEOUT(600s) | 588.7 | - | - | - |
| repo | M:c3+c5 | 2 | 11 | 5 | 5 | full | TIMEOUT(120s) | 122.4 | - | - | - |
| repo | M:c2+c3 | 2 | 12 | 6 | 5 | full | TIMEOUT(120s) | 122.7 | - | - | - |
| repo | M:c3+c4 | 2 | 12 | 5 | 6 | full | TIMEOUT(120s) | 122.3 | - | - | - |
| sampleA:2667 | M:c1 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.07 | 31090 | - |
| sampleA:2667 | M:c3 | 1 | 3 | 2 | 0 | full | UNSAT | 0.3 | 0.05 | 31086 | - |
| sampleA:2667 | M:c2 | 1 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.23 | 46755 | UNSAT@1800s |
| sampleA:2667 | M:c4 | 1 | 5 | 3 | 1 | full | UNSAT | 0.5 | 0.31 | 62705 | UNSAT@1800s |
| sampleA:2667 | M:c0 | 1 | 8 | 4 | 3 | full | UNSAT | 12.2 | 11.92 | 110703 | - |
| sampleA:2667 | M:c5 | 1 | 8 | 4 | 3 | full | UNSAT | 11.6 | 11.14 | 110521 | - |
| sampleA:2667 | M:c1+c3 | 2 | 6 | 4 | 1 | full | UNSAT | 1.1 | 0.78 | 78651 | - |
| sampleA:2667 | M:c1+c2 | 2 | 7 | 4 | 2 | full | UNSAT | 3.5 | 3.29 | 94552 | - |
| sampleA:2667 | M:c2+c3 | 2 | 7 | 4 | 2 | full | UNSAT | 3.7 | 3.48 | 94540 | - |
| sampleA:2667 | M:c1+c4 | 2 | 8 | 5 | 2 | full | UNSAT | 5.9 | 5.42 | 110914 | - |
| sampleA:2667 | M:c3+c4 | 2 | 8 | 5 | 2 | full | UNSAT | 5.2 | 4.97 | 110900 | - |
| sampleA:2667 | M:c2+c4 | 2 | 9 | 5 | 3 | full | UNSAT | 48.3 | 47.77 | 126967 | - |
| sampleA:2667 | M:c0+c1 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.8 | - | - | - |
| sampleA:2667 | M:c0+c4 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.1 | - | - | - |
| sampleA:2667 | M:c0+c3 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 122.1 | - | - | - |
| sampleA:2667 | M:c1+c5 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c3+c5 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c0+c2 | 2 | 12 | 6 | 5 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c4+c5 | 2 | 13 | 7 | 5 | full | TIMEOUT(120s) | 122.0 | - | - | - |
| sampleA:2667 | M:c0+c5 | 2 | 16 | 8 | 7 | full | TIMEOUT(120s) | 121.9 | - | - | - |
| sampleA:884 | M:c4 | 1 | 3 | 2 | 0 | full | UNSAT | 0.2 | 0.04 | 31138 | - |
| sampleA:884 | M:c0 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.21 | 46869 | UNSAT@1800s |
| sampleA:884 | M:c3 | 1 | 4 | 2 | 1 | full | UNSAT | 0.5 | 0.21 | 46851 | UNSAT@1800s |
| sampleA:884 | M:c5 | 1 | 4 | 2 | 1 | full | UNSAT | 0.6 | 0.31 | 46857 | UNSAT@1800s |
| sampleA:884 | M:c6 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.16 | 46785 | UNSAT@1800s |
| sampleA:884 | M:c2 | 1 | 5 | 3 | 1 | full | UNSAT | 0.5 | 0.31 | 62761 | - |
| sampleA:884 | M:c1 | 1 | 7 | 4 | 2 | full | UNSAT | 1.5 | 1.14 | 94732 | - |
| sampleA:884 | M:c2+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 2.5 | 2.32 | 78640 | UNSAT@1800s |
| sampleA:884 | M:c4+c6 | 2 | 6 | 3 | 2 | full | UNSAT | 1.8 | 1.57 | 78510 | - |
| sampleA:884 | M:c0+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 4.0 | 3.74 | 94768 | - |
| sampleA:884 | M:c3+c4 | 2 | 7 | 4 | 2 | full | UNSAT | 4.7 | 4.21 | 94732 | - |
| sampleA:884 | M:c4+c5 | 2 | 7 | 4 | 2 | full | UNSAT | 4.8 | 4.56 | 94744 | - |
| sampleA:884 | M:c2+c4 | 2 | 8 | 5 | 2 | full | UNSAT | 7.3 | 7.01 | 110998 | - |
| sampleA:884 | M:c0+c3 | 2 | 7 | 3 | 3 | full | UNSAT | 7.5 | 7.22 | 94587 | - |
| sampleA:884 | M:c0+c2 | 2 | 8 | 4 | 3 | full | UNSAT | 22.7 | 22.33 | 110829 | - |
| sampleA:884 | M:c0+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 22.7 | 22.39 | 110815 | - |
| sampleA:884 | M:c0+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 14.2 | 13.89 | 110647 | - |
| sampleA:884 | M:c3+c5 | 2 | 8 | 4 | 3 | full | UNSAT | 22.9 | 22.6 | 110773 | - |
| sampleA:884 | M:c3+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 22.5 | 22.18 | 110605 | - |
| sampleA:884 | M:c5+c6 | 2 | 8 | 4 | 3 | full | UNSAT | 19.5 | 19.04 | 110619 | - |
| sampleA:884 | M:c2+c5 | 2 | 9 | 5 | 3 | full | UNSAT | 53.4 | 53.01 | 127143 | - |
| sampleA:884 | M:c2+c6 | 2 | 9 | 5 | 3 | full | UNSAT | 41.4 | 41.04 | 126951 | - |
| sampleA:884 | M:c1+c4 | 2 | 10 | 6 | 3 | full | UNSAT | 71.0 | 70.68 | 143579 | - |
| sampleA:884 | M:c1+c5 | 2 | 9 | 4 | 4 | full | TIMEOUT(120s) | 121.9 | - | - | UNSAT@900s |
| sampleA:884 | M:c0+c1 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 121.8 | - | - | - |
| sampleA:884 | M:c1+c3 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 121.8 | - | - | - |
| sampleA:884 | M:c1+c6 | 2 | 11 | 6 | 4 | full | TIMEOUT(120s) | 121.8 | - | - | - |
| sampleA:884 | M:c1+c2 | 2 | 12 | 7 | 4 | full | TIMEOUT(120s) | 122.6 | - | - | - |
| sampleC:1011 | M:c1 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15448 | - |
| sampleC:1011 | M:c2 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.02 | 15448 | - |
| sampleC:1011 | M:c5 | 1 | 2 | 1 | 0 | full | UNSAT | 0.2 | 0.03 | 15448 | - |
| sampleC:1011 | M:c3 | 1 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.19 | 46851 | UNSAT@1800s |
| sampleC:1011 | M:c0 | 1 | 5 | 2 | 2 | full | UNSAT | 0.3 | 0.73 | 62656 | UNSAT@1800s |
| sampleC:1011 | M:c4 | 1 | 8 | 4 | 3 | full | UNSAT | 22.4 | 22.16 | 110815 | - |
| sampleC:1011 | M:c1+c2 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.28 | 46839 | - |
| sampleC:1011 | M:c1+c5 | 2 | 4 | 2 | 1 | full | UNSAT | 0.4 | 0.18 | 46839 | - |
| sampleC:1011 | M:c2+c5 | 2 | 4 | 2 | 1 | full | UNSAT | 0.7 | 0.44 | 46839 | - |
| sampleC:1011 | M:c1+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.6 | 1.42 | 78610 | - |
| sampleC:1011 | M:c2+c3 | 2 | 6 | 3 | 2 | full | UNSAT | 1.6 | 1.38 | 78610 | - |
| sampleC:1011 | M:c3+c5 | 2 | 6 | 3 | 2 | full | UNSAT | 2.0 | 1.76 | 78610 | - |
| sampleC:1011 | M:c0+c1 | 2 | 7 | 3 | 3 | full | UNSAT | 8.6 | 8.4 | 94587 | - |
| sampleC:1011 | M:c0+c2 | 2 | 7 | 3 | 3 | full | UNSAT | 7.8 | 7.63 | 94587 | - |
| sampleC:1011 | M:c0+c5 | 2 | 7 | 3 | 3 | full | UNSAT | 10.3 | 10.03 | 94587 | - |
| sampleC:1011 | M:c0+c3 | 2 | 9 | 4 | 4 | full | TIMEOUT(120s) | 122.3 | - | - | - |
| sampleC:1011 | M:c2+c4 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.2 | - | - | - |
| sampleC:1011 | M:c4+c5 | 2 | 10 | 5 | 4 | full | TIMEOUT(120s) | 122.2 | - | - | - |
| sampleC:1011 | M:c3+c4 | 2 | 12 | 6 | 5 | full | TIMEOUT(120s) | 122.2 | - | - | - |
| sampleC:1011 | M:c0+c4 | 2 | 13 | 6 | 6 | full | TIMEOUT(120s) | 122.2 | - | - | - |

## Counts per circuit and level [measured]

| circuit | level | pool | instances | UNSAT | SAT | TIMEOUT | max solved free | max solved k | UNSAT solve-time median / max (s) |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| repo | 1 | full | 7 | 7 | 0 | 0 | 3 | 8 | 0.2 / 12.0 |
| repo | 2 | full | 19 | 15 | 0 | 4 | 4 | 9 | 3.5 / 187.2 |
| sampleA:2667 | 1 | full | 6 | 6 | 0 | 0 | 3 | 8 | 0.3 / 11.9 |
| sampleA:2667 | 2 | full | 14 | 6 | 0 | 8 | 3 | 9 | 5.0 / 47.8 |
| sampleA:884 | 1 | full | 7 | 7 | 0 | 0 | 2 | 7 | 0.2 / 1.1 |
| sampleA:884 | 2 | full | 21 | 16 | 0 | 5 | 3 | 10 | 19.0 / 70.7 |
| sampleC:1011 | 1 | full | 6 | 6 | 0 | 0 | 3 | 8 | 0.2 / 22.2 |
| sampleC:1011 | 2 | full | 14 | 9 | 0 | 5 | 3 | 7 | 1.4 / 10.0 |

## Hardness by free values (all circuits, full pool) [measured]

| free | instances | UNSAT | TIMEOUT | UNSAT solve s min / median / max |
|---:|---:|---:|---:|---|
| 0 | 9 | 9 | 0 | 0.0 / 0.0 / 0.1 |
| 1 | 17 | 17 | 0 | 0.2 / 0.3 / 0.8 |
| 2 | 21 | 21 | 0 | 0.7 / 3.0 / 7.0 |
| 3 | 22 | 22 | 0 | 7.2 / 19.0 / 70.7 |
| 4 | 17 | 3 | 14 | 83.9 / 165.4 / 187.2 |
| 5 | 5 | 0 | 5 | - |
| 6 | 2 | 0 | 2 | - |
| 7 | 1 | 0 | 1 | - |

## Component statistics per circuit [checked: comp_*.json]

| circuit | depth | core | mobile | neutral moves | components | shapes (mobile+roots) | per-component (k, tW, free) | whole mobile part (k, tW, free) | values with >1 split |
|---|---:|---:|---:|---:|---:|---|---|---|---:|
| repo | 5 | 49 | 7 | 14 | 7 | 1+1 x7 | (2,1,0) (3,2,0) (4,2,1) (8,4,3) (5,2,2) (4,2,1) (3,2,0) | (23,10,12) | 61 |
| sampleA:1626 | 8 | 48 | 8 | 16 | 8 | 1+1 x8 | (4,2,1) (3,2,0) (4,2,1) (7,4,2) (2,1,0) (4,2,1) (3,2,0) (4,2,1) | (30,14,15) | 64 |
| sampleA:1773 | 8 | 47 | 9 | 20 | 9 | 1+1 x9 | (6,3,2) (12,6,5) (9,5,3) (4,2,1) (5,2,2) (3,2,0) (4,2,1) (2,1,0) (4,2,1) | (32,14,17) | 63 |
| sampleA:2667 | 8 | 50 | 6 | 16 | 6 | 1+1 x6 | (8,4,3) (3,2,0) (4,2,1) (3,2,0) (5,3,1) (8,4,3) | (23,12,10) | 64 |
| sampleA:884 | 7 | 49 | 7 | 16 | 7 | 1+1 x7 | (4,2,1) (7,4,2) (5,3,1) (4,2,1) (3,2,0) (4,2,1) (4,2,1) | (24,11,12) | 64 |
| sampleC:1011 | 12 | 49 | 7 | 18 | 6 | 1+1 x5, 2+1 x1 | (5,2,2) (2,1,0) (2,1,0) (4,2,1) (8,4,3) (2,1,0) | (21,10,10) | 64 |

Totals: 94 distinct instances: {'UNSAT': 72, 'TIMEOUT': 22}; solver wall 4154 s


## 4. What is now excluded that the window families did not cover [proved as stated; outcomes measured]

Each UNSAT row says: no <= 87 circuit contains K = S \ W for that circuit and that W (the W lists are
in `results.jsonl`).  Put together per circuit:

* Level 1 complete on four circuits (26 of 26 factors UNSAT): for every plateau factor i of the repo
  88@5, sampleC:1011, sampleA:2667 and sampleA:884, every <= 87 circuit misses a value outside W_i.
  In plateau language: no 87 is "the plateau with one factor rewritten", whatever the rewrite (any
  values, any re-sharing with the kept 76-86 values, one gate less).  The sat/ one-seed windows said
  this for the factors whose mobile-seeded window had k <= 8 under wiring closure; the factors with
  helper roots and k = 9-12 under wiring closure (e.g. repo c3, sampleA:1773 c1) were open there and
  the k = 8-9 ones are closed here (any-pair closure; the weaker-but-finished form).
* Level 2: every pair with free <= 3 (44 of 44 across the four circuits) and the repo pairs with
  free = 4 that finished at 600 s are UNSAT: no 87 keeps everything outside W_i u W_j.  So an 87 that
  keeps the core cannot be a re-pairing or re-sharing confined to two factors' windows of these kinds.
  Pairs with free >= 4 (mostly a helper-root factor with another helper-root factor) are the open
  set: 6 on the repo at 120 s (the two k = 9 ones closed at 600 s in 166-187 s; the k = 11 one timed out at 600 s; three not yet retried), 5 on sampleC:1011, 8 on
  sampleA:2667, 5 on sampleA:884 (one closed by the sat/ batch at 900 s).
* Combination [proved]: if every level-1 and every level-2 instance of a circuit is UNSAT, then any
  <= 87 circuit V that contains the kept core K_all (the values outside the whole mobile window) must
  miss values from at least THREE different factor windows W_i (otherwise V would contain some K_ij).
  With the present partial level 2, the statement is: the set of factor windows an 87 ⊇ K_all
  touches is not contained in any single W_i nor in any UNSAT pair W_i u W_j.
* Not covered, as before: an 87 that drops a core value (the fixed part of this scope by definition),
  an 87 on another plateau, and the open pairs above.  The whole-mobile-part instance (the direct
  form of scope (c), k = 21-32, free = 10-17) is queued but was not reached; the decomposition replaces
  it by the conjunction over all levels, and levels >= 3 have free 4-8, i.e. they sit at or beyond the
  present frontier.  So "the plateau's mobile part cannot be done with one fewer gate" is proved only
  in its one- and two-factor forms, not in full.

Contrast with the sat/ families: family A/C/B windows are seeded by a value or an output block and
never isolate "a factor"; the satmob windows are the plateau's own factors, so each UNSAT is a
statement about a plateau move class (re-pair factor i; re-pair and re-share i with j) rather than
about a neighbourhood of a value.  Coverage [checked: coverage.py]: the union of the UNSAT windows is
21-24 of 88 values per circuit, containing all mobile helpers, 4-6 core helpers (the helper roots and
what they force) and 10-12 outputs; it never contains the deep core (that is the scope's fixed part).

## 5. Frontier [measured]

* free <= 3: every instance finishes, 0.02-71 s wall under load (k up to 10).
* free = 4: 120 s solves 1 of 17 (84 s); 600 s solved the two k = 9 repo retries in 166-187 s but not the k = 11 one (6 forced outputs).  The
  600 s limit is the right one for free = 4 on this machine (900-1800 s if more than ~8 k values
  are forced, as on the k = 11 pairs) [guess from the measured growth 3 -> 4: x5-10 per free value].
* free >= 5: nothing finished at 120 s (8 instances); expected 600-6000 s each [guess], i.e. the
  regime of the sat/ k = 9 helper windows.
* Hardness tracks free = k - 1 - tW and not k, as predicted in sat/REPORT.txt section 4: k = 10 with
  free 3 (sampleA:884 c0+c2, 71 s) is easier than k = 9 with free 4 (84-187 s or timeout).
* Instance size stays small (k = 12: ~175k clauses, pairwise at-most-one dominated); the barrier is
  search.  The two encoding improvements listed in sat/REPORT.txt section 5 (ladder at-most-one, full
  lex order on independent gates) are untried and are the cheapest lever for free >= 5.

## 6. What is running and what to run with more cores

Still running when this was written (`campaign3.sh`, nohup, one child at a time, nice 8, idempotent,
`satmob/STOP` stops it between instances; `results.jsonl` / `run.log` grow accordingly): the remaining
repo pair retries at 600 s; then sampleA:1626 and sampleA:1773 levels 1-2 at 120 s; then repo triples
at 120 s; the whole mobile part of the repo at 600 s (full pool, then span pool); repo triples and
all five samples' pairs at 600 s.  Expected [guess]: the whole-mobile instance times out at 600 s
under either pool; the span-pool one is the first thing to retry at 3600 s because its pool is 20-25
constants instead of ~115.

With 12 cores for a few hours (same code, `mob.py run CID LEVELS LIMIT [span]`, shard by circuit):
1. All pairs with free 4-7 on the six analysed circuits at 1800 s (about 40 instances, ~20 h worst case
   serial, 2 h on 12 cores): completes level 2, which turns the combination statement of section 4
   into "an 87 keeping the core touches >= 3 factor windows" for each circuit.
2. Repo triples (34; free 2-8) at 1800 s, free-ascending; the free <= 4 half first (14 instances).
3. The whole mobile part, span pool, at 3600 s on all six circuits (6 instances) -- the weaker
   statement "no 87 keeps the core and builds the re-paired part from the trees' own leaves", which
   is exactly the plateau-move language; then full pool with the ladder encoding.
4. The coupled plateaus of the kste corpus (radices 33, 45, 108: factors with several trees sharing
   values; F2) -- there the components are genuinely larger than 1+1 and the factor encoding does
   something the one-seed windows cannot; `mob.py analyze kste:<i>` gives their sizes in seconds.
5. Encoding: ladder at-most-one and full lex symmetry (sat/REPORT.txt section 5, items 1-2) before
   any run at >= 1800 s; the free >= 5 regime is where they pay.

Findings
 F1 [measured] 26 of 26 single plateau factors on four structurally different 88 circuits are UNSAT:
    no 87 is one rewritten factor of these plateaus.
 F2 [measured] 44 of 44 factor pairs with <= 3 free values (and the repo free = 4 pairs finished at
    600 s) are UNSAT: no 87 is a two-factor re-pairing/re-sharing of these kinds.
 F3 [checked] On all six circuits analysed every mobile->consumer component is 1 mobile + 1 root (one
    2+1 on sampleC:1011): the decomposition of MOBILE_ENCODING.md collapses to "one factor at a time",
    and the whole mobile part is only reached as the conjunction over all levels (free 4-17), so
    scope (c) in full remains out of reach of this encoding at 600 s.
 F4 [measured] Hardness is governed by free = k - 1 - tW: free <= 3 solves in <= 71 s, free = 4 in
    84-187 s at best, free >= 5 does not finish at 120 s.
Rejected
 - "the mobile part is cheap once factored": the factors are cheap; their union is not (F3).
Open
 - pairs with free >= 4 on the four circuits (section 4), everything at level >= 3, the whole mobile
   part (both pools), sampleA:1626 / sampleA:1773 (analysed, instances queued).