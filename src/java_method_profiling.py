import subprocess
import os
from dotenv import load_dotenv
from utils import Logger
import sys

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
logger = Logger("logs", sys.argv[2]).logger

PROJECT_DIR = f"{USER_PREFIX}/src/java_code_extraction"
JAVA_CLASS_NAME = "JavaCodeExtraction"
TARGET_CLASSES_DIR = os.path.join(PROJECT_DIR, "target", "classes")

EXTRA_JARS = ""

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
