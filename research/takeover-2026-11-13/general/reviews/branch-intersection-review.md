# Independent review: physical branch values and intersection repair

2026-11-14. Independent machine review of the complete
[BRANCH_INTERSECTION_REPAIR.md](../BRANCH_INTERSECTION_REPAIR.md). I reconstructed
the branch accounting, telescoping identity, availability bound, sharpness
constructions, and exact rank ceiling. No circuit search, representation search,
or subset enumeration was used. This is not formal verification, human
certification, or a literature-novelty assessment.

## Branch budget and the exact identity

The complete selected ancestor union keeps both operand ports of every gate.
Counting selected terminal ports as reads is essential, particularly when one
selected value is an ancestor of another or when ports coincide. Every retained
ordinary occurrence has at least one such read. Thus the total fanout excess is
2g+k-(a+g)=g-a+k=beta+k-c, and the number of branching occurrences is at most
that amount. Parallel operand reads and duplicate occurrences are retained.

The reverse influence recursion includes every operand port and each terminal
basis vector. In the sum of a_v Delta_v(phi), the coefficient of phi(eta_h) at
each gate h is its result mask plus both parent masks, hence zero. The remaining
terms are exactly the input and terminal boundary in the displayed identity.
Degree-one occurrences contribute no defect. Repeated reads cancel correctly
in the influence recursion and in the scalar defect. A zero influence causes
no exception under phi(0)=0.

This proves a representation in one common dictionary of actual branch values.
It does not require any uncomputed mask as an operand. The common dictionary
does not, by itself, supply all of its different linear combinations for free.

## Pair intersections, timing, and exact local cost

For two selected ports and phi(s,t)=st, the terminal correction vanishes and
the input boundary is precisely the support-intersection mask. A connected
two-cone union has at most beta+1 branch occurrences. If the cones are
disconnected, their coordinate ancestors are disjoint and the intersection
is zero. The dictionary word-length inequality follows in both cases.

For distinct selected occurrences, the later selected occurrence cannot have
a retained gate reader: that would need to lead to one of the selected ports
after its creation. It has exactly one selected terminal, so it is not a branch.
All branch values are therefore already available before the later result.
Coincident selected ports are correctly treated separately: their intersection
is just the same available value, without a strict timing assertion.

For a nonzero intersection, the exact single-target dictionary theorem gives
remaining binary cost ell_S-1, hence at most beta. The zero-intersection case is
explicitly a statement about support repair, without requiring a physical zero
output. Cycle rank is monotone under subgraph enlargement, so using the whole
circuit's cycle rank as a weaker bound is valid.

## Sharpness at every beta

In the construction on c_i,a_i,b_i,x,y, all pair values and all chain sums map
to zero under F(c_i)=F(a_i)=F(b_i)=e_i, F(x)=F(y)=0. Thus every actual dictionary
member maps either to zero or to one unit vector. The intersection C maps to
the all-ones vector in dimension t, forcing at least t summands. The c_i attain
t. The counts g=4t, a=3t+2, c=1 give beta=t-1, including t=1. Hence both the
representation length and the appended repair cost attain the theorem exactly.

There are exactly 4t-2 distinct even pre-anchor values: 2t pair values and
2(t-1) chain sums. Giving each one a fresh private odd attachment adds 4t-2
inputs and as many gates. Including U,V and all 3t core identity outputs makes
the map square on 7t inputs. It is an all-odd involution because the core stays
fixed and every other coordinate receives a fixed even core sum.

Projection of the private attachment coordinates deletes at least 4t-2 gates;
the remaining 4t distinct non-input targets require at least 4t more. Thus
8t-2 is the unrestricted optimum, matching the construction. Each attachment
adds two vertices and two edges, preserving full cycle rank. Extending F by
zero on the new private coordinates preserves the word-length lower bound.
The note correctly confines this sharpness claim to appending the intersection
to the displayed actual dictionary; it does not infer the optimum of a freely
rewired enlarged target problem.

## Exact boundary span and rank-only ceiling

After normalizing phi to vanish at zero and all unit patterns, each distinct
occurring nonunit column pattern contributes an independently selectable class
indicator. Those indicators have disjoint nonempty supports, so their span has
dimension exactly p. Arbitrary unnormalized functions add no boundary dimension:
the correction for a unit-pattern indicator is its class indicator plus the
corresponding target row, which lies in the same nonunit-class span. Linear
functions have zero defect boundary. This establishes the all-functions
ceiling, rather than merely a ceiling for quadratic functions.

Combining this exact rank with the branch count gives g>=a+p-k and therefore
G>=n+p-k. For n<=32, p<=min(32,2^k-k-1). The elementary ranges k<=5 and k>=6
give the uniform ceiling 58 stated in the note. No target subset is selected
by search. This bounds only the rank certificate; the actual branch values,
their coefficients, and their joint supply cost retain additional information.

The full note passes review. It separates local repair from simultaneous
repair, full ancestor cycles from parity-specific cycles, and machine review
from formal verification. It makes no new numerical MixColumns claim.
