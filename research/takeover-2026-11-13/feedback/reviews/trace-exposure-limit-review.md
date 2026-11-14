# Independent review of the local-exposure limitation

2026-11-14. Independent machine review of [TRACE_EXPOSURE_LIMIT.md](../TRACE_EXPOSURE_LIMIT.md). No circuit search or enumeration was used. This is not formal verification or human certification.

**Verdict:** the counterexample and its six-entry decoration are correct. They refute the inference from two even helpers per literal mirror to at most two distinct class-adjacency pairs across all alternative local accumulation orders. No all-odd four-class closure follows from that inference.

I independently reconstructed the same example before reading the final note. The ordinary mirror has the two even helpers `p=x_0+x_1` and `j=x_0+x_1+x_2+x_3`; its other four gate values are precisely the odd triples. Its transpose uses `q=z_0+z_1+z_2` and `w=q+z_3`, with outputs `w+z_0,w+z_1,w+z_2,q`. The common `w` has three target-reader branches with unit traces `x_0,x_1,x_2`.

Accumulating any chosen pair of those three contributions first produces the corresponding even pair sum. The next accumulation produces their common triple sum, and the remaining construction is unchanged. Each choice has six gates and only two even helpers, but the chosen pair helper changes. The three exposures are alternatives at one original vertex, so the independent ordering choices at different vertices do not apply. The pair-helper derivative is the all-four mask of `w`; the other helper's derivative is the distinct triple `z_0+z_1+z_2`. Existing even-wire separation is respected.

The explicit decoration also checks. There are six non-entry consumer gates (`r,q,w,Y_0,Y_1,Y_2`) and six entries (`A_1,A_2,B_1,B_2,C_1,Y_3`), all with nonzero ordinary parts and all target-live. Direct substitution gives the displayed output source parts `a+b,k+l,c,d`. The traces are exactly the four unit masks with multiplicities `(2,2,1,1)`.

Taking `b=a+S`, `l=k+T`, with `a,k` independent modulo the rank-three diagonal, makes the actual entry span rank five. Its sole relation is the sum of all six labels, since the four prescribed diagonal values have only their all-four relation. The three first branch entries at `w` give an actual class-adjacency triangle. The optional choice `a=h`, `k=h+f` also supplies the stated one-even-free/one-odd-own quotient shape without changing that rank calculation.

The note correctly limits the construction to a consumer and interface. It neither supplies the four source rows and all labels within nine source gates nor gives a joint circuit below 22. Its return paths involve at most two trace classes, so it does not refute the desired cost conclusion. It refutes only the proposed global adjacency premise and identifies simultaneous exposure in one literal mirror as the valid counting requirement.

No all-odd four-class closure note was saved by this reviewer. That direction remains open in the current research state.
