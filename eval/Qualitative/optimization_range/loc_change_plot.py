import pandas as pd
import matplotlib.pyplot as plt

# --- Data ---
with_catalog = pd.DataFrame({
    "App": ["BioJava", "PMD", "GraphChi", "Fop", "ZXing"],
    "Same": [133, 2164, 224, 3552, 1543],
    "Added": [210, 127, 61, 403, 296],
    "Deleted": [8, 221, 17, 784, 35],
    "Modified": [1781, 198, 47, 604, 169],
    "Source": "With Catalog"
})

without_catalog = pd.DataFrame({
    "App": ["BioJava", "PMD", "GraphChi", "Fop", "ZXing"],
    "Same": [102, 2397, 217, 2396, 1917],
    "Added": [175, 351, 108, 440, 168],
    "Deleted": [15, 92, 21, 524, 129],
    "Modified": [1619, 224, 50, 356, 166],
    "Source": "Without Catalog"
})

# Combine
comparison = pd.concat([with_catalog, without_catalog])

# --- Focus on Added / Deleted / Modified ---
focus_metrics = ["Added", "Deleted", "Modified"]
colors_focus = {
    "Added": "#4c72b0",   # soft sky blue
    "Deleted": "#dd8452", # muted red
    "Modified": "#55a868" # light green
}

apps = comparison["App"].unique()
with_cat = comparison[comparison["Source"]=="With Catalog"].set_index("App")[focus_metrics]
without_cat = comparison[comparison["Source"]=="Without Catalog"].set_index("App")[focus_metrics]

# --- Plot ---
fig, ax = plt.subplots(figsize=(10,6))
bar_width = 0.35
x = range(len(apps))

# Side-by-side stacked bars
for i, metric in enumerate(focus_metrics):
    bottom_with = with_cat.iloc[:, :i].sum(axis=1) if i > 0 else 0
    bottom_without = without_cat.iloc[:, :i].sum(axis=1) if i > 0 else 0
    
    ax.bar([p - bar_width/2 for p in x], with_cat[metric], bar_width, 
           bottom=bottom_with, label=metric, color=colors_focus[metric])
    ax.bar([p + bar_width/2 for p in x], without_cat[metric], bar_width, 
           bottom=bottom_without, color=colors_focus[metric])

# --- Labels ---
ax.set_xticks(list(x))
ax.set_xticklabels(apps)

ax.set_title("Comparison of LOC Changes: Added, Deleted, Modified", fontsize=16)
ax.legend(title="Change Type", fontsize=12, title_fontsize=13)
ax.set_ylabel("Number of LOC Changed", fontsize=14)
ax.set_xticklabels(apps, fontsize=13)

plt.tight_layout()
plt.savefig("side_by_side_stacked_changes_fixed_colors.png", dpi=300)
plt.show()
