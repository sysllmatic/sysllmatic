import os
from dotenv import load_dotenv
import json
import sys
from agent import LLMAgent
from utils import Logger
import sys
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel
import re
import subprocess
import csv
import math

logger = Logger("logs", "default").logger

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
openai_key = os.getenv('API_KEY')
genai_api_key = os.getenv('GenAI_API_KEY')
DATASET_DIR = os.path.join(USER_PREFIX, "src/baseline/profcodegen/scimark/testcode.json")
RAPL_TOOL = os.path.join(USER_PREFIX, "RAPL/main")
RUNTIME_LOG = os.path.join(USER_PREFIX, "src/runtime_logs/java.csv")
env = Environment(loader=FileSystemLoader(f"{USER_PREFIX}/src/baseline/profcodegen/scimark/prompt"))

llm = LLMAgent(openai_api_key=openai_key, genai_api_key=genai_api_key, model="gpt-4o", system_message="")

def post_process(program, code):
    # Extract code inside ```java ... ```
    match = re.search(r'```java\s*(.*?)```', code, flags=re.DOTALL)
    if match:
        code = match.group(1)
    code = re.sub(r'//.*?$|/\*.*?\*/', '', code, flags=re.DOTALL | re.MULTILINE)
    code = re.sub(r'\bclass\s+\w+', f'class {program}Optimized', code)  # Change class name dynamically
    if not code.strip().startswith("package jnt.scimark2;"):
        code = "package jnt.scimark2;\n" + code
    return code

def compile(program, optimized_code):
    destination_path = f"{USER_PREFIX}/benchmark_scimark/{program}/{program}Optimized.java"
    with open(destination_path, "w") as file:
        file.write(optimized_code)

    os.chdir(f"{USER_PREFIX}/benchmark_scimark/{program}")
    try: 
        result = subprocess.run(
            ["make", "compile"], 
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Code compile successfully.\n")
    except subprocess.CalledProcessError as e:
        logger.error(f"Code compile failed {e.stderr}\n")
        return False
    
    return True

def process_output_content(content):
    """Remove all spaces, newline characters, and tabs for cleaner comparison."""
    if content is None or not isinstance(content, str):
        return content
    # If content is a list of lines, join it into a single string
    if isinstance(content, list):
        content = ''.join(content)
    # Remove all whitespace characters
    return re.sub(r'\s+', '', content)

def compare_outputs(program, expect_test_output, optimized_output):
    optimized_output = process_output_content(optimized_output)

    try:
        optimized_output_float = float(optimized_output)
    except ValueError:
        logger.error(f"Cannot convert optimized output to float: {optimized_output}")
        return False
    
    expect_test_output_float = float(expect_test_output)
    
    if program == "FFT":
        EPS = 1.0e-10
    elif program == "LU":
        EPS = 1.0e-12
    elif program == "MonteCarlo":
        EPS = math.pi
    elif program == "SOR":
        EPS = 0.003
    elif program == "SparseCompRow":
        EPS = 1.0e-10
    
    if program == "MonteCarlo":
        if abs(optimized_output_float - EPS) <= 0.05:
            logger.info(f"Output is within EPS threshold. Original output: {expect_test_output_float}, Optimized output: {optimized_output_float}")
            return True
        else:
            logger.error(f"Original program output: {expect_test_output}, Optimized program output: {optimized_output}")
            return False
    elif abs(optimized_output_float) <= EPS:
        logger.info(f"Output is within EPS threshold. Original output: {expect_test_output_float}, Optimized output: {optimized_output_float}")
        return True
    else:
        logger.error(f"Original program output: {expect_test_output}, Optimized program output: {optimized_output}")
        return False
    
def run_program(optimized):
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
        logger.error(f"Runtime error: {result.stderr}")
        return None

    # Filter out the unwanted lines
    filtered_output = "\n".join(
        line for line in result.stdout.splitlines()
        if not (line.startswith("make[") or line.startswith("./"))
    )

    return filtered_output.split("make")[0]

def run_tests(program: str) -> bool:
    os.chdir(f"{USER_PREFIX}/benchmark_scimark/{program}")

    expect_test_output = process_output_content(run_program(False))
    
    optimized_output = run_program(True)

    if optimized_output == None:
        logger.error("Runtime error")
        return False

    if not compare_outputs(program, expect_test_output, optimized_output):
        return False
    else:
        return True

def correctness_check(program: str, function_code: str) -> bool:
    # Compile and run the code
    if not compile(program, function_code):
        return False
    # Run the test code
    if not run_tests(program):
        return False
    
    return True

def measure_performance(program: str, optimized: bool):
    logger.info(f"Benchmark.run: clearing content in java.csv")
    log_file_path = f"{USER_PREFIX}/src/runtime_logs/java.csv"
    if os.path.exists(log_file_path):
        file = open(log_file_path, "w+")
        file.close()
        
    #run make measure using make file
    #change current directory to benchmarks/folder to run make file
    os.chdir(f"{USER_PREFIX}/benchmark_scimark/{program}")

    try:
        cmd = ["make", "measure_optimized" if optimized else "measure"]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        return extract_metrics(optimized)
    except subprocess.CalledProcessError as e:
        logger.error(f"Make measure failed: {e.stderr}")
        return 0

def extract_metrics(optimized):
    values = []
    with open(RUNTIME_LOG, mode='r') as file:
        reader = csv.reader(file)
        for index, row in enumerate(reader):
            try:
                energy = float(row[1])
                latency = float(row[2])
                cpu_cycles = float(row[3])
                peak_memory = float(row[4])
                values.append((energy, latency, cpu_cycles, peak_memory))
            except (IndexError, ValueError):
                continue

    if not values:
        return -1
    avg_energy = sum(x[0] for x in values) / len(values)
    avg_latency = sum(x[1] for x in values) / len(values)
    avg_cpu_cycles = sum(x[2] for x in values) / len(values)
    avg_peak_memory = sum(x[3] for x in values) / len(values)
    logger.info(f"Average energy: {avg_energy}")
    logger.info(f"Average CPU cycles: {avg_cpu_cycles}")
    logger.info(f"Average peak memory: {avg_peak_memory}")
    logger.info(f"Average latency: {avg_latency}")
    
     # get mflops
    try:
        cmd = ["make", "measure_mflops_optimized" if optimized else "measure_mflops"]
        measure_result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=180)
        logger.info(f"Mlops measure successfully.\n")
        # Filter out the unwanted lines
        mflops = "\n".join(
            line for line in measure_result.stdout.splitlines()
            if not (line.startswith("make[") or line.startswith("./"))
        )
        mflops = mflops.split("make")[0]
    except subprocess.CalledProcessError as e:
        logger.error(f"Mflops measure failed: {e}\n")
        mflops = 0
    except subprocess.TimeoutExpired:
        logger.error("Mflops measure timeout")
        mflops = 0
        
    logger.info(f"Mflops: {mflops}")
            
    return avg_energy, avg_latency, avg_cpu_cycles, avg_peak_memory, float(mflops)

def round_1(function_code: str):
    template = env.get_template("round_1.jinja")
    data = {
        "solution": function_code
    }
    prompt = template.render(data)
        
    logger.info(f"llm_optimize: Round 1 LLM Optimizing ....")
    logger.info(f"Round 1 prompt: {prompt}")
    
    class Optimization(BaseModel):
        code: str
    
    llm.add_to_memory("user", prompt)
    llm.generate_response(Optimization)
    response = llm.get_last_msg()
    
    try:
        content_dict = json.loads(response["content"])
        code = content_dict["code"]
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return
    
    if code == "":
        logger.error("Error in llm completion")
        return None
    
    return code

def round_2(testcase: str):
    template = env.get_template("round_2.jinja")
    data = {
        "testcase": testcase
    }
    prompt = template.render(data)
        
    logger.info(f"llm_optimize: Round 2 LLM Optimizing ....")
    logger.info(f"Round 2 prompt: {prompt}")
    
    class Optimization(BaseModel):
        code: str
    
    llm.add_to_memory("user", prompt)
    llm.generate_response(Optimization)
    response = llm.get_last_msg()
    
    try:
        content_dict = json.loads(response["content"])
        code = content_dict["code"]
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e}")
        return
    
    if code == "":
        logger.error("Error in llm completion")
        return None
    
    return code

def main():
    logger.info(f"Running PerfCodeGen on Scimark.")
    results = []
    programs = [
        "FFT",
        "LU",
        "MonteCarlo",
        "SOR",
        "SparseCompRow"
    ]
    
    with open(DATASET_DIR, "r") as f:
        dataset = json.load(f)
    
    for program in programs:
        logger.info(f"Processing: {program}")
        llm.clear_memory()
        
        # round 1 optimization
        command = f"cp {USER_PREFIX}/benchmark_scimark/{program}/{program}OptimizedOriginal {USER_PREFIX}/benchmark_scimark/{program}/{program}Optimized.java"
        subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        source_path = f"{USER_PREFIX}/benchmark_scimark/{program}/{program}Optimized.java"
        
        with open(source_path, "r") as file:
            code = file.read()
        
        logger.info(f"Optimizing {program} round 1")
        round_1_optimized_code = round_1(code)
        if round_1_optimized_code is None:
            logger.info(f"Error in round 1 llm completion for {program}")
            continue
        
        round_1_optimized_code = post_process(program, round_1_optimized_code)
        
        # correctness_check
        is_correct = correctness_check(program, round_1_optimized_code)
        
        if is_correct:
            logger.info(f"Correctness check passed for {program}")
        else:
            logger.info(f"Correctness check failed for {program}")
            results.append((program, -1))
            continue
        
        # exection
        logger.info("Getting most expensive unit test")
        most_expensive_unit_test = dataset[program]
        
        # round 2 optimization
        logger.info(f"Optimizing {program} round 2")
        round_2_optimized_code = round_2(most_expensive_unit_test)
        if round_2_optimized_code is None:
            logger.info(f"Error in round 2 llm completion for {program}")
            continue
        
        round_2_optimized_code = post_process(program, round_2_optimized_code)
        
        # correctness_check
        is_correct = correctness_check(program, round_2_optimized_code)
        
        final_code = round_2_optimized_code
        if is_correct:
            logger.info(f"Correctness check passed for {program}")
        else:
            logger.info(f"Correctness check failed for {program}")
            final_code = round_1_optimized_code
        
        # measure final performance
        can_compile = compile(program, final_code)
        if not can_compile:
            logger.error(f"Compilation failed for final code")
            results.append((program, -1))
            continue
        
        # measure final performance
        optimized_energy, optimized_latency, optimized_cpu_cycles, optimized_memory, optimized_mflops = measure_performance(program, optimized=True)
        original_energy, original_latency, original_cpu_cycles, original_memory, original_mflops = measure_performance(program, optimized=False)
        results.append((program, original_energy / optimized_energy, original_latency / optimized_latency, original_cpu_cycles / optimized_cpu_cycles, original_memory / optimized_memory, optimized_mflops / original_mflops))
        
    # Save results to CSV
    with open(f"{USER_PREFIX}/profcodegen_results.csv", "w") as f:
        writer = csv.writer(f)
        writer.writerow(["Id", "Energy", "Latency", "CPU Cycles", "Peak Memory", "Mflops"])
        writer.writerows(results)
        
    # # Compute average improvements across all entries
    # if results:
    #     total = len(results)
    #     correct = sum(1 for _, s in results if s != -1)
    #     optimized = sum(1 for _, s in results if s >= 1.1)
    #     speedups = [max(1, s) for _, s in results if s != -1]
    #     avg_speedup = round(sum(speedups) / len(speedups), 3) if speedups else 0

    #     percent_correct = round(100 * correct / total, 2)
    #     percent_optimized = round(100 * optimized / total, 2)

    #     logger.info(f"% correct: {percent_correct}%")
    #     logger.info(f"% optimized: {percent_optimized}%")
    #     logger.info(f"Average speedup (correct only, min 1x): {avg_speedup}x")
    # else:
    #     logger.error("No valid results to compute statistics.")
        
if __name__ == "__main__":
    main()