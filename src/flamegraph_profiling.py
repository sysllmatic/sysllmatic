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
        
        # path to the async-profiler native library
        prof_lib = os.path.join(
            USER_PREFIX, "async-profiler", "build", "lib", "libasyncProfiler.so"
        )
        
        if benchmark_name == "Dacapo":
            profiler_cmd = [
                "java",
                f"-agentpath:{prof_lib}=start,event=cpu,file=profile.txt,collapsed",
                "-jar", "/home/hpeng/E2COOL/benchmark_dacapo/benchmarks/dacapo-evaluation-git-unknown${git.dirty}.jar", application_name
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
    """
    1) Reads each line from 'profile.txt' (collapsed stack + count).
    2) Truncates stack to [first..last] occurrence of 'marker'.
    3) Strips trailing frames containing '$' *unless* it's a lambda frame (".lambda$...").
    4) Takes the rightmost frame from that truncated set.
       - If that frame is a lambda, rewrite it to the outer method name.
    5) Aggregates sample counts by that *unique* rightmost method.
    6) Returns a list of (rightmost_method, total_count) sorted descending by count,
       limited to top_n.
    """

    def truncate_stack(stack_str, marker):
        """Truncate to [first..last] occurrence of marker, then strip trailing '$'-frames (except lambdas)."""
        frames = stack_str.split(';')
        first_idx = None
        last_idx = None

        # Find first/last occurrence of marker
        for i, fr in enumerate(frames):
            if marker in fr:
                if first_idx is None:
                    first_idx = i
                last_idx = i

        if first_idx is None:
            return None  # No marker found

        truncated_frames = frames[first_idx:last_idx+1]

        if not truncated_frames:
            return None

        return truncated_frames


    import re

    def rewrite_method_name(method_name):
        """
        Rewrite the method name to a more concise form.

        Three cases are handled:
        
        1. Lambda methods:
            For example, if method_name is:
            org/biojava/nbio/aaproperties/Utils.lambda$getNumberOfInvalidChar$0
            it is transformed into:
            org/biojava/nbio/aaproperties/Utils.getNumberOfInvalidChar

        2. Inner class methods:
            For example, if method_name is:
            org/apache/fop/image/loader/batik/PreloaderWMF$Loader.getImage
            it is transformed into:
            org/apache/fop/image/loader/batik/PreloaderWMF.getImage

        3. Weird hex segments:
            For example, if method_name is:
            org/biojava/nbio/aaproperties/CommandPrompt.0x00007fb99013e050.<init>
            it is transformed into:
            org/biojava/nbio/aaproperties/CommandPrompt.<init>

        Otherwise, the method_name is returned unchanged.
        """
        # Handle lambda method names
        lambda_pattern = re.compile(r'^(.*)\.lambda\$([A-Za-z0-9_]+)\$\d+$')
        m = lambda_pattern.match(method_name)
        if m:
            prefix = m.group(1)
            real_method = m.group(2)
            return f"{prefix}.{real_method}"

        # Remove any '.0x...' segments (case #3)
        # e.g. org/biojava/nbio/aaproperties/CommandPrompt.0x00007fb99013e050.<init> -> org/biojava/nbio/aaproperties/CommandPrompt.<init>
        method_name = re.sub(r'\.0x[a-fA-F0-9]+[^.]*(?=\.)', '', method_name)

        # Handle inner class method names by removing the inner class part (case #2)
        # This regex removes any inner class section (e.g. "$Loader") that appears before the method call.
        if '$' in method_name:
            method_name = re.sub(r'\$[^.]+(?=\.)', '', method_name)

        return method_name

    sums = {}

    with open("profile.txt", 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            # Separate stack from count
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

            # Rightmost frame is the last frame
            rightmost_method = truncated_frames[-1]

            # If it's a lambda frame, rewrite
            rightmost_method = rewrite_method_name(rightmost_method)

            sums[rightmost_method] = sums.get(rightmost_method, 0) + count

    # Convert sums dict to list and sort by count descending
    items = [(method, total) for method, total in sums.items()]
    items.sort(key=lambda x: x[1], reverse=True)

    results = items[:top_n]
    logger.info(results)
    return results

def main():
    # Example usage
    results = get_hotspots("SciMark", "LU", 1)
    print(f"results length: {len(results)}")
    for method, total in results:
        print(f"{method} {total}")

if __name__ == "__main__":
    main()

def extract_package(file_path):
    """Extracts the package declaration from a .java file."""
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
    """
    Returns True if '@Test' appears outside of line or block comments.
    We do a naive approach:
      - Skip lines that begin with '//'
      - Track block comments between '/*' and '*/'
      - Search '@Test' in lines that are not commented out
    """
    in_block_comment = False

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line_strip = line.strip()

                # Detect start of block comment
                if '/*' in line_strip and '*/' not in line_strip:
                    in_block_comment = True

                # Detect end of block comment
                if '*/' in line_strip:
                    in_block_comment = False
                    # Possibly, '@Test' could appear after '*/' on the same line 
                    # but let's keep it simple and skip the rest of this line
                    continue

                # Skip lines entirely inside a block comment
                if in_block_comment:
                    continue

                # Skip single-line comment
                if line_strip.startswith('//'):
                    continue

                # Now see if '@Test' is here
                if '@Test' in line_strip:
                    return True
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")

    return False

def find_unit_test(root_dir, class_name, fallback_term):
    """
    Step 1: Find files whose name starts with `class_name`, return FQCNs 
            only if they contain an uncommented '@Test'.
    Step 2: If none found, search for files containing `fallback_term`, 
            but again only accept them if they contain an uncommented '@Test'.
    """
    filename_matches = []
    fallback_matches = []

    # Step 1: Match filenames like SequenceMixinTest.java and extract FQCNs
    for dirpath, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.startswith(class_name) and filename.endswith(".java"):
                file_path = os.path.join(dirpath, filename)
                # Check if file has an uncommented @Test
                if contains_uncommented_test(file_path):
                    package_name = extract_package(file_path)
                    class_name_no_ext = os.path.splitext(filename)[0]
                    fqcn = f"{package_name}.{class_name_no_ext}" if package_name else class_name_no_ext
                    filename_matches.append(fqcn)

    # Step 2: If no match, search for usage of fallback term
    if not filename_matches and fallback_term:
        for dirpath, _, filenames in os.walk(root_dir):
            for filename in filenames:
                if not filename.endswith(".java"):
                    continue
                file_path = os.path.join(dirpath, filename)

                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    if any(fallback_term in line for line in lines):
                        # Check if file has an uncommented @Test
                        if contains_uncommented_test(file_path):
                            package_name = extract_package(file_path)
                            class_name_no_ext = os.path.splitext(filename)[0]
                            fqcn = f"{package_name}.{class_name_no_ext}" if package_name else class_name_no_ext
                            fallback_matches.append(fqcn)
                except Exception as e:
                    logger.error(f"Error reading file {file_path}: {e}")

    res = filename_matches + fallback_matches
    logger.info(f"root_dir: {root_dir}, class_name: {class_name}, fallback_term: {fallback_term}, res: {res}")
    return res