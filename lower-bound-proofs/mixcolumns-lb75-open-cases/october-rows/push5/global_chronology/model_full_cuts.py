"""Exact integer coefficient model for the new globally valid cuts.

The inherited coefficient generator is loaded unchanged.  No numerical
dependency is imported here, so proof checking can use the standard library.
"""
import importlib.util
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "push5/sources/xor/AES_MixColumns_Lower_Bound_75/research_deep/root/certify75.py"
spec = importlib.util.spec_from_file_location("inherited_certify75_coefficients", SOURCE)
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

G = 75
EXCEPTIONAL_Q_MAX = 6


def system(key, include_new=True):
    h, y, F, ori, q, z = key
    types, A, B, names = old.system(key)
    if not include_new:
        return types, A, B, names
    # Each actual H--H edge contributes at most one incidence to a given
    # helper: there are no loops.  Consequently every helper has v<=z.
    # Retain the inherited type list unchanged and force impossible types
    # to have zero count, for transparent exact coefficient comparison.
    A.append([int(v > z) for r,u,v in types])
    B.append(0)
    names.append("new HH degree realizability <=")
    x = G-32-h-y
    classes = 5 if ori == "M" else 7
    cap = min(2*classes, (x+4*classes)//5)
    A.append([int(r == 3) for r,u,v in types])
    B.append(cap)
    names.append("new full helper chronological cap <=")
    A.append([int(r == 3) for r,u,v in types])
    B.append((G-32-h-q)//3)
    names.append("new full helper distinct represented labels <=")
    A.append([int(r == 2)+5*int(r == 3) for r,u,v in types])
    B.append(x+4*classes)
    names.append("new repeated helper joint birth ownership <=")
    if ori == "Mt":
        # h0 counts helpers with no represented H--B incidence.  If h0=0,
        # all helpers have three-boundary-form pivots, so every HH equation
        # is short when no missing color is exceptional.  Rank(R10)=29 then
        # forces at least one exceptional color, for any z.  For h0>=1 the
        # rows are already implied by the inherited missing-color budgets.
        A.append([(u if r == 3 else 0)-int(r == 0) for r,u,v in types])
        B.append(q-1)
        names.append("new transpose full missing unanchored coupling <=")
        A.append([max(0,r-1)*u + (max(0,u-2) if r == 3 else 0)-3*int(r == 0) for r,u,v in types])
        B.append(3*(q-1))
        names.append("new transpose weighted excess unanchored coupling <=")
    if ori == "Mt" and z == 0:
        exceptional = 2 if q <= EXCEPTIONAL_Q_MAX else 1
        A.append([u if r == 3 else 0 for r,u,v in types])
        B.append(q-exceptional)
        names.append("new transpose full missing exceptional colors <=")
        A.append([max(0,r-1)*u + (max(0,u-2) if r == 3 else 0) for r,u,v in types])
        B.append(3*(q-exceptional))
        names.append("new transpose weighted excess exceptional colors <=")
    return types, A, B, names


def direct_exclusion(key):
    return old.direct_exclusion(key)


def scalar_states():
    for a in range(24, G-44):
        for Y in range(G-31-a):
            he = G-32-a-Y
            for b in range(24, G-31):
                for V in range(Y+1):
                    ho = G-32-b-V
                    if ho < 0 or ho+Y < 13:
                        continue
                    Se = min(3*he+2*V+Y-32,2*b-a+G-96+V)
                    So = min(3*ho+2*Y+V-32,2*a-b+G-96+Y)
                    if min(Se,So) < 0:
                        continue
                    def low(h,y):
                        return next(s for s in range(65) if 2*h+y+max(s,comb(s,2)) >= 32)
                    le,lo = low(he,Y),low(ho,V)
                    budget = a+b+2*G-192
                    if le <= Se and lo <= So and le+lo <= budget:
                        yield (a,b,Y,V,he,ho,le,lo,Se,So,budget)
