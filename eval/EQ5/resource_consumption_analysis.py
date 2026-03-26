# Given values
# biojava and pmd
baseline_energy_J = [481.940060, 603.993466]  # Joules per run
improvement_factor = [2.151935437, 1.045950152]   # speedup/energy factor
num_query = [54, 60]

# cost in Wh
cost_Wh = 0.3  # Cost per run in Watt-hours

total_cost = [query * cost_Wh for query in num_query]

# Convert cost to Joules
cost_J = [cost * 3600 for cost in total_cost]  # 1 Wh = 3600 Joules

# After-energy and savings per run
E_after = [b / f for b, f in zip(baseline_energy_J, improvement_factor)]
savings_per_run_J = [b - a for b, a in zip(baseline_energy_J, E_after)]

# Break-even number of runs
N_break_even = [cost_J / deltaP_J for cost_J, deltaP_J in zip(cost_J, savings_per_run_J)]

print(f"break-even number of runs (energy): {N_break_even}")

baseline_latency_ms = [9.367834, 4.258019] # second per run
improvement_factor_latency = [3.617558445, 1.062438573]  # speedup factor
total_cost = [47*60, 45*60] # time cost in mins
L_after = [b / f for b, f in zip(baseline_latency_ms, improvement_factor_latency)]
savings_per_run_latency = [b - a for b, a in zip(baseline_latency_ms, L_after)]

N_break_even_latency = [cost / deltaL for cost, deltaL in zip(total_cost, savings_per_run_latency)]

print(f"break-even number of runs (latency): {N_break_even_latency}")

# data
# break-even number of runs (energy): [226.06096990615583, 2442.118876015289]
# break-even number of runs (latency): [416.03425524013727, 10789.641876391532]