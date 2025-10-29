import os
import sys
import json
import csv
import re
import signal
import subprocess
from dotenv import load_dotenv
from abstract_syntax_trees.cpp_ast import CPPAST
from benchmarks.benchmark import Benchmark
from utils import Logger

class TimeoutException(Exception): pass

def timeout_handler(signum, frame):
    raise TimeoutException("post_process timed out")
signal.signal(signal.SIGALRM, timeout_handler)

load_dotenv()
USER_PREFIX = os.getenv("USER_PREFIX")
logger = Logger("logs", sys.argv[2]).logger

class HumanEvalBenchmark(Benchmark):
    def __init__(self, task_id, function_code, stress_test, test_code, entry_point):
        self.program = task_id
        self.function_code = function_code
        self.stress_test = stress_test
        self.test_code = test_code
        self.entry_point = entry_point
        self.compilation_error = None
        self.runtime_error = None
        self.original_code = None
        self.energy_data = {}
        self.evaluator_feedback_data = {}
        self.optimization_iteration = 0
        self.working_dir = os.path.join(USER_PREFIX, "benchmark_human_eval", self.program)
        self.set_original_code()
        
    def set_original_code(self):
        self.original_code = self.function_code
    
    def get_original_code(self):
        return self.original_code

    def set_original_energy(self):
        logger.info("Run benchmark on the original code")
        self._write_code_file(f"{self.program}.cpp", self.function_code, self.test_code)
        self._write_code_file(f"stress_{self.program}.cpp", self.function_code, self.stress_test)

        if not self._compile(["compile", "compile_stress"]):
            return False

        if not self._run_rapl(optimized=False):
            return False

        energy, latency, cpu_cycles, peak_memory, throughput = self._compute_avg()
        self.energy_data[0] = (
            self.original_code,
            round(energy, 3), round(latency, 3), round(cpu_cycles, 3),
            round(peak_memory, 3), round(throughput, 3),
            len(self.original_code.splitlines())
        )
        return True

    def _write_code_file(self, filename, code, extra):
        path = os.path.join(self.working_dir, filename)
        with open(path, "w") as f:
            f.write(f"{code}\n\n{extra}")

    def _compile(self, targets):
        os.chdir(self.working_dir)
        for target in targets:
            try:
                subprocess.run(["make", target], check=True, capture_output=True, text=True, timeout=120)
                logger.info(f"Make {target} succeeded.")
            except subprocess.CalledProcessError as e:
                logger.error(f"Make {target} failed: {e.stderr}")
                self.compilation_error = e.stderr
                return False
            except subprocess.TimeoutExpired:
                logger.error(f"Make {target} timed out")
                return False
        self.compilation_error = None
        return True

    def pre_process(self, code):
        ast = CPPAST("cpp")
        ast_path = os.path.join(self.working_dir, f"ast_{self.program}.cpp")
        with open(ast_path, "w") as file:
            file.write(code)
        return ast.create_ast(ast_path, self.entry_point)

    def post_process(self, code, timeout_sec=60):
        logger.info("Post processing code")
        signal.alarm(timeout_sec)
        try:
            if "```cpp" in code:
                code = code.split("```cpp")[1].split("```")[0].strip()
            code = self._remove_main_function(code)
            return re.sub(r'//.*?$|/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
        except TimeoutException:
            logger.error("Post process timed out")
            return code
        finally:
            signal.alarm(0)

    def _remove_main_function(self, code):
        pattern = re.compile(r'\bint\s+main\s*\([^)]*\)\s*{(?:[^{}]*|{[^{}]*})*}', re.DOTALL)
        return re.sub(pattern, '', code)

    def compile(self, optimized_code):
        self._write_code_file(f"optimized_{self.program}.cpp", optimized_code, self.test_code)
        self._write_code_file(f"stress_optimized_{self.program}.cpp", optimized_code, self.stress_test)
        return self._compile(["compile_optimized", "compile_stress_optimized"])

    def run_tests(self):
        os.chdir(self.working_dir)
        try:
            result = subprocess.run(["make", "run_optimized"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="latin-1", timeout=120)
        except subprocess.TimeoutExpired:
            logger.error("Run timed out")
            return False
        except subprocess.CalledProcessError as e:
            self.runtime_error = e.stderr
            logger.error(f"Run failed: {self.runtime_error}")
            return False

        self.runtime_error = None
        return result.returncode == 0

    def measure_energy(self, optimized_code):
        logger.info(f"Iteration {self.optimization_iteration + 1}: measuring optimized code")
        if not self._run_rapl(optimized=True):
            return False

        energy, latency, cpu_cycles, peak_memory, throughput = self._compute_avg()
        original = self.energy_data[0]

        self.energy_data[self.optimization_iteration + 1] = (
            optimized_code,
            round(original[1] / energy, 3),
            round(original[2] / latency, 3),
            round(original[3] / cpu_cycles, 3),
            round(original[4] / peak_memory, 3),
            round(throughput / original[5], 3),
            len(optimized_code.splitlines())
        )
        self.evaluator_feedback_data = self._extract_content(self.energy_data)

    def _run_rapl(self, optimized):
        os.chdir(self.working_dir)
        log_path = os.path.join(USER_PREFIX, "src/runtime_logs/c++.csv")
        open(log_path, "w").close()
        try:
            subprocess.run(["make", "measure_optimized" if optimized else "measure"], check=True, capture_output=True, text=True, timeout=180)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Measure failed: {e.stderr}")
        except subprocess.TimeoutExpired:
            logger.error("Measure timed out")
        return False

    def _compute_avg(self):
        log_path = os.path.join(USER_PREFIX, "src/runtime_logs/c++.csv")
        benchmark_data = []
        throughput = 0

        with open(log_path, mode='r') as file:
            reader = csv.reader(file)
            for i, row in enumerate(reader):
                if i == 5:
                    throughput = row[1]
                else:
                    try:
                        benchmark_data.append(tuple(map(float, row[1:5])))
                    except ValueError:
                        continue

        if not benchmark_data:
            return 0, 0, 0, 0, 0

        avg = list(map(lambda i: sum(d[i] for d in benchmark_data) / len(benchmark_data), range(4)))
        return *avg, float(throughput)

    def _extract_content(self, contents):
        keys = list(contents.keys())
        first_value = contents[keys[0]]
        last_value = contents[keys[-1]]
        
        # print all values
        logger.info(f"key 0, avg_energy: {first_value[1]}, avg_runtime: {first_value[2]}, avg_cpu_cycles: {first_value[3]}, avg_memory: {first_value[4]}, throughput: {first_value[5]}, num_of_lines: {first_value[6]}")
        for key, (source_code, avg_energy, avg_runtime, avg_cpu_cycles, avg_memory, throughput, num_of_lines) in list(contents.items())[1:]:
            logger.info(f"key: {key}, avg_energy_improvement: {avg_energy}, avg_speedup: {avg_runtime}, avg_cpu_improvement: {avg_cpu_cycles}, avg_memory_improvement: {avg_memory}, avg_throughput_improvement: {throughput}, num_of_lines: {num_of_lines}")

        # Loop through the contents to find the key with the highest speedup
        max_avg_speedup = float('-inf')
        max_avg_speedup_key = None
        for key, (source_code, avg_energy, avg_speedup, avg_cpu_cycles, avg_memory, throughput, num_of_lines) in list(contents.items())[1:]:
            if avg_speedup > max_avg_speedup:
                max_avg_speedup = avg_speedup
                max_avg_speedup_key = key

        max_value = contents[max_avg_speedup_key]
        
        return {
            "original": {
                "source_code": first_value[0],
                "avg_energy": first_value[1],
                "avg_runtime": first_value[2],
                "avg_cpu_cycles": first_value[3],
                "avg_memory": first_value[4],
                "throughput": first_value[5],
                "num_of_lines": first_value[6]
            },
            "max_avg_speedup": {
                "source_code": max_value[0],
                "avg_energy_improvement": max_value[1],
                "avg_speedup": max_value[2],
                "avg_cpu_improvement": max_value[3],
                "avg_memory_improvement": max_value[4],
                "avg_throughput_improvement": max_value[5],
                "num_of_lines": max_value[6]
            },
            "current": {
                "source_code": last_value[0],
                "avg_energy_improvement": last_value[1],
                "avg_speedup": last_value[2],
                "avg_cpu_improvement": last_value[3],
                "avg_memory_improvement": last_value[4],
                "avg_throughput_improvement": last_value[5],
                "num_of_lines": last_value[6]
            }
        }

    def generate_flame_report(self, code):
        os.chdir(self.working_dir)
        flame_path = os.path.join(self.working_dir, f"flamegraph_{self.program}.cpp")
        with open(flame_path, "w") as f:
            f.write(f"{code}\n\n{self.stress_test}")

        try:
            subprocess.run(["make", "compile_code_for_flame_report"], check=True, capture_output=True, text=True)
            subprocess.run(["make", "generate_flame_report"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Flamegraph generation failed: {e.stderr}")
            return None

        report_path = os.path.join(self.working_dir, "flame_report.txt")
        if not os.path.exists(report_path):
            logger.error("Flame report not found")
            return None

        with open(report_path, "r") as f:
            lines = f.readlines()

        self.evaluator_feedback_data["flame_report"] = lines[13:60] if len(lines) > 60 else lines[13:-3]
        return self.evaluator_feedback_data["flame_report"]

    def get_energy_data(self):
        return super().get_energy_data()

    def get_evaluator_feedback_data(self):
        return super().get_evaluator_feedback_data()

    def static_analysis(self, optimized_code):
        return super().static_analysis(optimized_code)

    def dynamic_analysis(self, code):
        return super().dynamic_analysis(code)

def get_valid_humaneval_programs(n):
    path = os.path.join(USER_PREFIX, "benchmark_human_eval", "dataset.json")
    with open(path, "r") as f:
        data = json.load(f)

    valid_programs = []
    template_path = os.path.join(USER_PREFIX, "benchmark_human_eval", "makefile_template.mak")

    for entry in data[:n]:
        folder = os.path.join(USER_PREFIX, "benchmark_human_eval", entry["task_id"])
        os.makedirs(folder, exist_ok=True)

        with open(template_path, "r") as t:
            content = t.read().replace("${FILE_NAME}", entry["task_id"])
        with open(os.path.join(folder, "Makefile"), "w") as mf:
            mf.write(content)

        valid_programs.append((
            entry["task_id"],
            entry["function_code"],
            entry["cpp_stress_test"],
            entry["test_code"],
            entry["entry_point"]
        ))

    return valid_programs