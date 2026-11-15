#!/usr/bin/env python3
"""Hub operator wres2 = op_wres.py with the v2 defaults: equal-cost exploration queries (p 0.7), every new
equal-cost structure adopted (sideways 1.0), and 40% of the job time spent polishing (gate kernel, hub
op_polish settings) up to 2 adopted window results.  Arguments given on the command line override."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import op_wres  # noqa: E402

sys.exit(op_wres.main(['--explore', '0.7', '--sideways', '1.0', '--polish-share', '0.4', '--npolish', '2'] + sys.argv[1:]))
