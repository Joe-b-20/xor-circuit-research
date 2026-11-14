# Final scope and evidence review: subspace preparation and sharing capacity

2026-11-14. Independent review of the current
[general synthesis](../README.md), [checkpoint](../../CHECKPOINT.md), newest
[summary entry](../../SUMMARY.md), and Section 51 of the
[research record](../../../structure-2026-11-11/RECORD.md). I checked these against
[SUBSPACE_PREPARATION.md](../SUBSPACE_PREPARATION.md),
[SIDON_SUPPLY_TRADEOFF.md](../SIDON_SUPPLY_TRADEOFF.md), their independent proof
reviews, and the executable evidence. This is machine review, not formal
verification, human certification, or a literature-novelty assessment.

## Scope of the subspace result

The synthesis correctly presents a statement for arbitrary continuations from
an actual supplied dictionary. The selected subspace W and its required
spanning outputs are hypotheses on the problem being analyzed. No circuit is
required to stay in W, use a chosen basis, avoid cancellation, or preserve a
particular decomposition. Supplied dependence and all retained intermediates
are included.

R(S) is a space of values recoverable without outside-W work, not a dictionary
of physically free values. The closure and rank-growth argument is summarized
accurately. The first successful collision forces Delta-2 outside gates, and
the q-1 remaining independent directions require distinct later outside gates.
The temporary free supply of R_0 or U is explicitly a lower-bound relaxation.
The absorption claim preserves the minimum over W minus U, rather than claiming
that every individual word length stays unchanged.

The total-count bound adds only distinct absent W-valued outputs to the outside
count. Outside required outputs of a larger map already contribute to that
outside count and cannot be added again. The checkpoint and record make this
point explicit. All synthesis documents retain the two main limits: W=V makes
the obstruction vacuous, and outside counts for different proper subspaces can
overlap. The proposed next step is to control that overlap; it is not presented
as an already proved additive theorem.

The coordinate specialization retains minimum distance D>=3. The independent
triples corollary uses both independence and absence of weight-one/two vectors
in their full span, giving r=M=m and D=3. Separate two-gate formulas attain the
resulting lower bound 2m. Low-weight combinations are only a necessary condition
for a saving; no sufficiency or pairwise-overlap characterization is asserted.

The common-offset application counts the complete actual prefix dictionary.
Its 4rm-gate prefix is charged separately from the exact remaining cost
m+2r-1. Its individual target frontiers can stay unchanged while the joint
relation space gains dimension m-1. The synthesis does not claim a faster
end-to-end circuit or equality of all dictionary metrics.

## Scope and provenance of the sharing result

The first-target classification and bipartite capacity bound retain both
actual even gate count E and extra odd gate count H. These are physical gate
budgets, not the rank of a granted supply space. Arbitrary extra rank,
even-plus-even computation, repeated values, cancellation, and competing basis
choices remain possible. The Sidon condition is imposed on the full ordinary
input-and-target boundary, not only on targets or on internal circuit values.
The multiplicity extension gives the stated general odd-target-map inequality.

For a Sidon boundary alpha=1 and nu<=1; specifically nu=0 for one target and
nu=1 when at least two targets are present. The resulting Sidon inequality
remains valid in the one-target case. This convention is stated in the source
note and checkpoint and should be preserved in compact summaries.

The affine-incidence family proves exact unrestricted cost by projection and
column cloning; its displayed circuit alone supplies the upper bound. Its
unbounded sequence m=q^3 establishes sharpness of the overhead exponent 2/3,
not a sharp universal constant or a target-forced minimum even rank. The
synthesis maintains those distinctions.

The proof openly refines the earlier four-cycle/Sidon graph mechanism in
SIDON_REPAIR.md and the boundary-pair uniqueness already used in the archived
75 proof. It does not claim a new graph technique or literature novelty. The
absence of a free input-count term comes with the stronger boundary hypothesis
and the parity-resolved resource count.

## Executable evidence

I read [check_subspace_and_sidon.py](../checks/check_subspace_and_sidon.py) and
the imported circuit/rank primitives, ran the checker, and compared its parsed
output with [the saved results](../checks/subspace-sidon-result.json). After the
distance-three construction was aligned with the prose, the checker passed and
the saved JSON matched exactly.

The checker constructs fixed circuits and applies ordinary binary linear
algebra. Its quotient remainders identify colors; its generator ranks track
R(S_t) at every specified gate. It checks the chronological identity and final
rank for those traces. It does not search circuits, representations, target
subsets, or codewords, and it performs no optimization or case elimination.
Building the fixed finite affine-incidence graph is direct verification of one
specified construction, not an enumeration used to prove the Sidon property.
That property and all minimum-distance claims remain symbolic proof claims.

The reported instances are consistent with the synthesis:

- Dimension-three distance-three and distance-four examples have respectively
  three and four outside gates, with six and seven total gates.
- The dimension-one distance-seven example has five outside and six total
  gates.
- The common-offset instance r=m=3 has 36 separately paid prefix gates,
  initial relation rank two, one missing direction, five outside continuation
  gates, and eight continuation gates in total. The specified projection sends
  every retained dictionary member to weight at most one and each target to
  weight seven; the general escape-distance assertion comes from the hand proof.
- The q=3 incidence construction has 45 inputs, 27 distinct weight-five
  targets, 18 nonzero column classes, and 54 gates, with H=9 and E=18. Its
  displayed even supply has rank 18, with no EE gates or odd-graph cycles.

These checks corroborate constructions and accounting identities. They do not
establish global lower bounds or optimality independently of the mathematical
proofs. The synthesis labels their evidence accordingly.

## Overall assessment

The new mathematical scope and the claimed evidence agree. Both lines give
unrestricted circuit constraints under explicit target/dictionary hypotheses;
neither is presented as a restricted competitor model. They are correctly
separated from a new MixColumns-specific bound. The current range remains
75<=L(MixColumns)<=88, with no assumption that 88 is optimal. The next objective
is a general shared accounting across subspaces and sharing relations, rather
than incremental fixed-budget classification.
