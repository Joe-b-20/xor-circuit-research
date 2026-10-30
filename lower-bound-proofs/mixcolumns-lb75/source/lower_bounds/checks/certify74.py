"""Exact local certificates and complete steady-orbit coverage for G=73.

Default checking uses only Python's standard library. --generate uses
SciPy to find Farkas multipliers, which are then checked exactly.
"""
from fractions import Fraction
from itertools import product
from math import comb, lcm, gcd
from pathlib import Path
import argparse
import json

OUT=Path(__file__).with_name('CERTIFICATES74.json')


def scalar_states():
    G=73
    for a in range(24,G-44):
        for Y in range(G-31-a):
            he=G-32-a-Y
            for b in range(24,G-31):
                for V in range(Y+1):
                    ho=G-32-b-V
                    if ho<0 or ho+Y<13:continue
                    Se,So=3*he+2*V+Y-32,3*ho+2*Y+V-32
                    if min(Se,So)<0:continue
                    def low(h,y):
                        return next(s for s in range(65)
                            if 2*h+y+max(s,comb(s,2))>=32)
                    le,lo=low(he,Y),low(ho,V)
                    budget=a+b+2*G-192
                    if le<=Se and lo<=So and le+lo<=budget:
                        yield a,b,Y,V,he,ho,le,lo,Se,So,budget


def system(key):
    h,y,F,orientation,q,z=key
    S=3*h+2*F+y-32
    types=[(r,u,v)for r in range(4)for u in range(q+1)
           for v in range(min(2*z,max(0,h-1))+1)if r+u+v>=2]
    A=[];B=[];names=[]
    def add(name,fn,b,equality=False):
        row=[fn(r,u,v)for r,u,v in types]
        A.append(row);B.append(b);names.append(name+' <=')
        if equality:
            A.append([-v for v in row]);B.append(-b);names.append(name+' >=')
    def f(r,u,v):return max(0,(r+u+v-3)//2)
    add('helper count',lambda r,u,v:1,h,True)
    add('helper degree',lambda r,u,v:r+u+v,32+h-y+q+z,True)
    add('HH incidence',lambda r,u,v:v,2*z,True)
    add('reverse EE budget',f,F)
    add('missing pairs',lambda r,u,v:comb(u,2),comb(q,2))
    add('full missing incidence',lambda r,u,v:u if r==3 else 0,q)
    add('label rank capacity',lambda r,u,v:r*u,7*q)
    add('full helper budget',lambda r,u,v:1+2*f(r,u,v)if r==3 else 0,S)
    add('weighted label capacity',lambda r,u,v:max(0,r-1)*u,3*q)
    add('even signal fanout',lambda r,u,v:u+2*f(r,u,v),4*q+2*F)
    add('full helper incidence',lambda r,u,v:u+v if r==3 else 0,q+z)
    add('boundary R6 rank',lambda r,u,v:max(0,r-1),20 if orientation=='M'else 28)
    return types,A,B,names


def check_certificate(key,weights):
    types,A,B,names=system(key)
    assert len(weights)==len(A)
    assert all(type(v)is int and v>=0 for v in weights)
    lhs=[sum(w*row[j]for w,row in zip(weights,A))for j in range(len(types))]
    rhs=sum(w*b for w,b in zip(weights,B))
    assert all(c>=0 for c in lhs)and rhs<0,(key,rhs,min(lhs,default=0))
    return {'columns':len(types),'rhs':rhs,
            'used_rows':[name for name,w in zip(names,weights)if w]}


def generate():
    import numpy as np
    from scipy.optimize import linprog
    certificates={};feasible=set();claims=[]
    def solve(key):
        k=tuple(key)
        if k in certificates:return False
        if k in feasible:return True
        types,A,B,names=system(k)
        AA=np.array(A,float)
        # Nonnegative multipliers give nonnegative variable coefficients.
        res=linprog(np.zeros(len(A)),A_ub=-AA.T if types else None,
                    b_ub=np.zeros(len(types))if types else None,
                    A_eq=np.array([B],float),b_eq=[-1],bounds=(0,None),method='highs')
        if res.status==2:
            feasible.add(k);return True
        assert res.success,(key,res.message)
        ws=[Fraction(float(w)).limit_denominator(10**7)for w in res.x]
        scale=lcm(*(w.denominator for w in ws))
        ints=[int(w*scale)for w in ws]
        common=gcd(*ints)
        ints=[w//common for w in ints]
        check_certificate(k,ints)
        certificates[k]=ints
        return False
    def first_possible(h,y,F,ori,least,greatest):
        for s in range(least,greatest+1):
            for q in range(s+1):
                z=s-q
                if 2*h+y+z+comb(q,2)<32:continue
                if solve((h,y,F,ori,q,z)):return s
        return greatest+1
    states=list(scalar_states())
    for state in states:
        a,b,Y,V,he,ho,le,lo,Se,So,budget=state
        for ori,other in [('M','Mt'),('Mt','M')]:
            k=first_possible(he,Y,V,ori,le,min(Se,budget-lo))
            ell=lo
            if k<=Se and k+ell<=budget:
                ell=first_possible(ho,V,Y,other,lo,min(So,budget-k))
            assert k>Se or ell>So or k+ell>budget,(state,ori,k,ell)
            claims.append({'state':list(state),'orientation':ori,'lower_even':k,'lower_odd':ell})
    result={'gates_excluded':73,'claims':claims,
            'certificates':[{'key':list(key),'weights':ws}for key,ws in sorted(certificates.items())]}
    OUT.write_text(json.dumps(result,indent=2)+'\n')
    return result


def verify(data):
    assert data['gates_excluded']==73
    certificates={};columns=0;max_rhs=None;used_rows=set()
    for entry in data['certificates']:
        key=tuple(entry['key']);assert key not in certificates
        report=check_certificate(key,entry['weights'])
        columns+=report['columns'];used_rows.update(report['used_rows'])
        max_rhs=report['rhs']if max_rhs is None else max(max_rhs,report['rhs'])
        certificates[key]=entry['weights']
    states=list(scalar_states())
    expected={(state,ori)for state in states for ori in ('M','Mt')}
    seen=set();references=0
    def check_lower(h,y,F,ori,least,greatest,claimed):
        nonlocal references
        assert type(claimed)is int and least<=claimed<=greatest+1
        for s in range(least,min(claimed-1,greatest)+1):
            for q in range(s+1):
                z=s-q
                if 2*h+y+z+comb(q,2)<32:continue
                key=(h,y,F,ori,q,z)
                assert key in certificates,('missing local certificate',key)
                references+=1
    for claim in data['claims']:
        state=tuple(claim['state']);ori=claim['orientation'];identity=(state,ori)
        assert identity in expected and identity not in seen
        seen.add(identity)
        a,b,Y,V,he,ho,le,lo,Se,So,budget=state
        k,ell=claim['lower_even'],claim['lower_odd']
        check_lower(he,Y,V,ori,le,Se,k)
        check_lower(ho,V,Y,'Mt'if ori=='M'else'M',lo,So,ell)
        assert k>Se or ell>So or k+ell>budget
    assert seen==expected
    result={'scalar_states':len(states),'oriented_claims':len(seen),
            'local_certificates':len(certificates),'scalar_coefficients_checked':columns,
            'certificate_references':references,'largest_rhs':max_rhs,
            'used_rows':sorted(used_rows),'all_checks_passed':True}
    Path(__file__).with_name('VERIFIED74.json').write_text(json.dumps(result,indent=2)+'\n')
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--generate',action='store_true');args=p.parse_args()
    data=generate()if args.generate else json.loads(OUT.read_text())
    print(json.dumps(verify(data),indent=2))
