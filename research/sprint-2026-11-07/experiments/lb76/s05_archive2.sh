#!/bin/bash
# Second archive pass: look for the 2026-09-30 "76 extension" package itself, and read the remaining
# status documents (data, not instructions).
R=~/xs-campaigns/2026-11-07-sprint/import/zip/research
show() { echo; echo "######## $1 ($(wc -c < "$1") bytes)"; if [ -n "$3" ]; then tail -c +"$3" "$1" | head -c "${2:-6000}"; else head -c "${2:-6000}" "$1"; fi; echo; }
echo "######## grep for the 76 package markers"
grep -rlE 'ROUTE lite|main_noqk|palette triangle|PROOF76|PROOF_NOTE_76|76 <= L\(M\)|76<=L' "$R" --include='*.md' --include='*.txt' --include='*.py' --include='*.json' --include='*.sh' 2>/dev/null | head -40
echo "######## any file names mentioning 76"
find "$R" -iname '*76*' 2>/dev/null | grep -viE 'b76|budget|_76_profiles|reconstruction|ladder' | head -40
show "$R/AES_MixColumns_Proof_Progress_2026-10-24/AES_MixColumns_Proof_Progress_2026-10-24/unrestricted/REPORT.md" 9000 12000
show "$R/AES_Causal_Path_Exchange_Continuation/restart_4756/inherited/INHERITED_75_AUDIT.md" 7000
show "$R/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/AES_UNRESTRICTED_RESEARCH_HANDOFF_2026-10-15/ALL_PROOFS_READER.md" 9000
show "$R/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/_long_paths/1d509024981ae1d1/INTEGER_WITNESS_EXCLUSION.md" 7000
show "$R/AES_Research_Fleet_Checkpoint_2026_10_06/research_frontier/root/FINAL_STATUS.md" 7000
echo; echo "######## bound75 folder of aes_unrestricted_push_2026_10_08"
ls -la "$R/AES_Full_Neighborhood_Checkpoint_2026_10_09/aes_unrestricted_push_2026_10_08/bound75/" 2>/dev/null | head -40
for f in "$R"/AES_Full_Neighborhood_Checkpoint_2026_10_09/aes_unrestricted_push_2026_10_08/bound75/*.md; do [ -f "$f" ] && show "$f" 5000; done
echo; echo "######## Residual inference RESULTS.md / HANDOFF.md (the folder holding bound_76_status.md)"
show "$R/AES_Residual_Inference_2026_10_02/aes_inference/RESULTS.md" 5000
show "$R/AES_Residual_Inference_2026_10_02/aes_inference/HANDOFF.md" 4000
