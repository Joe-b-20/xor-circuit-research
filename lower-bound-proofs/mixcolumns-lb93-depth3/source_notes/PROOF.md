# A parity-assisted lower bound of 85 XOR gates at depth 3

Date: 2026-10-16. Objective attempted: prove the known 97-gate depth-3 AES
MixColumns circuit optimal. **That objective remains open.**

## 1. Result and model

Let D3 be the minimum number of two-input XOR gates computing one AES forward
MixColumns column, with raw inputs at depth zero and gate depth equal to one
plus the maximum of its two parent depths. Fan-out and cancellation are allowed.

The result of this attempt is

    85 <= D3 <= 97.

The upper bound is the included, independently reverified `control_97.json`.
The lower bound is computer-assisted: the structural reduction is proved below,
the first-layer parity premise is exhaustively checked, and an exact rational
dual certificate establishes the remaining inequality. All checking uses
standard-library Python. No solver's OPTIMAL or UNSAT status is a premise of
the 85 lower bound.

Bit 8*j+k is bit k of byte j, least-significant bit first. The AES coefficient
matrix is the cyclic matrix with first row (02,03,01,01), over the field with
reduction polynomial 0x11b. `verify_structure.py` reconstructs all 32 binary
output masks independently of the search model and checks `matrix.txt`.

## 2. Depth-3 odd/even normal form

Delete unused gates, zero results, and duplicated signals. Replacing a
weight-two signal made at depth two by the direct XOR of its two raw inputs
uses at most one gate and never increases a depth. Weight-one signals are
already raw inputs. Thus a minimum depth-3 circuit can be normalized to:

- P pairs: weight two, made at depth one from two inputs;
- T triples: weight three, made at depth two from a pair and a disjoint input;
- Q quartets: weight four, made at depth two from two disjoint pairs;
- 32 output gates, all at depth three.

The 32 distinct outputs have weights 5 (twenty outputs) or 7 (twelve outputs).
A depth-two signal has weight at most four, so every output must occur at depth
three and cannot feed a subsequent gate. Consequently

    G = 32 + P + T + Q.

Every final output is odd, so one parent is odd (weight one or three) and the
other even (weight two or four). The equation

    weight(a XOR b) = weight(a) + weight(b) - 2*weight(a AND b)

gives the exhaustive cases:

| Output weight | Parent weights | Intersection size |
| --- | --- | --- |
| 7 | 3 and 4 | 0 |
| 5 | 1 and 4 | 0 |
| 5 | 3 and 2 | 0 |
| 5 | 3 and 4 | 1 |

In the final row the common input bit is outside the output support. It is
explicitly retained throughout the proof. A weight-seven output's entire
unfolded construction is cancellation-free. A weight-five output can cancel
one repeated input occurrence pair; this is not an assumption that a separate
physical gate must be charged for cancellation.

The control has P=27, T=20, Q=18. Its weight-five output modes are 3 of type
1+4, 8 of type 3+2, and 9 of type overlapping 3+4. Excluding cancellation would
exclude this positive control.

## 3. The parity premise: P >= 24

Form the undirected graph on the 32 inputs with one edge for each selected
pair. If it has c connected components, its pair-mask span is the set of
vectors even on each component, and its dimension is 32-c <= P.

Each odd signal is one input plus a sum of pair masks: this holds for triples,
and for outputs after substituting their triple/quartet parents. Each output
therefore intersects exactly one graph component oddly and all others evenly.

For a component C let b_C be its input indicator. The vectors M*b_C have
disjoint supports covering the 32 output coordinates. Hence the pairs

    (b_C, M*b_C)

are disjoint nonzero graph-code words partitioning all 64 input/output
coordinates. A finite AES fact excludes a partition into nine such words.
More than nine components would also yield nine by merging blocks. Thus
c <= 8 and P >= 32-c >= 24.

### Exhaustive verification of the finite fact

The checker enumerates all nonzero graph-code words (u,M*u) of total weight at
most eight. At least one of u and M*u has weight at most four, so enumerating
all input halves of weight 1..4 and all output halves of weight 1..4 using
M inverse is complete. The result is 84 words of weight six and 276 of weight
eight, and none lighter. Every graph-code word has even weight because every
column of M has odd weight. Thus all nonzero words have weight at least six.

In any partition into nine nonzero words, the seven lightest words have
weight at most eight: while at least three words remain, their lightest has
weight at most the average, which is at most nine, and weights are even.
The checker enumerates all possible sorted choices of seven disjoint short
words, pruning only when the remaining words cannot all be at least as heavy
as the next choice.

For their remaining support R, let I and O be its input/output halves. The
dimension of the graph code shortened to R is

    |I| - rank_GF2(M[rows outside O, columns in I]).

The remainder indicator itself is a codeword, since (all ones, all ones) is
a codeword. It splits into two disjoint nonzero codewords exactly when this
shortened dimension is at least two: take a nonzero proper word and its
complement within R. No tested remainder has dimension two.

Recomputed counts: 1,485,213 search nodes, 62,112 remainder tests, zero splits.
Eight blocks exist (the eight bit families), so this component bound is sharp
as a parity-partition statement. It does not assert that an eight-component
graph can support a depth-3 circuit with only 24 pairs.

## 4. Charge complete output constructions

There are 496 possible pair masks and 7,897 triple/quartet masks occurring as
possible final parents: 3,008 triples and 4,889 quartets. The exhaustive final
parent decompositions number 6,120:

- 12*35 = 420 for weight-seven outputs;
- 20*(5+10+270) = 5,700 for weight-five outputs.

Each triple has three possible pair-plus-input constructions. Each quartet
has three disjoint-pair constructions. Expand each output decomposition into
all choices of its parents' constructions. A **recipe** is the set of paid
helper masks required by that complete construction, counting shared masks
once. There are 315 recipes per weight-seven output and 2,475 per weight-five
output, totaling 53,280. Recipes contain either three helpers (noncancelling
weight five) or five helpers (weight seven or cancelling weight five).

Let x_h indicate whether helper h is built and z_(o,r) indicate that output o
uses recipe r. For a real circuit choose one actual recipe per output. Then

    sum_r z_(o,r) >= 1                          for every output o,
    x_h - sum_(r containing h) z_(o,r) >= 0    for every output/helper pair,
    sum_(h of weight two) x_h >= 24,
    0 <= x_h,z_(o,r) <= 1.

The objective is sum_h x_h = P+T+Q. These are valid simultaneously: the
availability sum is taken for one output at a time, so helpers shared across
different outputs are charged only once.

The binary formulation is complete, not restricted to a search vocabulary.
Every normalized circuit maps to it. Conversely, from binary selected
helpers and one selected recipe per output, build all selected pairs first;
for each selected triple/quartet used by a recipe choose any witnessed
construction from those pairs; then build all outputs. Different recipes may
suggest different constructions of the same helper, but its mask is the
same and any one witnessed construction suffices for every use.

The certificate uses the relaxation to real variables in [0,1]. Its variable
count is 8,393 helper variables + 53,280 recipe variables = 61,673. There are
15,126 rows including the optional weight-seven inequality in section 6;
that optional row has dual multiplier zero.

## 5. Exact certificate: P+T+Q >= 53

Write the inequalities as A*p >= b, with objective c*p and 0<=p<=1. For any
nonnegative vector u, define the coordinate excess

    e_j = max(0, (A^T*u)_j - c_j).

Then

    c*p >= u*A*p - sum_j e_j >= u*b - sum_j e_j.

This follows directly from p_j<=1; it does not require floating-point dual
feasibility. It is also the usual dual certificate after adding the valid
upper-bound inequalities -p_j>=-1 with multipliers e_j.

`certificate_85.json` contains nonnegative integer numerators for u with
common denominator 10^12. The two checkers regenerate the entire model and
calculate every coefficient and rounding repair in exact Python integers.
They obtain

    P+T+Q >= 52682563822048 / 10^12
            = 52.682563822048 > 52.

The upper-bound repair is only 2762/10^12, and is subtracted exactly. Since
P+T+Q is an integer, it is at least 53, so G >= 32+53 = 85. QED.

`independent_check.py` regenerates parents by enumerating all possible odd
parents of weights one and three and testing their even complements. It
regenerates helper constructions independently from pair subsets and checks
the certificate without importing the original recipe/model generator.
The 97-gate control satisfies all inequalities at helper cost exactly 65.

## 6. A sharper description of the twelve weight-seven outputs

These twelve outputs require at least fifteen distinct triple/quartet
parents. This is a separate structural result, not the source of the 85
certificate.

View an output as an edge joining its odd triple parent to its even quartet
parent. The graph is a forest: a cycle would XOR a nonempty subset of the
independent output masks to zero. Exact support enumeration shows:

1. Any triple or quartet can parent at most two weight-seven outputs.
2. There are exactly 24 decompositions in which both parents can be reused
   by other weight-seven outputs. In every such decomposition, both other
   outputs belong to the same bit cluster as the original output.

Consequently the output-sharing graph has degree at most two. Any sharing
edge between two different clusters is an isolated edge: either endpoint
having a second sharing edge would contradict item 2. All other components
lie within one four-output cluster. Every component therefore contains at
most four outputs. There must be at least three components, and the parent
forest has at least 12+3=15 vertices.

The included selection attains fifteen parents algebraically; checking it
requires only XOR and popcount, not trusting the solver that found it. This
does not include the pair gates needed to construct those parents.

## 7. What failed to reach optimality

The original depth-3 certificate proves 80. Adding only the newer P>=24
parity constraint gives a numerical helper bound 50.44267149, corresponding
to 83 gates after rounding. Charging whole output recipes raises that to the
certified 85 above.

An exact feasible fractional point is saved with helper cost

    5268256474 / 10^8 = 52.68256474.

The independent checker verifies every row and every [0,1] bound at this
point. It is NOT a circuit. Its existence proves that these relaxed
constraints, without integrality or new inequalities, cannot certify the
65-helper target needed for 97-gate optimality.

Numerical diagnostics fixing the total triple mass at 11 and 12 still give
helper objectives below 53 (52.80740786 and 52.75406780). Thus the immediate
attempt to force another gate just by rounding the three category totals
did not succeed. These numerical diagnostics are not additional theorems.

A pair-only integer search with P between 24 and 27 timed out without a
feasible solution or certified bound; it proves nothing. The first simplex
run of the recipe relaxation timed out, while the interior-point run solved
it in roughly 7 seconds. A separate attempt to certify the older 83 bound
by a slackened dual timed out; the exact bounded-variable certificate above
avoids that problem. None of these timeouts is reported as an exclusion.

The unresolved step is to rule out all integral selections with at most 64
helpers. The remaining weakness is that fractional solutions distribute a
helper's purchase among many incompatible choices. The current inequalities
respect real shared gate costs, but do not force the globally integral
selection of exact masks that a circuit requires.

**Conclusion:** the attempt establishes a checkable depth-3 lower bound of
85 and a sharp fifteen-parent weight-seven lemma. It does not establish 97
optimality and finds no circuit below 97.
