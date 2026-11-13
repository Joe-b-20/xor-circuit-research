# A ten-gate sheet cannot supply five values in one clean-diagonal coset

2026-11-13. Hand proof only. No search, enumeration, exact circuit optimization, or computer-driven case elimination. This proves an actual supplier incompatibility for the eleven-gate interface theorem from `../row-cost/JOINT01.md`. It leaves the joint 21-to-22 gap and the unrestricted MixColumns interval unchanged.

## Main result

Let `a,b` be four-coordinate blocks. All vectors on `a` are free, and the four coordinates of `b` are inputs. Write

    E_c = sum of the three coordinates other than c,
    s_c = e_c+e_(c+1),                    indices modulo four,
    U_c = E_c(b)+s_c(a).

Let `C` be any ten-gate circuit computing all four `U_c`. Its available values consist of its gates, the coordinate inputs of `b`, and all free vectors on `a`. Define the three-dimensional clean diagonal

    D = { v(b)+v(a) : v has even weight }.

**Theorem S.** Every affine coset of `D` contains at most four distinct available values of `C`.

The word "four" is an upper bound; no attainment claim is made for every coset or for the overall maximum. The theorem includes the zero coset. Free values and input values count as available, so this is exactly the kind of supply statement needed by a subsequent sheet.

**Joint 0/1 consequence.** Under the existing hypothesis that no ancestor of a sheet-0 output touches block 1, a hypothetical 21-gate joint circuit whose first-sheet side has ten gates and whose second-sheet side has eleven gates must use at least one actual clean-diagonal entry label in the second sheet. An eleven-gate second sheet using only nonclean labels is impossible: Theorem N forces five distinct labels in one nonzero coset of `D`, while Theorem S says that the ten-gate supplier cannot provide them.

## Basic ten-gate facts

The four-target local sheet minimum is ten, by the hand-proved ten-gate lemma. Consequently a ten-gate realization can be reduced and restricted to target ancestors without losing any gate: otherwise a circuit with fewer than ten would remain. In particular, no counted gate is wholly free, zero, or a duplicate of another available value.

Write each value as `(beta | alpha)`, where `beta` is its `b` part and `alpha` its `a` part. Every gate has `beta!=0`. Call a gate an entry if exactly one operand is free, and let `tau` be the number of entries.

The transposition proof of the ten-gate lemma gives:

* `tau>=3`, since the target `a` parts span the three-dimensional even subspace;
* a transpose with `10-tau` gates computing the four triple sums;
* `10-tau>=6`, so `tau<=4`.

**Parity confinement.** Every actual entry label, and hence every gate's `alpha` part, is even.

If `tau=3`, its three labels span the required even space and therefore belong to it. If `tau=4` and an odd label occurs, the four labels span the whole four-dimensional `a` space. The formal label map is then injective. The unique all-four relation among the target free parts also holds formally, so all four influence traces are even and span a three-dimensional space. The transpose would need three distinct even gate values besides its four odd triple-sum gates, hence at least seven gates. But with four entries it has exactly six. This contradiction proves confinement.

This argument concerns labels actually used by the ten-gate supplier. Arbitrary odd free vectors on `a` are still available as potential operands of a later computation.

## Named values and residues

Let

    N = { b_0,b_1,b_2,b_3,U_0,U_1,U_2,U_3 }

be the eight named values, and define the residue

    rho(beta | alpha) = beta+alpha,

identifying corresponding coordinates of the two blocks.

All computed values have even `alpha`. On that subspace the kernel of `rho` is exactly `D`. Thus, for computed values and `b` inputs, equality of residues is equivalent to belonging to the same `D` coset.

The named residues are

    rho(b_i)=e_i,
    rho(U_c)=E_c+s_c=E_(c+1).

They are precisely the eight different odd vectors of a four-coordinate space, each occurring once.

The named values have one and only one nonzero linear relation: the sum of all eight is zero. Indeed, a relation selecting a subset of the `U_c` has zero `a` part only when that subset is empty or all four, because the `s_c` have only their all-four relation. The empty subset leaves independent `b` inputs; the full subset sums to all four `b` inputs, so all four must be included. Therefore the named values have rank seven.

In particular, **each nonzero value has at most one representation as the sum of an unordered pair of distinct named values**. Two different pairs with the same sum would give a nonzero relation among at most four named values, contradicting the preceding paragraph.

## Proof of Theorem S: even own-block parity

Suppose a `D` coset contains five distinct available values. Its `alpha` parity is constant, because every element of `D` has even `alpha`. If that parity were odd, parity confinement would exclude every computed gate and every `b` input. The coset meets the free `a` space in at most one point, since `D` meets that space only at zero. Five available values are therefore impossible. We may assume that the coset has even `alpha` parity.

Its `beta` parity is also constant. First suppose it is even. Projection onto `beta` is injective on a `D` coset: a difference in `D` with zero `beta` is zero. Of the five distinct projected values, at most one is zero. Hence at least four different nonzero even `beta` values occur as gates of the circuit. In addition, all four different triple values `E_c` occur as target projections.

These eight distinct non-input projections require at least eight first-occurrence gates. Each entry repeats its nonfree operand's `beta` and is therefore not such a first occurrence. Since there are at least three entries, the circuit would have at least `8+3=11` gates. This contradicts its size ten.

## Proof of Theorem S: odd own-block parity

Now suppose the five-value coset has odd `beta` parity. Because `alpha` is even, its residue `e` is odd. Exactly one of the named values has residue `e`. Every available value in this coset is an odd-`beta` node; no wholly free value lies there. Thus five available values force at least four odd gate values besides the four required output gates.

The circuit has at least eight odd-`beta` gates. It must also have at least two even-`beta` gates. To see this directly, if only one nonzero even projected value `p` existed, its first occurrence would be a pair of `b` inputs. Inductively every odd projected value lies in `{b_i,b_i+p : i=0,...,3}`: adding `p` twice returns the original input, and an entry does not change the projection. This set contains only the two triple sums containing the pair, and cannot produce the other two. With no even projected value, no triple can be produced at all. Two even physical gates are therefore necessary.

Since the circuit has ten gates, it has exactly eight odd gates and exactly two even gates, say `h_1,h_2`. Its four non-output odd gates all belong to the residue-`e` coset. Write `B` for the five odd nodes in that coset: these four gates and the unique named node of residue `e`. The complete set of odd nodes is `N union B`, with `N intersect B` that one named node.

### Each even value has at most two odd-pair decompositions

Fix either even gate value `h`. Count representations `h=u+v` by two distinct odd node values in the complete circuit.

If `rho(h)=0`, the two odd operands must have the same residue. Outside `B`, every odd residue occurs at most once. Thus both operands lie in the five-element set `B`. Translation by a nonzero value `h` pairs elements into disjoint unordered pairs. A five-element set contains at most two such pairs.

If `rho(h)!=0`, no pair lies wholly in `B`. A pair with one operand in `B` must have its other operand in the named set at residue `e+rho(h)`. There is exactly one named value at this odd residue, so `h` fixes at most one such pair. A pair with both operands outside `B` is a named pair; there is at most one by the rank-seven property of `N`. Hence there are at most two representations in this case as well.

### At most four non-entry gates, versus at least six

Every non-entry gate corresponds to an odd-pair decomposition of one of `h_1,h_2`:

* If its output is even, its two operands are odd. They cannot both be nonzero even nodes: when either of the two even gates is produced, at most one earlier even gate exists, and adding that value to itself has zero `beta`.
* If its output is odd, exactly one operand is odd and the other is one of the two even gates. Rearranging the equation writes that even value as the sum of the odd operand and odd output.

One three-value relation can account for at most one physical gate. In a reduced circuit its three values have unique nodes, and the latest of those nodes in topological order is the only one that can be computed from the other two. Thus the gate-to-relation assignment is injective.

Each even value has at most two relevant decompositions, so there are at most four non-entry gates. But transposition already showed `tau<=4`, leaving at least `10-tau>=6` non-entry gates. This contradiction excludes the odd coset and completes the proof. QED.

The global relation count deliberately includes even gates that are themselves entries. It does not assume that the construction of every even gate consumes an odd-pair relation.

## Applying the cap to the eleven-gate interface

Theorem N in `../row-cost/JOINT01.md` says that an at-most-eleven-gate four-triple sheet whose actual entry labels all avoid its required three-space `D` must have exactly five entries. Their labels are distinct and lie in one nonzero coset of `D`.

In a 21-gate joint 0/1 circuit with `(G_0,G_1)=(10,11)`, the ten `b'`-free gates must all belong to the first-sheet computation: the latter already needs ten gates, and its ancestors have no `b'` content by hypothesis. Every entry operand of the second sheet is consequently a first-sheet gate, a coordinate input of `b`, or a free vector of `a`. These are exactly the available values covered by Theorem S. Five labels from one `D` coset cannot be supplied.

Therefore this split, if it exists, uses at least one actual clean-diagonal entry in the second sheet. This is a restriction on actual supply, rather than on an unconstrained free interface.

## A rank-one clean supplier must saturate a nonclean coset

Combine Theorem S with the eleven-gate trace geometry in `QUOTIENT.md`. Suppose the clean-diagonal values actually available from a ten-gate producer span at most one dimension. Then an eleven-gate consumer for the second sheet, if it exists, must use exactly five entries: four distinct nonclean labels in one coset and one nonzero clean label. In particular the producer must attain the four-value cap on that nonzero coset.

Here is the proof without a circuit-configuration list. An all-clean interface must span the three-dimensional `D`, which is impossible. For an interface with a nonclean label, the projection bound gives quotient dimension one and total label rank four. Its trace counts are either four entries with a seven-gate mirror or five entries with a six-gate mirror.

The four-entry branch has two independent clean labels, so it is unavailable. In the five-entry branch, two nonclean labels together with a clean span of dimension at most one would give total label rank at most three, also impossible. If there are three nonclean labels, the remaining two clean labels would have to be dependent. Zero labels are excluded by the entry-deletion certificate, so these two labels would be equal. Their two positions would then support the unique label relation. That relation is the odd-trace indicator, forcing all three nonclean traces to be even. The trace relation has support precisely the three nonclean positions, so those three traces are distinct and nonzero. A six-gate triple-sum mirror has only two even signals, a contradiction. Five nonclean labels are excluded by Theorem S. Thus exactly four nonclean labels and one clean label remain, as claimed.

If the producer has no nonzero clean-diagonal value at all, this last possibility is unavailable as well.

### The displayed ten-gate diagonal supplier cannot be extended to a joint 21

For the concrete producer in `../row-cost/JOINT01.md`, use its names `p,q,u,v,w,d,U_0,...,U_3`. Its only nonzero clean-diagonal gate is `d`, so its available clean span has dimension one.

Its actual masks also show that no nonzero `D` coset has four available values:

* The even residue `1111` contains `u,v` and its unique free-`a` value: three values.
* The even residues `s_0` and `s_3` contain respectively `p` and `q`, together with the corresponding free value: two each.
* The zero residue contains `0,d`.
* The odd residue `E_1` contains `w,U_0`; the other triple residues each contain their one output, and the unit residues each contain their one input.

These are direct identities of the displayed construction, not a search over producers. All computed `a` parts are even. Odd free-`a` vectors lie in different `D` cosets from these computed values and supply only one value each; other even free cosets likewise supply only their one free value.

Thus this particular ten-gate first sheet cannot supply any eleven-gate second-sheet interface. It needs a joint total of at least 22 under the no-feedback hypothesis. This producer-specific obstruction does not assert that every ten-gate first sheet has clean rank at most one or misses every saturated four-value coset.

## Remaining scope

The theorem does not say that a ten-gate first sheet has no clean diagonal. The explicit ten-gate construction in `JOINT01.md` supplies one, so mixed clean/nonclean interfaces remain genuine possibilities.

It also does not settle the `(G_0,G_1)=(11,10)` split, which requires three independent clean diagonal suppliers among eleven first-side gates. Nor does it rule out every eleven-gate second-sheet interface containing a clean label. Consequently the known joint lower bound is still 21, its upper bound still 22, and the published unrestricted MixColumns interval remains unchanged.
