cd ~/xs-campaigns/2026-11-07-sprint/invtransfer
for s in oddh_sharing.py firstlayer.py lineage.py summarize_plateaus.py; do
  echo "=== $s $(date -u +%H:%M:%S)"
  nice -n 10 python3 "$s"
  echo "=== exit $? $(date -u +%H:%M:%S)"
done
echo ALL_DONE
