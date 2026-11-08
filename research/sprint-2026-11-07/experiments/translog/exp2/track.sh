#!/bin/bash
cd /home/joebachir20/xs-campaigns/2026-11-07-sprint/translog/exp2 || exit 1
exec nice -n 8 python3 track.py 5400 60 >> track.log 2>&1
