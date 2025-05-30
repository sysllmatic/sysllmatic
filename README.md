# SysLLMatic
## About
## Table of Contents
- [Environment Requirement](#environment-requirement)
- [Reproduce Results](#reproduce-results)
- [Running the pipeline](#running-the-pipeline)
- [Analysis and evaluation](#analysis-and-evaluation)
- [Code Dependencies](#code-dependencies)

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

## Reproduce Results
To set up the pipeline, follow these steps:
1. **Clone the repository:**
   ```bash
   git clone <repository-link>
   cd <project-directory>
2. **Install the required dependencies using the Makefile**
    ```bash
   make setup
3. **Create .env in root directory**
    This should include:
    ```bash
    API_KEY=your_openai_api_key_here
    USER_PREFIX=$(pwd)
    ```
    Then source your env with
    ```bash
    . .env
    ```
4. **Update RAPL/main.c write path**
    Change the path to language .csv file to match your absolute path
    ```bash
    strcpy(path, “ABSOLUTE_PATH/sysllmatic/src/runtime_logs/");
    ```
    Then run make in RAPL directory
    ```bash
    make
## Running the pipeline
5. **Run the main script in the home directory (/sysllmatic)**
    ```bash
    make run ARGS="--benchmark FILLME --llm gpt-4o --self_optimization_step 2 --num_programs 2"
    ```
    To use GenAI studio to inference open-source models
    ```bash
    make run ARGS="--benchmark FILLME --llm llama3.3:70b --self_optimization_step 2 --num_programs 2 --genai_studio True"
    ```
