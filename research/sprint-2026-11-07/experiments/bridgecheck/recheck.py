#!/usr/bin/env python3
"""Adversarial re-check of bridge/REPORT.md (F17).

Own reconstruction (value set -> gate list, full acyclic enumeration, no levelling heuristic),
own scalar/type computation, then the package's own Circuit.analyse / canonical_transpose / check_rows
on 40 circuits; comparison with bridge/profiles.json; period-2 test on circuits (not just profiles);
identity (E) and the two-phase margin identity; row slacks.
Writes bridgecheck/recheck.json and prints a log.
"""
import sys, json, re, time, random, itertools
from collections import Counter, defaultdict
from math import comb

HOME = '/home/joebachir20'
SPRINT = HOME + '/xs-campaigns/2026-11-07-sprint'
OUT = SPRINT + '/bridgecheck'
PKG = SPRINT + '/lb76/pkg_copy/source/lower_bounds/checks'
sys.path.insert(0, PKG)
import stress
from stress import Circuit, check_rows, ROWS, COLS, parity, TARGETS

INPUTS = [1 << i for i in range(32)]
ROWSET = set(ROWS)
pc = lambda v: bin(v).count('1')

# ------------------------------------------------------------------ own reconstruction
def all_pairs(v, sig):
    out = []
    for a in sig:
        b = a ^ v
        if b in sig and a < b:
            out.append((a, b))
    return out


def reconstructions(values, cap=2000):
    """Enumerate ALL acyclic parent assignments of the value set (every value is a gate; inputs are free).
    Returns list of assignments (dict value -> (a,b)), truncated at cap, plus per-value pair counts."""
    sig = set(INPUTS) | set(values)
    assert len(sig) == 32 + len(values), 'duplicate value or value equal to an input'
    P = {v: all_pairs(v, sig) for v in values}
    for v in values:
        assert P[v], 'value %x has no parent pair' % v
    vset = set(values)
    # sound pruning: dep[v] = least fixpoint of "values v depends on under EVERY remaining pair choice";
    # a pair (a,b) of v is impossible if a or b necessarily depends on v. Iterate until stable.
    changed = True
    while changed:
        changed = False
        dep = {v: set() for v in values}
        upd = True
        while upd:
            upd = False
            for v in values:
                sets = []
                for (a, b) in P[v]:
                    s = set()
                    for p in (a, b):
                        if p in vset:
                            s.add(p)
                            s |= dep[p]
                    sets.append(s)
                new = set.intersection(*sets) if sets else set()
                if new != dep[v]:
                    dep[v] = new
                    upd = True
        for v in values:
            keep = [(a, b) for (a, b) in P[v] if not any(p in vset and v in dep[p] for p in (a, b))]
            assert keep, 'no acyclic pair left for %x' % v
            if len(keep) < len(P[v]):
                P[v] = keep
                changed = True
    amb = [v for v in values if len(P[v]) > 1]
    fixed = {v: P[v][0] for v in values if len(P[v]) == 1}

    def reaches(src, dst, choice):
        """does dst depend on src under the partial assignment (src an ancestor of dst)?"""
        seen = set()
        stack = [dst]
        while stack:
            w = stack.pop()
            if w == src:
                return True
            if w in seen or w not in choice:
                continue
            seen.add(w)
            for p in choice[w]:
                if p in vset:
                    stack.append(p)
        return False

    # prune: a pair (a,b) for v is impossible if a or b already (through fixed choices) depends on v
    results = []
    amb.sort(key=lambda v: len(P[v]))

    def rec(i, choice):
        if len(results) >= cap:
            return
        if i == len(amb):
            results.append(dict(choice))
            return
        v = amb[i]
        for (a, b) in P[v]:
            if (a in vset and reaches(v, a, choice)) or (b in vset and reaches(v, b, choice)):
                continue
            choice[v] = (a, b)
            rec(i + 1, choice)
            del choice[v]

    rec(0, dict(fixed))
    # final acyclicity sanity (full Kahn) on each result
    for choice in results:
        indeg = {v: 0 for v in values}
        users = defaultdict(list)
        for v, (a, b) in choice.items():
            for p in (a, b):
                if p in indeg:
                    indeg[v] += 1
                    users[p].append(v)
        ready = [v for v in values if indeg[v] == 0]
        n = 0
        while ready:
            v = ready.pop()
            n += 1
            for w in users[v]:
                indeg[w] -= 1
                if indeg[w] == 0:
                    ready.append(w)
        assert n == len(values), 'cyclic reconstruction slipped through'
    return results, P, amb


def topo_gates(values, choice):
    """gate list over indices (inputs 0..31) in a topological order: by (depth, mask)."""
    depth = {m: 0 for m in INPUTS}

    def dep(v):
        if v in depth:
            return depth[v]
        a, b = choice[v]
        depth[v] = 1 + max(dep(a), dep(b))
        return depth[v]

    for v in values:
        dep(v)
    order = sorted(values, key=lambda v: (depth[v], v))
    idx = {m: i for i, m in enumerate(INPUTS)}
    gates = []
    for v in order:
        a, b = choice[v]
        idx[v] = 32 + len(gates)
        gates.append((idx[a], idx[b]))
    return gates, order


def levelled_ambiguity(values):
    """the bridge's notion: min-level rounds, admissible pair = both parents of strictly lower min-level."""
    lev = {m: 0 for m in INPUTS}
    pending = set(values)
    L = 0
    while pending:
        new = [v for v in pending if any((a ^ v) in lev and (a ^ v) != a for a in lev)]
        assert new
        L += 1
        for v in new:
            lev[v] = L
        pending -= set(new)
    nmulti = 0
    for v in values:
        cs = [(a, a ^ v) for a in lev if (a ^ v) in lev and a < (a ^ v) and lev[a] < lev[v] and lev[a ^ v] < lev[v]]
        if len(cs) > 1:
            nmulti += 1
    return nmulti


def yx_of(choice):
    y = sum(1 for v, (a, b) in choice.items() if not parity(a) and not parity(b))
    x = sum(1 for v, (a, b) in choice.items() if parity(a) and parity(b))
    return y, x


# ------------------------------------------------------------------ own scalar / type computation
def own_profile(gates, ori):
    """x, y, h, q, z, E_B, L_H-free quantities and helper types computed from scratch (no stress.py)."""
    n = 32 + len(gates)
    mask = [1 << i for i in range(32)] + [0] * len(gates)
    for k, (a, b) in enumerate(gates):
        mask[32 + k] = mask[a] ^ mask[b]
    tgt = TARGETS[ori]
    where = {m: i for i, m in enumerate(mask)}
    outs = {where[t] for t in tgt}
    odd = [pc(m) & 1 for m in mask]
    uses = [0] * n
    for a, b in gates:
        uses[a] += 1
        uses[b] += 1
    d = [uses[v] + (1 if v in outs else 0) for v in range(n)]
    B = set(range(32)) | outs
    H = [v for v in range(32, n) if odd[v] and v not in outs]
    x = y = 0
    edges = []  # (p, q, label)
    for k, (a, b) in enumerate(gates):
        s = 32 + k
        if odd[a] and odd[b]:
            x += 1
            edges.append((a, b, s))
        elif not odd[a] and not odd[b]:
            y += 1
        else:
            o, e = (a, b) if odd[a] else (b, a)
            edges.append((o, s, e))
    evens = [v for v in range(32, n) if not odd[v]]
    rep = set()
    for p, q, l in edges:
        if p in B and q in B:
            rep.add(l)
    qmiss = len(evens) - len(rep)
    z = sum(1 for p, q, l in edges if p not in B and q not in B)
    types = Counter()
    for v in H:
        r = u = vv = 0
        for p, q, l in edges:
            if v not in (p, q):
                continue
            w = q if p == v else p
            if w in B:
                if l in rep:
                    r += 1
                else:
                    u += 1
            else:
                vv += 1
        types[(r, u, vv)] += 1
    E_B = sum(max(0, d[v] - 2) for v in B)
    return dict(x=x, y=y, h=len(H), q=qmiss, z=z, s=qmiss + z, E_B=E_B, types=types,
                hdeg_min=min((r + u + v for (r, u, v) in types), default=99),
                w2=sum(1 for v in evens if pc(mask[v]) == 2),
                w2_rep=sum(1 for v in evens if pc(mask[v]) == 2 and v in rep),
                masks=mask)


def eqset(C):
    return frozenset(frozenset((C.mask[a], C.mask[b], C.mask[32 + k])) for k, (a, b) in enumerate(C.gates))


def orbit(gates, steps=6, rng_seed=None):
    C = Circuit(gates, 'M')
    recs = []
    circs = []
    for step in range(steps):
        I = C.analyse()
        rows = check_rows(I, C.ori)
        own = own_profile(C.gates, C.ori)
        # cross-check own vs package
        for k in ('x', 'y', 'h', 'q', 'z', 's', 'E_B'):
            assert own[k] == I[k], ('own != package', step, k, own[k], I[k])
        assert own['types'] == I['types'], ('types differ', step)
        recs.append(dict(step=step, ori=C.ori, G=C.G, x=I['x'], y=I['y'], h=I['h'], q=I['q'], z=I['z'], s=I['s'],
                         F=I['F'], F_H=I['F_H'], F_B=I['F_B'], e1=I['e1'], xp=I['xprime'], E_B=I['E_B'], L_H=I['L_H'],
                         rows=rows, types={'%d,%d,%d' % t: c for t, c in I['types'].items()},
                         hdeg_min=own['hdeg_min'], w2=own['w2'], w2_rep=own['w2_rep'],
                         helper_fanout=dict(Counter(C.d[v] for v in I['H']))))
        circs.append(C)
        if step + 1 < steps:
            rng = random.Random(rng_seed * 100 + step) if rng_seed is not None else None
            T, origin = C.canonical_transpose(I, rng)
            C = T
    # one-step identity (E) on every step
    for j in range(steps - 1):
        I, J = recs[j], recs[j + 1]
        lhs = J['e1'] - I['e1']
        rhs = I['s'] + 96 - I['G'] + I['x'] - 2 * I['xp'] + I['E_B'] + I['L_H']
        assert lhs == rhs, ('identity (E) fails', j, lhs, rhs)
        assert J['x'] == I['xp'] and J['y'] == I['F']
    # periodicity as circuits
    per = {}
    for j in range(steps - 2):
        A, Bc = circs[j], circs[j + 2]
        per['vals_%d_%d' % (j, j + 2)] = sorted(A.mask) == sorted(Bc.mask)
        per['eqs_%d_%d' % (j, j + 2)] = eqset(A) == eqset(Bc)
    return recs, per


def two_phase(recs, j):
    I, J = recs[j], recs[j + 1]
    G = I['G']
    budget = I['x'] + J['x'] + 2 * G - 192
    ssum = I['s'] + J['s']
    EB = I['E_B'] + J['E_B']
    LH = I['L_H'] + J['L_H']
    return dict(budget=budget, ssum=ssum, margin=ssum - budget, EB=EB, LH=LH,
                drift=recs[j + 2]['e1'] - recs[j]['e1'] if j + 2 < len(recs) else None,
                ident=(ssum - budget == -(EB + LH)) if False else (recs[j + 2]['e1'] - recs[j]['e1'] == ssum - budget + EB + LH))


# ------------------------------------------------------------------ repo circuits
GATE = re.compile(r"^(XOR)\s+(\S+)\s+(\S+)\s+(\S+)")


def read_ncff(path):
    names = {'x%d' % j: j for j in range(32)}
    gates = []
    for line in open(path):
        line = line.split('%')[0].strip()
        m = GATE.match(line)
        if not m:
            continue
        _, out, a, b = m.groups()
        gates.append((names[a], names[b]))
        names[out] = 32 + len(gates) - 1
    return gates


# ------------------------------------------------------------------ main
def main():
    t0 = time.time()
    prof = json.load(open(SPRINT + '/bridge/profiles.json'))['results']
    bytag = {r['tag']: r for r in prof}
    A = [r for r in prof if r['tag'].startswith('sample:A')][:20]
    D = [r for r in prof if r['tag'].startswith('sample:D')][:10]
    K = [r for r in prof if r['tag'].startswith('kste')][:7]
    # independent loading of the value sets from the source files
    hunt = {}
    for f in ('/hunt/samples.jsonl', '/hunt/samplesD/samples.jsonl'):
        for line in open(SPRINT + f):
            d = json.loads(line)
            hunt[d['hash']] = d
    kv = {}
    for vs in json.load(open(SPRINT + '/kste/data/kste_valuesets.json')):
        kv[tuple(sorted(vs))] = vs
    jobs = []
    for r in A + D:
        h = r['tag'].split(':')[2]
        d = hunt[h]
        assert d['gates'] == 88 and len(d['values']) == 88
        assert sorted(d['values']) == sorted(r['values']), 'profiles.json values differ from source'
        jobs.append((r['tag'], d['values'], None))
    for r in K:
        key = tuple(sorted(r['values']))
        assert key in kv, 'kste values not in kste_valuesets.json'
        jobs.append((r['tag'], kv[key], None))
    for name in ('xor88-depth5', 'xor89-depth4', 'xor97-depth3'):
        p = HOME + '/xor-circuit-research/circuits/aes-mixcolumns/aes-mixcolumns-%s.circ.txt' % name
        g = read_ncff(p)
        C = Circuit(g, 'M')
        jobs.append(('repo:%s' % name, list(C.mask[32:]), g))
    print('jobs', len(jobs), flush=True)

    results = []
    for tag, values, true_gates in jobs:
        rec = dict(tag=tag, G=len(values))
        t1 = time.time()
        sig0 = set(INPUTS) | set(values)
        rec['n_amb_raw'] = sum(1 for v in values if len(all_pairs(v, sig0)) > 1)
        recons, P, amb = reconstructions(values)
        rec['n_pairs_hist'] = dict(Counter(len(P[v]) for v in values))
        rec['n_amb_values'] = len(amb)
        rec['seconds_recon'] = time.time() - t1
        rec['n_acyclic_reconstructions'] = len(recons)
        rec['n_multi_levelled'] = levelled_ambiguity(values)
        rec['n_multi_bridge'] = bytag[tag]['recon']['n_multi']
        # distinct profiles over all acyclic reconstructions (x, y of C and of the orbit summaries)
        yx = Counter(yx_of(c) for c in recons)
        rec['yx_over_reconstructions'] = {'%d,%d' % k: c for k, c in yx.items()}
        # base: max y, then lexicographic
        base = max(recons, key=lambda c: (yx_of(c)[0], tuple(sorted(c.items()))))
        gates, order = topo_gates(values, base)
        recs, per = orbit(gates)
        rec['orbit'] = recs
        rec['period'] = per
        rec['two_raw'] = two_phase(recs, 0)
        rec['two_tail'] = two_phase(recs, 1)
        rec['two_tail2'] = two_phase(recs, 2)
        # random canonical choices: does period 2 survive?
        rp = []
        for sd in (1, 2, 3):
            r2, p2 = orbit(gates, steps=5, rng_seed=sd)
            rp.append(dict(seed=sd, per=p2, ys=[r['y'] for r in r2], ss=[r['s'] for r in r2],
                           EB=[r['E_B'] for r in r2], e1=[r['e1'] for r in r2],
                           tail=two_phase(r2, 1)))
        rec['random_canonical'] = rp
        # all other acyclic reconstructions: profile spread
        alt = []
        for c in recons[:30]:
            if c == base:
                continue
            g2, _ = topo_gates(values, c)
            r2, _ = orbit(g2, steps=3)
            alt.append(dict(x=r2[0]['x'], y=r2[0]['y'], h=r2[0]['h'], q=r2[0]['q'], z=r2[0]['z'], F=r2[0]['F'],
                            E_B=r2[0]['E_B'], tail=two_phase(r2, 1) if len(r2) > 3 else None,
                            raw_margin=r2[0]['s'] + r2[1]['s'] - (r2[0]['x'] + r2[1]['x'] + 2 * len(values) - 192),
                            xT=r2[1]['x'], yT=r2[1]['y'], qT=r2[1]['q'], zT=r2[1]['z'], E_BT=r2[1]['E_B']))
        rec['alternatives'] = alt
        if true_gates is not None:
            r3, p3 = orbit(true_gates)
            rec['true_orbit'] = r3
            rec['true_period'] = p3
            rec['true_two_tail'] = two_phase(r3, 1)
            rec['true_two_raw'] = two_phase(r3, 0)
            rec['true_eq_recon'] = eqset(Circuit(true_gates, 'M')) == eqset(Circuit(gates, 'M'))
        # comparison with profiles.json
        b = bytag[tag]
        diffs = []
        for st in range(6):
            mine, theirs = recs[st], b['orbit'][st]
            for k in ('ori', 'x', 'y', 'h', 'q', 'z', 's', 'F', 'F_H', 'F_B', 'e1', 'xp', 'E_B', 'L_H'):
                if mine[k] != theirs[k]:
                    diffs.append((st, k, mine[k], theirs[k]))
            if mine['types'] != theirs['types']:
                diffs.append((st, 'types', mine['types'], theirs['types']))
            for rn, sl in mine['rows'].items():
                if theirs['rows'].get(rn) != sl:
                    diffs.append((st, 'row:' + rn, sl, theirs['rows'].get(rn)))
        rec['diff_vs_profiles'] = diffs
        rec['bridge_two'] = b['two']
        results.append(rec)
        json.dump(dict(results=results, seconds=time.time() - t0), open(OUT + '/recheck.json', 'w'), default=str)
        tp = rec['two_tail']
        print('%-28s raw-amb=%d amb=%d recon=%d lev=%d/%d %.1fs | C x%d y%d h%d q%d z%d EB%d | tail a%d b%d Y%d V%d s%d+%d budget%d margin%d EB%d LH%d ident=%s | per2 eqs %s %s %s | rand per %s | diffs %d' % (
            tag, rec['n_amb_raw'], len(amb), len(recons), rec['n_multi_levelled'], rec['n_multi_bridge'], time.time() - t1,
            recs[0]['x'], recs[0]['y'], recs[0]['h'], recs[0]['q'], recs[0]['z'], recs[0]['E_B'],
            recs[1]['x'], recs[2]['x'], recs[1]['y'], recs[2]['y'], recs[1]['s'], recs[2]['s'],
            tp['budget'], tp['margin'], tp['EB'], tp['LH'], tp['ident'],
            per['eqs_1_3'], per['eqs_2_4'], per['eqs_0_2'],
            ''.join('T' if all(v for k, v in x['per'].items() if k.startswith('eqs_1') or k.startswith('eqs_2')) else 'F' for x in rp),
            len(diffs)), flush=True)
    json.dump(dict(results=results, seconds=time.time() - t0), open(OUT + '/recheck.json', 'w'), default=str)
    print('written', len(results), '%.0fs' % (time.time() - t0))


if __name__ == '__main__':
    main()
