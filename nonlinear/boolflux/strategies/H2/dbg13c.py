import os
from h2lib import Basis
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/d13/')
L = open(D + 'ad5-g14.txt.img').read().split('\n')
n, q = map(int, L[0].split())
im = [int(a, 16) << 64 | int(b, 16) for a, b in (l.split() for l in L[1:1 + n])]
A = [971, 962, 716, 30, 1076, 1007, 1175, 806, 1106, 115, 1250, 415, 250]
B = Basis()
for i in A: B.add(im[i])
print('rank of A28 images mod T_full:', B.n, 'distinct', len(set(im[i] for i in A)))
print([hex(im[i]) for i in A][:4])
