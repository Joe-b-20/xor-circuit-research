#!/usr/bin/env python3
"""exp2: add departure-key logging to the translog copy (knob translog.departure, default off).
When an accepted proposal takes the chain from <= id_gates to more gates, the engine computes the
88 state it left from the open journal's net changes (before = after - added + removed) and the
step row gets "xid" (identity of the departure state) and "xv" (its sorted values).
Nothing touches the RNG; cost is one key() + changes() per departure (~1/s)."""
from pathlib import Path
E = Path.home() / "xs-campaigns/2026-11-07-sprint/translog/xorflux-translog/xorflux/engine"
loop = (E / "loop.py").read_text()
tl = (E / "translog.py").read_text()

a1 = """                    else:
                        # Frontier points are recorded at their own depth, feasible or not: a"""
b1 = """                    else:
                        _tld = self._tl
                        if (_tld is not None and _tld.departure and g0 <= _tld.id_gates
                                and g1 > g0):
                            _ad, _rm = journal.changes()
                            _tld.pending_departure = (st.key() - set(_ad)) | set(_rm)
                        # Frontier points are recorded at their own depth, feasible or not: a"""
assert loop.count(a1) == 1
loop = loop.replace(a1, b1)

a2 = """    "file": Knob("translog.jsonl", "File name inside the worker directory."),"""
b2 = """    "file": Knob("translog.jsonl", "File name inside the worker directory."),
    "departure": Knob(False, "exp2: on an exit from <= id_gates, also log the state left "
                      "(xid identity, xv values), from the proposal journal's net changes."),"""
assert tl.count(a2) == 1
tl = tl.replace(a2, b2)
a3 = """                   cfg.id_gates, cfg.rotate_bits, cfg.values, cfg.values_gates)"""
b3 = """                   cfg.id_gates, cfg.rotate_bits, cfg.values, cfg.values_gates,
                   getattr(cfg, "departure", False))"""
assert tl.count(a3) == 1
tl = tl.replace(a3, b3)
a4 = """                 values_mode, values_gates=None):"""
b4 = """                 values_mode, values_gates=None, departure=False):"""
assert tl.count(a4) == 1
tl = tl.replace(a4, b4)
a5 = """        self.values_mode = values_mode
"""
b5 = """        self.values_mode = values_mode
        self.departure = bool(departure)
        self.pending_departure = None       # set by the loop on an accepted exit from id band
"""
assert tl.count(a5) == 1
tl = tl.replace(a5, b5)
a6 = """        elif g <= self.values_gates and self.values_mode != "never":
            row["v"] = sorted(state.key())
"""
b6 = """        elif g <= self.values_gates and self.values_mode != "never":
            row["v"] = sorted(state.key())
        dep = self.pending_departure
        if dep is not None:
            self.pending_departure = None
            if kind == "step" and p is not None and p <= self.id_gates < g:
                xv = sorted(dep)
                row["xid"] = _identity(xv, self.n, self.rotate)
                row["xv"] = xv
"""
assert tl.count(a6) == 1
tl = tl.replace(a6, b6)
(E / "loop.py").write_text(loop)
(E / "translog.py").write_text(tl)
print("patched")
