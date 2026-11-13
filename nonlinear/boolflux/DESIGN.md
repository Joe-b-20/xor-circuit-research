# BoolFlux design

BoolFlux searches for cheaper circuits of a complete multi-output Boolean function (an S-box,
given by its value table) under a configurable gate library, cost model, objective and
constraints. It is the nonlinear extension of XORFlux: it keeps XORFlux's working ideas (one
chain per worker that never leaves the space of correct circuits, a "remove and exactly repair"
main move, neutral plateau moves, restarts from the best, verified records with replay seeds)
and replaces the linear-map core with one for arbitrary gates.

## Representation

- **Circuit**: a straight-line program of two-input gates over `n` inputs. A gate is its 4-bit
  truth table `op` (`f(a,b) = (op >> ((a<<1)|b)) & 1`), so any two-input function can be a
  library member: AND 8, OR 14, XOR 6, XNOR 9, NAND 7, NOR 1, ANDN 4 (`a & ~b`), ORN 13
  (`a | ~b`), NOT 3 (unary). Every signal carries its complete truth table (`2^n` bits; 4
  machine words for an 8-bit S-box), so correctness is checked exhaustively at every step.
- **Bit order**: input `i` is bit `n-1-i` of the input integer and output `j` is bit `m-1-j` of
  the output integer (msb/msb, NIST's AES convention).
- **Model** (`models/*.json`): the allowed gate types and their costs. **Objective**: a
  lexicographic list over `cost, g, a, gd, ad` (weights 1, 1e-4, 1e-8). **Caps**: gate depth
  GD, AND depth AD, AND count A. A is the number of nonlinear gates (AND, NAND, OR, NOR, ANDN,
  ORN); GD counts every gate (NOT included) as one level; AD counts nonlinear gates only.
- **AND skeleton**: the same function as a list of K products `g_k = L_k * R_k` of affine forms
  over `(1, x, g_<k)`, with every output in the GF(2) span of `(1, x, g)`. Every nonlinear
  two-input gate is `((a^p) & (b^q)) ^ r`, so any circuit maps to a skeleton with K = A.

## Two search levels

**Gate level** (`kernel/bfx.c`). The state is always a correct circuit. A move picks a gate
`s`, computes its exact care set (the inputs on which flipping `s` changes an output, from one
re-simulation of `s`'s fanout cone) and its divisors (signals outside that cone), and looks
for an expression of 0 to 3 new library gates over the divisors that equals `s` on the care
set:

| level | form | search |
|---|---|---|
| 0 | an existing divisor | scan |
| 1 | `op(d1, d2)`, `NOT d` | all pairs of up to `pdiv` divisors, every library op and orientation |
| 2 | `XOR/XNOR(op(d1,d2), d3)` | hash table of the level-1 values, one lookup per `d3` |
| 2 | `op2(op(d1,d2), d3)`, op2 nonlinear | sampled `d3`, op2: the target for `op(d1,d2)` is derived lane by lane (some lanes free) |
| 3 | `XOR/XNOR(op(d1,d2), op'(d3,d4))` | hash lookups over the level-1 table |

Replacing `s` by a candidate keeps every output unchanged on all inputs; the gates only `s`
needed die. Candidates respect the depth caps exactly (arrival of the new root against `s`'s
required level). Each candidate is rebuilt (dead-gate sweep, structural hashing, merging of
gates with identical complete functions when that does not deepen anything) and scored.
Acceptance: the best strict improvement; otherwise a random equal-cost candidate (plateau
walk); otherwise, at temperature T (sawtooth schedule), a worse one with probability
`exp(-delta/T)`, never beyond `max_excess` over the best. After `stall_it` iterations without a
new best the chain restarts from the best. The kernel re-simulates every candidate on the
complete truth table and aborts if an output ever differs (a bug guard). These moves change
nonlinear structure directly: an AND can be replaced by XORs or by a different AND of different
operands, several ANDs in a cone can be replaced by one, and so on.

**Skeleton level** (`kernel/skel.c`). Moves on the AND skeleton that one-gate replacements
cannot make (they need coordinated changes of several ANDs and the linear layers around them),
each verified by Gaussian elimination on the complete truth tables:

- *swap*: replace a leaf AND `g_j` (read by no other AND) by any product `q = L*R` with
  `q = g_j (mod U_j)`, `U_j` the span of the basis without `g_j`; delete `g_j` if no output needs
  it.
- *merge*: for two leaves whose output usage has rank at most 1, replace both by one product
  `q = g_j + g_k (mod U_jk)`: K drops by one (this is how 16 schoolbook products of a GF(2^4)
  multiplication become 9).
- *split* (a kick, K+1) and *perturb* (random operand change, kept if the outputs stay in span).

Operands are searched over every linear form of the inputs (exhaustively for n <= 8) plus
forms built from existing operands and AND outputs. The skeleton objective is
`K + w_lin * E`, E an unshared XOR count. A skeleton becomes gates again by greedy synthesis
of its forms (largest overlap with an existing signal first), and the gate level then
optimises it under the real model.

`cli.py pipe` alternates the two in rounds over a pool of distinct best circuits; a share of
the jobs skips the skeleton level (gate search only), because resynthesis can lose a good
linear layer. `cli.py run` is the gate level alone.

## Verification

Inside the search, the kernel re-simulates every candidate on the complete truth table against
the start circuit's function. Every job's final circuit is checked by `core.Circuit.value_table`
against the target. The reported best circuit of a run (`best.circ.txt`) is checked by two
independent implementations: `core` (bitsliced, AES computed in `targets.py`, S-box tables from
`benchmarks/sboxes.json`) and `independent/verify.py` (written separately from a specification,
no shared code: per-input evaluation, its own AES code, reads the spec table file itself, its
own metrics, library check and cap check). A result counts only when both match the target, the
circuit uses only the model's gates, it meets the caps, and the two metric computations agree
(G, A, GD, AD, cost, counts by type). `campaigns/collect.py` re-runs both checks on every circuit
copied into `results/`. An independent review with fuzzing is in `review/REVIEW.md`.

## Reproducibility

Kernels are deterministic for a given start circuit, config and seed when the iteration
budget (`--iters`) ends the run (the time cap is only a safety stop; the schedule and restarts
count iterations). `summary.json` of every run records the command, the kernel source hash,
all settings, each job's seed, iteration of every improvement, wall time and metrics.
