# Sprint 2026-11-07: findings

Each entry: observation, mechanism (plain words), prediction that could be wrong, test, what
survived, limits. Tags: [proved] [checked] [measured] [cited] [guess]. Scripts are named; raw
data lives in `~/xs-campaigns/2026-11-07-sprint/`.

## F1. Descending to 88 on MixColumns is cheap; the difficulty is entirely below 88 [measured]

- Observation (hunt, first 25 min, 12 fresh-root chains, v8 uncapped): every chain reached <= 89
  within 10-162 s of its root; 4 of 12 reached 88 within 50-216 s. (`hunt/descents.py`)
- Compare: July 2026 engine, every 88 within 3,855 s of its root, median 2,234 s (restart.root_seconds
  doc string). The v5+ incremental kernel changed the picture: 88 is minutes away from any root.
- Prediction: with hours of such descents, the number of distinct 88 plateaus reached will tell
  whether the 88 level is a small finite set (saturating curve) or vast (linear growth).
- Status: open; curve to be read from `hunt/plateaus.py`.

## F2. A 3-way plateau factor is the pairing choice of an unshared 3-input XOR tree [checked on one circuit]

- Observation: the repo 88@5's remove1 plateau is a product of 7 factors with 3 choices each
  (2,187 states) [checked, PES compress]. For a 3-input XOR s = a ^ b ^ c the intermediate can be
  a^b, a^c or b^c; those three values XOR to zero and each is used only by s.
- Prediction: in every factor the three choice values XOR to zero. Test: `hunt/factors.py` on the
  repo 88@5: 7 of 7 factors satisfy it [checked].
- Consequence: walking an 88 plateau is re-pairing seven 3-input trees. It can never change the
  circuit's structure; the 2,187 states are one circuit in seven interchangeable spellings. A
  plateau walk at the bottom is therefore pure repeated work, and the only genuine moves out are
  the +1 / +2 edits of the 49-value core (which PES explored).
- Extended to all stored PES plateaus (`hunt/pes_plateaus_check.py`, 68 files, 52 distinct 88
  plateaus modulo rotation): 424 of 424 three-way factors XOR to zero [checked]. Radices: 32
  plateaus are 3^7; 13 are 33·3^5, 3 are 45·3^4, 1 is 108·3^4, 2 are 3^6, 1 is 12933·3^2: the
  non-3 factors are coupled blocks where several trees share values.
- Vocabulary: the union of helper values over the 52 plateaus is 524 raw values = 303 modulo
  byte rotation (popcount 2: 54, 3: 99, 4: 111, 5: 98, 6: 86, 7: 45, 8+: 31). The 88 level
  speaks a small language [checked]. Whether new plateaus found by the hunt add words to it is a
  sharper novelty measure than plateau counts (to be tracked).
- Limits: the "unshared" part is inferred from the product structure (if the intermediate had
  another consumer, re-pairing would change that consumer's recipe and the factor would not be
  independent).

## F3. Context from the literature and a public corpus (lit agent, 2026-11-07) [cited]

- 88 XOR is now published: J. Jean, ePrint 2026/1481 (July 2026); earlier 97 (2017), 95, 94,
  92 (2019-20), 91 (2021), 89 (Sun-Yang-Li 2025). Nothing below 88 is claimed anywhere found.
  So 87 would be a new record; 88 is a tie with the literature and NIST.
- github.com/kste/mixcolumns_xor holds 18,938 88-XOR MixColumns circuits (17,462 isomorphism
  classes claimed) and a README arguing an "88-XOR barrier" from a bit-slice block decomposition
  plus SAT/MITM refutations of 87 in stated scopes (73 "double-optimal" circuits; sub-DAGs; a
  1,607-signal pool; a tropical DP). None of the refutations is a general proof; the scopes are
  circuit classes around known 88s. Being checked by the `kste/` agent against our plateaus.
