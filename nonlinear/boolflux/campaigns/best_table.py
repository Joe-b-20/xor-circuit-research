#!/usr/bin/env python3
"""Best AES S-box circuits found so far, as NIST-style tables.

    python3 nonlinear/boolflux/campaigns/best_table.py [--out DIR] [--md FILE] [--clean]

Collects every candidate (results/aes, each track's found/, track E's admitted pools, every hub
archive), keeps the (A, AD, G, GD) tuples that no published circuit (pinned NIST set) dominates
and no other candidate strictly dominates, re-verifies each survivor with both verifiers on all
256 inputs (aes_check.check), copies it to DIR with a NIST-style name, and prints tables in NIST's
categories plus the published best within the same caps.

One row per tuple (review5 P11).  The row's circuit is the first one in candidate order
(results/aes, then the campaign tracks, then the hub archives; file names sorted inside each).
Other distinct circuits with the same tuple (a different gate list) are not dropped silently:
the last column counts them and DIR/BEST.json lists every one with its source file, together
with the candidate files that could not be read.  If the first circuit of a tuple fails
verification the next distinct one is tried; a tuple with no verifying circuit is reported and
the exit status is 1.

Files in DIR that an earlier run wrote and that are no longer in the table are listed; --clean
removes them (only files named aes-sbox-a*-ad*-g*-gd*-xx*.circ.txt).
"""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[1]))
import aes_check as AC                     # noqa: E402
from boolflux import core                  # noqa: E402

C = Path.home() / 'xs-campaigns' / '2026-11-13-aes'
SOURCES = [HERE.parent / 'results' / 'aes']
GLOBS = ['D/found/*.circ.txt', 'E/found/*.circ.txt', 'F/found/*.circ.txt', 'main/**/best.circ.txt',
         'E/long1/*/admitted/*.bfx', 'E/low1/**/admitted/*.bfx', 'C/found/*.circ.txt']
# 2026-11-14 hub phase: every hub campaign archive, track G found/
EXTRA = [(Path.home() / 'xs-campaigns' / '2026-11-14-hub', '*/archive/*.bfx'),
         (Path.home() / 'xs-campaigns' / '2026-11-14-G', 'found/*.circ.txt')]
OWN_NAME = re.compile(r'^aes-sbox-a\d+-ad\d+-g\d+-gd\d+-xx\d+-\d+\.circ\.txt$')


def candidates():
    files = []
    for d in SOURCES:
        files += sorted(d.glob('*.circ.txt'))
    for g in GLOBS:
        files += sorted(C.glob(g))
    for base, g in EXTRA:
        files += sorted(base.glob(g))
    return [f for f in files if '.check.' not in f.name]


def le(p, q):
    return all(a <= b for a, b in zip(p, q))


def load_circuit(f):
    return core.from_kernel(f.read_text()) if f.suffix == '.bfx' else core.read_ncff(str(f))


def circuit_key(c):
    """Identity of a circuit = its gate list and outputs (wire names and comments do not count)."""
    return hashlib.sha1(core.to_kernel(c).encode()).hexdigest()[:16]


def scan(files, model):
    """Metrics of every candidate file.  Returns (by_tuple, skipped):
    by_tuple[(A, AD, G, GD)] = distinct circuits in candidate order, each
    {'key', 'file' (first file holding it), 'files' (how many files hold it)};
    skipped = [(file, error)] for files that could not be read as a circuit.
    Byte-identical files (the hub's snapshot archives repeat most ids) are parsed once."""
    by_bytes = {}; by_tuple = {}; by_key = {}; skipped = []
    for f in files:
        try:
            raw = f.read_bytes()
        except OSError as e:
            skipped.append((f, repr(e))); continue
        h = hashlib.sha1(raw).digest()
        hit = by_bytes.get(h)
        if hit is None:
            try:
                text = raw.decode('utf-8')
                c = core.from_kernel(text) if f.suffix == '.bfx' else core.read_ncff(text if '\n' in text else str(f))
                m = c.metrics(model)
                hit = ((m['A'], m['AD'], m['G'], m['GD']), circuit_key(c))
            except Exception as e:
                hit = repr(e)
            by_bytes[h] = hit
        if isinstance(hit, str):
            skipped.append((f, hit)); continue
        t, key = hit
        ent = by_key.get(key)
        if ent is None:
            ent = by_key[key] = {'key': key, 'file': f, 'files': 0}
            by_tuple.setdefault(t, []).append(ent)
        ent['files'] += 1
    return by_tuple, skipped


def pareto(tuples, pub):
    """(new, front): the tuples that no published tuple dominates (all four <=, equality counts),
    and those of them that no other such tuple strictly dominates.  A dominating tuple sorts
    before the dominated one, so one pass against the front found so far is enough (the old
    all-pairs test was quadratic in the number of distinct tuples)."""
    pubt = sorted({u for u in pub})
    new = sorted(t for t in tuples if not any(le(u, t) for u in pubt))
    front = []
    for t in new:
        if not any(le(u, t) for u in front):
            front.append(t)
    return new, front


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog='best_table.py', formatter_class=argparse.RawDescriptionHelpFormatter,
        description='NIST-style tables of the best AES S-box circuits found so far (tuples that the pinned\n'
                    'NIST set does not dominate and no other candidate strictly dominates), each re-verified\n'
                    'by both verifiers.  One row per (A, AD, G, GD) tuple; other distinct circuits at the\n'
                    'same tuple are counted in the last column and listed in DIR/BEST.json.',
        epilog='Candidates: results/aes, ~/xs-campaigns/2026-11-13-aes (track found/ folders, main, track E\n'
               'pools), every ~/xs-campaigns/2026-11-14-hub/*/archive and 2026-11-14-G/found.\n'
               'Exit status 1 if a table tuple has no circuit that verifies.')
    ap.add_argument('--out', metavar='DIR', type=Path, default=C / 'best',
                    help='folder for the verified circuits, BEST.md and BEST.json (default: %(default)s)')
    ap.add_argument('--md', metavar='FILE', type=Path, help='markdown table file (default: DIR/BEST.md)')
    ap.add_argument('--clean', action='store_true',
                    help='remove circuit files of earlier runs in DIR that are no longer in the table')
    a = ap.parse_args(argv)
    out = a.out; md = a.md or out / 'BEST.md'
    out.mkdir(parents=True, exist_ok=True)
    model = core.Model.load('nist')
    pub = AC.published()
    files = candidates()
    by_tuple, skipped = scan(files, model)
    new, front = pareto(by_tuple, [u for u, _ in pub])
    rows = []; failed = []; record = []
    for t in sorted(front, key=lambda t: (t[3], t[2], t)):
        alts = by_tuple[t]; row = None; tried = []
        for ent in alts:                       # first circuit that verifies, in candidate order
            f = ent['file']
            c = load_circuit(f); m = c.metrics(model)
            c.name = 'aes-sbox-a%d-ad%d-g%d-gd%d' % t
            c.in_names = ['x%d' % i for i in range(8)]; c.out_names = ['y%d' % i for i in range(8)]
            cnt = dict(m['counts'])
            xor, xnor, nt = cnt.get('XOR', 0), cnt.get('XNOR', 0), cnt.get('NOT', 0)
            name = 'aes-sbox-a%d-ad%d-g%d-gd%d-xx%d-%d.circ.txt' % (t + (xor + xnor + nt, xnor + nt))
            dst = out / name
            dst.write_text(core.write_ncff(c, model, comments=['BoolFlux candidate; source %s' % f]))
            r = AC.check(dst)
            if r['ok'] and tuple(r['tuple']) == t:
                row = (t, xor, xnor + nt, name, str(f).replace(str(Path.home()), '~'), r, len(alts) - 1)
                break
            dst.unlink()
            tried.append(str(f))
            print('VERIFICATION FAILED', f, r.get('errors'), file=sys.stderr)
        if row is None:
            failed.append(t)
        else:
            rows.append(row)
        record.append({'tuple_A_AD_G_GD': list(t), 'file': row[3] if row else None, 'source': row[4] if row else None,
                       'failed_verification': tried,
                       'distinct_circuits': [{'key': e['key'], 'first_file': str(e['file']).replace(str(Path.home()), '~'),
                                              'files': e['files']} for e in alts]})
    lo = [u for u, _ in pub if 29 <= u[0] <= 31]
    cats = [('S-box with 29 <= #AND <= 31 (published circuits here have G >= %s)' % (min(u[2] for u in lo) if lo else '-'),
             lambda t: 29 <= t[0] <= 31),
            ('S-box with #AND = 28', lambda t: t[0] == 28),
            ('S-box with #AND < 28', lambda t: t[0] < 28),
            ('S-box with #AND = 32..36 / AD >= 4', lambda t: 32 <= t[0] <= 36 and t[1] >= 4),
            ('S-box with #AND <= 36 / AD3', lambda t: t[0] <= 36 and t[1] == 3),
            ('S-box with #AND <= 36 / AD <= 2', lambda t: t[0] <= 36 and t[1] <= 2),
            ('S-box with #AND > 36 (gate depth traded for ANDs)', lambda t: t[0] > 36)]
    L = ['# Best BoolFlux AES S-box circuits so far (not dominated by the pinned NIST set %s)' % json.load(open(AC.NIST / 'MANIFEST.json'))['commit'][:7], '', '',
         'Every row: verified by two independent implementations on all 256 inputs, NIST gate library',
         '{AND, XOR, XNOR, NOT}, every gate counted. "Published best" = fewest gates among published',
         'circuits within the same caps (#AND <= A, AND depth <= AD, gate depth <= GD); ** = better.',
         'One row per (A, AD, G, GD); "other" = further distinct circuits with the same tuple (BEST.json lists them).', '']
    for title, pred in cats:
        sel = [r for r in rows if pred(r[0])]
        if not sel: continue
        L += ['### ' + title, '',
              '| File | #AND (A) | AND depth | #Gates (G) | Gate depth | XX (x+x\') | #XOR | #XNOR | published best within the same caps | other |',
              '|---|---:|---:|---:|---:|---:|---:|---:|---|---:|']
        for t, xor, xnor, name, src, r, nalt in sel:
            b = r['best_at_a_ad_gd_caps']
            pb = 'none' if not b else '%d (A%d AD%d GD%d)' % (b['tuple'][2], b['tuple'][0], b['tuple'][1], b['tuple'][3])
            L.append('| %s | %d | %d | **%d** | %d | %d | %d | %d | %s | %d |' % (name, t[0], t[1], t[2], t[3], xor + xnor, xor, xnor, pb, nalt))
        L.append('')
    L += ['### Fewest gates at each gate-depth cap', '', '| GD <= | published best (A AD G GD) | ours (A AD G GD) |', '|---|---|---|']
    for d in range(10, 33):
        p = min((u for u, _ in pub if u[3] <= d), key=lambda u: (u[2], u), default=None)
        o = min((r[0] for r in rows if r[0][3] <= d), key=lambda u: (u[2], u), default=None)
        if o and p and o[2] < p[2]:
            L.append('| %d | %s | **%s** |' % (d, ' '.join(map(str, p)), ' '.join(map(str, o))))
    L += ['', 'Sources: ' + ', '.join(sorted({r[4].split('/')[3] if r[4].startswith('~/xs-') else 'results/aes' for r in rows}))]
    L += ['', 'Candidates: %d files, %d distinct circuits, %d distinct tuples, %d not dominated by the pinned set; '
          '%d files could not be read%s.' % (len(files), sum(len(v) for v in by_tuple.values()), len(by_tuple), len(new),
                                             len(skipped), '' if not failed else '; NO VERIFYING CIRCUIT for %s' % failed)]
    text = '\n'.join(L) + '\n'
    md.write_text(text)
    (out / 'BEST.json').write_text(json.dumps({
        'nist_commit': json.load(open(AC.NIST / 'MANIFEST.json'))['commit'], 'candidate_files': len(files),
        'rows': record, 'unreadable_files': [{'file': str(f), 'error': e[:200]} for f, e in skipped]}, indent=1) + '\n')
    print(text)
    keep = {r[3] for r in rows}
    stale = sorted(f for f in out.iterdir() if OWN_NAME.match(f.name) and f.name not in keep)
    if stale:
        if a.clean:
            for f in stale: f.unlink()
        print('%d circuit file(s) in %s are not in this table%s: %s' % (
            len(stale), out, ' (removed)' if a.clean else ' (left in place; --clean removes them)',
            ', '.join(f.name for f in stale[:8]) + (' ...' if len(stale) > 8 else '')), file=sys.stderr)
    for f, e in skipped[:10]:
        print('unreadable candidate %s: %s' % (f, e[:160]), file=sys.stderr)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
