"""Hub archive: content-addressed verified circuits, (A, AD, GD) cells keeping the min-G circuits
(up to K distinct), Pareto front derived from the cells, frontier-gain scoring.

On disk (DIR/archive/):  <id>.bfx (core.to_kernel text), <id>.json (record), cells.json (atomic).
Record fields: id, A, AD, G, GD, counts, parents, operator, operator_settings, seed, run_id,
code_version, cpu_s, wall_s, t_admit, verified.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .common import core, metrics, verify, cid, leq, atomic_write, published

K_PER_CELL = 4
# gain weights: lexicographic research priorities (AND count, AND depth first; then G, GD)
GAIN_W = {0: 8.0, 1: 4.0, 2: 2.0, 3: 1.0}
CELL_ONLY_GAIN = 0.01          # a better circuit in its (A, AD, GD) cell that is dominated elsewhere
GEN_SLACK = 40                 # nursery: new structures from generators may enter their cell this far above the front
NEAR_SLACK = 6                 # a dominated circuit enters its cell only if G <= (G of a dominating front point) + slack


class Archive:
    def __init__(self, root, load=True):
        self.dir = Path(root) / 'archive'; self.dir.mkdir(parents=True, exist_ok=True)
        self.rec = {}          # id -> record
        self.circ = {}         # id -> Circuit (lazy)
        self.cells = {}        # (A, AD, GD) -> [ids] (all with the cell's min G)
        if load: self._load()

    # ---- persistence ------------------------------------------------------------------------
    def _load(self):
        cf = self.dir / 'cells.json'
        for f in self.dir.glob('*.json'):
            if f.name == 'cells.json': continue
            try:
                r = json.loads(f.read_text())
            except Exception:
                continue
            self.rec[r['id']] = r
        if cf.exists():
            for k, ids in json.loads(cf.read_text()).items():
                self.cells[tuple(int(x) for x in k.split(','))] = ids
        else:
            for r in sorted(self.rec.values(), key=lambda r: r['t_admit']):
                self._place(r)

    def _save_cells(self):
        atomic_write(self.dir / 'cells.json', json.dumps({'%d,%d,%d' % k: v for k, v in sorted(self.cells.items())}))

    def circuit(self, i):
        if i not in self.circ:
            self.circ[i] = core.from_kernel((self.dir / (i + '.bfx')).read_text(), i)
        return self.circ[i]

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
        if getattr(self, '_front', None) is None:
            pts = self.points()
            self._front = [p for p in pts if not any(q != p and leq(q, p) for q in pts)]
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
        """frontier gain of tuple m against the current cell minima (before admission)"""
        pts = self.front()
        if any(leq(q, m) for q in pts):
            return CELL_ONLY_GAIN if self.would_place(m) else 0.0
        best = 0.0
        for k in range(4):     # coordinate k improved at the same (or better) other coordinates
            if any(all(q[j] <= m[j] for j in range(4) if j != k) for q in pts):
                best = max(best, GAIN_W[k])
        return best or 1.0

    def _place(self, r):
        m = (r['A'], r['AD'], r['G'], r['GD']); k = self.key(m)
        ids = self.cells.get(k, [])
        g = self.rec[ids[0]]['G'] if ids else None
        if g is None or r['G'] < g: self.cells[k] = [r['id']]; return True
        if r['G'] == g and r['id'] not in ids and len(ids) < K_PER_CELL: ids.append(r['id']); return True
        return False

    # ---- admission ----------------------------------------------------------------------------
    def admit(self, c, parents=(), operator='seed', settings=None, seed=None, run_id=None, code_version=None,
              cpu_s=None, wall_s=None, force_keep=False, slack=None):
        """Verify and admit c if it lowers (or ties, up to K) the G of its (A, AD, GD) cell.
        Returns (status, record_or_None, gain)."""
        i = cid(c)
        if i in self.rec: return 'duplicate', self.rec[i], 0.0
        m = metrics(c)
        if not self.would_place(m, slack) and not force_keep: return 'not-better', None, 0.0
        ok, info = verify(c)
        if not ok: return 'rejected: ' + info.get('error', '?'), None, 0.0
        g = self.gain(m)
        r = {'id': i, 'A': m[0], 'AD': m[1], 'G': m[2], 'GD': m[3], 'counts': info.get('counts'),
             'parents': list(parents), 'operator': operator, 'operator_settings': settings or {}, 'seed': seed,
             'run_id': run_id, 'code_version': code_version, 'cpu_s': cpu_s, 'wall_s': wall_s,
             't_admit': time.time(), 'verified': True,
             'pub_new': not any(leq(u, m) for u in published()), 'gain': g}
        (self.dir / (i + '.bfx')).write_text(core.to_kernel(c))
        atomic_write(self.dir / (i + '.json'), json.dumps(r, indent=1))
        self.rec[i] = r; self.circ[i] = c
        self._place(r); self._front = None; self._save_cells()
        return 'admitted', r, g
