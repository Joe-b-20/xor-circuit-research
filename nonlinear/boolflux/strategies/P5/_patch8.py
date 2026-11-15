"""invskel: --shard i/n (process only helper choices with index % n == i)."""
p = "invskel.py"; s = open(p).read()
s = s.replace("""    ap.add_argument('--maxcost', type=int, default=99, help='keep leaves with cost <= this')""",
"""    ap.add_argument('--maxcost', type=int, default=99, help='keep leaves with cost <= this')
    ap.add_argument('--shard', default='0/1', help='i/n: only first-AND choices with index %% n == i')""")
s = s.replace("""        if len(chosen) == 1 and not a.prefix: stats["top"] = stats.get("top", 0) + 1; print(""",
"""        if len(chosen) == 1 and not a.prefix:
            stats["top"] = stats.get("top", 0) + 1
            si, sn = map(int, a.shard.split('/'))
            if (stats["top"] - 1) % sn != si: return
            print(""")
open(p, "w").write(s)
