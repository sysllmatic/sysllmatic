import os
import subprocess
import csv
from dotenv import load_dotenv
import json
import tempfile

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
DATASET_JSON_PATH = os.path.join(USER_PREFIX, "benchmark_human_eval/dataset.json")
RAPL_TOOL = os.path.join(USER_PREFIX, "RAPL/main")

RUNTIME_LOG = os.path.join(USER_PREFIX, "src/runtime_logs/c++.csv")
# Check if the RAPL log file exists
if not os.path.exists(RUNTIME_LOG):
    os.makedirs(os.path.dirname(RUNTIME_LOG), exist_ok=True)
    with open(RUNTIME_LOG, "w") as f:
        f.write("")


def compile_and_run(file_path, obj_file, bin_file, opt_level=""):
    compile_flags = f"-g {opt_level} -c -pipe -fomit-frame-pointer -march=native -std=c++11 -fopenmp"
    link_flags = f"-g {opt_level} -fopenmp"

    # Compile
    subprocess.run(f"/usr/bin/g++ {compile_flags} {file_path} -o {obj_file}", shell=True, check=True)
    subprocess.run(f"/usr/bin/g++ {link_flags} {obj_file} -o {bin_file} -lssl -lcrypto", shell=True, check=True)

    # Run with RAPL
    # clear c++.cvs first
    with open(RUNTIME_LOG, "w") as f:
        f.write("")
    subprocess.run("sudo modprobe msr", shell=True, check=True)
    subprocess.run(f"sudo {RAPL_TOOL} {bin_file} c++ {file_path}", shell=True, check=True)
    subprocess.run(f"sudo chmod -R 777 {RUNTIME_LOG}", shell=True, check=True)

    return extract_metrics()

def extract_metrics():
    benchmark_data = []
    with open(RUNTIME_LOG, mode='r') as file:
        reader = csv.reader(file)
        for index, row in enumerate(reader):
            if index < 5:
                benchmark_data.append((row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4])))

    benchmark_data = [d for d in benchmark_data if d[1] >= 0]
    if not benchmark_data:
        return 0, 0, 0, 0, 0

    avg_energy = sum(d[1] for d in benchmark_data) / len(benchmark_data)
    avg_latency = sum(d[2] for d in benchmark_data) / len(benchmark_data)
    avg_cpu = sum(d[3] for d in benchmark_data) / len(benchmark_data)
    avg_memory = sum(d[4] for d in benchmark_data) / len(benchmark_data)

    return avg_energy, avg_latency, avg_cpu, avg_memory

def percent_improvement(before, after):
    return tuple(round(b / a, 3) if b != 0 else 0 for b, a in zip(before, after))

def main():
    results = []

    with open(DATASET_JSON_PATH, "r") as f:
        dataset = json.load(f)

    for entry in dataset:
        id = entry["task_id"]
        print(f"Processing: {id}")

        # Create a temporary directory for compilation
        with tempfile.TemporaryDirectory() as tmpdir:
            cpp_file = os.path.join(tmpdir, "solution.cpp")
            obj_file = os.path.join(tmpdir, "solution.cpp.o")
            bin_file = os.path.join(tmpdir, "solution.gpp_run")

            # Combine function and test code
            function_code = entry["function_code"]
            cpp_stress_test = entry["cpp_stress_test"]
            # Create the full code
            full_code = f"{function_code}\n\n{cpp_stress_test}"

            # Write to file
            with open(cpp_file, "w") as f:
                f.write(full_code)

            try:
                # Original compilation
                orig_metrics = compile_and_run(cpp_file, obj_file, bin_file, opt_level="")

                # Optimized compilation (-O3)
                opt_metrics = compile_and_run(cpp_file, obj_file, bin_file, opt_level="-O3")

                # Compute % improvement
                improvement = percent_improvement(orig_metrics, opt_metrics)
                results.append((id, *improvement))

                print(f"{id}: Energy: {improvement[0]}x, Latency: {improvement[1]}x, "
                    f"CPU Cycles: {improvement[2]}x, Memory: {improvement[3]}x")
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed processing {id}: {e}")

    # Save to CSV
    with open("optimization_results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Id", "Energy x", "Latency x", "CPU Cycles x", "Memory x"])
        writer.writerows(results)

    # Compute average improvements across all entries
    if results:
        num_entries = len(results)
        sum_energy = sum(r[1] for r in results)
        sum_latency = sum(r[2] for r in results)
        sum_cpu = sum(r[3] for r in results)
        sum_memory = sum(r[4] for r in results)

        avg_energy = round(sum_energy / num_entries, 3)
        avg_latency = round(sum_latency / num_entries, 3)
        avg_cpu = round(sum_cpu / num_entries, 3)
        avg_memory = round(sum_memory / num_entries, 3)

        print("\n=== Average % Improvement Across All Entries ===")
        print(f"Energy: {avg_energy}x")
        print(f"Latency: {avg_latency}x")
        print(f"CPU Cycles: {avg_cpu}x")
        print(f"Memory: {avg_memory}x")
    else:
        print("No valid results to aggregate.")

if __name__ == "__main__":
    main()