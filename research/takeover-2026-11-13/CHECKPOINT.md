# XOR structural research: checkpoint, 2026-11-14

Branch: `research-2026-11-13-structural`. This phase continues reviewed commit
`ed374d1`. Original verified base: `e89b8a25f69195266f1e24e815cb96c7526a3511`
on `phase-2026-11-09`. Other worktrees and `search/proposals/` are preserved.
Our worktree is this chat's `work/xor-structural`.

**New general structure:** odd trace ports are charges on the mirror's odd-value
forest. Cut equations give an exact equality between charge rank and edge-flux
rank modulo the clean target space. Directions invisible to class aggregates are
confined to individual trace copy trees, on the subtrees connecting their ports.

**Exact six-entry decomposition:** if t is the number of distinct traces and H
their aggregate source span, then `dim(H/D)=t-4` and `dim(U/H)=6-t`.
The mirror forest consists of two four-vertex paths, each carrying the same
nonzero clean aggregate. Global rank is 0,1,2 for t=4,5,6 respectively.
Local residual sectors are independent; a repeated pair carries its direction
on one port-connecting path. Different trace classes meet only at H-valued nodes.

**New exclusions and restrictions:** no trace occurs more than twice. The
two-repeated-even-pair profile and the three-term triangle/pair profile are excluded.
All-odd-own source entries are excluded, complementing the earlier all-even floor:
there are 2–5 odd-own entry occurrences. Adjacent equal traces form strict series;
a surviving intermediate must feed a useful exit, the pair sum must be physically
absent from the original source, and the source budget must equal nine.

**Still open:** the twelve-consumer minimum and larger consumer budgets.
An attempted all-odd repeated-trace closure failed: alternative local exposures
need not coexist in one mirror. Its specified counterexample is saved and reviewed.
**Retained:** every candidate below 22 with twelve consumer gates has six entries,
all target-live, actual-label rank five and trace rank four; at most two original
physical clean values. Exact-ten and exact-eleven joint minima and the no-feedback
minimum are 22. Block-monotone MixColumns remains at least 85; unrestricted
`75<=L<=88`. No assumption that 88 is optimal.

All universal statements have hand proofs and independent machine reviews, not
formal verification or human certification. No circuit search or enumeration was used.

## Read next

1. [Current structure, restrictions, and judgment](feedback/CHARGED_FRONTIER.md).
2. [Charged odd forests, exact rank split, and local carriers](feedback/CHARGED_ODD_FOREST.md).
3. [Triple traces excluded](feedback/TRIPLE_TRACE_CLOSED.md),
   [two repeated even pairs](feedback/DOUBLE_EVEN_PAIR_CLOSED.md), and
   [triangle plus separated pair](feedback/TRIANGLE_SEPARATED_PAIR.md).
4. [Odd-only source obstruction](feedback/ODD_ONLY_SIX_ENTRIES.md),
   [free-seeded replay](feedback/FREE_SEEDED_REPLAY.md), and
   [equal-trace series restrictions](feedback/EQUAL_TRACE_SERIES.md).
   [Exposure limitation and counterexample](feedback/TRACE_EXPOSURE_LIMIT.md).
5. Supporting results: [six-entry reduction and complete preceding coverage](feedback/SIX_ENTRY_FRONTIER.md),
   [saturated collisions](feedback/SATURATED_QUOTIENT.md),
   [source parity normal form](feedback/EVEN_ENTRY_SOURCE_FLOOR.md),
   [six-entry trace identities](feedback/TWELVE_ENTRY_WIRES.md),
   [A12](augmented/PROOF.md), and [four-diagonal supplier](feedback/FOUR_DIAGONALS.md).
6. [Takeover history](SUMMARY.md), historical [record](../structure-2026-11-11/RECORD.md),
   [checkpoint](../structure-2026-11-11/CHECKPOINT.md), and
   [visible account](../structure-2026-11-11/visible/VISIBLE.md).

## Distinctions that matter

- H-valued consumer source parts and component clean sums need not be physical
  source values. The charged identities alone imply no replay or gate lower bound.
- Trace parity and source-own parity are different. The unique actual-label relation
  uses odd trace positions; the new source obstruction concerns ordinary b masks.
- The unique even free direction q is available before any consumer entry reads it.
  Seeded replay allows prefixes augmented by that free line. For the first odd-own
  entry h, `G0>=7+m_D+1_{h+q in A}`. At two physical clean values, h+q must be absent
  from the entire original source set, even if it would be supplied later.
- Free-coordinate normalization changes physical values outside U. Recompute
  physical counts and credits in the normalized circuit.
- Equal-trace series restrictions require adjacency. They do not merge all repeated
  traces or treat their intermediate exit uses as dispensable.
- Count only trace sums exposed simultaneously in one literal mirror. Reordering
  an accumulator can change its unmarked even helpers; separate local exposures
  cannot be counted together. The all-odd repeated-trace case is still open.

## Next structural task

Relate the cost of useful returns to the exact global/local split. At four distinct
traces, two local paths carry every nonclean direction while forest aggregates are
clean. At five, one local path interacts with one global direction. At six, all
quotient directions occur in forest charges. The physical carrier and entry-separator
theorems are available; a general joint cost inequality remains to be proved.

Reviews are linked from the current frontier. Use Git with `-c core.filemode=false`;
shared configuration is unchanged. Stage only intended research files.
