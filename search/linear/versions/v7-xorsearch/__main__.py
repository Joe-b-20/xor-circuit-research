"""Entry point: ``python3 search/xorsearch ...`` from the repository root, or
``python3 -m xorsearch ...`` with ``search/`` on the path (see ``cli.py``)."""
import os
import sys

if not __package__:
    # Run as a directory (`python3 search/xorsearch`): import the package from its parent
    # instead of putting the package directory itself on sys.path.
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path[0] = os.path.dirname(_here)
    _prog = "python3 " + os.path.relpath(_here)
else:
    _prog = "python3 -m xorsearch"

from xorsearch.cli import main  # noqa: E402

raise SystemExit(main(prog=_prog))
