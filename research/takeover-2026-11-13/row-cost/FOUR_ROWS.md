# A four-row translation lift that loses its advantage

2026-11-13. Hand argument; no SAT, enumeration, circuit search, exact-gate search, or computer-driven case elimination. The exact event-free lower bound below is a symbolic proof with a matching explicit construction. It concerns a specified family and does not change the MixColumns interval or assert generic additivity for all `Q_T` circuits.

## Result

A direct lift of the shared-hidden-value mechanism to all four structured `E_c/s_c` rows does **not** retain its earlier advantage. For each `r>=8`, the concrete map below has event-free complexity exactly `22r+8`. Its natural four-translation circuit uses `22r+12` gates, four more, despite sharing the same four cancellation translations across all `r` sheets. Its hidden count is exactly eight. The output rows have weight five or seven, their boundary relation distance is six, and the output windows have at most three blocks of dimension at most four.

The explanation is structural: in an event-free circuit, a sheet producing both four-row variants needs at least 14 own-block-carrying gates. Meeting this minimum forces all four source pairs for **each** of the two common blocks to exist. Across many sheets those eight pair gates can be shared, so the clean event-free circuit pays only a constant eight-gate overhead. Building the four cross-block translations and cancelling them at every target adds four more gates. This rules out this particular economical lift; it does not rule out other architectures that share different intermediates or trade extra work for savings.

## The map

Let `X={x_0,...,x_3}` and `Y={y_0,...,y_3}` be common four-coordinate blocks. For each sheet `i=1,...,r`, let `Z_i={z_i0,...,z_i3}` be a private four-coordinate block. For each `(i,c)` with `c=0,1,2,3`, let `W_ic={w_ic0,w_ic1}` be a private two-coordinate block. All these coordinates are independent. Indices on `c` are modulo four.

For any four-coordinate block `B`, write

    E_c(B) = sum_{d != c} B_d,
    s_c(B) = B_c + B_(c+1).

The required `8r` outputs are the four target rows and four tagged partner rows

    F_ic = E_c(Z_i) + s_c(X),
    A_ic = E_c(Z_i) + s_c(Y) + w_ic0 + w_ic1.

Each `F_ic` has weight five and each `A_ic` weight seven. Windows are `{X,Z_i}` for `F_ic` and `{Y,Z_i,W_ic}` for `A_ic`. A natural own block is `Z_i` for the four-row `F_i` sheet and `W_ic` for the one-row `A_ic` family. They are all distinct, with no reciprocal own-block incidence. Each `{X,Z_i}` is a maximal clique, since the only neighbours of `X` are the mutually nonadjacent blocks `Z_j`. Every output is supported in its stated window.

The full output set is independent: each `A_ic` has private coordinates, so its coefficient in a relation must vanish; for each `i`, the four `E_c(Z_i)` are independent (their matrix `I+J` satisfies `(I+J)^2=I` over `F_2`). The map is rectangular, has common blocks of increasing incidence degree, and has one-row tagged families in addition to its genuine four-row sheets. It is not MixColumns.

## The direct shared-translation circuit

Compute the eight source pairs `s_c(X),s_c(Y)` in eight gates, then compute

    h_c = s_c(X) + s_c(Y)                         (four gates).

For each `Z_i`, compute the four `E_c(Z_i)` in six gates: compute `z_i0+z_i1` and `z_i2+z_i3`, then add the missing third coordinate to obtain each of the four triples. Form

    p_ic = E_c(Z_i) + s_c(Y),
    F_ic = p_ic + h_c,
    A_ic = (p_ic + w_ic0) + w_ic1.

There are `12+6r+4r+4r+8r = 22r+12` gates. All `4r` target gates `F_ic` are events, cancelling the entire `Y` block. The four gates `h_c` are nonlocal, and the four `s_c(X)` gates are local but hidden: all their paths to outputs pass through a target event. Every other gate has an event-free continuation to some `A_ic` output. Thus `H=8`, and these eight physical gates are shared across arbitrarily many target sheets. The circuit is reduced and live: the clean source pairs, translations, own-block sums, untagged partners, final targets, and tag prefixes are all distinct non-input values, and every gate serves an output. Direct evaluation of this specified construction at `r=8` checked all 64 output masks, 188 distinct gates, 32 target events, and exactly eight hidden gates; the general claims follow from the displayed symbolic construction.

## A 14-gate charged lower bound per sheet

First ignore the private tags and require both

    F_ic = E_c(Z_i)+s_c(X),       P_ic = E_c(Z_i)+s_c(Y)

for all `i,c`. Take any reduced event-free circuit for these `8r` values. Support grows along every edge. A gate carrying `Z_i` and feeding an `i`-sheet output is supported either on `Z_i` alone, on `{X,Z_i}`, or on `{Y,Z_i}`. No gate carrying `Z_i` can feed an output for a different sheet, and a gate carrying both `X` and `Y` can feed neither variant.

Fix `i`. Let `n` count its distinct pure-`Z_i` ancestor gates, `u` its gates carrying both `X` and `Z_i` that feed an `F` output, and `v` its gates carrying both `Y` and `Z_i` that feed a `P` output. By the established ten-gate local sheet lemma, treating all vectors of `X` as free gives `n+u>=10`, and treating all vectors of `Y` as free gives `n+v>=10`. Each side also has four distinct output gates, so `u,v>=4`. Therefore

    n+u+v >= n + 2 max(4,10-n) >= 14.             (1)

These charged gate sets are disjoint across sheets, because `Z_i` occurs in no other sheet's output support.

If equality holds in (1), then necessarily `n=6` and `u=v=4`, so every mixed `X,Z_i` gate is one of the four `F` outputs, and every mixed `Y,Z_i` gate is one of the four `P` outputs. These outputs cannot be used to build one another within their side:

* `F_ic+F_id` has nonzero components on both `X` and `Z_i` for `c!=d`, so neither is the other plus a pure-`X` or pure-`Z_i` value.
* `E_c(Z_i)+E_d(Z_i)` has even weight, whereas each `E_e(Z_i)` has odd weight. Thus two prior `F` outputs cannot sum to a third. The same argument applies to the `P` outputs.

It follows that each `F_ic` gate combines a pure-`Z_i` value with a pure-`X` value, which must be exactly `E_c(Z_i)` and `s_c(X)`. Likewise every `P_ic` requires the pure-`Y` value `s_c(Y)`. Hence equality for even one sheet forces all eight distinct non-input source pairs `s_c(X),s_c(Y)` to exist as physical gates outside every sheet's charged set.

If all eight exist, the whole circuit has at least `14r+8` gates. If even one is absent, equality is impossible in every sheet, so each sheet has at least 15 charged gates and the total is at least `15r`. Thus, for every `r`,

    G_eventfree(untagged) >= 14r + min(r,8).          (2)

The clean construction computes eight source pairs, six `E` gates per sheet, and eight output gates per sheet, attaining `14r+8`. In particular, (2) is exact for `r>=8`.

## Saturation theorem for any number of source blocks

The same interface argument applies to any `k>=2` independent four-coordinate source blocks `X_1,...,X_k`. For each of `r` disjoint own blocks `Z_i`, require all `4k` rows

    F_ijc = E_c(Z_i) + s_c(X_j),       j=1,...,k; c=0,1,2,3.

Every row has support on exactly its own block and one source block. Any event-free circuit for these outputs has

    G >= (6+4k)r + min(r,4k).                         (3)

For `r>=4k` this is exact: compute the `4k` source pairs once, the four own-block triples in six gates per `Z_i`, and each of the `4kr` output rows in one further gate. The result is `(6+4k)r+4k`.

To prove (3), let `n_i` be the number of pure-`Z_i` gates feeding the `i`th outputs, and let `u_ij` count its mixed `{Z_i,X_j}` gates feeding the `j`th variant. Support growth makes the mixed sets disjoint for different `j`, and disjoint across different own blocks. The ten-gate local lemma gives `n_i+u_ij>=10`, while the four output gates give `u_ij>=4`. Hence

    n_i + sum_j u_ij >= n_i + k max(4,10-n_i) >= 6+4k.

For `k>=2`, equality forces `n_i=6` and every `u_ij=4`. The argument immediately above then forces all four pure source pairs of every `X_j` to exist. If all `4k` pairs exist, they give `4k` gates outside the disjoint charged sheet sets. If any pair is absent, every sheet has at least one extra charged gate. Taking the weaker of these two alternatives proves (3).

The qualification `k>=2` matters: with only one source, the numerical inequality can attain ten without forcing exactly six pure own-block gates. This theorem concerns several **alternative outputs**, one per source block, that share the same own-block triple. It is not the different multi-neighbour problem in which a single output row contains several source-block terms simultaneously. It counts physical gates and uses only the hand-proved ten-gate lemma, not optimization of a finite circuit family.

## Restore the tags

The `8r` private coordinates appear one by one in their own designated `A_ic` outputs. Zero them successively, normalizing ordinary XOR circuits after each restriction. Each not-yet-zeroed coordinate still occurs in its projected `A_ic` together with the nonzero `E_c(Z_i)+s_c(Y)`, so its earliest live direct reader disappears when it is zeroed. At least `8r` gates are lost. Intermediate restrictions can introduce events inside a partially zeroed private block; they are not assumed event-free.

After all private coordinates are zero, the cumulative projection removes complete private blocks. Equal-value redirects remain equal after further projections, so every surviving original gate has its original operand values projected onto the remaining blocks. Any final whole-block cancellation would therefore already have been present at that original gate. The final circuit is event-free and computes the untagged `F,P` map. Combining (2) with the deletion count gives

    G_eventfree(tagged) >= 22r + min(r,8).

For `r>=8`, the clean construction above followed by the two private-coordinate attachments for each `P_ic` meets `22r+8`. Thus the tagged event-free minimum is exactly `22r+8` in this range.

## Boundary relation distance six

A linear relation among distinct coordinate inputs and outputs is uniquely specified by a chosen nonempty output subset and the support of its XOR. If at least two tagged `A` rows are chosen, their disjoint two-coordinate private tags give at least four surviving input coordinates, and the two output vectors make relation weight at least six. If exactly one `A` and at least one `F` are chosen, its two private coordinates and its two `Y` coordinates survive, again giving at least six. A single `A` alone gives weight eight.

With only `F` rows, consider the `q` chosen rows of one sheet. Their own-block contribution has weight 3, 2, 1, or 4 for `q=1,2,3,4`, respectively. Hence `q` plus that weight is at least four for every nonempty sheet. Two or more sheets already give relation weight at least eight. For one sheet with `q=1,2,3`, the sum of its `s_c(X)` components is nonzero and has even weight at least two: the four cycle-edge pairs have only their all-four relation. The relation weight is at least six; for `q=4` it is eight. A single weight-five `F` row and its five input coordinates attain six.

## Scope and dependency

The lower bound invokes the established ten-gate sheet lemma; no analogous statement is asserted without it. This family has all four `E_c/s_c` rows on each selected sheet, but has extra tagged partner outputs and a common predecessor block whose incidence grows with `r`. Its result does not prove that all four-row XOR circuits are additive or that shared cancellation cannot help. In particular the established 28-gate `Q_3` construction remains compatible: it uses a different cyclic sharing architecture and saves two gates against a 30-gate block-monotone bound.
