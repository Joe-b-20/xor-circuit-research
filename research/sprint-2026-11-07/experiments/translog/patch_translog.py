#!/usr/bin/env python3
"""Apply the translog hooks to xorflux-translog/xorflux (a copy of the repo's frozen v8
search/xorflux).  Every anchor must match exactly once; the script refuses to run twice."""
import sys
from pathlib import Path

ROOT = Path.home() / "xs-campaigns/2026-11-07-sprint/translog/xorflux-translog/xorflux"


def patch(rel, edits):
    p = ROOT / rel
    text = p.read_text()
    for old, new in edits:
        n = text.count(old)
        if n != 1:
            sys.exit(f"{rel}: anchor matched {n} times:\n{old}")
        text = text.replace(old, new)
    p.write_text(text)
    print(f"patched {rel}: {len(edits)} edits")


# 1. knob registry
patch("config/registry.py", [(
    '    "xorflux.engine.phase",\n',
    '    "xorflux.engine.phase",\n    "xorflux.engine.translog",\n')])

# 2. engine loop
patch("engine/loop.py", [
    # import
    ('from .scheduler import Scheduler, Tightness\n',
     'from .scheduler import Scheduler, Tightness\nfrom .translog import TransitionLog\n'),
    # construction (end of _setup)
    ('        source = getattr(recorder, "set_epoch_source", None)\n'
     '        if source is not None:\n'
     '            source(self.epoch_fields)\n',
     '        source = getattr(recorder, "set_epoch_source", None)\n'
     '        if source is not None:\n'
     '            source(self.epoch_fields)\n'
     '        # EXPERIMENTAL transition log (engine/translog.py); None when off.\n'
     '        self._tl = TransitionLog.from_settings(settings, target, recorder, worker_id)\n'),
    # chain begin: start / restart
    ('        self.cur_g, self.cur_d, self.cur_key = g, d, key\n'
     '        values = state.key()\n'
     '        self.root_values = values\n',
     '        self.cur_g, self.cur_d, self.cur_key = g, d, key\n'
     '        if self._tl is not None:\n'
     '            self._tl.transition("chain", self.it, g, d, source, self.chain_seq, state)\n'
     '        values = state.key()\n'
     '        self.root_values = values\n'),
    # the step: after the proposal's own timing, before anything charged to the move
    ('        # A proposal\'s cost includes scoring and its undo (rollback is kernel work for it).\n'
     '        secs = perf_counter() - t0\n',
     '        # A proposal\'s cost includes scoring and its undo (rollback is kernel work for it).\n'
     '        secs = perf_counter() - t0\n'
     '        tl = self._tl\n'
     '        if tl is not None and g1 != tl.g:\n'
     '            tl.transition("step", it, g1, d1, move.name, self.chain_seq, self.state)\n'),
    # periodic flush
    ('    def _periodic(self) -> None:\n'
     '        self._t = t = self.recorder.now()\n',
     '    def _periodic(self) -> None:\n'
     '        self._t = t = self.recorder.now()\n'
     '        if self._tl is not None:\n'
     '            self._tl.flush()\n'),
    # epoch summary
    ('            "counters": dict(self.counters),\n        }\n',
     '            "counters": dict(self.counters),\n'
     '            "translog": None if self._tl is None else self._tl.summary(),\n        }\n'),
    # checkpoint flush
    ('        if self._canonical:\n'
     '            self._set_state(self._make_state(self.state.values(), self._cap))\n'
     '        t = self.recorder.now()\n',
     '        if self._canonical:\n'
     '            self._set_state(self._make_state(self.state.values(), self._cap))\n'
     '        if self._tl is not None:\n'
     '            self._tl.flush()\n'
     '        t = self.recorder.now()\n'),
    # resume
    ('        self.cur_key = self._key(self.cur_g, self.cur_d)\n'
     '        self.chain_seq = chain["seq"]\n',
     '        self.cur_key = self._key(self.cur_g, self.cur_d)\n'
     '        self.chain_seq = chain["seq"]\n'
     '        if self._tl is not None:\n'
     '            self._tl.transition("chain", self.it, self.cur_g, self.cur_d, "resume",\n'
     '                                self.chain_seq, self.state)\n'),
])

# 3. worker: close the log with the recorder
patch("campaign/worker.py", [(
    '            self.checkpoint()\n'
     '            self.write_status("stopped")\n'
     '            self.recorder.close(reason)\n',
    '            self.checkpoint()\n'
     '            self.write_status("stopped")\n'
     '            self.recorder.close(reason)\n'
     '            tl = getattr(engine, "_tl", None)\n'
     '            if tl is not None:\n'
     '                tl.close()\n')])
print("done")
