import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Data dictionary without 'No meaningful changes'
data = {
    'Algorithm-Level Optimizations': {
        'Select Computationally Efficient Algorithms': 42,
        'Structure Algorithm to Support Instruction-Level Parallelism (ILP)': 28,
        'Select Space-Efficient Algorithm': 13,
        'Select Algorithm Based on Instruction Speed': 14,
        'Select Efficient Data Structures': 1
    },
    'Memory and Data Locality Optimizations': {
        'Buffering': 40,
        'Increase Cache Efficiency via Locality': 24
    },
    'Data Structure Selection and Adaptation': {
        'Darwinian Data Structure Selection': 5
    },
    'Code Smells and Structural Simplification': {
        'Remove Unnecessary Method Calls': 9,
        'Remove Code Bloat by Removing Optional Features': 2,
        'Remove duplicate code': 1
    },
    'Loop Transformations': {
        'Loop Unrolling': 5,
        'Loop Fusion': 2
    },
    'Control-Flow and Branching Optimizations': {
        'Combining branches': 1,
        'Remove branches with min/max instructions': 1,
        'Rearranging Branches': 2
    }
}

# Short y-axis labels
short_labels = {
    'Algorithm-Level Optimizations': 'Algorithm Opt.',
    'Memory and Data Locality Optimizations': 'Memory & Locality',
    'Data Structure Selection and Adaptation': 'DS Structure',
    'Code Smells and Structural Simplification': 'Code Smells',
    'Loop Transformations': 'Loop Trans.',
    'Control-Flow and Branching Optimizations': 'Control-Flow'
}

# Descriptive legend labels for subpatterns
sub_short = {
    'Select Computationally Efficient Algorithms': 'Computationally Efficient',
    'Structure Algorithm to Support Instruction-Level Parallelism (ILP)': 'ILP Structure',
    'Select Space-Efficient Algorithm': 'Space-Efficient Algorithm',
    'Select Algorithm Based on Instruction Speed': 'Instruction-Speed Algorithm',
    'Select Efficient Data Structures': 'Efficient Data Structures',
    'Buffering': 'Buffering',
    'Increase Cache Efficiency via Locality': 'Cache Locality',
    'Darwinian Data Structure Selection': 'Darwinian DS',
    'Remove Unnecessary Method Calls': 'Remove Method Calls',
    'Remove Code Bloat by Removing Optional Features': 'Remove Code Bloat',
    'Remove duplicate code': 'Remove Duplicate Code',
    'Loop Unrolling': 'Loop Unrolling',
    'Loop Fusion': 'Loop Fusion',
    'Combining branches': 'Combine Branches',
    'Remove branches with min/max instructions': 'Min/Max Branches',
    'Rearranging Branches': 'Rearrange Branches'
}

# Color maps for each category
colormaps = {
    'Algorithm-Level Optimizations': ('Blues', 5),
    'Memory and Data Locality Optimizations': ('Greens', 2),
    'Data Structure Selection and Adaptation': ('PuBu', 1),
    'Code Smells and Structural Simplification': ('Oranges', 3),
    'Loop Transformations': ('Reds', 2),
    'Control-Flow and Branching Optimizations': ('PuRd', 3)
}

# Flatten subpatterns
subpatterns = []
for cat, sub in data.items():
    for sp in sub.keys():
        subpatterns.append((cat, sp))

# Build DataFrame
rows = []
for cat in data.keys():
    row = [data[cat].get(sp, 0) for _, sp in subpatterns]
    rows.append(row)
df = pd.DataFrame(rows,
                  index=list(data.keys()),
                  columns=[sp for _, sp in subpatterns])

# Generate colors by category
colors = []
for cat, sp in subpatterns:
    cmap_name, count = colormaps[cat]
    cmap = plt.get_cmap(cmap_name)
    idx = list(data[cat].keys()).index(sp)
    colors.append(cmap((idx + 0.5) / count))

# Plot
fig, ax = plt.subplots(figsize=(12, 7))
left = np.zeros(len(df))
y_labels = [short_labels[cat] for cat in df.index]

for i, (_, sp) in enumerate(subpatterns):
    ax.barh(y_labels, df.iloc[:, i], left=left,
            label=sub_short[sp], color=colors[i])
    left += df.iloc[:, i].values

# Add total counts
totals = df.sum(axis=1).values
for i, total in enumerate(totals):
    ax.text(total + 1, i, str(total), va='center', fontsize=12)

# Final styling
ax.set_xlabel('Count', fontsize=17)
ax.tick_params(axis='y', labelsize=16)
ax.tick_params(axis='x', labelsize=15)
ax.set_xlim(0, max(totals) * 1.15)

# Legend at top center
legend = ax.legend(title='Sub-Patterns',
                   loc='upper center',
                   bbox_to_anchor=(0.57, 1),
                   ncol=3,
                   framealpha=0.3,
                   fontsize=12,
                   title_fontsize=14)
legend.get_frame().set_edgecolor('none')

plt.tight_layout()
plt.savefig('optimization_pattern.png', dpi=300)
plt.show()
