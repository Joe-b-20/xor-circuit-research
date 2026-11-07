#!/bin/bash
# Read the archive documents that discuss pushing beyond 75 (data, not instructions).
R=~/xs-campaigns/2026-11-07-sprint/import/zip/research
show() { echo; echo "######## $1 ($(wc -c < "$1") bytes)"; head -c "${2:-6000}" "$1"; echo; }
show "$R/AES_Residual_Inference_2026_10_02/aes_inference/reference/bound_76_status.md" 12000
show "$R/AES_MixColumns_Proof_Progress_2026-10-24/AES_MixColumns_Proof_Progress_2026-10-24/unrestricted/REPORT.md" 12000
show "$R/AES_MixColumns_Proof_Progress_2026-10-24/AES_MixColumns_Proof_Progress_2026-10-24/continuation_unrestricted/FRONTIER.md" 12000
show "$R/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/push6/global_chronology/SCAN_AND_CERTIFICATE_STATUS.txt" 10000
show "$R/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/push5/global_chronology/SCAN_AND_CERTIFICATE_STATUS.txt" 6000
show "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/README.md" 8000
show "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/STATUS.json" 3000
show "$R/AES_Weight_Parity_Joint_Accounting_2026_10_12/NEXT.md" 4000
show "$R/AES_Unrestricted_Weight_Parity_2026_10_12/aes_weight_parity_2026_10_12/README.md" 6000
show "$R/AES_Research_Fleet_Checkpoint_2026_10_06/research_frontier/root/FINAL_STATUS.md" 6000
show "$R/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/AES_UNRESTRICTED_RESEARCH_HANDOFF_2026-10-15/ALL_PROOFS_READER.md" 8000
show "$R/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/_long_paths/1d509024981ae1d1/INTEGER_WITNESS_EXCLUSION.md" 6000
echo; echo "######## listing of push6/global_chronology and push5/global_chronology"
ls -la "$R/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/push6/global_chronology/"
ls -la "$R/AES_DEPTH4_LOWER_BOUND_ATTEMPT_2026-10-23/AES_EXACT_MASK_SHARING_PUSH6_2026-10-23/push5/global_chronology/"
echo; echo "######## listing of Proof_Progress unrestricted dirs"
ls -la "$R/AES_MixColumns_Proof_Progress_2026-10-24/AES_MixColumns_Proof_Progress_2026-10-24/unrestricted/" "$R/AES_MixColumns_Proof_Progress_2026-10-24/AES_MixColumns_Proof_Progress_2026-10-24/continuation_unrestricted/"
