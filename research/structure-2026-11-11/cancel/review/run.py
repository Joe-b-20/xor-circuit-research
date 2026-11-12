import sys, os
from rev import *

ROOT = os.path.expanduser('~/xor-circuit-research')
KSTE = os.path.expanduser('~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor')

def check_sheet_language(M):
    for j in range(8):
        for c in range(4):
            r = M.rows[j][c]
            for b in range(8):
                p = M.part(r, b)
                want = E[c] if b == j else (S[c] if b == (j - 1) % 8 or (b == 7 and j in (1, 3, 4)) else 0)
                assert p == want, (j, c, b, p, want)
    return True

def gamma_graph(M, W):
    sheets = sorted(W)
    edges = {x: [y for y in sheets if y != x and W[y] >> x & 1] for x in sheets}
    # directed girth: shortest closed walk via path-length powers (tiny graph)
    best = None
    for s in sheets:
        dist = {s: 0}; fr = [s]; d = 0
        while fr and best is None or (fr and d < (best or 99)):
            d += 1; nf = []
            for x in fr:
                for y in edges[x]:
                    if y == s:
                        best = d if best is None else min(best, d)
                    if y not in dist:
                        dist[y] = d; nf.append(y)
            fr = nf
    return edges, best

def show_rot(name, m, detail=False):
    n, gates = read_rot(os.path.join(ROOT, 'research/structure-2026-11-11/rotation/circuits', name))
    M = Q(m)
    r = analyse(M, gates)
    st = r['stats']
    print(name, 'ok', r['ok'], 'G', r['G'], 'E', r['E'], 'R', r['R'], 'U', r['U'], 'c', r['c'], 'cj', r['cj'],
          'exits', r['nexits'], 'union', r['union'])
    print('  dc gates', st['dc_gates'], 'instances', st['inst'], 'cancelling-needed', st['inst_cancel'],
          'conf&nonesc', st['conf_nonesc'], '(on needed cancels', st['conf_nonesc_cancel'], ')',
          'conf-escape', st['conf_esc'], 'notconf', st['notconf'], 'exits used', sorted(st['exits_used']))
    return M, n, gates, r

if __name__ == '__main__':
    M = MC()
    print('sheet language check', check_sheet_language(M))
    W = {j: sup(M, M.rows[j][0]) for j in range(8)}
    print('MC windows', {j: blocks(W[j]) for j in W})
    ed, gam = gamma_graph(M, W)
    print('MC Gamma', ed, 'girth', gam)
    for m in (2, 3, 4, 5, 8):
        Mq = Q(m); Wq = {j: sup(Mq, Mq.rows[j][0]) for j in range(m)}
        print('Q_%d girth' % m, gamma_graph(Mq, Wq)[1])
    # chain of 3 sheets (blocks 0..3, sheets 1..3, windows {j-1, j})
    Wc = {1: 0b0011, 2: 0b0110, 3: 0b1100}
    print('chain girth', gamma_graph(type('X', (), {})(), Wc)[1])

    for name, m in (('q2_16.txt', 2), ('q3_28.txt', 3), ('q4_40.txt', 4), ('q8_80.txt', 8)):
        out = show_rot(name, m)
    # Q_3 detail
    Mq, n, gates, r = show_rot('q3_28.txt', 3)
    def fmt(v):
        return ' '.join('%d:%s' % (b, format(Mq.part(v, b), '04b')[::-1]) for b in range(3) if Mq.part(v, b))
    for s in range(n, n + len(gates)):
        a, b = gates[s - n]
        print('  g%d = %d + %d  [%s]  F:%s  %s' % (s, a, b, fmt(r['val'][s]),
              [j for j in r['F'] if s in r['F'][j]], 'EXIT lost ' + str(blocks(r['isexit'][s])) if s in r['isexit'] else ''))
    for case in r['stats']['conf_ok_cases']:
        print('  conf/nonesc on needed cancel: g, sheet, exit, off, l, off charged to', case)
