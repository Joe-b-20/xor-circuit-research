#!/usr/bin/env python3
"""Independent exact G=74 exclusion coverage and coefficient checks.

No model/builder imports. Scalar ranges, direct geometric exclusions,
helper coefficients, and all coverage obligations are rebuilt here.
Mathematical premises are reviewed in AUDIT75.md and the cited audits.
"""
from pathlib import Path
from functools import lru_cache
import json


def c2(x):
    return x*(x-1)//2


@lru_cache(None)
def least_s(h, y):
    for s in range(65):
        if any(2*h+y+(s-q)+c2(q) >= 32 for q in range(s+1)):
            return s
    raise AssertionError


def scalar_domain():
    states = set()
    for a in range(24, 30):
        for b in range(24, 43):
            for Y in range(43-a):
                ha = 42-a-Y
                for Z in range(min(Y, 42-b)+1):
                    hb = 42-b-Z
                    if hb+Y < 13:
                        continue
                    Sa = min(3*ha+2*Z+Y-32, 2*b-a-22+Z)
                    Sb = min(3*hb+2*Y+Z-32, 2*a-b-22+Y)
                    if Sa < 0 or Sb < 0:
                        continue
                    la, lb = least_s(ha, Y), least_s(hb, Z)
                    budget = a+b-44
                    if la <= Sa and lb <= Sb and la+lb <= budget:
                        states.add((a,b,Y,Z,ha,hb,la,lb,Sa,Sb,budget))
    return states


def weighted_certificate(key, weights):
    h,y,F,ori,q,z = key
    assert ori in ('M', 'Mt')
    assert all(type(v) is int and v >= 0 for v in (h,y,F,q,z))
    assert all(type(w) is int and w >= 0 for w in weights)
    rho = 20 if ori == 'M' else 28
    reserve = 8 if ori == 'M' else 4
    total_degree = 32+h-y+q+z
    rhs = [h,-h,total_degree,-total_degree,2*z,-2*z,
           F,c2(q),q,7*q,3*h+2*F+y-32,3*q,4*q+2*F,q+z,rho,
           2*y+2*z+7*q-2*reserve,
           2*y+2*z+7*q-2*reserve+(2 if ori == 'M' else 0),
           y+z+3*q-reserve,
           3*q]
    if ori == 'M':
        rhs.append(3*y+3*z+6*q-24)
    else:
        rhs += [3*y+3*z+3*q-12, 3*y+3*z+7*q-12,
                y-3, 3*y+2*z-9]
        if q == 0:
            rhs += [-1,y-3]
    if q == 6:
        rhs.append(4)
    if q == 7:
        rhs.append(14)
    assert len(weights) == len(rhs), (key,len(weights),len(rhs))
    weighted_rhs = sum(w*b for w,b in zip(weights,rhs))
    assert weighted_rhs < 0, (key,weighted_rhs)
    count = 0
    minimum = None
    for r in range(4):
        for u in range(q+1):
            for v in range(min(2*z,max(0,h-1))+1):
                degree = r+u+v
                if degree < 3:
                    continue
                f = max(0,(degree-3)//2)
                full = int(r == 3)
                excess = max(0,r-1)
                deficit = (u-1)*int(r == 0)
                overflow = max(0,u-2)*full
                row = [1,-1,degree,-degree,v,-v,
                       f,c2(u),full*u,r*u,full*(1+2*f),excess*u,
                       u+2*f,full*(u+v),excess,
                       r*u-2*deficit,r*u+full*u-2*deficit,
                       excess*u-deficit,excess*u+overflow]
                if ori == 'M':
                    row.append(2*excess*u+2*overflow-3*deficit)
                else:
                    row += [excess*u+overflow-3*deficit,
                            r*u+full*u-3*deficit,
                            -(u+v-1)*int(r==0)-v*int(r==1),
                            -(3*u+v-3)*int(r==0)]
                    if q == 0:
                        row += [-int(r==0),-(v-1)*int(r==0)]
                if q == 6:
                    row.append((0,0,0,1,3,4,4)[u])
                if q == 7:
                    row.append((0,0,0,2,7,12,14,14)[u])
                assert len(row) == len(weights)
                coefficient = sum(w*c for w,c in zip(weights,row))
                assert coefficient >= 0, (key,r,u,v,coefficient)
                minimum = coefficient if minimum is None else min(minimum,coefficient)
                count += 1
    return count, weighted_rhs


def geometric_exclusion(key):
    _,_,_,ori,q,z = key
    if q != 0:
        return False
    return z == 0 or (ori == 'Mt' and z <= 7)


def main():
    source = Path(__file__).with_name('CERTIFICATES75.json')   # flat layout of lower_bounds/checks (original: ../root/)
    data = json.loads(source.read_text())
    assert data['gates_excluded'] == 74
    certificates = set()
    coefficients = 0
    rhs_values = []
    for entry in data['certificates']:
        key = tuple(entry['key'])
        assert key not in certificates
        count,rhs = weighted_certificate(key,entry['weights'])
        coefficients += count
        rhs_values.append(rhs)
        certificates.add(key)
    states = scalar_domain()
    expected = {(s,o) for s in states for o in ('M','Mt')}
    seen = set()
    references = 0
    direct_count = 0
    distinct_used = set()
    for claim in data['claims']:
        s,ori = tuple(claim['state']),claim['orientation']
        identity = s,ori
        assert identity in expected and identity not in seen
        seen.add(identity)
        a,b,Y,Z,ha,hb,la,lb,Sa,Sb,budget = s
        k,l = claim['lower_even'],claim['lower_odd']
        assert type(k) is int and type(l) is int
        assert la <= k <= Sa+1 and lb <= l <= Sb+1
        other = 'Mt' if ori == 'M' else 'M'
        for h,y,F,o,low,cap,bound in ((ha,Y,Z,ori,la,Sa,k),
                                    (hb,Z,Y,other,lb,Sb,l)):
            for total in range(low,min(cap,bound-1)+1):
                for z in range(total+1):
                    q = total-z
                    if 2*h+y+z+c2(q) < 32:
                        continue
                    key = h,y,F,o,q,z
                    if geometric_exclusion(key):
                        direct_count += 1
                        continue
                    assert key in certificates, ('uncovered',identity,key)
                    references += 1
                    distinct_used.add(key)
        assert k > Sa or l > Sb or k+l > budget
    assert seen == expected
    result = dict(gates_excluded=74, scalar_states=len(states),
                  oriented_claims=len(seen), local_certificates=len(certificates),
                  helper_type_coefficients=coefficients,
                  largest_right_side=max(rhs_values),
                  certificate_references=references,
                  distinct_referenced_certificates=len(distinct_used),
                  direct_geometric_references=direct_count,
                  all_checks_passed=True)
    assert result['scalar_states'] == 1102
    assert result['oriented_claims'] == 2204
    assert result['local_certificates'] == 4057
    assert result['helper_type_coefficients'] == 163599
    assert result['certificate_references'] == 9604
    assert result['largest_right_side'] == -1
    Path(__file__).with_name('INDEPENDENT75.json').write_text(
        json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
