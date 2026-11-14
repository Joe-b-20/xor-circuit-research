# Available values, exact preparation cost, and ternary normal form

2026-11-14. General structural hand proofs for unrestricted XOR circuits. No search or enumeration. Independent machine review is linked [here](reviews/available-supply-review.md); it is not formal verification or human certification. No literature-novelty claim is made. The ternary reformulation was proposed by the primary agent and independently reconstructed here.

The [first-odd-target theorem](FIRST_ODD_TARGET_TRADEOFF.md) extends to any actual available dictionary, even when its values are dependent. A weighted word length gives an exact update under each gate and the exact one-target cost in the combined resource of odd gates plus even-plus-even gates. For whole all-odd target maps, that combined resource is exactly ordinary ternary XOR circuit complexity. These statements leave the physical pair-supply cost in the binary gate count.

## 1. The dictionary is physical; its span is not free

Fix a parity functional lambda. Let S be the finite set of nonzero values physically available at some chronological boundary. Its elements may be dependent. Previously computed values remain available, and fanout is free. An arbitrary vector in span(S) is not an available operand merely because it lies in that span.

Give each dictionary value the weight

    w(s)=1 if s is odd,      w(s)=2 if s is even.

For x in span(S), define

    Omega_S(x)=min { sum_{s in R} w(s) : R subset S,
                                           XOR_{s in R} s=x }.       (1)

Put Omega_S(0)=0. A minimum uses each dictionary value at most once. The value Omega_S(x) has the parity lambda(x). Every nonzero physical dictionary value has Omega_S(s)=w(s). An absent odd value has word length at least three; an absent even value can have word length two if it is the sum of two available odd values.

The distinction in the last sentence matters. This word length measures preparation, not whether every even pair sum has already been physically built.

For example, S={a,b,c} and S'={a,b,c,a+b}, with a,b,c independent odd inputs, have identical weighted word lengths for every value. Yet making a+b+c takes two binary XORs from S and one from S'. The combined resource below costs one in both cases. Thus the word length deliberately leaves physical pair supply unresolved.

## 2. Exact update under one binary gate

Let a,b be available and let v=a+b be the gate's nonzero result. Then

    Omega_{S union {v}}(x)
      = min(Omega_S(x), w(v)+Omega_S(x+v)).                         (2)

A representation either omits v or uses it once; its remaining terms lie in S. This proves the formula, including when v was already available.

The parent weights give a sharp distinction.

- For odd-plus-odd producing even v, w(a)+w(b)=w(v)=2. Substituting the two parents for v shows that adding v leaves Omega unchanged for every x.
- For an odd gate, or an even-plus-even gate, w(a)+w(b)=w(v)+2. Substitution shows that each Omega decreases by at most two. Since its parity is fixed, the decrease is either zero or two.

Zero results and reads of a zero operand cannot improve the dictionary and may be treated as inert. Repeated values likewise change no word length. All these gates can still be included in a circuit's cost.

For a gate of the second kind, its affected set is exactly

    A_v(S)={x : Omega_S(x)=w(v)+Omega_S(x+v)+2}.                    (3)

Thus one useful gate shortens each affected weighted representation by two, but the set of affected targets can be arbitrarily large.

## 3. The exact one-target combined resource

For a continuation circuit from S, let P count its odd gates plus its even-plus-even gates. Odd-plus-odd gates remain physical XOR gates but are not counted in this particular resource.

**Theorem 1.** For every nonzero z in span(S), the minimum possible P needed to make z physically available is exactly

    min P = (Omega_S(z)-w(z))/2.                                  (4)

**Lower bound.** Each counted gate decreases the fixed target's word length by at most two; an odd-plus-odd gate changes none. At completion its word length is w(z). Equation (4) follows as a lower bound.

**Attainment.** Choose a minimum representation of z using o odd dictionary values and e even ones. Pair the odd terms using odd-plus-odd gates. If z is even, all o terms can be paired. This leaves o/2+e even operands, which can be combined with o/2+e-1 even-plus-even gates. If z is odd, leave one odd term as an anchor and pair the other o-1 terms. Add the resulting (o-1)/2+e even operands to that anchor through odd gates. The respective counted costs are exactly (4). Already available values may be reused; every operand used is either in S or has just been physically computed. QED.

For one new odd target, its final odd gate is one unit of P. If h counts other odd gates and d counts even-plus-even gates, the exact minimum is therefore

    min(h+d)=(Omega_S(z)-3)/2.                                   (5)

Any split between h and d with this total is attainable: combine some of the even operands first, then add the resulting even operands to the odd anchor. This is an exact statement about one designated target. With several designated targets, this construction might produce another target first; no fixed target-order attainment claim is made.

Equation (4) is not a formula for ordinary binary circuit size. The pair-formation gates used in its attainment have real cost. They are omitted only from the explicitly named resource P.

## 4. Actual chronological intervals can be summed

In a circuit with several required odd targets, order their first appearances. At the start of the interval ending at the next new target z_j, let S_j contain every physically available value. Let h_j count the other odd gates in that interval and let d_j count its even-plus-even gates.

The update bound gives

    h_j+d_j >= (Omega_{S_j}(z_j)-3)/2.                            (6)

The intervals are disjoint, so these inequalities may be summed without counting a gate twice. The dictionaries must be the actual successive dictionaries. Replacing every S_j by the initial dictionary would generally overstate the cost: one shared preparation value can shorten many later targets at once.

The cone proof from the first-target theorem also applies directly: boundary values in S_j need not be independent. The parity of path multiplicities gives a representation using a subset of the physical boundary values, so its weighted size bounds Omega from above. No span element is granted as a free operand.

## 5. An exact ledger for shared progress

Fix m distinct odd targets T that are absent from the initial dictionary and eventually computed. Define

    C_S(z)=(Omega_S(z)-1)/2.

For each gate let A_g be the subset of T whose C value decreases. An odd-plus-odd gate has A_g empty; any other gate decreases C by exactly one at each member of A_g. Since the final C values are zero,

    sum_{z in T} C_initial(z) = sum_{odd or even-plus-even g} |A_g|.   (7)

Mark the m first-production gates of the targets. Each is odd and affects its own target, so |A_g|>=1 there. Let preparation gates mean all remaining odd gates together with all even-plus-even gates. Subtracting m gives the exact identity

    sum_{z in T} (C_initial(z)-1)
      = sum_{preparation g} |A_g|
        + sum_{first-target g} (|A_g|-1).                         (8)

This separates shared preparation from progress on other targets made by a gate that was already needed as an output. It is an accounting identity, not a constant-capacity lower bound.

The [shared-triple family](SHARED_HELPER_AMPLIFICATION.md) shows why that qualification is necessary. Initially each weight-five target has C=2. The common odd triple shortens all m targets to C=1 in one gate; each output gate then finishes its own target. Its single preparation gate has |A_g|=m. In the construction with no odd helper, each of the m even combinations shortens only its corresponding target. Thus a universal bound on the number of targets helped by one preparation gate is false.

## 6. Exact ternary normal form for all-odd target maps

Now use total input parity, so every coordinate input is odd, and suppose every required target is odd. Let L_3(T) be the minimum gate count in a circuit whose gates XOR three earlier odd values. Fanout is free, arbitrary cancellation is allowed, and repeated operands are harmless. Let O and d count odd gates and even-plus-even gates in a binary XOR circuit for T.

**Theorem 2.**

    min_binary (O+d) = L_3(T).                                  (9)

If m counts distinct required non-input targets and H=O-m, then

    min_binary (H+d) = L_3(T)-m.                                (10)

**Binary to ternary.** Proceed in the binary gate order. Keep every already computed odd binary value physically available in the ternary circuit. Represent every already computed even binary value as a pair a+b of earlier available odd ternary values.

An odd-plus-odd binary gate creates such a pair representation at no ternary gate cost. An odd binary gate u+(a+b) is made by the one ternary gate u+a+b. For an even-plus-even binary gate (a+b)+(c+d), introduce the odd value t=a+b+c with one ternary gate and represent the new even value by the pair t+d. Every introduced value is available before it is used. Existing ternary values can be reused when a proposed gate duplicates one. This constructs T with at most O+d ternary gates.

**Ternary to binary.** Expand a+b+c into the even pair a+b and then its sum with c. Each ternary gate uses one odd-plus-odd gate and one odd gate, and no even-plus-even gate. Thus a K-gate ternary circuit gives a binary circuit with O+d=K. The two inequalities prove (9), and subtracting m proves (10). QED.

Even pair representations in the first direction are bookkeeping for the ternary model, not physical free binary values. The theorem preserves the named resource, not total binary size, even rank, or the cheapest pair-supply implementation.

## 7. What remains in the full binary problem

By the exact component account, every binary circuit in the setting of Theorem 2 has

    G=r+(O+d)+mu >= r+L_3(T)+mu.                              (11)

If r_min is a target-forced lower bound on even rank, then

    L_2(T) >= r_min+L_3(T).                                  (12)

This inequality does not establish simultaneous attainment of the separate minima.
Even simultaneous attainment of r_min and L_3 need not determine binary size,
because mu can be positive. The later [graph-tagged family](PRIVATE_TAGGING_TRADEOFF.md)
attains minimum rank and minimum O+d simultaneously while paying an unbounded mu;
its minimum physical pair count k=r+mu and minimum O+d are incompatible. The
missing physical pair-supply cost and its sharing remain part of the binary problem.

For the even complement family, the preceding proofs give L_3=3k-2 and r_min=k, jointly attained by the displayed binary constructions. For the shared-triple family, L_3=m+1 and r_min=m+1 are also jointly attained. These are illustrations, not a universal separation principle.

The dictionary theorem solves the single-target combined resource exactly. Equations (7)–(8) identify the multi-target issue: one new odd value can provide useful preparation to many targets simultaneously. The ternary normal form expresses that sharing as a whole-map computation on actual odd values. A stronger unrestricted argument must control this shared computation together with physical pair supply, rather than assume a constant price per target or a constant price for removing an intermediate.

The [specified checker](checks/check_supply_certificates.py) applies the exact
binary-to-ternary translation to the recorded
`circuits/aes-mixcolumns/aes-mixcolumns-xor88-depth5.circ.txt` construction.
Its physical counts are O=48, E=40, r=24, d=16, and mu=0. The deterministic
translation produces 64 ternary gates and verifies all thirty-two target rows.
This establishes only L_3(MixColumns)<=64, not optimality of that ternary
construction or a new binary circuit. The
[saved result](checks/supply-certificates-result.json) records the direct check;
no circuit or representation search is performed.

No new numerical MixColumns bound is asserted.
