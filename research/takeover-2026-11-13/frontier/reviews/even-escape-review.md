# Independent review: one-helper even-coset escape

Hand review of `../EVEN_ESCAPE.md`, the physical-value independence argument in `../PROJECTION_TREE.md`, and inspection of `../check_tree.py` and its imported helpers. No SAT, enumeration, exact-gate search, or computer-driven case elimination was used in this review. This is not formal verification.

## Verdict

The named-triple rigidity lemma and its application exclude exactly one odd helper in the rank-two-clean, rank-three-even-own ten-gate producer class, provided the stated projection-tree normal form. The proof correctly uses independence of the **physical even values**, a stronger fact than rank three of their own projections. It does not settle the remaining two-helper even escape or the rank-two-own odd-coset escape.

## Named-triple lemma

If `k_i=x+n_i=p_i+q_i`, none of `n_i,p_i,q_i` can repeat within that triple: `p_i=q_i` is excluded, and either other repetition would give `x` equal to a named node. Two distinct three-element named sets with the same sum would have a nonempty symmetric difference of at most six, contradicting the hypothesis. Thus the three sets are identical. Distinct `k_i=x+n_i` give distinct `n_i`, which exhaust that common three-element set; hence `k_1+k_2+k_3=0`. This is a symbolic relation argument, not a search over triples.

## Physical even-value independence

The projection-tree argument gives exactly seven first own-mask occurrences and three entries. The three first even values have independent own projections. Each remaining physical even value is connected to its earlier same-own-mask operand by an even-entry edge; the resulting rooted-fibre trees allow every even-entry free label to be expressed as the XOR of that edge's two physical endpoint values. Since the three entry labels are independent, any subset of the even-entry labels is independent. The first three values remain independent modulo the pure-free subspace because their own masks are independent. Thus all `e=3+(3-A)` physical even values are independent, including when some share an own projection. For `A=1`, this gives five independent physical even values.

## Six-relation cap

With one odd helper `x`, the odd physical nodes are the eight named values plus `x`; the named values have no nonempty relation of size at most six. At least two physical even values are clean because clean rank is two. There cannot be a third distinct clean value: a clean value is determined by its own mask, and the three distinct available even own masks are independent. Thus exactly two even values are clean.

A clean even value cannot be a sum of two named odd nodes, whose residues are all distinct. It has at most one decomposition involving `x`: its named partner must have the same residue as `x`, and there is at most one named node of each residue. This bounds the two clean values together by one odd-pair relation.

Each of the other three even values has at most one named-pair representation and at most one representation as `x` plus a named node. If all three attained both, the named-triple lemma would give a nonzero linear relation among the three physical even values, contradicting their independently established physical-value independence. Thus their odd-pair relation count is at most `2+2+1`, and the total is at most six.

The five even values are independent, so no gate equation can involve three nonzero even values. Every one of the seven non-entry gate equations must therefore have two odd nodes and one even node. In a reduced acyclic circuit, the latest node of a three-value relation is its only possible gate output, so each odd-pair relation accounts for at most one physical equation. Seven non-entry gates cannot fit into six relations. The conclusion follows.

## Direct tree check

`check_tree.py` constructs one specified ten-gate circuit, checks the stated row masks and entry structure, computes ranks and graph component counts for that single circuit, and reports the results. The imported helpers perform direct XOR evaluation and Gaussian elimination on that circuit. The graph routine loops over its specified edge list; it does not enumerate trees or candidate circuits. This is a fixed-instance check of the projection-tree normal form, not evidence replacing the universal hand argument.
