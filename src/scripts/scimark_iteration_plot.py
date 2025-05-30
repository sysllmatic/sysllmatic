import pandas as pd
import matplotlib.pyplot as plt

# Sample data for Feedback Iterations 1–4 (replace with your actual values)
data = {
    'Iteration': [1, 2, 3, 4],
    'Energy': [1.505, 2.850, 3.195, 3.984],
    'Latency': [1.551, 3.592, 6.700, 6.667],
    'CPU': [1.516, 0.963, 0.704, 0.890],
    'Memory': [0.982, 0.915, 0.883, 0.829],
    'MFLOPS': [1.385, 4.161, 6.464, 6.664]  # Note: increasing trend expected
}

df = pd.DataFrame(data)

# Plot each metric
plt.figure(figsize=(10, 6))
for metric in ['Energy', 'Latency', 'CPU', 'Memory', 'MFLOPS']:
    plt.plot(df['Iteration'], df[metric], marker='o', label=metric)

plt.title('SciMark Results Across 1 to 4 Feedback Iterations')
plt.xlabel('Evaluator Feedback Iteration')
plt.ylabel('Relative Improvement (x)')
plt.legend()
plt.grid(True)
plt.xticks([1, 2, 3, 4]) 
import numpy as np
plt.yticks(np.arange(0.5, 7.1, 0.5))
plt.tight_layout()
plt.savefig("feedback_iteration.png", bbox_inches="tight")
plt.show()
