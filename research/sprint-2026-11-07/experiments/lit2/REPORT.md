# Literature report 2: XOR-gate complexity of AES MixColumns (one 32x32 column)

Date: 2026-11-07. Scope: 2-input XOR straight-line programs (g-XOR / SLP length, cancellation allowed) unless a model is named. Labels: [found online] = read on a primary page (abstract page, file, README) or in a secondary page that quotes the primary; [not found] = searched, nothing; [inferred] = my deduction from what was read. "Snippet" = a search-engine excerpt of a PDF I could not open.

Retrieval constraints this run: every eprint.iacr.org PDF returns 403 (WebFetch), a Cloudflare "Just a moment" page (curl with browser UA), and a Cloudflare Turnstile challenge in the desktop browser pane, which I did not click through (bot-check rule). ePrint abstract pages, iacr.org news items, raw.githubusercontent.com, arxiv.org and the arXiv API, ISI Digital Commons and aimsciences work. tosc.iacr.org, tches.iacr.org, ojs.ub.rub.de, philosophymindscience.org and dblp.org are behind Anubis (access denied); DOAJ and peerj.com 403. api.semanticscholar.org rate-limited (429) on all three tries. Files saved under ~/xs-campaigns/2026-11-07-sprint/lit2/dl/ (kste README, NIST circuit files, Cloudflare page), scripts mcstats.py and show_nist.py in lit2/. The earlier report lit/REPORT.txt remains valid; this one adds to it.

---

## 1. J. Jean, ePrint 2026/1481

| Item | Finding | Status |
|---|---|---|
| Title | "88-XOR Implementation of the AES MixColumns Matrix" | [found online] abstract page, IACR news item 29064 |
| Author | Jeremy Jean, ANSSI | [found online] |
| Dates | received 2026-07-20, approved/posted 2026-07-23; keyword "AES"; licence CC BY | [found online] |
| Abstract (verbatim) | "We give in this short note a circuit implementing the matrix-vector product with the 32x32 binary matrix of the AES MixColumns using 88 XOR gates. Previously known circuits minimizing this metric have been published in the past years and achieved 94 XOR, 92 XOR, 91 XOR, and 89 XOR. As far as we can tell, a circuit with 88 XOR was previously unknown." | [found online] |
| Length / nature | a two-page note (per Pandey, arXiv 2609.20873, who read the PDF) | [found online] secondary |
| Method | Not stated in the abstract. Pandey quotes the acknowledgements: the circuit was "found with the help of AI, most specifically models from OpenAI under codex". No algorithm (BP variant, SAT, local search) is described in any text I could read. | [found online] secondary; method itself [not found] |
| Depth of the 88 circuit | Not in the abstract or the news item. Our own repo README (github.com/Joe-b-20/aes-mixcolumns-xor-circuits) says the 88@5 is "two levels shallower" than Jean's and that our depth-7 88-gate circuit shares 61 of 88 values with Jean's; that puts Jean's circuit at depth 7. | [inferred] from secondary text only; PDF unread |
| Lower bound / optimality | None. Pandey: the note "reports no lower bound, no optimality claim, and no correctness-verification procedure". | [found online] secondary |
| Is 87 discussed | No (abstract: no; Pandey's reading: no). | [found online] |
| Prior art he cites | 94 (Tan-Peyrin), 92 (Maximov / Xiang et al.), 91 (Lin et al.), 89 ([SYL25] = Sun-Yang-Li ePrint 2025/1493). He omits 95 (Banik-Funabiki-Isobe 2019). | [found online] |

Mirrors tried: eprint.iacr.org/2026/1481.pdf (403 on three routes), Google Scholar / Semantic Scholar (429), IACR news item (abstract only), ePrint "complete/compact" listing (no PDF). The PDF still has to be downloaded by hand in a normal browser.

---

## 2. Table of bounds

### 2a. Upper bounds (smallest published circuits, by depth)

| Model | Depth | Bound | Source | Verified how |
|---|---|---|---|---|
| 2-XOR | 3 | 103 | Banik-Funabiki-Isobe, IEICE Trans. Fund. 2021 (randomised depth-limited BP, after Li et al. FSE 2019 at 105) | [found online] snippet of IEICE index, secondary |
| 2-XOR | 3 | 103 | Liu, Wang, Fan, Wu, Sun, Wang, ToSC 2022(1) / ePrint 2022/231 (backward search) | [found online] abstract page |
| 2-XOR | 3 | 102 | Liu, Zhao, Wang, CT-RSA 2023 / ePrint 2023/174 ("102 XORs under minimum latency") | [found online] abstract page |
| 2-XOR | 3 | 99 | Shi, Feng, Xu, "A Framework with Improved Heuristics to Optimize Low-Latency Implementations of Linear Layers", ToSC 2023(4):489-510 | [found online] snippet of the ToSC PDF and abstract; page itself Anubis-blocked |
| 2-XOR | 3 | 97 | NIST Circuits repo, aes-mixcols-xor97-depth3.circ.txt, file timestamp 2026-08-29, "Compiled by: NIST circuit complexity team", no external credit | [found online] file downloaded (dl/nist_97d3.txt) |
| 2-XOR | 4 | 97 | Osvik-Canright, "A More Compact AES, and More", ePrint 2024/1076 | [found online] search snippet of the PDF only ("97-XOR depth-4 variant") |
| 2-XOR | 4 | 90 | NIST Circuits repo, aes-mixcols-xor90-depth4.circ.txt, timestamp 2026-08-30, uncredited | [found online] file downloaded |
| 2-XOR | 5 | 94 | Osvik-Canright, ePrint 2024/1076 ("94 XORs at depth 5") | [found online] snippet only |
| 2-XOR | 5 | 88 | NIST Circuits repo, aes-mixcols-xor88-depth5.circ.txt, timestamp 2026-08-28, uncredited | [found online] file downloaded |
| 2-XOR | 5 | 88 | github.com/kste/mixcolumns_xor, circuits_depth5.txt: 46 pairwise non-isomorphic depth-5 88-XOR circuits (unreviewed, undated, author "kste" only) | [found online] README downloaded |
| 2-XOR | 6 | 95 | Banik-Funabiki-Isobe, IWSEC 2019 / ePrint 2019/856 (depth 6 per PeerJ cs-1820 Table 5) | [found online] abstract (count) + secondary table (depth) |
| 2-XOR | 6 | 92 | Maximov, ePrint 2019/833: abstract reads "92 XOR gates and depth 6" | [found online] abstract page |
| 2-XOR | 6 | 92 | Xiang, Zeng, Lin, Bao, Zhang, ToSC 2020(2) (depth 6 per PeerJ table) | [found online] secondary table |
| 2-XOR | 6 | 88 | kste repo circuits_1.txt: 47 circuits, min depth 6 (unreviewed) | [found online] README |
| 2-XOR | 7 | 91 | Lin, Xiang, Zeng, Zhang, CT-RSA 2021 (depth 7 per PeerJ table); 91 also obtained independently by Yuan et al., ToSC 2024 (per Pandey) | [found online] secondary |
| 2-XOR | 7 (inferred) | 88 | Jean, ePrint 2026/1481 | count [found online]; depth [inferred] |
| 2-XOR | 9 | 94 | Tan-Peyrin, TCHES 2020(1) / ePrint 2019/847 | [found online] abstract + secondary table |
| 2-XOR | n/s | 89 | Sun, Yang, Li, "Revisit the Boyar-Peralta Algorithm to Solve the Shortest Linear Program Problem", ePrint 2025/1493 (rev. 2025-11-13); "requiring only 89 g-XOR operations", previous best 91; depth not stated on the page | [found online] abstract page |
| 2-XOR | n/s | 97 | Kranz, Leander, Stoffelen, Wiemer, ToSC 2017(4) | [found online] |
| 2-XOR | n/s | 103 / 108 | Jean-Moradi-Peyrin-Sasdrich CHES 2017 (103); Satoh et al. ASIACRYPT 2001 (108), as listed by Pandey | [found online] secondary |
| XOR2/3/4 mix | 3 | 44 gates (5 XOR2 + 7 XOR3 + 32 XOR4) | Kurt Pehlivanoglu-Demir, PeerJ CS 10:e1820 (2024); earlier Liu et al. 2022 (55 gates, depth 5), Baksi et al. 2021 (59, depth 4), BFI 2019 (39 XOR2 + 28 XOR3) | [found online] PMC full text; different model, not comparable |
| quantum (CNOT) | depth 10 | n/a | Xu-Sun arXiv 2511.18226 (v2 2026-05); Zhang et al. IEEE TC 2024 | [found online]; different metric |

Our numbers for comparison: 88@5, 89@4, 97@3 (plus 88 at depths 6-8 in our repo).

### 2b. Lower bounds

| Model | Depth | Bound | Source | Verified how |
|---|---|---|---|---|
| 2-XOR, fixed MixColumns matrix | any | 32 (counting bound: 32 distinct outputs, none an input) | Pandey, arXiv 2609.20873 (Sept 2026): "no lower bound of any kind is published" for this matrix; the free counting bound 32 is the floor of his Figure 3 | [found online] |
| 2-XOR, fixed matrix | any | 34 (trivial): every output row has weight 5 or 7; no row is the XOR of two other rows and no row is another row plus one input (computed, mcstats.py), so each output gate has a non-output, non-input operand of weight >= 3, which itself needs >= 2 gates | [inferred] my derivation; not in any paper |
| 2-XOR, fixed matrix | depth floor | depth >= 3 (max row weight 7, ceil(log2 7) = 3) | kste README states the same floor but from "maximum Hamming weight ... is 5", which is wrong: 12 of the 32 rows have weight 7 (mcstats.py) | [inferred] |
| d-XOR (trivial per-output implementation) | - | 152 = 184 ones - 32 | computed; NIST defines d-XOR this way | [inferred] |
| sw-XOR (sequential word XOR), any 4x4 MDS over GL(n,F2) | - | >= 8n + 3, i.e. 67 for n = 8; tight for n = 4 (35) and n = 8 (67) | Venkateswarlu, Kesarwani, Sarkar, "On the Lower Bound of Cost of MDS Matrices", ToSC 2022(4):266-290, DOI 10.46586/tosc.v2022.i4.266-290. Abstract also says the bound "matches the known lower bounds according to s-XOR and g-XOR metrics" for those n (body unread; which g-XOR bounds are meant is unclear) | [found online] abstract via ISI Digital Commons |
| sw-XOR, 4x4 MDS over GL(n,F2) | - | >= 8n + 2 | Wang, Li, Tian, Zeng, "Four by four MDS matrices with the fewest XOR gates based on words", Adv. Math. Commun. 17(4):845-872 (2023) | [found online] abstract |
| word-level fan-in-2 additions, t x t MDS over large prime fields | - | t=4: >= 8 (tight); t=3..8: 5, 8, 12, 16, 21, 26 (tight for t <= 6) via the superconcentrator property of the circuit DAG | Lee, Park, Son, "Addition-Efficient MDS Matrices from Superconcentrators", ASIACRYPT 2026 / ePrint 2026/1973 | [found online] abstract; word-level, not a bit-level bound |
| general linear circuits, explicit families | - | 3n - o(n) (Chashkin; from Hamming parity-check matrix at 2n - o(n)); gate elimination "essentially the only known" technique for linear lower bounds | Boyar-Find, arXiv 1207.5321 / 1305.3041 and surveys cited there | [found online]; asymptotic, specific families, not applicable to a fixed 32x32 matrix |
| cancellation-free 2-XOR | - | Omega(number of ones) for matrices whose bipartite graph is K_{h+1,k+1}-free; (1/2) n log n for Sierpinski | Boyar-Find 2012 | [found online]; MixColumns is not in a regime where this beats trivial |
| 2-XOR, fixed matrix, scoped SAT claims | any | "UNSAT at <= 87 gates" inside a 1,607-signal "Z4-closed pool"; "UNSAT for < 88" over 73 "double-optimal" circuits (CaDiCaL, 42.6 CPU h); a "tropical DP" giving ">= 80 + 8 => 88" | kste/mixcolumns_xor README, section "The 88-XOR Barrier"; unreviewed, scopes restricted, no artefacts beyond the README; Pandey does not mention it | [found online] README; not a published bound |
| 2-XOR, fixed matrix | any | 75 | owner's computer-assisted proof (github.com/Joe-b-20/aes-mixcolumns-xor-circuits release v4.0.0, "review draft") | own work, not literature |
| 2-XOR, fixed matrix | 3 | 93 (ours); the older owner repo README says 80 (certificate) / 81 (time-limited) and 92 for a restricted class | own work | own work |

Conclusion for Task 2: the best published unrestricted (g-XOR) lower bound for the fixed MixColumns matrix is the counting bound 32; nothing above it is published, and a September 2026 arXiv paper says so explicitly. The only published bounds in the 60s (67 sw-XOR; 8 word additions, which is 64 bit-XORs only if additions are whole-word) are in restricted or word-level models and do not transfer to g-XOR. Relative to the literature, a proven 75 is new by a wide margin; a proven 93 at depth 3 is likewise unprecedented (no depth-limited lower bound for this matrix was found at all).

---

## 3. Structure of near-optimal circuits and lower-bound techniques (Task 4)

Published on MixColumns circuit structure: nothing. No paper describes plateaus, neutral networks, counts of optimal circuits, or "no 87" arguments. [not found]

Unreviewed but on point:
- kste/mixcolumns_xor README (dl/kste_README.md, lines ~95-120): 18,938 88-XOR circuits in 17,462 isomorphism classes (isomorphism = equal sets of 32-bit gate signatures), depths 5-12; 46 at depth 5; "SAT verification ... depth <= 4 is UNSAT at 88 XORs"; a bit-slice decomposition into 6 blocks with isolated minima summing to 83 and a "slack conservation law" (slacks sum to 5 in every known 88); a "16-gate quotient core"; SAT/MITM refutation table with restricted scopes (see 2b). Also 14,324 88-XOR Inverse MixColumns circuits (depths 16-34). No author, date, paper or external reference; the depth-floor premise (max weight 5) is factually wrong. Treat as a hypothesis generator, not evidence.
- Pandey, "The Refutation Gap: Certifying Both Halves of an Optimality Claim", arXiv 2609.20873 (16 Sep 2026, cs.LO): a pipeline for minimal XOR circuits over GF(2) that emits DRAT proofs checked independently; 121 optimality results for n = 6..9 (111 by verified refutation, 10 by a counting bound). Relevant as the certification standard a MixColumns lower bound would be held to; it treats MixColumns only as a case study of a record with no lower bound.

Lower-bound techniques in the literature that could apply:
- Gate elimination for linear circuits (substitute an input, remove the gates it feeds; the Boyar-Find survey calls it essentially the only technique for linear lower bounds). Gives only linear-in-n bounds and, for a fixed 32x32 matrix, nothing beyond the trivial 32-40 range without matrix-specific case analysis.
- Cancellation-free restriction (Boyar-Peralta; Boyar-Find 2012): structure is much easier to reason about; the known gap between cancellation-free and general size is a factor up to 2 (Svensson), so a cancellation-free bound for MixColumns would not transfer.
- Superconcentrator / DAG connectivity (Lee-Park-Son 2026): the circuit DAG of an MDS map is a superconcentrator at word level; size-reduction lemmas give tight small-t bounds over large fields. At bit level the MDS property gives only byte-block nonsingularity, so the argument would need a bit-level analogue; untested.
- sw-XOR / s-XOR design bounds (Venkateswarlu et al. 2022; Wang et al. 2023; Jean-Peyrin-Sim-Tourteaux ToSC 2017 for small exhaustive searches): bound the best matrix in a class under a sequential model, not a given matrix under g-XOR.
- Exact SAT with proof logging (Pandey 2026; Stoffelen FSE 2016 for S-boxes): feasible for full matrices up to n of about 9; for 32x32 only on sub-blocks or with strong symmetry breaking.
- Structural heuristics that exploit the matrix: Sun-Yang-Li 2025 ("analysis of the structural properties of the AES linear layer matrix", abstract only); Xu-Sun arXiv 2511.18226 (circulant structure to build transformation matrices for heuristics); Huang-Sun-Wu-Chen ePrint 2026/2520 (GPU meet-in-the-middle BP; InvMixColumns 157 g-XOR at depth 5; no forward MixColumns figure, no optimality claims).

---

## 4. 2025-2026 items checked for missed results

- ePrint search "MixColumns" (32 hits): only 2026/1481 concerns XOR counts; 2026/786 (Gerhalter-Eichlseder, degree bounds), 2026/2608, 2025/2240 are unrelated to circuit size. [found online]
- arXiv API (MixColumns / shortest linear program / XOR count, newest first): only Xu-Sun 2511.18226 is relevant; nothing on bounds. [found online]
- Web searches for "87 XOR", "88 barrier", "MixColumns lower bound", "mixcolumns_xor github": only Jean, Pandey, kste, NIST and our own repos surface. [found online]
- NIST list-of-circuits (last updated 2026-11-05): MixColumns 97@3, 90@4, 88@5 (files compiled 2026-08-28..30 by "NIST circuit complexity team", README gives no credit; commits by brandao-git 2026-09-23 to 10-02); Inverse MixColumns 119@5, 106@6, 102@7, 96@8, 95@9, 91@15, 90@20. The "AES implementations" header line "MixColumns: G<=86; G<=93/GD3", "Inverse MixColumns: G<=105/GD<=5", "S-Box ...: A<=27; G<=100; G<=110/GD<=14" is undefined on the page; since A<=27 is below every known S-box AND count, the line reads as a list of open targets, not achieved circuits. [inferred]
- Yu-Liu ePrint 2025/1960 (MRM / Hsilu), Lee-Park-Son 2026/1973, Huang et al. 2026/2520: no forward MixColumns numbers. [found online]
- Semantic Scholar citation sweep: failed (429). dblp: Anubis. So "cited-by" of Jean's note could not be enumerated beyond Pandey and our repos. [not found]

---

## 5. Which of our numbers are new relative to the literature

| Our result | Literature status | Verdict |
|---|---|---|
| 88 gates (any depth) | Jean, ePrint 2026/1481, received 2026-07-20, has priority for the count. | not new |
| 88 at depth 5 | No paper gives an 88 at depth 5 (Jean's depth is unstated, inferred 7). The NIST repository already lists an uncredited 88@5 (file compiled 2026-08-28) and the kste repo lists 46 depth-5 88s (unreviewed, undated). | new relative to papers [not found in any paper]; already public in two repositories, provenance unknown |
| 89 at depth 4 | Best published depth-4 figure is 97 (Osvik-Canright 2024, snippet); NIST lists 90@4 (uncredited). Nothing at 89 or below found. | new [not found] |
| 97 at depth 3 | Best published paper figure 99 (Shi-Feng-Xu ToSC 2023); NIST lists an uncredited 97@3 (compiled 2026-08-29). | new relative to papers; ties the NIST entry |
| 93 lower bound at depth 3 | No depth-limited lower bound for MixColumns published anywhere. | new [not found] |
| 75 unrestricted lower bound | Only the counting bound 32 is published; Pandey (Sept 2026) states no lower bound of any kind exists in print. Best bounds in the 60s are restricted-model (sw-XOR 67) or word-level and do not transfer. | new [found online: explicit statement of absence] |
| 87 | Not discussed by Jean or Pandey; kste claims scoped UNSAT at <= 87 (unreviewed); NIST's "G<=86" line appears to be a target. | open in the literature |

Caveat on provenance: the NIST 97@3 / 90@4 / 88@5 files carry no source; if they were taken from our public repo, the "ties NIST" lines above are ties with ourselves. The NIST team (committer brandao-git) could be asked.

---

## 6. Sources (URL, what was read, status)

Primary / abstract pages read:
- https://eprint.iacr.org/2026/1481 (Jean; abstract page) - read. PDF https://eprint.iacr.org/2026/1481.pdf - blocked (Cloudflare 403 / Turnstile).
- https://iacr.org/news/item/29064 (IACR news, Jean) - read.
- https://arxiv.org/abs/2609.20873 and https://arxiv.org/html/2609.20873 (Pandey, Refutation Gap) - read.
- https://eprint.iacr.org/2025/1493 (Sun-Yang-Li, 89 g-XOR) - abstract read; PDF blocked.
- https://eprint.iacr.org/2019/833 (Maximov, 92 at depth 6) - abstract read.
- https://eprint.iacr.org/2019/856 (Banik-Funabiki-Isobe 2019, 95) - abstract read.
- https://eprint.iacr.org/2022/231 (Liu et al. ToSC 2022, 103 at depth 3) - abstract read.
- https://eprint.iacr.org/2023/174 (Liu-Zhao-Wang CT-RSA 2023, 102 at min latency) - abstract read; PDF blocked.
- https://eprint.iacr.org/2024/1076 (Osvik-Canright) - abstract read (no numbers); 94@5 / 97@4 from a search snippet of the PDF only.
- https://eprint.iacr.org/2026/1973 (Lee-Park-Son, superconcentrator MDS bounds) - abstract read.
- https://eprint.iacr.org/2026/2520 (Huang et al., GPU BP) - abstract read.
- https://eprint.iacr.org/2025/1960 (Yu-Liu, MRM) - abstract read; irrelevant.
- https://eprint.iacr.org/search?q=MixColumns - read (32 hits).
- https://arxiv.org/abs/2511.18226 (Xu-Sun) - read.
- https://pmc.ncbi.nlm.nih.gov/articles/PMC10807753/ (PeerJ cs-1820 full text; Table 5 with depths for 95/94/92/92/91) - read. peerj.com itself 403.
- https://digitalcommons.isical.ac.in/journal-articles/2831 (Venkateswarlu-Kesarwani-Sarkar ToSC 2022, 8n+3 sw-XOR) - abstract read; tosc.iacr.org and ojs.ub.rub.de Anubis-blocked.
- https://www.aimsciences.org/article/doi/10.3934/amc.2021025 (Wang-Li-Tian-Zeng, 8n+2 sw-XOR) - abstract read.
- https://ar5iv.labs.arxiv.org/html/1207.5321 (Boyar-Find, cancellation-free) - read.
- https://github.com/kste/mixcolumns_xor and raw README - read, saved to dl/kste_README.md.
- https://csrc.nist.gov/projects/circuit-complexity/list-of-circuits - read (updated 2026-11-05).
- https://raw.githubusercontent.com/usnistgov/Circuits/master/data/slp/aes/aes-mixcols/ README.md and the three .circ.txt files - downloaded (dl/nist_*).
- https://github.com/usnistgov/Circuits/commits/master/data/slp/aes/aes-mixcols - read (commits 2026-09-23 .. 10-02, brandao-git).
- https://github.com/Joe-b-20/aes-mixcolumns-xor-circuits (own repo; used only for the Jean-depth inference) - read.
- http://export.arxiv.org/api/query?search_query=all:MixColumns... - read.

Secondary only (search snippets / aggregator pages): Shi-Feng-Xu ToSC 2023(4) 99@3 (tosc.iacr.org/index.php/ToSC/article/view/11297, blocked; DOAJ 403); Banik-Funabiki-Isobe IEICE 2021 103@3 (IEICE author index); Lin et al. CT-RSA 2021 91@7 and Xiang et al. ToSC 2020 92@6 (PeerJ table); Yuan et al. ToSC 2024 independent 91 (Pandey bibliography); Kranz et al. 2017 97 (ToSC / ePrint 2017/1151, abstract known from lit/REPORT.txt).

Failed: api.semanticscholar.org (429 x3), dblp.org (Anubis), calhoun.nps.edu (JS-only page), sites.google.com/site/davidrcanright (no 2024 paper listed).