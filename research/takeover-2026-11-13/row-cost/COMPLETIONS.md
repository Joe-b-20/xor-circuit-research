# Local completions of MixColumns row spans

2026-11-13. Hand proofs and one directly verified circuit construction. No circuit search or subset enumeration. The statements below constrain specified event profiles and leave the unrestricted interval \(75\le L(\mathrm{MixColumns})\le88\) unchanged.

## Row algebra

Use \(e_c\) for the four byte-coordinate units in a block, \(P\) for the linear cyclic shift \(e_c\mapsto e_{c+1}\), and \(J=I+P+P^2+P^3\) for the all-ones operator. The own triple of output \(c\) is \(E_c=(I+J)e_c\) and each of its neighbour labels is \(s_c=(I+P)e_c\). Because \((I+J)^2=I\) and \((I+P)J=0\), the map from the own mask to a neighbour mask is exactly

$$
R=(I+P)(I+J)=I+P.
$$

Thus if \(K_j\) is the span of all four rows of sheet \(j\), its elements are parametrized by \(x\in\mathbb F_2^4\). The element for \(x\) has \(x\) on block \(j\) and \(Rx\) on every other block in \(W_j\). The kernel of \(R\) is the line spanned by \(t=e_0+e_1+e_2+e_3\), since \((I+P)x=0\) means that all coordinates agree. Also \(R^2=I+P^2\) has kernel dimension two, \(R^3=J\), and \(R^4=0\). Let \(t_j\) be the mask \(t\) supported on block \(j\). It is the sum of all four sheet-\(j\) rows.

## One maximal-window sheet

Consider an operand component of [Theorem AC](../continuation/AFFINE.md) assigned some designated output events from one sheet \(j\), where \(W_j\) is a maximal clique in the window graph. Write \(K\) for the span of its assigned rows and \(a+K\) for the component's common coset. Nonlocality of \(a\) ensures a nonzero outside-\(W_j\) mask. Choose a block \(q\) of that mask. The maximal-clique property provides a block \(d\in W_j\) not adjacent to \(q\). Every geometrically local completion in \(a+K\) vanishes on \(d\). Differences of completions therefore lie in the kernel of projection onto \(d\) on \(K\).

If \(d=j\), this kernel is zero. If \(d\ne j\), the kernel on \(K_j\) is the line \(\langle t_j\rangle\). On a proper subset of the four row generators its kernel is zero, since \(t_j\) uses all four independent rows. Consequently:

- For a component assigned a proper subset of the sheet's rows, the completion set is empty or a singleton.
- For a component assigned all four rows, the set is empty, a singleton, or exactly \(\{\ell,\ell+t_j\}\). Only the last case gives a nonzero completion-difference space, and its dimension is one.
- If the set has two points, they belong to a common output window. Pick a completion whose own component on \(j\) is nonzero. A window containing this completion contains block \(j\) and all its other nonzero blocks. The other completion differs only on \(j\), so it belongs to the same window.

In particular this one-dimensional loss occurs within a window. Allowing completion differences between different windows adds no new directions for a single maximal-window sheet.

If all four outputs are events and use only three distinct nonlocal operands, the component rank bound forces all four events into one component. The two-point completion case must occur. The operand forest argument from [Theorem H](../directions/independent.md) shows that the component has two nonlocal/nonlocal edges and two local-partner events, with the three vertices forming a path. On a separated off-own block, the four output projections have rank three and sum to zero. Thus the three vertex projections are independent, and the two local-partner events must attach at the endpoints. Adding the four actual gate equations cancels all three nonlocal values, so the two local partners sum to \(t_j\). They are distinct and both carry the common nonzero outside mask. At least one partner has own-block content and outside content, and hence is a physical gate in another window containing \(j\). This does not imply an additional hidden gate.

## A sharp four-event MixColumns witness

The following construction realizes exactly three hidden gates in a reduced live circuit whose only events are the four sheet-5 outputs. Write \(u_i,x_i,v_i\) for the coordinate inputs of blocks 4, 5, 6, respectively. Let \(q=v_0\), and construct

$$
\begin{array}{lll}
\beta_0=u_0+u_1, & \beta_1=u_0+u_2, & \beta_2=u_3+u_0,\\
p_0=q+x_1+x_3+x_2, & p_1=q+x_0+x_1, & p_2=q+x_3,\\
\ell=p_0+x_0=q+t_5, & a_i=\beta_i+p_i & (i=0,1,2).
\end{array}
$$

Build each \(p_i\) in the input order displayed. The four designated sheet-5 outputs, in row order, are

$$
a_0+q,\qquad a_0+a_1,\qquad a_1+a_2,\qquad a_2+\ell.
$$

Every one cancels block 6. Their own masks are respectively \(E_0,E_1,E_2,E_3\), and their block-4 labels are \(s_0,s_1,s_2,s_3\). The three \(a_i\) meet blocks 4 and 6, which occur in no common window.

Keep the local operands and their ancestors through explicit event-free paths:

| Starting value | Add these inputs in order | Designated output |
| --- | --- | --- |
| \(\ell\) | \(v_2,v_3,x_0,x_3\) | Sheet 6, row 1 |
| \(p_0\) | \(v_1,v_3,x_1\) | Sheet 6, row 2 |
| \(p_1\) | \(v_1,v_2,v_3,v_0\) | Sheet 6, row 0 |
| \(p_2\) | \(v_1,v_2,x_0\) | Sheet 6, row 3 |

For \(\beta_0,\beta_1,\beta_2\), add respectively \(u_2,u_3,u_1\) to form the own triples of sheet 4, rows \(3,1,2\). Append the respective pair on block 3 and then on block 7. Construct each remaining output by an input-coordinate chain in increasing global block and coordinate order. Reuse the earliest node with a matching mask and prune dead gates.

The [direct verifier](check_completions.py) checks the 32 masks, the designated event operand identities, and the live and event-free reachable node sets. It gives 145 distinct non-input live gates, precisely the four sheet-5 output events, and hidden set \(\{a_0,a_1,a_2\}\). The actual local partners are \(q,\ell\), and \(\ell\) belongs to the sheet-6 charge family since it contains block 6 and has an event-free continuation to that sheet. Thus the parity-related local partner can be a retained charge. This example establishes sharpness for hidden-gate counting at the specified event profile, without estimating the least total cost of that profile.

## Two sheets: exact intersection equations

Take distinct sheets \(j,k\) and write \(N_j=W_j\setminus\{j\}\), \(N_k=W_k\setminus\{k\}\). Parametrize the two contributions by their own masks \(x,y\). Let \(b_d(x,y)\) be the block-\(d\) component of their sum. The equations are

$$
\begin{aligned}
b_j(x,y)&=x+[j\in N_k]Ry,\\
b_k(x,y)&=y+[k\in N_j]Rx,\\
b_d(x,y)&=R([d\in N_j]x+[d\in N_k]y)\quad(d\notin\{j,k\}).
\end{aligned}
$$

There is no reciprocal own-block incidence for MixColumns. Thus the first two equations are triangular and define an invertible map from \((x,y)\) to the two own-block values. In particular \(K=K_j+K_k\) has dimension eight. A window \(U\) is eligible for a local completion in \(a+K\) exactly when the equations

$$
b_d(x,y)=a_d \qquad(d\notin U)
$$

are consistent. Their solution, if any, is an affine translate of their homogeneous kernel. This gives the following dimensions for the kernel \(K\cap V_U\), independent of eligibility:

- If \(U\) omits both own blocks, the kernel is zero.
- If \(U\) includes both own blocks, let \(\rho\) be the rank over \(\mathbb F_2\) of the omitted neighbour incidence vectors \(([d\in N_j],[d\in N_k])\). The dimension is \(8-3\rho\). Each independent incidence constraint imposes one rank-three equation with \(R\).
- If \(U\) omits only \(j\), put \(\epsilon=[j\in N_k]\). The homogeneous own equation gives \(x=\epsilon Ry\), so every remaining omitted block imposes
  \[
  [d\in N_k]Ry+\epsilon[d\in N_j]R^2y=0.
  \]
  If any such \(d\) is in \(N_k\), the equation has kernel \(\ker R\), because \(I+R=P\) is invertible and preserves \(\ker R\). All other equations vanish on \(\ker R\). The dimension is then one. Otherwise if \(\epsilon=1\) and some other omitted block is in \(N_j\), the constraint is \(R^2 y=0\) and the dimension is two. In the remaining case the dimension is four. The case omitting only \(k\) interchanges the roles.

These formulas classify the within-window completion directions by symbolic row structure. For several eligible windows, their kernel spaces and the differences between one representative from each window determine the full \(\Delta\) by [equation (3) of AFFINE](../continuation/AFFINE.md). The dimension of a single window intersection is insufficient to bound the sum when representative differences or different kernel directions are present.

## A two-sheet profile with an exact completion plane

Let all eight outputs of sheets 2 and 3 be selected events, each cancelling block 4. These events necessarily have a nonlocal operand. Sheet 2 contains block 1 and sheet 3 contains block 2, and neither block occurs with block 4 in a window. Take the common enclosing block set \(\{1,2,3,7\}\) of the selected values. In each operand component the outside mask is fixed and nonzero on block 4. Every possible local partner therefore vanishes on both blocks 1 and 2. For the full row span, the projection onto those two blocks has rank six: its kernel is described by

$$
Rx=0,\qquad x+Ry=0,
$$

which is equivalent to \(x=Ry,\ R^2y=0\) and has dimension two. Applying the projection bound componentwise gives at least six distinct nonlocal operands, even if the components are split. Indeed the sum of the ranks of the projected component row spans is at least the rank of the full projected span.

The affine quotient has an exact description when all eight rows belong to one component and its outside mask is supported exactly on block 4. A local completion must fit \(W_4=\{3,4,7\}\) or \(W_5=\{4,5\}\), the only windows containing block 4. A \(W_5\)-completion has no nonzero component on block 5, so it is supported on block 4 alone and also fits \(W_4\). Thus the entire completion set is either empty or a single affine plane, with direction \(K\cap V_{W_4}\) of dimension two by the previous equations. The nonempty case occurs geometrically, for example with \(a=q+f\) for a block-4 input \(q\) and a sheet-2 row \(f\). The completion \(q\) then belongs to \(a+K\), while \(a\) is nonlocal. This last example describes a coset and does not assert realization of all eight events with six hidden gates.

If these eight designated outputs are the complete visible set in a reduced circuit, Theorem V's 84 form gives \(G\ge 84+6-(4\cdot 2+4\cdot 3)+4=74\), using the four own-triple sharing credits of [JOINT](../directions/JOINT.md). This profile illustrates simultaneous row rank across two windows but does not improve the unrestricted lower bound.
