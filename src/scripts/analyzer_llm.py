from dotenv import load_dotenv  
from pydantic import BaseModel  
import sys  
import os  
import json  
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from agent import LLMAgent

# Setup environment  
load_dotenv()  
USER_PREFIX = os.getenv('USER_PREFIX')  
openai_key = os.getenv('API_KEY')
genai_api_key = os.getenv('GenAI_API_KEY')

class AnalysisResult(BaseModel):  
    description: str
    comparison: str
    optimization_pattern: str
  
def analyze_optimization(original_code, optimized_code, llm_assistant):  
    
    print("Analyzing code optimization...")

    prompt = f"""  
I have two versions of a program: an original implementation and a final optimized version. Please analyze the differences between them with the following goals:

1. **Code Function Explanation**: Briefly explain what the code is doing—what problem it solves and how it works.

2. **Optimization Comparison**: Compare the original and optimized versions to identify:
   - **Algorithmic changes**: Any differences in logic, algorithm design, or problem-solving approach.
   - **Performance improvements**: Enhancements related to time complexity, space efficiency, or runtime behavior.
   - **Redundant code removal**: Elimination of unnecessary logic, method calls, or control structures.
   - **Other noteworthy changes**: Any structural or stylistic differences that could impact performance or readability.
   
3. **Optimization Pattern Classification**:
   Based on the overall nature of the optimized code, assign the following. Return No Meaningful Change if no meaningful change is made.
   - **Exactly one high-level optimization pattern** from the list below  
   - **One most representative sub-pattern** within that high-level category
   
   ### High-Level Optimization Patterns Taxonomy:
   - **Algorithm-Level Optimizations**
        - Select Computationally Efficient Algorithms
        - Select Algorithm Based on Instruction Speed
        - Structure Algorithm to Support ILP
        - Select Space Efficient Algorithm
        - Inheritance over Delegation for Energy Efficiency
   - **Control-Flow and Branching Optimizations**
        - Make Conditional Branches More Predictable
        - Remove Branches with min/max Instructions
        - Remove Branches by Doing Extra Work
        - Remove Branching with Masking
        - Rearranging Branches
        - Combining Branches
   - **Memory and Data Locality Optimizations**
        - Access Data with Appropriate Type
        - Increase Cache Efficiency via Locality
        - Arrange Data for Optimal Prefetching
        - Avoid Cache Capacity Issues
        - Increase Workload to Hide Latency
        - Use Smaller Data Types
        - Caching, Buffering
        - Improve Data Structure Locality
        - Optimize Object Use
        - Reduce RTSJ Immortal Memory Bloat
   - **Loop Transformations**
        - Remove Conditional by Loop Unrolling
        - Loop Distribution (Fission)
        - Loop Fusion, Peeling, Interchanging
        - Loop Invariant Branches
        - Loop Strip-mining
   - **I/O and Synchronization**
        - Selection of I/O Size
        - Polling
        - Non-Blocking I/O
   - **Data Structure Selection and Adaptation**
        - Choose Structure for Energy Efficiency
        - Darwinian Selection
        - Select via Method Calls
        - Cross-Library Comparison
   - **Code Smells and Structural Simplification**
        - Remove Optional Features
        - Remove Redundant Method Calls
        - Extract Long Methods
        - Remove Duplicates
        - Move Methods to Reduce Feature Envy
        - Minimize God Classes
        - Type Checking
         
Here are the two versions of the code:  
            
Original Code:  
{original_code}  

Final Optimized Code:  
{optimized_code}  

Output Structure:  
First provide a brief description of what the code is doing.  
Then provide a detailed comparison and highlight the specific optimizations or decisions made in the optimized version.  
Assign the **single most representative high-level optimization pattern** from the list above to the changes made in the optimized version. Or return "No Meaningful Change" if no meaningful change is made.
"""  
  
    # Send to LLM for analysis  
    llm_assistant.add_to_memory("user", prompt)  
    llm_assistant.generate_response(response_format=AnalysisResult)  
    response = llm_assistant.get_last_msg()  
      
    try:  
        content_dict = json.loads(response["content"])  
        return content_dict  
    except json.JSONDecodeError as e:  
        print(f"Failed to decode JSON: {e}")  
        return "Error: Failed to analyze code optimization."  

if __name__ == "__main__":
    results_dir = f"{USER_PREFIX}/final_results/humaneval" 
    valid_files = sorted(os.listdir(results_dir))
    valid_files = [file for file in valid_files if file.endswith(".txt") and file != "optimization_summary.txt"]

    for program in range(0, 164):
        filename = f"{program}.txt"
        if filename not in valid_files:
            print(f"File {filename} not found in {results_dir}")
        else:
            with open(os.path.join(results_dir, filename), "r") as f:
                data = json.load(f)
                original_code = data.get("0")[0]
                
                res_1 = data.get("1")
                optimized_code = res_1[0]
                runtime_improvement = res_1[2]    
                if data.get("2") is not None:
                    res_2 = data.get("2")
                    if res_2[2] > runtime_improvement:
                        # If the second result is worse, we ignore it
                        optimized_code = res_2[0]
    
                # Initialize LLM agent  
                analyzer_llm = LLMAgent(openai_api_key=openai_key, genai_api_key=genai_api_key,   
                    model="gpt-4o-mini", use_genai_studio=False,   
                    system_message="You are a code expert. Analyze code optimizations thoroughly.")  
                
                # Analyze code optimization  
                content_dict = analyze_optimization(original_code, optimized_code, analyzer_llm)
                content_dict["program_name"] = program  
                print("Analysis Result:")
                print(content_dict)
                analyzer_llm.clear_memory()

                with open("analysis_result_humaneval.txt", "a") as f:  
                    f.write(json.dumps(content_dict, indent=2))
                print("Analysis result saved to analysis_result.txt")