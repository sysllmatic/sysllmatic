# dacapo_apps.py
import os
from abc import ABC, abstractmethod
from pathlib import Path
import subprocess
from utils import Logger
from dotenv import load_dotenv
import sys
import csv

load_dotenv()
USER_PREFIX = os.getenv("USER_PREFIX")

class DaCapoApp(ABC):
    @abstractmethod
    def get_source_path(self, class_name, namespace_name, group_name):
        pass

    @abstractmethod
    def get_test_info_from_parts(self, parts, test_class):
        pass

    @abstractmethod
    def get_build_dir(self, group_name):
        pass

    @abstractmethod
    def get_makefile_subfolders(self):
        pass
    
    @abstractmethod
    def get_workload_num(self):
        pass

    @abstractmethod
    def get_app_name(self):
        pass

    @abstractmethod
    def rebuild_and_run(self):
        pass

class FopApp(DaCapoApp):
    def __init__(self):
        self.root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/fop/build/fop-2.8/fop-core"
        self.src_dir = f"{self.root_dir}/src/main/java/org/apache/fop"

    def get_source_path(self, class_name, namespace_name, group_name):
        if namespace_name:
            return f"{self.src_dir}/{namespace_name}/{class_name}.java"
        return f"{self.src_dir}/{class_name}.java"

    def get_test_info_from_parts(self, parts, test_class):
        test_namespace = '/'.join(parts[3:-1])
        test_group = "test_group"
        unit_test_class_name = f"{test_class}TestCase"
        root_path = f"{self.root_dir}/src/test/java/org/apache/fop"
        return test_namespace, test_group, unit_test_class_name, root_path

    def get_build_dir(self, group_name):
        return self.root_dir

    def get_makefile_subfolders(self):
        folder_path = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/fop/build/fop-2.8"
        return [f.path for f in os.scandir(folder_path) if f.is_dir()]
    
    def get_app_name(self):
        return "fop"
    
    def rebuild_and_run(self):
        try:
            subprocess.run(["bash", f"{USER_PREFIX}/benchmark_dacapo/benchmarks/run_fop.sh"], cwd=f"{USER_PREFIX}/benchmark_dacapo/benchmarks/", check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run Fop benchmark: {e}")
            return False
        return True
    
    def get_workload_num(self):
        return 55

class BioJavaApp(DaCapoApp):
    def __init__(self):
        self.root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/biojava/build"

    def get_source_path(self, class_name, namespace_name, group_name):
        folder_name = "aa-prop" if group_name == "aaproperties" else group_name
        base = f"{self.root_dir}/biojava-{folder_name}/src/main/java/org/biojava/nbio/{group_name}"
        return f"{base}/{namespace_name}/{class_name}.java" if namespace_name else f"{base}/{class_name}.java"

    def get_test_info_from_parts(self, parts, test_class):
        test_namespace = '/'.join(parts[4:-1])
        if len(parts) < 4:
            return None, None, None, None
        test_group = parts[3]
        folder_name = "aa-prop" if test_group == "aaproperties" else test_group
        root_path = f"{self.root_dir}/biojava-{folder_name}/src/test/java/org/biojava/nbio/{test_group}"
        unit_test_class_name = f"{test_class}Test"
        return test_namespace, test_group, unit_test_class_name, root_path

    def get_build_dir(self, group_name):
        folder_name = "aa-prop" if group_name == "aaproperties" else group_name
        return f"{self.root_dir}/biojava-{folder_name}"

    def get_makefile_subfolders(self):
        return [f.path for f in os.scandir(self.root_dir) if f.is_dir() and f.name.startswith('biojava-')]
    
    def get_workload_num(self):
        return 2839

    def get_app_name(self):
        return "biojava"

    def rebuild_and_run(self):
        try:
            subprocess.run(["bash", f"{USER_PREFIX}/benchmark_dacapo/benchmarks/run_biojava.sh"], cwd=f"{USER_PREFIX}/benchmark_dacapo/benchmarks/", check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run BioJava benchmark: {e}")
            return False
        return True

class PmdApp(DaCapoApp):
    def __init__(self):
        self.root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/pmd/build/pmd-core"
        self.src_dir = f"{self.root_dir}/src/main/java/net/sourceforge/pmd"

    def get_source_path(self, class_name, namespace_name, group_name):
        return f"{self.src_dir}/{namespace_name}/{class_name}.java" if namespace_name else f"{self.src_dir}/{class_name}.java"

    def get_test_info_from_parts(self, parts, test_class):
        test_namespace = '/'.join(parts[3:-1])
        test_group = "test_group"
        unit_test_class_name = f"{test_class}Test"
        root_path = f"{self.root_dir}/src/test/java/net/sourceforge/pmd"
        return test_namespace, test_group, unit_test_class_name, root_path

    def get_build_dir(self, group_name):
        return self.root_dir

    def get_makefile_subfolders(self):
        return [f.path for f in os.scandir(os.path.dirname(self.root_dir)) if f.is_dir() and f.name.startswith('pmd-')]
    
    def get_app_name(self):
        return "pmd"
    
    def get_workload_num(self):
        return 601
    
    def rebuild_and_run(self):
        try:
            subprocess.run(["bash", f"{USER_PREFIX}/benchmark_dacapo/benchmarks/run_pmd.sh"], cwd=f"{USER_PREFIX}/benchmark_dacapo/benchmarks/", check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run BioJava benchmark: {e}")
            return False
        return True

class GraphchiApp(DaCapoApp):
    def __init__(self):
        self.root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/graphchi/build"
        self.src_dir = f"{self.root_dir}/src/main/java/edu/cmu/graphchi"

    def get_source_path(self, class_name, namespace_name, group_name):
        return f"{self.src_dir}/{namespace_name}/{class_name}.java" if namespace_name else f"{self.src_dir}/{class_name}.java"

    def get_test_info_from_parts(self, parts, test_class):
        test_namespace = '/'.join(parts[3:-1])
        test_group = "test_group"
        unit_test_class_name = f"Test{test_class}"
        root_path = f"{self.root_dir}/test/edu/cmu/graphchi"
        return test_namespace, test_group, unit_test_class_name, root_path

    def get_build_dir(self, group_name):
        return self.root_dir

    def get_makefile_subfolders(self):
        folder_path = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/graphchi"
        return [f.path for f in os.scandir(folder_path) if f.is_dir() and f.name == 'build']
    
    def get_app_name(self):
        return "graphchi"
    
    def get_workload_num(self):
        return 1000000
    
    def rebuild_and_run(self):
        try:
            subprocess.run(["bash", f"{USER_PREFIX}/benchmark_dacapo/benchmarks/run_graphchi.sh"], cwd=f"{USER_PREFIX}/benchmark_dacapo/benchmarks/", check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run BioJava benchmark: {e}")
            return False
        return True
    
class ZxingApp(DaCapoApp):
    def __init__(self):
        self.root_dir = f"{USER_PREFIX}/benchmark_dacapo/benchmarks/bms/zxing/build/core"
        self.src_dir = f"{self.root_dir}/src/main/java/com/google/zxing"
        
    def get_source_path(self, class_name, namespace_name, group_name):
        return f"{self.src_dir}/{namespace_name}/{class_name}.java" if namespace_name else f"{self.src_dir}/{class_name}.java"

    def get_test_info_from_parts(self, parts, test_class):
        test_namespace = '/'.join(parts[3:-1])
        test_group = "test_group"
        unit_test_class_name = f"{test_class}TestCase"
        root_path = f"{self.root_dir}/src/test/java/com/google/zxing"
        return test_namespace, test_group, unit_test_class_name, root_path
    
    def get_build_dir(self, group_name):
        return self.root_dir

    def get_makefile_subfolders(self):
        return [f.path for f in os.scandir(os.path.dirname(self.root_dir)) if f.is_dir() and f.name == 'core']
    
    def get_app_name(self):
        return "zxing"
    
    def get_workload_num(self):
        return 1254
    
    def rebuild_and_run(self):
        try:
            subprocess.run(["bash", f"{USER_PREFIX}/benchmark_dacapo/benchmarks/run_zxing.sh"], cwd=f"{USER_PREFIX}/benchmark_dacapo/benchmarks/", check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to run zxing benchmark: {e}")
            return False
        return True

def get_app(app_name, check:True) -> DaCapoApp:
    mapping = {
        'fop': FopApp,
        'biojava': BioJavaApp,
        'pmd': PmdApp,
        'graphchi': GraphchiApp,
        'zxing': ZxingApp,
    }
    
    if check:
        if app_name not in mapping:
            raise ValueError(f"Unknown DaCapo app: {app_name}")
        
        if not _build_app(app_name):
            raise RuntimeError(f"Failed to build {app_name} app.")
    
    return mapping[app_name]()

# === Utilities ===
DACAPO_ROOT = Path(f"{USER_PREFIX}/benchmark_dacapo/benchmarks")
dirty_jar = DACAPO_ROOT / "dacapo-evaluation-git-4e3de06d-dirty.jar"
clean_jar = DACAPO_ROOT / "dacapo-evaluation-git-4e3de06d.jar"
DACAPO_JAR = dirty_jar if dirty_jar.exists() else clean_jar
JAVA8_HOME = "/usr/lib/jvm/java-8-openjdk-amd64"
JAVA11_HOME = "/usr/lib/jvm/java-11-openjdk-amd64"
RUNTIME_LOG = os.path.join(USER_PREFIX, "src/runtime_logs/java.csv")
RAPL_TOOL = os.path.join(USER_PREFIX, "MEASURE/main")

logger = Logger("logs", sys.argv[2]).logger

def _build_app(app_name):
    # Set Java 8 for build
    _set_java_home(JAVA8_HOME)

    result = subprocess.run(["ant", app_name], cwd=str(DACAPO_ROOT), check=True)
    
    if result.returncode != 0:
        logger.error(f"Failed to build {app_name} with ant.")
        return False
    else:
        return True

def _set_java_home(java_home: str):
    os.environ["JAVA_HOME"] = java_home
    os.environ["PATH"] = f"{java_home}/bin:" + os.environ["PATH"]
    
def run_app_and_measure(app):
    """
    Builds and runs a DaCapo benchmark with profiling.
    If memory is 0, tries again once.
    """
    app_name = app.get_app_name()
    logger.info(f"Running benchmark with profiling: {app_name}")
    try:
        metrics = _run_dacapo(app_name)
        # If memory is 0, try again once
        if metrics[3] == 0:
            logger.warning(f"Memory usage is 0 for {app_name}, retrying...")
            metrics = _run_dacapo(app_name)
        throughput = app.get_workload_num() / metrics[1] if metrics[1] != 0 else 0
        logger.info(f"✅ Success: {app_name} → Energy={metrics[0]} J, Latency={metrics[1]} s, CPU={metrics[2]}, Mem={metrics[3]} MB, Throughput={throughput} ops/s")
        if any(m == 0 for m in metrics):
            return (0, 0, 0, 0, 0)
        return metrics + (throughput,)
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error running {app_name}: {e}")
        return (0, 0, 0, 0, 0)
    
def _run_dacapo(app_name):

    with open(RUNTIME_LOG, "w") as f:
        f.write("")

    subprocess.run("sudo modprobe msr", shell=True, check=True, cwd=str(DACAPO_ROOT))

    # Construct Java command
    java_cmd = f"java -jar {DACAPO_JAR} --no-validation {app_name}"

    # Run with RAPL tool
    subprocess.run(f"sudo {RAPL_TOOL} \"{java_cmd}\" java {app_name}", cwd=str(DACAPO_ROOT), shell=True, check=True)
    subprocess.run(f"sudo chmod -R 777 {RUNTIME_LOG}", shell=True, check=True, cwd=str(DACAPO_ROOT))

    return extract_metrics()

def extract_metrics():
    benchmark_data = []
    with open(RUNTIME_LOG, mode='r') as file:
        reader = csv.reader(file)
        for index, row in enumerate(reader):
            if index < 5:
                benchmark_data.append((row[0], float(row[1]), float(row[2]), float(row[3]), float(row[4])))

    benchmark_data = [d for d in benchmark_data if d[1] >= 0]
    if not benchmark_data:
        return 0, 0, 0, 0

    avg_energy = sum(d[1] for d in benchmark_data) / len(benchmark_data)
    avg_latency = sum(d[2] for d in benchmark_data) / len(benchmark_data)
    avg_cpu = sum(d[3] for d in benchmark_data) / len(benchmark_data)
    avg_memory = sum(d[4] for d in benchmark_data) / len(benchmark_data)

    return avg_energy, avg_latency, avg_cpu, avg_memory
