#!/usr/bin/env python3
"""Fix 2 (after the 20-min test): knob translog.values_gates -- rows whose gate count is at
most this also carry the state's values, so the 89 state right after an exit from 88 is kept
(the exit 88 state is one of its 88-subsets: the exact same-plateau test before/after an
excursion can then be done offline).  Default = id_gates (the behaviour of the test run)."""
from pathlib import Path
p = Path.home() / "xs-campaigns/2026-11-07-sprint/translog/xorflux-translog/xorflux/engine/translog.py"
t = p.read_text()
edits = [
    ('    "id_gates": Knob(88, "States with at most this many gates get an identity hash (and values, "\n'
     '                     "by translog.values) in their row.", min=0),\n',
     '    "id_gates": Knob(88, "States with at most this many gates get an identity hash (and values, "\n'
     '                     "by translog.values) in their row.", min=0),\n'
     '    "values_gates": Knob(None, "Rows with at most this many gates also carry the state\'s values "\n'
     '                         "(no identity): set it to band_gates to keep the 89 state right after "\n'
     '                         "an exit from 88, whose 88 exit state is one of its 88-subsets. "\n'
     '                         "null = id_gates.", kind=int, nullable=True, min=0),\n'),
    ('        return cls(Path(directory) / cfg.file, worker_id, target, recorder, cfg.band_gates,\n'
     '                   cfg.id_gates, cfg.rotate_bits, cfg.values)\n',
     '        return cls(Path(directory) / cfg.file, worker_id, target, recorder, cfg.band_gates,\n'
     '                   cfg.id_gates, cfg.rotate_bits, cfg.values, cfg.values_gates)\n'),
    ('    def __init__(self, path, worker_id, target, recorder, band_gates, id_gates, rotate_bits,\n'
     '                 values_mode):\n',
     '    def __init__(self, path, worker_id, target, recorder, band_gates, id_gates, rotate_bits,\n'
     '                 values_mode, values_gates=None):\n'),
    ('        self.id_gates = id_gates\n',
     '        self.id_gates = id_gates\n'
     '        self.values_gates = id_gates if values_gates is None else values_gates\n'),
    ('                     "band_gates": band_gates, "id_gates": id_gates, "rotate_bits": self.rotate,\n'
     '                     "values": values_mode, "n_inputs": self.n})\n',
     '                     "band_gates": band_gates, "id_gates": id_gates, "rotate_bits": self.rotate,\n'
     '                     "values": values_mode, "values_gates": self.values_gates,\n'
     '                     "n_inputs": self.n})\n'),
    ('            elif mode == "new" and ident not in self._seen:\n'
     '                self._seen.add(ident)\n'
     '                row["v"] = values\n',
     '            elif mode == "new" and ident not in self._seen:\n'
     '                self._seen.add(ident)\n'
     '                row["v"] = values\n'
     '        elif g <= self.values_gates and self.values_mode != "never":\n'
     '            row["v"] = sorted(state.key())\n'),
]
for old, new in edits:
    assert t.count(old) == 1, old
    t = t.replace(old, new)
p.write_text(t)
print("fix2 applied")
