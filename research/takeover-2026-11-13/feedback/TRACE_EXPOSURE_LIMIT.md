# Local trace exposure does not bound the global adjacency graph

2026-11-14. A specified symbolic counterexample to a proposed structural inference. No search or circuit enumeration. The example concerns a consumer and its literal mirror, not a joint circuit with a nine-gate source.

## The failed inference

At a vertex where two entry edges meet, an allowed local adjoint accumulation order can expose the sum of their traces on a mirror wire. A six-gate ordinary mirror has only two even helper values.

It does **not** follow that the graph of all distinct trace-class adjacencies has at most two edges. Different pairs meeting at the same original vertex can require different accumulation orders. The unmarked even helpers can change with that order. The existence of each exposure separately does not put all exposed values in one mirror.

Exposures at different original vertices can still be chosen simultaneously, as in the odd-run theorem. The error is to apply that independence to incompatible choices at one vertex.

## A specified six-gate ordinary mirror

On ordinary inputs `x_0,x_1,x_2,x_3`, compute

    p=x_0+x_1,
    t=p+x_2,
    j=t+x_3,
    E_0=j+x_0,
    E_1=j+x_1,
    E_2=j+x_2,
    E_3=t.                  (output alias)

These are six XOR gates and the four outputs are exactly the four triples. The two even gate values are `p=x_0+x_1` and `j=x_0+x_1+x_2+x_3`.

The transpose on ordinary inputs `z_0,z_1,z_2,z_3` can be written as

    r=z_0+z_1,
    q=r+z_2,
    w=q+z_3,
    E_0=w+z_0,
    E_1=w+z_1,
    E_2=w+z_2,
    E_3=q.                  (output alias)

Again there are six XORs. The node `w` has three outgoing target-reader branches, with traces the unit vectors `x_0,x_1,x_2`. An entry placed on each branch gives three pairwise class adjacencies at `w`.

The three corresponding trace sums are

    x_0+x_1,       x_0+x_2,       x_1+x_2.

They can each be exposed by choosing which two contributions to the adjoint of `w` are added first. For example, replace the first two mirror equations by `p'=x_0+x_2`, `t=p'+x_1` to expose the second sum. Choosing `p''=x_1+x_2`, `t=p''+x_0` exposes the third. Each resulting mirror has six gates, with that chosen pair sum and `j` as its two even helpers. There is no single accumulation order that creates all three pair sums within this budget.

The marked ordinary derivative of each chosen pair-sum wire is the all-four mask, the own mask of `w`. The other even helper `j` has derivative `z_0+z_1+z_2`. Thus the existing even-wire separation theorem remains valid in every one of these mirrors.

## A six-entry decoration in the exact rank-five interface

The same example can be decorated with the six-entry trace multiplicities `(2,2,1,1)`. Keep the three ordinary gates `r,q,w` above and compute

    A_1=w+a,
    A_2=A_1+b,
    Y_0=A_2+z_0,
    B_1=w+k,
    B_2=B_1+l,
    Y_1=B_2+z_1,
    C_1=w+c,
    Y_2=C_1+z_2,
    Y_3=q+d.

Together these are twelve consumer-bearing XORs: six ordinary non-entry gates and six entries. Every gate belongs to a relaxed target cone. Direct substitution gives

    Y_0=E_0(z)+(a+b),
    Y_1=E_1(z)+(k+l),
    Y_2=E_2(z)+c,
    Y_3=E_3(z)+d.

Choose the usual rank-three target diagonal values `S,T,c,d` with sole relation `S+T+c+d=0`. Choose `a,k` independent modulo that diagonal and put

    b=a+S,       l=k+T.

The six actual labels have rank five and sole relation

    a+b+k+l+c+d=0.

Their traces are `x_0,x_0,x_1,x_1,x_2,x_3`, respectively, all odd, with four distinct independent trace values. At `w`, the first entries on the `A`, `B`, and `C` branches meet. The trace-class adjacency graph therefore contains the triangle on `x_0,x_1,x_2`, with three edges.

If desired, the allowed source-space shape can also be imposed: choose an even wholly free value `f` and an odd-own value `h`, independent together modulo `D`, and take `a=h`, `k=h+f`. Then the actual entry span is `D direct-sum span{f,h}`. This does not provide those labels and the four source rows within nine gates; no such source supplier is claimed.

## Consequence for the proposed closure

The proposed all-odd, four-trace-class closure used the false global two-edge bound to force a single class path. That proof cannot be relied on and must be withdrawn. The specified example does not refute the desired lower bound: its own return paths use at most two classes and admit the previously described cheap replay. It refutes the structural premise used to exclude all other fibres.

The valid replacement principle is narrower: count trace sums that can be exposed **simultaneously in one literal mirror**. Local alternative exposures, especially three or more branches at one original vertex, cannot be added together as if they were fixed helper values. The all-odd repeated-trace case remains open by this argument.
