# Timing of five distinct rank-four entry labels

2026-11-13. Hand proof and one fixed symbolic construction. No circuit search or finite-family checks. This note concerns source-value-preserving repair and gives no new joint MixColumns bound.

## One extra gate after all five values are available

Suppose five distinct nonzero source values spanning a four-dimensional binary space \(U\) are physically available. One additional XOR, or none, suffices to make every value of \(U\) available or the sum of two available values. This follows from the form of the unique relation among the five values. Take four of them as a basis \(a,b,c,d\). The remaining value is a sum of two, three, or four basis elements, since it is distinct from zero and from each basis element. Up to renaming:

- If the fifth value is \(a+b\), add \(c+d\). The basis pairs are one XOR away. Every triple contains one of the supplied pairs \(a+b,c+d\), and the four-term sum is the sum of those two pairs.
- If it is \(a+b+c\), add \(a+d\). The triple \(a+b+c\) is supplied, and the triples \(a+b+d,a+c+d\) use \(a+d\). The remaining triple \(b+c+d\) is \((a+b+c)+(a+d)\). The four-term sum is \((a+b+c)+d\).
- If it is \(a+b+c+d\), add nothing. Adding one basis element to the fifth value gives the complementary triple. Basis pairs already take only one XOR.

Thus the statement covers relation weights three, four, and five. No basis element or pair is treated as available merely because it belongs to a span.

This gives a chronological sufficient condition for a one-gate overhead. Assume all actual entry labels of a circuit belong to \(U\), and replay its source-side gates as in [GENERAL_REPAIR](GENERAL_REPAIR.md). Until the five values are available, copy or bypass ordinary source gates and supply each exit in at most its original one gate whenever possible. If that process reaches a stage with all five values available before any exit requires extra work, apply the preceding construction at that stage. It uses only the already supplied five values. Every later exit is in \(U\), by the causal entry-span invariant, so it can be supplied in at most its original one gate. Values already present before the five labels arrive remain available throughout; they may make earlier exits cost-preserving, or supply the one additional pair without paying another gate. The criterion does not replace the actual availability of five labels by their eventual occurrence later in the circuit.

## Five actual labels need not lower the total overhead

Take four independent ordinary source-coordinate inputs \(a_1,a_2,a_3,a_4\), four ordinary consumer-coordinate inputs \(z_1,z_2,z_3,z_4\), and zero as the only free value. Begin by making
\[
p_i=z_i+a_i\qquad(i=1,2,3,4).
\]
For the three specified index sets
\[
\mathcal I=\{\{1,2,3\},\{1,2,4\},\{1,3,4\}\},
\]
perform the following operations in the displayed order of the index sets. For \(I=\{i<j<k\}\), compute
\[
P_I=(p_i+p_j)+p_k,\qquad Z_I=(z_i+z_j)+z_k,
\qquad t_I=P_I+Z_I,
\]
using left association for each binary chain. Reuse an earlier wire if an identical value is prescribed again. Both chains have nonzero consumer part at every step, because they accumulate nonempty subsets of distinct consumer coordinates. Their final consumer parts agree, so \(t_I\) is a source-side exit with value \(a_i+a_j+a_k\).

Finally make the consumer value
\[
p_1+t_{\{1,3,4\}}=z_1+a_3+a_4.
\]
Designate the three \(t_I\)'s as source outputs and that last value as a consumer output. Every gate is live through one of these outputs. The source side has exactly three physical gates, all exits. There are exactly five entry occurrences: the four gates \(p_i\) and the final gate using \(t_{\{1,3,4\}}\). The two chains for each \(I\) read only consumer-bearing operands. Thus the five distinct actual entry labels are \(a_1,a_2,a_3,a_4,t_{\{1,3,4\}}\), of rank four with one four-term relation. The fifth label is only available after all three exits.

A source-only circuit preserving these three exit values needs at least five gates, even with advance knowledge of all three requests. They are three distinct odd triple sums of four ordinary inputs. In a circuit of at most four gates, the first gate must supply an even pair \(q\), because a new nonzero value from two coordinate units is a pair. That leaves at most the three required odd triple gates. Every odd gate can then only add \(q\) to an earlier odd value, so all attainable odd masks belong to the sets \(\{a_i,a_i+q\}\). Only the two units outside \(q\) produce triples in these sets. This excludes three triple sums in four gates.

Five gates suffice: build \(a_1+a_2\), use it for \(t_{\{1,2,3\}}\) and \(t_{\{1,2,4\}}\), then build \(a_3+a_4\) and add \(a_1\) for \(t_{\{1,3,4\}}\). This order also preserves chronological availability, with two source gates for the first exit, one for the second, and two for the third. The minimum source replay overhead is exactly two.

## Scope of the example

This is a source-only replay lower bound relative to the three original source gates. It gives no comparison between the optimal full feedback and no-feedback circuit sizes.

It is also not an eleven-gate four-row consumer. To see a further limitation, let \(D\) be the kernel in \(U\) of the functional taking value one on \(a_1,a_2\) and zero on \(a_3,a_4\). The returned fifth label \(t_{\{1,3,4\}}\) is nonclean. Its exit operand pair and its later consumer entry pair are two distinct physical pairs with that same difference. Such a nonclean return read verbatim as an entry is forbidden under the one-gate-slack hypothesis of [the collision bound](ENTRY_RETURN_RIGIDITY.md). Thus the example establishes a genuine timing obstruction for general rank-four repair with five distinct labels. It does not settle whether the specialized eleven-gate interface can have that obstruction.
