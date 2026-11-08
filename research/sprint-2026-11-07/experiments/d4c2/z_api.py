"""z_api.py -- check which CP-SAT python features this ortools build has (bound callback, stop_search,
subsolver_params)."""
import ortools
from ortools.sat.python import cp_model
from ortools.sat import sat_parameters_pb2 as sp
print("ortools", ortools.__version__)
sv = cp_model.CpSolver()
print("best_bound_callback" in dir(sv), "stop_search" in dir(sv), "StopSearch" in dir(sv))
p = sp.SatParameters()
print("subsolver_params" in p.DESCRIPTOR.fields_by_name, "subsolvers" in p.DESCRIPTOR.fields_by_name,
      "extra_subsolvers" in p.DESCRIPTOR.fields_by_name, "num_full_subsolvers" in p.DESCRIPTOR.fields_by_name)
for f in ("core_minimization_level", "find_multiple_cores", "cover_optimization", "max_sat_stratification",
          "max_sat_assumption_order", "max_sat_reverse_assumption_order", "share_level_zero_bounds",
          "share_binary_clauses", "share_glue_clauses"):
    print(f, f in p.DESCRIPTOR.fields_by_name, getattr(p, f, None))
