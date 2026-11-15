# X3 status (fresh-perspective red team)

**X3b took over from X3 at about 03:05 UTC 2026-11-15** (X3's model hit a usage limit). X3b continues in
this directory; entries below up to 03:00 are X3's.

X3b 03:05: file check after X3 stopped mid-edit (`x3b_check.sh`): all .py compile with -W error after
fixing invalid escapes `K \ GF(4)` in the docstrings of semi.py and semi_check.py (now raw strings);
all 5 .c compile and link; no CR bytes; NOTES.md / SEMI.md complete (NOTES has no section 8 yet: that
is the 05:00 critique slot). No content change to X3's results.
X3b 03:15: task 2 done (NOTES 10.1, message sent): H3's A28 and X1's 11 spangen A28s all have g124's
U (junk 3, c5 = 0), U not 9-coverable [C]; span changes = top redec of {g17, g26}, x=0 indicator in
the middle, new 10-product stage 1. X1's "redec keeps the span" is false [P].
X3b 03:20: [C] singleton-pair family (NOTES 10.2): 64.5M M8-compatible singleton pairs, 36.9M with free
n-junk, 36.4M of those with x^5 junk; data x3b/singleton_classes.npz.
X3b 04:05-04:45: H2 9+5+14 (s59, s58) and X1b g158 (NOTES 10.3-10.4): all minimal slack windows k <= 5,
stage 1 free, O2 (OV for the s59 pair): no completion gives 27 [C]; best 28 (10-coverable U').
Correction 04:20: x3b_cand/cand2 U' key bug ("one U'"), superseded by x3b_cand3.py.
Build path validated (X3/found/x3b-...-drop0-8-10-*: verified 28/6/594/30, control only).
Critique sent 04:30 (NOTES 8). QUEUE.md "X3b" (x3b_night.py, 4 CPUs): all ~60 H2/X1b 9+5+14 files.
X3b 04:58: pair windows of all 86 built 9+5+14 / 10+5+13 files (NOTES 10.5): 52 with completions, all
U' dim 7, none 9-coverable; no 27 [C, O2, stage 1 free].
Running: nothing. Final report sent ~05:05.

Updated 2026-11-15 03:00 UTC. CPU 12 (shared, short jobs).

Running: nothing.

Done (NOTES.md, SEMI.md):
- assumption list (13 items), routes assessed;
- [C] GF(16): all 156,960 optimal inversion circuits are 1 quadratic + 4 chained cubic ANDs, no norm;
- [C] GF(32): MC(x^-1) >= 9 (7 and 8 exhaustively excluded; 18 chunks finished 02:54, 0 found);
- [C] AES: no junk-free top product over 4 known prefixes;
- [C] top layer >= 10 products for operands aff(x) + V0; 10-spans = H2's 10,200 member spans;
- [C] semi-members (107,100 tensors, types (K,K), (K,Q), (Q,K)), junk formula [P], coset classes mod M8,
  positive control on NIST A28 / A29 / A32-AD4 layers; files semi_members.tsv, semi_classes.tsv.

Messages to the coordinator: 02:30 results + critique; 02:45 SEMI.md + correction; 02:50 "12 + 1 is vacuous".
Queue: QUEUE.md entry "X3: small-field inversion from scratch" (1 CPU, low priority).
Next: critique of H1-H4 notes around 05:00; final report by 06:30.
Best: no circuit (analysis agent).
