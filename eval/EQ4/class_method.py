import matplotlib.pyplot as plt
import numpy as np

# Categories and values
categories = ['Latency', 'Memory', 'CPU', 'Throughput', 'Energy']
method_values = [1.492, 0.973, 0.775, 1.251, 2.253]
class_values = [1.551, 0.982, 1.516, 1.385, 1.505]
method_correct = 0.60
class_correct = 1.00

x = np.arange(len(categories))

# Create stacked bar chart
fig, ax = plt.subplots(figsize=(10, 6))

# Plot correctness as base
ax.bar(x - 0.2, [method_correct]*len(x), width=0.4, label='Correctness (Function)', color='lightgray')
ax.bar(x + 0.2, [class_correct]*len(x), width=0.4, label='Correctness (Class)', color='darkgray')

# Plot performance metrics stacked on top of correctness
ax.bar(x - 0.2, method_values, width=0.4, bottom=[method_correct]*len(x), label='Function-Level', alpha=0.7, color='lightblue')
ax.bar(x + 0.2, class_values, width=0.4, bottom=[class_correct]*len(x), label='Class-Level', alpha=1, color='skyblue')

# Formatting
ax.set_ylabel('Value (Correctness + Metric)', fontsize=16)
# ax.set_title('Comparision between Function-level and Class-level Optimization on SciMark')
ax.set_xticks(x)
ax.set_xticklabels(categories, fontsize=16)
ax.legend(loc='upper left', fontsize=14)

plt.tight_layout()
plt.savefig("class_method.png", bbox_inches="tight")
plt.show()
