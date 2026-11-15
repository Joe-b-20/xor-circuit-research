"""One-off patch of pdrive.py (copy of strategies/F/fdrive.py): hard A/AD guard on retained states,
trb imported from strategies/F."""
from pathlib import Path
p = Path(__file__).resolve().parent / 'pdrive.py'
s = p.read_text()
s = s.replace("sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))",
              "sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'F'))")
s = s.replace('"""Track-F driver:', '"""P3 copy of strategies/F/fdrive.py with a hard A/AD guard: a stage result that breaks\n--cap-a or --cap-ad is never retained as the current state (logged as hard-reject).\n\nTrack-F driver:', 1)
# guard helper after feas definition
s = s.replace("    key = lambda c: (0 if feas(c) else 1, metrics(c)[0], metrics(c)[2])",
              "    key = lambda c: (0 if feas(c) else 1, metrics(c)[0], metrics(c)[2])\n"
              "    hard = lambda c: metrics(c)[3] <= a.cap_ad and (a.cap_a is None or metrics(c)[1] <= a.cap_a)\n"
              "    assert hard(start), 'start breaks the hard A/AD caps'")
def guard(old, var):
    global s
    new = old.replace('cur = %s' % var, 'cur = (%s if hard(%s) else (note(\'hard-reject\', %s, stage) or cur))' % (var, var, var))
    assert old in s, old
    s = s.replace(old, new)
guard("offer(c, stage, 'gate'); cur = c", 'c')
guard("offer(c3, stage, 'osc-gate'); cur = c3", 'c3')
guard("                cur = c2\n", 'c2')
guard("offer(c2, stage, 'trb-%s' % reg); cur = c2", 'c2')
p.write_text(s)
print('patched')
