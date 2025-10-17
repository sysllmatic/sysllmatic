import subprocess
import csv
import sys
import os
import json

def run_lizard(java_file):
    """Run lizard on the given Java file and return output."""
    try:
        result = subprocess.run(["lizard", java_file], capture_output=True, text=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running lizard: {e.stdout}")
        sys.exit(1)

def parse_file_summary(lizard_output):
    """Extract the file-level summary from lizard output."""
    lines = lizard_output.strip().split('\n')
    summary_start = False
    for i, line in enumerate(lines):
        if line.startswith("Total") and "AvgCCN" in line:
            summary_start = True
            data_line = lines[i+2]
            break

    if not summary_start:
        print(f"File-level summary not found in lizard output.")
        return None

    # Parse header and values
    values = [v.strip() for v in data_line.split()]
    return values

def main():
    if len(sys.argv) != 3:
        print("Usage: python lizard_summary_to_csv.py <app_name> <original>")
        sys.exit(1)

    app_name = sys.argv[1]
    original = sys.argv[2]
    if original == "true":
        output_csv = f"data/{app_name}_original.csv"
    else:
        output_csv = f"data/{app_name}_optimized.csv"
    
    folder = f"./../../EQ1/dacapo/raw_code/{app_name}"
    
    # remove all existing .java files in the folder
    for root, _, files in os.walk(folder):
        for file in files:
            if file.endswith(".java"):
                os.remove(os.path.join(root, file))
    
    txt_files = [os.path.join(root, file)
        for root, _, files in os.walk(folder)
        for file in files if file.endswith(".txt")]
    
    for txt_file in txt_files:
        content = json.load(open(txt_file))
        if original == "true":
            src_code = content.get('0')[0]
        else:
            src_code = content.get('2', content.get('1'))[0]
        with open(txt_file.replace(".txt", ".java"), 'w') as f:
            f.write(src_code)
    
    java_files = [os.path.join(root, file)
        for root, _, files in os.walk(folder)
        for file in files if file.endswith(".java")]

    if not java_files:
        print("No Java files found in the specified folder.")
        sys.exit(1)

    header = ["File", "Total nloc", "Avg.NLOC", "AvgCCN", "Avg.token", "Fun Cnt", "Warning cnt", "Fun Rt", "nloc Rt"]
    rows = []
    
    for java_file in java_files:
        output = run_lizard(java_file)
        if output:
            file_name = os.path.basename(java_file)
            values = parse_file_summary(output)
            if values:
                rows.append([file_name] + values)
            else:
                print(f"Warning: could not parse summary for {java_file}")

    # Write to CSV
    with open(output_csv, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)
    print(f"Summary written to {output_csv}")

if __name__ == "__main__":
    main()
