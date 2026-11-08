#!/bin/bash
# satmob2 phase B: the coupled-factor instances (fac.py), then the remaining local singles.
# Waits for phase A1; one solver child at a time, nice 8; idempotent; STOP stops between instances.
cd ~/xs-campaigns/2026-11-07-sprint/satmob2
while ! grep -q A1_DONE campaignA1.out 2>/dev/null; do sleep 10; done
# 1. every coupled factor at 120 s, full pool (sizes + a first hardness reading), cheapest first
python3 fac.py run kste:1557  kste:41 120
python3 fac.py run kste:3146  kste:43 120
python3 fac.py run kste:2229  kste:34 120
python3 fac.py run sampleA:109 hunt:p943c008e56986b92 120
python3 fac.py run sampleA:48  hunt:pce9227a62d5504c7 120
python3 fac.py run sampleA:781 file:../giants/pl_p80424727ddf34e79.json 120
python3 fac.py run sampleC:131 file:../giants/pl_p55f9dc07f8b3409b.json 120
# 2. the two free = 5 coupled factors at 600 s
python3 fac.py run kste:1557  kste:41 600
python3 fac.py run kste:3146  kste:43 600
# 3. local singles with free > 3 at 120 s (the helper-root 3-way factors)
for c in kste:3146 kste:2229 kste:1557 sampleA:109 sampleA:48 sampleA:781 sampleC:131; do python3 mob2.py run "$c" 1 120; done
# 4. span pool (weaker statement) for the radix 45 and 2101 coupled factors at 600 s
python3 fac.py run kste:2229  kste:34 600 0 span
python3 fac.py run sampleA:109 hunt:p943c008e56986b92 600 0 span
# 5. local pairs with free = 4 at 120 s, as time permits
for c in kste:3146 kste:2229 kste:1557 sampleA:109 sampleA:48 sampleA:781 sampleC:131; do python3 mob2.py run "$c" 2 120 4; done
echo B_DONE
