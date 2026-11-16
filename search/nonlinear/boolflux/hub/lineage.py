#!/usr/bin/env python3
"""Lineage audit of a hub archive: does every circuit carry what is needed to say how it was made?

    python3 search/nonlinear/boolflux/hub/lineage.py CAMPAIGN [--also CAMPAIGN2 ...] [--front | --id ID] [--json OUT]

For every record (default), the front circuits (--front), or one circuit (--id); always including
all ancestors.  Checks per record:
  file      <id>.bfx exists and its content hash is the id
  operator  present; 'seed' / 'ingest' records name their source file
  for records made by an operator job:
  parents   at least one, all present in the archive
  seed, code_version, settings (operator_settings not empty)
  run       run_id present and a run file for it found in CAMPAIGN/runs or an --also campaign whose
            outcome lists this circuit id.  (Run ids written before 2026-11-14 are 'r<number>-<op>' and
            repeat between campaigns; an archive copied from another campaign needs --also to find
            its runs, and the outcome check keeps the wrong run of the same name from matching.)
Prints the counts and the gaps; exit code 1 if any record has a gap.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from boolflux import core                                # noqa: E402
from boolflux.hub.archive import Archive                 # noqa: E402
from boolflux.hub.common import cid                      # noqa: E402

SOURCE_OPS = ('seed', 'ingest')


def find_run(run_id, ident, dirs):
    """(path, run record) of the run file named run_id whose outcome lists ident, else (None, None)"""
    for d in dirs:
        f = Path(d) / 'runs' / (run_id + '.json')
        if not f.exists(): continue
        try:
            r = json.loads(f.read_text())
        except Exception:
            continue
        if any(o.get('id') == ident and o.get('status') == 'admitted' for o in r.get('outcome', [])): return f, r
    return None, None


def audit(campaign, also=(), ids=None, check_files=True):
    """returns (rows, gaps): rows = {id: {'operator', 'run_file', 'gaps': [...]}}"""
    ar = Archive(campaign)
    dirs = [Path(campaign)] + [Path(a) for a in also]
    todo = list(ar.rec) if ids is None else list(ids); seen = set(); rows = {}
    while todo:
        i = todo.pop()
        if i in seen: continue
        seen.add(i)
        r = ar.rec.get(i)
        if r is None:
            rows[i] = {'operator': None, 'run_file': None, 'gaps': ['record missing']}; continue
        g = []
        if check_files:
            try:
                if cid(core.from_kernel((ar.dir / (i + '.bfx')).read_text(), i)) != i: g.append('file: content hash differs from the id')
            except Exception as e:
                g.append('file: %s' % type(e).__name__)
        op = r.get('operator'); st = r.get('operator_settings') or {}; rf = None
        if not op: g.append('operator')
        if not r.get('verified'): g.append('verified')
        if op in SOURCE_OPS:
            if not st.get('file'): g.append('source file')
        else:
            ps = r.get('parents') or []
            if not ps: g.append('parents')
            g += ['parent %s not in the archive' % p for p in ps if p not in ar.rec]
            todo += [p for p in ps if p in ar.rec]
            if r.get('seed') is None: g.append('seed')
            if not r.get('code_version'): g.append('code_version')
            if not [k for k, v in st.items() if v is not None and k != 'nursery']: g.append('settings')
            if not r.get('run_id'): g.append('run_id')
            else:
                rf, run = find_run(r['run_id'], i, dirs)
                if rf is None: g.append('run file for %s (with this circuit in its outcome)' % r['run_id'])
        rows[i] = {'operator': op, 'run_file': str(rf) if rf else None, 'gaps': g}
    return rows, {i: v['gaps'] for i, v in rows.items() if v['gaps']}


def main(argv=None):
    a = list(sys.argv[1:] if argv is None else argv)
    def opt(name, n=1):
        out = []
        while name in a:
            k = a.index(name); out.append(a[k + 1]); del a[k:k + 2]
        return out
    also = opt('--also'); one = opt('--id'); jout = opt('--json')
    front = '--front' in a
    if front: a.remove('--front')
    if len(a) != 1:
        print(__doc__); return 2
    ids = None
    if one: ids = one
    elif front: ids = Archive(a[0]).front_ids()
    rows, gaps = audit(a[0], also, ids)
    kinds = {}
    for i, g in gaps.items():
        for x in g:
            k = x.split(' ')[0]; kinds[k] = kinds.get(k, 0) + 1
    print('%s: %d records checked, %d complete, %d with gaps %s' % (a[0], len(rows), len(rows) - len(gaps), len(gaps), kinds or ''))
    for i, g in sorted(gaps.items())[:40]: print('  %s (%s): %s' % (i, rows[i]['operator'], '; '.join(g)))
    if len(gaps) > 40: print('  ... %d more (see --json)' % (len(gaps) - 40))
    if jout: Path(jout[0]).write_text(json.dumps(rows, indent=1) + '\n')
    return 1 if gaps else 0


if __name__ == '__main__':
    sys.exit(main())
