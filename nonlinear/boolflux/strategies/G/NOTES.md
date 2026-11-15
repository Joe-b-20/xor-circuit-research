# Track G: direct nonlinear-basis search for an AES S-box circuit with <= 27 AND gates

Evidence tags: **[C]** exhaustive/exact computation (solver named), **[V]** verified on all 256
inputs (aes_check), **[H]** heuristic search result (method, budget and calibration given; a
negative [H] result means "not found", not "impossible").

Notation as in `strategies/C/NOTES.md`: x the input byte, N = x^17 (GF(16) norm), n = N^-1,
T = the 8 S-box output tables, V_N = span of N's 4 coordinates (quadratic forms in x),
V0 = functions of N (16-dim), Quad = quadratic forms in x (28-dim), O = span(x, N, n) (16 dims).
A28 files: AD5 = aes-sbox-a28-ad5-g124 (10 | 5 | 13), AD4 = aes-sbox-a28-ad4-g131-gd31 (9 | 6 | 13).
Runs and logs: `~/xs-campaigns/2026-11-14-G/` (STATUS.md there).

## 1. Tools (all in this directory)

| file | what |
|---|---|
| `nlb.c` | generic basis local search: K products, each an AND of two XORs of (1, inputs, earlier products); score = rank deficit of target groups (targets + free addends) modulo the span; moves = operand bit flips (SA) and exact/sampled re-choice of a slot. Optional q-mode (quadratic targets via ANF, min-rank residual score) and coset-distance score. |
| `llay.c` | exact coordinate descent for a last AND layer over a space E: one move re-chooses one slot over ALL products l*m, l, m in O (Gray code over l, linear solve for m), uniformly among the deficit-reducing ones. Extensions: stage-1 slots (exact re-choice over all 10795 rank-2 forms, N required in their span), junk slots (free vectors of a space, exact; or best of a list), feasibility mode (score = junk deficit + 10 x deficit with a whole extra space F free), multi-solution mode (dump plateau states, kick). |
| `nlbprob.py`, `aes_prob.py`, `ll_prob.py`, `relax.py` | problem files, solution -> circuit builders. |
| `inv_fit.py`, `midfit.py`, `sat_small.py`, `inv_classes.py` | middle stage as a 4-bit problem on the 16 values of N: requirement of a (stage 1, last layer) pair; nlb fit; exact SAT (CHM encoding with addends); sampling of the product spans of 5-AND GF(16) inversions. |
| `eval3.py`, `eval_v.py`, `cover_cli.py` | three-stage evaluation of a last layer: split of the junk into quadratic and N-function parts; exact stage-1 cover of U = V_N + quadratic junk (track C's cover_enum when l - dim U <= 2, else SAT); 4-bit middle fit; circuit + aes_check on success. |
| `subsets.py`, `lns_sat.py` | which members of a published layer a K-member layer over E can keep (all 2^13 subsets, exact), and SAT on those neighbourhoods (track C's qmc model). |
| `small.py` | calibration driver on small functions. |
| `walk.py`, `camp3.py` | long-run drivers. |

All builders were validated by rebuilding A = 28 circuits that pass `campaigns/aes_check.py`
**[V]**: llay layer over the AD5 prefix; joint stage-1 + last layer; relaxed layer + AD5 level 1;
AD4 level 1 + an nlb-found 6-AND middle + AD4 layer (A 28, AD 7).

## 2. Calibration on known cases

### 2.1 Generic basis search (nlb) **[H]**

| target | K | depth | runs solved | limit | best deficit (unsolved) |
|---|---|---|---|---|---|
| GF(16) inversion (MC 5 [C, track C SAT]) | 5 | any | 5/5 (0.03-1.5 s) | 20 s | - |
| GF(16) inversion | 4 | any | 0/2 | 10 s | 1, 1 (correct: MC = 5) |
| PRESENT (MC 4) | 4 | any | 5/5 (0.01-0.03 s) | 20 s | - |
| GF(16) multiplication, 8 -> 4 | 9 | level 1 | 0/3 | 60 s | 1, 2, 1 |
| x -> x^17 coordinates (V_N) | 9 | level 1 | 0/3 | 60 s | 1, 2, 2 |
| U of AD4 (V_N + 2 junk forms; the AD4 file's 9 products span it) | 9 | level 1 | 0/1 | 240 s | 2 |

Fine scores (coset distance by Gray code, min-rank of the residual alternating form) made the
8-bit cases slower (<= 1000 evaluations/s) and not better within 60 s.  Conclusion: a generic
deficit-scored basis search finds optimal 4-bit circuits instantly but cannot solve 8-bit,
9-product quadratic covers that SAT solves in 33 s; a from-scratch search for a 27-product AES
basis with it would be meaningless, so it was not used as evidence.

### 2.2 Exact last-layer coordinate descent (llay) **[H]**

Over the AD5 prefix (10 + 5 products), K = 13, start = published layer with R slots random:

| R | solved / runs (60 s) | best deficit of the others |
|---|---|---|
| 4 | 1/1 (2 s) | - |
| 6 | 0/3 | 2, 2, 1 |
| 8 | 0/3 | 1, 1, 1 |
| 10 | 0/3 | 8, 5, 6 |
| 13 (scratch) | 0/3 | 8, 8, 8 |

From scratch no single product of O x O ever reduces the deficit (the useful products only work
in combination: the 5 "junk" dimensions of the layer must cancel).  Every layer the walks found
near the published ones is of GF(4)-norm type (x-parts of the two operands in ratio w or w^2:
13/13 products in each checked layer) **[V]**.  Feasibility-mode walks (junk minimised, all
quadratic forms allowed) reach valid 12-member layers from "published layer minus one" in
about a minute (junk 7-8).

### 2.3 Exact middle-stage DFS (exact_mid.py) **[C]**

Positive control: the product span of the AD5 inversion (g124 and g150 files) is re-found in
0.01 s; a circuit built from the DFS middle + AD5 level 1 + AD5 layer passes aes_check
(A 28, AD 6) **[V]**.

## 3. AES results

### 3.1 Three-stage accounting (exact parts)

Every output must be  T = (last-layer part) + q + r + affine  with q in Quad, r in V0.  For a last
layer LL with operands in O, the extra space it needs over span(1, x, N, n, LL) splits into
quadratic junk Wq (stage 1 must span U = V_N + Wq) and N-function junk (the middle must span n plus
it).  Then #AND = l + m + K with l >= cover(U) and m >= MC of span(n, N-junk) on the 4 bits of N.

* **5-AND middles realise exactly 30 of the 127 possible 5-dim spaces span(n) + <v>** (v taken mod
  span(1, N, n)) **[C, exhaustive DFS: with 5 products and a 5-dim target every product must lie in
  the target span + affine, so the search over all operand pairs is complete]**.
* AD5 layer: needs only n and dim U = 7 (3 quadratic junk forms); U is not spanned by 9 level-1
  products (track C's cover lemma, exact) -> l = 10, total 28.
* AD4 layer with AD4 level 1: needs n plus one N-function r, dim U = 6 (2 quadratic junk; the
  file's 9 level-1 products span it).  r is NOT in the 30 classes: **no 5-AND middle (operands
  functions of N) exists for this pair [C, DFS]** (one hour of CHM SAT did not finish; nlb deficit
  1).  So AD4 needs a 6-AND middle: total 28.  Consistently, AD4 level 1 + AD5 inversion + AD4
  layer (27 ANDs) misses exactly one output dimension [C].
* The two published designs sit on opposite sides: AD5 pays in stage 1 (dim U = 7), AD4 in the
  middle (r outside the 30 classes).  A 27 in this 3-stage family needs a 13-member layer with
  quadratic junk 2 and N-junk in the 30 classes (or junk 3 with a 9-coverable U), or a 12-member
  layer with cover(U) <= 10 and N-junk in the 30 classes.  The long runs search exactly this.

### 3.2 Keep-sets of the published layers (subsets.py) **[C]**

A K-member layer over a fixed prefix E that keeps a subset X of a published layer needs
d(X) = dim(T + E + X) - dim(E + X) <= K - |X|.  Over the AD5 prefix with K = 12: at most 11
members can be kept ({1,2,4,...,11,13} with d = 1: one new product must then fix the last output
dimension, which the exact walk never found); the published layer is far from generic
(min d by kept size 0..13: 8 8 7 7 6 5 5 4 3 3 2 1 1 0, generic 8 8 8 8 8 8 7 6 5 4 3 2 1 0).
Over AD4-L + AD5-inv with K = 13: the AD5 layer keeps at most 8 members (d = 5); the AD4 layer
is complete except one dimension (d(13) = 1).

### 3.3 Walks (exact moves) over last layers, evaluated exactly

(results at the end of the push; live: `~/xs-campaigns/2026-11-14-G/STATUS-auto.md`)

## 4. Pitfalls met

* An early junk-slot walk did not start the junk slots at their exact best response, so plateau
  moves of the layer drifted away before the junk was re-chosen; the statements of 18:40-19:20
  that "12-member layers stay at deficit 1 even with 12 free junk forms" were artefacts and are
  withdrawn (fully relaxed walks reach valid 12-member layers in 30 s).
* Full relaxation (all quadratic forms and N-functions free) lets the junk grow (dim U = 12): the
  walks must minimise the junk (feasibility mode, score = junk + 10 x infeasibility).
* pysat's interrupt timer did not stop CaDiCaL inside one process; long SAT calls now run in a
  subprocess with a wall-clock timeout (cover_cli.py).
