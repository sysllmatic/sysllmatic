import os
import subprocess
import json
import re
import sys
import csv
from dotenv import load_dotenv
from abstract_syntax_trees.cpp_ast import CPPAST
from benchmark import Benchmark
from utils import Logger
import signal

class TimeoutException(Exception):
    pass

def timeout_handler(signum, frame):
    raise TimeoutException("post_process timed out")
signal.signal(signal.SIGALRM, timeout_handler)

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
logger = Logger("logs", sys.argv[2]).logger

class HumanEvalBenchmark(Benchmark):
    def __init__(self, id, function_code, stress_test, test_code, entry_point):
        self.program = id
        self.function_code = function_code
        self.stress_test = stress_test
        self.test_code = test_code
        self.entry_point = entry_point
        self.compilation_error = None
        self.runtime_error = None
        self.energy_data = {}
        self.evaluator_feedback_data = {}
        self.original_code = None
        self.optimization_iteration = 0
        self.set_original_code()

    def set_original_code(self):
        self.original_code = self.function_code

    def get_original_code(self):
        return self.original_code

    def set_original_energy(self):
        logger.info("Run benchmark on the original code")
        os.chdir(f"{USER_PREFIX}/benchmark_human_eval/{self.program}")
                
        destination_path = f"{USER_PREFIX}/benchmark_human_eval/{self.program}/{self.program}.cpp"
        with open(destination_path, "w") as file:
            file.write(f"{self.function_code}\n\n{self.test_code}")
            
        destination_path = f"{USER_PREFIX}/benchmark_human_eval/{self.program}/stress_{self.program}.cpp"
        with open(destination_path, "w") as file_stress:
            file_stress.write(f"{self.function_code}\n\n{self.stress_test}")

        try:
            subprocess.run(["make", "compile"], check=True, capture_output=True, text=True, timeout=120)
            subprocess.run(["make", "compile_stress"], check=True, capture_output=True, text=True, timeout=120)
            logger.info("Original code compiled successfully.")
        except subprocess.TimeoutExpired:
            logger.error("Make compile timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code compile failed: {e.stderr}")
            return False

        success = self._run_rapl(optimized=False)
        if not success:
            return False

        energy, latency, cpu_cycles, peak_memory, throughput = self._compute_avg()

        self.energy_data[0] = (
            self.original_code,
            round(energy, 3),
            round(latency, 3),
            round(cpu_cycles, 3),
            round(peak_memory, 3),
            round(throughput, 3),
            len(self.original_code.splitlines())
        )
        return True

    def pre_process(self, code):
        ast = CPPAST("cpp")
        source_code_path = f"{USER_PREFIX}/benchmark_human_eval/{self.program}/ast_{self.program}.cpp"
        with open(source_code_path, 'w') as file:
            file.write(code)
        ast = ast.create_ast(source_code_path, self.entry_point)
        return ast

    def post_process(self, code, timeout_sec=60):
        logger.info(f"Post processing code")
        signal.alarm(timeout_sec)  # Start timer
        
        try:
            if "```cpp" in code:
                code = code.split("```cpp")[1].split("```")[0].strip()
        
            def remove_main_function(cpp_code: str) -> str:
                # Regex pattern to match the main function (basic heuristic)
                pattern = re.compile(
                    r'\bint\s+main\s*\([^)]*\)\s*{'
                    r'(?:[^{}]*|{[^{}]*})*'
                    r'}', 
                    re.DOTALL
                )

                cleaned_code = re.sub(pattern, '', cpp_code)
                return cleaned_code
            code = remove_main_function(code)
            return re.sub(r'//.*?$|/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
        except TimeoutException:
            logger.error("Post process timed out")
            return code
        finally:
            signal.alarm(0) # Stop timer
        
    def compile(self, optimized_code):
        destination_path = f"{USER_PREFIX}/benchmark_human_eval/{self.program}/optimized_{self.program}.cpp"
        with open(destination_path, "w") as file:
            file.write(f"{optimized_code}\n\n{self.test_code}")
            
        destination_path = f"{USER_PREFIX}/benchmark_human_eval/{self.program}/stress_optimized_{self.program}.cpp"
        with open(destination_path, "w") as file_stress:
            file_stress.write(f"{optimized_code}\n\n{self.stress_test}")

        os.chdir(f"{USER_PREFIX}/benchmark_human_eval/{self.program}")
        try:
            subprocess.run(["make", "compile_optimized"], check=True, capture_output=True, text=True)
            subprocess.run(["make", "compile_stress_optimized"], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            self.compilation_error = e.stderr
            logger.error(f"Compile failed: {self.compilation_error}")
            return False
        
        self.compilation_error = None
        return True

    def run_tests(self):
        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_human_eval/{self.program}")

        try:        
            logger.info(f"Running optimized program")
            result = subprocess.run(["make", "run_optimized"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1', timeout=120)
        except subprocess.CalledProcessError as e:
            self.runtime_error = e.stderr
            logger.error(f"Run_Test failed: {self.runtime_error}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Make run timeout")
            return False

        if result.returncode is None or result.returncode != 0:
            return False
        
        self.runtime_error = None
        return True

    def measure_energy(self, optimized_code):
        logger.info(f"Iteration {self.optimization_iteration + 1}, run benchmark on the optimized code")
                
        measure_success = self._run_rapl(optimized=True)
        if not measure_success:
            return False
        energy, latency, cpu_cycles, peak_memory, throughput = self._compute_avg()

        original_data = self.energy_data[0]
        self.energy_data[self.optimization_iteration + 1] = (
            optimized_code,
            round(original_data[1] / energy, 3),
            round(original_data[2] / latency, 3),
            round(original_data[3] / cpu_cycles, 3),
            round(original_data[4] / peak_memory, 3),
            round(throughput / original_data[5], 3),
            len(optimized_code.splitlines())
        )
        self.evaluator_feedback_data = self._extract_content(self.energy_data)
      
    def _run_rapl(self, optimized):
        log_file_path = f"{USER_PREFIX}/src/runtime_logs/c++.csv"
        open(log_file_path, "w").close()

        os.chdir(f"{USER_PREFIX}/benchmark_human_eval/{self.program}")

        try:
            cmd = ["make", "measure_optimized" if optimized else "measure"]
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Make measure failed: {e.stderr}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Make measure timeout")
            return False

    def _compute_avg(self):
        benchmark_data = []
        throughput = 0
        with open(f'{USER_PREFIX}/src/runtime_logs/c++.csv', mode='r') as file:
            reader = csv.reader(file)
            for index, row in enumerate(reader):
                if index == 5:
                    throughput = row[1]
                else:
                    benchmark_data.append((row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4])))

        if not benchmark_data:
            return 0, 0, 0, 0, 0

        #Find average energy usage and average runtime
        avg_energy = 0
        avg_latency = 0
        avg_cpu_cycles = 0
        avg_memory = 0
        for data in benchmark_data:
            energy = float(data[1])
            if energy < 0:
                benchmark_data.remove(data)
            else:
                avg_energy += energy
                avg_latency += float(data[2])
                avg_cpu_cycles += float(data[3])
                avg_memory += float(data[4])

        avg_energy /= len(benchmark_data)
        avg_latency /= len(benchmark_data)
        avg_cpu_cycles /= len(benchmark_data)
        avg_memory /= len(benchmark_data)

        return avg_energy, avg_latency, avg_cpu_cycles, avg_memory, float(throughput)

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
        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_human_eval/{self.program}")

        #Generate flame report using test case #0
        problem_id = self.program.split('.')[0]

        source_code_path = f"{USER_PREFIX}/benchmark_human_eval/{self.program}/flamegraph_{self.program}.cpp"
        with open(source_code_path, 'w') as file:
            file.write(f"{code}\n\n{self.stress_test}")
            
        # compile the code
        try: 
            result = subprocess.run(
                ["make", "compile_code_for_flame_report"], 
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Compiled code used for flame report successfully.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Compiling code used for flame report failed: {e.stdout + e.stderr}\n")
            return

        logger.info(f"Generating flame report for original program across all test cases")
        
        try: 
            result_flame_report = subprocess.run(
                ["make", "generate_flame_report"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='latin-1'
            )
            logger.info(f"Generate flame_report successfully.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Generate flame_report failed: {e.stdout + e.stderr}\n")
        
        try:
            flame_report_path = f"{USER_PREFIX}/benchmark_human_eval/{problem_id}/flame_report.txt"
        except FileNotFoundError:
            logger.error(f"Flame report file not found: {flame_report_path}\n")
            return
        
        def extract_subtree(input_file_path):
            with open(input_file_path, 'r') as input_file:
                lines = input_file.readlines()
            start_index = 13
            
            if len(lines) < 80:
                return lines[start_index:-3]
            return lines[start_index:60]
        
        flame_report = extract_subtree(flame_report_path)
        
        if flame_report is None:
            logger.error(f"Flame report is None\n")
            return
        
        logger.info(f"Flame report:\n{flame_report}\n")
                
        self.evaluator_feedback_data["flame_report"] = flame_report
        return flame_report

    def get_energy_data(self):
        return super().get_energy_data()
    
    def get_evaluator_feedback_data(self):
        return super().get_evaluator_feedback_data()

    def static_analysis(self, optimized_code):
        return super().static_analysis(optimized_code)

    def dynamic_analysis(self, code):
        return super().dynamic_analysis(code)

def get_valid_humaneval_programs(num_programs):
    with open(f"{USER_PREFIX}/benchmark_human_eval/dataset.json", 'r') as file:
        data = json.load(file)
        
    valid_programs = []
    
    for entry in data[:num_programs]:
        id = entry['task_id']
        folder_path = f"{USER_PREFIX}/benchmark_human_eval/{id}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        #Create a new cpp file in the folder with the source code
        function_code = entry['function_code']
        stress_test = entry['cpp_stress_test']
        test_code = entry['test_code']
        entry_point = entry['entry_point']
        
        #Create parameterized Makefile for each problem id folder
        makefile_template = open(f"{USER_PREFIX}/benchmark_human_eval/makefile_template.mak", "r")
        makefile_content = makefile_template.read()
        makefile_content = makefile_content.replace("${FILE_NAME}", id)
        makefile_template.close()
        makefile_template = open(f"{folder_path}/Makefile", "w")
        makefile_template.write(makefile_content)
        makefile_template.close()
        
        valid_programs.append((id, function_code, stress_test, test_code, entry_point))
    
    return valid_programs
        