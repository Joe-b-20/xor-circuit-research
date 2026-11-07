#!/usr/bin/env python3
"""Summarise the discovery table in plateaus.log: cumulative vocabulary and new-word counts."""
import re, sys
rows = []
for line in open(sys.argv[1] if len(sys.argv) > 1 else "plateaus.log"):
    m = re.match(r"\s+(\d+)\s+([AB])\s+(\S+)\s+([\d.]+)\s+(\d+)\s+(\[.*?\])\s+(\d+)\s+(\d+)\s+(\d+)\s*$", line)
    if m:
        rows.append((int(m.group(1)), m.group(2), float(m.group(4)), int(m.group(5)), m.group(6),
                     int(m.group(7)), int(m.group(8)), int(m.group(9))))
print("plateaus in table:", len(rows))
for r in rows[::max(1, len(rows) // 10)] + rows[-1:]:
    print(f"  #{r[0]:3d} {r[1]} t={r[2]:6.1f} min size={r[3]:8d} new_words={r[5]:3d} cum_words={r[6]:4d}")
tot = sum(r[5] for r in rows)
zero = sum(1 for r in rows if r[5] == 0)
print(f"new words total {tot} over {len(rows)} plateaus; plateaus adding no new word: {zero}")
