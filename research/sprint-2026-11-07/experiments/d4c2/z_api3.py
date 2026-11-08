"""z_api3.py -- does CpModel.minimize replace an existing objective?"""
import inspect
from ortools.sat.python import cp_model as c
print(inspect.getsource(c.CpModel.minimize)[:700])
m = c.CpModel(); a = m.NewBoolVar("a"); b = m.NewBoolVar("b"); m.AddBoolOr([a, b])
m.Minimize(a + 2 * b); m.Minimize(3 * a + b)
s = c.CpSolver(); s.Solve(m); print("obj", s.ObjectiveValue(), s.Value(a), s.Value(b))
