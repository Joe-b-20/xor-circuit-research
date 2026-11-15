"""Hub archive: content-addressed verified circuits, (A, AD, GD) cells keeping the min-G circuits
(up to K distinct structures), Pareto front derived from the cells, frontier-gain scoring.

On disk (DIR/archive/):  <id>.bfx (core.to_kernel text), <id>.json (record), index.jsonl (one
compact record per line, appended on admission; a cache of the record files), cells.json (atomic;
a cache of the cells for readers outside this module).
Record fields: id, A, AD, G, GD, counts, parents, operator, operator_settings, seed, run_id,
code_version, cpu_s, wall_s, t_admit, verified, pub_new, gain, skey.

The record files are the truth.  On load the cells are always recomputed from the records in
admission order (the same `_place` replay that produced them), so a crash between writing a record
and writing cells.json, or a cells.json that names a missing record, cannot corrupt the cells
(review 5, H1).  Only one process (the scheduler) admits; operators open the archive read-only.
"""
from __future__ import annotations

import json
import time
from collections import OrderedDict
from pathlib import Path

from .common import core, metrics, verify, cid, leq, atomic_write, published, structure_key, clean

K_PER_CELL = 4
# gain weights: lexicographic research priorities (AND count, AND depth first; then G, GD)
GAIN_W = {0: 8.0, 1: 4.0, 2: 2.0, 3: 1.0}
CELL_ONLY_GAIN = 0.01          # a better circuit in its (A, AD, GD) cell that is dominated elsewhere
GEN_SLACK = 40                 # nursery: new structures from generators may enter their cell this far above the front
NEAR_SLACK = 6                 # a dominated circuit enters its cell only if G <= (G of a dominating front point) + slack
CIRCUIT_CACHE = 512            # parsed circuits kept in memory (LRU); the archive itself is on disk


def pareto(pts):
    """non-dominated points of a list of equal-length tuples (duplicates collapse to one)"""
    out = []
    for p in sorted(set(pts)):             # lexicographic order: a dominating point always comes first
        if not any(leq(q, p) for q in out): out.append(p)
    return out


class Archive:
    def __init__(self, root, load=True, cache=CIRCUIT_CACHE, gain_mode='value'):
        if gain_mode not in ('value', 'legacy'): raise ValueError('gain_mode %r' % (gain_mode,))
        self.gain_mode = gain_mode
        self.dir = Path(root) / 'archive'; self.dir.mkdir(parents=True, exist_ok=True)
        self.rec = {}          # id -> record
        self.circ = OrderedDict()   # id -> Circuit (bounded LRU)
        self.cache = cache
        self.cells = {}        # (A, AD, GD) -> [ids] (all with the cell's min G)
        self.load_errors = []  # unreadable record files / index lines (never silently dropped)
        self.cells_repaired = False   # cells.json on disk differed from the replay of the records
        self.index_missing = 0        # records not in index.jsonl (the owner calls write_index())
        self._front = None; self._skeys = None
        if load: self._load()

    # ---- persistence ------------------------------------------------------------------------
    def _load(self):
        ix = self.dir / 'index.jsonl'
        if ix.exists():
            for n, ln in enumerate(ix.read_text().splitlines()):
                try:
                    r = json.loads(ln); self.rec[r['id']] = r
                except Exception:
                    self.load_errors.append('index.jsonl line %d' % (n + 1))
        for f in self.dir.glob('*.json'):
            if f.name == 'cells.json' or f.stem in self.rec: continue
            try:
                r = json.loads(f.read_text()); r['id'], r['G'], r['t_admit']
            except Exception as e:
                self.load_errors.append('%s: %r' % (f.name, e)); continue
            self.rec[r['id']] = r; self.index_missing += 1
        self.rebuild_cells()
        cf = self.dir / 'cells.json'
        if cf.exists():
            try:
                disk = {tuple(int(x) for x in k.split(',')): v for k, v in json.loads(cf.read_text()).items()}
            except Exception:
                disk = None
            self.cells_repaired = disk != self.cells

    def rebuild_cells(self):
        """replay of the records in admission order (with the structure keys known so far)"""
        self.cells = {}; self._front = None
        for r in sorted(self.rec.values(), key=lambda r: (r['t_admit'], r['id'])):
            self._place(r)

    def dedupe_legacy(self):
        """Archives filled before review 5 hold the same structure up to K times per cell (their
        records carry no 'skey').  Owner only: compute the keys, replay the cells so that a cell
        keeps distinct structures, and store the keys in index.jsonl so that every reader gets the
        same cells.  The record files and circuits stay.  Returns the number of cell members dropped."""
        if all('skey' in r for r in self.rec.values()): return 0
        before = sum(len(v) for v in self.cells.values())
        self.skeys(); self.rebuild_cells(); self.write_index(); self._save_cells()
        return before - sum(len(v) for v in self.cells.values())

    def reclean_legacy(self, code_version=None, log=None):
        """Owner only, once per record (archive/cleaned.json lists the records already looked at).
        Records admitted before candidates were cleaned may hold duplicate gates: their recorded
        metrics are those of the stored text, not of the circuit it computes most cheaply.  Each
        such record is reported through log(id, old metrics, cleaned metrics, status, new id, gain); its files are not
        touched; the cleaned circuit is admitted as a new record (operator 'clean', parent = the
        old record).  Returns the number of records whose cleaned metrics differ."""
        mf = self.dir / 'cleaned.json'
        try:
            done = set(json.loads(mf.read_text()))
        except Exception:
            done = set()
        todo = [i for i in self.rec if i not in done]
        if not todo: return 0
        n = 0
        for i in todo:
            try:
                c = core.from_kernel((self.dir / (i + '.bfx')).read_text(), i)
                cc = clean(c)
            except Exception:
                continue
            done.add(i)
            if cc is c: continue
            r = self.rec[i]; m0 = (r['A'], r['AD'], r['G'], r['GD']); m1 = metrics(cc)
            if m1 == m0: continue
            n += 1
            st, nr, g = self.admit(cc, parents=[i], operator='clean', code_version=code_version, force_keep=True,
                                   settings={'cleaned_from': i, 'raw_metrics': list(m0), 'nursery': bool((r.get('operator_settings') or {}).get('nursery'))})
            if nr is not None: done.add(nr['id'])
            if log: log(i, m0, m1, st, nr['id'] if nr else None, g)
        atomic_write(mf, json.dumps(sorted(done)))
        return n

    def _save_cells(self):
        atomic_write(self.dir / 'cells.json', json.dumps({'%d,%d,%d' % k: v for k, v in sorted(self.cells.items())}))

    def write_index(self):
        """rewrite index.jsonl from the loaded records (owner only; makes later loads one file read)"""
        atomic_write(self.dir / 'index.jsonl', ''.join(json.dumps(r) + '\n' for r in
                                                     sorted(self.rec.values(), key=lambda r: (r['t_admit'], r['id']))))
        self.index_missing = 0

    def circuit(self, i):
        c = self.circ.get(i)
        if c is None:
            c = core.from_kernel((self.dir / (i + '.bfx')).read_text(), i)
            self._remember(i, c)
        else:
            self.circ.move_to_end(i)
        return c

    def _remember(self, i, c):
        self.circ[i] = c; self.circ.move_to_end(i)
        while len(self.circ) > self.cache: self.circ.popitem(last=False)

    def skeys(self):
        """structure key -> id for every archived circuit (records admitted before review 5 carry no
        'skey': computed once from their .bfx)"""
        if self._skeys is None:
            self._skeys = {}
            for i, r in self.rec.items():
                k = r.get('skey')
                if k is None:
                    try:
                        k = structure_key(core.from_kernel((self.dir / (i + '.bfx')).read_text(), i))
                    except Exception:
                        continue
                    r['skey'] = k
                self._skeys.setdefault(k, i)
        return self._skeys

    # ---- cells and front ----------------------------------------------------------------------
    @staticmethod
    def key(m):
        return (m[0], m[1], m[3])

    def cell_min(self, k):
        ids = self.cells.get(k)
        return self.rec[ids[0]]['G'] if ids else None

    def points(self):
        """(A, AD, G, GD) of every cell minimum"""
        return [(k[0], k[1], self.rec[ids[0]]['G'], k[2]) for k, ids in self.cells.items() if ids]

    def front(self):
        if self._front is None:
            self._front = pareto(self.points())
        return self._front

    def front_ids(self):
        f = set(self.front())
        return [i for k, ids in self.cells.items() for i in ids if (k[0], k[1], self.rec[i]['G'], k[2]) in f]

    def would_place(self, m, slack=None):
        """slack: allowed G excess over a dominating front point (NEAR_SLACK; generators use GEN_SLACK)"""
        slack = NEAR_SLACK if slack is None else slack
        k = self.key(m); g = self.cell_min(k)
        if not (g is None or m[2] < g or (m[2] == g and len(self.cells[k]) < K_PER_CELL)): return False
        doms = [q[2] for q in self.front() if leq(q, m)]
        return not doms or m[2] <= min(doms) + slack

    def gain(self, m):
        """frontier gain of tuple m against the current front (before admission).

        'value' (default, review 5 H5): credit only for what the tuple adds, in the order of the
        research priorities (AND count > AND depth > gates > gate depth):
          (A, AD) reach: no archived circuit has A <= m.A and AD <= m.AD (any G, GD):
                    some circuit meets the AD cap, so the AND count at that depth drops            -> 8
                    none does: a new AND depth                                                     -> 4
          GD reach: lower gate depth than every archived circuit with A <= m.A and AD <= m.AD       -> 1
          fewer gates: the best G inside the cap box A <= m.A, AD <= m.AD, GD <= m.GD drops by d     -> 0.5 * min(d, 6)
        (the first that applies); dominated tuples score 0.
        'legacy': the rule used until 2026-11-14, which asked only for some archived point no worse
        on the other three coordinates and therefore scored almost every front admission as
        "lowers A" (a higher-A circuit with fewer gates nearly always exists)."""
        pts = self.front()
        if self.gain_mode == 'legacy':
            if any(leq(q, m) for q in pts):
                return CELL_ONLY_GAIN if self.would_place(m) else 0.0
            best = 0.0
            for k in range(4):     # coordinate k improved at the same (or better) other coordinates
                if any(all(q[j] <= m[j] for j in range(4) if j != k) for q in pts):
                    best = max(best, GAIN_W[k])
            return best or 1.0
        if any(leq(q, m) for q in pts): return 0.0
        A, AD, G, GD = m
        if not any(q[0] <= A and q[1] <= AD for q in pts):
            return GAIN_W[0] if any(q[1] <= AD for q in pts) else GAIN_W[1]
        box = [q[2] for q in pts if q[0] <= A and q[1] <= AD and q[3] <= GD]
        if not box: return GAIN_W[3]
        return 0.5 * min(min(box) - G, 6)      # min(box) > G because m is not dominated

    def _place(self, r):
        m = (r['A'], r['AD'], r['G'], r['GD']); k = self.key(m)
        ids = self.cells.get(k, [])
        g = self.rec[ids[0]]['G'] if ids else None
        if g is None or r['G'] < g:
            self.cells[k] = [r['id']]
            self._front_update(m, None if g is None else (k[0], k[1], g, k[2]))
            return True
        if r['G'] == g and r['id'] not in ids and len(ids) < K_PER_CELL:
            sk = r.get('skey')
            if sk is not None and any(self.rec[i].get('skey') == sk for i in ids): return False   # same structure
            ids.append(r['id']); return True
        return False

    def _front_update(self, p, old):
        """p is the new minimum of its cell (old: the previous one).  O(front) instead of the
        O(cells^2) recomputation after every admission."""
        fr = self._front
        if fr is None: return
        if any(q != old and leq(q, p) for q in fr): return     # dominated: old was dominated too, front unchanged
        self._front = [q for q in fr if not leq(p, q)] + [p]

    # ---- admission ----------------------------------------------------------------------------
    def admit(self, c, parents=(), operator='seed', settings=None, seed=None, run_id=None, code_version=None,
              cpu_s=None, wall_s=None, force_keep=False, slack=None, clean_first=True):
        """Verify and admit c if it lowers (or ties, up to K distinct structures) the G of its
        (A, AD, GD) cell.  Returns (status, record_or_None, gain); status is 'admitted', 'duplicate'
        (same text), 'duplicate-structure' (same DAG written differently), 'not-better' or
        'rejected: <why>'.  Never raises for a malformed circuit.
        clean_first (default): c is cleaned first (common.clean: identical gates merged, dead gates
        dropped); the archive stores, measures and places the cleaned circuit, and its record keeps
        `cleaned_from` (id of the text as given) and `raw_metrics` in operator_settings.  Review 5:
        172 of 2311 records of the 2026-11-14 campaign held a duplicate AND, so their A was one high."""
        try:
            if clean_first:              # merge identical gates, drop dead ones: the archive stores the cleaned circuit
                raw = c; c = clean(raw)
                if c is not raw:
                    settings = dict(settings or {}, cleaned_from=cid(raw), raw_metrics=list(metrics(raw)))
            i = cid(c); m = metrics(c)
        except Exception as e:
            return 'rejected: malformed circuit: %r' % (e,), None, 0.0
        if i in self.rec: return 'duplicate', self.rec[i], 0.0
        if not force_keep and not self.would_place(m, slack): return 'not-better', None, 0.0
        ok, info = verify(c)
        if not ok: return 'rejected: ' + info.get('error', '?'), None, 0.0
        sk = structure_key(c); j = self.skeys().get(sk)
        if j is not None: return 'duplicate-structure', self.rec[j], 0.0
        g = self.gain(m)
        r = {'id': i, 'A': m[0], 'AD': m[1], 'G': m[2], 'GD': m[3], 'counts': info.get('counts'),
             'parents': list(parents), 'operator': operator, 'operator_settings': settings or {}, 'seed': seed,
             'run_id': run_id, 'code_version': code_version, 'cpu_s': cpu_s, 'wall_s': wall_s,
             't_admit': time.time(), 'verified': True,
             'pub_new': not any(leq(u, m) for u in published()), 'gain': g, 'skey': sk}
        atomic_write(self.dir / (i + '.bfx'), core.to_kernel(c))
        atomic_write(self.dir / (i + '.json'), json.dumps(r, indent=1, default=str))
        with open(self.dir / 'index.jsonl', 'a') as f: f.write(json.dumps(r, default=str) + '\n')
        self.rec[i] = r; self._skeys[sk] = i; self._remember(i, c)
        self._place(r); self._save_cells()
        return 'admitted', r, g
