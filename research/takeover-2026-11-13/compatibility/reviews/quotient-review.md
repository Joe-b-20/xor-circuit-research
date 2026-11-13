# Independent review: quotient entry deletion and eleven-gate traces

Hand review of `../QUOTIENT.md`. No SAT, enumeration, exact-gate search, or computer-driven case elimination was used. This is not formal verification.

## Verdict

The occurrence-deletion certificate, the four-triple `10+c` bound and sharp construction, the mixed-label eleven-gate classifications, the clean-label count restrictions, and the displayed five-entry example are correct in the stated free-vector-space model. Repeated labels, repeated traces, and zero labels are handled by different arguments and cannot be conflated. These statements constrain possible interfaces; they do not rule out the all-clean joint profile or prove a 22-gate bound.

## Occurrence deletion and `10+c`

Once ordinary-zero-part values are taken as free, each counted gate has nonzero ordinary part and reads at most one free operand. If selected entry labels span `C` with `C intersect D=0`, extend `C` to a complement of `D` in the actual label span and project along it onto `D`. This fixes every designated target and kills every selected free operand. The corresponding distinct physical entry gates can all be bypassed, even when chained: each redirected value is exactly the projected original gate value. Deleting additional duplicates or dead gates can only reduce the count. Thus `K>=L_D+|I|`. The chosen labels need not be independent; repeated nonzero labels and the zero label are legitimate occurrences and each selected occurrence deletes a separate gate.

For the four-triple case, the formal target coefficient matrix `Z` has row space `L`, and the label map sends `L` onto the rank-three target-label span `D`. Hence `r=dim L` is three or four. The composite map to `U/D` has rank `c` and annihilates `L`, so `tau>=r+c`. The four-input transpose has `K-tau` gates and includes the own triples and all entry traces. When `r=3`, the label map is injective on `L`, so the four formal target rows sum to zero and every trace has even weight. Their rank three requires three distinct nonzero even gate signals besides the four odd triple outputs, giving at least seven mirrored gates. When `r=4`, the usual triple-sum argument gives at least six. Both branches yield `K>=10+c`, including zero and repeated trace occurrences.

The displayed baseline construction has the required target free parts by the four identities involving `alpha,beta,gamma`; replacing the single `alpha` entry by the specified `c+1` chained entries increases the cost exactly by `c`, keeps the resulting value unchanged, and makes the entry span have quotient dimension exactly `c`. It is an admissible free-label construction; whether an external producer actually supplies those labels is a separate question.

## Mixed eleven-gate classifications

For `c>0`, the bound gives `c=1,K=11`. Since `F_2` has one nonzero element, all nonclean labels have the same nonzero quotient signature. The occurrence-deletion certificate excludes two occurrences of one nonclean value and also excludes a zero-label entry alongside a nonclean entry. Equality in the transpose inequalities leaves only `(tau,r)=(4,3)` and `(5,4)`.

The quotient map on formal coordinates is the functional whose support is the nonclean occurrence set `N`. Since `L` has dimension `tau-1` in either branch and lies in its kernel, `L=N^perp` and the only trace relation is the indicator of `N`.

For `(4,3)`, the label map has four-dimensional image and is injective. Three independent even traces require exactly the three gate masks beyond the four triple outputs of the seven-gate mirror. A zero trace would require an additional zero signal, while a fourth distinct trace would also exceed that budget. Thus the four occurrences consist of exactly three distinct nonzero masks, with one repeated twice. The sole trace relation identifies the repeated pair as exactly the two nonclean occurrences. The two clean labels and the sum of that pair are images under an injective label map of a basis of the three-dimensional quotient kernel, hence form a basis of `D`.

For `(5,4)`, the label map has a one-dimensional kernel. The trace-parity vector is nonzero because `Z` has full row rank; it maps to the sum of all four target labels, namely zero, and hence generates that kernel. It lies in `L=N^perp`, proving that the number of odd nonclean traces is even. A six-gate transpose has exactly four triple gates and two other nonzero even gate masks: a zero or duplicate signal could be bypassed to obtain a forbidden five-gate triple circuit, and every nonzero odd four-bit mask is an input or a triple. The stated cases for two, three, four, or five nonclean occurrences follow. In particular a repeated trace would give a two-coordinate trace relation and is possible only when `|N|=2`.

The clean-label dimension formula follows by restricting the unique label-kernel line to the coordinates of clean occurrences: it subtracts one exactly when that kernel vector is supported wholly there. Conversely, a rank-four trace matrix with sole relation `N` makes `Z^T` injective; defining the label map on its image by the target labels and extending once outside `D` produces the claimed algebraic label geometry. This does not assert circuit or producer realizability.

For the fixed five-entry example, `A` has free part `d1`, `B` has free part `d3`, and `lambda=d0+d1=d2+d3`. The four displayed outputs have free parts `d0,d1,d2,d3` and the correct own triples. Its gate count is five before the outputs and six for them, totaling eleven. The two nonclean entries `h,h+d1` occur consecutively on the same wire and thus have the same even `{0,1}` trace. The repeated clean `lambda` enters separately at rows 0 and 2, giving distinct odd singleton traces. This explicitly distinguishes label repetition from trace repetition without relying on a search.

## Clean-only interfaces and scope

When `c=0`, the same bounds give the four listed `(tau,r)` possibilities: `(3,3)`, `(4,3)`, `(4,4)`, `(5,4)`, with the corresponding mirror sizes. For `(4,3)` the seven-gate budget again permits three distinct nonzero even traces with one repetition. For `(5,4)` the label kernel is two-dimensional, so parity gives one relation but need not be the unique one. A zero entry can be selected as an occurrence-deletion certificate by itself; at most one is possible at `K=11` given the ten-gate lower bound.

The producer-facing conclusion is therefore a necessary interface condition only. The proof does not charge a virtual difference as a physical producer gate, does not show that every algebraically allowed trace set is executable, and leaves open whether an actual ten-gate producer can serve a tight consumer or whether an all-clean case reaches the joint lower bound.
