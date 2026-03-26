# break_even_plots.py
# Compute & plot break-even runs for BioJava and ZXing under multiple energy models.

import math
import matplotlib.pyplot as plt

# ---------------------------
# Inputs
# ---------------------------
apps = ["BioJava", "ZXing"]

# Energy model inputs
baseline_energy_J = [481.940060, 603.993466]       # Joules per run (before optimization)
improvement_factor_energy = [2.151935437, 1.045950152]      # energy speedup factor
num_queries = [54, 60]                        # number of LLM queries used to optimize each app

# Latency model inputs
baseline_latency_s = [9.367834, 4.258019]        # seconds per run (before optimization)
improvement_factor_latency = [3.617558445, 1.062438573]
total_time_cost_s = [47*60, 45*60]            # one-time optimization time cost in seconds

# ---------------------------
# Energy models (Wh per query)
# ---------------------------
energy_models_Wh_per_query = {
    "0.24 Wh/q": 0.24,
    "0.30 Wh/q": 0.30,
    "3.00 Wh/q":  3.00,
    "4.32 Wh/q": 4.32,
}

# ---------------------------
# Calculations — Energy
# ---------------------------
E_after_J = [b / f for b, f in zip(baseline_energy_J, improvement_factor_energy)]
savings_per_run_J = [b - a for b, a in zip(baseline_energy_J, E_after_J)]  # ΔE per run

def total_opt_cost_J(Wh_per_query, n_queries):
    return Wh_per_query * n_queries * 3600.0  # 1 Wh = 3600 J

break_even_energy = {label: [] for label in energy_models_Wh_per_query}
for label, wh_q in energy_models_Wh_per_query.items():
    for n_q, dE in zip(num_queries, savings_per_run_J):
        cost_J = total_opt_cost_J(wh_q, n_q)
        N = cost_J / dE if dE > 0 else math.inf
        break_even_energy[label].append(N)

# ---------------------------
# Calculations — Latency
# ---------------------------
L_after_s = [b / f for b, f in zip(baseline_latency_s, improvement_factor_latency)]
savings_per_run_latency_s = [b - a for b, a in zip(baseline_latency_s, L_after_s)]
break_even_latency = [
    cost / dL if dL > 0 else math.inf
    for cost, dL in zip(total_time_cost_s, savings_per_run_latency_s)
]

# ---------------------------
# Plot — Energy Break-even
# ---------------------------
fig_w, fig_h = 6.5, 4.0
plt.figure(figsize=(fig_w, fig_h))

x = range(len(apps))
bar_width = 0.2
offsets = [-1.5*bar_width, -0.5*bar_width, 0.5*bar_width, 1.5*bar_width]

model_order = ["0.24 Wh/q", "0.30 Wh/q", "3.00 Wh/q", "4.32 Wh/q"]

for i, label in enumerate(model_order):
    vals = break_even_energy[label]
    xpos = [xi + offsets[i] for xi in x]
    bars = plt.bar(xpos, vals, width=bar_width, label=label)
    for bx, v in zip(bars, vals):
        plt.annotate(f"{v:.0f}",
                     (bx.get_x() + bx.get_width()/2, v),
                     ha="center", va="bottom", fontsize=8)

plt.xticks(x, apps)
plt.yscale("log")
plt.ylabel("Break-even runs (energy, log scale)")
plt.title("Break-even Runs vs. Energy Model per LLM Query")
plt.legend()
plt.tight_layout()
plt.savefig("break_even_energy_biojava_ZXing.png", dpi=200)
plt.close()

# ---------------------------
# Console summary
# ---------------------------
print("Energy savings per run (J):", [f"{v:.3f}" for v in savings_per_run_J])
print("Break-even runs (energy):")
for label in model_order:
    vals = break_even_energy[label]
    print(f"  {label}: BioJava={vals[0]:.2f}, ZXing={vals[1]:.2f}")

print("\nBreak-even runs (latency):")
print(f"  BioJava={break_even_latency[0]:.2f}, ZXing={break_even_latency[1]:.2f}")
