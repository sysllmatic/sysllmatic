# dacapo_benchmark.py
from benchmarks.benchmark import Benchmark
import os
import subprocess
import sys
from dotenv import load_dotenv
from abstract_syntax_trees.java_ast import JavaAST
from utils import Logger
import csv
import re
from flamegraph_profiling import get_hotspots, find_unit_test
from java_method_profiling import replace_method_body, get_method_source_code, compile_java_project
from .dacapo_apps import get_app, run_app_and_measure

load_dotenv()
USER_PREFIX = os.path.expanduser(os.getenv('USER_PREFIX'))
logger = Logger("logs", sys.argv[2]).logger

class DaCapoBenchmark(Benchmark):
    def __init__(self, test_method, test_class, test_namespace, test_group, unit_tests, benchmark_name, method_level, methods_list):
        self.method_name = test_method
        self.class_name = test_class
        self.namespace_name = test_namespace
        self.group_name = test_group
        self.unit_tests = unit_tests
        self.program = benchmark_name
        self.app = get_app(benchmark_name, check=False)

        self.compilation_error = None
        self.runtime_error = None
        self.energy_data = {}
        self.evaluator_feedback_data = {}
        self.original_code = None
        self.optimization_iteration = 0
        self.method_level = method_level
        self.methods_list = methods_list
        self.set_original_code()

    def set_original_code(self):
        source_path = self.app.get_source_path(self.class_name, self.namespace_name, self.group_name)
        if self.method_level:
            compile_java_project()
            code = get_method_source_code(source_path, self.method_name)
        else:
            try:
                with open(source_path, 'r') as file:
                    code = file.read()
            except FileNotFoundError:
                logger.error(f"File not found: {source_path}")
                return

        if code is None:
            logger.error(f"Failed to retrieve code for {self.class_name} in {self.program}.")
            return
        if len(code.splitlines()) >= 1000:
            logger.error(f"Code has more than 1000 lines, skipping...")
            return

        self.original_code = self.remove_java_comments(code)

    def remove_java_comments(self, code):
        pattern = r'''
            ("(?:\\.|[^"\\])*")       |  # Group 1: Match double-quoted strings
            ('(?:\\.|[^'\\])*')       |  # Group 2: Match single-quoted strings
            (//.*?$)                  |  # Group 3: Match single-line comments
            (/\*[\s\S]*?\*/)             # Group 4: Match multi-line comments
        '''
        def replacer(match):
            if match.group(1) or match.group(2):
                return match.group(0)
            else:
                return ''

        return re.sub(pattern, replacer, code, flags=re.MULTILINE | re.VERBOSE)

    def get_original_code(self):
        return self.original_code

    def set_original_energy(self):
        logger.info("Run benchmark on the original code")
        os.chdir(self.app.get_build_dir(self.group_name))

        try:
            subprocess.run(["sudo", "make", "compile", f"BENCHMARK={self.program}"], check=True, capture_output=True, text=True)
            logger.info("Original code compile successfully.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code compile failed: {e.stdout + e.stderr}\n")
            return False

        if not self._run_rapl():
            return False

        avg_energy, avg_latency, avg_cpu_cycles, avg_memory, throughput = self._compute_avg()

        self.energy_data[0] = (self.original_code, round(avg_energy, 3), round(avg_latency, 3),  avg_cpu_cycles, avg_memory, round(throughput, 3), len(self.original_code.splitlines()))        
        return True

    def pre_process(self, code):
        ast = JavaAST("java")
        return ast.create_ast(code)

    def post_process(self, code):
        code = code.replace("```java", "").replace("```", "")
        return self.remove_java_comments(code)

    def _get_destination_path_of_source_code(self):
        return self.app.get_source_path(self.class_name, self.namespace_name, self.group_name)

    def compile(self, optimized_code):
        destination_path = self._get_destination_path_of_source_code()
        if self.method_level:
            with open(f"{USER_PREFIX}/src/runtime_logs/optimized_java.txt", "w") as file:
                file.write(optimized_code)
            replace_successfully = replace_method_body(destination_path, self.method_name)
            if not replace_successfully:
                self.compilation_error = "Please provide Java code in the original method format"
                return False
        else:
            with open(destination_path, "w") as file:
                file.write(optimized_code)

        os.chdir(self.app.get_build_dir(self.group_name))

        try:
            subprocess.run(["sudo", "make", "compile", f"BENCHMARK={self.program}"], check=True, capture_output=True, text=True)
            logger.info("Optimized code compile successfully.\n")
            self.compilation_error = None
            return True
        except subprocess.CalledProcessError as e:
            self.compilation_error = e.stdout + e.stderr
            logger.error(f"Compile optimized code failed: {e}\n")
            logger.error(f"Maven output: {self.compilation_error}")
            return False

    def get_compilation_error(self):
        return super().get_compilation_error()

    def run_tests(self):
        os.chdir(self.app.get_build_dir(self.group_name))

        for test in self.unit_tests:
            logger.info(f"Run unit test: {test}")
            try:
                result = subprocess.run(["sudo", "make", "test", f"BENCHMARK={self.program}", f"TEST={test}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1')
                if result.returncode != 0:
                    logger.error(f"Test {test} failed with error:\nstdout: {result.stdout}\nstderr: {result.stderr}")
                    self.runtime_error = result.stderr + result.stdout
                    return False             
            except subprocess.CalledProcessError as e:
                self.runtime_error = result.stderr + result.stdout
                logger.error(f"Test {test} execution failed: {e}\nstdout: {e.stdout}\nstderr: {e.stderr}")
                return False
            
        # try:
        #     result = subprocess.run(["sudo", "make", "test", f"BENCHMARK={self.program}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1')
        #     if result.returncode != 0:
        #         logger.error(f"Test failed with error:\nstdout: {result.stdout}\nstderr: {result.stderr}")
        #         self.runtime_error = result.stderr + result.stdout
        #         return False             
        # except subprocess.CalledProcessError as e:
        #     self.runtime_error = result.stderr + result.stdout
        #     logger.error(f"Test execution failed: {e}\nstdout: {e.stdout}\nstderr: {e.stderr}")
        #     return False
    
        logger.info("All test passed successfully.")
        self.runtime_error = None
        return True

    def measure_energy(self, optimized_code):
        logger.info(f"Iteration {self.optimization_iteration + 1}, run benchmark on the optimized code")
        self._run_rapl()

        avg_energy, avg_latency, avg_cpu_cycles, avg_memory, throughput = self._compute_avg()
        if avg_energy == 0 or avg_latency == 0 or avg_cpu_cycles == 0 or avg_memory == 0 or throughput == 0:
            logger.error(f"RAPL returns 0")
            return False

        original_data = self.energy_data[0]
        energy_change = original_data[1] / avg_energy
        speedup = original_data[2] / avg_latency
        cpu_change = original_data[3] / avg_cpu_cycles
        memory_change = original_data[4] / avg_memory
        throughput_change = throughput / original_data[5]

        self.energy_data[self.optimization_iteration + 1] = (optimized_code, round(energy_change, 3), round(speedup, 3), cpu_change, memory_change, throughput_change, len(optimized_code.splitlines()))
        self.evaluator_feedback_data = self._extract_content(self.energy_data)   
        return True

    def _run_rapl(self):
        log_file_path = f"{USER_PREFIX}/src/runtime_logs/java.csv"
        open(log_file_path, "w").close()
        os.chdir(self.app.get_build_dir(self.group_name))

        try:
            subprocess.run(["sudo", "make", "measure", f"TEST={self.unit_tests[0]}"], check=True, capture_output=True, text=True, timeout=120)
            logger.info("Make measure successfully.\n")
            return True
        except subprocess.TimeoutExpired:
            logger.error("Make measure timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Make measure failed: {e.stderr + e.stdout}\n")
            return False

    def _compute_avg(self):
        benchmark_data = []
        throughput = 0
        with open(f'{USER_PREFIX}/src/runtime_logs/java.csv', mode='r', newline='') as file:
            csv_reader = csv.reader(file)
            for index, row in enumerate(csv_reader):
                if index == 5:
                    throughput = row[1]
                else:
                    benchmark_data.append(tuple(row[:5]))

        avg_energy = avg_latency = avg_cpu_cycles = avg_memory = 0
        for data in benchmark_data:
            energy = float(data[1])
            if energy >= 0:
                avg_energy += energy
                avg_latency += float(data[2])
                avg_cpu_cycles += float(data[3])
                avg_memory += float(data[4])

        count = len(benchmark_data)
        return avg_energy/count, avg_latency/count, avg_cpu_cycles/count, avg_memory/count, float(throughput)

    def get_evaluator_feedback_data(self):
        return super().get_evaluator_feedback_data()

    def static_analysis(self, optimized_code):
        return super().static_analysis(optimized_code)

    def _extract_content(self, contents):
        keys = list(contents.keys())
        first_value = contents[keys[0]]
        last_value = contents[keys[-1]]

        max_key = max(contents.items(), key=lambda x: x[1][2])[0]
        max_value = contents[max_key]

        return {
            "original": dict(zip(["source_code", "avg_energy", "avg_runtime", "avg_cpu_cycles", "avg_memory", "throughput", "num_of_lines"], first_value)),
            "max_avg_speedup": dict(zip(["source_code", "avg_energy_improvement", "avg_speedup", "avg_cpu_improvement", "avg_memory_improvement", "avg_throughput_improvement", "num_of_lines"], max_value)),
            "current": dict(zip(["source_code", "avg_energy_improvement", "avg_speedup", "avg_cpu_improvement", "avg_memory_improvement", "avg_throughput_improvement", "num_of_lines"], last_value))
        }

    def generate_flame_report(self, code):
        return self.methods_list

    def dynamic_analysis(self, code):
        return super().dynamic_analysis(code)

    def restore_last_working_optimized_code(self, code):
        destination_path = self._get_destination_path_of_source_code()
        with open(destination_path, "w") as file:
            file.write(code)

def get_valid_dacapo_classes(application_name):
    # step 1: get app instance if app exists and built successfully
    app = get_app(application_name, check=True)
    
    # profile
    hotspots = get_hotspots("Dacapo", application_name, top_K=50)
    methods_name = [method for method, count in hotspots]

    transformed_data = []
    for method in methods_name:
        logger.info(f"method: {method}")
        parts = method.split('/')
        
        # Fail-safe extraction of test_class and test_method
        if '.' in parts[-1]:
            test_class, test_method = parts[-1].rsplit('.', 1)
        else:
            logger.error(f"Invalid method format: {parts[-1]}")
            continue

        test_namespace, test_group, unit_test_class_name, root_path = app.get_test_info_from_parts(parts, test_class)
        
        if test_namespace is None:
            logger.error(f"Failed to extract source code for: {method}")
            continue
        
        unit_tests = find_unit_test(root_path, unit_test_class_name, test_class)

        if len(unit_tests) == 0:
            logger.error(f"{test_class} has no unit tests!")
            continue

        transformed_data.append((test_method, test_class, test_namespace, test_group, unit_tests))

    logger.info(transformed_data)
    setup_makefile(application_name)
    return transformed_data

def setup_makefile(application_name):
    app = get_app(application_name, check=False)
    subfolders = app.get_makefile_subfolders()

    for subfolder in subfolders:
        logger.info(subfolder)
        with open(f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/makefile_template.mak", "r") as template_file:
            makefile_content = template_file.read()
        with open(f"{subfolder}/Makefile", "w") as makefile:
            makefile.write(makefile_content)