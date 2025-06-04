import os
import subprocess
import csv
from dotenv import load_dotenv
import json
import tempfile

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
RAPL_TOOL = os.path.join(USER_PREFIX, "MEASURE/main")
RUNTIME_LOG = os.path.join(USER_PREFIX, "src/runtime_logs/java.csv")

def run_dacapo(jar_path, benchmark_name, jvm_flags=""):

    with open(RUNTIME_LOG, "w") as f:
        f.write("")

    subprocess.run("sudo modprobe msr", shell=True, check=True)

    # Construct Java command
    java_cmd = f"java {jvm_flags} -jar {jar_path} {benchmark_name}"

    # Run with RAPL tool
    subprocess.run(f"sudo {RAPL_TOOL} \"{java_cmd}\" java {jar_path}", shell=True, check=True)
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
        return 0, 0, 0, 0

    avg_energy = sum(d[1] for d in benchmark_data) / len(benchmark_data)
    avg_latency = sum(d[2] for d in benchmark_data) / len(benchmark_data)
    avg_cpu = sum(d[3] for d in benchmark_data) / len(benchmark_data)
    avg_memory = sum(d[4] for d in benchmark_data) / len(benchmark_data)

    return avg_energy, avg_latency, avg_cpu, avg_memory

def percent_improvement(before, after):
    return tuple(round(b / a, 3) if b != 0 else 0 for b, a in zip(before, after))

def build_benchmark(benchmark_name):

    try:
        print(f"Building {benchmark_name}...")
        os.chdir(f"{USER_PREFIX}/benchmark_dacapo/benchmarks")
        subprocess.run(["ant", benchmark_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to build {benchmark_name}: {e}")
        return False
    return True

def main():
    results = []
    # benchmarks = ["fop", "biojava", "pmd", "graphchi"]

    benchmarks = ["biojava"]

    dacapo_jar = os.path.join(USER_PREFIX, "benchmark_dacapo/benchmarks/dacapo-evaluation-git-4e3de06d-dirty.jar")

    for benchmark in benchmarks:
        print(f"\nProcessing: {benchmark}")
        
        # Verify/build benchmark if needed
        if not build_benchmark(benchmark):
            continue

        try:
            print("Running baseline...")
            orig_metrics = run_dacapo(dacapo_jar, benchmark)

            jit_flags = (  
                "-server "
                "-XX:+UseSuperWord "
                "-XX:+TieredCompilation "
                "-XX:TieredStopAtLevel=4 "
                "-XX:MaxInlineSize=100 "
                "-XX:FreqInlineSize=100 "
                "-Xms2g -Xmx2g "
            )

            print("Running with optimizations...")
            opt_metrics = run_dacapo(dacapo_jar, benchmark, jvm_flags=jit_flags)

            # Calculate improvement like SciMark
            improvement = percent_improvement(orig_metrics, opt_metrics)
            results.append((benchmark, *improvement))

            print(f"{benchmark}: Energy: {improvement[0]}x, Latency: {improvement[1]}x, "
                  f"CPU Cycles: {improvement[2]}x, Memory: {improvement[3]}x")

        except subprocess.CalledProcessError as e:
            print(f"❌ Failed processing {benchmark}: {e}")

    # Save to CSV
    with open("dacapo_optimization_results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Benchmark", "Energy x", "Latency x", "CPU Cycles x", "Memory x"])
        writer.writerows(results)

    # Aggregate results
    if results:
        num_entries = len(results)
        sum_energy = sum(r[1] for r in results)
        sum_latency = sum(r[2] for r in results)
        sum_cpu = sum(r[3] for r in results)
        sum_memory = sum(r[4] for r in results)

        print("\n=== Average % Improvement Across All Benchmarks ===")
        print(f"Energy: {round(sum_energy / num_entries, 3)}x")
        print(f"Latency: {round(sum_latency / num_entries, 3)}x")
        print(f"CPU Cycles: {round(sum_cpu / num_entries, 3)}x")
        print(f"Memory: {round(sum_memory / num_entries, 3)}x")
    else:
        print("No valid results to aggregate.")

if __name__ == "__main__":
    main()