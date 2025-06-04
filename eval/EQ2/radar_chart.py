import matplotlib.pyplot as plt
import numpy as np

# Define the benchmark names and metrics
benchmarks = ["SciMark", "HumanEval", "DaCapoBench"]
metrics = ['Correct', 'Latency', 'Memory', 'CPU', 'Throughput', 'Energy']

# Raw metric values for each benchmark (including Correctness initially)
data = {
    "SciMark":   [1.00, 1.55, 0.98, 1.52, 1.39, 1.51],
    "HumanEval": [0.8841, 1.69, 1.01, 10.40, 0.0, 2.04],  # Throughput was missing; use 0
    "DaCapoBench": [0.75, 1.846, 1.106, 0.892, 2.244, 1.456]
}

# Filter out 'Correct' (index 0)
metric_indices = [1, 2, 3, 4, 5]
filtered_metrics = [metrics[i] for i in metric_indices]

# Extract the data without the Correctness metric
filtered_data_matrix = np.array([data[b] for b in benchmarks])[:, metric_indices]

# Normalize values by the maximum of each column
max_vals = np.max(filtered_data_matrix, axis=0)
normalized_data = filtered_data_matrix / max_vals

# Compute angles for radar plot
angles = np.linspace(0, 2 * np.pi, len(filtered_metrics), endpoint=False).tolist()
angles += angles[:1]  # close the circle

# Create radar plot
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

for i, benchmark in enumerate(benchmarks):
    values = normalized_data[i].tolist()
    values += values[:1]  # close the circle
    ax.plot(angles, values, label=benchmark, marker='o')
    ax.fill(angles, values, alpha=0.1)

# Set aesthetics
ax.set_yticklabels([])
ax.set_xticks(angles[:-1])
ax.set_xticklabels(filtered_metrics, fontsize=20)
# ax.set_title("Trade-off Analysis of Multi-Metric Optimization Gains", size=14)
ax.legend(loc='center left', fontsize=16)

plt.tight_layout()
plt.savefig("radar_chart.png", bbox_inches="tight")
plt.show()
