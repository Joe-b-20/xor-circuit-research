# Obstruction O, exact statement and scope

Main agent, phase 6 (2026-11-12), from `REPORT.md` section 3, `../../review-p/REVIEW.md` section 2 and the
independent verification in `../../review-O/` (own matrix, own parsers, the whole kste corpus: 18,938 valid
circuits, plus the recorded 88, 89, 97; checks, no search). Nothing here changes 75 <= L(MixColumns) <= 88.

## 1. Objects

**Cuts.** A cut is a single primal bit-position block b in {0..7} (16 = 8 x 2 cuts counting the mirror), or a
single mirror group k in {0..7} of a transposed circuit (transposition preserves the gate count for the
32 x 32 MixColumns map; the two summation orders fwd and rev were used). Arbitrary partitions of the eight
groups, arcs, and several cuts at once are NOT covered by this statement.
**Split (identity).** For a circuit T and a cut: level gates = gates nonzero on the cut block; f = first gates
(new block part), e = entries (a level signal plus a signal zero on the block; label = that operand's value),
h = other duplicates; P = gates zero on the block (ordinary, or exits: two level operands with equal block
part). near = f + h, far = |P| + e, |T| = near + far. No exports exist for MixColumns (no free part), so no
export offset enters; for mirror cuts the mirror circuit has the same size.
**Interface quantities.** W = span of the parts outside the block of the required rows that meet the block
(dim 7 at primal blocks 0-6 and mirror groups 0, 2, 5, 6, 7; 19 at primal block 7; 11 at mirror groups 1,
3, 4; verified); the labels of every circuit span W (verified on all 18,941 circuits, all 24 splits).
tau_min = fewest labels spanning W; sigma = e - tau_min; chi as in TWOSIDED 5.3 with W in place of E.
**Lemma O.1 (proved).** At a cut with no exit, chi = tau_min exactly. (chi <= tau_min with the empty
replacement. Conversely, given a replacement R and a spanning set of tau_R elements, remove the last gate of
R; if its value is in the spanning set, put its two operands in instead (at most one more element); |R| + tau_R
does not increase; repeating leaves only labels, so chi >= tau_min.) Hence chi - e = -sigma there.

## 2. The proof templates whose strength is limited

(T0) Fixed baselines: constants A, B with near(T) >= A and far(T) >= B for EVERY MixColumns circuit T at a
fixed cut; conclusion L >= A + B.
(T1) SB*-type correction: constants A, B with near(T) >= A + (chi(T) - e(T)) and far(T) >= B - (chi(T) - e(T))
for EVERY MixColumns circuit T at a fixed cut; conclusion L >= A + B.
**Theorem O (proved from Lemma O.1 and verified witnesses).**
(i) Under (T0): A <= 8 and B <= minfar(cut), so A + B <= 8 + minfar <= 86 at every cut.
(ii) Under (T1): A <= 9 at every cut, and B <= far(W) - sigma(W) for every circuit W with no exit at the cut,
so A + B <= 9 + min over exit-free W of (far - sigma). This is at most 87 at every cut, and exactly 87 at
primal blocks 5, 6 and mirror groups 2, 5, 6 for the witnesses found (least values: 66 at primal block 7, 74
at mirror group 1, 76 at mirror groups 3, 4, 80 at mirror groups 0, 7, 81 at primal block 3, 84 at primal
blocks 2, 4, 85 at primal blocks 0, 1, 87 at P5, P6, M2, M5, M6).
(Review-compat: the "least values" in this paragraph are minima over ALL exit-free witnesses, smaller than the
table column, which is evaluated at the least-far witness; the caps 86 and 87 are corpus caps from checks,
not theorems.) So neither template, at any single cut, can prove L >= 88; neither can exclude an 87-gate circuit.
*Proof of the directions.* (T1) at a circuit T1 gives A <= near(T1) - chi(T1) + e(T1); an upper bound on this
needs a LOWER bound on chi(T1): Lemma O.1 gives chi = tau_min exactly for exit-free T1, so A <= near(T1) +
sigma(T1). The supplier instance (verified at all 16 cuts): far side computing all outside parts honestly, 8
first gates building the 8 non-unit block parts, no non-entry duplicates, one entry per row meeting the block
(label = its outside part): f = 8, h = 0, no exits, e = rows meeting the block (8, 20 or 12), sigma = 1;
primal instances compute MixColumns and are reduced (128-143 gates), mirror instances compute M^T and are
reduced. Hence A <= 9. (T1) at a circuit T2 gives B <= far(T2) + chi(T2) - e(T2); an upper bound needs an
UPPER bound on chi(T2): chi <= tau_min (empty replacement), so B <= far(T2) - sigma(T2) for exit-free T2. The
witnesses are 88-gate verified circuits (each computes MixColumns, is reduced; mirror witnesses' transposes
compute M^T in both orders). Under (T0) the constructed instance gives A <= 8 directly.

**Witness table (verified, review-O; first circuit found at the least far; c1/c2 = kste circuits_1/2.txt with
the file's own line numbers; rec88 = circuits/aes-mixcolumns/aes-mixcolumns-xor88-depth5).**

| cut | witness | near | far | e | tau_min | sigma | 8 + minfar | 9 + (far - sigma) |
|---|---|---|---|---|---|---|---|---|
| P0 | c1 L9 | 11 | 77 | 8 | 7 | 1 | 85 | 85 |
| P1 | c1 L39 | 11 | 77 | 8 | 7 | 1 | 85 | 85 |
| P2 | c1 L2 | 10 | 78 | 9 | 7 | 2 | 86 | 85 |
| P3 | c1 L10 | 12 | 76 | 10 | 7 | 3 | 84 | 82 |
| P4 | c1 L1 | 10 | 78 | 10 | 7 | 3 | 86 | 84 |
| P5 | rec88 | 10 | 78 | 7 | 7 | 0 | 86 | 87 |
| P6 | c1 L1 | 10 | 78 | 7 | 7 | 0 | 86 | 87 |
| P7 | c1 L22 | 24 | 64 | 24 | 19 | 5 | 72 | 68 |
| M0 | c2 L1128 | 11 | 77 | 11 | 7 | 4 | 85 | 82 |
| M1 | c1 L26 | 17 | 71 | 16 | 11 | 5 | 79 | 75 |
| M2 | rec88 | 10 | 78 | 7 | 7 | 0 | 86 | 87 |
| M3 | c1 L4 | 14 | 74 | 18 | 11 | 7 | 82 | 76 |
| M4 | c1 L3 | 15 | 73 | 15 | 11 | 4 | 81 | 78 |
| M5 | c1 L2 | 10 | 78 | 7 | 7 | 0 | 86 | 87 |
| M6 | rec88 | 10 | 78 | 7 | 7 | 0 | 86 | 87 |
| M7 | c1 L1 | 10 | 78 | 10 | 7 | 3 | 86 | 84 |
(Mirror rows in the fwd order. Corrections to earlier text: the block-7 witness formerly cited as
"circuits_3 line 15380" is circuits_3.txt line 13114 (also at far 64); the least far at each cut is attained
by an exit-free circuit.)

## 3. Scope: what escapes the limitation

- **Quantifiers.** The templates are limited because their inequalities are claimed for ALL circuits, so the
  88-gate witnesses and the constructed instances (128-143 gates) must satisfy them. An inequality proved only
  for optimal circuits, or only for circuits with at most 87 gates, is not constrained: the witnesses are not
  known to be optimal while an 87 remains possible, and the constructed instances are far from optimal.
  Theorem 7.1 of TWOSIDED needs only optimal circuits.
- **Interface-dependent baselines.** A bound of the form cost >= min over interfaces I of [nu(I) + phi(I)],
  with nu, phi the least near and far costs for interface I, is not of the forms (T0), (T1) and is not limited
  by O. But (compose/compat Prop 1, reviewed) for the label interface alone this minimum is exactly the least
  size of a circuit with NO EXIT at that cut, which is at most 88 at P7 (the recorded 88 has no exit there); a
  bound on L itself of that form must also carry the exit interface (labels, exit values, precedence).
- **Several cuts at once**, arcs and other partitions, and arguments not of cut form.
- **Corrections other than chi - e**: for an arbitrary correction c(T) the template gives no bound at all
  unless c is constrained; O speaks only about c = 0 and c = chi - e.
What O does NOT say: that cut decompositions are useless for MixColumns. It says that the chain's mechanism (a
free-neighbour export boundary making the supplier rigid, then separately minimised baselines) has no
instance: every MixColumns cut is ring-like, and at a single cut the separately minimised baselines (with or
without the chi - e correction) add to at most 86 (T0) or 87 (T1).
