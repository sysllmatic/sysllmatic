import subprocess
import sys
from dotenv import load_dotenv
from utils import Logger
import os
import re

load_dotenv()
USER_PREFIX = os.getenv('USER_PREFIX')
logger = Logger("logs", sys.argv[2]).logger

def get_hotspots(benchmark_name, application_name, top_K):
    """Run the Java application with async-profiler. Need to manually run ant build command first."""
    try:        
        logger.info(f"Running application {application_name} with async-profiler...")
        
        prof_lib = os.path.join(
            USER_PREFIX, "async-profiler", "build", "lib", "libasyncProfiler.so"
        )
        
        if benchmark_name == "Dacapo":
            profiler_cmd = [
                "java",
                f"-agentpath:{prof_lib}=start,event=cpu,file=profile.txt,collapsed",
                "-jar", f"{USER_PREFIX}/benchmark_dacapo/benchmarks/dacapo-evaluation-git-4e3de06d-dirty.jar", application_name
            ]
        elif benchmark_name == "SciMark":
            os.chdir(f"{USER_PREFIX}/benchmark_scimark/{application_name}")     
            main_class = f"jnt.scimark2.{application_name}"
            profiler_cmd = [
                "java",
                "-cp", ".",
                f"-agentpath:{prof_lib}=start,event=cpu,file=profile.txt,collapsed",
                main_class,
            ]
        else:
            raise ValueError(f"Unknown benchmark name: {benchmark_name}")
        subprocess.run(profiler_cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error during async-profiler execution: {e}")

    hotspots = aggregate_by_rightmost_method(application_name, top_K)
    return hotspots

def aggregate_by_rightmost_method(marker, top_n):
    def truncate_stack(stack_str, marker):
        frames = stack_str.split(';')
        first_idx = None
        last_idx = None

        for i, fr in enumerate(frames):
            if marker in fr:
                if first_idx is None:
                    first_idx = i
                last_idx = i

        if first_idx is None:
            return None

        truncated_frames = frames[first_idx:last_idx+1]

        if not truncated_frames:
            return None

        return truncated_frames


    import re

    def rewrite_method_name(method_name):
        lambda_pattern = re.compile(r'^(.*)\.lambda\$([A-Za-z0-9_]+)\$\d+$')
        m = lambda_pattern.match(method_name)
        if m:
            prefix = m.group(1)
            real_method = m.group(2)
            return f"{prefix}.{real_method}"

        method_name = re.sub(r'\.0x[a-fA-F0-9]+[^.]*(?=\.)', '', method_name)

        if '$' in method_name:
            method_name = re.sub(r'\$[^.]+(?=\.)', '', method_name)

        return method_name

    sums = {}

    with open("profile.txt", 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.rsplit(" ", 1)
            if len(parts) != 2:
                continue

            stack_str, count_str = parts
            try:
                count = int(count_str)
            except ValueError:
                continue

            truncated_frames = truncate_stack(stack_str, marker)
            if truncated_frames is None:
                continue

            rightmost_method = truncated_frames[-1]

            rightmost_method = rewrite_method_name(rightmost_method)

            sums[rightmost_method] = sums.get(rightmost_method, 0) + count

    items = [(method, total) for method, total in sums.items()]
    items.sort(key=lambda x: x[1], reverse=True)

    results = items[:top_n]
    logger.info(results)
    return results

def extract_package(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                match = re.match(r'\s*package\s+([\w\.]+);', line)
                if match:
                    return match.group(1)
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
    return None

def contains_uncommented_test(file_path):
    in_block_comment = False

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_strip = line.strip()

                if '/*' in line_strip and '*/' not in line_strip:
                    in_block_comment = True

                if '*/' in line_strip:
                    in_block_comment = False
                    continue

                if in_block_comment:
                    continue

                if line_strip.startswith('//'):
                    continue

                if '@Test' in line_strip:
                    return True
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")

    return False

def find_unit_test(root_dir, class_name, fallback_term):
    fallback_matches = []

    if fallback_term:
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if not filename.endswith(".java"):
                    continue
                file_path = os.path.join(dirpath, filename)

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    if any(fallback_term in line for line in lines):
                        if contains_uncommented_test(file_path):
                            package_name = extract_package(file_path)
                            class_name_no_ext = os.path.splitext(filename)[0]
                            fqcn = f"{package_name}.{class_name_no_ext}" if package_name else class_name_no_ext
                            fallback_matches.append(fqcn)
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")

    res = fallback_matches
    logger.info(f"root_dir: {root_dir}, class_name: {class_name}, fallback_term: {fallback_term}, res: {res}")
    return res