# Independent verification of Obstruction O's numbers

Machine verification, phase 6 (2026-11-12), separate model instance (Opus, medium effort), own code only;
saved by the main agent, condensed. Scripts and outputs here: olib.py, scanlib.py, s0_sanity.py ..
s5_witness.py, s1_scan.out, s3_ties.out. Inspection of existing circuits only; no SAT, no search.

**What was checked.**
- Own MixColumns matrix over GF(2^8) (polynomial 0x11b, the files' bit numbering): identical to
  circuits/aes-mixcolumns/aes-mixcolumns.mat.txt and to review-pair/rlib.py mc_model.
- Own parsers (NCFF, pair format), transposition (fwd and rev summation orders), reduction, cut classification.
- Recorded 88@5, 89@4, 97@3 compute MixColumns and are reduced; their transposes compute M^T at the same size.
  The files under rotation/ do not compute MixColumns (rotation-model circuits): no witnesses there.
- The whole kste corpus (~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor): 19,184 lines,
  18,938 reduced MixColumns circuits (the 246 failing lines of circuits_2.txt are those the corpus README marks
  invalid); each split at 8 primal blocks and 8 mirror groups in 2 orders.
- W_b: dim 7 (primal blocks 0-6; mirror groups 0, 2, 5, 6, 7), 19 (primal block 7, 20 rows), 11 (mirror groups
  1, 3, 4, 12 rows); 8 distinct non-unit block parts at every cut; labels span W_b in all 18,941 circuits and
  all 24 splits.
- chi = tau_min at an exit-free cut (proof as in compose/mc/OBSTRUCTION.md Lemma O.1).
- review-p's corrected references reproduced (circuits_3 line 13114 at block 7: f 10, h 14, e 23, 0 exits,
  far 64; line 15380: far 68; circuits_2 line 313 at mirror group 1: far 71, exit-free both orders; line 213 at
  group 4: far 73; circuits_1 line 40 at group 3: far 74, exit-free there but with an exit at primal block 7).
  At every cut the least far with exits allowed equals the exit-free least.
- Supplier instances at all 16 cuts (s2_supplier.py): f = 8, h = 0, no exits, e = 8 / 20 / 12, sigma = 1;
  primal instances compute MixColumns and are reduced (128-143 gates); mirror instances compute M^T and are
  reduced (134-140; transposed back they compute MixColumns but are not reduced).
**Result.** The per-cut table in compose/mc/OBSTRUCTION.md. No cut reaches 88 by either formula, even with the
least favourable tied witness (with other tied witnesses P4 and M7 also reach 87 under 9 + far - sigma).
**Not checked.** REPORT B's statement that the recorded 97 has f = 8, h = 0 at blocks 7 and 0; summation
orders other than fwd and rev; the typed quantities nu, phi.
