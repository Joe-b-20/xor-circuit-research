#!/bin/bash
# wait.sh FILE PATTERN SECONDS : return when FILE contains PATTERN or after SECONDS; then print the file.
f="$1"; pat="$2"; secs="${3:-170}"
end=$(( $(date +%s) + secs ))
while [ "$(date +%s)" -lt "$end" ]; do
  if grep -q -E "$pat" "$f" 2>/dev/null; then break; fi
  sleep 2
done
cat "$f" 2>/dev/null
date
