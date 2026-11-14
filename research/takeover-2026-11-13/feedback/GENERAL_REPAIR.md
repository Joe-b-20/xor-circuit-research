# Feedback removal is bounded by the rank of the entry space

2026-11-13. Constructive hand proof. No circuit search, enumeration, or computer-driven
case elimination. This is a general interface theorem; no claim of literature novelty
is made. The sharper MixColumns-specific question remains open.

The later [credited replay theorem](CREDITED_REPLAY.md) retains this rank-only bound
and sharpens it using original physical group values, including values whose production
is advanced during replay and paid by bypassing their later original gates.

## Statement

Partition ordinary inputs into source coordinates and consumer coordinates `z`; all
free values are on the source side. Zero is available without cost. A gate is
consumer-bearing if its `z` part is nonzero, and source-side otherwise. An exit is a
source-side gate with two consumer-bearing operands, whose equal nonzero `z` parts
cancel. Every other source-side gate has two source-side operands.

Assume all actual source-side operands read by consumer-bearing gates lie in one fixed
source-value space `D` of dimension at most `d`. These operands are the entry labels.
Consumer coordinate inputs have zero source part. Let `G_0` count source-side gates and
`G_1` consumer-bearing gates, so `G=G_0+G_1`.

Define

    h(d)=2^ceil(d/2)+2^floor(d/2)-d-2.

This is zero at dimensions zero, one, and two.

**Theorem FR.** All original source-side values have a source-only realization with at
most `G_0+h(d)` gates, preserving their original chronological availability. Consequently
the full computation has a no-feedback realization of size at most `G+h(d)` with the
same consumer entry values. For `d=0,1,2,3,4`, the respective allowances are `0,0,0,1,2`.
The bounds are sharp for `d=3,4`; no sharpness claim is made for `d>=5`.

Thus feedback cannot save any gates across a rank-at-most-two entry space. Across rank
three it can save at most one gate. Rank here measures the whole entry-value span,
not the dimension of the block being cancelled.

## Every exit is in an already available span

Induction in the original gate order puts the source part of each consumer-bearing
node in the span of the entry labels that have appeared so far. A consumer input has
source part zero; an entry adds one such label; adding two consumer-bearing values
adds their source parts. Therefore an exit lies in the span of earlier entry labels.

This is chronological. A later exit may itself be read as an entry, but it cannot
create a direction outside the span previously read by the consumer. The repair will
use only values already physically supplied; belonging to a span does not make an
operand free.

## Two growing basis groups give the bound

During chronological source-only replay, maintain a basis of the span of all currently
available values in `D`. Initialize it from the original source inputs and free values
that lie in `D`. Put newly chosen basis elements alternately into two groups, retaining
each element in its group forever. Maintain physically available every nonzero sum
within either group's span.

When a new independent basis value `g` joins a group of size `k`, it is already supplied
by an original input, free value, or replayed ordinary source gate. For each nonzero
old group sum `x`, compute `g+x` if it is not already available. This takes at most
`2^k-1` additional XOR gates. The operands are available: `g` has just been supplied,
and the old group span was maintained. These synthetic sums cannot increase the basis
rank because they belong to its current span. An ordinary source gate can increase
the rank by at most one; an exit cannot increase it, by the preceding causal argument.

The two group spans have zero intersection and sum to the full current basis span.
Every exit value therefore decomposes into two currently available group sums, one of
which may be zero. Reproduce the exit with at most one XOR, covered by its original
gate. Every other original source gate also costs at most one gate in replay. Additional
work is confined to completing the two group spans.

A group ending with `k` basis elements has incurred at most

    sum_(j=0)^(k-1) (2^j-1) = 2^k-1-k

additional gates. This includes initialization if several basis values were available
from the start. The alternating assignment leaves group sizes `ceil(r/2), floor(r/2)`
when the final rank is `r<=d`, giving total additional cost at most `h(r)<=h(d)`.
The function is nondecreasing: each rank increment adds `2^floor(r/2)-1>=0` to `h(r)`.
This proves the chronological source-only bound.

Compute that source-only circuit first, then replay all original consumer-bearing
gates in their original order. Every source operand is supplied and every consumer
predecessor precedes its reader. This adds `G_1` gates and has no consumer-bearing
ancestor of any source-side value, proving the full no-feedback bound.

This is a basis-sum construction applied to a causal interface, not a claim that
balanced groups minimize the extra work. The smaller rank-three argument below and
in [R3](RANK_THREE.md) shows exactly when its single extra gate can be necessary.

## An alternative potential proof and a density criterion

The following proof gives the weaker bound `f(0)=0`, `f(d)=2^(d-1)-d` for `d>=1`.
It agrees with `h` through rank three. Its useful additional information is a condition
under which already available values make every further exit cost at most one gate.

### Half of a binary space suffices for one-XOR access

Let `S` be the currently available distinct nonzero values in `D`, and put
`r=dim span S`. If `r>=1` and `|S|>=2^(r-1)`, every nonzero value in `span S` is either
already in `S` or the sum of two members of `S`.

Indeed, if `t` is not in `S`, both `S` and `S+t` lie in `span S` minus `{0,t}`. Their
combined sizes exceed `2^r-2`, so they intersect. An intersection gives `u=v+t` with
`u,v in S`, and hence `t=u+v`. The operands are distinct and nonzero.

If a desired `t in span S` is neither available nor a pair sum, there exists some
missing nonzero pair sum of members of `S`. Otherwise `S union {0}` would be a subspace,
contradicting `t not in S`. Such a pair sum can be physically computed in one gate,
increasing `|S|` without changing its rank.

### A potential pays for every extra repair gate

Replay the original source-side gates in their original order, omitting consumer-bearing
gates. Recreate an ordinary source-side gate from its already supplied operands, or
bypass it if its value is available. At an exit, its value is in the span of already
supplied values in `D` by the preceding causal argument.

If the exit value is available or one XOR away, use zero or one gate. Otherwise add
missing pair sums until the exit becomes available or one XOR away, and finish it.
Only the intermediate pair sums are extra to the one gate originally charged to that
exit. Stop before computing the desired exit as an intermediate; if it becomes a pair
sum, its computation uses the exit's original one-gate allowance.

To bound all extra intermediates together, use

    P=0 if r=0,
    P=max(0, 2^(r-1)-|S|) if r>=1.

Every extra pair sum is added while the desired exit is not one XOR away. The half-space
lemma then implies `P>0`. This addition increases `|S|` by one at fixed rank, reducing
`P` by exactly one.

Dependent additions from ordinary source gates or completed exits never increase `P`.
If an ordinary source gate supplies a value of `D` outside the current span, the rank
increases from `r` to `r+1`, and `|S|` increases by one. For `r>=1`, its increase in `P`
is at most

    2^(r-1)-1 = f(r+1)-f(r).

This also holds when the previous potential was zero, since then `|S|>=2^(r-1)`.
The transition from rank zero to one has zero increase. Values outside `D` do not change
`S` or `P`. Initially `|S|>=r`, so the initial potential is at most `f(r)`.

The initial potential plus all possible increases telescopes to at most `f(d)`. Each
extra repair gate consumes one unit; all other changes can only spend or leave potential.
Thus at most `f(d)` extra gates occur in the entire replay, proving this alternative source-only bound.
This argument accounts for rank growth during the computation, not just an assumed
initial basis.

Finally compute that source-only circuit and then replay all original consumer-bearing
gates in their original order. Their source operands are now available, and their
consumer-bearing predecessors are supplied in order. This uses the original `G_1`
gates and has no consumer-bearing ancestor of a source-side output, proving the alternative full
no-feedback bound.

## Sharpness at rank three

Take independent source inputs `u,v,w` and one consumer input `z`. Require the four values

    p=z+u,       q=z+u+v,       r=z+w,       e=u+v+w.

Compute `p=z+u`, `q=p+v`, `r=z+w`, and `e=q+r`. These are four gates, three consumer-bearing
and one exit. All four targets are distinct non-input values, so four is the unrestricted
minimum. Every entry lies in the rank-three space `span{u,v,w}`.

Without feedback to the source output `e`, its ancestor cone needs at least two gates
to sum three independent source coordinates. The three distinct consumer outputs have
nonzero `z` part and need three additional gates outside that cone. Thus no feedback
costs at least five, attained by computing `e` in two source gates and `p,q,r` in three
consumer gates. The one-gate allowance is therefore sharp, even for the full circuit.
The [direct verifier](check_feedback.py) evaluates these specified circuits.

## Sharpness at rank four

Take independent source inputs `u1,u2,u3,u4` and consumer input `z`, and require

    p1=z+u1,    p2=z+u1+u2,    p3=z+u1+u2+u3,
    q=z+u4,     e=u1+u2+u3+u4.

Compute the three prefixes in order, then `q=z+u4` and `e=p3+q`. These five distinct
non-input targets have an unrestricted minimum of five gates. A no-feedback cone for
`e` needs at least three source gates to connect its four independent source inputs;
the four distinct consumer-bearing target gates lie outside that cone. Thus the
no-feedback minimum is seven, attained by computing `e` separately in three gates
and the consumer targets in four. The two-gate allowance `h(4)=2` is sharp for the
full circuit as well. This is an instance of the familiar prefix sharing/cancellation
mechanism, not a claim of novelty for the example. The direct verifier checks both
rank-four constructions as well as the rank-three ones.

## Relation to the joint research problem

For a ten-gate consumer in the unrestricted MixColumns 0/1 problem, entry deletion forces
all its entry labels into the rank-three diagonal space. The [rank-three specialization](RANK_THREE.md)
then gives at least eleven zero-consumer gates and characterizes the possible ternary
exit at total 21. A larger consumer may use a larger entry space. The bound here does
not prove an unrestricted joint minimum of 22 or increase the unrestricted MixColumns
lower bound.

The subsequent [five-diagonal theorem](FIVE_DIAGONALS.md) strengthens this application:
if rank-three replay costs one extra gate, it retains five distinct diagonal values.
They and the first-sheet rows need thirteen source gates. Hence every joint circuit
with exactly ten consumer-bearing gates needs at least 22 total gates, even with
feedback. The unrestricted joint problem at larger consumer budgets remains open.
