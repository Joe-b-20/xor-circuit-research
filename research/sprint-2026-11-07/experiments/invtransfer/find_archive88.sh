#!/bin/bash
# Locate the archive's two unrestricted 88-gate inverse circuits (depths 19 and 33).
Z=~/xs-campaigns/2026-11-07-sprint/import/zip
D=$Z/research/AES_OPTIMALITY_ALL_FINDINGS_COMPLETE_PUSH9_2026-10-20/AES_UNRESTRICTED_RESEARCH_HANDOFF_2026-10-15/historical_notes
echo "== historical_notes"; ls "$D" | head -50
echo "== loader lines"; grep -n "json\|open(\|glob" "$D/xor_inverse_experiment.py" | head -20
echo "== metrics"; head -c 2000 "$D/xor_inverse_experiment_metrics.json"; echo
echo "== candidates by name"
find "$Z" -iname "*inv*88*" -o -iname "*inverse*circuit*" -o -iname "*invmix*.json" 2>/dev/null | grep -v "\.pyc" | head -30
echo "== INVENTORY lines on depths 19/33"
grep -n "depth 19\|depth 33\|depths 19\|19 and 33" ~/xs-campaigns/2026-11-07-sprint/import/INVENTORY.md | head
