#!/usr/bin/env python3
"""Task 4: for leaves the pilot excludes by 'step S (LP)', re-check with the reviewer's own enumeration that no complete
skeleton allowed by R4-R6 and Lemma 4.6 (R5) has an LP-feasible count system (prune only on HiGHS status 2).

Decomposition (different from the pilot's role-by-role skeleton DFS): (1) DFS over COUNT vectors c_(r,u) (12 classes),
classes in a fixed order, one helper added at a time; a prefix is pruned only if the LP with sum_v n_(r,u,v) >= c is
status 2 (a valid relaxation: final counts dominate prefixes) or if a count-level consequence of R4/R5 fails
(#r=3 helpers carry exactly a labels in total and at most a of them; #u=3 <= 1; #u=2 <= 3; u=3 present => no other u>=2);
(2) for every count vector whose EXACT LP is not status 2, search for a skeleton (label sets per helper) satisfying R4,
R5, R6 and (separately reported) (B-1) W_l <= 7.  Any such skeleton is a skeleton the pilot missed.
usage: t4_stepS.py "(h,y,F,'Mt',3,z)" a d"""
import sys, itertools, json, time
from collections import Counter
import rcheck

key = eval(sys.argv[1]); a = int(sys.argv[2]); d = int(sys.argv[3])
rows = rcheck.Rows(key, a, d)
CL = [(r, u) for r in range(4) for u in range(1, 4)]
present = [c for c in CL if c in rows.cls]
status = ['F'] * a + ['B'] * (3 - a - d) + ['D'] * d
lpstat = Counter(); nodes = 0; exact_feasible = []; t0 = time.time()


def struct_ok(c, final):
    n3 = sum(v for (r, u), v in c.items() if r == 3); A = sum(u * v for (r, u), v in c.items() if r == 3)
    if A > a or n3 > a: return False
    nu3 = sum(v for (r, u), v in c.items() if u == 3); nu2 = sum(v for (r, u), v in c.items() if u == 2)
    if nu3 > 1 or nu2 > 3 or (nu3 and nu2): return False
    if final and A != a: return False
    return True


def dfs(j, c):
    global nodes
    nodes += 1
    if struct_ok(c, True):
        st = rows.lp(dict(c), True); lpstat[('exact', st)] += 1
        if st != 2: exact_feasible.append(dict(c))
    for k in range(j, len(present)):
        c2 = Counter(c); c2[present[k]] += 1
        if not struct_ok(c2, False): continue
        st = rows.lp(dict(c2), False); lpstat[('mono', st)] += 1
        if st == 2: continue
        dfs(k, c2)


dfs(0, Counter())


def skeleton_exists(c):
    """label sets for the helpers of c satisfying R4, R5, R6; returns (with B-1, without B-1) examples or None."""
    helpers = sorted([(r, u) for (r, u), v in c.items() for _ in range(v)], key=lambda x: (-x[0], -x[1]))
    F = {s for s in range(3) if status[s] == 'F'}; D = {s for s in range(3) if status[s] == 'D'}
    sets = {u: [frozenset(L) for L in itertools.combinations(range(3), u)] for u in (1, 2, 3)}
    found = {'B1': None, 'noB1': None}

    def rec(i, chosen):
        if found['B1'] is not None: return
        if i == len(helpers):
            ok = True
            for s in range(3):
                full = sum(1 for (r, L) in chosen if r == 3 and s in L); anch = any(r >= 1 and s in L for r, L in chosen)
                if status[s] == 'F' and full != 1: ok = False
                if status[s] != 'F' and full: ok = False
                if status[s] == 'B' and not anch: ok = False
                if status[s] == 'D' and anch: ok = False
            if not ok: return
            W = [sum(r for r, L in chosen if s in L) for s in range(3)]
            ex = [(r, sorted(L)) for r, L in chosen]
            if found['noB1'] is None: found['noB1'] = ex
            if max(W) <= 7: found['B1'] = ex
            return
        r, u = helpers[i]
        for L in sets[u]:
            if r == 3 and not L <= F: continue
            if r >= 1 and L & D: continue
            if any(len(L & L2) >= 2 for _, L2 in chosen): continue
            # canonical within identical classes: non-decreasing label-set index
            if i > 0 and helpers[i - 1] == (r, u) and sorted(L) < sorted(chosen[-1][1]): continue
            rec(i + 1, chosen + [(r, L)])
    rec(0, [])
    return found


missed = []
for c in exact_feasible:
    f = skeleton_exists(c)
    if f['noB1'] is not None:
        missed.append(dict(counts={f'{r},{u}': v for (r, u), v in c.items()}, with_B1=f['B1'], without_B1=f['noB1']))
print(json.dumps(dict(key=list(key), a=a, d=d, classes_present=present, count_nodes=nodes, lp_status={str(k): v for k, v in lpstat.items()},
                      exact_feasible_count_vectors=len(exact_feasible), skeletons_found=missed[:5], n_missed=len(missed),
                      n_missed_with_B1=sum(1 for m in missed if m['with_B1']), seconds=round(time.time() - t0, 1))))
