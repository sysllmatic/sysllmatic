import os
import subprocess
import csv
from dotenv import load_dotenv
import json
import tempfile

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
RAPL_TOOL = os.path.join(USER_PREFIX, "RAPL/main")
RUNTIME_LOG = os.path.join(USER_PREFIX, "src/runtime_logs/java.csv")

def run_mflops(jar_path, benchmark_class, jvm_flags=""):
    java_cmd = f"java {jvm_flags} -cp {jar_path} {benchmark_class} false"
    result = subprocess.run(java_cmd, shell=True, check=True, capture_output=True, text=True)
    # Filter out the unwanted lines
    mflops = "\n".join(
        line for line in result.stdout.splitlines()
        if not (line.startswith("make[") or line.startswith("./"))
    )
    mflops = float(mflops.split("make")[0])
    print(f"MFLOPS: {mflops}")
    return mflops

def run_java(jar_path, main_class, jvm_flags=""):
    # Clear runtime log
    with open(RUNTIME_LOG, "w") as f:
        f.write("")

    # Load MSR module
    subprocess.run("sudo modprobe msr", shell=True, check=True)

    # Construct Java run command
    java_cmd = f"java {jvm_flags} -cp {jar_path} {main_class}"

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

    programs = [
        "FFT",
        "LU",
        "MonteCarlo",
        "SOR",
        "SparseCompRow"
    ]

    for program in programs:
        print(f"Processing: {program}")

        # Use provided Java classpath or path to .jar or compiled classes
        java_path = os.path.join(USER_PREFIX, f"benchmark_scimark/{program}/")  # You must include this in your dataset.json
        main_class = f"jnt.scimark2.{program}"
        benchmark_class = f"jnt.scimark2.{program}Benchmark"

        try:
            # Run without JIT optimization
            orig_metrics = run_java(java_path, main_class)
            orig_mflops = run_mflops(java_path, benchmark_class)

            # Run with JIT optimization flags
            jit_flags = (
                # "-server "
                # "-XX:+UseSuperWord "
                # "-XX:+TieredCompilation "
                # "-XX:TieredStopAtLevel=4 "
                # "-XX:MaxInlineSize=100 "
                # "-XX:FreqInlineSize=100 "

                "-server "
                "-Xms512m -Xmx512m "
                "-XX:-TieredCompilation "
                "-Xbatch "
                "-XX:+UseSuperWord "
            )


            opt_metrics = run_java(java_path, main_class, jvm_flags=jit_flags)
            opt_mflops = run_mflops(java_path, benchmark_class, jvm_flags=jit_flags)
            mflops_improvement = round(opt_mflops / orig_mflops, 3)

            # Compute % improvement
            improvement = percent_improvement(orig_metrics, opt_metrics)+ (mflops_improvement,)
            results.append((program, *improvement))

            print(f"{program}: Energy: {improvement[0]}x, Latency: {improvement[1]}x, "
                  f"CPU Cycles: {improvement[2]}x, Memory: {improvement[3]}x, Mflops: {improvement[4]}x")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed processing {program}: {e}")

    # Save to CSV
    with open("optimization_results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Id", "Energy x", "Latency x", "CPU Cycles x", "Memory x", "Mflops x"])
        writer.writerows(results)

    # Aggregate results
    if results:
        num_entries = len(results)
        sum_energy = sum(r[1] for r in results)
        sum_latency = sum(r[2] for r in results)
        sum_cpu = sum(r[3] for r in results)
        sum_memory = sum(r[4] for r in results)
        sum_mflops = sum(r[5] for r in results)

        print("\n=== Average % Improvement Across All Entries ===")
        print(f"Energy: {round(sum_energy / num_entries, 3)}x")
        print(f"Latency: {round(sum_latency / num_entries, 3)}x")
        print(f"CPU Cycles: {round(sum_cpu / num_entries, 3)}x")
        print(f"Memory: {round(sum_memory / num_entries, 3)}x")
        print(f"Mflops: {round(sum_mflops / num_entries, 3)}x")
    else:
        print("No valid results to aggregate.")

if __name__ == "__main__":
    main()