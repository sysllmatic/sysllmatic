from abstract_syntax_trees.cpp_ast import CPPAST
from benchmark import Benchmark
from dotenv import load_dotenv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
from utils import Logger
import csv

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
logger = Logger("logs", sys.argv[2]).logger

class PIEBenchmark(Benchmark):
    def __init__(self, program):
        self.program = program #This is the CPP file name including the .cpp extension
        self.compilation_error = None
        self.energy_data = {}
        self.evaluator_feedback_data = {}
        self.expect_test_output = None
        self.original_code = None
        self.optimization_iteration = 0

        self.set_original_code()
    
    def set_original_code(self):
        source_path = f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}/{self.program}"
        with open(source_path, 'r') as file:
            self.original_code = file.read()

    def get_original_code(self):
        return self.original_code
    
    def set_original_energy(self):
        logger.info("Run benchmark on the original code")

        # compile
        # Needed for makefiles
        problem_id = self.program.split('.')[0]
        os.chdir(f"{USER_PREFIX}/benchmark_pie/{problem_id}")  
        try: 
            result = subprocess.run(
                ["make", "compile"], 
                check=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            self.compilation_error = result.stdout + result.stderr
            logger.info(f"Original code compile successfully.\n")
        except subprocess.TimeoutExpired:
            logger.error("Make compile timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code compile failed: {e}\n")
            return False
        
        test_case_folder = f"{USER_PREFIX}/benchmark_pie/{problem_id}/test_cases"
        input_files = sorted(glob.glob(f"{test_case_folder}/input.*.txt"))

        total_energy = 0
        total_latency = 0
        total_cpu_cycles = 0
        total_memory = 0
        total_throughput = 0
        
        for input_file in input_files:
            run_rapl_success = self._run_rapl(problem_id, optimized=False, input_file=input_file)
            if not run_rapl_success:
                return False
            energy, latency, cpu_cycles, peak_memory, throughput = self._compute_avg()

            total_energy += energy
            total_latency += latency
            total_cpu_cycles += cpu_cycles
            total_memory += peak_memory
            total_throughput += throughput

        total_num_input = len(input_files)
        avg_energy = total_energy / total_num_input
        avg_latency = total_latency / total_num_input
        avg_cpu_cycles = total_cpu_cycles / total_num_input
        avg_memory = total_memory / total_num_input
        avg_throughput = total_throughput / total_num_input

        #Append results to benchmark data dict
        self.energy_data[0] = (self.original_code, round(avg_energy, 3), round(avg_latency, 3),  round(avg_cpu_cycles, 3), round(avg_memory, 3), round(avg_throughput, 3), len(self.original_code.splitlines()))
        return True

    def pre_process(self, code):
        ast = CPPAST("cpp")
        source_code_path = f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}/ast_{self.program}"
        with open(source_code_path, 'w') as file:
            file.write(code)
        return ast.create_ast(source_code_path)

    def post_process(self, code):
        # Remove code block delimiters
        code = code.replace("```cpp", "").replace("```", "")
        # Remove all comments
        code = re.sub(r'//.*?$|/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
        return code

    def compile(self, optimized_code):
        logger.info(f"llm_optimize: : writing optimized code to benchmark_pie/{self.program.split('.')[0]}/optimized_{self.program}")
        destination_path = f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}/optimized_{self.program}"
        with open(destination_path, "w") as file:
            file.write(optimized_code)

        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}")  
        try: 
            result = subprocess.run(
                ["make", "compile_optimized"], 
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Compile successfully.\n")
            return True
        except subprocess.CalledProcessError as e:
            self.compilation_error = e.stderr
            logger.error(f"Compile failed: {self.compilation_error}\n")
            return False

    def get_compilation_error(self):
        return super().get_compilation_error()

    def run_tests(self):
        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}")

        # Iterate through all test cases and perform correctness check
        problem_id = self.program.split('.')[0]
        test_case_folder = f"{USER_PREFIX}/benchmark_pie/{problem_id}/test_cases"
        input_files = sorted(glob.glob(f"{test_case_folder}/input.*.txt"))
        output_files = sorted(glob.glob(f"{test_case_folder}/output.*.txt"))

        assert (len(input_files) == len(output_files)), "Number of input files and output files do not match"
        
        for i, input_file in enumerate(input_files):
            with open(output_files[i], 'r') as file:
                self.expect_test_output = self._process_output_content(file.read())

            optimized_output = self._run_program(True, input_file)

            if optimized_output == None:
                return False

            if not self._compare_outputs(optimized_output):
                return False
        return True

    def measure_energy(self, optimized_code):            
        #load the optimized code and data
        logger.info(f"Iteration {self.optimization_iteration + 1}, run benchmark on the optimized code")
        
        problem_id = self.program.split('.')[0]
        test_case_folder = f"{USER_PREFIX}/benchmark_pie/{problem_id}/test_cases"
        input_files = sorted(glob.glob(f"{test_case_folder}/input.*.txt"))
        
        energy_changes = []
        speedups = []
        cpu_changes = []
        memory_changes = []
        throughput_changes = []
        for input_file in input_files:
            self._run_rapl(problem_id, optimized=False, input_file=input_file)
            original_energy, original_latency, original_cpu_cycles, original_peak_memory, original_throughput = self._compute_avg()
            #print(f"unoptimized metrics: {original_energy}, {original_latency}, {original_cpu_cycles}, {original_peak_memory}, {original_throughput}")

            self._run_rapl(problem_id, optimized=True, input_file=input_file)
            energy, latency, cpu_cycles, peak_memory, throughput = self._compute_avg()

            energy_changes.append(original_energy / energy)
            speedups.append(original_latency / latency)
            cpu_changes.append(original_cpu_cycles / cpu_cycles)
            memory_changes.append(original_peak_memory / peak_memory)
            throughput_changes.append(throughput / original_throughput)

        avg_energy_change = sum(energy_changes) / len(energy_changes)
        avg_speed_up = sum(speedups) / len(speedups)
        avg_cpu_change = sum(cpu_changes) / len(cpu_changes)
        avg_memory_change = sum(memory_changes) / len(memory_changes)
        avg_throughput_change = sum(throughput_changes) / len(throughput_changes)

        #Append results to benchmark data dict
        self.energy_data[self.optimization_iteration + 1] = (optimized_code, round(avg_energy_change, 3), round(avg_speed_up, 3), round(avg_cpu_change, 3), round(avg_memory_change, 3), round(avg_throughput_change, 3), len(optimized_code.splitlines()))
        
        # Find the required benchmark elements
        self.evaluator_feedback_data = self._extract_content(self.energy_data)

    def generate_flame_report(self, code):
        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}")

        #Generate flame report using test case #0
        problem_id = self.program.split('.')[0]

        source_code_path = f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}/flamegraph_{self.program}"
        with open(source_code_path, 'w') as file:
            file.write(code)
            
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
            flame_report_path = f"{USER_PREFIX}/benchmark_pie/{problem_id}/flame_report.txt"
        except FileNotFoundError:
            logger.error(f"Flame report file not found: {flame_report_path}\n")
            return
        
        def extract_subtree(input_file_path):
            with open(input_file_path, 'r') as input_file:
                lines = input_file.readlines()
                
            start_index = 13

            root_line = lines[start_index].strip()
            root_indent = len(lines[start_index]) - len(lines[start_index].lstrip())

            subtree_lines = [root_line[1:] + '\n']

            for i in range(start_index + 1, len(lines) - 3):
                line = lines[i].strip()

                if not line:
                    continue  # Skip blank lines
                if line.startswith("|--"):
                    break  # End of subtree
                else:
                    if line[1:].lstrip() != "|":
                        subtree_lines.append(line[1:].lstrip() + '\n')

            return subtree_lines
        
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

    def _run_program(self, optimized, input_file):
        # Run the make command and capture the output in a variable
        try:
            if not optimized:
                result = subprocess.run(["make", "run"], stdin=open(input_file, 'r'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1', timeout=120)
            else:
                logger.info(f"Running optimized program with input file: {input_file}")
                result = subprocess.run(["make", "run_optimized"], stdin=open(input_file, 'r'), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1', timeout=120)
        except subprocess.TimeoutExpired:
            logger.error("Make run timeout")
            return None
            
        logger.info(f"_run_program result: {result}")

        # Check for runtime errors
        if result.returncode is not None and result.returncode != 0:
            return None

        # Filter out the unwanted lines
        filtered_output = "\n".join(
            line for line in result.stdout.splitlines()
            if not (line.startswith("make[") or line.startswith("./"))
        )
        logger.info(f"filtered_output: {filtered_output}")
        return filtered_output.split("make")[0]
    
    def _compare_outputs(self, optimized_output):
        # whitespace remove
        optimized_output = self._process_output_content(optimized_output)
        
        if self.expect_test_output == optimized_output:
            logger.info("Outputs are the same.\n")
            return True
        else:
            logger.error(f"Original program output:\n{self.expect_test_output}\n")
            logger.error(f"Optimized program output:\n{optimized_output}\n\n")
            return False
            
    def _process_output_content(self, content):
        """Remove all spaces, newline characters, and tabs for cleaner comparison."""
        if content is None or not isinstance(content, str):
           return content
        # If content is a list of lines, join it into a single string
        if isinstance(content, list):
            content = ''.join(content)
        # Remove all whitespace characters
        return re.sub(r'\s+', '', content)

    def _run_rapl(self, problem_id, optimized, input_file):
        # First clear the contents of the energy data log file
        logger.info(f"Benchmark.run: clearing content in c++.csv")
        log_file_path = f"{USER_PREFIX}/src/runtime_logs/c++.csv"
        if os.path.exists(log_file_path):
            file = open(log_file_path, "w+")
            file.close()

        #run make measure using make file
        #change current directory to benchmarks/folder to run make file
        os.chdir(f"{USER_PREFIX}/benchmark_pie/{self.program.split('.')[0]}")
        current_dir = os.getcwd()
        logger.info(f"Current directory: {current_dir}")

        try:
            measure_unoptimized = ["make", "measure", f"input={input_file}", f"problem_id={problem_id}"]
            measure_optimized = ["make", "measure_optimized", f"input={input_file}", f"problem_id={problem_id}"]
            if not optimized:
                logger.info("Make measure on original program\n")
                subprocess.run(measure_unoptimized, check=True, capture_output=True, text=True, timeout=120)
            else:
                logger.info("Make measure on optimized program\n")
                subprocess.run(measure_optimized, check=True, capture_output=True, text=True, timeout=120)
            logger.info("Benchmark.run: make measure successfully\n")
            return True
        except subprocess.TimeoutExpired:
            logger.error("Make measure timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Benchmark.run: make measure failed: {e}\n")
            return False

    def _compute_avg(self):
        benchmark_data = []
        throughput = 0  # Initialize throughput variable
        with open(f'{USER_PREFIX}/src/runtime_logs/c++.csv', mode='r', newline='') as file:
            csv_reader = csv.reader(file)
            for index, row in enumerate(csv_reader):
                if index == 5:
                    throughput = row[1]
                else:
                    benchmark_name = row[0]
                    energy = row[1]
                    latency = row[2]
                    cpu_cycles = row[3]
                    peak_memory = row[4]
                    benchmark_data.append((benchmark_name, energy, latency, cpu_cycles, peak_memory))

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
        # Convert keys to a sorted list to access the first and last elements
        keys = list(contents.keys())

        # Extract the first(original) and last(current) elements
        first_key = keys[0]
        last_key = keys[-1]

        first_value = contents[first_key]
        last_value = contents[last_key]

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

        # Prepare results in a structured format (dictionary)
        benchmark_info = {
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
        
        return benchmark_info

def get_valid_pie_programs(num_programs):
    slow_fast_pairs = []
    source_code = []

    file = open(f"{USER_PREFIX}/benchmark_pie/test.jsonl", "r")
    all_programs = []
    for line in file:
        json_line = json.loads(line)
        all_programs.append(json_line)
    file.close()
    
    all_programs.sort(key=lambda x: float(x["src_agg_runtime"]), reverse=True)

    # Select the top num_programs programs
    selected_programs = all_programs[:num_programs]
    
    # Extract program details
    for program in selected_programs:
        slow_fast_pairs.append(program)
        src_code = program["src_code"].replace("\n\n", "\n")
        source_code.append(src_code)
        print(f"src_agg_runtime: {program['src_agg_runtime']}")
    
    #Return only the program names
    valid_programs = [f"{pair['problem_id']}_{pair['src_id']}_t{pair['tgt_id'][1:]}.cpp" for pair in slow_fast_pairs]
    setup_benchmarks(valid_programs, source_code)
    #print valid_programs list and src_agg_runtime
    for i, pair in enumerate(slow_fast_pairs):
        print(f"{i}: {pair['problem_id']}_{pair['src_id']}_t{pair['tgt_id'][1:]}, {pair['src_agg_runtime']}")
    exit(0)
    return valid_programs

def setup_benchmarks(valid_programs, source_code):
    for i, program in enumerate(valid_programs):
        #Create the folder if it does not exist
        folder_path = f"{USER_PREFIX}/benchmark_pie/{program.split('.')[0]}"
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        #Create a new cpp file in the folder with the source code
        file = open(f"{folder_path}/{program}", "w")
        file.write(f"{source_code[i]}")
        file.close()
        
        #Copy the test case folder from all_test_cases/ into the program's folder
        problem_id = program.split('_')[0]
        test_case_folder_src = f"{USER_PREFIX}/benchmark_pie/merged_test_cases/{problem_id}"
        test_case_folder_dest = f"{folder_path}/test_cases"
        if not os.path.exists(test_case_folder_dest):
            shutil.copytree(test_case_folder_src, test_case_folder_dest)

        #Create parameterized Makefile for each problem id folder
        makefile_template = open(f"{USER_PREFIX}/benchmark_pie/makefile_template.mak", "r")
        makefile_content = makefile_template.read()
        makefile_content = makefile_content.replace("${FILE_NAME}", program.split('.')[0])
        makefile_content = makefile_content.replace("${PROBLEM_ID}", program)
        makefile_template.close()
        makefile_template = open(f"{folder_path}/Makefile", "w")
        makefile_template.write(makefile_content)
        makefile_template.close()
 
        #Create bash script for each problem to run through all test cases
        bash_script_template = open(f"{USER_PREFIX}/benchmark_pie/bash_script_template.sh", "r")
        bash_script_content = bash_script_template.read()
        bash_script_content = bash_script_content.replace("${EXE_NAME}", f"flamegraph_{program.split('.')[0]}.gpp_run")
        bash_script_template.close()
        bash_script = open(f"{folder_path}/run_all_test_cases.sh", "w")
        bash_script.write(bash_script_content)
        bash_script.close()
        os.chmod(f"{folder_path}/run_all_test_cases.sh", 0o755)

