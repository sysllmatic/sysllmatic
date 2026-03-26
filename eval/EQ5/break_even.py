# Full, self-contained code to generate the combined break-even plot for BioJava and zxing
# (and optionally the individual plots). This saves PNG files to /mnt/data and prints paths.

import numpy as np
import matplotlib.pyplot as plt

# --- Inputs: break-even runs (from your computed results) ---
BIOJAVA_ENERGY_RUNS = 226.06096990615583
BIOJAVA_LATENCY_RUNS = 416.03425524013727
ZXING_ENERGY_RUNS = 2442.118876015289
ZXING_LATENCY_RUNS = 10789.641876391532

# --- Usage frequencies to plot (runs per day) ---
runs_per_day = np.array([10, 50, 100, 150, 200, 300, 400, 500, 750, 1000], dtype=float)

def days_to_break_even(break_even_runs, runs_per_day_values):
    """Compute days to break-even = break-even runs / runs per day."""
    return break_even_runs / runs_per_day_values

# --- Compute curves (days to break-even for each metric/app) ---
biojava_energy_days  = days_to_break_even(BIOJAVA_ENERGY_RUNS,  runs_per_day)
biojava_latency_days = days_to_break_even(BIOJAVA_LATENCY_RUNS, runs_per_day)
zxing_energy_days      = days_to_break_even(ZXING_ENERGY_RUNS,      runs_per_day)
zxing_latency_days     = days_to_break_even(ZXING_LATENCY_RUNS,     runs_per_day)

# --- Convert to executions per month (assuming 30 days/month) ---
exec_per_month = runs_per_day * 30

# --- Compute time to break-even in months ---
def months_to_break_even(break_even_runs, exec_month_values):
    return break_even_runs / exec_month_values

biojava_energy_months  = months_to_break_even(BIOJAVA_ENERGY_RUNS,  exec_per_month)
biojava_latency_months = months_to_break_even(BIOJAVA_LATENCY_RUNS, exec_per_month)
zxing_energy_months      = months_to_break_even(ZXING_ENERGY_RUNS,      exec_per_month)
zxing_latency_months     = months_to_break_even(ZXING_LATENCY_RUNS,     exec_per_month)

# Hybrid plot: X-axis log scale (executions/month), Y-axis linear scale (months to break-even)

plt.figure(figsize=(7, 5))
plt.plot(exec_per_month, biojava_energy_months,  marker='o', label='BioJava Energy')
plt.plot(exec_per_month, biojava_latency_months, marker='s', label='BioJava Latency')
plt.plot(exec_per_month, zxing_energy_months,      marker='^', label='ZXing Energy')
plt.plot(exec_per_month, zxing_latency_months,     marker='d', label='ZXing Latency')

plt.xscale('log')  # Wide range of execution frequencies
# my_ticks = [10*30, 50*30, 100*30, 150*30, 200*30, 300*30, 400*30, 500*30, 750*30, 1000*30]
# plt.xticks(my_ticks, labels=[str(t) for t in my_ticks])
plt.xlabel('Executions per month (log scale)')
plt.ylabel('Months to break-even (linear scale)')
plt.title('Time to Break-even vs Monthly Execution Frequency')
plt.legend()
plt.grid(True, which='both', linestyle='--', linewidth=0.5)

plt.tight_layout()
hybrid_fig_path = 'combined_break_even_hybrid.png'
plt.savefig(hybrid_fig_path, dpi=200)
plt.close()

hybrid_fig_path


def print_payoff(app_name, energy_runs, latency_runs, daily_freq):
    energy_days = energy_runs / daily_freq
    latency_days = latency_runs / daily_freq
    
    print(f"--- {app_name} at {daily_freq} exec/day ---")
    
    # Energy formatting
    if energy_days > 365:
        print(f"Energy Payoff:  {energy_days/365:.2f} years")
    elif energy_days > 30:
        print(f"Energy Payoff:  {energy_days/30:.2f} months")
    else:
        print(f"Energy Payoff:  {energy_days:.2f} days")
        
    # Latency formatting
    if latency_days > 365:
        print(f"Latency Payoff: {latency_days/365:.2f} years")
    elif latency_days > 30:
        print(f"Latency Payoff: {latency_days/30:.2f} months")
    else:
        print(f"Latency Payoff: {latency_days:.2f} days")
    print()

# 1. Conservative Scenario
print("### CONSERVATIVE SCENARIO ###")
print_payoff("BioJava", BIOJAVA_ENERGY_RUNS, BIOJAVA_LATENCY_RUNS, 50)
print_payoff("ZXing", ZXING_ENERGY_RUNS, ZXING_LATENCY_RUNS, 50)

# 2. Heavy-Usage Scenario
print("### HEAVY-USAGE SCENARIO ###")
print_payoff("BioJava", BIOJAVA_ENERGY_RUNS, BIOJAVA_LATENCY_RUNS, 500)
print_payoff("ZXing", ZXING_ENERGY_RUNS, ZXING_LATENCY_RUNS, 500)