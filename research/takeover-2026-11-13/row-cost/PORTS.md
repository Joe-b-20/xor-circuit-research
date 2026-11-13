# Exact cost of free and ordinary neighboring blocks

2026-11-13. Hand proof and explicit constructions. This is a local linear-circuit theorem, not a new unrestricted MixColumns bound. The one-free and two-free cases extend the recorded [ten/thirteen-gate proof](../../structure-2026-11-11/tenth-gate/PROOF.md). No literature novelty is asserted.

## Statement

Let `B` be a four-coordinate own block, let `A_1,...,A_p` be ordinary four-coordinate neighboring blocks, and let `C_1,...,C_f` be free four-coordinate neighboring blocks. All coordinates are independent. Ordinary coordinates are available as individual inputs. Every vector supported on any **one** free block is available at zero cost; a vector mixing distinct free blocks is not free.

Write `E_c(B)=sum_{j!=c} b_j` and `s_c(D)=d_c+d_(c+1)`, with subscripts modulo four. Require the four outputs

    t_c = E_c(B) + sum_i s_c(A_i) + sum_j s_c(C_j).

Every paid gate adds two available values, with unrestricted sharing and cancellation. The exact number of paid gates is

    L(p,f) = 6                         if p=f=0;
             3f+7                      if p=0 and f>=1;
             4p+3f+8                   if p>=1.

The same minima hold if whole-block cancellations are forbidden: the constructions below are event-free.

Thus, once at least one neighbor is present, each additional free neighbor costs three gates; the first free neighbor costs four. Starting with free neighbors only, changing the first neighbor from free to ordinary costs two gates, and each later such change costs one. The distinction is the trace interface that must be present in the transpose, rather than four unrelated output attachments.

## Transposition with separately free blocks

Trim to the four target nodes and their ancestors. Delete gates whose values lie entirely in one free block, redirecting readers to that free value; bypass zero operands by wiring. Trim again after these redirections, and repeat until stable. For each remaining use of a free value from `C_j`, introduce its own formal input. Let `tau_j` count these uses and `tau=sum tau_j`. Every such free operand is nonzero, so its block is unambiguous. A gate adding two values from different free blocks remains a paid gate and contributes two uses.

The resulting ordinary circuit has `4+4p+tau` inputs and four terminal outputs. Each formal input is read once, and every ordinary input is live because its column in the target matrix is nonzero. Reverse the circuit by accumulating the adjoints of readers at each signal. If it had `K` gates, the resulting circuit `T`, on four inputs `w_0,...,w_3`, has

    (2K+4) - (K+4+4p+tau) = K-4p-tau

gates. Here a signal with `d` readers, including terminal readers, needs at most `d-1` gates; using this literal accumulation gives the displayed count, even if some adjoints coincide or cancel. The signals of `T` include:

* the four own-block column traces `E_c(w)`;
* when `p>=1`, the four adjacent pair traces `w_c+w_(c-1)` from each ordinary neighboring block (identical traces may be reused across blocks);
* every formal-input trace belonging to every free neighboring block.

For each free block, its four target components `s_c(C_j)` have rank three, with their only nonzero row relation the all-four sum. Consequently the span of its `tau_j` traces contains the three-dimensional even subspace of `F_2^4`. In particular `tau_j>=3`. If `tau_j=3`, its three traces are independent nonzero even signals.

The four triple sums require at least six gates. For completeness, fewer than six would leave at most one gate besides the four odd triple outputs. The first gate must be an even pair or zero. Zero cannot generate a first triple. For a pair `w_i+w_j`, adding inputs can first generate only the two triples containing that pair; the other two triples differ by that pair and each would need the other already present. Thus five gates cannot suffice. Six suffice by computing two complementary pairs and then the four triples.

If `p=0,f>=1`, then either `tau>=3f+1`, giving `K>=6+3f+1`, or `tau=3f`. In the latter case the mirror contains three distinct even signals as well as the four distinct odd non-input triple outputs. They require at least seven gates, so again `K>=3f+7`.

If `p>=1`, the four adjacent pairs and four triples are eight distinct non-input signals, so `|T|>=8` and

    K = |T|+4p+tau >= 8+4p+3f.

The case `p=f=0` is the six-gate triple-sum problem above. These lower bounds allow arbitrary cancellations.

## Construction with only free neighbors

Suppose `f>=1`. In each free block use its available values

    alpha_j = c_j0+c_j1,
    beta_j  = c_j0+c_j2,
    gamma_j = c_j0+c_j3.

Build the following as binary chains; sums of free values from distinct blocks are paid for in these counts:

    U = b_2+b_3 + sum_j alpha_j       (f+1 gates),
    V = b_0     + sum_j beta_j        (f gates),
    W = b_1     + sum_j gamma_j       (f gates).

Then build

    t_0 = U+b_1,
    t_1 = U+V,
    t_2 = (V+W)+b_3,
    t_3 = (b_0+b_2)+W.

The last four rows cost six gates, for `3f+7` in total. The identities `alpha+beta=s_1`, `beta+gamma=s_2`, `alpha=s_0`, and `gamma=s_3` check the free parts. All nonzero block components survive each addition, so this construction is event-free.

## Construction with at least one ordinary neighbor

Suppose `p>=1`. Use the same three free values per free block. Build

    U_0 = b_3 + sum_i a_i1 + sum_j alpha_j,
    U_1 = b_0 + sum_i a_i2 + sum_j beta_j,
    U_2 = b_1 + sum_i a_i3 + sum_j gamma_j,
    U_3 = b_2 + sum_i a_i0.

Starting each chain from its own-block coordinate costs `p+f`, `p+f`, `p+f`, and `p` gates, respectively. Finally build

    t_0 = (U_0+U_3)+b_1,
    t_1 = (U_0+U_1)+b_2,
    t_2 = (U_1+U_2)+b_3,
    t_3 = (U_2+U_3)+b_0.

These eight further gates give `4p+3f+8`. Each output has exactly the required own triple and neighboring pairs. No entire nonzero block is cancelled.

## What the formula says, and what it does not

For a single sheet with several neighboring terms, the same three even traces can serve every free block. The extra mirrored gate needed to expose those traces is paid once, irrespective of the number of free neighbors. Once an ordinary neighbor is present, the four adjacent-pair traces are already mandatory, and the free neighbors add no further mirrored surcharge.

This is different from the [source saturation theorem](FOUR_ROWS.md): that theorem requires alternative four-row output sets using different source blocks, and shows that a locally tight event-free implementation forces physical source-pair gates. Here every output contains all neighboring terms simultaneously. Neither theorem permits local costs from overlapping sheets to be summed without accounting for shared physical gates.

For MixColumns, the local instances are `L(0,1)=10`, `L(0,2)=13`, `L(1,0)=12`, `L(1,1)=15`, and `L(2,0)=16`. These are exact isolated-sheet or free-neighbor costs, not global charges automatically available in a circuit for all 32 outputs.
