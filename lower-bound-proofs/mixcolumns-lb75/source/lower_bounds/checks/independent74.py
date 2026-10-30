#!/usr/bin/env python3
"""Independent exact check of all G=73 steady-orbit certificates.

This file imports no research model or certificate builder. It reconstructs
the scalar domain, evaluates each weighted helper coefficient directly,
and proves complete coverage of the claimed lower s bounds.
"""
from pathlib import Path
import json


def choose2(n):
    return n*(n-1)//2


def min_s(h, y):
    # Exhaust actual q,z allocations instead of invoking the convex envelope.
    for s in range(65):
        if any(2*h+y+(s-q)+choose2(q) >= 32 for q in range(s+1)):
            return s
    raise AssertionError('No s found')


def domain():
    out = set()
    for a in range(24, 29):
        for b in range(24, 42):
            for Y in range(42-a):
                h_even = 41-a-Y
                for Z in range(min(Y, 41-b)+1):
                    h_odd = 41-b-Z
                    if h_odd+Y < 13:
                        continue
                    cap_even = 3*h_even+2*Z+Y-32
                    cap_odd = 3*h_odd+2*Y+Z-32
                    if cap_even < 0 or cap_odd < 0:
                        continue
                    least_even, least_odd = min_s(h_even, Y), min_s(h_odd, Z)
                    budget = a+b-46
                    if least_even > cap_even or least_odd > cap_odd:
                        continue
                    if least_even+least_odd > budget:
                        continue
                    out.add((a,b,Y,Z,h_even,h_odd,least_even,least_odd,
                             cap_even,cap_odd,budget))
    return out


def local_check(key, weights):
    h, y, F, orientation, q, z = key
    assert orientation in ('M', 'Mt')
    assert all(type(v) is int and v >= 0 for v in (h,y,F,q,z))
    assert len(weights) == 15
    assert all(type(w) is int and w >= 0 for w in weights)
    w = weights
    checked = 0
    for r in range(4):
        for u in range(q+1):
            # A simple graph has at most h-1 helper neighbors per helper.
            for v in range(min(2*z, max(0,h-1))+1):
                degree = r+u+v
                if degree < 2:
                    continue
                f = max(0, (degree-3)//2)
                full = int(r == 3)
                excess = max(0, r-1)
                coefficient = (
                    w[0]-w[1] + (w[2]-w[3])*degree + (w[4]-w[5])*v
                    + w[6]*f + w[7]*choose2(u) + w[8]*full*u
                    + w[9]*r*u + w[10]*full*(1+2*f)
                    + w[11]*excess*u + w[12]*(u+2*f)
                    + w[13]*full*(u+v) + w[14]*excess)
                assert coefficient >= 0, (key,r,u,v,coefficient)
                checked += 1
    degree_sum = 32+h-y+q+z
    reverse_slack = 3*h+2*F+y-32
    rho6 = 20 if orientation == 'M' else 28
    rhs = ((w[0]-w[1])*h + (w[2]-w[3])*degree_sum
           + (w[4]-w[5])*2*z + w[6]*F + w[7]*choose2(q)
           + w[8]*q + w[9]*7*q + w[10]*reverse_slack
           + w[11]*3*q + w[12]*(4*q+2*F)
           + w[13]*(q+z) + w[14]*rho6)
    assert rhs < 0, (key, rhs)
    return checked, rhs


def main():
    path = Path(__file__).with_name('CERTIFICATES74.json')   # flat layout of lower_bounds/checks (original: ../root/)
    data = json.loads(path.read_text())
    assert data['gates_excluded'] == 73
    certs = {}
    coefficients = 0
    right_sides = []
    for entry in data['certificates']:
        key = tuple(entry['key'])
        assert key not in certs
        count, rhs = local_check(key, entry['weights'])
        certs[key] = entry['weights']
        coefficients += count
        right_sides.append(rhs)
    expected = {(state, orientation) for state in domain()
                for orientation in ('M', 'Mt')}
    seen = set()
    referenced_keys = set()
    references = 0
    for claim in data['claims']:
        state, orientation = tuple(claim['state']), claim['orientation']
        item = (state, orientation)
        assert item in expected and item not in seen
        seen.add(item)
        a,b,Y,Z,he,ho,le,lo,Se,So,budget = state
        k,l = claim['lower_even'], claim['lower_odd']
        assert type(k) is int and type(l) is int
        assert le <= k <= Se+1 and lo <= l <= So+1
        other = 'Mt' if orientation == 'M' else 'M'
        for h,y,F,ori,low,cap,claimed in ((he,Y,Z,orientation,le,Se,k),
                                         (ho,Z,Y,other,lo,So,l)):
            # Each s below the claimed lower bound is fully excluded:
            # either the old incidence inequality fails for a q,z allocation,
            # or its entire helper-type relaxation has an exact certificate.
            for s in range(low, min(cap, claimed-1)+1):
                for z in range(s+1):
                    q = s-z
                    if 2*h+y+z+choose2(q) < 32:
                        continue
                    key = (h,y,F,ori,q,z)
                    assert key in certs, ('uncovered', item, key)
                    referenced_keys.add(key)
                    references += 1
        assert k > Se or l > So or k+l > budget
    assert seen == expected
    result = dict(gates_excluded=73, scalar_states=len(domain()),
                  oriented_claims=len(seen), local_certificates=len(certs),
                  independently_checked_coefficients=coefficients,
                  largest_right_side=max(right_sides),
                  certificate_references=references,
                  distinct_referenced_certificates=len(referenced_keys),
                  all_checks_passed=True)
    assert result['scalar_states'] == 262
    assert result['oriented_claims'] == 524
    assert result['local_certificates'] == 484
    assert result['independently_checked_coefficients'] == 13819
    assert result['largest_right_side'] == -1
    Path(__file__).with_name('INDEPENDENT74.json').write_text(
        json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
