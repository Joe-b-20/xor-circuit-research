# Independent review: subspace preparation

2026-11-14. Reviewer: independent `sparse_closure` agent. This is a mathematical machine review, not formal verification, human certification, or a literature-novelty assessment.

Reviewed [SUBSPACE_PREPARATION.md](../SUBSPACE_PREPARATION.md), including its closure lemma, color ledger, distance theorem, subspace/profile extension, sharpness families, and common-offset application. The review reconstructed the arguments directly and checked the application against the complete actual prefix in [COMMON_OFFSET_PREPARATION.md](../COMMON_OFFSET_PREPARATION.md). No search, enumeration, or numerical circuit optimization was used.

## Verdict

The stated inequalities and constructions are sound. No consequential mathematical gap was found. They apply to arbitrary binary XOR continuations from the stated actual dictionary, including dependent supplied values, cancellation, sharing, and arbitrary intermediate values.

## Main proof checks

1. **Closure and dimension ledger.** With no new outside-W values, every W-valued gate either sums two current W-values or combines two originally supplied values of the same nonzero quotient color. These operations generate exactly R(S). A new outside value of an old color adds at most one relation direction: differences from any two old representatives already agree modulo the old R. A new color adds none. Retaining all values makes the ledger monotone. Repeated physical values still count as gates and contribute to the unsuccessful-collision term. Once available outputs span W, R must equal W, so the number of one-dimensional increases is exactly q.

2. **First-collision relaxation.** Before the first dimension increase every W-valued gate is in R_0. Granting all R_0 values lets one erase precisely those gates and retain the original outside gates in their chronological order. At the first successful collision, appending the difference with an earlier same-color representative computes a nonzero member of W outside R_0. There are at most H_*+1 retained gates. This is a valid relaxed circuit even when the supplied dictionary is dependent; zero operations or copies can be erased or rewired.

3. **Absorption is an equality of set minima.** In a representation using S and granted U-values, the original-S summands alone sum to a member of W outside U whenever the represented result lies there. Thus their number is at least min_{w in W minus U} ell_S(w). Granting U cannot reduce that minimum. It need not preserve the length of each individual representative, and the draft correctly does not claim that. This distinction resolves the main possible gap in the first-collision argument.

4. **The complete bound.** The single-target word-length lower bound gives H_* >= Delta-2. Each of the remaining q-1 dimension increases needs a distinct later outside gate. The M absent W-valued outputs each need a separate W-valued first-production gate, which cannot overlap these outside gates. Consequently H >= q+Delta-3 and G >= M+q+Delta-3 follow without restricting any competing intermediate value.

5. **Proper-U and rank-profile extension.** After granting U containing R_0, the initial relation space is exactly U: the new values have zero quotient color and create no new nonzero-color pairs. Absorption preserves the minimum escape length. The original continuation remains legal with the same outside-W gate count. R_[2]=R_0 holds in both directions because all length-at-most-two W-values are precisely the generators already considered, up to sums within W. If R_[k] is proper, each value outside it has integer length at least k+1. Equations (9) and (10) follow.

## Boundary cases

- Delta>=3 is automatic when q>0. All one-term or two-term W-values are already in R_0.
- If all spanning targets are already supplied, R_0=W and q=0. The theorem correctly excludes Delta in that case.
- Supplied duplicate values may be identified without changing dictionary word length; physical repeated gate occurrences remain charged by H and G.
- Supplied zero values and zero gates do not help the argument. As usual, the closure statement concerns nonzero values with zero ignored.
- For independent coordinate inputs, zero-color coordinates and each nonzero color class have disjoint coordinate supports. Their ranks add to n-t_0, verifying q=t_0-codim(W) and the specialized ledger.

## Constructions and application

The distance-three family has nonempty combination weight 2|J|+(|J| mod 2), hence minimum three; its r two-coordinate helper values lie outside W. The distance-four family has nonempty combination weight 2(|J|+(|J| mod 2)), hence minimum four; its r+1 individual pair values lie outside the even-block subspace W. The one-dimensional family has D-2 proper partial sums outside W. All three meet the stated lower bounds under unrestricted competition.

The independent-triples corollary also follows exactly: m independent required coordinate-weight-three targets whose span contains no nonzero vector of weight one or two have r=M=m and D=3. The theorem gives G>=2m, attained by separate two-gate formulas. A saving below 2m therefore requires some nonzero weight-one or weight-two linear combination of the full target set. This is a necessary condition, not a sufficiency claim; independence is used at r=m.

For the common-offset application, every retained prefix member has F-image zero or a unit vector: this includes the original coordinates, all pair gates, every accumulation, and all supplied u_i. A nonzero W-value has image of weight at least two. An odd target combination has image weight at least 2r+1, so it cannot be supplied or be a sum of two supplied members. Thus R_0 is contained in the even target-combination subspace. Conversely u_i+u_j=t_i+t_j supplies every pair relation; u_i and u_j have the same nonzero W-quotient color. These relations span the entire even-combination subspace, of dimension m-1. Hence q=1. Every value outside R_0 is an odd combination, giving Delta>=2r+1, and a single original target representation attains equality. Computing the anchor sum in 2r-1 outside gates and then the m targets gives equality in both bounds, including r=1 and m=1.

## Scope

The theorem's restriction is a hypothesis about a selected target subspace, not a restriction on competing circuits. It does not make bounds from different subspaces additive: the same gate may lie outside several subspaces. Taking W=V makes the initial closure all of W and gives q=0, so an invertible full output map does not acquire a numerical lower bound merely by using its entire span. Proper target subspaces can still be used in the same unrestricted circuit model. No improved numerical MixColumns bound follows from this review.
