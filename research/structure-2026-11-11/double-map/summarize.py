"""Compact view of a run_exh.py table.  usage: python3 summarize.py table_m4.txt"""
import re
import sys

rows = []
for line in open(sys.argv[1]):
    m = re.match(r"(\S+)\s+rk=(\d+) delta=(\d+) F=(\d) eps=(\S+)", line)
    if not m:
        continue
    T, rk, d, F, e = m.groups()
    ns = re.search(r"solution_sets=(\d+) pair_partition_sets=(\d+)", line)
    hc = re.search(r"blocks c\):(.*?)\]", line)
    rows.append((T, int(rk), int(d), int(F), e, ns.group(1) if ns else "-", ns.group(2) if ns else "-",
                 hc.group(1).strip() if hc else ""))
print(f"{'T':<22} rk delta F eps  sets  pair  (h,c) histogram of optimal extra-sets")
for r in rows:
    print(f"{r[0]:<22} {r[1]:>2} {r[2]:>5} {r[3]} {r[4]:>3} {r[5]:>6} {r[6]:>5}  {r[7]}")
print()
cnt = {}
for r in rows:
    key = (r[2], r[4])
    cnt[key] = cnt.get(key, 0) + 1
print("classes by (delta, eps):", dict(sorted(cnt.items())))
print("classes with eps = 0:", sum(1 for r in rows if r[4] == "0"), " with F = 1:", sum(1 for r in rows if r[3] == 1),
      " with delta = 0:", sum(1 for r in rows if r[2] == 0))
print("classes with no pair-partition optimum:", [r[0] for r in rows if r[6] == "0"])
print("solved classes without a helper-free optimum:", [r[0] for r in rows if r[5] != "-" and "(h=0," not in r[7]])
print("solved classes with eps >= 1 and no optimum that uses a helper:",
      [r[0] for r in rows if r[5] != "-" and r[4] != "0" and "(h=1," not in r[7] and "(h=2," not in r[7] and "(h=3," not in r[7]])
print("classes with eps > delta:", [(r[0], r[1], r[2], r[4]) for r in rows if r[4].isdigit() and int(r[4]) > r[2]])
