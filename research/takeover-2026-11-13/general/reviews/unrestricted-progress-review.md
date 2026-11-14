# Final scope review: unrestricted combined-cost progress

2026-11-14. Independent machine review of the current
[general synthesis](../README.md), [checkpoint](../../CHECKPOINT.md),
[takeover summary](../../SUMMARY.md), and historical
[record, section 46](../../../structure-2026-11-11/RECORD.md).
The four mathematical notes and their individual reviews were checked before
this synthesis review. No new research or circuit search was performed here.

## The general theorem

The first-odd-target statement requires a nonzero parity functional with at
least one required non-input odd target. Its minimum is over those targets,
using initially odd/even coordinate support counts and the weighted quantity
w_o+2*w_e. The full theorem explicitly has this hypothesis; the four synthesis
files now repeat the nonempty-target condition, and the checkpoint explicitly
specifies the minimum's target set. Even required
targets may occur earlier and remain permitted. Initially even coordinates
are individually available, not a free space of all their combinations.

The exact cone identity counts actual operand ports, canceled input ancestors,
and repeated use. Combining H+d with effective even rank r and cycle rank mu
does not duplicate gates. The target-only bound uses the maximum of the even
target population and the rank-plus-startup requirement. Separate parity or
output-group bounds are not summed.

## Exact families and their interpretations

The complement family has optimum 2n-2 for every n>=4. For even n=2k,
the stronger general theorem forces every optimum to have r=k, mu=0,
and H+d=k-2. The displayed constructions attain every split. The laminar
proof remains the separate justification covering odd n.

The shared-helper family has unrestricted optimum 2m+2 for m>=1. The
3m+1 comparison forbids all additional odd values while otherwise permitting
arbitrary rewiring and cancellation. For m>=2, every unrestricted optimum
has one odd helper, minimum even rank, and zero defect. This is correctly
used to refute a universal constant helper-removal allowance, rather than
presented as a separate restricted-bound objective or as uniqueness of the
helper's value.

The odd-arm square family has exact forward, cyclic, and inverse costs with
the stated restrictions r odd, r>=3, and k>=2. Its ratio approaches two by
choosing the parameters large; no universal upper comparison factor follows.
The saved fixed-construction result records dimension/rank 15, forward count
25, inverse/cyclic count 18, and the specified projection checks. These checks
verify a named construction; the universal lower bounds are hand proofs.

## Scope and status

The synthesis accurately prioritizes unrestricted combined-cost arguments
and defers the earlier fixed-budget case queue. Existing restricted results
remain historical support. The parity foundation is attributed to prior
work; the dependent-even refinement is kept distinct from it. The quadratic
relaxation's 60-term ceiling is not a circuit construction or an improvement
to a lower bound.

The four results explain cost, sharing, and executable availability without
claiming a new unrestricted MixColumns number. The 75–88 interval and the
absence of an 88-optimality assumption are preserved. The next shared-supply
problem is explicitly open. Hand proof with independent machine review is
kept distinct from formal verification, human certification, and claims of
literature novelty.

The final saved synthesis passes this scope review. No consequential open
correction remains.
