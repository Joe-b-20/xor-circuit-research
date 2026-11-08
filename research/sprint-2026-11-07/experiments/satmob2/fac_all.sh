#!/bin/bash
# factor analysis (no solving) for the seven circuits against their plateau objects
cd ~/xs-campaigns/2026-11-07-sprint/satmob2
python3 fac.py analyze kste:3146  kste:43
python3 fac.py analyze kste:2229  kste:34
python3 fac.py analyze kste:1557  kste:41
python3 fac.py analyze sampleA:109 hunt:p943c008e56986b92
python3 fac.py analyze sampleA:48  hunt:pce9227a62d5504c7
python3 fac.py analyze sampleA:781 file:../giants/pl_p80424727ddf34e79.json
python3 fac.py analyze sampleC:131 file:../giants/pl_p55f9dc07f8b3409b.json
