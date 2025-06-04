# SysLLMatic: Large Language Models are Software System Optimizers
## About
This repository contains the artifacts for the project **SysLLMatic: Large Language Models are Software System Optimizers**. It includes implementation details, instructions to reproduce results, and experimental data.

Our artifact includes the following
| Item             | Description                                         | Corresponding content in the paper         | Path                                                                                 |
|------------------|-----------------------------------------------------|--------------------------------------------|--------------------------------------------------------------------------------------|
| Pattern Catalog  | The catalog including 43 performance optimization patterns | §4, Figure 2-3, Table 2                   | [pattern_catalog](./pattern_catalog)                                                 |
| Implementation   | The implementation of SysLLMatic                    | §5, Figure 4                               | [src](./src)                                                                         |
| Benchmarks       | The benchmarks we used in evaluation                | §6-B                                      | [humaneval](./benchmark_humaneval), [scimark](./benchmark_scimark), [dacapo](./benchmark_dacapo) |
| Eval             | The evaluation scripts and results                  | §7, Figure 5-9, Table 4-6                  | [eval](./eval)                                                                       |

## Table of Contents
- [Environment Requirement](#environment-requirement)
- [Environment Setup](#environment-setup)
- [Running the pipeline](#running-the-pipeline)

## Environment Requirement
This artifact requires a machine with the following capabilities to support RAPL (Running Average Power Limit) and read MSR (Model-Specific Registers):

1. **Hardware**
- Intel Processor: Machine with Intel processors supporting RAPL (Sandy Bridge or newer).
- MSR Support: Machine must allow access to MSRs.

2. **Operating System**
- Linux-based OS (e.g., Ubuntu 16.04+).
- Linux Kernel Version 3.13+ required for RAPL support.
- Root Access: MSRs can only be accessed with root/superuser privileges.

3. **Software**
- msr-tools: Install for reading MSRs:
    ```bash
    sudo apt-get install msr-tools
    ```
## Environment Setup
1. **Clone the repository:**
   ```bash
   git clone <repository-link>
   cd <project-directory>
   ```
2. **Install the required dependencies using the Makefile**
    ```bash
   make setup
   ```
3. **Create `.env` file in the root directory**
    Add the following:
    ```bash
    API_KEY=your_openai_api_key_here
    USER_PREFIX=$(pwd)
    ```
    Then source your env with
    ```bash
    . .env
    ```
4. **Compile performance measurement module**
    In the `MEASURE` directory, run:
    ```bash
    make
    ```

## Running the pipeline
5. **Run the main script from the project root (`/sysllmatic`)**
    Run HumanEval_CPP benchmark
    ```bash
    make run ARGS="--benchmark HumanEval --llm gpt-4o --self_optimization_step 2 --num_programs 2"
    ```
    Run SciMark benchmark
    ```bash
    make run ARGS="--benchmark SciMark --llm gpt-4o --self_optimization_step 2"
    ```
    Run Dacapo benchmark
    Prebuild the target application following the Dacapobench official instruction, then run:
    ```bash
    make run ARGS="--benchmark Dacapobench --llm gpt-4o --self_optimization_step 2 --application_name biojava"
    ```