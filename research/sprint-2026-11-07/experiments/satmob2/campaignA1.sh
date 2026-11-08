#!/bin/bash
# satmob2 phase A1: local components (satmob method) on the coupled-plateau circuits.
# singles and pairs with free <= 3 at 120 s; one solver child at a time, nice 8; idempotent.
cd ~/xs-campaigns/2026-11-07-sprint/satmob2
CIRCS="kste:3146 kste:2229 kste:1557 sampleA:109 sampleA:48 sampleA:781 sampleC:131"
for c in $CIRCS; do python3 mob2.py run "$c" 1 120 3; done
for c in $CIRCS; do python3 mob2.py run "$c" 2 120 3; done
echo A1_DONE
