# Design note: a factor-structured exact encoding for the plateau's mobile part (scope (c))

Status: design only, no code. Written 2026-11-07 for the sat/ campaign. Tags as in the sprint brief.

## Why the plain window encoding fails here [checked, dsizes.py]

The mobile part M of an 88 plateau state S (helpers touched by some remove1-neutral move, 6-9 values
on the six picked circuits; 7-16 in general) is not a detachable corner. Removing M forces, even under
the minimal any-pair closure, the removal of every value that can only be rebuilt through M: on the six
circuits k = |W| = 21-32 with 10-14 outputs in W. The plain encoding then has 20-31 free 32-bit values
with a ~120-element operand pool each: ~2 x 10^5 clauses and a search space the solver does not
finish at 120 s (two timeouts measured). The structure that makes the plateau an exact product of
3-way re-pairings is invisible to it.

## What the plateau structure says [cited: 2026-11-05-visual SYNTHESIS, kste report section E]

Every known 88 plateau is core C (40-49 helpers, fixed on the plateau) times independent factors; a
3-way factor is an unshared 3-input XOR tree a+b+c whose intermediate value can be a+b, a+c or b+c.
Larger factors (15, 45, 60, 99, ... choices) are coupled re-pairings of a few such trees. The mobile
helpers are exactly the intermediate values of these trees; their consumers are the tree roots
(mostly outputs, sometimes other helpers). So the neighbourhood we want to search is: core fixed,
and the sub-circuit "from the core and the inputs to the roots of the trees" free.

## Proposed formulation

Fix the core C (its values are constants in the pool, as the kept set K is today). Let R be the set
of ROOTS: every value of S that is not in C and not in M, i.e. the consumers (outputs and the few
helpers) that the mobile values feed, plus any value of S \ C that cannot be rebuilt from C u INPUTS
alone. Let the free gates be m = |M| + |R| - 1 new values (one fewer than S uses for M u R), with the
constraint that every root that is a target is among them. This is exactly the window encoding with
W = M u R and k = |W|, i.e. k = 21-32 on our circuits, and that is what timed out. The factor
structure is used to CUT the search, not to change the question:

1. Two-level decomposition (what makes it tractable). The roots split into groups by which mobile
   values they share (connected components of the bipartite graph M -- R). A 3-way factor is a
   component with one mobile value and one root; coupled factors are components with 2-6 mobile
   values and 2-8 roots. Components are independent given the core: the gates of one component never
   feed another (they are roots or intermediates of disjoint trees) [proved for the product
   structure; false if an 87 re-shares across components, see limits]. So first solve each
   component separately: for component i with m_i mobile values and r_i roots, ask SAT for m_i + r_i
   - 1 new gates over pool INPUTS u C u (the other components' roots as constants). Instance size:
   m_i + r_i - 1 <= 13 free values, tW = number of target roots (usually = r_i), so free = m_i - 1
   <= 5 -- the regime where the window encoding finishes in seconds to minutes [measured: free <= 3
   finishes at k <= 9]. A component that is SAT is an 87 outright (verify as usual). If every
   component is UNSAT, the saving must come from re-sharing ACROSS components, and only then is the
   second level needed.

2. Second level: pairs of components. For each pair (i, j) with a plausible shared value (a value v
   with v in span of component i's inputs and of component j's inputs; computable by Gaussian
   elimination on the 32-bit masks, cheap), run the window on the union: m_i + m_j + r_i + r_j - 1
   gates, free = m_i + m_j - 1 <= 9. On our circuits components have m_i <= 3 typically, so free <= 5
   again. Triples only if the pair level produces a timeout pattern.

3. Pruning inside a component instance (all sound):
   - a new gate that equals a root is fixed bitwise (already in the encoding via the target clauses;
     extend it to helper roots: they must appear too, unless the solver is allowed to drop a helper
     root -- allow dropping: a helper root is not required, only targets are);
   - restrict the first level's operand pool to values whose mask lies in the GF(2) span of the
     component's leaf set L_i (leaves = inputs and core values that the component's trees read) plus
     at most one extra core value; this is the "same leaves, any re-pairing" scope; then widen to the
     full pool for the final run. The restricted pool has 10-25 elements instead of 120, so the
     pairwise at-most-one shrinks 25-100x and the solver's decision depth with it;
   - the Z4 byte rotation maps components of a rotation-closed core to each other: solve one
     representative per orbit.

## Expected instance size [guess from the measured encoding sizes]

Per component instance: pool 32 + |C| + (other roots) ~ 110-120 constants, m = m_i + r_i - 1 <= 13
gates: 13 x (2 x 120 selectors + 120 prefix + 32 bits + 32 x ~2 AND/OR vars + distinctness 120 x 32)
~ 13 x 5,000 = 65k variables (distinctness dominates; drop it against constants, keep it against new
gates: ~ 13 x 1,200 = 16k variables) and ~ 13 x 15k = 200k clauses with the pairwise at-most-one over
120, or ~ 13 x 3k = 40k clauses with the ladder at-most-one. With the restricted pool (25 elements)
the whole instance is under 20k clauses. The hardness driver is free = m_i - 1 <= 5, not m: measured
free <= 3 solves in <= 60 s, free = 5 (helper windows k = 9, tW = 4) timed out at 60 s single-core but
is the 900 s class.

Whole mobile part in one instance (no decomposition): k = 21-32, free = 11-18: ~ 30 x 15k = 450k
clauses and free values beyond anything measured; expected to time out at any limit we can afford.
The decomposition replaces it by ~5-10 component instances per circuit (free <= 5) plus ~10-30 pair
instances (free <= 9): roughly 1-3 solver-hours per circuit at 900 s limits [guess].

## What it proves and what it does not

A component (or pair) UNSAT proves: no <= 87 circuit contains C and the roots of the other components
-- the same kind of statement as today's windows, on a window defined by the plateau's own structure
rather than by a seed value. Level 1 + level 2 all UNSAT proves there is no 87 that keeps the core and
re-shares across at most two factors. It does not exclude an 87 that abandons a core value (the core
is the fixed part by definition of this scope) or that re-shares across three or more factors. The
statement "the mobile part cannot be done with one fewer gate" is the union over all levels; with
components independent given the core, the level-3+ cases need a value shared by three trees, which
Gaussian elimination can enumerate and would usually show to be empty.

## Minimal implementation (if wanted; ~150 lines on top of sat87/run_scopes)

1. components(order, mobile): bipartite graph mobile -> consumers under the wiring, connected
   components, roots = consumers not in mobile.
2. For each component: W = mobile_i u roots_i (then the usual dead-cone and any-pair closure in
   run_scopes.window); instance I(K, |W| - 1); optional pool restriction = a `pool_filter` argument to
   sat87.encode that drops constants outside span(L_i) (a 32-bit GF(2) rank test per constant).
3. Pairs: W = union, same call.  Family "M" in run_scopes.scopes; the batch drivers take it unchanged.
