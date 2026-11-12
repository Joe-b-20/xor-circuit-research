import os, sys
from collections import Counter
from rev import *

ROOT = os.path.expanduser('~/xor-circuit-research')
KSTE = os.path.expanduser('~/xs-campaigns/2026-11-07-sprint/kste/external/mixcolumns_xor')
M = MC()

def summary(tag, r):
    st = r['stats']
    return (tag, r['ok'], r['G'], r['E'], r['R'], r['U'], r['c'], st['dc_gates'], st['inst_cancel'],
            st['conf_nonesc_cancel'], st['conf_nonesc'], st['conf_esc'], st['notconf'])

def offpath_kinds(r, gates):
    """For needed cancellations: kind of the off-path operand (input / uncharged gate / charged gate)."""
    n = 32; kinds = Counter(); offs = set()
    for g in range(n, n + len(gates)):
        if r['mult'][g] < 2:
            continue
        for j in r['F']:
            if g not in r['F'][j]:
                continue
            need = r['sp'][g] & ~r['W'][j]
            if not need:
                continue
            for e, lost in r['isexit'].items():
                if not (r['A'][j] >> e & 1):
                    continue
                a, b = gates[e - n]
                for o, off in ((a, b), (b, a)):
                    if r['anc'][o] >> g & 1 and lost & need & r['sp'][o]:
                        offs.add((e, off))
                        if off < n:
                            kinds['input'] += 1
                        elif r['mult'][off] == 0:
                            kinds['uncharged'] += 1
                        else:
                            kinds['charged'] += 1
    return kinds, offs

if __name__ == '__main__':
    step = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    rows = []
    agg = Counter(); kinds_all = Counter()
    minunion = None
    for nm in ('aes-mixcolumns-xor88-depth5', 'aes-mixcolumns-xor89-depth4', 'aes-mixcolumns-xor97-depth3'):
        gates = read_ncff(os.path.join(ROOT, 'circuits/aes-mixcolumns', nm + '.circ.txt'))
        r = analyse(M, gates)
        print(summary(nm, r), 'cj', r['cj'], 'union', r['union'])
        rows.append(r)
    sample = []
    for fn in ('circuits_1.txt', 'circuits_2.txt', 'circuits_3.txt', 'circuits_depth5.txt'):
        lines = open(os.path.join(KSTE, fn)).read().splitlines()
        for i in range(0, len(lines), step):
            if lines[i].strip():
                sample.append((fn, i + 1, lines[i]))
    allr = []
    for fn, ln, line in sample:
        gates = read_kste_line(line)
        r = analyse(M, gates)
        if not r['ok']:
            print('NOT MixColumns:', fn, ln, len(gates), line[:60])
            continue
        allr.append(((fn, ln), r, gates))
    allr += [(('recorded', k), rr, None) for k, rr in enumerate(rows)]
    nok = sum(1 for _, r, _ in allr if r['ok'])
    print('circuits', len(allr), 'computing MixColumns', nok)
    hist_dc = Counter()
    for key, r, gates in allr:
        st = r['stats']
        for k in ('dc_gates', 'inst', 'inst_cancel', 'conf_nonesc', 'conf_nonesc_cancel', 'conf_esc', 'notconf',
                  'off_uncharged', 'off_input'):
            agg[k] += st[k]
        agg['R'] += r['R']
        hist_dc[r['R']] += 1
        if r['R'] > 0:
            agg['circuits_with_dc'] += 1
        if gates is not None:
            kd, offs = offpath_kinds(r, gates)
            kinds_all.update(kd)
            agg['distinct_partners'] += len(offs)
        u = r['union']; minunion = u if minunion is None else min(minunion, u)
        if r['E'] < r['R']:
            agg['E<R'] += 1
        if r['c'] < r['R']:
            agg['c<R'] += 1
    print(dict(agg))
    print('off-path kinds at needed cancellations', dict(kinds_all))
    print('R histogram', dict(sorted(hist_dc.items())), 'min |union F|', minunion)
    print('G histogram', dict(sorted(Counter(r['G'] for _, r, _ in allr).items())))
    # specific claim: circuits_3.txt line 7451
    lines = open(os.path.join(KSTE, 'circuits_3.txt')).read().splitlines()
    for ln in (7450, 7451, 7452):
        r = analyse(M, read_kste_line(lines[ln - 1]))
        print('circuits_3.txt line', ln, summary('', r), 'cj', r['cj'])
