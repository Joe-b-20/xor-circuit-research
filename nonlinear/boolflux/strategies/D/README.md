# Track D: exact SAT resynthesis of multi-output windows

Files (all in `nonlinear/boolflux/strategies/D/`):

| file | role |
|---|---|
| `wresyn.py` | library: circuit analysis, window growth, Boolean-relation flexibility, SAT encoding, replacement |
| `run.py` | optimiser driver (modes `g` and `depth`), logs and best circuits |
| `kern.py`, `bfx.c`, `bfx` | private copy of the BoolFlux gate kernel (`kernel/bfx.c` at 0659eb9, `lex cost,a,gd`) and a Python wrapper |
| `breathe.py` | cycles: windows at GD+1, kernel repair/anneal at GD, windows polish at GD |
| `control.py` | control for breathe: the same kernel alone, same caps and wall time |
| `fairtest.sh` | the final breathe-vs-control queue (one CPU per queue) |
| `probe.py`, `bench_sym.py`, `sanity.py`, `validate.py`, `prof.py`, `frontier.py` | diagnostics (`validate.py`: the original window must satisfy its own encoding; `bench_sym.py` now compares full vs incremental pattern solving) |

`wresyn.solve(..., cegis=True)` solves on 12 constrained patterns and adds failing ones
incrementally; the 2026-11-14 bench decided fewer windows than the full encoding, so the
default is the full encoding.

## Usage

    cd nonlinear/boolflux/strategies/D
    # shrink G at the start circuit's own caps (or give --cap-gd/--cap-ad/--cap-a)
    taskset -c 10 python3 run.py --start FILE.circ.txt --out DIR --seconds 3600 --seed 1
    # pull the gate depth down to T, spending at most GMAX gates in total, then shrink G at T
    taskset -c 10 python3 run.py --start FILE --out DIR --mode depth --target-gd T --gmax GMAX

Window parameters: `--kmin/--kmax` window gates, `--cmax` cut inputs, `--mmax` window outputs,
`--ndiv` extra divisor inputs, `--budget` CaDiCaL conflict budget per SAT call.
Every accepted circuit is re-simulated on all 256 inputs (`wresyn.correct`); improved circuits
are written as NCFF with a JSON sidecar (start, command, seed, move list, time to result).
Claimed circuits must also pass `campaigns/aes_check.py`.

## Window and flexibility

1. **Window**: grown from a seed gate by adding random fanin or fanout gates (in depth mode
   preferring critical ones), then made convex: every outside gate on a path between two window
   gates is added, so replacing the window cannot create a cycle.  Cut inputs = signals outside
   the window read by it; outputs = window gates read outside or driving primary outputs.
   Optionally up to `ndiv` extra divisor signals (outside the window and its transitive fanout,
   two levels around the window) are added as free inputs.
2. **Exact relation**: with `m` outputs, for each of the `2^m` output vectors `v` the transitive
   fanout of the window is re-simulated (all 256 S-box inputs bit-parallel) with the window outputs
   forced to `v`; `ok_v` = inputs where all 8 S-box outputs stay correct.  Inputs with the same
   window-input pattern `p` form a class `X_p`; the allowed set at `p` is
   `{v : X_p subset of ok_v}`.  Patterns never occurring are unconstrained.  This is the complete
   flexibility of the window (satisfiability and observability don't-cares, jointly over outputs).
3. **Timing**: arrival = current gate level / AND level of each window input; required level of a
   window output = cap minus its longest outside path to a primary output (gate count / AND count).

## SAT encoding (r gates over c window inputs, P occurring patterns, m outputs)

Variables: `l[i][j]`, `r[i][j]` (gate i's left/right operand is signal j, j < c+i), `t[i][T]`
(type T in {AND, XOR, XNOR, NOT}), `a[i][p]`, `b[i][p]` (operand values), `x[i][p]` (gate value),
`w[o][s]` (output o is signal s, inputs included), `y[o][p]` (output value), unary depth
`D[s][l]` = level(s) >= l and `E[s][l]` = AND-level(s) >= l.

- exactly one of `l[i][*]`, `r[i][*]`, `t[i][*]`, `w[o][*]` (pairwise or sequential counter);
- binary gates: `l < r` (clauses `-l[i][j] -r[i][k] t[i][NOT]`, k <= j); NOT: `r = l`;
- operand values: `l[i][j] -> (a[i][p] <-> x[j][p])` (a unit-conditioned literal when j is an input);
- semantics per (i, p): `t_AND -> x = a & b`, `t_XOR -> x = a ^ b`, `t_XNOR -> x = ~(a ^ b)`,
  `t_NOT -> x = ~a` (13 clauses);
- outputs: `w[o][s] -> (y[o][p] <-> x[s][p])`;
- relation per pattern p: outputs fixed over all allowed vectors become units; every forbidden
  vector agreeing with them is a blocking clause over the free outputs;
- every gate is used by a later gate or an output;
- symmetry: adjacent independent gates in co-lexicographic order of (right, left) operand;
- depth: `D[g][1]`, `D[g][l+1] -> D[g][l]`, operand j selected -> `D[j][l] -> D[g][l+1]` (inputs:
  `D[g][arr_j + 1]`), output o on gate s -> `-D[s][req_o + 1]`; same for AND depth with
  `E[j][l] -> E[g][l]` and `t_AND & E[j][l] -> E[g][l+1]`;
- AND count: sequential-counter at-most-`amax` over `t[i][AND]`.

Mode g tries `r = k-1, k-2, ...` with `amax` = the A cap's room, and if `k-1` fails, `r = k`
with one AND fewer.  Mode depth takes required levels from the target cap T and accepts the
smallest r in `[k-2, k+slack]` (total G <= gmax); the number of critical signals
(level + tail > T) then strictly decreases, so the loop terminates at GD <= T or stalls.

## Results (2026-11-14 AES push)

- Mode g at the frontier caps (grow and cut windows, k up to 9-12, A cap raised by up to 4):
  0 improving windows out of ~3,900 on published 103/116/124(A28)/127/133 and the kernel results
  108@19, 124@14, 131@13 (about 60% UNSAT, 40% over a 30k-conflict budget). Depth mode (GD-1): 0 of ~115.
- With the GD cap relaxed by one, windows find occasional -1 steps (127->126@15, 133->132@14); the
  kernel repair back to the cap undid them every time.
- Breathe vs kernel-alone control (18 min each, one CPU): 127@14 -> 125@14 (B) vs 127 (C);
  133@13 -> 133 / 133; 124@14 -> 121@14 A37 (B) vs 122@14 A37 (C). In both B gains the window stage
  returned its input unchanged, so the gain is the kernel stage's. Circuits and checker output:
  `~/xs-campaigns/2026-11-13-aes/D/found/`; logs: `~/xs-campaigns/2026-11-13-aes/D/fair/`.
- Conclusion: published and kernel-optimised AES circuits are locally exact-optimal for windows of
  up to about 9-12 gates at their caps; this mechanism added nothing over the gate kernel.
