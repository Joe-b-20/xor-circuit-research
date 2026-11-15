#!/usr/bin/env python3
"""Result ledger of campaign 2026-11-15-targets (ten NIST AES S-box targets T01..T10, plus Z).

    python3 nonlinear/boolflux/campaigns/targets/ledger.py baseline   # once, before results arrive
    python3 nonlinear/boolflux/campaigns/targets/ledger.py run        # any time; idempotent

What it does (see README.md here):
  * reads TARGETS.json (references, hard limits, tradeoff rules) every run, so thresholds the
    user changes there take effect on the next run;
  * scans the campaign's found/ folders (circuits + JSON sidecars) and the archive (best-1400,
    hub long archive .bfx, results/aes, the study found/ folders);
  * verifies every circuit file with campaigns/aes_check.py's check() (core + independent
    verifier, all 256 inputs, NIST library {AND, XOR, XNOR, NOT}); results are cached by the
    sha256 of the file bytes and a fingerprint of the verifier code, so a re-run only checks new
    or changed files;
  * per target: every verified circuit within the hard limits (A <= ref A, AD <= ref AD), classes
    strict / tradeoff / other (rules recomputed from TARGETS.json), the (G, GD) Pareto frontier
    and the (A, AD, G, GD) Pareto frontier, each point compared with the reference and with the
    complete pinned NIST forward AES S-box collection (aes_check.published()), and provenance:
    known (in the archive at the baseline cut-off), reproduced (structure or tuple equal to a
    known circuit), or new;
  * T05: best G (then GD) per AND depth at A <= ref A;
  * any verified circuit with A <= 27 anywhere in the scanned folders;
  * sidecar audit of the campaign's found/ folders (missing fields, tuple mismatches, files that
    fail verification, hard-limit violations).
Outputs: <campaign>/LEDGER.md and <campaign>/LEDGER.json (written atomically).

The baseline (subcommand 'baseline') is the archive as of the cut-off (default 2026-11-15 15:20
UTC): every archive circuit file whose mtime (hub archive: its record's t_admit) is <= the
cut-off, keyed by structural hash (hub.common.structure_key) and by tuple.  It is written once;
it is never rewritten without --force.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
CAMPAIGNS = HERE.parent
PKG = CAMPAIGNS.parent
REPO = PKG.parents[1]
sys.path.insert(0, str(CAMPAIGNS))
import aes_check                                  # noqa: E402  (sets sys.path for boolflux + verify)
from boolflux import core                         # noqa: E402
from boolflux.hub.common import structure_key     # noqa: E402

HOME = Path.home()
CAMP = Path(os.environ.get('LEDGER_CAMPAIGN', HOME / 'xs-campaigns' / '2026-11-15-targets'))
STATE = CAMP / 'L0'
CACHE = STATE / 'cache' / 'verify.json'
BASELINE = STATE / 'baseline' / 'baseline.json'
CUTOFF_DEFAULT = '2026-11-15T15:20:00Z'

ARCHIVE_SOURCES = [            # (group label, directory, recursive)
    ('best-1400', HOME / 'xs-campaigns' / '2026-11-15-study' / 'best-1400', False),
    ('hub-long', HOME / 'xs-campaigns' / '2026-11-14-hub' / 'long' / 'archive', False),
    ('results-aes', PKG / 'results' / 'aes', True),
]
STUDY = HOME / 'xs-campaigns' / '2026-11-15-study'
CIRC_SUFFIXES = ('.circ.txt', '.bfx')
SIDECAR_FIELDS = ['target', 'A', 'AD', 'G', 'GD', 'start', 'method', 'command', 'seed',
                  'elapsed_s', 'code', 'aes_check', 'utc']


# ---- helpers ---------------------------------------------------------------------------------
def utc(ts):
    return dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_utc(s):
    return dt.datetime.strptime(s.replace('Z', '+0000'), '%Y-%m-%dT%H:%M:%S%z').timestamp()


def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def atomic_write(path, text):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name('.' + path.name + '.tmp')
    tmp.write_text(text); os.replace(tmp, path)


def is_circ(p):
    return p.is_file() and p.name.endswith(CIRC_SUFFIXES)


def stem(p):
    n = p.name
    for s in CIRC_SUFFIXES:
        if n.endswith(s): return n[:-len(s)]
    return n


def verifier_fingerprint():
    h = hashlib.sha256()
    for f in (CAMPAIGNS / 'aes_check.py', PKG / 'core.py', PKG / 'targets.py',
              PKG / 'independent' / 'verify.py', PKG / 'hub' / 'common.py'):
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def git_head():
    try:
        return (REPO / '.git').exists() and os.popen('git -C %s rev-parse --short HEAD 2>/dev/null' % REPO).read().strip()
    except Exception:
        return None


# ---- verification cache ------------------------------------------------------------------------
class Verifier:
    def __init__(self):
        self.fp = verifier_fingerprint()
        self.cache = {}
        if CACHE.exists():
            try:
                d = json.loads(CACHE.read_text())
                if d.get('fingerprint') == self.fp: self.cache = d['rows']
            except (ValueError, OSError, KeyError):
                self.cache = {}
        self.new = 0

    def check(self, path, digest):
        r = self.cache.get(digest)
        if r is not None: return r
        res = aes_check.check(str(path))
        r = {'ok': res['ok'], 'tuple': list(res['tuple']) if res.get('tuple') else None,
             'counts': res.get('counts'), 'errors': res.get('errors'), 'checked_utc': utc(time.time())}
        if res['ok']:
            c, _ = aes_check.load(path)
            r['skey'] = structure_key(c)
        self.cache[digest] = r; self.new += 1
        if self.new % 500 == 0: self.save()
        return r

    def save(self):
        atomic_write(CACHE, json.dumps({'fingerprint': self.fp, 'rows': self.cache}))


# ---- scanning ----------------------------------------------------------------------------------
def archive_files():
    """(group, path) of every circuit file in the archive sources (current state)."""
    out = []
    for g, d, rec in ARCHIVE_SOURCES:
        if d.exists():
            it = d.rglob('*') if rec else d.iterdir()
            out += [(g, p) for p in sorted(it) if is_circ(p)]
    if STUDY.exists():
        for fd in sorted(STUDY.rglob('found')):
            if fd.is_dir():
                rel = fd.relative_to(STUDY)
                if rel.parts[0] == 'best-1400': continue
                out += [('study:' + str(rel), p) for p in sorted(fd.rglob('*')) if is_circ(p)]
    return out


def campaign_files():
    """(agent, path) of every circuit file in <campaign>/<agent>/found/ (recursive)."""
    out = []
    for ad in sorted(CAMP.iterdir()):
        fd = ad / 'found'
        if ad.is_dir() and ad.name != 'L0' and fd.is_dir():
            out += [(ad.name, p) for p in sorted(fd.rglob('*')) if is_circ(p)]
    return out


def hub_t_admit(p):
    j = p.with_suffix('.json')
    try:
        return json.loads(j.read_text()).get('t_admit')
    except (OSError, ValueError):
        return None


def sidecar_of(p):
    j = p.with_name(stem(p) + '.json')
    if not j.exists(): j = p.with_name(p.name + '.json')          # <name>.circ.txt.json also accepted
    if not j.exists(): return None, None
    try:
        return j, json.loads(j.read_text())
    except (OSError, ValueError) as e:
        return j, {'_error': 'unreadable JSON: %r' % (e,)}


# ---- baseline ----------------------------------------------------------------------------------
def cmd_baseline(a):
    if BASELINE.exists() and not a.force:
        print('baseline exists (%s); not rewritten (use --force)' % BASELINE); return 0
    cut = parse_utc(a.cutoff)
    V = Verifier(); rows = []; skipped = 0
    t0 = time.time()
    for g, p in archive_files():
        st = p.stat()
        ta = hub_t_admit(p) if g == 'hub-long' else None
        when = ta if ta is not None else st.st_mtime
        if when > cut:
            skipped += 1; continue
        d = sha256(p); r = V.check(p, d)
        rows.append({'group': g, 'path': str(p), 'sha256': d, 'mtime': utc(st.st_mtime),
                     't_admit': utc(ta) if ta else None, 'ok': r['ok'], 'tuple': r['tuple'],
                     'skey': r.get('skey')})
    V.save()
    doc = {'cutoff_utc': a.cutoff, 'built_utc': utc(time.time()), 'fingerprint': V.fp,
           'rule': 'archive circuit files with mtime (hub archive: t_admit) <= cutoff',
           'sources': [str(d) for _, d, _ in ARCHIVE_SOURCES] + [str(STUDY / '*' / 'found')],
           'n_files': len(rows), 'n_after_cutoff_skipped': skipped,
           'n_verified': sum(1 for r in rows if r['ok']), 'rows': rows}
    atomic_write(BASELINE, json.dumps(doc, indent=0))
    print('baseline: %d files (%d verified AES S-box), %d after cut-off skipped, %d checks, %.0f s -> %s'
          % (len(rows), doc['n_verified'], skipped, V.new, time.time() - t0, BASELINE))
    return 0


# ---- classification ----------------------------------------------------------------------------
def dominates(u, v):
    return all(x <= y for x, y in zip(u, v)) and tuple(u) != tuple(v)


def pareto(points, key):
    """Pareto-minimal items of points under key(item) -> tuple (ties kept: one per distinct key)."""
    ks = sorted({tuple(key(p)) for p in points})
    front = [k for k in ks if not any(dominates(o, k) for o in ks)]
    return front


def front_by(ts, key):
    """One representative tuple (smallest A, then AD) per Pareto-minimal key(t)."""
    return [min((t for t in ts if tuple(key(t)) == k), key=lambda t: (t[0], t[1], t[2], t[3]))
            for k in pareto(ts, key=key)]


def classify(t, tgt, defs):
    """'strict', ('tradeoff', kind) or 'other' for tuple t = (A, AD, G, GD) within hard limits."""
    A, AD, G, GD = t
    rG, rGD, rAD = tgt['G'], tgt['GD'], tgt['AD']
    if G <= rG and GD <= rGD and (G < rG or GD < rGD):
        return 'strict', None
    gain = defs.get('min_gate_gain_for_depth_cost', 3)
    cost = defs.get('max_gate_cost_for_depth_gain', 8)
    for tr in tgt.get('tradeoffs', []):
        k = tr['kind']
        if k == 'gates_for_depth' and rGD < GD <= tr['GD_max'] and G <= rG - gain:
            return 'tradeoff', k
        if k == 'depth_for_gates' and GD <= tr['GD_max'] and GD < rGD and rG < G <= rG + cost:
            return 'tradeoff', k
        if k == 'and_depth_for_gates' and AD < rAD and AD <= max(tr['AD_targets']) and (G > rG or GD > rGD):
            return 'tradeoff', k
    return 'other', None


# ---- run ---------------------------------------------------------------------------------------
def cmd_run(a):
    t0 = time.time()
    spec = json.loads((CAMP / 'TARGETS.json').read_text())
    defs = spec.get('definitions', {})
    if not BASELINE.exists():
        print('no baseline; run "ledger.py baseline" first'); return 2
    base = json.loads(BASELINE.read_text())
    base_by_sha = {r['sha256']: r for r in base['rows']}
    base_skey, base_tuple = {}, {}
    for r in base['rows']:
        if not r['ok']: continue
        base_skey.setdefault(r['skey'], r['path'])
        base_tuple.setdefault(tuple(r['tuple']), r['path'])
    V = Verifier()
    pub = aes_check.published()                         # ((A, AD, G, GD), name) of the pinned set
    nist_check = nist_integrity()

    recs = []                                           # one per file
    for g, p in archive_files():
        d = sha256(p); r = V.check(p, d)
        recs.append({'kind': 'archive', 'group': g, 'path': str(p), 'sha256': d,
                     'baseline': d in base_by_sha, 'mtime': utc(p.stat().st_mtime), **r})
    issues = []
    for agent, p in campaign_files():
        d = sha256(p); r = V.check(p, d)
        sj, sc = sidecar_of(p)
        rec = {'kind': 'campaign', 'group': agent, 'path': str(p), 'sha256': d, 'baseline': False,
               'mtime': utc(p.stat().st_mtime), 'sidecar': str(sj) if sj else None, 'meta': sc, **r}
        recs.append(rec)
        issues += audit(rec, spec, V)
    for agent, sj in orphan_sidecars():
        issues.append({'level': 'WARN', 'file': str(sj), 'agent': agent, 'issue': 'sidecar without a circuit file'})
    V.save()

    for r in recs:                                      # provenance per file
        if not r['ok']: r['status'] = None; continue
        if r['baseline']: r['status'] = 'known'; continue
        k, t = r.get('skey'), tuple(r['tuple'])
        if k in base_skey: r['status'] = 'reproduced'; r['same_as'] = {'structure': base_skey[k]}
        elif t in base_tuple: r['status'] = 'reproduced'; r['same_as'] = {'tuple': base_tuple[t]}
        else: r['status'] = 'new'
    certify(recs)
    ok = [r for r in recs if r['ok']]

    out = {'generated_utc': utc(time.time()), 'campaign': str(CAMP), 'nist_pin': spec.get('nist_pin'),
           'nist_integrity': nist_check, 'baseline': {k: base[k] for k in ('cutoff_utc', 'built_utc', 'n_files', 'n_verified')},
           'verifier_fingerprint': V.fp, 'code_head': git_head(), 'definitions': defs,
           'scan': {'archive_files': sum(1 for r in recs if r['kind'] == 'archive'),
                    'campaign_files': sum(1 for r in recs if r['kind'] == 'campaign'),
                    'verified_ok': len(ok), 'checked_this_run': V.new,
                    'archive_not_aes_or_failed': sum(1 for r in recs if r['kind'] == 'archive' and not r['ok'])},
           'targets': {}, 'issues': issues}
    for tgt in spec['targets']:
        out['targets'][tgt['id']] = target_report(tgt, defs, ok, pub)
    out['a_le_27'] = [slim(r) for r in ok if r['tuple'][0] <= 27]
    out['campaign_results'] = [slim(r, meta=True) for r in recs if r['kind'] == 'campaign']
    out['elapsed_s'] = round(time.time() - t0, 1)
    prev = None
    if (CAMP / 'LEDGER.json').exists():
        try: prev = json.loads((CAMP / 'LEDGER.json').read_text())
        except ValueError: prev = None
    out['changes'] = changes(prev, out)
    atomic_write(CAMP / 'LEDGER.json', json.dumps(out, indent=1))
    atomic_write(CAMP / 'LEDGER.md', render(out, spec))
    hist = STATE / 'history'; hist.mkdir(parents=True, exist_ok=True)
    stamp = out['generated_utc'].replace(':', '').replace('-', '')
    atomic_write(hist / ('LEDGER-%s.json' % stamp), json.dumps(out))
    print('ledger: %d files (%d verified, %d checked now), %d issues, %.1f s -> %s'
          % (len(recs), len(ok), V.new, len(issues), out['elapsed_s'], CAMP / 'LEDGER.md'))
    for c in out['changes']:
        print('CHANGE', c)
    return 0


def nist_integrity():
    """Pinned files vs MANIFEST.json sha256 (forward aes-sbox folder)."""
    man = json.loads((REPO / 'nonlinear' / 'nist' / 'MANIFEST.json').read_text())
    bad, n = [], 0
    for f in man['files']:
        p = REPO / 'nonlinear' / 'nist' / f['folder'] / f['file']
        n += 1
        if not p.exists() or sha256(p) != f['sha256']: bad.append(f['folder'] + '/' + f['file'])
    return {'commit': man.get('commit'), 'files': n, 'mismatch': bad}


def slim(r, meta=False):
    d = {k: r.get(k) for k in ('kind', 'group', 'path', 'sha256', 'tuple', 'status', 'same_as', 'skey', 'cert', 'cert_by', 'donor')}
    if meta:
        d['ok'] = r['ok']; d['errors'] = r.get('errors'); d['sidecar'] = r.get('sidecar')
        m = r.get('meta') or {}
        d['meta'] = {k: m.get(k) for k in ('target', 'start', 'method', 'command', 'seed', 'elapsed_s',
                                            'code', 'aes_check', 'utc', 'path_certified', 'reproduces',
                                            'donor_outside_limits') + DONOR_STATEMENT_KEYS}
    return d


CERT_OK = ('certified', 'reproduced-certified')


def certify(recs):
    """Search-path certification (COMPLIANCE-1820.md).  Campaign file: sidecar path_certified
    true -> 'certified', false -> 'not certified', anything else or missing -> 'unknown'; a file
    that a certified campaign file names in its sidecar 'reproduces' (path, basename or sha256),
    with a tuple all <= its own, becomes 'reproduced-certified' (cert_by = that file).  Archive
    files: 'n/a' (they are starts, not campaign results).
    Lineage (coordinator 18:50): a file whose own run is certified but whose start is a campaign
    file (matched by path or sha256) without an effective certification is 'not certified
    (inherited from START)'; it becomes certified again as soon as that ancestor is certified or
    reproduced-certified.  Archive starts do not affect it.  Computed to a fixpoint."""
    camp = [r for r in recs if r['kind'] == 'campaign']
    for r in recs:
        if r['kind'] != 'campaign': r['cert'] = 'n/a'; continue
        pc = (r.get('meta') or {}).get('path_certified', 'unknown')
        r['own_cert'] = 'certified' if pc is True else 'not certified' if pc is False else 'unknown'
        r['donor'] = donor_state(r.get('meta') or {})
    by_path = {r['path']: r for r in camp}
    by_sha = {}
    for r in camp: by_sha.setdefault(r['sha256'], r)

    def start_rec(r):
        sp, sh = start_of(r.get('meta') or {})
        a = by_path.get(str(sp).replace('~', str(HOME), 1)) if sp else None
        a = a or (by_sha.get(sh) if sh else None)
        return a if a is not r else None

    repro = {}                                          # id(file) -> certified reproducing file
    for _ in range(50):
        memo = {}

        def eff(r):
            k = id(r)
            if k in memo: return memo[k]
            memo[k] = 'unknown (lineage cycle)'
            if k in repro: v = 'reproduced-certified'
            else:
                v = r['own_cert']
                if v == 'certified':
                    a = start_rec(r)
                    if a is not None and not eff(a).startswith(CERT_OK):
                        v = 'not certified (inherited from %s)' % Path(a['path']).name
            memo[k] = v
            return v
        for r in camp:
            r['cert'] = eff(r)
            r['cert_by'] = repro.get(id(r))
        changed = False
        for y in camp:
            if not y['cert'].startswith(CERT_OK) or not y['ok']: continue
            rp = (y.get('meta') or {}).get('reproduces')
            for x in (rp if isinstance(rp, list) else [rp] if rp else []):
                x = str(x).replace('~', str(HOME), 1)
                for r in camp:
                    if r is y or r['cert'].startswith(CERT_OK) or not r['ok'] or id(r) in repro: continue
                    if x in (r['path'], Path(r['path']).name, stem(Path(r['path'])), r['sha256']) and \
                            all(a <= b for a, b in zip(y['tuple'], r['tuple'])):
                        repro[id(r)] = y['path']; changed = True
        if not changed: break


def path_of_tuple(rows, cls):
    """'path' of a ledger point: n/a when no campaign file realises the tuple (archive starts);
    else the best certification among its campaign files.  'claim' qualifies a strict or
    tradeoff point that has no certified campaign file."""
    camp = [r for r in rows if r['kind'] == 'campaign']
    if any(r['status'] == 'known' for r in rows): return {'path': 'n/a (known)', 'claim': None}
    if not camp: return {'path': 'n/a', 'claim': None}
    for want in CERT_OK + ('unknown', 'not certified'):
        hit = [r for r in camp if r['cert'].startswith(want)]
        if hit:
            p = hit[0]['cert'] if want != 'reproduced-certified' else 'reproduced-certified (by %s)' % short(hit[0].get('cert_by'))
            if want == 'certified': p = 'certified (%s)' % short(hit[0]['path'])
            if hit[0].get('donor') == 'ok': p += '; ' + DONOR_NOTE
            elif hit[0].get('donor') == 'no statement': p += '; donor outside the limits, builder statement MISSING'
            claim = None
            if cls in ('strict', 'tradeoff') and want not in CERT_OK:
                claim = 'within limits; search path not certified'
            return {'path': p, 'claim': claim}
    return {'path': 'unknown', 'claim': None}


def prov_of_tuple(t, rows):
    """Status of a tuple from the files that realise it: known if a baseline file does; else
    the earliest campaign file's status; files listed per status."""
    pri = {'results-aes': 0, 'best-1400': 1, 'hub-long': 3}
    known = sorted([r for r in rows if r['status'] == 'known'], key=lambda r: (pri.get(r['group'], 2), r['path']))
    camp = sorted([r for r in rows if r['kind'] == 'campaign'], key=lambda r: ((r.get('meta') or {}).get('utc') or r['mtime']))
    post = [r for r in rows if r['kind'] == 'archive' and not r['baseline']]
    if known:
        st = 'known'
        if camp: st += '; reproduced by ' + ', '.join(sorted({r['group'] for r in camp}))
    elif camp:
        st = 'new (%s)' % camp[0]['group']
        if any(r['status'] == 'reproduced' for r in camp): st = camp[0]['status']
    elif post:
        st = 'new (archive after cut-off: %s)' % post[0]['group']
    else:
        st = '?'
    rep = (known or camp or post or rows)[0]
    return st, rep


def nist_compare(t, pub, tgt):
    dom = sorted([(list(u), n) for u, n in pub if dominates(u, t)], key=lambda x: x[0])
    eq = [n for u, n in pub if tuple(u) == tuple(t)]
    return {'dominated_by': dom, 'equal_tuple': eq,
            'vs_ref': {'dG': t[2] - tgt['G'], 'dGD': t[3] - tgt['GD'], 'dA': t[0] - tgt['A'], 'dAD': t[1] - tgt['AD']}}


def target_report(tgt, defs, ok, pub):
    rA, rAD = tgt['A'], tgt['AD']
    inl = [r for r in ok if r['tuple'][0] <= rA and r['tuple'][1] <= rAD]
    by_t = {}
    for r in inl: by_t.setdefault(tuple(r['tuple']), []).append(r)

    def point(t):
        rows = by_t[t]; st, rep = prov_of_tuple(t, rows)
        cls, kind = classify(t, tgt, defs)
        m = rep.get('meta') or {}
        return {'tuple': list(t), 'class': cls if kind is None else 'tradeoff:' + kind, 'status': st,
                'file': rep['path'], 'sha256': rep['sha256'], 'source': rep['kind'] + ':' + rep['group'],
                'structures': len({r['skey'] for r in rows}), 'files': len(rows),
                'start': m.get('start'), 'method': m.get('method'), 'seed': m.get('seed'),
                'elapsed_s': m.get('elapsed_s'), 'aes_check': m.get('aes_check') or 'ledger: aes_check.check OK',
                'same_as': rep.get('same_as'), 'nist': nist_compare(t, pub, tgt), **path_of_tuple(rows, cls)}

    ts = list(by_t)
    f2 = pareto(ts, key=lambda t: (t[2], t[3]))
    f2t = [min((t for t in ts if (t[2], t[3]) == k), key=lambda t: (t[0], t[1])) for k in f2]
    f4 = pareto(ts, key=lambda t: t)
    strict = [t for t in ts if classify(t, tgt, defs)[0] == 'strict']
    trade = [t for t in ts if classify(t, tgt, defs)[0] == 'tradeoff']
    # a tradeoff that a strict circuit dominates (in (G, GD); AND-depth kind: in (AD, G, GD)) is not a tradeoff worth listing
    def _k(t):
        return (t[1], t[2], t[3]) if classify(t, tgt, defs)[1] == 'and_depth_for_gates' else (t[2], t[3])
    trade = [t for t in trade if not any(all(a <= b for a, b in zip(_k(s) if len(_k(t)) == 2 else (s[1], s[2], s[3]), _k(t)))
                                         for s in strict)]
    strict_f = front_by(strict, lambda t: (t[2], t[3]))                    # Pareto in (G, GD)
    trade_f = []                                                          # per kind: (G, GD); AND depth: (AD, G, GD)
    for k in sorted({classify(t, tgt, defs)[1] for t in trade}):
        tk = [t for t in trade if classify(t, tgt, defs)[1] == k]
        trade_f += front_by(tk, (lambda t: (t[1], t[2], t[3])) if k == 'and_depth_for_gates' else (lambda t: (t[2], t[3])))
    pub_in = [u for u, n in pub if u[0] <= rA and u[1] <= rAD]
    pub_front = [[list(u), n] for u, n in sorted(pub, key=lambda x: x[0])
                 if u[0] <= rA and u[1] <= rAD and tuple((u[2], u[3])) in set(pareto(pub_in, key=lambda u: (u[2], u[3])))]
    rep = {'ref': tgt, 'n_files_within_limits': len(inl), 'n_tuples': len(ts),
           'n_structures': len({r['skey'] for r in inl}),
           'best_strict_by_G': point(min(strict, key=lambda t: (t[2], t[3], t[0], t[1]))) if strict else None,
           'best_strict_by_GD': point(min(strict, key=lambda t: (t[3], t[2], t[0], t[1]))) if strict else None,
           'best_certified_strict_by_G': (lambda c: point(min(c, key=lambda t: (t[2], t[3], t[0], t[1]))) if c else None)(
               [t for t in strict if str(path_of_tuple(by_t[t], 'strict')['path']).startswith(CERT_OK + ('n/a (known)',))]),
           'strict_frontier': [point(t) for t in strict_f],
           'tradeoff_frontier': [point(t) for t in trade_f],
           'best_tradeoff': best_tradeoffs(trade, tgt, defs, point),
           'frontier_G_GD': [point(t) for t in f2t],
           'frontier_A_AD_G_GD': [point(t) for t in f4],
           'pinned_frontier_within_limits': pub_front}
    if any(tr['kind'] == 'and_depth_for_gates' for tr in tgt.get('tradeoffs', [])):
        per = {}
        for d in range(rAD, 0, -1):
            td = [t for t in ts if t[1] == d]
            fr = [list(min((u for u in td if (u[2], u[3]) == k), key=lambda u: u[0]))
                  for k in pareto(td, key=lambda t: (t[2], t[3]))]
            tle = [t for t in ts if t[1] <= d]
            per[str(d)] = {'best_G': point(min(td, key=lambda t: (t[2], t[3], t[0]))) if td else None,
                           'best_G_at_AD_le': point(min(tle, key=lambda t: (t[2], t[3], t[1], t[0]))) if tle else None,
                           'best_GD': point(min(td, key=lambda t: (t[3], t[2], t[0]))) if td else None,
                           'frontier_G_GD': fr}
        rep['per_and_depth'] = per
    return rep


def best_tradeoffs(trade, tgt, defs, point):
    out = {}
    for t in trade:
        k = classify(t, tgt, defs)[1]
        out.setdefault(k, []).append(t)
    res = {}
    for k, ts in out.items():
        if k == 'gates_for_depth': b = min(ts, key=lambda t: (t[2], t[3], t[0], t[1]))
        elif k == 'depth_for_gates': b = min(ts, key=lambda t: (t[3], t[2], t[0], t[1]))
        else:                                   # AND depth: best G (then GD) at each AD
            for d in sorted({t[1] for t in ts}, reverse=True):
                res['%s AD%d' % (k, d)] = point(min((t for t in ts if t[1] == d), key=lambda t: (t[2], t[3], t[0])))
            continue
        res[k] = point(b)
    return res


# ---- sidecar audit -----------------------------------------------------------------------------
def audit(rec, spec, V=None):
    iss = []; f = rec['path']; ag = rec['group']
    def add(level, msg): iss.append({'level': level, 'file': f, 'agent': ag, 'issue': msg})
    if not rec['ok']:
        add('FAIL', 'circuit FAILS verification: %s' % rec.get('errors'))
    m = rec.get('meta')
    if m is None:
        add('WARN', 'no JSON sidecar'); return iss
    if '_error' in m:
        add('WARN', m['_error']); return iss
    miss = [k for k in SIDECAR_FIELDS if m.get(k) in (None, '', [])]
    if miss: add('WARN', 'sidecar missing fields: %s' % ', '.join(miss))
    if rec['ok']:
        t = rec['tuple']; st = [m.get(k) for k in ('A', 'AD', 'G', 'GD')]
        if all(x is not None for x in st) and list(st) != list(t):
            add('FAIL', 'sidecar tuple %s != verified %s' % (st, t))
        tid = m.get('target')
        tg = {x['id']: x for x in spec['targets']}
        for one in (tid if isinstance(tid, list) else [tid]):
            if one in tg and (t[0] > tg[one]['A'] or t[1] > tg[one]['AD']):
                add('FAIL', 'HARD LIMIT VIOLATED for %s: A AD = %d %d > ref %d %d' % (one, t[0], t[1], tg[one]['A'], tg[one]['AD']))
            elif one not in tg and one not in ('Z', 'Z1', None):
                add('WARN', 'sidecar target %r is not a target id' % (one,))
    s = m.get('start')
    sp, sh = start_of(m)
    if sp and sh:
        sp = Path(str(sp).replace('~', str(HOME), 1))
        if not sp.exists(): add('WARN', 'start file missing: %s' % sp)
        elif sha256(sp) != sh: add('WARN', 'start sha256 mismatch: %s' % sp)
    elif s is not None:
        add('WARN', 'start has no path + sha256')
    pc = m.get('path_certified', 'unknown')
    if pc not in (True, False, 'unknown'):
        add('WARN', 'path_certified is %r (expected true, false or "unknown")' % (pc,))
    kf = kernel_flag(m, V, spec)
    if kf:
        note = ' '.join(str(m.get(k) or '') for k in ('path_note', 'path_certified_note', 'certification')).lower()
        if pc is True and any(w in note for w in ('trace', 'replay', 'accepted kernel states')):
            add('NOTE', kf + '; certified by a trace audit (rule 2): %s' % (m.get('path_note') or m.get('path_certified_note'))[:200])
        else:
            add('FLAG', kf + (' -- but the sidecar says path_certified true' if pc is True else ''))
    st = start_tuple(m, V); tg = {x['id']: x for x in spec['targets']}
    tids = m.get('target') if isinstance(m.get('target'), list) else [m.get('target')]
    dn = donor_state(m)
    if dn == 'no statement':
        add('WARN', 'donor_outside_limits %s without the builder statement that no complete circuit held, retained '
            'or output exceeded the A/AD limits (Ruling 18:45; fields %s)' % (m.get('donor_outside_limits'), ', '.join(DONOR_STATEMENT_KEYS)))
    for one in tids:
        if st and one in tg and (st[0] > tg[one]['A'] or st[1] > tg[one]['AD']) and dn != 'ok':
            add('WARN', 'start %s is outside %s hard limits A <= %d, AD <= %d (COMPLIANCE-1820 rule 1: starts inside A/AD; '
                'a construction needs donor_outside_limits + builder statement)%s'
                % ('/'.join(map(str, st)), one, tg[one]['A'], tg[one]['AD'],
                   '; sidecar path_note: %s' % m['path_note'] if m.get('path_note') else ''))
    return iss


DONOR_STATEMENT_KEYS = ('donor_note', 'donor_statement', 'builder_statement', 'retained_states', 'intermediate_states', 'statement')
DONOR_NOTE = 'construction from a donor outside the limits; all retained states within limits'


def donor_state(m):
    """Ruling 18:45: None (no donor_outside_limits), 'ok' (donor + builder statement), 'no statement'."""
    if not m or not m.get('donor_outside_limits'): return None
    return 'ok' if any(isinstance(m.get(k), str) and m.get(k).strip() for k in DONOR_STATEMENT_KEYS) else 'no statement'


KERNEL_WORDS = ('kernel', 'fdrive', '/bin/bfx', 'bfx-', 'bfx.c', 'hub/', 'scheduler', 'op_polish', 'op_trb', 'op_pull')


def caps_of(m):
    """Caps a sidecar states: method.caps / caps dicts, and --cap / --cap-gd / --cap-a / --cap-ad
    flags in the command.  Keys A, AD, GD."""
    import re
    caps = {}
    for d in ((m.get('method') or {}).get('caps') if isinstance(m.get('method'), dict) else None, m.get('caps')):
        if isinstance(d, dict):
            for k, v in d.items():
                K = str(k).upper().replace('CAP_', '').replace('CAP-', '')
                if K in ('A', 'AD', 'GD') and isinstance(v, int): caps[K] = min(v, caps.get(K, v))
    cmd = json.dumps(m.get('command') or '')
    for flag, K in (('--cap-ad', 'AD'), ('--cap-a', 'A'), ('--cap-gd', 'GD'), ('--cap', 'GD')):
        for v in re.findall(re.escape(flag) + r'[ =](\d+)', cmd):
            caps[K] = min(int(v), caps.get(K, int(v)))
    return caps


def start_tuple(m, V):
    """(A, AD, G, GD) of the sidecar's start file (verified, cached), else its stated tuple, else None."""
    sp, _ = start_of(m)
    if sp and V is not None:
        p = Path(str(sp).replace('~', str(HOME), 1))
        if p.exists() and is_circ(p):
            r = V.check(p, sha256(p))
            if r['ok']: return r['tuple']
    s = m.get('start')
    if isinstance(s, dict) and isinstance(s.get('tuple'), list): return s['tuple']
    return None


def kernel_flag(m, V, spec):
    """COMPLIANCE-1820: a kernel stage whose start is above one of its caps, with no repair_keep
    in the sidecar, may have left the A/AD limits on the way.  Returns a message or None."""
    text = json.dumps({k: m.get(k) for k in ('method', 'command', 'lineage')}).lower()    # not 'code': it lists binaries present
    if not any(w in text for w in KERNEL_WORDS): return None
    if 'repair_keep' in json.dumps(m).lower(): return None
    st = start_tuple(m, V)
    if st is None:
        return 'kernel stage, no repair_keep, start tuple unknown (cannot check start against caps)'
    caps = caps_of(m)
    tg = {x['id']: x for x in spec['targets']}
    tid = m.get('target'); tid = tid[0] if isinstance(tid, list) and tid else tid
    if tid in tg:
        caps.setdefault('A', tg[tid]['A']); caps.setdefault('AD', tg[tid]['AD'])
    over = ['%s %d > cap %d' % (K, st[i], caps[K]) for i, K in ((0, 'A'), (1, 'AD'), (3, 'GD')) if K in caps and st[i] > caps[K]]
    if over:
        return 'kernel stage with start %s above its caps (%s) and no repair_keep' % ('/'.join(map(str, st)), ', '.join(over))
    return None


def start_of(m):
    """(path, sha256) of a sidecar's start: {'path', 'sha256'} or a path with 'start_sha256'."""
    s = m.get('start')
    if isinstance(s, dict):
        return s.get('path') or s.get('file'), s.get('sha256')
    if isinstance(s, str):
        return s, m.get('start_sha256')
    return None, None


def orphan_sidecars():
    out = []
    for ad in sorted(CAMP.iterdir()):
        fd = ad / 'found'
        if ad.is_dir() and ad.name != 'L0' and fd.is_dir():
            for j in fd.rglob('*.json'):
                b = j.name[:-5]
                try:
                    jd = json.loads(j.read_text())
                    if not isinstance(jd, dict) or not {'target', 'aes_check', 'A'} & set(jd): continue   # not a sidecar (e.g. *.check.json)
                except (OSError, ValueError):
                    pass
                if not (j.with_name(b).exists() and b.endswith(CIRC_SUFFIXES)) and                         not any((j.with_name(b + s)).exists() for s in CIRC_SUFFIXES):
                    out.append((ad.name, j))
    return out


# ---- change detection --------------------------------------------------------------------------
def changes(prev, cur):
    """New strict / tradeoff frontier tuples per target since the previous ledger run."""
    out = []
    for tid, rep in cur['targets'].items():
        p = (prev or {}).get('targets', {}).get(tid, {})
        for fk, lab in (('strict_frontier', 'strict'), ('tradeoff_frontier', 'tradeoff')):
            old = {tuple(x['tuple']): str(x.get('path')) for x in p.get(fk, [])}
            for x in rep[fk]:
                t = tuple(x['tuple']); pa = str(x.get('path'))
                newly_cert = t in old and pa.startswith(CERT_OK) and not old[t].startswith(CERT_OK)
                if (t not in old or newly_cert) and not x['status'].startswith('known'):
                    out.append('%s %s %s %s [%s; path %s]%s %s' % (tid, lab, ' '.join(map(str, x['tuple'])), cls_txt(x),
                                                                   x['status'], pa, ' NEWLY CERTIFIED' if newly_cert else '', x['file']))
    for tid, rep in cur['targets'].items():                 # best certified strict moved
        b = rep.get('best_certified_strict_by_G'); pb = (prev or {}).get('targets', {}).get(tid, {}).get('best_certified_strict_by_G')
        if b and (not pb or pb['tuple'] != b['tuple']) and not b['status'].startswith('known'):
            out.append('%s best certified strict now %s [%s; path %s] %s' % (tid, tup(b['tuple']), b['status'], b.get('path'), b['file']))
    for r in cur['a_le_27']:
        if not any(r['sha256'] == q['sha256'] for q in (prev or {}).get('a_le_27', [])):
            out.append('A<=27 %s %s [%s]' % (' '.join(map(str, r['tuple'])), r['path'], r['status']))
    return out


# ---- rendering ---------------------------------------------------------------------------------
def tup(t): return '%d/%d/%d/%d' % tuple(t)


def short(p):
    s = str(p); h = str(HOME)
    return '~' + s[len(h):] if s.startswith(h) else s


def nist_cell(x):
    d = x['nist']['dominated_by']
    s = 'none' if not d else '%d: %s' % (len(d), ', '.join('%s (%s)' % (tup(u), n) for u, n in d[:3]) + (' ...' if len(d) > 3 else ''))
    if x['nist']['equal_tuple']: s += '; equal tuple: ' + ', '.join(x['nist']['equal_tuple'])
    return s


def row(x):
    v = x['nist']['vs_ref']
    return '| %s | %s | %+d / %+d | %s | %s | %s | %d | `%s` |' % (
        tup(x['tuple']), cls_txt(x), v['dG'], v['dGD'], x['status'], x.get('path'), nist_cell(x), x['structures'], short(x['file']))


def cls_txt(x):
    return x['class'] + (' (%s)' % x['claim'] if x.get('claim') else '')


HDR = '| A/AD/G/GD | class | vs ref dG / dGD | status | path | pinned NIST circuits dominating it | structures | file |\n|---|---|---|---|---|---|---|---|'


def detail(x, label):
    if x is None: return '- %s: none\n' % label
    s = '- %s: **%s** (%s), %s, path: %s, `%s` (sha256 %s)\n' % (label, tup(x['tuple']), cls_txt(x), x['status'], x.get('path'), short(x['file']), x['sha256'][:12])
    if x['source'].startswith('campaign'):
        st = x.get('start')
        st = (short(st.get('path')) + ' sha256 ' + str(st.get('sha256'))[:12]) if isinstance(st, dict) else st
        s += '  - start: %s; method: %s; seed: %s; elapsed: %s s\n' % (st, x.get('method'), x.get('seed'), x.get('elapsed_s'))
        s += '  - verification: %s; ledger re-check OK\n' % x.get('aes_check')
    else:
        s += '  - source: %s (archive); verification: ledger aes_check.check OK\n' % x['source']
    if x.get('same_as'): s += '  - same as baseline: %s\n' % x['same_as']
    s += '  - pinned NIST dominating: %s\n' % nist_cell(x)
    return s


def render(o, spec):
    L = []
    w = L.append
    w('# Ledger: campaign 2026-11-15-targets\n')
    w('Generated %s by `nonlinear/boolflux/campaigns/targets/ledger.py run` (%.1f s). Do not edit; rerun.\n'
      % (o['generated_utc'], o['elapsed_s']))
    ni = o['nist_integrity']
    w('- NIST pin %s: %d manifest files, %s. Comparison set: every forward AES S-box circuit in '
      '`nonlinear/nist/` (`aes_check.published()`: aes-sbox/, old-2020/, sbox/).' % (
          ni['commit'], ni['files'], 'all sha256 match' if not ni['mismatch'] else 'MISMATCH: %s' % ni['mismatch']))
    w('- Baseline ("known"): archive as of %s (built %s), %d files, %d verified AES S-box circuits.'
      % (o['baseline']['cutoff_utc'], o['baseline']['built_utc'], o['baseline']['n_files'], o['baseline']['n_verified']))
    s = o['scan']
    w('- Scanned: %d archive files, %d campaign files; %d verified OK (all 256 inputs, two verifiers, NIST library); '
      '%d checked this run; %d archive files are not forward AES S-box circuits or fail.' % (
          s['archive_files'], s['campaign_files'], s['verified_ok'], s['checked_this_run'], s['archive_not_aes_or_failed']))
    d = o['definitions']
    w('- Rules (from TARGETS.json, recomputed every run): hard A <= ref A, AD <= ref AD. strict: G <= ref G, GD <= ref GD, '
      'one strictly smaller. tradeoff gates_for_depth: ref GD < GD <= GD_max and G <= ref G - %d; depth_for_gates: GD <= GD_max '
      '(< ref GD) and ref G < G <= ref G + %d; and_depth_for_gates: AD < ref AD, AD <= max(AD_targets), G or GD above ref. '
      'Tradeoffs never dominate the reference.' % (d.get('min_gate_gain_for_depth_cost', 3), d.get('max_gate_cost_for_depth_gain', 8)))
    w('- Status: known = tuple realised by a baseline archive file; reproduced = campaign circuit structurally equal '
      '(hub.common.structure_key) or tuple-equal to a baseline circuit; new = neither. Evidence: every row is [C] for '
      '"this file computes the AES S-box with this (A, AD, G, GD)"; "new"/"dominated" are [C] relative to the scanned '
      'folders and the pinned set only.\n')
    if o['changes']:
        w('## Changes since the previous run\n')
        for c in o['changes']: w('- ' + c)
        w('')
    w('## Summary\n')
    w('"path" = search-path certification (COMPLIANCE-1820.md): certified | reproduced-certified (by FILE) | '
      'not certified | unknown (sidecar path_certified missing); n/a = archive start, not a campaign result. '
      'A strict or tradeoff point without a certified campaign file is a result "within limits; search path not certified".\n')
    w('| target | reference | best strict (by G) | best strict (by GD) | best strict, certified path or known | best tradeoff | (G,GD) frontier points |')
    w('|---|---|---|---|---|---|---|')
    for tid, r in o['targets'].items():
        ref = r['ref']
        bt = '; '.join('%s %s [%s; path %s]' % (k, tup(x['tuple']), x['status'], x.get('path')) for k, x in r['best_tradeoff'].items()) or '-'
        f = lambda x: '%s [%s; path %s]' % (tup(x['tuple']), x['status'], x.get('path')) if x else '-'
        w('| %s | %s | %s | %s | %s | %s | %d |' % (tid, tup((ref['A'], ref['AD'], ref['G'], ref['GD'])),
                                                    f(r['best_strict_by_G']), f(r['best_strict_by_GD']),
                                                    f(r.get('best_certified_strict_by_G')), bt, len(r['frontier_G_GD'])))
    w('')
    if o['a_le_27']:
        w('## VERIFIED CIRCUITS WITH A <= 27\n')
        for r in o['a_le_27']: w('- %s `%s` [%s]' % (tup(r['tuple']), short(r['path']), r['status']))
    else:
        w('## A <= 27\n\nNo verified circuit with A <= 27 in any scanned folder.')
    w('')
    if o['issues']:
        w('## Sidecar / verification issues (campaign found/ folders)\n')
        for i in sorted(o['issues'], key=lambda i: (i['level'] != 'FAIL', i['agent'], i['file'])):
            w('- **%s** %s `%s`: %s' % (i['level'], i['agent'], short(i['file']), i['issue']))
        w('')
    for tid, r in o['targets'].items():
        ref = r['ref']
        w('## %s: reference %s `%s`\n' % (tid, tup((ref['A'], ref['AD'], ref['G'], ref['GD'])), ref['ref']))
        w('Hard limits A <= %d, AD <= %d. Primary: %s. Ideal: %s. Tradeoffs allowed: %s.\n' % (
            ref['A'], ref['AD'], ref.get('primary'), ref.get('ideal'), ref.get('tradeoffs') or 'none'))
        w('%d verified files within the hard limits, %d distinct structures, %d distinct tuples.\n' % (
            r['n_files_within_limits'], r['n_structures'], r['n_tuples']))
        w(detail(r['best_strict_by_G'], 'Best strict (by G, then GD)'))
        if r['best_strict_by_GD'] and r['best_strict_by_G'] and r['best_strict_by_GD']['tuple'] != r['best_strict_by_G']['tuple']:
            w(detail(r['best_strict_by_GD'], 'Best strict (by GD, then G)'))
        if r['best_tradeoff']:
            for k, x in r['best_tradeoff'].items(): w(detail(x, 'Best tradeoff (%s)' % k))
        else:
            w('- Best tradeoff: none\n')
        w('\n### (G, GD) Pareto frontier within the hard limits\n')
        w(HDR)
        for x in r['frontier_G_GD']: w(row(x))
        w('\n### Strict improvements (Pareto in G, GD; smallest A, AD shown)\n')
        if r['strict_frontier']:
            w(HDR)
            for x in r['strict_frontier']: w(row(x))
        else:
            w('none')
        w('\n### Permitted tradeoffs (per kind, Pareto in G, GD; AND-depth kind: in AD, G, GD)\n')
        if r['tradeoff_frontier']:
            w(HDR)
            for x in r['tradeoff_frontier']: w(row(x))
        else:
            w('none')
        w('\n### (A, AD, G, GD) Pareto frontier within the hard limits (%d points)\n' % len(r['frontier_A_AD_G_GD']))
        w(HDR)
        for x in r['frontier_A_AD_G_GD']: w(row(x))
        if 'per_and_depth' in r:
            w('\n### Best per AND depth at A <= %d\n' % ref['A'])
            w('| AD | best G (then GD) at AD = d | status | best G at AD <= d | best GD (then G) at AD = d | status | (G,GD) frontier at AD = d |\n|---|---|---|---|---|---|---|')
            for dd, v in r['per_and_depth'].items():
                bg, bd, bl = v['best_G'], v['best_GD'], v['best_G_at_AD_le']
                w('| %s | %s | %s | %s | %s | %s | %s |' % (dd, tup(bg['tuple']) if bg else '-', bg['status'] if bg else '',
                                                   tup(bl['tuple']) if bl else '-',
                                                   tup(bd['tuple']) if bd else '-', bd['status'] if bd else '',
                                                   ', '.join(tup(t) for t in v['frontier_G_GD'])))
        w('\nPinned NIST (G, GD) frontier within the same hard limits: %s\n' % (
            ', '.join('%s %s' % (tup(u), n) for u, n in r['pinned_frontier_within_limits']) or 'none'))
    cr = o['campaign_results']
    w('## All campaign circuit files (%d)\n' % len(cr))
    if cr:
        w('| agent | file | ok | A/AD/G/GD | target | status | path | seed | elapsed_s | method |\n|---|---|---|---|---|---|---|---|---|---|')
        for r in sorted(cr, key=lambda r: (r['group'], r['path'])):
            m = r['meta']
            pth = r.get('cert') or 'unknown'
            if pth == 'reproduced-certified': pth += ' (by %s)' % Path(r.get('cert_by') or '').name
            if r.get('donor') == 'ok': pth += '; ' + DONOR_NOTE
            elif r.get('donor') == 'no statement': pth += '; donor outside limits, statement MISSING'
            w('| %s | `%s` | %s | %s | %s | %s | %s | %s | %s | %s |' % (
                r['group'], Path(r['path']).name, 'OK' if r['ok'] else 'FAIL', tup(r['tuple']) if r['tuple'] else '-',
                m.get('target'), r['status'] or '-', pth, m.get('seed'), m.get('elapsed_s'), str(m.get('method'))[:80]))
    return '\n'.join(L) + '\n'


def cmd_curate(a):
    """Plan (default) or perform (--apply) the copy of non-known campaign frontier / strict /
    tradeoff points of LEDGER.json into results/targets/<ID>/ (layout: results/targets/README.md).
    Uses the last LEDGER.json; run 'run' first.  Never overwrites an existing file."""
    o = json.loads((CAMP / 'LEDGER.json').read_text())
    dest_root = PKG / 'results' / 'targets'
    plan = []
    for tid, r in o['targets'].items():
        seen = set()
        for fk in ('strict_frontier', 'tradeoff_frontier', 'frontier_G_GD'):
            for x in r[fk]:
                if x['status'].startswith('known') or not x['source'].startswith('campaign') or x['sha256'] in seen:
                    continue
                seen.add(x['sha256'])
                agent = x['source'].split(':', 1)[1]
                base = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s-%s' % (*x['tuple'], tid, agent)
                k = 1
                while (dest_root / tid / ('%s-%d.circ.txt' % (base, k))).exists(): k += 1
                plan.append((tid, x, '%s-%d' % (base, k), fk))
    for tid, x, name, fk in plan:
        print('%s %s %-26s %s -> results/targets/%s/%s.circ.txt' % (tid, tup(x['tuple']), x['class'], short(x['file']), tid, name))
    if not a.apply:
        print('%d files planned (dry run; --apply copies them)' % len(plan)); return 0
    for tid, x, name, fk in plan:
        src = Path(x['file']); d = dest_root / tid; lg = d / 'logs' / name
        lg.mkdir(parents=True, exist_ok=True)
        if src.name.endswith('.bfx'):
            c, txt = aes_check.load(src)
            (d / (name + '.circ.txt')).write_text(txt)
        else:
            (d / (name + '.circ.txt')).write_bytes(src.read_bytes())
        sj, sc = sidecar_of(src)
        if sj: (d / (name + '.json')).write_bytes(sj.read_bytes())
        res = aes_check.check(str(d / (name + '.circ.txt')))
        (lg / 'aes_check.json').write_text(json.dumps(res, indent=1) + '\n')
        found = {'circuit': name + '.circ.txt', 'target': tid, 'tuple': x['tuple'], 'class': x['class'],
                 'status': x['status'], 'ledger_list': fk, 'source_file': str(src), 'source_sha256': x['sha256'],
                 'curated_utc': utc(time.time()), 'sidecar': sc, 'nist': x['nist'],
                 'logs': ['aes_check.json', 'REPRODUCE.md']}
        (lg / 'found.json').write_text(json.dumps(found, indent=1) + '\n')
        m = sc or {}
        sp, sh = start_of(m)
        (lg / 'REPRODUCE.md').write_text(
            '# Reproduce %s (%s, A/AD/G/GD = %s)\n\n```bash\npython3 nonlinear/boolflux/campaigns/aes_check.py '
            'nonlinear/boolflux/results/targets/%s/%s.circ.txt\n```\n\n- class: %s; status: %s; pinned NIST dominating: %s\n'
            '- start: `%s` (sha256 %s)\n- method: %s\n- code: %s\n- seed: %s; found after %s s; found %s\n'
            '- reproduction: %s\n\n## Re-run\n\n```bash\n%s\n```\n' % (
                name, tid, tup(x['tuple']), tid, name, x['class'], x['status'], nist_cell(x), sp, sh,
                m.get('method'), json.dumps(m.get('code')), m.get('seed'), m.get('elapsed_s'), m.get('utc'),
                m.get('reproduction', 'not stated in the sidecar'), m.get('command')))
        print('copied %s/%s (%s)' % (tid, name, 'OK' if res['ok'] else 'FAIL'))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog='ledger.py', description=__doc__.split('\n\n')[0])
    sp = ap.add_subparsers(dest='cmd', required=True)
    b = sp.add_parser('baseline', help='build the archive baseline once (refuses to overwrite)')
    b.add_argument('--cutoff', default=CUTOFF_DEFAULT); b.add_argument('--force', action='store_true')
    sp.add_parser('run', help='scan, verify (cached), classify, write LEDGER.md / LEDGER.json')
    c = sp.add_parser('curate', help='plan (or --apply) the copy of new campaign points into results/targets/')
    c.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    return {'baseline': cmd_baseline, 'run': cmd_run, 'curate': cmd_curate}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
