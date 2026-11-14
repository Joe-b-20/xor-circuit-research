# Final scope review: shared supply and multi-output preparation

2026-11-14. Independent machine review of the current
[general synthesis](../README.md), [checkpoint](../../CHECKPOINT.md),
[summary](../../SUMMARY.md), and [record, section 47](../../../structure-2026-11-11/RECORD.md).
The two mathematical notes have separate complete reviews. This pass checks
their synthesis, limitations, and the newly linked specified verification.
It performs no new mathematical exploration or circuit search.

The multi-output statement explicitly requires a nonzero parity with at least
one required non-input odd target. Its minimum ranges over subsets of those
targets. Distinguished first occurrences, all required ancestors in an
arbitrary cone union, and the special first-k credit are kept distinct. The
prefix inequalities are maximized rather than summed. The common-core
construction and its exact resource and total-cost claims match the proof.

The dictionary is a set of actual available values. Weighted representation
cost is defined on its span without granting that span as available operands.
The one-target formula counts odd and even-plus-even operations, not all
binary gates. The interval argument uses the actual successive dictionaries;
the progress ledger retains unbounded shared benefit and progress made by
required output gates. The exact ternary normal form starts from ordinary
coordinate inputs under total parity with all-odd targets. It preserves the
named resource, not physical pair supply, rank, or joint attainment of separate
minima. The README was asked to repeat the coordinate-input condition already
explicit in the theorem and checkpoint.

The total-parity MixColumns profile is exactly one by the reviewed fixed
ordering argument. The number 57 is explicitly a ceiling on the standalone
rank-plus-profile certificate, not a circuit upper bound or a claimed
MixColumns lower bound. Other parities and arguments retaining actual supply,
cycle, or fanout data are outside that limitation.

I inspected the new checker and saved result. They evaluate one recorded
88-gate circuit, translate it deterministically using the proved pair
representations, and check all 32 output rows. The counts O=48, E=40, r=24,
d=16, mu=0 and 64 ternary gates agree with the saved assertions. The reported
64 is only an upper witness for L_3, not an optimality assertion or a new
binary circuit. The target-order check follows one specified nested sequence;
it does not optimize over subsets. The common-core example uses the explicitly
described odd-accumulation alternative: 17 inputs, 16 gates, H=5, and d=0.
It attains the same proved combined-resource bound as the even-combination
construction. The validation paragraphs distinguish these two versions.

The fixed-budget queue remains deferred. The synthesis accurately identifies
the open problem as the joint cost of odd computation and physical even-pair
supply, with no fixed per-helper benefit assumption. Unrestricted MixColumns
remains 75–88. Machine review and specified-construction checks are kept
distinct from formal verification, human certification, and literature
novelty. No consequential mathematical correction remains.
