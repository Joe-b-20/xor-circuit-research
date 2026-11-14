# General arguments for unrestricted XOR circuits

2026-11-14, continuing `095f142`. The research priority is general structural
understanding and unrestricted arguments. Restricted lemmas need a specified
role in such an argument. The fixed-budget twelve-consumer case breakdown is
not the active task. Its reviewed results remain saved as supporting history.

## A combined cost forced by the first odd target

[The first-odd-target theorem](FIRST_ODD_TARGET_TRADEOFF.md) gives an unrestricted
tradeoff determined by the target map. Choose a nonzero parity functional with
at least one required non-input odd target. Let H count odd gates beyond the
required odd non-input targets, and let d count gates whose two operands are even. For a required odd target z, let w_o and w_e count its
supported initially odd and initially even coordinate inputs. Then

    H+d >= min_z (w_o(z)+2*w_e(z)-3)/2.                   (1)

Under total input parity this becomes H+d>=(w_min-3)/2. An implementation cannot
avoid the combined cost by moving the work between odd accumulations and even
combinations. The proof counts the actual operand ports in the ancestor cone of
the first odd target. It permits arbitrary sharing, cancellation, repeated reads,
even helper dependencies, and earlier even outputs.

The exact cone identity also identifies the cost of canceled input ancestors
and repeated use within that cone. With r the effective even rank and mu the
odd-graph cycle rank, the whole circuit has

    G=t_o+r+H+d+mu >= t_o+r+b_min+mu.

Here t_o counts required odd non-input values and b_min is the right side of (1).
Using the target-compatible partition bound on r gives a target-only lower bound.
The result is not a promise of a strong numerical bound for every matrix.

## Exact unrestricted families explain the tradeoffs

[Complement sums](COMPLEMENT_TRADEOFF.md) require all n values J+x_i, where J is
the full input XOR. Their optimum is 2n-2 for every n>=4. For even n=2k, (1)
and the even-rank bound prove this directly. Every optimum has minimum even rank,
no odd-graph cycles, and H+d=k-2. Explicit optimal circuits realize every split
between these two types of work. This is a scalable, exact exchange law.

[Shared-helper amplification](SHARED_HELPER_AMPLIFICATION.md) shows that a
one-for-one exchange is not universal. The m targets

    y_i=x+a+b+c_i+d_i

have unrestricted optimum 2m+2. One shared odd intermediate achieves it. Removing
all extra odd values raises the optimum to 3m+1, even when the entire circuit may
be reorganized with arbitrary cancellation. The m-1 penalty is unbounded.
For m>=2 every optimum has exactly one odd helper and zero even redundancy.
The comparison refutes a constant-overhead helper-removal rule; it is not a
separate restricted-bound research program.

## Algebraic explanation can omit almost half the execution cost

[The causal bootstrap family](CAUSAL_BOOTSTRAP_GAP.md) gives explicit square
invertible maps M_(r,k), for every odd r>=3 and k>=2, with

    L(M_(r,k)) = (2r-1)k-2,
    L_cyc(M_(r,k)) = L(M_(r,k)^(-1)) = rk+r-2.

L_cyc counts independent three-term XOR equations that determine all values,
without requiring an executable ordering. The ratio of forward circuit cost to
cyclic cost approaches two. Thus an order-free explanation can omit a linear
amount of actual work, even for square invertible maps. This establishes no
universal upper comparison factor.

The obstruction is the first required value: it has many input coordinates and
must be prepared before the inexpensive relations among targets can be used.
A separate freezing-and-projection argument proves the exact cyclic and inverse
costs. A fixed r=5,k=3 construction verifies the displayed 15-dimensional map,
its 25-gate forward circuit and 18-gate inverse/cyclic realizations. Universal
bounds are proved by hand; no search or enumeration supplies them.

## Foundations and rejected shortcuts

[Parity components](ODD_COMPONENT_DEFECT.md) retain the historical partition-span
theorem and the exact physical accounting E-r=mu+d. For marked networks, even
occurrence aggregates outside the boundary and odd aggregates have rank at most
that defect. These are occurrence statements, not free access to computed spans.
Every all-odd target set has some zero-defect realization, potentially with many
odd helpers; forcing defect alone therefore cannot be a general strategy.

[The quadratic lift](QUADRATIC_LIFT_LIMIT.md) counts each gate once in an exact
tensor identity, but its unconstrained atom model has a sixty-term MixColumns
decomposition. It cannot recover 75. It loses the cost of supplying parents and
the requirement that all influences belong to one executable network.

## Judgment and next task

We now have a genuine unrestricted combined-cost inequality and two exact kinds
of sharing behavior. The causal separation shows why preserving the order in
which values become available matters. None of these facts justifies summing
first-target bounds over overlapping output groups: the shared-helper family
shows how severely that can overcount.

The next task is a general accounting of shared supply across multiple groups or
stages. It must charge each actual helper once, retain what has already been
computed, and measure how that supply reduces the work for later outputs. A new
invariant is welcome if it captures this more directly than parity. Another
fixed-budget classification or a sharper estimate inside the unconstrained
quadratic relaxation is not the objective.

Unrestricted MixColumns remains 75 to 88, with no assumption that 88 is optimal.
All claims above have hand proofs and independent machine reviews, not formal
verification or human certification. Reviews are linked from each note.

[Final scope review](reviews/unrestricted-progress-review.md) checks this synthesis
and the checkpoint against the four independently reviewed proofs.
