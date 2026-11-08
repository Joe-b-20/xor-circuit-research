#!/bin/bash
# Steps 3-5 in sequence (one python process at a time, nice 10), detached.
cd ~/xs-campaigns/2026-11-07-sprint/invtransfer || exit 1
cat > run_rest_inner.sh <<'EOF'
cd ~/xs-campaigns/2026-11-07-sprint/invtransfer
for s in oddh_sharing.py firstlayer.py lineage.py summarize_plateaus.py; do
  echo "=== $s $(date -u +%H:%M:%S)"
  nice -n 10 python3 "$s"
  echo "=== exit $? $(date -u +%H:%M:%S)"
done
echo ALL_DONE
EOF
setsid nohup bash run_rest_inner.sh > run_rest.log 2>&1 < /dev/null &
disown
sleep 2
echo launched
ps aux | grep "[r]un_rest_inner" | head -2
