# A sharp restricted obstruction for the 11-gate diagonal interface

2026-11-13. Hand proof; no SAT, enumeration, exact-gate search, or computer-driven case elimination. This is a restricted interface theorem, not a resolution of the general augmented-sheet 11-versus-12 question.

## Result

Let `b_0,...,b_3` be ordinary inputs and let every vector on the separate four-coordinate block `a` be free. Put

    E_c = sum_{d != c} b_d,
    s_c = e_c+e_(c+1),
    T_c = E_c+s_c(a),
    D_c = s_c(b)+s_c(a).

Indices are modulo four; `P` is the cyclic coordinate shift `P e_c=e_(c+1)`. Require all four `T_c` and any three of the four `D_c`. Assume:

* the circuit is event-free for the partition `{a,b}`; and
* every paid gate other than these seven required output nodes is supported on block `b` alone. In particular, there is no auxiliary mixed `a+b` gate.

Then the circuit needs at least **12 gates**. This is sharp: the event-free 12-gate construction in [DIAGONALS.md](../compatibility/DIAGONALS.md) uses exactly five pure-`b` auxiliary gates and the seven required mixed nodes. By cyclic relabelling, it works for any choice of three of the four cycle-pair diagonals.

Consequently an event-free eleven-gate solution for any such triple of diagonals would require at least one **mixed auxiliary** beyond the seven requested values. The statement does not cover an arbitrary basis containing the opposite-pair or all-four even mask, and it does not exclude an eleven-gate circuit with an auxiliary mixed gate or with whole-block cancellations.

## Why the paired rows demand pure-own values

By cyclic symmetry, take the required diagonals to be `D_0,D_1,D_2`; `T_3` is the unpaired row. The seven required mixed values have distinct nonzero `b` masks: four odd triples and three even pairs. The four free masks `s_c(a)` are distinct.

No required target can be made from two other required targets, nor from one required target and one `b`-coordinate input:

* The XOR of two different rows `T_i,T_j` cannot be diagonal. Its own mask is `e_i+e_j`, while its free mask is `(I+P)(e_i+e_j)`; equality would imply the impossible equation `P(e_i+e_j)=0`.
* The defect `own+free` of `T_i` is `E_(i+1)`, so adding a diagonal cannot turn it into a different row. Two distinct required diagonals cannot produce the third because the three chosen pair masks are independent.
* A row and a diagonal with the same free part differ on block `b` by the triple `E_(c+1)`, not a unit. Other pairs have incompatible free parts or own parity.

Nor can adding a free value to a previous required mixed value produce a different required target: their own masks are distinct. Under the no-mixed-auxiliary hypothesis, every non-free operand available to a required gate is a pure-`b` value or another required target. Thus, for each `c=0,1,2`, whichever of `T_c,D_c` is made first must be formed by adding its own pure-`b` mask (`E_c` or `s_c`) to the free value `s_c(a)`. To make the other one, either its own mask must also exist pure, or the first mixed value is combined with their pure-own difference

    T_c + D_c = E_(c+1).

Therefore the pure-own node set contains at least two of

    {s_c(b), E_c, E_(c+1)}                         (c=0,1,2).       (1)

No selected diagonal has the same free mask as `T_3`, so its first appearance requires the pure-own value `E_3`.

## Counting and the triple-sum bottleneck

Suppose at most eleven gates suffice. The seven required mixed targets are distinct paid gates, leaving at most four pure-own auxiliary gates. Let `x` count the pure triples among `E_0,E_1,E_2,E_3`, and let `y` count the pure pairs among `s_0,s_1,s_2`. These are distinct non-input values, so `x+y<=4`.

The three conditions (1) contribute at least six incidences. An `E` value can occur in at most two of the three sets, except that the required `E_3` occurs in only one; each `s_c` occurs in one. Hence

    2x - 1 + y >= 6,       x+y <= 4,

which forces `x>=3`.

Because the circuit is event-free, every ancestor of a pure-own value is also pure-own. Yet producing any three distinct four-input triple sums requires at least five pure-own XOR gates. To see this, suppose only four gates suffice. Three must be the distinct triples, leaving one other gate; the first gate is a pair of inputs. That pair can directly seed only the two triples containing both of its inputs. XORing it with either such triple leaves a unit, while the two remaining triples differ by the pair and can only seed each other. XORs of two triples or of a triple and a unit have even own weight, so cannot supply the missing first triple. Thus one helper plus three triple gates cannot work.

The three pure triples consequently require five pure-own gates, contradicting the four-gate budget. The lower bound is 12, and the cited explicit circuit attains it.

## Scope and relation to the open problem

The result uses physical gate values and only the seven designated mixed targets; the pure-own difference is not treated as free. It sharpens the earlier exact 13-gate statement that additionally required **all four** clean own triples: here one may omit a triple, and the matching 12-gate circuit does omit one.

The original augmented problem allows three arbitrary independent even diagonal masks and unrestricted cancellations or mixed auxiliaries. Its current bounds remain `11<=L<=12`. The entry-deletion argument in [QUOTIENT.md](../compatibility/QUOTIENT.md) proves any hypothetical eleven-gate solution must use only even actual free labels, but it does not impose the no-mixed-auxiliary condition used here. No assertion about eleven in the unrestricted problem follows.
