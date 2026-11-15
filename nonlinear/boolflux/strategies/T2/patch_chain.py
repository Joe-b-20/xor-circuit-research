"""one-off patch: add --chain (follow an unshare result for K jobs) to walk.py"""
p = 'walk.py'; s = open(p).read()


def rep(a, b):
    global s
    assert a in s, a
    s = s.replace(a, b, 1)


rep("        if rng.random() < a.p_start or not elite:",
    """        if follow is not None and follow[1] > 0:
            c = core.from_kernel(follow[0], 'f'); origin = 'chain%d:' % follow[1] + follow[2]
            follow = (follow[0], follow[1] - 1, follow[2])
        elif rng.random() < a.p_start or not elite:""")
rep("        if a.p_unshare and rng.random() < a.p_unshare:",
    """        unsh = False
        if not origin.startswith('chain') and a.p_unshare and rng.random() < a.p_unshare:
            unsh = True""")
rep("    t0 = time.time(); it = 0; best = None; seen_found = set()",
    "    t0 = time.time(); it = 0; best = None; seen_found = set(); follow = None")
rep("        log.write(json.dumps(rec) + '\\n'); log.flush()\n        print(",
    """        if a.chain and (unsh or origin.startswith('chain')):
            if feasible(m, acaps if use_alt else caps):
                left_ = a.chain if unsh else follow[1]
                follow = (k, left_, 'it%d' % it) if left_ > 0 else None
            elif unsh:
                follow = None
        log.write(json.dumps(rec) + '\\n'); log.flush()
        print(""")
rep("    ap.add_argument('--p-unshare'",
    "    ap.add_argument('--chain', type=int, default=0, help='after an unshare job, continue its result for this many jobs')\n    ap.add_argument('--p-unshare'")
open(p, 'w').write(s)
print('patched')
