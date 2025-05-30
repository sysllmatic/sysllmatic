from benchmark import Benchmark
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

load_dotenv()
USER_PREFIX = os.path.expanduser(os.getenv('USER_PREFIX'))

logger = Logger("logs", sys.argv[2]).logger

fop_root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/fop/build/fop-2.8/fop-core"
fop_src_dir = f"{fop_root_dir}/src/main/java/org/apache/fop"

spring_root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/spring/build"
spring_src_dir = f"{spring_root_dir}/src/main/java/org/springframework/samples/petclinic"

biojava_root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/biojava/build"

pmd_root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/pmd/build/pmd-core"
pmd_src_dir = f"{pmd_root_dir}/src/main/java/net/sourceforge/pmd"

graphchi_root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/graphchi/build"
graphchi_src_dir = f"{graphchi_root_dir}/src/main/java/edu/cmu/graphchi"

class DaCapoBenchmark(Benchmark):
    def __init__(self, test_method, test_class, test_namespace, test_group, unit_tests, benchmark_name, method_level, methods_list):
        # ex. test_class = PDFNumsArray, test_namespace = pdf, test_group = core, benchmark_name = fop
        self.method_name = test_method
        self.class_name = test_class
        self.namespace_name = test_namespace
        self.group_name = test_group
        self.unit_tests = unit_tests
        self.program = benchmark_name
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
        if self.program == 'fop':
            if self.namespace_name and self.namespace_name != "":
                source_path = f"{fop_src_dir}/{self.class_name}.java"
            else:
                source_path = f"{fop_src_dir}/{self.namespace_name}/{self.class_name}.java"
        elif self.program == 'spring':
            source_path = f"{spring_src_dir}/{self.namespace_name}/{self.class_name}.java"
        elif self.program == 'biojava':
            folder_name = "aa-prop" if self.group_name == "aaproperties" else self.group_name
            if self.namespace_name and self.namespace_name != "":
                source_path = f"{biojava_root_dir}/biojava-{folder_name}/src/main/java/org/biojava/nbio/{self.group_name}/{self.namespace_name}/{self.class_name}.java"
            else:
                source_path = f"{biojava_root_dir}/biojava-{folder_name}/src/main/java/org/biojava/nbio/{self.group_name}/{self.class_name}.java"
        elif self.program == 'pmd':
            if self.namespace_name and self.namespace_name != "":
                source_path = f"{pmd_src_dir}/{self.namespace_name}/{self.class_name}.java"
            else:
                source_path = f"{pmd_src_dir}/{self.class_name}.java"
        elif self.program == 'graphchi':
            if self.namespace_name and self.namespace_name != "":
                source_path = f"{graphchi_src_dir}/{self.namespace_name}/{self.class_name}.java"
            else:
                source_path = f"{graphchi_src_dir}/{self.class_name}.java"

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
        
        filtered_code = self.remove_java_comments(code)
        self.original_code = filtered_code
        
    def remove_java_comments(self, code):
        pattern = r'''
            ("(?:\\.|[^"\\])*")       |  # Group 1: Match double-quoted strings
            ('(?:\\.|[^'\\])*')       |  # Group 2: Match single-quoted strings
            (//.*?$)                  |  # Group 3: Match single-line comments
            (/\*[\s\S]*?\*/)             # Group 4: Match multi-line comments
        '''
        def replacer(match):
            # Keep string literals untouched
            if match.group(1) or match.group(2):
                return match.group(0)
            else:
                return ''  # Remove comments

        return re.sub(pattern, replacer, code, flags=re.MULTILINE | re.VERBOSE)
    
    def get_original_code(self):
        return self.original_code
    
    def set_original_energy(self):
        logger.info("Run benchmark on the original code")

        # compile
        # Needed for makefiles
        if self.program == 'fop':
            os.chdir(f"{fop_root_dir}/")
        elif self.program == 'spring':
            os.chdir(f"{spring_root_dir}/")
        elif self.program == 'biojava':
            folder_name = "aa-prop" if self.group_name == "aaproperties" else self.group_name
            os.chdir(f"{biojava_root_dir}/biojava-{folder_name}/")
        elif self.program == 'pmd':
            os.chdir(f"{pmd_root_dir}/")
        elif self.program == 'graphchi':
            os.chdir(f"{graphchi_root_dir}/")

        try:
            result = subprocess.run(["make", "compile", f"BENCHMARK={self.program}"], check=True, capture_output=True, text=True)
            logger.info("Original code compile successfully.\n")
        except subprocess.CalledProcessError as e:
            logger.error(f"Original code compile failed: {e.stdout + e.stderr}\n")
            return False
        
        #run make measure using make file for same test class
        if not self._run_rapl():
            return False

        #compute avg energy and avg runtime
        avg_energy, avg_latency, avg_cpu_cycles, avg_memory, throughput = self._compute_avg()

        self.energy_data[0] = (self.original_code, round(avg_energy, 3), round(avg_latency, 3),  avg_cpu_cycles, avg_memory, round(throughput, 3), len(self.original_code.splitlines()))        
        return True
    
    def pre_process(self, code):
        ast = JavaAST("java")
        return ast.create_ast(code)
    
    def post_process(self, code):
        code = code.replace("```java", "")
        code = code.replace("```", "")
        filtered_code = self.remove_java_comments(code)
        return filtered_code
    
    def _get_destination_path_of_source_code(self):
        if self.program == 'fop':
            if self.namespace_name and self.namespace_name != "":
                destination_path = f"{fop_src_dir}/{self.namespace_name}/{self.class_name}.java"
            else:
                destination_path = f"{fop_src_dir}/{self.class_name}.java"
        elif self.program == 'spring':
            destination_path = f"{spring_src_dir}/{self.namespace_name}/{self.class_name}.java"
        elif self.program == 'biojava':
            folder_name = "aa-prop" if self.group_name == "aaproperties" else self.group_name
            if self.namespace_name and self.namespace_name != "":
                destination_path = f"{biojava_root_dir}/biojava-{folder_name}/src/main/java/org/biojava/nbio/{self.group_name}/{self.namespace_name}/{self.class_name}.java"
            else:
                destination_path = f"{biojava_root_dir}/biojava-{folder_name}/src/main/java/org/biojava/nbio/{self.group_name}/{self.class_name}.java"
        elif self.program == 'pmd':
            if self.namespace_name and self.namespace_name != "":
                destination_path = f"{pmd_src_dir}/{self.namespace_name}/{self.class_name}.java"
            else:
                destination_path = f"{pmd_src_dir}/{self.class_name}.java"
        elif self.program == 'graphchi':

            if self.namespace_name and self.namespace_name != "":
                destination_path = f"{graphchi_src_dir}/{self.namespace_name}/{self.class_name}.java"
            else:
                destination_path = f"{graphchi_src_dir}/{self.class_name}.java"
        return destination_path

    def compile(self, optimized_code):
        #write optimized code to file
        destination_path = self._get_destination_path_of_source_code()
        
        # save optimized code to optimized_java.txt first with the format { method_body }
        # then replace the method body with the optimized code
        def extract_block_only(optimized_code: str) -> str:
            start = optimized_code.find("{")
            end = optimized_code.rfind("}")
            if start == -1 or end == -1 or start > end:
                raise ValueError("Could not locate complete block braces in the method source.")
            return optimized_code[start:end+1]

        if self.method_level:
            # remove method signature from optimized code
            try:
                optimized_code = extract_block_only(optimized_code)
            except ValueError as e:
                logger.error(f"Error extracting block from optimized code: {e}")
                return False
            with open(f"{USER_PREFIX}/src/runtime_logs/optimized_java.txt", "w") as file:
                file.write(optimized_code)
            logger.info(f"optimized_code: {optimized_code}")
            replace_successfully = replace_method_body(destination_path, self.method_name)
            if not replace_successfully:
                return False
        else:
            with open(destination_path, "w") as file:
                file.write(optimized_code)

        #compile optimized code
        if self.program == 'fop':
            os.chdir(f"{fop_root_dir}")
        elif self.program == 'spring':
            os.chdir(f"{spring_root_dir}")
        elif self.program == 'biojava':
            folder_name = "aa-prop" if self.group_name == "aaproperties" else self.group_name
            os.chdir(f"{biojava_root_dir}/biojava-{folder_name}")
        elif self.program == 'pmd':
            os.chdir(f"{fop_root_dir}")
        elif self.program == 'graphchi':
            os.chdir(f"{graphchi_root_dir}")

        try:
            result = subprocess.run(
                ["make", "compile", f"BENCHMARK={self.program}"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            logger.info(f"Optimized code compile successfully.\n")
            self.compilation_error = None
            return True
        except subprocess.CalledProcessError as e:
            self.compilation_error = e.stdout + e.stderr  # Capture both stdout and stderr
            logger.error(f"Compile optimized code failed: {e}\n")
            logger.error(f"Maven output: {self.compilation_error}")
            return False

    def get_compilation_error(self):
        return super().get_compilation_error()
    
    def run_tests(self):
        if self.program == 'fop':
            os.chdir(f"{fop_root_dir}")
        elif self.program == 'spring':
            os.chdir(f"{spring_root_dir}")
        elif self.program == 'biojava':
            folder_name = "aa-prop" if self.group_name == "aaproperties" else self.group_name
            os.chdir(f"{biojava_root_dir}/biojava-{folder_name}")
        elif self.program == 'pmd':
            os.chdir(f"{pmd_root_dir}")
        elif self.program == 'graphchi':
            os.chdir(f"{graphchi_root_dir}")

        for test in self.unit_tests:
            try:
                # Using subprocess.PIPE allows us to capture both stdout and stderr
                result = subprocess.run(
                    ["make", "test", f"BENCHMARK={self.program}", f"TEST={test}"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='latin-1'
                )
                
                # Check if the command failed (non-zero return code)
                if result.returncode != 0:
                    logger.error(f"Test {test} failed with error:\nstdout: {result.stdout}\nstderr: {result.stderr}")
                    self.runtime_error = result.stderr + result.stdout
                    return False             
            except subprocess.CalledProcessError as e:
                self.runtime_error = result.stderr + result.stdout
                logger.error(f"Test {test} execution failed: {e}\nstdout: {e.stdout}\nstderr: {e.stderr}")
                return False
        
        # If all tests pass, return True
        logger.info("All test passed successfully.")
        self.runtime_error = None
        return True
        
    def measure_energy(self, optimized_code):
         #load the optimized code and data
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
        # First clear the contents of the energy data log file
        logger.info(f"Benchmark.run: clearing content in java.csv")
        log_file_path = f"{USER_PREFIX}/src/runtime_logs/java.csv"
        if os.path.exists(log_file_path):
            file = open(log_file_path, "w")
            file.close()

        #run make measure using make file
        if self.program == 'fop':
            os.chdir(f"{fop_root_dir}")
        elif self.program == 'spring':
            os.chdir(f"{spring_root_dir}")
        elif self.program == 'biojava':
            folder_name = "aa-prop" if self.group_name == "aaproperties" else self.group_name
            os.chdir(f"{biojava_root_dir}/biojava-{folder_name}")
        elif self.program == 'pmd':
            os.chdir(f"{pmd_root_dir}")
        elif self.program == 'graphchi':
            os.chdir(f"{graphchi_root_dir}")

        try:
            result = subprocess.run(["make", "measure", f"BENCHMARK={self.program}", f"TEST={self.unit_tests[0]}"], check=True, capture_output=True, text=True, timeout=120)
            logger.info("Make measure successfully.\n")
            logger.info(result.stdout)
            return True
        except subprocess.TimeoutExpired:
            logger.error("Make measure timeout")
            return False
        except subprocess.CalledProcessError as e:
            logger.error(f"Make measure failed: {e.stderr + e.stdout}\n")
            #to get the error message, might have to return the error message from here
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
        
    def get_evaluator_feedback_data(self):
        return super().get_evaluator_feedback_data()

    def static_analysis(self, optimized_code):
        return super().static_analysis(optimized_code)
        
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
    
    def generate_flame_report(self, code):
        return self.methods_list
    
    def dynamic_analysis(self, code):
        return super().dynamic_analysis(code)
    
    def restore_last_working_optimized_code(self, code):
        destination_path = self._get_destination_path_of_source_code()
        with open(destination_path, "w") as file:
            file.write(code)

def get_valid_dacapo_classes(application_name):
    hotspots = get_hotspots("Dacapo", application_name, top_K=50)
    methods_name = [method for method, count in hotspots]

    transformed_data = []
    
    for method in methods_name:
        logger.info(f"method: {method}")
        parts = method.split('/')
        test_class, test_method = parts[-1].split('.')  # Split the last part into class and method

        if application_name == "biojava":
            test_namespace = '/'.join(parts[4:-1])
            test_group = parts[3]
            folder_name = "aa-prop" if test_group == "aaproperties" else test_group
            root_path = f"{biojava_root_dir}/biojava-{folder_name}/src/test/java/org/biojava/nbio/{test_group}"
            unit_test_class_name = f"{test_class}Test"
        elif application_name == "fop":
            test_namespace = '/'.join(parts[3:-1])
            test_group = "test_group"
            root_path = f"{fop_root_dir}/src/test/java/org/apache/fop"
            unit_test_class_name = f"{test_class}TestCase"
        elif application_name == "pmd":
            test_namespace = '/'.join(parts[3:-1])
            test_group = "test_group"
            root_path = f"{pmd_root_dir}/src/test/java/net/sourceforge/pmd"
            unit_test_class_name = f"{test_class}Test"
        elif application_name == "spring":
            test_namespace = '/'.join(parts[3:-1])
            test_group = "test_group"
            root_path = f"{spring_root_dir}/src/test/java/org/springframework/samples/petclinic"
            unit_test_class_name = f"{test_class}Tests"
        elif application_name == "graphchi":
            test_namespace = '/'.join(parts[3:-1])
            test_group = "test_group"
            root_path = f"{graphchi_root_dir}/src/test/java/edu/cmu/graphchi"
            unit_test_class_name = f"Test{test_class}"

        unit_tests = find_unit_test(root_path, unit_test_class_name, test_class)

        if len(unit_tests) == 0:
            logger.error(f"{test_class} has no unit tests!")
            continue

        transformed_data.append((test_method, test_class, test_namespace, test_group, unit_tests))

    logger.info(transformed_data)

    setup_makefile(application_name)
    return transformed_data

def setup_makefile(application_name):
    if application_name == 'fop':
        folder_path = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/{application_name}/build/fop-2.8"
        subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir()]
    elif application_name == 'spring':
        folder_path = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/{application_name}"
        subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir() and f.name == 'build']
    elif application_name == 'biojava':
        folder_path = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/{application_name}/build"
        subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir() and f.name.startswith('biojava-')]
    elif application_name == 'pmd':
        folder_path = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/{application_name}/build"
        subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir() and f.name.startswith('pmd-')]
    elif application_name == 'graphchi':
        folder_path = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/{application_name}"
        subfolders = [f.path for f in os.scandir(folder_path) if f.is_dir() and f.name == 'build']

    for subfolder in subfolders:
        logger.info(subfolder)
        makefile_template = open(f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/makefile_template.mak", "r")
        makefile_content = makefile_template.read()
        makefile_template.close()
        makefile_template = open(f"{subfolder}/Makefile", "w")
        makefile_template.write(makefile_content)
        makefile_template.close()

#just to test the code
def main():


    # ff = DaCapoBenchmark('PDFNumsArray', 'pdf', 'core', 'fop')
    # ff.set_original_energy()
    # status = ff.static_analysis(ff.original_code)
    # print(f"Status: {status}")
    # ff = DaCapoBenchmark('OwnerController', 'owner', 'none', 'spring')
    # ff.set_original_energy()

    # setup_makefile('spring')
    # ff.static_analysis(ff.original_code)

    # ff = DaCapoBenchmark('ChromosomeSequence', 'sequence', 'core', 'biojava')
    # setup_makefile('biojava')
    # ff.set_original_energy()
    # status = ff.static_analysis(ff.original_code)

    ff = DaCapoBenchmark('DocumentFile', 'document', 'core', 'pmd')
    setup_makefile('pmd')
    ff.set_original_energy()
    status = ff.static_analysis(ff.original_code)
    #[INFO] Running net.sourceforge.pmd.document.DocumentFileTest


if __name__ == '__main__':
    main()