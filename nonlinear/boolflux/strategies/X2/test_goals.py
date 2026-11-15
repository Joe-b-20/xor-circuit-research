#!/usr/bin/env python3
"""X2: checks of hub/goals.py (python3 test_goals.py)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub import goals as GL   # noqa: E402

B, C, G = GL.goal('B'), GL.goal('C'), GL.goal('G')
assert GL.meets(B, (28, 4, 130, 22)) and not GL.meets(B, (28, 4, 131, 22)) and GL.meets(B, (27, 3, 120, 20))
assert GL.key(B, (28, 4, 131, 23)) == (0, 0, 2, 1)
assert GL.key(B, (28, 4, 131, 23)) < GL.key(B, (28, 4, 133, 20))          # sum 2 < sum 3
assert GL.key(B, (28, 5, 120, 20)) > GL.key(B, (28, 4, 160, 30))          # AD excess outranks any G/GD excess
assert GL.key(B, (29, 4, 130, 22)) > GL.key(B, (28, 5, 200, 40))          # AND excess outranks everything
assert GL.scalar(G, (48, 4, 151, 11)) == 4011 and GL.scalar(G, (43, 4, 141, 12)) == 2
assert GL.stepping(B, (28, 4, 140, 22)) and not GL.stepping(B, (28, 4, 140, 23)) and not GL.stepping(B, (28, 4, 130, 22))
assert GL.stepping(GL.goal('A'), (28, 6, 300, 40)) and not GL.stepping(GL.goal('A'), (29, 4, 130, 22))
assert GL.step_gain((0, 0, 3, 1), (0, 0, 2, 2)) == 1.0 and GL.step_gain((1, 0, 0, 0), (0, 0, 5, 1)) == 8.0
assert GL.step_gain((0, 0, 3, 1), (0, 0, 3, 0)) == 0.25 and GL.step_gain((0, 0, 2, 1), (0, 0, 2, 1)) == 0.0
s0 = GL.state([(28, 4, 131, 23), (35, 3, 139, 27)]); s1 = GL.state([(28, 4, 131, 23), (35, 3, 138, 26)])
assert GL.state_key(s1) < GL.state_key(s0) and s1['F']['met']
s2 = GL.state([(28, 4, 131, 22), (35, 3, 139, 27)])                       # B progress outranks F met
assert GL.state_key(s2) < GL.state_key(s1)
print('goals ok')
