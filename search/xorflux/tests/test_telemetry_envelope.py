"""Caller fields never override or collide with the event envelope."""
import json
import tempfile
import unittest
from pathlib import Path

from xorflux.telemetry.recorder import Recorder


class EnvelopeTests(unittest.TestCase):
    def test_epoch_and_event_fields_named_like_envelope_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = Recorder(Path(tmp), "w0")
            rec.begin("start", {})
            rec.proposal({"it": 5, "move": "m", "accepted": True, "neutral": False,
                          "d_gates": 0, "d_depth": 0, "gates": 3, "depth": 2, "work": 1,
                          "components": []})
            # The engine's epoch fields carry its own iteration counter as "it".
            rec.epoch({"it": 5, "t": 1.0, "worker": "other", "cur": [3, 2]})
            rec.event("phase", it=5, t=99.0, phase="plateau")
            rec.close()
            lines = [json.loads(l) for l in (Path(tmp) / "events.jsonl").read_text().splitlines()]
            epoch = next(l for l in lines if l["ev"] == "epoch")
            self.assertEqual(epoch["worker"], "w0")
            self.assertEqual(epoch["cur"], [3, 2])
            self.assertTrue(any(l["ev"] == "phase" for l in lines))


if __name__ == "__main__":
    unittest.main()
