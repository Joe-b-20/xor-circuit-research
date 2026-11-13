# A ten-gate consumer can return a three-label sum early

2026-11-13. One prescribed construction, verified directly; no search or circuit enumeration. This refutes a local one-XOR-per-exit claim. It does not refute cost-preserving removal of all feedback, and it does not give a twenty-one-gate joint circuit.

Take consumer inputs `z_0,...,z_3` and three independent, physically supplied source values `a,b,c`. The fourth entry label will be `a+b`. Compute the ten consumer-bearing gates

    q = z_0+z_1,
    r = q+z_2,
    t = r+z_3,
    u = t+a,
    v = u+c,
    w = v+b,
    Y_0 = w+z_0,
    Y_1 = v+z_1,
    Y_2 = u+z_2,
    Y_3 = r+(a+b).

They have the four target values

    Y_0 = E_0(z)+(a+b+c),
    Y_1 = E_1(z)+(a+c),
    Y_2 = E_2(z)+a,
    Y_3 = E_3(z)+(a+b).

Their source labels span rank three and have their all-four sum as their only nonzero relation.

Immediately after `w`, before supplying the fourth label `a+b`, the one-gate exit

    e=t+w=a+b+c

is available. If the available source values at that point are precisely the independent `a,b,c`, this returned value needs two source-only XORs: it is neither one available value nor the sum of two. The original own fibre is the chain `t,u,v,w`, whose three entry edges carry `a,c,b`.

To obtain a complete causal circuit from source inputs `a,b,c`, insert `e=t+w`, then supply `a+b=e+c`, and finish the four consumer outputs. This uses ten consumer-bearing and two source-side gates. Alternatively the fourth label can be supplied directly as `a+b`; its timing is still after the demonstrated return.

## The four-entry label relation has weight three

In entry order the actual labels are

    a, c, b, a+b.

Their unique relation uses the first, third, and fourth entries. Their output-influence traces are, respectively,

    {0,1,2},       {0,1},       {0},       {3}.

These traces are independent. Three are odd and one is even. Thus the four-entry branch cannot be divided only into a repeated-label case with two odd traces and a four-label relation with four odd traces. The three-odd-trace case is actually attained.

For the MixColumns consumer labels `d_i=D(s_i)`, the construction specializes by choosing

    a=d_2,       b=d_2+d_3=D(02),       c=d_1+d_2=D(13).

These three values are independent, and the displayed target source parts become `d_0,d_1,d_2,d_3`. The return is `d_0`. This is an interface specification; it does not claim that these three labels and the first-sheet outputs have been jointly supplied within a twenty-one-gate budget.

## The future label cancels the total repair overhead

The example does not establish a saving in total source work. A source-only repair can first compute `a+b` and then `e=(a+b)+c`, using two gates. The later original gate supplying `a+b` is now redundant. This repairs both source-side values with the same two-gate total, while the return itself was not one-XOR realizable from the earlier source values.

The same chronological credit is general for a rank-three entry set consisting of four distinct values with a unique three-term relation. If a rank-three replay ever reaches the exceptional three-label return of [R3](RANK_THREE.md), the earlier entry labels must be an independent triple. They cannot include all four distinct labels, because four available values eliminate the exception. Therefore the missing fourth label is the sum of two members of that earlier triple; the return is that missing label plus the third member. Materialize the missing label as the first repair gate and the return as the second. When its original first supplier later occurs, bypass that gate. This cancels the one extra gate allowed by R3. The missing label cannot be an already available input or free value, since that would have prevented the exception.

After this step, at least four nonzero clean values are available, so no further R3 overhead occurs. Consequently feedback through such a four-value entry set can be removed without increasing the total source-side gate count, even though a particular exit may require two gates at its original position.

In the ten-gate joint-consumer setting, this cost-preserving repair together with the augmented minimum twelve forces at least twelve source-side gates, hence at least twenty-two total gates, **for this three-term-label-relation class**. The distinction between a local exit cost and total replay cost is essential.

The [direct checker](check_ternary_consumer.py) evaluates only the specified construction, its actual chronology, its entry traces, and the displayed MixColumns label substitution. It performs no search.
