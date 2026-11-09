"""Exact push6 rows appended to the frozen push5 coefficient model.

New resource inequalities K<=base+c*p are combined mechanically with
proved upper budgets s*p-g(n)<=b for the repeated-bright color count p.
The original push5 row prefix is retained unchanged for certificate reuse.
"""
from fractions import Fraction
from functools import lru_cache
from math import gcd
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUSH5_MODEL = ROOT / 'push5/global_chronology/model_full_cuts.py'
spec = importlib.util.spec_from_file_location('frozen_push5_coefficients', PUSH5_MODEL)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)

G = prior.G
SOURCE = prior.SOURCE
EXCEPTIONAL_Q_MAX = prior.EXCEPTIONAL_Q_MAX
MODEL_VERSION = 'push6-core-rounded-overload-p-capacity-v4'


@lru_cache(maxsize=None)
def overload_breakpoints(q):
    """Positive coefficient/RHS breakpoints; the omitted initial row is 0<=p."""
    largest = max(4,q+2)
    return tuple(sorted({Fraction(a,d) for d in range(1,largest+1)
                         for a in range(1,d+1)}))


def system(key, include_new=True):
    types, rows, bounds, names = prior.system(key)
    if not include_new:
        return types, rows, bounds, names
    h, y, F_T, orientation, q, z = key
    C = 20 if orientation == 'M' else 28
    t = C//4
    x = G-32-h-y
    q_eff = q
    if orientation == 'Mt' and z <= 2:
        q_eff = q-1
    if orientation == 'Mt' and z == 0 and q <= EXCEPTIONAL_Q_MAX:
        q_eff = q-2
    # Only new rows are normalized/deduplicated.  Dividing by the gcd of
    # both coefficients AND RHS is exact over the reals; no extra rounding.
    new = {}
    def add(name, row, bound):
        common = gcd(abs(bound),*(abs(c) for c in row))
        if common > 1:
            row = [c//common for c in row]
            bound //= common
        if not any(row) and bound >= 0:
            return
        signature = tuple(row)
        if signature not in new or bound < new[signature][0]:
            new[signature] = (bound,'push6 '+name+' <=')
    def vector(fn):
        return [fn(r,u,v) for r,u,v in types]
    U = vector(lambda r,u,v: u if r >= 2 else 0)
    Erep = vector(lambda r,u,v: max(0,r-1))
    Cost = vector(lambda r,u,v: int(r == 2)+5*int(r == 3))
    A = vector(lambda r,u,v: u if r == 3 else 0)
    Q = vector(lambda r,u,v: max(0,r-1)*u+(max(0,u-2) if r == 3 else 0))
    # A budget tuple denotes s*p-g(n)<=b.
    budgets = [('fixed repeated-color capacity',1,[0]*len(types),q_eff)]
    if orientation == 'Mt':
        h0 = vector(lambda r,u,v: int(r == 0))
        h00 = vector(lambda r,u,v: int(r == 0 and u == 0))
        V0_minus_h00 = vector(lambda r,u,v: v-int(u == 0) if r == 0 else 0)
        D2 = vector(lambda r,u,v: (2*v-2 if u == 0 else v+min(v,q-u)) if r == 0 else 0)
        budgets += [
            ('unanchored helper capacity',1,h0,q-1),
            ('HH unanchored incidence deficiency',3,V0_minus_h00,3*(q-1)),
            ('HH edge deficiency',3,[-c for c in h00],3*(q-1)+z),
            ('HH label matching deficiency',6,D2,6*(q-1)),
        ]
        if q <= 6 or y <= 3:
            twice_h0_plus_W = vector(lambda r,u,v: 2*int(r == 0)+(v if r in (1,2) else 0))
            budgets.append(('small palette anchored full HH',1,twice_h0_plus_W,q-2))
    # A resource tuple denotes K(n)<=base+c*p.
    resources = [
        ('repeated contact core ownership',[a+b for a,b in zip(Erep,U)],C,1),
        ('repeated contact OO three halves',[2*a+3*b for a,b in zip(Cost,U)],2*x+2*C,3),
        ('repeated contact OO full colors',[a+2*b+c for a,b,c in zip(Cost,U,A)],x+C,3),
    ]
    if orientation == 'Mt':
        resources += [('full contacts',A,0,1),('weighted excess',Q,0,3)]
    for ratio in overload_breakpoints(q):
        a,d = ratio.numerator,ratio.denominator
        coeff = vector(lambda r,u,v,a=a,d=d: (a*(r-1+u))//d if r >= 2 else 0)
        resources.append(('class overload ratio '+str(a)+'/'+str(d),coeff,t*((4*a)//d),1))
    for resource,K,base,c in resources:
        for budget,s,g,b in budgets:
            add(resource+' / '+budget,[s*k-c*gg for k,gg in zip(K,g)],s*base+c*b)
    # Floor in each class subset, average over all subsets, then use the
    # integer total.  Here p is replaced only by its constant upper bound.
    for d in range(2,q+3):
        cap = min((t*((4*k+q_eff)//d))//k for k in range(1,t+1))
        coeff = vector(lambda r,u,v,d=d: (r-1+u)//d if r >= 2 else 0)
        add('rounded class core divisor '+str(d),coeff,cap)
    for signature,(bound,name) in new.items():
        rows.append(list(signature))
        bounds.append(bound)
        names.append(name)
    return types, rows, bounds, names


def direct_exclusion(key):
    return prior.direct_exclusion(key)


def scalar_states():
    yield from prior.scalar_states()
