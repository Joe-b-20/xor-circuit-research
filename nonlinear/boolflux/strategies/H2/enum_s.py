"""Enumerate bilinear spans S (dim k >= T, spanned by member bilinear parts) in real coordinates,
and report |members in S| statistics.  Saves the list of S (as member index lists) to a pickle."""
import itertools, pickle, sys, time
from h2lib import Basis
import relax as RX

k = int(sys.argv[1]) if len(sys.argv) > 1 else 10
out = sys.argv[2] if len(sys.argv) > 2 else None
t0 = time.time()
M = RX.all_members()
T = [RX.target_parts(1 << i, 0)[0] for i in range(8)]
TB = Basis()
for t in T: TB.add(t)
assert TB.n == 8
img = [TB.full_reduce(m[0])[0] for m in M]
print('members', len(M), 'in T:', sum(1 for i in img if i == 0), 'distinct images mod T:', len(set(img)), 'time', round(time.time() - t0, 1))
# span of all member bil parts
AB = Basis()
for m in M: AB.add(m[0])
print('dim span(member bil) =', AB.n, ' T inside:', all(AB.contains(t) for t in T))
pts = sorted(set(i for i in img if i))
e = k - 8
res = []
seen = set()
for combo in itertools.combinations(pts, e):
    Wsp = {0}; ok = True
    for r in combo:
        if r in Wsp: ok = False; break
        Wsp |= {s ^ r for s in Wsp}
    if not ok: continue
    key = frozenset(Wsp)
    if key in seen: continue
    seen.add(key)
    inside = [i for i, r in enumerate(img) if r in Wsp]
    S = Basis()
    for i in inside: S.add(M[i][0])
    if S.n == k and all(S.contains(t) for t in T):
        res.append(inside)
hist = {}
for r in res: hist[len(r)] = hist.get(len(r), 0) + 1
print('k =', k, 'spans:', len(res), 'members-in-S histogram:', dict(sorted(hist.items())), 'time', round(time.time() - t0, 1))
if out:
    pickle.dump({'k': k, 'S': res}, open(out, 'wb'))
