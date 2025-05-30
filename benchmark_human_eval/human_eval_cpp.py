from datasets import load_dataset
import subprocess
import tempfile
import os
import time
import json
import re

# script to construct the human_eval dataset for C++ with stress test

def evaluate_cpp_solution(function_code: str, test_code: str):
    # Create a temporary directory for compilation
    with tempfile.TemporaryDirectory() as tmpdir:
        cpp_file = os.path.join(tmpdir, "solution.cpp")
        binary_file = os.path.join(tmpdir, "solution.out")

        # Combine function and test code
        full_code = f"{function_code}\n\n{test_code}"

        # Write to file
        with open(cpp_file, "w") as f:
            f.write(full_code)

        # Compile using g++
        compile_cmd = [
            "g++", "-std=c++11", cpp_file, "-o", binary_file,
            "-I", "/opt/homebrew/include",  # Include Boost headers
            "-L", "/opt/homebrew/lib",      # Link Boost libraries
            "-lboost_system", "-lboost_filesystem",  # Link specific Boost libraries if needed
            "-lssl", "-lcrypto"
        ]
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True)

        if compile_result.returncode != 0:
            print("❌ Compilation failed:")
            print(compile_result.stderr)
            return False

        # Run the compiled binary
        start_time = time.time()
        run_result = subprocess.run([binary_file], capture_output=True, text=True)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Elapsed time: {elapsed_time:.2f} seconds")

        if run_result.returncode == 0:
            print("✅ Test passed.")
            return True
        else:
            print("❌ Test failed:")
            print(run_result.stderr or run_result.stdout)
            return False

# Load the test dataset
test_dataset_file = "/home/hpeng/E2COOL/benchmark_human_eval/dataset.json"
with open(test_dataset_file, "r") as f:
    test_dataset = json.load(f) 

# Loop through the dataset and evaluate each function
count = 0
for test_entry in test_dataset:
    if "cpp_stress_test" in test_entry:
        function_code = test_entry["function_code"]
        test_code = test_entry["cpp_stress_test"]
        correctness = test_entry["test_code"]
        print(f"Evaluating task: {test_entry['task_id']}")
        res = evaluate_cpp_solution(function_code, test_code)
        
        if res == True:
            count += 1
print(f"Total passed tests: {count}/{len(test_dataset)}")

# # Load the C++ HumanEval-X dataset
# human_eval_dataset = load_dataset("THUDM/humaneval-x", "cpp")

# # Placeholder for loading the COFFE dataset
# coffe_dataset = load_dataset("smartdub/COFFE")
# coffe_humaneval = coffe_dataset["func"].filter(lambda x: x["original_dataset"] == "openai_humaneval")

# # Build dictionary
# entry_to_stress_test = {}

# for entry in coffe_humaneval:
#     entry_point = entry.get("entry_point")
#     stress_test = entry.get("stressful_testcase")  
#     entry_to_stress_test[entry_point] = stress_test

# def extract_entry_point(declaration: str) -> str:
#     # Get the last non-empty line
#     lines = [line.strip() for line in declaration.strip().splitlines() if line.strip()]
#     if not lines:
#         return None

#     last_line = lines[-1]

#     # Apply regex only to the last line
#     match = re.search(r'\b(?:[\w:<>]+(?:\s*[\*&])?\s+)+(\w+)\s*\(', last_line)
#     if match:
#         return match.group(1)
#     return None

# test_dataset = []

# for entry in human_eval_dataset["test"]:
#     task_id = entry["task_id"]
#     declaration = entry["declaration"]
#     solution = entry["canonical_solution"]
#     test = entry["test"]

#     # Combine declaration and solution
#     function_code = f"{declaration.strip()}\n{solution.strip()}"

#     # Find the corresponding stress test
#     entry_point = extract_entry_point(declaration)
#     if task_id == "CPP/38":
#         entry_point = "decode_cyclic"
#     if entry_point == "filp_case": entry_point = "flip_case"
#     elif entry_point == "iscuber": entry_point = "iscube"
#     elif entry_point == "solutions": entry_point = "solution"
#     elif entry_point == "get_matrix_triples": entry_point = "get_max_triples"
#     elif entry_point == "int_to_mini_romank": entry_point = "int_to_mini_roman"
#     stress_test = entry_to_stress_test.get(entry_point)

#     # Append to the dataset
#     test_dataset.append({
#         "task_id": task_id,
#         "entry_point": entry_point,
#         "stress_test": stress_test,
#         "function_code": function_code,
#         "test_code": test,
#     })

# # Save to a JSON file
# output_file = "/Users/peng397/Desktop/test_dataset_original.json"
# with open(output_file, "w") as f:
#     json.dump(test_dataset, f, indent=4)

# print(f"Test dataset saved to {output_file}")