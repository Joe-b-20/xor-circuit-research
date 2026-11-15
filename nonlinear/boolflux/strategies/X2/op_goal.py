#!/usr/bin/env python3
"""X2 wrapper operator: lets hub/scheduler_goal.py use the hub's own Scheduler.launch unchanged (run ids, job
dict, pinning) and still give a job goal caps / objective.  The scheduler sets, just for the Popen inside
Scheduler.launch, env X2_REAL = the real operator script, X2_CAPS = 'A,AD,GD' ('-' = free, empty = none),
X2_OBJECTIVE; this wrapper appends --caps / --objective to its argv and execs the real script (the job's
process tree, pinning and memory cap are unchanged)."""
import os
import sys

real = os.environ.get('X2_REAL')
if not real:
    sys.exit('op_goal.py: X2_REAL not set')
argv = [sys.executable, real] + sys.argv[1:]
if os.environ.get('X2_CAPS'): argv += ['--caps=' + os.environ['X2_CAPS']]   # '=': a value may start with '-'
if os.environ.get('X2_OBJECTIVE'): argv += ['--objective', os.environ['X2_OBJECTIVE']]
os.execv(sys.executable, argv)
