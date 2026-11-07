# Inventory of the imported archive `XOR_Unpublished_Proofs_and_Findings_2026-11-07`

Prepared 2026-11-07 from `~/xs-campaigns/2026-11-07-sprint/import/zip/` (WSL). Reading only: no program from the archive was run, nothing in `~/xor-circuit-research` was touched. Helper scripts and raw survey output are in `import/inventory/` (`folders.txt` = file counts and doc lists per folder, `heads.txt` = first lines of each folder's main doc, `sources_by_folder.txt` = SOURCES.csv by folder).

**Reading rule used throughout.** Every statement below is *the archive's own claim*, labelled with the status the archive gives it. `guides/CURRENT_STATUS.md` (owner's table, 2026-11-07) governs interpretation; where an older file says more than that table, the table wins and the difference is listed under Flags. Nothing here was re-verified by me.

**Archive shape.** 270 folders under `research/` (155,204 unique files, ~21.4 GiB), from 594 sources (SOURCES.csv). Identical files are stored once, so a small folder may hold only a manifest while its members sit in a later folder (checked with `manifests/occurrences.jsonl`; e.g. the 71-bound package is stored inside `AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/.../push5/sources/xor/AES_MixColumns_Lower_Bound_75/`, the 85..92 depth-3 packages inside `AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/`, the Nov 3-4 FROZEN / v9 / master / small-map / transfer packages inside `XOR_Adversarial_Audit_2026-11-04/.../audit_work/`, and the Nov 5 Global Ledger / Joined Bounds / Structural Capacity / Constructor Tradeoff / Normalization checkpoints inside `MixColumns_Ordinary_Union_Checkpoint/`). 54 expanded sources therefore have no folder of their own.

---

## 1. Folder table

Topic codes: **ULB** unrestricted lower bound; **D3** depth-3 lower bound; **D4** depth-4; **A87** 87 construction attempts; **S89** 89@4/90@4 structure; **P88** 88 plateau/exit experiments; **INV** inverse MixColumns; **SBOX** S-box bottom; **MAPS** other maps / transfer; **ENG** search engine/learning; **AUD** audits; **VIS** visualizations; **MISC** misc.
Relevance column gives A/B/C/D/E scores 0-3 (A: 87 or proof none exists; B: beating 75; C: why 89@4 is special; D: local search on the 88 level; E: other maps).
The six `g*-d*-<sha256>` record folders are shown with abbreviated hashes. Dates are SOURCES.csv `modified_at` (UTC date). "Status" is the archive's own label; "superseded by X" is my reading of the dated lineage and the guides.

| Folder | Date | Topic | Headline claim (archive's own) | Status (archive) | A/B/C/D/E |
|---|---|---|---|---|---|
| 18_pair_87_checkpoint | 09-09 | A87 | 18 primitive pairs regenerate 84 of an 88's values; only outputs o9,o10,o18 missing; single/two-gate repairs fail | experiment, negative | 1/0/0/1/0 |
| AES_87_Gate_Mold_Discussion_2026-10-21 | 10-21 | A87 | "Empty mold" plan: 87 = 32 outputs + 55 slots filled under proven constraints only | discussion (plan) | 1/0/0/0/0 |
| AES_Alternative_Producer_Pool | 09-26 | A87 | Connected backward grammars / crossover on five 88 controls: no 87 | experiment, negative | 1/0/0/1/0 |
| AES_Authentic_Replay_Artifacts | 10-07 | ENG | 45-run LLM-agent replay of 3 historical checkpoints x 3 arms: 0/5 breakthroughs in every cell | completed, null result | 0/0/0/1/0 |
| AES_Authentic_Replay_Report | 10-07 | ENG/VIS | HTML report of the replay study above | completed | 0/0/0/1/0 |
| AES_Backward_Grammar_Experiment | 09-26 | A87 | One 88@8 candidate from backward output exchange (rest stored in Connected_Grammar) | experiment | 1/0/0/1/0 |
| AES_Causal_Path_Exchange_Continuation | 09-25 | A87 | Integer-path restart / causal path exchange: no circuit below 88, no new bound | negative | 1/0/0/1/0 |
| AES_Checkpoint_Audit_2026_10_10 | 10-10 | ULB | Replays G75 frontier families; frontier 49 profiles/139 keys -> 44/114; "does not raise 75" | audited, incomplete | 0/2/0/0/0 |
| AES_Cluster_Extensions_2026_10_07 | 10-07 | MAPS | Cluster sub-maps 5,6,7 (LB 25, witness 33); 5,6,7,1 (37/49); 5,6,7,0 (29/43) | bounds verified, optima open | 1/1/0/0/1 |
| AES_Cluster_Pairs_Completion_2026_10_07 | 10-07 | MAPS | Cluster pairs 0&1 21-25, 1&2 25-26, 5&6 21-22; clusters 3,4 exactly 16 each, 3&4 29-30 | verified bounds, UNKNOWN = timeout | 1/1/0/0/1 |
| AES_Clusters_0_to_5_71_Gates | 10-08 | MAPS | 71-gate depth-5 circuit for 24 outputs (clusters 0-5), restricted from 88s | verified upper bound | 1/0/0/0/1 |
| AES_Clusters_0_to_5_From_Scratch_72_Gates | 10-08 | MAPS | 72-gate depth-8 circuit for clusters 0-5, from scratch | verified upper bound | 1/0/0/0/1 |
| AES_Clusters_0_to_5_Search_2026_10_08 | 10-08 | MAPS | Search bundle behind the 71; nothing <=70 found | upper bound only | 1/0/0/0/1 |
| AES_Clusters_3_4_2026_10_07 | 10-07 | MAPS | 16-gate circuits for clusters 3 and 4, 30-gate joint circuit | verified | 1/0/0/0/1 |
| AES_Connected_Grammar_Continuation | 09-26 | A87 | Backward output grammar from five 88 controls (depth 5..8): no 87 | negative | 1/0/0/1/0 |
| AES_Counterpart_Replacement_Experiment_2026-10-25 | 10-25 | A87 | Removing one cancellation in 88@5 costs +4/+5 (93/92@5): ancestors serve other outputs | experiment | 1/0/0/1/0 |
| AES_Cross_Output_Search_2026_10_07 | 10-07 | A87 | Rooted-forest output-difference search: 104-110 gates, none <88 | negative | 1/0/0/0/0 |
| AES_DEPTH3_BOUND86_WEIGHT7_EXACT48 | 10-16 | D3 | 86 <= D3; W7 cluster 16, clusters 3&4 32, twelve W7 outputs 48 | superseded by BOUND89..93 | 0/0/0/0/0 |
| AES_DEPTH3_BOUND89_CONSTRUCTION_PROOF | 10-16 | D3 | 89 <= D3; projection lemma; W5 cluster 12 | superseded by BOUND90..93 | 0/0/0/0/0 |
| AES_DEPTH3_BOUND90_PAIR25_PROOF | 10-16 | D3 | 90 <= D3; normalized pair count P >= 25 | superseded by BOUND92/93 | 0/0/0/0/0 |
| AES_DEPTH3_BOUND92_PAIR26_EXACT | 10-17 | D3 | 92 <= D3; minimum P exactly 26 (26-pair circuit uses 100 gates) | superseded by LB93 | 0/0/0/0/0 |
| AES_DEPTH3_PAIR_TRADEOFF_PROOF_2026-10-17 | 10-17 | D3 | PAIR25/PAIR26 proofs (P>=25, P>=26) | absorbed in LB93 | 0/0/0/0/0 |
| AES_DEPTH3_RECIPE_LINKED_PROOF_2026-10-16 | 10-17 | D3 | Manifest: linked certificate 92 <= D3 <= 97 PASS (members stored in PUSH9) | superseded by LB93 | 0/0/0/0/0 |
| AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23 | 10-23 | D4/ULB | 75 <= D4 <= 89; >=12 direct pairs in pair normal form; N >= max(0,65-3p); also holds EXACT_MASK_SHARING_PUSH6 (301 partial exclusions at 75, 509 surviving aggregate profiles) and the full 63->75 source chain | incomplete (no 76, no 87=>depth5) | 1/2/1/0/0 |
| AES_DEPTH4_RECURSIVE_ACCOUNTING_PUSH2_2026-10-23 | 10-23 | D4 | N+4p+P_odd+F_inputs >= 81; N+4p+kappa >= 81 (audited); q=0 slice of 241/451 tuples excluded at G=75 | partly audited, incomplete | 1/2/1/0/0 |
| AES_Deep_Repair_75_76_Profiles_2026_10_02 | 10-02 | A87 | 75/76-gate partial circuits with 27 exact outputs; no <=87 full circuit | heuristic | 1/0/0/1/0 |
| AES_Depth3_Checkpoint35_Addendum | 10-29 | D3 | Three-pair star theorem Y >= 3 under cp34 reduced-C1 contract | scoped/conditional; 93-97 unchanged | 0/0/0/0/0 |
| AES_Depth3_Checkpoint44 | 10-31 | D3 | Checkpoints 36-44: role/family closures at union allowance 68; exact h=61 master point | incomplete; superseded by Nov 3-5 work | 0/0/0/0/0 |
| AES_Depth3_Checkpoint44_Recovery_25 | 10-31 | D3 | Recovery checkpoint after outage; five residual systems (32,211 free vars) open | incomplete ("not a complete certificate archive") | 0/0/0/0/0 |
| AES_Depth3_Checkpoint44_Unrestricted | 10-31 | D3 | (Depth-3 despite the name.) All 19 strong image systems still give helper objective 61 (rational point) | exact barrier; incomplete | 0/1/0/0/0 |
| AES_Depth3_Proof_Program_2026-10-27 | 10-29 | D3 | Checkpoints 33/34 proof program; 93-97 | incomplete; superseded by cp35-44 | 0/0/0/0/0 |
| AES_Depth5_Pool205_Continuation | 09-27 | A87 | No 87@<=5 using only the 205 masks of three 88 controls (HiGHS infeasible); also 169-value pool | solver-status, vocabulary-conditional | 2/0/0/1/0 |
| AES_Family_Sharing_Check_2026_10_10 | 10-10 | ULB | Family-limited sharing examples on two 88s; no bound | descriptive | 0/1/0/1/0 |
| AES_Fixed_71_Completion_17_Gates | 10-08 | A87 | Fixed 71-gate prefix + 17 = 88 | verified (88) | 1/0/0/1/0 |
| AES_Fixed_Budget_Reconstruction_60_76_2026_10_02 | 10-02 | A87 | 7,978 input-only rebuilds at caps 60-76; best full circuit 88 | negative | 1/0/0/1/0 |
| AES_Four_Exterior_and_Value_Compatibility | 09-24 | A87 | Family with live root x7^x23 and <=4 quotient values outside the 114-value pool: optimum exactly 88; any <=87 with that root needs >=5 outside values | audited, family-scoped | 2/1/0/1/0 |
| AES_From_Scratch_and_71_Completion_2026_10_08 | 10-08 | MAPS | From scratch clusters 0-5: 72; fixed-71 completion: 71+17 = 88 (<=15 extra not found) | verified upper bounds | 1/0/0/1/1 |
| AES_Full_Neighborhood_Checkpoint_2026_10_09 | 10-09 | ULB | G75 phase-family exclusions (Farkas leaves) aiming at 76; 12.6 GB | incomplete; "75 is a review draft" | 0/2/0/0/0 |
| AES_GLOBAL_STRUCTURAL_ARCHIVE_VERIFICATION_PUSH8_2026-10-20 | 10-20 | D3/AUD | Receipt: universal parent bound 25; exact optimum 108 at 25 parents | PASS receipt | 0/0/0/0/0 |
| AES_Gate_By_Gate_Ladder_2026_10_02 | 10-02 | A87 | Two literal 59->88 ladders (recovery of 88 with hints); no 87 | negative | 1/0/0/1/0 |
| AES_Gate_XOR_Results | 09-29 | MISC | XOR of all gates over 295 lists; 200 88-gate lists give 91 sums; A^H = sum of inputs | descriptive | 0/0/0/1/0 |
| AES_Global_Proof_Pricing_Snapshots | 10-26 | D3 | Raw column-generation pricing data (global97) | data | 0/0/0/0/0 |
| AES_Global_Proof_Research_Checkpoint | 10-26 | D3 | global97 parent/helper tradeoff; common-bank threshold theorem; "target not met" | incomplete | 0/0/0/0/0 |
| AES_HEAVY_HELPER_PREPARATION | 10-15 | ULB | Heavy helpers need forced companions / first-birth preparation | proved deduction, no new bound | 1/1/0/0/0 |
| AES_Helper_Set_Comparison_2026_10_10 | 10-10 | P88 | 260 audited 88s: 256 distinct helper sets, 2 common helpers (00808000, 20002000), union 265 | descriptive | 1/0/0/2/0 |
| AES_Helper_Sharing_Checkpoint_2026_10_08 | 10-08 | ULB | Hash manifest only (members in Full_Neighborhood) | n/a | 0/1/0/0/0 |
| AES_Historical_Intervention_Replay_2026_10_06 | 10-06 | ENG | 21 replay runs: no intervention effect; includes demand-flow / bi-mask findings | null result | 0/0/0/1/0 |
| AES_Incomplete_Gate_Arrays_2026_10_07 | 10-07 | A87 | Exported 75/76 partial prefixes; retaining them needs exactly 88 | descriptive | 1/0/0/1/0 |
| AES_Joint_Accounting_Case_Bounds_2026_10_12 | 10-12 | ULB/A87 | Manifest only (CLASS_87.json etc. stored in Multi_Helper folder) | n/a | 1/1/0/0/0 |
| AES_Larger_Cluster_Maps_2026_10_07 | 10-07 | MAPS | 5,6,7,0,1: 34-55; 2,3,4: 33-41; 5..2: 45-65 | bounds, optima open | 1/0/0/0/1 |
| AES_MixColumns_Checked_Continuation | 09-23 | ULB | q=5 => z>=k00+1, so q+z>=6; byte programs with <=3 scalar mults need exactly 96 | audited, scoped | 0/1/0/0/0 |
| AES_MixColumns_Continuation_92_Restricted | 09-22 | ULB/A87 | If every odd signal is an input or output (h=0): >= 92; bracket then 63-88 | computer-assisted, two implementations | 2/1/0/0/0 |
| AES_MixColumns_Depth3_Lower_Bound_93 | 10-23 | D3 | PDF of the 93 proof | audited (Nov 4 full replay) | 1/0/0/0/0 |
| AES_MixColumns_Lower_Bound_71 | 09-22 | ULB | Hash manifest only (71 chain stored under DEPTH4 attempt) | superseded by 75 | 0/1/0/0/0 |
| AES_MixColumns_Proof_Progress_2026-10-24 | 10-24 | ULB/D3 | 427 local + 166 oriented 75-gate profile exclusions; depth-3 conditional endpoint L=26,P=47,G=105 | incomplete; bounds stay 75/93 | 0/2/0/0/0 |
| AES_MixColumns_Unrestricted_Lower_Bound_75 | 10-23 | ULB | PDF of the 75 proof | audited (Nov 4 replay) | 1/3/0/0/0 |
| AES_MixColumns_structural_proof_work_2026-11-03 | 11-03 | D3 | human97 simplification branch; "not yet a short standalone proof" | historical candidate, open | 0/0/0/0/0 |
| AES_MixColumns_structural_proof_work_v6_2026-11-03 | 11-04 | D3 | human97_v2: G = 64+L+mu-q; L+mu-q >= 33 open | historical candidate, open | 0/0/0/0/1 |
| AES_Multi_Helper_Proof_Continuation_2026_10_12 | 10-12 | ULB/A87 | Exactly two odd non-output helpers => >= 88; any <=87 needs 3..31 odd helpers | computer-assisted, independent AUDIT.json | 3/2/0/0/0 |
| AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20 | 10-20 | D3/ULB | 93 <= D3 <= 97 (Oct 17) + recipe-293 branch excluded; PUSH7 structural lemmas; unrestricted handoff (250-fact ledger); two-foreign exclusion; <=1 outside value => >=84; claim G<=87 => h>=3 (proof dir missing) | 93 audited; rest incomplete | 2/2/1/0/0 |
| AES_Optimal_Cluster_Helper_Sharing_2026_10_07 | 10-07 | MAPS | Fixed 76-helper-bin question: max saving 10, min union 98 | exact within its restriction | 1/1/0/0/1 |
| AES_Output_Distance_Accounting_2026_10_10 | 10-10 | ULB | Exact local accounting of output distances; no bound | descriptive | 0/1/0/1/0 |
| AES_Overlapping_Group_Accounting_2026_10_10 | 10-10 | ULB | Overlap ledger of one 88 control, 255 group views | descriptive | 0/1/0/1/0 |
| AES_PUSH9_RELEASE_INTEGRITY | 10-20 | AUD | Archive integrity receipt | PASS | 0/0/0/0/0 |
| AES_Proof_Recovery_Supplement_2026-10-27_v6 | 10-27 | D3 | Recomputed four-output source minima, native-bank tables, envelope theorems | "does not claim a 97 proof" | 0/0/0/0/0 |
| AES_RECURSIVE_CONSTRUCTOR_PUSH2_2026-10-22 | 10-22 | ULB | Receipt only: conditional 82 for canonical incidences (members in PUSH4) | superseded by PUSH4 | 0/1/0/0/0 |
| AES_RECURSIVE_CONSTRUCTOR_PUSH4_2026-10-22 | 10-22 | ULB | Fixed first-birth output-parent incidence theorems: conditional 82-84 gates; no global bound | scoped proofs | 1/1/0/1/0 |
| AES_Research_Fleet_Checkpoint_2026_10_06 | 10-06 | ULB | U <= 3x'+2q+F-e'-64; low-weight boundary dependencies span 29 < 32; construction lane best 96 | audited, scoped | 0/2/0/0/0 |
| AES_Residual_Inference_2026_10_02 | 10-02 | A87 | Residual-aware inference engine: no <=87; contains `reference/bound_76_status.md` (76 claim) | negative; 76 unaudited | 1/1/0/1/0 |
| AES_STRUCTURAL_ARCHIVE_VERIFICATION_2026-10-20 | 10-20 | AUD | Archive integrity receipt | PASS | 0/0/0/0/0 |
| AES_Scale2_Optimal_26_Proof | 09-29 | MAPS | Scale-2 sub-map: 26 gates optimal (solver-free proof) | proof (archive) | 0/0/0/0/2 |
| AES_Scale3_43_to_46_Handoff | 09-29 | MAPS | Scale-3 sub-map 43-46 | open | 0/0/0/0/2 |
| AES_Scale3_Cancellation_Campaign | 09-29 | MAPS | Scale 3: 43-46; lift16 (a,b,a,b): 26-XOR upper bound | open | 0/0/0/0/2 |
| AES_Scale3_Continuation_10_Partitions | 09-29 | MAPS | Ten-part decompositions excluded; still 43-46 | open | 0/0/0/0/2 |
| AES_Sharing_Patterns_and_Optimal_Variants | 09-29 | MAPS | Scale 1: unique 9-gate circuit; scale 2: exactly 12 cancellation-free optimal 26-gate helper sets | MILP-complete (archive) | 0/0/0/1/2 |
| AES_Three_Helper_Obstruction_2026_10_02 | 10-02 | ULB | Manifest only (members in Research_Fleet) | n/a | 0/1/0/0/0 |
| AES_Unrestricted_Weight_Parity_2026_10_12 | 10-12 | ULB | Weight refinements of two 75-proof inequalities; no new bound | proved refinements | 0/1/0/0/0 |
| AES_Value_Pool_169_Continuation | 09-27 | A87 | No 87 within the 166/168-value pools (MILP infeasible) | solver-status, pool-conditional | 2/0/0/1/0 |
| AES_Weight_Parity_Joint_Accounting_2026_10_12 | 10-12 | ULB/A87 | New necessary conditions; two solver "87 points" rejected as non-circuits | no new bound | 1/1/0/0/0 |
| AES_XOR_Atlas_Interactive | 10-13 | VIS | Interactive atlas of the 184 input/output occurrences | tool | 0/0/0/0/0 |
| AES_depth3_exact_search | 10-16 | D3 | 85 <= D3 (parity P>=24) | superseded by BOUND86+ | 0/0/0/0/0 |
| AUDIT(1) | 10-10 | AUD/P88 | 260 88-gate circuits: all 56 helpers, 256 distinct value sets, union 297, output reuse 2-8 | audit PASS | 1/0/0/2/0 |
| AUDIT(2) | 10-12 | AUD | Multi-helper premises: 33,420 two-helper cases reconciled | audit PASS | 1/1/0/0/0 |
| AUDIT_NOTE | 10-10 | AUD | Fresh verifier for Full_Neighborhood circuits | audit | 0/0/0/1/0 |
| Barrier Tree | 11-06 | P88 | mc24 exit search on plateau B11 (8,019 circuits): 2,605/2,605 +1 classes descended, 0 improve, 1,687 unresolved; +2 band 0 descended | empirical, explicitly incomplete | 2/0/0/3/0 |
| CHECKPOINT_PROOF_EXCERPT | 10-10 | ULB | Excerpt: full-centred cliques have star rank <= 3 | excerpt of review draft | 0/1/0/0/0 |
| Circuit_Lower_Bound_Discovery_RECOVERED | 09-23 | AUD | Recovery manifest + verifier for Exact96, Frontier, LB75 zips | integrity only | 0/1/0/0/0 |
| Circuit_Lower_Bound_Discovery_RECOVERY | 09-23 | AUD | Recovery README; "last unfinished work was not fully recovered" | integrity only | 0/1/0/0/0 |
| Circular Byte Projection and Output Paths | 08-20 | VIS | PNG of circular byte projection | picture | 0/0/0/0/0 |
| FINAL_AUDIT | 10-12 | AUD | Weight-3 finite premises for M and M^T | audit PASS | 0/1/0/0/0 |
| FULL_AUDIT | 10-10 | AUD | Geometry/accounting checks (output distance); no bound | audit | 0/1/0/0/0 |
| HANDOFF(3) | 10-09 | ENG | SK Lab v0.6: neural proposer pilot vs 88: zero wins | completed, null | 0/0/0/1/0 |
| HANDOFF(4) | 10-12 | ENG | SK Lab v0.7: policy trained from scratch; no AES win | completed, null | 0/0/0/1/0 |
| INDEPENDENT_AUDIT(1) | 10-12 | AUD | Multi-helper finite premises rechecked | audit PASS | 1/1/0/0/0 |
| L28_recursive_progress_2026-10-24 | 10-24 | D3 | L=28, P<=36 signature closures, 0 survivors in listed signatures | incomplete | 0/0/0/0/0 |
| L28_recursive_progress_pass2_2026-10-24 | 10-24 | D3 | More L=28 signatures closed | incomplete | 0/0/0/0/0 |
| L28_signature_engine_profile_cluster_prune | 10-24 | D3 | C++ engine (cutoff = INCOMPLETE) | code | 0/0/0/0/0 |
| LATEST_RUN_REPORT | 09-22 | ENG | Collapse v0.10 autonomous segment report (aes87 domain) | completed, no 87 | 0/0/0/1/0 |
| LATEST_RUN_REPORT(1) | 09-22 | ENG | Same, next segment | completed | 0/0/0/1/0 |
| LATEST_RUN_REPORT(2) | 09-22 | ENG | Same, "aes-autonomous-research-001" | completed | 0/0/0/1/0 |
| LATEST_RUN_REPORT(3) | 09-23 | ENG | Same, diagnosis pipeline validation | completed | 0/0/0/1/0 |
| LEARN_REPORT | 10-12 | ENG | v0.7 learner vs pretrained models vs cheap search | completed, null on AES | 0/0/0/1/0 |
| MixColumns_Ordinary_Union_Checkpoint | 11-05 | D3 | Latest depth-3: two-group union bound; H0=16 => >=2 original CC; one r4 pattern left; boundary floor 49 FALSE (124@3 counterexample); fixed-parent minima 97/107 | local results audited; 97 open | 1/0/0/0/1 |
| MixColumns_Proof_Diagnosis | 11-05 | D3 | Complete finite depth-3 model; strengthened LP has exact point 81.204 (cannot exceed 82) | diagnosis; 97 open | 1/1/0/0/1 |
| NEW_SIGNATURE_RANGE_VERIFICATION | 10-24 | D3 | Range-split replay receipt for signature 18_6 | PASS receipt | 0/0/0/0/0 |
| NIST_MixColumns_provenance_audit_2026-10-20 | 10-20 | MISC | NIST 88@5 shares 48/56 helpers with Joe's Jean-derived 88 after byte rotation; no causal claim | assessment | 0/0/0/1/0 |
| OVERLAP_RESULTS | 10-10 | AUD | Overlap accounting of one 88 control | descriptive | 0/1/0/1/0 |
| PAID_FIXED_2_CERTIFICATE | 10-12 | ULB | Rational multipliers for the h=2 paid-connector case | certificate | 1/1/0/0/0 |
| PROOF__b23b37f694cd | 10-12 | ULB | Joint weight/parity/preparation accounting PROOF.md | no new bound | 1/1/0/0/0 |
| PUSH6_ARCHIVE_VERIFICATION_2026-10-19 | 10-19 | AUD | Archive integrity receipt | PASS | 0/0/0/0/0 |
| Pasted markdown | 08-21 | VIS | Circle picture: 32 outputs = 5 shapes under point rotations | observation | 0/0/0/1/0 |
| Pasted markdown(20260812-133059) | 08-12 | A87 | ATTEMPTS_SINCE_PUSH catalog Jul 30-Aug 12: nothing <=87; 13 "theorem-grade" negatives incl. D3 >= 80; calibrated P(87/descent) < 2e-3 | catalog; logs not all recovered | 3/1/0/3/0 |
| Pasted markdown(20260919-155158) | 09-19 | ENG | Repo survey: 520-record corpus sample, ~1.8M untracked campaign circuits | notes | 0/0/0/1/0 |
| Pasted markdown(20260920-150502) | 09-20 | A87 | Keep-set covering leaves six pairs in {7,15,23,31}; prices a "57" bound | notes, unknown | 1/0/0/0/0 |
| Pasted markdown(20260921-121623) | 09-21 | ENG | Collapse diagnosed missing capability (counterexample sweep) | notes | 0/0/0/0/0 |
| Pasted markdown(20260921-155206) | 09-21 | ENG | Collapse status: 88 vs "L(M) >= 56" | superseded (63..75 by 09-22) | 0/0/0/0/0 |
| Pasted markdown(20260921-161406) | 09-21 | ENG | Same status, pilot data | superseded | 0/0/0/0/0 |
| Pasted markdown(20260921-182057) | 09-21 | ENG | Same status | superseded | 0/0/0/0/0 |
| Pasted markdown(20260921-202925) | 09-21 | ENG | Same status | superseded | 0/0/0/0/0 |
| Pasted markdown(20260922-001043) | 09-22 | ENG | Collapse experimental lane design, 899 tests | engineering | 0/0/0/0/0 |
| Pasted markdown(20260922-133618) | 09-22 | ENG | Collapse slot-cap bug root cause | engineering | 0/0/0/0/0 |
| Pasted markdown(20260922-194600) | 09-22 | ENG | Collapse test suite green | engineering | 0/0/0/0/0 |
| Pasted text | 10-06 | MISC | Research prompt: unrestricted XOR-SLP statement for 87/88 | prompt (data) | 0/0/0/0/0 |
| Pasted text(1) | 10-14 | MISC | Prompt: prove or refute 87-gate global sharing | prompt (data) | 0/0/0/0/0 |
| Pasted text(20260921-155804) | 09-21 | ENG | Collapse `actions --help` dump | log | 0/0/0/0/0 |
| Pasted text(20260921-160539) | 09-21 | ENG | Collapse action manifests dump | log | 0/0/0/0/0 |
| Pasted text(20260921-161755) | 09-21 | ENG | Process listing during Collapse pilot | log | 0/0/0/0/0 |
| Pasted text(8) | 06-15 | ENG | Build log of a GF(2) XOR-SLP domain pack (earlier engine) | log | 0/0/0/0/0 |
| Pasted text(9) | 06-15 | ENG/MAPS | Plan: self-prove a small bit-replicated cipher matrix to check citations | plan | 0/0/0/0/1 |
| README(4) | 10-30 | ENG | `xorsearch` README (search folder) | docs | 0/0/0/1/0 |
| README_NEAR26 | 08-15 | A87 | Only n16 of 18 near-miss 26-mask states recoverable | missing data recorded | 1/0/0/1/0 |
| README_TRAJECTORY_STATUS | 08-15 | ENG | Bi-mask metric provenance; routing-LNS 97 witness and per-gate CSV missing | missing data recorded | 0/0/0/1/0 |
| RECORD_89(1) | 07-08 | MISC | 89-gate unrestricted circuit (depth 10; NOT 89@4) | verified (report) | 1/0/0/1/0 |
| RECORD_89_BOUND | 07-08 | MISC | Same 89 in xorslp schema | verified | 1/0/0/1/0 |
| RECORD_89_vs_90_structural_report | 07-08 | MISC | 89 vs prior 90: share 80 internal forms; 33 cancellation gates | verified report | 1/0/0/1/0 |
| RECORD_98_depth3 | 07-08 | D3 | 98@3 circuit | verified | 0/0/0/0/0 |
| RECORD_98_depth3_verification_report | 07-08 | D3 | 98@3 report; depth 3 minimal since weights 5/7 > 4 | verified | 0/0/0/0/0 |
| SHA256SUMS | 08-15 | AUD | Checksums of an August bundle | n/a | 0/0/0/0/0 |
| STATUS_87_DEPTH_ATTACK | 08-14 | A87 | Exact Z3 QF_BV 87@<=4 and 87@<=5: UNKNOWN; vocab-restricted optima 97/96/93@<=5 | UNKNOWN (no UNSAT) | 2/0/0/0/0 |
| STATUS_87_DEPTH_ATTACK(1) | 08-14 | A87/D3 | Same + depth-3 tradeoff P<=26 => E>=30 | UNKNOWN / solver-closed | 2/0/0/0/0 |
| XORProof_Lab_2026-11-04 | 11-04 | MAPS/AUD | Generic map program; corrected theorems; reproduces S-box 28 and 16 group optima | corrected, scoped | 1/1/0/0/3 |
| XORSLP_PILOT_REPORT | 10-09 | ENG | 7B local model pilot vs 88: zero wins | completed, null | 0/0/0/1/0 |
| XOR_Adversarial_Audit_2026-11-04 | 11-04 | AUD | Audit: constructions verified; 75/93 replay OK; v9 lemmas false; 97 not recertified; inverse LP = 32 | audit (governs) | 2/2/0/0/2 |
| XOR_Atlas_Proof_Workbench | 10-23 | VIS | Proof workbench page (75 proved, 88 known) | tool | 0/0/0/0/0 |
| XOR_FOREST_CHECKPOINT_2026-10-13 | 10-13 | ULB | Output-parent forest identity G = 64+c-b+p; 88 <=> c-b+p >= 24 (open) | identity proved; bound open | 1/2/0/1/0 |
| XOR_Mold_Solver_2026-10-23 | 10-24 | ENG | Z3 "mold" constructor; blank 96@3 and 87@5 UNKNOWN | tool, validated small | 1/0/0/0/0 |
| XOR_Mold_Solver_2026-10-24 | 10-24 | ENG | Same tool, docs release | supersedes 10-23 | 1/0/0/0/0 |
| aes88_rotation_coordinate_audit | 08-20 | VIS/P88 | One 88: 30 point-rotation archetypes of gate shapes, 5 output archetypes | descriptive | 0/0/0/1/0 |
| aes_88_xor_circle_viewer | 08-20 | VIS | Circle viewer of from-scratch 88@5 | tool | 0/0/0/0/0 |
| aes_cpu_control_2026-10-21 | 10-21 | ENG | CPU-affinity helper for 20-worker run | tool | 0/0/0/0/0 |
| aes_long20_audit_and_own90_2026-10-21 | 10-21 | S89 | 12 h 20-worker run: own-lineage 90@4 found by worker 14 from 91 seed, adopted by 2 | verified audit | 0/0/2/2/0 |
| aes_mixcolumns_87_depth_attack | 08-14 | A87 | SMT-LIB 87@4/87@5 instances + Z3 scripts | UNKNOWN | 1/0/0/0/0 |
| aes_mixcolumns_88_cluster_chain_workbench | 08-26 | VIS | Cluster-chain view of an 88@5 (14,11,10,15,11,10,10,7) | tool | 0/0/0/1/0 |
| aes_mixcolumns_90_bound | 07-08 | MISC | Prior 90-gate unrestricted circuit | verified | 0/0/0/0/0 |
| aes_mixcolumns_completion_90 | 10-08 | MISC | 90-XOR SLP (76+14 completion) | verified by script | 0/0/0/0/0 |
| aes_mixcolumns_family_cluster_workbench | 08-18 | VIS | Family/cluster workbench | tool | 0/0/0/0/0 |
| aes_mixcolumns_simple_workbench | 08-18 | VIS | Manual XOR workbench | tool | 0/0/0/0/0 |
| aes_reduction_star_26xor | 08-21 | MISC | 26-XOR "reduction-star" sub-circuit (bit-7 hub + co-feeds) | construction | 1/0/0/0/0 |
| aes_search_rediscovery_results_2026-10-20 | 10-21 | ENG | 300 s rediscovery: 0/14 target hits; depth-3 annealer hits 97@3 in 15-51 s | benchmark | 0/0/1/2/0 |
| aes_search_v2_2026-10-20 | 10-20 | ENG | Hash list only (code in v3 / public) | n/a | 0/0/0/1/0 |
| aes_search_v3_2026-10-22 | 10-22 | ENG | Search v3 (proof-guided moves); frontier 97@3, own 89@4, 88@5; no 96@3/88@4/87 | validated, negative | 1/0/1/2/0 |
| alien_search | 08-29 | A87 | MILP "alien" search script over 88 unions | code | 1/0/0/1/0 |
| analyze_gate78_all | 08-28 | P88 | C++ analysis of gate 78 in a fixed 88 | code | 0/0/0/1/0 |
| assemble_signature_chunked | 10-24 | D3 | C++ cover assembly (cutoff = INCOMPLETE) | code | 0/0/0/0/0 |
| audit_native87 | 08-15 | A87 | Native map: p^4=0; 1,857 local states; p-adic seed 105@6 | audit PASS | 1/0/0/0/0 |
| backbone_bypasses_19 | 08-15 | P88 | 19 "gainful" two-gate bypasses of backbone masks | data | 1/0/0/2/0 |
| backbone_defect_bundle | 08-15 | P88 | 22-mask core states, triple-backbone index | data | 1/0/0/2/0 |
| backbone_defect_checksums | 08-15 | P88 | Checksums | n/a | 0/0/0/0/0 |
| bi_mask_requested_evidence | 08-15 | P88/A87 | 22-mask backbone + 5 repair coordinates => 3^5 = 243 optimal 27-mask modules in a frozen 61-mask exterior (26 would give 87) | exterior-conditional | 2/0/0/3/0 |
| c96_descent_1203 | 09-10 | ENG | 95-gate descent state | data | 0/0/0/1/0 |
| checkpoint | 10-21 | ENG | long20 run archive snapshot (e.g. 92@4) | data | 0/0/1/1/0 |
| checkpoint(1) | 10-21 | ENG | Same, other worker | data | 0/0/1/1/0 |
| circuit | 07-08 | MISC | 90-gate circuit JSON | verified | 0/0/0/0/0 |
| circuit-space-views | 11-05 | VIS/P88/S89 | Plateaus are exact products: 88@5 3^7=2,187; 89@4 3^4=81 holds all 81 known; Inv 118@5 200; partial barrier trees | facts-only figures | 1/0/3/3/1 |
| cold88_proto | 09-10 | ENG | Cold-start 88 prototype engine | code | 0/0/0/1/0 |
| cold97_generated_from_scratch | 09-10 | ENG | 97-gate state from scratch | data | 0/0/0/1/0 |
| collapse_framework_v0_1 | 09-19 | ENG | Collapse v0.1 framework (aes87 domain) | code | 0/0/0/1/0 |
| cone_surgery_iter | 09-10 | ENG | Cone-surgery iteration script | code | 0/0/0/1/0 |
| cpu_control | 10-21 | ENG | CPU control script | code | 0/0/0/0/0 |
| cycle_cut_strong | 08-29 | A87 | MILP cycle cuts (deps missing) | code | 1/0/0/0/0 |
| cycle_cut_triangles | 08-29 | A87 | Same, triangle cuts (deps missing) | code | 1/0/0/0/0 |
| defect_rank3_dynamic | 08-28 | P88 | Rank-3 defect search on a fixed 88 | code | 0/0/0/1/0 |
| defect_vocabulary_36 | 08-15 | P88 | 36-mask defect vocabulary | data | 0/0/0/1/0 |
| depth3_p26_tradeoff | 08-14 | D3 | P<=26 => E>=30 (solver-closed); certified D3 >= 80 | not certificate-grade; superseded | 0/0/0/0/0 |
| depth_optimal_129 | 07-08 | D3 | 129@3, "depth-optimal" (depth only) | verified | 0/0/0/0/0 |
| depth_optimal_129_BOUND | 07-08 | D3 | Same in schema | verified | 0/0/0/0/0 |
| depth_optimal_129_report | 07-08 | D3 | Report: depth 3 minimal | verified | 0/0/0/0/0 |
| direct_88_formula_metamorphosis_report | 09-10 | P88 | Neutral reshapes move 5/6 88 species at equal gates; 2-deletion + 1-repair exhaustive on 3 states: no 87 | exhaustive within move | 2/0/0/3/0 |
| dump_gate78 | 08-28 | P88 | Dump of gate 78 analysis | code | 0/0/0/1/0 |
| ecosystem_88_w9_w11 | 09-10 | P88 | 88 with weight-9/11 helpers | data | 0/0/0/1/0 |
| ernbp95_dump | 08-29 | ENG | 95-gate output of ernbp_mix | data | 0/0/0/1/0 |
| ernbp_mix | 08-29 | ENG | C++ heuristic | code | 0/0/0/1/0 |
| exact_k2_88 | 09-10 | A87 | Delete 2 values from an 88, test <=86 completion | code | 1/0/0/1/0 |
| experiment1_236_pairs_108 | 09-09 | A87 | Inside-output pair vocabulary: 108 gates | construction | 0/0/0/0/0 |
| experiment2_260_pairs_143 | 09-09 | A87 | Outside pairs only: 143 | construction | 0/0/0/0/0 |
| experiment2_260_pairs_strict_187 | 09-09 | A87 | Strict outside pairs: 187 | construction | 0/0/0/0/0 |
| foundation_productivity | 09-10 | ENG | Foundation productivity metrics script | code | 0/0/0/1/0 |
| full_union_alien1 | 08-29 | A87 | MILP over union of 88s (deps missing) | code | 1/0/0/0/0 |
| g128-d7-0a2c...cfe9 | 10-27 | MAPS | fox_mu4 128@7 record | record | 0/0/0/0/1 |
| g129-d6-00a8...6f58 | 10-27 | MAPS | fox_mu4 129@6 record | record | 0/0/0/0/1 |
| g129-d7-0a49...34ed | 10-27 | MAPS | fox_mu4 129@7 record | record | 0/0/0/0/1 |
| g28-d5-0a39...264b | 10-27 | SBOX | S-box bottom 28@5 record | record | 0/0/0/0/2 |
| g29-d4-1cf0...8a9f | 10-27 | SBOX | S-box bottom 29@4 record | record | 0/0/0/0/2 |
| g29-d4-...rng-start | 10-27 | SBOX | RNG start state of the 29@4 chunk | data | 0/0/0/0/1 |
| global97_joint_commitment_audit_2026-10-27 | 10-27 | D3 | 32 seven-bit interfaces, 312,500 patterns checked; no exclusion | audit | 0/0/0/0/0 |
| global97_state01_recovered_proof_2026-10-27 | 10-27 | D3 | Shared triple-value bank pricing theorem; "no 97 bound asserted" | relaxation | 0/0/0/0/0 |
| hub87_abstract | 09-11 | A87 | Abstract 57-node hub graph with "physical_required": 87 | unknown; not a circuit | 1/0/0/0/0 |
| human_proof_draft | 11-04 | D3 | Draft short 97 proof ("not yet obtained") | historical candidate, open | 0/0/0/0/0 |
| human_theorem_v1 | 11-04 | D3 | "Modular human proof ... needs 97", conditional on six lemmas | historical candidate, open | 0/0/0/0/0 |
| lemma_beam | 08-29 | A87 | Beam search over lemmas (needs missing lemma_data.hpp) | code, incomplete | 1/0/0/1/0 |
| lineage_cold | 09-10 | ENG | Lineage cold-start engine | code | 0/0/0/1/0 |
| lineage_descent_1102 | 09-10 | ENG | 96-gate state | data | 0/0/0/1/0 |
| lineage_opt | 09-10 | ENG | Lineage optimizer | code | 0/0/0/1/0 |
| lineage_walk | 09-10 | ENG | Lineage walk | code | 0/0/0/1/0 |
| macro_formula_jump88 | 09-10 | P88 | Macro formula jumps on 88 | code | 0/0/0/2/0 |
| metamorphose88 | 09-10 | P88 | Neutral metamorphosis on 88 | code | 0/0/0/2/0 |
| min_private | 09-10 | ENG | Minimize private helpers | code | 0/0/0/1/0 |
| min_private95_triplereshape | 09-10 | ENG | 95-gate state | data | 0/0/0/1/0 |
| minpriv_descent_7001 | 09-10 | ENG | 95-gate state | data | 0/0/0/1/0 |
| mixcolumns-g89-d4-1b2a9fcbb250 | 10-27 | S89 | 89@4 record | record | 0/0/2/1/0 |
| mixcolumns-g97-d3-0b4035d99a8d | 10-27 | D3 | 97@3 record | record | 0/0/0/0/0 |
| mixcolumns_88_19_primitive_pairs | 09-09 | P88 | 88 with only 19 primitive pairs (weights 19/12/12/25/7/13) | verified | 1/0/0/1/0 |
| mixcolumns_88_examples(1) | 09-11 | P88 | Six 88s, one per weight profile, with corpus counts (e.g. 13,363 share 16/11/15/8/4/2) | data | 0/0/0/2/0 |
| mixcolumns_90gates_depth4_own_2026-10-21 | 10-21 | S89 | Own-lineage 90@4 witness | verified | 0/0/2/1/0 |
| mixcolumns_pair_experiments | 09-09 | A87 | Pair vocabulary experiments | code | 0/0/0/0/0 |
| mold87 | 09-11 | A87 | 87-mold vocabulary with one forced common anchor (restricted class) | code | 1/0/0/0/0 |
| native87_motif_service_bundle | 08-16 | A87 | Native motif catalogue; tail T4567 = 33 in restricted class; Q-service prices 33..37 | restricted class | 1/0/0/0/1 |
| native87_representation_bundle | 08-15 | A87 | Native form f(alpha,p) = 1+alpha*p+p^3, p^4 = 0 | representation | 1/0/0/0/1 |
| native_element_factor_search | 08-15 | A87 | No three-linear factorization; best sparse 2-factor CSE 108 | negative | 0/0/0/0/0 |
| native_local_states | 08-15 | A87 | 1,857 local corner states | data | 0/0/0/0/0 |
| native_python_104_circuit | 09-09 | A87 | 104-gate deterministic heuristic | construction | 0/0/0/0/0 |
| native_python_99_circuit | 09-09 | A87 | 99-gate pair/cancellation graph circuit | construction | 0/0/0/0/0 |
| native_python_99_verify | 09-09 | A87 | Verifier for 99 | code | 0/0/0/0/0 |
| native_service_states_256 | 08-15 | A87 | 256 service-mask states with min costs | data | 0/0/0/0/0 |
| neutral2_best | 09-10 | ENG | 95-gate state | data | 0/0/0/1/0 |
| offer | 10-21 | S89 | long20 offer record (90@4 from worker 01) | data | 0/0/1/0/0 |
| outsider1_exact | 08-29 | A87 | Exact one-outsider search (needs missing header) | code, incomplete | 1/0/0/1/0 |
| padic_triangular_seed | 08-15 | A87 | 105-gate p-adic triangular seed | construction | 0/0/0/0/0 |
| pair_motif_crossK_frontier | 08-16 | A87 | 1,897 Pareto profiles K=4..7 | data | 0/0/0/0/0 |
| pair_triple_catalog_report | 09-09 | MISC | 496 pairs (236 inside outputs), 4,960 triples (536 inside; 84 in two outputs) | computed counts | 1/1/0/0/0 |
| pre_email_review_bundle | 10-01 | AUD | Pre-email review of the 75 repos: run_all.sh masks failures etc. | review | 0/1/0/0/0 |
| private_pair_reshape | 09-10 | ENG | Private pair reshape script | code | 0/0/0/1/0 |
| private_triple_reshape_fast | 09-10 | ENG | Private triple reshape script | code | 0/0/0/1/0 |
| productive_root | 09-10 | ENG | Productive-root builder | code | 0/0/0/1/0 |
| profiles | 09-10 | P88 | 15,652 helper-weight profiles of the 88 corpus with circuit counts | data | 0/0/0/2/0 |
| proposed_run_all | 10-01 | AUD | Proposed fail-closed run_all.sh | tool | 0/0/0/0/0 |
| provenance | 10-27 | MISC | Provenance of local/NIST frontier witnesses | metadata | 0/0/1/0/0 |
| r34_regional_search | 08-17 | ENG | Regional heuristic for clusters 3+4 | code | 0/0/0/1/0 |
| radius3_bits_exact | 08-29 | A87 | Radius-3 exact neighbourhood (needs missing header) | code, incomplete | 1/0/0/1/0 |
| radius4_bits_exact_chunk | 08-29 | A87 | Radius-4 chunked (needs missing header) | code, incomplete | 1/0/0/1/0 |
| rank3_subspace_scan | 08-28 | P88 | Rank-3 subspace scan of a fixed 88 | code | 0/0/0/1/0 |
| reuse_first_98_circuit | 09-09 | A87 | 98-gate reuse-first circuit | construction | 0/0/0/0/0 |
| reuse_first_98_report | 09-09 | A87 | Report on the 98 | verified | 0/0/0/0/0 |
| reuse_first_98_verify | 09-09 | A87 | Verifier | code | 0/0/0/0/0 |
| shared_ancestor_search | 09-10 | ENG | Shared-ancestor search script | code | 0/0/0/1/0 |
| t3_k4_class1_witness | 08-16 | A87 | Native motif witness | data | 0/0/0/0/0 |
| tail_service_shadow_prices | 08-16 | A87 | Native tail min cost 33 + q for q Q-services | restricted class | 0/0/0/0/0 |
| test_synergy_pairs | 08-29 | A87 | Synergy-pair MILP (deps missing) | code | 1/0/0/0/0 |
| twodefect_fast | 08-28 | P88 | Two-defect search on a fixed 88 | code | 1/0/0/1/0 |
| twodefect_unbound | 08-28 | P88 | Same, unbounded | code | 1/0/0/1/0 |
| twodefect_unbound_filter | 08-28 | P88 | Same, filtered | code | 1/0/0/1/0 |
| twodefect_unbound_filter_all | 08-28 | P88 | Same, all | code | 1/0/0/1/0 |
| uphill_backbone28_raw | 08-15 | P88 | Raw uphill bypass output (source of the 19 bypasses) | data | 0/0/0/1/0 |
| verify_88_19_pairs | 09-09 | P88 | Verifier for the 19-pair 88 | code | 0/0/0/0/0 |
| verify_RECORD_89 | 07-08 | MISC | Verifier for RECORD_89 | code | 0/0/0/0/0 |
| verify_RECORD_98_depth3 | 07-08 | D3 | Verifier for 98@3 | code | 0/0/0/0/0 |
| verify_aes_90 | 10-08 | MISC | Verifier for completion_90 | code | 0/0/0/0/0 |
| verify_aes_mixcolumns_90 | 07-08 | MISC | Verifier for 90 | code | 0/0/0/0/0 |
| verify_depth_optimal_129 | 07-08 | D3 | Verifier for 129@3 | code | 0/0/0/0/0 |
| worker | 10-21 | S89 | long20 worker log: 91@4 -> 90@4 (08:42, reseed from 14) -> 89@4 (13:28, reseed from 07_d4_own91) | log | 0/0/3/2/0 |

Inverse MixColumns and S-box-bottom work have no top-level folder of their own: they live in `XOR_Adversarial_Audit_2026-11-04/.../audit_work/AES_smallmap_inverse_depth5_proofs_2026-11-04/`, `.../XOR_proof_master_bundle_2026-11-04/`, `.../AES_XOR_lower_bound_transfer_v2/` and `.../audit_results/{inverse_local,sbox}.md`, plus `AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/_long_paths/1b07e95627c98762/S18_XOR_FORWARD_INVERSE_COMPARISON_2026-10-14.md` (two inverse 88-gate unrestricted circuits replayed).

---

## 2. Latest checkpoints and what supersedes what

**Depth-3 lower-bound lineage (forward, depth <= 3).**
- Aug 14: `depth3_p26_tradeoff` and the Aug 12 catalog give D3 >= 80 (exact rational certificate) and the solver-only P<=26 => E>=30.
- Oct 16-17: 85 (`AES_depth3_exact_search`, P>=24) -> 86 (`..BOUND86..`) -> 89 (`..BOUND89..`) -> 90 (`..BOUND90_PAIR25..`, P>=25) -> 91 (`recovered_partial/02_depth3_bound91/`, P>=26; original zip damaged) -> 92 (`..BOUND92_PAIR26_EXACT`, `..RECIPE_LINKED..`) -> **93** (`AES_DEPTH3_LOWER_BOUND_93_2026-10-17`, public; standalone package `audit_work/AES_MixColumns_Depth3_LB93_2026-10-23/`, repaired and replayed 10-27; audited Nov 4). Each step supersedes the previous.
- Oct 17-20 (PUSH3..PUSH9): exclusion of 93-gate branches (P30 recipe-293), parent bound 25, PUSH7 structural lemmas. Interval stays 93-97.
- Oct 26-27: global97 pricing / common-bank program (`AES_Global_Proof_Research_Checkpoint`, `..Pricing_Snapshots`, `..Proof_Recovery_Supplement_v6`, `global97_*`). Target not met.
- Oct 27-31: proof program checkpoints 33/34 (`AES_Depth3_Proof_Program_2026-10-27`), 35 (`..Checkpoint35_Addendum`), 36-44 (`AES_Depth3_Checkpoint44`, `..Recovery_25`, `..Unrestricted`). Scoped closures; h=61 relaxation barrier.
- Nov 3: `AES_MixColumns_97_depth3_FROZEN_2026-11-03` (only inside audit_work) claims the full 97 bound; `AES_MixColumns_structural_proof_work*`, `human_proof_draft`, `human_theorem_v1`, and `AES_MixColumns_human_proof_v9_98_minus_one` (audit_work) try to shorten it.
- Nov 4: `XOR_Adversarial_Audit_2026-11-04` finds false v9 lemmas, does not recertify FROZEN; `XORProof_Lab_2026-11-04` carries corrected statements.
- Nov 5: `MixColumns_Proof_Diagnosis` and `MixColumns_Ordinary_Union_Checkpoint` (which embeds the Normalization / Global Ledger / Joined Bounds / Structural Capacity / Constructor Tradeoff checkpoints) are the **latest**. Status: 93 <= D3 <= 97, 97 optimality open.

**Unrestricted lower-bound lineage.**
- Aug: "N >= 33" trivial bound (Aug 12 catalog). Sep 21 Collapse status shows "L(M) >= 56".
- Sep 22: 63 (`research_6473`) -> 67, 69 (`research_next/`) -> 70 -> **71** (`research_push/PROOF71.md`, AUDIT71, FRESH_AUDIT71) -> 72, 73 (`research_deep/paired/`) -> 74 (`PROOF74.md`) -> **75** (`research_deep/PROOF75.md`). All stored at `research/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/push5/sources/xor/AES_MixColumns_Lower_Bound_75/` (subfolders `research_6473`, `research_next`, `research_push`, `research_deep`). Standalone edition 10-23: `audit_work/AES_MixColumns_Unrestricted_LB75_2026-10-23/` (public). Nov 4 audit: fresh replay passed, no substantive gap.
- **Beyond 75:** (i) a **76** claim dated 09-29/30, described only in `AES_Residual_Inference_2026_10_02/aes_inference/reference/bound_76_status.md` (948 MB package "kept by the author"; not in this archive; no human review; 10-13 memory says "do not claim it as independently verified"). (ii) G75 frontier work aiming to exclude 75 (`AES_Full_Neighborhood_Checkpoint_2026_10_09`, `AES_Checkpoint_Audit_2026_10_10`), (iii) exact-mask-sharing PUSH4-6 (509 surviving aggregate profiles at 75), (iv) `AES_MixColumns_Proof_Progress_2026-10-24` (166 oriented 75-gate profiles excluded), (v) depth-4 accounting push (no 76). None of (ii)-(v) claims 76. The guides keep **75**.

**Depth-4 lower-bound attempts.** `AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23` (75 <= D4 <= 89; >=12 direct pairs; N >= max(0,65-3p)); `AES_DEPTH4_RECURSIVE_ACCOUNTING_PUSH2_2026-10-23` (N+4p+kappa >= 81, audited; q=0 slice exclusions at G=75). PUSH7 (in PUSH9) proves "saturated represented sharing with a weight>=5 helper forces depth >= 5" but states `claims_all_87_circuits_need_depth_at_least_5: false`. `AES_XOR_lower_bound_transfer_v2` (audit_work) reduces 89@4 optimality to Psi >= 25, unproved. The Aug catalog says the depth-3 LP formulation is saturated (47.598) so the depth-4 theorem is unreachable on it. No depth-4 bound above 75 exists.

**87 construction attempts (methods -> outcomes).** All outcomes: no circuit below 88.
- Jul 30-Aug 12 (`Pasted markdown(20260812-133059)`): dual/transpose, global vocab + exact assembly, SAT ladders, NRPA, LLM-evolution, Steinberg words, down-step, sub-block resynthesis, union SAT, DFS over derivation DAGs, from-scratch M^T. Calibrated: P(87 per descent) < 2.0e-3 (95%); over 1,119,399 harvested 88-states no pair trimming to <=86 completes.
- Aug 14: exact symbolic Z3 87@<=4, 87@<=5 -> UNKNOWN (`STATUS_87_DEPTH_ATTACK*`, `aes_mixcolumns_87_depth_attack`).
- Aug 14-16: demand-flow / bi-mask routing (243 optimal 27-mask modules in a frozen exterior; 18 near-26 states, 17 lost); native algebra f(alpha,p) motif catalogues (restricted class).
- Aug 28-Sep 11: two-defect/radius-k scans on a fixed 88, alien MILP, 18-pair foundation, pair vocabularies (99..187), cold-start lineage walks (95-97), formula metamorphosis on 88 (no 87), mold87.
- Sep 19-23: Collapse autonomous framework; SK Lab neural pilots (Oct 9/12).
- Sep 22-27: restricted exact exclusions: h=0 => >=92; value pools 166/168/169 and depth<=5 pool 205 (MILP infeasible); four-exterior family optimum 88.
- Oct 2-8: residual inference, deep repair, fixed-budget reconstruction, gate ladder, cluster decompositions (71+17=88), cross-output forests (104+).
- Oct 12-15: h=2 => >=88 (so <=87 needs 3..31 odd helpers); two-foreign exclusion around 14 inventories; <=1 outside value => >=84 (LP cannot exclude 87); exact construction CNF `GLOBAL_87_NORMAL.cnf` (no UNSAT recorded; `GLOBAL_87.cnf` truncated).
- Oct 20-25: search v2/v3, mold solver (blank 87@5 UNKNOWN), counterpart replacement.
- Nov 5-6: exit search mc24 / barrier tree (0 improvements; mostly unresolved), circuit-space views.

---

## 3. Claims most relevant to the current search and proof questions

1. **Unrestricted L(M) >= 75.** Evidence: `research/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/push5/sources/xor/AES_MixColumns_Lower_Bound_75/research_deep/PROOF75.md` (+ PROOF74, paired/, research_push/PROOF71.md); standalone `research/XOR_Adversarial_Audit_2026-11-04/XOR_Adversarial_Audit_2026-11-04/audit_work/AES_MixColumns_Unrestricted_LB75_2026-10-23/`; PDF `research/AES_MixColumns_Unrestricted_Lower_Bound_75/`. Archive: computer-assisted, "review draft" (Oct); Nov 4 audit replay 52 s, 484 + 4,057 certificates, "no substantive gap" (`audit_results/baseline_bounds.md`, `baseline_75_replay_summary.json`). To trust: read the transposition-sequence / bounded-potential argument and check that the integer certificates cover every profile; it is public already.
2. **76 claim.** Evidence: only `research/AES_Residual_Inference_2026_10_02/aes_inference/reference/bound_76_status.md`. Archive: "machine-certified", no human review, package not shipped. To trust: obtain the 948 MB package; until then it is not evidence.
3. **Any <=87 circuit has 3..31 odd non-output helpers** (h=0 => >=92; h=1 inherited; h=2 => >=88). Evidence: `research/AES_MixColumns_Continuation_92_Restricted/research_continue/NO_ODD_HELPERS.md`; `research/AES_Multi_Helper_Proof_Continuation_2026_10_12/aes_multi_helper_2026_10_12/PROOF.md`, `AUDIT.json`; `research/AUDIT(2)`, `research/INDEPENDENT_AUDIT(1)`, `research/PAID_FIXED_2_CERTIFICATE`. Archive: computer-assisted, independent checks; the 10-17 package notes the later "h>=3" claim's proof directory (`small_odd/`) is missing. To trust: rerun the h=2 enumeration in a fresh implementation; locate the h=1 proof (stated as inherited).
4. **Output-parent forest identity G = 64 + c - b + p**, so 88 is optimal iff c-b+p >= 24 for every circuit. Evidence: `research/XOR_FOREST_CHECKPOINT_2026-10-13/xor_forest_checkpoint/XOR_PROJECT_MEMORY.md`; generalized as G = 2m+K+c-r-q in `audit_work/AES_XOR_lower_bound_transfer_v2/transfer_v1/`. Archive: identity correct (audit `transfer_framework.md`); the inequality is open. To trust: the identity is short; check normalization (distinct live masks, outputs independent).
5. **Sharing identity G = 108 + delta - S**; 88 optimal iff S <= 20 + delta; repo 88@5 has delta = 20, S = 40. Evidence: `audit_work/XOR_proof_master_bundle_2026-11-04/xor_proof_master_2026-11-04/status/forward88/STATUS.md`. Archive: identity survives audit; interface theorem open; support-moment relaxation gives only ~32.2. To trust: needs disjoint output blocks and no dead gates.
6. **Four-output group minima** 12,16,12,16,16,12,12,12 (forward, sum 108) and 23,27,27,35,35,31,27,23 (inverse, 228). Evidence: `audit_work/XOR_proof_master_bundle_2026-11-04/.../validated/four_output_groups/`; `XORProof_Lab_2026-11-04/xorproof_lab/corrected_proofs/CORRECTED_THEOREMS.md`; audit `inverse_local.md`. Archive: confirmed with matching circuits; theorem needs no zero rows and no zero columns. To trust: small exhaustive checks; not additive.
7. **Value-pool exclusions.** No 87 using only masks of the two depth-5 88s (+ up to 3 depth-6 masks: pools 166/168/169), and no 87@<=5 within the 205-mask pool of three controls. Evidence: `research/AES_Value_Pool_169_Continuation/`, `research/AES_Depth5_Pool205_Continuation/DEPTH5_POOL205_REPORT.md`. Archive: HiGHS status 8 (infeasible), positive control at 88. To trust: an independent MILP/SAT with a proof log; these are vocabulary-conditional (the Aug catalog warns such harvested-vocabulary negatives have likelihood ratio ~1).
8. **Four-exterior family**: with live root x7^x23 and <=4 quotient values outside the 114-value pool the optimum is 88; a <=87 with that root needs >=5 outside values. Evidence: `research/AES_Four_Exterior_and_Value_Compatibility/AES_Four_Exterior_and_Value_Compatibility/START_HERE.md`. Archive: audited, family-scoped. To trust: check the quotient-completeness argument.
9. **Two-foreign completeness**: every <=55-helper circuit within 2 masks of one of 14 known 56-helper inventories is excluded (409,640 deletion cases). Evidence: `research/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/AES_TWO_FOREIGN_2026-10-15/`. Archive: two enumeration implementations. To trust: rerun independent mode; inventory-conditional.
10. **88 plateaus are exact Cartesian products.** Repo 88@5 remove-one closure (no cap) = 2,187 = 3^7 (49-value core, Hamming graph H(7,3), depths 45/1,494/648); 49 closures hold 437 of 442 record sets, shapes 3^7, 3^6, 45x3^4, 33x3^5. Evidence: `research/circuit-space-views/circuit-space-views.html` (V3); companion `Barrier Tree/Barrier Tree.pdf` (B11 = 8,019 = 33x3^5, depths 5..10). Archive: facts-only; generated from `~/xs-campaigns` runs (not in archive). To trust: rerun the closure enumerator from the run records.
11. **Exit search from B11 found no improvement but is mostly unresolved**: 2,605 +1 classes, home 671, join 247, unresolved 1,687, improve 0; 2,064 descents used a heuristic factor shortcut; +2 band 13,212 classes not descended. Evidence: `research/Barrier Tree/Barrier Tree.pdf`; `guides/BARRIER_TREE_FINDINGS.md`. Archive: "empirical snapshot, explicitly incomplete". To trust: path sequences and census verifier (not in archive).
12. **89@4 is one closed product family.** Remove-one closure of repo 89@4 at cap 4 = 81 = 3^4 (53-value core); all 81 distinct record circuits (525 files) are its cells; its +1 band (16,173) and that band's closure (76,626) descend only into it; level profile 26/22/29/12 in all 156 recorded circuits; first-layer change rebuilds reach 92+. Evidence: `research/circuit-space-views/circuit-space-views.html` (V2, V3, V6); `guides/RECENT_CONVERSATION_FINDINGS.md` (conversation reconstruction, C1/C2). Archive: exact for expand-once-then-remove1 only; "not 'no other 89@4 exists'". To trust: the enumerator and logs; the 26-layer and "6 of 10 runs" claims are conversation-only.
13. **Where 89@4 came from**: own-lineage 91@4 seed -> 90@4 (worker 14) -> 89@4 at 13:28 on 10-21 (reseed from 07_d4_own91). Evidence: `research/worker/worker.log`, `research/aes_long20_audit_and_own90_2026-10-21/long20_audit_2026-10-21/RESULTS.txt`, `research/mixcolumns-g89-d4-1b2a9fcbb250/`. Archive: 90@4 audited; 89@4 independently verified in the Nov 4 audit (`audit_results/circuits.md`). To trust: replay the long20 records (not run here).
14. **Search-operator wall at 88.** From 1,500 clean from-scratch descents P(87 per descent) < 2.0e-3 and P(87 | reached 88) < 0.056 (95%); no harvested-88 pair trimming to <=86 completes over 1,119,399 states. Evidence: `research/Pasted markdown(20260812-133059)/Pasted markdown(20260812-133059).md` (SCOREBOARD; underlying logs under a REPO path not included). Archive: "a statement about the operator class, not about existence". To trust: the original W5 logs.
15. **Depth-3 relaxations cannot reach 97 by themselves**: strengthened LP has an exact point of value 81.20413618 (`research/MixColumns_Proof_Diagnosis/mixcolumns_blocker_diagnosis/model_results/MODEL_AND_RESULTS.md`); h=61 helper relaxation barrier (`research/AES_Depth3_Checkpoint44_Unrestricted/.../H61_STRONG_IMAGES_BARRIER44.md`); <=1-outside-value pricing reaches 83.85 only (`PUSH9/pricing_lab/PROOFS_AND_RESULTS.txt`). Archive: exact rational points checked. Relevance: method lesson for B (LP-only routes stall well below the target). To trust: rerun the stand-alone rational checkers.

---

## 4. Flags

**Titles claiming proof / complete / FROZEN that the guides mark open or corrected.**
- `audit_work/AES_MixColumns_97_depth3_FROZEN_2026-11-03/.../README.md`: "Verdict: the corrected argument establishes the 97-XOR lower bound". CURRENT_STATUS: 97 optimality **open**; Nov 4 audit "not disproved; not independently recertified".
- `audit_work/AES_MixColumns_human_proof_v9_98_minus_one/`: "32 + 30 + 36 - 1 = 97". Audit: 18-helper lemma false (16-helper counterexample `audit_results/v9_recheck/surcharge_counterexample_16_6.json`), equality list misses (16,12,4), global matching bridge unproved.
- `human_theorem_v1` ("A modular human proof that depth-three AES MixColumns needs 97") and `human_proof_draft`, `AES_MixColumns_structural_proof_work*`: SOURCES.csv note "Historical candidate; 97 optimality remains open".
- `audit_work/AES_smallmap_inverse_depth5_proofs_2026-11-04/proof_transfer_work/RESULTS.md`: claims C5(InvMixColumns) = 118 and "no 28-gate S-box circuit at depth <= 4, so 29@4 optimal". Audit: inverse LP optimum is 32 (claim refuted); S-box 29@4 "not established", certificates absent.
- `audit_work/XOR_proof_master_bundle_2026-11-04/`: "integer optimum 37" (audit: only feasible 37, interval 36-37 unresolved) and four-output theorem missing the no-zero-rows hypothesis.
- `AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20`: "COMPLETE" refers to archive completeness; contains the unverified h>=3 claim.
- `depth_optimal_129*`: "optimal" means minimal depth only (129 gates).
- `AES_Depth3_Checkpoint44_Unrestricted`: depth-3 work despite the name.
- `depth3_p26_tradeoff`: solver-closed, "NOT yet rational/DRAT/VIPR certified".
- `Barrier Tree`: "2,605/2,605 classes descended" reads as complete; 1,687 unresolved and 2,064 heuristic shortcuts.

**Contradictions between files.**
- 76 (bound_76_status, "genuine, machine-certified") vs 75 everywhere else (guides, audit, 10-13 memory).
- Inverse 118@5 optimal (small-map RESULTS) vs open (audit, CURRENT_STATUS).
- S-box 29@4 optimal (small-map RESULTS) vs withdrawn.
- FROZEN verdict vs audit/CURRENT_STATUS.
- Aug 12 catalog lists "XOR-count(M) = XOR-count(M^T) exactly for dead-gate-free SLPs" while the S-box proof uses C(A) = C(A^T) + 10 for the rectangular map; consistent only if the square-map case is meant (check before reuse).
- 89@4 record counts: "156 records" (Nov 2 conversation) vs "525 files, 81 distinct circuits" (Nov 5 views). Different dates and units, not necessarily a conflict.
- 88@5 plateau sizes: views tree leaf 0 = 4,374 (neutral remove1 + expand-envelope, depth window 7) vs repo remove1 closure 2,187 vs B11 8,019 (depths 5..10). Different move sets and caps; compare only with the definitions.
- `RECORD_89*` (Jul 8) is an unrestricted 89 at depth 10, not the 89@4.
- `hub87_abstract` carries "physical_required": 87 but is an abstract graph, not a circuit; nothing in the archive realizes it.

**Missing evidence (referenced but not present).**
- 76 package (948 MB, 4,842 files): absent.
- `small_odd/` proof tree for h=1/h>=3, `source/` tree, final `MANIFEST.json` of `AES_REASONING_GLOBAL_2026-10-16.zip` (unreadable original; `PUSH9/AES_OPTIMALITY_ALL_FINDINGS_2026-10-17/packaging/MISSING_FILES_AND_LIMITS.txt`).
- `GLOBAL_87.cnf` truncated (only `GLOBAL_87_NORMAL.cnf` complete, stored in PUSH9 `AES_UNRESTRICTED_RESEARCH_HANDOFF_2026-10-15/recovered/`); no solver result for either.
- `AES_DEPTH3_BOUND91_PAIR26_PROOF.zip`: only 3 distinct files recovered (`recovered_partial/02_depth3_bound91/`); `recovered_partial/05_unrestricted_push/` holds no file; `AES_Unrestricted_Push_2026_10_08.zip` complete entries only, directory lost.
- S-box 29@4 certificates; routing-LNS 97@3 witness and per-gate trajectory CSV; 17 of 18 near-26 states; SK Lab v0.6/0.7 code, `LEARN_README.md`, `XORSLP_README.md`.
- C++ files `lemma_beam`, `outsider1_exact`, `radius3_bits_exact`, `radius4_bits_exact_chunk` include `lemma_data.hpp` (absent); Python `alien_search`-family scripts import `/mnt/data/combined_d5d6.py` and `more88s.py` (absent).
- Aug 12 catalog's W5/W6 ledgers (paths under `/home/joebachir20/xor_ui/slp-plateau-search`) are not in the archive.
- 10-13 memory: "checks of 200 circuits and their transposes ... logs have not been recovered".
- Barrier Tree path sequences and census verifier; the 81-circuit family enumerator and logs (the Nov 5 views derive from `~/xs-campaigns` runs, not shipped).
- `AES_Depth3_Checkpoint44_Recovery_25`: "not a complete continuation25 certificate archive"; Checkpoint44's first NPZ cache damaged (complete V2 replacement present and matching).
- `Circuit_Lower_Bound_Discovery_RECOVERY`: last unfinished work "not fully recovered".

---

## 5. Statements the archive treats as established (with exact scope)

Each is the archive's claim, tagged with its source; "audited" means the Nov 4 audit reports a check, not that I checked it.

1. Forward outputs have weights 5 (20 rows) and 7 (12 rows); a depth-2 signal has support <= 4; hence forward depth >= 3 and every output needs its own depth-3 gate. `RECORD_98_depth3_verification_report`; `MixColumns_Proof_Diagnosis/.../model_audit/MODEL_EQUIVALENCE.md`; row profile in PUSH9 `_long_paths/1b07e95627c98762/S18_XOR_FORWARD_INVERSE_COMPARISON_2026-10-14.md`.
2. Inverse MixColumns needs depth >= 5: eight outputs have weight 19 > 16 = max support at depth 4; a 118@5 circuit exists. Inverse weights 8 each of 11, 13, 19 and 4 each of 15, 17. Audited. `XOR_Adversarial_Audit_2026-11-04/.../audit_results/inverse_local.md`; `guides/CURRENT_STATUS.md`.
3. M^4 = I and M^3 = N (inverse); this gives no gate-preserving conversion. `S18_XOR_FORWARD_INVERSE_COMPARISON_2026-10-14.md`.
4. Unrestricted 75 <= L(M) <= 88 (any depth, cancellation, fan-out). Audited replay. `audit_results/baseline_bounds.md`; LB75 package (section 3, item 1).
5. Depth-3 93 <= D3 <= 97. Audited full replay (962 s, 0 uncovered). `audit_results/baseline_bounds.md`; `audit_work/AES_MixColumns_Depth3_LB93_2026-10-23/`.
6. Verified constructions: forward 97@3, 89@4, 88@5 (88s also at depths 6..13 per the Aug catalog), 90@4 (NIST and own lineage); inverse 118@5; inverse unrestricted 88 (two circuits, depths 19 and 33). Audit `audit_results/circuits.md`; `aes_long20_audit_and_own90_2026-10-21`; S18 comparison file.
7. Four-output group minima (unrestricted, exact): forward 12,16,12,16,16,12,12,12 (sum 108), inverse 23,27,27,35,35,31,27,23 (sum 228); requires no zero rows and no zero columns; not additive. Audited. `XORProof_Lab_2026-11-04/xorproof_lab/corrected_proofs/CORRECTED_THEOREMS.md`; `audit_results/inverse_local.md`.
8. Depth-3 internal facts (depth <= 3 only): W5 group optimum 12, W7 group 16, W7 groups 3&4 together 32, all twelve W7 outputs 48; normalized pair count P >= 26 and P = 26 attainable (by a 100-gate circuit); W7 helper union >= 36 (audited, with corrected higher-cost accounting); parent bound 25. `..BOUND86..`, `..BOUND89..`, `..BOUND92_PAIR26_EXACT/README_CURRENT.txt`; `audit_results/depth3_v9.md`; `AES_GLOBAL_STRUCTURAL_ARCHIVE_VERIFICATION_PUSH8_2026-10-20`.
9. Nov 5 local depth-3 results: two-group union |J5 u J6 u R56| >= 6 + beta(t) + |Z|, beta = 6,6,6,7,8; H0 = 16 forces >= 2 original CC pairs (315 roots, 49,683,204 leaves); fixed-parent all-birth minima 97 and 107; boundary-only floor 49 false (124@3 circuit). Audited within the prepared/normalized model. `MixColumns_Ordinary_Union_Checkpoint/ordinary_completion/ROOT_REVIEW.txt`, `STATUS.json`.
10. Exact identities (not bounds): G = 32 + x + y + h (parity); G = 64 + c - b + p (output-parent forest); G = 2m + K + c - r - q; G = 108 + delta - S (forward), G = 228 + delta - S (inverse), with targets S <= 20 + delta and S <= 110 + delta open. Audited as identities. `audit_results/transfer_framework.md`; `XOR_FOREST_CHECKPOINT_2026-10-13`; master `status/forward88/STATUS.md`.
11. Restricted unrestricted-depth exclusions: h = 0 => >= 92; h = 2 => >= 88; any <=87 has 3 <= h <= 31; live root x7^x23 family needs >= 5 outside quotient values; two-foreign exclusion around 14 inventories; <= 1 outside value => >= 84. Computer-assisted, not audited on Nov 4. Section 3 items 3, 8, 9; PUSH9 `pricing_lab`.
12. Symmetry: free wire-symmetry group of MixColumns is order 4 (byte rotation); count-preserving symmetry order 8. Byte-level programs need >= 3 multiplications and cannot reach 88; byte programs with <= 3 arbitrary scalar multiplications need exactly 96. `Pasted markdown(20260812-133059)` (items 8-9); `Circuit_Lower_Bound_Discovery_RECOVERY`.
13. Pair/triple geometry: 496 pairs, 236 inside some output; 4,960 triples, 536 inside some output, 84 inside two outputs (68 same cluster). `pair_triple_catalog_report`. Root geometry: min raw/raw path 6, raw/output 10, no input or input pair in the W7 span (audited, `audit_results/root_geometry_independent.json`).
14. 88 plateau census (record-conditional, remove-one moves): repo 88@5 closure 3^7 = 2,187 (49-value core), 49 closures cover 437/442 record sets, each an exact product; across 653 distinct 88@5 records only 2 rotation orbits (3 values) are common; B11 = 8,019 = 33 x 3^5 with depths 5:18, 6:2,250, 7:3,321, 8:810, 9:972, 10:648. Earlier: 260 audited 88s have 256 distinct helper sets and 2 common helpers; demand-flow module family = 22-mask backbone x 3^5 = 243 within one frozen exterior. `circuit-space-views`; `Barrier Tree`; `AES_Helper_Set_Comparison_2026_10_10`; `bi_mask_requested_evidence/02_backbone_defects/BACKBONE_DEFECT_FINDINGS.md`.
15. 89@4 census (cap 4, remove-one): exactly 81 = 3^4 circuits with a 53-value core (37 common rotation orbits), equal to all 81 known distinct 89@4 records; +1 band 16,173 and its closure 76,626 return only to it. Inverse 118@5 repo closure 200 circuits; 56 closures hold all 510 record sets. `circuit-space-views` (V2, V3, V6). Conversation-only (not established): 26/22/29/12 level profile in 156 records, "change one first-layer gate -> 92 or worse". `guides/RECENT_CONVERSATION_FINDINGS.md`.
16. S-box bottom (18 independent inputs, 8 affine outputs, XOR/XNOR): unrestricted optimum 28; transpose optimum 18; C(A) = C(A^T) + 10. Audited. 29@4 optimality not established. `audit_results/sbox.md`; master `validated/aes_sbox_bottom/PROOF.md`.
17. Small maps: scale-1 unique 9-gate circuit; scale-2 optimum 26 (exactly 12 cancellation-free optimal helper sets); scale-3 43..46; clusters 3 and 4 exactly 16 each, together 29..30. `AES_Sharing_Patterns_and_Optimal_Variants/scale_sharing/REPORT.md`; `AES_Scale2_Optimal_26_Proof`; `AES_Cluster_Pairs_Completion_2026_10_07`.
18. Inverse LP relaxation facts: original occurrence LP optimum exactly 32 (not a circuit); capped version ~34.3133; integer value 37 feasible, optimum unresolved (36-37). Audited. `audit_results/inverse_local.md`.
