"""z_api2.py -- set subsolver_params via merge_text_format on this ortools build, check the portfolio on a toy."""
import random
from ortools.sat.python import cp_model


def core4_text(workers=4):
    V = [("core_a", "linearization_level: 1"), ("core_b", "linearization_level: 0 random_seed: 7"),
         ("core_c", "linearization_level: 1 find_multiple_cores: false random_seed: 13"),
         ("core_d", "linearization_level: 0 max_sat_reverse_assumption_order: true random_seed: 29")][:workers]
    t = f"num_workers: {workers} num_full_subsolvers: {workers} "
    t += " ".join(f'subsolvers: "{n}"' for n, _ in V) + " "
    t += " ".join(f'subsolver_params {{ name: "{n}" optimize_with_core: true {o} }}' for n, o in V)
    return t


sv2 = cp_model.CpSolver()
sv2.parameters.merge_text_format(core4_text())
m = cp_model.CpModel()
xs = [m.NewBoolVar(f"x{i}") for i in range(400)]
random.seed(1)
for i in range(1200):
    a, b, c = random.sample(range(400), 3)
    m.AddBoolOr([xs[a], xs[b], xs[c]])
m.Minimize(sum(xs))
sv2.parameters.max_time_in_seconds = 5
sv2.parameters.log_search_progress = True
sv2.parameters.log_to_stdout = False
lines = []
sv2.log_callback = lambda s: lines.append(s)
st = sv2.Solve(m)
print(sv2.StatusName(st), sv2.ObjectiveValue(), sv2.BestObjectiveBound())
for l in lines:
    if "subsolver" in l.lower() or l.startswith("#Bound") or l.startswith("#Done") or "core_" in l or "workers" in l:
        print(l[:160])
