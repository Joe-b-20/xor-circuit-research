# Independent review: rank-two clean supply

Hand review of `../RANK_TWO.md`, with its dependencies on the parity confinement, named-value relation, coset, and odd-pair graph results as stated in the earlier relation notes. No SAT, exhaustive enumeration, exact-gate search, or computer-driven case elimination was used. This is not formal verification.

## Verdict

The no-odd-helper exclusion, the even-coset escape criterion, its seven-first-gate/three-entry consequence, the exclusion with exactly three physical even gates, and the stated odd-coset ancestry criterion are correct under their hypotheses. The argument is partial: it does not exclude an even escape with four or more physical even gates, nor an odd-coset crossing. It does not settle the full rank-two interface or a 22-gate joint lower bound.

## Why clean rank two requires an odd helper

Assume no odd non-output gate. A row target has a distinct own triple, so it cannot be an entry preserving an earlier own mask; it reads one physical even value and one named odd value. The same even value cannot serve two different output-gate equations: the eight named odd values have only their all-eight relation, so a nonzero value has at most one unordered named-pair representation, and a single physical three-node relation cannot execute in both directions without a cycle.

Before the first physical even gate, an odd output cannot appear: with no odd helper, an entry can only preserve an available own unit, and combining two odd own masks would already create an even gate. Thus the first even gate adds two distinct own inputs. Its residue is nonzero, and its named pair contains only inputs, so it is different from the four even values supporting row-output equations. At least five of the six even gates are therefore nonclean, leaving at most one clean gate. Clean rank two requires an odd non-output helper.

## Even-coset escape and equality structure

All paid-gate free parts are even by the ten-gate parity-confinement result; an odd-free-parity `D`-coset contains at most one available value, its pure-free representative. On even-free-parity values, `D`-cosets are exactly fibres of `rho=beta+alpha`.

For an even physical gate `(beta,alpha)` with nonzero residue `r`, the freely available value `(0,r)` is in the same coset and their difference is the diagonal `(beta,beta)`. Conversely, the own part of any difference between values in an even coset lies in the span `P_b` of physical even-gate own masks. Since the two available clean diagonal values already span `W_b`, some even coset can complete `W` exactly when `dim P_b=3`.

If `dim P_b=3`, three distinct nonzero even own projections and the four target triples force at least seven first-occurrence gates. At least three entry gates are also necessary because the target free parts have rank three. Ten total gates force equality: seven first occurrences and three entries, with no other duplicate-own-projection gates. The three even own masks form a basis of the even space and the three entry labels form a basis of the free even space. Within each own fibre, an entry edge connects to a prior node of the same own mask. With one first occurrence (or an ordinary input for a unit fibre), these edges form a rooted tree, so path-label sums give within-fibre differences and paths in different fibres use disjoint entry occurrences.

## Excluding three physical even gates in the escape case

With exactly three physical even gates and `dim P_b=3`, their own masks, hence their complete values, are independent. Two are the independent clean values `h1,h2`; the third `k` has nonzero residue, otherwise clean rank would be three. There are seven odd gates, including the four row outputs, and therefore three odd helpers in addition to the eight named odd values.

No physical non-entry equation can involve three even nodes: their own masks are independent. Every such equation is an odd-pair edge labelled by one of the three even values. Since the three even values are independent, the parity of every colour on any actual graph cycle is even; therefore the formal relation rank equals the odd-vertex incidence rank. Seven non-entry gates give seven independent formal equations, so the graph on eleven odd nodes has at most four components.

Clean edges preserve residue; `k` edges toggle its nonzero residue. The eight named nodes occupy all eight odd residues once, so there are four residue-pair classes and no edge between them. Each class must therefore be connected, and each must contain a `k` edge. Translation by a fixed nonzero value is a matching. At most one of those edges joins two named nodes, by named-pair uniqueness, and at most three touch a helper, so exactly one named-to-named edge and three single-helper edges occur.

In each of the latter three classes, the remaining named node must be joined to its same-residue helper by a clean edge, labelled `h1` or `h2`. The four distinct named-pair sums are therefore `k` and three values drawn from `{k+h1,k+h2}`. Two sums would coincide, contradicting the unique nonzero relation among the eight named nodes. Thus exactly three physical even gates cannot realize an even escape; four or more are not excluded by this argument.

## Odd-coset criterion

If `P_b=W_b`, an odd entry preserves the own mask and an odd non-entry gate has one odd operand plus an even mask in `W_b`. Following odd ancestry reaches some original odd unit, placing the node's own mask in one of the classes `b_i+W_b`. For two same-residue nodes, their difference is a clean diagonal; that difference is outside `W` exactly when their own masks differ outside `W_b`.

When the two-dimensional even space `W_b` omits the all-four mask, its three nonzero values are pair masks on a common three-coordinate set `I`: independent pairs must intersect, since disjoint ones sum to the omitted all-four mask. Let `j` be the remaining coordinate. Among odd masks, membership in `b_i+W_b` is determined by the `j`th coordinate, so a same-residue pair escapes precisely when those bits differ. The triple `E_j` can trace odd ancestry only to inputs from `I`, whereas the other three own triples can trace only to `b_j`. This is a necessary ancestry restriction, not an exclusion of such a crossing, as the note correctly says.
