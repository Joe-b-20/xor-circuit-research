import sys, os
sys.argv = ['vd13.py', os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/d13/ad5-g14'), '0']
src = open('vd13.py').read().split("sys.path.insert(0, str(Path(__file__)")[0]
exec(src)
A = [971, 962, 716, 30, 1076, 1007, 1175, 806, 1106, 115, 1250, 415, 250]
ALL = [30, 115, 250, 340, 415, 671, 716, 806, 811, 856, 961, 962, 971, 972, 1007, 1076, 1106, 1175, 1250]
print('A28 covers', covers(A), 'all19 covers', covers(ALL), 'sol3', covers(sols[3]))
# rank of member tables mod free
Bq = FB.copy(); r0 = Bq.n
for i in A: Bq.add(mtab(i))
print('rank A28 mod free', Bq.n - r0)
Bq = FB.copy()
for i in sols[3]: Bq.add(mtab(i))
print('rank sol3 mod free', Bq.n - r0, [Bq.contains(t) for t in T])
