from benchmark import Benchmark
from dotenv import load_dotenv
import os
import subprocess
import sys
from utils import Logger
import re
from abstract_syntax_trees.cpp_ast import CPPAST

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
logger = Logger("logs", sys.argv[2]).logger

class EnergyLanguageBenchmark(Benchmark):
    def __init__(self, program):
        self.program = program
        self.compilation_error = None
        self.energy_data = {}
        self.evaluator_feedback_data = {}
        self.expect_test_output = None
        self.original_code = None
        self.optimization_iteration = 0
        self.set_original_code()
    
    def set_original_code(self):
        source_path = f"{USER_PREFIX}/benchmark_c++/{self.program.split('.')[0]}/{self.program}"
        with open(source_path, 'r') as file:
            self.original_code = file.read()

    def get_original_code(self):
        return self.original_code
    
    def set_optimization_iteration(self, num):
        return super().set_optimization_iteration(num)
    
    def get_optimization_iteration(self):
        return super().get_optimization_iteration()
    
    def set_original_energy(self):
        logger.info("Run benchmark on the original code")

        # compile
        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_c++/{self.program.split('.')[0].split('_')[-1]}")  
        try: 
            result = subprocess.run(
                ["make", "compile"], 
                check=True,
                capture_output=True,
                text=True
            )
            self.compilation_error = result.stdout + result.stderr
            logger.info(f"Original code compile successfully.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code compile failed: {e}\n")
            return False

        self._run_rapl()

        avg_energy, avg_runtime = self._compute_avg()

        #Append results to benchmark data dict
        self.energy_data[0] = (self.original_code, round(avg_energy, 3), round(avg_runtime, 3), len(self.original_code.splitlines()))
        logger.info(f"original_energy_data: {self.energy_data[0]}")
        return True

    def pre_process(self, code):
        ast = CPPAST("cpp")
        source_code_path = f"{USER_PREFIX}/benchmark_c++/{self.program.split('.')[0]}/ast_{self.program}"
        with open(source_code_path, 'w') as file:
            file.write(code)
        return ast.create_ast(source_code_path)

    def post_process(self, code):
        # Remove code block delimiters
        code = code.replace("```cpp", "")
        code = code.replace("```", "")
        return code

    def compile(self, optimized_code):
        logger.info(f"llm_optimize: : writing optimized code to benchmark_c++/{self.program.split('.')[0]}/optimized_{self.program}")
        destination_path = f"{USER_PREFIX}/benchmark_c++/{self.program.split('.')[0]}/optimized_{self.program}"
        with open(destination_path, "w") as file:
            file.write(optimized_code)

        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_c++/{self.program.split('.')[0].split('_')[-1]}")  
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
        os.chdir(f"{USER_PREFIX}/benchmark_c++/{self.program.split('.')[0].split('_')[-1]}")

        if (self.expect_test_output == None):   
            self.expect_test_output = self._process_output_content(self._run_program(False))
        
        optimized_output = self._run_program(True)

        if not self._compare_outputs(optimized_output):
            return False
        else:
            return True
    
    def measure_energy(self, optimized_code):            
        #load the optimized code and data
        logger.info(f"Iteration {self.optimization_iteration + 1}, run benchmark on the optimized code")
        
        self._run_rapl()
    
        avg_energy, avg_runtime = self._compute_avg()
        
        #Append results to benchmark data dict
        self.energy_data[self.optimization_iteration + 1] = (optimized_code, round(avg_energy, 3), round(avg_runtime, 3), len(optimized_code.splitlines()))
        
        # Find the required benchmark elements
        self.evaluator_feedback_data = self._extract_content(self.energy_data)
        
        # Print the benchmark information
        self._print_benchmark_info(self.evaluator_feedback_data)

 
    def get_energy_data(self):
        return super().get_energy_data()
    
    def get_evaluator_feedback_data(self):
        return super().get_evaluator_feedback_data()
    
    def static_analysis(self, optimized_code):
        return super().static_analysis(optimized_code)

    def _run_program(self, optimized):
        # Run the make command and capture the output in a variable
        if not optimized:
            result = subprocess.run(["make", "run"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1')
        else:
            result = subprocess.run(["make", "run_optimized"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1')
        
        # Check for runtime errors
        if result.returncode != 0:
            return

        # Filter out the unwanted lines
        filtered_output = "\n".join(
            line for line in result.stdout.splitlines()
            if not (line.startswith("make[") or line.startswith("./"))
        )
        
        return filtered_output
    
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

    def _run_rapl(self):
        # First clear the contents of the energy data log file
        logger.info(f"Benchmark.run: clearing content in c++.csv")
        log_file_path = f"{USER_PREFIX}/src/runtime_logs/c++.csv"
        if os.path.exists(log_file_path):
            file = open(log_file_path, "w+")
            file.close()

        #run make measure using make file
        #change current directory to benchmarks/folder to run make file
        os.chdir(f"{USER_PREFIX}/benchmark_c++/{self.program.split('.')[0]}")
        current_dir = os.getcwd()
        logger.info(f"Current directory: {current_dir}")

        try:
            if (self.optimization_iteration == 0):
                subprocess.run(["make", "measure"], check=True, capture_output=True, text=True)
            else:
                subprocess.run(["make", "measure_optimized"], check=True, capture_output=True, text=True)
            logger.info("Benchmark.run: make measure successfully\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Benchmark.run: make measure failed: {e}\n")

    def _compute_avg(self):
        energy_data_file = open(f"{USER_PREFIX}/src/runtime_logs/c++.csv", "r")
        benchmark_data = []
        for line in energy_data_file:
            parts = line.split(';')
            benchmark_name = parts[0].strip()
            energy_data = [vals.strip() for vals in parts[1].split(',')]
            
            #Remove empty strings for CPU, GPU, DRAM and convert remaining numbers to floats
            energy_data = [float(num) for num in energy_data if num]
            benchmark_data.append((benchmark_name, *energy_data))

        energy_data_file.close()

        #Find average energy usage and average runtime
        avg_energy = 0
        avg_runtime = 0
        for data in benchmark_data:
            if data[1] < 0 or data[2] < 0:
                benchmark_data.remove(data)
            else:
                avg_energy += data[1]
                avg_runtime += data[2]

        avg_energy /= len(benchmark_data)
        avg_runtime /= len(benchmark_data)

        return avg_energy, avg_runtime
    
    def _extract_content(self, contents):
        # Convert keys to a sorted list to access the first and last elements
        keys = list(contents.keys())

        # print all values
        for key, (source_code, avg_energy, avg_runtime, num_of_lines) in contents.items():
            logger.info(f"key: {key}, avg_energy: {avg_energy}, avg_runtime: {avg_runtime}, num_of_lines: {num_of_lines}")

        # Extract the first(original) and last(current) elements
        first_key = keys[0]
        last_key = keys[-1]

        first_value = contents[first_key]
        last_value = contents[last_key]


        # Loop through the contents to find the key with the lowest avg_energy
        min_avg_energy = float('inf')
        min_energy_key = None
        for key, (source_code, avg_energy, avg_runtime, num_of_lines) in contents.items():
            if avg_energy < min_avg_energy:
                min_avg_energy = avg_energy
                min_energy_key = key

        min_value = contents[min_energy_key]

        # Prepare results in a structured format (dictionary)
        benchmark_info = {
            "original": {
                "source_code": first_value[0],
                "avg_energy": first_value[1],
                "avg_runtime": first_value[2],
                "num_of_lines": first_value[3]
            },
            "lowest_avg_energy": {
                "source_code": min_value[0],
                "avg_energy": min_value[1],
                "avg_runtime": min_value[2],
                "num_of_lines": min_value[3]
            },
            "current": {
                "source_code": last_value[0],
                "avg_energy": last_value[1],
                "avg_runtime": last_value[2],
                "num_of_lines": last_value[3]
            }
        }
        
        return benchmark_info
    
    def _print_benchmark_info(self, benchmark_info):
        logger.info("Original: Average Energy: {}, Average Runtime: {}".format(benchmark_info["original"]["avg_energy"], benchmark_info["original"]["avg_runtime"]))
        logger.info("Lowest Average Energy: Average Energy: {}, Average Runtime: {}".format(benchmark_info["lowest_avg_energy"]["avg_energy"], benchmark_info["lowest_avg_energy"]["avg_runtime"]))
        logger.info("Current: Average Energy: {}, Average Runtime: {}".format(benchmark_info["current"]["avg_energy"], benchmark_info["current"]["avg_runtime"]))

def get_valid_energy_language_programs():
    valid_programs = [
        "binarytrees.gpp-9.c++",
        "chameneosredux.gpp-5.c++",
        # "fannkuchredux.gpp-5.c++",
        # "fasta.gpp-5.c++",
        # "knucleotide.gpp-3.c++",
        # "mandelbrot.gpp-6.c++",
        # "nbody.gpp-8.c++",
        # "pidigits.gpp-4.c++",
        # "regexredux.gpp-3.c++",
        # "revcomp.gpp-4.c++",
        # "spectralnorm.gpp-6.c++"
    ]
    return valid_programs