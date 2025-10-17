import pandas as pd
import matplotlib.pyplot as plt

# Create the dataset
data = {
    "app": ["ZXing", "ZXing", "ZXing", "Pmd", "Pmd", "Pmd", "Fop", "Fop", "Fop"],
    "k": [50, 100, 150, 50, 100, 150, 50, 100, 150],
    "energy": [-2, -8.591847141, 2.752033435, 16, 0.605586665, -0.8986027373, 3, -12.18784854, -2.879265427],
    "latency": [5, -9.063685366, 5.853761623, 11, 2.951424472, -0.611122482, 2, 8.764348322, -2.440538217],
    "cpu": [7, -7.733971862, 3.246179599, 26, 6.354401886, -0.3541298901, 4, -7.208556753, -2.573035051],
    "memory": [4, -1.901997458, 7.392423529, 0, -6.472735143, -7.191639829, 0, 0.858876906, -0.3715122527],
    "throughput": [-1, -9.065349268, 5.867760672, 12, 2.951304726, -0.5983454166, 7, 3.321698384, -2.440538217],
}

df = pd.DataFrame(data)

# Convert to cumulative (incremental sum per app)
df_cum = df.copy()
metrics = ["energy", "latency", "cpu", "memory", "throughput"]

for app in df["app"].unique():
    mask = df["app"] == app
    df_cum.loc[mask, metrics] = df.loc[mask, metrics].cumsum()

# Plot: one figure with subplots
fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=True)

for ax, app in zip(axes, df_cum["app"].unique()):
    subset = df_cum[df_cum["app"] == app]
    for metric in metrics:
        ax.plot(subset["k"], subset[metric], marker="o", label=metric)
    ax.set_title(app.capitalize(), fontsize=18)
    ax.set_xlabel("k")
    ax.set_xlabel("Top-K Hotspots", fontsize=17)
    ax.tick_params(axis="both", labelsize=15)
    ax.grid(True)

axes[0].set_ylabel("Cumulative Value", fontsize=17)

# Shared legend at bottom
fig.legend(metrics, loc="lower center", ncol=len(metrics), fontsize=15)
fig.suptitle("Cumulative Performance Improvement by Varying Top-K Hotspots", fontsize=21)

plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # make space for legend
plt.savefig("metrics_line_chart.png", dpi=300, bbox_inches="tight")
plt.show()