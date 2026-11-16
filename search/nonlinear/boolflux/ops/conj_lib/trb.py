"""``import trb`` for the conjugate helpers: the hub's copy of the timing-aware region rebuild
(boolflux/hub/trb_impl.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from boolflux.hub import trb_impl as _trb  # noqa: E402

sys.modules[__name__] = _trb
