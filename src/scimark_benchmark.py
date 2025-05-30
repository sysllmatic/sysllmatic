from benchmark import Benchmark
from dotenv import load_dotenv
import os
import subprocess
import sys
from utils import Logger
import re
from abstract_syntax_trees.java_ast import JavaAST
import csv
import math
from flamegraph_profiling import get_hotspots
from java_method_profiling import replace_method_body, get_method_source_code, compile_java_project

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
logger = Logger("logs", sys.argv[2]).logger

class SciMarkBenchmark(Benchmark):
    def __init__(self, program, method_name, method_level):
        self.program = program
        self.compilation_error = None
        self.runtime_error = None
        self.energy_data = {}
        self.evaluator_feedback_data = {}
        self.expect_test_output = None
        self.original_code = None
        self.optimization_iteration = 0
        self.method_level = method_level
        self.method_name = method_name
        self.set_original_code()
    
    # Copy the original code to the optimized code (because we only measure the optimized code)
    def set_original_code(self):
        command = f"cp {USER_PREFIX}/benchmark_scimark/{self.program}/{self.program}OptimizedOriginal {USER_PREFIX}/benchmark_scimark/{self.program}/{self.program}Optimized.java"
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        source_path = f"{USER_PREFIX}/benchmark_scimark/{self.program}/{self.program}Optimized.java"
        
        if self.method_level:
            compile_java_project()
            self.original_code = get_method_source_code(source_path, self.method_name)
        else:
            with open(source_path, "r") as file:
                self.original_code = file.read()
        
    def get_original_code(self):
        return self.original_code

    def set_original_energy(self):
        logger.info("Run benchmark on the original code")

        # compile
        # Needed for makefiles
        os.chdir(f"{USER_PREFIX}/benchmark_scimark/{self.program}")  
        try: 
            compile_result = subprocess.run(
                ["make", "compile"], 
                check=True,
                capture_output=True,
                text=True,
                timeout=120
            )
            self.compilation_error = compile_result.stdout + compile_result.stderr
            logger.info(f"Original code compile successfully.\n")
        except subprocess.TimeoutExpired:
            logger.error("Make compile timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code compile failed: {e}\n")
            return False
        
        # get mflops
        try:
            measure_result = subprocess.run(["make", "measure_mflops"], check=True, capture_output=True, text=True, timeout=120)
            logger.info(f"Original code mlops measure successfully.\n")
        except subprocess.TimeoutExpired:
            logger.error("Make measure_mflops timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code mflops measure failed: {e}\n")
            return False

        # Filter out the unwanted lines
        mflops = "\n".join(
            line for line in measure_result.stdout.splitlines()
            if not (line.startswith("make[") or line.startswith("./"))
        )
        
        mflops = mflops.split("make")[0]

        self._run_rapl(optimized=False)

        avg_energy, avg_latency, avg_cpu_cycles, avg_memory, throughput = self._compute_avg()

        #Append results to benchmark data dict
        self.energy_data[0] = (self.original_code, round(avg_energy, 3), round(avg_latency, 3),  avg_cpu_cycles, round(avg_memory, 3), round(throughput, 3), float(mflops), len(self.original_code.splitlines()))
        return True

    def pre_process(self, code):
        ast = JavaAST("Java")
        return ast.create_ast(code)

    def post_process(self, code):
       # Extract code inside ```java ... ```
        match = re.search(r'```java\s*(.*?)```', code, flags=re.DOTALL)
        if match:
            code = match.group(1)
        code = re.sub(r'//.*?$|/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
        code = re.sub(r'\bclass\s+\w+', f'class {self.program}Optimized', code)  # Change class name dynamically
        if not code.strip().startswith("package jnt.scimark2;"):
            code = "package jnt.scimark2;\n" + code
        return code
        
    def compile(self, optimized_code):
        logger.info(f"llm_optimize: : writing optimized code to benchmark/{self.program}/{self.program}Optimized.java")
        destination_path = f"{USER_PREFIX}/benchmark_scimark/{self.program}/{self.program}Optimized.java"
        
        if self.method_level:
            with open(f"{USER_PREFIX}/src/runtime_logs/optimized_java.txt", "w") as file:
                file.write(optimized_code)
            logger.info(f"optimized_code: {optimized_code}")
            replace_successfully = replace_method_body(destination_path, self.method_name)
            if not replace_successfully:
                self.compilation_error = "Please provide Java code in the original method format"
                return False
        else:
            with open(destination_path, "w") as file:
                file.write(optimized_code)

        os.chdir(f"{USER_PREFIX}/benchmark_scimark/{self.program}")
        try: 
            result = subprocess.run(
                ["make", "compile"], 
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Optimized code compile successfully.\n")
        except subprocess.CalledProcessError as e:
            self.compilation_error = e.stderr
            logger.error(f"Optimized code compile failed: {self.compilation_error}\n")
            return False
        
        self.compilation_error = None
        return True

    def run_tests(self):
        os.chdir(f"{USER_PREFIX}/benchmark_scimark/{self.program}")

        if (self.expect_test_output == None):   
            self.expect_test_output = self._process_output_content(self._run_program(False))
        
        optimized_output = self._run_program(True)

        if optimized_output == None:
            logger.error("Runtime error")
            return False

        if not self._compare_outputs(optimized_output):
            return False
        else:
            self.runtime_error = None
            return True

    def measure_energy(self, optimized_code):            
        #load the optimized code and data
        logger.info(f"Iteration {self.optimization_iteration + 1}, run benchmark on the optimized code")

        # get mflops
        try:
            measure_result = subprocess.run(["make", "measure_mflops_optimized"], check=True, capture_output=True, text=True, timeout=180)
            logger.info(f"Optimized code mlops measure successfully.\n")
            # Filter out the unwanted lines
            mflops = "\n".join(
                line for line in measure_result.stdout.splitlines()
                if not (line.startswith("make[") or line.startswith("./"))
            )
            mflops = mflops.split("make")[0]
        except subprocess.CalledProcessError as e:
            logger.error(f"Optimized code mflops measure failed: {e}\n")
            mflops = 0
        except subprocess.TimeoutExpired:
            logger.error("Make measure_mflops_optimized timeout")
            mflops = 0
        
        self._run_rapl(optimized=True)
            
        #Append results to benchmark data dict
        avg_energy, avg_latency, avg_cpu_cycles, avg_memory, throughput = self._compute_avg()
        original_data = self.energy_data[0]
        energy_change = original_data[1] / avg_energy
        speedup = original_data[2] / avg_latency
        cpu_change = original_data[3] / avg_cpu_cycles
        memory_change = original_data[4] / avg_memory
        throughput_change = throughput / original_data[5]
        mflops_change = float(mflops) / float(original_data[6])

        self.energy_data[self.optimization_iteration + 1] = (optimized_code, round(energy_change, 3), round(speedup, 3), cpu_change, memory_change, throughput_change, mflops_change, len(optimized_code.splitlines()))
        
        # Find the required benchmark elements
        self.evaluator_feedback_data = self._extract_content(self.energy_data)

    def get_energy_data(self):
        return super().get_energy_data()
    
    def get_evaluator_feedback_data(self):
        return super().get_evaluator_feedback_data()
    
    def static_analysis(self, optimized_code):
        return super().static_analysis(optimized_code)

    def _run_program(self, optimized):
        try:
            if not optimized:
                result = subprocess.run(["make", "run"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1', timeout=120)
            else:
                result = subprocess.run(["make", "run_optimized"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='latin-1', timeout=120)
        except subprocess.TimeoutExpired:
            logger.error("Timeout expired while running the make command")
            return None
        
        logger.info(f"_run_program result: {result}")
       
        # Check for runtime errors
        if result.returncode is not None and result.returncode != 0:
            self.runtime_error = result.stderr
            logger.error(f"Runtime error: {result.stderr}")
            return None

        # Filter out the unwanted lines
        filtered_output = "\n".join(
            line for line in result.stdout.splitlines()
            if not (line.startswith("make[") or line.startswith("./"))
        )

        return filtered_output.split("make")[0]

    def _process_output_content(self, content):
        """Remove all spaces, newline characters, and tabs for cleaner comparison."""
        if content is None or not isinstance(content, str):
           return content
        # If content is a list of lines, join it into a single string
        if isinstance(content, list):
            content = ''.join(content)
        # Remove all whitespace characters
        return re.sub(r'\s+', '', content)

    def _compare_outputs(self, optimized_output):
        optimized_output = self._process_output_content(optimized_output)

        try:
            optimized_output_float = float(optimized_output)
        except ValueError:
            logger.error(f"Cannot convert optimized output to float: {optimized_output}")
            return False
        
        expect_test_output_float = float(self.expect_test_output)
        
        if self.program == "FFT":
            EPS = 1.0e-10
        elif self.program == "LU":
            EPS = 1.0e-12
        elif self.program == "MonteCarlo":
            EPS = math.pi
        elif self.program == "SOR":
            EPS = 0.003
        elif self.program == "SparseCompRow":
            EPS = 1.0e-10
        
        if self.program == "MonteCarlo":
            if abs(optimized_output_float - EPS) <= 0.05:
                logger.info(f"Output is within EPS threshold. Original output: {expect_test_output_float}, Optimized output: {optimized_output_float}")
                return True
            else:
                logger.error(f"Original program output: {self.expect_test_output}, Optimized program output: {optimized_output}")
                self.runtime_error = f"Original program output: {self.expect_test_output}, Optimized program output: {optimized_output}"
                return False
        elif abs(optimized_output_float) <= EPS:
            logger.info(f"Output is within EPS threshold. Original output: {expect_test_output_float}, Optimized output: {optimized_output_float}")
            return True
        else:
            logger.error(f"Original program output: {self.expect_test_output}, Optimized program output: {optimized_output}")
            self.runtime_error = f"Original program output: {self.expect_test_output}, Optimized program output: {optimized_output}"
            return False

    def _run_rapl(self, optimized):
        # First clear the contents of the energy data log file
        logger.info(f"Benchmark.run: clearing content in java.csv")
        log_file_path = f"{USER_PREFIX}/src/runtime_logs/java.csv"
        if os.path.exists(log_file_path):
            file = open(log_file_path, "w+")
            file.close()

        #run make measure using make file
        #change current directory to benchmarks/folder to run make file
        os.chdir(f"{USER_PREFIX}/benchmark_scimark/{self.program}")

        try:
            measure_unoptimized = ["make", "measure"]
            measure_optimized = ["make", "measure_optimized"]
            if not optimized:
                logger.info("Make measure on original program\n")
                subprocess.run(measure_unoptimized, check=True, capture_output=True, text=True, timeout=180)
            else:
                logger.info("Make measure on optimized program\n")
                subprocess.run(measure_optimized, check=True, capture_output=True, text=True, timeout=180)
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
        with open(f'{USER_PREFIX}/src/runtime_logs/java.csv', mode='r', newline='') as file:
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
                    
        if benchmark_data == []:
            logger.error("No data in the benchmark data")
            return None, None, None, None, None

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

        logger.info(f"key 0, avg_energy: {first_value[1]}, avg_runtime: {first_value[2]}, avg_cpu_cycles: {first_value[3]}, avg_memory: {first_value[4]}, throughput: {first_value[5]}, mflops: {first_value[6]}, num_of_lines: {first_value[7]}")
        for key, (source_code, avg_energy, avg_runtime, avg_cpu_cycles, avg_memory, throughput, mflops, num_of_lines) in list(contents.items())[1:]:
            logger.info(f"key: {key}, avg_energy_improvement: {avg_energy}, avg_speedup: {avg_runtime}, avg_cpu_improvement: {avg_cpu_cycles}, avg_memory_improvement: {avg_memory}, avg_throughput_improvement: {throughput}, average_mflops_improvement: {mflops}, num_of_lines: {num_of_lines}")

        # Loop through the contents to find the key with the lowest avg_energy
        max_avg_speedup = float('-inf')
        max_avg_speedup_key = None
        for key, (source_code, avg_energy, avg_speedup, avg_cpu_cycles, avg_memory, throughput, mflops, num_of_lines) in list(contents.items())[1:]:
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
                "mflops": first_value[6],
                "num_of_lines": first_value[7]
            },
            "max_avg_speedup": {
                "source_code": max_value[0],
                "avg_energy_improvement": max_value[1],
                "avg_speedup": max_value[2],
                "avg_cpu_improvement": max_value[3],
                "avg_memory_improvement": max_value[4],
                "avg_throughput_improvement": max_value[5],
                "mflops_improvement": max_value[6],
                "num_of_lines": max_value[7]
            },
            "current": {
                "source_code": last_value[0],
                "avg_energy_improvement": last_value[1],
                "avg_speedup": last_value[2],
                "avg_cpu_improvement": last_value[3],
                "avg_memory_improvement": last_value[4],
                "avg_throughput_improvement": last_value[5],
                "mflops_improvement": last_value[6],
                "num_of_lines": last_value[7]
            }
        }
        
        return benchmark_info

    def generate_flame_report(self, code):
        """
        Run two async-profiler sessions (alloc & cpu) on the SciMark class
        """
        # cd into the per-benchmark folder
        os.chdir(f"{USER_PREFIX}/benchmark_scimark/{self.program}")
        
        code = re.sub(r'\bclass\s+\w+', f'class {self.program}Flamegraph', code)  # Change class name dynamically
        code = re.sub(rf'\bpublic\s+{self.program}Optimized\b', f'public {self.program}Flamegraph', code)  # Update public class declaration

        # save code to file
        with open(f"{self.program}Flamegraph.java", "w") as f:
            f.write(code)
        
        main_class = f"jnt.scimark2.{self.program}Flamegraph"
        
        # compile the class
        try: 
            result = subprocess.run(
                ["make", "compile"], 
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Flamegraph code compile successfully.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Flamegraph code compile failed: {e.stderr}\n")
            return

        # path to the async-profiler native library
        prof_lib = os.path.join(
            USER_PREFIX, "async-profiler", "build", "lib", "libasyncProfiler.so"
        )

        # 1 allocation profile
        alloc_cmd = [
            "java",
            "-cp", ".",     
            f"-agentpath:{prof_lib}=start,event=alloc,flat=10,file=alloc_profile.txt",
            main_class,
        ]
        logger.info(f"Running alloc profile: {' '.join(alloc_cmd)}")
        try:
            subprocess.run(
                alloc_cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Allocation profile failed:\n{e.stderr}")
            raise
        
        # 2) CPU profile
        cpu_cmd = [
            "java",
            "-cp", ".",
            f"-agentpath:{prof_lib}=start,event=cpu,flat=10,file=cpu_profile.txt",
            main_class,
        ]
        logger.info(f"Running cpu profile: {' '.join(cpu_cmd)}")
        try:
            subprocess.run(
                cpu_cmd,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=300,
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"CPU profile failed:\n{e.stderr}")
            raise
        
        # clean up Flamegraph file
        os.remove(f"{self.program}Flamegraph.java")

        # read them back
        with open("alloc_profile.txt", "r") as f:
            alloc_profile = f.read()
        with open("cpu_profile.txt", "r") as f:
            cpu_profile = f.read()

        # stash into our feedback map
        self.evaluator_feedback_data["alloc_profile"] = alloc_profile
        self.evaluator_feedback_data["cpu_profile"] = cpu_profile

        profile = {
            "alloc_profile": alloc_profile,
            "cpu_profile": cpu_profile
        }
        
        return profile["cpu_profile"]

    def dynamic_analysis(self, code):
        logger.info(f"Generating async-profiler profiles")
        return super().dynamic_analysis(code)

def get_valid_scimark_programs():
    valid_programs = [
        "FFT",
        "LU",
        "MonteCarlo",
        "SOR",
        "SparseCompRow"
    ]
    
    transformed_data = []
    
    for program in valid_programs:
        # compile
        os.chdir(f"{USER_PREFIX}/benchmark_scimark/{program}")
        
        command = f"cp {USER_PREFIX}/benchmark_scimark/{program}/{program}OptimizedOriginal {USER_PREFIX}/benchmark_scimark/{program}/{program}Optimized.java"
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
        try: 
            compile_result = subprocess.run(
                ["make", "compile"], 
                check=True,
                capture_output=True,
                text=True,
                timeout=120
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code compile failed: {e}\n")
            continue
        
        hotspot = get_hotspots("SciMark", program, 1)
        method_name = hotspot[0][0]
        parts = method_name.split('/')
        test_class, test_method = parts[-1].split('.')  # Split the last part into class and method
        logger.info(f"Method name: {test_method}")
        
        transformed_data.append((program, test_method))
    logger.info(f"Valid programs and method: {transformed_data}")   
    return transformed_data