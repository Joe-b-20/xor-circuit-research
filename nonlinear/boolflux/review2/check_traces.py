"""Re-verify the worked traces independently of show_trace.py.

For every MOVES.txt.it<N>.before/.after pair of ~/xs-campaigns/2026-11-13-boolflux/traces/<x>/:
  * evaluate both with an independent evaluator (common.eval_circuit) and compare with the target
    (maj3 / AES S-box from a separately written S-box generator below, not targets.py);
  * check the trace line's before/after (cost, G, A, GD, AD) against the files;
  * classify the nonlinear gates by output function with a multiset and ordered operands
    (removed = output function gone, new = function not present before, rewired = same output
    function, different operand-function multiset) and compare with show_trace.py's counts.
    taskset -c 16 python3 check_traces.py
"""
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

from common import R2, PKG, core, eval_circuit

TR = Path.home() / 'xs-campaigns' / '2026-11-13-boolflux' / 'traces'
NL = {8, 14, 7, 1, 4, 13, 2, 11}
SYM = {8, 14, 6, 9, 7, 1}          # symmetric: operand order is not structure


def aes_sbox_independent():
    # GF(2^8) inverse by exponentiation x^254, then the FIPS-197 affine map
    def mul(a, b):
        r = 0
        for _ in range(8):
            if b & 1: r ^= a
            hi = a & 0x80; a = (a << 1) & 0xFF
            if hi: a ^= 0x1B
            b >>= 1
        return r
    out = []
    for x in range(256):
        y = 1
        for _ in range(254): y = mul(y, x)
        if x == 0: y = 0
        rot = lambda v, k: ((v << k) | (v >> (8 - k))) & 0xFF
        out.append(y ^ rot(y, 1) ^ rot(y, 2) ^ rot(y, 3) ^ rot(y, 4) ^ 0x63)
    return out


def metrics(c):
    lg = [0] * c.n; la = [0] * c.n
    for op, a, b in c.gates:
        lg.append(max(lg[a], lg[b]) + 1); la.append(max(la[a], la[b]) + (op in NL))
    return {'G': len(c.gates), 'A': sum(op in NL for op, _, _ in c.gates),
            'GD': max(lg[o] for o in c.outputs), 'AD': max(la[o] for o in c.outputs)}


def tables(c):
    N = 1 << c.n; t = []
    for i in range(c.n): t.append(sum(((x >> (c.n - 1 - i)) & 1) << x for x in range(N)))
    ones = (1 << N) - 1
    for op, a, b in c.gates:
        A, B = t[a], t[b]; v = 0
        for idx, (pa, pb) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
            if (op >> idx) & 1: v |= (A if pa else ~A & ones) & (B if pb else ~B & ones)
        t.append(v)
    return t


def nl_by_output(c):
    t = tables(c); d = {}
    for j, (op, a, b) in enumerate(c.gates):
        if op in NL:
            key = (op,) + (tuple(sorted((t[a], t[b]))) if op in SYM else (t[a], t[b]))
            d.setdefault(t[c.n + j], Counter())[key] += 1
    return d


def main():
    target = {'maj3': [1 if bin(x).count('1') >= 2 else 0 for x in range(8)], 'aes142': aes_sbox_independent(),
              'aes109': aes_sbox_independent()}
    from boolflux import targets
    assert target['aes142'] == targets.aes_sbox()
    problems = 0
    for x in ('maj3', 'aes142', 'aes109'):
        mv = TR / x / 'moves.txt'
        lines = mv.read_text().splitlines()
        print('==', x, len(lines), 'accepted moves in the log')
        # the improving moves (those with files); show_trace's own classification for comparison
        st = subprocess.run([sys.executable, str(PKG / 'bench' / 'show_trace.py'), str(mv)], capture_output=True, text=True).stdout
        st_counts = {}
        cur_it = None
        for ln in st.splitlines():
            if ln.startswith('it '): cur_it = int(ln.split()[1])
            mm = re.match(r'\s+AND gates: (\d+) removed, (\d+) with a new function, (\d+) rewired', ln)
            if mm: st_counts[cur_it] = tuple(int(g) for g in mm.groups())
        recorded = (TR / ('%s-trace.txt' % x)).read_text()
        print('   recorded trace text == current show_trace output:', recorded.strip() == st.strip())
        for ln in lines:
            it = int(ln.split()[1])
            bf = Path(str(mv) + '.it%d.before' % it)
            if not bf.exists(): continue
            b = core.from_kernel(bf.read_text()); a = core.from_kernel(Path(str(mv) + '.it%d.after' % it).read_text())
            vb = eval_circuit(b.n, b.gates, b.outputs); va = eval_circuit(a.n, a.gates, a.outputs)
            ok = vb == target[x] and va == target[x]
            mb, ma = metrics(b), metrics(a)
            m1 = re.search(r'before cost [\d.]+ G (\d+) A (\d+) GD (\d+) AD (\d+) -> after cost [\d.]+ G (\d+) A (\d+) GD (\d+) AD (\d+)', ln)
            lb = tuple(int(g) for g in m1.groups()[:4]); la = tuple(int(g) for g in m1.groups()[4:])
            line_ok = lb == (mb['G'], mb['A'], mb['GD'], mb['AD']) and la == (ma['G'], ma['A'], ma['GD'], ma['AD'])
            ob, oa = nl_by_output(b), nl_by_output(a)
            gone = [o for o in ob if o not in oa]; new = [o for o in oa if o not in ob]
            rew = [o for o in ob if o in oa and ob[o] != oa[o]]
            mine = (len(gone), len(new), len(rew))
            dup_b = sum(sum(v.values()) - len(v) for v in ob.values()); dup_a = sum(sum(v.values()) - len(v) for v in oa.values())
            agree = st_counts.get(it) in (None, mine)
            problems += (not ok) + (not line_ok) + (not agree)
            print('   it %-6d target_ok %s line_metrics_ok %s  G %d->%d A %d->%d  ANDs gone/new/rewired %s  show_trace %s  dup-NL-gates %d/%d'
                  % (it, ok, line_ok, mb['G'], ma['G'], mb['A'], ma['A'], mine, st_counts.get(it, 'n/a'), dup_b, dup_a))
    print('problems', problems)


if __name__ == '__main__':
    main()
