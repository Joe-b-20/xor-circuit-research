# Final scope review: flag activation and common-anchor graphs

2026-11-14. Reviewer: independent `sparse_closure` agent. This is a machine review of mathematical scope and supporting evidence, not formal verification, human certification, or a novelty assessment.

Reviewed the current checkpoint, newest general synthesis sections and closing direction, newest SUMMARY entry, and RECORD Section 52 against [FLAG_RELATION_TRANSPORT.md](../FLAG_RELATION_TRANSPORT.md), [COMMON_ANCHOR_GRAPH.md](../COMMON_ANCHOR_GRAPH.md), and their independent proof reviews. Also inspected the source of [the specified checker](../checks/check_flag_and_anchor.py), its imported quotient-rank routine, and [the saved result](../checks/flag-anchor-result.json).

## Verdict

The synthesis accurately presents the reviewed results and their limitations. No consequential gap or unsupported numerical improvement was found. Two minor wording precisions were sent to the primary author: state the startup correction only when Phi>0, and describe the square path embedding's nonidentity outputs as weight three, since its two identity outputs have weight one.

The key mathematical and attribution distinctions are preserved:

- A general flag permits potential changes -1,0,+1. In a target-prefix flag, strict steps have dimension one, occupied layers remain occupied, and the final appended ambient layer never contributes a deficit. Hence its potential is monotone, with each useful gate activating at most one empty layer.
- Zero output credit requires the circuit's actual selected-output production order. The exact account is G=M+Phi_initial+Z, with Z counting neutral auxiliary gates. Other required outputs remain auxiliaries when omitted from the selection. An arbitrary favorable order cannot be imposed on competitors.
- The startup bound uses initial escape length and potential from the same order. The distance term is not defined when Phi=0; the stated convention then uses zero correction.
- The abstract transport optimum discards actual values and available parents. Its exact Phi moves do not certify a physical Phi-gate circuit.
- The four-coordinate block construction proves unrestricted optimum 5B, including circuits that mix blocks. Only the initial closure decomposition and arbitrary-interleaving argument are blockwise.
- The ceiling 58 concerns the bare complete-flag certificate for a 32-output coordinate-input basis map. It is neither a circuit-complexity upper bound nor a ceiling on the distance-augmented certificate.
- The graph cost m+tau(F) is explicitly attributed to Boyar–Matthews–Peralta's existing theorem. The binary parity proof, relation-closure description, and diagnostic use of the family are kept distinct from any claim of a new optimum or literature novelty.
- The optimality consequences H=d_EE=mu=0 do not imply cancellation-free wiring or anchor-star helpers in every optimum. The five-gate cancelling triangle is explicitly retained.
- The m+1 ceiling on connected common-anchor graphs is for the named target-only certificate after minimization over each selected subset's possible orders. It does not rule out stronger invariants, other lower-bound arguments, or a proved circuit normalization that allows a useful order. Omitted output gates cannot simply be added again.

## Supporting computation

The checker builds five specified examples and performs direct binary linear algebra. It does not search circuits, representations, output orders, vertex covers, or target subsets. Its relation routine computes quotient colors of the actual retained dictionary and spans same-color differences, matching the mathematical definition.

The saved examples agree with the source assertions:

- Three interleaved blocks: 12 independent targets, 15 gates, initial Phi=3, three activating auxiliaries and no neutral auxiliaries.
- Seven-edge path: seven targets, 11 gates, initial Phi=1, one activating auxiliary and three neutral auxiliaries. A displayed four-edge matching certifies the displayed four-vertex cover. The square embedding has rank nine and all rows odd.
- Cancelling triangle: three targets, five gates, even rank two, Phi=1, one activating and one neutral auxiliary. The code directly checks x_2 in both final parents and absent from their XOR, and checks zero parity defect.
- Wrong-order example: the favorable but incorrect target order has Phi=1 while the actual two-output order has Phi=0. The actual circuit has two gates and no auxiliaries.
- Six overlapping cuts: one specified gate increases all six relation ranks but lowers Phi by only one.

For the actual output flags, every gate is checked for interval rank growth, physical endpoint restriction, persistent occupied layers, and monotone potential. Selected first productions are checked to have zero rank credit. The final exact auxiliary ledger is checked. These are supporting checks of displayed constructions; the general proofs do not rely on finite verification.

## Scope of the next direction

The proposed next task follows the evidence: physical supply can remain expensive after relation spaces are already accessible, and common-anchor graphs make that gap exact. Coupling this supply cost to parity partitions or richer dictionary information is compatible with unrestricted sharing and cancellation. Non-nested overlap remains open. The synthesis preserves the unchanged MixColumns range 75–88 and does not assume 88 is optimal.
