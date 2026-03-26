import pandas as pd
import matplotlib.pyplot as plt

# Create the dataset
data = {
    "app": ["ZXing", "ZXing", "ZXing", "PMD", "PMD", "PMD", "Fop", "Fop", "Fop"],
    "k": [50, 100, 150, 50, 100, 150, 50, 100, 150],
    "energy": [
        4.595015227, -6.539661008, -1.817004741,
        2.439387656, -4.259107534, 1.924575851,
        0.5337539988, 0.1916595344, -3.060452459
    ],
    "latency": [
        6.243857259, -5.829383886, -1.987146935,
        2.250380938, -4.035354369, 2.030309983,
        0.9004087439, 0.02626960355, -2.665650233
    ],
    "cpu": [
        16.5753511, -6.468481244, -3.322495344,
        2.710692932, -8.549528369, 5.840066251,
        1.753908135, -0.9380959101, -1.355386429
    ],
    "memory": [
        1.840302138, -2.646372196, 6.827345383,
        4.688015769, -2.311096793, -0.06335916818,
        -1.50096817, 2.022635896, 1.910732321
    ],
    "throughput": [
        6.24384457, -5.829383913, -1.987135618,
        2.250369023, -4.035353971, 2.030321232,
        0.9003911993, 0.0262866281, -2.665649924
    ],
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
        # Make throughput markers smaller
        markersize = 4 if metric == "throughput" else 8
        ax.plot(subset["k"], subset[metric], marker="o", label=metric, alpha=0.7, markersize=markersize)
    ax.set_title(app, fontsize=18)
    ax.set_xlabel("k")
    ax.set_xlabel("Top-K Hotspots", fontsize=17)
    ax.tick_params(axis="both", labelsize=15)
    ax.grid(True)

axes[0].set_ylabel("Cumulative Value", fontsize=17)

# Shared legend at bottom
fig.legend(metrics, loc="lower center", ncol=len(metrics), fontsize=15)
fig.suptitle("Cumulative Performance Improvement by Varying Top-K Hotspots", fontsize=21)

plt.tight_layout(rect=[0, 0.05, 1, 0.95])  # make space for legend
plt.savefig("metrics_line_chart_new.png", dpi=300, bbox_inches="tight")
plt.show()