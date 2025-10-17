import csv
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import json

try:
    import lizard
except Exception:
    print("ERROR: 'lizard' is required. Install with: pip install lizard", file=sys.stderr)
    sys.exit(1)

def strip_comments_java(src: str) -> str:
    src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
    src = re.sub(r'//.*?$', '', src, flags=re.M)
    return src

def normalize(src: str) -> str:
    src = strip_comments_java(src)
    src = re.sub(r'\s+', '', src)
    return src

def analyze_functions_with_ranges(java_path: str) -> Dict[str, str]:
    """
    Parse a Java file, break it into individual functions, and extract the code for each one so we can compare bodies later.
    Returns: dict long_name -> raw body slice
    """
    with open(java_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.read().splitlines()
    result = lizard.analyze_file(java_path)
    flist = sorted(result.function_list, key=lambda x: getattr(x, 'start_line', 0))
    funcs: Dict[str, str] = {}
    for i, f in enumerate(flist):
        start = getattr(f, 'start_line', None)
        end = getattr(f, 'end_line', None)
        if start is None:
            continue
        if end is None:
            next_start = getattr(flist[i+1], 'start_line', None) if i+1 < len(flist) else None
            end = (next_start - 1) if next_start else len(lines)
        long_name = getattr(f, 'long_name', getattr(f, 'name', 'unknown'))
        body = '\n'.join(lines[int(start)-1:int(end)])
        funcs[long_name] = body
    return funcs

def count_changed_functions(before_path: str, after_path: str) -> Tuple[int, int]:
    """
    Returns (functions_changed, functions_compared) where:
      functions_compared = |union(before_funcs, after_funcs)| How many functions exist in either version
      functions_changed  = |added| + |deleted| + |modified(shared bodies differ)| How many are “changed” (added, deleted, or modified in body)
    """
    funcs_before = analyze_functions_with_ranges(before_path)
    funcs_after  = analyze_functions_with_ranges(after_path)

    keys_before = set(funcs_before.keys())
    keys_after  = set(funcs_after.keys())

    shared = keys_before & keys_after
    added  = keys_after  - keys_before
    deleted= keys_before - keys_after

    modified = 0
    for k in shared:
        if normalize(funcs_before[k]) != normalize(funcs_after[k]):
            modified += 1

    functions_compared = len(shared) + len(added) + len(deleted)  # union size
    # functions_compared = len(keys_before)
    functions_changed  = modified + len(added) + len(deleted)

    return functions_changed, functions_compared

def find_pairs(before_dir: Path, after_dir: Path) -> List[Tuple[str, str]]:
    pairs = []
    for b in before_dir.rglob("*.java"):
        rel = b.relative_to(before_dir)
        a = after_dir / rel
        if a.exists():
            pairs.append((str(b), str(a)))
    return pairs

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} App_name", file=sys.stderr)
        sys.exit(2)
    app_name = Path(sys.argv[1])
    folder = f"./../../EQ3/Dacapo_ablation/raw_code/{app_name}_raw"
    # folder = f"./../../EQ1/dacapo/raw_code/{app_name}"

    txt_files = [os.path.join(root, file)
        for root, _, files in os.walk(folder)
        for file in files if file.endswith(".txt")]
    
    os.makedirs(os.path.join(folder, "before"), exist_ok=True)
    os.makedirs(os.path.join(folder, "after"), exist_ok=True)
        
    for txt_file in txt_files:
        content = json.load(open(txt_file))
        src_code_original = content.get('0')[0]
        src_code_optimized = content.get('2', content.get('1'))[0]
        before_java = os.path.join(folder, "before", os.path.basename(txt_file).replace(".txt", ".java"))
        after_java = os.path.join(folder, "after", os.path.basename(txt_file).replace(".txt", ".java"))
        with open(before_java, 'w', encoding='utf-8') as f:
            f.write(src_code_original)
        with open(after_java, 'w', encoding='utf-8') as f:
            f.write(src_code_optimized)
        
    before_dir = os.path.join(folder, "before")
    after_dir = os.path.join(folder, "after")
    before_dir = Path(before_dir)
    after_dir = Path(after_dir)
    pairs = find_pairs(before_dir, after_dir)
    if not pairs:
        print("ERROR: No matching .java files found in before/after directories", file=sys.stderr)
        sys.exit(4)
    rows = []
    total_changed = 0
    total_compared = 0
    for before, after in sorted(pairs):
        changed, compared = count_changed_functions(before, after)
        rows.append({
            "file_name": Path(after).name,
            "functions_compared": compared,
            "functions_changed": changed
        })
        total_changed += changed
        total_compared += compared
    avg = total_changed / len(rows) if rows else 0.0
    avg_compared = total_compared / len(rows) if rows else 0.0
    out_path = Path(f"changed_funcs_report_{app_name}.csv")
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_name", "functions_compared", "functions_changed"])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        writer.writerow({
            "file_name": "AVERAGE",
            "functions_compared":f"{avg_compared:.6f}",
            "functions_changed": f"{avg:.6f}"
        })
    print(f"Wrote CSV to {out_path} with {len(rows)} pairs. Average changed per pair: {avg:.6f}")

if __name__ == "__main__":
    main()