#!/usr/bin/env python3
"""Run a list of windows.  Usage:
    run.py CIRCUIT LOG SECONDS "W1;W2;..." [--dm D] [--closure]
Each window is a comma list of AND indices; with --closure the window is the consumer closure of
the listed ANDs (otherwise the list must already be closed).  m = |U| - D (default D = 1).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wsat import Base, run_window, mklog  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('circuit'); ap.add_argument('log'); ap.add_argument('seconds', type=float)
ap.add_argument('windows')
ap.add_argument('--dm', type=int, default=1)
ap.add_argument('--closure', action='store_true')
ap.add_argument('--tag', default='w')
ap.add_argument('--out', default='/home/joebachir20/xs-campaigns/2026-11-15-study/H3/found')
a = ap.parse_args()
b = Base(a.circuit)
log = mklog(a.log)
for i, w in enumerate(a.windows.split(';')):
    W = [int(t) for t in w.split(',') if t.strip()]
    U = b.closure(W) if a.closure else set(W)
    assert b.closure(U) == U, 'window not closed under consumers: %s' % sorted(U)
    run_window(b, U, len(U) - a.dm, a.seconds, '%s%d' % (a.tag, i), a.out, log,
               extra={'W': W, 'dm': a.dm})
