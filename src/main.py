from dotenv import load_dotenv
import json
import os
import sys
from utils import Logger
import argparse
from agent import LLMAgent
from status import Status
from llm.generator_llm import llm_optimize, handle_error
from llm.evaluator_llm import evaluator_llm
from llm.advisor_llm import filter_patterns
from scimark_benchmark import get_valid_scimark_programs, SciMarkBenchmark
from dacapo_benchmark import get_valid_dacapo_classes, DaCapoBenchmark
from humaneval_benchmark import get_valid_humaneval_programs, HumanEvalBenchmark
from collections import defaultdict
import glob
import time

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
openai_key = os.getenv('API_KEY')
genai_api_key = os.getenv('GenAI_API_KEY')
logger = Logger("logs", sys.argv[2]).logger

def parse_arguments():
    parser = argparse.ArgumentParser(description="LLM-Code-Optimization")
    parser.add_argument("--benchmark", type=str, default="HumanEval", choices=["SciMark", "Dacapobench", "HumanEval"], help="dataset used for experiment")
    parser.add_argument("--llm", type=str, default="gpt-4.1", choices=["gpt-4.1", "gpt-4o", "gpt-4o-mini", "o3-mini", "deepseek-r1:32b","deepseek-r1:70b", "qwen2.5:72b", "llama3.3:70b", "codellama:latest"], help="llm used for inference")
    parser.add_argument("--self_optimization_step", type=int, default=2, help="number of LLM optimization step")
    parser.add_argument("--num_programs", type=int, default=5, help="For HumanEval only, number of programs from the benchmark to test")
    parser.add_argument("--application_name", type=str, default="fop", choices=["biojava", "fop", "graphchi", "pmd"], help="For Dacapobench only, name of the application from the benchmark to test")
    parser.add_argument("--method_level", type=bool, default=False, help="Flag to indicate if method level optimization is used")

    args = parser.parse_args()
    return args

def get_valid_programs(benchmark, num_programs, application_name, method_level):
    if (benchmark == "HumanEval"):
        return get_valid_humaneval_programs(num_programs)
    elif (benchmark == "SciMark"):
        # cleanup
        txt_files = glob.glob(f"{USER_PREFIX}/benchmark_scimark/*/*.txt")
        flamegraph_files = glob.glob(f"{USER_PREFIX}/benchmark_scimark/*/*Flamegraph.java")
        all_files_to_remove = txt_files + flamegraph_files
        for file_path in all_files_to_remove:
            try:
                os.remove(file_path)
            except Exception as e:
                logger.error(f"Error removing {file_path}: {e}")
        return get_valid_scimark_programs()
    elif (benchmark == "Dacapobench"):
        programs = get_valid_dacapo_classes(application_name)
        if not method_level:
            class_methods_map = {}
            for prog in programs:
                test_class = prog[1]  # prog[1] is the test_class
                class_methods_map.setdefault(test_class, set()).add(prog[0])
        
            unique_classes = set()
            filtered_programs = []
            for prog in programs:
                if prog[1] not in unique_classes:  # prog[1] is test_class
                    unique_classes.add(prog[1])
                    prog_list = list(prog)
                    prog_list.append(class_methods_map.get(prog[1]))  # prog[0] is test_method
                    filtered_programs.append(tuple(prog_list))
                    logger.info(f"filtered program: {prog_list}")
            programs = filtered_programs
        return programs
    else:
        return []
    
def write_result(energy_data, program, evaluator_feedback_data, results_dir):
    dict_str = json.dumps(energy_data, indent=4)
    if not os.path.exists(results_dir):
        os.makedirs(results_dir)
    with open(f"{results_dir}/{program}.txt", "w+") as file:
        file.write(str(dict_str))

    avg_energy_improvement = evaluator_feedback_data["max_avg_speedup"]["avg_energy_improvement"]
    avg_speedup = evaluator_feedback_data["max_avg_speedup"]["avg_speedup"]
    avg_cpu_improvement = evaluator_feedback_data["max_avg_speedup"]["avg_cpu_improvement"]
    avg_memory_improvement = evaluator_feedback_data["max_avg_speedup"]["avg_memory_improvement"]
    avg_throughput_improvement = evaluator_feedback_data["max_avg_speedup"]["avg_throughput_improvement"]
    if "mflops_improvement" in evaluator_feedback_data["max_avg_speedup"]:
        avg_mflops_improvement = evaluator_feedback_data["max_avg_speedup"]["mflops_improvement"]
    lowest_loc = evaluator_feedback_data["max_avg_speedup"]["num_of_lines"]
    original_loc = evaluator_feedback_data["original"]["num_of_lines"]

    return {
        "energy_improvement": avg_energy_improvement,
        "runtime_improvement": avg_speedup,
        "cpu_cycles_improvement": avg_cpu_improvement,
        "peak_memory_improvement": avg_memory_improvement,
        "throughput_improvement": avg_throughput_improvement,
        "mflops_improvement": avg_mflops_improvement if "mflops_improvement" in evaluator_feedback_data["max_avg_speedup"] else None,
        "loc_improvement": round(original_loc / lowest_loc, 3),
    }

def master_script(benchmark, num_programs, application_name, model, self_optimization_step, method_level):
    #create LLM agent
    generator = LLMAgent(openai_api_key=openai_key, model=model, system_message="You are a code expert. Think through the code optimizations strategies possible step by step.")
    evaluator = LLMAgent(openai_api_key=openai_key, model=model, system_message="You are a code expert. Think through the code optimizations strategies possible step by step.")
    advisor = LLMAgent(openai_api_key=openai_key, model=model, system_message="You are an expert in software optimization patterns. You will be given a list of optimization patterns and source code. Your task is to analyze the source code and patterns to determine which are most suitable for improving its overall efficiency.")

    results = {}
    
    results_dir = f"{USER_PREFIX}/results/{benchmark}"
        
    for program in get_valid_programs(benchmark, num_programs, application_name, method_level):
        if benchmark == "HumanEval":
            id = program[0]
            function_code = program[1]
            stress_test = program[2]
            test_code = program[3]
            entry_point = program[4]
            benchmark_obj = HumanEvalBenchmark(id, function_code, stress_test, test_code, entry_point)
        elif benchmark == "SciMark":
            target_program = program[0]
            target_method = program[1]
            benchmark_obj = SciMarkBenchmark(target_program, target_method, method_level)
        elif benchmark == "Dacapobench":
            #program is a tuple of (test_method, test_class, test_namespace, test_group, unit_tests)
            test_method = program[0]
            test_class = program[1]
            test_namespace = program[2]
            test_group = program[3]
            unit_tests = program[4]
            methods_list = program[5] if not method_level else None
            benchmark_obj = DaCapoBenchmark(test_method, test_class, test_namespace, test_group, unit_tests, application_name, method_level, methods_list)
        else:
            logger.error("Invalid benchmark")
            break

        folder_name = program[1] if isinstance(program, tuple) else program
        if benchmark == "HumanEval": 
            folder_name = program[0]

        if benchmark_obj.get_original_code() is None:
            results[folder_name] = "Unable to find original code"
            continue
        
        original_code_compiles = benchmark_obj.set_original_energy()
        if not original_code_compiles:
            logger.error(f"Unable to compile or measure energy of the original code for {program}")
            results[folder_name] = "Unable to compile or measure energy of the original code or timeout"
            continue
        
        errors = 0
        reoptimize_lastly_flag = 0
        evaluator_feedback = ""
        original_code = benchmark_obj.get_original_code()
        last_working_optimized_code = original_code
        last_optimized_code = original_code
        num_success_iteration = 0
        total_failure = 0

        # filter optimization patterns for most applicable
        ast = benchmark_obj.pre_process(last_optimized_code)
        flame_report = benchmark_obj.dynamic_analysis(code=last_optimized_code) if benchmark == "HumanEval" or not method_level else None
        top_k_patterns = filter_patterns(llm_assistant=advisor, code=original_code, ast=None, flame_report=None)

        while True:
            if total_failure == 2:
                logger.error("Unable to produce functional equivalent programs.")
                if benchmark == "Dacapobench":
                    # restore the last_working_optimized_code
                    benchmark_obj.restore_last_working_optimized_code(last_working_optimized_code)
                if num_success_iteration == 0:
                    results[folder_name] = "Unable to produce functional equivalent programs."
                else:
                    logger.info(f"{num_success_iteration} optimization completes, writing results to file.....")
                    energy_data = benchmark_obj.get_energy_data()
                    results[folder_name] = write_result(energy_data, folder_name, evaluator_feedback_data, results_dir)
                break
            # optimize code
            if reoptimize_lastly_flag == 0:
                logger.info(f"Optimizing {program}, iteration {num_success_iteration}")
                if errors > 0 and errors < 3:
                    error_message = benchmark_obj.get_compilation_error()
                    if error_message is None: 
                        error_message = benchmark_obj.get_runtime_error()
                    last_optimized_code = handle_error(error_message=error_message, llm_assistant=generator)
                else:
                    if evaluator_feedback is not None and evaluator_feedback != "":
                        last_optimized_code = llm_optimize(code=last_optimized_code, llm_assistant=generator, evaluator_feedback=evaluator_feedback)
                    else:
                        ast = benchmark_obj.pre_process(last_optimized_code)
                        flame_report = benchmark_obj.dynamic_analysis(code=last_optimized_code) if benchmark == "HumanEval" or not method_level else None
                        last_optimized_code = llm_optimize(code=last_optimized_code, llm_assistant=generator, evaluator_feedback=evaluator_feedback, ast=ast, flame_report=flame_report, optimization_patterns=top_k_patterns)
            else:
                logger.info("re-optimizing from latest working optimization")
                generator.clear_memory()
                evaluator.clear_memory()
                evaluator_feedback = ""
                ast = benchmark_obj.pre_process(last_working_optimized_code)
                flame_report = benchmark_obj.dynamic_analysis(code=last_working_optimized_code) if benchmark == "HumanEval" or not method_level else None
                last_optimized_code = llm_optimize(code=last_working_optimized_code, llm_assistant=generator, evaluator_feedback=evaluator_feedback, ast=ast, flame_report=flame_report)
                reoptimize_lastly_flag = 0
            
            # Error in LLM completion
            if last_optimized_code is not None:       
                # code post_process
                last_optimized_code = benchmark_obj.post_process(last_optimized_code)

                # static analysis
                status = benchmark_obj.static_analysis(last_optimized_code)
            else:
                status = Status.RUNTIME_ERROR_OR_TEST_FAILED
            
            # switch case of status
            if (status == Status.COMPILATION_ERROR or status == Status.RUNTIME_ERROR_OR_TEST_FAILED):
                if errors == 3:
                    logger.error("Could not compile or run optimized file after 3 attempts, will re-optimize from lastest working optimized file")
                    reoptimize_lastly_flag = 1
                    errors = 0
                    evaluator_feedback = ""
                    total_failure += 1
                errors += 1
                logger.error("Compile or runtime error in optimized file, re-optimizing")
                continue
            else:
                num_success_iteration += 1
                errors = 0
                # Copy lastest optimized code for logic error re-optimization
                last_working_optimized_code = last_optimized_code
                total_failure = 0

                evaluator_feedback_data = benchmark_obj.get_evaluator_feedback_data()
                
                if num_success_iteration == self_optimization_step:
                    logger.info("Optimization Complete, writing results to file.....")
                    energy_data = benchmark_obj.get_energy_data()
                    results[folder_name] = write_result(energy_data, folder_name, evaluator_feedback_data, results_dir)
                    break
                
                # Perform dynamic analysis using flame graph
                if benchmark == "HumanEval" or not method_level:
                    benchmark_obj.dynamic_analysis(last_optimized_code)
                    evaluator_feedback_data = benchmark_obj.get_evaluator_feedback_data()

                # getting feedback from the evaluator
                logger.info("Regression test success, getting evaluator feedback")
                evaluator_feedback = evaluator_llm(evaluator_feedback_data=evaluator_feedback_data, llm_assistant=evaluator)
                logger.info("Got evaluator feedback")
        
        # clearing LLM memory
        generator.clear_memory()
        evaluator.clear_memory()
        advisor.clear_memory()
    
def main():
    args=parse_arguments()
    
    benchmark = args.benchmark
    num_programs = args.num_programs
    model = args.llm
    self_optimization_step = args.self_optimization_step
    application_name = args.application_name
    method_level = args.method_level
    
    if benchmark == "Dacapobench":
        start_time = time.time()

    master_script(benchmark, num_programs, application_name, model, self_optimization_step, method_level)       

    if benchmark == "Dacapobench":
        end_time = time.time()
        elapsed_time = end_time - start_time
        num_steps = LLMAgent.get_global_counter()
        logger.info(f"Total time taken: {elapsed_time:.2f} seconds")
        logger.info(f"Total steps taken: {num_steps}")
        with open(f"{USER_PREFIX}/results/{benchmark}/system_{application_name}.txt", "w") as f:
            f.write(f"Total steps taken: {num_steps}\n")
            f.write(f"Total time taken: {elapsed_time:.2f} seconds\n")
if __name__ == "__main__":
    main()