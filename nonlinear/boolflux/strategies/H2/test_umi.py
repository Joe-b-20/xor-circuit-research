import json, sys
import tsearch as TS
from tower import W, W2
cells = [(1, W2), (W, W2), (W2, 1), (W, 1), (W2, W)]
mem = []
for a, b, c in TS.ROWS:
    for r, t in cells:
        mem.append([list(TS.lin_comb(r, a, t, b)), list(c)])
json.dump({'gamma': 0, 'members': mem, 'name': 'h2-umizame-rebuild'}, open(sys.argv[1], 'w'))
