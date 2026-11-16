#!/usr/bin/env python3
"""Result ledger of campaign 2026-11-15-targets (ten NIST AES S-box targets T01..T10, plus Z).

    python3 nonlinear/boolflux/campaigns/targets/ledger.py baseline   # once, before results arrive
    python3 nonlinear/boolflux/campaigns/targets/ledger.py snapshot   # once: "known-by-23:50" (phase 2)
    python3 nonlinear/boolflux/campaigns/targets/ledger.py run        # any time; idempotent
    python3 nonlinear/boolflux/campaigns/targets/ledger.py curate [--apply]

Phase 2 (L1, 2026-11-16; README.md "Phase 2"): night runs <night>/<run>/found/ scanned too;
labels known (15:20 archive) / known-by-23:50 (the 11-15 campaign) / new (night); search-path
certification informational only; notable lines T03 G <= 123, T05 G <= 102 at any GD.

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
# phase 2 (BRIEF2): the overnight runs of 2026-11-16 save into <night>/<run>/found/
NIGHT = Path(os.environ.get('LEDGER_NIGHT', HOME / 'xs-campaigns' / '2026-11-16-night'))
# LEDGER.md / LEDGER.json / history go to LEDGER_OUT (default: the campaign folder); a dry run
# (campaigns/targets/morning.sh --dry-run) points it elsewhere so the campaign's ledger is untouched
OUT = Path(os.environ.get('LEDGER_OUT', CAMP))
STATE = CAMP / 'L0'
CACHE = STATE / 'cache' / 'verify.json'
BASELINE = STATE / 'baseline' / 'baseline.json'
CUTOFF_DEFAULT = '2026-11-15T15:20:00Z'
# second snapshot (L1, 2026-11-16): archive + campaign files as of 23:50 UTC, the end of the
# first campaign day.  Labels: known (archive at 15:20) / known-by-23:50 (the 11-15 campaign) / new
SNAP2 = STATE / 'baseline' / 'known-by-2350.json'
SNAP2_CUTOFF = '2026-11-15T23:50:00Z'
SNAP2_LABEL = 'known-by-23:50'
# "notable" lines (BRIEF2 decision 4, user 23:50 UTC): any G <= n at any GD within the hard limits.
# TARGETS.json may override per target with "notable_G_max".
NOTABLE_DEFAULT = {'T03': 123, 'T05': 102}
NOTABLE_NOTE = {'T03': 'beats the pinned 124/27', 'T05': 'a new overall gate-count record'}

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


def found_dirs():
    """(group, folder) of every campaign found/ folder: <campaign>/<agent>/found (group = agent)
    and <night>/<run>/found (group = 'night:<run>')."""
    out = []
    for base, pre in ((CAMP, ''), (NIGHT, 'night:')):
        if not base.is_dir(): continue
        for ad in sorted(base.iterdir()):
            fd = ad / 'found'
            if ad.is_dir() and ad.name != 'L0' and fd.is_dir():
                out.append((pre + ad.name, fd))
    return out


def campaign_files():
    """(group, path) of every circuit file in the campaign found/ folders (recursive)."""
    out = []
    for g, fd in found_dirs():
        out += [(g, p) for p in sorted(fd.rglob('*')) if is_circ(p)]
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


def cmd_snapshot(a):
    """Second snapshot "known-by-23:50": every archive AND campaign found/ circuit file whose mtime
    (hub archive: t_admit) is <= the cut-off.  Files there that are not in the 15:20 baseline are
    the 11-15 campaign's results; files after it (the night runs) are "new"."""
    if SNAP2.exists() and not a.force:
        print('snapshot exists (%s); not rewritten (use --force)' % SNAP2); return 0
    cut = parse_utc(a.cutoff)
    V = Verifier(); rows = []; skipped = 0; t0 = time.time()
    for kind, files in (('archive', archive_files()), ('campaign', campaign_files())):
        for g, p in files:
            st = p.stat()
            ta = hub_t_admit(p) if g == 'hub-long' else None
            when = ta if ta is not None else st.st_mtime
            if when > cut:
                skipped += 1; continue
            d = sha256(p); r = V.check(p, d)
            rows.append({'kind': kind, 'group': g, 'path': str(p), 'sha256': d, 'mtime': utc(st.st_mtime),
                         't_admit': utc(ta) if ta else None, 'ok': r['ok'], 'tuple': r['tuple'], 'skey': r.get('skey')})
    V.save()
    doc = {'label': SNAP2_LABEL, 'cutoff_utc': a.cutoff, 'built_utc': utc(time.time()), 'fingerprint': V.fp,
           'rule': 'archive and campaign found/ circuit files with mtime (hub archive: t_admit) <= cutoff',
           'sources': [str(d) for _, d, _ in ARCHIVE_SOURCES] + [str(STUDY / '*' / 'found'), str(CAMP / '*' / 'found'),
                                                                 str(NIGHT / '*' / 'found')],
           'raw_listing': 'L1/snapshot-2350/filelist-2350-relevant.tsv (find at 23:50:10 UTC: path, mtime, size)',
           'n_files': len(rows), 'n_after_cutoff_skipped': skipped,
           'n_verified': sum(1 for r in rows if r['ok']), 'rows': rows}
    atomic_write(SNAP2, json.dumps(doc, indent=0))
    print('snapshot %s: %d files (%d campaign, %d verified), %d after cut-off skipped, %d checks, %.0f s -> %s'
          % (SNAP2_LABEL, len(rows), sum(r['kind'] == 'campaign' for r in rows), doc['n_verified'], skipped,
             V.new, time.time() - t0, SNAP2))
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
    # a tradeoff entry may override the global thresholds ("min_gate_gain" / "max_gate_cost");
    # when several kinds apply, the gate-saving kind wins (T05: a circuit with fewer gates, more
    # depth and lower AND depth is a gate record first)
    pri = {'gates_for_depth': 0, 'depth_for_gates': 1, 'and_depth_for_gates': 2}
    for tr in sorted(tgt.get('tradeoffs', []), key=lambda tr: pri.get(tr['kind'], 9)):
        k = tr['kind']
        gain = tr.get('min_gate_gain', defs.get('min_gate_gain_for_depth_cost', 3))
        cost = tr.get('max_gate_cost', defs.get('max_gate_cost_for_depth_gain', 8))
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

    snap = json.loads(SNAP2.read_text()) if SNAP2.exists() else None
    snap_sha, snap_skey, snap_tuple = set(), {}, {}
    for r in (snap or {}).get('rows', []):
        snap_sha.add(r['sha256'])
        if r['ok']:
            snap_skey.setdefault(r['skey'], r['path']); snap_tuple.setdefault(tuple(r['tuple']), r['path'])
    for r in recs:                                      # provenance per file
        r['in_snap2'] = r['sha256'] in snap_sha
        if not r['ok']: r['status'] = None; continue
        if r['baseline']: r['status'] = 'known'; continue
        k, t = r.get('skey'), tuple(r['tuple'])
        if k in base_skey: r['status'] = 'reproduced'; r['same_as'] = {'structure': base_skey[k]}
        elif t in base_tuple: r['status'] = 'reproduced'; r['same_as'] = {'tuple': base_tuple[t]}
        elif r['in_snap2']: r['status'] = SNAP2_LABEL
        elif k in snap_skey: r['status'] = 'reproduced-' + SNAP2_LABEL; r['same_as'] = {'structure': snap_skey[k]}
        elif t in snap_tuple: r['status'] = 'reproduced-' + SNAP2_LABEL; r['same_as'] = {'tuple': snap_tuple[t]}
        else: r['status'] = 'new'
    certify(recs)
    ok = [r for r in recs if r['ok']]

    out = {'generated_utc': utc(time.time()), 'campaign': str(CAMP), 'night': str(NIGHT), 'nist_pin': spec.get('nist_pin'),
           'nist_integrity': nist_check, 'baseline': {k: base[k] for k in ('cutoff_utc', 'built_utc', 'n_files', 'n_verified')},
           'snapshot2': ({k: snap[k] for k in ('label', 'cutoff_utc', 'built_utc', 'n_files', 'n_verified')}
                         if snap else None),
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
    prev_f = OUT / 'LEDGER.json'
    if not prev_f.exists() and OUT != CAMP: prev_f = CAMP / 'LEDGER.json'     # dry run: changes vs the campaign's ledger
    if prev_f.exists():
        try: prev = json.loads(prev_f.read_text())
        except ValueError: prev = None
    out['changes'] = changes(prev, out)
    atomic_write(OUT / 'LEDGER.json', json.dumps(out, indent=1))
    atomic_write(OUT / 'LEDGER.md', render(out, spec))
    hist = (STATE if OUT == CAMP else OUT) / 'history'; hist.mkdir(parents=True, exist_ok=True)
    stamp = out['generated_utc'].replace(':', '').replace('-', '')
    atomic_write(hist / ('LEDGER-%s.json' % stamp), json.dumps(out))
    nfail = sum(1 for i in issues if i['level'] == 'FAIL')
    print('ledger: %d files (%d verified, %d checked now), %d issues (%d FAIL, %d WARN, %d informational), %.1f s -> %s'
          % (len(recs), len(ok), V.new, len(issues), nfail, sum(1 for i in issues if i['level'] == 'WARN'),
             sum(1 for i in issues if i['level'] in INFO_LEVELS), out['elapsed_s'], OUT / 'LEDGER.md'))
    if not snap:
        print('NOTE no %s snapshot (%s): "ledger.py snapshot" builds it; until then the 11-15 campaign and the '
              'night are both labelled new' % (SNAP2_LABEL, SNAP2))
    for c in out['changes']:
        print('CHANGE', c)
    for i in issues:
        if i['level'] == 'FAIL': print('FAIL', i['agent'], i['file'], i['issue'])
    return 1 if (nfail and a.strict) else 0


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
    d = {k: r.get(k) for k in ('kind', 'group', 'path', 'sha256', 'tuple', 'status', 'same_as', 'skey', 'cert', 'cert_by', 'donor', 'in_snap2')}
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
    else the best certification among its campaign files.  Informational only from 2026-11-15
    23:50 UTC (BRIEF2 decision 2): 'claim' is always None, nothing is demoted by the path."""
    return dict(_path_of_tuple(rows, cls), claim=None)


def _path_of_tuple(rows, cls):
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
    """(status, representative file, era) of a tuple from the files that realise it.
    era 'archive': a 15:20 baseline file realises it (status 'known'); era 'campaign-11-15': a
    file of the 23:50 snapshot does (status 'known-by-23:50 (<agent>; new vs archive)'); era
    'new': only files after 23:50 (the night runs), status 'new (<group>)'."""
    pri = {'results-aes': 0, 'best-1400': 1, 'hub-long': 3}
    known = sorted([r for r in rows if r['status'] == 'known'], key=lambda r: (pri.get(r['group'], 2), r['path']))
    when = lambda r: ((r.get('meta') or {}).get('utc') or r['mtime'])
    camp = sorted([r for r in rows if r['kind'] == 'campaign'], key=when)
    post = [r for r in rows if r['kind'] == 'archive' and not r['baseline']]
    today = [r for r in camp if r.get('in_snap2')]
    later = [r for r in camp if not r.get('in_snap2')]
    # representative file: among campaign files of the tuple, a certified search path wins the tie
    # (coordinator 2026-11-16, DOCS-TODO 32.1: the cleaner record), then the earliest; the status
    # still names the agent of the earliest file.  Among certified files: scan order (found/ folders,
    # sorted paths), the order the path column uses, so the two name the same file; else the earliest
    pref = lambda rs: sorted(rs, key=lambda r: (0, rows.index(r), '') if str(r.get('cert', '')).startswith(CERT_OK) else (1, 0, when(r)))
    if known:
        st, era = 'known', 'archive'
        if camp: st += '; reproduced by ' + ', '.join(sorted({r['group'] for r in camp}))
        rep = known[0]
    elif today or any(r.get('in_snap2') for r in post):
        era = 'campaign-11-15'
        src = today[0]['group'] if today else 'archive after the 15:20 cut-off: %s' % next(r for r in post if r.get('in_snap2'))['group']
        st = '%s (%s; new vs archive)' % (SNAP2_LABEL, src)
        if later: st += '; reproduced by ' + ', '.join(sorted({r['group'] for r in later}))
        rep = (pref(today) or [r for r in post if r.get('in_snap2')])[0]
    elif camp:
        st, era = 'new (%s)' % camp[0]['group'], 'new'
        if any(r['status'] == 'reproduced' for r in camp): st, era = 'reproduced', 'archive'   # (baseline file since removed)
        rep = pref(camp)[0]
    elif post:
        st, era = 'new (archive after cut-off: %s)' % post[0]['group'], 'new'
        rep = post[0]
    else:
        st, era, rep = '?', None, rows[0]
    return st, rep, era


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
        rows = by_t[t]; st, rep, era = prov_of_tuple(t, rows)
        cls, kind = classify(t, tgt, defs)
        m = rep.get('meta') or {}
        return {'tuple': list(t), 'class': cls if kind is None else 'tradeoff:' + kind, 'status': st, 'era': era,
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
    n = notable_max(tgt)
    if n is not None:
        nt = [t for t in ts if t[2] <= n]
        rep['notable'] = {'G_max': n, 'rule': 'G <= %d at any GD within the hard limits (BRIEF2 decision 4, user 23:50 UTC%s)'
                                              % (n, '; ' + NOTABLE_NOTE[tgt['id']] if tgt['id'] in NOTABLE_NOTE else ''),
                          'best': point(min(nt, key=lambda t: (t[2], t[3], t[0], t[1]))) if nt else None,
                          'points': [point(t) for t in front_by(nt, lambda t: (t[2], t[3]))]}
    return rep


def notable_max(tgt):
    """G threshold of the target's "notable" line (TARGETS.json notable_G_max, else NOTABLE_DEFAULT)."""
    return tgt.get('notable_G_max', NOTABLE_DEFAULT.get(tgt['id']))


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
        add('INFO', 'path_certified is %r (expected true, false or "unknown")' % (pc,))
    kf = kernel_flag(m, V, spec)
    if kf:
        note = ' '.join(str(m.get(k) or '') for k in ('path_note', 'path_certified_note', 'certification')).lower()
        if pc is True and any(w in note for w in ('trace', 'replay', 'accepted kernel states')):
            add('NOTE', kf + '; certified by a trace audit (rule 2): %s' % (m.get('path_note') or m.get('path_certified_note'))[:200])
        else:
            add('INFO', kf + (' -- but the sidecar says path_certified true' if pc is True else ''))
    st = start_tuple(m, V); tg = {x['id']: x for x in spec['targets']}
    tids = m.get('target') if isinstance(m.get('target'), list) else [m.get('target')]
    dn = donor_state(m)
    if dn == 'no statement':
        add('INFO', 'donor_outside_limits %s without the builder statement that no complete circuit held, retained '
            'or output exceeded the A/AD limits (Ruling 18:45; fields %s)' % (m.get('donor_outside_limits'), ', '.join(DONOR_STATEMENT_KEYS)))
    for one in tids:
        if st and one in tg and (st[0] > tg[one]['A'] or st[1] > tg[one]['AD']) and dn != 'ok':
            add('INFO', 'start %s is outside %s hard limits A <= %d, AD <= %d (COMPLIANCE-1820 rule 1: starts inside A/AD; '
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


INFO_LEVELS = ('INFO', 'NOTE')          # search-path items: informational from 23:50 UTC (BRIEF2 decision 2)


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
    p = m.get('parent')                              # night operators (BRIEF2 contract): parent file + sha256
    if isinstance(p, dict):
        return p.get('path') or p.get('file'), p.get('sha256')
    if isinstance(p, str):
        return p, m.get('parent_sha256')
    return None, None


def orphan_sidecars():
    out = []
    for g, fd in found_dirs():
        for j in fd.rglob('*.json'):
            b = j.name[:-5]
            try:
                jd = json.loads(j.read_text())
                if not isinstance(jd, dict) or not {'target', 'aes_check', 'A'} & set(jd): continue   # not a sidecar (e.g. *.check.json)
            except (OSError, ValueError):
                pass
            if not (j.with_name(b).exists() and b.endswith(CIRC_SUFFIXES)) and \
                    not any((j.with_name(b + s)).exists() for s in CIRC_SUFFIXES):
                out.append((g, j))
    return out


# ---- change detection --------------------------------------------------------------------------
def changes(prev, cur):
    """New strict / tradeoff frontier tuples per target since the previous ledger run."""
    out = []
    for tid, rep in cur['targets'].items():
        p = (prev or {}).get('targets', {}).get(tid, {})
        lists = [('strict_frontier', 'strict'), ('tradeoff_frontier', 'tradeoff')]
        for fk, lab in lists + [('notable', 'notable')]:
            if fk == 'notable':
                cl = (rep.get('notable') or {}).get('points', []); pl = ((p.get('notable') or {}).get('points', []))
            else:
                cl, pl = rep[fk], p.get(fk, [])
            old = {tuple(x['tuple']) for x in pl}
            for x in cl:
                t = tuple(x['tuple'])
                if t not in old and not is_archive(x):
                    out.append('%s %s %s %s [%s; path %s (informational)] %s' % (
                        tid, lab, ' '.join(map(str, x['tuple'])), cls_txt(x), x['status'], x.get('path'), x['file']))
    for r in cur['a_le_27']:
        if not any(r['sha256'] == q['sha256'] for q in (prev or {}).get('a_le_27', [])):
            out.append('A<=27 %s %s [%s]' % (' '.join(map(str, r['tuple'])), r['path'], r['status']))
    return out


def is_archive(x):
    """A ledger point realised by the 15:20 archive baseline (era 'archive'; older LEDGER.json
    without 'era': status 'known...')."""
    return x.get('era') == 'archive' if 'era' in x else str(x.get('status', '')).startswith('known')


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
    s2 = o.get('snapshot2')
    if s2:
        w('- Second snapshot ("%s"): archive and campaign found/ files as of %s (built %s), %d files, %d verified: '
          'the results of the 2026-11-15 campaign day. Night runs: `%s/*/found/`.'
          % (s2['label'], s2['cutoff_utc'], s2['built_utc'], s2['n_files'], s2['n_verified'], short(o.get('night'))))
    else:
        w('- Second snapshot (%s): MISSING (`ledger.py snapshot`); 11-15 campaign and night results are both labelled new.' % SNAP2_LABEL)
    s = o['scan']
    w('- Scanned: %d archive files, %d campaign files; %d verified OK (all 256 inputs, two verifiers, NIST library); '
      '%d checked this run; %d archive files are not forward AES S-box circuits or fail.' % (
          s['archive_files'], s['campaign_files'], s['verified_ok'], s['checked_this_run'], s['archive_not_aes_or_failed']))
    d = o['definitions']
    w('- Rules (from TARGETS.json, recomputed every run): hard A <= ref A, AD <= ref AD on every recorded result (search '
      'states may exceed the caps, user 23:50 UTC). strict: G <= ref G, GD <= ref GD, '
      'one strictly smaller. tradeoff gates_for_depth: ref GD < GD <= GD_max and G <= ref G - %d; depth_for_gates: GD <= GD_max '
      '(< ref GD) and ref G < G <= ref G + %d; and_depth_for_gates: AD < ref AD, AD <= max(AD_targets), G or GD above ref '
      '(a circuit matching several kinds takes gates_for_depth first). Tradeoffs never dominate the reference. '
      'Notable: %s.' % (d.get('min_gate_gain_for_depth_cost', 3), d.get('max_gate_cost_for_depth_gain', 8),
                        '; '.join('%s G <= %d at any GD' % (tid, r['notable']['G_max']) for tid, r in o['targets'].items()
                                  if r.get('notable')) or 'none'))
    w('- Status: known = tuple realised by a 15:20 baseline archive file; reproduced = campaign circuit structurally equal '
      '(hub.common.structure_key) or tuple-equal to a baseline circuit; %s = first realised by the 11-15 campaign '
      '(a file of the 23:50 snapshot; new against the archive); new = first realised after 23:50 (night runs). '
      'Evidence: every row is [C] for '
      '"this file computes the AES S-box with this (A, AD, G, GD)"; "new"/"dominated" are [C] relative to the scanned '
      'folders and the pinned set only.' % SNAP2_LABEL)
    w('- Search path ("path" columns): certified | reproduced-certified | not certified | unknown (COMPLIANCE-1820.md); '
      '**informational only** from 23:50 UTC (BRIEF2 decision 2): it never demotes a result.\n')
    if o['changes']:
        w('## Changes since the previous run\n')
        for c in o['changes']: w('- ' + c)
        w('')
    w('## Summary\n')
    w('| target | reference | best strict (by G) | best strict (by GD) | best tradeoff | notable (any GD) | (G,GD) frontier points |')
    w('|---|---|---|---|---|---|---|')
    for tid, r in o['targets'].items():
        ref = r['ref']
        bt = '; '.join('%s %s [%s]' % (k, tup(x['tuple']), x['status']) for k, x in r['best_tradeoff'].items()) or '-'
        f = lambda x: '%s [%s]' % (tup(x['tuple']), x['status']) if x else '-'
        nb = r.get('notable')
        nc = '-' if not nb else ('G <= %d: %s' % (nb['G_max'], f(nb['best']) if nb['best'] else 'none'))
        w('| %s | %s | %s | %s | %s | %s | %d |' % (tid, tup((ref['A'], ref['AD'], ref['G'], ref['GD'])),
                                                    f(r['best_strict_by_G']), f(r['best_strict_by_GD']),
                                                    bt, nc, len(r['frontier_G_GD'])))
    w('')
    if o['a_le_27']:
        w('## VERIFIED CIRCUITS WITH A <= 27\n')
        for r in o['a_le_27']: w('- %s `%s` [%s]' % (tup(r['tuple']), short(r['path']), r['status']))
    else:
        w('## A <= 27\n\nNo verified circuit with A <= 27 in any scanned folder.')
    w('')
    main_iss = [i for i in o['issues'] if i['level'] not in INFO_LEVELS]
    info_iss = [i for i in o['issues'] if i['level'] in INFO_LEVELS]
    if main_iss:
        w('## Sidecar / verification issues (campaign found/ folders)\n')
        for i in sorted(main_iss, key=lambda i: (i['level'] != 'FAIL', i['agent'], i['file'])):
            w('- **%s** %s `%s`: %s' % (i['level'], i['agent'], short(i['file']), i['issue']))
        w('')
    if info_iss:
        w('## Search-path notes (informational only from 23:50 UTC; not rules)\n')
        for i in sorted(info_iss, key=lambda i: (i['agent'], i['file'])):
            w('- %s %s `%s`: %s' % (i['level'], i['agent'], short(i['file']), i['issue']))
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
        nb = r.get('notable')
        if nb:
            w(detail(nb['best'], 'Notable (%s)' % nb['rule']))
            if len(nb['points']) > 1:
                w('  - all notable (G, GD) Pareto points: %s\n' % ', '.join('%s [%s]' % (tup(x['tuple']), x['status']) for x in nb['points']))
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
    """Plan (default) or perform (--apply) the curation of LEDGER.json into results/targets/<ID>/
    (layout: results/targets/README.md).  Uses the last LEDGER.json; run 'run' first.

    Selection: every campaign point not realised by the 15:20 archive (era != 'archive': the 11-15
    campaign and the night) on a target's strict, tradeoff, notable or (G, GD) frontier list, as the
    ledger's representative file of the tuple (a certified search path wins a tie).  A source
    circuit already curated for that target (same source sha256) is not copied again; a curated
    entry of the same tuple from another source file is REPLACED by the representative (the old
    entry is named in found.json 'replaces'; git history keeps its files).
    Refresh (--apply, every curated entry, idempotent): sidecar corrections from corrections.json
    (curated copy only, <field>_original kept); class fields of the folder's target (class strict /
    tradeoff / other, class_kind, class_target, notable, class_rule; a different class the agent
    wrote is kept as class_agent); header comments of the circuit (Not a NIST-issued circuit /
    Found by / Started from / Logs; comments only, re-verified with aes_check); logs/<name>/:
    start.circ.txt (copy of the start when it is not in this repository; .bfx converted to NCFF),
    command.sh (the recorded command, repository paths as $REPO), REPRODUCE.md, aes_check.json,
    found.json."""
    o = json.loads((OUT / 'LEDGER.json').read_text())
    dest_root = PKG / 'results' / 'targets'
    cert_of = {r['sha256']: r.get('cert') for r in o.get('campaign_results', [])}
    plan = []
    for tid, r in o['targets'].items():
        idx = curated_index(dest_root / tid)
        have = {e['source_sha256'] for e in idx} | {e['circuit_sha256'] for e in idx}
        seen, taken = set(), set()
        for fk in ('strict_frontier', 'tradeoff_frontier', 'notable', 'frontier_G_GD'):
            lst = (r.get('notable') or {}).get('points', []) if fk == 'notable' else r[fk]
            for x in lst:
                if is_archive(x) or not x['source'].startswith('campaign') or x['sha256'] in seen:
                    continue
                seen.add(x['sha256'])
                if x['sha256'] in have:
                    continue
                old = [e for e in idx if list(e['tuple']) == list(x['tuple']) and e['name'] not in taken]
                # an existing entry of the tuple whose source has a certified path stays (no churn
                # between equally clean files); an uncertified one is replaced by the representative
                if old and any(str(cert_of.get(e['source_sha256'], '')).startswith(CERT_OK) for e in old) \
                        or (old and not str(x.get('path', '')).startswith(CERT_OK)):
                    continue
                taken |= {e['name'] for e in old}
                agent = x['source'].split(':', 1)[1].replace(':', '-')
                base = 'aes-sbox-a%d-ad%d-g%d-gd%d-%s-%s' % (*x['tuple'], tid, agent)
                k = 1
                while ((dest_root / tid / ('%s-%d.circ.txt' % (base, k))).exists()
                       and '%s-%d' % (base, k) not in {e['name'] for e in old}) or \
                        any(p[2] == '%s-%d' % (base, k) for p in plan if p[0] == tid):
                    k += 1
                plan.append((tid, x, '%s-%d' % (base, k), fk, old))
    for tid, x, name, fk, old in plan:
        print('%s %s %-26s %s -> results/targets/%s/%s.circ.txt%s' % (
            tid, tup(x['tuple']), x['class'], short(x['file']), tid, name,
            ' (replaces %s)' % ', '.join(e['name'] for e in old) if old else ''))
    print('%d files planned (%d replace an entry of the same tuple)%s' % (
        len(plan), sum(1 for p in plan if p[4]), '' if a.apply else '; dry run: --apply copies them and refreshes every entry'))
    if not a.apply:
        return 0
    bad = 0
    for tid, x, name, fk, old in plan:
        src = Path(x['file']); d = dest_root / tid; lg = d / 'logs' / name
        rep_old = []
        for e in old:                                   # remove the replaced entry (git keeps it)
            rep_old.append({'name': e['name'], 'source_file': e.get('source_file'), 'source_sha256': e['source_sha256'],
                            'reason': 'same tuple; the ledger representative (certified search path first, then earliest) is %s'
                                      % short(src)})
            for f in (d / (e['name'] + '.circ.txt'), d / (e['name'] + '.json')):
                if f.exists(): f.unlink()
            ld = d / 'logs' / e['name']
            if ld.is_dir():
                for f in sorted(ld.rglob('*'), reverse=True):
                    f.unlink() if f.is_file() else f.rmdir()
                ld.rmdir()
        lg.mkdir(parents=True, exist_ok=True)
        if src.name.endswith('.bfx'):
            c, txt = aes_check.load(src)
            (d / (name + '.circ.txt')).write_text(txt)
        else:
            (d / (name + '.circ.txt')).write_bytes(src.read_bytes())
        sj, sc = sidecar_of(src)
        if sj: (d / (name + '.json')).write_bytes(sj.read_bytes())
        else:                                           # no campaign sidecar: a minimal one (the class fields follow)
            A, AD, G, GD = x['tuple']
            (d / (name + '.json')).write_text(json.dumps({
                'target': tid, 'A': A, 'AD': AD, 'G': G, 'GD': GD, 'source_file': short(src), 'source_sha256': x['sha256'],
                'note': 'the campaign file had no sidecar; written by ledger.py curate'}, indent=1) + '\n')
        found = {'circuit': name + '.circ.txt', 'target': tid, 'tuple': x['tuple'], 'class': x['class'],
                 'status': x['status'], 'era': x.get('era'), 'ledger_list': fk, 'source_file': short(src),
                 'source_sha256': x['sha256'], 'source_path_certified': x.get('path'),
                 'curated_utc': utc(time.time()), 'sidecar': sc, 'nist': x['nist']}
        if rep_old: found['replaces'] = rep_old
        (lg / 'found.json').write_text(json.dumps(found, indent=1) + '\n')
        print('copied %s/%s%s' % (tid, name, ' (replaced %s)' % ', '.join(e['name'] for e in old) if old else ''))
    n, bad2 = refresh_curated(o, dest_root)
    print('refreshed %d curated entries (sidecar class fields and corrections, circuit header, logs); %d failed verification'
          % (n, bad2))
    return 1 if (bad or bad2) else 0


def curated_index(d):
    """Curated entries of results/targets/<ID>/: name, tuple, source and circuit sha256."""
    out = []
    if not d.is_dir(): return out
    for f in sorted(d.glob('*.circ.txt')):
        name = f.name[:-len('.circ.txt')]
        fj = d / 'logs' / name / 'found.json'
        try: fd = json.loads(fj.read_text()) if fj.exists() else {}
        except ValueError: fd = {}
        t = fd.get('tuple')
        if not t:
            import re
            m = re.match(r'aes-sbox-a(\d+)-ad(\d+)-g(\d+)-gd(\d+)-', f.name)
            t = [int(v) for v in m.groups()] if m else None
        out.append({'name': name, 'tuple': t, 'source_sha256': fd.get('source_sha256'), 'source_file': fd.get('source_file'),
                    'circuit_sha256': sha256(f)})
    return out


def curated_sources(d):
    """sha256 of every source circuit already curated in results/targets/<ID>/."""
    return {e['source_sha256'] for e in curated_index(d)} | {e['circuit_sha256'] for e in curated_index(d)}


def load_corrections():
    f = HERE / 'corrections.json'
    return json.loads(f.read_text()).get('corrections', []) if f.exists() else []


def apply_corrections(sd, source_file, source_sha, corr):
    """Sidecar dict with the corrections whose match names this source (basename or sha256)."""
    new = dict(sd)
    for c in corr:
        m = c.get('match') or {}
        if m.get('source_basename') not in (None, Path(str(source_file or '')).name) or \
                m.get('source_sha256') not in (None, source_sha):
            continue
        if not m: continue
        for k, v in (c.get('set') or {}).items():
            if new.get(k) != v:
                new.setdefault(k + '_original', sd.get(k))
                new[k] = v
        for k in ('method_corrected_by', 'reason'):
            if c.get(k): new['correction_' + k if k == 'reason' else k] = c[k]
    return new


HEADER_KEYS = ('% Not a NIST-issued circuit', '% Found by:', '% Started from:', '% Logs:')


def with_header(text, lines):
    """NCFF text with the curation header comment lines (replacing an earlier set): inserted
    before the first comment line after 'begin circuit', else before 'Inputs:'."""
    L = [l for l in text.split('\n') if not l.strip().startswith(HEADER_KEYS)]
    b = next((i for i, l in enumerate(L) if l.startswith('begin circuit')), None)
    if b is None: return text
    j = next((i for i in range(b + 1, len(L)) if L[i].strip().startswith('%') or L[i].startswith('Inputs:')), b + 1)
    if L[j].startswith('Inputs:'):
        ins = ['  ' + s for s in lines] + ['']
    else:
        ins = ['  ' + s for s in lines]
    return '\n'.join(L[:j] + ins + L[j:])


def repo_rel(p):
    """Repository-relative path when p is inside this repository (or the campaign machine's
    ~/xcr-boolflux), else ~/... ."""
    s = str(p).replace('~', str(HOME), 1) if str(p).startswith('~') else str(p)
    for root in (str(REPO), str(HOME / 'xcr-boolflux')):
        if s.startswith(root + '/'): return s[len(root) + 1:]
    return short(s)


def refresh_curated(o, dest_root):
    """Bring every curated entry up to date (see cmd_curate).  Returns (entries, failures)."""
    corr = load_corrections(); n = bad = 0
    for tid, r in o['targets'].items():
        d = dest_root / tid
        if not d.is_dir(): continue
        ref = r['ref']; defs = o.get('definitions', {}); nmax = notable_max(ref)
        pts = {}
        for fk in ('frontier_A_AD_G_GD', 'frontier_G_GD', 'tradeoff_frontier', 'strict_frontier'):
            for x in r[fk]: pts[tuple(x['tuple'])] = x
        for x in (r.get('notable') or {}).get('points', []): pts[tuple(x['tuple'])] = x
        for e in curated_index(d):
            name = e['name']; cf = d / (name + '.circ.txt'); sj = d / (name + '.json'); lg = d / 'logs' / name
            lg.mkdir(parents=True, exist_ok=True)
            fj = lg / 'found.json'
            fd = json.loads(fj.read_text()) if fj.exists() else {'circuit': cf.name, 'target': tid, 'tuple': e['tuple']}
            fd0 = fd
            px = pts.get(tuple(e['tuple']))
            if px is not None:                          # current ledger status of the tuple
                fd = dict(fd, status=px['status'], era=px.get('era'), nist=px['nist'])
            else:
                fd = dict(fd, ledger_note='tuple no longer on a frontier list of %s in the ledger' % tid)
            sd = json.loads(sj.read_text()) if sj.exists() else {}
            t = e['tuple']; n += 1
            # sidecar: corrections, class fields
            new = apply_corrections(sd, fd.get('source_file'), fd.get('source_sha256'), corr)
            cls, kind = classify(tuple(t), ref, defs)
            if 'class' in sd and sd.get('class_target') != tid and sd['class'] not in (cls, 'tradeoff:%s' % kind):
                new['class_agent'] = sd['class']            # what the agent wrote (maybe for another target)
            new.update({'class': cls, 'class_kind': kind, 'class_target': tid,
                        'class_rule': 'ledger.py classify(): TARGETS.json targets and definitions as recorded in LEDGER.json'})
            if nmax is not None: new['notable'] = t[2] <= nmax
            if new != sd: sj.write_text(json.dumps(new, indent=1) + '\n')
            m = new
            # start copy and command
            sp, sh = start_of(m)
            start_rec = {'recorded_path': sp, 'recorded_sha256': sh}
            spp = Path(str(sp).replace('~', str(HOME), 1)) if sp else None
            if spp is None:
                start_rec['note'] = 'no start in the sidecar'
            elif str(spp).startswith((str(REPO) + '/', str(HOME / 'xcr-boolflux') + '/')):
                start_rec['in_repository'] = repo_rel(spp)
            elif spp.exists() and is_circ(spp):
                c, txt = aes_check.load(spp)
                body = txt if txt is not None else spp.read_text()
                sc = lg / 'start.circ.txt'
                if not sc.exists() or sc.read_text() != body: sc.write_text(body)
                rs = aes_check.check(str(sc))
                start_rec.update({'copy': 'start.circ.txt', 'copy_of_sha256': sha256(spp), 'sha256_matches_recorded': sha256(spp) == sh,
                                  'converted_from_bfx': spp.name.endswith('.bfx'),
                                  'aes_check': 'OK %s' % tup(rs['tuple']) if rs['ok'] else 'FAIL %s' % rs.get('errors')})
            else:
                start_rec['note'] = 'start file not found on this machine'
            cmd = m.get('command')
            cmd = cmd if isinstance(cmd, str) else json.dumps(cmd) if cmd else None
            rcmd = None
            if cmd:
                rcmd = cmd
                if start_rec.get('copy') and str(spp) in rcmd:
                    rcmd = rcmd.replace(str(spp), '"$REPO"/nonlinear/boolflux/results/targets/%s/logs/%s/start.circ.txt' % (tid, name))
                for root in (str(REPO), str(HOME / 'xcr-boolflux')):
                    rcmd = rcmd.replace(root + '/', '"$REPO"/').replace(root + ' ', '"$REPO" ')
                rcmd = rcmd.replace(str(HOME) + '/', '"$HOME"/')
                sh_txt = ('#!/bin/bash\n# %s: the command recorded in the campaign sidecar (%s, %s).\n'
                          '# Repository paths are written "$REPO"; other paths ("$HOME"/...) are files of the campaign machine.\n'
                          '%s# A time-budgeted search: a re-run gives a verified circuit, not necessarily this one.\n'
                          '# As recorded:\n#   %s\nREPO=${REPO:-$(git rev-parse --show-toplevel)}\n%s\n' % (
                              name, short(fd.get('source_file') or ''), m.get('utc'),
                              '# The start circuit is logs/%s/start.circ.txt here.\n' % name if start_rec.get('copy') else '',
                              cmd.replace('\n', '\n#   '), rcmd))
                cs = lg / 'command.sh'
                if not cs.exists() or cs.read_text() != sh_txt: cs.write_text(sh_txt)
            # circuit header (comments only), re-verified
            camp = 'campaign 2026-11-15-targets'
            src = str(fd.get('source_file') or '').replace('~', str(HOME), 1)
            for root, lab in ((CAMP, 'campaign 2026-11-15-targets, agent %s; strategies/%s/NOTES.md'),
                              (NIGHT, 'night runs 2026-11-16, run %s')):
                try:
                    agent = Path(src).relative_to(root).parts[0]
                except (ValueError, IndexError):
                    continue
                camp = lab % ((agent,) * lab.count('%s'))
            hdr = ['%% Not a NIST-issued circuit: a BoolFlux result (NIST circuit file format, NIST counting), target %s, curated %s'
                   % (tid, (fd.get('curated_utc') or '')[:10]),
                   '%% Found by: %s, %s, seed %s' % (camp, m.get('utc') or '?', m.get('seed')),
                   '%% Started from: %s%s' % (repo_rel(sp) if sp else 'not recorded', (' (sha256 %s), copy logs/%s/start.circ.txt' % (str(sh)[:12], name))
                                              if start_rec.get('copy') else (' (sha256 %s)' % str(sh)[:12] if sh else '')),
                   '% Logs: nonlinear/boolflux/results/targets/{0}/logs/{1}/ (found.json, REPRODUCE.md, command.sh, aes_check.json)'.format(tid, name)]
            txt = cf.read_text(); nt = with_header(txt, hdr)
            if nt != txt or not (lg / 'aes_check.json').exists():
                tmp = cf.with_name('.' + cf.name + '.tmp'); tmp.write_text(nt)
                res = aes_check.check(str(tmp))
                if res['ok'] and list(res['tuple']) == list(t):
                    os.replace(tmp, cf)
                else:
                    tmp.unlink(); bad += 1
                    print('HEADER NOT WRITTEN (verification failed) %s/%s: %s' % (tid, name, res.get('errors')))
                    res = aes_check.check(str(cf))
                (lg / 'aes_check.json').write_text(json.dumps(res, indent=1, default=str) + '\n')
            # REPRODUCE.md and found.json
            x = {'class': cls if kind is None else 'tradeoff:' + kind}
            repro = m.get('reproduction') or ('one-off: time-budgeted search (%s, seed %s, %s s); not bit-reproducible. '
                                              'command.sh re-runs it%s; check any result with aes_check.py.' % (
                                                  camp.split(';')[0], m.get('seed'), m.get('elapsed_s'),
                                                  ' from start.circ.txt' if start_rec.get('copy') else ''))
            nist = fd.get('nist') or {'dominated_by': [], 'equal_tuple': []}
            rp = ('# Reproduce %s (%s, A/AD/G/GD = %s)\n\n```bash\npython3 nonlinear/boolflux/campaigns/aes_check.py '
                  'nonlinear/boolflux/results/targets/%s/%s.circ.txt\n```\n\n- class (%s): %s; status: %s; pinned NIST dominating: %s\n'
                  '- found by: %s; at %s; seed %s; after %s s\n'
                  '- start: %s\n- method: %s%s\n- code: %s\n- reproduction: %s\n\n'
                  '## Re-run\n\n`command.sh` here (recorded command; repository paths as `$REPO`):\n\n```bash\n%s\n```\n' % (
                      name, tid, tup(t), tid, name, tid, x['class'], fd.get('status'), nist_cell({'nist': nist}),
                      camp, m.get('utc'), m.get('seed'), m.get('elapsed_s'),
                      ('`nonlinear/boolflux/results/targets/%s/logs/%s/start.circ.txt` (copy of `%s`, sha256 %s; %s)'
                       % (tid, name, short(sp), str(sh)[:12], start_rec.get('aes_check'))) if start_rec.get('copy')
                      else ('`%s` (sha256 %s)' % (repo_rel(sp), str(sh)[:12]) if sp else 'not recorded'),
                      m.get('method'), (' (corrected: %s; original: %s)' % (m.get('method_corrected_by'), m.get('method_original')))
                      if m.get('method_corrected_by') else '',
                      json.dumps(m.get('code')), repro, rcmd or 'no command recorded'))
            rf = lg / 'REPRODUCE.md'
            if not rf.exists() or rf.read_text() != rp: rf.write_text(rp)
            nfd = dict(fd, **{'class': x['class'], 'class_target': tid, 'start': start_rec,
                              'logs': sorted(p.name for p in lg.iterdir() if p.is_file() and p.name != 'found.json')})
            if m.get('method_corrected_by'): nfd['sidecar_corrections'] = {'method_corrected_by': m['method_corrected_by']}
            if nfd != fd0: fj.write_text(json.dumps(nfd, indent=1, default=str) + '\n')
    return n, bad


def main(argv=None):
    ap = argparse.ArgumentParser(prog='ledger.py', description=__doc__.split('\n\n')[0])
    sp = ap.add_subparsers(dest='cmd', required=True)
    b = sp.add_parser('baseline', help='build the archive baseline once (refuses to overwrite)')
    b.add_argument('--cutoff', default=CUTOFF_DEFAULT); b.add_argument('--force', action='store_true')
    s2 = sp.add_parser('snapshot', help='build the second snapshot "known-by-23:50" once (refuses to overwrite)')
    s2.add_argument('--cutoff', default=SNAP2_CUTOFF); s2.add_argument('--force', action='store_true')
    r = sp.add_parser('run', help='scan, verify (cached), classify, write LEDGER.md / LEDGER.json')
    r.add_argument('--strict', action='store_true', help='exit status 1 if an issue has level FAIL')
    c = sp.add_parser('curate', help='plan (or --apply) the copy of new campaign points into results/targets/')
    c.add_argument('--apply', action='store_true')
    a = ap.parse_args(argv)
    return {'baseline': cmd_baseline, 'snapshot': cmd_snapshot, 'run': cmd_run, 'curate': cmd_curate}[a.cmd](a)


if __name__ == '__main__':
    sys.exit(main())
