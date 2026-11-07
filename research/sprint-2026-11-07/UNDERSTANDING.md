# Linear maps and the XORFlux search: what we understand (sprint 2026-11-07)

Status: DRAFT, being filled during the sprint. Every statement carries an evidence tag:
[proved] [checked] [measured] [cited] [guess]. Four kinds of object are kept apart throughout:
the MAP (the matrix), the CIRCUIT (a value set), the SEARCH PROCEDURE (moves, acceptance,
restarts, sharing) and the IMPLEMENTATION (how fast each step runs). Numbered findings F1, F2,
... refer to [FINDINGS.md](FINDINGS.md); inherited results name their source folder.

## 1. The objects

- A circuit for a map M is exactly a set S of values (GF(2) masks) closed under "every output
  and every helper is the XOR of two earlier members"; gates = |S| minus the inputs; depth is a
  function of S alone [proved, 2026-11-05-visual]. Two circuits with the same S are the same point.
- The map's symmetries act on S: for MixColumns the byte rotation Z4 (and nothing else among bit
  permutations) [checked, 2026-11-05-space]. Distances and counts must be taken modulo it.
- A plateau = the set of circuits reachable from S by the walk's neutral remove-one moves. At the
  bottom of the known landscapes it is an exact Cartesian product of independent small factors
  [checked, 2026-11-05-views/plateau, 2026-11-05-exit]; each 3-way factor is the pairing choice of
  an unshared 3-input XOR tree (F2) [checked on 52 MixColumns 88 plateaus].

## 2. What the search does (procedure)

(to be filled: moves and what each can and cannot change; acceptance; restarts; sharing; which
decisions the evidence supports)

## 3. Where it succeeds and why

- Descending from any constructor root to 88 on MixColumns takes 1-4 minutes with v8 uncapped
  (F1) [measured, hunt].

## 4. Where it fails or stalls and why

- At the bottom, the walk re-spells the same circuit (F2); exits need +1/+2 edits of the core;
  from 49 known 88 plateaus the +1 exits lead only to other 88s or home [checked, PES].

## 5. What makes it slow (implementation versus procedure)

- ~35 % of proposal CPU is remove1 calls that return nothing; depth.repair is a no-op at the
  minimum depth [measured, v10-proto]. (procedure/implementation split to be quantified)

## 6. What properties of a map matter

(to be filled from crossmap/ and bench/)

## 7. What transfers and what is specific

(to be filled)

## 8. What remains unexplained

(to be filled)
