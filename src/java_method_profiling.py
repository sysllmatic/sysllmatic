import subprocess
import os
from dotenv import load_dotenv
from utils import Logger
import sys

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
logger = Logger("logs", sys.argv[2]).logger

# Adjust these constants to your project paths
PROJECT_DIR = "/home/hpeng/E2COOL/src/java_code_extraction"
JAVA_CLASS_NAME = "JavaCodeExtraction"  # The main class name with 'main' method
# The 'target/classes' directory where classes are compiled
TARGET_CLASSES_DIR = os.path.join(PROJECT_DIR, "target", "classes")

# If you need external jars (like JavaParser), put them all into a single path string below.
# For example:
# "/path/to/javaparser-core-3.25.4.jar:/path/to/another-lib.jar"
# If you used Maven, the simplest approach is to create a "fat jar" (shade plugin) or copy dependencies into a folder.
EXTRA_JARS = ""  # e.g. "/home/hpeng/E2COOL/libs/javaparser-core-3.25.4.jar"

def compile_java_project():
    """
    Runs 'mvn clean compile' inside PROJECT_DIR to compile the Java code.
    """
    logger.info("Compiling Java project...")
    cmd = ["mvn", "clean", "compile"]
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, check=True)
        logger.info("Java project compiled successfully.\n")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error compiling Java project:\n{e.stderr}")
        return False

def get_method_source_code(file_path: str, method_name: str) -> str:
    cmd = [
        "mvn",
        "-q",
        "exec:java",
        f"-Dexec.args=print {file_path} {method_name}",
    ]
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, check=True)
        output = result.stdout.strip()
        logger.info(f"method source code: {output}")
        return output
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in get_method_source_code:\n{e.stderr}")

def replace_method_body(file_path: str, method_name: str) -> str:
    cmd = [
        "mvn",
        "-q",
        "exec:java",
        f"-Dexec.args=replace {file_path} {method_name}",
    ]
    try:
        result = subprocess.run(cmd, cwd=PROJECT_DIR, capture_output=True, text=True, check=True)
        logger.info(f"Method body replaced successfully")   
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Error in replace_method_body:\n{e.stderr}")
        return False

if __name__ == "__main__":
    # 1) Compile the Java project
    compile_java_project()

    # 2) Example usage: define a Java file & method name to test
    # java_file_path = "/home/hpeng/dacapobench/benchmarks/bms/fop/build/fop-2.8/fop-core/src/main/java/org/apache/fop/cli/Main.java"
    java_file_path = "/home/hpeng/E2COOL/benchmark_scimark/FFT/FFTOptimized.java"

    method_name = "transform_internal"

    # 3) Get the original method source
    original_src = get_method_source_code(java_file_path, method_name)
    print("Original method source:\n", original_src)

    # 4) Replace the method body (from optimized_java.txt)
    replace_output = replace_method_body(java_file_path, method_name)
    print("After replacement:\n", replace_output)
