# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`d295965`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Other worktrees and `search/proposals/` are preserved.
Our worktree is this chat's `work/xor-structural`.

## Research direction

General unrestricted arguments are the priority. The user rejects incremental
numerical improvements or restricted bounds without a specified unrestricted use.
The twelve-consumer case queue remains deferred. No SAT, circuit enumeration,
exact circuit search, or computer-driven elimination. Specified construction
checks and supporting linear algebra are allowed.

Read [the general synthesis](general/README.md) first.

## New multi-output result

[Shared preparation](general/MULTI_OUTPUT_STARTUP.md): for a nonzero parity with
at least one required non-input odd target, extra odd gates H and even-plus-even
gates d satisfy

    H+d >= B_* = max_k min_(|S|=k)
                       ceil((omega(U(S))-kappa(S)-2k)/2).

S ranges over required non-input odd targets, U is the input-support union,
omega weights odd/even coordinates by 1/2, and kappa is support-overlap component
count. The proof uses the union of the first k target cones, counting shared
preparation once. For arbitrary cone unions the correct credit is ALL required
odd first occurrences in the union, not just chosen roots.

The exact union identity is
2(H_C+d_C)=a+2f-c-2q_C+beta+B_e. Actual prefix unions have q_C=k; support overlap
gives c<=kappa. Different prefixes/parities are maximized, never simply summed.
No enumeration of target subsets is used in the theorem or its applications.

For a common odd core of 2a+1 inputs and disjoint private groups of 2b_i inputs,
min(H+d)=a+sum_i(b_i-1) exactly. The core is paid once. Total binary cost is n-1.
Complete-graph star targets demonstrate a quadratic improvement over the one-
target resource bound as a function of row weight, with no new total-cost claim.

## Physical dictionaries and ternary reformulation

[Available supply](general/AVAILABLE_SUPPLY.md): S contains actual available
values, not every vector in their span. Weighted word length Omega assigns odd
values cost 1 and even values cost 2. Adding v=a+b obeys the exact minimum update.
Odd-plus-odd gates never change Omega; odd and even-plus-even gates reduce it by
zero or two per target. One nonzero target z needs exactly
(Omega_S(z)-w(z))/2 such counted gates. An absent even pair sum can therefore
have counted cost zero while still needing a physical binary XOR.

Actual disjoint intervals can be summed with their actual dictionaries. The
progress ledger credits a helper once with all targets it helps and also records
progress supplied by required output gates. No universal capacity per helper is
assumed.

For coordinate inputs under total parity and all-odd targets,
min_binary(O+d)=L_3(T), hence min(H+d)=L_3(T)-m. Ternary gates XOR three earlier
odd values. Binary even values are represented by pairs of already available
odd values during the translation. This is not free physical binary pair supply.
The reverse translation proves resource equality. Total binary cost, rank, and
joint optimality are not preserved. L_2>=r_min+L_3 is valid; separate minima need
not be jointly attainable.

## A decisive MixColumns limitation

The total-parity support profile B_* is exactly 1. The specified sheet-by-sheet
output order has connected prefix overlaps and union size at most 2k+3; the first
row minimum gives equality. The eight bit-position blocks form a compatible
partition. Therefore the standalone rank-plus-support-profile certificate cannot
exceed 57 and cannot recover 75. This limits that certificate only, not other
parities or stronger physical-supply arguments. Do not invest in optimizing this
same support profile for a numerical MixColumns improvement.

[Direct checks](general/checks/check_supply_certificates.py) verify the displayed
order, a common-core construction, and a deterministic ternary conversion of the
single recorded 88-gate circuit. It has O=48, E=40, r=24, d=16, mu=0 and yields 64 ternary
gates with all 32 outputs verified. This is only an upper witness L_3<=64. The
[saved result](general/checks/supply-certificates-result.json) contains no search.
Both new notes have independent machine reviews; the primary agent checked them.
A [final scope review](general/reviews/shared-supply-progress-review.md) checks
the synthesis and specified-construction evidence.
No formal verification, human certification, or literature-novelty claim.

## Retained results and next task

Unrestricted MixColumns stays 75<=L<=88. Prior general results remain in
[the first-target theorem](general/FIRST_ODD_TARGET_TRADEOFF.md),
[complement tradeoffs](general/COMPLEMENT_TRADEOFF.md),
[shared-helper amplification](general/SHARED_HELPER_AMPLIFICATION.md), and
[causal gaps](general/CAUSAL_BOOTSTRAP_GAP.md). The earlier restricted 85/local 22
results and open fixed-budget cases remain historical support.

Next: couple actual odd-value computation to physical even-pair supply and its
reuse across outputs. The cone-union theorem counts overlap correctly but its
support-only certificate is weak on MixColumns. The dictionary metric solves
one named resource exactly but omits pair-formation cost. A useful theorem must
control their joint realization, not assume free spans or a fixed price per
helper. A different invariant is allowed if it addresses that interaction better.

History: [summary](SUMMARY.md), [record](../structure-2026-11-11/RECORD.md).
Use Git with `-c core.filemode=false`; shared configuration is unchanged.
Stage only intended research files.
