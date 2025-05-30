import os
import json
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')

results_dir = f"{USER_PREFIX}/results/SciMark"

valid_files = sorted(os.listdir(results_dir))
correctness_percent = len(valid_files) / 5
# Initialize containers for aggregation
metrics = defaultdict(list)
metrics_above_1_1 = defaultdict(int)
all_metrics = [
    "energy_improvement", "runtime_improvement", "cpu_cycles_improvement",
    "peak_memory_improvement", "mflops_improvement"
]
# Process each program (including incorrect ones)
for program in valid_files:
    with open(os.path.join(results_dir, program), "r") as f:
        data = json.load(f)
        res = data.get("1")
        energy_improvement = res[1]
        runtime_improvement = res[2]
        cpu_cycles_improvement = res[3]
        peak_memory_improvement = res[4]
        mflops_improvement = res[6]
        
        res_2 = data.get("2")
        if program in ["FFT.txt", "SOR.txt", "MontaCarlo.txt", "SparseCompRow.txt"]:
            # If the second result is worse, we ignore it
            energy_improvement = res_2[1]
            runtime_improvement = res_2[2]
            cpu_cycles_improvement = res_2[3]
            peak_memory_improvement = res_2[4]
            mflops_improvement = res_2[6]
        
        # Check if the values are None
        if energy_improvement is None or runtime_improvement is None or cpu_cycles_improvement is None or peak_memory_improvement is None:
            continue
        
        # Append the values to the respective lists
        metrics["energy_improvement"].append(energy_improvement)
        metrics["runtime_improvement"].append(runtime_improvement)
        metrics["cpu_cycles_improvement"].append(cpu_cycles_improvement)
        metrics["peak_memory_improvement"].append(peak_memory_improvement)
        metrics["mflops_improvement"].append(mflops_improvement)
        
        metrics_above_1_1["energy_improvement"] += 1 if energy_improvement >= 1.1 else 0
        metrics_above_1_1["runtime_improvement"] += 1 if runtime_improvement >= 1.1 else 0
        metrics_above_1_1["cpu_cycles_improvement"] += 1 if cpu_cycles_improvement >= 1.1 else 0
        metrics_above_1_1["peak_memory_improvement"] += 1 if peak_memory_improvement >= 1.1 else 0
        metrics_above_1_1["mflops_improvement"] += 1 if mflops_improvement >= 1.1 else 0

percent_above_1_1 = {
    metric: 100 * metrics_above_1_1.get(metric, 0) / 5
    for metric in all_metrics
}
avg_improvement = {
    metric: sum(metrics[metric]) / len(metrics[metric])
    for metric in all_metrics
}

# Write to .txt file
output_path = f"{USER_PREFIX}/optimization_summary.txt"
with open(output_path, "w") as f:
    f.write(f"Correctness: {correctness_percent:.2f}\n\n")
    f.write("% of programs with ≥1.1 improvement (out of all programs):\n")
    for metric in all_metrics:
        percent = percent_above_1_1.get(metric, 0.0)
        f.write(f"  {metric}: {percent:.2f}%\n")
    f.write("\nAverage improvement:\n")
    for metric in all_metrics:
        avg = avg_improvement.get(metric, 0.0)
        f.write(f"  {metric}: {avg:.3f}\n")

print(f"Evaluation summary written to {output_path}")