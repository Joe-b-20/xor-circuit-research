# Independent review: mirror exits and rank-three exit repair

Hand review of `../MIRROR_EXITS.md` and `../RANK_THREE.md`. No SAT, exhaustive enumeration, circuit search, exact-gate search, or computer-driven case elimination was used. This is not formal verification.

## Mirror no-exit theorem

The reverse-transposition argument is sound with the revised literal-wiring convention. A forward path from a first-group mirror input to a designated `B_i` must at some point pass from nonzero first part to zero first part, so it contains an exit in that `B_i` cone. If there is no such exit, no first-group input has a forward path to a `B` terminal. In the reverse wiring, each adjoint and every partial XOR used to compute it depends only on terminal uses below the corresponding forward signal. Therefore each first-sheet reverse output cone avoids the `B` terminal variables. Substituting free `a`-block forms for export variables cannot introduce a consumer input into those cones.

The export substitution is possible because the desired transpose columns for the `a` block span precisely the even diagonal `D`, which is contained in the span of the designated exports. This is a linear-factorization statement, not a requirement that the export list itself be a diagonal basis when `tau>3`.

After dead-cone trimming, every physical signal has a reader or terminal use. The eight mirror inputs all occur because the target matrix has no zero input column. Summing `d-1` adjoint-combining gates over `|T|+8` physical signals, whose total uses are `2|T|+8+tau`, gives `|T|+tau`. Coinciding, zero, or free adjoints need not be reused to obtain this count. Applying the no-feedback joint 22 bound to this literal reverse circuit proves the inequality.

The correction to the earlier wording matters: replacing a node by an unrelated earlier equal-valued node can introduce consumer-input ancestry into a first-sheet cone. Retaining literal wiring, or bypassing only free/zero/copy results in an ancestry-preserving way, avoids that issue. The later direct-exit classification is now explicitly stated for a reduced mirror rather than silently transferring its conclusion through arbitrary duplicate-value reuse.

## Three-export consequences

With `tau=3`, the three export values span the three-dimensional diagonal and hence are an actual diagonal basis. Treating all zero-first-part values as free leaves the nonzero-first-part gates as an augmented supplier of the four `A_i` and those three diagonal values; the index reflection preserves the diagonal. A12 gives `m>=12`.

If all actual entry labels were even, their span would contain the three-dimensional even space, requiring three distinct nonzero even zero-first-part gate values in addition to the four odd triple outputs `B_i`. The budget would then be at least `12+7+3=22`. Therefore an odd label occurs. The entry-deletion projection bound then raises the augmented portion to `m>=13`, and budget 21 gives `4<=n_0<=5`.

For `n_0=4`, the only such gates are the four `B_i`; zero-first-part inputs and these target values are all odd, so an odd triple cannot be produced by XORing two of them and each target gate is a direct exit. For `n_0=5`, under the reduced and no-direct-`B`-exit assumptions, the one further zero-first-part value must be a nonzero even mask `h`. If `h` is a pair, its two-point translation orbits can seed only the two triples containing that pair; the other two cannot be reached from unit inputs. Thus `h` is the all-ones mask. It must be an exit, since before it there can be no non-exit `B` triple, and two unit inputs produce only a pair. Every `B_i` is then `h` plus the corresponding unit. The note correctly does not claim that this configuration has a compatible thirteen-gate first-part circuit.

## Rank-three chronological repair

At a consumer-bearing gate, its source part is the sum of the source parts of its consumer-bearing operands and any actual zero-consumer entry label. Consumer coordinate inputs start with source part zero. Induction therefore puts the source part of each such node, and the value of each subsequent exit, in the span of entry labels already physically available before that node.

For a set of distinct nonzero available values in a space of dimension at most two, every vector in its span is already available or is one XOR of available values. In dimension three, the only exception is the sum of exactly three available independent values when no fourth nonzero value is available. Once that sum is built with two gates, at least four values in the three-dimensional span are available; every further value in that span is then available or one XOR away. The chronological replay can reproduce each ordinary source-side gate with at most one gate and each exit with at most one, except at most one exceptional exit requiring two. It preserves every original source-side value by its original time and uses at most `G_0+1` gates; for dimension at most two it uses at most `G_0`.

For a ten-gate consumer in the joint problem, entry deletion forces its actual source-side entry labels into the three-dimensional clean diagonal, and the target source parts force those labels to span it. The source-only replay contains the four first-sheet rows and three independent actual diagonal labels, so A12 implies `G_0+1>=12`. If the original total is 21, any cost-preserving replay would contradict A12; thus the stated exceptional three-term exit is necessary. A one-XOR realization using *any* earlier available source values, even outside the clean space, would remove that overhead and is likewise excluded. This is a necessary condition and not a 22-gate unrestricted lower bound.
